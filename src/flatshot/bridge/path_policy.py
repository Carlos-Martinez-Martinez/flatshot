"""Path access policy for local bridge file operations."""
from __future__ import annotations

import threading
from pathlib import Path

from flatshot.bridge.errors import BridgeError


class TrustedPathPolicy:
    """Track user-imported roots and validate image paths against them."""

    def __init__(self) -> None:
        self._roots: set[Path] = set()
        self._lock = threading.Lock()

    def register_root(self, path: Path) -> None:
        candidate = Path(path).expanduser()
        try:
            if candidate.is_file():
                candidate = candidate.parent
            if not candidate.exists() or not candidate.is_dir():
                return
            resolved = candidate.resolve()
        except OSError:
            return

        with self._lock:
            self._roots.add(resolved)

    def validate_image_path(self, path: Path) -> None:
        self._validate_path(path, message="Imagen fuera de las carpetas importadas.")

    def validate_output_path(self, path: Path) -> None:
        self._validate_path(path, message="Destino fuera de las carpetas importadas.")

    def _validate_path(self, path: Path, *, message: str) -> None:
        with self._lock:
            roots = tuple(self._roots)
        if not roots:
            raise BridgeError("path_not_allowed", message, status=403)

        try:
            resolved = Path(path).expanduser().resolve(strict=False)
        except OSError as exc:
            raise BridgeError("path_not_allowed", message, status=403) from exc

        if any(resolved == root or root in resolved.parents for root in roots):
            return

        raise BridgeError("path_not_allowed", message, status=403)
