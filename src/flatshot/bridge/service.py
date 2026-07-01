"""Testable bridge service for the modern FlatShot desktop prototype."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any, Callable, Mapping

from flatshot.application.config_paths import ConfigPathResolver
from flatshot.application.contracts import ExportJobRequest
from flatshot.application.export_config_service import ExportConfigService
from flatshot.application.export_runner import (
    ExportRunner,
    OutputPathValidationError,
    validate_export_requests_outputs,
)
from flatshot.application.folder_scanner import FolderScanner
from flatshot.application.preset_service import PresetService
from flatshot.application.preview_service import PreviewService
from flatshot.application.settings_service import SettingsService
from flatshot.bridge import app_info as bridge_app_info
from flatshot.bridge import export_endpoints, preferences, preset_endpoints, preview_endpoints
from flatshot.bridge.errors import BridgeError, InvalidRequestError
from flatshot.bridge.export_jobs import BridgeExportJob, ExportRunnerFactory
from flatshot.bridge.payload_helpers import (
    backgroundColorTuple,
)
from flatshot.bridge.payload_helpers import (
    export_size as _export_size,
)
from flatshot.bridge.payload_helpers import (
    optional_string as _optional_string,
)
from flatshot.bridge.payload_helpers import (
    preview_settings as _preview_settings,
)
from flatshot.bridge.serialization import (
    batch_scan_result_to_dict,
    serialize_path,
)
from flatshot.bridge.validation import export_image_paths
from flatshot.core.models import SHADOW_ENGINE_DEFAULT, ExportConfig, normalize_shadow_settings
from flatshot.core.overrides import normalize_image_override


class FlatShotBridgeService:
    """Small Qt-free facade over reusable application services."""

    def __init__(
        self,
        *,
        folder_scanner: FolderScanner | None = None,
        preview_service: PreviewService | None = None,
        export_config_service: ExportConfigService | None = None,
        export_runner_factory: ExportRunnerFactory = ExportRunner,
        config_resolver: ConfigPathResolver | None = None,
        folder_picker: Callable[[Path | None], Path | None] | None = None,
        max_concurrent_exports: int = 1,
    ) -> None:
        self.folder_scanner = folder_scanner or FolderScanner()
        self.preview_service = preview_service or PreviewService()
        self.export_config_service = export_config_service or ExportConfigService()
        self.export_runner_factory = export_runner_factory
        self.config_resolver = config_resolver or ConfigPathResolver()
        self.folder_picker = folder_picker or pick_folder_with_tk
        self.max_concurrent_exports = max_concurrent_exports
        self._jobs: dict[str, BridgeExportJob] = {}
        self._jobs_lock = threading.Lock()

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
        return preset_endpoints.list_presets(self)

    def save_preset(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        return preset_endpoints.save_preset(self, payload)

    def delete_preset(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        return preset_endpoints.delete_preset(self, payload)

    def load_ui_preferences(self) -> dict[str, Any]:
        return preferences.load_ui_preferences(self)

    def save_ui_preferences(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        return preferences.save_ui_preferences(self, payload)

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
        return preview_endpoints.render_preview(self, payload)

    def render_preview_binary(self, payload: Mapping[str, Any]) -> tuple[str, bytes, int, int, str | None]:
        return preview_endpoints.render_preview_binary(self, payload)

    def render_thumbnail(self, payload: Mapping[str, Any]) -> tuple[str, bytes]:
        return preview_endpoints.render_thumbnail(self, payload)

    def prepare_export(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        return export_endpoints.prepare_export(self, payload)

    def start_export(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        return export_endpoints.start_export(self, payload)

    def export_status(self, job_id: str) -> dict[str, Any]:
        return self._job(job_id).snapshot()

    def pause_export(self, job_id: str) -> dict[str, Any]:
        job = self._job(job_id)
        job.pause()
        return job.snapshot()

    def resume_export(self, job_id: str) -> dict[str, Any]:
        job = self._job(job_id)
        job.resume()
        return job.snapshot()

    def cancel_export(self, job_id: str) -> dict[str, Any]:
        job = self._job(job_id)
        job.cancel()
        return job.snapshot()

    def _export_requests(self, payload: Mapping[str, Any]) -> tuple[list[ExportJobRequest], ExportConfig]:
        if not isinstance(payload, Mapping):
            raise InvalidRequestError("Expected a JSON object.")

        image_paths = export_image_paths(payload.get("imagePaths"))
        settings = normalize_shadow_settings(
            _preview_settings(payload.get("settings", {})),
            missing_engine=SHADOW_ENGINE_DEFAULT,
        )
        raw_image_overrides = payload.get("imageOverrides", {})
        if raw_image_overrides is None:
            raw_image_overrides = {}
        if not isinstance(raw_image_overrides, Mapping):
            raise InvalidRequestError("Field 'imageOverrides' must be an object when provided.")
        image_overrides = {
            str(key): normalized
            for key, value in raw_image_overrides.items()
            if (normalized := normalize_image_override(value))
        }
        export_config = self._export_config(payload.get("export", {}))
        errors = self.export_config_service.validate(export_config)
        if errors:
            raise InvalidRequestError(errors[0])

        grouped: dict[Path, list[Path]] = {}
        for image_path in image_paths:
            grouped.setdefault(image_path.parent, []).append(image_path)

        return (
            [
                ExportJobRequest(
                    input_folder=folder,
                    input_files=sorted(paths),
                    settings=settings,
                    export_config=export_config,
                    curve_data=None,
                    preset_name=_optional_string(payload.get("presetName")),
                    image_overrides=image_overrides,
                )
                for folder, paths in sorted(grouped.items(), key=lambda item: str(item[0]))
            ],
            export_config,
        )

    @staticmethod
    def _validate_export_outputs(requests: list[ExportJobRequest]) -> None:
        try:
            validate_export_requests_outputs(requests)
        except OutputPathValidationError as exc:
            raise BridgeError("export_output_collision", str(exc), status=409) from exc

    def _export_config(self, raw_export: Any) -> ExportConfig:
        if raw_export is None:
            raw_export = {}
        if not isinstance(raw_export, Mapping):
            raise InvalidRequestError("Field 'export' must be an object when provided.")

        width, height = _export_size(raw_export)
        background = str(raw_export.get("background", "rgb230"))
        destination_mode = str(raw_export.get("destinationMode", "source"))
        destination_value = _optional_string(raw_export.get("destinationValue"))
        output_destination = "custom" if destination_mode == "custom" else "subfolder"
        custom_output_path = _optional_string(raw_export.get("customOutputPath")) or (
            destination_value if output_destination == "custom" else None
        )
        output_folder_name = (
            _optional_string(raw_export.get("outputFolderName"))
            or (destination_value if output_destination == "subfolder" else None)
            or "_SALIDA_PRO"
        )

        settings = {
            "format": raw_export.get("format", "JPG"),
            "output_width": width,
            "output_height": height,
            "transparent_bg": background == "transparent",
            "bg_color": backgroundColorTuple(background),
            "output_folder_name": output_folder_name,
            "suffix": raw_export.get("suffix", "_PRO"),
            "naming_template": raw_export.get("namingTemplate", "{original}{suffix}"),
            "output_destination": output_destination,
            "custom_output_path": custom_output_path,
            "variants": raw_export.get("variants", []),
        }
        return self.export_config_service.build_from_settings(settings)

    def _job(self, job_id: str) -> BridgeExportJob:
        if not isinstance(job_id, str) or not job_id.strip():
            raise InvalidRequestError("Job id is required.")
        with self._jobs_lock:
            job = self._jobs.get(job_id)
        if job is None:
            raise BridgeError("job_not_found", "Exportación no encontrada.", status=404)
        return job

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

    def _writable_preset_service(self) -> PresetService:
        config_dir = self.config_resolver.config_dir(create=False)
        if config_dir.exists() and not config_dir.is_dir():
            raise BridgeError("config_path_invalid", "Config path is not a directory.", status=409)
        return PresetService(config_dir)

    def _writable_settings_service(self) -> SettingsService:
        config_dir = self.config_resolver.config_dir(create=False)
        if config_dir.exists() and not config_dir.is_dir():
            raise BridgeError("config_path_invalid", "Config path is not a directory.", status=409)
        return SettingsService(config_dir / "settings.json")


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
