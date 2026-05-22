"""
Log Manager for FlatShot.

Compatibility wrapper that keeps the current Qt-based log directory resolver
for the GUI while delegating log file operations to a Qt-free service.
"""
from pathlib import Path

from PyQt6.QtCore import QStandardPaths

from flatshot.application.log_service import ActivityLogService


class LogManager(ActivityLogService):
    """Manages activity logs for FlatShot export operations."""

    _instance = None

    @classmethod
    def get_instance(cls) -> "LogManager":
        """Get singleton instance of LogManager."""
        if cls._instance is None:
            cls._instance = LogManager()
        return cls._instance

    def __init__(self):
        super().__init__(self._get_log_dir())

    def _get_log_dir(self) -> Path:
        """Get the log directory path using the existing Qt resolver."""
        base_path = Path(
            QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.AppConfigLocation
            )
        )
        log_path = base_path / "logs"
        log_path.mkdir(parents=True, exist_ok=True)
        return log_path
