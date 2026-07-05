"""Bridge-owned image ids for paths discovered during scans."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping

from flatshot.bridge.errors import BridgeError, InvalidRequestError
from flatshot.bridge.validation import SUPPORTED_IMAGE_SUFFIXES, export_image_paths, preview_image_path


class BridgeImageRegistry:
    def __init__(self) -> None:
        self._paths: dict[str, Path] = {}

    def register(self, path: Path) -> str:
        resolved = Path(path).expanduser().resolve(strict=False)
        image_id = "img_" + sha256(resolved.as_posix().encode("utf-8")).hexdigest()[:20]
        self._paths[image_id] = resolved
        return image_id

    def resolve(self, image_id: str) -> Path:
        if not isinstance(image_id, str) or not image_id.strip():
            raise InvalidRequestError("Field 'imageId' must be a non-empty string.")
        path = self._paths.get(image_id.strip())
        if path is None:
            raise BridgeError("image_id_not_found", "Imagen no registrada en el lote actual.", status=404)
        return _validated_registered_path(path)


def payload_image_path(service, payload: Mapping[str, Any]) -> Path:
    raw_id = payload.get("imageId")
    if raw_id not in (None, ""):
        return service.image_registry.resolve(raw_id)
    return preview_image_path(payload)


def payload_export_image_paths(service, payload: Mapping[str, Any]) -> list[Path]:
    paths: list[Path] = []
    raw_ids = payload.get("imageIds")
    if raw_ids is not None:
        if not isinstance(raw_ids, list):
            raise InvalidRequestError("Field 'imageIds' must be a list of image ids when provided.")
        for index, raw_id in enumerate(raw_ids):
            try:
                paths.append(service.image_registry.resolve(raw_id))
            except InvalidRequestError as exc:
                raise InvalidRequestError(f"Field 'imageIds[{index}]' must be a non-empty string.") from exc

    raw_paths = payload.get("imagePaths")
    if raw_paths is not None:
        if not isinstance(raw_paths, list) or raw_paths or not paths:
            paths.extend(export_image_paths(raw_paths))
    if not paths:
        raise InvalidRequestError("Field 'imageIds' or 'imagePaths' must include at least one image.")

    unique: dict[str, Path] = {}
    for path in paths:
        unique.setdefault(path.resolve(strict=False).as_posix(), path)
    return list(unique.values())


def _validated_registered_path(path: Path) -> Path:
    if not path.exists():
        raise BridgeError("registered_image_not_found", "Imagen registrada no encontrada.", status=404)
    if not path.is_file():
        raise InvalidRequestError("Registered image must point to a file.")
    if path.suffix.lower() not in SUPPORTED_IMAGE_SUFFIXES:
        raise BridgeError("unsupported_registered_image", "Formato de imagen no soportado.", status=415)
    return path
