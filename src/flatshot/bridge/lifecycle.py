"""Bridge lifecycle coordination for background jobs."""

from __future__ import annotations

from time import perf_counter


def shutdown_service(service, timeout: float = 5.0) -> bool:
    """Cancel active background work and wait for worker threads to exit."""
    with service._jobs_lock:
        export_jobs = [
            job for job in service._jobs.values()
            if job.status in {"queued", "running", "paused", "cancelling"}
        ]
    with service._scan_jobs_lock:
        scan_jobs = [
            job for job in service._scan_jobs.values()
            if job.status in {"queued", "running", "cancelling"}
        ]
    for job in export_jobs:
        job.cancel()
    for job in scan_jobs:
        job.cancel()

    deadline = perf_counter() + max(0.0, float(timeout))
    all_stopped = True
    for job in [*export_jobs, *scan_jobs]:
        remaining = max(0.0, deadline - perf_counter())
        if not job.join(remaining):
            all_stopped = False
    return all_stopped
