from __future__ import annotations

import hashlib
import importlib.util
import os
import zipfile
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str, relative_path: str):
    path = PROJECT_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


package_candidate = load_script("flatshot_package_candidate_test", "scripts/package_release_candidate.py")
verify_candidate = load_script("flatshot_verify_candidate_test", "scripts/verify_portable_candidate.py")


def make_portable_tree(root: Path) -> Path:
    portable = root / "FlatShotPortable"
    (portable / "_internal" / "frontend").mkdir(parents=True)
    (portable / "_internal" / "frontend" / "index.html").write_text("FlatShot", encoding="utf-8")
    (portable / "FlatShot.exe").write_bytes(b"MZ-frozen")
    for name in ("Abrir FlatShot.vbs", "Diagnostico FlatShot.bat", "README_PORTABLE.txt"):
        (portable / name).write_text("FlatShot", encoding="utf-8")
    (portable / "data").mkdir()
    return portable


def test_package_portable_writes_versioned_zip_and_lowercase_sha256(tmp_path):
    portable = make_portable_tree(tmp_path / "build")

    archive, sums = package_candidate.package_portable(portable, tmp_path / "release", "1.0.1")

    expected_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
    assert archive.name == "FlatShotPortable-v1.0.1.zip"
    assert sums.read_text(encoding="ascii") == f"{expected_hash}  {archive.name}\n"
    with zipfile.ZipFile(archive) as bundle:
        assert "FlatShotPortable/FlatShot.exe" in bundle.namelist()


def test_verify_checksum_rejects_modified_archive(tmp_path):
    portable = make_portable_tree(tmp_path / "build")
    archive, sums = package_candidate.package_portable(portable, tmp_path / "release", "1.0.1")
    archive.write_bytes(archive.read_bytes() + b"tampered")

    with pytest.raises(RuntimeError, match="checksum"):
        verify_candidate.verify_checksum(archive, sums)


def test_extract_archive_rejects_path_traversal(tmp_path):
    archive = tmp_path / "malicious.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("../outside.txt", "unsafe")

    with pytest.raises(RuntimeError, match="unsafe archive path"):
        verify_candidate.extract_archive(archive, tmp_path / "extract")
    assert not (tmp_path / "outside.txt").exists()


def test_sanitized_environment_removes_python_state_and_reduces_path(monkeypatch):
    monkeypatch.setenv("PYTHONHOME", "C:/Python")
    monkeypatch.setenv("PYTHONPATH", "C:/repo/src")
    monkeypatch.setenv("VIRTUAL_ENV", "C:/repo/venv")
    monkeypatch.setenv("PATH", "C:/Python;C:/repo/venv/Scripts")
    monkeypatch.setenv("SystemRoot", "C:/Windows")

    env = verify_candidate.sanitized_portable_environment()

    assert "PYTHONHOME" not in env
    assert "PYTHONPATH" not in env
    assert "VIRTUAL_ENV" not in env
    assert env["PYTHONNOUSERSITE"] == "1"
    assert [entry.replace("\\", "/").casefold() for entry in env["PATH"].split(os.pathsep)] == [
        "c:/windows",
        "c:/windows/system32",
        "c:/windows/system32/wbem",
    ]


def test_verify_candidate_extracts_and_validates_without_executing(tmp_path):
    portable = make_portable_tree(tmp_path / "build")
    archive, sums = package_candidate.package_portable(portable, tmp_path / "release", "1.0.1")

    extracted = verify_candidate.verify_candidate(
        archive,
        sums,
        tmp_path / "Ruta separada con espacios y á",
        execute_smoke=False,
    )

    assert extracted == (tmp_path / "Ruta separada con espacios y á" / "FlatShotPortable").resolve()
    assert (extracted / "FlatShot.exe").read_bytes() == b"MZ-frozen"
