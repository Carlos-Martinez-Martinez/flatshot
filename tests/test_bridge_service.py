from pathlib import Path
import base64
from concurrent.futures import Future
from io import BytesIO
from time import sleep

import pytest
from PIL import Image

from flatshot.application.config_paths import ConfigPathResolver
from flatshot.application.export_runner import ExportRunner
from flatshot.application.preset_service import PresetService
from flatshot.bridge.errors import BridgeError, InvalidRequestError, error_response
from flatshot.bridge.serialization import image_file_info_to_dict
from flatshot.bridge.service import FlatShotBridgeService
from flatshot.application.contracts import ExportJobResult, ImageFileInfo, PreviewResult


def _png(path: Path) -> Path:
    Image.new("RGBA", (4, 4), (255, 0, 0, 255)).save(path)
    return path


def _service(config_dir: Path) -> FlatShotBridgeService:
    return FlatShotBridgeService(config_resolver=ConfigPathResolver(config_dir))


class InlineExecutor:
    def __init__(self, max_workers=1):
        self.max_workers = max_workers

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.shutdown()

    def submit(self, fn, arg):
        future = Future()
        try:
            future.set_result(fn(arg))
        except Exception as exc:
            future.set_exception(exc)
        return future

    def shutdown(self, wait=True, cancel_futures=False):
        return None


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


def _wait_for_export(service: FlatShotBridgeService, job_id: str) -> dict:
    for _ in range(50):
        status = service.export_status(job_id)
        if status["status"] in {"completed", "partial", "failed", "cancelled"}:
            return status
        sleep(0.02)
    raise AssertionError("export job did not finish")


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

    response = _service(tmp_path / "config").render_preview(
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


def test_bridge_render_preview_returns_png_payload(tmp_path):
    image = _png(tmp_path / "source.png")

    response = _service(tmp_path / "config").render_preview(
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

    mime_type, payload = _service(tmp_path / "config").render_thumbnail({"imagePath": str(image), "size": 24})

    assert mime_type == "image/png"
    assert payload.startswith(b"\x89PNG")
    with Image.open(BytesIO(payload)) as opened:
        assert opened.width <= 24
        assert opened.height <= 24


def test_bridge_render_preview_clamps_target_size(tmp_path):
    image = _png(tmp_path / "source.png")

    response = _service(tmp_path / "config").render_preview(
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
    if payload.get("imagePath") == "item.png":
        payload = dict(payload, imagePath=str(_png(tmp_path / "item.png")))

    with pytest.raises(Exception) as exc_info:
        _service(tmp_path / "config").render_preview(payload)

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
    service = _export_service(tmp_path / "config")

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


def test_bridge_start_export_writes_output_and_reports_progress(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    png = _png(source / "item.png")
    service = _export_service(tmp_path / "config")

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


def test_bridge_export_rejects_same_filename_across_folders_with_common_destination(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    output = tmp_path / "out"
    first.mkdir()
    second.mkdir()
    output.mkdir()
    first_png = _png(first / "same.png")
    second_png = _png(second / "same.png")
    service = _export_service(tmp_path / "config")

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
    service = _export_service(tmp_path / "config")

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


def test_bridge_export_rejects_existing_output_without_overwriting(tmp_path):
    source = tmp_path / "source"
    output = tmp_path / "out"
    source.mkdir()
    output.mkdir()
    png = _png(source / "item.png")
    existing = output / "item_PRO.png"
    existing.write_bytes(b"existing-output")
    service = _export_service(tmp_path / "config")

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
    first_png = _png(first / "one.png")
    second_png = _png(second / "two.png")
    service = _export_service(tmp_path / "config")

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


def test_bridge_start_export_reports_structured_item_errors(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    png = _png(source / "item.png")
    service = FlatShotBridgeService(
        config_resolver=ConfigPathResolver(tmp_path / "config"),
        export_runner_factory=_failing_export_runner_factory,
    )

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
    assert final["completedItems"][0] == {"name": "item.png", "success": False}


def test_bridge_start_export_marks_false_runner_result_as_failed(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    png = _png(source / "item.png")
    service = FlatShotBridgeService(
        config_resolver=ConfigPathResolver(tmp_path / "config"),
        export_runner_factory=_false_result_export_runner_factory,
    )

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


def test_bridge_export_rejects_invalid_input(tmp_path):
    with pytest.raises(InvalidRequestError):
        _export_service(tmp_path / "config").prepare_export({"imagePaths": []})


def test_bridge_export_rejects_custom_destination_without_path(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    png = _png(source / "item.png")

    with pytest.raises(InvalidRequestError) as exc_info:
        _export_service(tmp_path / "config").prepare_export(
            {
                "imagePaths": [str(png)],
                "export": {
                    "destinationMode": "custom",
                    "destinationValue": "",
                },
            }
        )

    assert "destino personalizado" in str(exc_info.value)


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
