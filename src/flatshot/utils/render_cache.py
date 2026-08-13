import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any, Iterable, Mapping

from PIL import Image, UnidentifiedImageError

class RenderCache:
    """Manages cached full-resolution renders to speed up export."""

    CACHE_VERSION = 6
    CACHE_DIR_ENV_VAR = "FLATSHOT_RENDER_CACHE_DIR"
    OWNER_MARKER = ".flatshot-cache"
    OWNER_MARKER_CONTENT = "flatshot-render-cache-v1\n"
    _CACHE_FILE_RE = re.compile(r"^[0-9a-f]{64}\.(?:jpg|png)$", re.IGNORECASE)
    _TEMP_SIDECAR_RE = re.compile(
        r"^\.[0-9a-f]{64}\.(?:jpg|png)\.[A-Za-z0-9_-]+\.tmp$",
        re.IGNORECASE,
    )
    _MARKER_TEMP_RE = re.compile(r"^\.flatshot-cache\.[A-Za-z0-9_-]+\.tmp$")
    
    def __init__(self):
        configured_cache = os.environ.get(self.CACHE_DIR_ENV_VAR, "").strip()
        self.cache_dir = (
            Path(configured_cache).expanduser()
            if configured_cache
            else Path(tempfile.gettempdir()) / "flatshot_render_cache"
        )
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._claim_cache_directory()
        self._prune_temp_sidecars()

    def _claim_cache_directory(self) -> None:
        marker = self.cache_dir / self.OWNER_MARKER
        if marker.exists() or marker.is_symlink():
            try:
                marker_is_valid = (
                    not marker.is_symlink()
                    and marker.is_file()
                    and marker.read_text(encoding="utf-8") == self.OWNER_MARKER_CONTENT
                )
            except OSError:
                marker_is_valid = False
            if not marker_is_valid:
                raise ValueError("Render cache path is not a dedicated FlatShot cache directory.")
            self._prune_marker_temps()
            return
        unmanaged = [
            path.name
            for path in self.cache_dir.iterdir()
            if not self._is_managed_cache_entry(path)
        ]
        if unmanaged:
            raise ValueError("Render cache path must be a dedicated FlatShot cache directory.")
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="",
                prefix=f"{self.OWNER_MARKER}.",
                suffix=".tmp",
                dir=self.cache_dir,
                delete=False,
            ) as marker_file:
                marker_file.write(self.OWNER_MARKER_CONTENT)
                marker_file.flush()
                os.fsync(marker_file.fileno())
                temporary_path = Path(marker_file.name)
            os.replace(temporary_path, marker)
        except OSError as exc:
            if not self._is_valid_owner_marker(marker):
                raise ValueError(
                    "Render cache path is not a dedicated FlatShot cache directory."
                ) from exc
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
        if not self._is_valid_owner_marker(marker):
            raise ValueError("Render cache path is not a dedicated FlatShot cache directory.")
        self._prune_marker_temps()

    def _is_valid_owner_marker(self, marker: Path) -> bool:
        try:
            return (
                not marker.is_symlink()
                and marker.is_file()
                and marker.read_text(encoding="utf-8") == self.OWNER_MARKER_CONTENT
            )
        except OSError:
            return False

    def _is_managed_cache_entry(self, path: Path) -> bool:
        return not path.is_symlink() and path.is_file() and bool(
            self._CACHE_FILE_RE.fullmatch(path.name)
            or self._TEMP_SIDECAR_RE.fullmatch(path.name)
            or self._MARKER_TEMP_RE.fullmatch(path.name)
        )

    def _prune_marker_temps(self) -> None:
        for path in self.cache_dir.iterdir():
            if path.is_symlink() or not path.is_file() or not self._MARKER_TEMP_RE.fullmatch(path.name):
                continue
            try:
                path.unlink()
            except OSError:
                pass
        
    def _file_fingerprint(self, image_path: str) -> dict:
        path = Path(image_path)
        try:
            for _ in range(3):
                before = path.stat()
                digest = hashlib.sha256()
                with path.open("rb") as source:
                    for chunk in iter(lambda: source.read(1024 * 1024), b""):
                        digest.update(chunk)
                after = path.stat()
                if before.st_size == after.st_size and before.st_mtime_ns == after.st_mtime_ns:
                    return {
                        "path": str(path.resolve()),
                        "size": after.st_size,
                        "mtime_ns": after.st_mtime_ns,
                        "sha256": digest.hexdigest(),
                    }
            return {
                "path": str(path.resolve()),
                "size": after.st_size,
                "mtime_ns": after.st_mtime_ns,
                "sha256": digest.hexdigest(),
                "unstable": True,
            }
        except OSError:
            return {
                "path": str(path.resolve()),
                "size": None,
                "mtime_ns": None,
                "sha256": None,
            }

    @staticmethod
    def normalize_format(fmt: str | None) -> str:
        normalized = (fmt or "png").lower().lstrip(".")
        if normalized == "jpeg":
            return "jpg"
        if normalized not in {"jpg", "png"}:
            return "png"
        return normalized

    def get_cache_key(
        self,
        image_path: str,
        settings_dict: dict,
        curve_dict: dict,
        target_size: tuple,
        local_override: dict | None = None,
        export_format: str | None = None,
        *,
        export_options: Mapping[str, Any] | None = None,
    ) -> str:
        """Generate a unique key for a specific render configuration."""
        # Use a stable representation of the inputs
        # Settings and curve are sorted to ensure consistent hashing
        data = {
            "version": self.CACHE_VERSION,
            "source": self._file_fingerprint(image_path),
            "settings": settings_dict,
            "curve": curve_dict,
            "size": target_size,
            "local_override": local_override or {},
            "format": self.normalize_format(export_format),
        }
        normalized_export_options = {
            str(key): value
            for key, value in dict(export_options or {}).items()
            if value is not None
        }
        if normalized_export_options:
            data["export_options"] = normalized_export_options
        
        # Normalize floating point values to strings with fixed precision if necessary
        # but pydantic/json should be stable enough here for our purposes.
        dump = json.dumps(data, sort_keys=True)
        return hashlib.sha256(dump.encode('utf-8')).hexdigest()
        
    def get_cached_path(self, key: str, fmt: str = "png") -> Path:
        """Return the path where a cached render would be stored."""
        return self.cache_dir / f"{key}.{self.normalize_format(fmt)}"

    def get_temp_path(self, cache_path: Path, token: str) -> Path:
        """Return a sidecar temp path for atomic cache writes."""
        safe_token = "".join(ch for ch in str(token) if ch.isalnum() or ch in ("-", "_"))
        return cache_path.with_name(f".{cache_path.name}.{safe_token}.tmp")
         
    def exists(self, key: str, fmt: str = "png", validate: bool = False) -> bool:
        """Check if a cached render exists and is valid."""
        path = self.get_cached_path(key, fmt)
        try:
            if not path.exists() or path.stat().st_size <= 0:
                return False
            if not validate:
                return True
            with Image.open(path) as img:
                img.verify()
            return True
        except (OSError, UnidentifiedImageError):
            return False
        
    def clear(self):
        """Clear all cached renders."""
        for path in list(self._cache_files()) + list(self._temp_sidecars()):
            try:
                path.unlink()
            except OSError:
                pass

    def _prune_temp_sidecars(self) -> None:
        for temp_file in self._temp_sidecars():
            try:
                temp_file.unlink()
            except OSError:
                pass

    def _temp_sidecars(self) -> Iterable[Path]:
        return (
            path
            for path in self.cache_dir.iterdir()
            if not path.is_symlink()
            and path.is_file()
            and self._TEMP_SIDECAR_RE.fullmatch(path.name)
        )

    def _cache_files(self) -> Iterable[Path]:
        return (
            path for path in self.cache_dir.glob("*.*")
            if not path.is_symlink()
            and path.is_file()
            and self._CACHE_FILE_RE.fullmatch(path.name)
        )

    def prune(self, max_files=1000, max_bytes: int | None = 2 * 1024 * 1024 * 1024):
        """Remove oldest files if cache exceeds file or byte limits."""
        self._prune_temp_sidecars()

        files = []
        total_size = 0
        for path in self._cache_files():
            try:
                stat = path.stat()
            except OSError:
                continue
            files.append((path, stat.st_atime, stat.st_size))
            total_size += stat.st_size

        files.sort(key=lambda item: item[1])
        while files and (
            (max_files is not None and len(files) > max_files)
            or (max_bytes is not None and total_size > max_bytes)
        ):
            path, _atime, size = files.pop(0)
            try:
                path.unlink()
                total_size -= size
            except OSError:
                pass
