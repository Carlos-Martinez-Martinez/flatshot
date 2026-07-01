from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageDraw
from PIL.JpegImagePlugin import get_sampling

from flatshot.application.contracts import ExportJobRequest
from flatshot.application.export_runner import (
    ExportRunner,
    build_variant_output_path,
    validate_output_path_collisions,
    variant_target_size,
)
from flatshot.core.models import CurveData, ExportConfig, ExportVariant, ShadowSettings, WEB_RGB230, WHITE_RGB255
from tests.helpers import InlineExecutor


def _curve():
    return CurveData(xp=[0.0, 1.0], fp=[1.0, 1.0])


def _source(folder: Path):
    source = folder / "camiseta_001.png"
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle((8, 5, 23, 26), fill=(20, 120, 240, 255))
    img.save(source)
    return source


def _source_with_dpi(folder: Path, dpi=(300, 300)):
    source = folder / "camiseta_dpi.png"
    img = Image.new("RGBA", (40, 48), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((10, 8, 29, 39), radius=3, fill=(20, 120, 240, 255))
    img.save(source, dpi=dpi)
    return source


def _assert_dpi_close(actual, expected=(300, 300)):
    assert actual is not None
    assert actual[0] == pytest.approx(expected[0], abs=1)
    assert actual[1] == pytest.approx(expected[1], abs=1)


def _has_grayscale_shadow(path: Path, bg: tuple[int, int, int]) -> bool:
    with Image.open(path) as img:
        arr = np.asarray(img.convert("RGB"), dtype=np.int16)
    bg_arr = np.asarray(bg, dtype=np.int16)
    differs_from_bg = np.any(arr != bg_arr, axis=2)
    below_or_equal_bg = np.all(arr <= bg_arr, axis=2)
    near_grayscale = (arr.max(axis=2) - arr.min(axis=2)) <= 8
    return bool(np.any(differs_from_bg & below_or_equal_bg & near_grayscale))


def _contains_background(path: Path, bg: tuple[int, int, int]) -> bool:
    with Image.open(path) as img:
        arr = np.asarray(img.convert("RGB"), dtype=np.int16)
    return bool(np.any(np.all(arr == np.asarray(bg, dtype=np.int16), axis=2)))


def test_two_enabled_variants_with_different_suffixes_generate_distinct_paths(tmp_path):
    config = ExportConfig(
        format="PNG",
        variants=[
            WEB_RGB230,
            WHITE_RGB255.model_copy(update={"enabled": True}),
        ],
    )

    web_path, _ = build_variant_output_path(tmp_path, config, config.variants[0], "camiseta_001", "Camisetas", 1)
    white_path, _ = build_variant_output_path(tmp_path, config, config.variants[1], "camiseta_001", "Camisetas", 1)

    assert web_path.name == "camiseta_001_PRO.png"
    assert white_path.name == "camiseta_001_BLANCO.png"
    validate_output_path_collisions(
        [
            {"save_path": web_path, "variant": config.variants[0]},
            {"save_path": white_path, "variant": config.variants[1]},
        ]
    )


def test_two_enabled_variants_with_same_suffix_detect_collision(tmp_path):
    white_same_suffix = WHITE_RGB255.model_copy(update={"enabled": True, "suffix": "_PRO"})
    config = ExportConfig(
        format="PNG",
        variants=[
            WEB_RGB230,
            white_same_suffix,
        ],
    )
    web_path, _ = build_variant_output_path(tmp_path, config, config.variants[0], "camiseta_001", "Camisetas", 1)
    white_path, _ = build_variant_output_path(tmp_path, config, config.variants[1], "camiseta_001", "Camisetas", 1)

    with pytest.raises(ValueError, match="generarían el mismo archivo"):
        validate_output_path_collisions(
            [
                {"save_path": web_path, "variant": config.variants[0]},
                {"save_path": white_path, "variant": config.variants[1]},
            ]
        )


def test_export_runner_exports_two_variant_files_with_expected_backgrounds(tmp_path):
    _source(tmp_path)
    config = ExportConfig(
        format="PNG",
        output_width=80,
        output_height=80,
        variants=[
            WEB_RGB230,
            WHITE_RGB255.model_copy(update={"enabled": True}),
        ],
    )
    settings = ShadowSettings(
        opacity=50,
        blur=4,
        distance=4,
        noise=0,
        padding=80,
        shadow_engine="legacy",
    )

    runner = ExportRunner(executor_factory=InlineExecutor)
    runner.run(
        ExportJobRequest(
            input_folder=tmp_path,
            settings=settings,
            export_config=config,
            curve_data=_curve(),
        )
    )

    web_output = tmp_path / "_SALIDA_PRO" / "camiseta_001_PRO.png"
    white_output = tmp_path / "_SALIDA_PRO" / "camiseta_001_BLANCO.png"

    assert web_output.exists()
    assert white_output.exists()

    assert _contains_background(web_output, (230, 230, 230))
    assert _contains_background(white_output, (255, 255, 255))

    assert _has_grayscale_shadow(web_output, (230, 230, 230))
    assert _has_grayscale_shadow(white_output, (255, 255, 255))


def test_single_variant_export_keeps_default_behavior(tmp_path):
    _source(tmp_path)
    config = ExportConfig(format="PNG", output_width=40, output_height=40)
    settings = ShadowSettings(opacity=0, blur=0, noise=0)

    runner = ExportRunner(executor_factory=InlineExecutor)
    runner.run(
        ExportJobRequest(
            input_folder=tmp_path,
            settings=settings,
            export_config=config,
            curve_data=_curve(),
        )
    )

    output = tmp_path / "_SALIDA_PRO" / "camiseta_001_PRO.png"
    assert output.exists()


def test_variant_format_destination_template_and_size_override_are_independent(tmp_path):
    jpg_variant = ExportVariant(
        id="marketplace_jpg",
        label="Marketplace JPG",
        format="JPG",
        suffix="_MK",
        output_destination="subfolder",
        output_folder_name="_MARKET",
        naming_template="{folder}_{original}{suffix}",
        output_width=120,
        output_height=160,
    )
    png_variant = ExportVariant(
        id="archive_png",
        label="Archive PNG",
        format="PNG",
        suffix="_ARCH",
        output_destination="custom",
        custom_output_path=str(tmp_path / "archive"),
        naming_template="{original}_{variant_id}{suffix}",
        output_width=80,
        output_height=80,
    )
    config = ExportConfig(
        format="JPG",
        output_width=40,
        output_height=40,
        variants=[jpg_variant, png_variant],
    )

    jpg_path, jpg_fmt = build_variant_output_path(
        tmp_path / "_MARKET",
        config,
        jpg_variant,
        "camiseta_001",
        "Camisetas",
        1,
    )
    png_path, png_fmt = build_variant_output_path(
        tmp_path / "archive",
        config,
        png_variant,
        "camiseta_001",
        "Camisetas",
        1,
    )

    assert jpg_path == tmp_path / "_MARKET" / "Camisetas_camiseta_001_MK.jpg"
    assert jpg_fmt == "jpg"
    assert variant_target_size(config, jpg_variant) == (120, 160)
    assert png_path == tmp_path / "archive" / "camiseta_001_archive_png_ARCH.png"
    assert png_fmt == "png"
    assert variant_target_size(config, png_variant) == (80, 80)


def test_export_runner_writes_variant_specific_formats_destinations_and_sizes(tmp_path):
    _source(tmp_path)
    custom_output = tmp_path / "custom-output"
    config = ExportConfig(
        format="JPG",
        output_width=40,
        output_height=40,
        variants=[
            ExportVariant(
                id="shop_jpg",
                label="Shop JPG",
                format="JPG",
                suffix="_SHOP",
                output_destination="subfolder",
                output_folder_name="_SHOP",
                naming_template="{original}{suffix}",
                output_width=30,
                output_height=50,
            ),
            ExportVariant(
                id="archive_png",
                label="Archive PNG",
                format="PNG",
                suffix="_ARCH",
                output_destination="custom",
                custom_output_path=str(custom_output),
                naming_template="{original}{suffix}",
                output_width=20,
                output_height=20,
            ),
        ],
    )
    settings = ShadowSettings(opacity=0, blur=0, noise=0)

    result = ExportRunner(executor_factory=InlineExecutor).run(
        ExportJobRequest(
            input_folder=tmp_path,
            settings=settings,
            export_config=config,
            curve_data=_curve(),
        )
    )

    jpg_output = tmp_path / "_SHOP" / "camiseta_001_SHOP.jpg"
    png_output = custom_output / "camiseta_001_ARCH.png"
    assert result.success
    assert result.total == 2
    assert jpg_output.exists()
    assert png_output.exists()
    with Image.open(jpg_output) as jpg:
        assert jpg.format == "JPEG"
        assert jpg.size == (30, 50)
    with Image.open(png_output) as png:
        assert png.format == "PNG"
        assert png.size == (20, 20)


def test_export_runner_preserves_output_metadata_transparency_and_source_file(tmp_path):
    source = _source_with_dpi(tmp_path)
    source_bytes = source.read_bytes()
    config = ExportConfig(
        format="JPG",
        output_width=64,
        output_height=96,
        variants=[
            ExportVariant(
                id="marketplace_jpg",
                label="Marketplace JPG",
                format="JPG",
                suffix="_MK",
                output_width=64,
                output_height=96,
                transparent_bg=False,
                bg_color=(230, 230, 230),
            ),
            ExportVariant(
                id="transparent_png",
                label="Transparent PNG",
                format="PNG",
                suffix="_TR",
                output_width=64,
                output_height=96,
                transparent_bg=True,
            ),
        ],
    )
    settings = ShadowSettings(
        shadow_engine="legacy",
        adaptive_zoom=False,
        opacity=0,
        blur=0,
        noise=0,
    )

    result = ExportRunner(executor_factory=InlineExecutor).run(
        ExportJobRequest(
            input_folder=tmp_path,
            settings=settings,
            export_config=config,
            curve_data=_curve(),
        )
    )

    jpg_output = tmp_path / "_SALIDA_PRO" / "camiseta_dpi_MK.jpg"
    png_output = tmp_path / "_SALIDA_PRO" / "camiseta_dpi_TR.png"

    assert result.success
    assert result.total == 2
    assert source.read_bytes() == source_bytes

    with Image.open(jpg_output) as jpg:
        assert jpg.format == "JPEG"
        assert jpg.mode == "RGB"
        assert jpg.size == (64, 96)
        assert get_sampling(jpg) == 0
        _assert_dpi_close(jpg.info.get("dpi"))

    with Image.open(png_output) as png:
        assert png.format == "PNG"
        assert png.mode == "RGBA"
        assert png.size == (64, 96)
        assert png.getpixel((0, 0))[3] == 0
        assert png.getchannel("A").getbbox() is not None
        _assert_dpi_close(png.info.get("dpi"))
