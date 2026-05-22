import json

import flatshot.application.settings_service as settings_service_module
from flatshot.application.settings_service import DEFAULT_APP_SETTINGS, SettingsService
from flatshot.core.models import SHADOW_ENGINE_COMPAT, SHADOW_ENGINE_DEFAULT


def test_settings_service_does_not_import_pyqt():
    source = settings_service_module.Path(settings_service_module.__file__).read_text(encoding="utf-8")

    assert "PyQt6" not in source
    assert "QStandardPaths" not in source


def test_load_missing_settings_returns_independent_defaults(tmp_path):
    service = SettingsService(tmp_path / "settings.json")

    first = service.load()
    second = service.load()
    first["preview_guides"]["opacity"] = 99

    assert second["preview_guides"]["opacity"] == DEFAULT_APP_SETTINGS["preview_guides"]["opacity"]
    assert second["shadow_engine"] == SHADOW_ENGINE_DEFAULT


def test_load_normalizes_loaded_settings(tmp_path):
    settings_file = tmp_path / "settings.json"
    settings_file.write_text(
        json.dumps(
            {
                "format": "PNG",
                "bg_color": [1, 2, 3],
                "output_width": 1000,
            }
        ),
        encoding="utf-8",
    )
    service = SettingsService(settings_file)

    settings = service.load()

    assert settings["format"] == "PNG"
    assert settings["bg_color"] == (1, 2, 3)
    assert settings["output_width"] == 1000
    assert settings["output_height"] == DEFAULT_APP_SETTINGS["output_height"]
    assert settings["shadow_engine"] == SHADOW_ENGINE_COMPAT


def test_load_invalid_json_returns_defaults(tmp_path):
    settings_file = tmp_path / "settings.json"
    settings_file.write_text("{invalid", encoding="utf-8")

    settings = SettingsService(settings_file).load()

    assert settings == SettingsService.default_settings()


def test_load_non_object_json_returns_defaults(tmp_path):
    settings_file = tmp_path / "settings.json"
    settings_file.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")

    settings = SettingsService(settings_file).load()

    assert settings == SettingsService.default_settings()


def test_save_writes_settings_file(tmp_path):
    settings_file = tmp_path / "nested" / "settings.json"
    service = SettingsService(settings_file)
    settings = service.default_settings()
    settings["format"] = "PNG"
    settings["bg_color"] = (10, 20, 30)

    service.save(settings)

    saved = json.loads(settings_file.read_text(encoding="utf-8"))
    assert saved["format"] == "PNG"
    assert saved["bg_color"] == [10, 20, 30]
