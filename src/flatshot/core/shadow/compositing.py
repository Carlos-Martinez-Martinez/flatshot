from __future__ import annotations

import numpy as np
from PIL import Image

from flatshot.core.shadow.geometry import lightweight_mask_signature
from flatshot.core.shadow.types import ShadowPaint


def alpha_to_shadow_rgba(alpha: np.ndarray, paint: ShadowPaint) -> Image.Image:
    alpha_u8 = np.clip(alpha * 255.0, 0, 255).astype(np.uint8)
    rgba = np.zeros((alpha_u8.shape[0], alpha_u8.shape[1], 4), dtype=np.uint8)
    rgba[:, :, 0] = int(paint.rgb[0])
    rgba[:, :, 1] = int(paint.rgb[1])
    rgba[:, :, 2] = int(paint.rgb[2])
    rgba[:, :, 3] = alpha_u8
    return Image.fromarray(rgba, mode="RGBA")


def accumulate_alpha(base: np.ndarray, layer: np.ndarray) -> np.ndarray:
    return 1.0 - ((1.0 - base) * (1.0 - np.clip(layer, 0.0, 1.0)))


def deterministic_noise_alpha(
    alpha: np.ndarray,
    mask: Image.Image,
    *,
    intensity_percent: int,
    settings_key: tuple,
    bbox: tuple[int, int, int, int] | None = None,
) -> np.ndarray:
    if intensity_percent <= 0 or alpha.size == 0:
        return alpha

    signature = lightweight_mask_signature(mask, bbox)
    seed = signature
    for value in settings_key:
        seed = ((seed * 16777619) ^ int(value)) & 0xFFFFFFFF

    rng = np.random.default_rng(seed)
    sigma = max(0.0, float(intensity_percent)) / 100.0 * 0.45
    noise = rng.normal(1.0, sigma, alpha.shape).astype(np.float32)
    return np.clip(alpha * noise, 0.0, 1.0)
