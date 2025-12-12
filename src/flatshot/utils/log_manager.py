"""
Log Manager for FlatShot
Handles activity logging for export operations.
"""
import logging
from pathlib import Path
from datetime import datetime, timedelta
from PyQt6.QtCore import QStandardPaths


class LogManager:
    """Manages activity logs for FlatShot export operations."""
    
    _instance = None
    _logger = None
    
    @classmethod
    def get_instance(cls) -> 'LogManager':
        """Get singleton instance of LogManager."""
        if cls._instance is None:
            cls._instance = LogManager()
        return cls._instance
    
    def __init__(self):
        self.log_dir = self._get_log_dir()
        self._setup_logger()
        self._cleanup_old_logs()
    
    def _get_log_dir(self) -> Path:
        """Get the log directory path."""
        base_path = Path(QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppConfigLocation
        ))
        log_path = base_path / "logs"
        log_path.mkdir(parents=True, exist_ok=True)
        return log_path
    
    def _setup_logger(self):
        """Setup the file logger."""
        self._logger = logging.getLogger("flatshot")
        self._logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        self._logger.handlers.clear()
        
        # Create daily log file
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.log_dir / f"flatshot_{today}.log"
        
        handler = logging.FileHandler(log_file, encoding='utf-8')
        handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)
    
    def _cleanup_old_logs(self, days_to_keep: int = 7):
        """Remove logs older than specified days."""
        cutoff = datetime.now() - timedelta(days=days_to_keep)
        for log_file in self.log_dir.glob("flatshot_*.log"):
            try:
                # Parse date from filename
                date_str = log_file.stem.replace("flatshot_", "")
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                if file_date < cutoff:
                    log_file.unlink()
            except (ValueError, OSError):
                pass  # Skip files with unexpected names
    
    def log_export_start(self, folder: str, total_images: int, preset_name: str = None):
        """Log the start of an export operation."""
        preset_info = f" con preset '{preset_name}'" if preset_name else ""
        self._logger.info(
            f"Iniciando procesamiento de '{folder}'{preset_info} ({total_images} imágenes)"
        )
    
    def log_export_complete(self, folder: str, processed: int, total: int, duration_sec: float):
        """Log successful completion of export."""
        self._logger.info(
            f"Completado '{folder}': {processed}/{total} imágenes en {duration_sec:.1f}s"
        )
    
    def log_export_cancelled(self, folder: str, processed: int, total: int):
        """Log cancelled export."""
        self._logger.warning(
            f"Cancelado '{folder}': {processed}/{total} imágenes procesadas"
        )
    
    def log_error(self, message: str, image_name: str = None):
        """Log an error."""
        if image_name:
            self._logger.error(f"Error en '{image_name}': {message}")
        else:
            self._logger.error(message)
    
    def log_queue_start(self, num_jobs: int):
        """Log start of queue processing."""
        self._logger.info(f"Iniciando cola de {num_jobs} trabajos")
    
    def log_queue_complete(self, completed: int, errors: int, total_images: int):
        """Log completion of queue."""
        self._logger.info(
            f"Cola completada: {completed} trabajos, {errors} errores, {total_images} imágenes totales"
        )
    
    def get_today_log_path(self) -> Path:
        """Get path to today's log file."""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"flatshot_{today}.log"
    
    def get_recent_entries(self, max_lines: int = 50) -> list:
        """Get recent log entries from today's log."""
        log_file = self.get_today_log_path()
        if not log_file.exists():
            return []
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                return lines[-max_lines:]
        except Exception:
            return []
