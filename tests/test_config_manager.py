import json

from flatshot.utils.config import ConfigManager


def _use_temp_config_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(
        ConfigManager,
        "get_config_dir",
        staticmethod(lambda: tmp_path),
    )


def test_export_presets_to_file_writes_portable_bundle(tmp_path, monkeypatch):
    _use_temp_config_dir(monkeypatch, tmp_path)

    presets = ConfigManager._get_default_categorized_presets()
    presets.categories["custom"].presets["Mi preset"] = {
        "angle": 135,
        "distance": 18,
    }
    ConfigManager.save_all_presets(presets)

    export_path = tmp_path / "flatshot_presets.json"
    assert ConfigManager.export_presets_to_file(str(export_path)) is True

    exported = json.loads(export_path.read_text(encoding="utf-8"))
    assert exported["flatshot_export"]["type"] == "presets"
    assert exported["flatshot_export"]["version"] == ConfigManager.PRESETS_EXPORT_VERSION
    assert exported["presets"]["categories"]["custom"]["presets"]["Mi preset"]["angle"] == 135


def test_import_presets_from_bundle_merges_and_syncs_legacy_file(tmp_path, monkeypatch):
    _use_temp_config_dir(monkeypatch, tmp_path)

    existing = ConfigManager._get_default_categorized_presets()
    existing.categories["custom"].presets["Local"] = {
        "angle": 90,
        "distance": 20,
    }
    ConfigManager.save_all_presets(existing)

    incoming_path = tmp_path / "incoming_presets.json"
    incoming_path.write_text(
        json.dumps(
            {
                "flatshot_export": {"type": "presets", "version": 1},
                "presets": {
                    "categories": {
                        "custom": {
                            "name": "Personalizados",
                            "presets": {
                                "Remoto": {
                                    "angle": 140,
                                    "distance": 12,
                                }
                            },
                            "locked": False,
                        }
                    },
                    "uncategorized": {},
                },
            }
        ),
        encoding="utf-8",
    )

    imported = ConfigManager.import_presets_from_file(str(incoming_path), merge=True)

    flat = ConfigManager.get_flat_presets_from_categorized(imported)
    assert "Local" in flat
    assert "Remoto" in flat

    legacy_file = json.loads((tmp_path / ConfigManager.PRESETS_FILE).read_text(encoding="utf-8"))
    assert "Remoto" in legacy_file


def test_import_presets_accepts_legacy_flat_mapping(tmp_path, monkeypatch):
    _use_temp_config_dir(monkeypatch, tmp_path)

    legacy_import = tmp_path / "legacy_presets.json"
    legacy_import.write_text(
        json.dumps(
            {
                "Preset legado": {
                    "angle": 180,
                    "distance": 25,
                }
            }
        ),
        encoding="utf-8",
    )

    imported = ConfigManager.import_presets_from_file(str(legacy_import), merge=False)

    flat = ConfigManager.get_flat_presets_from_categorized(imported)
    assert "Preset legado" in flat
