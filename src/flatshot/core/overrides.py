from pathlib import Path
from typing import Any

from flatshot.core.models import SHADOW_SETTING_LIMITS, ShadowSettings


LOCAL_OVERRIDE_DEFAULTS = {
    "size_delta": 0,
    "shadow_delta": 0,
    "blur_delta": 0,
}

LOCAL_OVERRIDE_LIMITS = {
    "size_delta": (-30, 30),
    "shadow_delta": (-40, 40),
    "blur_delta": (-40, 40),
}


def clamp_int(value: Any, minimum: int, maximum: int) -> int:
    try:
        parsed = int(round(float(value)))
    except (TypeError, ValueError):
        parsed = 0
    return max(min(parsed, maximum), minimum)


def override_key(path: str | Path | None) -> str:
    """Stable key for per-image adjustments."""
    if not path:
        return ""
    candidate = Path(path)
    try:
        return str(candidate.resolve())
    except OSError:
        return str(candidate)


def normalize_image_override(override: dict | None) -> dict:
    """Return only non-zero, clamped local deltas."""
    if not isinstance(override, dict):
        return {}

    normalized = {}
    for field, default in LOCAL_OVERRIDE_DEFAULTS.items():
        minimum, maximum = LOCAL_OVERRIDE_LIMITS[field]
        value = clamp_int(override.get(field, default), minimum, maximum)
        if value != default:
            normalized[field] = value
    return normalized


def has_image_override(override: dict | None) -> bool:
    return bool(normalize_image_override(override))


def apply_image_override(settings: ShadowSettings, override: dict | None) -> ShadowSettings:
    """Apply per-image deltas without mutating the preset/global settings."""
    normalized = normalize_image_override(override)
    if not normalized:
        return settings.model_copy()

    updates = {}
    if "size_delta" in normalized:
        updates["scale_adjustment"] = clamp_int(
            getattr(settings, "scale_adjustment", 0) + normalized["size_delta"],
            -30,
            30,
        )
    if "shadow_delta" in normalized:
        updates["opacity"] = clamp_int(settings.opacity + normalized["shadow_delta"], 0, 100)
    if "blur_delta" in normalized:
        minimum, maximum = SHADOW_SETTING_LIMITS["blur"]
        updates["blur"] = clamp_int(settings.blur + normalized["blur_delta"], minimum, maximum)

    return settings.model_copy(update=updates)
