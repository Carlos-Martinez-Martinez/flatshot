from pathlib import Path
import base64
import json
import shutil
import threading
from io import BytesIO
from time import sleep

import pytest
from PIL import Image

from flatshot.application.config_paths import ConfigPathResolver
from flatshot.application.export_runner import ExportRunner
from flatshot.application.events import ExportImageCompletedEvent, ExportLogEvent
from flatshot.application.preset_service import PresetService
from flatshot.bridge.errors import BridgeError, InvalidRequestError, error_response
from flatshot.bridge.export_job_repository import ExportJobRepository
from flatshot.bridge.export_jobs import BridgeExportJob
from flatshot.bridge import onboarding_assets
from flatshot.bridge.serialization import image_file_info_to_dict, serialize_path
from flatshot.bridge.service import FlatShotBridgeService
from flatshot.application.contracts import BatchScanResult, ExportJobResult, FolderScanResult, ImageFileInfo, PreviewResult
from flatshot.core.scaling import DEFAULT_SCALE_CURVE, normalize_curve_data
from tests.helpers import InlineExecutor


def _png(path: Path) -> Path:
    Image.new("RGBA", (4, 4), (255, 0, 0, 255)).save(path)
    return path


def _service(config_dir: Path) -> FlatShotBridgeService:
    return FlatShotBridgeService(config_resolver=ConfigPathResolver(config_dir))


def _export_runner_factory(**kwargs) -> ExportRunner:
    return ExportRunner(**kwargs, executor_factory=InlineExecutor)


def _failing_export_runner_factory(**kwargs) -> ExportRunner:
    def fail_image(args):
        image_path = Path(args[0])
        return False, f"{image_path.name}: fallo controlado", None

    return ExportRunner(**kwargs, executor_factory=InlineExecutor, image_processor=fail_image)


def _false_result_export_runner_factory(**kwargs):
    class FalseResultRunner:
        def run(self, request):
            return ExportJobResult(
                success=False,
                processed=0,
                total=len(request.input_files or []),
                errors=0,
                duration=0.0,
                destinations=[],
            )

    return FalseResultRunner()


def _export_service(config_dir: Path) -> FlatShotBridgeService:
    return FlatShotBridgeService(
        config_resolver=ConfigPathResolver(config_dir),
        export_runner_factory=_export_runner_factory,
    )


def _allow_roots(service: FlatShotBridgeService, *paths: Path) -> FlatShotBridgeService:
    for path in paths:
        service.path_policy.register_root(path)
    return service


def _wait_for_export(service: FlatShotBridgeService, job_id: str) -> dict:
    for _ in range(50):
        status = service.export_status(job_id)
        if status["status"] in {"completed", "partial", "failed", "cancelled"}:
            return status
        sleep(0.02)
    raise AssertionError("export job did not finish")


def _wait_for_scan_job(service: FlatShotBridgeService, job_id: str) -> dict:
    for _ in range(100):
        status = service.scan_job_status(job_id)
        if status["status"] in {"completed", "cancelled", "failed"}:
            return status
        sleep(0.02)
    raise AssertionError("scan job did not finish")


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
        "presetsWrite": True,
        "previewRender": True,
        "previewRenderBinary": True,
        "thumbnailRender": True,
        "exportRun": True,
        "exportProgress": True,
        "nativeFolderPicker": False,
    }


def test_bridge_presets_return_defaults_without_creating_config_dir(tmp_path):
    config_dir = tmp_path / "missing-config"
    service = _service(config_dir)

    response = service.list_presets()

    assert response["source"] == "defaults"
    assert [item["name"] for item in response["items"]] == ["Luz cenital", "Estándar oscuro"]
    first_settings = response["items"][0]["settings"]
    assert first_settings["opacity"] == 20
    assert first_settings["blur"] == 30
    assert first_settings["distance"] == 25
    assert first_settings["padding"] == 10
    assert first_settings["shadow_engine"] == "realistic_v2"
    assert not config_dir.exists()


def test_bridge_presets_read_existing_categorized_config(tmp_path):
    preset_service = PresetService(tmp_path)
    categorized = preset_service.get_default_categorized_presets()
    categorized.categories["custom"].presets["Local"] = {"angle": 90, "distance": 10}
    preset_service.save_all_presets(categorized)

    response = _service(tmp_path).list_presets()

    assert response["source"] == "config"
    assert "Local" in {item["name"] for item in response["items"]}
    local = next(item for item in response["items"] if item["name"] == "Local")
    assert local["settings"]["angle"] == 90
    assert local["settings"]["distance"] == 10
    assert local["settings"]["shadow_engine"] == "legacy"


def test_bridge_save_preset_creates_persisted_config(tmp_path):
    config_dir = tmp_path / "config"
    service = _service(config_dir)

    response = service.save_preset(
        {
            "name": "Luz cenital",
            "settings": {"opacity": 35, "blur": 12, "distance": 8, "shadow_engine": "realistic_v2"},
        }
    )

    assert response["ok"] is True
    assert response["source"] == "config"
    saved = next(item for item in response["items"] if item["name"] == "Luz cenital")
    assert saved["settings"]["opacity"] == 35
    assert saved["settings"]["blur"] == 12
    assert (config_dir / PresetService.CATEGORIZED_PRESETS_FILE).exists()


def test_bridge_save_preset_rejects_extreme_numeric_settings(tmp_path):
    service = _service(tmp_path / "config")

    with pytest.raises(InvalidRequestError, match="blur"):
        service.save_preset(
            {
                "name": "Bad",
                "settings": {"blur": 10000, "opacity": 20, "shadow_engine": "realistic_v2"},
            }
        )


def test_bridge_ui_preferences_persist_between_service_instances(tmp_path):
    config_dir = tmp_path / "config"
    preferences = {
        "outputProfiles": [
            {
                "id": "jpg_rgb230",
                "name": "JPG gris claro",
                "enabled": True,
                "format": "JPG",
                "width": 1800,
                "height": 2400,
                "background": "rgb230",
                "destinationMode": "source",
                "destinationValue": "Salida",
                "naming": "{original}{suffix}",
                "suffix": "_WEB",
            }
        ],
        "activeOutputProfile": "jpg_rgb230",
        "activeOutputFormats": ["jpg_rgb230"],
        "exportPreferences": {"format": "JPG", "size": "1800x2400", "background": "rgb230"},
    }

    saved = _service(config_dir).save_ui_preferences(preferences)
    loaded = _service(config_dir).load_ui_preferences()

    assert saved["ok"] is True
    assert loaded["source"] == "config"
    assert loaded["preferences"] == preferences


def test_bridge_delete_preset_persists_remaining_presets(tmp_path):
    preset_service = PresetService(tmp_path)
    categorized = preset_service.get_default_categorized_presets()
    categorized.categories["custom"].presets["Local"] = {"angle": 90, "distance": 10}
    preset_service.save_all_presets(categorized)

    response = _service(tmp_path).delete_preset({"name": "Local"})

    assert response["ok"] is True
    assert response["source"] == "config"
    assert "Local" not in {item["name"] for item in response["items"]}
    assert response["activePreset"] == "Luz cenital"


def test_bridge_render_preview_accepts_preset_settings_from_presets(tmp_path):
    image = _png(tmp_path / "source.png")
    preset_payload = _service(tmp_path / "missing-config").list_presets()
    settings = preset_payload["items"][1]["settings"]
    service = _allow_roots(_service(tmp_path / "config"), image.parent)

    response = service.render_preview(
        {
            "imagePath": str(image),
            "targetWidth": 32,
            "targetHeight": 32,
            "settings": settings,
        }
    )

    assert response["ok"] is True
    assert response["image"]["width"] == 32
    assert response["image"]["height"] == 32


def test_bridge_render_preview_applies_local_override(tmp_path):
    image = _png(tmp_path / "source.png")
    captured = {}

    class CapturingPreviewService:
        def render_preview(self, request):
            captured["settings"] = request.settings
            return PreviewResult(width=1, height=1, bytes_rgb=b"\x00\x00\x00")

    service = FlatShotBridgeService(
        config_resolver=ConfigPathResolver(tmp_path / "config"),
        preview_service=CapturingPreviewService(),
    )
    _allow_roots(service, image.parent)

    response = service.render_preview(
        {
            "imagePath": str(image),
            "targetWidth": 1,
            "targetHeight": 1,
            "settings": {"opacity": 20, "blur": 30, "scale_adjustment": 0},
            "localOverride": {"size_delta": 5, "shadow_delta": -10, "blur_delta": 8},
        }
    )

    assert response["ok"] is True
    assert captured["settings"].scale_adjustment == 5
    assert captured["settings"].opacity == 10
    assert captured["settings"].blur == 38


def test_bridge_render_preview_uses_render_configuration(tmp_path):
    image = _png(tmp_path / "source.png")
    captured = {}

    class CapturingPreviewService:
        def render_preview(self, request):
            captured["request"] = request
            return PreviewResult(width=1, height=1, bytes_rgb=b"\x00\x00\x00")

    service = FlatShotBridgeService(
        config_resolver=ConfigPathResolver(tmp_path / "config"),
        preview_service=CapturingPreviewService(),
    )
    _allow_roots(service, image.parent)

    response = service.render_preview(
        {
            "imagePath": str(image),
            "targetWidth": 1,
            "targetHeight": 1,
            "settings": {"opacity": 20, "blur": 30, "noise": 0},
            "localOverride": {"shadow_delta": -5},
            "curveData": {"xp": [0.0, 1.0], "fp": [0.9, 1.1], "base_fill": 0.55},
        }
    )

    request = captured["request"]
    assert response["ok"] is True
    assert request.render_config is not None
    assert request.render_config.settings == request.settings
    assert request.render_config.settings.opacity == 15
    assert request.render_config.curve_data == normalize_curve_data(
        {"xp": [0.0, 1.0], "fp": [0.9, 1.1], "base_fill": 0.55}
    )


def test_bridge_render_preview_accepts_lighting_scene_alias(tmp_path):
    image = _png(tmp_path / "source.png")
    captured = {}

    class CapturingPreviewService:
        def render_preview(self, request):
            captured["settings"] = request.settings
            return PreviewResult(width=1, height=1, bytes_rgb=b"\x00\x00\x00")

    service = FlatShotBridgeService(
        config_resolver=ConfigPathResolver(tmp_path / "config"),
        preview_service=CapturingPreviewService(),
    )
    _allow_roots(service, image.parent)

    response = service.render_preview(
        {
            "imagePath": str(image),
            "targetWidth": 1,
            "targetHeight": 1,
            "settings": {
                "shadowEngine": "studio_2_5d",
                "lightingScene": {
                    "main": {
                        "type": "strip",
                        "x": 0.45,
                        "y": -0.7,
                        "height": 0.4,
                        "size": 0.35,
                        "intensity": 1.1,
                    },
                    "ambient_intensity": 0.2,
                },
            },
        }
    )

    assert response["ok"] is True
    assert captured["settings"].shadow_engine == "studio_2_5d"
    assert captured["settings"].lighting_scene.main.type == "strip"
    assert captured["settings"].lighting_scene.main.x == 0.45
    assert captured["settings"].lighting_scene.ambient_intensity == 0.2


def test_bridge_render_preview_passes_curve_data(tmp_path):
    image = _png(tmp_path / "source.png")
    captured = {}

    class CapturingPreviewService:
        def render_preview(self, request):
            captured["curve_data"] = request.curve_data
            return PreviewResult(width=1, height=1, bytes_rgb=b"\x00\x00\x00")

    service = FlatShotBridgeService(
        config_resolver=ConfigPathResolver(tmp_path / "config"),
        preview_service=CapturingPreviewService(),
    )
    _allow_roots(service, image.parent)

    response = service.render_preview(
        {
            "imagePath": str(image),
            "targetWidth": 1,
            "targetHeight": 1,
            "curveData": {"xp": [0.0, 1.0], "fp": [0.9, 1.1]},
        }
    )

    assert response["ok"] is True
    assert captured["curve_data"].xp == [0.0, 1.0, 3.0]
    assert captured["curve_data"].fp == [0.9, 1.1, 1.1]


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
    assert response["totalFiles"] == 0
    assert response["totalImages"] == 0
    assert response["totalOmitted"] == 0
    assert response["adjustedImages"] == 0
    assert response["folders"][0]["exists"] is True
    assert response["folders"][0]["isDir"] is True
    assert response["folders"][0]["images"] == []
    assert response["folders"][0]["omitted"] == []
    assert response["errors"] == []


def test_bridge_scan_folder_with_png(tmp_path):
    png = _png(tmp_path / "b.png")
    _png(tmp_path / "a.png")
    (tmp_path / "notes.txt").write_text("ignore", encoding="utf-8")

    response = _service(tmp_path / "config").scan_folders({"folders": [str(tmp_path)]})

    assert response["totalFolders"] == 1
    assert response["totalFiles"] == 3
    assert response["totalImages"] == 2
    assert response["totalOmitted"] == 1
    assert response["omittedByReason"] == {"unsupported_extension": 1}
    assert response["omittedByCategory"] == {"ignored": 1}
    assert [image["name"] for image in response["folders"][0]["images"]] == ["a.png", "b.png"]
    assert response["folders"][0]["images"][1]["path"] == png.as_posix()
    assert response["folders"][0]["images"][1]["sizeBytes"] > 0
    assert response["folders"][0]["omitted"][0]["name"] == "notes.txt"
    assert response["folders"][0]["omitted"][0]["severity"] == "ignored"


def test_bridge_scan_reports_omitted_items(tmp_path):
    nested = tmp_path / "nested"
    nested.mkdir()
    _png(nested / "inside.png")
    (tmp_path / "broken.png").write_bytes(b"broken")
    (tmp_path / "photo.jpg").write_bytes(b"not supported")

    response = _service(tmp_path / "config").scan_folders({"folders": [str(tmp_path)]})

    assert response["totalFiles"] == 2
    assert response["totalImages"] == 0
    assert response["totalOmitted"] == 3
    assert response["omittedByReason"] == {
        "read_error": 1,
        "subfolder_not_scanned": 1,
        "unsupported_extension": 1,
    }
    assert response["omittedByCategory"] == {
        "ignored": 2,
        "warning": 1,
    }
    reasons = {item["name"]: item["reason"] for item in response["folders"][0]["omitted"]}
    assert reasons == {
        "broken.png": "read_error",
        "nested": "subfolder_not_scanned",
        "photo.jpg": "unsupported_extension",
    }
    severities = {item["name"]: item["severity"] for item in response["folders"][0]["omitted"]}
    assert severities == {
        "broken.png": "warning",
        "nested": "ignored",
        "photo.jpg": "ignored",
    }


def test_bridge_scan_job_status_paginates_result_images(tmp_path):
    class StaticScanner:
        def scan_folders(self, folders, image_overrides=None, **kwargs):
            images = [
                ImageFileInfo(
                    path=folders[0] / f"item-{index}.png",
                    name=f"item-{index}.png",
                    stem=f"item-{index}",
                    suffix=".png",
                    size_bytes=10 + index,
                )
                for index in range(5)
            ]
            return BatchScanResult(
                folders=[
                    FolderScanResult(
                        folder=folders[0],
                        exists=True,
                        is_dir=True,
                        images=images,
                        files_found=len(images),
                    )
                ],
                total_folders=1,
                total_images=len(images),
                total_files=len(images),
            )

    source = tmp_path / "source"
    source.mkdir()
    service = FlatShotBridgeService(
        config_resolver=ConfigPathResolver(tmp_path / "config"),
        folder_scanner=StaticScanner(),
    )

    started = service.start_scan_job({"folders": [str(source)]})
    _wait_for_scan_job(service, started["jobId"])
    paged = service.scan_job_status(started["jobId"], image_offset=1, image_limit=2)

    assert paged["result"]["totalImages"] == 5
    assert paged["result"]["page"] == {
        "imageOffset": 1,
        "imageLimit": 2,
        "imageCount": 2,
        "totalImages": 5,
        "hasMore": True,
    }
    assert paged["result"]["folders"][0]["validImages"] == 5
    assert [image["name"] for image in paged["result"]["folders"][0]["images"]] == [
        "item-1.png",
        "item-2.png",
    ]


def test_bridge_scan_recursive_includes_nested_images(tmp_path):
    root = _png(tmp_path / "root.png")
    nested = tmp_path / "nested"
    nested.mkdir()
    nested_png = _png(nested / "inside.png")

    response = _service(tmp_path / "config").scan_folders({"folders": [str(tmp_path)], "recursive": True})

    assert response["totalImages"] == 2
    assert response["totalOmitted"] == 0
    assert response["omittedByReason"] == {}
    assert [image["path"] for image in response["folders"][0]["images"]] == [
        serialize_path(nested_png),
        serialize_path(root),
    ]


def test_bridge_scan_registers_image_ids_for_thumbnail_and_export(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    png = _png(source / "item.png")
    service = _export_service(tmp_path / "config")

    response = service.scan_folders({"folders": [str(source)]})
    image_id = response["folders"][0]["images"][0]["imageId"]

    assert image_id
    assert response["folders"][0]["images"][0]["path"] == serialize_path(png)
    mime_type, payload = service.render_thumbnail({"imageId": image_id, "size": 24})
    assert mime_type == "image/png"
    assert payload.startswith(b"\x89PNG")

    plan = service.prepare_export(
        {
            "imageIds": [image_id],
            "settings": {"opacity": 0, "blur": 0, "noise": 0},
            "export": {"format": "PNG", "size": "8x8", "destinationValue": "_OUT"},
        }
    )
    assert plan["sourceImages"] == 1


def test_bridge_export_accepts_registered_image_ids_with_empty_paths_array(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    _png(source / "item.png")
    service = _export_service(tmp_path / "config")

    response = service.scan_folders({"folders": [str(source)]})
    image_id = response["folders"][0]["images"][0]["imageId"]
    payload = {
        "imageIds": [image_id],
        "imagePaths": [],
        "settings": {"opacity": 0, "blur": 0, "noise": 0},
        "export": {"format": "PNG", "size": "8x8", "destinationValue": "_OUT"},
    }

    plan = service.prepare_export(payload)
    started = service.start_export(payload)
    final = _wait_for_export(service, started["jobId"])

    assert plan["sourceImages"] == 1
    assert final["status"] == "completed"
    assert (source / "_OUT" / "item_PRO.png").exists()


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


def test_bridge_pick_folder_returns_selected_path(tmp_path):
    selected = tmp_path / "selected"
    selected.mkdir()
    service = FlatShotBridgeService(
        config_resolver=ConfigPathResolver(tmp_path / "config"),
        folder_picker=lambda initial_path: selected,
    )

    response = service.pick_folder({"initialPath": str(tmp_path)})

    assert response == {"ok": True, "selected": True, "path": selected.as_posix()}


def test_bridge_pick_folder_handles_cancel(tmp_path):
    service = FlatShotBridgeService(
        config_resolver=ConfigPathResolver(tmp_path / "config"),
        folder_picker=lambda initial_path: None,
    )

    response = service.pick_folder({})

    assert response == {"ok": True, "selected": False, "path": None}


def test_bridge_pick_folder_rejects_invalid_initial_path(tmp_path):
    with pytest.raises(InvalidRequestError):
        _service(tmp_path / "config").pick_folder({"initialPath": 123})


def test_bridge_restricts_preview_paths_after_folder_scan(tmp_path):
    allowed = tmp_path / "allowed"
    outside = tmp_path / "outside"
    allowed.mkdir()
    outside.mkdir()
    allowed_png = _png(allowed / "allowed.png")
    outside_png = _png(outside / "outside.png")
    service = _service(tmp_path / "config")

    service.scan_folders({"folders": [str(allowed)]})

    mime_type, payload = service.render_thumbnail({"imagePath": str(allowed_png), "size": 24})
    assert mime_type == "image/png"
    assert payload.startswith(b"\x89PNG")
    with pytest.raises(BridgeError) as exc_info:
        service.render_thumbnail({"imagePath": str(outside_png), "size": 24})

    assert exc_info.value.code == "path_not_allowed"
    assert exc_info.value.status == 403


def test_bridge_rejects_preview_thumbnail_and_export_before_folder_scan(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    png = _png(source / "item.png")
    service = _export_service(tmp_path / "config")

    with pytest.raises(BridgeError) as preview_exc:
        service.render_preview({"imagePath": str(png), "targetWidth": 16, "targetHeight": 16})
    with pytest.raises(BridgeError) as thumbnail_exc:
        service.render_thumbnail({"imagePath": str(png), "size": 16})
    with pytest.raises(BridgeError) as export_exc:
        service.prepare_export(
            {
                "imagePaths": [str(png)],
                "settings": {"opacity": 0, "blur": 0, "noise": 0},
                "export": {"format": "PNG", "size": "8x8", "destinationValue": "_OUT"},
            }
        )

    assert preview_exc.value.code == "path_not_allowed"
    assert thumbnail_exc.value.code == "path_not_allowed"
    assert export_exc.value.code == "path_not_allowed"


def test_bridge_restricts_export_paths_after_folder_scan(tmp_path):
    allowed = tmp_path / "allowed"
    outside = tmp_path / "outside"
    allowed.mkdir()
    outside.mkdir()
    _png(allowed / "allowed.png")
    outside_png = _png(outside / "outside.png")
    service = _export_service(tmp_path / "config")

    service.scan_folders({"folders": [str(allowed)]})

    with pytest.raises(BridgeError) as exc_info:
        service.prepare_export(
            {
                "imagePaths": [str(outside_png)],
                "settings": {"opacity": 0, "blur": 0, "noise": 0},
                "export": {"format": "PNG", "size": "8x8", "destinationValue": "_OUT"},
            }
        )

    assert exc_info.value.code == "path_not_allowed"
    assert exc_info.value.status == 403


def test_bridge_export_rejects_subfolder_that_escapes_source_root(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    png = _png(source / "item.png")
    service = _allow_roots(_export_service(tmp_path / "config"), source)
    service.scan_folders({"folders": [str(source)]})

    with pytest.raises(InvalidRequestError) as exc_info:
        service.prepare_export(
            {
                "imagePaths": [str(png)],
                "settings": {"opacity": 0, "blur": 0, "noise": 0},
                "export": {"format": "PNG", "size": "8x8", "destinationValue": "../escape"},
            }
        )

    assert "subcarpeta" in str(exc_info.value).lower()


def test_bridge_export_rejects_custom_destination_outside_registered_roots(tmp_path):
    source = tmp_path / "source"
    outside = tmp_path / "outside"
    source.mkdir()
    outside.mkdir()
    png = _png(source / "item.png")
    service = _export_service(tmp_path / "config")
    service.scan_folders({"folders": [str(source)]})

    with pytest.raises(BridgeError) as exc_info:
        service.prepare_export(
            {
                "imagePaths": [str(png)],
                "settings": {"opacity": 0, "blur": 0, "noise": 0},
                "export": {
                    "format": "PNG",
                    "size": "8x8",
                    "destinationMode": "custom",
                    "customOutputPath": str(outside),
                    "namingTemplate": "{original}{suffix}",
                },
            }
        )

    assert exc_info.value.code == "path_not_allowed"
    assert exc_info.value.status == 403


def test_bridge_open_onboarding_assets_folder_uses_frontend_assets_dir(tmp_path):
    opened: list[Path] = []
    service = FlatShotBridgeService(
        config_resolver=ConfigPathResolver(tmp_path / "config"),
        folder_opener=lambda path: opened.append(path),
    )

    response = service.open_onboarding_assets_folder()

    assets_dir = Path(response["path"])
    assert response["ok"] is True
    assert assets_dir.name == "onboarding"
    assert (assets_dir / "flatshot-abstract-01.png").exists()
    assert opened == [assets_dir]


def test_bridge_open_folder_uses_trusted_output_path(tmp_path):
    source = tmp_path / "source"
    output = source / "Salida"
    output.mkdir(parents=True)
    opened: list[Path] = []
    service = _allow_roots(
        FlatShotBridgeService(
            config_resolver=ConfigPathResolver(tmp_path / "config"),
            folder_opener=lambda path: opened.append(path),
        ),
        source,
    )

    response = service.open_folder({"path": str(output)})

    assert response == {"ok": True, "path": serialize_path(output)}
    assert opened == [output]


def test_bridge_open_folder_rejects_untrusted_path(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    service = _allow_roots(_service(tmp_path / "config"), source)

    with pytest.raises(BridgeError) as exc_info:
        service.open_folder({"path": str(outside)})

    assert exc_info.value.code == "path_not_allowed"


def test_bridge_reveal_output_path_uses_trusted_output_path(tmp_path):
    source = tmp_path / "source"
    output = source / "Salida"
    output.mkdir(parents=True)
    exported = output / "item_PRO.png"
    exported.write_bytes(b"export")
    revealed = []
    service = _allow_roots(
        FlatShotBridgeService(
            config_resolver=ConfigPathResolver(tmp_path / "config"),
            path_revealer=lambda path: revealed.append(path),
        ),
        source,
    )

    response = service.reveal_path({"path": str(exported)})

    assert response == {"ok": True, "path": serialize_path(exported)}
    assert revealed == [exported]


def test_reveal_path_with_system_uses_windows_select_command_with_quoted_path(tmp_path, monkeypatch):
    exported = tmp_path / "OneDrive - Live Española S.A" / "Salida" / "Capa 1.png"
    exported.parent.mkdir(parents=True)
    exported.write_bytes(b"export")
    calls = []

    monkeypatch.setattr(onboarding_assets.sys, "platform", "win32")
    monkeypatch.setattr(onboarding_assets.subprocess, "Popen", lambda command: calls.append(command))

    onboarding_assets.reveal_path_with_system(exported)

    assert calls == [f'explorer.exe /select,"{exported.resolve()}"']


def test_bridge_render_preview_returns_png_payload(tmp_path):
    image = _png(tmp_path / "source.png")
    service = _allow_roots(_service(tmp_path / "config"), image.parent)

    response = service.render_preview(
        {
            "imagePath": str(image),
            "targetWidth": 32,
            "targetHeight": 32,
            "settings": {"opacity": 0, "blur": 0, "noise": 0, "bgColor": [230, 230, 230]},
        }
    )

    assert response["ok"] is True
    assert response["image"]["mimeType"] == "image/png"
    assert response["image"]["width"] == 32
    assert response["image"]["height"] == 32
    assert response["source"]["name"] == "source.png"
    assert response["renderTimeMs"] >= 0
    assert base64.b64decode(response["image"]["dataBase64"]).startswith(b"\x89PNG")


def test_bridge_render_thumbnail_returns_png_bytes(tmp_path):
    image = _png(tmp_path / "source.png")
    service = _allow_roots(_service(tmp_path / "config"), image.parent)

    mime_type, payload = service.render_thumbnail({"imagePath": str(image), "size": 24})

    assert mime_type == "image/png"
    assert payload.startswith(b"\x89PNG")
    with Image.open(BytesIO(payload)) as opened:
        assert opened.width <= 24
        assert opened.height <= 24


def test_bridge_render_thumbnail_uses_persistent_cache(tmp_path, monkeypatch):
    image = _png(tmp_path / "source.png")
    service = _allow_roots(_service(tmp_path / "config"), image.parent)
    from flatshot.bridge import preview_endpoints

    original_open = preview_endpoints.Image.open
    open_count = 0

    def counting_open(path, *args, **kwargs):
        nonlocal open_count
        if Path(path) == image:
            open_count += 1
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(preview_endpoints.Image, "open", counting_open)

    first_mime, first_payload = service.render_thumbnail({"imagePath": str(image), "size": 24})
    second_mime, second_payload = service.render_thumbnail({"imagePath": str(image), "size": 24})

    assert first_mime == second_mime == "image/png"
    assert first_payload == second_payload
    assert open_count == 1
    assert any((tmp_path / "config" / "thumbnail-cache").glob("*.png"))


def test_bridge_render_preview_clamps_target_size(tmp_path):
    image = _png(tmp_path / "source.png")
    service = _allow_roots(_service(tmp_path / "config"), image.parent)

    response = service.render_preview(
        {"imagePath": str(image), "targetWidth": 5000, "targetHeight": 5000}
    )

    assert response["image"]["width"] == 1200
    assert response["image"]["height"] == 1200


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"imagePath": ""},
        {"imagePath": 123},
        {"imagePath": "missing.png"},
        {"imagePath": None},
        {"imagePath": "item.png", "settings": []},
        {"imagePath": "item.png", "targetWidth": 0},
        {"imagePath": "item.png", "targetHeight": "no"},
    ],
)
def test_bridge_render_preview_rejects_invalid_input(payload, tmp_path):
    service = _service(tmp_path / "config")
    if payload.get("imagePath") == "item.png":
        payload = dict(payload, imagePath=str(_png(tmp_path / "item.png")))
        _allow_roots(service, tmp_path)

    with pytest.raises(Exception) as exc_info:
        service.render_preview(payload)

    message = str(exc_info.value)
    assert "Traceback" not in message


def test_bridge_render_preview_rejects_unsupported_file(tmp_path):
    item = tmp_path / "item.txt"
    item.write_text("not an image", encoding="utf-8")

    with pytest.raises(Exception) as exc_info:
        _service(tmp_path / "config").render_preview({"imagePath": str(item)})

    assert "Formato de imagen no soportado" in str(exc_info.value)


def test_bridge_prepare_export_returns_real_plan(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    png = _png(source / "item.png")
    service = _allow_roots(_export_service(tmp_path / "config"), source)

    response = service.prepare_export(
        {
            "imagePaths": [str(png)],
            "settings": {"opacity": 0, "blur": 0, "noise": 0},
            "export": {
                "format": "PNG",
                "size": "8x8",
                "destinationMode": "source",
                "destinationValue": "_OUT",
                "namingTemplate": "{original}{suffix}",
            },
        }
    )

    assert response["ok"] is True
    assert response["sourceImages"] == 1
    assert response["totalOutputs"] == 1
    assert response["destinations"] == [(source / "_OUT").as_posix()]
    assert response["activeVariants"][0]["label"] == "Web RGB230"


def test_bridge_prepare_export_rejects_insufficient_temp_space(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    png = source / "large.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n" + (b"0" * 1024 * 1024))
    service = _allow_roots(_export_service(tmp_path / "config"), source)

    monkeypatch.setattr(shutil, "disk_usage", lambda _path: shutil._ntuple_diskusage(10, 9, 1))

    with pytest.raises(BridgeError) as exc_info:
        service.prepare_export(
            {
                "imagePaths": [str(png)],
                "settings": {"opacity": 0, "blur": 0, "noise": 0},
                "export": {
                    "format": "PNG",
                    "size": "8x8",
                    "destinationMode": "source",
                    "destinationValue": "_OUT",
                    "namingTemplate": "{original}{suffix}",
                },
            }
        )

    assert exc_info.value.code == "export_insufficient_space"
    assert "espacio" in str(exc_info.value).lower()


def test_bridge_start_export_writes_output_and_reports_progress(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    png = _png(source / "item.png")
    service = _allow_roots(_export_service(tmp_path / "config"), source)

    started = service.start_export(
        {
            "imagePaths": [str(png)],
            "settings": {"opacity": 0, "blur": 0, "noise": 0},
            "export": {
                "format": "PNG",
                "size": "8x8",
                "destinationMode": "source",
                "destinationValue": "_OUT",
                "namingTemplate": "{original}{suffix}",
            },
        }
    )
    final = _wait_for_export(service, started["jobId"])

    assert final["status"] == "completed"
    assert final["progress"] == {"processed": 1, "total": 1, "percent": 100}
    assert final["result"]["success"] is True
    assert (source / "_OUT" / "item_PRO.png").exists()
    assert final["completedItems"][0]["outputPath"] == serialize_path(source / "_OUT" / "item_PRO.png")


def test_bridge_start_export_writes_manifest(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    png = _png(source / "item.png")
    config_dir = tmp_path / "config"
    service = _allow_roots(_export_service(config_dir), source)

    started = service.start_export(
        {
            "imagePaths": [str(png)],
            "settings": {"opacity": 0, "blur": 0, "noise": 0},
            "export": {"format": "PNG", "size": "8x8", "destinationValue": "_OUT"},
        }
    )
    final = _wait_for_export(service, started["jobId"])
    manifest_path = config_dir / "export-manifests" / f"{started['jobId']}.json"

    assert final["status"] == "completed"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["jobId"] == started["jobId"]
    assert manifest["status"] == "completed"
    assert manifest["sourceImages"] == [png.as_posix()]
    assert manifest["result"]["success"] is True


def test_bridge_start_export_uses_injected_job_repository(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    png = _png(source / "item.png")
    manifest_root = tmp_path / "job-cache"
    service = FlatShotBridgeService(
        config_resolver=ConfigPathResolver(tmp_path / "config"),
        export_job_repository=ExportJobRepository(manifest_root),
        export_runner_factory=_export_runner_factory,
    )
    _allow_roots(service, source)

    started = service.start_export(
        {
            "imagePaths": [str(png)],
            "settings": {"opacity": 0, "blur": 0, "noise": 0},
            "export": {"format": "PNG", "size": "8x8", "destinationValue": "_OUT"},
        }
    )
    final = _wait_for_export(service, started["jobId"])
    manifest_path = manifest_root / f"{started['jobId']}.json"

    assert final["status"] == "completed"
    assert manifest_path.exists()
    assert not (tmp_path / "config" / "export-manifests" / f"{started['jobId']}.json").exists()


def test_bridge_start_export_writes_multiple_format_variants(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    png = _png(source / "item.png")
    custom_output = tmp_path / "archive"
    custom_output.mkdir()
    service = _allow_roots(_export_service(tmp_path / "config"), source, custom_output)

    started = service.start_export(
        {
            "imagePaths": [str(png)],
            "settings": {"opacity": 0, "blur": 0, "noise": 0},
            "export": {
                "format": "JPG",
                "size": "12x12",
                "destinationMode": "source",
                "destinationValue": "_WEB",
                "namingTemplate": "{original}{suffix}",
                "suffix": "_WEB",
                "variants": [
                    {
                        "id": "web_jpg",
                        "label": "Web JPG",
                        "enabled": True,
                        "format": "JPG",
                        "transparent_bg": False,
                        "bg_color": [230, 230, 230],
                        "suffix": "_WEB",
                        "naming_template": "{original}{suffix}",
                        "output_destination": "subfolder",
                        "output_folder_name": "_WEB",
                        "output_width": 12,
                        "output_height": 12,
                    },
                    {
                        "id": "archive_png",
                        "label": "Archive PNG",
                        "enabled": True,
                        "format": "PNG",
                        "transparent_bg": True,
                        "bg_color": [230, 230, 230],
                        "suffix": "_ARCH",
                        "naming_template": "{original}{suffix}",
                        "output_destination": "custom",
                        "custom_output_path": str(custom_output),
                        "output_width": 8,
                        "output_height": 8,
                    },
                ],
            },
        }
    )
    final = _wait_for_export(service, started["jobId"])

    assert final["status"] == "completed"
    assert final["progress"] == {"processed": 2, "total": 2, "percent": 100}
    assert (source / "_WEB" / "item_WEB.jpg").exists()
    assert (custom_output / "item_ARCH.png").exists()


def test_bridge_export_rejects_same_filename_across_folders_with_common_destination(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    output = tmp_path / "out"
    first.mkdir()
    second.mkdir()
    output.mkdir()
    first_png = _png(first / "same.png")
    second_png = _png(second / "same.png")
    service = _allow_roots(_export_service(tmp_path / "config"), first, second, output)

    with pytest.raises(BridgeError) as exc_info:
        service.start_export(
            {
                "imagePaths": [str(first_png), str(second_png)],
                "settings": {"opacity": 0, "blur": 0, "noise": 0},
                "export": {
                    "format": "PNG",
                    "size": "8x8",
                    "destinationMode": "custom",
                    "customOutputPath": str(output),
                    "namingTemplate": "{original}{suffix}",
                },
            }
        )

    assert exc_info.value.code == "export_output_collision"
    assert "archivos de salida repetidos" in str(exc_info.value)
    assert list(output.iterdir()) == []


def test_bridge_export_rejects_template_collision_without_partial_outputs(tmp_path):
    source = tmp_path / "source"
    output = tmp_path / "out"
    source.mkdir()
    output.mkdir()
    first_png = _png(source / "first.png")
    second_png = _png(source / "second.png")
    service = _allow_roots(_export_service(tmp_path / "config"), source, output)

    with pytest.raises(BridgeError) as exc_info:
        service.start_export(
            {
                "imagePaths": [str(first_png), str(second_png)],
                "settings": {"opacity": 0, "blur": 0, "noise": 0},
                "export": {
                    "format": "PNG",
                    "size": "8x8",
                    "destinationMode": "custom",
                    "customOutputPath": str(output),
                    "namingTemplate": "flatshot{suffix}",
                },
            }
        )

    assert exc_info.value.code == "export_output_collision"
    assert list(output.iterdir()) == []


def test_bridge_export_rejects_output_name_that_escapes_destination(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    png = _png(source / "item.png")
    service = _allow_roots(_export_service(tmp_path / "config"), source)

    with pytest.raises(InvalidRequestError) as exc_info:
        service.start_export(
            {
                "imagePaths": [str(png)],
                "settings": {"opacity": 0, "blur": 0, "noise": 0},
                "export": {
                    "format": "PNG",
                    "size": "8x8",
                    "destinationMode": "source",
                    "destinationValue": "_OUT",
                    "namingTemplate": "../escape_{original}{suffix}",
                },
            }
        )

    assert "naming template" in str(exc_info.value)
    assert not (source / "escape_item_PRO.png").exists()


def test_bridge_export_rejects_existing_output_without_overwriting(tmp_path):
    source = tmp_path / "source"
    output = tmp_path / "out"
    source.mkdir()
    output.mkdir()
    png = _png(source / "item.png")
    existing = output / "item_PRO.png"
    existing.write_bytes(b"existing-output")
    service = _allow_roots(_export_service(tmp_path / "config"), source, output)

    with pytest.raises(BridgeError) as exc_info:
        service.start_export(
            {
                "imagePaths": [str(png)],
                "settings": {"opacity": 0, "blur": 0, "noise": 0},
                "export": {
                    "format": "PNG",
                    "size": "8x8",
                    "destinationMode": "custom",
                    "customOutputPath": str(output),
                    "namingTemplate": "{original}{suffix}",
                },
            }
        )

    assert exc_info.value.code == "export_output_collision"
    assert existing.read_bytes() == b"existing-output"


def test_bridge_export_allows_valid_common_destination_without_collisions(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    output = tmp_path / "out"
    first.mkdir()
    second.mkdir()
    output.mkdir()
    first_png = _png(first / "one.png")
    second_png = _png(second / "two.png")
    service = _allow_roots(_export_service(tmp_path / "config"), first, second, output)

    started = service.start_export(
        {
            "imagePaths": [str(first_png), str(second_png)],
            "settings": {"opacity": 0, "blur": 0, "noise": 0},
            "export": {
                "format": "PNG",
                "size": "8x8",
                "destinationMode": "custom",
                "customOutputPath": str(output),
                "namingTemplate": "{original}{suffix}",
            },
        }
    )
    final = _wait_for_export(service, started["jobId"])

    assert final["status"] == "completed"
    assert (output / "one_PRO.png").exists()
    assert (output / "two_PRO.png").exists()


def test_bridge_export_preserves_image_overrides(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    png = _png(source / "item.png")
    captured = []

    def capture_runner_factory(**kwargs):
        class CaptureRunner:
            def run(self, request):
                captured.append(request)
                return ExportJobResult(
                    success=True,
                    processed=len(request.input_files or []),
                    total=len(request.input_files or []),
                    errors=0,
                    duration=0.0,
                    destinations=[],
                )

        return CaptureRunner()

    service = FlatShotBridgeService(
        config_resolver=ConfigPathResolver(tmp_path / "config"),
        export_runner_factory=capture_runner_factory,
    )
    _allow_roots(service, source)

    started = service.start_export(
        {
            "imagePaths": [str(png)],
            "settings": {"opacity": 0, "blur": 0, "noise": 0},
            "imageOverrides": {str(png): {"size_delta": 6, "shadow_delta": 0}},
            "export": {"format": "PNG", "size": "8x8", "destinationValue": "_OUT"},
        }
    )
    final = _wait_for_export(service, started["jobId"])

    assert final["status"] == "completed"
    assert captured[0].image_overrides == {str(png): {"size_delta": 6}}


def test_bridge_export_uses_default_curve_data_when_missing(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    png = _png(source / "item.png")
    captured = []

    def capture_runner_factory(**kwargs):
        class CaptureRunner:
            def run(self, request):
                captured.append(request)
                return ExportJobResult(True, 1, 1, 0, 0.0, [])

        return CaptureRunner()

    service = FlatShotBridgeService(
        config_resolver=ConfigPathResolver(tmp_path / "config"),
        export_runner_factory=capture_runner_factory,
    )
    _allow_roots(service, source)

    started = service.start_export(
        {
            "imagePaths": [str(png)],
            "settings": {"opacity": 0, "blur": 0, "noise": 0},
            "export": {"format": "PNG", "size": "8x8", "destinationValue": "_OUT"},
        }
    )
    final = _wait_for_export(service, started["jobId"])

    assert final["status"] == "completed"
    assert captured[0].curve_data == normalize_curve_data(DEFAULT_SCALE_CURVE.copy())


def test_bridge_export_accepts_curve_data_payload(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    png = _png(source / "item.png")
    captured = []

    def capture_runner_factory(**kwargs):
        class CaptureRunner:
            def run(self, request):
                captured.append(request)
                return ExportJobResult(True, 1, 1, 0, 0.0, [])

        return CaptureRunner()

    service = FlatShotBridgeService(
        config_resolver=ConfigPathResolver(tmp_path / "config"),
        export_runner_factory=capture_runner_factory,
    )
    _allow_roots(service, source)

    started = service.start_export(
        {
            "imagePaths": [str(png)],
            "settings": {"opacity": 0, "blur": 0, "noise": 0},
            "curveData": {"xp": [0.0, 1.0], "fp": [0.85, 1.15], "base_fill": 0.5},
            "export": {"format": "PNG", "size": "8x8", "destinationValue": "_OUT"},
        }
    )
    final = _wait_for_export(service, started["jobId"])

    assert final["status"] == "completed"
    assert captured[0].curve_data.xp == [0.0, 1.0, 3.0]
    assert captured[0].curve_data.fp == [0.85, 1.15, 1.15]
    assert captured[0].curve_data.base_fill == 0.5


def test_bridge_start_export_reports_structured_item_errors(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    png = _png(source / "item.png")
    service = FlatShotBridgeService(
        config_resolver=ConfigPathResolver(tmp_path / "config"),
        export_runner_factory=_failing_export_runner_factory,
    )
    _allow_roots(service, source)

    started = service.start_export(
        {
            "imagePaths": [str(png)],
            "settings": {"opacity": 0, "blur": 0, "noise": 0},
            "export": {"format": "PNG", "size": "8x8", "destinationValue": "_OUT"},
        }
    )
    final = _wait_for_export(service, started["jobId"])

    assert final["status"] == "partial"
    assert final["progress"] == {"processed": 1, "total": 1, "percent": 100}
    assert final["issues"][0]["level"] == "error"
    assert final["issues"][0]["title"] == "item.png"
    assert "fallo controlado" in final["issues"][0]["detail"]
    assert final["completedItems"][0] == {
        "name": "item.png",
        "outputPath": serialize_path(source / "_OUT" / "item_PRO.png"),
        "path": png.as_posix(),
        "success": False,
    }


def test_bridge_start_export_marks_false_runner_result_as_failed(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    png = _png(source / "item.png")
    service = FlatShotBridgeService(
        config_resolver=ConfigPathResolver(tmp_path / "config"),
        export_runner_factory=_false_result_export_runner_factory,
    )
    _allow_roots(service, source)

    started = service.start_export(
        {
            "imagePaths": [str(png)],
            "settings": {"opacity": 0, "blur": 0, "noise": 0},
            "export": {"format": "PNG", "size": "8x8", "destinationValue": "_OUT"},
        }
    )
    final = _wait_for_export(service, started["jobId"])

    assert final["status"] == "failed"
    assert final["issues"][0]["title"] == "Exportación"


def test_bridge_start_export_keeps_zero_processed_result_at_zero(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    images = [_png(source / f"item-{index}.png") for index in range(3)]
    service = FlatShotBridgeService(
        config_resolver=ConfigPathResolver(tmp_path / "config"),
        export_runner_factory=_false_result_export_runner_factory,
    )
    _allow_roots(service, source)

    started = service.start_export(
        {
            "imagePaths": [str(path) for path in images],
            "settings": {"opacity": 0, "blur": 0, "noise": 0},
            "export": {"format": "PNG", "size": "8x8", "destinationValue": "_OUT"},
        }
    )
    final = _wait_for_export(service, started["jobId"])

    assert final["status"] == "failed"
    assert final["progress"]["processed"] == 0
    assert final["progress"]["total"] == 3
    assert final["result"]["processed"] == 0


def test_bridge_service_prunes_old_finished_export_jobs(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    images = [_png(source / f"item-{index}.png") for index in range(3)]
    service = _allow_roots(_export_service(tmp_path / "config"), source)
    service.max_retained_jobs = 2
    started_jobs = []

    for image in images:
        started = service.start_export(
            {
                "imagePaths": [str(image)],
                "settings": {"opacity": 0, "blur": 0, "noise": 0},
                "export": {"format": "PNG", "size": "8x8", "destinationValue": f"_OUT_{image.stem}"},
            }
        )
        started_jobs.append(started["jobId"])
        _wait_for_export(service, started["jobId"])

    assert len(service._jobs) <= 2
    assert started_jobs[0] not in service._jobs
    assert started_jobs[-1] in service._jobs


def test_bridge_start_export_reserves_concurrent_slot(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    image = _png(source / "item.png")
    started = threading.Event()
    release = threading.Event()

    class BlockingRunner:
        def run(self, request):
            started.set()
            release.wait(timeout=2)
            return ExportJobResult(False, 0, 1, 1, 0.0, [])

    def runner_factory(**_kwargs):
        return BlockingRunner()

    service = _allow_roots(
        FlatShotBridgeService(
            config_resolver=ConfigPathResolver(tmp_path / "config"),
            export_runner_factory=runner_factory,
            max_concurrent_exports=1,
        ),
        source,
    )
    payload = {
        "imagePaths": [str(image)],
        "settings": {"opacity": 0, "blur": 0, "noise": 0},
        "export": {"format": "PNG", "size": "8x8", "destinationValue": "_OUT"},
    }

    first = service.start_export(payload)
    assert started.wait(timeout=1)
    with pytest.raises(BridgeError, match="exportación en curso"):
        service.start_export(payload)

    release.set()
    assert _wait_for_export(service, first["jobId"])["status"] == "partial"


def test_bridge_start_export_reuses_job_for_same_idempotency_key(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    image = _png(source / "item.png")
    service = _allow_roots(_export_service(tmp_path / "config"), source)
    payload = {
        "imagePaths": [str(image)],
        "settings": {"opacity": 0, "blur": 0, "noise": 0},
        "export": {"format": "PNG", "size": "8x8", "destinationValue": "_OUT"},
    }

    first = service.start_export(payload, idempotency_key="attempt-1")
    final = _wait_for_export(service, first["jobId"])
    repeated = service.start_export(payload, idempotency_key="attempt-1")

    assert repeated["jobId"] == first["jobId"]
    assert repeated["status"] == final["status"]
    assert len(service._jobs) == 1


def test_bridge_start_scan_enforces_active_scan_limit(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    started = threading.Event()
    release = threading.Event()

    class BlockingScanner:
        def scan_folders(self, folders, image_overrides=None, cancellation_token=None, **_kwargs):
            started.set()
            while not release.is_set() and not cancellation_token.cancelled:
                sleep(0.01)
            return BatchScanResult(total_folders=1)

    service = _allow_roots(
        FlatShotBridgeService(
            config_resolver=ConfigPathResolver(tmp_path / "config"),
            folder_scanner=BlockingScanner(),
            max_concurrent_scans=1,
        ),
        source,
    )

    first = service.start_scan_job({"folders": [str(source)]})
    assert started.wait(timeout=1)
    with pytest.raises(BridgeError, match="escaneo en curso"):
        service.start_scan_job({"folders": [str(source)]})

    release.set()
    assert _wait_for_scan_job(service, first["jobId"])["status"] == "completed"


def test_bridge_shutdown_cancels_and_joins_active_scan_jobs(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    started = threading.Event()

    class BlockingScanner:
        def scan_folders(self, folders, image_overrides=None, cancellation_token=None, **_kwargs):
            started.set()
            while not cancellation_token.cancelled:
                sleep(0.01)
            return BatchScanResult(total_folders=1)

    service = _allow_roots(
        FlatShotBridgeService(
            config_resolver=ConfigPathResolver(tmp_path / "config"),
            folder_scanner=BlockingScanner(),
        ),
        source,
    )
    first = service.start_scan_job({"folders": [str(source)]})
    assert started.wait(timeout=1)

    assert service.shutdown(timeout=1)
    assert service.scan_job_status(first["jobId"])["status"] == "cancelled"


def test_bridge_export_job_keeps_internal_event_lists_bounded(tmp_path):
    job = BridgeExportJob(
        job_id="job",
        requests=[],
        source_images=0,
        total_outputs=200,
        destinations=[],
    )

    for index in range(260):
        job._handle_event(ExportLogEvent(f"Aviso: item-{index}: detalle"), 0)
        job._handle_event(ExportImageCompletedEvent(f"item-{index}.png", False, tmp_path / f"item-{index}.png"), 0)

    assert len(job.messages) <= 200
    assert len(job.issues) <= 200
    assert len(job.completed_items) <= 200
    assert job.messages[-1] == "Aviso: item-259: detalle"


def test_bridge_export_manifest_keeps_complete_event_history(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    job = BridgeExportJob(
        job_id="job",
        requests=[],
        source_images=0,
        total_outputs=260,
        destinations=[],
        manifest_path=manifest_path,
    )

    for index in range(260):
        job._handle_event(ExportLogEvent(f"Aviso: item-{index}: detalle"), 0)
        job._handle_event(ExportImageCompletedEvent(f"item-{index}.png", False, tmp_path / f"item-{index}.png"), 0)

    with job._lock:
        job.status = "partial"
        job.result = ExportJobResult(False, 260, 260, 260, 1.0, [])
        job._write_manifest_locked()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert len(job.completed_items) == 200
    assert len(manifest["completedItems"]) == 260
    assert len(manifest["issues"]) == 520


def test_bridge_export_snapshot_includes_complete_failed_items_for_retry(tmp_path):
    job = BridgeExportJob(
        job_id="job",
        requests=[],
        source_images=0,
        total_outputs=260,
        destinations=[],
    )

    for index in range(260):
        success = index % 10 != 0
        job._handle_event(ExportImageCompletedEvent(f"item-{index}.png", success, tmp_path / f"item-{index}.png"), 0)

    snapshot = job.snapshot()

    assert len(snapshot["completedItems"]) == 50
    assert snapshot["completedItems"][0]["name"] == "item-210.png"
    assert len(snapshot["failedItems"]) == 26
    assert snapshot["failedItems"][0] == {
        "name": "item-0.png",
        "success": False,
        "path": serialize_path(tmp_path / "item-0.png"),
    }
    assert snapshot["failedItems"][-1]["name"] == "item-250.png"


def test_bridge_export_rejects_invalid_input(tmp_path):
    with pytest.raises(InvalidRequestError):
        _export_service(tmp_path / "config").prepare_export({"imagePaths": []})


def test_bridge_export_rejects_custom_destination_without_path(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    png = _png(source / "item.png")
    service = _allow_roots(_export_service(tmp_path / "config"), source)

    with pytest.raises(InvalidRequestError) as exc_info:
        service.prepare_export(
            {
                "imagePaths": [str(png)],
                "export": {
                    "destinationMode": "custom",
                    "destinationValue": "",
                },
            }
        )

    assert "destino personalizado" in str(exc_info.value)


def test_bridge_export_rejects_extreme_numeric_settings_before_planning(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    png = _png(source / "item.png")
    service = _allow_roots(_export_service(tmp_path / "config"), source)

    with pytest.raises(InvalidRequestError, match="padding"):
        service.prepare_export(
            {
                "imagePaths": [str(png)],
                "settings": {"padding": 10000},
                "export": {"format": "PNG", "size": "8x8", "destinationValue": "_OUT"},
            }
        )


def test_bridge_export_unknown_job_returns_controlled_error(tmp_path):
    with pytest.raises(Exception) as exc_info:
        _export_service(tmp_path / "config").export_status("missing")

    assert "Exportación no encontrada" in str(exc_info.value)


def test_bridge_preview_code_does_not_import_pyqt():
    bridge_files = [
        Path("src/flatshot/bridge/service.py"),
        Path("src/flatshot/bridge/http_server.py"),
        Path("src/flatshot/bridge/serialization.py"),
    ]

    for path in bridge_files:
        source = path.read_text(encoding="utf-8")
        assert "PyQt6" not in source
        assert "QImage" not in source
        assert "QPixmap" not in source
