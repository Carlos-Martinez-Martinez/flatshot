"""Testable bridge service for the modern FlatShot desktop prototype."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any, Callable, Mapping

from flatshot.application.config_paths import ConfigPathResolver
from flatshot.application.export_config_service import ExportConfigService
from flatshot.application.export_runner import ExportRunner
from flatshot.application.folder_scanner import FolderScanner
from flatshot.application.preset_service import PresetService
from flatshot.application.preview_service import PreviewService
from flatshot.application.settings_service import SettingsService
from flatshot.bridge import app_info as bridge_app_info
from flatshot.bridge import export_endpoints, export_requests, preferences, preset_endpoints, preview_endpoints
from flatshot.bridge.errors import BridgeError, InvalidRequestError
from flatshot.bridge.export_jobs import BridgeExportJob, ExportRunnerFactory
from flatshot.bridge.onboarding_assets import onboarding_assets_folder, open_folder_with_system
from flatshot.bridge.path_policy import TrustedPathPolicy
from flatshot.bridge.serialization import (
    batch_scan_result_to_dict,
    serialize_path,
)


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
        folder_opener: Callable[[Path], None] | None = None,
        max_concurrent_exports: int = 1,
        max_retained_jobs: int = 20,
        path_policy: TrustedPathPolicy | None = None,
    ) -> None:
        self.folder_scanner = folder_scanner or FolderScanner()
        self.preview_service = preview_service or PreviewService()
        self.export_config_service = export_config_service or ExportConfigService()
        self.export_runner_factory = export_runner_factory
        self.config_resolver = config_resolver or ConfigPathResolver()
        self.folder_picker = folder_picker or pick_folder_with_tk
        self.folder_opener = folder_opener or open_folder_with_system
        self.max_concurrent_exports = max_concurrent_exports
        self.max_retained_jobs = max(1, int(max_retained_jobs))
        self.path_policy = path_policy or TrustedPathPolicy()
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
            path = Path(folder).expanduser()
            folders.append(path)
            self.path_policy.register_root(path)

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

        self.path_policy.register_root(selected)
        return {"ok": True, "selected": True, "path": serialize_path(selected)}

    def open_onboarding_assets_folder(self) -> dict[str, Any]:
        folder = onboarding_assets_folder()
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise BridgeError("folder_open_unavailable", "No se pudo preparar la carpeta de fondos.", status=503) from exc
        try:
            self.folder_opener(folder)
        except BridgeError:
            raise
        except Exception as exc:
            raise BridgeError("folder_open_unavailable", "No se pudo abrir la carpeta de fondos.", status=503) from exc
        return {"ok": True, "path": serialize_path(folder)}

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

    def _export_requests(self, payload: Mapping[str, Any]):
        return export_requests.build_export_requests(self, payload)

    @staticmethod
    def _validate_export_outputs(requests) -> None:
        export_requests.validate_export_outputs(requests)

    def _export_config(self, raw_export: Any):
        return export_requests.build_export_config(self.export_config_service, raw_export)

    def _job(self, job_id: str) -> BridgeExportJob:
        if not isinstance(job_id, str) or not job_id.strip():
            raise InvalidRequestError("Job id is required.")
        with self._jobs_lock:
            job = self._jobs.get(job_id)
        if job is None:
            raise BridgeError("job_not_found", "Exportación no encontrada.", status=404)
        return job

    def _prune_finished_jobs_locked(self, *, reserve_slots: int = 0) -> None:
        retained_limit = max(0, self.max_retained_jobs - max(0, int(reserve_slots)))
        finished_jobs = sorted(
            (
                (job_id, job)
                for job_id, job in self._jobs.items()
                if job.is_terminal
            ),
            key=lambda item: item[1].retention_timestamp,
        )
        remove_count = len(finished_jobs) - retained_limit
        if remove_count <= 0:
            return
        for job_id, _job in finished_jobs[:remove_count]:
            del self._jobs[job_id]

    def _validate_image_path_access(self, path: Path) -> None:
        self.path_policy.validate_image_path(path)

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
