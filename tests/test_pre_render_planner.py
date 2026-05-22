from pathlib import Path

from PIL import Image

import flatshot.application.pre_render_planner as pre_render_planner_module
from flatshot.application.pre_render_planner import (
    build_pre_render_context_signature,
    build_pre_render_jobs,
    ordered_pre_render_candidates,
)
from flatshot.core.overrides import override_key
from flatshot.utils.render_cache import RenderCache


def _png(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", (8, 8), (200, 50, 50, 255)).save(path)


def _cache(tmp_path):
    cache = RenderCache()
    cache.cache_dir = tmp_path / "cache"
    cache.cache_dir.mkdir()
    return cache


def test_pre_render_planner_does_not_import_pyqt():
    source = pre_render_planner_module.Path(pre_render_planner_module.__file__).read_text(encoding="utf-8")

    assert "PyQt6" not in source
    assert "QTimer" not in source
    assert "QObject" not in source


def test_context_signature_is_stable_and_changes_with_current_image(tmp_path):
    folder = tmp_path / "batch"
    current = folder / "a.png"

    base = dict(
        folders=[folder],
        active_folder=folder,
        current_image_path=current,
        settings_dict={"opacity": 20, "blur": 30},
        curve_dict={"fp": [1.0, 1.0], "xp": [0.0, 1.0]},
        target_size=(1800, 2400),
        export_format="jpg",
        image_overrides={},
    )

    first = build_pre_render_context_signature(**base)
    second = build_pre_render_context_signature(**base)
    changed = build_pre_render_context_signature(**{**base, "current_image_path": folder / "b.png"})

    assert first == second
    assert changed != first


def test_ordered_candidates_put_current_image_then_active_folder_then_rest(tmp_path):
    folder_a = tmp_path / "a"
    folder_b = tmp_path / "b"
    current = folder_a / "current.png"
    other_a = folder_a / "other.png"
    active_b = folder_b / "active.png"
    ignored = folder_b / "ignored.txt"
    for path in (current, other_a, active_b):
        _png(path)
    ignored.write_text("ignored", encoding="utf-8")

    candidates = ordered_pre_render_candidates(
        folders=[folder_a, folder_b],
        active_folder=folder_b,
        current_image_path=current,
    )

    assert candidates == [current, active_b, other_a]


def test_build_jobs_counts_cached_outputs_and_preserves_local_overrides(tmp_path):
    folder = tmp_path / "batch"
    first = folder / "a.png"
    second = folder / "b.png"
    _png(first)
    _png(second)
    cache = _cache(tmp_path)
    settings = {"opacity": 20, "transparent_bg": False}
    override = {"size_delta": 5}
    overrides = {override_key(first): override}

    jobs, prepared, total = build_pre_render_jobs(
        candidates=[first, second],
        cache=cache,
        settings_dict=settings,
        curve_dict=None,
        target_size=(1800, 2400),
        export_format="jpg",
        image_overrides=overrides,
    )
    Path(jobs[0]["cache_path"]).write_bytes(b"cached")
    jobs_after_cache, prepared_after_cache, total_after_cache = build_pre_render_jobs(
        candidates=[first, second],
        cache=cache,
        settings_dict=settings,
        curve_dict=None,
        target_size=(1800, 2400),
        export_format="jpg",
        image_overrides=overrides,
    )

    assert prepared == 0
    assert total == 2
    assert jobs[0]["local_override"] == override
    assert prepared_after_cache == 1
    assert total_after_cache == 2
    assert len(jobs_after_cache) == 1
    assert Path(jobs_after_cache[0]["image_path"]) == second


def test_build_jobs_ignores_incomplete_temp_cache_files(tmp_path):
    folder = tmp_path / "batch"
    image = folder / "a.png"
    _png(image)
    cache = _cache(tmp_path)

    jobs, prepared, total = build_pre_render_jobs(
        candidates=[image],
        cache=cache,
        settings_dict={"opacity": 20},
        curve_dict=None,
        target_size=(1800, 2400),
        export_format="jpg",
        image_overrides={},
    )
    temp_path = cache.get_temp_path(Path(jobs[0]["cache_path"]), "partial")
    temp_path.write_bytes(b"partial")
    jobs_after_temp, prepared_after_temp, total_after_temp = build_pre_render_jobs(
        candidates=[image],
        cache=cache,
        settings_dict={"opacity": 20},
        curve_dict=None,
        target_size=(1800, 2400),
        export_format="jpg",
        image_overrides={},
    )

    assert prepared == 0
    assert total == 1
    assert prepared_after_temp == 0
    assert total_after_temp == 1
    assert len(jobs_after_temp) == 1
