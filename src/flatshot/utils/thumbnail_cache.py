"""Persistent thumbnail cache for local bridge previews."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path


class ThumbnailCache:
    CACHE_VERSION = 1

    def __init__(self, cache_dir: str | Path) -> None:
        self.cache_dir = Path(cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, source_path: Path, size: int) -> bytes | None:
        path = self._cache_path(source_path, size)
        try:
            return path.read_bytes() if path.is_file() else None
        except OSError:
            return None

    def put(self, source_path: Path, size: int, payload: bytes) -> None:
        cache_path = self._cache_path(source_path, size)
        tmp_path = cache_path.with_name(f".{cache_path.name}.tmp")
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path.write_bytes(payload)
            os.replace(tmp_path, cache_path)
        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass

    def _cache_path(self, source_path: Path, size: int) -> Path:
        return self.cache_dir / f"{self._key(source_path, size)}.png"

    def _key(self, source_path: Path, size: int) -> str:
        stat = source_path.stat()
        digest = hashlib.sha256()
        digest.update(str(self.CACHE_VERSION).encode("ascii"))
        digest.update(b"\0")
        digest.update(source_path.resolve().as_posix().encode("utf-8", errors="surrogatepass"))
        digest.update(b"\0")
        digest.update(str(int(size)).encode("ascii"))
        digest.update(b"\0")
        digest.update(str(stat.st_size).encode("ascii"))
        digest.update(b"\0")
        digest.update(str(stat.st_mtime_ns).encode("ascii"))
        return digest.hexdigest()
