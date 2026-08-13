from __future__ import annotations

import ctypes
import json
import os
import secrets
import socket
import sys
import threading
import time
import traceback
import urllib.error
import urllib.request
import webbrowser
from dataclasses import dataclass
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlencode, urlparse


APP_NAME = "FlatShot"
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from manifest import (  # noqa: E402
    PORTABLE_DEPENDENCIES,
    dependency_manifest_hash,
    dependency_sync_status,
    frontend_manifest_hash,
    runtime_manifest_hash,
    source_manifest_hash,
)
from runtime_sync import sync_runtime_app  # noqa: E402

APP_PARENT = ROOT / "app"
APP_PACKAGE = APP_PARENT / "flatshot"
FRONTEND_DIR = APP_PARENT / "frontend"
AUTOSYNC_STAMP = ROOT / ".autosync.json"
SOURCE_POINTER = ROOT / "source_path.txt"
HOST = "127.0.0.1"
DEFAULT_BRIDGE_PORT = 8765
DEFAULT_FRONTEND_PORT = 4173
LIVE_RELOAD_ENV_VAR = "FLATSHOT_LIVE_RELOAD"
PORTABLE_DEV_ENV_VAR = "FLATSHOT_PORTABLE_DEV"
DEVELOPMENT_FLAG = ROOT / "development.flag"
LIVE_RELOAD_ENDPOINT = "/__flatshot_live_reload"
LIVE_RELOAD_INTERVAL_MS = 700
UI_PREFERENCES_SETTINGS_KEY = "desktop_ui_preferences"
BOOT_PREFERENCES_SCRIPT_ID = "flatshot-boot-preferences"
BOOT_PREFERENCE_KEYS = ("themePreference", "brandTone", "interfacePreferences")


def configure_portable_environment() -> None:
    os.environ["FLATSHOT_PORTABLE"] = "1"
    os.environ["FLATSHOT_CONFIG_DIR"] = str(ROOT / "data" / "config")
    os.environ["FLATSHOT_RENDER_CACHE_DIR"] = str(ROOT / "data" / "render_cache")
    (ROOT / "data").mkdir(parents=True, exist_ok=True)


def auto_sync_from_source(source_root: Path | None = None) -> None:
    if not development_mode_enabled():
        return
    source_root = source_root or find_source_root()
    if source_root is None:
        return
    try:
        stamp = read_sync_stamp()
        runtime_hash = runtime_manifest_hash(source_root)
        dependency_hash = dependency_manifest_hash(source_root)
        dependency_status = dependency_sync_status(stamp, dependency_hash)
        if dependency_status == "needs_rebuild":
            write_launcher_log(
                "Dependencias portable",
                "requirements.txt o pyproject.toml han cambiado. "
                "Ejecuta python scripts\\build_portable.py para actualizar el venv portable.",
            )
        if not should_sync(source_root, runtime_hash, stamp):
            return
        sync_package(source_root)
        recorded_dependency_hash = dependency_hash
        if dependency_status == "needs_rebuild":
            recorded_dependency_hash = str(stamp.get("dependency_hash") or dependency_hash)
        write_sync_stamp(source_root, runtime_hash, recorded_dependency_hash, dependency_status)
    except Exception:
        write_launcher_log("Auto-sync portable", traceback.format_exc())


def find_source_root() -> Path | None:
    if not development_mode_enabled():
        return None
    candidates: list[Path] = []
    env_source = os.environ.get("FLATSHOT_SOURCE_ROOT")
    if env_source:
        candidates.append(Path(env_source))
    if SOURCE_POINTER.exists():
        try:
            candidates.append(Path(SOURCE_POINTER.read_text(encoding="utf-8").strip()))
        except OSError:
            pass
    candidates.append(ROOT.parent.parent)

    for candidate in candidates:
        resolved = candidate.expanduser().resolve()
        if is_valid_source_root(resolved):
            return resolved
    return None


def is_valid_source_root(path: Path) -> bool:
    if path == APP_PACKAGE or str(path).lower().startswith(str(APP_PACKAGE).lower()):
        return False
    return (
        (path / "pyproject.toml").exists()
        and (path / "src" / "flatshot" / "bridge" / "service.py").exists()
        and (path / "apps" / "flatshot-desktop" / "frontend" / "index.html").exists()
    )


def should_sync(source_root: Path, runtime_hash: str, stamp: dict[str, object] | None = None) -> bool:
    if not APP_PACKAGE.exists() or not FRONTEND_DIR.exists():
        return True
    stamp = stamp or read_sync_stamp()
    previous_runtime_hash = stamp.get("runtime_hash") or stamp.get("manifest_hash")
    return stamp.get("source_root") != str(source_root) or previous_runtime_hash != runtime_hash


def read_sync_stamp() -> dict[str, object]:
    try:
        return json.loads(AUTOSYNC_STAMP.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_sync_stamp(source_root: Path, runtime_hash: str, dependency_hash: str, dependency_status: str) -> None:
    AUTOSYNC_STAMP.write_text(
        json.dumps(
            {
                "source_root": str(source_root),
                "manifest_hash": source_manifest_hash(source_root),
                "runtime_hash": runtime_hash,
                "dependency_hash": dependency_hash,
                "portable_dependencies": list(PORTABLE_DEPENDENCIES),
                "dependency_status": dependency_status,
                "python_version": sys.version.split()[0],
                "synced_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def sync_package(source_root: Path) -> None:
    sync_runtime_app(source_root, APP_PARENT)


def write_launcher_log(context: str, details: str) -> None:
    log_dir = ROOT / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    with (log_dir / "runtime.log").open("a", encoding="utf-8") as handle:
        handle.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {context}\n{details}\n\n")


def source_frontend_dir(source_root: Path) -> Path:
    return source_root / "apps" / "flatshot-desktop" / "frontend"


def live_reload_enabled() -> bool:
    if not development_mode_enabled():
        return False
    configured = os.environ.get(LIVE_RELOAD_ENV_VAR, "").strip().lower()
    return configured not in {"0", "false", "no", "off"}


def development_mode_enabled() -> bool:
    configured = os.environ.get(PORTABLE_DEV_ENV_VAR, "").strip().lower()
    if configured:
        return configured not in {"0", "false", "no", "off"}
    return DEVELOPMENT_FLAG.exists()


def resolve_frontend_runtime(source_root: Path | None) -> tuple[Path, bool]:
    if source_root is not None and live_reload_enabled():
        candidate = source_frontend_dir(source_root)
        if (candidate / "index.html").exists():
            return candidate, True
    return FRONTEND_DIR, False


@dataclass
class LocalServer:
    label: str
    host: str
    port: int
    server: ThreadingHTTPServer
    thread: threading.Thread

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def stop(self) -> None:
        service = getattr(self.server, "service", None)
        if service is not None:
            try:
                service.shutdown()
            except Exception:
                pass
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


class LocalStaticServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class QuietStaticHandler(SimpleHTTPRequestHandler):
    live_reload_dir: Path | None = None

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == LIVE_RELOAD_ENDPOINT:
            self.serve_live_reload_status()
            return
        if parsed.path in {"", "/", "/index.html"}:
            self.serve_index()
            return
        super().do_GET()

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("Pragma", "no-cache")
        super().end_headers()

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        return

    def copyfile(self, source, outputfile) -> None:
        try:
            super().copyfile(source, outputfile)
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
            return

    def serve_live_reload_status(self) -> None:
        version = frontend_manifest_hash(self.live_reload_dir) if self.live_reload_dir is not None else ""
        payload = json.dumps({"liveReload": self.live_reload_dir is not None, "version": version}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def serve_index(self) -> None:
        index_path = Path(self.directory) / "index.html"
        try:
            html = index_path.read_text(encoding="utf-8")
        except OSError:
            self.send_error(404, "index.html no disponible")
            return
        html = inject_boot_preferences_script(html, read_boot_preferences())
        if self.live_reload_dir is not None:
            html = inject_live_reload_script(html)
        payload = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def read_boot_preferences() -> dict[str, object]:
    return boot_preferences_from_settings(ROOT / "data" / "config" / "settings.json")


def boot_preferences_from_settings(settings_path: Path) -> dict[str, object]:
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(settings, dict):
        return {}
    raw_preferences = settings.get(UI_PREFERENCES_SETTINGS_KEY)
    if not isinstance(raw_preferences, dict):
        return {}
    preferences: dict[str, object] = {}
    for key in BOOT_PREFERENCE_KEYS:
        value = raw_preferences.get(key)
        if key == "interfacePreferences":
            if isinstance(value, dict):
                preferences[key] = value
        elif isinstance(value, str):
            preferences[key] = value
    return preferences


def inject_boot_preferences_script(html: str, preferences: dict[str, object]) -> str:
    if not preferences or BOOT_PREFERENCES_SCRIPT_ID in html:
        return html
    payload = json.dumps(preferences, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    script = f'    <script id="{BOOT_PREFERENCES_SCRIPT_ID}" type="application/json">{payload}</script>\n'
    marker = "    <script>\n      (() => {"
    marker_index = html.find(marker)
    if marker_index >= 0:
        return html[:marker_index] + script + html[marker_index:]
    head_index = html.lower().find("</head>")
    if head_index >= 0:
        return html[:head_index] + script + html[head_index:]
    return script + html


def inject_live_reload_script(html: str) -> str:
    script = live_reload_script()
    marker = "</body>"
    marker_index = html.lower().rfind(marker)
    if marker_index < 0:
        return html + script
    return html[:marker_index] + script + html[marker_index:]


def live_reload_script() -> str:
    return f"""
<script>
(() => {{
  const endpoint = "{LIVE_RELOAD_ENDPOINT}";
  let currentVersion = null;
  let reloading = false;

  async function checkFlatShotLiveReload() {{
    try {{
      const response = await fetch(endpoint, {{ cache: "no-store" }});
      if (!response.ok) return;
      const data = await response.json();
      if (!currentVersion) {{
        currentVersion = data.version || "";
        return;
      }}
      if (data.version && data.version !== currentVersion && !reloading) {{
        reloading = true;
        window.dispatchEvent(new CustomEvent("flatshot:before-live-reload"));
        window.location.reload();
      }}
    }} catch (_error) {{}}
  }}

  window.setInterval(checkFlatShotLiveReload, {LIVE_RELOAD_INTERVAL_MS});
  checkFlatShotLiveReload();
}})();
</script>
"""


def main() -> int:
    bridge = None
    frontend = None
    try:
        configure_portable_environment()
        source_root = find_source_root()
        auto_sync_from_source(source_root)
        ensure_runtime_paths()
        frontend = start_frontend_server(source_root)
        bridge_token = secrets.token_urlsafe(24)
        bridge = start_bridge_server(allowed_origins={frontend.url}, auth_token=bridge_token)
        app_url = (
            frontend.url
            + "?"
            + urlencode({"bridge": bridge.url})
            + "#"
            + urlencode({"bridgeToken": bridge_token})
        )
        open_desktop_window(app_url)
        return 0
    except Exception as error:
        details = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        write_launcher_log("Portable launcher", details)
        show_error_dialog(
            "No se pudo arrancar FlatShot.\n\n"
            f"Detalle: {error}\n\n"
            f"Log: {ROOT / 'data' / 'logs' / 'runtime.log'}"
        )
        return 1
    finally:
        for server in [frontend, bridge]:
            if server is not None:
                try:
                    server.stop()
                except Exception:
                    pass


def ensure_runtime_paths() -> None:
    if not APP_PACKAGE.exists():
        raise RuntimeError(f"No existe el paquete portable: {APP_PACKAGE}")
    if not FRONTEND_DIR.exists():
        raise RuntimeError(f"No existe el frontend portable: {FRONTEND_DIR}")
    if str(APP_PARENT) not in sys.path:
        sys.path.insert(0, str(APP_PARENT))


def start_bridge_server(allowed_origins: set[str] | None = None, auth_token: str = "") -> LocalServer:
    from flatshot.bridge.http_server import create_server

    port = find_available_port(DEFAULT_BRIDGE_PORT)
    server = create_server(HOST, port, allowed_origins=allowed_origins, auth_token=auth_token)
    local = LocalServer("bridge", HOST, server.server_port, server, threading.Thread(target=server.serve_forever, daemon=True))
    local.thread.start()
    wait_until_ready(local.url + "/health")
    return local


def start_frontend_server(source_root: Path | None = None) -> LocalServer:
    port = find_available_port(DEFAULT_FRONTEND_PORT)
    frontend_dir, live_reload = resolve_frontend_runtime(source_root)
    handler_class = type("FlatShotStaticHandler", (QuietStaticHandler,), {})
    handler_class.live_reload_dir = frontend_dir if live_reload else None
    handler = partial(handler_class, directory=str(frontend_dir))
    server = LocalStaticServer((HOST, port), handler)
    local = LocalServer("frontend", HOST, server.server_port, server, threading.Thread(target=server.serve_forever, daemon=True))
    local.thread.start()
    wait_until_ready(local.url)
    return local


def find_available_port(preferred: int, attempts: int = 100) -> int:
    for port in range(preferred, min(preferred + attempts, 65536)):
        if is_port_available(port):
            return port
    raise RuntimeError("No hay puertos locales libres para arrancar FlatShot.")


def is_port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.2)
        if probe.connect_ex((HOST, port)) == 0:
            return False
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((HOST, port))
        except OSError:
            return False
    return True


def wait_until_ready(url: str, timeout_seconds: float = 20.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=0.5) as response:
                if 200 <= response.status < 500:
                    return
        except (OSError, urllib.error.URLError) as error:
            last_error = error
            time.sleep(0.15)
    raise RuntimeError(f"El servidor local no respondio a tiempo: {last_error}")


def open_desktop_window(url: str) -> None:
    try:
        import webview

        webview.create_window(APP_NAME, url, width=1360, height=900, min_size=(1100, 720), confirm_close=False)
        webview.start(gui="edgechromium", debug=False)
    except Exception:
        write_launcher_log("Native desktop window", traceback.format_exc())
        open_fallback_browser_window(url)


def open_fallback_browser_window(url: str) -> None:
    try:
        from tkinter import Tk, ttk
    except Exception:
        webbrowser.open(url)
        show_info_dialog("FlatShot se abrio en el navegador.\n\nPulsa Aceptar para detenerlo.")
        return

    webbrowser.open(url)
    root = Tk()
    root.title(APP_NAME)
    root.geometry("460x170")
    root.resizable(False, False)
    root.columnconfigure(0, weight=1)
    ttk.Label(
        root,
        text="FlatShot esta abierto en el navegador.\nCierra esta ventana para detener el servidor local.",
        justify="center",
    ).grid(row=0, column=0, padx=24, pady=(24, 12), sticky="ew")
    ttk.Button(root, text="Abrir navegador", command=lambda: webbrowser.open(url)).grid(row=1, column=0, pady=(0, 8))
    ttk.Button(root, text="Cerrar FlatShot", command=root.destroy).grid(row=2, column=0, pady=(0, 20))
    root.mainloop()


def show_error_dialog(message: str) -> None:
    try:
        ctypes.windll.user32.MessageBoxW(None, message, APP_NAME, 0x10)
    except Exception:
        pass


def show_info_dialog(message: str) -> None:
    try:
        ctypes.windll.user32.MessageBoxW(None, message, APP_NAME, 0x40)
    except Exception:
        time.sleep(3600)


if __name__ == "__main__":
    raise SystemExit(main())
