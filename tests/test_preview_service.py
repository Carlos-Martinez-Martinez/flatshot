from PIL import Image

import flatshot.application.preview_service as preview_service_module
from flatshot.application.contracts import PreviewRequest, TilePreviewRequest
from flatshot.application.preview_service import PreviewService
from flatshot.core.engine import ShadowEngine
from flatshot.core.models import CurveData, ShadowSettings


def _curve():
    return CurveData(xp=[0.0, 1.0], fp=[1.0, 1.0])


def _image(size=(24, 24)):
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    image.paste(Image.new("RGBA", (12, 12), (120, 80, 40, 255)), (6, 6))
    return image


def _expected_rgb_payload(image, settings, target_size, curve, scale_factor=1.0, is_preview=True):
    final_pil, diagnostics = ShadowEngine._aplicar_efectos_with_diagnostics(
        image,
        settings,
        target_size,
        scale_factor=scale_factor,
        curve_data=curve,
        is_preview=is_preview,
    )
    if final_pil.mode == "RGBA":
        bg = Image.new("RGB", final_pil.size, settings.bg_color)
        bg.paste(final_pil, (0, 0), mask=final_pil)
        final_pil = bg
    final_pil = final_pil.convert("RGB")
    warning = diagnostics.warning if diagnostics.fallback_used else None
    return final_pil.width, final_pil.height, final_pil.tobytes("raw", "RGB"), warning


def test_preview_service_does_not_import_pyqt():
    source = preview_service_module.Path(preview_service_module.__file__).read_text(encoding="utf-8")

    assert "PyQt6" not in source
    assert "QImage" not in source
    assert "QPixmap" not in source


def test_render_preview_matches_previous_rgb_payload():
    source = _image()
    settings = ShadowSettings(
        opacity=0,
        blur=0,
        noise=0,
        bg_color=(12, 34, 56),
        transparent_bg=False,
    )
    curve = _curve()

    result = PreviewService().render_preview(
        PreviewRequest(
            image=source,
            settings=settings.model_dump(),
            curve_data=curve.model_dump(),
            target_size=(48, 48),
            scale_factor=1.0,
            is_preview=True,
        )
    )

    expected_width, expected_height, expected_bytes, expected_warning = _expected_rgb_payload(
        source,
        settings,
        (48, 48),
        curve,
    )
    assert result.width == expected_width
    assert result.height == expected_height
    assert result.mode == "RGB"
    assert result.bytes_rgb == expected_bytes
    assert result.warning == expected_warning


def test_render_preview_accepts_image_path(tmp_path):
    path = tmp_path / "source.png"
    _image().save(path)

    result = PreviewService().render_preview(
        PreviewRequest(
            image_path=path,
            settings=ShadowSettings(opacity=0, blur=0, noise=0),
            curve_data=_curve(),
            target_size=(32, 32),
            scale_factor=1.0,
        )
    )

    assert result.width == 32
    assert result.height == 32
    assert len(result.bytes_rgb) == result.width * result.height * 3


def test_render_tile_preview_returns_processed_and_original_payloads(tmp_path):
    path = tmp_path / "tile.png"
    _image((40, 30)).save(path)
    target_size = (32, 32)

    result = PreviewService().render_tile_preview(
        TilePreviewRequest(
            image_path=path,
            settings=ShadowSettings(opacity=0, blur=0, noise=0, bg_color=(230, 230, 230)),
            curve_data=_curve().model_dump(),
            target_size=target_size,
        )
    )

    assert result.processed.width == target_size[0]
    assert result.processed.height == target_size[1]
    assert len(result.processed.bytes_rgb) == result.processed.width * result.processed.height * 3
    assert result.original.width <= target_size[0]
    assert result.original.height <= target_size[1]
    assert len(result.original.bytes_rgb) == result.original.width * result.original.height * 3
