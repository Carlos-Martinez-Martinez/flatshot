"""
Configuration Manager for FlatShot.

Compatibility wrapper around Qt-free application services plus the current
Qt-based config directory resolver.
"""
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QStandardPaths

from flatshot.application.preset_service import PresetService
from flatshot.core.models import CategorizedPresets, SHADOW_ENGINE_COMPAT


class ConfigManager:
    """Manages application configuration and presets."""

    PRESETS_FILE = PresetService.PRESETS_FILE
    CATEGORIZED_PRESETS_FILE = PresetService.CATEGORIZED_PRESETS_FILE
    PRESETS_EXPORT_VERSION = PresetService.PRESETS_EXPORT_VERSION

    @staticmethod
    def get_config_dir() -> Path:
        """Get the application config directory."""
        path = Path(
            QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.AppConfigLocation
            )
        )
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def _service() -> PresetService:
        return PresetService(ConfigManager.get_config_dir())

    # ========== Legacy Presets (flat dict) ==========

    @staticmethod
    def save_presets(presets: dict):
        """Save presets in legacy flat format."""
        ConfigManager._service().save_presets(presets)

    @staticmethod
    def load_presets() -> dict:
        """Load presets from legacy flat format."""
        return ConfigManager._service().load_presets()

    # ========== Categorized Presets ==========

    @staticmethod
    def save_categorized_presets(presets: CategorizedPresets):
        """Save presets in categorized format."""
        ConfigManager._service().save_categorized_presets(presets)

    @staticmethod
    def save_all_presets(presets: CategorizedPresets):
        """Persist categorized and legacy preset files together."""
        ConfigManager._service().save_all_presets(presets)

    @staticmethod
    def load_categorized_presets() -> CategorizedPresets:
        """Load presets in categorized format, with automatic migration from legacy."""
        return ConfigManager._service().load_categorized_presets()

    @staticmethod
    def migrate_legacy_presets(legacy_presets: dict) -> CategorizedPresets:
        """Migrate legacy flat presets to categorized format."""
        return ConfigManager._service().migrate_legacy_presets(legacy_presets)

    @staticmethod
    def normalize_categorized_presets(
        categorized: CategorizedPresets,
        *,
        missing_engine: str = SHADOW_ENGINE_COMPAT,
    ) -> CategorizedPresets:
        """Ensure every stored preset has an explicit shadow_engine."""
        return PresetService.normalize_categorized_presets(
            categorized,
            missing_engine=missing_engine,
        )

    @staticmethod
    def _categorize_flat_presets(legacy_presets: dict) -> CategorizedPresets:
        """Convert a legacy flat preset mapping to categorized presets."""
        return PresetService.categorize_flat_presets(legacy_presets)

    @staticmethod
    def _get_default_categorized_presets() -> CategorizedPresets:
        """Get default categorized presets structure."""
        return PresetService.get_default_categorized_presets()

    # ========== Import/Export ==========

    @staticmethod
    def export_presets_to_file(file_path: str) -> bool:
        """Export all presets to an external JSON file."""
        return ConfigManager._service().export_presets_to_file(file_path)

    @staticmethod
    def import_presets_from_file(file_path: str, merge: bool = True) -> Optional[CategorizedPresets]:
        """
        Import presets from an external JSON file.

        Args:
            file_path: Path to the JSON file to import
            merge: If True, merge with existing presets. If False, replace.

        Returns:
            The imported presets, or None if import failed.
        """
        return ConfigManager._service().import_presets_from_file(file_path, merge=merge)

    @staticmethod
    def _parse_imported_presets(data: dict) -> CategorizedPresets:
        """Accept direct categorized JSON, exported bundles, or legacy flat mappings."""
        return PresetService.parse_imported_presets(data)

    @staticmethod
    def _merge_categorized_presets(
        base: CategorizedPresets,
        incoming: CategorizedPresets,
    ) -> CategorizedPresets:
        """Merge imported presets into the current categorized structure."""
        return PresetService.merge_categorized_presets(base, incoming)

    # ========== Utility Methods ==========

    @staticmethod
    def get_flat_presets_from_categorized(categorized: CategorizedPresets) -> dict:
        """Convert categorized presets to flat dict for backward compatibility."""
        return PresetService.get_flat_presets_from_categorized(categorized)
