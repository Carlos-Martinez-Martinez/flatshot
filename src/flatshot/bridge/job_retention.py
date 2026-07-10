"""Retention helpers for in-memory bridge jobs."""

from __future__ import annotations


def prune_finished_export_jobs(service, *, reserve_slots: int = 0) -> None:
    retained_limit = max(0, service.max_retained_jobs - max(0, int(reserve_slots)))
    finished_jobs = sorted(
        ((job_id, job) for job_id, job in service._jobs.items() if job.is_terminal),
        key=lambda item: item[1].retention_timestamp,
    )
    remove_count = len(finished_jobs) - retained_limit
    if remove_count <= 0:
        return
    for job_id, _job in finished_jobs[:remove_count]:
        del service._jobs[job_id]
        for key, mapped_job_id in list(service._export_idempotency.items()):
            if mapped_job_id == job_id:
                del service._export_idempotency[key]


def prune_finished_scan_jobs(service, *, reserve_slots: int = 0) -> None:
    retained_limit = max(0, service.max_retained_jobs - max(0, int(reserve_slots)))
    finished_jobs = sorted(
        ((job_id, job) for job_id, job in service._scan_jobs.items() if job.is_terminal),
        key=lambda item: item[1].retention_timestamp,
    )
    remove_count = len(finished_jobs) - retained_limit
    if remove_count <= 0:
        return
    for job_id, _job in finished_jobs[:remove_count]:
        del service._scan_jobs[job_id]
