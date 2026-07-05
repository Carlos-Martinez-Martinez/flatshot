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


def image_file_info_to_dict(
    image: ImageFileInfo,
    *,
    image_id: str | None = None,
) -> dict[str, Any]:
    payload = {
        "path": serialize_path(image.path),
        "name": image.name,
        "stem": image.stem,
        "suffix": image.suffix,
        "sizeBytes": image.size_bytes,
        "hasLocalOverride": image.has_local_override,
    }
    if image_id:
        payload["imageId"] = image_id
    return payload


def omitted_scan_item_to_dict(item: OmittedScanItem) -> dict[str, Any]:
    return {
        "path": serialize_path(item.path),
        "name": item.name,
        "suffix": item.suffix,
        "reason": item.reason,
        "detail": item.detail,
        "category": item.category,
        "severity": item.severity,
    }


def folder_scan_result_to_dict(
    folder: FolderScanResult,
    *,
    images: list[ImageFileInfo] | None = None,
    image_id_for_path=None,
) -> dict[str, Any]:
    folder_images = folder.images if images is None else images
    return {
        "path": serialize_path(folder.folder),
        "exists": folder.exists,
        "isDir": folder.is_dir,
        "images": [
            image_file_info_to_dict(
                image,
                image_id=image_id_for_path(image.path) if image_id_for_path else None,
            )
            for image in folder_images
        ],
        "errors": list(folder.errors),
        "filesFound": folder.files_found,
        "validImages": len(folder.images),
        "omittedCount": len(folder.omitted),
        "omitted": [omitted_scan_item_to_dict(item) for item in folder.omitted],
    }


def batch_scan_result_to_dict(
    result: BatchScanResult,
    *,
    image_offset: int = 0,
    image_limit: int | None = None,
    image_id_for_path=None,
) -> dict[str, Any]:
    page_requested = image_limit is not None or image_offset > 0
    offset = max(0, int(image_offset))
    limit = None if image_limit is None else max(0, int(image_limit))
    total_images = sum(len(folder.images) for folder in result.folders)
    folders = [
        folder_scan_result_to_dict(
            folder,
            images=_folder_page_images(folder, offset, limit, cursor),
            image_id_for_path=image_id_for_path,
        )
        for folder, cursor in _folder_image_cursors(result.folders)
    ] if page_requested else [
        folder_scan_result_to_dict(folder, image_id_for_path=image_id_for_path)
        for folder in result.folders
    ]

    payload = {
        "folders": folders,
        "totalFolders": result.total_folders,
        "totalImages": result.total_images,
        "adjustedImages": result.adjusted_images,
        "totalFiles": result.total_files,
        "totalOmitted": result.total_omitted,
        "omittedByReason": dict(result.omitted_by_reason),
        "omittedByCategory": dict(result.omitted_by_category),
        "errors": list(result.errors),
    }
    if page_requested:
        returned = sum(len(folder["images"]) for folder in folders)
        payload["page"] = {
            "imageOffset": offset,
            "imageLimit": limit,
            "imageCount": returned,
            "totalImages": total_images,
            "hasMore": offset + returned < total_images,
        }
    return payload


def _folder_image_cursors(folders: list[FolderScanResult]) -> list[tuple[FolderScanResult, int]]:
    cursor = 0
    cursors = []
    for folder in folders:
        cursors.append((folder, cursor))
        cursor += len(folder.images)
    return cursors


def _folder_page_images(
    folder: FolderScanResult,
    image_offset: int,
    image_limit: int | None,
    cursor: int,
) -> list[ImageFileInfo]:
    if image_limit is None:
        start = max(0, image_offset - cursor)
        return list(folder.images[start:])

    end = image_offset + image_limit
    folder_start = cursor
    folder_end = cursor + len(folder.images)
    if end <= folder_start or image_offset >= folder_end:
        return []
    start = max(0, image_offset - folder_start)
    stop = min(len(folder.images), end - folder_start)
    return list(folder.images[start:stop])


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
