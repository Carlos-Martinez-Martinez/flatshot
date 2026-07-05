"""Reusable preflight checks for export workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import tempfile
from typing import Callable

from flatshot.application.contracts import ExportJobRequest


DEFAULT_EXPORT_SPACE_MULTIPLIER = 4
DEFAULT_EXPORT_SPACE_BUFFER_BYTES = 64 * 1024 * 1024


@dataclass(frozen=True)
class ExportSpaceCheck:
    source_bytes: int
    required_bytes: int
    free_bytes: int
    checked_path: Path


class InsufficientExportSpaceError(Exception):
    def __init__(self, check: ExportSpaceCheck) -> None:
        self.check = check
        super().__init__(
            f"Insufficient temporary space: {check.free_bytes} bytes free, "
            f"{check.required_bytes} bytes required."
        )


def estimate_export_source_bytes(requests: list[ExportJobRequest]) -> int:
    total = 0
    seen: set[str] = set()
    for request in requests:
        for path in request.input_files or []:
            source_path = Path(path)
            key = _path_key(source_path)
            if key in seen:
                continue
            seen.add(key)
            try:
                total += max(0, source_path.stat().st_size)
            except OSError:
                continue
    return total


def ensure_export_space(
    requests: list[ExportJobRequest],
    *,
    checked_path: Path | None = None,
    disk_usage: Callable[[str | Path], shutil._ntuple_diskusage] | None = None,
    multiplier: int = DEFAULT_EXPORT_SPACE_MULTIPLIER,
    buffer_bytes: int = DEFAULT_EXPORT_SPACE_BUFFER_BYTES,
) -> ExportSpaceCheck:
    path = checked_path or Path(tempfile.gettempdir())
    source_bytes = estimate_export_source_bytes(requests)
    required_bytes = (source_bytes * max(1, int(multiplier))) + max(0, int(buffer_bytes))
    usage = (disk_usage or shutil.disk_usage)(path)
    check = ExportSpaceCheck(
        source_bytes=source_bytes,
        required_bytes=required_bytes,
        free_bytes=max(0, int(usage.free)),
        checked_path=Path(path),
    )
    if source_bytes > 0 and check.free_bytes < check.required_bytes:
        raise InsufficientExportSpaceError(check)
    return check


def _path_key(path: Path) -> str:
    try:
        return str(path.resolve()).casefold()
    except OSError:
        return str(path.absolute()).casefold()
