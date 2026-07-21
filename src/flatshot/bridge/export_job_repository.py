"""JSON persistence for bridge export job manifests."""

from __future__ import annotations

import json
import os
import re
import threading
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4


_JOB_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{8,128}$")


class ExportJobRepository:
    """Persist export job manifests under one configured directory."""

    def __init__(self, root: Path, *, max_retained_manifests: int = 100) -> None:
        self.root = Path(root)
        self.max_retained_manifests = max(1, int(max_retained_manifests))
        self._lock = threading.RLock()

    def manifest_path(self, job_id: str) -> Path:
        safe_job_id = self._safe_job_id(job_id)
        return self.root / f"{safe_job_id}.json"

    def write_manifest(self, job_id: str, payload: Mapping[str, Any]) -> None:
        with self._lock:
            manifest_path = self.manifest_path(job_id)
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = manifest_path.with_name(f".{manifest_path.name}.{uuid4().hex}.tmp")
            try:
                with tmp_path.open("w", encoding="utf-8") as handle:
                    json.dump(dict(payload), handle, indent=2, ensure_ascii=False)
                os.replace(tmp_path, manifest_path)
            finally:
                tmp_path.unlink(missing_ok=True)
            self.prune()

    def prune(self) -> int:
        """Keep the newest safe job manifests and return the removal count."""
        with self._lock:
            if not self.root.exists():
                return 0
            manifests = []
            for path in self.root.glob("*.json"):
                if not path.is_file() or not _JOB_ID_PATTERN.fullmatch(path.stem):
                    continue
                try:
                    manifests.append((path.stat().st_mtime_ns, path.name, path))
                except OSError:
                    continue
            manifests.sort(key=lambda item: (item[0], item[1]), reverse=True)
            removed = 0
            for _mtime, _name, path in manifests[self.max_retained_manifests :]:
                try:
                    path.unlink()
                    removed += 1
                except OSError:
                    continue
            return removed

    @staticmethod
    def _safe_job_id(job_id: str) -> str:
        value = str(job_id or "").strip()
        if not _JOB_ID_PATTERN.fullmatch(value):
            raise ValueError("Invalid export job id.")
        return value
