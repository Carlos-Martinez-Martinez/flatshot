"""Minimal local HTTP server for the FlatShot bridge."""
from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from flatshot.bridge.errors import (
    BridgeError,
    MethodNotAllowedError,
    NotFoundError,
    error_response,
)
from flatshot.bridge.service import FlatShotBridgeService

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
DEFAULT_ALLOWED_ORIGINS = {
    "http://127.0.0.1:4173",
    "http://localhost:4173",
}
CLIENT_DISCONNECT_ERRORS = (BrokenPipeError, ConnectionAbortedError, ConnectionResetError)


class FlatShotBridgeHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        server_address,
        handler_class,
        *,
        service: FlatShotBridgeService | None = None,
        allowed_origins: set[str] | None = None,
    ) -> None:
        super().__init__(server_address, handler_class)
        self.service = service or FlatShotBridgeService()
        self.allowed_origins = allowed_origins or set(DEFAULT_ALLOWED_ORIGINS)


class FlatShotBridgeRequestHandler(BaseHTTPRequestHandler):
    server: FlatShotBridgeHTTPServer

    def do_OPTIONS(self) -> None:
        self._send_json({}, status=204)

    def do_GET(self) -> None:
        try:
            path = urlparse(self.path).path
            if path == "/health":
                self._send_json(self.server.service.health())
            elif path == "/app-info":
                self._send_json(self.server.service.app_info())
            elif path == "/capabilities":
                self._send_json(self.server.service.capabilities())
            elif path == "/presets":
                self._send_json(self.server.service.list_presets())
            elif path == "/folders/scan":
                raise MethodNotAllowedError("Use POST for /folders/scan.")
            elif path == "/folders/pick":
                raise MethodNotAllowedError("Use POST for /folders/pick.")
            elif path == "/preview/render":
                raise MethodNotAllowedError("Use POST for /preview/render.")
            else:
                raise NotFoundError()
        except CLIENT_DISCONNECT_ERRORS:
            return
        except Exception as exc:
            self._send_error(exc)

    def do_POST(self) -> None:
        try:
            path = urlparse(self.path).path
            if path == "/folders/scan":
                self._send_json(self.server.service.scan_folders(self._read_json_body()))
            elif path == "/folders/pick":
                self._send_json(self.server.service.pick_folder(self._read_json_body()))
            elif path == "/preview/render":
                self._send_json(self.server.service.render_preview(self._read_json_body()))
            else:
                if path in {"/health", "/app-info", "/capabilities", "/presets"}:
                    raise MethodNotAllowedError("Use GET for this endpoint.")
                raise NotFoundError()
        except CLIENT_DISCONNECT_ERRORS:
            return
        except Exception as exc:
            self._send_error(exc)

    def do_PUT(self) -> None:
        self._send_error(MethodNotAllowedError())

    def do_PATCH(self) -> None:
        self._send_error(MethodNotAllowedError())

    def do_DELETE(self) -> None:
        self._send_error(MethodNotAllowedError())

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        return

    def _read_json_body(self) -> dict[str, Any]:
        content_type = self.headers.get("Content-Type", "")
        if content_type and "application/json" not in content_type:
            raise BridgeError("unsupported_media_type", "Content-Type must be application/json.", status=415)

        raw_length = self.headers.get("Content-Length", "0")
        try:
            length = int(raw_length)
        except ValueError as exc:
            raise BridgeError("invalid_request", "Invalid Content-Length.", status=400) from exc

        raw_body = self.rfile.read(length) if length else b"{}"
        try:
            parsed = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise BridgeError("invalid_json", "Request body must be valid JSON.", status=400) from exc
        if not isinstance(parsed, dict):
            raise BridgeError("invalid_request", "Request body must be a JSON object.", status=400)
        return parsed

    def _send_error(self, exc: Exception) -> None:
        if isinstance(exc, CLIENT_DISCONNECT_ERRORS):
            return
        status = exc.status if isinstance(exc, BridgeError) else 500
        self._send_json(error_response(exc), status=status)

    def _send_json(self, payload: dict[str, Any], *, status: int = 200) -> None:
        body = b"" if status == 204 else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self._send_cors_headers()
            if status != 204:
                self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if body:
                self.wfile.write(body)
        except CLIENT_DISCONNECT_ERRORS:
            return

    def _send_cors_headers(self) -> None:
        origin = self.headers.get("Origin")
        if origin and origin in self.server.allowed_origins:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")


def create_server(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    *,
    service: FlatShotBridgeService | None = None,
    allowed_origins: set[str] | None = None,
) -> FlatShotBridgeHTTPServer:
    return FlatShotBridgeHTTPServer(
        (host, port),
        FlatShotBridgeRequestHandler,
        service=service,
        allowed_origins=allowed_origins,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="flatshot-bridge", description="FlatShot local development bridge")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args(argv)

    if args.host not in {"127.0.0.1", "localhost"}:
        parser.error("APP.3 bridge must bind to 127.0.0.1 or localhost.")

    server = create_server(args.host, args.port)
    print(f"FlatShot bridge listening on http://{args.host}:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
