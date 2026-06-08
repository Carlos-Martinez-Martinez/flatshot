"""Testable bridge service for the modern FlatShot desktop prototype."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import threading
from time import perf_counter
from typing import Any, Callable, Mapping
from uuid import uuid4

from PIL import Image

from flatshot.application.config_paths import ConfigPathResolver
from flatshot.application.contracts import ExportJobRequest, PreviewRequest
from flatshot.application.export_config_service import ExportConfigService
from flatshot.application.export_runner import (
    ExportRunner,
    OutputPathValidationError,
    get_enabled_export_variants,
    validate_export_requests_outputs,
)
from flatshot.application.folder_scanner import FolderScanner
from flatshot.application.preset_service import PresetService
from flatshot.application.preview_service import PreviewService
from flatshot.bridge import app_info as bridge_app_info
from flatshot.bridge.errors import BridgeError, InvalidRequestError
from flatshot.bridge.export_jobs import BridgeExportJob, ExportRunnerFactory
from flatshot.bridge.serialization import (
    batch_scan_result_to_dict,
    categorized_presets_to_dict,
    preview_result_to_dict,
    serialize_path,
)
from flatshot.core.models import ExportConfig, SHADOW_ENGINE_DEFAULT, normalize_shadow_settings
from flatshot.core.overrides import apply_image_override, normalize_image_override


MAX_PREVIEW_SIDE = 1200
DEFAULT_PREVIEW_SIDE = 900
MAX_THUMBNAIL_SIDE = 320
DEFAULT_THUMBNAIL_SIDE = 160
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
        export_config_service: ExportConfigService | None = None,
        export_runner_factory: ExportRunnerFactory = ExportRunner,
        config_resolver: ConfigPathResolver | None = None,
        folder_picker: Callable[[Path | None], Path | None] | None = None,
    ) -> None:
        self.folder_scanner = folder_scanner or FolderScanner()
        self.preview_service = preview_service or PreviewService()
        self.export_config_service = export_config_service or ExportConfigService()
        self.export_runner_factory = export_runner_factory
        self.config_resolver = config_resolver or ConfigPathResolver()
        self.folder_picker = folder_picker or pick_folder_with_tk
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

    def save_preset(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, Mapping):
            raise InvalidRequestError("Expected a JSON object.")

        name = _required_string(payload.get("name"), "name")
        raw_settings = payload.get("settings")
        if not isinstance(raw_settings, Mapping):
            raise InvalidRequestError("Field 'settings' must be an object.")

        try:
            settings = normalize_shadow_settings(
                self._preview_settings(raw_settings),
                missing_engine=SHADOW_ENGINE_DEFAULT,
            ).model_dump()
        except Exception as exc:
            raise InvalidRequestError("Field 'settings' contains invalid preset values.") from exc

        service = self._writable_preset_service()
        flat_presets = service.load_flat_presets()
        updated = PresetService.save_current_preset(flat_presets, name, settings)
        service.save_flat_presets_preserving_categories(updated)

        response = self.list_presets()
        response["ok"] = True
        response["activePreset"] = name
        return response

    def delete_preset(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, Mapping):
            raise InvalidRequestError("Expected a JSON object.")

        name = _required_string(payload.get("name"), "name")
        service = self._writable_preset_service()
        flat_presets = service.load_flat_presets()
        if len(flat_presets) <= 1:
            raise InvalidRequestError("At least one preset must remain.")

        try:
            updated = PresetService.delete_preset(flat_presets, name)
        except ValueError as exc:
            raise InvalidRequestError(str(exc)) from exc

        service.save_flat_presets_preserving_categories(updated)
        response = self.list_presets()
        response["ok"] = True
        response["activePreset"] = response["items"][0]["name"] if response.get("items") else None
        return response

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
        settings = normalize_shadow_settings(
            self._preview_settings(payload.get("settings", {})),
            missing_engine=SHADOW_ENGINE_DEFAULT,
        )
        local_override = normalize_image_override(payload.get("localOverride", {}))
        preview_settings = apply_image_override(settings, local_override)

        started = perf_counter()
        try:
            result = self.preview_service.render_preview(
                PreviewRequest(
                    image_path=image_path,
                    settings=preview_settings,
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

    def render_thumbnail(self, payload: Mapping[str, Any]) -> tuple[str, bytes]:
        if not isinstance(payload, Mapping):
            raise InvalidRequestError("Expected a JSON object.")

        image_path = self._preview_image_path(payload)
        size = min(_positive_int(payload.get("size"), "size", default=DEFAULT_THUMBNAIL_SIDE), MAX_THUMBNAIL_SIDE)

        try:
            with Image.open(image_path) as opened:
                thumbnail = opened.convert("RGBA")
                thumbnail.thumbnail((size, size), Image.Resampling.LANCZOS)
        except BridgeError:
            raise
        except Exception as exc:
            raise BridgeError("thumbnail_failed", "No se pudo generar la miniatura.", status=422) from exc

        buffer = BytesIO()
        thumbnail.save(buffer, format="PNG")
        return "image/png", buffer.getvalue()

    def prepare_export(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        requests, config = self._export_requests(payload)
        self._validate_export_outputs(requests)
        image_count = sum(len(request.input_files or []) for request in requests)
        variants = get_enabled_export_variants(config)
        destinations = self.export_config_service.destinations_for_folders(
            [request.input_folder for request in requests],
            config,
        )
        return {
            "ok": True,
            "sourceImages": image_count,
            "totalOutputs": image_count * len(variants),
            "destinations": [serialize_path(path) for path in destinations],
            "activeVariants": [
                {
                    "id": variant.id,
                    "label": variant.label,
                    "format": variant.format or config.format,
                    "outputWidth": variant.output_width or config.output_width,
                    "outputHeight": variant.output_height or config.output_height,
                    "destinationMode": variant.output_destination or config.output_destination,
                    "outputFolderName": variant.output_folder_name or config.output_folder_name,
                    "customOutputPath": variant.custom_output_path or config.custom_output_path,
                    "namingTemplate": variant.naming_template or config.naming_template,
                    "suffix": variant.suffix,
                }
                for variant in variants
            ],
            "errors": [],
        }

    def start_export(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        requests, config = self._export_requests(payload)
        self._validate_export_outputs(requests)
        image_count = sum(len(request.input_files or []) for request in requests)
        variants = get_enabled_export_variants(config)
        destinations = self.export_config_service.destinations_for_folders(
            [request.input_folder for request in requests],
            config,
        )
        job_id = uuid4().hex
        job = BridgeExportJob(
            job_id=job_id,
            requests=requests,
            source_images=image_count,
            total_outputs=image_count * len(variants),
            destinations=destinations,
            runner_factory=self.export_runner_factory,
        )
        with self._jobs_lock:
            self._jobs[job_id] = job
        job.start()
        return job.snapshot()

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

    def _export_requests(self, payload: Mapping[str, Any]) -> tuple[list[ExportJobRequest], ExportConfig]:
        if not isinstance(payload, Mapping):
            raise InvalidRequestError("Expected a JSON object.")

        image_paths = self._export_image_paths(payload.get("imagePaths"))
        settings = normalize_shadow_settings(
            self._preview_settings(payload.get("settings", {})),
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

    @staticmethod
    def _export_image_paths(raw_paths: Any) -> list[Path]:
        if not isinstance(raw_paths, list) or not raw_paths:
            raise InvalidRequestError("Field 'imagePaths' must be a non-empty list of paths.")

        paths: list[Path] = []
        for index, raw_path in enumerate(raw_paths):
            if not isinstance(raw_path, str) or not raw_path.strip():
                raise InvalidRequestError(f"Field 'imagePaths[{index}]' must be a non-empty path string.")
            path = Path(raw_path).expanduser()
            if not path.exists():
                raise BridgeError("export_file_not_found", "Imagen no encontrada.", status=404)
            if not path.is_file():
                raise InvalidRequestError(f"Field 'imagePaths[{index}]' must point to a file.")
            if path.suffix.lower() != ".png":
                raise BridgeError("unsupported_export_file", "Formato de exportación no soportado.", status=415)
            paths.append(path)
        return paths

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
        output_folder_name = _optional_string(raw_export.get("outputFolderName")) or (
            destination_value if output_destination == "subfolder" else None
        ) or "_SALIDA_PRO"

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


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise InvalidRequestError("Expected string value.")
    text = value.strip()
    return text or None


def _required_string(value: Any, field_name: str) -> str:
    text = _optional_string(value)
    if text is None:
        raise InvalidRequestError(f"Field '{field_name}' must be a non-empty string.")
    return text


def _export_size(raw_export: Mapping[str, Any]) -> tuple[int, int]:
    size = raw_export.get("size")
    if isinstance(size, str):
        normalized = size.lower().replace("×", "x")
        parts = normalized.split("x", 1)
        if len(parts) == 2:
            return (
                _positive_int(parts[0], "outputWidth", default=1800),
                _positive_int(parts[1], "outputHeight", default=2400),
            )

    return (
        _positive_int(raw_export.get("outputWidth"), "outputWidth", default=1800),
        _positive_int(raw_export.get("outputHeight"), "outputHeight", default=2400),
    )


def backgroundColorTuple(value: str) -> tuple[int, int, int]:
    if value == "white":
        return (255, 255, 255)
    return (230, 230, 230)
