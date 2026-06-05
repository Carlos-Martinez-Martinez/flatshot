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


def test_build_frontend_app_url_keeps_default_bridge_url_clean():
    frontend_url = "http://127.0.0.1:4174"
    bridge_url = "http://127.0.0.1:8765"

    app_url = run_dev.build_frontend_app_url(frontend_url, bridge_url)

    assert app_url == frontend_url
