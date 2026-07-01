"""Validation helpers for FlatShot bridge payloads."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from flatshot.bridge.errors import BridgeError, InvalidRequestError


SUPPORTED_IMAGE_SUFFIXES = {".png"}


def preview_image_path(payload: Mapping[str, Any]) -> Path:
    raw_path = payload.get("imagePath")
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise InvalidRequestError("Field 'imagePath' must be a non-empty path string.")

    path = Path(raw_path).expanduser()
    if not path.exists():
        raise BridgeError("preview_file_not_found", "Imagen no encontrada.", status=404)
    if not path.is_file():
        raise InvalidRequestError("Field 'imagePath' must point to a file.")
    if path.suffix.lower() not in SUPPORTED_IMAGE_SUFFIXES:
        raise BridgeError("unsupported_preview_file", "Formato de imagen no soportado.", status=415)
    return path


def export_image_paths(raw_paths: Any) -> list[Path]:
    if not isinstance(raw_paths, list) or not raw_paths:
        raise InvalidRequestError("Field 'imagePaths' must be a non-empty list of paths.")

    paths: list[Path] = []
    for index, raw_path in enumerate(raw_paths):
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise InvalidRequestError(f"Field 'imagePaths[{index}]' must be a non-empty path string.")
        path = Path(raw_path).expanduser()
        if not path.exists():
            raise BridgeError("export_file_not_found", "Imagen no encontrada.", status=404)
        if not path.is_file():
            raise InvalidRequestError(f"Field 'imagePaths[{index}]' must point to a file.")
        if path.suffix.lower() not in SUPPORTED_IMAGE_SUFFIXES:
            raise BridgeError("unsupported_export_file", "Formato de exportación no soportado.", status=415)
        paths.append(path)
    return paths
