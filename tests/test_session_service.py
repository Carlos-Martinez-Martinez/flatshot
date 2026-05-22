import json
from pathlib import Path

import flatshot.application.session_service as session_service_module
from flatshot.application.session_service import SessionService
from flatshot.utils.session_manager import SessionManager


def test_session_service_does_not_import_pyqt():
    source = session_service_module.Path(session_service_module.__file__).read_text(encoding="utf-8")

    assert "PyQt6" not in source
    assert "QStandardPaths" not in source
    assert "QMessageBox" not in source


def test_default_session_file_uses_flatshot_session_path(tmp_path):
    assert SessionService.default_session_file(tmp_path) == tmp_path / ".flatshot" / "session.json"


def test_save_and_load_session_roundtrip(tmp_path):
    service = SessionService(tmp_path / "nested" / "session.json")
    data = {
        "current_preset": "Luz cenital",
        "selected_folders": ["C:/imagenes"],
        "export_config": {"format": "PNG"},
        "unicode": "ñ",
    }

    assert service.save_session(data) is True

    loaded = service.load_session()
    saved = json.loads(service.session_file.read_text(encoding="utf-8"))
    assert loaded == data
    assert saved["unicode"] == "ñ"


def test_load_missing_invalid_or_non_object_session_returns_none(tmp_path):
    missing = SessionService(tmp_path / "missing.json")
    assert missing.load_session() is None

    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text("{invalid", encoding="utf-8")
    assert SessionService(invalid_path).load_session() is None

    list_path = tmp_path / "list.json"
    list_path.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")
    assert SessionService(list_path).load_session() is None


def test_clear_session_deletes_file_and_tolerates_missing(tmp_path):
    session_file = tmp_path / "session.json"
    session_file.write_text(json.dumps({"ok": True}), encoding="utf-8")
    service = SessionService(session_file)

    assert service.clear_session() is True
    assert not session_file.exists()
    assert service.clear_session() is True


def test_build_session_data_preserves_existing_session_shape(tmp_path):
    session = SessionService.build_session_data(
        geometry="geometry64",
        state="state64",
        selected_folders=[tmp_path / "entrada", "D:/otra"],
        current_preset="Preset",
        current_mock="dark",
        splitter_sizes=(100, 200),
        output_folder_name="_SALIDA_PRO",
        suffix="_pro",
        export_format="JPG",
        output_destination="custom",
        custom_output_path=tmp_path / "salida",
        shadow_settings={"angle": 180, "distance": 25},
    )

    assert session == {
        "geometry": "geometry64",
        "state": "state64",
        "selected_folders": [str(tmp_path / "entrada"), "D:/otra"],
        "current_preset": "Preset",
        "current_mock": "dark",
        "splitter_sizes": [100, 200],
        "export_config": {
            "output_folder_name": "_SALIDA_PRO",
            "suffix": "_pro",
            "format": "JPG",
            "output_destination": "custom",
            "custom_output_path": str(tmp_path / "salida"),
        },
        "shadow_settings": {"angle": 180, "distance": 25},
    }


def test_session_manager_delegates_to_session_service(tmp_path, monkeypatch):
    session_file = tmp_path / ".flatshot" / "session.json"
    monkeypatch.setattr(
        SessionService,
        "default_session_file",
        staticmethod(lambda home=None: session_file),
    )
    manager = SessionManager()

    assert manager.session_file == session_file
    assert manager.save_session({"current_mock": "dark"}) is True
    assert manager.load_session() == {"current_mock": "dark"}

    manager.clear_session()
    assert not session_file.exists()
