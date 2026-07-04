"""Qt-free preset persistence and import/export service."""
from __future__ import annotations

import json
import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

from flatshot.core.models import (
    CategorizedPresets,
    PresetCategory,
    SHADOW_ENGINE_COMPAT,
    SHADOW_ENGINE_DEFAULT,
    normalize_shadow_settings_dict,
)


class PresetService:
    PRESETS_FILE = "presets.json"
    CATEGORIZED_PRESETS_FILE = "presets_v2.json"
    PRESETS_EXPORT_VERSION = 1

    def __init__(self, config_dir: str | Path) -> None:
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._write_lock = threading.Lock()

    @property
    def presets_path(self) -> Path:
        return self.config_dir / self.PRESETS_FILE

    @property
    def categorized_presets_path(self) -> Path:
        return self.config_dir / self.CATEGORIZED_PRESETS_FILE

    def save_presets(self, presets: dict) -> None:
        normalized = {
            name: normalize_shadow_settings_dict(
                settings,
                missing_engine=SHADOW_ENGINE_COMPAT,
            )
            for name, settings in (presets or {}).items()
        }
        _atomic_write_json(self.presets_path, normalized, indent=4)

    def load_presets(self) -> dict:
        if not self.presets_path.exists():
            return {}
        try:
            with self.presets_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            return {
                name: normalize_shadow_settings_dict(
                    settings,
                    missing_engine=SHADOW_ENGINE_COMPAT,
                )
                for name, settings in (data or {}).items()
            }
        except Exception as exc:
            logging.error(f"Error loading presets: {exc}")
            return {}

    def save_categorized_presets(self, presets: CategorizedPresets) -> None:
        _atomic_write_json(self.categorized_presets_path, presets.model_dump(), indent=4, ensure_ascii=False)

    def save_all_presets(self, presets: CategorizedPresets) -> None:
        presets = self.normalize_categorized_presets(
            presets,
            missing_engine=SHADOW_ENGINE_COMPAT,
        )
        with self._write_lock:
            self.save_categorized_presets(presets)
            self.save_presets(self.get_flat_presets_from_categorized(presets))

    def load_categorized_presets(self) -> CategorizedPresets:
        if self.categorized_presets_path.exists():
            try:
                with self.categorized_presets_path.open("r", encoding="utf-8") as handle:
                    data = json.load(handle)
                return self.normalize_categorized_presets(
                    CategorizedPresets(**data),
                    missing_engine=SHADOW_ENGINE_COMPAT,
                )
            except Exception as exc:
                logging.error(f"Error loading categorized presets: {exc}")

        legacy = self.load_presets()
        if legacy:
            return self.migrate_legacy_presets(legacy)

        return self.get_default_categorized_presets()

    def load_flat_presets(self) -> dict:
        return self.get_flat_presets_from_categorized(self.load_categorized_presets())

    def migrate_legacy_presets(self, legacy_presets: dict) -> CategorizedPresets:
        categorized = self.categorize_flat_presets(legacy_presets)
        self.save_all_presets(categorized)
        return categorized

    def save_flat_presets_preserving_categories(self, flat_presets: dict) -> None:
        categorized = self.load_categorized_presets()
        category_names = set()
        for category in categorized.categories.values():
            for preset_name in list(category.presets.keys()):
                category_names.add(preset_name)
                if preset_name in flat_presets:
                    category.presets[preset_name] = flat_presets[preset_name]
                else:
                    del category.presets[preset_name]

        categorized.uncategorized = {
            name: settings
            for name, settings in flat_presets.items()
            if name not in category_names
        }
        self.save_all_presets(categorized)

    @staticmethod
    def save_current_preset(flat_presets: dict, name: str, settings: dict) -> dict:
        updated = dict(flat_presets or {})
        if name:
            updated[name] = settings
        return updated

    @staticmethod
    def create_preset(flat_presets: dict, name: str, settings: dict) -> dict:
        updated = dict(flat_presets or {})
        if not name:
            raise ValueError("Preset name cannot be empty")
        if name in updated:
            raise ValueError("Preset already exists")
        updated[name] = settings
        return updated

    @staticmethod
    def rename_preset(flat_presets: dict, old_name: str, new_name: str) -> dict:
        updated = dict(flat_presets or {})
        if old_name not in updated:
            raise ValueError("Preset does not exist")
        if not new_name:
            raise ValueError("Preset name cannot be empty")
        if new_name != old_name and new_name in updated:
            raise ValueError("Preset already exists")
        updated[new_name] = updated.pop(old_name)
        return updated

    @staticmethod
    def delete_preset(flat_presets: dict, name: str) -> dict:
        updated = dict(flat_presets or {})
        if name not in updated:
            raise ValueError("Preset does not exist")
        del updated[name]
        return updated

    def export_presets_to_file(self, file_path: str | Path) -> bool:
        try:
            presets = self.load_categorized_presets()
            export_payload = {
                "flatshot_export": {
                    "type": "presets",
                    "version": self.PRESETS_EXPORT_VERSION,
                    "exported_at": datetime.now(timezone.utc).isoformat(),
                    "preset_count": len(self.get_flat_presets_from_categorized(presets)),
                },
                "presets": presets.model_dump(),
            }
            _atomic_write_json(Path(file_path), export_payload, indent=4, ensure_ascii=False)
            return True
        except Exception as exc:
            logging.error(f"Error exporting presets: {exc}")
            return False

    def import_presets_from_file(self, file_path: str | Path, merge: bool = True) -> Optional[CategorizedPresets]:
        try:
            with Path(file_path).open("r", encoding="utf-8") as handle:
                data = json.load(handle)

            imported = self.parse_imported_presets(data)
            if merge:
                imported = self.merge_categorized_presets(
                    self.load_categorized_presets(),
                    imported,
                )

            self.save_all_presets(imported)
            return imported
        except Exception as exc:
            logging.error(f"Error importing presets: {exc}")
            return None

    @classmethod
    def parse_imported_presets(cls, data: dict) -> CategorizedPresets:
        if not isinstance(data, dict):
            raise ValueError("El archivo de presets no contiene un objeto JSON válido.")

        candidate = data
        export_meta = data.get("flatshot_export")
        if isinstance(export_meta, dict) and export_meta.get("type") == "presets":
            candidate = data.get("presets", {})

        if isinstance(candidate, dict) and (
            "categories" in candidate or "uncategorized" in candidate
        ):
            return cls.normalize_categorized_presets(
                CategorizedPresets(**candidate),
                missing_engine=SHADOW_ENGINE_COMPAT,
            )

        return cls.categorize_flat_presets(candidate)

    @staticmethod
    def merge_categorized_presets(
        base: CategorizedPresets,
        incoming: CategorizedPresets,
    ) -> CategorizedPresets:
        for cat_key, cat_value in incoming.categories.items():
            if cat_key in base.categories:
                base.categories[cat_key].presets.update(cat_value.presets)
            else:
                base.categories[cat_key] = cat_value
        base.uncategorized.update(incoming.uncategorized)
        return base

    @staticmethod
    def normalize_categorized_presets(
        categorized: CategorizedPresets,
        *,
        missing_engine: str = SHADOW_ENGINE_COMPAT,
    ) -> CategorizedPresets:
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

    @classmethod
    def categorize_flat_presets(cls, legacy_presets: dict) -> CategorizedPresets:
        categorized = cls.get_default_categorized_presets()

        for name, settings in legacy_presets.items():
            category_key = None
            name_lower = name.lower()

            if "clar" in name_lower or "light" in name_lower:
                category_key = "ropa_clara"
            elif "oscur" in name_lower or "dark" in name_lower:
                category_key = "ropa_oscura"

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
    def get_default_categorized_presets() -> CategorizedPresets:
        return CategorizedPresets(
            categories={
                "ropa_clara": PresetCategory(
                    name="Ropa Clara",
                    presets={
                        "Luz cenital": {
                            "angle": 180,
                            "distance": 25,
                            "blur": 30,
                            "spread": 0,
                            "fusion": 1,
                            "opacity": 20,
                            "noise": 2,
                            "padding": 10,
                            "contact_blur": 10,
                            "adaptive_zoom": True,
                            "shadow_engine": SHADOW_ENGINE_DEFAULT,
                            "lighting_scene": {
                                "main": {
                                    "type": "softbox",
                                    "x": -0.25,
                                    "y": -0.65,
                                    "height": 0.65,
                                    "size": 0.55,
                                    "intensity": 0.85,
                                },
                                "ambient_intensity": 0.25,
                            },
                        }
                    },
                ),
                "ropa_oscura": PresetCategory(
                    name="Ropa Oscura",
                    presets={
                        "Estándar oscuro": {
                            "angle": 180,
                            "distance": 20,
                            "blur": 40,
                            "spread": 3,
                            "fusion": 5,
                            "opacity": 45,
                            "noise": 5,
                            "padding": 10,
                            "contact_blur": 12,
                            "adaptive_zoom": True,
                            "shadow_engine": SHADOW_ENGINE_DEFAULT,
                            "lighting_scene": {
                                "main": {
                                    "type": "softbox",
                                    "x": -0.25,
                                    "y": -0.65,
                                    "height": 0.65,
                                    "size": 0.55,
                                    "intensity": 0.85,
                                },
                                "ambient_intensity": 0.25,
                            },
                        }
                    },
                ),
                "complementos": PresetCategory(
                    name="Complementos",
                    presets={},
                ),
                "custom": PresetCategory(
                    name="Personalizados",
                    presets={},
                ),
            },
            uncategorized={},
        )

    @staticmethod
    def get_flat_presets_from_categorized(categorized: CategorizedPresets) -> dict:
        flat = {}
        for category in categorized.categories.values():
            flat.update(category.presets)
        flat.update(categorized.uncategorized)
        return flat


def _atomic_write_json(path: Path, payload: dict, **dump_kwargs) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        with tmp_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, **dump_kwargs)
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
