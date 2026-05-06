from PIL import Image

from flatshot.core.scaling import (
    build_curve_from_controls,
    calculate_subject_scale,
    find_subject_bbox,
    get_curve_control_values,
    normalize_curve_data,
)


def _make_subject(canvas_size, draw_fn):
    img = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    draw_fn(img)
    return img


def test_normalize_curve_data_accepts_legacy_five_point_curves():
    curve = normalize_curve_data(
        {
            "xp": [0.35, 0.60, 0.85, 1.10, 1.40],
            "fp": [0.82, 0.90, 1.00, 0.95, 0.90],
        }
    )

    assert curve.xp == [0.0, 0.35, 0.60, 0.85, 1.10, 1.40, 3.0]
    assert curve.fp == [0.82, 0.82, 0.90, 1.00, 0.95, 0.90, 0.90]


def test_curve_editor_helpers_keep_the_five_control_points():
    built = build_curve_from_controls([0.80, 0.90, 1.00, 0.95, 0.90])
    values = get_curve_control_values(built)

    assert [round(value, 2) for value in values] == [0.80, 0.90, 1.00, 0.95, 0.90]


def test_calculate_subject_scale_compensates_low_occupancy_shapes():
    curve = normalize_curve_data(None)
    safe_size = (300, 300)

    full_block = _make_subject(
        (120, 120),
        lambda img: img.paste(Image.new("RGBA", (120, 120), (255, 255, 255, 255)), (0, 0)),
    )
    hollow_frame = _make_subject(
        (120, 120),
        lambda img: (
            img.paste(Image.new("RGBA", (120, 18), (255, 255, 255, 255)), (0, 0)),
            img.paste(Image.new("RGBA", (120, 18), (255, 255, 255, 255)), (0, 102)),
            img.paste(Image.new("RGBA", (18, 120), (255, 255, 255, 255)), (0, 0)),
            img.paste(Image.new("RGBA", (18, 120), (255, 255, 255, 255)), (102, 0)),
        ),
    )

    full_result = calculate_subject_scale(full_block, safe_size, curve)
    hollow_result = calculate_subject_scale(hollow_frame, safe_size, curve)

    assert hollow_result.occupancy < full_result.occupancy
    assert hollow_result.final_scale > full_result.final_scale


def test_find_subject_bbox_detects_flat_light_backgrounds():
    img = Image.new("RGBA", (300, 300), (242, 242, 242, 255))
    img.paste(Image.new("RGBA", (120, 160), (75, 80, 78, 255)), (90, 70))

    bbox = find_subject_bbox(img)

    assert bbox is not None
    assert bbox[0] < 95
    assert bbox[1] < 75
    assert bbox[2] > 205
    assert bbox[3] > 225
    assert bbox[2] - bbox[0] < 170
    assert bbox[3] - bbox[1] < 210


def test_calculate_subject_scale_balances_long_and_compact_garments():
    curve = normalize_curve_data(None)
    safe_size = (300, 400)
    pants = _make_subject(
        (90, 260),
        lambda img: img.paste(Image.new("RGBA", (90, 260), (255, 255, 255, 255)), (0, 0)),
    )
    shorts = _make_subject(
        (160, 130),
        lambda img: img.paste(Image.new("RGBA", (160, 130), (255, 255, 255, 255)), (0, 0)),
    )

    pants_result = calculate_subject_scale(pants, safe_size, curve)
    shorts_result = calculate_subject_scale(shorts, safe_size, curve)

    # With the relaxed tallness penalty, pants are allowed to fill more
    # of the safe zone — but should still stay within the safe area.
    assert pants_result.height < int(safe_size[1] * 1.01)
    assert shorts_result.width > int(safe_size[0] * 0.85)


def test_calculate_subject_scale_uses_mass_aspect_for_optical_profile():
    curve = normalize_curve_data(None)
    safe_size = (320, 420)
    tshirt_like = _make_subject(
        (220, 260),
        lambda img: (
            img.paste(Image.new("RGBA", (140, 160), (255, 255, 255, 255)), (40, 70)),
            img.paste(Image.new("RGBA", (55, 60), (255, 255, 255, 255)), (5, 70)),
            img.paste(Image.new("RGBA", (55, 60), (255, 255, 255, 255)), (160, 70)),
        ),
    )

    result = calculate_subject_scale(tshirt_like, safe_size, curve)

    assert result.mass_aspect != result.bbox_aspect
    assert min(result.mass_aspect, result.bbox_aspect) <= result.optical_aspect <= max(result.mass_aspect, result.bbox_aspect)


# --- New tests for presence-based visual balance ---


def test_presence_correction_boosts_tall_garments():
    """A tall garment (dress-like) should get a presence correction > 1.0."""
    curve = normalize_curve_data(None)
    safe_size = (300, 400)
    dress = _make_subject(
        (100, 320),
        lambda img: img.paste(Image.new("RGBA", (100, 320), (255, 255, 255, 255)), (0, 0)),
    )

    result = calculate_subject_scale(dress, safe_size, curve)

    assert result.presence_correction > 1.0, (
        f"Tall garment should get a positive presence boost, got {result.presence_correction:.4f}"
    )


def test_presence_correction_reduces_compact_wide_garments():
    """A compact/wide garment (top-like) should get a presence correction <= 1.0."""
    curve = normalize_curve_data(None)
    safe_size = (300, 400)
    wide_top = _make_subject(
        (240, 140),
        lambda img: img.paste(Image.new("RGBA", (240, 140), (255, 255, 255, 255)), (0, 0)),
    )

    result = calculate_subject_scale(wide_top, safe_size, curve)

    assert result.presence_correction <= 1.0, (
        f"Wide garment should not get a positive boost, got {result.presence_correction:.4f}"
    )


def test_presence_correction_is_conservative():
    """Presence corrections should stay within ±10%."""
    curve = normalize_curve_data(None)
    safe_size = (300, 400)

    shapes = [
        (60, 350),   # very tall
        (250, 100),  # very wide
        (180, 180),  # square
        (100, 200),  # moderately tall
    ]
    for w, h in shapes:
        subject = _make_subject(
            (w, h),
            lambda img, _w=w, _h=h: img.paste(
                Image.new("RGBA", (_w, _h), (255, 255, 255, 255)), (0, 0)
            ),
        )
        result = calculate_subject_scale(subject, safe_size, curve)
        assert 0.90 <= result.presence_correction <= 1.10, (
            f"Presence correction {result.presence_correction:.4f} out of ±10% range for shape {w}x{h}"
        )


def test_tall_dress_not_smaller_than_wide_top():
    """A tall dress-like garment should maintain visual hierarchy against a
    wide compact top of similar overall pixel area.

    This is the core bug that the presence system was designed to fix: previously
    the double tallness penalty made dresses look subordinate to wide tops.
    """
    curve = normalize_curve_data(None)
    safe_size = (300, 400)

    # Dress: tall, narrow — approx area 90*280 = 25200
    dress = _make_subject(
        (90, 280),
        lambda img: img.paste(Image.new("RGBA", (90, 280), (255, 255, 255, 255)), (0, 0)),
    )
    # Wide top: short, wide — approx area 200*130 = 26000
    top = _make_subject(
        (200, 130),
        lambda img: img.paste(Image.new("RGBA", (200, 130), (255, 255, 255, 255)), (0, 0)),
    )

    dress_result = calculate_subject_scale(dress, safe_size, curve)
    top_result = calculate_subject_scale(top, safe_size, curve)

    dress_area = dress_result.width * dress_result.height
    top_area = top_result.width * top_result.height

    # The dress should have at least 70% of the top's visual area,
    # not be dramatically smaller as with the old double-penalty.
    ratio = dress_area / max(top_area, 1)
    assert ratio > 0.70, (
        f"Dress visual area ({dress_area}) is too small vs top ({top_area}), ratio={ratio:.3f}"
    )


def test_strappy_top_gets_strap_reduction():
    """A top with thin straps (wide bbox but thin top zone) should have its
    presence reduced slightly vs a solid rectangular garment of same bbox."""
    curve = normalize_curve_data(None)
    safe_size = (300, 400)

    # Strappy top: wide bbox but straps are thin at the top
    strappy = _make_subject(
        (200, 180),
        lambda img: (
            # Thin straps at top (10px wide each, 40px tall)
            img.paste(Image.new("RGBA", (10, 40), (255, 255, 255, 255)), (40, 0)),
            img.paste(Image.new("RGBA", (10, 40), (255, 255, 255, 255)), (150, 0)),
            # Body of the top
            img.paste(Image.new("RGBA", (160, 140), (255, 255, 255, 255)), (20, 40)),
        ),
    )
    # Solid rectangular garment of same bbox
    solid = _make_subject(
        (200, 180),
        lambda img: img.paste(Image.new("RGBA", (200, 180), (255, 255, 255, 255)), (0, 0)),
    )

    strappy_result = calculate_subject_scale(strappy, safe_size, curve)
    solid_result = calculate_subject_scale(solid, safe_size, curve)

    # The strappy top should get a lower presence correction than the solid
    # one (the strap detection penalises it). Note: final_scale may differ
    # because occupancy compensation is independent of presence, so we
    # compare the presence_correction field directly.
    assert strappy_result.presence_correction <= solid_result.presence_correction, (
        f"Strappy top correction ({strappy_result.presence_correction:.4f}) should be "
        f"<= solid correction ({solid_result.presence_correction:.4f})"
    )


def test_presence_correction_default_for_neutral_shapes():
    """A roughly square garment should get a near-neutral presence correction."""
    curve = normalize_curve_data(None)
    safe_size = (300, 400)
    square = _make_subject(
        (180, 180),
        lambda img: img.paste(Image.new("RGBA", (180, 180), (255, 255, 255, 255)), (0, 0)),
    )

    result = calculate_subject_scale(square, safe_size, curve)

    # A square/compact shape receives a small compact_reduction (up to -4%)
    # which is by design — compact garments should lose a tiny bit of
    # presence to balance against taller ones. ±6% tolerance.
    assert 0.94 <= result.presence_correction <= 1.03, (
        f"Square garment should have near-neutral correction, got {result.presence_correction:.4f}"
    )
