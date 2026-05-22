"""Qt-free application settings service."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Mapping

from flatshot.core.models import SHADOW_ENGINE_COMPAT, SHADOW_ENGINE_DEFAULT
from flatshot.core.scaling import DEFAULT_SCALE_CURVE


DEFAULT_APP_SETTINGS: dict[str, Any] = {
    "output_folder_name": "_SALIDA_PRO",
    "suffix": "_PRO",
    "format": "JPG",
    "transparent_bg": False,
    "bg_color": (230, 230, 230),
    "output_width": 1800,
    "output_height": 2400,
    "naming_template": "{original}{suffix}",
    "output_destination": "subfolder",
    "custom_output_path": None,
    "last_input_folder": "",
    "preview_bg_color": "#E6E6E6",
    "preview_grid": False,
    "preview_guides": {
        "preset": "thirds",
        "color": "#FFFFFF",
        "opacity": 42,
    },
    "image_overrides": {},
    "shadow_engine": SHADOW_ENGINE_DEFAULT,
    "scale_curve": dict(DEFAULT_SCALE_CURVE),
    "section_visibility": {
        "presets": True,
        "lighting": True,
        "shadows": True,
        "finishing": False,
        "advanced": False,
        "export": True,
    },
    "grid_columns": 3,
    "grid_folder_index": 0,
    "background_pre_render": False,
    "background_pre_render_cache_mb": 2048,
    "background_pre_render_idle_ms": 8000,
}


class SettingsService:
    def __init__(self, settings_file: str | Path) -> None:
        self.settings_file = Path(settings_file)

    def load(self) -> dict[str, Any]:
        if not self.settings_file.exists():
            return self.default_settings()

        try:
            with self.settings_file.open("r", encoding="utf-8") as handle:
                loaded = json.load(handle)
        except Exception:
            return self.default_settings()

        if not isinstance(loaded, Mapping):
            return self.default_settings()
        return self.normalize(loaded)

    def load_existing(self, fallback: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """Load settings only when an existing file contains a JSON object."""
        if not self.settings_file.exists():
            return dict(fallback or {})

        try:
            with self.settings_file.open("r", encoding="utf-8") as handle:
                loaded = json.load(handle)
        except Exception:
            return dict(fallback or {})

        if not isinstance(loaded, Mapping):
            return dict(fallback or {})
        return self.normalize(loaded)

    def save(self, settings: Mapping[str, Any]) -> None:
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
        with self.settings_file.open("w", encoding="utf-8") as handle:
            json.dump(dict(settings), handle, indent=4)

    @classmethod
    def normalize(cls, loaded: Mapping[str, Any]) -> dict[str, Any]:
        data = dict(loaded)
        if isinstance(data.get("bg_color"), list):
            data["bg_color"] = tuple(data["bg_color"])
        if "shadow_engine" not in data:
            data["shadow_engine"] = SHADOW_ENGINE_COMPAT
        return {**cls.default_settings(), **data}

    @staticmethod
    def default_settings() -> dict[str, Any]:
        return copy.deepcopy(DEFAULT_APP_SETTINGS)
