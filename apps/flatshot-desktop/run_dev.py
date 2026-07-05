"""Run the FlatShot modern desktop prototype for local visual review."""
from __future__ import annotations

import argparse
import secrets
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from urllib.parse import urlencode


HOST = "127.0.0.1"
DEFAULT_BRIDGE_PORT = 8765
DEFAULT_FRONTEND_PORT = 4173

APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parents[1]
FRONTEND_DIR = APP_DIR / "frontend"
BRIDGE_RUNNER = APP_DIR / "bridge" / "run_bridge.py"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="flatshot-desktop-dev",
        description="Arranca el bridge local y el frontend estatico de la nueva app FlatShot.",
    )
    parser.add_argument("--open", action="store_true", help="Abre el navegador en el frontend.")
    parser.add_argument("--no-bridge", action="store_true", help="Arranca solo el frontend estatico.")
    parser.add_argument(
        "--bridge-port",
        type=int,
        default=None,
        help=f"Puerto exacto para el bridge. Si se omite, se busca desde {DEFAULT_BRIDGE_PORT}.",
    )
    parser.add_argument(
        "--frontend-port",
        type=int,
        default=None,
        help=f"Puerto exacto para el frontend. Si se omite, se busca desde {DEFAULT_FRONTEND_PORT}.",
    )
    return parser.parse_args(argv)


def is_port_available(port: int, host: str = HOST) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.2)
        if probe.connect_ex((host, port)) == 0:
            return False

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, port))
        except OSError:
            return False
    return True


def require_available_port(port: int, label: str) -> None:
    if not is_port_available(port):
        raise SystemExit(f"Puerto ocupado: {label} {HOST}:{port}")


def find_available_port(start_port: int, host: str = HOST, *, attempts: int = 100) -> int:
    for offset in range(attempts):
        port = start_port + offset
        if port > 65535:
            break
        if is_port_available(port, host):
            return port
    raise SystemExit(f"No hay puertos libres para {host} desde {start_port}")


def resolve_port(requested_port: int | None, default_port: int, label: str) -> int:
    if requested_port is not None:
        require_available_port(requested_port, label)
        return requested_port

    port = find_available_port(default_port)
    if port != default_port:
        print(f"[dev] {label} {HOST}:{default_port} ocupado; usando {HOST}:{port}", flush=True)
    return port


def build_frontend_app_url(frontend_url: str, bridge_url: str | None, *, bridge_token: str = "") -> str:
    params = {}
    if bridge_url and bridge_url != f"http://{HOST}:{DEFAULT_BRIDGE_PORT}":
        params["bridge"] = bridge_url
    if bridge_token:
        params["bridgeToken"] = bridge_token
    if not params:
        return frontend_url
    return f"{frontend_url}?{urlencode(params)}"


def wait_for_url(url: str, *, timeout: float = 10.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as response:
                if 200 <= response.status < 500:
                    return True
        except (OSError, urllib.error.URLError):
            time.sleep(0.2)
    return False


def start_process(label: str, args: list[str]) -> subprocess.Popen:
    print(f"[dev] arrancando {label}: {' '.join(args)}", flush=True)
    return subprocess.Popen(args, cwd=PROJECT_ROOT)


def stop_processes(processes: list[tuple[str, subprocess.Popen]]) -> None:
    for label, process in reversed(processes):
        if process.poll() is not None:
            continue
        print(f"[dev] deteniendo {label}", flush=True)
        process.terminate()

    for label, process in reversed(processes):
        if process.poll() is not None:
            continue
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print(f"[dev] forzando cierre de {label}", flush=True)
            process.kill()
            process.wait(timeout=5)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    bridge_port = None if args.no_bridge else resolve_port(args.bridge_port, DEFAULT_BRIDGE_PORT, "bridge")
    frontend_port = resolve_port(args.frontend_port, DEFAULT_FRONTEND_PORT, "frontend")
    bridge_url = f"http://{HOST}:{bridge_port}" if bridge_port is not None else None
    bridge_token = secrets.token_urlsafe(24) if bridge_url is not None else ""
    frontend_url = f"http://{HOST}:{frontend_port}"
    frontend_app_url = build_frontend_app_url(frontend_url, bridge_url, bridge_token=bridge_token)
    processes: list[tuple[str, subprocess.Popen]] = []

    if not FRONTEND_DIR.exists():
        raise SystemExit(f"No existe el frontend: {FRONTEND_DIR}")
    if not args.no_bridge and not BRIDGE_RUNNER.exists():
        raise SystemExit(f"No existe el runner del bridge: {BRIDGE_RUNNER}")

    try:
        if bridge_port is not None and bridge_url is not None:
            bridge_process = start_process(
                "bridge",
                [
                    sys.executable,
                    str(BRIDGE_RUNNER),
                    "--host",
                    HOST,
                    "--port",
                    str(bridge_port),
                    "--allowed-origin",
                    frontend_url,
                    "--auth-token",
                    bridge_token,
                ],
            )
            processes.append(("bridge", bridge_process))
            health_url = f"{bridge_url}/health"
            if not wait_for_url(health_url):
                raise RuntimeError(f"El bridge no responde en {health_url}")

        frontend_process = start_process(
            "frontend",
            [
                sys.executable,
                "-m",
                "http.server",
                str(frontend_port),
                "--bind",
                HOST,
                "--directory",
                str(FRONTEND_DIR),
            ],
        )
        processes.append(("frontend", frontend_process))
        if not wait_for_url(frontend_url):
            raise RuntimeError(f"El frontend no responde en {frontend_url}")

        print("", flush=True)
        print("FlatShot nueva app - entorno local", flush=True)
        print(f"Frontend: {frontend_app_url}", flush=True)
        if bridge_url is None:
            print("Bridge: desactivado (--no-bridge)", flush=True)
        else:
            print(f"Bridge:   {bridge_url}", flush=True)
            print(f"Health:   {bridge_url}/health OK", flush=True)
        print("Detener:  Ctrl+C", flush=True)
        print("", flush=True)

        if args.open:
            webbrowser.open(frontend_app_url)

        while True:
            for label, process in processes:
                exit_code = process.poll()
                if exit_code is not None:
                    raise RuntimeError(f"{label} se detuvo con codigo {exit_code}")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[dev] Ctrl+C recibido", flush=True)
        return 0
    except Exception as exc:
        print(f"[dev] error: {exc}", file=sys.stderr, flush=True)
        return 1
    finally:
        stop_processes(processes)


if __name__ == "__main__":
    raise SystemExit(main())
