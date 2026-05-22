from argparse import Namespace
from concurrent.futures import Future
from pathlib import Path

import pytest
from PIL import Image

from flatshot import cli
from flatshot.application.contracts import ExportJobRequest
from flatshot.application.export_runner import ExportRunner
from flatshot.core.models import ExportConfig, ShadowSettings
from flatshot.core.scaling import DEFAULT_SCALE_CURVE, normalize_curve_data


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
        pass


class StubLogger:
    def log_export_start(self, *args, **kwargs):
        pass

    def log_export_complete(self, *args, **kwargs):
        pass

    def log_error(self, *args, **kwargs):
        pass


def _write_png(folder: Path, name: str = "product.png") -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGBA", (24, 32), (0, 0, 0, 0))
    for x in range(6, 18):
        for y in range(8, 24):
            image.putpixel((x, y), (200, 40, 20, 255))
    path = folder / name
    image.save(path, dpi=(300, 300))
    return path


def _cli_args(source: Path, *, dry_run: bool = False) -> Namespace:
    return Namespace(
        input=str(source),
        preset=None,
        output="_PARITY_OUT",
        size="80x100",
        format="JPG",
        suffix="_PRO",
        template="{original}{suffix}",
        dry_run=dry_run,
        shadow_engine=None,
    )


def _patch_cli_user_state(monkeypatch):
    monkeypatch.setattr(cli, "_load_app_settings", lambda: {})
    monkeypatch.setattr(cli, "_log_service", lambda: StubLogger())


def _run_cli(monkeypatch, source: Path) -> Path:
    _patch_cli_user_state(monkeypatch)
    cli.process_folder(_cli_args(source))
    return source / "_PARITY_OUT" / "product_PRO.jpg"


def _run_export_runner(source: Path):
    config = ExportConfig(
        output_folder_name="_PARITY_OUT",
        suffix="_PRO",
        format="JPG",
        output_width=80,
        output_height=100,
        naming_template="{original}{suffix}",
    )
    request = ExportJobRequest(
        input_folder=source,
        settings=ShadowSettings(),
        export_config=config,
        curve_data=normalize_curve_data(DEFAULT_SCALE_CURVE.copy()),
    )
    runner = ExportRunner(executor_factory=InlineExecutor)

    result = runner.run(request)

    return result, source / "_PARITY_OUT" / "product_PRO.jpg"


def _image_metadata(path: Path) -> dict:
    with Image.open(path) as image:
        dpi = image.info.get("dpi")
        return {
            "name": path.name,
            "extension": path.suffix.lower(),
            "size": image.size,
            "mode": image.mode,
            "dpi": dpi,
        }


def _assert_dpi_close(actual, expected=(300, 300)):
    assert actual is not None
    assert actual[0] == pytest.approx(expected[0], abs=1)
    assert actual[1] == pytest.approx(expected[1], abs=1)


def test_cli_and_export_runner_preserve_basic_jpg_output_metadata(monkeypatch, tmp_path, capsys):
    cli_source = tmp_path / "cli-source"
    runner_source = tmp_path / "runner-source"
    _write_png(cli_source)
    _write_png(runner_source)

    cli_output = _run_cli(monkeypatch, cli_source)
    capsys.readouterr()
    runner_result, runner_output = _run_export_runner(runner_source)

    cli_metadata = _image_metadata(cli_output)
    runner_metadata = _image_metadata(runner_output)

    assert runner_result.success
    assert runner_result.processed == 1
    assert runner_result.total == 1
    assert cli_metadata["name"] == runner_metadata["name"] == "product_PRO.jpg"
    assert cli_metadata["extension"] == runner_metadata["extension"] == ".jpg"
    assert cli_metadata["size"] == runner_metadata["size"] == (80, 100)
    assert cli_metadata["mode"] == runner_metadata["mode"] == "RGB"
    _assert_dpi_close(cli_metadata["dpi"])
    _assert_dpi_close(runner_metadata["dpi"])


def test_cli_dry_run_reports_plan_without_creating_output(monkeypatch, tmp_path, capsys):
    source = tmp_path / "cli-dry-run"
    _write_png(source)
    _patch_cli_user_state(monkeypatch)

    cli.process_folder(_cli_args(source, dry_run=True))

    captured = capsys.readouterr()
    assert "DRY RUN" in captured.out
    assert "Found 1 images to process" in captured.out
    assert not (source / "_PARITY_OUT").exists()
