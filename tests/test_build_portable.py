from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


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

    build_portable.write_release_support_files(target)

    assert not (target / "source_path.txt").exists()
    assert not (target / "development.flag").exists()
    assert (target / "release.flag").read_text(encoding="utf-8") == "release\n"
    assert not (target / ".autosync.json").exists()
    assert "FlatShot.exe" in (target / "Abrir FlatShot.vbs").read_text(encoding="utf-8")
    assert "pythonw.exe" not in (target / "Abrir FlatShot.vbs").read_text(encoding="utf-8")


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


def make_frozen_layout(root: Path) -> None:
    (root / "_internal" / "frontend").mkdir(parents=True)
    (root / "_internal" / "frontend" / "index.html").write_text("<title>FlatShot</title>", encoding="utf-8")
    (root / "FlatShot.exe").write_bytes(b"MZ")
    build_portable.write_release_support_files(root)


def test_release_validation_accepts_frozen_one_folder_layout(tmp_path):
    target = tmp_path / "FlatShotPortable"
    make_frozen_layout(target)

    build_portable.validate_release_portable(target, forbidden_roots=[PROJECT_ROOT])


@pytest.mark.parametrize(
    "relative_path",
    [
        "pyvenv.cfg",
        "venv/Scripts/python.exe",
        "venv/Scripts/pythonw.exe",
        "source_path.txt",
        "development.flag",
    ],
)
def test_release_validation_rejects_non_relocatable_development_entries(tmp_path, relative_path):
    target = tmp_path / "FlatShotPortable"
    make_frozen_layout(target)
    bad_file = target / relative_path
    bad_file.parent.mkdir(parents=True, exist_ok=True)
    bad_file.write_text("builder state", encoding="utf-8")

    with pytest.raises(RuntimeError, match="non-relocatable"):
        build_portable.validate_release_portable(target)


@pytest.mark.parametrize("marker", ["hostedtoolcache", "RUNNER_WORKSPACE", "GITHUB_WORKSPACE"])
def test_release_validation_rejects_ci_builder_markers_in_text_configuration(tmp_path, marker):
    target = tmp_path / "FlatShotPortable"
    make_frozen_layout(target)
    (target / "runtime.cfg").write_text(f"home=C:/build/{marker}/python.exe", encoding="utf-8")

    with pytest.raises(RuntimeError, match="builder path"):
        build_portable.validate_release_portable(target)


def test_release_validation_rejects_known_checkout_path_in_text_configuration(tmp_path):
    target = tmp_path / "FlatShotPortable"
    make_frozen_layout(target)
    checkout = tmp_path / "checkout with spaces"
    (target / "runtime.json").write_text(json.dumps({"root": str(checkout)}), encoding="utf-8")

    with pytest.raises(RuntimeError, match="builder path"):
        build_portable.validate_release_portable(target, forbidden_roots=[checkout])
