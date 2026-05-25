"""Testable bridge service for the modern FlatShot desktop prototype."""
from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Any, Callable, Mapping

from flatshot.application.config_paths import ConfigPathResolver
from flatshot.application.contracts import PreviewRequest
from flatshot.application.folder_scanner import FolderScanner
from flatshot.application.preset_service import PresetService
from flatshot.application.preview_service import PreviewService
from flatshot.bridge import app_info as bridge_app_info
from flatshot.bridge.errors import BridgeError, InvalidRequestError
from flatshot.bridge.serialization import (
    batch_scan_result_to_dict,
    categorized_presets_to_dict,
    preview_result_to_dict,
    serialize_path,
)


MAX_PREVIEW_SIDE = 1200
DEFAULT_PREVIEW_SIDE = 900
SUPPORTED_PREVIEW_SUFFIXES = {".png"}
PREVIEW_SETTING_ALIASES = {
    "transparentBg": "transparent_bg",
    "bgColor": "bg_color",
    "scaleAdjustment": "scale_adjustment",
    "shadowEngine": "shadow_engine",
    "contactBlur": "contact_blur",
    "adaptiveZoom": "adaptive_zoom",
}
PREVIEW_SETTING_KEYS = {
    "angle",
    "distance",
    "blur",
    "spread",
    "fusion",
    "opacity",
    "noise",
    "padding",
    "contact_blur",
    "contraction",
    "adaptive_zoom",
    "scale_adjustment",
    "shadow_engine",
    "transparent_bg",
    "bg_color",
}


class FlatShotBridgeService:
    """Small Qt-free facade over reusable application services."""

    def __init__(
        self,
        *,
        folder_scanner: FolderScanner | None = None,
        preview_service: PreviewService | None = None,
        config_resolver: ConfigPathResolver | None = None,
        folder_picker: Callable[[Path | None], Path | None] | None = None,
    ) -> None:
        self.folder_scanner = folder_scanner or FolderScanner()
        self.preview_service = preview_service or PreviewService()
        self.config_resolver = config_resolver or ConfigPathResolver()
        self.folder_picker = folder_picker or pick_folder_with_tk

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

    def pick_folder(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, Mapping):
            raise InvalidRequestError("Expected a JSON object.")

        initial_path = self._folder_picker_initial_path(payload.get("initialPath"))
        try:
            selected = self.folder_picker(initial_path)
        except BridgeError:
            raise
        except Exception as exc:
            raise BridgeError("folder_picker_unavailable", "Selector de carpeta no disponible.", status=503) from exc

        if selected is None:
            return {"ok": True, "selected": False, "path": None}

        return {"ok": True, "selected": True, "path": serialize_path(selected)}

    def render_preview(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, Mapping):
            raise InvalidRequestError("Expected a JSON object.")

        image_path = self._preview_image_path(payload)
        target_size = self._preview_target_size(payload)
        settings = self._preview_settings(payload.get("settings", {}))

        started = perf_counter()
        try:
            result = self.preview_service.render_preview(
                PreviewRequest(
                    image_path=image_path,
                    settings=settings,
                    target_size=target_size,
                    scale_factor=1.0,
                    is_preview=True,
                )
            )
        except BridgeError:
            raise
        except Exception as exc:
            raise BridgeError("preview_failed", "No se pudo generar la preview.", status=422) from exc

        elapsed_ms = int(round((perf_counter() - started) * 1000))
        return preview_result_to_dict(result, source_path=image_path, render_time_ms=elapsed_ms)

    @staticmethod
    def _preview_image_path(payload: Mapping[str, Any]) -> Path:
        raw_path = payload.get("imagePath")
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise InvalidRequestError("Field 'imagePath' must be a non-empty path string.")

        path = Path(raw_path).expanduser()
        if not path.exists():
            raise BridgeError("preview_file_not_found", "Imagen no encontrada.", status=404)
        if not path.is_file():
            raise InvalidRequestError("Field 'imagePath' must point to a file.")
        if path.suffix.lower() not in SUPPORTED_PREVIEW_SUFFIXES:
            raise BridgeError("unsupported_preview_file", "Formato de imagen no soportado.", status=415)
        return path

    @staticmethod
    def _preview_target_size(payload: Mapping[str, Any]) -> tuple[int, int]:
        width = _positive_int(payload.get("targetWidth"), "targetWidth", default=DEFAULT_PREVIEW_SIDE)
        height = _positive_int(payload.get("targetHeight"), "targetHeight", default=DEFAULT_PREVIEW_SIDE)
        return min(width, MAX_PREVIEW_SIDE), min(height, MAX_PREVIEW_SIDE)

    @staticmethod
    def _preview_settings(raw_settings: Any) -> dict[str, Any]:
        if raw_settings is None:
            return {}
        if not isinstance(raw_settings, Mapping):
            raise InvalidRequestError("Field 'settings' must be an object when provided.")

        settings: dict[str, Any] = {}
        for key, value in raw_settings.items():
            normalized_key = PREVIEW_SETTING_ALIASES.get(str(key), str(key))
            if normalized_key in PREVIEW_SETTING_KEYS:
                settings[normalized_key] = value
        return settings

    @staticmethod
    def _folder_picker_initial_path(value: Any) -> Path | None:
        if value in (None, ""):
            return None
        if not isinstance(value, str):
            raise InvalidRequestError("Field 'initialPath' must be a path string when provided.")

        path = Path(value).expanduser()
        if path.exists() and path.is_dir():
            return path
        if path.exists() and path.is_file():
            return path.parent
        return None


def pick_folder_with_tk(initial_path: Path | None = None) -> Path | None:
    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception as exc:
        raise BridgeError("folder_picker_unavailable", "Selector de carpeta no disponible.", status=503) from exc

    root = tk.Tk()
    root.withdraw()
    root.update()
    try:
        try:
            root.attributes("-topmost", True)
        except tk.TclError:
            pass
        selected = filedialog.askdirectory(
            parent=root,
            title="Seleccionar carpeta FlatShot",
            initialdir=str(initial_path or Path.home()),
            mustexist=True,
        )
    finally:
        root.destroy()

    return Path(selected).expanduser() if selected else None


def _positive_int(value: Any, field_name: str, *, default: int) -> int:
    if value is None:
        return default
    if isinstance(value, bool):
        raise InvalidRequestError(f"Field '{field_name}' must be a positive integer.")
    try:
        numeric = int(value)
    except (TypeError, ValueError) as exc:
        raise InvalidRequestError(f"Field '{field_name}' must be a positive integer.") from exc
    if numeric <= 0:
        raise InvalidRequestError(f"Field '{field_name}' must be a positive integer.")
    return numeric
