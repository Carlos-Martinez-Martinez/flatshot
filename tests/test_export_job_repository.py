from __future__ import annotations

import json
import os
import time

from flatshot.bridge.export_job_repository import ExportJobRepository


def test_manifest_retention_keeps_newest_entries_and_ignores_unrelated_files(tmp_path):
    repository = ExportJobRepository(tmp_path, max_retained_manifests=2)
    unrelated = tmp_path / "notes.json"
    unrelated.write_text("{}", encoding="utf-8")

    for index in range(3):
        repository.write_manifest(f"job-{index:08d}", {"jobId": f"job-{index:08d}"})
        time.sleep(0.01)

    assert not (tmp_path / "job-00000000.json").exists()
    assert (tmp_path / "job-00000001.json").exists()
    assert (tmp_path / "job-00000002.json").exists()
    assert unrelated.exists()
    assert json.loads((tmp_path / "job-00000002.json").read_text(encoding="utf-8"))["jobId"] == "job-00000002"


def test_manifest_retention_removes_only_safe_job_names(tmp_path):
    repository = ExportJobRepository(tmp_path, max_retained_manifests=1)
    old_job = tmp_path / "job-00000001.json"
    old_job.write_text("{}", encoding="utf-8")
    os.utime(old_job, (1, 1))
    unrelated = tmp_path / "notes.json"
    unrelated.write_text("{}", encoding="utf-8")

    repository.write_manifest("job-00000002", {"jobId": "job-00000002"})

    assert not old_job.exists()
    assert unrelated.exists()
