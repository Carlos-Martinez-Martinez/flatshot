from __future__ import annotations

import http.client
import json
import base64
import threading
from contextlib import contextmanager
from pathlib import Path

from PIL import Image

from flatshot.application.config_paths import ConfigPathResolver
from flatshot.bridge.http_server import create_server
from flatshot.bridge.service import FlatShotBridgeService


def _png(path: Path) -> Path:
    Image.new("RGBA", (4, 4), (255, 0, 0, 255)).save(path)
    return path


@contextmanager
def running_bridge(config_dir: Path):
    service = FlatShotBridgeService(config_resolver=ConfigPathResolver(config_dir))
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
    assert data["exportRun"] is False


def test_bridge_http_scan_folder(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    png = _png(source / "item.png")

    with running_bridge(tmp_path / "config") as port:
        status, data = request_json(port, "POST", "/folders/scan", {"folders": [str(source)]})

    assert status == 200
    assert data["totalImages"] == 1
    assert data["folders"][0]["images"][0]["path"] == png.as_posix()


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
