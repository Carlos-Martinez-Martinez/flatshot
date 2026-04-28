from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np
from PIL import Image, ImageFilter

from flatshot.core.models import CurveData

CURVE_CONTROL_XP = [0.35, 0.60, 0.85, 1.10, 1.40]

DEFAULT_SCALE_CURVE = {
    "xp": [0.0, 0.35, 0.60, 0.85, 1.10, 1.40, 3.0],
    "fp": [0.88, 0.88, 0.96, 1.04, 1.02, 0.98, 0.98],
    "base_fill": 0.52,
    "aspect_mix": 0.45,
    "occupancy_influence": 0.42,
    "manual_curve_strength": 0.60,
}


@dataclass(frozen=True)
class ScaleComputation:
    width: int
    height: int
    final_scale: float
    scale_fit: float
    bbox_aspect: float
    mass_aspect: float
    optical_aspect: float
    occupancy: float
    curve_adjustment: float
    shape_balance: float
    fit_fill: float


def normalize_curve_data(curve: CurveData | Mapping[str, Any] | None) -> CurveData:
    data = dict(DEFAULT_SCALE_CURVE)
    if curve is not None:
        raw = curve.model_dump() if isinstance(curve, CurveData) else dict(curve)
        data.update({key: value for key, value in raw.items() if value is not None})

    xp = list(data.get("xp") or [])
    fp = list(data.get("fp") or [])
    is_valid_pair = len(xp) >= 2 and len(xp) == len(fp) and all(x2 > x1 for x1, x2 in zip(xp, xp[1:]))

    if not is_valid_pair:
        xp = list(DEFAULT_SCALE_CURVE["xp"])
        fp = list(DEFAULT_SCALE_CURVE["fp"])
    elif len(xp) == len(CURVE_CONTROL_XP):
        xp = [0.0, *xp, 3.0]
        fp = [fp[0], *fp, fp[-1]]
    else:
        if xp[0] > 0.0:
            xp = [0.0, *xp]
            fp = [fp[0], *fp]
        if xp[-1] < 3.0:
            xp = [*xp, 3.0]
            fp = [*fp, fp[-1]]

    data["xp"] = xp
    data["fp"] = fp
    return CurveData(**data)


def get_curve_control_values(curve: CurveData | Mapping[str, Any] | None) -> list[float]:
    normalized = normalize_curve_data(curve)
    values = np.interp(CURVE_CONTROL_XP, normalized.xp, normalized.fp)
    return [float(value) for value in values]


def build_curve_from_controls(
    control_values: list[float],
    base_curve: CurveData | Mapping[str, Any] | None = None,
) -> CurveData:
    if len(control_values) != len(CURVE_CONTROL_XP):
        raise ValueError("Expected 5 control values for the scale curve editor.")

    normalized = normalize_curve_data(base_curve).model_dump()
    fp = [float(value) for value in control_values]
    normalized["xp"] = [0.0, *CURVE_CONTROL_XP, 3.0]
    normalized["fp"] = [fp[0], *fp, fp[-1]]
    return CurveData(**normalized)


def _alpha_foreground_mask(img_rgba: Image.Image) -> Image.Image | None:
    if "A" not in img_rgba.getbands():
        return None

    alpha = img_rgba.getchannel("A")
    min_alpha, max_alpha = alpha.getextrema()
    if min_alpha >= 250 and max_alpha >= 250:
        return None
    return alpha.point(lambda p: 255 if p > 8 else 0)


def _resize_for_detection(img_rgba: Image.Image, max_side: int) -> tuple[Image.Image, float]:
    largest = max(img_rgba.size, default=0)
    if largest <= max_side:
        return img_rgba, 1.0

    ratio = max_side / largest
    resized = img_rgba.resize(
        (
            max(1, int(round(img_rgba.width * ratio))),
            max(1, int(round(img_rgba.height * ratio))),
        ),
        Image.Resampling.BILINEAR,
    )
    return resized, ratio


def _flat_background_mask(img_rgba: Image.Image) -> Image.Image | None:
    rgb = np.asarray(img_rgba.convert("RGB"), dtype=np.float32)
    height, width = rgb.shape[:2]
    if width < 8 or height < 8:
        return None

    patch_w = max(2, int(width * 0.08))
    patch_h = max(2, int(height * 0.08))
    corner_samples = np.concatenate(
        [
            rgb[:patch_h, :patch_w].reshape(-1, 3),
            rgb[:patch_h, -patch_w:].reshape(-1, 3),
            rgb[-patch_h:, :patch_w].reshape(-1, 3),
            rgb[-patch_h:, -patch_w:].reshape(-1, 3),
        ],
        axis=0,
    )
    bg = np.median(corner_samples, axis=0)
    dist = np.linalg.norm(rgb - bg, axis=2)

    border_w = max(2, int(width * 0.035))
    border_h = max(2, int(height * 0.035))
    border_dist = np.concatenate(
        [
            dist[:border_h, :].ravel(),
            dist[-border_h:, :].ravel(),
            dist[:, :border_w].ravel(),
            dist[:, -border_w:].ravel(),
        ]
    )
    threshold = float(np.percentile(border_dist, 98) + 8.0)
    threshold = min(max(threshold, 10.0), 34.0)

    mask = (dist > threshold).astype(np.uint8) * 255
    coverage = float(mask.mean() / 255.0)
    if coverage < 0.003 or coverage > 0.92:
        return None

    mask_img = Image.fromarray(mask, mode="L")
    mask_img = mask_img.filter(ImageFilter.MaxFilter(size=5)).filter(ImageFilter.MinFilter(size=3))
    return mask_img


def build_subject_mask(img_rgba: Image.Image, max_side: int = 640) -> Image.Image:
    work_img, ratio = _resize_for_detection(img_rgba, max_side=max_side)
    mask = _alpha_foreground_mask(work_img)
    if mask is None:
        mask = _flat_background_mask(work_img)
    if mask is None:
        mask = Image.new("L", work_img.size, 255)

    if ratio != 1.0:
        mask = mask.resize(img_rgba.size, Image.Resampling.NEAREST)
    return mask


def find_subject_bbox(img_rgba: Image.Image, max_side: int = 640) -> tuple[int, int, int, int] | None:
    mask = build_subject_mask(img_rgba, max_side=max_side)
    bbox = mask.getbbox()
    if not bbox:
        return None

    pad_x = max(2, int(img_rgba.width * 0.015))
    pad_y = max(2, int(img_rgba.height * 0.015))
    return (
        max(0, bbox[0] - pad_x),
        max(0, bbox[1] - pad_y),
        min(img_rgba.width, bbox[2] + pad_x),
        min(img_rgba.height, bbox[3] + pad_y),
    )


def _bell(value: float, center: float, width: float) -> float:
    return math.exp(-math.pow((value - center) / width, 2.0))


def _measure_optical_profile(img_rgba: Image.Image) -> tuple[float, float]:
    alpha = build_subject_mask(img_rgba, max_side=320)

    weights = np.asarray(alpha, dtype=np.float32) / 255.0
    if weights.size == 0:
        return 1.0, 1.0

    visible_area = float(weights.sum())
    if visible_area <= 1e-6:
        return 1.0, 1.0

    bbox_area = float(weights.shape[0] * weights.shape[1])
    occupancy = min(max(visible_area / max(bbox_area, 1.0), 0.0), 1.0)

    col_weights = weights.sum(axis=0)
    row_weights = weights.sum(axis=1)
    xs = np.arange(weights.shape[1], dtype=np.float32)
    ys = np.arange(weights.shape[0], dtype=np.float32)

    mean_x = float((col_weights * xs).sum() / visible_area)
    mean_y = float((row_weights * ys).sum() / visible_area)
    var_x = float((col_weights * np.square(xs - mean_x)).sum() / visible_area)
    var_y = float((row_weights * np.square(ys - mean_y)).sum() / visible_area)
    mass_aspect = math.sqrt(max(var_x, 1e-6) / max(var_y, 1e-6))
    mass_aspect = min(max(mass_aspect, 0.15), 4.0)

    return mass_aspect, occupancy


def calculate_subject_scale(
    trimmed_rgba: Image.Image,
    safe_size: tuple[int, int],
    curve_data: CurveData | Mapping[str, Any] | None,
    color_scale_factor: float = 1.0,
) -> ScaleComputation:
    safe_w, safe_h = safe_size
    real_w, real_h = trimmed_rgba.size
    if real_w <= 0 or real_h <= 0 or safe_w <= 0 or safe_h <= 0:
        return ScaleComputation(1, 1, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0)

    curve = normalize_curve_data(curve_data)
    bbox_aspect = real_w / real_h
    mass_aspect, occupancy = _measure_optical_profile(trimmed_rgba)

    aspect_mix = min(max(curve.aspect_mix, 0.0), 1.0)
    optical_aspect = bbox_aspect * (1.0 - aspect_mix) + mass_aspect * aspect_mix
    raw_curve_adjustment = float(np.interp(optical_aspect, curve.xp, curve.fp))
    curve_adjustment = 1.0 + (raw_curve_adjustment - 1.0) * curve.manual_curve_strength

    tallness = min(max((0.70 - optical_aspect) / 0.35, 0.0), 1.0)
    wideness = min(max((optical_aspect - 1.25) / 0.75, 0.0), 1.0)
    compactness = _bell(math.log(max(optical_aspect, 0.05)), 0.0, 0.48)
    shape_balance = 1.0 + 0.12 * compactness - 0.10 * tallness - 0.06 * wideness
    shape_balance = min(max(shape_balance, 0.88), 1.12)

    scale_fit = min(safe_w / real_w, safe_h / real_h)
    safe_area = float(safe_w * safe_h)
    occupancy_influence = min(max(curve.occupancy_influence, 0.0), 1.0)
    effective_area = float(real_w * real_h) * (
        (1.0 - occupancy_influence) + occupancy_influence * occupancy
    )
    target_area = safe_area * curve.base_fill * curve_adjustment * shape_balance
    area_scale = math.sqrt(max(target_area, 1.0) / max(effective_area, 1.0))

    fit_fill = 1.0 - 0.08 * tallness - 0.04 * wideness
    max_scale = scale_fit * min(max(fit_fill, 0.90), 1.0)
    final_scale = min(area_scale * max(color_scale_factor, 0.01), max_scale)

    width = max(1, int(real_w * final_scale))
    height = max(1, int(real_h * final_scale))
    return ScaleComputation(
        width=width,
        height=height,
        final_scale=final_scale,
        scale_fit=scale_fit,
        bbox_aspect=bbox_aspect,
        mass_aspect=mass_aspect,
        optical_aspect=optical_aspect,
        occupancy=occupancy,
        curve_adjustment=curve_adjustment,
        shape_balance=shape_balance,
        fit_fill=fit_fill,
    )
