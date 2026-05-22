from pathlib import Path

import flatshot.application.queue_runner as queue_runner_module
from flatshot.application.contracts import QueueRunRequest
from flatshot.application.events import (
    ExportImageCompletedEvent,
    ExportLogEvent,
    ExportProgressEvent,
    QueueFinishedEvent,
    QueueJobCompletedEvent,
    QueuePausedEvent,
    QueueResumedEvent,
)
from flatshot.application.execution_control import CancellationToken
from flatshot.application.queue_runner import QueueRunner
from flatshot.core.models import CurveData, ExportConfig, JobItem, ShadowSettings


class CollectingSink:
    def __init__(self):
        self.events = []

    def emit(self, event):
        self.events.append(event)


class CollectingLogger:
    def __init__(self):
        self.calls = []

    def log_queue_start(self, num_jobs: int):
        self.calls.append(("queue_start", num_jobs))

    def log_export_start(self, folder: str, total_images: int, preset_name: str | None = None):
        self.calls.append(("export_start", folder, total_images, preset_name))

    def log_export_complete(self, folder: str, processed: int, total: int, duration_sec: float):
        self.calls.append(("export_complete", folder, processed, total))

    def log_export_cancelled(self, folder: str, processed: int, total: int):
        self.calls.append(("export_cancelled", folder, processed, total))

    def log_queue_complete(self, completed: int, errors: int, total_images: int):
        self.calls.append(("queue_complete", completed, errors, total_images))


class FakeExportRunner:
    def __init__(self, calls, outcomes_by_folder, **kwargs):
        self.calls = calls
        self.outcomes_by_folder = outcomes_by_folder
        self.event_sink = kwargs["event_sink"]

    def run(self, request):
        self.calls.append(request)
        outcomes = self.outcomes_by_folder.get(
            request.input_folder.name,
            [True for _ in request.input_files or []],
        )
        total = len(outcomes)
        self.event_sink.emit(ExportLogEvent(f"running {request.input_folder.name}"))
        for index, success in enumerate(outcomes, start=1):
            self.event_sink.emit(ExportImageCompletedEvent(f"image_{index}.png", success))
            self.event_sink.emit(ExportProgressEvent(index, total, int((index / total) * 100)))


def _curve():
    return CurveData(xp=[0.0, 1.0], fp=[1.0, 1.0])


def _request(jobs):
    return QueueRunRequest(
        jobs=jobs,
        settings=ShadowSettings(opacity=0, blur=0, noise=0),
        export_config=ExportConfig(format="PNG", output_width=8, output_height=8),
        curve_data=_curve(),
        preset_name="Test preset",
    )


def _source(folder: Path, name: str = "source.png"):
    path = folder / name
    path.write_bytes(b"png")
    return path


def _factory(calls, outcomes_by_folder=None):
    outcomes_by_folder = outcomes_by_folder or {}

    def create_runner(**kwargs):
        return FakeExportRunner(calls, outcomes_by_folder, **kwargs)

    return create_runner


def test_queue_runner_does_not_import_pyqt():
    source = queue_runner_module.Path(queue_runner_module.__file__).read_text(encoding="utf-8")

    assert "PyQt6" not in source
    assert "QThread" not in source
    assert "pyqtSignal" not in source


def test_queue_runner_empty_queue_finishes_without_export_runner():
    sink = CollectingSink()
    calls = []
    runner = QueueRunner(export_runner_factory=_factory(calls), event_sink=sink)

    result = runner.run(_request([]))

    assert result.completed_jobs == 0
    assert result.errors == 0
    assert result.total_images == 0
    assert calls == []
    assert any(isinstance(event, QueueFinishedEvent) for event in sink.events)


def test_queue_runner_processes_one_folder(tmp_path):
    folder = tmp_path / "one"
    folder.mkdir()
    _source(folder, "a.png")
    _source(folder, "b.png")
    job = JobItem(folder_path=str(folder))
    sink = CollectingSink()
    logger = CollectingLogger()
    calls = []
    runner = QueueRunner(export_runner_factory=_factory(calls), event_sink=sink, logger=logger)

    result = runner.run(_request([job]))

    assert result.completed_jobs == 1
    assert result.errors == 0
    assert result.total_images == 2
    assert job.status == "completed"
    assert job.total_images == 2
    assert job.processed_images == 2
    assert len(calls) == 1
    assert calls[0].input_folder == folder
    assert len(calls[0].input_files) == 2
    assert ("queue_start", 1) in logger.calls
    assert any(call[0] == "export_complete" and call[2] == 2 for call in logger.calls)


def test_queue_runner_processes_multiple_folders_in_order(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    _source(first)
    _source(second)
    jobs = [JobItem(folder_path=str(first)), JobItem(folder_path=str(second))]
    calls = []
    runner = QueueRunner(export_runner_factory=_factory(calls))

    result = runner.run(_request(jobs))

    assert result.completed_jobs == 2
    assert [call.input_folder for call in calls] == [first, second]
    assert [job.status for job in jobs] == ["completed", "completed"]


def test_queue_runner_completes_empty_folder_inside_queue(tmp_path):
    empty = tmp_path / "empty"
    filled = tmp_path / "filled"
    empty.mkdir()
    filled.mkdir()
    _source(filled)
    jobs = [JobItem(folder_path=str(empty)), JobItem(folder_path=str(filled))]
    sink = CollectingSink()
    calls = []
    runner = QueueRunner(export_runner_factory=_factory(calls), event_sink=sink)

    result = runner.run(_request(jobs))

    assert result.completed_jobs == 2
    assert jobs[0].status == "completed"
    assert jobs[0].total_images == 0
    assert jobs[0].progress == 100
    assert [call.input_folder for call in calls] == [filled]


def test_queue_runner_marks_folder_error_when_image_fails(tmp_path):
    folder = tmp_path / "bad"
    folder.mkdir()
    _source(folder, "a.png")
    _source(folder, "b.png")
    job = JobItem(folder_path=str(folder))
    sink = CollectingSink()
    calls = []
    runner = QueueRunner(
        export_runner_factory=_factory(calls, {"bad": [True, False]}),
        event_sink=sink,
    )

    result = runner.run(_request([job]))

    assert result.completed_jobs == 0
    assert result.errors == 1
    assert result.total_images == 1
    assert job.status == "error"
    assert job.processed_images == 1
    assert job.error_message == "Procesadas OK: 1 / Errores: 1 / Total: 2"
    completed_events = [event for event in sink.events if isinstance(event, QueueJobCompletedEvent)]
    assert completed_events[-1].success is False


def test_queue_runner_cancellation_before_run_marks_jobs_cancelled(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    _source(first)
    _source(second)
    jobs = [JobItem(folder_path=str(first)), JobItem(folder_path=str(second))]
    token = CancellationToken()
    token.cancel()
    calls = []
    runner = QueueRunner(export_runner_factory=_factory(calls), cancellation_token=token)

    result = runner.run(_request(jobs))

    assert result.cancelled
    assert result.completed_jobs == 0
    assert calls == []
    assert [job.status for job in jobs] == ["cancelled", "cancelled"]


def test_queue_runner_pause_resume_events():
    sink = CollectingSink()
    runner = QueueRunner(event_sink=sink)

    runner.pause()
    assert runner.pause_token.paused
    runner.resume()

    assert not runner.pause_token.paused
    assert any(isinstance(event, QueuePausedEvent) for event in sink.events)
    assert any(isinstance(event, QueueResumedEvent) for event in sink.events)
