from __future__ import annotations

import shutil
from pathlib import Path


IGNORED_GENERATED_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "build",
    "dist",
}
IGNORED_GENERATED_SUFFIXES = (".pyc", ".pyo", ".tsbuildinfo")


def sync_runtime_app(source_root: Path, app_parent: Path) -> None:
    app_parent.mkdir(parents=True, exist_ok=True)
    copy_tree(source_root / "src" / "flatshot", app_parent / "flatshot")
    copy_tree(source_root / "apps" / "flatshot-desktop" / "frontend", app_parent / "frontend")


def copy_tree(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination, ignore=ignore_generated)


def ignore_generated(_directory: str, names: list[str]) -> set[str]:
    return {
        name
        for name in names
        if name in IGNORED_GENERATED_NAMES or name.endswith(IGNORED_GENERATED_SUFFIXES)
    }
