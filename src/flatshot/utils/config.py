"""
Configuration Manager for FlatShot
Handles presets, settings, and import/export functionality.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from PyQt6.QtCore import QStandardPaths
from flatshot.core.models import (
    CategorizedPresets,
    PresetCategory,
    SHADOW_ENGINE_COMPAT,
    SHADOW_ENGINE_DEFAULT,
    normalize_shadow_settings_dict,
)


class ConfigManager:
    """Manages application configuration and presets."""
    
    PRESETS_FILE = "presets.json"
    CATEGORIZED_PRESETS_FILE = "presets_v2.json"
    PRESETS_EXPORT_VERSION = 1
    
    @staticmethod
    def get_config_dir() -> Path:
        """Get the application config directory."""
        path = Path(QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppConfigLocation
        ))
        path.mkdir(parents=True, exist_ok=True)
        return path

    # ========== Legacy Presets (flat dict) ==========
    
    @staticmethod
    def save_presets(presets: dict):
        """Save presets in legacy flat format."""
        file_path = ConfigManager.get_config_dir() / ConfigManager.PRESETS_FILE
        try:
            normalized = {
                name: normalize_shadow_settings_dict(
                    settings,
                    missing_engine=SHADOW_ENGINE_COMPAT,
                )
                for name, settings in (presets or {}).items()
            }
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(normalized, f, indent=4)
        except Exception as e:
            logging.error(f"Error saving presets: {e}")

    @staticmethod
    def load_presets() -> dict:
        """Load presets from legacy flat format."""
        file_path = ConfigManager.get_config_dir() / ConfigManager.PRESETS_FILE
        if not file_path.exists():
            return {}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return {
                name: normalize_shadow_settings_dict(
                    settings,
                    missing_engine=SHADOW_ENGINE_COMPAT,
                )
                for name, settings in (data or {}).items()
            }
        except Exception as e:
            logging.error(f"Error loading presets: {e}")
            return {}

    # ========== Categorized Presets ==========
    
    @staticmethod
    def save_categorized_presets(presets: CategorizedPresets):
        """Save presets in categorized format."""
        file_path = ConfigManager.get_config_dir() / ConfigManager.CATEGORIZED_PRESETS_FILE
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(presets.model_dump(), f, indent=4, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Error saving categorized presets: {e}")

    @staticmethod
    def save_all_presets(presets: CategorizedPresets):
        """Persist categorized and legacy preset files together."""
        presets = ConfigManager.normalize_categorized_presets(
            presets,
            missing_engine=SHADOW_ENGINE_COMPAT,
        )
        ConfigManager.save_categorized_presets(presets)
        ConfigManager.save_presets(ConfigManager.get_flat_presets_from_categorized(presets))
    
    @staticmethod
    def load_categorized_presets() -> CategorizedPresets:
        """Load presets in categorized format, with automatic migration from legacy."""
        file_path = ConfigManager.get_config_dir() / ConfigManager.CATEGORIZED_PRESETS_FILE
        
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return ConfigManager.normalize_categorized_presets(
                        CategorizedPresets(**data),
                        missing_engine=SHADOW_ENGINE_COMPAT,
                    )
            except Exception as e:
                logging.error(f"Error loading categorized presets: {e}")
        
        # Try to migrate from legacy format
        legacy = ConfigManager.load_presets()
        if legacy:
            return ConfigManager.migrate_legacy_presets(legacy)
        
        # Return default structure
        return ConfigManager._get_default_categorized_presets()
    
    @staticmethod
    def migrate_legacy_presets(legacy_presets: dict) -> CategorizedPresets:
        """Migrate legacy flat presets to categorized format."""
        categorized = ConfigManager._categorize_flat_presets(legacy_presets)
        ConfigManager.save_all_presets(categorized)
        return categorized

    @staticmethod
    def normalize_categorized_presets(
        categorized: CategorizedPresets,
        *,
        missing_engine: str = SHADOW_ENGINE_COMPAT,
    ) -> CategorizedPresets:
        """Ensure every stored preset has an explicit shadow_engine."""
        data = categorized.model_dump()
        for category in data.get("categories", {}).values():
            category["presets"] = {
                name: normalize_shadow_settings_dict(
                    settings,
                    missing_engine=missing_engine,
                )
                for name, settings in (category.get("presets") or {}).items()
            }
        data["uncategorized"] = {
            name: normalize_shadow_settings_dict(
                settings,
                missing_engine=missing_engine,
            )
            for name, settings in (data.get("uncategorized") or {}).items()
        }
        return CategorizedPresets(**data)

    @staticmethod
    def _categorize_flat_presets(legacy_presets: dict) -> CategorizedPresets:
        """Convert a legacy flat preset mapping to categorized presets."""
        categorized = ConfigManager._get_default_categorized_presets()

        for name, settings in legacy_presets.items():
            category_key = None
            name_lower = name.lower()

            if 'clar' in name_lower or 'light' in name_lower:
                category_key = 'ropa_clara'
            elif 'oscur' in name_lower or 'dark' in name_lower:
                category_key = 'ropa_oscura'

            if category_key and category_key in categorized.categories:
                categorized.categories[category_key].presets[name] = normalize_shadow_settings_dict(
                    settings,
                    missing_engine=SHADOW_ENGINE_COMPAT,
                )
            else:
                categorized.uncategorized[name] = normalize_shadow_settings_dict(
                    settings,
                    missing_engine=SHADOW_ENGINE_COMPAT,
                )

        return categorized
    
    @staticmethod
    def _get_default_categorized_presets() -> CategorizedPresets:
        """Get default categorized presets structure."""
        return CategorizedPresets(
            categories={
                'ropa_clara': PresetCategory(
                    name='Ropa Clara',
                    presets={
                        'Luz cenital': {
                            'angle': 180, 'distance': 25, 'blur': 30, 'spread': 0,
                            'fusion': 1, 'opacity': 20, 'noise': 2, 'padding': 10,
                            'contact_blur': 10, 'adaptive_zoom': True,
                            'shadow_engine': SHADOW_ENGINE_DEFAULT,
                        }
                    }
                ),
                'ropa_oscura': PresetCategory(
                    name='Ropa Oscura',
                    presets={
                        'Estándar oscuro': {
                            'angle': 180, 'distance': 20, 'blur': 40, 'spread': 3,
                            'fusion': 5, 'opacity': 45, 'noise': 5, 'padding': 10,
                            'contact_blur': 12, 'adaptive_zoom': True,
                            'shadow_engine': SHADOW_ENGINE_DEFAULT,
                        }
                    }
                ),
                'complementos': PresetCategory(
                    name='Complementos',
                    presets={}
                ),
                'custom': PresetCategory(
                    name='Personalizados',
                    presets={}
                )
            },
            uncategorized={}
        )

    # ========== Import/Export ==========
    
    @staticmethod
    def export_presets_to_file(file_path: str) -> bool:
        """Export all presets to an external JSON file."""
        try:
            presets = ConfigManager.load_categorized_presets()
            export_payload = {
                "flatshot_export": {
                    "type": "presets",
                    "version": ConfigManager.PRESETS_EXPORT_VERSION,
                    "exported_at": datetime.now(timezone.utc).isoformat(),
                    "preset_count": len(ConfigManager.get_flat_presets_from_categorized(presets)),
                },
                "presets": presets.model_dump(),
            }
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_payload, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            logging.error(f"Error exporting presets: {e}")
            return False
    
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
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            imported = ConfigManager._parse_imported_presets(data)
            
            if merge:
                imported = ConfigManager._merge_categorized_presets(
                    ConfigManager.load_categorized_presets(),
                    imported,
                )

            ConfigManager.save_all_presets(imported)
            return imported
                
        except Exception as e:
            logging.error(f"Error importing presets: {e}")
            return None

    @staticmethod
    def _parse_imported_presets(data: dict) -> CategorizedPresets:
        """Accept direct categorized JSON, exported bundles, or legacy flat mappings."""
        if not isinstance(data, dict):
            raise ValueError("El archivo de presets no contiene un objeto JSON válido.")

        candidate = data
        export_meta = data.get("flatshot_export")
        if isinstance(export_meta, dict) and export_meta.get("type") == "presets":
            candidate = data.get("presets", {})

        if isinstance(candidate, dict) and (
            "categories" in candidate or "uncategorized" in candidate
        ):
            return ConfigManager.normalize_categorized_presets(
                CategorizedPresets(**candidate),
                missing_engine=SHADOW_ENGINE_COMPAT,
            )

        return ConfigManager._categorize_flat_presets(candidate)

    @staticmethod
    def _merge_categorized_presets(
        base: CategorizedPresets,
        incoming: CategorizedPresets,
    ) -> CategorizedPresets:
        """Merge imported presets into the current categorized structure."""
        for cat_key, cat_value in incoming.categories.items():
            if cat_key in base.categories:
                base.categories[cat_key].presets.update(cat_value.presets)
            else:
                base.categories[cat_key] = cat_value
        base.uncategorized.update(incoming.uncategorized)
        return base
    
    # ========== Utility Methods ==========
    
    @staticmethod
    def get_flat_presets_from_categorized(categorized: CategorizedPresets) -> dict:
        """Convert categorized presets to flat dict for backward compatibility."""
        flat = {}
        for category in categorized.categories.values():
            flat.update(category.presets)
        flat.update(categorized.uncategorized)
        return flat
