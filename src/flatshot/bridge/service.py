"""Testable bridge service for the modern FlatShot desktop prototype."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any, Callable, Mapping
from uuid import uuid4

from flatshot.application.config_paths import ConfigPathResolver
from flatshot.application.export_config_service import ExportConfigService
from flatshot.application.export_preflight import ensure_export_space
from flatshot.application.folder_scan_jobs import FolderScanJob
from flatshot.application.export_runner import ExportRunner
from flatshot.application.folder_scanner import FolderScanner
from flatshot.application.preset_service import PresetService
from flatshot.application.preview_service import PreviewService
from flatshot.application.settings_service import SettingsService
from flatshot.bridge import app_info as bridge_app_info
from flatshot.bridge import export_endpoints, export_requests, preferences, preset_endpoints
from flatshot.bridge import preview_endpoints, scan_job_endpoints, scan_requests
from flatshot.bridge.errors import BridgeError, InvalidRequestError
from flatshot.bridge.export_job_repository import ExportJobRepository
from flatshot.bridge.export_jobs import BridgeExportJob, ExportRunnerFactory
from flatshot.bridge.image_registry import BridgeImageRegistry
from flatshot.bridge.onboarding_assets import onboarding_assets_folder, open_folder_with_system
from flatshot.bridge.path_policy import TrustedPathPolicy
from flatshot.bridge.serialization import batch_scan_result_to_dict, serialize_path
from flatshot.utils.thumbnail_cache import ThumbnailCache


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
        thumbnail_cache: ThumbnailCache | None = None,
        image_registry: BridgeImageRegistry | None = None,
        export_job_repository: ExportJobRepository | None = None,
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
        self.thumbnail_cache = thumbnail_cache
        self.image_registry = image_registry or BridgeImageRegistry()
        self.export_job_repository = export_job_repository or ExportJobRepository(
            self.config_resolver.config_dir(create=False) / "export-manifests"
        )
        self._jobs: dict[str, BridgeExportJob] = {}
        self._jobs_lock = threading.Lock()
        self._scan_jobs: dict[str, FolderScanJob] = {}
        self._scan_jobs_lock = threading.Lock()

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
        folders, image_overrides, verify_images, recursive = self._scan_request(payload)
        result = self.folder_scanner.scan_folders(
            folders,
            dict(image_overrides),
            verify_images=verify_images,
            recursive=recursive,
        )
        return batch_scan_result_to_dict(result, image_id_for_path=self.image_registry.register)

    def start_scan_job(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        folders, image_overrides, verify_images, recursive = self._scan_request(payload)
        job = FolderScanJob(
            job_id=uuid4().hex,
            folders=folders,
            image_overrides=dict(image_overrides),
            scanner=self.folder_scanner,
            verify_images=verify_images,
            recursive=recursive,
        )
        with self._scan_jobs_lock:
            self._prune_finished_scan_jobs_locked(reserve_slots=1)
            self._scan_jobs[job.job_id] = job
        job.start()
        return scan_job_endpoints.scan_job_snapshot(job, image_id_for_path=self.image_registry.register)

    def scan_job_status(
        self,
        job_id: str,
        *,
        image_offset: int = 0,
        image_limit: int | None = None,
    ) -> dict[str, Any]:
        return scan_job_endpoints.scan_job_snapshot(
            self._scan_job(job_id),
            image_offset=image_offset,
            image_limit=image_limit,
            image_id_for_path=self.image_registry.register,
        )

    def cancel_scan_job(self, job_id: str) -> dict[str, Any]:
        job = self._scan_job(job_id)
        job.cancel()
        return scan_job_endpoints.scan_job_snapshot(job, image_id_for_path=self.image_registry.register)

    def _scan_request(self, payload: Mapping[str, Any]) -> tuple[list[Path], dict, bool, bool]:
        return scan_requests.parse_scan_request(payload, self.path_policy)

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

    def _validate_export_outputs(self, requests) -> None:
        export_requests.validate_export_outputs(requests, path_policy=self.path_policy)

    def _ensure_export_space(self, requests) -> None:
        ensure_export_space(requests)

    def _export_config(self, raw_export: Any):
        return export_requests.build_export_config(self.export_config_service, raw_export)

    def _thumbnail_cache(self) -> ThumbnailCache:
        if self.thumbnail_cache is None:
            self.thumbnail_cache = ThumbnailCache(self.config_resolver.config_dir() / "thumbnail-cache")
        return self.thumbnail_cache

    def _job(self, job_id: str) -> BridgeExportJob:
        if not isinstance(job_id, str) or not job_id.strip():
            raise InvalidRequestError("Job id is required.")
        with self._jobs_lock:
            job = self._jobs.get(job_id)
        if job is None:
            raise BridgeError("job_not_found", "Exportación no encontrada.", status=404)
        return job

    def _scan_job(self, job_id: str) -> FolderScanJob:
        if not isinstance(job_id, str) or not job_id.strip():
            raise InvalidRequestError("Scan job id is required.")
        with self._scan_jobs_lock:
            job = self._scan_jobs.get(job_id)
        if job is None:
            raise BridgeError("scan_job_not_found", "Escaneo no encontrado.", status=404)
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

    def _prune_finished_scan_jobs_locked(self, *, reserve_slots: int = 0) -> None:
        retained_limit = max(0, self.max_retained_jobs - max(0, int(reserve_slots)))
        finished_jobs = sorted(
            (
                (job_id, job)
                for job_id, job in self._scan_jobs.items()
                if job.is_terminal
            ),
            key=lambda item: item[1].retention_timestamp,
        )
        remove_count = len(finished_jobs) - retained_limit
        if remove_count <= 0:
            return
        for job_id, _job in finished_jobs[:remove_count]:
            del self._scan_jobs[job_id]

    def _validate_image_path_access(self, path: Path) -> None:
        self.path_policy.validate_image_path(path)

    def _validate_output_path_access(self, path: Path) -> None:
        self.path_policy.validate_output_path(path)

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
