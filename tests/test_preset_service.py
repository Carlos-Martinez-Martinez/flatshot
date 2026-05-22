import json

import pytest

import flatshot.application.preset_service as preset_service_module
from flatshot.application.preset_service import PresetService
from flatshot.core.models import SHADOW_ENGINE_COMPAT, SHADOW_ENGINE_DEFAULT


def test_preset_service_does_not_import_pyqt():
    source = preset_service_module.Path(preset_service_module.__file__).read_text(encoding="utf-8")

    assert "PyQt6" not in source
    assert "QStandardPaths" not in source
    assert "QMessageBox" not in source


def test_default_presets_use_realistic_v2(tmp_path):
    service = PresetService(tmp_path)

    flat = service.get_flat_presets_from_categorized(service.get_default_categorized_presets())

    assert flat
    assert {settings["shadow_engine"] for settings in flat.values()} == {SHADOW_ENGINE_DEFAULT}


def test_flat_preset_load_and_save_adds_shadow_engine(tmp_path):
    service = PresetService(tmp_path)
    raw = {"Antiguo": {"angle": 180, "distance": 25}}
    service.presets_path.write_text(json.dumps(raw), encoding="utf-8")

    loaded = service.load_presets()
    assert loaded["Antiguo"]["shadow_engine"] == SHADOW_ENGINE_COMPAT

    service.save_presets(raw)
    saved = json.loads(service.presets_path.read_text(encoding="utf-8"))
    assert saved["Antiguo"]["shadow_engine"] == SHADOW_ENGINE_COMPAT


def test_load_categorized_presets_migrates_legacy_file(tmp_path):
    service = PresetService(tmp_path)
    service.presets_path.write_text(
        json.dumps({"Preset legado": {"angle": 180, "distance": 25}}),
        encoding="utf-8",
    )

    categorized = service.load_categorized_presets()
    flat = service.get_flat_presets_from_categorized(categorized)

    assert "Preset legado" in flat
    assert flat["Preset legado"]["shadow_engine"] == SHADOW_ENGINE_COMPAT
    assert service.categorized_presets_path.exists()


def test_save_flat_presets_preserves_existing_categories(tmp_path):
    service = PresetService(tmp_path)
    categorized = service.get_default_categorized_presets()
    categorized.categories["custom"].presets["Local"] = {"angle": 90, "distance": 20}
    service.save_all_presets(categorized)

    flat = service.load_flat_presets()
    flat["Local"]["angle"] = 135
    flat["Nuevo"] = {"angle": 45, "distance": 12}
    service.save_flat_presets_preserving_categories(flat)

    saved = service.load_categorized_presets()
    assert saved.categories["custom"].presets["Local"]["angle"] == 135
    assert saved.uncategorized["Nuevo"]["shadow_engine"] == SHADOW_ENGINE_COMPAT


def test_export_presets_to_file_writes_portable_bundle(tmp_path):
    service = PresetService(tmp_path)
    presets = service.get_default_categorized_presets()
    presets.categories["custom"].presets["Mi preset"] = {"angle": 135, "distance": 18}
    service.save_all_presets(presets)

    export_path = tmp_path / "flatshot_presets.json"
    assert service.export_presets_to_file(export_path) is True

    exported = json.loads(export_path.read_text(encoding="utf-8"))
    assert exported["flatshot_export"]["type"] == "presets"
    assert exported["flatshot_export"]["version"] == service.PRESETS_EXPORT_VERSION
    assert exported["presets"]["categories"]["custom"]["presets"]["Mi preset"]["angle"] == 135
    assert (
        exported["presets"]["categories"]["custom"]["presets"]["Mi preset"]["shadow_engine"]
        == SHADOW_ENGINE_COMPAT
    )


def test_import_presets_from_bundle_merges_and_syncs_legacy_file(tmp_path):
    service = PresetService(tmp_path)
    existing = service.get_default_categorized_presets()
    existing.categories["custom"].presets["Local"] = {"angle": 90, "distance": 20}
    service.save_all_presets(existing)

    incoming_path = tmp_path / "incoming_presets.json"
    incoming_path.write_text(
        json.dumps(
            {
                "flatshot_export": {"type": "presets", "version": 1},
                "presets": {
                    "categories": {
                        "custom": {
                            "name": "Personalizados",
                            "presets": {"Remoto": {"angle": 140, "distance": 12}},
                            "locked": False,
                        }
                    },
                    "uncategorized": {},
                },
            }
        ),
        encoding="utf-8",
    )

    imported = service.import_presets_from_file(incoming_path, merge=True)

    flat = service.get_flat_presets_from_categorized(imported)
    assert "Local" in flat
    assert "Remoto" in flat

    legacy_file = json.loads(service.presets_path.read_text(encoding="utf-8"))
    assert "Remoto" in legacy_file
    assert legacy_file["Remoto"]["shadow_engine"] == SHADOW_ENGINE_COMPAT


def test_import_presets_accepts_legacy_flat_mapping(tmp_path):
    service = PresetService(tmp_path)
    legacy_import = tmp_path / "legacy_presets.json"
    legacy_import.write_text(
        json.dumps({"Preset legado": {"angle": 180, "distance": 25}}),
        encoding="utf-8",
    )

    imported = service.import_presets_from_file(legacy_import, merge=False)

    flat = service.get_flat_presets_from_categorized(imported)
    assert "Preset legado" in flat
    assert flat["Preset legado"]["shadow_engine"] == SHADOW_ENGINE_COMPAT


def test_preset_name_operations_return_updated_flat_presets():
    presets = {"Uno": {"angle": 1}, "Dos": {"angle": 2}}

    presets = PresetService.save_current_preset(presets, "Uno", {"angle": 10})
    assert presets["Uno"]["angle"] == 10

    presets = PresetService.create_preset(presets, "Tres", {"angle": 3})
    assert presets["Tres"]["angle"] == 3

    presets = PresetService.rename_preset(presets, "Tres", "Cuatro")
    assert "Tres" not in presets
    assert presets["Cuatro"]["angle"] == 3

    presets = PresetService.delete_preset(presets, "Cuatro")
    assert "Cuatro" not in presets


def test_preset_name_operations_reject_invalid_changes():
    with pytest.raises(ValueError):
        PresetService.create_preset({"Uno": {}}, "Uno", {})
    with pytest.raises(ValueError):
        PresetService.rename_preset({"Uno": {}, "Dos": {}}, "Uno", "Dos")
    with pytest.raises(ValueError):
        PresetService.delete_preset({"Uno": {}}, "Dos")
