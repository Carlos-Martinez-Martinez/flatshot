import hashlib
import json
from pathlib import Path
import tempfile
import shutil

class RenderCache:
    """Manages cached full-resolution renders to speed up export."""

    CACHE_VERSION = 2
    
    def __init__(self):
        self.cache_dir = Path(tempfile.gettempdir()) / "flatshot_render_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def _file_fingerprint(self, image_path: str) -> dict:
        path = Path(image_path)
        try:
            stat = path.stat()
            return {
                "path": str(path.resolve()),
                "size": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
            }
        except OSError:
            return {
                "path": str(path.resolve()),
                "size": None,
                "mtime_ns": None,
            }

    def get_cache_key(
        self,
        image_path: str,
        settings_dict: dict,
        curve_dict: dict,
        target_size: tuple,
        local_override: dict | None = None,
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
        }
        
        # Normalize floating point values to strings with fixed precision if necessary
        # but pydantic/json should be stable enough here for our purposes.
        dump = json.dumps(data, sort_keys=True)
        return hashlib.sha256(dump.encode('utf-8')).hexdigest()
        
    def get_cached_path(self, key: str, fmt: str = "png") -> Path:
        """Return the path where a cached render would be stored."""
        return self.cache_dir / f"{key}.{fmt}"
        
    def exists(self, key: str, fmt: str = "png") -> bool:
        """Check if a cached render exists and is valid."""
        path = self.get_cached_path(key, fmt)
        return path.exists() and path.stat().st_size > 0
        
    def clear(self):
        """Clear all cached renders."""
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def prune(self, max_files=500):
        """Remove oldest files if cache exceeds limit."""
        files = list(self.cache_dir.glob("*.*"))
        if len(files) > max_files:
            # Sort by access time
            files.sort(key=lambda x: x.stat().st_atime)
            for f in files[:len(files) - max_files]:
                try:
                    f.unlink()
                except:
                    pass
