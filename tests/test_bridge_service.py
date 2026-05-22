from pathlib import Path

import pytest
from PIL import Image

from flatshot.application.config_paths import ConfigPathResolver
from flatshot.application.preset_service import PresetService
from flatshot.bridge.errors import InvalidRequestError, error_response
from flatshot.bridge.serialization import image_file_info_to_dict
from flatshot.bridge.service import FlatShotBridgeService
from flatshot.application.contracts import ImageFileInfo


def _png(path: Path) -> Path:
    Image.new("RGBA", (4, 4), (255, 0, 0, 255)).save(path)
    return path


def _service(config_dir: Path) -> FlatShotBridgeService:
    return FlatShotBridgeService(config_resolver=ConfigPathResolver(config_dir))


def test_bridge_health_app_info_and_capabilities(tmp_path):
    service = _service(tmp_path / "missing-config")

    assert service.health() == {
        "ok": True,
        "service": "flatshot-bridge",
        "mode": "development",
    }
    assert service.app_info()["bridgeVersion"] == "0.1.0"
    assert service.app_info()["engine"] == "python"
    assert service.capabilities() == {
        "folderScan": True,
        "presetsRead": True,
        "previewRender": False,
        "exportRun": False,
        "exportProgress": False,
        "nativeFolderPicker": False,
    }


def test_bridge_presets_return_defaults_without_creating_config_dir(tmp_path):
    config_dir = tmp_path / "missing-config"
    service = _service(config_dir)

    response = service.list_presets()

    assert response["source"] == "defaults"
    assert [item["name"] for item in response["items"]] == ["Luz cenital", "Estándar oscuro"]
    assert not config_dir.exists()


def test_bridge_presets_read_existing_categorized_config(tmp_path):
    preset_service = PresetService(tmp_path)
    categorized = preset_service.get_default_categorized_presets()
    categorized.categories["custom"].presets["Local"] = {"angle": 90, "distance": 10}
    preset_service.save_all_presets(categorized)

    response = _service(tmp_path).list_presets()

    assert response["source"] == "config"
    assert "Local" in {item["name"] for item in response["items"]}


def test_bridge_serializes_image_info_with_stable_keys(tmp_path):
    image = ImageFileInfo(
        path=tmp_path / "item.png",
        name="item.png",
        stem="item",
        suffix=".png",
        size_bytes=123,
        has_local_override=True,
    )

    assert image_file_info_to_dict(image) == {
        "path": (tmp_path / "item.png").as_posix(),
        "name": "item.png",
        "stem": "item",
        "suffix": ".png",
        "sizeBytes": 123,
        "hasLocalOverride": True,
    }


def test_bridge_error_response_is_controlled():
    response = error_response(InvalidRequestError("Bad input."))

    assert response == {
        "ok": False,
        "error": {
            "code": "invalid_request",
            "message": "Bad input.",
        },
    }


def test_bridge_scan_empty_folder(tmp_path):
    response = _service(tmp_path / "config").scan_folders({"folders": [str(tmp_path)]})

    assert response["totalFolders"] == 1
    assert response["totalImages"] == 0
    assert response["adjustedImages"] == 0
    assert response["folders"][0]["exists"] is True
    assert response["folders"][0]["isDir"] is True
    assert response["folders"][0]["images"] == []
    assert response["errors"] == []


def test_bridge_scan_folder_with_png(tmp_path):
    png = _png(tmp_path / "b.png")
    _png(tmp_path / "a.png")
    (tmp_path / "notes.txt").write_text("ignore", encoding="utf-8")

    response = _service(tmp_path / "config").scan_folders({"folders": [str(tmp_path)]})

    assert response["totalFolders"] == 1
    assert response["totalImages"] == 2
    assert [image["name"] for image in response["folders"][0]["images"]] == ["a.png", "b.png"]
    assert response["folders"][0]["images"][1]["path"] == png.as_posix()
    assert response["folders"][0]["images"][1]["sizeBytes"] > 0


def test_bridge_scan_missing_folder_returns_partial_error(tmp_path):
    missing = tmp_path / "missing"

    response = _service(tmp_path / "config").scan_folders({"folders": [str(missing)]})

    assert response["totalFolders"] == 1
    assert response["totalImages"] == 0
    assert response["folders"][0]["exists"] is False
    assert response["errors"]


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"folders": "not-a-list"},
        {"folders": [""]},
        {"folders": [123]},
        {"folders": [], "imageOverrides": []},
    ],
)
def test_bridge_scan_rejects_invalid_input(payload, tmp_path):
    with pytest.raises(InvalidRequestError):
        _service(tmp_path / "config").scan_folders(payload)
