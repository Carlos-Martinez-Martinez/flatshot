"""Qt-free export runner and export planning helpers."""
from __future__ import annotations

import os
import shutil
import tempfile
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from pathlib import Path
from time import time
from typing import Callable, Protocol

from PIL import Image

from flatshot.application.contracts import ExportJobRequest, ExportJobResult
from flatshot.application.events import (
    ExportEvent,
    ExportFinishedEvent,
    ExportImageCompletedEvent,
    ExportLogEvent,
    ExportProgressEvent,
    ExportStartedEvent,
)
from flatshot.application.execution_control import CancellationToken, PauseToken
from flatshot.core.engine import ShadowEngine
from flatshot.core.models import (
    CurveData,
    ExportConfig,
    ExportVariant,
    SHADOW_ENGINE_DEFAULT,
    build_variant_settings,
    normalize_export_variants,
    normalize_shadow_settings,
)
from flatshot.core.overrides import apply_image_override, override_key
from flatshot.application.export_config_service import (
    variant_base_destination as variant_base_output_folder,
    variant_output_folder,
)
from flatshot.utils.render_cache import RenderCache


EXPORT_OUTPUT_COLLISION_MESSAGE = (
    "Hay archivos de salida repetidos o ya existentes. "
    "Cambia el destino, el sufijo o el patrón de nombre antes de exportar."
)


class OutputPathValidationError(ValueError):
    """Raised when planned export outputs are not safe to write."""


class ExportEventSink(Protocol):
    def emit(self, event: ExportEvent) -> None:
        ...


def apply_naming_template(
    template: str,
    original_name: str,
    suffix: str,
    folder_name: str,
    index: int,
    variant_label: str = "",
    variant_id: str = "",
    bg: str = "",
) -> str:
    """
    Apply naming template to generate output filename.

    Supported placeholders:
    - {original}: Original filename without extension
    - {suffix}: The suffix from export config
    - {folder}: Parent folder name
    - {variant}: Output variant label
    - {variant_id}: Output variant id
    - {bg}: Output background as RRGGBB
    - {index}: Zero-padded index (e.g., 001, 002)
    - {index:03d}: Custom padding format
    """
    result = template
    result = result.replace("{original}", original_name)
    result = result.replace("{suffix}", suffix)
    result = result.replace("{folder}", folder_name)
    result = result.replace("{variant}", _safe_filename_token(variant_label))
    result = result.replace("{variant_id}", _safe_filename_token(variant_id))
    result = result.replace("{bg}", _safe_filename_token(bg))

    if "{index:" in result:
        import re

        match = re.search(r"\{index:(\d+)d\}", result)
        if match:
            padding = int(match.group(1))
            result = re.sub(r"\{index:\d+d\}", str(index).zfill(padding), result)
    else:
        result = result.replace("{index}", str(index).zfill(3))

    return result


def _safe_filename_token(value: str) -> str:
    text = str(value or "").strip()
    for char in '<>:"/\\|?*':
        text = text.replace(char, "_")
    text = "".join("_" if ord(ch) < 32 else ch for ch in text)
    return text.strip(" .")


def variant_bg_token(variant: ExportVariant) -> str:
    return "{:02X}{:02X}{:02X}".format(*variant.bg_color)


def get_enabled_export_variants(export_config: ExportConfig) -> list[ExportVariant]:
    return [variant for variant in normalize_export_variants(export_config) if variant.enabled]


def variant_export_format(export_config: ExportConfig, variant: ExportVariant) -> str:
    return RenderCache.normalize_format(variant.format or export_config.format)


def variant_naming_template(export_config: ExportConfig, variant: ExportVariant) -> str:
    return variant.naming_template or export_config.naming_template


def variant_target_size(export_config: ExportConfig, variant: ExportVariant) -> tuple[int, int]:
    return (
        int(variant.output_width or export_config.output_width),
        int(variant.output_height or export_config.output_height),
    )


def build_variant_output_path(
    base_output_folder: Path,
    export_config: ExportConfig,
    variant: ExportVariant,
    original_name: str,
    folder_name: str,
    index: int,
) -> tuple[Path, str]:
    fmt = variant_export_format(export_config, variant)
    output_folder = variant_output_folder(base_output_folder, variant)
    base_name = apply_naming_template(
        variant_naming_template(export_config, variant),
        original_name,
        variant.suffix,
        folder_name,
        index,
        variant_label=variant.label,
        variant_id=variant.id,
        bg=variant_bg_token(variant),
    )
    return output_folder / f"{base_name}.{fmt}", fmt


def _path_collision_key(path: Path) -> str:
    return os.path.normcase(os.path.abspath(str(path)))


def validate_output_path_collisions(planned_outputs: list[dict], *, check_existing: bool = True) -> None:
    seen: dict[str, dict] = {}
    for item in planned_outputs:
        key = _path_collision_key(Path(item["save_path"]))
        previous = seen.get(key)
        if previous is None:
            seen[key] = item
            continue

        current_variant = item["variant"]
        previous_variant = previous["variant"]
        if current_variant.id != previous_variant.id:
            raise OutputPathValidationError(
                f"{EXPORT_OUTPUT_COLLISION_MESSAGE} "
                "Las variantes "
                f"{previous_variant.label} y {current_variant.label} generarían el mismo archivo. "
                "Cambia el sufijo o la subcarpeta."
            )

        raise OutputPathValidationError(
            f"{EXPORT_OUTPUT_COLLISION_MESSAGE} "
            f"Dos entradas generarían el mismo archivo: {Path(item['save_path']).name}. "
            "Cambia la plantilla de nombre, el sufijo o la subcarpeta."
        )

    if not check_existing:
        return

    for item in planned_outputs:
        save_path = Path(item["save_path"])
        try:
            exists = save_path.exists()
        except OSError as exc:
            raise OutputPathValidationError(
                f"{EXPORT_OUTPUT_COLLISION_MESSAGE} "
                f"No se pudo comprobar la salida {save_path.name}."
            ) from exc
        if exists:
            raise OutputPathValidationError(
                f"{EXPORT_OUTPUT_COLLISION_MESSAGE} "
                f"Ya existe una salida llamada {save_path.name}."
            )


def planned_output_paths_for_request(request: ExportJobRequest) -> list[dict]:
    """Plan the output paths for a single request without touching the filesystem."""
    if request.input_files is not None:
        image_paths = [Path(p) for p in request.input_files]
        image_paths = [p for p in image_paths if p.is_file() and p.suffix.lower() == ".png"]
    else:
        image_paths = [
            path
            for path in request.input_folder.iterdir()
            if path.is_file() and path.suffix.lower() == ".png"
        ]

    enabled_variants = get_enabled_export_variants(request.export_config)
    parent_folder_name = request.input_folder.name
    planned_outputs: list[dict] = []

    for index, img_path in enumerate(sorted(image_paths, key=lambda path: path.name), start=1):
        for variant in enabled_variants:
            base_output_folder = variant_base_output_folder(
                request.input_folder,
                request.export_config,
                variant,
            )
            save_path, fmt = build_variant_output_path(
                base_output_folder,
                request.export_config,
                variant,
                img_path.stem,
                parent_folder_name,
                index,
            )
            planned_outputs.append(
                {
                    "save_path": save_path,
                    "variant": variant,
                    "image_path": img_path,
                    "format": fmt,
                    "input_folder": request.input_folder,
                }
            )

    return planned_outputs


def planned_output_paths_for_requests(requests: list[ExportJobRequest]) -> list[dict]:
    planned_outputs: list[dict] = []
    for request in requests:
        planned_outputs.extend(planned_output_paths_for_request(request))
    return planned_outputs


def validate_export_requests_outputs(
    requests: list[ExportJobRequest],
    *,
    check_existing: bool = True,
) -> list[dict]:
    planned_outputs = planned_output_paths_for_requests(requests)
    validate_output_path_collisions(planned_outputs, check_existing=check_existing)
    return planned_outputs


def process_single_image(args):
    """Process a single image in a worker process."""
    (
        img_path,
        save_path,
        settings_dict,
        target_size,
        fmt,
        curve_data_dict,
        local_override,
        display_name,
    ) = args

    try:
        settings = apply_image_override(
            normalize_shadow_settings(
                settings_dict,
                missing_engine=SHADOW_ENGINE_DEFAULT,
            ),
            local_override,
        )
        curve_data = CurveData(**curve_data_dict) if curve_data_dict else None

        original = Image.open(img_path).convert("RGBA")
        dpi = original.info.get("dpi", (300, 300))

        final_img, diagnostics = ShadowEngine._aplicar_efectos_with_diagnostics(
            original,
            settings,
            target_size,
            scale_factor=1.0,
            curve_data=curve_data,
        )
        warning = diagnostics.warning if diagnostics.fallback_used else None

        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        if fmt in ["jpg", "jpeg"]:
            final_img = final_img.convert("RGB")
            final_img.save(save_path, quality=100, subsampling=0, dpi=dpi)
        else:
            final_img.save(save_path, optimize=False, compress_level=0, dpi=dpi)

        return True, display_name, warning
    except Exception as e:
        return False, f"{img_path.name}: {e}", None


def copy_stable(src: Path, dest: Path, copy_file: Callable = shutil.copy2) -> bool:
    """Copy a file while ensuring we capture a stable snapshot."""
    for _ in range(3):
        try:
            before = src.stat()
        except FileNotFoundError:
            return False
        try:
            copy_file(src, dest)
        except Exception:
            return False
        try:
            after = src.stat()
        except FileNotFoundError:
            try:
                dest.unlink(missing_ok=True)
            except Exception:
                pass
            return False
        if before.st_mtime_ns == after.st_mtime_ns and before.st_size == after.st_size:
            return True
        try:
            dest.unlink(missing_ok=True)
        except Exception:
            pass
    return False


class ExportRunner:
    def __init__(
        self,
        event_sink: ExportEventSink | None = None,
        cancellation_token: CancellationToken | None = None,
        pause_token: PauseToken | None = None,
        *,
        executor_factory=ProcessPoolExecutor,
        image_processor: Callable = process_single_image,
        copy_file: Callable = shutil.copy2,
    ):
        self.event_sink = event_sink
        self.cancellation_token = cancellation_token or CancellationToken()
        self.pause_token = pause_token or PauseToken()
        self.executor_factory = executor_factory
        self.image_processor = image_processor
        self.copy_file = copy_file
        self.executor = None
        self._snapshot_dir: Path | None = None

    def run(self, request: ExportJobRequest) -> ExportJobResult:
        start_time = time()
        completed_count = 0
        error_count = 0
        total = 0
        destinations: list[Path] = []

        try:
            image_items = self._snapshot_image_items(request)
            source_total = len(image_items)
            if source_total == 0:
                result = ExportJobResult(True, 0, 0, 0, 0.0, destinations)
                self._emit(ExportFinishedEvent(True, 0, 0, 0, 0.0))
                return result

            enabled_variants = get_enabled_export_variants(request.export_config)
            total = source_total * len(enabled_variants)
            self._emit(ExportStartedEvent(source_total, total))
            if not enabled_variants:
                self._emit(ExportLogEvent("No hay variantes de salida activas. Activa al menos una salida."))
                duration = time() - start_time
                result = ExportJobResult(False, 0, 0, 0, duration, destinations)
                self._emit(ExportFinishedEvent(False, 0, 0, 0, duration))
                return result

            self._emit(
                ExportLogEvent("Salidas activas: " + ", ".join(variant.label for variant in enabled_variants))
            )

            curve_data_dict = request.curve_data.model_dump() if request.curve_data else None
            parent_folder_name = request.input_folder.name
            cache = RenderCache()

            tasks = []
            cached_tasks = []
            planned_outputs = []

            for index, (img_path, local_key, cache_identity_path) in enumerate(
                sorted(image_items, key=lambda item: item[0].name),
                start=1,
            ):
                local_override = dict(request.image_overrides or {}).get(local_key, {})

                for variant in enabled_variants:
                    variant_settings = build_variant_settings(request.settings, variant)
                    settings_dict = variant_settings.model_dump()
                    target_size = variant_target_size(request.export_config, variant)
                    variant_base_folder = variant_base_output_folder(
                        request.input_folder,
                        request.export_config,
                        variant,
                    )
                    save_path, fmt = build_variant_output_path(
                        variant_base_folder,
                        request.export_config,
                        variant,
                        img_path.stem,
                        parent_folder_name,
                        index,
                    )
                    display_name = f"{img_path.name} · {variant.label}"
                    task_args = (
                        img_path,
                        save_path,
                        settings_dict,
                        target_size,
                        fmt,
                        curve_data_dict,
                        local_override,
                        display_name,
                    )
                    key = cache.get_cache_key(
                        str(cache_identity_path),
                        settings_dict,
                        curve_data_dict,
                        target_size,
                        local_override,
                        fmt,
                    )
                    planned_outputs.append(
                        {
                            "save_path": save_path,
                            "variant": variant,
                            "image_path": img_path,
                        }
                    )
                    if cache.exists(key, fmt, validate=True):
                        cached_tasks.append(
                            {
                                "img_path": img_path,
                                "key": key,
                                "fmt": fmt,
                                "save_path": save_path,
                                "task_args": task_args,
                                "display_name": display_name,
                            }
                        )
                    else:
                        tasks.append(task_args)

            try:
                validate_output_path_collisions(planned_outputs)
                destinations = sorted(
                    {Path(item["save_path"]).parent for item in planned_outputs},
                    key=lambda path: str(path),
                )
                for folder in destinations:
                    folder.mkdir(parents=True, exist_ok=True)
            except Exception as exc:
                message = str(exc)
                if isinstance(exc, OutputPathValidationError):
                    message = f"Error: Exportación: {message}"
                self._emit(ExportLogEvent(message))
                duration = time() - start_time
                result = ExportJobResult(False, 0, total, 0, duration, destinations)
                self._emit(ExportFinishedEvent(False, 0, total, 0, duration))
                return result

            completed_count, error_count, fallback = self._export_cached_tasks(
                cached_tasks,
                cache,
                completed_count,
                error_count,
                total,
            )

            if fallback:
                tasks.extend(fallback)

            if tasks and not self.cancellation_token.cancelled:
                self.pause_token.wait_if_paused()
                if self.cancellation_token.cancelled:
                    self._emit(ExportLogEvent("Exportación cancelada."))
                else:
                    completed_count, error_count = self._export_render_tasks(
                    tasks,
                    completed_count,
                    error_count,
                    total,
                )

        except Exception as exc:
            self._emit(ExportLogEvent(f"Error crítico en ExportRunner: {exc}"))
        finally:
            if self._snapshot_dir:
                shutil.rmtree(self._snapshot_dir, ignore_errors=True)
            if self.executor:
                self.executor.shutdown(wait=False, cancel_futures=True)

        duration = time() - start_time
        success = not self.cancellation_token.cancelled and error_count == 0
        result = ExportJobResult(success, completed_count, total, error_count, duration, destinations)
        self._emit(ExportFinishedEvent(success, completed_count, total, error_count, duration))
        return result

    def _snapshot_image_items(self, request: ExportJobRequest) -> list[tuple[Path, str, Path]]:
        if request.input_files is not None:
            source_files = [Path(p) for p in request.input_files]
            source_files = [p for p in source_files if p.is_file() and p.suffix.lower() == ".png"]
            snap_dir = Path(tempfile.mkdtemp(prefix="flatshot_snap_"))
            self._snapshot_dir = snap_dir
            image_items = []
            for src in source_files:
                dest = snap_dir / src.name
                if copy_stable(src, dest, self.copy_file):
                    image_items.append((dest, override_key(src), src))
            return image_items

        return [
            (f, override_key(f), f)
            for f in request.input_folder.iterdir()
            if f.is_file() and f.suffix.lower() == ".png"
        ]

    @staticmethod
    def _base_output_folder(request: ExportJobRequest) -> Path:
        if request.export_config.output_destination == "custom" and request.export_config.custom_output_path:
            return Path(request.export_config.custom_output_path)
        return request.input_folder / request.export_config.output_folder_name

    def _export_cached_tasks(
        self,
        cached_tasks: list[dict],
        cache: RenderCache,
        completed_count: int,
        error_count: int,
        total: int,
    ) -> tuple[int, int, list]:
        if not cached_tasks:
            return completed_count, error_count, []

        fallback_tasks: list[tuple] = []
        self._emit(ExportLogEvent(f"Exportando {len(cached_tasks)} archivos desde caché..."))
        for cached in cached_tasks:
            if self.cancellation_token.cancelled:
                break
            self.pause_token.wait_if_paused()

            try:
                cache_path = cache.get_cached_path(cached["key"], cached["fmt"])
                save_path = Path(cached["save_path"])
                save_path.parent.mkdir(parents=True, exist_ok=True)
                self.copy_file(cache_path, save_path)

                completed_count += 1
                self._emit(ExportImageCompletedEvent(cached["display_name"], True))
                self._emit_progress(completed_count, total)
            except Exception as e:
                self._emit(
                    ExportLogEvent(
                        f"Caché no válida para {cached['display_name']}; renderizando normal ({e})"
                    )
                )
                fallback_tasks.append(cached["task_args"])

        return completed_count, error_count, fallback_tasks

    def _export_render_tasks(
        self,
        tasks: list[tuple],
        completed_count: int,
        error_count: int,
        total: int,
    ) -> tuple[int, int]:
        max_workers = max(1, (os.cpu_count() or 2) - 1)
        self._emit(ExportLogEvent(f"Procesando {len(tasks)} archivos restantes con {max_workers} núcleos..."))

        try:
            with self.executor_factory(max_workers=max_workers) as executor:
                self.executor = executor
                pending_tasks = iter(tasks)
                in_flight = set()

                for _ in range(min(max_workers, len(tasks))):
                    try:
                        in_flight.add(executor.submit(self.image_processor, next(pending_tasks)))
                    except StopIteration:
                        break

                while in_flight and not self.cancellation_token.cancelled:
                    self.pause_token.wait_if_paused()
                    if self.cancellation_token.cancelled:
                        break

                    done, _ = wait(in_flight, timeout=0.2, return_when=FIRST_COMPLETED)
                    if not done:
                        continue

                    for future in done:
                        in_flight.discard(future)
                        try:
                            success, msg, warning = future.result()
                        except Exception as exc:
                            success, msg, warning = False, f"Worker error: {exc}", None

                        if success:
                            if warning:
                                self._emit(ExportLogEvent(f"Aviso: {msg}: {warning}"))
                            self._emit(ExportImageCompletedEvent(msg, True))
                        else:
                            error_count += 1
                            self._emit(ExportLogEvent(f"Error: {msg}"))
                            self._emit(ExportImageCompletedEvent(msg.split(":")[0], False))

                        completed_count += 1
                        self._emit_progress(completed_count, total)

                        if not self.cancellation_token.cancelled and not self.pause_token.paused:
                            try:
                                in_flight.add(executor.submit(self.image_processor, next(pending_tasks)))
                            except StopIteration:
                                pass
        except Exception as exc:
            self._emit(ExportLogEvent(f"Error en el proceso de exportación: {exc}"))

        return completed_count, error_count

    def _emit_progress(self, completed_count: int, total: int) -> None:
        self._emit(ExportProgressEvent(completed_count, total, int((completed_count / total) * 100)))

    def _emit(self, event: ExportEvent) -> None:
        if self.event_sink is not None:
            self.event_sink.emit(event)
