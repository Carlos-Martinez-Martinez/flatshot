"""
Tests for FlatShot Models
"""
import pytest
from flatshot.core.models import (
    SHADOW_ENGINE_COMPAT,
    SHADOW_ENGINE_DEFAULT,
    WEB_RGB230,
    WHITE_RGB255,
    ExportVariant,
    ShadowSettings, ExportConfig, CurveData,
    JobItem, PresetCategory, CategorizedPresets,
    build_variant_settings,
    normalize_export_variants,
    normalize_shadow_settings,
)


class TestShadowSettings:
    """Tests for ShadowSettings model."""
    
    def test_default_values(self):
        """Test default values are set correctly."""
        settings = ShadowSettings()
        
        assert settings.angle == 180
        assert settings.distance == 25
        assert settings.blur == 30
        assert settings.opacity == 20
        assert settings.padding == 10
        assert settings.adaptive_zoom is True
        assert settings.shadow_engine == SHADOW_ENGINE_DEFAULT
        assert settings.transparent_bg is False
        assert settings.bg_color == (230, 230, 230)
    
    def test_custom_values(self):
        """Test custom values are accepted."""
        settings = ShadowSettings(
            angle=90,
            distance=50,
            blur=40,
            opacity=50
        )
        
        assert settings.angle == 90
        assert settings.distance == 50
        assert settings.blur == 40
        assert settings.opacity == 50
    
    def test_angle_bounds(self):
        """Test angle validation."""
        # Valid angle
        settings = ShadowSettings(angle=0)
        assert settings.angle == 0
        
        settings = ShadowSettings(angle=359)
        assert settings.angle == 359
    
    def test_model_dump(self):
        """Test model serialization."""
        settings = ShadowSettings()
        data = settings.model_dump()
        
        assert isinstance(data, dict)
        assert 'angle' in data
        assert 'distance' in data
        assert 'blur' in data
        assert data['shadow_engine'] == SHADOW_ENGINE_DEFAULT

    def test_normalize_missing_shadow_engine_uses_legacy_for_loaded_data(self):
        settings = normalize_shadow_settings({"angle": 90, "distance": 12})

        assert settings.shadow_engine == SHADOW_ENGINE_COMPAT
        assert settings.angle == 90

    def test_normalize_preserves_explicit_shadow_engine(self):
        settings = normalize_shadow_settings(
            {"angle": 90, "shadow_engine": SHADOW_ENGINE_DEFAULT},
        )

        assert settings.shadow_engine == SHADOW_ENGINE_DEFAULT


class TestExportConfig:
    """Tests for ExportConfig model."""
    
    def test_default_values(self):
        """Test default export config values."""
        config = ExportConfig()
        
        assert config.output_folder_name == "_SALIDA_PRO"
        assert config.suffix == "_PRO"
        assert config.format == "JPG"
        assert config.variants == []
        assert config.output_width == 1800
        assert config.output_height == 2400
        assert config.naming_template == "{original}{suffix}"
    
    def test_naming_template_custom(self):
        """Test custom naming template."""
        config = ExportConfig(
            naming_template="{folder}_{original}_{index}"
        )
        
        assert config.naming_template == "{folder}_{original}_{index}"
    
    def test_output_size_custom(self):
        """Test custom output size."""
        config = ExportConfig(
            output_width=1200,
            output_height=1600
        )
        
        assert config.output_width == 1200
        assert config.output_height == 1600


class TestExportVariant:
    """Tests for output variant model and migration helpers."""

    def test_variant_validates_rgb_suffix_and_delta(self):
        variant = ExportVariant(
            id="white_rgb255",
            label="Blanco RGB255",
            bg_color=[255, 255, 255],
            suffix="_BLANCO",
            shadow_opacity_delta=-5,
        )

        assert variant.bg_color == (255, 255, 255)
        assert variant.suffix == "_BLANCO"
        assert variant.shadow_opacity_delta == -5

    def test_variant_rejects_invalid_rgb_suffix_and_delta(self):
        with pytest.raises(ValueError):
            ExportVariant(id="bad_rgb", label="Bad", bg_color=(300, 0, 0))

        with pytest.raises(ValueError):
            ExportVariant(id="bad_suffix", label="Bad", suffix="../BAD")

        with pytest.raises(ValueError):
            ExportVariant(id="bad_delta", label="Bad", shadow_opacity_delta=-101)

    def test_recommended_templates_are_named_output_variants(self):
        assert WEB_RGB230.label == "Web RGB230"
        assert WEB_RGB230.enabled is True
        assert WEB_RGB230.bg_color == (230, 230, 230)
        assert WEB_RGB230.suffix == "_PRO"

        assert WHITE_RGB255.label == "Blanco RGB255"
        assert WHITE_RGB255.enabled is False
        assert WHITE_RGB255.bg_color == (255, 255, 255)
        assert WHITE_RGB255.suffix == "_BLANCO"
        assert WHITE_RGB255.shadow_opacity_delta == -5

    def test_normalize_export_variants_migrates_old_settings_to_single_variant(self):
        variants = normalize_export_variants(
            {
                "bg_color": [240, 241, 242],
                "transparent_bg": True,
                "suffix": "_OLD",
            }
        )

        assert len(variants) == 1
        assert variants[0].enabled is True
        assert variants[0].bg_color == (240, 241, 242)
        assert variants[0].transparent_bg is True
        assert variants[0].suffix == "_OLD"

    def test_normalize_export_variants_loads_existing_variants(self):
        variants = normalize_export_variants(
            {
                "suffix": "_PRO",
                "variants": [
                    WEB_RGB230.model_dump(),
                    WHITE_RGB255.model_dump(),
                ],
            }
        )

        assert [variant.id for variant in variants] == ["web_rgb230", "white_rgb255"]

    def test_build_variant_settings_applies_shadow_delta_and_override(self):
        base = ShadowSettings(opacity=20)

        adjusted = build_variant_settings(base, WHITE_RGB255)
        assert adjusted.opacity == 15
        assert adjusted.bg_color == (255, 255, 255)
        assert base.opacity == 20

        override = WHITE_RGB255.model_copy(update={"shadow_opacity_override": 42})
        adjusted_override = build_variant_settings(base, override)
        assert adjusted_override.opacity == 42

        clamped = WHITE_RGB255.model_copy(update={"shadow_opacity_delta": -100})
        assert build_variant_settings(ShadowSettings(opacity=10), clamped).opacity == 0


class TestJobItem:
    """Tests for JobItem model."""
    
    def test_default_status(self):
        """Test default job status."""
        job = JobItem(folder_path="/test/path")
        
        assert job.status == "pending"
        assert job.progress == 0
        assert job.total_images == 0
        assert job.error_message is None
    
    def test_status_values(self):
        """Test various status values."""
        job = JobItem(folder_path="/test/path", status="processing")
        assert job.status == "processing"
        
        job = JobItem(folder_path="/test/path", status="completed")
        assert job.status == "completed"
        
        job = JobItem(folder_path="/test/path", status="error", error_message="Test error")
        assert job.status == "error"
        assert job.error_message == "Test error"


class TestPresetCategory:
    """Tests for PresetCategory model."""
    
    def test_create_category(self):
        """Test creating a preset category."""
        category = PresetCategory(
            name="Ropa Clara",
            presets={
                "Default": {"angle": 180, "distance": 25}
            }
        )
        
        assert category.name == "Ropa Clara"
        assert len(category.presets) == 1
        assert "Default" in category.presets
    
    def test_locked_category(self):
        """Test locked category flag."""
        category = PresetCategory(
            name="System",
            locked=True
        )
        
        assert category.locked is True


class TestCategorizedPresets:
    """Tests for CategorizedPresets model."""
    
    def test_create_structure(self):
        """Test creating categorized presets structure."""
        presets = CategorizedPresets(
            categories={
                "light": PresetCategory(name="Light", presets={}),
                "dark": PresetCategory(name="Dark", presets={})
            },
            uncategorized={"Legacy": {"angle": 90}}
        )
        
        assert len(presets.categories) == 2
        assert "light" in presets.categories
        assert "Legacy" in presets.uncategorized
