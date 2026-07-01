from __future__ import annotations

import hashlib
from pathlib import Path


RUNTIME_SOURCE_DIRS = (
    Path("src") / "flatshot",
    Path("apps") / "flatshot-desktop" / "frontend",
)
DEPENDENCY_FILES = ("pyproject.toml", "requirements.txt")
PORTABLE_DEPENDENCIES = ("pywebview>=6.0",)


def source_manifest_hash(source_root: Path) -> str:
    return files_manifest_hash(iter_source_files(source_root), source_root)


def runtime_manifest_hash(source_root: Path) -> str:
    return files_manifest_hash(iter_runtime_source_files(source_root), source_root)


def frontend_manifest_hash(frontend_dir: Path) -> str:
    return files_manifest_hash(iter_frontend_files(frontend_dir), frontend_dir)


def dependency_manifest_hash(source_root: Path) -> str:
    digest = hashlib.sha256()
    digest.update(files_manifest_hash(iter_dependency_files(source_root), source_root).encode("utf-8"))
    for dependency in PORTABLE_DEPENDENCIES:
        digest.update(f"\0portable:{dependency}\n".encode("utf-8"))
    return digest.hexdigest()


def files_manifest_hash(files, source_root: Path) -> str:
    digest = hashlib.sha256()
    for file in files:
        stat = file.stat()
        rel = file.relative_to(source_root).as_posix()
        digest.update(f"{rel}\0{stat.st_size}\0{stat.st_mtime_ns}\n".encode("utf-8"))
    return digest.hexdigest()


def iter_source_files(source_root: Path):
    yield from iter_runtime_source_files(source_root)
    yield from iter_dependency_files(source_root)


def iter_runtime_source_files(source_root: Path):
    for source_dir in RUNTIME_SOURCE_DIRS:
        root = source_root / source_dir
        if not root.exists():
            continue
        for file in root.rglob("*"):
            if should_skip_source_file(file):
                continue
            if file.is_file():
                yield file


def iter_frontend_files(frontend_dir: Path):
    if not frontend_dir.exists():
        return
    for file in frontend_dir.rglob("*"):
        if should_skip_source_file(file):
            continue
        if file.is_file():
            yield file


def iter_dependency_files(source_root: Path):
    for file_name in DEPENDENCY_FILES:
        file = source_root / file_name
        if file.exists() and file.is_file():
            yield file


def should_skip_source_file(file: Path) -> bool:
    parts = set(file.parts)
    if {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "release", "venv", ".venv"} & parts:
        return True
    return file.suffix in {".pyc", ".pyo"} or file.name.endswith(".tsbuildinfo")


def dependency_sync_status(stamp: dict[str, object], dependency_hash: str) -> str:
    previous_hash = stamp.get("dependency_hash")
    if previous_hash and previous_hash != dependency_hash:
        return "needs_rebuild"
    return "current"
