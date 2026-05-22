"""Qt-free activity logging service."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path


class ActivityLogService:
    """File-backed logger for export and queue activity."""

    def __init__(self, log_dir: str | Path, *, logger_name: str = "flatshot") -> None:
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._logger_name = logger_name
        self._setup_logger()
        self._cleanup_old_logs()

    @classmethod
    def from_config_dir(cls, config_dir: str | Path) -> "ActivityLogService":
        return cls(Path(config_dir) / "logs")

    def _setup_logger(self) -> None:
        self._logger = logging.getLogger(self._logger_name)
        self._logger.setLevel(logging.INFO)
        self._logger.handlers.clear()

        handler = logging.FileHandler(self.get_today_log_path(), encoding="utf-8")
        handler.setLevel(logging.INFO)
        handler.setFormatter(
            logging.Formatter(
                "[%(asctime)s] [%(levelname)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        self._logger.addHandler(handler)

    def _cleanup_old_logs(self, days_to_keep: int = 7) -> None:
        cutoff = datetime.now() - timedelta(days=days_to_keep)
        for log_file in self.log_dir.glob("flatshot_*.log"):
            try:
                file_date = datetime.strptime(
                    log_file.stem.replace("flatshot_", ""),
                    "%Y-%m-%d",
                )
                if file_date < cutoff:
                    log_file.unlink()
            except (ValueError, OSError):
                pass

    def log_export_start(self, folder: str, total_images: int, preset_name: str = None) -> None:
        preset_info = f" con preset '{preset_name}'" if preset_name else ""
        self._logger.info(
            f"Iniciando procesamiento de '{folder}'{preset_info} ({total_images} imágenes)"
        )

    def log_export_complete(self, folder: str, processed: int, total: int, duration_sec: float) -> None:
        self._logger.info(
            f"Completado '{folder}': {processed}/{total} imágenes en {duration_sec:.1f}s"
        )

    def log_export_cancelled(self, folder: str, processed: int, total: int) -> None:
        self._logger.warning(
            f"Cancelado '{folder}': {processed}/{total} imágenes procesadas"
        )

    def log_error(self, message: str, image_name: str = None) -> None:
        if image_name:
            self._logger.error(f"Error en '{image_name}': {message}")
        else:
            self._logger.error(message)

    def log_queue_start(self, num_jobs: int) -> None:
        self._logger.info(f"Iniciando cola de {num_jobs} trabajos")

    def log_queue_complete(self, completed: int, errors: int, total_images: int) -> None:
        self._logger.info(
            f"Cola completada: {completed} trabajos, {errors} errores, {total_images} imágenes totales"
        )

    def get_today_log_path(self) -> Path:
        today = datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"flatshot_{today}.log"

    def get_recent_entries(self, max_lines: int = 50) -> list[str]:
        log_file = self.get_today_log_path()
        if not log_file.exists():
            return []

        try:
            with log_file.open("r", encoding="utf-8") as handle:
                return handle.readlines()[-max_lines:]
        except Exception:
            return []
