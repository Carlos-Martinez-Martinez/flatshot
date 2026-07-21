"""Bounded executor loops used by :mod:`export_runner`."""

from __future__ import annotations

import os
from concurrent.futures import FIRST_COMPLETED, wait
from pathlib import Path
from uuid import uuid4

from flatshot.application.events import ExportImageCompletedEvent, ExportLogEvent
from flatshot.application.export_snapshots import cleanup_snapshot_folder, queue_next_render_task
from flatshot.application.export_workers import commit_output_file
from flatshot.application.export_planning import ExportRenderTask
from flatshot.utils.render_cache import RenderCache


DEFAULT_MAX_EXPORT_WORKERS = 4
MAX_EXPORT_WORKERS = 8
MAX_EXPORT_WORKERS_ENV = "FLATSHOT_MAX_WORKERS"


def resolve_export_max_workers(configured_max_workers: int | None = None) -> int:
    """Return a bounded export worker count for high-resolution renders."""
    if configured_max_workers is not None:
        return min(max(1, int(configured_max_workers)), MAX_EXPORT_WORKERS)

    raw_env = os.environ.get(MAX_EXPORT_WORKERS_ENV)
    if raw_env:
        try:
            return min(max(1, int(raw_env)), MAX_EXPORT_WORKERS)
        except ValueError:
            pass

    cpu_workers = max(1, (os.cpu_count() or 2) - 1)
    return min(cpu_workers, DEFAULT_MAX_EXPORT_WORKERS, MAX_EXPORT_WORKERS)


def export_cached_tasks(runner, cached_tasks, cache: RenderCache, completed_count: int, error_count: int, total: int):
    if not cached_tasks:
        return completed_count, error_count, []

    fallback_tasks = []
    runner._emit(ExportLogEvent(f"Exportando {len(cached_tasks)} archivos desde caché..."))
    for cached in cached_tasks:
        if runner.cancellation_token.cancelled:
            break
        if runner.pause_token.wait_if_paused(timeout=None, cancellation_token=runner.cancellation_token):
            break

        try:
            cache_path = cache.get_cached_path(cached.key, cached.fmt)
            save_path = Path(cached.save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            temporary_path = save_path.with_name(f".{save_path.stem}.{uuid4().hex}{save_path.suffix}")
            try:
                runner.copy_file(cache_path, temporary_path)
                commit_output_file(temporary_path, save_path)
            finally:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass

            completed_count += 1
            runner._emit(ExportImageCompletedEvent(cached.display_name, True, cached.source_path, save_path))
            runner._emit_progress(completed_count, total)
        except Exception as exc:
            runner._emit(ExportLogEvent(f"Caché no válida para {cached.display_name}; renderizando normal ({exc})"))
            fallback_tasks.append(cached)

    return completed_count, error_count, fallback_tasks


def export_render_tasks(runner, tasks, cache: RenderCache, completed_count: int, error_count: int, total: int):
    max_workers = resolve_export_max_workers(runner.max_workers)
    runner._emit(ExportLogEvent(f"Procesando {len(tasks)} archivos restantes con {max_workers} núcleos..."))

    try:
        with runner.executor_factory(max_workers=max_workers) as executor:
            runner.executor = executor
            pending_tasks = iter(tasks)
            in_flight = {}

            for _ in range(min(max_workers, len(tasks))):
                if runner.cancellation_token.cancelled and not in_flight:
                    break
                completed_count, error_count, runner._snapshot_dir = queue_next_render_task(
                    executor=executor,
                    pending_tasks=pending_tasks,
                    in_flight=in_flight,
                    snapshot_dir=runner._snapshot_dir,
                    copy_file=runner.copy_file,
                    image_processor=runner.image_processor,
                    cancellation_token=runner.cancellation_token,
                    emit=runner._emit,
                    emit_progress=runner._emit_progress,
                    completed_count=completed_count,
                    error_count=error_count,
                    total=total,
                    allow_cancelled=True,
                )

            while in_flight:
                if not runner.cancellation_token.cancelled and runner.pause_token.wait_if_paused(
                    timeout=None, cancellation_token=runner.cancellation_token
                ):
                    continue

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
                        runner._store_render_cache(task, cache)
                        if warning:
                            runner._emit(ExportLogEvent(f"Aviso: {msg}: {warning}"))
                        runner._emit(ExportImageCompletedEvent(msg, True, task.source_path, Path(task.save_path)))
                    else:
                        error_count += 1
                        runner._emit(ExportLogEvent(f"Error: {msg}"))
                        runner._emit(ExportImageCompletedEvent(msg.split(":")[0], False, task.source_path, Path(task.save_path)))

                    completed_count += 1
                    runner._emit_progress(completed_count, total)

                    if not runner.cancellation_token.cancelled and not runner.pause_token.paused:
                        completed_count, error_count, runner._snapshot_dir = queue_next_render_task(
                            executor=executor,
                            pending_tasks=pending_tasks,
                            in_flight=in_flight,
                            snapshot_dir=runner._snapshot_dir,
                            copy_file=runner.copy_file,
                            image_processor=runner.image_processor,
                            cancellation_token=runner.cancellation_token,
                            emit=runner._emit,
                            emit_progress=runner._emit_progress,
                            completed_count=completed_count,
                            error_count=error_count,
                            total=total,
                        )
    except Exception as exc:
        runner._fatal_error = str(exc) or exc.__class__.__name__
        runner._emit(ExportLogEvent(f"Error en el proceso de exportación: {exc}"))

    return completed_count, error_count
