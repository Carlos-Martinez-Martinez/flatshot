from __future__ import annotations

import numpy as np
from PIL import Image, ImageChops, ImageFilter

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


def to_float(mask: Image.Image) -> np.ndarray:
    return np.asarray(mask, dtype=np.float32) / 255.0


def from_float(alpha: np.ndarray) -> Image.Image:
    return Image.fromarray(np.clip(alpha * 255.0, 0, 255).astype(np.uint8), mode="L")


def smoothstep(edge0: float, edge1: float, value: np.ndarray) -> np.ndarray:
    if edge1 <= edge0:
        return (value >= edge1).astype(np.float32)
    t = np.clip((value - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def vertical_profile(mask_alpha: np.ndarray) -> tuple[np.ndarray, tuple[int, int, int, int] | None]:
    ys, xs = np.where(mask_alpha > 0.02)
    h, w = mask_alpha.shape
    if len(xs) == 0 or len(ys) == 0:
        return np.zeros_like(mask_alpha, dtype=np.float32), None

    left = int(xs.min())
    right = int(xs.max()) + 1
    top = int(ys.min())
    bottom = int(ys.max()) + 1
    denom = max(bottom - top - 1, 1)
    row = (np.arange(h, dtype=np.float32)[:, None] - top) / float(denom)
    profile = np.broadcast_to(np.clip(row, 0.0, 1.0), (h, w)).copy()
    return profile, (left, top, right, bottom)


def make_protection_lut(strength: float) -> list[int]:
    return [int(max(0.0, min(255.0, 255.0 - value * strength))) for value in range(256)]


def apply_protection(layer: Image.Image, mask: Image.Image, *, strength: float, blur: float) -> Image.Image:
    if strength <= 0:
        return layer
    protect = mask
    if blur > 0:
        protect = protect.filter(ImageFilter.GaussianBlur(blur))
    lut = make_protection_lut(strength)
    return ImageChops.multiply(layer, protect.point(lut))
