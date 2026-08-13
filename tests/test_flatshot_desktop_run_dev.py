from __future__ import annotations

import importlib.util
import socket
from contextlib import closing
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUN_DEV_PATH = PROJECT_ROOT / "apps" / "flatshot-desktop" / "run_dev.py"

spec = importlib.util.spec_from_file_location("flatshot_desktop_run_dev", RUN_DEV_PATH)
assert spec is not None
run_dev = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(run_dev)


def _listening_socket() -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((run_dev.HOST, 0))
    sock.listen(1)
    return sock


def test_resolve_port_auto_skips_occupied_default():
    with closing(_listening_socket()) as sock:
        occupied_port = sock.getsockname()[1]

        selected_port = run_dev.resolve_port(None, occupied_port, "frontend")

    assert selected_port != occupied_port
    assert run_dev.is_port_available(selected_port)


def test_resolve_port_explicit_rejects_occupied_port():
    with closing(_listening_socket()) as sock:
        occupied_port = sock.getsockname()[1]

        with pytest.raises(SystemExit, match="Puerto ocupado: frontend"):
            run_dev.resolve_port(occupied_port, run_dev.DEFAULT_FRONTEND_PORT, "frontend")


def test_build_frontend_app_url_passes_non_default_bridge_url():
    frontend_url = "http://127.0.0.1:4174"
    bridge_url = "http://127.0.0.1:8766"

    app_url = run_dev.build_frontend_app_url(frontend_url, bridge_url)

    assert app_url == "http://127.0.0.1:4174?bridge=http%3A%2F%2F127.0.0.1%3A8766"


def test_build_frontend_app_url_includes_bridge_token():
    frontend_url = "http://127.0.0.1:4174"
    bridge_url = "http://127.0.0.1:8766"

    app_url = run_dev.build_frontend_app_url(frontend_url, bridge_url, bridge_token="secret")

    assert app_url == (
        "http://127.0.0.1:4174?"
        "bridge=http%3A%2F%2F127.0.0.1%3A8766#bridgeToken=secret"
    )


def test_build_frontend_app_url_keeps_default_bridge_url_clean():
    frontend_url = "http://127.0.0.1:4174"
    bridge_url = "http://127.0.0.1:8765"

    app_url = run_dev.build_frontend_app_url(frontend_url, bridge_url)

    assert app_url == frontend_url


def test_display_args_redacts_bridge_token():
    args = ["python", "run_bridge.py", "--auth-token", "session-secret", "--port", "8765"]

    displayed = run_dev.display_args(args)

    assert "session-secret" not in displayed
    assert "--auth-token [redacted]" in displayed


def test_launcher_passes_bridge_token_outside_process_arguments():
    source = RUN_DEV_PATH.read_text(encoding="utf-8")

    assert '"FLATSHOT_BRIDGE_AUTH_TOKEN"' in source
    assert '"--auth-token",\n                    bridge_token' not in source


def test_parse_args_supports_explicit_authenticated_url_output():
    args = run_dev.parse_args(["--print-auth-url"])

    assert args.print_auth_url is True
