"""Bridge scan-job response helpers."""
from __future__ import annotations

from typing import Any

from flatshot.application.folder_scan_jobs import FolderScanJob
from flatshot.bridge.serialization import batch_scan_result_to_dict


def scan_job_snapshot(
    job: FolderScanJob,
    *,
    image_offset: int = 0,
    image_limit: int | None = None,
    image_id_for_path=None,
) -> dict[str, Any]:
    snapshot = job.snapshot()
    result = snapshot.pop("result", None)
    if result is not None:
        snapshot["result"] = batch_scan_result_to_dict(
            result,
            image_offset=image_offset,
            image_limit=image_limit,
            image_id_for_path=image_id_for_path,
        )
    return snapshot
