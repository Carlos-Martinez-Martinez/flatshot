"""
Tests for FlatShot Core Engine
"""
import pytest
import numpy as np
from PIL import Image

from flatshot.core.engine import ShadowEngine
from flatshot.core.models import ShadowSettings, CurveData


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
