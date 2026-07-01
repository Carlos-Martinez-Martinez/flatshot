"""Qt-free export runner and export planning helpers."""

from __future__ import annotations

import os
import shutil
import tempfile
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from pathlib import Path
from time import time
from typing import Callable, Protocol
from uuid import uuid4

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
from flatshot.application.export_naming import (
    OutputPathValidationError,
    validate_output_path_collisions,
)
from flatshot.application.export_naming import (
    apply_naming_template as apply_naming_template,
)
from flatshot.application.export_naming import (
    build_variant_output_path as build_variant_output_path,
)
from flatshot.application.export_naming import (
    get_enabled_export_variants as get_enabled_export_variants,
)
from flatshot.application.export_naming import (
    validate_export_requests_outputs as validate_export_requests_outputs,
)
from flatshot.application.export_naming import (
    variant_target_size as variant_target_size,
)
from flatshot.application.export_planning import ExportPlan as ExportPlan
from flatshot.application.export_planning import ExportRenderTask, build_export_plan
from flatshot.application.export_workers import copy_stable, process_single_image
from flatshot.core.overrides import override_key
from flatshot.utils.render_cache import RenderCache

DEFAULT_MAX_EXPORT_WORKERS = 4
MAX_EXPORT_WORKERS_ENV = "FLATSHOT_MAX_WORKERS"


def resolve_export_max_workers(configured_max_workers: int | None = None) -> int:
    """Return a bounded export worker count for high-resolution renders."""
    if configured_max_workers is not None:
        return max(1, int(configured_max_workers))

    raw_env = os.environ.get(MAX_EXPORT_WORKERS_ENV)
    if raw_env:
        try:
            return max(1, int(raw_env))
        except ValueError:
            pass

    cpu_workers = max(1, (os.cpu_count() or 2) - 1)
    return min(cpu_workers, DEFAULT_MAX_EXPORT_WORKERS)


class ExportEventSink(Protocol):
    def emit(self, event: ExportEvent) -> None: ...


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
        max_workers: int | None = None,
    ):
        self.event_sink = event_sink
        self.cancellation_token = cancellation_token or CancellationToken()
        self.pause_token = pause_token or PauseToken()
        self.executor_factory = executor_factory
        self.image_processor = image_processor
        self.copy_file = copy_file
        self.max_workers = max_workers
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
            cache = RenderCache()
            plan = build_export_plan(request, image_items, cache)
            if plan.source_total == 0:
                result = ExportJobResult(True, 0, 0, 0, 0.0, destinations)
                self._emit(ExportFinishedEvent(True, 0, 0, 0, 0.0))
                return result

            total = plan.total
            self._emit(ExportStartedEvent(plan.source_total, total))
            if not plan.enabled_variants:
                self._emit(ExportLogEvent("No hay variantes de salida activas. Activa al menos una salida."))
                duration = time() - start_time
                result = ExportJobResult(False, 0, 0, 0, duration, destinations)
                self._emit(ExportFinishedEvent(False, 0, 0, 0, duration))
                return result

            self._emit(
                ExportLogEvent("Salidas activas: " + ", ".join(variant.label for variant in plan.enabled_variants))
            )

            try:
                validate_output_path_collisions(plan.planned_outputs)
                destinations = sorted(
                    {Path(item["save_path"]).parent for item in plan.planned_outputs},
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
                plan.cached_tasks,
                cache,
                completed_count,
                error_count,
                total,
            )

            tasks = list(plan.render_tasks)
            if fallback:
                tasks.extend(fallback)

            if tasks and not self.cancellation_token.cancelled:
                self.pause_token.wait_if_paused()
                if self.cancellation_token.cancelled:
                    self._emit(ExportLogEvent("Exportación cancelada."))
                else:
                    completed_count, error_count = self._export_render_tasks(
                        tasks,
                        cache,
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
        cached_tasks: list[ExportRenderTask],
        cache: RenderCache,
        completed_count: int,
        error_count: int,
        total: int,
    ) -> tuple[int, int, list[ExportRenderTask]]:
        if not cached_tasks:
            return completed_count, error_count, []

        fallback_tasks: list[ExportRenderTask] = []
        self._emit(ExportLogEvent(f"Exportando {len(cached_tasks)} archivos desde caché..."))
        for cached in cached_tasks:
            if self.cancellation_token.cancelled:
                break
            self.pause_token.wait_if_paused()

            try:
                cache_path = cache.get_cached_path(cached.key, cached.fmt)
                save_path = Path(cached.save_path)
                save_path.parent.mkdir(parents=True, exist_ok=True)
                self.copy_file(cache_path, save_path)

                completed_count += 1
                self._emit(ExportImageCompletedEvent(cached.display_name, True))
                self._emit_progress(completed_count, total)
            except Exception as e:
                self._emit(ExportLogEvent(f"Caché no válida para {cached.display_name}; renderizando normal ({e})"))
                fallback_tasks.append(cached)

        return completed_count, error_count, fallback_tasks

    def _export_render_tasks(
        self,
        tasks: list[ExportRenderTask],
        cache: RenderCache,
        completed_count: int,
        error_count: int,
        total: int,
    ) -> tuple[int, int]:
        max_workers = resolve_export_max_workers(self.max_workers)
        self._emit(ExportLogEvent(f"Procesando {len(tasks)} archivos restantes con {max_workers} núcleos..."))

        try:
            with self.executor_factory(max_workers=max_workers) as executor:
                self.executor = executor
                pending_tasks = iter(tasks)
                in_flight = {}

                for _ in range(min(max_workers, len(tasks))):
                    try:
                        task = next(pending_tasks)
                        future = executor.submit(self.image_processor, task.task_args)
                        in_flight[future] = task
                    except StopIteration:
                        break

                while in_flight and not self.cancellation_token.cancelled:
                    self.pause_token.wait_if_paused()
                    if self.cancellation_token.cancelled:
                        break

                    done, _ = wait(set(in_flight), timeout=0.2, return_when=FIRST_COMPLETED)
                    if not done:
                        continue

                    for future in done:
                        task = in_flight.pop(future)
                        try:
                            success, msg, warning = future.result()
                        except Exception as exc:
                            success, msg, warning = False, f"Worker error: {exc}", None

                        if success:
                            self._store_render_cache(task, cache)
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
                                task = next(pending_tasks)
                                future = executor.submit(self.image_processor, task.task_args)
                                in_flight[future] = task
                            except StopIteration:
                                pass
        except Exception as exc:
            self._emit(ExportLogEvent(f"Error en el proceso de exportación: {exc}"))

        return completed_count, error_count

    def _store_render_cache(self, task: ExportRenderTask, cache: RenderCache) -> None:
        cache_path = Path(task.cache_path)
        save_path = Path(task.save_path)
        temp_path = cache.get_temp_path(cache_path, str(uuid4()))
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.copy_file(save_path, temp_path)
            os.replace(temp_path, cache_path)
        except Exception as exc:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
            self._emit(ExportLogEvent(f"Aviso: no se pudo actualizar la caché de {task.display_name}: {exc}"))

    def _emit_progress(self, completed_count: int, total: int) -> None:
        self._emit(ExportProgressEvent(completed_count, total, int((completed_count / total) * 100)))

    def _emit(self, event: ExportEvent) -> None:
        if self.event_sink is not None:
            self.event_sink.emit(event)
