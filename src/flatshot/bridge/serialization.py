"""JSON serialization helpers for bridge contracts."""
from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image

from flatshot.application.contracts import (
    BatchScanResult,
    FolderScanResult,
    ImageFileInfo,
    OmittedScanItem,
    PreviewResult,
)


def serialize_path(path: str | Path) -> str:
    return Path(path).as_posix()


def image_file_info_to_dict(image: ImageFileInfo) -> dict[str, Any]:
    return {
        "path": serialize_path(image.path),
        "name": image.name,
        "stem": image.stem,
        "suffix": image.suffix,
        "sizeBytes": image.size_bytes,
        "hasLocalOverride": image.has_local_override,
    }


def omitted_scan_item_to_dict(item: OmittedScanItem) -> dict[str, Any]:
    return {
        "path": serialize_path(item.path),
        "name": item.name,
        "suffix": item.suffix,
        "reason": item.reason,
        "detail": item.detail,
    }


def folder_scan_result_to_dict(folder: FolderScanResult) -> dict[str, Any]:
    return {
        "path": serialize_path(folder.folder),
        "exists": folder.exists,
        "isDir": folder.is_dir,
        "images": [image_file_info_to_dict(image) for image in folder.images],
        "errors": list(folder.errors),
        "filesFound": folder.files_found,
        "validImages": len(folder.images),
        "omittedCount": len(folder.omitted),
        "omitted": [omitted_scan_item_to_dict(item) for item in folder.omitted],
    }


def batch_scan_result_to_dict(result: BatchScanResult) -> dict[str, Any]:
    return {
        "folders": [folder_scan_result_to_dict(folder) for folder in result.folders],
        "totalFolders": result.total_folders,
        "totalImages": result.total_images,
        "adjustedImages": result.adjusted_images,
        "totalFiles": result.total_files,
        "totalOmitted": result.total_omitted,
        "omittedByReason": dict(result.omitted_by_reason),
        "errors": list(result.errors),
    }


def categorized_presets_to_dict(categorized) -> dict[str, Any]:
    data = categorized.model_dump()
    items: list[dict[str, Any]] = []

    for category_id, category in data.get("categories", {}).items():
        for name, settings in (category.get("presets") or {}).items():
            items.append(
                {
                    "name": name,
                    "categoryId": category_id,
                    "category": category.get("name") or category_id,
                    "settings": settings,
                }
            )

    for name, settings in (data.get("uncategorized") or {}).items():
        items.append(
            {
                "name": name,
                "categoryId": "uncategorized",
                "category": "Sin categoría",
                "settings": settings,
            }
        )

    return {"items": items}


def preview_result_to_dict(
    result: PreviewResult,
    *,
    source_path: str | Path,
    render_time_ms: int,
) -> dict[str, Any]:
    image = Image.frombytes("RGB", (result.width, result.height), result.bytes_rgb)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    source = Path(source_path)

    return {
        "ok": True,
        "image": {
            "mimeType": "image/png",
            "dataBase64": encoded,
            "width": result.width,
            "height": result.height,
        },
        "source": {
            "path": serialize_path(source),
            "name": source.name,
        },
        "warning": result.warning,
        "renderTimeMs": render_time_ms,
    }
