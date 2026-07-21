"""Qt-free user config path resolution."""
from __future__ import annotations

import os
import json
import shutil
import sys
from pathlib import Path
from typing import Mapping
from uuid import uuid4


CONFIG_DIR_ENV_VAR = "FLATSHOT_CONFIG_DIR"
LEGACY_CONFIG_FILES = ("settings.json", "presets.json", "presets_v2.json")
LEGACY_CONFIG_DIRS = ("logs",)


class ConfigPathResolver:
    """Resolve FlatShot persistence paths without importing Qt.

    The default mirrors the current Qt fallback when no application name is
    configured: the platform config root itself.
    """

    def __init__(
        self,
        config_dir: str | Path | None = None,
        *,
        environ: Mapping[str, str] | None = None,
        home: str | Path | None = None,
        platform: str | None = None,
    ) -> None:
        self._config_dir = Path(config_dir).expanduser() if config_dir else None
        self._environ = environ if environ is not None else os.environ
        self._home = Path(home).expanduser() if home else Path.home()
        self._platform = platform

    def config_dir(self, *, create: bool = True) -> Path:
        explicit_path = self._config_dir or self._env_config_dir()
        path = explicit_path or self.default_user_config_dir(
            environ=self._environ,
            home=self._home,
            platform=self._platform,
        )
        if create:
            if explicit_path is None:
                self._migrate_legacy_default_config(path)
            path.mkdir(parents=True, exist_ok=True)
        return path

    def settings_file(self) -> Path:
        return self.config_dir() / "settings.json"

    def logs_dir(self) -> Path:
        path = self.config_dir() / "logs"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _env_config_dir(self) -> Path | None:
        configured = str(self._environ.get(CONFIG_DIR_ENV_VAR, "")).strip()
        if not configured:
            return None
        return Path(configured).expanduser()

    def _migrate_legacy_default_config(self, target: Path) -> None:
        legacy = self.legacy_user_config_dir(
            environ=self._environ,
            home=self._home,
            platform=self._platform,
        )
        if target == legacy or not legacy.exists():
            return

        has_legacy_data = any((legacy / name).exists() for name in LEGACY_CONFIG_FILES + LEGACY_CONFIG_DIRS)
        if not has_legacy_data:
            return

        target.mkdir(parents=True, exist_ok=True)
        for filename in LEGACY_CONFIG_FILES:
            source = legacy / filename
            destination = target / filename
            if not source.is_file():
                continue
            if filename == "presets.json" and (target / "presets_v2.json").is_file():
                _merge_legacy_presets_into_categorized(source, target / "presets_v2.json")
            elif destination.exists() and filename == "presets.json":
                _merge_legacy_flat_presets(source, destination)
            elif not destination.exists():
                shutil.copy2(source, destination)
        for dirname in LEGACY_CONFIG_DIRS:
            source = legacy / dirname
            destination = target / dirname
            if source.is_dir() and not destination.exists():
                shutil.copytree(source, destination)

    @staticmethod
    def legacy_user_config_dir(
        *,
        environ: Mapping[str, str] | None = None,
        home: str | Path | None = None,
        platform: str | None = None,
    ) -> Path:
        env = environ if environ is not None else os.environ
        user_home = Path(home).expanduser() if home else Path.home()
        current_platform = platform or sys.platform

        if current_platform.startswith("win"):
            return Path(env.get("LOCALAPPDATA") or (user_home / "AppData" / "Local"))
        if current_platform == "darwin":
            return user_home / "Library" / "Preferences"
        return Path(env.get("XDG_CONFIG_HOME") or (user_home / ".config"))

    @classmethod
    def default_user_config_dir(
        cls,
        *,
        environ: Mapping[str, str] | None = None,
        home: str | Path | None = None,
        platform: str | None = None,
    ) -> Path:
        base = cls.legacy_user_config_dir(environ=environ, home=home, platform=platform)
        current_platform = platform or sys.platform
        name = "FlatShot" if current_platform.startswith("win") or current_platform == "darwin" else "flatshot"
        return base / name


def _merge_legacy_flat_presets(source: Path, destination: Path) -> None:
    try:
        legacy = json.loads(source.read_text(encoding="utf-8"))
        current = json.loads(destination.read_text(encoding="utf-8"))
        if not isinstance(legacy, dict) or not isinstance(current, dict):
            return
        merged = dict(current)
        for name, settings in legacy.items():
            merged.setdefault(name, settings)
        if merged == current:
            return
        _atomic_json_write(destination, merged)
    except (OSError, ValueError, TypeError):
        return


def _merge_legacy_presets_into_categorized(source: Path, destination: Path) -> None:
    try:
        legacy = json.loads(source.read_text(encoding="utf-8"))
        categorized = json.loads(destination.read_text(encoding="utf-8"))
        if not isinstance(legacy, dict) or not isinstance(categorized, dict):
            return
        categories = categorized.setdefault("categories", {})
        uncategorized = categorized.setdefault("uncategorized", {})
        existing = set(uncategorized)
        for category in categories.values():
            if isinstance(category, dict):
                existing.update((category.get("presets") or {}).keys())
        changed = False
        for name, settings in legacy.items():
            if name not in existing:
                uncategorized[name] = settings
                changed = True
        if changed:
            _atomic_json_write(destination, categorized)
    except (OSError, ValueError, TypeError):
        return


def _atomic_json_write(path: Path, payload: dict) -> None:
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        temporary.write_text(json.dumps(payload, indent=4, ensure_ascii=False), encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)

