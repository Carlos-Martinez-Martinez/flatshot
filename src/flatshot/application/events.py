"""Neutral application events emitted by Qt-free runners."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExportStartedEvent:
    source_images: int
    total_outputs: int


@dataclass(frozen=True)
class ExportLogEvent:
    message: str


@dataclass(frozen=True)
class ExportProgressEvent:
    processed: int
    total: int
    percent: int


@dataclass(frozen=True)
class ExportImageCompletedEvent:
    image_name: str
    success: bool
    source_path: Path | None = None
    output_path: Path | None = None


@dataclass(frozen=True)
class ExportFinishedEvent:
    success: bool
    processed: int
    total: int
    errors: int
    duration: float


@dataclass(frozen=True)
class QueueStartedEvent:
    total_jobs: int


@dataclass(frozen=True)
class QueueJobStartedEvent:
    job_index: int
    folder_path: Path


@dataclass(frozen=True)
class QueueJobProgressEvent:
    job_index: int
    progress_percent: int


@dataclass(frozen=True)
class QueueJobCompletedEvent:
    job_index: int
    success: bool
    processed: int
    total: int
    duration: float


@dataclass(frozen=True)
class QueueFinishedEvent:
    completed_jobs: int
    errors: int
    total_images: int


@dataclass(frozen=True)
class QueuePausedEvent:
    pass


@dataclass(frozen=True)
class QueueResumedEvent:
    pass


@dataclass(frozen=True)
class QueueCancelledEvent:
    pass


ExportEvent = (
    ExportStartedEvent
    | ExportLogEvent
    | ExportProgressEvent
    | ExportImageCompletedEvent
    | ExportFinishedEvent
)

QueueEvent = (
    QueueStartedEvent
    | QueueJobStartedEvent
    | QueueJobProgressEvent
    | QueueJobCompletedEvent
    | QueueFinishedEvent
    | QueuePausedEvent
    | QueueResumedEvent
    | QueueCancelledEvent
)

ApplicationEvent = ExportEvent | QueueEvent
