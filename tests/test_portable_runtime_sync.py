from __future__ import annotations

import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SYNC_PATH = PROJECT_ROOT / "scripts" / "portable" / "runtime_sync.py"


def load_runtime_sync():
    spec = importlib.util.spec_from_file_location("flatshot_portable_runtime_sync", SYNC_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_sync_runtime_app_copies_backend_and_frontend_without_generated_files(tmp_path):
    runtime_sync = load_runtime_sync()
    source_root = tmp_path / "source"
    app_parent = tmp_path / "portable" / "app"
    backend = source_root / "src" / "flatshot"
    frontend = source_root / "apps" / "flatshot-desktop" / "frontend"
    backend.mkdir(parents=True)
    frontend.mkdir(parents=True)
    (backend / "service.py").write_text("service = True\n", encoding="utf-8")
    (backend / "__pycache__").mkdir()
    (backend / "__pycache__" / "service.pyc").write_text("generated\n", encoding="utf-8")
    (frontend / "index.html").write_text("<html></html>\n", encoding="utf-8")
    (frontend / "node_modules").mkdir()
    (frontend / "node_modules" / "generated.js").write_text("generated\n", encoding="utf-8")
    (app_parent / "flatshot").mkdir(parents=True)
    (app_parent / "flatshot" / "stale.py").write_text("stale\n", encoding="utf-8")

    runtime_sync.sync_runtime_app(source_root, app_parent)

    assert (app_parent / "flatshot" / "service.py").read_text(encoding="utf-8") == "service = True\n"
    assert (app_parent / "frontend" / "index.html").exists()
    assert not (app_parent / "flatshot" / "stale.py").exists()
    assert not (app_parent / "flatshot" / "__pycache__").exists()
    assert not (app_parent / "frontend" / "node_modules").exists()
