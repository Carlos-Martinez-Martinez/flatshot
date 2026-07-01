from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import pairwise
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
    presence_correction: float = 1.0


def normalize_curve_data(curve: CurveData | Mapping[str, Any] | None) -> CurveData:
    data = dict(DEFAULT_SCALE_CURVE)
    if curve is not None:
        raw = curve.model_dump() if isinstance(curve, CurveData) else dict(curve)
        data.update({key: value for key, value in raw.items() if value is not None})

    xp = list(data.get("xp") or [])
    fp = list(data.get("fp") or [])
    is_valid_pair = len(xp) >= 2 and len(xp) == len(fp) and all(x2 > x1 for x1, x2 in pairwise(xp))

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


def _measure_optical_profile(
    img_rgba: Image.Image,
) -> tuple[float, float, np.ndarray, np.ndarray, float]:
    """Return (mass_aspect, occupancy, col_weights, row_weights, visible_area).

    The extra arrays are reused by ``_measure_presence_profile`` so we avoid
    building the mask twice.
    """
    alpha = build_subject_mask(img_rgba, max_side=320)

    weights = np.asarray(alpha, dtype=np.float32) / 255.0
    if weights.size == 0:
        return 1.0, 1.0, np.zeros(1), np.zeros(1), 0.0

    visible_area = float(weights.sum())
    if visible_area <= 1e-6:
        return 1.0, 1.0, np.zeros(1), np.zeros(1), 0.0

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

    return mass_aspect, occupancy, col_weights, row_weights, visible_area


@dataclass(frozen=True)
class _PresenceProfile:
    """Continuous descriptors of visual presence for a garment silhouette."""

    length_score: float       # 0 = very compact/short, 1 = very long
    compact_score: float      # 0 = elongated, 1 = square/compact
    strap_like_score: float   # 0 = no thin top zone, 1 = clear strap-like top
    mean_width_ratio: float   # avg width / max width — how uniform the width is
    top_vacancy: float        # how empty the top 20% of the bbox is
    correction: float         # final multiplicative correction to apply


def _measure_presence_profile(
    img_rgba: Image.Image,
    optical_aspect: float,
    occupancy: float,
    col_weights: np.ndarray,
    row_weights: np.ndarray,
    visible_area: float,
) -> _PresenceProfile:
    """Compute a continuous presence profile for a garment silhouette.

    Instead of hard categories (top vs dress), this measures continuous
    properties of the silhouette and derives a small, conservative correction
    factor that prevents tall garments from losing visual hierarchy against
    compact/wide ones.

    Returns a ``_PresenceProfile`` with the correction factor.
    """
    height_px = len(row_weights)
    width_px = len(col_weights)

    if height_px < 4 or width_px < 4 or visible_area <= 1e-6:
        return _PresenceProfile(
            length_score=0.5,
            compact_score=0.5,
            strap_like_score=0.0,
            mean_width_ratio=1.0,
            top_vacancy=0.0,
            correction=1.0,
        )

    # --- length_score: how elongated the silhouette is (continuous 0..1) ---
    # Based on optical_aspect; < 0.55 is very tall, > 1.1 is very wide/compact
    length_score = min(max((0.55 - optical_aspect) / 0.45, 0.0), 1.0)

    # --- compact_score: how square/compact the silhouette is (continuous 0..1) ---
    # Peaks near aspect ratio 1.0, falls off for both tall and wide shapes
    compact_score = _bell(optical_aspect, 1.0, 0.55)

    # --- mean_width_ratio: average width / max width ---
    # Measures how uniform the garment width is across its height.
    # Strappy tops have very uneven widths (thin at top, wide at body).
    max_row_mass = float(row_weights.max())
    if max_row_mass > 1e-6:
        mean_row_mass = float(row_weights[row_weights > 0.1].mean()) if np.any(row_weights > 0.1) else 0.0
        mean_width_ratio = min(mean_row_mass / max_row_mass, 1.0)
    else:
        mean_width_ratio = 1.0

    # --- top_vacancy: how empty the top 20% of the silhouette is ---
    # High for garments with straps/hangers at top but body below.
    top_slice = max(1, int(height_px * 0.20))
    top_mass = float(row_weights[:top_slice].sum())
    total_mass = float(row_weights.sum())
    # If mass were evenly distributed, top 20% would have 20% of total mass.
    # top_vacancy measures how much *less* than expected the top zone has.
    expected_top_fraction = top_slice / height_px
    actual_top_fraction = top_mass / max(total_mass, 1e-6)
    top_vacancy = min(max((expected_top_fraction - actual_top_fraction) / max(expected_top_fraction, 1e-6), 0.0), 1.0)

    # --- strap_like_score: detect thin strap-like structures at the top ---
    # Look at the top 15% of rows: if their average width is much less than
    # the overall average, there are straps or a hanger.
    strap_slice = max(1, int(height_px * 0.15))
    strap_zone_mass = row_weights[:strap_slice]
    body_zone_mass = row_weights[strap_slice:]

    if len(body_zone_mass) > 0 and float(body_zone_mass.mean()) > 1e-6:
        strap_body_ratio = float(strap_zone_mass.mean()) / float(body_zone_mass.mean())
        # If straps are much thinner than body, strap_like_score is high.
        # A ratio of 0.3 means straps are 30% the width of the body => high score.
        strap_like_score = min(max((0.65 - strap_body_ratio) / 0.45, 0.0), 1.0)
    else:
        strap_like_score = 0.0

    # === Presence correction ===
    # The correction is a small multiplier that adjusts target area / fit_fill.
    # Goal: tall garments get a slight *boost*, compact/wide garments get a
    # slight *reduction*, so they end up with more balanced visual presence.
    #
    # Corrections are deliberately conservative:
    #   tall/long garments:        +2% to +8%
    #   compact/wide garments:     -2% to -6%
    #   strappy short garments:    -1% to -4% (they look bigger than they are)
    #   tall garments with empty top (straps on a dress): partial offset
    #
    # The final correction is never more than ~±10%.

    correction = 1.0

    # Boost for tall/long silhouettes — counteract the old double penalty
    # length_score is 0..1 where 1 = very tall
    tall_boost = length_score * 0.08  # up to +8%
    # If the garment is tall but has lots of empty space at top (straps on a
    # long dress), reduce the boost slightly — visual mass is lower.
    tall_boost *= 1.0 - 0.3 * top_vacancy

    # Reduction for compact/wide silhouettes
    # compact_score peaks at 1.0 for squarish garments
    compact_reduction = compact_score * 0.04  # up to -4%
    # Extra reduction if the garment is truly wide (not just compact)
    wide_extra = min(max((optical_aspect - 1.15) / 0.60, 0.0), 1.0) * 0.04  # up to -4%

    # Strap adjustment: garments with visible straps and compact body look
    # wider than they are because straps push the bbox out.
    strap_adjustment = strap_like_score * (1.0 - length_score) * 0.04  # up to -4% for short+strappy

    correction += tall_boost
    correction -= compact_reduction
    correction -= wide_extra
    correction -= strap_adjustment

    # Occupancy-aware damping: if occupancy is very low (lots of empty space
    # inside the bbox), the garment has less visual mass than bbox suggests,
    # so we slightly dampen any positive correction.
    if occupancy < 0.45:
        low_occ_damping = (0.45 - occupancy) / 0.45  # 0..1
        if correction > 1.0:
            correction = 1.0 + (correction - 1.0) * (1.0 - 0.3 * low_occ_damping)

    # Hard clamp: never exceed ±10%
    correction = min(max(correction, 0.90), 1.10)

    return _PresenceProfile(
        length_score=length_score,
        compact_score=compact_score,
        strap_like_score=strap_like_score,
        mean_width_ratio=mean_width_ratio,
        top_vacancy=top_vacancy,
        correction=correction,
    )


def calculate_subject_scale(
    trimmed_rgba: Image.Image,
    safe_size: tuple[int, int],
    curve_data: CurveData | Mapping[str, Any] | None,
    color_scale_factor: float = 1.0,
) -> ScaleComputation:
    safe_w, safe_h = safe_size
    real_w, real_h = trimmed_rgba.size
    if real_w <= 0 or real_h <= 0 or safe_w <= 0 or safe_h <= 0:
        return ScaleComputation(1, 1, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0)

    curve = normalize_curve_data(curve_data)
    bbox_aspect = real_w / real_h
    mass_aspect, occupancy, col_weights, row_weights, visible_area = _measure_optical_profile(trimmed_rgba)

    aspect_mix = min(max(curve.aspect_mix, 0.0), 1.0)
    optical_aspect = bbox_aspect * (1.0 - aspect_mix) + mass_aspect * aspect_mix
    raw_curve_adjustment = float(np.interp(optical_aspect, curve.xp, curve.fp))
    curve_adjustment = 1.0 + (raw_curve_adjustment - 1.0) * curve.manual_curve_strength

    # --- Presence-based shape balance (replaces old double-penalty) ---
    presence = _measure_presence_profile(
        trimmed_rgba, optical_aspect, occupancy, col_weights, row_weights, visible_area,
    )

    # Residual shape_balance: keep a *mild* version of the old compactness
    # bonus so that the curve still has some shape-awareness, but remove
    # the harsh tallness/wideness penalties that caused the original problem.
    tallness = min(max((0.70 - optical_aspect) / 0.35, 0.0), 1.0)
    wideness = min(max((optical_aspect - 1.25) / 0.75, 0.0), 1.0)
    compactness = _bell(math.log(max(optical_aspect, 0.05)), 0.0, 0.48)

    # Old formula was: 1.0 + 0.12*compactness - 0.10*tallness - 0.06*wideness
    # New formula: keep small compactness bonus, drastically reduce tallness
    # penalty (from -0.10 to -0.03), and reduce wideness penalty (from -0.06
    # to -0.02). The presence_correction handles the rest.
    shape_balance = 1.0 + 0.08 * compactness - 0.03 * tallness - 0.02 * wideness
    shape_balance = min(max(shape_balance, 0.92), 1.10)

    scale_fit = min(safe_w / real_w, safe_h / real_h)
    safe_area = float(safe_w * safe_h)
    occupancy_influence = min(max(curve.occupancy_influence, 0.0), 1.0)
    effective_area = float(real_w * real_h) * (
        (1.0 - occupancy_influence) + occupancy_influence * occupancy
    )

    # Apply presence correction to target area
    target_area = safe_area * curve.base_fill * curve_adjustment * shape_balance * presence.correction
    area_scale = math.sqrt(max(target_area, 1.0) / max(effective_area, 1.0))

    # Old fit_fill: 1.0 - 0.08*tallness - 0.04*wideness (double penalty)
    # New fit_fill: much gentler, just a small safety margin for extreme shapes
    fit_fill = 1.0 - 0.02 * tallness - 0.02 * wideness
    max_scale = scale_fit * min(max(fit_fill, 0.94), 1.0)
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
        presence_correction=presence.correction,
    )
