"""Run the FlatShot modern desktop prototype for local visual review."""
from __future__ import annotations

import argparse
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path


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
    parser.add_argument("--bridge-port", type=int, default=DEFAULT_BRIDGE_PORT)
    parser.add_argument("--frontend-port", type=int, default=DEFAULT_FRONTEND_PORT)
    return parser.parse_args(argv)


def is_port_available(port: int, host: str = HOST) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return False
    return True


def require_available_port(port: int, label: str) -> None:
    if not is_port_available(port):
        raise SystemExit(f"Puerto ocupado: {label} {HOST}:{port}")


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
    bridge_url = f"http://{HOST}:{args.bridge_port}"
    frontend_url = f"http://{HOST}:{args.frontend_port}"
    processes: list[tuple[str, subprocess.Popen]] = []

    if not FRONTEND_DIR.exists():
        raise SystemExit(f"No existe el frontend: {FRONTEND_DIR}")
    if not args.no_bridge and not BRIDGE_RUNNER.exists():
        raise SystemExit(f"No existe el runner del bridge: {BRIDGE_RUNNER}")

    if not args.no_bridge:
        require_available_port(args.bridge_port, "bridge")
    require_available_port(args.frontend_port, "frontend")

    try:
        if not args.no_bridge:
            bridge_process = start_process(
                "bridge",
                [
                    sys.executable,
                    str(BRIDGE_RUNNER),
                    "--host",
                    HOST,
                    "--port",
                    str(args.bridge_port),
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
                str(args.frontend_port),
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
        print(f"Frontend: {frontend_url}", flush=True)
        if args.no_bridge:
            print("Bridge: desactivado (--no-bridge)", flush=True)
        else:
            print(f"Bridge:   {bridge_url}", flush=True)
            print(f"Health:   {bridge_url}/health OK", flush=True)
        print("Detener:  Ctrl+C", flush=True)
        print("", flush=True)

        if args.open:
            webbrowser.open(frontend_url)

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
