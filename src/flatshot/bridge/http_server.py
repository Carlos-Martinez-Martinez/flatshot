"""Minimal local HTTP server for the FlatShot bridge."""
from __future__ import annotations

import argparse
import os
import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

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
MAX_JSON_BODY_BYTES = 1_000_000
DEFAULT_MAX_ACTIVE_CONNECTIONS = 16
DEFAULT_REQUEST_TIMEOUT_SECONDS = 10.0
_logger = logging.getLogger(__name__)


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
        auth_token: str | None = None,
        max_active_connections: int = DEFAULT_MAX_ACTIVE_CONNECTIONS,
        request_timeout_seconds: float = DEFAULT_REQUEST_TIMEOUT_SECONDS,
    ) -> None:
        super().__init__(server_address, handler_class)
        self.service = service or FlatShotBridgeService()
        self.allowed_origins = allowed_origins or set(DEFAULT_ALLOWED_ORIGINS)
        self.auth_token = str(auth_token or "").strip()
        self.max_active_connections = max(1, int(max_active_connections))
        self.request_timeout_seconds = max(0.1, float(request_timeout_seconds))
        self._connection_slots = threading.BoundedSemaphore(self.max_active_connections)

    def get_request(self):
        request, client_address = super().get_request()
        request.settimeout(self.request_timeout_seconds)
        return request, client_address

    def process_request(self, request, client_address) -> None:
        if not self._connection_slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self._connection_slots.release()
            raise

    def process_request_thread(self, request, client_address) -> None:
        try:
            super().process_request_thread(request, client_address)
        finally:
            self._connection_slots.release()


class FlatShotBridgeRequestHandler(BaseHTTPRequestHandler):
    server: FlatShotBridgeHTTPServer

    def do_OPTIONS(self) -> None:
        try:
            self._require_origin()
            self._send_json({}, status=204)
        except Exception as exc:
            self._send_error(exc)

    def do_GET(self) -> None:
        try:
            parsed = urlparse(self.path)
            path = parsed.path
            self._require_origin()
            self._require_auth(path, query=parse_qs(parsed.query))
            if path == "/health":
                self._send_json(self.server.service.health())
            elif path == "/app-info":
                self._send_json(self.server.service.app_info())
            elif path == "/capabilities":
                self._send_json(self.server.service.capabilities())
            elif path == "/presets":
                self._send_json(self.server.service.list_presets())
            elif path == "/ui/preferences":
                self._send_json(self.server.service.load_ui_preferences())
            elif path == "/assets/onboarding/open":
                raise MethodNotAllowedError("Use POST for /assets/onboarding/open.")
            elif path == "/folders/open":
                raise MethodNotAllowedError("Use POST for /folders/open.")
            elif path == "/files/reveal":
                raise MethodNotAllowedError("Use POST for /files/reveal.")
            elif path == "/images/thumbnail":
                query = parse_qs(parsed.query)
                image_id = _single_query_value(query, "imageId", required=False)
                mime_type, body = self.server.service.render_thumbnail(
                    {
                        "imageId": image_id,
                        "imagePath": _single_query_value(query, "path", required=image_id is None),
                        "size": _single_query_value(query, "size", required=False),
                    }
                )
                self._send_binary(body, content_type=mime_type)
            elif _is_export_job_status_path(path):
                self._send_json(self.server.service.export_status(_export_job_id(path)))
            elif _is_scan_job_status_path(path):
                query = parse_qs(parsed.query)
                self._send_json(
                    self.server.service.scan_job_status(
                        _scan_job_id(path),
                        image_offset=_integer_query_value(query, "imageOffset", default=0, required=False),
                        image_limit=_integer_query_value(query, "imageLimit", required=False),
                    )
                )
            elif path == "/folders/scan":
                raise MethodNotAllowedError("Use POST for /folders/scan.")
            elif path == "/folders/scan/jobs":
                raise MethodNotAllowedError("Use POST for /folders/scan/jobs.")
            elif path == "/folders/pick":
                raise MethodNotAllowedError("Use POST for /folders/pick.")
            elif path == "/preview/render":
                raise MethodNotAllowedError("Use POST for /preview/render.")
            elif path == "/preview/render-image":
                raise MethodNotAllowedError("Use POST for /preview/render-image.")
            elif path.startswith("/exports/"):
                raise MethodNotAllowedError("Use POST for this export endpoint.")
            else:
                raise NotFoundError()
        except CLIENT_DISCONNECT_ERRORS:
            return
        except Exception as exc:
            self._send_error(exc)

    def do_POST(self) -> None:
        try:
            path = urlparse(self.path).path
            self._require_origin()
            self._require_auth(path)
            if path == "/folders/scan":
                self._send_json(self.server.service.scan_folders(self._read_json_body()))
            elif path == "/folders/scan/jobs":
                self._send_json(self.server.service.start_scan_job(self._read_json_body()), status=202)
            elif _is_scan_job_action_path(path, "cancel"):
                self._send_json(self.server.service.cancel_scan_job(_scan_job_id(path)))
            elif path == "/folders/pick":
                self._send_json(self.server.service.pick_folder(self._read_json_body()))
            elif path == "/folders/open":
                self._send_json(self.server.service.open_folder(self._read_json_body()))
            elif path == "/files/reveal":
                self._send_json(self.server.service.reveal_path(self._read_json_body()))
            elif path == "/preview/render-image":
                mime_type, body, width, height, warning = self.server.service.render_preview_binary(self._read_json_body())
                self._send_binary(body, content_type=mime_type, width=width, height=height, warning=warning)
            elif path == "/preview/render":
                self._send_json(self.server.service.render_preview(self._read_json_body()))
            elif path == "/presets/save":
                self._send_json(self.server.service.save_preset(self._read_json_body()))
            elif path == "/presets/delete":
                self._send_json(self.server.service.delete_preset(self._read_json_body()))
            elif path == "/ui/preferences":
                self._send_json(self.server.service.save_ui_preferences(self._read_json_body()))
            elif path == "/assets/onboarding/open":
                self._send_json(self.server.service.open_onboarding_assets_folder())
            elif path == "/exports/prepare":
                self._send_json(self.server.service.prepare_export(self._read_json_body()))
            elif path == "/exports/run":
                self._send_json(
                    self.server.service.start_export(
                        self._read_json_body(),
                        idempotency_key=self.headers.get("Idempotency-Key"),
                    ),
                    status=202,
                )
            elif _is_export_job_action_path(path, "pause"):
                self._send_json(self.server.service.pause_export(_export_job_id(path)))
            elif _is_export_job_action_path(path, "resume"):
                self._send_json(self.server.service.resume_export(_export_job_id(path)))
            elif _is_export_job_action_path(path, "cancel"):
                self._send_json(self.server.service.cancel_export(_export_job_id(path)))
            else:
                if path in {"/health", "/app-info", "/capabilities", "/presets", "/ui/preferences"}:
                    raise MethodNotAllowedError("Use GET for this endpoint.")
                if _is_export_job_status_path(path) or _is_scan_job_status_path(path):
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
        raw_length = self.headers.get("Content-Length", "0")
        try:
            length = int(raw_length)
        except ValueError as exc:
            raise BridgeError("invalid_request", "Invalid Content-Length.", status=400) from exc
        if length < 0:
            raise BridgeError("invalid_request", "Invalid Content-Length.", status=400)
        content_type = self.headers.get("Content-Type", "")
        if length and "application/json" not in content_type.lower():
            raise BridgeError("unsupported_media_type", "Content-Type must be application/json.", status=415)
        if length > MAX_JSON_BODY_BYTES:
            self.rfile.read(min(length, MAX_JSON_BODY_BYTES + 1))
            raise BridgeError("payload_too_large", "Request body is too large.", status=413)

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
        if not isinstance(exc, BridgeError):
            _logger.error(
                "Unhandled bridge error for %s %s",
                getattr(self, "command", "?"),
                getattr(self, "path", "?"),
                exc_info=(type(exc), exc, exc.__traceback__),
            )
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

    def _send_binary(self, body: bytes, *, content_type: str, status: int = 200, width: int | None = None, height: int | None = None, warning: str | None = None) -> None:
        try:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-store")
            self._send_cors_headers()
            if width is not None:
                self.send_header("X-FlatShot-Width", str(width))
            if height is not None:
                self.send_header("X-FlatShot-Height", str(height))
            if warning:
                self.send_header("X-FlatShot-Warning", warning)
            expose_headers = []
            if width is not None or height is not None:
                expose_headers.append("X-FlatShot-Width")
                expose_headers.append("X-FlatShot-Height")
            if warning:
                expose_headers.append("X-FlatShot-Warning")
            if expose_headers:
                self.send_header("Access-Control-Expose-Headers", ", ".join(expose_headers))
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except CLIENT_DISCONNECT_ERRORS:
            return

    def _send_cors_headers(self) -> None:
        origin = self.headers.get("Origin")
        if origin and origin in self.server.allowed_origins:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-FlatShot-Token, Idempotency-Key")

    def _require_auth(self, path: str, *, query: dict[str, list[str]] | None = None) -> None:
        token = self.server.auth_token
        if not token or path in {"/health", "/app-info", "/capabilities"}:
            return
        supplied = self.headers.get("X-FlatShot-Token", "")
        if not supplied and query is not None:
            supplied = _single_query_value(query, "token", required=False) or ""
        if supplied != token:
            raise BridgeError("unauthorized", "Token local de FlatShot no válido.", status=401)

    def _require_origin(self) -> None:
        origin = self.headers.get("Origin")
        if origin and origin not in self.server.allowed_origins:
            raise BridgeError("origin_not_allowed", "Request origin is not allowed.", status=403)


def create_server(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    *,
    service: FlatShotBridgeService | None = None,
    allowed_origins: set[str] | None = None,
    auth_token: str | None = None,
    max_active_connections: int = DEFAULT_MAX_ACTIVE_CONNECTIONS,
    request_timeout_seconds: float = DEFAULT_REQUEST_TIMEOUT_SECONDS,
) -> FlatShotBridgeHTTPServer:
    return FlatShotBridgeHTTPServer(
        (host, port),
        FlatShotBridgeRequestHandler,
        service=service,
        allowed_origins=allowed_origins,
        auth_token=auth_token,
        max_active_connections=max_active_connections,
        request_timeout_seconds=request_timeout_seconds,
    )


def _path_parts(path: str) -> list[str]:
    return [part for part in path.strip("/").split("/") if part]


def _single_query_value(query: dict[str, list[str]], name: str, *, required: bool = True) -> str | None:
    values = query.get(name) or []
    value = values[0] if values else None
    if required and (value is None or not value.strip()):
        raise BridgeError("invalid_request", f"Query parameter '{name}' is required.", status=400)
    return value


def _integer_query_value(
    query: dict[str, list[str]],
    name: str,
    *,
    default: int | None = None,
    required: bool = True,
) -> int | None:
    value = _single_query_value(query, name, required=required)
    if value in (None, ""):
        return default
    try:
        parsed = int(value)
    except ValueError as exc:
        raise BridgeError("invalid_request", f"Query '{name}' must be an integer.", status=400) from exc
    if parsed < 0:
        raise BridgeError("invalid_request", f"Query '{name}' must be zero or greater.", status=400)
    return parsed


def _is_export_job_status_path(path: str) -> bool:
    parts = _path_parts(path)
    return len(parts) == 3 and parts[:2] == ["exports", "jobs"]


def _is_scan_job_status_path(path: str) -> bool:
    parts = _path_parts(path)
    return len(parts) == 4 and parts[:3] == ["folders", "scan", "jobs"]


def _is_export_job_action_path(path: str, action: str) -> bool:
    parts = _path_parts(path)
    return len(parts) == 4 and parts[:2] == ["exports", "jobs"] and parts[3] == action


def _is_scan_job_action_path(path: str, action: str) -> bool:
    parts = _path_parts(path)
    return len(parts) == 5 and parts[:3] == ["folders", "scan", "jobs"] and parts[4] == action


def _export_job_id(path: str) -> str:
    return _path_parts(path)[2]


def _scan_job_id(path: str) -> str:
    return _path_parts(path)[3]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="flatshot-bridge", description="FlatShot local development bridge")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--allowed-origin",
        action="append",
        default=[],
        help="Frontend origin allowed to call the local bridge. Can be passed multiple times.",
    )
    parser.add_argument(
        "--auth-token",
        default=os.environ.get("FLATSHOT_BRIDGE_AUTH_TOKEN", ""),
        help="Optional local token required for sensitive endpoints.",
    )
    args = parser.parse_args(argv)

    if args.host not in {"127.0.0.1", "localhost"}:
        parser.error("APP.3 bridge must bind to 127.0.0.1 or localhost.")

    allowed_origins = set(DEFAULT_ALLOWED_ORIGINS)
    allowed_origins.update(origin.strip() for origin in args.allowed_origin if origin and origin.strip())
    server = create_server(args.host, args.port, allowed_origins=allowed_origins, auth_token=args.auth_token)
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
