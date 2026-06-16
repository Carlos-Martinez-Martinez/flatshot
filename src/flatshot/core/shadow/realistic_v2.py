from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np
from PIL import Image, ImageChops, ImageFilter

from flatshot.core.shadow.compositing import (
    accumulate_alpha,
    alpha_to_shadow_rgba,
    apply_protection,
    deterministic_noise_alpha,
    from_float,
    smoothstep,
    to_float,
    vertical_profile,
)
from flatshot.core.shadow.geometry import (
    compute_shadow_roi,
    paste_offset,
    resize_for_cap,
    shadow_vector_from_angle,
)
from flatshot.core.shadow.types import (
    RenderDiagnostics,
    ShadowRenderContext,
    ShadowRenderResult,
)


HEIGHT_INFLUENCE = 0.25
PRODUCT_LUMINANCE_DENSITY_STRENGTH = 0.16


@dataclass(frozen=True)
class LayerSpec:
    name: str
    cap: int
    offset_factor: float
    blur_factor: float
    contact_blur_factor: float
    weight: float
    contact: bool = False
    height_weighted: bool = False
    protect_strength: float = 0.0
    protect_blur_factor: float = 0.0


LAYER_SPECS = (
    LayerSpec("contact_hard", 1600, 0.02, 0.00, 0.20, 0.88, contact=True, protect_strength=0.0, protect_blur_factor=0.00),
    LayerSpec("contact_soft", 1200, 0.08, 0.00, 0.82, 0.78, contact=True, protect_strength=0.04, protect_blur_factor=0.06),
    LayerSpec("ambient_volume", 900, 0.00, 1.25, 0.20, 0.50, protect_strength=0.06, protect_blur_factor=0.10),
    LayerSpec("near_body", 900, 0.22, 0.55, 0.18, 0.58, protect_strength=0.12, protect_blur_factor=0.14),
    LayerSpec("directional", 700, 1.00, 1.00, 0.12, 0.52, height_weighted=True, protect_strength=0.22, protect_blur_factor=0.22),
    LayerSpec("far_wash", 520, 0.70, 1.85, 0.10, 0.22, height_weighted=True, protect_strength=0.32, protect_blur_factor=0.30),
)


def _contact_source(mask_alpha: np.ndarray) -> np.ndarray:
    vertical, bbox = vertical_profile(mask_alpha)
    if bbox is None:
        return mask_alpha
    bottom_bias = smoothstep(0.58, 1.0, vertical)
    baseline = 0.10 + 0.90 * bottom_bias
    return np.clip(mask_alpha * baseline, 0.0, 1.0)


def _height_weighted_source(mask_alpha: np.ndarray) -> np.ndarray:
    vertical, bbox = vertical_profile(mask_alpha)
    if bbox is None:
        return mask_alpha
    height_map = 1.0 - vertical
    influence = min(max(HEIGHT_INFLUENCE, 0.15), 0.35)
    weight = (1.0 - influence) + influence * height_map
    return np.clip(mask_alpha * weight, 0.0, 1.0)


def _weighted_mask(mask: Image.Image, *, contact: bool) -> Image.Image:
    bbox = mask.getbbox()
    if not bbox:
        return mask
    h = mask.height
    denom = max(bbox[3] - bbox[1] - 1, 1)
    vertical = (np.arange(h, dtype=np.float32) - bbox[1]) / float(denom)
    vertical = np.clip(vertical, 0.0, 1.0)
    if contact:
        lower_falloff = smoothstep(0.35, 1.0, vertical)
        weights = 1.0 - 0.08 * lower_falloff
    else:
        influence = min(max(HEIGHT_INFLUENCE, 0.15), 0.35)
        weights = (1.0 - influence) + influence * (1.0 - vertical)
    gradient = Image.fromarray(
        np.clip(weights * 255.0, 0, 255).astype(np.uint8).reshape(h, 1),
        mode="L",
    ).resize(mask.size, Image.Resampling.BILINEAR)
    return ImageChops.multiply(mask, gradient)


def _local_background_luminance(
    context: ShadowRenderContext,
    roi_box: tuple[int, int, int, int],
    roi_mask: Image.Image,
    shadow_alpha: np.ndarray,
) -> float:
    if context.background_rgb is None:
        return 0.5

    protect = roi_mask.filter(ImageFilter.GaussianBlur(max(1.0, min(roi_mask.size) * 0.012)))
    protect_arr = to_float(protect)
    valid = (shadow_alpha > 0.01) & (protect_arr < 0.08)
    if int(valid.sum()) < 32:
        return 0.5

    r, g, b = context.background_rgb
    return float((0.299 * r + 0.587 * g + 0.114 * b) / 255.0)


def _product_luminance_shadow_factor(luminance: float) -> float:
    luminance = min(max(float(luminance), 0.0), 1.0)
    factor = 1.0 + (0.5 - luminance) * PRODUCT_LUMINANCE_DENSITY_STRENGTH
    return min(max(factor, 0.92), 1.08)


def _render_layer(
    roi_mask: Image.Image,
    spec: LayerSpec,
    *,
    distance: float,
    angle: int,
    blur: float,
    contact_blur: float,
    spread: float,
) -> Image.Image:
    layer_mask, scale = resize_for_cap(roi_mask, spec.cap)

    if spec.contact:
        source_mask = _weighted_mask(layer_mask, contact=True)
    elif spec.height_weighted:
        source_mask = _weighted_mask(layer_mask, contact=False)
    else:
        source_mask = layer_mask
    vector = shadow_vector_from_angle(angle)
    dx = int(round(distance * spec.offset_factor * vector.x * scale))
    dy = int(round(distance * spec.offset_factor * vector.y * scale))
    shifted = paste_offset(source_mask, dx, dy)

    layer_blur = max(
        0.0,
        (blur * spec.blur_factor + contact_blur * spec.contact_blur_factor + spread * 0.35) * scale,
    )
    if layer_blur > 0:
        shifted = shifted.filter(ImageFilter.GaussianBlur(layer_blur))

    if shifted.size != roi_mask.size:
        shifted = shifted.resize(roi_mask.size, Image.Resampling.BILINEAR)
    return shifted


def render_realistic_v2(context: ShadowRenderContext) -> ShadowRenderResult:
    settings = context.settings
    canvas_w, canvas_h = context.canvas_size
    empty = Image.new("RGBA", context.canvas_size, (0, 0, 0, 0))

    if settings.opacity <= 0:
        return ShadowRenderResult(
            shadow=empty,
            diagnostics=RenderDiagnostics("realistic_v2", "realistic_v2"),
        )

    if not context.subject_mask_canvas.getbbox():
        return ShadowRenderResult(
            shadow=empty,
            diagnostics=RenderDiagnostics("realistic_v2", "realistic_v2"),
        )

    scale_factor = max(float(context.scale_factor), 0.0)
    distance = max(0.0, float(settings.distance) * scale_factor)
    blur = max(0.0, float(settings.blur) * scale_factor)
    contact_blur = max(0.0, float(settings.contact_blur) * scale_factor)
    spread = max(0.0, float(settings.spread) * scale_factor)
    max_blur = max(blur * 1.55, contact_blur * 0.72, spread)

    roi = compute_shadow_roi(
        context.subject_mask_canvas,
        distance=distance,
        max_blur=max_blur,
        angle=settings.angle,
        canvas_size=context.canvas_size,
    )
    if roi.local_mask.width <= 0 or roi.local_mask.height <= 0:
        return ShadowRenderResult(
            shadow=empty,
            diagnostics=RenderDiagnostics("realistic_v2", "realistic_v2", roi=roi.box),
        )

    work_cap = 1200 if max(context.canvas_size) < 2000 else 620
    work_mask, work_scale = resize_for_cap(roi.local_mask, work_cap)
    scaled_distance = distance * work_scale
    scaled_blur = blur * work_scale
    scaled_contact_blur = contact_blur * work_scale
    scaled_spread = spread * work_scale

    contact_alpha = np.zeros((work_mask.height, work_mask.width), dtype=np.float32)
    diffuse_alpha = np.zeros((work_mask.height, work_mask.width), dtype=np.float32)
    opacity_scale = max(0.0, min(float(settings.opacity) / 100.0, 1.0))

    for spec in LAYER_SPECS:
        layer_mask = _render_layer(
            work_mask,
            spec,
            distance=scaled_distance,
            angle=settings.angle,
            blur=scaled_blur,
            contact_blur=scaled_contact_blur,
            spread=scaled_spread,
        )
        layer_mask = apply_protection(
            layer_mask,
            work_mask,
            strength=spec.protect_strength,
            blur=max(0.0, (scaled_blur * spec.protect_blur_factor + scaled_contact_blur * 0.08)),
        )

        layer = to_float(layer_mask) * opacity_scale * spec.weight
        if spec.contact:
            contact_alpha = accumulate_alpha(contact_alpha, layer)
        else:
            diffuse_alpha = accumulate_alpha(diffuse_alpha, layer)

    roi_alpha = accumulate_alpha(contact_alpha, diffuse_alpha)
    bg_lum = _local_background_luminance(context, roi.box, work_mask, roi_alpha)
    bg_factor = min(max(1.22 - bg_lum * 0.22, 0.78), 1.28)
    density = bg_factor * _product_luminance_shadow_factor(context.luminance_value)
    contact_alpha = np.clip(contact_alpha * density, 0.0, 1.0)
    diffuse_alpha = np.clip(diffuse_alpha * density, 0.0, 1.0)

    diffuse_alpha = deterministic_noise_alpha(
        diffuse_alpha,
        work_mask,
        intensity_percent=settings.noise,
        settings_key=(
            settings.angle,
            settings.distance,
            settings.blur,
            settings.contact_blur,
            settings.opacity,
            settings.spread,
        ),
        bbox=work_mask.getbbox(),
    )
    roi_alpha = accumulate_alpha(contact_alpha, diffuse_alpha)

    alpha_image = from_float(roi_alpha)
    if alpha_image.size != roi.local_mask.size:
        alpha_image = alpha_image.resize(roi.local_mask.size, Image.Resampling.BILINEAR)
        roi_alpha = to_float(alpha_image)

    local_shadow = alpha_to_shadow_rgba(roi_alpha, context.paint)
    shadow = Image.new("RGBA", context.canvas_size, (0, 0, 0, 0))
    shadow.paste(local_shadow, roi.origin, mask=local_shadow)

    return ShadowRenderResult(
        shadow=shadow,
        diagnostics=RenderDiagnostics(
            engine_requested="realistic_v2",
            engine_used="realistic_v2",
            fallback_used=False,
            roi=roi.box,
        ),
    )
