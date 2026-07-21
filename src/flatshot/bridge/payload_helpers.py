"""Shared bridge payload parsing helpers."""
from __future__ import annotations

from typing import Any, Mapping

from flatshot.bridge.errors import InvalidRequestError
from flatshot.core.models import SHADOW_SETTING_LIMITS, CurveData
from flatshot.core.scaling import DEFAULT_SCALE_CURVE, normalize_curve_data

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
PREVIEW_SETTING_LIMITS = SHADOW_SETTING_LIMITS


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


def bounded_int(value: Any, field_name: str, *, minimum: int, maximum: int) -> int:
    if isinstance(value, bool):
        raise InvalidRequestError(
            f"Field '{field_name}' must be an integer between {minimum} and {maximum}."
        )
    try:
        numeric = int(value)
    except (TypeError, ValueError) as exc:
        raise InvalidRequestError(
            f"Field '{field_name}' must be an integer between {minimum} and {maximum}."
        ) from exc
    if numeric < minimum or numeric > maximum:
        raise InvalidRequestError(
            f"Field '{field_name}' must be an integer between {minimum} and {maximum}."
        )
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
            if normalized_key in PREVIEW_SETTING_LIMITS:
                minimum, maximum = PREVIEW_SETTING_LIMITS[normalized_key]
                settings[normalized_key] = bounded_int(value, normalized_key, minimum=minimum, maximum=maximum)
            else:
                settings[normalized_key] = value
    return settings


def curve_data_payload(payload: Mapping[str, Any]) -> CurveData:
    raw_curve = payload.get("curveData")
    if raw_curve is None:
        raw_curve = payload.get("scaleCurve")
    if raw_curve is None:
        raw_curve = DEFAULT_SCALE_CURVE.copy()
    if not isinstance(raw_curve, Mapping):
        raise InvalidRequestError("Field 'curveData' must be an object when provided.")
    try:
        return normalize_curve_data(raw_curve)
    except (TypeError, ValueError) as exc:
        raise InvalidRequestError("Field 'curveData' is not a valid scale curve.") from exc


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
