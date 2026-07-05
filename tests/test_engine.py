"""
Tests for FlatShot Core Engine
"""
import pytest
import numpy as np
from PIL import Image

from flatshot.core.engine import ShadowEngine
from flatshot.core.models import ShadowSettings, CurveData
from flatshot.core.shadow.geometry import shadow_vector_from_angle
from flatshot.core.shadow.realistic_v2 import render_realistic_v2
from flatshot.core.shadow.studio_2_5d import render_studio_2_5d
from flatshot.core.shadow.types import ShadowRenderContext


def _alpha_centroid(image: Image.Image) -> tuple[float, float]:
    alpha = np.asarray(image.getchannel("A"), dtype=np.float32)
    total = float(alpha.sum())
    assert total > 0
    ys, xs = np.indices(alpha.shape, dtype=np.float32)
    return float((xs * alpha).sum() / total), float((ys * alpha).sum() / total)


def _shadow_context(settings: ShadowSettings, luminance_value: float = 0.5) -> ShadowRenderContext:
    mask = Image.new("L", (220, 220), 0)
    mask.paste(255, (80, 70, 140, 150))
    return ShadowRenderContext(
        settings=settings,
        canvas_size=mask.size,
        scale_factor=1.0,
        subject_width=60,
        subject_mask_canvas=mask,
        subject_mask_local=mask.crop((80, 70, 140, 150)),
        subject_position=(80, 70),
        luminance_value=luminance_value,
        background_rgb=(230, 230, 230),
    )


class TestNoiseGeneration:
    """Tests for noise generation."""
    
    def test_generar_ruido_returns_correct_dimensions(self):
        """Test that generated noise has correct dimensions."""
        noise = ShadowEngine.generar_ruido(100, 200, 0.1)
        assert noise is not None
        assert noise.size == (100, 200)
        assert noise.mode == 'L'
    
    def test_generar_ruido_returns_none_for_zero_intensity(self):
        """Test that zero intensity returns None."""
        noise = ShadowEngine.generar_ruido(100, 200, 0)
        assert noise is None
    
    def test_generar_ruido_cache_works(self):
        """Test that caching works for same parameters."""
        noise1 = ShadowEngine.generar_ruido(50, 50, 0.1)
        noise2 = ShadowEngine.generar_ruido(50, 50, 0.1)
        assert noise1 is noise2  # Same object from cache
    
    def test_generar_ruido_different_params_not_cached(self):
        """Test that different parameters get different results."""
        noise1 = ShadowEngine.generar_ruido(50, 50, 0.1)
        noise2 = ShadowEngine.generar_ruido(60, 60, 0.1)
        assert noise1 is not noise2


class TestColorFactor:
    """Tests for color factor calculation."""
    
    def test_calcular_factor_color_white_image(self):
        """Test factor for white/light image."""
        # Create a white product on transparent background
        img = Image.new("RGBA", (100, 100), (255, 255, 255, 255))
        factor, lum = ShadowEngine._calcular_factor_color(img)
        
        assert factor > 1.0  # Light images get factor > 1
        assert lum > 0.5  # High luminance
    
    def test_calcular_factor_color_black_image(self):
        """Test factor for black/dark image."""
        img = Image.new("RGBA", (100, 100), (0, 0, 0, 255))
        factor, lum = ShadowEngine._calcular_factor_color(img)
        
        assert factor < 1.0  # Dark images get factor < 1
        assert lum < 0.5  # Low luminance
    
    def test_calcular_factor_color_transparent_image(self):
        """Test factor for fully transparent image."""
        img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        factor, lum = ShadowEngine._calcular_factor_color(img)
        
        # Should return defaults for transparent images
        assert factor == 1.0
        assert lum == 0.5


class TestAplicarEfectos:
    """Tests for the main effect application."""
    
    @pytest.fixture
    def sample_image(self):
        """Create a sample test image."""
        # Create a simple colored rectangle on transparent background
        img = Image.new("RGBA", (200, 300), (0, 0, 0, 0))
        # Draw a "product" in the center
        product = Image.new("RGBA", (100, 200), (128, 128, 128, 255))
        img.paste(product, (50, 50), product)
        return img
    
    @pytest.fixture
    def default_settings(self):
        """Create default shadow settings."""
        return ShadowSettings()
    
    @pytest.fixture
    def default_curve(self):
        """Create default curve data."""
        return CurveData(
            xp=[0.0, 0.35, 0.60, 0.85, 1.10, 1.40, 3.0],
            fp=[0.80, 0.80, 0.90, 1.00, 0.95, 0.90, 0.90]
        )
    
    def test_aplicar_efectos_returns_correct_size(self, sample_image, default_settings, default_curve):
        """Test that output has correct target size."""
        target_size = (400, 600)
        result = ShadowEngine.aplicar_efectos(
            sample_image, default_settings, target_size, 
            scale_factor=1.0, curve_data=default_curve
        )
        
        assert result.size == target_size
    
    def test_aplicar_efectos_rgb_mode_without_transparency(self, sample_image, default_settings, default_curve):
        """Test that output is RGB when transparency is disabled."""
        default_settings.transparent_bg = False
        target_size = (400, 600)
        
        result = ShadowEngine.aplicar_efectos(
            sample_image, default_settings, target_size,
            scale_factor=1.0, curve_data=default_curve
        )
        
        assert result.mode == "RGB"
    
    def test_aplicar_efectos_rgba_mode_with_transparency(self, sample_image, default_settings, default_curve):
        """Test that output is RGBA when transparency is enabled."""
        default_settings.transparent_bg = True
        target_size = (400, 600)
        
        result = ShadowEngine.aplicar_efectos(
            sample_image, default_settings, target_size,
            scale_factor=1.0, curve_data=default_curve
        )
        
        assert result.mode == "RGBA"
    
    def test_aplicar_efectos_with_adaptive_zoom(self, sample_image, default_settings, default_curve):
        """Test adaptive zoom processing."""
        default_settings.adaptive_zoom = True
        target_size = (400, 600)
        
        result = ShadowEngine.aplicar_efectos(
            sample_image, default_settings, target_size,
            scale_factor=1.0, curve_data=default_curve
        )
        
        assert result is not None
        assert isinstance(result, Image.Image)
    
    def test_aplicar_efectos_without_adaptive_zoom(self, sample_image, default_settings, default_curve):
        """Test processing without adaptive zoom."""
        default_settings.adaptive_zoom = False
        target_size = (400, 600)
        
        result = ShadowEngine.aplicar_efectos(
            sample_image, default_settings, target_size,
            scale_factor=1.0, curve_data=default_curve
        )
        
        assert result is not None
        assert isinstance(result, Image.Image)

    def test_aplicar_efectos_with_contraction_preview(self, sample_image, default_settings, default_curve):
        """Preview mode should support contraction without errors."""
        default_settings.contraction = 5
        target_size = (300, 400)

        result = ShadowEngine.aplicar_efectos(
            sample_image, default_settings, target_size,
            scale_factor=0.25, curve_data=default_curve, is_preview=True
        )

        assert result.size == target_size
        assert isinstance(result, Image.Image)

    def test_export_resize_keeps_detail_for_large_subjects(self):
        """Full export should not pre-downsample detailed source pixels before final resize."""
        subject_w, subject_h = 3000, 1000
        canvas = Image.new("RGBA", (3300, 1300), (0, 0, 0, 0))
        x = np.arange(subject_w, dtype=np.uint16)
        y = np.arange(subject_h, dtype=np.uint16)[:, None]
        pattern = (((x // 3 + y // 3) % 2) * 255).astype(np.uint8)
        rgb = np.dstack(
            [
                pattern,
                np.roll(pattern, 1, axis=1),
                np.roll(pattern, 2, axis=0),
            ]
        )
        alpha = np.full((subject_h, subject_w), 255, dtype=np.uint8)
        canvas.alpha_composite(Image.fromarray(np.dstack([rgb, alpha]), "RGBA"), (150, 150))
        settings = ShadowSettings(
            adaptive_zoom=False,
            padding=0,
            transparent_bg=True,
            opacity=0,
            blur=0,
            contact_blur=0,
            noise=0,
        )

        result = ShadowEngine.aplicar_efectos(canvas, settings, (2400, 800))
        subject = result.crop(result.getbbox()).convert("RGB")
        arr = np.asarray(subject, dtype=np.int16)
        horizontal_detail = float(np.mean(np.abs(arr[:, 1:, :] - arr[:, :-1, :])))

        assert horizontal_detail > 75.0

    def test_export_downscale_uses_lanczos_for_subject_detail(self):
        size = 101
        x = np.arange(size, dtype=np.uint16)
        y = np.arange(size, dtype=np.uint16)[:, None]
        pattern = ((x * 3 + y * 5 + ((x // 2 + y // 3) % 2) * 90) % 256).astype(np.uint8)
        rgb = np.dstack(
            [
                pattern,
                np.roll(pattern, 3, axis=1),
                np.roll(pattern, 5, axis=0),
            ]
        )
        source = Image.fromarray(
            np.dstack([rgb, np.full((size, size), 255, dtype=np.uint8)]),
            "RGBA",
        )
        settings = ShadowSettings(
            adaptive_zoom=False,
            padding=0,
            transparent_bg=True,
            opacity=0,
            blur=0,
            contact_blur=0,
            noise=0,
        )

        result = ShadowEngine.aplicar_efectos(source, settings, (67, 67))
        subject = result.crop(result.getbbox()).convert("RGB")
        bicubic = source.resize(result.size, Image.Resampling.BICUBIC).convert("RGB")
        lanczos = source.resize(result.size, Image.Resampling.LANCZOS).convert("RGB")

        subject_arr = np.asarray(subject, dtype=np.int16)

        def best_delta(reference: Image.Image) -> float:
            max_left = reference.width - subject.width
            max_top = reference.height - subject.height
            deltas = []
            for left in range(max_left + 1):
                for top in range(max_top + 1):
                    crop = reference.crop((left, top, left + subject.width, top + subject.height))
                    deltas.append(
                        float(np.mean(np.abs(subject_arr - np.asarray(crop, dtype=np.int16))))
                    )
            return min(deltas)

        bicubic_delta = best_delta(bicubic)
        lanczos_delta = best_delta(lanczos)

        assert lanczos_delta < bicubic_delta

    def test_legacy_golden_synthetic_output(self):
        """Legacy renderer keeps the established visual output within tolerance."""
        img = Image.new("RGBA", (80, 120), (0, 0, 0, 0))
        img.paste(Image.new("RGBA", (40, 70), (128, 128, 128, 255)), (20, 25))
        settings = ShadowSettings(
            shadow_engine="legacy",
            adaptive_zoom=False,
            angle=180,
            distance=18,
            blur=12,
            opacity=35,
            noise=0,
            contact_blur=6,
            padding=10,
        )

        result = ShadowEngine.aplicar_efectos(img, settings, (180, 240))
        arr = np.asarray(result, dtype=np.int64)

        assert result.mode == "RGB"
        assert abs(int(arr.sum()) - 22290180) <= 5000

    @pytest.mark.parametrize(
        ("engine_name", "expected_sum"),
        [
            ("realistic_v2", 22149618),
            ("studio_2_5d", 22080705),
        ],
    )
    def test_modern_shadow_engines_golden_synthetic_output(self, engine_name, expected_sum):
        """Modern renderers keep small synthetic output stable within tolerance."""
        img = Image.new("RGBA", (80, 120), (0, 0, 0, 0))
        img.paste(Image.new("RGBA", (40, 70), (128, 128, 128, 255)), (20, 25))
        settings = ShadowSettings(
            shadow_engine=engine_name,
            adaptive_zoom=False,
            angle=180,
            distance=18,
            blur=12,
            opacity=35,
            noise=0,
            contact_blur=6,
            padding=10,
        )

        result = ShadowEngine.aplicar_efectos(img, settings, (180, 240))
        arr = np.asarray(result, dtype=np.int64)

        assert result.mode == "RGB"
        assert abs(int(arr.sum()) - expected_sum) <= 5000

    def test_adaptive_scale_golden_synthetic_output(self):
        """Adaptive scaling keeps a small transparent output stable within tolerance."""
        img = Image.new("RGBA", (90, 140), (0, 0, 0, 0))
        img.paste(Image.new("RGBA", (34, 96), (90, 120, 180, 255)), (28, 24))
        settings = ShadowSettings(
            shadow_engine="realistic_v2",
            adaptive_zoom=True,
            transparent_bg=True,
            angle=180,
            distance=12,
            blur=8,
            opacity=30,
            noise=0,
            contact_blur=4,
            padding=12,
        )

        result = ShadowEngine.aplicar_efectos(
            img,
            settings,
            (180, 260),
            scale_factor=1.0,
            curve_data=CurveData(
                xp=[0.0, 0.35, 0.60, 0.85, 1.10, 1.40, 3.0],
                fp=[0.80, 0.80, 0.90, 1.00, 0.95, 0.90, 0.90],
            ),
        )
        arr = np.asarray(result, dtype=np.int64)
        alpha_sum = int(np.asarray(result.getchannel("A"), dtype=np.int64).sum())

        assert result.mode == "RGBA"
        assert result.getbbox() == (49, 22, 132, 238)
        assert abs(int(arr.sum()) - 9594010) <= 5000
        assert abs(alpha_sum - 3768226) <= 5000

    def test_realistic_v2_is_deterministic_with_noise(self, sample_image):
        settings = ShadowSettings(
            shadow_engine="realistic_v2",
            adaptive_zoom=False,
            transparent_bg=True,
            opacity=45,
            blur=18,
            noise=5,
        )

        one = ShadowEngine.aplicar_efectos(sample_image, settings, (360, 480))
        two = ShadowEngine.aplicar_efectos(sample_image, settings, (360, 480))

        assert one.tobytes() == two.tobytes()

    def test_realistic_v2_noise_keeps_lower_contact_visible(self):
        clean = render_realistic_v2(
            _shadow_context(
                ShadowSettings(
                    shadow_engine="realistic_v2",
                    angle=180,
                    distance=28,
                    blur=18,
                    contact_blur=6,
                    opacity=45,
                    noise=0,
                )
            )
        ).shadow
        noisy = render_realistic_v2(
            _shadow_context(
                ShadowSettings(
                    shadow_engine="realistic_v2",
                    angle=180,
                    distance=28,
                    blur=18,
                    contact_blur=6,
                    opacity=45,
                    noise=20,
                )
            )
        ).shadow

        clean_alpha = np.asarray(clean.getchannel("A"), dtype=np.float32)
        noisy_alpha = np.asarray(noisy.getchannel("A"), dtype=np.float32)
        bottom_contact = np.s_[138:170, 80:140]

        assert np.percentile(noisy_alpha[bottom_contact], 20) >= (
            np.percentile(clean_alpha[bottom_contact], 20) * 0.92
        )

    def test_realistic_v2_contact_is_not_bottom_heavy(self):
        shadow = render_realistic_v2(
            _shadow_context(
                ShadowSettings(
                    shadow_engine="realistic_v2",
                    angle=180,
                    distance=28,
                    blur=18,
                    contact_blur=6,
                    opacity=45,
                    noise=0,
                )
            )
        ).shadow

        alpha = np.asarray(shadow.getchannel("A"), dtype=np.float32)
        upper_contact = alpha[70:95, 80:140].mean()
        lower_contact = alpha[125:150, 80:140].mean()

        assert lower_contact <= upper_contact * 1.20

    def test_realistic_v2_dark_products_cast_slightly_stronger_shadow(self):
        settings = ShadowSettings(
            shadow_engine="realistic_v2",
            angle=180,
            distance=28,
            blur=18,
            contact_blur=6,
            opacity=34,
            noise=0,
        )

        dark = render_realistic_v2(_shadow_context(settings, luminance_value=0.15)).shadow
        light = render_realistic_v2(_shadow_context(settings, luminance_value=0.85)).shadow
        dark_sum = float(np.asarray(dark.getchannel("A"), dtype=np.float32).sum())
        light_sum = float(np.asarray(light.getchannel("A"), dtype=np.float32).sum())
        ratio = dark_sum / max(light_sum, 1.0)

        assert ratio > 1.06
        assert ratio < 1.22

    def test_realistic_v2_handles_empty_mask_without_fallback(self):
        settings = ShadowSettings(shadow_engine="realistic_v2", opacity=50, noise=0)
        mask = Image.new("L", (120, 120), 0)
        context = ShadowRenderContext(
            settings=settings,
            canvas_size=mask.size,
            scale_factor=1.0,
            subject_width=0,
            subject_mask_canvas=mask,
            subject_mask_local=mask,
            subject_position=(0, 0),
            luminance_value=0.5,
        )

        result = render_realistic_v2(context)

        assert result.shadow.getchannel("A").getbbox() is None
        assert result.diagnostics.fallback_used is False

    def test_realistic_v2_opacity_zero_returns_empty_shadow(self):
        result = render_realistic_v2(
            _shadow_context(ShadowSettings(shadow_engine="realistic_v2", opacity=0))
        )

        assert result.shadow.getchannel("A").getbbox() is None
        assert result.diagnostics.fallback_used is False

    def test_angle_convention_is_shadow_fall_direction(self):
        assert shadow_vector_from_angle(0).y < 0
        assert shadow_vector_from_angle(90).x > 0
        assert shadow_vector_from_angle(180).y > 0
        assert shadow_vector_from_angle(270).x < 0

    def test_realistic_v2_angle_moves_shadow_centroid(self):
        right = render_realistic_v2(
            _shadow_context(
                ShadowSettings(
                    shadow_engine="realistic_v2",
                    angle=90,
                    distance=70,
                    blur=12,
                    contact_blur=4,
                    opacity=55,
                    noise=0,
                )
            )
        ).shadow
        left = render_realistic_v2(
            _shadow_context(
                ShadowSettings(
                    shadow_engine="realistic_v2",
                    angle=270,
                    distance=70,
                    blur=12,
                    contact_blur=4,
                    opacity=55,
                    noise=0,
                )
            )
        ).shadow

        assert _alpha_centroid(right)[0] > _alpha_centroid(left)[0]

    def test_realistic_v2_distance_moves_centroid_farther(self):
        near = render_realistic_v2(
            _shadow_context(
                ShadowSettings(
                    shadow_engine="realistic_v2",
                    angle=90,
                    distance=10,
                    blur=10,
                    opacity=55,
                    noise=0,
                )
            )
        ).shadow
        far = render_realistic_v2(
            _shadow_context(
                ShadowSettings(
                    shadow_engine="realistic_v2",
                    angle=90,
                    distance=80,
                    blur=10,
                    opacity=55,
                    noise=0,
                )
            )
        ).shadow

        assert _alpha_centroid(far)[0] > _alpha_centroid(near)[0] + 3.0

    def test_realistic_v2_blur_expands_support(self):
        sharp = render_realistic_v2(
            _shadow_context(
                ShadowSettings(
                    shadow_engine="realistic_v2",
                    angle=180,
                    distance=30,
                    blur=2,
                    contact_blur=1,
                    opacity=55,
                    noise=0,
                )
            )
        ).shadow
        soft = render_realistic_v2(
            _shadow_context(
                ShadowSettings(
                    shadow_engine="realistic_v2",
                    angle=180,
                    distance=30,
                    blur=35,
                    contact_blur=10,
                    opacity=55,
                    noise=0,
                )
            )
        ).shadow

        sharp_support = int((np.asarray(sharp.getchannel("A")) > 0).sum())
        soft_support = int((np.asarray(soft.getchannel("A")) > 0).sum())
        assert soft_support > sharp_support

    def test_realistic_v2_limit_inputs_do_not_error(self):
        border = Image.new("RGBA", (120, 160), (0, 0, 0, 0))
        border.paste(Image.new("RGBA", (40, 70), (80, 140, 200, 255)), (0, 0))
        tiny = Image.new("RGBA", (20, 20), (0, 0, 0, 0))
        tiny.paste(Image.new("RGBA", (2, 2), (200, 80, 40, 180)), (9, 9))
        rgb = Image.new("RGB", (80, 80), (245, 245, 245))
        rgb.paste(Image.new("RGB", (30, 40), (10, 20, 30)), (25, 20))
        settings = ShadowSettings(
            shadow_engine="realistic_v2",
            adaptive_zoom=False,
            blur=0,
            distance=0,
            noise=0,
            transparent_bg=True,
        )

        for image in (border, tiny, rgb):
            result = ShadowEngine.aplicar_efectos(image, settings, (180, 240))
            assert result.size == (180, 240)

    def test_realistic_v2_auto_fallback_records_warning(self, monkeypatch):
        import flatshot.core.engine as engine_module

        def fail_renderer(_context):
            raise RuntimeError("boom")

        monkeypatch.setattr(engine_module, "render_realistic_v2", fail_renderer)
        result = ShadowEngine._render_shadow(
            _shadow_context(
                ShadowSettings(
                    shadow_engine="realistic_v2",
                    opacity=30,
                    noise=0,
                )
            )
        )

        assert result.diagnostics.fallback_used is True
        assert result.diagnostics.engine_used == "legacy"
        assert "boom" in result.diagnostics.warning

    def test_realistic_v2_strict_mode_propagates_error(self, monkeypatch):
        import flatshot.core.engine as engine_module

        def fail_renderer(_context):
            raise RuntimeError("boom")

        monkeypatch.setenv("FLATSHOT_SHADOW_STRICT", "1")
        monkeypatch.setattr(engine_module, "render_realistic_v2", fail_renderer)

        with pytest.raises(RuntimeError, match="boom"):
            ShadowEngine._render_shadow(
                _shadow_context(
                    ShadowSettings(
                        shadow_engine="realistic_v2",
                        opacity=30,
                        noise=0,
                    )
                )
            )

    def test_studio_2_5d_is_deterministic_with_noise(self):
        settings = ShadowSettings(
            shadow_engine="studio_2_5d",
            angle=180,
            distance=30,
            blur=20,
            contact_blur=8,
            opacity=42,
            noise=8,
            lighting_scene={
                "main": {
                    "type": "softbox",
                    "x": -0.45,
                    "y": -0.65,
                    "height": 0.55,
                    "size": 0.62,
                    "intensity": 0.95,
                },
                "ambient_intensity": 0.25,
            },
        )

        one = render_studio_2_5d(_shadow_context(settings)).shadow
        two = render_studio_2_5d(_shadow_context(settings)).shadow

        assert one.tobytes() == two.tobytes()

    def test_studio_2_5d_light_position_controls_shadow_direction(self):
        left_light = render_studio_2_5d(
            _shadow_context(
                ShadowSettings(
                    shadow_engine="studio_2_5d",
                    distance=55,
                    blur=12,
                    opacity=55,
                    noise=0,
                    lighting_scene={"main": {"x": -0.8, "y": -0.55, "height": 0.45}},
                )
            )
        ).shadow
        right_light = render_studio_2_5d(
            _shadow_context(
                ShadowSettings(
                    shadow_engine="studio_2_5d",
                    distance=55,
                    blur=12,
                    opacity=55,
                    noise=0,
                    lighting_scene={"main": {"x": 0.8, "y": -0.55, "height": 0.45}},
                )
            )
        ).shadow

        assert _alpha_centroid(left_light)[0] > _alpha_centroid(right_light)[0] + 2.0

    def test_studio_2_5d_bottom_spot_keeps_ground_contact_visible(self):
        settings = ShadowSettings(
            shadow_engine="studio_2_5d",
            distance=80,
            blur=30,
            contact_blur=15,
            opacity=20,
            noise=0,
            lighting_scene={
                "main": {
                    "type": "spot",
                    "x": 0.0,
                    "y": 1.0,
                    "height": 0.65,
                    "size": 0.0,
                    "intensity": 1.15,
                },
                "ambient_intensity": 0.0,
            },
        )
        context = _shadow_context(settings)
        shadow = render_studio_2_5d(context).shadow

        alpha = np.asarray(shadow.getchannel("A"), dtype=np.float32)
        left, _top, right, bottom = context.subject_mask_canvas.getbbox()
        below_contact = alpha[bottom:min(alpha.shape[0], bottom + 36), left:right]

        assert below_contact.max() >= 6.0
        assert below_contact.sum() >= 900.0

    def test_studio_2_5d_light_types_produce_distinct_shadows(self):
        base = {
            "shadow_engine": "studio_2_5d",
            "distance": 80,
            "blur": 24,
            "contact_blur": 9,
            "opacity": 45,
            "noise": 0,
            "lighting_scene": {
                "main": {"x": -0.55, "y": -0.55, "height": 0.45, "size": 0.45, "intensity": 0.95},
                "ambient_intensity": 0.20,
            },
        }
        def settings_for(light_type):
            data = dict(base)
            scene = {
                **base["lighting_scene"],
                "main": {**base["lighting_scene"]["main"], "type": light_type},
            }
            data["lighting_scene"] = scene
            return ShadowSettings(**data)

        def wide_context(settings):
            mask = Image.new("L", (420, 420), 0)
            mask.paste(255, (160, 130, 260, 260))
            return ShadowRenderContext(
                settings=settings,
                canvas_size=mask.size,
                scale_factor=1.0,
                subject_width=100,
                subject_mask_canvas=mask,
                subject_mask_local=mask.crop((160, 130, 260, 260)),
                subject_position=(160, 130),
                luminance_value=0.5,
                background_rgb=(230, 230, 230),
            )

        def light_metrics(light_type):
            context = wide_context(settings_for(light_type))
            shadow = render_studio_2_5d(context).shadow
            alpha = np.asarray(shadow.getchannel("A"), dtype=np.float32)
            alpha[np.asarray(context.subject_mask_canvas) > 0] = 0
            ys, xs = np.where(alpha > 2)
            weights = alpha[ys, xs]
            total = float(weights.sum())
            assert total > 0

            vector_x, vector_y = 0.55, 0.55
            length = float(np.hypot(vector_x, vector_y))
            vector_x, vector_y = vector_x / length, vector_y / length
            perp_x, perp_y = -vector_y, vector_x
            center_x = float((xs * weights).sum() / total)
            center_y = float((ys * weights).sum() / total)
            parallel = (xs - center_x) * vector_x + (ys - center_y) * vector_y
            perpendicular = (xs - center_x) * perp_x + (ys - center_y) * perp_y
            parallel_std = float(np.sqrt(((parallel * parallel) * weights).sum() / total))
            perpendicular_std = float(np.sqrt(((perpendicular * perpendicular) * weights).sum() / total))

            return {
                "peak": float(alpha.max()),
                "mean": float(weights.mean()),
                "support": int(weights.size),
                "parallel_std": parallel_std,
                "perpendicular_std": perpendicular_std,
                "perpendicular_ratio": perpendicular_std / max(parallel_std, 1e-6),
            }

        softbox = light_metrics("softbox")
        spot = light_metrics("spot")
        strip = light_metrics("strip")

        assert softbox["support"] > spot["support"] * 1.15
        assert spot["peak"] > softbox["peak"] * 2.4
        assert spot["mean"] > softbox["mean"] * 4.0
        assert spot["perpendicular_ratio"] < 0.90
        assert strip["perpendicular_ratio"] > 1.04
        assert strip["perpendicular_std"] > spot["perpendicular_std"] * 1.15
        assert strip["mean"] < spot["mean"] * 0.45

    def test_studio_2_5d_handles_transparent_context_and_empty_inputs(self):
        transparent = _shadow_context(
            ShadowSettings(
                shadow_engine="studio_2_5d",
                transparent_bg=True,
                opacity=40,
                noise=0,
            )
        )
        transparent = ShadowRenderContext(
            settings=transparent.settings,
            canvas_size=transparent.canvas_size,
            scale_factor=transparent.scale_factor,
            subject_width=transparent.subject_width,
            subject_mask_canvas=transparent.subject_mask_canvas,
            subject_mask_local=transparent.subject_mask_local,
            subject_position=transparent.subject_position,
            luminance_value=transparent.luminance_value,
            background_rgb=None,
        )

        result = render_studio_2_5d(transparent)
        assert result.shadow.getchannel("A").getbbox() is not None
        assert result.diagnostics.engine_used == "studio_2_5d"

        empty_mask = Image.new("L", (120, 120), 0)
        empty = render_studio_2_5d(
            ShadowRenderContext(
                settings=ShadowSettings(shadow_engine="studio_2_5d", opacity=40),
                canvas_size=empty_mask.size,
                scale_factor=1.0,
                subject_width=0,
                subject_mask_canvas=empty_mask,
                subject_mask_local=empty_mask,
                subject_position=(0, 0),
                luminance_value=0.5,
            )
        )
        assert empty.shadow.getchannel("A").getbbox() is None
