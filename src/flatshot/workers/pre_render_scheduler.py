"""Idle, abortable scheduler for opportunistic export pre-rendering."""

from __future__ import annotations

import multiprocessing as mp
from pathlib import Path
from queue import Empty
from time import monotonic
from typing import Callable

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from flatshot.application.pre_render_planner import (
    build_pre_render_context_signature,
    build_pre_render_jobs,
    ordered_pre_render_candidates,
)
from flatshot.utils.render_cache import RenderCache
from flatshot.workers.pre_render_process import run_pre_render_job


class PreRenderScheduler(QObject):
    """Prepare export cache entries only while the UI is genuinely idle."""

    status_changed = pyqtSignal(str, int, int)  # state, prepared, total
    error = pyqtSignal(str)

    def __init__(
        self,
        *,
        idle_ms: int = 8000,
        max_cache_bytes: int = 2 * 1024 * 1024 * 1024,
        max_cache_files: int = 1000,
        busy_callback: Callable[[], bool] | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.cache = RenderCache()
        self.enabled = False
        self.idle_ms = max(1000, int(idle_ms))
        self.max_cache_bytes = int(max_cache_bytes)
        self.max_cache_files = int(max_cache_files)
        self.busy_callback = busy_callback

        self._folders: list[Path] = []
        self._active_folder: Path | None = None
        self._current_image_path: Path | None = None
        self._settings_dict: dict = {}
        self._curve_dict: dict | None = None
        self._target_size: tuple[int, int] = (1800, 2400)
        self._export_format = "jpg"
        self._image_overrides: dict[str, dict] = {}
        self._context_signature = ""

        self._last_activity_at = monotonic()
        self._last_status: tuple[str, int, int] | None = None
        self._last_prepared = 0
        self._last_total = 0

        self._ctx = mp.get_context("spawn")
        self._current_process = None
        self._current_queue = None
        self._current_job: dict | None = None

        self._idle_timer = QTimer(self)
        self._idle_timer.setSingleShot(True)
        self._idle_timer.timeout.connect(self._try_start)

        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(250)
        self._poll_timer.timeout.connect(self._poll_process)

        self._heartbeat_timer = QTimer(self)
        self._heartbeat_timer.setInterval(250)
        self._heartbeat_timer.timeout.connect(self._check_ui_heartbeat)
        self._heartbeat_at = monotonic()

    def update_context(
        self,
        *,
        enabled: bool,
        folders: list[Path],
        active_folder: str | Path | None,
        current_image_path: str | Path | None,
        settings_dict: dict,
        curve_dict: dict | None,
        target_size: tuple[int, int],
        export_format: str,
        image_overrides: dict[str, dict],
        idle_ms: int | None = None,
        max_cache_bytes: int | None = None,
    ) -> None:
        self.enabled = bool(enabled)
        if idle_ms is not None:
            self.idle_ms = max(1000, int(idle_ms))
        if max_cache_bytes is not None:
            self.max_cache_bytes = max(128 * 1024 * 1024, int(max_cache_bytes))

        self._folders = [Path(folder) for folder in folders]
        self._active_folder = Path(active_folder) if active_folder else None
        self._current_image_path = Path(current_image_path) if current_image_path else None
        self._settings_dict = dict(settings_dict or {})
        self._curve_dict = dict(curve_dict or {}) if curve_dict else None
        self._target_size = tuple(target_size)
        self._export_format = RenderCache.normalize_format(export_format)
        self._image_overrides = dict(image_overrides or {})

        signature = self._make_context_signature()
        changed = signature != self._context_signature
        self._context_signature = signature

        if not self.enabled:
            self.shutdown(emit_idle=True)
            return

        if not self._heartbeat_timer.isActive():
            self._heartbeat_at = monotonic()
            self._heartbeat_timer.start()

        if changed:
            self.note_activity("context")
        else:
            self.schedule()

    def _make_context_signature(self) -> str:
        return build_pre_render_context_signature(
            folders=self._folders,
            active_folder=self._active_folder,
            current_image_path=self._current_image_path,
            settings_dict=self._settings_dict,
            curve_dict=self._curve_dict,
            target_size=self._target_size,
            export_format=self._export_format,
            image_overrides=self._image_overrides,
        )

    def note_activity(self, reason: str = "activity") -> None:
        if not self.enabled:
            return
        self._last_activity_at = monotonic()
        self._terminate_current(reason)
        if self._folders:
            self._emit_status("paused", self._last_prepared, self._last_total)
            self.schedule()

    def schedule(self, delay_ms: int | None = None) -> None:
        if not self.enabled:
            return
        delay = self.idle_ms if delay_ms is None else max(250, int(delay_ms))
        self._idle_timer.start(delay)

    def shutdown(self, emit_idle: bool = False) -> None:
        self.enabled = False
        self._idle_timer.stop()
        self._poll_timer.stop()
        self._heartbeat_timer.stop()
        self._terminate_current("shutdown", emit_status=False)
        if emit_idle:
            self._emit_status("idle", 0, 0)

    def _check_ui_heartbeat(self) -> None:
        now = monotonic()
        expected = self._heartbeat_timer.interval() / 1000.0
        lag = now - self._heartbeat_at - expected
        self._heartbeat_at = now
        if lag > 0.150:
            self.note_activity("ui-lag")

    def _try_start(self) -> None:
        if not self.enabled:
            return
        if self._current_process is not None:
            return
        if self.busy_callback and self.busy_callback():
            self._emit_status("paused", self._last_prepared, self._last_total)
            self.schedule(1000)
            return

        elapsed_ms = int((monotonic() - self._last_activity_at) * 1000)
        if elapsed_ms < self.idle_ms:
            self.schedule(self.idle_ms - elapsed_ms)
            return

        jobs, prepared, total = self._build_jobs()
        self._last_prepared = prepared
        self._last_total = total

        if total == 0:
            self._emit_status("idle", 0, 0)
            return
        if prepared >= total:
            self._emit_status("ready", prepared, total)
            self.cache.prune(max_files=self.max_cache_files, max_bytes=self.max_cache_bytes)
            return
        if not jobs:
            self._emit_status("partial", prepared, total)
            self.schedule(30000)
            return

        self._emit_status("preparing", prepared, total)
        self._start_process(jobs[0])

    def _ordered_candidates(self) -> list[Path]:
        return ordered_pre_render_candidates(
            folders=self._folders,
            active_folder=self._active_folder,
            current_image_path=self._current_image_path,
        )

    def _build_jobs(self) -> tuple[list[dict], int, int]:
        return build_pre_render_jobs(
            candidates=self._ordered_candidates(),
            cache=self.cache,
            settings_dict=self._settings_dict,
            curve_dict=self._curve_dict,
            target_size=self._target_size,
            export_format=self._export_format,
            image_overrides=self._image_overrides,
        )

    def _start_process(self, job: dict) -> None:
        self._current_job = job
        self._current_queue = self._ctx.Queue(maxsize=1)
        self._current_process = self._ctx.Process(
            target=run_pre_render_job,
            args=(job, self._current_queue),
        )
        self._current_process.daemon = True
        try:
            self._current_process.start()
            self._poll_timer.start()
        except Exception as exc:
            self._cleanup_current_process()
            self.error.emit(f"No se pudo iniciar pre-render: {exc}")
            self.schedule(30000)

    def _poll_process(self) -> None:
        process = self._current_process
        if process is None:
            self._poll_timer.stop()
            return
        if process.is_alive():
            if self.busy_callback and self.busy_callback():
                self.note_activity("busy")
            return

        self._poll_timer.stop()
        result = None
        try:
            result = self._current_queue.get(timeout=0.05) if self._current_queue else None
        except Empty:
            result = None
        except Exception:
            result = None

        job = self._current_job
        self._cleanup_current_process()

        success = False
        message = None
        if result:
            success, _key, message = result
        if success and job:
            if self.cache.exists(job["key"], job["format"], validate=True):
                self._last_prepared = min(self._last_prepared + 1, max(self._last_total, 1))
                self._emit_status("preparing", self._last_prepared, self._last_total)
            else:
                success = False
                message = "La caché generada no es válida"

        if not success and message:
            self.error.emit(f"Pre-render falló: {message}")

        self.cache.prune(max_files=self.max_cache_files, max_bytes=self.max_cache_bytes)
        self.schedule(250)

    def _cleanup_current_process(self) -> None:
        if self._current_process is not None:
            try:
                self._current_process.join(timeout=0.1)
            except Exception:
                pass
        if self._current_queue is not None:
            try:
                self._current_queue.close()
            except Exception:
                pass
        self._current_process = None
        self._current_queue = None
        self._current_job = None

    def _terminate_current(self, reason: str, emit_status: bool = True) -> None:
        process = self._current_process
        job = self._current_job
        if process is None:
            return

        self._poll_timer.stop()
        try:
            if process.is_alive():
                process.terminate()
                process.join(timeout=0.5)
                if process.is_alive() and hasattr(process, "kill"):
                    process.kill()
                    process.join(timeout=0.5)
        except Exception:
            pass

        if job:
            cache_path = Path(job["cache_path"])
            for temp_path in cache_path.parent.glob(f".{cache_path.name}.*.tmp"):
                try:
                    temp_path.unlink()
                except OSError:
                    pass

        self._cleanup_current_process()
        if emit_status:
            self._emit_status("paused", self._last_prepared, self._last_total)

    def _emit_status(self, state: str, prepared: int, total: int) -> None:
        status = (state, int(prepared), int(total))
        if status == self._last_status:
            return
        self._last_status = status
        self.status_changed.emit(*status)
