"""Qt-free export runner and export planning helpers."""

from __future__ import annotations

import os
import shutil
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
from flatshot.application.export_snapshots import (
    cleanup_snapshot_folder,
    queue_next_render_task,
    source_image_items,
)
from flatshot.application.export_workers import commit_output_file, process_single_image
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
        self._fatal_error: str | None = None

    def run(self, request: ExportJobRequest) -> ExportJobResult:
        start_time = time()
        completed_count = 0
        error_count = 0
        total = 0
        destinations: list[Path] = []
        cache: RenderCache | None = None
        self._fatal_error = None

        try:
            image_items = source_image_items(request)
            cache = RenderCache()
            plan = build_export_plan(
                request,
                image_items,
                cache,
                snapshot_inputs=request.input_files is not None,
            )
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
                self.pause_token.wait_if_paused(timeout=None, cancellation_token=self.cancellation_token)
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
            self._fatal_error = str(exc) or exc.__class__.__name__
            self._emit(ExportLogEvent(f"Error crítico en ExportRunner: {exc}"))
        finally:
            if cache is not None:
                try:
                    cache.prune()
                except Exception as exc:
                    self._emit(ExportLogEvent(f"Aviso: no se pudo limpiar la caché: {exc}"))
            if self._snapshot_dir:
                shutil.rmtree(self._snapshot_dir, ignore_errors=True)
            if self.executor:
                self.executor.shutdown(wait=False, cancel_futures=True)

        duration = time() - start_time
        success = (
            not self.cancellation_token.cancelled
            and self._fatal_error is None
            and error_count == 0
            and completed_count == total
        )
        result = ExportJobResult(
            success,
            completed_count,
            total,
            error_count,
            duration,
            destinations,
            self._fatal_error,
        )
        self._emit(ExportFinishedEvent(success, completed_count, total, error_count, duration))
        return result

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
            if self.pause_token.wait_if_paused(timeout=None, cancellation_token=self.cancellation_token):
                break

            try:
                cache_path = cache.get_cached_path(cached.key, cached.fmt)
                save_path = Path(cached.save_path)
                save_path.parent.mkdir(parents=True, exist_ok=True)
                temporary_path = save_path.with_name(f".{save_path.stem}.{uuid4().hex}{save_path.suffix}")
                try:
                    self.copy_file(cache_path, temporary_path)
                    commit_output_file(temporary_path, save_path)
                finally:
                    try:
                        temporary_path.unlink(missing_ok=True)
                    except OSError:
                        pass

                completed_count += 1
                self._emit(ExportImageCompletedEvent(cached.display_name, True, cached.source_path, save_path))
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
                    completed_count, error_count, self._snapshot_dir = queue_next_render_task(
                        executor=executor,
                        pending_tasks=pending_tasks,
                        in_flight=in_flight,
                        snapshot_dir=self._snapshot_dir,
                        copy_file=self.copy_file,
                        image_processor=self.image_processor,
                        cancellation_token=self.cancellation_token,
                        emit=self._emit,
                        emit_progress=self._emit_progress,
                        completed_count=completed_count,
                        error_count=error_count,
                        total=total,
                    )

                while in_flight and not self.cancellation_token.cancelled:
                    if self.pause_token.wait_if_paused(timeout=None, cancellation_token=self.cancellation_token):
                        break
                    if self.cancellation_token.cancelled:
                        break

                    done, _ = wait(set(in_flight), timeout=0.2, return_when=FIRST_COMPLETED)
                    if not done:
                        continue

                    for future in done:
                        task, snapshot_folder = in_flight.pop(future)
                        try:
                            success, msg, warning = future.result()
                        except Exception as exc:
                            success, msg, warning = False, f"Worker error: {exc}", None
                        finally:
                            cleanup_snapshot_folder(snapshot_folder)

                        if success:
                            self._store_render_cache(task, cache)
                            if warning:
                                self._emit(ExportLogEvent(f"Aviso: {msg}: {warning}"))
                            self._emit(ExportImageCompletedEvent(msg, True, task.source_path, Path(task.save_path)))
                        else:
                            error_count += 1
                            self._emit(ExportLogEvent(f"Error: {msg}"))
                            self._emit(ExportImageCompletedEvent(msg.split(":")[0], False, task.source_path, Path(task.save_path)))

                        completed_count += 1
                        self._emit_progress(completed_count, total)

                        if not self.cancellation_token.cancelled and not self.pause_token.paused:
                            completed_count, error_count, self._snapshot_dir = queue_next_render_task(
                                executor=executor,
                                pending_tasks=pending_tasks,
                                in_flight=in_flight,
                                snapshot_dir=self._snapshot_dir,
                                copy_file=self.copy_file,
                                image_processor=self.image_processor,
                                cancellation_token=self.cancellation_token,
                                emit=self._emit,
                                emit_progress=self._emit_progress,
                                completed_count=completed_count,
                                error_count=error_count,
                                total=total,
                            )
        except Exception as exc:
            self._fatal_error = str(exc) or exc.__class__.__name__
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
