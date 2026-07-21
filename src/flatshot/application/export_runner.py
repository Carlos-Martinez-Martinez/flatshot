"""Qt-free export runner and export planning helpers."""

from __future__ import annotations

import shutil
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from time import time
from typing import Callable, Protocol
from uuid import uuid4

from flatshot.application.contracts import ExportJobRequest, ExportJobResult
from flatshot.application.events import (
    ExportEvent,
    ExportFinishedEvent,
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
from flatshot.application.export_snapshots import source_image_items
from flatshot.application.export_workers import process_single_image
from flatshot.application.export_execution import (
    MAX_EXPORT_WORKERS,
    export_cached_tasks,
    export_render_tasks,
    resolve_export_max_workers,
)
from flatshot.utils.render_cache import RenderCache

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
        return export_cached_tasks(self, cached_tasks, cache, completed_count, error_count, total)

    def _export_render_tasks(
        self,
        tasks: list[ExportRenderTask],
        cache: RenderCache,
        completed_count: int,
        error_count: int,
        total: int,
    ) -> tuple[int, int]:
        return export_render_tasks(self, tasks, cache, completed_count, error_count, total)

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
