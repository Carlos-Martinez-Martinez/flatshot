"""Qt-free session persistence service."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional


class SessionService:
    SESSION_DIR_NAME = ".flatshot"
    SESSION_FILE_NAME = "session.json"

    def __init__(
        self,
        session_file: str | Path,
        logger: logging.Logger | None = None,
    ) -> None:
        self.session_file = Path(session_file)
        self.logger = logger or logging.getLogger("flatshot.session")

    @staticmethod
    def default_session_file(home: str | Path | None = None) -> Path:
        base = Path(home) if home is not None else Path.home()
        return base / SessionService.SESSION_DIR_NAME / SessionService.SESSION_FILE_NAME

    def save_session(self, data: Mapping[str, Any]) -> bool:
        try:
            self.session_file.parent.mkdir(parents=True, exist_ok=True)
            with self.session_file.open("w", encoding="utf-8") as handle:
                json.dump(dict(data), handle, indent=2, ensure_ascii=False)
            self.logger.info("Session saved successfully")
            return True
        except Exception as exc:
            self.logger.error("Failed to save session: %s", exc)
            return False

    def load_session(self) -> Optional[dict[str, Any]]:
        if not self.session_file.exists():
            return None

        try:
            with self.session_file.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception as exc:
            self.logger.error("Failed to load session: %s", exc)
            return None

        if not isinstance(data, dict):
            self.logger.error("Failed to load session: session data is not an object")
            return None
        self.logger.info("Session loaded successfully")
        return data

    def clear_session(self) -> bool:
        try:
            if self.session_file.exists():
                self.session_file.unlink()
                self.logger.info("Session cleared")
            return True
        except Exception as exc:
            self.logger.error("Failed to clear session: %s", exc)
            return False

    @staticmethod
    def build_session_data(
        *,
        geometry: str,
        state: str,
        selected_folders: Iterable[str | Path],
        current_preset: str,
        current_mock: str,
        splitter_sizes: Iterable[int],
        output_folder_name: str | None,
        suffix: str | None,
        export_format: str | None,
        output_destination: str,
        custom_output_path: str | Path | None,
        shadow_settings: Mapping[str, Any],
    ) -> dict[str, Any]:
        custom_path = str(custom_output_path) if custom_output_path else None
        return {
            "geometry": geometry,
            "state": state,
            "selected_folders": [str(folder) for folder in selected_folders],
            "current_preset": current_preset,
            "current_mock": current_mock,
            "splitter_sizes": list(splitter_sizes),
            "export_config": {
                "output_folder_name": output_folder_name,
                "suffix": suffix,
                "format": export_format,
                "output_destination": output_destination,
                "custom_output_path": custom_path,
            },
            "shadow_settings": dict(shadow_settings),
        }
