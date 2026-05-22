"""Neutral export events emitted by application runners."""
from __future__ import annotations

from dataclasses import dataclass


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


@dataclass(frozen=True)
class ExportFinishedEvent:
    success: bool
    processed: int
    total: int
    errors: int
    duration: float


ExportEvent = (
    ExportStartedEvent
    | ExportLogEvent
    | ExportProgressEvent
    | ExportImageCompletedEvent
    | ExportFinishedEvent
)
