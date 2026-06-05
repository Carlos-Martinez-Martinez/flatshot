from pathlib import Path
from concurrent.futures import Future

import pytest
from PIL import Image, ImageDraw

from flatshot.application.contracts import ExportJobRequest
from flatshot.application.export_runner import (
    ExportRunner,
    build_variant_output_path,
    validate_output_path_collisions,
)
from flatshot.core.models import CurveData, ExportConfig, ShadowSettings, WEB_RGB230, WHITE_RGB255


class InlineExecutor:
    def __init__(self, max_workers=1):
        self.max_workers = max_workers

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.shutdown()

    def submit(self, fn, arg):
        future = Future()
        try:
            future.set_result(fn(arg))
        except Exception as exc:
            future.set_exception(exc)
        return future

    def shutdown(self, wait=True, cancel_futures=False):
        return None


def _curve():
    return CurveData(xp=[0.0, 1.0], fp=[1.0, 1.0])


def _source(folder: Path):
    source = folder / "camiseta_001.png"
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle((8, 5, 23, 26), fill=(20, 120, 240, 255))
    img.save(source)
    return source


def _has_grayscale_shadow(path: Path, bg: tuple[int, int, int]) -> bool:
    with Image.open(path) as img:
        rgb = img.convert("RGB")
        for pixel in rgb.getdata():
            if pixel == bg:
                continue
            if not all(pixel[index] <= bg[index] for index in range(3)):
                continue
            if max(pixel) - min(pixel) <= 8:
                return True
    return False


def _contains_background(path: Path, bg: tuple[int, int, int]) -> bool:
    with Image.open(path) as img:
        return bg in set(img.convert("RGB").getdata())


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
