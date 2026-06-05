from __future__ import annotations

import importlib.machinery
import importlib.util
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
    monkeypatch.delenv(launcher.LIVE_RELOAD_ENV_VAR, raising=False)

    frontend_dir, live_reload = launcher.resolve_frontend_runtime(PROJECT_ROOT)

    assert frontend_dir == PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
    assert live_reload is True


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
    assert injected.index(launcher.LIVE_RELOAD_ENDPOINT) < injected.lower().index("</body>")


def test_frontend_manifest_hash_changes_with_frontend_file_content(tmp_path):
    launcher = load_launcher()
    index = tmp_path / "index.html"
    index.write_text("<html>one</html>", encoding="utf-8")
    first_hash = launcher.frontend_manifest_hash(tmp_path)

    index.write_text("<html>two and more</html>", encoding="utf-8")

    assert launcher.frontend_manifest_hash(tmp_path) != first_hash
