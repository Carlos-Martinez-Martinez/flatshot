from PIL import Image

from flatshot.core.engine import ShadowEngine
from flatshot.core.models import ShadowSettings
from flatshot.core.overrides import (
    apply_image_override,
    has_image_override,
    normalize_image_override,
)
from flatshot.application.export_runner import process_single_image


def test_normalize_image_override_keeps_only_non_zero_clamped_deltas():
    override = normalize_image_override(
        {
            "size_delta": 120,
            "shadow_delta": 0,
            "blur_delta": -120,
            "unknown": 12,
        }
    )

    assert override == {"size_delta": 30, "blur_delta": -40}
    assert has_image_override(override)
    assert not has_image_override({"size_delta": 0, "shadow_delta": 0, "blur_delta": 0})


def test_apply_image_override_does_not_mutate_global_settings():
    base = ShadowSettings(opacity=80, blur=12, scale_adjustment=0)

    effective = apply_image_override(
        base,
        {"size_delta": 18, "shadow_delta": 30, "blur_delta": -5},
    )

    assert base.opacity == 80
    assert base.blur == 12
    assert base.scale_adjustment == 0
    assert effective.opacity == 100
    assert effective.blur == 7
    assert effective.scale_adjustment == 18


def test_scale_adjustment_changes_rendered_subject_size():
    subject = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    subject.paste(Image.new("RGBA", (60, 60), (200, 40, 40, 255)), (20, 20))

    common = dict(
        adaptive_zoom=False,
        padding=20,
        transparent_bg=True,
        opacity=0,
        blur=0,
        contact_blur=0,
        noise=0,
    )
    smaller = ShadowEngine.aplicar_efectos(
        subject,
        ShadowSettings(**common, scale_adjustment=-20),
        (300, 300),
    )
    larger = ShadowEngine.aplicar_efectos(
        subject,
        ShadowSettings(**common, scale_adjustment=20),
        (300, 300),
    )

    smaller_bbox = smaller.getchannel("A").getbbox()
    larger_bbox = larger.getchannel("A").getbbox()

    assert smaller_bbox is not None
    assert larger_bbox is not None
    assert larger_bbox[2] - larger_bbox[0] > smaller_bbox[2] - smaller_bbox[0]


def test_process_single_image_accepts_local_override(tmp_path):
    source = tmp_path / "source.png"
    subject = Image.new("RGBA", (100, 120), (0, 0, 0, 0))
    subject.paste(Image.new("RGBA", (60, 80), (40, 80, 180, 255)), (20, 20))
    subject.save(source)

    save_path = tmp_path / "source_PRO.png"
    success, message, warning = process_single_image(
        (
            source,
            save_path,
            ShadowSettings(adaptive_zoom=False, opacity=0, blur=0, noise=0).model_dump(),
            (300, 400),
            "png",
            None,
            {"size_delta": 10, "shadow_delta": -5, "blur_delta": 3},
            "source.png",
        )
    )

    assert success, message
    assert warning is None
    assert save_path.exists()
