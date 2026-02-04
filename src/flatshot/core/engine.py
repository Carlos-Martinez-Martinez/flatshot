import math
import numpy as np
from PIL import Image, ImageFilter, ImageChops
from typing import Tuple, Optional
from flatshot.core.models import ShadowSettings, CurveData

class ShadowEngine:
    _noise_cache = {}

    @staticmethod
    def generar_ruido(width: int, height: int, intensidad: float) -> Optional[Image.Image]:
        if intensidad <= 0 or width < 1 or height < 1: return None
        key = (width, height, round(intensidad, 2))
        if key in ShadowEngine._noise_cache:
            return ShadowEngine._noise_cache[key]

        sigma = intensidad * 255.0
        noise = np.random.normal(128, sigma, (height, width)).astype(np.uint8)
        img = Image.fromarray(noise, mode='L')
        
        if len(ShadowEngine._noise_cache) > 20: ShadowEngine._noise_cache.clear()
        ShadowEngine._noise_cache[key] = img
        return img

    @staticmethod
    def _crear_capa_base(silueta: Image.Image, canvas_size: Tuple[int, int], offset: Tuple[int, int], blur: float, opacity: float, spread: float) -> Image.Image:
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

    @staticmethod
    def _crear_capa_ao(silueta: Image.Image, canvas_size: Tuple[int, int], blur_ref: float, intensity: float) -> Image.Image:
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
        except: return 1.0, 0.5

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
        canvas_w, canvas_h = target_size
        padding_pct = settings.padding / 100.0
        safe_w = int(canvas_w * (1.0 - padding_pct))
        safe_h = int(canvas_h * (1.0 - padding_pct))
        
        bbox = original_rgba.getbbox()
        if bbox: original_trimmed = original_rgba.crop(bbox)
        else: original_trimmed = original_rgba

        color_scale_factor, lum_val = ShadowEngine._calcular_factor_color(original_trimmed)

        if settings.adaptive_zoom and curve_data:
            real_w, real_h = original_trimmed.size
            if real_w > 0 and real_h > 0:
                aspect_ratio = real_w / real_h
                
                # Calculate the scale that would fit the image within safe bounds
                scale_fit = min(safe_w / real_w, safe_h / real_h)
                
                # Target visual area as percentage of safe area
                # A "regular" product (AR ~0.85) should fill about 50% of safe area
                safe_area = safe_w * safe_h
                target_fill = 0.50  # Base target: 50% of safe area
                
                # Get curve adjustment factor
                adj = np.interp(aspect_ratio, curve_data.xp, curve_data.fp)
                
                # Calculate current area if scaled to fit
                fitted_w = real_w * scale_fit
                fitted_h = real_h * scale_fit
                fitted_area = fitted_w * fitted_h
                
                # Calculate scale needed to hit target area (adjusted by curve)
                target_area = safe_area * target_fill * adj
                area_scale = np.sqrt(target_area / (real_w * real_h))
                
                # Use the smaller of: area-based scale or fit scale (to not exceed bounds)
                final_scale = min(area_scale, scale_fit) * color_scale_factor
                
                # Safety clamp: ensure we don't exceed safe bounds
                prop_w = real_w * final_scale
                prop_h = real_h * final_scale
                if prop_w > safe_w: final_scale = safe_w / real_w
                if prop_h > safe_h: final_scale = min(final_scale, safe_h / real_h)
                
                new_w = max(1, int(real_w * final_scale))
                new_h = max(1, int(real_h * final_scale))
            else: 
                new_w, new_h = 100, 100
        else:
            ratio = min(safe_w / original_trimmed.width, safe_h / original_trimmed.height)
            new_w = int(original_trimmed.width * ratio)
            new_h = int(original_trimmed.height * ratio)

        if original_trimmed.width == 0: return Image.new("RGB", target_size, (230,230,230))
        
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

        silueta_canvas = Image.new("L", target_size, 0)
        silueta_canvas.paste(subject_resized.split()[-1], (pos_x, pos_y))

        shadow_density_mult = 1.7 - (lum_val * 0.8)
        
        s_dist = settings.distance * scale_factor
        angle = math.radians(settings.angle)
        vx = math.sin(angle); vy = -math.cos(angle) 
        
        base_alpha = settings.opacity * 2.55 * shadow_density_mult
        
        blur = settings.blur * scale_factor
        c_blur = max(1, settings.contact_blur * scale_factor)

        l_vol = ShadowEngine._crear_capa_base(silueta_canvas, target_size, (0, 0), max(10, blur*1.5), base_alpha*0.4, max(5, int(new_w*0.025)))
        l_dir = ShadowEngine._crear_capa_base(silueta_canvas, target_size, (int(s_dist*vx), int(s_dist*vy)), blur, base_alpha*0.7, 0)
        
        core_int = 1.0 - (max(0, lum_val - 0.2) * 0.5) 
        l_soft = ShadowEngine._crear_capa_base(silueta_canvas, target_size, (int(s_dist*0.1*vx), int(s_dist*0.1*vy)), c_blur, min(255, base_alpha*0.8), 0)
        l_core = ShadowEngine._crear_capa_base(silueta_canvas, target_size, (0, int(2*scale_factor)), max(1, c_blur*0.25), min(255, base_alpha*1.5*core_int), 0)
        
        l_ao = ShadowEngine._crear_capa_ao(silueta_canvas, target_size, blur, 0.25 * shadow_density_mult)

        final_shadow = Image.new("RGBA", target_size, (0,0,0,0))
        final_shadow.paste(l_vol, (0,0), mask=l_vol)
        final_shadow.paste(l_dir, (0,0), mask=l_dir)
        final_shadow.paste(l_soft, (0,0), mask=l_soft)
        final_shadow.paste(l_core, (0,0), mask=l_core)
        final_shadow.paste(l_ao, (0,0), mask=l_ao)

        if settings.noise > 0:
            nm = ShadowEngine.generar_ruido(canvas_w, canvas_h, settings.noise/100.0)
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

        if settings.transparent_bg:
            final = Image.new("RGBA", target_size, (0,0,0,0))
            final.paste(final_shadow, (0, 0), mask=final_shadow)
            final.paste(subject_resized, (pos_x, pos_y), mask=subject_resized)
            return final
        else:
            bg = settings.bg_color
            final = Image.new("RGB", target_size, bg)
            final.paste(final_shadow, (0, 0), mask=final_shadow)
            final.paste(subject_resized, (pos_x, pos_y), mask=subject_resized)
            return final
