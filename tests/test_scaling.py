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

    assert pants_result.height < int(safe_size[1] * 0.95)
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
