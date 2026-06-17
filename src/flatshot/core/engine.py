import os
import logging
import numpy as np
from PIL import Image, ImageFilter
from typing import Tuple, Optional
from flatshot.core.models import (
    SHADOW_ENGINE_LEGACY,
    SHADOW_ENGINE_REALISTIC_V2,
    SHADOW_ENGINE_STUDIO_2_5D,
    ShadowSettings,
    CurveData,
    normalize_shadow_settings,
)
from flatshot.core.scaling import build_subject_mask, calculate_subject_scale, find_subject_bbox
from flatshot.core.shadow.legacy import (
    crear_capa_ao,
    crear_capa_base,
    generar_ruido as legacy_generar_ruido,
    render_legacy,
)
from flatshot.core.shadow.realistic_v2 import render_realistic_v2
from flatshot.core.shadow.studio_2_5d import render_studio_2_5d
from flatshot.core.shadow.types import RenderDiagnostics, ShadowRenderContext, ShadowRenderResult

class ShadowEngine:

    @staticmethod
    def generar_ruido(width: int, height: int, intensidad: float) -> Optional[Image.Image]:
        return legacy_generar_ruido(width, height, intensidad)

    @staticmethod
    def _crear_capa_base(silueta: Image.Image, canvas_size: Tuple[int, int], offset: Tuple[int, int], blur: float, opacity: float, spread: float) -> Image.Image:
        return crear_capa_base(silueta, canvas_size, offset, blur, opacity, spread)

    @staticmethod
    def _crear_capa_ao(silueta: Image.Image, canvas_size: Tuple[int, int], blur_ref: float, intensity: float) -> Image.Image:
        return crear_capa_ao(silueta, canvas_size, blur_ref, intensity)

    @staticmethod
    def _calcular_factor_color(img_rgba: Image.Image) -> Tuple[float, float]:
        try:
            small = img_rgba.resize((50, 50), Image.Resampling.NEAREST)
            arr = np.array(small)
            alpha = arr[:, :, 3]
            mask = alpha > 20
            if not np.any(mask): return 1.0, 0.5
            
            rgb = arr[:, :, :3]; valid_rgb = rgb[mask]
            lum = 0.299 * valid_rgb[:, 0] + 0.587 * valid_rgb[:, 1] + 0.114 * valid_rgb[:, 2]
            
            median_lum = np.median(lum)
            lum_norm = median_lum / 255.0
            
            INTENSITY = 0.06 
            factor = 1.0 + (lum_norm - 0.5) * INTENSITY
            return factor, lum_norm
        except Exception:
            return 1.0, 0.5

    @staticmethod
    def _calcular_centro_masa(img_rgba: Image.Image) -> Tuple[int, int]:
        bbox = img_rgba.getbbox()
        if not bbox:
            return img_rgba.width // 2, img_rgba.height // 2
        
        cx = (bbox[0] + bbox[2]) // 2
        cy = (bbox[1] + bbox[3]) // 2
        return cx, cy

    @staticmethod
    def _odd_kernel(size: int, minimum: int = 1) -> int:
        """Normalize kernel size to an odd integer."""
        kernel = max(int(round(size)), minimum)
        if kernel % 2 == 0:
            kernel += 1
        return kernel

    @staticmethod
    def _apply_min_filter(mask: Image.Image, kernel_size: int, max_pass_kernel: int = 0) -> Image.Image:
        """
        Apply MinFilter with optional decomposition in smaller passes.
        This keeps preview responsive when large kernels are requested.
        """
        kernel = ShadowEngine._odd_kernel(kernel_size, minimum=3)
        pass_kernel = ShadowEngine._odd_kernel(max_pass_kernel, minimum=3) if max_pass_kernel else 0

        if not pass_kernel or kernel <= pass_kernel:
            return mask.filter(ImageFilter.MinFilter(size=kernel))

        filtered = mask
        remaining = kernel
        while remaining > pass_kernel:
            filtered = filtered.filter(ImageFilter.MinFilter(size=pass_kernel))
            remaining -= (pass_kernel - 1)

        if remaining > 1:
            filtered = filtered.filter(ImageFilter.MinFilter(size=remaining))
        return filtered

    @staticmethod
    def aplicar_efectos(original_rgba: Image.Image, settings: ShadowSettings, target_size: Tuple[int, int], scale_factor: float = 1.0, curve_data: Optional[CurveData] = None, is_preview: bool = False) -> Image.Image:
        final, _diagnostics = ShadowEngine._aplicar_efectos_with_diagnostics(
            original_rgba,
            settings,
            target_size,
            scale_factor=scale_factor,
            curve_data=curve_data,
            is_preview=is_preview,
        )
        return final

    @staticmethod
    def _aplicar_efectos_with_diagnostics(original_rgba: Image.Image, settings: ShadowSettings, target_size: Tuple[int, int], scale_factor: float = 1.0, curve_data: Optional[CurveData] = None, is_preview: bool = False) -> tuple[Image.Image, RenderDiagnostics]:
        settings = normalize_shadow_settings(settings, missing_engine=SHADOW_ENGINE_REALISTIC_V2)
        if original_rgba.mode != "RGBA":
            original_rgba = original_rgba.convert("RGBA")
        canvas_w, canvas_h = target_size
        padding_pct = settings.padding / 100.0
        safe_w = int(canvas_w * (1.0 - padding_pct))
        safe_h = int(canvas_h * (1.0 - padding_pct))
        
        bbox = find_subject_bbox(original_rgba)
        if bbox: original_trimmed = original_rgba.crop(bbox)
        else: original_trimmed = original_rgba

        color_scale_factor, lum_val = ShadowEngine._calcular_factor_color(original_trimmed)

        if settings.adaptive_zoom and curve_data:
            scale_result = calculate_subject_scale(
                original_trimmed,
                (safe_w, safe_h),
                curve_data,
                color_scale_factor=color_scale_factor,
            )
            new_w = scale_result.width
            new_h = scale_result.height
        else:
            ratio = min(safe_w / original_trimmed.width, safe_h / original_trimmed.height)
            new_w = int(original_trimmed.width * ratio)
            new_h = int(original_trimmed.height * ratio)

        scale_adjustment = getattr(settings, "scale_adjustment", 0)
        if scale_adjustment:
            local_scale = 1.0 + (scale_adjustment / 100.0)
            adjusted_w = max(1, int(round(new_w * local_scale)))
            adjusted_h = max(1, int(round(new_h * local_scale)))
            fit_ratio = min(safe_w / adjusted_w, safe_h / adjusted_h, 1.0)
            new_w = max(1, int(round(adjusted_w * fit_ratio)))
            new_h = max(1, int(round(adjusted_h * fit_ratio)))

        if original_trimmed.width == 0 or original_trimmed.height == 0:
            empty = Image.new("RGB", target_size, settings.bg_color)
            return empty, RenderDiagnostics(settings.shadow_engine, settings.shadow_engine)
        
        # Prepare subject for processing
        # Working at a reasonable resolution ensures speed and quality
        # In preview mode we use a smaller resolution for better interactivity
        max_work_w = 1200 if is_preview else 2000
        if original_trimmed.width > max_work_w:
            w_ratio = max_work_w / original_trimmed.width
            subject_working = original_trimmed.resize(
                (max_work_w, int(original_trimmed.height * w_ratio)), 
                Image.Resampling.BILINEAR
            )
        else:
            subject_working = original_trimmed.copy()

        # Apply silhouette contraction (erode alpha channel)
        if settings.contraction > 0:
            # Scale the kernel relative to the current working subject width vs preview width
            scaling_to_working = subject_working.width / max(new_w, 1)
            
            # FAST PREVIEW PATH: 
            # If the kernel is very large or we are in preview, we can downsample 
            # the alpha channel even more to speed up the filter, then upscale it back.
            if is_preview:
                # Downsample alpha for lightning fast filtering
                alpha_full = subject_working.split()[-1]
                preview_filter_w = min(600, alpha_full.width)
                ds_ratio = preview_filter_w / max(alpha_full.width, 1)
                ds_h = max(1, int(alpha_full.height * ds_ratio))

                if preview_filter_w != alpha_full.width:
                    alpha_ds = alpha_full.resize((preview_filter_w, ds_h), Image.Resampling.NEAREST)
                else:
                    alpha_ds = alpha_full
                
                # Adjust kernel for downsampled resolution
                k_size = int(round(settings.contraction * 2 * (preview_filter_w / max(new_w, 1)) + 1))
                k_size = ShadowEngine._odd_kernel(k_size, minimum=3)
                # Safety cap to prevent hangs on extreme scales
                k_size = min(k_size, 51)
                
                alpha_contracted_ds = ShadowEngine._apply_min_filter(alpha_ds, k_size, max_pass_kernel=21)
                if alpha_contracted_ds.size != alpha_full.size:
                    # Upscale back to work resolution with BILINEAR to keep edges smooth
                    alpha_contracted = alpha_contracted_ds.resize(alpha_full.size, Image.Resampling.BILINEAR)
                else:
                    alpha_contracted = alpha_contracted_ds
            else:
                # High quality path for export
                k_size = int(round(settings.contraction * 2 * scaling_to_working + 1))
                k_size = ShadowEngine._odd_kernel(k_size, minimum=3)
                k_size = min(k_size, 101)
                
                alpha = subject_working.split()[-1]
                alpha_contracted = ShadowEngine._apply_min_filter(alpha, k_size, max_pass_kernel=31)
            
            subject_working.putalpha(alpha_contracted)

        subject_resized = subject_working.resize((new_w, new_h), Image.Resampling.BICUBIC)
        
        cx, cy = ShadowEngine._calcular_centro_masa(subject_resized)
        opt_y = int(canvas_h * 0.015) 
        pos_x = (canvas_w // 2) - cx
        pos_y = ((canvas_h // 2) - opt_y) - cy

        subject_mask = build_subject_mask(subject_resized)
        paste_mask = subject_resized.getchannel("A")
        if paste_mask.getextrema()[0] >= 250:
            paste_mask = subject_mask

        silueta_canvas = Image.new("L", target_size, 0)
        silueta_canvas.paste(subject_mask, (pos_x, pos_y))

        render_context = ShadowRenderContext(
            settings=settings,
            canvas_size=target_size,
            scale_factor=scale_factor,
            subject_width=new_w,
            subject_mask_canvas=silueta_canvas,
            subject_mask_local=subject_mask,
            subject_position=(pos_x, pos_y),
            luminance_value=lum_val,
            background_rgb=None if settings.transparent_bg else settings.bg_color,
            is_preview=is_preview,
        )
        render_result = ShadowEngine._render_shadow(render_context)
        final_shadow = render_result.shadow
        diagnostics = render_result.diagnostics

        if settings.transparent_bg:
            final = Image.new("RGBA", target_size, (0,0,0,0))
            final.paste(final_shadow, (0, 0), mask=final_shadow)
            final.paste(subject_resized, (pos_x, pos_y), mask=paste_mask)
            return final, diagnostics

        bg = settings.bg_color
        final = Image.new("RGB", target_size, bg)
        final.paste(final_shadow, (0, 0), mask=final_shadow)
        final.paste(subject_resized, (pos_x, pos_y), mask=paste_mask)
        return final, diagnostics

    @staticmethod
    def _render_shadow(context: ShadowRenderContext) -> ShadowRenderResult:
        engine = context.settings.shadow_engine
        if engine == SHADOW_ENGINE_LEGACY:
            return render_legacy(context)

        try:
            if engine == SHADOW_ENGINE_STUDIO_2_5D:
                return render_studio_2_5d(context)
            return render_realistic_v2(context)
        except Exception as exc:
            if os.environ.get("FLATSHOT_SHADOW_STRICT") == "1":
                raise
            warning = f"{engine} failed; rendered legacy: {exc}"
            logging.warning("FlatShot shadow fallback: %s", warning)
            legacy_result = render_legacy(context)
            return ShadowRenderResult(
                shadow=legacy_result.shadow,
                diagnostics=RenderDiagnostics(
                    engine_requested=engine,
                    engine_used=SHADOW_ENGINE_LEGACY,
                    fallback_used=True,
                    warning=warning,
                ),
            )
