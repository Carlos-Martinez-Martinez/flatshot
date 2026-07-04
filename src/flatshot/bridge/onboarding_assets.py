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
