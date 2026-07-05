from __future__ import annotations

import argparse
import contextlib
import http.server
import re
import socket
import threading
import urllib.error
import urllib.request
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HOST = "127.0.0.1"


class QuietStaticHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        return


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a stdlib frontend E2E smoke check.")
    parser.add_argument("--frontend-dir", type=Path, default=FRONTEND_DIR)
    args = parser.parse_args(argv)

    with serve_frontend(args.frontend_dir) as base_url:
        html = fetch_text(f"{base_url}/")
        assert_contains(html, "FlatShot", "app shell marker")
        assert_contains(html, 'id="primary-action"', "primary action")
        assert_not_contains(html, 'id="qa-lab-modal"', "QA Lab modal in product HTML")

        checked_assets = check_linked_assets(base_url, html)

    print(f"frontend_e2e_smoke OK - {checked_assets} linked assets")
    return 0


@contextlib.contextmanager
def serve_frontend(frontend_dir: Path):
    if not frontend_dir.exists():
        raise RuntimeError(f"Frontend directory not found: {frontend_dir}")

    handler = lambda *args, **kwargs: QuietStaticHandler(*args, directory=str(frontend_dir), **kwargs)
    server = http.server.ThreadingHTTPServer((HOST, 0), handler)
    thread = threading.Thread(target=server.serve_forever, name="flatshot-e2e-smoke", daemon=True)
    thread.start()
    try:
        yield f"http://{HOST}:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def check_linked_assets(base_url: str, html: str) -> int:
    assets = [
        src.split("?", 1)[0]
        for src in re.findall(r'<script\s+src="\./([^"]+)"', html)
    ]
    assets.extend(
        href.split("?", 1)[0]
        for href in re.findall(r'<link\s+[^>]*href="\./([^"]+\.css[^"]*)"', html)
    )
    if not assets:
        raise RuntimeError("No linked frontend assets found.")

    for asset in assets:
        fetch_bytes(f"{base_url}/{asset}")
    return len(assets)


def fetch_text(url: str) -> str:
    return fetch_bytes(url).decode("utf-8")


def fetch_bytes(url: str) -> bytes:
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            if response.status != 200:
                raise RuntimeError(f"{url} returned HTTP {response.status}")
            return response.read()
    except (OSError, socket.timeout, urllib.error.URLError) as exc:
        raise RuntimeError(f"Could not fetch {url}: {exc}") from exc


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise RuntimeError(f"Missing {label}: {needle}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise RuntimeError(f"Unexpected {label}: {needle}")


if __name__ == "__main__":
    raise SystemExit(main())
