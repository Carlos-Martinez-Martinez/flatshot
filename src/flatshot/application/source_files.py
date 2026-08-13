"""Safe source-image discovery shared by UI and CLI workflows."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable


def regular_png_files(paths: Iterable[Path]) -> list[Path]:
    """Return regular PNG files without following symlinked entries."""
    return [
        path
        for path in paths
        if not path.is_symlink() and path.is_file() and path.suffix.lower() == ".png"
    ]
