"""In-memory export jobs for the local FlatShot bridge."""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from time import perf_counter
from typing import Callable

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
from flatshot.application.export_runner import ExportRunner
from flatshot.bridge.serialization import serialize_path


ExportRunnerFactory = Callable[..., ExportRunner]


@dataclass
class BridgeExportJob:
    job_id: str
    requests: list[ExportJobRequest]
    source_images: int
    total_outputs: int
    destinations: list
    runner_factory: ExportRunnerFactory = ExportRunner
    status: str = "queued"
    processed: int = 0
    errors: int = 0
    percent: int = 0
    messages: list[str] = field(default_factory=list)
    completed_items: list[dict] = field(default_factory=list)
    issues: list[dict] = field(default_factory=list)
    result: ExportJobResult | None = None

    def __post_init__(self) -> None:
        self.cancellation_token = CancellationToken()
        self.pause_token = PauseToken()
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._started_at = 0.0
        self._finished_at = 0.0

    def start(self) -> None:
        with self._lock:
            if self.status != "queued":
                return
            self.status = "running"
            self._started_at = perf_counter()
        self._thread = threading.Thread(target=self._run, name=f"flatshot-export-{self.job_id}", daemon=False)
        self._thread.start()

    def pause(self) -> None:
        with self._lock:
            if self.status == "running":
                self.status = "paused"
                self.pause_token.pause()
                self.messages.append("Exportación pausada.")

    def resume(self) -> None:
        with self._lock:
            if self.status == "paused":
                self.status = "running"
                self.pause_token.resume()
                self.messages.append("Exportación reanudada.")

    def cancel(self) -> None:
        with self._lock:
            if self.status in {"queued", "running", "paused"}:
                self.status = "cancelling"
                self.cancellation_token.cancel()
                self.pause_token.resume()
                self.messages.append("Cancelando exportación.")

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "ok": True,
                "jobId": self.job_id,
                "status": self.status,
                "sourceImages": self.source_images,
                "totalOutputs": self.total_outputs,
                "progress": {
                    "processed": self.processed,
                    "total": self.total_outputs,
                    "percent": self.percent,
                },
                "errors": self.errors,
                "messages": list(self.messages[-20:]),
                "completedItems": list(self.completed_items[-50:]),
                "issues": list(self.issues[-50:]),
                "destinations": [serialize_path(path) for path in self.destinations],
                "durationMs": int(round(self._duration_seconds_locked() * 1000)),
                "result": self._result_dict(),
            }

    def _run(self) -> None:
        completed_offset = 0
        error_count = 0
        destinations = list(self.destinations)
        success = True

        try:
            for request in self.requests:
                if self.cancellation_token.cancelled:
                    success = False
                    break

                sink = _BridgeExportEventSink(self, completed_offset)
                runner = self.runner_factory(
                    event_sink=sink,
                    cancellation_token=self.cancellation_token,
                    pause_token=self.pause_token,
                )
                result = runner.run(request)
                completed_offset += result.total
                error_count += result.errors
                destinations.extend(result.destinations)
                success = success and result.success

                with self._lock:
                    self.processed = max(self.processed, min(completed_offset, self.total_outputs))
                    self.errors = error_count
                    self.percent = _percent(self.processed, self.total_outputs)
            with self._lock:
                if self.cancellation_token.cancelled:
                    self.status = "cancelled"
                    success = False
                elif error_count:
                    self.status = "partial"
                    success = False
                elif not success:
                    self.status = "failed"
                    if not self.issues:
                        self.issues.append(
                            {
                                "level": "error",
                                "title": "Exportación",
                                "detail": "No se pudo completar la exportación.",
                            }
                        )
                else:
                    self.status = "completed"
                self._finished_at = perf_counter()
                self.destinations = sorted(set(destinations), key=lambda path: str(path))
                self.result = ExportJobResult(
                    success=success,
                    processed=self.processed,
                    total=self.total_outputs,
                    errors=error_count,
                    duration=self._duration_seconds_locked(),
                    destinations=self.destinations,
                )
                self.percent = 100 if self.status == "completed" else self.percent
        except Exception as exc:
            with self._lock:
                self.status = "failed"
                self.errors += 1
                self._finished_at = perf_counter()
                self.messages.append(f"Error de exportación: {exc}")
                self.result = ExportJobResult(
                    success=False,
                    processed=self.processed,
                    total=self.total_outputs,
                    errors=self.errors,
                    duration=self._duration_seconds_locked(),
                    destinations=self.destinations,
                )

    def _handle_event(self, event: ExportEvent, completed_offset: int) -> None:
        with self._lock:
            if isinstance(event, ExportStartedEvent):
                self.messages.append(f"Exportando {event.total_outputs} archivos.")
            elif isinstance(event, ExportProgressEvent):
                self.processed = min(completed_offset + event.processed, self.total_outputs)
                self.percent = _percent(self.processed, self.total_outputs)
            elif isinstance(event, ExportImageCompletedEvent):
                self.completed_items.append({"name": event.image_name, "success": event.success})
                if not event.success:
                    self.errors += 1
                    self.issues.append(
                        {
                            "level": "error",
                            "title": event.image_name,
                            "detail": "No se pudo exportar.",
                        }
                    )
            elif isinstance(event, ExportLogEvent):
                self.messages.append(event.message)
                issue = _issue_from_log_message(event.message)
                if issue:
                    self.issues.append(issue)
            elif isinstance(event, ExportFinishedEvent):
                self.errors = max(self.errors, event.errors)
                if not event.success and event.errors and not self.issues:
                    self.issues.append(
                        {
                            "level": "error",
                            "title": "Exportación",
                            "detail": f"{event.errors} errores durante la exportación.",
                        }
                    )

    def _duration_seconds_locked(self) -> float:
        if not self._started_at:
            return 0.0
        end = self._finished_at or perf_counter()
        return max(0.0, end - self._started_at)

    def _result_dict(self) -> dict | None:
        if self.result is None:
            return None
        return {
            "success": self.result.success,
            "processed": self.result.processed,
            "total": self.result.total,
            "errors": self.result.errors,
            "durationMs": int(round(self.result.duration * 1000)),
            "destinations": [serialize_path(path) for path in self.result.destinations],
        }


class _BridgeExportEventSink:
    def __init__(self, job: BridgeExportJob, completed_offset: int) -> None:
        self.job = job
        self.completed_offset = completed_offset

    def emit(self, event: ExportEvent) -> None:
        self.job._handle_event(event, self.completed_offset)


def _percent(processed: int, total: int) -> int:
    if total <= 0:
        return 0
    return max(0, min(100, int(round((processed / total) * 100))))


def _issue_from_log_message(message: str) -> dict | None:
    text = str(message or "").strip()
    if text.startswith("Error:"):
        detail = text.removeprefix("Error:").strip()
        title, _, rest = detail.partition(":")
        return {
            "level": "error",
            "title": title.strip() or "Exportación",
            "detail": rest.strip() or detail or "No se pudo exportar.",
        }
    if text.startswith("Aviso:"):
        detail = text.removeprefix("Aviso:").strip()
        title, _, rest = detail.partition(":")
        return {
            "level": "warning",
            "title": title.strip() or "Exportación",
            "detail": rest.strip() or detail,
        }
    return None
