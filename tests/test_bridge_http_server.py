from __future__ import annotations

import http.client
import json
import base64
import logging
import os
import threading
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
from time import sleep
from types import SimpleNamespace
from urllib.parse import quote

import pytest
from PIL import Image

from flatshot.application.config_paths import ConfigPathResolver
from flatshot.application.contracts import BatchScanResult
from flatshot.application.export_runner import ExportRunner
from flatshot.bridge.http_server import (
    MAX_JSON_BODY_BYTES,
    FlatShotBridgeRequestHandler,
    create_server,
)
from flatshot.bridge.service import FlatShotBridgeService
from tests.helpers import InlineExecutor


def _png(path: Path) -> Path:
    Image.new("RGBA", (4, 4), (255, 0, 0, 255)).save(path)
    return path


def _export_runner_factory(**kwargs) -> ExportRunner:
    return ExportRunner(**kwargs, executor_factory=InlineExecutor)


@contextmanager
def running_bridge(
    config_dir: Path,
    service: FlatShotBridgeService | None = None,
    allowed_origins: set[str] | None = None,
    auth_token: str | None = None,
):
    service = service or FlatShotBridgeService(config_resolver=ConfigPathResolver(config_dir))
    server = create_server("127.0.0.1", 0, service=service, allowed_origins=allowed_origins, auth_token=auth_token)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_port
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def request_json(port: int, method: str, path: str, body: dict | str | None = None, headers: dict[str, str] | None = None):
    request_headers = dict(headers or {})
    payload = None
    if isinstance(body, dict):
        payload = json.dumps(body).encode("utf-8")
        request_headers["Content-Type"] = "application/json"
    elif isinstance(body, str):
        payload = body.encode("utf-8")
        request_headers["Content-Type"] = "application/json"

    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request(method, path, body=payload, headers=request_headers)
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
    handler.command = "GET"
    handler.path = "/test"
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


def test_bridge_http_logs_unexpected_errors(caplog):
    handler = _handler_with_disconnected_writer()
    caplog.set_level(logging.ERROR, logger="flatshot.bridge.http_server")

    handler._send_error(RuntimeError("boom"))

    assert any(
        "Unhandled bridge error for GET /test" in record.message and record.exc_info
        for record in caplog.records
    )


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


def test_bridge_http_auth_token_protects_sensitive_endpoints(tmp_path):
    source = tmp_path / "source"
    source.mkdir()

    with running_bridge(tmp_path / "config", auth_token="secret") as port:
        health_status, health = request_json(port, "GET", "/health")
        rejected_status, rejected = request_json(port, "POST", "/folders/scan", {"folders": [str(source)]})
        allowed_status, allowed = request_json(
            port,
            "POST",
            "/folders/scan",
            {"folders": [str(source)]},
            headers={"X-FlatShot-Token": "secret"},
        )

    assert health_status == 200
    assert health["ok"] is True
    assert rejected_status == 401
    assert rejected["error"]["code"] == "unauthorized"
    assert allowed_status == 200
    assert allowed["totalFolders"] == 1


def test_bridge_http_allows_configured_localhost_frontend_origin_on_custom_port(tmp_path):
    origin = "http://127.0.0.1:4174"
    with running_bridge(tmp_path / "config", allowed_origins={origin}) as port:
        status, headers = request_with_headers(
            port,
            "GET",
            "/health",
            {"Origin": origin},
        )

    assert status == 200
    assert headers["Access-Control-Allow-Origin"] == origin


@pytest.mark.parametrize(
    "origin",
    [
        "http://localhost:4173\r\nX-Injected: yes",
        "http://localhost:4173/path",
        "http://user@localhost:4173",
        "javascript:alert(1)",
    ],
)
def test_bridge_http_rejects_invalid_allowed_origin_configuration(tmp_path, origin):
    service = FlatShotBridgeService(config_resolver=ConfigPathResolver(tmp_path / "config"))

    with pytest.raises(ValueError, match="allowed origin"):
        create_server("127.0.0.1", 0, service=service, allowed_origins={origin})


def test_bridge_http_export_preflight_allows_idempotency_key(tmp_path):
    origin = "http://127.0.0.1:4174"
    with running_bridge(tmp_path / "config", allowed_origins={origin}) as port:
        status, headers = request_with_headers(
            port,
            "OPTIONS",
            "/exports/run",
            {
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,idempotency-key",
            },
        )

    assert status == 204
    allowed_headers = {
        header.strip().lower()
        for header in headers["Access-Control-Allow-Headers"].split(",")
    }
    assert "idempotency-key" in allowed_headers


def test_bridge_http_rejects_unconfigured_localhost_frontend_origin(tmp_path):
    with running_bridge(tmp_path / "config") as port:
        status, headers = request_with_headers(
            port,
            "GET",
            "/health",
            {"Origin": "http://127.0.0.1:4174"},
        )

    assert status == 403
    assert "Access-Control-Allow-Origin" not in headers


def test_bridge_http_rejects_state_change_without_json_content_type(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    payload = json.dumps({"folders": [str(source)]}).encode("utf-8")

    with running_bridge(tmp_path / "config") as port:
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        try:
            connection.request("POST", "/folders/scan", body=payload)
            response = connection.getresponse()
            data = json.loads(response.read().decode("utf-8"))
        finally:
            connection.close()

    assert response.status == 415
    assert data["error"]["code"] == "unsupported_media_type"


def test_bridge_http_server_bounds_connections_and_sets_socket_timeout(tmp_path):
    service = FlatShotBridgeService(config_resolver=ConfigPathResolver(tmp_path / "config"))
    server = create_server("127.0.0.1", 0, service=service)
    try:
        assert server.max_active_connections == 16
        assert server.request_timeout_seconds == 10.0
        assert server._connection_slots._value == 16
    finally:
        server.server_close()


def test_bridge_http_presets_include_settings(tmp_path):
    with running_bridge(tmp_path / "config") as port:
        status, data = request_json(port, "GET", "/presets")

    assert status == 200
    assert data["source"] == "defaults"
    assert data["items"][0]["name"] == "Luz cenital"
    assert data["items"][0]["settings"]["opacity"] == 20
    assert data["items"][0]["settings"]["shadow_engine"] == "realistic_v2"


def test_bridge_http_ui_preferences_round_trip(tmp_path):
    preferences = {
        "outputProfiles": [{"id": "png_transparent", "name": "PNG transparente", "enabled": True}],
        "activeOutputProfile": "png_transparent",
        "activeOutputFormats": ["png_transparent"],
    }

    with running_bridge(tmp_path / "config") as port:
        save_status, saved = request_json(port, "POST", "/ui/preferences", preferences)
        load_status, loaded = request_json(port, "GET", "/ui/preferences")

    assert save_status == 200
    assert saved["ok"] is True
    assert load_status == 200
    assert loaded["source"] == "config"
    assert loaded["preferences"] == preferences


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


def test_bridge_http_open_onboarding_assets_folder(tmp_path):
    opened: list[Path] = []
    service = FlatShotBridgeService(
        config_resolver=ConfigPathResolver(tmp_path / "config"),
        folder_opener=lambda path: opened.append(path),
    )

    with running_bridge(tmp_path / "config", service=service) as port:
        status, data = request_json(port, "POST", "/assets/onboarding/open", {})
        get_status, get_data = request_json(port, "GET", "/assets/onboarding/open")

    assets_dir = Path(data["path"])
    assert status == 200
    assert data["ok"] is True
    assert assets_dir.name == "onboarding"
    assert opened == [assets_dir]
    assert get_status == 405
    assert get_data["error"]["code"] == "method_not_allowed"


def test_bridge_http_open_folder_uses_service_folder_opener(tmp_path):
    source = tmp_path / "source"
    output = source / "Salida"
    output.mkdir(parents=True)
    opened: list[Path] = []
    service = FlatShotBridgeService(
        config_resolver=ConfigPathResolver(tmp_path / "config"),
        folder_opener=lambda path: opened.append(path),
    )
    service.path_policy.register_root(source)

    with running_bridge(tmp_path / "config", service=service) as port:
        status, data = request_json(port, "POST", "/folders/open", {"path": str(output)})
        get_status, get_data = request_json(port, "GET", "/folders/open")

    assert status == 200
    assert data == {"ok": True, "path": output.as_posix()}
    assert opened == [output]


def test_bridge_http_reveal_path_uses_service_path_revealer(tmp_path):
    source = tmp_path / "source"
    output = source / "Salida"
    output.mkdir(parents=True)
    exported = output / "item_PRO.png"
    exported.write_bytes(b"export")
    revealed = []
    service = FlatShotBridgeService(
        config_resolver=ConfigPathResolver(tmp_path / "config"),
        path_revealer=lambda path: revealed.append(path),
    )
    service.path_policy.register_root(source)

    with running_bridge(tmp_path / "config", service=service) as port:
        status, data = request_json(port, "POST", "/files/reveal", {"path": str(exported)})
        get_status, get_data = request_json(port, "GET", "/files/reveal")

    assert status == 200
    assert data == {"ok": True, "path": exported.as_posix()}
    assert revealed == [exported]
    assert get_status == 405
    assert get_data["error"]["code"] == "method_not_allowed"


def test_bridge_http_render_preview(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    png = _png(source / "item.png")

    with running_bridge(tmp_path / "config") as port:
        scan_status, _ = request_json(port, "POST", "/folders/scan", {"folders": [str(source)]})
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

    assert scan_status == 200
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
        scan_status, _ = request_json(port, "POST", "/folders/scan", {"folders": [str(source)]})
        status, headers, body = request_raw(
            port,
            "GET",
            f"/images/thumbnail?path={quote(str(png), safe='')}&size=24",
        )

    assert scan_status == 200
    assert status == 200
    assert headers["Content-Type"] == "image/png"
    assert body.startswith(b"\x89PNG")


def test_bridge_http_render_thumbnail_accepts_image_id(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    _png(source / "item.png")

    with running_bridge(tmp_path / "config") as port:
        scan_status, scan = request_json(port, "POST", "/folders/scan", {"folders": [str(source)]})
        image_id = scan["folders"][0]["images"][0]["imageId"]
        status, headers, body = request_raw(
            port,
            "GET",
            f"/images/thumbnail?imageId={quote(image_id, safe='')}&size=24",
        )

    assert scan_status == 200
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
        scan_status, _ = request_json(port, "POST", "/folders/scan", {"folders": [str(source)]})
        status, headers, body = request_raw(
            port,
            "GET",
            f"/images/thumbnail?path={quote(str(png), safe='')}&size=40",
        )

    assert scan_status == 200
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
        scan_status, _ = request_json(port, "POST", "/folders/scan", {"folders": [str(source)]})
        status, plan = request_json(port, "POST", "/exports/prepare", payload)
        run_status, started = request_json(port, "POST", "/exports/run", payload)
        final = started
        for _ in range(50):
            _, final = request_json(port, "GET", f"/exports/jobs/{started['jobId']}")
            if final["status"] in {"completed", "partial", "failed", "cancelled"}:
                break
            sleep(0.02)

    assert scan_status == 200
    assert status == 200
    assert plan["sourceImages"] == 1
    assert run_status == 202
    assert final["status"] == "completed"
    assert final["progress"]["percent"] == 100
    assert final["issues"] == []
    assert (source / "_OUT" / "item_PRO.png").exists()


def test_bridge_http_scan_job_runs_and_returns_result(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    _png(source / "item.png")

    with running_bridge(tmp_path / "config") as port:
        start_status, started = request_json(
            port,
            "POST",
            "/folders/scan/jobs",
            {"folders": [str(source)], "scanMode": "verified"},
        )
        final = started
        for _ in range(50):
            _, final = request_json(port, "GET", f"/folders/scan/jobs/{started['jobId']}")
            if final["status"] in {"completed", "cancelled", "failed"}:
                break
            sleep(0.02)

    assert start_status == 202
    assert started["jobId"]
    assert final["status"] == "completed"
    assert final["progress"]["percent"] == 100
    assert final["result"]["totalImages"] == 1
    assert final["result"]["folders"][0]["images"][0]["name"] == "item.png"


def test_bridge_http_scan_job_status_paginates_result_images(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    for index in range(3):
        _png(source / f"item-{index}.png")

    with running_bridge(tmp_path / "config") as port:
        start_status, started = request_json(
            port,
            "POST",
            "/folders/scan/jobs",
            {"folders": [str(source)], "scanMode": "verified"},
        )
        final = started
        for _ in range(50):
            _, final = request_json(port, "GET", f"/folders/scan/jobs/{started['jobId']}")
            if final["status"] in {"completed", "cancelled", "failed"}:
                break
            sleep(0.02)
        paged_status, paged = request_json(
            port,
            "GET",
            f"/folders/scan/jobs/{started['jobId']}?imageOffset=1&imageLimit=1",
        )

    assert start_status == 202
    assert final["status"] == "completed"
    assert paged_status == 200
    assert paged["result"]["page"] == {
        "imageOffset": 1,
        "imageLimit": 1,
        "imageCount": 1,
        "totalImages": 3,
        "hasMore": True,
    }
    assert [image["name"] for image in paged["result"]["folders"][0]["images"]] == ["item-1.png"]


def test_bridge_http_scan_job_can_be_cancelled(tmp_path):
    class SlowScanner:
        def __init__(self):
            self.started = threading.Event()

        def scan_folders(self, folders, image_overrides=None, progress_callback=None, cancellation_token=None, **kwargs):
            self.started.set()
            for index in range(20):
                if cancellation_token is not None and cancellation_token.cancelled:
                    break
                if progress_callback is not None:
                    progress_callback(index + 1, 20)
                sleep(0.02)
            return BatchScanResult(total_folders=1)

    scanner = SlowScanner()
    source = tmp_path / "source"
    source.mkdir()
    service = FlatShotBridgeService(
        config_resolver=ConfigPathResolver(tmp_path / "config"),
        folder_scanner=scanner,
    )

    with running_bridge(tmp_path / "config", service=service) as port:
        start_status, started = request_json(port, "POST", "/folders/scan/jobs", {"folders": [str(source)]})
        assert scanner.started.wait(timeout=2)
        cancel_status, cancelled = request_json(port, "POST", f"/folders/scan/jobs/{started['jobId']}/cancel", {})
        final = cancelled
        for _ in range(50):
            _, final = request_json(port, "GET", f"/folders/scan/jobs/{started['jobId']}")
            if final["status"] == "cancelled":
                break
            sleep(0.02)

    assert start_status == 202
    assert cancel_status == 200
    assert final["status"] == "cancelled"
    assert final["progress"]["processed"] < 20


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
        scan_status, _ = request_json(
            port,
            "POST",
            "/folders/scan",
            {"folders": [str(first), str(second), str(output)]},
        )
        status, data = request_json(port, "POST", "/exports/run", payload)

    assert scan_status == 200
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


def test_bridge_http_rejects_oversized_json_body(tmp_path):
    payload = {"payload": "x" * (MAX_JSON_BODY_BYTES + 1)}

    with running_bridge(tmp_path / "config") as port:
        status, data = request_json(port, "POST", "/folders/scan", payload)

    assert status == 413
    assert data["ok"] is False
    assert data["error"]["code"] == "payload_too_large"


def test_bridge_http_thumbnail_rejects_path_traversal(tmp_path):
    """Thumbnail endpoint must not leak file existence via 404 vs 415 for arbitrary paths."""
    traversed = "C:/Windows/System32/drivers/etc/hosts" if os.name == "nt" else "/etc/passwd"
    encoded = quote(traversed, safe="")
    with running_bridge(tmp_path / "config") as port:
        status, data = request_json(port, "GET", f"/images/thumbnail?path={encoded}&size=128")
    assert data.get("ok") is False


def test_bridge_http_thumbnail_handles_relative_path(tmp_path):
    """Relative paths should be rejected safely."""
    with running_bridge(tmp_path / "config") as port:
        status, data = request_json(port, "GET", "/images/thumbnail?path=../secret.png&size=128")
    assert data.get("ok") is False


def test_bridge_http_thumbnail_handles_missing_param(tmp_path):
    """Missing path parameter should return error, not crash."""
    with running_bridge(tmp_path / "config") as port:
        status, data = request_json(port, "GET", "/images/thumbnail?size=128")
    assert data.get("ok") is False
