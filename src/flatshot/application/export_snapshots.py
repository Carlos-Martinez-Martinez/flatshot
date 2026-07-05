"""Progressive source snapshot helpers for export runs."""
from __future__ import annotations

import shutil
import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Callable
from uuid import uuid4

from flatshot.application.contracts import ExportJobRequest
from flatshot.application.events import ExportImageCompletedEvent, ExportLogEvent
from flatshot.application.export_planning import ExportRenderTask
from flatshot.application.export_workers import copy_stable
from flatshot.core.overrides import override_key


class SnapshotError(Exception):
    def __init__(self, task: ExportRenderTask, message: str) -> None:
        super().__init__(message)
        self.task = task


def source_image_items(request: ExportJobRequest) -> list[tuple[Path, str, Path]]:
    if request.input_files is not None:
        source_files = [Path(p) for p in request.input_files]
    else:
        source_files = list(request.input_folder.iterdir())
    return [
        (path, override_key(path), path)
        for path in source_files
        if path.is_file() and path.suffix.lower() == ".png"
    ]


def snapshot_root(current: Path | None) -> Path:
    return current or Path(tempfile.mkdtemp(prefix="flatshot_snap_"))


def snapshot_render_task(
    task: ExportRenderTask,
    root: Path,
    copy_file: Callable = shutil.copy2,
) -> tuple[ExportRenderTask, Path | None]:
    if not task.needs_snapshot:
        return task, None

    snapshot_folder = root / uuid4().hex
    snapshot_path = snapshot_folder / task.source_path.name
    snapshot_folder.mkdir(parents=True, exist_ok=True)
    if not copy_stable(task.source_path, snapshot_path, copy_file):
        cleanup_snapshot_folder(snapshot_folder)
        raise SnapshotError(task, f"{task.source_path.name}: no se pudo crear un snapshot estable.")

    return replace(task, img_path=snapshot_path, task_args=(snapshot_path, *task.task_args[1:])), snapshot_folder


def cleanup_snapshot_folder(folder: Path | None) -> None:
    if folder is not None:
        shutil.rmtree(folder, ignore_errors=True)


def queue_next_render_task(
    *,
    executor,
    pending_tasks,
    in_flight: dict,
    snapshot_dir: Path | None,
    copy_file: Callable,
    image_processor: Callable,
    cancellation_token,
    emit: Callable,
    emit_progress: Callable[[int, int], None],
    completed_count: int,
    error_count: int,
    total: int,
) -> tuple[int, int, Path | None]:
    while not cancellation_token.cancelled:
        try:
            task = next(pending_tasks)
        except StopIteration:
            return completed_count, error_count, snapshot_dir
        try:
            snapshot_dir = snapshot_root(snapshot_dir) if task.needs_snapshot else snapshot_dir
            prepared, snapshot_folder = snapshot_render_task(task, snapshot_dir or Path(), copy_file)
        except SnapshotError as exc:
            error_count += 1
            completed_count += 1
            emit(ExportLogEvent(f"Error: {exc}"))
            emit(ExportImageCompletedEvent(exc.task.source_path.name, False, exc.task.source_path))
            emit_progress(completed_count, total)
            continue
        future = executor.submit(image_processor, prepared.task_args)
        in_flight[future] = (prepared, snapshot_folder)
        return completed_count, error_count, snapshot_dir
    return completed_count, error_count, snapshot_dir
