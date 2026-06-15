from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageChops, ImageFilter

from flatshot.core.shadow.compositing import (
    accumulate_alpha,
    deterministic_noise_alpha,
)
from flatshot.core.shadow.geometry import (
    ShadowVector,
    compute_shadow_roi,
    paste_offset,
    resize_for_cap,
)
from flatshot.core.shadow.types import RenderDiagnostics, ShadowRenderContext, ShadowRenderResult


@dataclass(frozen=True)
class StudioProfile:
    contact_gain: float
    directional_gain: float
    ambient_gain: float
    softness: float
    strip_anisotropy: float = 0.0


STUDIO_PROFILES = {
    "softbox": StudioProfile(0.92, 0.72, 0.72, 1.12),
    "spot": StudioProfile(1.12, 1.05, 0.42, 0.58),
    "strip": StudioProfile(0.98, 0.82, 0.54, 0.82, strip_anisotropy=1.0),
}
LIGHT_TYPE_SEEDS = {"softbox": 101, "spot": 211, "strip": 307}


def _to_float(mask: Image.Image) -> np.ndarray:
    return np.asarray(mask, dtype=np.float32) / 255.0


def _from_float(alpha: np.ndarray) -> Image.Image:
    return Image.fromarray(np.clip(alpha * 255.0, 0, 255).astype(np.uint8), mode="L")


def _alpha_to_rgba(alpha: Image.Image, context: ShadowRenderContext) -> Image.Image:
    shadow = Image.new("RGBA", alpha.size, (*context.paint.rgb, 0))
    shadow.putalpha(alpha)
    return shadow


def _smoothstep(edge0: float, edge1: float, value: np.ndarray) -> np.ndarray:
    if edge1 <= edge0:
        return (value >= edge1).astype(np.float32)
    t = np.clip((value - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _vertical_profile(mask: Image.Image) -> tuple[np.ndarray, tuple[int, int, int, int] | None]:
    arr = _to_float(mask)
    ys, xs = np.where(arr > 0.02)
    if len(xs) == 0 or len(ys) == 0:
        return np.zeros_like(arr, dtype=np.float32), None

    bbox = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    denom = max(bbox[3] - bbox[1] - 1, 1)
    row = (np.arange(mask.height, dtype=np.float32)[:, None] - bbox[1]) / float(denom)
    vertical = np.broadcast_to(np.clip(row, 0.0, 1.0), arr.shape).copy()
    return vertical, bbox


def _weighted_source(mask: Image.Image, kind: str) -> Image.Image:
    alpha = _to_float(mask)
    vertical, bbox = _vertical_profile(mask)
    if bbox is None:
        return mask

    if kind == "contact":
        weight = 0.18 + 0.82 * _smoothstep(0.52, 1.0, vertical)
    elif kind == "height":
        weight = 0.78 + 0.22 * (1.0 - vertical)
    else:
        weight = np.ones_like(alpha, dtype=np.float32)
    return _from_float(np.clip(alpha * weight, 0.0, 1.0))


def _shadow_vector_from_light(x: float, y: float) -> ShadowVector:
    sx = -float(x)
    sy = -float(y)
    length = math.hypot(sx, sy)
    if length < 1e-4:
        return ShadowVector(0.0, 1.0)
    return ShadowVector(sx / length, sy / length)


def _angle_from_shadow_vector(vector: ShadowVector) -> float:
    return math.degrees(math.atan2(vector.x, -vector.y)) % 360.0


def _spread_mask(mask: Image.Image, spread: float) -> Image.Image:
    radius = int(round(max(0.0, spread)))
    if radius <= 0:
        return mask
    kernel = radius * 2 + 1
    if kernel % 2 == 0:
        kernel += 1
    return mask.filter(ImageFilter.MaxFilter(kernel))


def _render_offset_layer(
    source: Image.Image,
    vector: ShadowVector,
    *,
    distance: float,
    blur: float,
) -> Image.Image:
    dx = int(round(distance * vector.x))
    dy = int(round(distance * vector.y))
    shifted = paste_offset(source, dx, dy)
    if blur > 0:
        shifted = shifted.filter(ImageFilter.GaussianBlur(blur))
    return shifted


def _strip_smear(mask: Image.Image, vector: ShadowVector, radius: float) -> Image.Image:
    if radius <= 0:
        return mask

    perp = ShadowVector(-vector.y, vector.x)
    offsets = (-1.0, -0.5, 0.0, 0.5, 1.0)
    weights = (0.16, 0.28, 0.42, 0.28, 0.16)
    alpha = np.zeros((mask.height, mask.width), dtype=np.float32)
    for offset, weight in zip(offsets, weights):
        dx = int(round(perp.x * radius * offset))
        dy = int(round(perp.y * radius * offset))
        shifted = paste_offset(mask, dx, dy)
        alpha = accumulate_alpha(alpha, _to_float(shifted) * weight)
    return _from_float(alpha)


def _protected(layer: Image.Image, mask: Image.Image, *, strength: float, blur: float) -> Image.Image:
    if strength <= 0:
        return layer
    protect = mask
    if blur > 0:
        protect = protect.filter(ImageFilter.GaussianBlur(blur))
    lut = [int(max(0.0, min(255.0, 255.0 - value * strength))) for value in range(256)]
    return ImageChops.multiply(layer, protect.point(lut))


def _background_luminance(context: ShadowRenderContext) -> float:
    if context.background_rgb is None:
        return 0.86
    r, g, b = context.background_rgb
    return float((0.299 * r + 0.587 * g + 0.114 * b) / 255.0)


def _density_factor(context: ShadowRenderContext) -> float:
    bg_lum = min(max(_background_luminance(context), 0.0), 1.0)
    product_lum = min(max(float(context.luminance_value), 0.0), 1.0)
    bg_factor = min(max(1.18 - bg_lum * 0.18, 0.84), 1.22)
    product_factor = min(max(1.0 + (0.5 - product_lum) * 0.14, 0.93), 1.07)
    return bg_factor * product_factor


def _work_cap(context: ShadowRenderContext) -> int:
    if context.is_preview:
        return 460
    largest = max(context.canvas_size)
    if largest <= 1600:
        return 620
    if largest <= 2600:
        return 640
    return 620


def render_studio_2_5d(context: ShadowRenderContext) -> ShadowRenderResult:
    settings = context.settings
    empty = Image.new("RGBA", context.canvas_size, (0, 0, 0, 0))

    if settings.opacity <= 0:
        return ShadowRenderResult(empty, RenderDiagnostics("studio_2_5d", "studio_2_5d"))
    if not context.subject_mask_canvas.getbbox():
        return ShadowRenderResult(empty, RenderDiagnostics("studio_2_5d", "studio_2_5d"))

    scene = settings.lighting_scene
    light = scene.main
    profile = STUDIO_PROFILES.get(light.type, STUDIO_PROFILES["softbox"])
    vector = _shadow_vector_from_light(light.x, light.y)
    angle = _angle_from_shadow_vector(vector)

    scale_factor = max(float(context.scale_factor), 0.0)
    distance_setting = max(0.0, float(settings.distance) * scale_factor)
    blur_setting = max(0.0, float(settings.blur) * scale_factor)
    contact_setting = max(0.0, float(settings.contact_blur) * scale_factor)
    spread_setting = max(0.0, float(settings.spread) * scale_factor)
    light_distance = math.hypot(float(light.x), float(light.y))
    height = min(max(float(light.height), 0.0), 1.0)
    size = min(max(float(light.size), 0.0), 1.0)
    intensity = min(max(float(light.intensity), 0.0), 1.5)
    ambient = min(max(float(scene.ambient_intensity), 0.0), 1.0)

    cast_distance = distance_setting * (0.55 + light_distance * 0.50 + (1.0 - height) * 0.82)
    cast_blur = blur_setting * profile.softness * (0.44 + size * 1.05 + height * 0.20)
    contact_blur = contact_setting * (0.24 + size * 0.36)
    max_blur = max(cast_blur * 1.65, contact_blur * 1.2, spread_setting)

    roi = compute_shadow_roi(
        context.subject_mask_canvas,
        distance=cast_distance,
        max_blur=max_blur,
        angle=angle,
        canvas_size=context.canvas_size,
    )
    if roi.local_mask.width <= 0 or roi.local_mask.height <= 0:
        return ShadowRenderResult(empty, RenderDiagnostics("studio_2_5d", "studio_2_5d", roi=roi.box))

    work_mask, work_scale = resize_for_cap(roi.local_mask, _work_cap(context))
    scaled_distance = cast_distance * work_scale
    scaled_blur = cast_blur * work_scale
    scaled_contact_blur = contact_blur * work_scale
    scaled_spread = spread_setting * work_scale
    source_mask = _spread_mask(work_mask, scaled_spread)

    contact_source = _weighted_source(source_mask, "contact")
    height_source = _weighted_source(source_mask, "height")
    if profile.strip_anisotropy:
        height_source = _strip_smear(height_source, vector, max(1.0, scaled_blur * 0.38))

    shape = (work_mask.height, work_mask.width)
    contact_alpha = np.zeros(shape, dtype=np.float32)
    diffuse_alpha = np.zeros(shape, dtype=np.float32)
    opacity_scale = max(0.0, min(float(settings.opacity) / 100.0, 1.0))
    contact_energy = (0.34 * ambient + 0.86 * intensity) * profile.contact_gain
    directional_energy = intensity * profile.directional_gain
    ambient_energy = ambient * profile.ambient_gain

    hard_contact = _render_offset_layer(
        contact_source,
        vector,
        distance=scaled_distance * 0.025,
        blur=max(0.0, scaled_contact_blur * 0.36),
    )
    soft_contact = _render_offset_layer(
        contact_source,
        vector,
        distance=scaled_distance * 0.085,
        blur=max(0.0, scaled_contact_blur * 1.15 + scaled_blur * 0.06),
    )
    near_body = _render_offset_layer(
        source_mask,
        vector,
        distance=scaled_distance * 0.22,
        blur=max(0.0, scaled_blur * 0.55 + scaled_contact_blur * 0.10),
    )
    cast = _render_offset_layer(
        height_source,
        vector,
        distance=scaled_distance,
        blur=max(0.0, scaled_blur),
    )
    wash = _render_offset_layer(
        height_source,
        vector,
        distance=scaled_distance * 0.62,
        blur=max(0.0, scaled_blur * 1.72 + scaled_contact_blur * 0.08),
    )
    ambient_layer = _render_offset_layer(
        source_mask,
        vector,
        distance=scaled_distance * 0.03,
        blur=max(0.0, scaled_blur * 1.05 + scaled_contact_blur * 0.24),
    )

    contact_alpha = accumulate_alpha(contact_alpha, _to_float(hard_contact) * opacity_scale * contact_energy * 0.82)
    contact_alpha = accumulate_alpha(contact_alpha, _to_float(soft_contact) * opacity_scale * contact_energy * 0.48)

    near_body = _protected(near_body, work_mask, strength=0.10, blur=max(0.0, scaled_blur * 0.12))
    cast = _protected(cast, work_mask, strength=0.26, blur=max(0.0, scaled_blur * 0.18))
    wash = _protected(wash, work_mask, strength=0.34, blur=max(0.0, scaled_blur * 0.26))
    ambient_layer = _protected(ambient_layer, work_mask, strength=0.08, blur=max(0.0, scaled_blur * 0.10))

    diffuse_alpha = accumulate_alpha(diffuse_alpha, _to_float(ambient_layer) * opacity_scale * ambient_energy * 0.42)
    diffuse_alpha = accumulate_alpha(diffuse_alpha, _to_float(near_body) * opacity_scale * directional_energy * 0.34)
    diffuse_alpha = accumulate_alpha(diffuse_alpha, _to_float(cast) * opacity_scale * directional_energy * 0.46)
    diffuse_alpha = accumulate_alpha(diffuse_alpha, _to_float(wash) * opacity_scale * directional_energy * 0.18)

    density = _density_factor(context)
    contact_alpha = np.clip(contact_alpha * density, 0.0, 1.0)
    diffuse_alpha = np.clip(diffuse_alpha * density, 0.0, 1.0)
    diffuse_alpha = deterministic_noise_alpha(
        diffuse_alpha,
        work_mask,
        intensity_percent=settings.noise,
        settings_key=(
            settings.distance,
            settings.blur,
            settings.contact_blur,
            settings.opacity,
            settings.spread,
            int(round(light.x * 1000)),
            int(round(light.y * 1000)),
            int(round(height * 1000)),
            int(round(size * 1000)),
            int(round(intensity * 1000)),
            int(round(ambient * 1000)),
            LIGHT_TYPE_SEEDS.get(light.type, 0),
        ),
        bbox=work_mask.getbbox(),
    )
    roi_alpha = accumulate_alpha(contact_alpha, diffuse_alpha)

    alpha_image = _from_float(roi_alpha)
    if alpha_image.size != roi.local_mask.size:
        alpha_image = alpha_image.resize(roi.local_mask.size, Image.Resampling.BILINEAR)

    local_shadow = _alpha_to_rgba(alpha_image, context)
    shadow = Image.new("RGBA", context.canvas_size, (0, 0, 0, 0))
    shadow.paste(local_shadow, roi.origin, mask=alpha_image)

    return ShadowRenderResult(
        shadow=shadow,
        diagnostics=RenderDiagnostics(
            engine_requested="studio_2_5d",
            engine_used="studio_2_5d",
            fallback_used=False,
            roi=roi.box,
        ),
    )
