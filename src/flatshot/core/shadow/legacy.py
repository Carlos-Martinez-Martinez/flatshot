from __future__ import annotations

from typing import Optional, Tuple

import numpy as np
from PIL import Image, ImageChops, ImageFilter

from flatshot.core.shadow.types import (
    RenderDiagnostics,
    ShadowRenderContext,
    ShadowRenderResult,
)


_noise_cache = {}


def generar_ruido(width: int, height: int, intensidad: float) -> Optional[Image.Image]:
    if intensidad <= 0 or width < 1 or height < 1: return None
    key = (width, height, round(intensidad, 2))
    if key in _noise_cache:
        return _noise_cache[key]

    sigma = intensidad * 255.0
    noise = np.random.normal(128, sigma, (height, width)).astype(np.uint8)
    img = Image.fromarray(noise, mode='L')

    if len(_noise_cache) > 20: _noise_cache.clear()
    _noise_cache[key] = img
    return img


def crear_capa_base(silueta: Image.Image, canvas_size: Tuple[int, int], offset: Tuple[int, int], blur: float, opacity: float, spread: float) -> Image.Image:
    if opacity <= 0: return Image.new("RGBA", canvas_size, (0,0,0,0))
    spread_radius = int(spread + 0.5)

    mask_base = silueta
    if spread_radius > 0:
        k_size = spread_radius * 2 + 1
        mask_base = mask_base.filter(ImageFilter.MaxFilter(size=k_size))

    shadow_layer = Image.new("RGBA", canvas_size, (0,0,0,0))
    alpha_val = min(255, int(opacity))
    solid_black = Image.new("RGBA", canvas_size, (0,0,0, alpha_val))

    if blur > 0:
        mask_blur = mask_base.filter(ImageFilter.GaussianBlur(blur))
    else: mask_blur = mask_base

    temp_mask = Image.new("L", canvas_size, 0)
    temp_mask.paste(mask_blur, offset)
    shadow_layer.paste(solid_black, (0,0), mask=temp_mask)
    return shadow_layer


def crear_capa_ao(silueta: Image.Image, canvas_size: Tuple[int, int], blur_ref: float, intensity: float) -> Image.Image:
    if intensity <= 0: return Image.new("RGBA", canvas_size, (0,0,0,0))

    ao_blur = blur_ref * 1.0
    mask_blur = silueta.filter(ImageFilter.GaussianBlur(ao_blur))

    threshold = 90
    lut = []
    for p in range(256):
        if p < threshold: lut.append(0)
        else: lut.append(min(255, int((p - threshold) * 2.5)))

    mask_ao = mask_blur.point(lut)
    mask_ao = mask_ao.filter(ImageFilter.GaussianBlur(ao_blur * 0.3))

    ao_layer = Image.new("RGBA", canvas_size, (0,0,0,0))
    alpha_val = min(255, int(255 * intensity))
    solid_black = Image.new("RGBA", canvas_size, (0,0,0, alpha_val))

    ao_layer.paste(solid_black, (0,0), mask=mask_ao)
    return ao_layer


def render_legacy(context: ShadowRenderContext) -> ShadowRenderResult:
    settings = context.settings
    target_size = context.canvas_size
    scale_factor = context.scale_factor
    new_w = context.subject_width
    lum_val = context.luminance_value
    silueta_canvas = context.subject_mask_canvas

    import math

    shadow_density_mult = 1.7 - (lum_val * 0.8)

    s_dist = settings.distance * scale_factor
    angle = math.radians(settings.angle)
    vx = math.sin(angle); vy = -math.cos(angle)

    base_alpha = settings.opacity * 2.55 * shadow_density_mult

    blur = settings.blur * scale_factor
    c_blur = max(1, settings.contact_blur * scale_factor)

    l_vol = crear_capa_base(silueta_canvas, target_size, (0, 0), max(10, blur*1.5), base_alpha*0.4, max(5, int(new_w*0.025)))
    l_dir = crear_capa_base(silueta_canvas, target_size, (int(s_dist*vx), int(s_dist*vy)), blur, base_alpha*0.7, 0)

    core_int = 1.0 - (max(0, lum_val - 0.2) * 0.5)
    l_soft = crear_capa_base(silueta_canvas, target_size, (int(s_dist*0.1*vx), int(s_dist*0.1*vy)), c_blur, min(255, base_alpha*0.8), 0)
    l_core = crear_capa_base(silueta_canvas, target_size, (0, int(2*scale_factor)), max(1, c_blur*0.25), min(255, base_alpha*1.5*core_int), 0)

    l_ao = crear_capa_ao(silueta_canvas, target_size, blur, 0.25 * shadow_density_mult)

    final_shadow = Image.new("RGBA", target_size, (0,0,0,0))
    final_shadow.paste(l_vol, (0,0), mask=l_vol)
    final_shadow.paste(l_dir, (0,0), mask=l_dir)
    final_shadow.paste(l_soft, (0,0), mask=l_soft)
    final_shadow.paste(l_core, (0,0), mask=l_core)
    final_shadow.paste(l_ao, (0,0), mask=l_ao)

    if settings.noise > 0:
        nm = generar_ruido(target_size[0], target_size[1], settings.noise/100.0)
        if nm:
            nl = Image.new("RGBA", target_size, (0,0,0,0)); nl.paste(nm, (0,0))
            final_shadow = ImageChops.multiply(final_shadow, nl.convert('RGBA'))

    fusion_orig = int(settings.fusion * scale_factor)
    if fusion_orig > 0:
        bleed_factor = 1.0 - (lum_val * 0.6)
        dynamic_fusion = max(1, int(fusion_orig * bleed_factor))
        mask_protectora = silueta_canvas.filter(ImageFilter.MinFilter(size=dynamic_fusion * 2 + 1))
        mask_cutout = mask_protectora.point(lambda p: 255 if p > 10 else 0)
        final_shadow = Image.composite(Image.new("RGBA", target_size, (0,0,0,0)), final_shadow, mask_cutout)

    return ShadowRenderResult(
        shadow=final_shadow,
        diagnostics=RenderDiagnostics(
            engine_requested="legacy",
            engine_used="legacy",
            fallback_used=False,
        ),
    )
