"""Qt-free queue runner for sequential folder exports."""
from __future__ import annotations

from pathlib import Path
from time import sleep, time
from typing import Callable, Protocol

from flatshot.application.contracts import ExportJobRequest, QueueRunRequest, QueueRunResult
from flatshot.application.events import (
    ApplicationEvent,
    ExportImageCompletedEvent,
    ExportLogEvent,
    ExportProgressEvent,
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
from flatshot.application.export_runner import (
    ExportRunner,
    OutputPathValidationError,
    validate_export_requests_outputs,
)
from flatshot.core.models import JobItem, normalize_export_variants


class QueueEventSink(Protocol):
    def emit(self, event: ApplicationEvent) -> None:
        ...


class QueueLogger(Protocol):
    def log_queue_start(self, num_jobs: int) -> None:
        ...

    def log_export_start(self, folder: str, total_images: int, preset_name: str | None = None) -> None:
        ...

    def log_export_complete(self, folder: str, processed: int, total: int, duration_sec: float) -> None:
        ...

    def log_export_cancelled(self, folder: str, processed: int, total: int) -> None:
        ...

    def log_queue_complete(self, completed: int, errors: int, total_images: int) -> None:
        ...


class _QueueExportEventSink:
    def __init__(self, runner: "QueueRunner", job_index: int, job: JobItem) -> None:
        self.runner = runner
        self.job_index = job_index
        self.job = job
        self.processed_ok = 0
        self.processed_err = 0

    def emit(self, event: ApplicationEvent) -> None:
        if isinstance(event, ExportProgressEvent):
            self.job.progress = event.percent
            self.runner._emit(QueueJobProgressEvent(self.job_index, event.percent))
        elif isinstance(event, ExportImageCompletedEvent):
            if event.success:
                self.processed_ok += 1
            else:
                self.processed_err += 1
            self.job.processed_images = self.processed_ok
        elif isinstance(event, ExportLogEvent):
            self.runner._emit(event)


class QueueRunner:
    def __init__(
        self,
        export_runner_factory: Callable[..., ExportRunner] = ExportRunner,
        event_sink: QueueEventSink | None = None,
        cancellation_token: CancellationToken | None = None,
        pause_token: PauseToken | None = None,
        *,
        logger: QueueLogger | None = None,
        pause_poll_seconds: float = 0.1,
    ) -> None:
        self.export_runner_factory = export_runner_factory
        self.event_sink = event_sink
        self.cancellation_token = cancellation_token or CancellationToken()
        self.pause_token = pause_token or PauseToken()
        self.logger = logger
        self.pause_poll_seconds = pause_poll_seconds
        self.current_runner: ExportRunner | None = None

    def run(self, request: QueueRunRequest) -> QueueRunResult:
        total_jobs = len(request.jobs)
        if total_jobs == 0:
            self._emit(QueueFinishedEvent(0, 0, 0))
            return QueueRunResult(0, 0, 0, cancelled=self.cancellation_token.cancelled)

        if self.logger:
            self.logger.log_queue_start(total_jobs)
        self._emit(QueueStartedEvent(total_jobs))

        completed = 0
        errors = 0
        total_images = 0
        planned_requests: list[ExportJobRequest] = []

        for job in request.jobs:
            folder_path = Path(job.folder_path)
            images = self._job_images(job, folder_path)
            if not images:
                continue
            planned_requests.append(
                ExportJobRequest(
                    input_folder=folder_path,
                    settings=request.settings,
                    export_config=request.export_config,
                    curve_data=request.curve_data,
                    preset_name=request.preset_name,
                    input_files=[Path(p) for p in images],
                    image_overrides=request.image_overrides,
                )
            )

        if not self.cancellation_token.cancelled:
            try:
                validate_export_requests_outputs(planned_requests)
            except OutputPathValidationError as exc:
                for job in request.jobs:
                    job.status = "error"
                    job.error_message = str(exc)
                self._emit(ExportLogEvent(f"Error: Exportación: {exc}"))
                if self.logger:
                    self.logger.log_queue_complete(0, total_jobs, 0)
                self._emit(QueueFinishedEvent(0, total_jobs, 0))
                return QueueRunResult(0, total_jobs, 0, cancelled=self.cancellation_token.cancelled)

        for index, job in enumerate(request.jobs):
            if self.cancellation_token.cancelled:
                job.status = "cancelled"
                continue

            self._wait_if_paused()
            if self.cancellation_token.cancelled:
                job.status = "cancelled"
                continue

            folder_path = Path(job.folder_path)
            job.status = "processing"
            images = self._job_images(job, folder_path)
            active_variant_count = len(
                [variant for variant in normalize_export_variants(request.export_config) if variant.enabled]
            )
            job.total_images = len(images) * max(1, active_variant_count)

            self._emit(QueueJobStartedEvent(index, folder_path))
            if self.logger:
                self.logger.log_export_start(folder_path.name, job.total_images, request.preset_name)

            if job.total_images == 0:
                job.status = "completed"
                job.progress = 100
                self._emit(QueueJobCompletedEvent(index, True, 0, 0, 0.0))
                completed += 1
                continue

            export_sink = _QueueExportEventSink(self, index, job)
            start_time = time()
            self.current_runner = self.export_runner_factory(
                event_sink=export_sink,
                cancellation_token=self.cancellation_token,
                pause_token=self.pause_token,
            )

            try:
                self.current_runner.run(
                    ExportJobRequest(
                        input_folder=folder_path,
                        settings=request.settings,
                        export_config=request.export_config,
                        curve_data=request.curve_data,
                        preset_name=request.preset_name,
                        input_files=[Path(p) for p in images] if images else None,
                        image_overrides=request.image_overrides,
                    )
                )
            finally:
                self.current_runner = None

            duration = time() - start_time

            if self.cancellation_token.cancelled:
                job.status = "cancelled"
                if self.logger:
                    self.logger.log_export_cancelled(folder_path.name, export_sink.processed_ok, job.total_images)
            elif export_sink.processed_err == 0 and export_sink.processed_ok == job.total_images:
                job.status = "completed"
                completed += 1
                if self.logger:
                    self.logger.log_export_complete(
                        folder_path.name,
                        export_sink.processed_ok,
                        job.total_images,
                        duration,
                    )
            else:
                job.status = "error"
                job.error_message = (
                    f"Procesadas OK: {export_sink.processed_ok} / "
                    f"Errores: {export_sink.processed_err} / Total: {job.total_images}"
                )
                errors += 1

            total_images += export_sink.processed_ok
            self._emit(
                QueueJobCompletedEvent(
                    index,
                    job.status == "completed",
                    export_sink.processed_ok,
                    job.total_images,
                    duration,
                )
            )

        if self.logger:
            self.logger.log_queue_complete(completed, errors, total_images)
        self._emit(QueueFinishedEvent(completed, errors, total_images))
        return QueueRunResult(completed, errors, total_images, cancelled=self.cancellation_token.cancelled)

    def pause(self) -> None:
        self.pause_token.pause()
        self._emit(QueuePausedEvent())

    def resume(self) -> None:
        self.pause_token.resume()
        self._emit(QueueResumedEvent())

    def stop(self) -> None:
        self.cancellation_token.cancel()
        self.pause_token.resume()
        self._emit(QueueCancelledEvent())

    def _wait_if_paused(self) -> None:
        while self.pause_token.paused and not self.cancellation_token.cancelled:
            sleep(self.pause_poll_seconds)

    def _emit(self, event: ApplicationEvent) -> None:
        if self.event_sink is not None:
            self.event_sink.emit(event)

    @staticmethod
    def _job_images(job: JobItem, folder_path: Path) -> list[Path]:
        if job.input_files:
            return [Path(p) for p in job.input_files if Path(p).suffix.lower() == ".png"]
        return list(folder_path.glob("*.png"))
