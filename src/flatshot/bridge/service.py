"""Testable bridge service for the modern FlatShot desktop prototype."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from flatshot.application.config_paths import ConfigPathResolver
from flatshot.application.folder_scanner import FolderScanner
from flatshot.application.preset_service import PresetService
from flatshot.bridge import app_info as bridge_app_info
from flatshot.bridge.errors import InvalidRequestError
from flatshot.bridge.serialization import batch_scan_result_to_dict, categorized_presets_to_dict


class FlatShotBridgeService:
    """Small Qt-free facade over reusable application services."""

    def __init__(
        self,
        *,
        folder_scanner: FolderScanner | None = None,
        config_resolver: ConfigPathResolver | None = None,
    ) -> None:
        self.folder_scanner = folder_scanner or FolderScanner()
        self.config_resolver = config_resolver or ConfigPathResolver()

    def health(self) -> dict[str, Any]:
        return {
            "ok": True,
            "service": bridge_app_info.BRIDGE_SERVICE_NAME,
            "mode": bridge_app_info.BRIDGE_MODE,
        }

    def app_info(self) -> dict[str, Any]:
        return bridge_app_info.app_info()

    def capabilities(self) -> dict[str, bool]:
        return bridge_app_info.capabilities()

    def list_presets(self) -> dict[str, Any]:
        config_dir = self.config_resolver.config_dir(create=False)
        source = "defaults"
        warning = None

        if config_dir.exists() and not config_dir.is_dir():
            categorized = PresetService.get_default_categorized_presets()
            warning = "Config path is not a directory. Default presets returned."
        elif config_dir.exists():
            service = PresetService(config_dir)
            if service.categorized_presets_path.exists():
                categorized = service.load_categorized_presets()
                source = "config"
            elif service.presets_path.exists():
                categorized = service.categorize_flat_presets(service.load_presets())
                source = "legacy-config"
            else:
                categorized = PresetService.get_default_categorized_presets()
        else:
            categorized = PresetService.get_default_categorized_presets()

        payload = categorized_presets_to_dict(categorized)
        payload["source"] = source
        if warning:
            payload["warning"] = warning
        return payload

    def scan_folders(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, Mapping):
            raise InvalidRequestError("Expected a JSON object.")

        raw_folders = payload.get("folders")
        if not isinstance(raw_folders, list):
            raise InvalidRequestError("Field 'folders' must be a list of paths.")

        folders: list[Path] = []
        for index, folder in enumerate(raw_folders):
            if not isinstance(folder, str) or not folder.strip():
                raise InvalidRequestError(f"Field 'folders[{index}]' must be a non-empty path string.")
            folders.append(Path(folder).expanduser())

        image_overrides = payload.get("imageOverrides", {})
        if image_overrides is None:
            image_overrides = {}
        if not isinstance(image_overrides, Mapping):
            raise InvalidRequestError("Field 'imageOverrides' must be an object when provided.")

        result = self.folder_scanner.scan_folders(folders, dict(image_overrides))
        return batch_scan_result_to_dict(result)
