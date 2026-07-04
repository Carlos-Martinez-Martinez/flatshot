"""Preview and thumbnail bridge operations."""
from __future__ import annotations

from io import BytesIO
from time import perf_counter
from typing import Any, Mapping

from PIL import Image

from flatshot.application.contracts import PreviewRequest
from flatshot.bridge.errors import BridgeError, InvalidRequestError
from flatshot.bridge.payload_helpers import positive_int, preview_settings
from flatshot.bridge.serialization import preview_result_to_dict
from flatshot.bridge.validation import preview_image_path
from flatshot.core.models import SHADOW_ENGINE_DEFAULT, normalize_shadow_settings
from flatshot.core.overrides import apply_image_override, normalize_image_override
from flatshot.core.scaling import find_subject_bbox

MAX_PREVIEW_SIDE = 1200
DEFAULT_PREVIEW_SIDE = 900
MAX_THUMBNAIL_SIDE = 320
DEFAULT_THUMBNAIL_SIDE = 160


def render_preview(service, payload: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise InvalidRequestError("Expected a JSON object.")

    image_path = preview_image_path(payload)
    service._validate_image_path_access(image_path)
    target_size = preview_target_size(payload)
    settings = normalize_shadow_settings(
        preview_settings(payload.get("settings", {})),
        missing_engine=SHADOW_ENGINE_DEFAULT,
    )
    local_override = normalize_image_override(payload.get("localOverride", {}))
    preview_shadow_settings = apply_image_override(settings, local_override)

    started = perf_counter()
    try:
        result = service.preview_service.render_preview(
            PreviewRequest(
                image_path=image_path,
                settings=preview_shadow_settings,
                target_size=target_size,
                scale_factor=1.0,
                is_preview=True,
            )
        )
    except BridgeError:
        raise
    except Exception as exc:
        raise BridgeError("preview_failed", "No se pudo generar la preview.", status=422) from exc

    elapsed_ms = int(round((perf_counter() - started) * 1000))
    return preview_result_to_dict(result, source_path=image_path, render_time_ms=elapsed_ms)


def render_preview_binary(service, payload: Mapping[str, Any]) -> tuple[str, bytes, int, int, str | None]:
    if not isinstance(payload, Mapping):
        raise InvalidRequestError("Expected a JSON object.")

    image_path = preview_image_path(payload)
    service._validate_image_path_access(image_path)
    target_size = preview_target_size(payload)
    settings = normalize_shadow_settings(
        preview_settings(payload.get("settings", {})),
        missing_engine=SHADOW_ENGINE_DEFAULT,
    )
    local_override = normalize_image_override(payload.get("localOverride", {}))
    preview_shadow_settings = apply_image_override(settings, local_override)

    try:
        result = service.preview_service.render_preview(
            PreviewRequest(
                image_path=image_path,
                settings=preview_shadow_settings,
                target_size=target_size,
                scale_factor=1.0,
                is_preview=True,
            )
        )
    except BridgeError:
        raise
    except Exception as exc:
        raise BridgeError("preview_failed", "No se pudo generar la preview.", status=422) from exc

    image = Image.frombytes("RGB", (result.width, result.height), result.bytes_rgb)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return "image/png", buffer.getvalue(), result.width, result.height, result.warning


def render_thumbnail(service, payload: Mapping[str, Any]) -> tuple[str, bytes]:
    if not isinstance(payload, Mapping):
        raise InvalidRequestError("Expected a JSON object.")

    image_path = preview_image_path(payload)
    service._validate_image_path_access(image_path)
    size = min(positive_int(payload.get("size"), "size", default=DEFAULT_THUMBNAIL_SIDE), MAX_THUMBNAIL_SIDE)

    try:
        with Image.open(image_path) as opened:
            thumbnail = thumbnail_canvas(opened.convert("RGBA"), size)
    except BridgeError:
        raise
    except Exception as exc:
        raise BridgeError("thumbnail_failed", "No se pudo generar la miniatura.", status=422) from exc

    buffer = BytesIO()
    thumbnail.save(buffer, format="PNG")
    return "image/png", buffer.getvalue()


def preview_target_size(payload: Mapping[str, Any]) -> tuple[int, int]:
    width = positive_int(payload.get("targetWidth"), "targetWidth", default=DEFAULT_PREVIEW_SIDE)
    height = positive_int(payload.get("targetHeight"), "targetHeight", default=DEFAULT_PREVIEW_SIDE)
    return min(width, MAX_PREVIEW_SIDE), min(height, MAX_PREVIEW_SIDE)


def thumbnail_subject(image: Image.Image) -> Image.Image:
    bbox = find_subject_bbox(image)
    if not bbox:
        return image

    left, top, right, bottom = bbox
    if right <= left or bottom <= top:
        return image
    if (left, top, right, bottom) == (0, 0, image.width, image.height):
        return image
    return image.crop(bbox)


def thumbnail_canvas(image: Image.Image, size: int) -> Image.Image:
    subject = thumbnail_subject(image)
    subject.thumbnail((size, size), Image.Resampling.LANCZOS)

    thumbnail = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    left = (size - subject.width) // 2
    top = (size - subject.height) // 2
    thumbnail.alpha_composite(subject, (left, top))
    return thumbnail
