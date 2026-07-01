"""Qt-free application settings service."""
from __future__ import annotations

import copy
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping

from flatshot.core.models import SHADOW_ENGINE_COMPAT, SHADOW_ENGINE_DEFAULT
from flatshot.core.scaling import DEFAULT_SCALE_CURVE


LOGGER = logging.getLogger(__name__)

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
}


class SettingsService:
    def __init__(self, settings_file: str | Path) -> None:
        self.settings_file = Path(settings_file)

    def load(self) -> dict[str, Any]:
        loaded = self._load_existing_mapping()
        if loaded is None:
            return self.default_settings()
        return self.normalize(loaded)

    def load_existing(self, fallback: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """Load settings only when an existing file contains a JSON object."""
        loaded = self._load_existing_mapping()
        if loaded is None:
            return dict(fallback or {})
        return self.normalize(loaded)

    def _load_existing_mapping(self) -> Mapping[str, Any] | None:
        if not self.settings_file.exists():
            return None

        try:
            with self.settings_file.open("r", encoding="utf-8") as handle:
                loaded = json.load(handle)
        except Exception as exc:
            self._preserve_invalid_file("Invalid settings file", exc)
            return None

        if not isinstance(loaded, Mapping):
            self._preserve_invalid_file("Invalid settings file is not a JSON object")
            return None
        return loaded

    def _preserve_invalid_file(self, reason: str, exc: Exception | None = None) -> None:
        backup_path = self.settings_file.with_name(f"{self.settings_file.name}.invalid")
        try:
            backup_path.write_bytes(self.settings_file.read_bytes())
            LOGGER.warning("%s: %s. Backed up to %s.", reason, self.settings_file, backup_path)
        except Exception as backup_exc:
            LOGGER.warning(
                "%s: %s. Could not create backup: %s.",
                reason,
                self.settings_file,
                backup_exc,
            )
        if exc is not None:
            LOGGER.debug("Settings load error", exc_info=exc)

    def save(self, settings: Mapping[str, Any]) -> None:
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.settings_file.with_suffix(".tmp")
        try:
            with open(tmp_path, "w", encoding="utf-8") as handle:
                json.dump(dict(settings), handle, indent=4)
            os.replace(tmp_path, self.settings_file)
        finally:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)

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
