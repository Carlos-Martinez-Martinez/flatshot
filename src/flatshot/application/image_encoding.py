"""Output image encoding helpers for export workers."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image


JPEG_SUBSAMPLING_PENALTY = {
    0: 0,
    1: 6,
    2: 10,
}


def save_export_image(
    image: Image.Image,
    save_path: Path,
    fmt: str,
    *,
    dpi: tuple[int, int] | tuple[float, float] | None,
    max_file_size_kb: int | None = None,
) -> str | None:
    normalized = str(fmt or "png").lower().lstrip(".")
    if normalized in {"jpg", "jpeg"}:
        rgb_image = image.convert("RGB")
        if max_file_size_kb:
            return _save_limited_jpeg(rgb_image, save_path, dpi=dpi, max_file_size_kb=max_file_size_kb)
        rgb_image.save(save_path, quality=100, subsampling=0, dpi=dpi)
        return None

    image.save(save_path, optimize=False, compress_level=0, dpi=dpi)
    return None


def _save_limited_jpeg(
    image: Image.Image,
    save_path: Path,
    *,
    dpi: tuple[int, int] | tuple[float, float] | None,
    max_file_size_kb: int,
) -> str | None:
    target_bytes = int(max_file_size_kb) * 1024
    candidates: list[tuple[int, int, bytes]] = []
    smallest: tuple[int, int, bytes] | None = None

    for subsampling in (0, 1, 2):
        low = 1
        high = 100
        best_for_subsampling: tuple[int, int, bytes] | None = None
        while low <= high:
            quality = (low + high) // 2
            payload = _jpeg_bytes(image, quality=quality, subsampling=subsampling, dpi=dpi)
            candidate = (quality, subsampling, payload)
            if smallest is None or len(payload) < len(smallest[2]):
                smallest = candidate
            if len(payload) <= target_bytes:
                best_for_subsampling = candidate
                low = quality + 1
            else:
                high = quality - 1
        if best_for_subsampling is not None:
            candidates.append(best_for_subsampling)

    if candidates:
        quality, subsampling, payload = max(candidates, key=_jpeg_candidate_score)
        save_path.write_bytes(payload)
        return None

    if smallest is None:
        return "No se pudo codificar el JPG."

    _quality, _subsampling, payload = smallest
    save_path.write_bytes(payload)
    final_kb = max(1, round(len(payload) / 1024))
    return f"No se pudo alcanzar {max_file_size_kb} KB; archivo final {final_kb} KB."


def _jpeg_candidate_score(candidate: tuple[int, int, bytes]) -> tuple[int, int]:
    quality, subsampling, _payload = candidate
    return quality - JPEG_SUBSAMPLING_PENALTY.get(subsampling, 10), -subsampling


def _jpeg_bytes(
    image: Image.Image,
    *,
    quality: int,
    subsampling: int,
    dpi: Any,
) -> bytes:
    buffer = BytesIO()
    image.save(
        buffer,
        format="JPEG",
        quality=quality,
        subsampling=subsampling,
        optimize=True,
        dpi=dpi,
    )
    return buffer.getvalue()
