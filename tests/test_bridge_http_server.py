from __future__ import annotations

import http.client
import json
import base64
import threading
from concurrent.futures import Future
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
from time import sleep
from types import SimpleNamespace
from urllib.parse import quote

from PIL import Image

from flatshot.application.config_paths import ConfigPathResolver
from flatshot.application.export_runner import ExportRunner
from flatshot.bridge.http_server import FlatShotBridgeRequestHandler, create_server
from flatshot.bridge.service import FlatShotBridgeService


def _png(path: Path) -> Path:
    Image.new("RGBA", (4, 4), (255, 0, 0, 255)).save(path)
    return path


class InlineExecutor:
    def __init__(self, max_workers=1):
        self.max_workers = max_workers

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.shutdown()

    def submit(self, fn, arg):
        future = Future()
        try:
            future.set_result(fn(arg))
        except Exception as exc:
            future.set_exception(exc)
        return future

    def shutdown(self, wait=True, cancel_futures=False):
        return None


def _export_runner_factory(**kwargs) -> ExportRunner:
    return ExportRunner(**kwargs, executor_factory=InlineExecutor)


@contextmanager
def running_bridge(config_dir: Path, service: FlatShotBridgeService | None = None):
    service = service or FlatShotBridgeService(config_resolver=ConfigPathResolver(config_dir))
    server = create_server("127.0.0.1", 0, service=service)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_port
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def request_json(port: int, method: str, path: str, body: dict | str | None = None):
    headers = {}
    payload = None
    if isinstance(body, dict):
        payload = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    elif isinstance(body, str):
        payload = body.encode("utf-8")
        headers["Content-Type"] = "application/json"

    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request(method, path, body=payload, headers=headers)
        response = connection.getresponse()
        raw = response.read()
        data = json.loads(raw.decode("utf-8")) if raw else {}
        return response.status, data
    finally:
        connection.close()


def request_raw(port: int, method: str, path: str):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request(method, path)
        response = connection.getresponse()
        raw = response.read()
        return response.status, dict(response.getheaders()), raw
    finally:
        connection.close()


def request_with_headers(port: int, method: str, path: str, headers: dict[str, str]):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request(method, path, headers=headers)
        response = connection.getresponse()
        response.read()
        return response.status, dict(response.getheaders())
    finally:
        connection.close()


class _DisconnectedWriter:
    def write(self, body: bytes) -> None:
        raise ConnectionAbortedError("client disconnected")


def _handler_with_disconnected_writer() -> FlatShotBridgeRequestHandler:
    handler = object.__new__(FlatShotBridgeRequestHandler)
    handler.server = SimpleNamespace(allowed_origins=set())
    handler.headers = {}
    handler.wfile = _DisconnectedWriter()
    handler.send_response = lambda status: None
    handler.send_header = lambda name, value: None
    handler.end_headers = lambda: None
    return handler


def test_bridge_http_send_json_ignores_client_disconnect():
    handler = _handler_with_disconnected_writer()

    handler._send_json({"ok": True})


def test_bridge_http_send_error_ignores_client_disconnect():
    handler = _handler_with_disconnected_writer()

    handler._send_error(RuntimeError("boom"))


def test_bridge_http_health(tmp_path):
    with running_bridge(tmp_path / "config") as port:
        status, data = request_json(port, "GET", "/health")

    assert status == 200
    assert data["ok"] is True
    assert data["service"] == "flatshot-bridge"


def test_bridge_http_capabilities(tmp_path):
    with running_bridge(tmp_path / "config") as port:
        status, data = request_json(port, "GET", "/capabilities")

    assert status == 200
    assert data["folderScan"] is True
    assert data["previewRender"] is True
    assert data["thumbnailRender"] is True
    assert data["exportRun"] is True
    assert data["exportProgress"] is True


def test_bridge_http_allows_localhost_frontend_origin_on_custom_port(tmp_path):
    with running_bridge(tmp_path / "config") as port:
        status, headers = request_with_headers(
            port,
            "GET",
            "/health",
            {"Origin": "http://127.0.0.1:4174"},
        )

    assert status == 200
    assert headers["Access-Control-Allow-Origin"] == "http://127.0.0.1:4174"


def test_bridge_http_presets_include_settings(tmp_path):
    with running_bridge(tmp_path / "config") as port:
        status, data = request_json(port, "GET", "/presets")

    assert status == 200
    assert data["source"] == "defaults"
    assert data["items"][0]["name"] == "Luz cenital"
    assert data["items"][0]["settings"]["opacity"] == 20
    assert data["items"][0]["settings"]["shadow_engine"] == "realistic_v2"


def test_bridge_http_scan_folder(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    png = _png(source / "item.png")

    with running_bridge(tmp_path / "config") as port:
        status, data = request_json(port, "POST", "/folders/scan", {"folders": [str(source)]})

    assert status == 200
    assert data["totalFiles"] == 1
    assert data["totalImages"] == 1
    assert data["totalOmitted"] == 0
    assert data["folders"][0]["images"][0]["path"] == png.as_posix()


def test_bridge_http_pick_folder(tmp_path):
    selected = tmp_path / "selected"
    selected.mkdir()
    service = FlatShotBridgeService(
        config_resolver=ConfigPathResolver(tmp_path / "config"),
        folder_picker=lambda initial_path: selected,
    )

    with running_bridge(tmp_path / "config", service=service) as port:
        status, data = request_json(port, "POST", "/folders/pick", {})

    assert status == 200
    assert data == {"ok": True, "selected": True, "path": selected.as_posix()}


def test_bridge_http_pick_folder_rejects_invalid_initial_path(tmp_path):
    service = FlatShotBridgeService(
        config_resolver=ConfigPathResolver(tmp_path / "config"),
        folder_picker=lambda initial_path: tmp_path,
    )

    with running_bridge(tmp_path / "config", service=service) as port:
        status, data = request_json(port, "POST", "/folders/pick", {"initialPath": 123})

    assert status == 400
    assert data["ok"] is False
    assert data["error"]["code"] == "invalid_request"


def test_bridge_http_render_preview(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    png = _png(source / "item.png")

    with running_bridge(tmp_path / "config") as port:
        status, data = request_json(
            port,
            "POST",
            "/preview/render",
            {
                "imagePath": str(png),
                "targetWidth": 32,
                "targetHeight": 32,
                "settings": {"opacity": 0, "blur": 0, "noise": 0},
            },
        )

    assert status == 200
    assert data["ok"] is True
    assert data["image"]["mimeType"] == "image/png"
    assert data["image"]["width"] == 32
    assert data["image"]["height"] == 32
    assert base64.b64decode(data["image"]["dataBase64"]).startswith(b"\x89PNG")


def test_bridge_http_render_thumbnail(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    png = _png(source / "item.png")

    with running_bridge(tmp_path / "config") as port:
        status, headers, body = request_raw(
            port,
            "GET",
            f"/images/thumbnail?path={quote(str(png), safe='')}&size=24",
        )

    assert status == 200
    assert headers["Content-Type"] == "image/png"
    assert body.startswith(b"\x89PNG")


def test_bridge_http_render_thumbnail_crops_transparent_subject(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    png = source / "offset.png"
    image = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
    for x in range(56, 72):
        for y in range(52, 72):
            image.putpixel((x, y), (255, 0, 0, 255))
    image.save(png)

    with running_bridge(tmp_path / "config") as port:
        status, headers, body = request_raw(
            port,
            "GET",
            f"/images/thumbnail?path={quote(str(png), safe='')}&size=40",
        )

    assert status == 200
    assert headers["Content-Type"] == "image/png"
    thumbnail = Image.open(BytesIO(body))
    assert thumbnail.size == (40, 40)
    bbox = thumbnail.getbbox()
    assert bbox is not None
    thumb_center = (thumbnail.size[0] / 2, thumbnail.size[1] / 2)
    bbox_center = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
    assert abs(thumb_center[0] - bbox_center[0]) <= 1
    assert abs(thumb_center[1] - bbox_center[1]) <= 1


def test_bridge_http_render_preview_rejects_unsupported_file(tmp_path):
    item = tmp_path / "item.txt"
    item.write_text("not an image", encoding="utf-8")

    with running_bridge(tmp_path / "config") as port:
        status, data = request_json(port, "POST", "/preview/render", {"imagePath": str(item)})

    assert status == 415
    assert data["ok"] is False
    assert data["error"]["code"] == "unsupported_preview_file"


def test_bridge_http_render_preview_rejects_empty_path(tmp_path):
    with running_bridge(tmp_path / "config") as port:
        status, data = request_json(port, "POST", "/preview/render", {"imagePath": ""})

    assert status == 400
    assert data["ok"] is False
    assert data["error"]["code"] == "invalid_request"


def test_bridge_http_render_preview_invalid_json_returns_json_error(tmp_path):
    with running_bridge(tmp_path / "config") as port:
        status, data = request_json(port, "POST", "/preview/render", "{")

    assert status == 400
    assert data == {
        "ok": False,
        "error": {
            "code": "invalid_json",
            "message": "Request body must be valid JSON.",
        },
    }


def test_bridge_http_export_prepare_and_run(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    png = _png(source / "item.png")
    service = FlatShotBridgeService(
        config_resolver=ConfigPathResolver(tmp_path / "config"),
        export_runner_factory=_export_runner_factory,
    )
    payload = {
        "imagePaths": [str(png)],
        "settings": {"opacity": 0, "blur": 0, "noise": 0},
        "export": {
            "format": "PNG",
            "size": "8x8",
            "destinationMode": "source",
            "destinationValue": "_OUT",
            "namingTemplate": "{original}{suffix}",
        },
    }

    with running_bridge(tmp_path / "config", service=service) as port:
        status, plan = request_json(port, "POST", "/exports/prepare", payload)
        run_status, started = request_json(port, "POST", "/exports/run", payload)
        final = started
        for _ in range(50):
            _, final = request_json(port, "GET", f"/exports/jobs/{started['jobId']}")
            if final["status"] in {"completed", "partial", "failed", "cancelled"}:
                break
            sleep(0.02)

    assert status == 200
    assert plan["sourceImages"] == 1
    assert run_status == 202
    assert final["status"] == "completed"
    assert final["progress"]["percent"] == 100
    assert final["issues"] == []
    assert (source / "_OUT" / "item_PRO.png").exists()


def test_bridge_http_export_collision_returns_json_error(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    output = tmp_path / "out"
    first.mkdir()
    second.mkdir()
    output.mkdir()
    first_png = _png(first / "same.png")
    second_png = _png(second / "same.png")
    service = FlatShotBridgeService(
        config_resolver=ConfigPathResolver(tmp_path / "config"),
        export_runner_factory=_export_runner_factory,
    )
    payload = {
        "imagePaths": [str(first_png), str(second_png)],
        "settings": {"opacity": 0, "blur": 0, "noise": 0},
        "export": {
            "format": "PNG",
            "size": "8x8",
            "destinationMode": "custom",
            "customOutputPath": str(output),
            "namingTemplate": "{original}{suffix}",
        },
    }

    with running_bridge(tmp_path / "config", service=service) as port:
        status, data = request_json(port, "POST", "/exports/run", payload)

    assert status == 409
    assert data["ok"] is False
    assert data["error"]["code"] == "export_output_collision"
    assert "archivos de salida repetidos" in data["error"]["message"]
    assert list(output.iterdir()) == []


def test_bridge_http_export_unknown_job_returns_json_error(tmp_path):
    with running_bridge(tmp_path / "config") as port:
        status, data = request_json(port, "GET", "/exports/jobs/missing")

    assert status == 404
    assert data["ok"] is False
    assert data["error"]["code"] == "job_not_found"


def test_bridge_http_unknown_route_returns_json_error(tmp_path):
    with running_bridge(tmp_path / "config") as port:
        status, data = request_json(port, "GET", "/missing")

    assert status == 404
    assert data == {
        "ok": False,
        "error": {
            "code": "not_found",
            "message": "Endpoint not found.",
        },
    }


def test_bridge_http_method_not_allowed_returns_json_error(tmp_path):
    with running_bridge(tmp_path / "config") as port:
        status, data = request_json(port, "GET", "/folders/scan")

    assert status == 405
    assert data["ok"] is False
    assert data["error"]["code"] == "method_not_allowed"


def test_bridge_http_invalid_json_returns_json_error(tmp_path):
    with running_bridge(tmp_path / "config") as port:
        status, data = request_json(port, "POST", "/folders/scan", "{")

    assert status == 400
    assert data == {
        "ok": False,
        "error": {
            "code": "invalid_json",
            "message": "Request body must be valid JSON.",
        },
    }
