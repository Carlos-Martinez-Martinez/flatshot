import sys
from pathlib import Path

from PIL import Image
from PyQt6.QtCore import QCoreApplication

from flatshot.workers.pre_render_scheduler import PreRenderScheduler


def _app():
    return QCoreApplication.instance() or QCoreApplication(sys.argv[:1])


def _png(path: Path):
    Image.new("RGBA", (8, 8), (200, 50, 50, 255)).save(path)


def _context(folder, **overrides):
    data = {
        "enabled": True,
        "folders": [folder],
        "active_folder": folder,
        "current_image_path": None,
        "settings_dict": {"opacity": 20, "transparent_bg": False},
        "curve_dict": {"xp": [0.0, 1.0], "fp": [1.0, 1.0]},
        "target_size": (1800, 2400),
        "export_format": "JPG",
        "image_overrides": {},
        "idle_ms": 1000,
        "max_cache_bytes": 128 * 1024 * 1024,
    }
    data.update(overrides)
    return data


def test_scheduler_waits_for_idle_before_starting(tmp_path):
    _app()
    folder = tmp_path / "batch"
    folder.mkdir()
    _png(folder / "a.png")

    scheduler = PreRenderScheduler(idle_ms=1000)
    started = []

    def fake_start(job):
        started.append(job)
        scheduler._current_process = object()

    scheduler._start_process = fake_start
    scheduler.update_context(**_context(folder))

    scheduler._try_start()
    assert started == []

    scheduler._last_activity_at -= 2
    scheduler._try_start()
    scheduler._try_start()

    assert len(started) == 1
    scheduler.shutdown()


def test_scheduler_pauses_and_terminates_on_activity(tmp_path):
    _app()
    folder = tmp_path / "batch"
    folder.mkdir()
    _png(folder / "a.png")

    scheduler = PreRenderScheduler(idle_ms=1000)
    statuses = []
    scheduler.status_changed.connect(lambda state, prepared, total: statuses.append((state, prepared, total)))

    scheduler.update_context(**_context(folder))
    scheduler._last_total = 1
    scheduler._current_process = object()
    scheduler._current_job = {"cache_path": str(tmp_path / "cache" / "job.png")}
    scheduled = []
    scheduler.schedule = lambda delay_ms=None: scheduled.append(delay_ms)

    scheduler.note_activity("mouse")

    assert scheduler._current_process is None
    assert statuses[-1][0] == "paused"
    assert scheduled == [None]
    scheduler.shutdown()


def test_scheduler_orders_current_image_then_active_folder_then_rest(tmp_path):
    _app()
    folder_a = tmp_path / "a"
    folder_b = tmp_path / "b"
    folder_a.mkdir()
    folder_b.mkdir()
    current = folder_a / "current.png"
    other_a = folder_a / "other.png"
    active_b = folder_b / "active.png"
    for path in (current, other_a, active_b):
        _png(path)

    scheduler = PreRenderScheduler(idle_ms=1000)
    scheduler.update_context(
        **_context(
            folder_a,
            folders=[folder_a, folder_b],
            active_folder=folder_b,
            current_image_path=current,
        )
    )

    jobs, prepared, total = scheduler._build_jobs()

    assert prepared == 0
    assert total == 3
    assert [Path(job["image_path"]) for job in jobs] == [current, active_b, other_a]
    scheduler.shutdown()


def test_scheduler_does_not_count_incomplete_temp_cache(tmp_path):
    _app()
    folder = tmp_path / "batch"
    folder.mkdir()
    image = folder / "a.png"
    _png(image)

    scheduler = PreRenderScheduler(idle_ms=1000)
    scheduler.cache.cache_dir = tmp_path / "cache"
    scheduler.cache.cache_dir.mkdir()
    scheduler.update_context(**_context(folder))

    jobs, prepared, total = scheduler._build_jobs()
    temp_path = scheduler.cache.get_temp_path(Path(jobs[0]["cache_path"]), "partial")
    temp_path.write_bytes(b"partial")
    jobs_after_temp, prepared_after_temp, total_after_temp = scheduler._build_jobs()

    assert prepared == 0
    assert total == 1
    assert prepared_after_temp == 0
    assert total_after_temp == 1
    assert len(jobs_after_temp) == 1
    scheduler.shutdown()
