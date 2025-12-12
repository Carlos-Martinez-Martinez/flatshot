"""
Configuration Manager for FlatShot
Handles presets, settings, and import/export functionality.
"""
import json
import logging
from pathlib import Path
from typing import Optional
from PyQt6.QtCore import QStandardPaths
from flatshot.core.models import CategorizedPresets, PresetCategory


class ConfigManager:
    """Manages application configuration and presets."""
    
    PRESETS_FILE = "presets.json"
    CATEGORIZED_PRESETS_FILE = "presets_v2.json"
    
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
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(presets, f, indent=4)
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
                return json.load(f)
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
                json.dump(presets.model_dump(), f, indent=4)
        except Exception as e:
            logging.error(f"Error saving categorized presets: {e}")
    
    @staticmethod
    def load_categorized_presets() -> CategorizedPresets:
        """Load presets in categorized format, with automatic migration from legacy."""
        file_path = ConfigManager.get_config_dir() / ConfigManager.CATEGORIZED_PRESETS_FILE
        
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return CategorizedPresets(**data)
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
        # Create default categories
        categorized = ConfigManager._get_default_categorized_presets()
        
        # Move all legacy presets to uncategorized
        for name, settings in legacy_presets.items():
            # Try to auto-categorize based on name
            category_key = None
            name_lower = name.lower()
            
            if 'clar' in name_lower or 'light' in name_lower:
                category_key = 'ropa_clara'
            elif 'oscur' in name_lower or 'dark' in name_lower:
                category_key = 'ropa_oscura'
            
            if category_key and category_key in categorized.categories:
                categorized.categories[category_key].presets[name] = settings
            else:
                categorized.uncategorized[name] = settings
        
        # Save migrated presets
        ConfigManager.save_categorized_presets(categorized)
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
                            'contact_blur': 10, 'adaptive_zoom': True
                        }
                    }
                ),
                'ropa_oscura': PresetCategory(
                    name='Ropa Oscura',
                    presets={
                        'Estándar oscuro': {
                            'angle': 180, 'distance': 20, 'blur': 40, 'spread': 3,
                            'fusion': 5, 'opacity': 45, 'noise': 5, 'padding': 10,
                            'contact_blur': 12, 'adaptive_zoom': True
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
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(presets.model_dump(), f, indent=4)
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
            
            imported = CategorizedPresets(**data)
            
            if merge:
                existing = ConfigManager.load_categorized_presets()
                # Merge categories
                for cat_key, cat_value in imported.categories.items():
                    if cat_key in existing.categories:
                        existing.categories[cat_key].presets.update(cat_value.presets)
                    else:
                        existing.categories[cat_key] = cat_value
                # Merge uncategorized
                existing.uncategorized.update(imported.uncategorized)
                ConfigManager.save_categorized_presets(existing)
                return existing
            else:
                ConfigManager.save_categorized_presets(imported)
                return imported
                
        except Exception as e:
            logging.error(f"Error importing presets: {e}")
            return None
    
    # ========== Utility Methods ==========
    
    @staticmethod
    def get_flat_presets_from_categorized(categorized: CategorizedPresets) -> dict:
        """Convert categorized presets to flat dict for backward compatibility."""
        flat = {}
        for category in categorized.categories.values():
            flat.update(category.presets)
        flat.update(categorized.uncategorized)
        return flat
