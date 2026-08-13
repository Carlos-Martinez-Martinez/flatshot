from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import sys
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
