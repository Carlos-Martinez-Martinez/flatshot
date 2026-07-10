from __future__ import annotations

import importlib.util
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUILD_PORTABLE_PATH = PROJECT_ROOT / "scripts" / "build_portable.py"

spec = importlib.util.spec_from_file_location("flatshot_build_portable", BUILD_PORTABLE_PATH)
assert spec is not None
build_portable = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(build_portable)


def test_build_portable_without_venv_copies_runtime_files(tmp_path):
    target = tmp_path / "FlatShotPortable"

    build_portable.build_portable(PROJECT_ROOT, target, install_dependencies=False)

    assert (target / "portable.flag").read_text(encoding="utf-8") == "portable\n"
    assert (target / "source_path.txt").read_text(encoding="utf-8") == str(PROJECT_ROOT)
    assert (target / ".autosync.json").exists()
    assert (target / "FlatShot.pyw").exists()
    assert (target / "manifest.py").exists()
    assert (target / "runtime_sync.py").exists()
    assert (target / "Abrir FlatShot.vbs").exists()
    assert (target / "Diagnostico FlatShot.bat").exists()
    assert (target / "app" / "flatshot" / "bridge" / "service.py").exists()
    assert (target / "app" / "frontend" / "index.html").exists()
    assert not (target / "venv").exists()


def test_build_portable_sync_stamp_separates_runtime_and_dependencies(tmp_path):
    target = tmp_path / "FlatShotPortable"

    build_portable.build_portable(PROJECT_ROOT, target, install_dependencies=False)

    stamp = json.loads((target / ".autosync.json").read_text(encoding="utf-8"))
    assert stamp["source_root"] == str(PROJECT_ROOT)
    assert stamp["manifest_hash"] == build_portable.source_manifest_hash(PROJECT_ROOT)
    assert stamp["runtime_hash"] == build_portable.runtime_manifest_hash(PROJECT_ROOT)
    assert stamp["dependency_hash"] == build_portable.dependency_manifest_hash(PROJECT_ROOT)
    assert stamp["portable_dependencies"] == list(build_portable.PORTABLE_DEPENDENCIES)
    assert stamp["dependency_status"] == "current"
    assert stamp["python_version"].startswith(str(build_portable.sys.version_info.major))


def test_release_portable_does_not_embed_development_source_pointer(tmp_path):
    target = tmp_path / "FlatShotPortable"

    build_portable.build_portable(
        PROJECT_ROOT,
        target,
        install_dependencies=False,
        development=False,
    )

    assert not (target / "source_path.txt").exists()
    assert not (target / "development.flag").exists()
    assert (target / "release.flag").read_text(encoding="utf-8") == "release\n"
    stamp = json.loads((target / ".autosync.json").read_text(encoding="utf-8"))
    assert stamp["source_root"] is None
    assert stamp["portable_mode"] == "release"


def test_source_manifest_tracks_backend_and_frontend_files():
    files = {path.relative_to(PROJECT_ROOT).as_posix() for path in build_portable.iter_source_files(PROJECT_ROOT)}

    assert "src/flatshot/bridge/service.py" in files
    assert "apps/flatshot-desktop/frontend/index.html" in files
    assert "requirements.txt" in files
    assert not any("__pycache__" in path for path in files)


def test_runtime_manifest_excludes_dependency_files():
    files = {
        path.relative_to(PROJECT_ROOT).as_posix()
        for path in build_portable.iter_runtime_source_files(PROJECT_ROOT)
    }

    assert "src/flatshot/bridge/service.py" in files
    assert "apps/flatshot-desktop/frontend/index.html" in files
    assert "requirements.txt" not in files
    assert "pyproject.toml" not in files


def test_portable_window_dependency_is_recorded():
    assert any(dependency.startswith("pywebview==") for dependency in build_portable.PORTABLE_DEPENDENCIES)


def test_portable_runtime_lock_is_present_and_constrained():
    lock = (PROJECT_ROOT / "requirements.lock").read_text(encoding="utf-8")

    assert "Pillow==" in lock
    assert "numpy==" in lock
    assert "pydantic==" in lock
    assert not any(line.startswith(("Pillow>=", "numpy>=", "pydantic>=")) for line in lock.splitlines())
