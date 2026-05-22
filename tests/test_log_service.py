from datetime import datetime, timedelta

import flatshot.application.log_service as log_service_module
from flatshot.application.log_service import ActivityLogService


def test_activity_log_service_does_not_import_pyqt():
    source = log_service_module.Path(log_service_module.__file__).read_text(encoding="utf-8")

    assert "PyQt6" not in source
    assert "QStandardPaths" not in source


def test_activity_log_service_writes_export_entries(tmp_path):
    service = ActivityLogService(tmp_path / "logs", logger_name="flatshot-test-export")

    service.log_export_start("entrada", 2, "Preset")
    service.log_error("fallo", "img.png")
    service.log_export_complete("entrada", 1, 2, 3.4)

    entries = "".join(service.get_recent_entries())
    assert "Iniciando procesamiento de 'entrada' con preset 'Preset' (2 imágenes)" in entries
    assert "Error en 'img.png': fallo" in entries
    assert "Completado 'entrada': 1/2 imágenes en 3.4s" in entries


def test_activity_log_service_writes_queue_entries(tmp_path):
    service = ActivityLogService(tmp_path / "logs", logger_name="flatshot-test-queue")

    service.log_queue_start(3)
    service.log_queue_complete(2, 1, 9)

    entries = "".join(service.get_recent_entries())
    assert "Iniciando cola de 3 trabajos" in entries
    assert "Cola completada: 2 trabajos, 1 errores, 9 imágenes totales" in entries


def test_activity_log_service_cleans_old_logs(tmp_path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    old_date = (datetime.now() - timedelta(days=8)).strftime("%Y-%m-%d")
    old_log = log_dir / f"flatshot_{old_date}.log"
    old_log.write_text("old", encoding="utf-8")

    ActivityLogService(log_dir, logger_name="flatshot-test-cleanup")

    assert not old_log.exists()
