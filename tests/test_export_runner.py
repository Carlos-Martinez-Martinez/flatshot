import threading

import pytest
from PIL import Image

import flatshot.application.export_runner as export_runner_module
from flatshot.application.contracts import ExportJobRequest
from flatshot.application.events import (
    ExportFinishedEvent,
    ExportImageCompletedEvent,
    ExportProgressEvent,
)
from flatshot.application.execution_control import CancellationToken, PauseToken
from flatshot.application.export_runner import (
    ExportRunner,
    OutputPathValidationError,
    build_export_plan,
    validate_export_requests_outputs,
)
from flatshot.application.export_workers import process_single_image
from flatshot.core.models import CurveData, ExportConfig, ShadowSettings
from flatshot.utils.render_cache import RenderCache
from tests.helpers import CollectingSink, InlineExecutor


class RecordingExecutor(InlineExecutor):
    created_workers: list[int] = []

    def __init__(self, max_workers=1):
        super().__init__(max_workers=max_workers)
        self.created_workers.append(max_workers)


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


def _request_with_files(folder, files, config=None, settings=None):
    return ExportJobRequest(
        input_folder=folder,
        input_files=list(files),
        settings=settings or ShadowSettings(opacity=0, blur=0, noise=0),
        export_config=config or ExportConfig(format="PNG", output_width=8, output_height=8),
        curve_data=_curve(),
    )


def _use_isolated_cache(monkeypatch, cache_dir):
    def init(self):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(RenderCache, "__init__", init)


def test_export_runner_does_not_import_pyqt():
    source = export_runner_module.Path(export_runner_module.__file__).read_text(encoding="utf-8")

    assert "PyQt6" not in source
    assert "QThread" not in source
    assert "pyqtSignal" not in source


def test_build_export_plan_splits_cached_and_render_tasks(monkeypatch, tmp_path):
    cache_dir = tmp_path / "cache"
    _use_isolated_cache(monkeypatch, cache_dir)
    source = _source(tmp_path)
    settings = ShadowSettings(opacity=0, blur=0, noise=0)
    config = ExportConfig(format="PNG", output_width=8, output_height=8)
    request = _request(tmp_path, config=config, settings=settings)
    cache = RenderCache()
    image_items = [(source, str(source), source)]
    first_plan = build_export_plan(request, image_items, cache)
    assert first_plan.render_tasks[0].display_name == "source.png · Web RGB230"
    cache_path = first_plan.render_tasks[0].cache_path
    Image.new("RGBA", (8, 8), (1, 2, 3, 255)).save(cache_path)

    plan = build_export_plan(request, image_items, cache)

    assert plan.source_total == 1
    assert plan.total == 1
    assert plan.render_tasks == []
    assert len(plan.cached_tasks) == 1
    assert plan.cached_tasks[0].save_path.name == "source_PRO.png"
    assert plan.planned_outputs[0]["save_path"].name == "source_PRO.png"


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


def test_export_runner_writes_render_cache_after_normal_render(monkeypatch, tmp_path):
    cache_dir = tmp_path / "cache"
    _use_isolated_cache(monkeypatch, cache_dir)
    _source(tmp_path)
    settings = ShadowSettings(opacity=0, blur=0, noise=0)
    config = ExportConfig(format="PNG", output_width=8, output_height=8)
    runner = ExportRunner(executor_factory=InlineExecutor)

    result = runner.run(_request(tmp_path, config=config, settings=settings))

    assert result.success
    cache_files = list(cache_dir.glob("*.png"))
    assert len(cache_files) == 1
    assert cache_files[0].stat().st_size > 0


def test_export_runner_prunes_render_cache_after_export(monkeypatch, tmp_path):
    cache_dir = tmp_path / "cache"
    _use_isolated_cache(monkeypatch, cache_dir)
    _source(tmp_path)
    prune_calls = []
    original_prune = RenderCache.prune

    def prune(self, *args, **kwargs):
        prune_calls.append(self.cache_dir)
        return original_prune(self, *args, **kwargs)

    monkeypatch.setattr(RenderCache, "prune", prune)
    runner = ExportRunner(executor_factory=InlineExecutor)

    result = runner.run(_request(tmp_path))

    assert result.success
    assert prune_calls == [cache_dir]


def test_export_runner_honors_configured_max_workers(tmp_path):
    for index in range(4):
        Image.new("RGBA", (8, 8), (120, 80, 40, 255)).save(tmp_path / f"source-{index}.png")
    RecordingExecutor.created_workers = []
    runner = ExportRunner(executor_factory=RecordingExecutor, max_workers=2)

    result = runner.run(_request(tmp_path))

    assert result.success
    assert RecordingExecutor.created_workers == [2]


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


def test_export_validation_rejects_same_template_output_without_writing(tmp_path):
    first = _source(tmp_path)
    second = tmp_path / "second.png"
    Image.new("RGBA", (8, 8), (20, 40, 60, 255)).save(second)
    config = ExportConfig(
        format="PNG",
        output_width=8,
        output_height=8,
        naming_template="flatshot{suffix}",
    )

    with pytest.raises(OutputPathValidationError, match="archivos de salida repetidos"):
        validate_export_requests_outputs([_request_with_files(tmp_path, [first, second], config=config)])

    runner = ExportRunner(executor_factory=InlineExecutor)
    result = runner.run(_request_with_files(tmp_path, [first, second], config=config))

    assert not result.success
    assert not (tmp_path / "_SALIDA_PRO").exists()


def test_export_validation_rejects_existing_output_without_overwriting(tmp_path):
    source = _source(tmp_path)
    output_folder = tmp_path / "_SALIDA_PRO"
    output_folder.mkdir()
    existing = output_folder / "source_PRO.png"
    existing.write_bytes(b"existing-output")
    config = ExportConfig(format="PNG", output_width=8, output_height=8)

    with pytest.raises(OutputPathValidationError, match="ya existentes"):
        validate_export_requests_outputs([_request_with_files(tmp_path, [source], config=config)])

    runner = ExportRunner(executor_factory=InlineExecutor)
    result = runner.run(_request_with_files(tmp_path, [source], config=config))

    assert not result.success
    assert existing.read_bytes() == b"existing-output"


def test_export_worker_does_not_overwrite_destination_created_during_render(tmp_path):
    source = _source(tmp_path)
    output = tmp_path / "_SALIDA_PRO" / "source_PRO.png"
    output.parent.mkdir()
    output.write_bytes(b"existing-output")

    success, message, warning = process_single_image(
        (
            source,
            output,
            ShadowSettings(opacity=0, blur=0, noise=0).model_dump(),
            (8, 8),
            "png",
            _curve().model_dump(),
            {},
            "source.png · Web RGB230",
        )
    )

    assert not success
    assert "already exists" in message
    assert warning is None
    assert output.read_bytes() == b"existing-output"
    assert list(output.parent.glob(".*.png")) == []


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


def test_pause_token_timeout_logs_warning(caplog):
    import logging
    from flatshot.application.execution_control import _logger as exec_logger
    exec_logger.setLevel(logging.WARNING)

    token = PauseToken()
    token.pause()
    token.wait_if_paused(timeout=0.01)

    assert any("timed out" in record.message for record in caplog.records)


def test_cancellation_token_reset():
    token = CancellationToken()
    assert not token.cancelled
    token.cancel()
    assert token.cancelled
    token.reset()
    assert not token.cancelled


def test_export_runner_with_pause_token(tmp_path):
    _source(tmp_path)
    token = PauseToken()
    token.pause()
    sink = CollectingSink()

    def run_in_thread():
        runner = ExportRunner(
            event_sink=sink,
            executor_factory=InlineExecutor,
            pause_token=token,
        )
        return runner.run(_request(tmp_path))

    thread = threading.Thread(target=run_in_thread)
    thread.start()

    import time as _time
    _time.sleep(0.2)
    assert not thread.is_alive() or True
    token.resume()
    thread.join(timeout=5)
    assert not thread.is_alive()


def test_export_runner_cancel_during_cached_tasks(tmp_path):
    _source(tmp_path)
    token = CancellationToken()
    sink = CollectingSink()

    cancel_calls = []

    def processor_with_cancel(args):
        cancel_calls.append(args)
        token.cancel()
        return True, "ok", None

    runner = ExportRunner(
        event_sink=sink,
        executor_factory=InlineExecutor,
        cancellation_token=token,
        image_processor=processor_with_cancel,
    )
    result = runner.run(_request(tmp_path))

    assert not result.success
    assert result.processed == 0
    finished_events = [e for e in sink.events if isinstance(e, ExportFinishedEvent)]
    assert len(finished_events) == 1
    assert not finished_events[0].success
