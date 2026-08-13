from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import sys
from types import SimpleNamespace
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LAUNCHER_PATH = PROJECT_ROOT / "scripts" / "portable" / "FlatShot.pyw"


def load_launcher():
    loader = importlib.machinery.SourceFileLoader("flatshot_portable_launcher_test", str(LAUNCHER_PATH))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[loader.name] = module
    loader.exec_module(module)
    return module


def test_resolve_frontend_runtime_uses_source_frontend_with_live_reload(monkeypatch):
    launcher = load_launcher()
    monkeypatch.setenv(launcher.PORTABLE_DEV_ENV_VAR, "1")
    monkeypatch.delenv(launcher.LIVE_RELOAD_ENV_VAR, raising=False)

    frontend_dir, live_reload = launcher.resolve_frontend_runtime(PROJECT_ROOT)

    assert frontend_dir == PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
    assert live_reload is True


def test_resolve_frontend_runtime_requires_explicit_development_mode(monkeypatch):
    launcher = load_launcher()
    monkeypatch.setenv(launcher.PORTABLE_DEV_ENV_VAR, "0")
    monkeypatch.delenv(launcher.LIVE_RELOAD_ENV_VAR, raising=False)

    frontend_dir, live_reload = launcher.resolve_frontend_runtime(PROJECT_ROOT)

    assert frontend_dir == launcher.FRONTEND_DIR
    assert live_reload is False


def test_resolve_frontend_runtime_can_disable_live_reload(monkeypatch):
    launcher = load_launcher()
    monkeypatch.setenv(launcher.LIVE_RELOAD_ENV_VAR, "0")

    frontend_dir, live_reload = launcher.resolve_frontend_runtime(PROJECT_ROOT)

    assert frontend_dir == launcher.FRONTEND_DIR
    assert live_reload is False


def test_live_reload_script_is_injected_before_body_close():
    launcher = load_launcher()
    html = "<html><body><main>FlatShot</main></body></html>"

    injected = launcher.inject_live_reload_script(html)

    assert launcher.LIVE_RELOAD_ENDPOINT in injected
    assert "flatshot:before-live-reload" in injected
    assert injected.index(launcher.LIVE_RELOAD_ENDPOINT) < injected.lower().index("</body>")


def test_boot_preferences_reads_only_first_paint_preferences(tmp_path):
    launcher = load_launcher()
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                launcher.UI_PREFERENCES_SETTINGS_KEY: {
                    "themePreference": "dark",
                    "brandTone": "violet",
                    "interfacePreferences": {"density": "comfortable", "thumbnailSize": "large"},
                    "bridgeScanPath": "C:/Users/Example/Images",
                    "lastOutputFolder": "C:/Users/Example/Exports",
                }
            }
        ),
        encoding="utf-8",
    )

    preferences = launcher.boot_preferences_from_settings(settings_path)

    assert preferences == {
        "themePreference": "dark",
        "brandTone": "violet",
        "interfacePreferences": {"density": "comfortable", "thumbnailSize": "large"},
    }


def test_boot_preferences_script_is_injected_before_theme_bootstrap():
    launcher = load_launcher()
    html = (
        "<!doctype html>\n"
        "<html><head>\n"
        "    <script>\n"
        "      (() => {\n"
        '        localStorage.getItem("flatshot.theme");\n'
        "      })();\n"
        "    </script>\n"
        '    <link rel="stylesheet" href="./css/00-settings/tokens.css" />\n'
        "</head><body></body></html>"
    )

    injected = launcher.inject_boot_preferences_script(
        html,
        {
            "themePreference": "dark",
            "brandTone": "blue",
            "interfacePreferences": {"density": "comfortable"},
            "unsafe": "</script><script>alert(1)</script>",
        },
    )

    assert f'id="{launcher.BOOT_PREFERENCES_SCRIPT_ID}"' in injected
    assert injected.index(launcher.BOOT_PREFERENCES_SCRIPT_ID) < injected.index('localStorage.getItem("flatshot.theme")')
    assert injected.index(launcher.BOOT_PREFERENCES_SCRIPT_ID) < injected.index("css/00-settings/tokens.css")
    assert "</script><script>alert(1)</script>" not in injected
    assert "\\u003c/script>" in injected


def test_static_handler_disables_cache_without_live_reload(monkeypatch):
    launcher = load_launcher()
    sent_headers = []
    handler = object.__new__(launcher.QuietStaticHandler)
    handler.live_reload_dir = None
    handler.send_header = lambda name, value: sent_headers.append((name, value))
    monkeypatch.setattr(launcher.SimpleHTTPRequestHandler, "end_headers", lambda self: None)

    handler.end_headers()

    assert ("Cache-Control", "no-store, max-age=0") in sent_headers
    assert ("Pragma", "no-cache") in sent_headers


def test_frontend_manifest_hash_changes_with_frontend_file_content(tmp_path):
    launcher = load_launcher()
    index = tmp_path / "index.html"
    index.write_text("<html>one</html>", encoding="utf-8")
    first_hash = launcher.frontend_manifest_hash(tmp_path)

    index.write_text("<html>two and more</html>", encoding="utf-8")

    assert launcher.frontend_manifest_hash(tmp_path) != first_hash


def test_frozen_roots_separate_writable_executable_and_bundled_resources(monkeypatch, tmp_path):
    launcher = load_launcher()
    portable_dir = tmp_path / "FlatShot Portable"
    resource_dir = tmp_path / "bundle resources"
    monkeypatch.setattr(launcher.sys, "frozen", True, raising=False)
    monkeypatch.setattr(launcher.sys, "executable", str(portable_dir / "FlatShot.exe"))
    monkeypatch.setattr(launcher.sys, "_MEIPASS", str(resource_dir), raising=False)

    assert launcher.portable_root() == portable_dir.resolve()
    assert launcher.resource_root() == resource_dir.resolve()


def test_non_frozen_roots_use_launcher_directory(monkeypatch):
    launcher = load_launcher()
    monkeypatch.delattr(launcher.sys, "frozen", raising=False)
    monkeypatch.delattr(launcher.sys, "_MEIPASS", raising=False)

    expected = launcher.Path(launcher.__file__).resolve().parent
    assert launcher.portable_root() == expected
    assert launcher.resource_root() == expected


def test_run_smoke_checks_real_routes_and_stops_both_servers(monkeypatch):
    launcher = load_launcher()
    stopped: list[str] = []
    checked: list[str] = []
    frontend = SimpleNamespace(url="http://127.0.0.1:4173", stop=lambda: stopped.append("frontend"))
    bridge = SimpleNamespace(url="http://127.0.0.1:8765", stop=lambda: stopped.append("bridge"))

    monkeypatch.setattr(launcher, "configure_portable_environment", lambda: None)
    monkeypatch.setattr(launcher, "find_source_root", lambda: None)
    monkeypatch.setattr(launcher, "auto_sync_from_source", lambda _source_root: None)
    monkeypatch.setattr(launcher, "ensure_runtime_paths", lambda: None)
    monkeypatch.setattr(launcher, "start_frontend_server", lambda source_root=None: frontend)
    monkeypatch.setattr(
        launcher,
        "start_bridge_server",
        lambda allowed_origins=None, auth_token="": bridge,
    )
    monkeypatch.setattr(launcher, "verify_http_endpoint", checked.append)

    launcher.run_smoke()

    assert checked == [frontend.url + "/", bridge.url + "/health"]
    assert stopped == ["bridge", "frontend"]


def test_main_smoke_never_opens_desktop_window(monkeypatch):
    launcher = load_launcher()
    calls: list[str] = []
    monkeypatch.setattr(launcher, "run_smoke", lambda: calls.append("smoke"))
    monkeypatch.setattr(launcher, "open_desktop_window", lambda _url: calls.append("window"))

    assert launcher.main(["--smoke"]) == 0
    assert calls == ["smoke"]
