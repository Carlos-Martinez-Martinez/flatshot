import threading
from concurrent.futures import Future

from PIL import Image

import flatshot.application.export_runner as export_runner_module
from flatshot.application.contracts import ExportJobRequest
from flatshot.application.events import (
    ExportFinishedEvent,
    ExportImageCompletedEvent,
    ExportProgressEvent,
)
from flatshot.application.execution_control import CancellationToken, PauseToken
from flatshot.application.export_runner import ExportRunner
from flatshot.core.models import CurveData, ExportConfig, ShadowSettings


class InlineExecutor:
    def __init__(self, max_workers=1):
        self.max_workers = max_workers
        self.shutdown_called = False

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
        self.shutdown_called = True


class CollectingSink:
    def __init__(self):
        self.events = []

    def emit(self, event):
        self.events.append(event)


def _curve():
    return CurveData(xp=[0.0, 1.0], fp=[1.0, 1.0])


def _source(folder):
    source = folder / "source.png"
    Image.new("RGBA", (8, 8), (120, 80, 40, 255)).save(source)
    return source


def _request(folder, config=None, settings=None):
    return ExportJobRequest(
        input_folder=folder,
        settings=settings or ShadowSettings(opacity=0, blur=0, noise=0),
        export_config=config or ExportConfig(format="PNG", output_width=8, output_height=8),
        curve_data=_curve(),
    )


def test_export_runner_does_not_import_pyqt():
    source = export_runner_module.Path(export_runner_module.__file__).read_text(encoding="utf-8")

    assert "PyQt6" not in source
    assert "QThread" not in source
    assert "pyqtSignal" not in source


def test_export_runner_empty_folder_returns_success(tmp_path):
    sink = CollectingSink()
    runner = ExportRunner(event_sink=sink, executor_factory=InlineExecutor)

    result = runner.run(_request(tmp_path))

    assert result.success
    assert result.processed == 0
    assert result.total == 0
    assert any(isinstance(event, ExportFinishedEvent) for event in sink.events)


def test_export_runner_exports_one_png_to_subfolder(tmp_path):
    _source(tmp_path)
    sink = CollectingSink()
    runner = ExportRunner(event_sink=sink, executor_factory=InlineExecutor)

    result = runner.run(_request(tmp_path))

    output = tmp_path / "_SALIDA_PRO" / "source_PRO.png"
    assert result.success
    assert result.processed == 1
    assert result.total == 1
    assert output.exists()
    assert output.parent in result.destinations
    assert any(isinstance(event, ExportProgressEvent) and event.percent == 100 for event in sink.events)
    assert any(isinstance(event, ExportImageCompletedEvent) and event.success for event in sink.events)


def test_export_runner_exports_to_custom_destination(tmp_path):
    _source(tmp_path)
    custom_output = tmp_path / "custom-output"
    config = ExportConfig(
        format="PNG",
        output_width=8,
        output_height=8,
        output_destination="custom",
        custom_output_path=str(custom_output),
    )
    runner = ExportRunner(executor_factory=InlineExecutor)

    result = runner.run(_request(tmp_path, config=config))

    assert result.success
    assert (custom_output / "source_PRO.png").exists()
    assert result.destinations == [custom_output]


def test_export_runner_honors_cancellation_before_rendering(tmp_path):
    _source(tmp_path)
    token = CancellationToken()
    token.cancel()

    def fail_if_called(_args):
        raise AssertionError("render should not run when export is already cancelled")

    runner = ExportRunner(
        cancellation_token=token,
        executor_factory=InlineExecutor,
        image_processor=fail_if_called,
    )

    result = runner.run(_request(tmp_path))

    assert not result.success
    assert result.processed == 0
    assert result.total == 1
    assert not (tmp_path / "_SALIDA_PRO" / "source_PRO.png").exists()


def test_pause_token_blocks_until_resume():
    token = PauseToken()
    reached = threading.Event()
    token.pause()

    thread = threading.Thread(target=lambda: (token.wait_if_paused(), reached.set()))
    thread.start()

    assert not reached.wait(0.05)
    token.resume()
    assert reached.wait(1)
    thread.join(timeout=1)
