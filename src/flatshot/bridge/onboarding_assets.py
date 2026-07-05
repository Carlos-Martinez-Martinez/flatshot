"""Helpers for desktop onboarding asset folder access."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def onboarding_assets_folder() -> Path:
    service_path = Path(__file__).resolve()
    candidates = [
        service_path.parents[2] / "frontend" / "assets" / "onboarding",
        service_path.parents[3] / "apps" / "flatshot-desktop" / "frontend" / "assets" / "onboarding",
    ]
    for candidate in candidates:
        if candidate.exists() or candidate.parent.exists():
            return candidate
    return candidates[0]


def open_folder_with_system(path: Path) -> None:
    resolved = path.expanduser().resolve()
    if sys.platform.startswith("win"):
        os.startfile(str(resolved))  # type: ignore[attr-defined]
        return
    if sys.platform == "darwin":
        subprocess.Popen(["open", str(resolved)])
        return
    subprocess.Popen(["xdg-open", str(resolved)])


def reveal_path_with_system(path: Path) -> None:
    resolved = path.expanduser().resolve(strict=True)
    if sys.platform.startswith("win"):
        subprocess.Popen(_windows_explorer_select_command(resolved))
        return
    if sys.platform == "darwin":
        subprocess.Popen(["open", "-R", str(resolved)])
        return
    target = resolved.parent if resolved.is_file() else resolved
    subprocess.Popen(["xdg-open", str(target)])


def _windows_explorer_select_command(path: Path) -> str:
    # Explorer reliably selects paths with spaces when the path, not the whole switch, is quoted.
    return f'explorer.exe /select,"{path}"'
