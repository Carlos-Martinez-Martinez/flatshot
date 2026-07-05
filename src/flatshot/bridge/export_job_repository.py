"""JSON persistence for bridge export job manifests."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Mapping


_JOB_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{8,128}$")


class ExportJobRepository:
    """Persist export job manifests under one configured directory."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def manifest_path(self, job_id: str) -> Path:
        safe_job_id = self._safe_job_id(job_id)
        return self.root / f"{safe_job_id}.json"

    def write_manifest(self, job_id: str, payload: Mapping[str, Any]) -> None:
        manifest_path = self.manifest_path(job_id)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = manifest_path.with_name(f".{manifest_path.name}.tmp")
        with tmp_path.open("w", encoding="utf-8") as handle:
            json.dump(dict(payload), handle, indent=2, ensure_ascii=False)
        os.replace(tmp_path, manifest_path)

    @staticmethod
    def _safe_job_id(job_id: str) -> str:
        value = str(job_id or "").strip()
        if not _JOB_ID_PATTERN.fullmatch(value):
            raise ValueError("Invalid export job id.")
        return value
