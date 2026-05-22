"""JSON serialization helpers for bridge contracts."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from flatshot.application.contracts import BatchScanResult, FolderScanResult, ImageFileInfo


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


def folder_scan_result_to_dict(folder: FolderScanResult) -> dict[str, Any]:
    return {
        "path": serialize_path(folder.folder),
        "exists": folder.exists,
        "isDir": folder.is_dir,
        "images": [image_file_info_to_dict(image) for image in folder.images],
        "errors": list(folder.errors),
    }


def batch_scan_result_to_dict(result: BatchScanResult) -> dict[str, Any]:
    return {
        "folders": [folder_scan_result_to_dict(folder) for folder in result.folders],
        "totalFolders": result.total_folders,
        "totalImages": result.total_images,
        "adjustedImages": result.adjusted_images,
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
