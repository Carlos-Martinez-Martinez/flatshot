"""
Queue Worker for FlatShot.

Qt adapter for the application queue runner.
"""
from pathlib import Path
from typing import List

from PyQt6.QtCore import QThread, pyqtSignal

from flatshot.application.contracts import QueueRunRequest
from flatshot.application.events import (
    ExportLogEvent,
    QueueCancelledEvent,
    QueueFinishedEvent,
    QueueJobCompletedEvent,
    QueueJobProgressEvent,
    QueueJobStartedEvent,
    QueuePausedEvent,
    QueueResumedEvent,
    QueueStartedEvent,
)
from flatshot.application.execution_control import CancellationToken, PauseToken
from flatshot.application.export_runner import ExportRunner
from flatshot.application.queue_runner import QueueRunner
from flatshot.core.models import CurveData, ExportConfig, JobItem, ShadowSettings
from flatshot.utils.log_manager import LogManager
from flatshot.workers import export_worker as export_worker_module


class _QtQueueEventSink:
    def __init__(self, worker: "QueueWorker") -> None:
        self.worker = worker

    def emit(self, event) -> None:
        self.worker._handle_queue_event(event)


class QueueWorker(QThread):
    """Worker thread that processes a queue of folder jobs sequentially."""

    # Signals for queue status
    queue_started = pyqtSignal(int)  # total_jobs
    job_started = pyqtSignal(int, str)  # job_index, folder_path
    job_progress = pyqtSignal(int, int)  # job_index, progress_percent
    job_completed = pyqtSignal(int, bool, int, int, float)  # index, success, processed, total, duration
    queue_finished = pyqtSignal(int, int, int)  # completed_jobs, errors, total_images
    log_message = pyqtSignal(str)  # log messages

    def __init__(
        self,
        jobs: List[JobItem],
        shadow_settings: ShadowSettings,
        export_config: ExportConfig,
        curve_data: CurveData,
        preset_name: str = None,
        image_overrides: dict | None = None,
    ):
        super().__init__()
        self.jobs = jobs
        self.settings = shadow_settings
        self.export_config = export_config
        self.curve_data = curve_data
        self.preset_name = preset_name
        self.image_overrides = dict(image_overrides or {})
        self.is_running = True
        self.is_paused = False
        self.current_worker = None
        self.logger = LogManager.get_instance()
        self._cancellation_token = CancellationToken()
        self._pause_token = PauseToken()
        self._runner: QueueRunner | None = None

    def run(self):
        """Process all jobs in the queue."""
        self._runner = QueueRunner(
            export_runner_factory=self._create_export_runner,
            event_sink=_QtQueueEventSink(self),
            cancellation_token=self._cancellation_token,
            pause_token=self._pause_token,
            logger=self.logger,
        )
        self._runner.run(
            QueueRunRequest(
                jobs=self.jobs,
                settings=self.settings,
                export_config=self.export_config,
                curve_data=self.curve_data,
                preset_name=self.preset_name,
                image_overrides=self.image_overrides,
            )
        )
        self.current_worker = None

    def pause(self):
        """Pause queue progression and current export runner when possible."""
        self.is_paused = True
        if self._runner:
            self._runner.pause()
        else:
            self._pause_token.pause()

    def resume(self):
        """Resume queue progression and current export runner."""
        self.is_paused = False
        if self._runner:
            self._runner.resume()
        else:
            self._pause_token.resume()

    def stop(self):
        """Stop the queue and current job."""
        self.is_running = False
        if self._runner:
            self._runner.stop()
        else:
            self._cancellation_token.cancel()
            self._pause_token.resume()

    @staticmethod
    def count_images_in_folder(folder_path: str) -> int:
        """Count PNG images in a folder."""
        return len(list(Path(folder_path).glob("*.png")))

    def _create_export_runner(self, **kwargs) -> ExportRunner:
        runner = ExportRunner(
            event_sink=kwargs.get("event_sink"),
            cancellation_token=kwargs.get("cancellation_token"),
            pause_token=kwargs.get("pause_token"),
            executor_factory=export_worker_module.ProcessPoolExecutor,
            image_processor=export_worker_module.process_single_image,
            copy_file=export_worker_module.shutil.copy2,
        )
        self.current_worker = runner
        return runner

    def _handle_queue_event(self, event) -> None:
        if isinstance(event, QueueStartedEvent):
            self.queue_started.emit(event.total_jobs)
        elif isinstance(event, QueueJobStartedEvent):
            self.job_started.emit(event.job_index, str(event.folder_path))
        elif isinstance(event, QueueJobProgressEvent):
            self.job_progress.emit(event.job_index, event.progress_percent)
        elif isinstance(event, QueueJobCompletedEvent):
            self.current_worker = None
            self.job_completed.emit(
                event.job_index,
                event.success,
                event.processed,
                event.total,
                event.duration,
            )
        elif isinstance(event, QueueFinishedEvent):
            self.queue_finished.emit(event.completed_jobs, event.errors, event.total_images)
        elif isinstance(event, ExportLogEvent):
            self.log_message.emit(event.message)
        elif isinstance(event, QueuePausedEvent):
            self.is_paused = True
        elif isinstance(event, QueueResumedEvent):
            self.is_paused = False
        elif isinstance(event, QueueCancelledEvent):
            self.is_running = False
