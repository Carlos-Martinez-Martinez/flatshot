"""Shared bridge payload parsing helpers."""
from __future__ import annotations

from typing import Any, Mapping

from flatshot.bridge.errors import InvalidRequestError

PREVIEW_SETTING_ALIASES = {
    "transparentBg": "transparent_bg",
    "bgColor": "bg_color",
    "scaleAdjustment": "scale_adjustment",
    "shadowEngine": "shadow_engine",
    "contactBlur": "contact_blur",
    "adaptiveZoom": "adaptive_zoom",
    "lightingScene": "lighting_scene",
}
PREVIEW_SETTING_KEYS = {
    "angle",
    "distance",
    "blur",
    "spread",
    "fusion",
    "opacity",
    "noise",
    "padding",
    "contact_blur",
    "contraction",
    "adaptive_zoom",
    "scale_adjustment",
    "shadow_engine",
    "lighting_scene",
    "transparent_bg",
    "bg_color",
}


def positive_int(value: Any, field_name: str, *, default: int) -> int:
    if value is None:
        return default
    if isinstance(value, bool):
        raise InvalidRequestError(f"Field '{field_name}' must be a positive integer.")
    try:
        numeric = int(value)
    except (TypeError, ValueError) as exc:
        raise InvalidRequestError(f"Field '{field_name}' must be a positive integer.") from exc
    if numeric <= 0:
        raise InvalidRequestError(f"Field '{field_name}' must be a positive integer.")
    return numeric


def optional_string(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise InvalidRequestError("Expected string value.")
    text = value.strip()
    return text or None


def required_string(value: Any, field_name: str) -> str:
    text = optional_string(value)
    if text is None:
        raise InvalidRequestError(f"Field '{field_name}' must be a non-empty string.")
    return text


def json_compatible(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): json_compatible(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_compatible(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def preview_settings(raw_settings: Any) -> dict[str, Any]:
    if raw_settings is None:
        return {}
    if not isinstance(raw_settings, Mapping):
        raise InvalidRequestError("Field 'settings' must be an object when provided.")

    settings: dict[str, Any] = {}
    for key, value in raw_settings.items():
        normalized_key = PREVIEW_SETTING_ALIASES.get(str(key), str(key))
        if normalized_key in PREVIEW_SETTING_KEYS:
            settings[normalized_key] = value
    return settings


def export_size(raw_export: Mapping[str, Any]) -> tuple[int, int]:
    size = raw_export.get("size")
    if isinstance(size, str):
        normalized = size.lower().replace("×", "x")
        parts = normalized.split("x", 1)
        if len(parts) == 2:
            return (
                positive_int(parts[0], "outputWidth", default=1800),
                positive_int(parts[1], "outputHeight", default=2400),
            )

    return (
        positive_int(raw_export.get("outputWidth"), "outputWidth", default=1800),
        positive_int(raw_export.get("outputHeight"), "outputHeight", default=2400),
    )


def backgroundColorTuple(value: str) -> tuple[int, int, int]:
    if value == "white":
        return (255, 255, 255)
    return (230, 230, 230)
