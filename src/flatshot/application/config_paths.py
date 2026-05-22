"""Qt-free user config path resolution."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Mapping


CONFIG_DIR_ENV_VAR = "FLATSHOT_CONFIG_DIR"


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
    ) -> None:
        self._config_dir = Path(config_dir).expanduser() if config_dir else None
        self._environ = environ if environ is not None else os.environ
        self._home = Path(home).expanduser() if home else Path.home()

    def config_dir(self, *, create: bool = True) -> Path:
        path = self._config_dir or self._env_config_dir() or self.default_user_config_dir(
            environ=self._environ,
            home=self._home,
        )
        if create:
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

    @staticmethod
    def default_user_config_dir(
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
