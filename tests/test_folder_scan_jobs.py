from pathlib import Path
from time import sleep

from flatshot.application.contracts import BatchScanResult
from flatshot.application.folder_scan_jobs import FolderScanJob


class SlowScanner:
    def scan_folders(self, folders, image_overrides=None, progress_callback=None, cancellation_token=None, **kwargs):
        for index in range(20):
            if cancellation_token is not None and cancellation_token.cancelled:
                break
            if progress_callback is not None:
                progress_callback(index + 1, 20)
            sleep(0.01)
        return BatchScanResult(total_folders=1)


def test_folder_scan_job_reports_progress_and_cancels_slow_scans(tmp_path):
    job = FolderScanJob(
        job_id="scan-1",
        folders=[Path(tmp_path)],
        scanner=SlowScanner(),
    )

    job.start()
    running = _wait_for(lambda: _snapshot_if(job, processed=True))
    job.cancel()
    final = _wait_for(lambda: _snapshot_if(job, status="cancelled"))

    assert running["status"] == "running"
    assert final["status"] == "cancelled"
    assert final["progress"]["processed"] < 20


def _wait_for(predicate):
    for _ in range(100):
        snapshot = predicate()
        if snapshot:
            return snapshot
        sleep(0.01)
    raise AssertionError("condition was not reached")


def _snapshot_if(job, *, processed: bool = False, status: str | None = None):
    snapshot = job.snapshot()
    if processed and snapshot["progress"]["processed"] <= 0:
        return None
    if status is not None and snapshot["status"] != status:
        return None
    return snapshot
