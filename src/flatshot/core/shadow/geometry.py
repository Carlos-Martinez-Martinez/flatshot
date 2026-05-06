from __future__ import annotations

import math
import zlib
from dataclasses import dataclass
from typing import Tuple

import numpy as np
from PIL import Image


@dataclass(frozen=True)
class ShadowVector:
    x: float
    y: float


@dataclass(frozen=True)
class ShadowRoi:
    box: Tuple[int, int, int, int]
    local_mask: Image.Image
    origin: Tuple[int, int]


def shadow_vector_from_angle(angle: int | float) -> ShadowVector:
    """Angle is the direction where the shadow falls: 0 up, 90 right, 180 down."""
    radians = math.radians(float(angle))
    return ShadowVector(math.sin(radians), -math.cos(radians))


def compute_shadow_roi(
    mask_canvas: Image.Image,
    *,
    distance: float,
    max_blur: float,
    angle: int | float,
    canvas_size: Tuple[int, int],
) -> ShadowRoi:
    bbox = mask_canvas.getbbox()
    if not bbox:
        return ShadowRoi((0, 0, 0, 0), Image.new("L", (0, 0), 0), (0, 0))

    vector = shadow_vector_from_angle(angle)
    max_dx = int(math.ceil(abs(distance * vector.x)))
    max_dy = int(math.ceil(abs(distance * vector.y)))
    blur_pad = int(math.ceil(max(0.0, max_blur) * 3.5))
    safety = max(8, int(math.ceil(max(canvas_size) * 0.01)))
    base = blur_pad + safety

    left_pad = base + (max_dx if vector.x < 0 else 0)
    right_pad = base + (max_dx if vector.x > 0 else 0)
    top_pad = base + (max_dy if vector.y < 0 else 0)
    bottom_pad = base + (max_dy if vector.y > 0 else 0)

    left = max(0, bbox[0] - left_pad)
    top = max(0, bbox[1] - top_pad)
    right = min(canvas_size[0], bbox[2] + right_pad)
    bottom = min(canvas_size[1], bbox[3] + bottom_pad)
    box = (left, top, right, bottom)
    return ShadowRoi(box, mask_canvas.crop(box), (left, top))


def resize_for_cap(image: Image.Image, cap: int, resample=Image.Resampling.BILINEAR) -> tuple[Image.Image, float]:
    largest = max(image.size, default=0)
    if largest <= 0:
        return image, 1.0
    if largest <= cap:
        return image.copy(), 1.0
    scale = cap / largest
    size = (
        max(1, int(round(image.width * scale))),
        max(1, int(round(image.height * scale))),
    )
    return image.resize(size, resample), scale


def paste_offset(mask: Image.Image, dx: int, dy: int) -> Image.Image:
    out = Image.new("L", mask.size, 0)
    sx0 = max(0, -dx)
    sy0 = max(0, -dy)
    sx1 = min(mask.width, mask.width - dx) if dx >= 0 else mask.width
    sy1 = min(mask.height, mask.height - dy) if dy >= 0 else mask.height
    if sx1 <= sx0 or sy1 <= sy0:
        return out
    crop = mask.crop((sx0, sy0, sx1, sy1))
    out.paste(crop, (max(0, dx), max(0, dy)))
    return out


def mask_centroid(mask: Image.Image) -> tuple[float, float]:
    arr = np.asarray(mask, dtype=np.float32)
    total = float(arr.sum())
    if total <= 1e-6:
        return mask.width / 2.0, mask.height / 2.0
    ys, xs = np.indices(arr.shape, dtype=np.float32)
    return float((xs * arr).sum() / total), float((ys * arr).sum() / total)


def lightweight_mask_signature(mask: Image.Image, bbox: tuple[int, int, int, int] | None = None) -> int:
    """Stable low-cost signature for deterministic alpha noise."""
    bbox = bbox or mask.getbbox() or (0, 0, 0, 0)
    cropped = mask.crop(bbox) if bbox[2] > bbox[0] and bbox[3] > bbox[1] else mask
    small = cropped.resize((32, 32), Image.Resampling.BILINEAR) if cropped.size != (32, 32) else cropped
    arr = np.asarray(small, dtype=np.uint8)
    full = np.asarray(mask, dtype=np.uint8)
    alpha_sum = int(full.sum())
    cx, cy = mask_centroid(mask)
    payload = (
        f"{mask.size}|{bbox}|{alpha_sum}|{cx:.2f}|{cy:.2f}|".encode("ascii")
        + arr.tobytes()
    )
    return zlib.crc32(payload) & 0xFFFFFFFF
