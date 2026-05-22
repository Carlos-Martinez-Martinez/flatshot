"""
Export Worker for FlatShot.

Qt adapter for the application export runner. Public helpers are re-exported
from this module to keep the existing UI, CLI and tests compatible.
"""
from __future__ import annotations

import shutil
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from time import time

from PyQt6.QtCore import QThread, pyqtSignal

from flatshot.application.contracts import ExportJobRequest
from flatshot.application.events import (
    ExportFinishedEvent,
    ExportImageCompletedEvent,
    ExportLogEvent,
    ExportProgressEvent,
    ExportStartedEvent,
)
from flatshot.application.execution_control import CancellationToken, PauseToken
from flatshot.application.export_runner import (
    ExportRunner,
    apply_naming_template,
    build_variant_output_path,
    get_enabled_export_variants,
    process_single_image,
    validate_output_path_collisions,
    variant_bg_token,
    variant_export_format,
    variant_output_folder,
)
from flatshot.core.models import CurveData, ExportConfig, ShadowSettings


class _QtExportEventSink:
    def __init__(self, worker: "ExportWorker") -> None:
        self.worker = worker

    def emit(self, event) -> None:
        self.worker._handle_export_event(event)


class ExportWorker(QThread):
    """Worker thread for batch image export."""

    progress_updated = pyqtSignal(int)
    log_updated = pyqtSignal(str)
    image_completed = pyqtSignal(str, bool)  # image_name, success
    finished_process = pyqtSignal(bool, int, int, float)  # success, processed, total, duration

    def __init__(
        self,
        input_folder: str,
        shadow_settings: ShadowSettings,
        export_config: ExportConfig,
        curve_data: CurveData,
        preset_name: str = None,
        input_files: list[str] | None = None,
        image_overrides: dict | None = None,
    ):
        super().__init__()
        self.input_folder = Path(input_folder)
        self.settings = shadow_settings
        self.export_config = export_config
        self.curve_data = curve_data
        self.preset_name = preset_name
        self.is_running = True
        self.executor = None
        self.start_time = None
        self.input_files = input_files
        self.image_overrides = dict(image_overrides or {})
        self._cancellation_token = CancellationToken()
        self._pause_token = PauseToken()
        self._runner: ExportRunner | None = None

    def run(self):
        self.start_time = time()

        try:
            request = ExportJobRequest(
                input_folder=self.input_folder,
                settings=self.settings,
                export_config=self.export_config,
                curve_data=self.curve_data,
                preset_name=self.preset_name,
                input_files=[Path(p) for p in self.input_files] if self.input_files is not None else None,
                image_overrides=self.image_overrides,
            )
            self._runner = ExportRunner(
                event_sink=_QtExportEventSink(self),
                cancellation_token=self._cancellation_token,
                pause_token=self._pause_token,
                executor_factory=ProcessPoolExecutor,
                image_processor=process_single_image,
                copy_file=shutil.copy2,
            )
            result = self._runner.run(request)
            self.executor = self._runner.executor
            self.finished_process.emit(
                result.success,
                result.processed,
                result.total,
                result.duration,
            )
        except Exception as exc:
            self.log_updated.emit(f"Error crítico en ExportWorker: {exc}")
            duration = time() - self.start_time if self.start_time else 0.0
            self.finished_process.emit(False, 0, 0, duration)

    def stop(self):
        """Stop the export process."""
        self.is_running = False
        self._cancellation_token.cancel()
        self._pause_token.resume()

    def pause(self):
        """Pause dispatching/consuming new image tasks."""
        self._pause_token.pause()

    def resume(self):
        """Resume image processing after a pause."""
        self._pause_token.resume()

    def _handle_export_event(self, event) -> None:
        if isinstance(event, ExportLogEvent):
            self.log_updated.emit(event.message)
        elif isinstance(event, ExportProgressEvent):
            self.progress_updated.emit(event.percent)
        elif isinstance(event, ExportImageCompletedEvent):
            self.image_completed.emit(event.image_name, event.success)
        elif isinstance(event, (ExportStartedEvent, ExportFinishedEvent)):
            return
