"""Background scan jobs for large local folders."""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter
from typing import Any

from flatshot.application.contracts import BatchScanResult
from flatshot.application.execution_control import CancellationToken
from flatshot.application.folder_scanner import FolderScanner


TERMINAL_SCAN_STATUSES = {"completed", "cancelled", "failed"}


@dataclass
class FolderScanJob:
    job_id: str
    folders: list[Path]
    image_overrides: dict[str, Any] = field(default_factory=dict)
    scanner: FolderScanner = field(default_factory=FolderScanner)
    verify_images: bool = True
    recursive: bool = False
    status: str = "queued"
    processed: int = 0
    total: int = 0
    result: BatchScanResult | None = None
    errors: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.cancellation_token = CancellationToken()
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._started_at = 0.0
        self._finished_at = 0.0

    def start(self) -> None:
        with self._lock:
            if self.status != "queued":
                return
            self.status = "running"
            self.total = max(1, len(self.folders))
            self._started_at = perf_counter()
        self._thread = threading.Thread(target=self._run, name=f"flatshot-scan-{self.job_id}", daemon=False)
        self._thread.start()

    def cancel(self) -> None:
        with self._lock:
            if self.status in {"queued", "running"}:
                self.status = "cancelling"
                self.cancellation_token.cancel()

    def join(self, timeout: float | None = None) -> bool:
        thread = self._thread
        if thread is None:
            return True
        thread.join(timeout=timeout)
        return not thread.is_alive()

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "ok": True,
                "jobId": self.job_id,
                "status": self.status,
                "progress": {
                    "processed": self.processed,
                    "total": self.total,
                    "percent": _percent(self.processed, self.total),
                },
                "errors": list(self.errors),
                "durationMs": int(round(self._duration_seconds_locked() * 1000)),
                "result": self.result,
            }

    @property
    def is_terminal(self) -> bool:
        return self.status in TERMINAL_SCAN_STATUSES

    @property
    def retention_timestamp(self) -> float:
        return self._finished_at or self._started_at

    def _run(self) -> None:
        try:
            result = self.scanner.scan_folders(
                self.folders,
                dict(self.image_overrides),
                progress_callback=self._record_progress,
                verify_images=self.verify_images,
                recursive=self.recursive,
                cancellation_token=self.cancellation_token,
            )
            with self._lock:
                self.result = result
                self.processed = self.processed if self.cancellation_token.cancelled else self.total
                self.status = "cancelled" if self.cancellation_token.cancelled else "completed"
                self._finished_at = perf_counter()
        except Exception as exc:
            with self._lock:
                self.status = "failed"
                self.errors = [str(exc)]
                self._finished_at = perf_counter()

    def _record_progress(self, processed: int, total: int) -> None:
        with self._lock:
            self.processed = max(0, int(processed))
            self.total = max(1, int(total))

    def _duration_seconds_locked(self) -> float:
        if not self._started_at:
            return 0.0
        end = self._finished_at or perf_counter()
        return max(0.0, end - self._started_at)


def _percent(processed: int, total: int) -> int:
    if total <= 0:
        return 0
    return max(0, min(100, int(round((processed / total) * 100))))
