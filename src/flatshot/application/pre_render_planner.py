"""Qt-free planning helpers for opportunistic export pre-rendering."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from flatshot.core.overrides import override_key
from flatshot.utils.render_cache import RenderCache


def build_pre_render_context_signature(
    *,
    folders: Iterable[Path],
    active_folder: Path | None,
    current_image_path: Path | None,
    settings_dict: dict,
    curve_dict: dict | None,
    target_size: tuple[int, int],
    export_format: str,
    image_overrides: dict[str, dict],
) -> str:
    data = {
        "folders": [str(path) for path in folders],
        "active_folder": str(active_folder) if active_folder else None,
        "current_image_path": str(current_image_path) if current_image_path else None,
        "settings": settings_dict,
        "curve": curve_dict,
        "target_size": target_size,
        "format": export_format,
        "overrides": image_overrides,
    }
    return json.dumps(data, sort_keys=True, default=str)


def ordered_pre_render_candidates(
    *,
    folders: Iterable[Path],
    active_folder: Path | None,
    current_image_path: Path | None,
) -> list[Path]:
    seen: set[str] = set()
    existing_folders = [folder for folder in folders if folder.exists()]
    paths_by_folder: dict[str, list[Path]] = {}
    all_paths: list[Path] = []

    for folder in existing_folders:
        try:
            images = sorted(path for path in folder.iterdir() if path.is_file() and path.suffix.lower() == ".png")
        except OSError:
            images = []
        paths_by_folder[str(folder.resolve())] = images
        all_paths.extend(images)

    ordered: list[Path] = []
    if current_image_path and current_image_path.exists():
        ordered.append(current_image_path)

    if active_folder and active_folder.exists():
        try:
            active_key = str(active_folder.resolve())
            ordered.extend(paths_by_folder.get(active_key, []))
        except OSError:
            pass

    ordered.extend(all_paths)

    deduped: list[Path] = []
    for path in ordered:
        try:
            key = str(path.resolve())
        except OSError:
            key = str(path)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(path)
    return deduped


def build_pre_render_jobs(
    *,
    candidates: Iterable[Path],
    cache: RenderCache,
    settings_dict: dict,
    curve_dict: dict | None,
    target_size: tuple[int, int],
    export_format: str,
    image_overrides: dict[str, dict],
) -> tuple[list[dict], int, int]:
    jobs: list[dict] = []
    prepared = 0
    total = 0

    for img_path in candidates:
        if not img_path.exists():
            continue
        local_override = image_overrides.get(override_key(str(img_path)), {})
        key = cache.get_cache_key(
            str(img_path),
            settings_dict,
            curve_dict,
            target_size,
            local_override,
            export_format,
        )
        total += 1
        if cache.exists(key, export_format):
            prepared += 1
            continue
        cache_path = cache.get_cached_path(key, export_format)
        jobs.append(
            {
                "key": key,
                "image_path": str(img_path),
                "settings_dict": settings_dict,
                "curve_dict": curve_dict,
                "target_size": target_size,
                "cache_path": str(cache_path),
                "local_override": local_override,
                "format": export_format,
            }
        )

    return jobs, prepared, total
