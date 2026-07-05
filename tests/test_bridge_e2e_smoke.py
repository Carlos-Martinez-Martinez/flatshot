from __future__ import annotations

from pathlib import Path
from time import monotonic, sleep

from PIL import Image

from flatshot.application.config_paths import ConfigPathResolver
from flatshot.bridge.service import FlatShotBridgeService

EXPORT_E2E_TIMEOUT_SECONDS = 8.0


def _png(path: Path) -> Path:
    image = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    image.paste(Image.new("RGBA", (8, 8), (180, 60, 40, 255)), (4, 4))
    image.save(path)
    return path


def _wait_for_export(service: FlatShotBridgeService, job_id: str) -> dict:
    deadline = monotonic() + EXPORT_E2E_TIMEOUT_SECONDS
    last_status = None
    while monotonic() < deadline:
        status = service.export_status(job_id)
        last_status = status
        if status["status"] in {"completed", "partial", "failed", "cancelled"}:
            return status
        sleep(0.02)
    raise AssertionError(
        f"export job did not finish within {EXPORT_E2E_TIMEOUT_SECONDS:.1f}s; "
        f"last status: {last_status}"
    )


def test_bridge_e2e_scan_preview_prepare_run_status_completed(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    image_path = _png(source / "item.png")
    service = FlatShotBridgeService(config_resolver=ConfigPathResolver(tmp_path / "config"))

    scan = service.scan_folders({"folders": [str(source)], "scanMode": "verified"})
    scanned_image = scan["folders"][0]["images"][0]["path"]
    preview = service.render_preview(
        {
            "imagePath": scanned_image,
            "targetWidth": 32,
            "targetHeight": 32,
            "settings": {"opacity": 0, "blur": 0, "noise": 0},
        }
    )
    payload = {
        "imagePaths": [scanned_image],
        "settings": {"opacity": 0, "blur": 0, "noise": 0},
        "export": {
            "format": "PNG",
            "size": "8x8",
            "destinationMode": "source",
            "destinationValue": "_OUT",
            "namingTemplate": "{original}{suffix}",
        },
    }
    plan = service.prepare_export(payload)
    started = service.start_export(payload)
    final = _wait_for_export(service, started["jobId"])

    assert scan["totalImages"] == 1
    assert Path(scanned_image) == image_path
    assert preview["ok"] is True
    assert preview["image"]["width"] == 32
    assert preview["image"]["height"] == 32
    assert plan["sourceImages"] == 1
    assert plan["totalOutputs"] == 1
    assert final["status"] == "completed"
    assert final["progress"] == {"processed": 1, "total": 1, "percent": 100}
    assert (source / "_OUT" / "item_PRO.png").exists()
