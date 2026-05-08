from PIL import Image

from flatshot.utils.render_cache import RenderCache


def test_render_cache_key_changes_with_local_override(tmp_path):
    source = tmp_path / "source.png"
    Image.new("RGBA", (8, 8), (255, 0, 0, 255)).save(source)

    cache = RenderCache()
    settings = {"opacity": 20}
    curve = {"xp": [0.0, 1.0], "fp": [1.0, 1.0]}

    base_key = cache.get_cache_key(str(source), settings, curve, (1800, 2400))
    override_key = cache.get_cache_key(
        str(source),
        settings,
        curve,
        (1800, 2400),
        {"size_delta": 10},
    )

    assert base_key != override_key


def test_render_cache_key_changes_when_source_changes(tmp_path):
    source = tmp_path / "source.png"
    Image.new("RGBA", (8, 8), (255, 0, 0, 255)).save(source)

    cache = RenderCache()
    settings = {"opacity": 20}
    curve = {"xp": [0.0, 1.0], "fp": [1.0, 1.0]}

    before_key = cache.get_cache_key(str(source), settings, curve, (1800, 2400))

    Image.new("RGBA", (9, 9), (0, 255, 0, 255)).save(source)
    after_key = cache.get_cache_key(str(source), settings, curve, (1800, 2400))

    assert before_key != after_key


def test_render_cache_key_changes_with_format_size_settings_curve_and_override(tmp_path):
    source = tmp_path / "source.png"
    Image.new("RGBA", (8, 8), (255, 0, 0, 255)).save(source)

    cache = RenderCache()
    settings = {"opacity": 20, "transparent_bg": False}
    curve = {"xp": [0.0, 1.0], "fp": [1.0, 1.0]}

    base_key = cache.get_cache_key(str(source), settings, curve, (1800, 2400), {}, "jpg")

    assert base_key != cache.get_cache_key(str(source), settings, curve, (1800, 2400), {}, "png")
    assert base_key != cache.get_cache_key(str(source), settings, curve, (1200, 1600), {}, "jpg")
    assert base_key != cache.get_cache_key(str(source), {"opacity": 30}, curve, (1800, 2400), {}, "jpg")
    assert base_key != cache.get_cache_key(
        str(source),
        settings,
        {"xp": [0.0, 1.0], "fp": [0.9, 1.0]},
        (1800, 2400),
        {},
        "jpg",
    )
    assert base_key != cache.get_cache_key(
        str(source),
        settings,
        curve,
        (1800, 2400),
        {"size_delta": 5},
        "jpg",
    )


def test_render_cache_validate_rejects_corrupt_files_and_temp_sidecars(tmp_path):
    cache = RenderCache()
    cache.cache_dir = tmp_path / "cache"
    cache.cache_dir.mkdir()

    key = "abc123"
    cache_path = cache.get_cached_path(key, "png")
    temp_path = cache.get_temp_path(cache_path, "job")
    temp_path.write_bytes(b"partial")

    assert not cache.exists(key, "png")

    cache_path.write_bytes(b"not an image")

    assert cache.exists(key, "png")
    assert not cache.exists(key, "png", validate=True)


def test_render_cache_prune_removes_oldest_files_and_temp_sidecars(tmp_path):
    cache = RenderCache()
    cache.cache_dir = tmp_path / "cache"
    cache.cache_dir.mkdir()

    old_file = cache.cache_dir / "old.png"
    new_file = cache.cache_dir / "new.png"
    temp_file = cache.cache_dir / ".new.png.job.tmp"
    old_file.write_bytes(b"old")
    new_file.write_bytes(b"new")
    temp_file.write_bytes(b"partial")

    old_time = 1_700_000_000
    new_time = old_time + 10
    import os

    os.utime(old_file, (old_time, old_time))
    os.utime(new_file, (new_time, new_time))

    cache.prune(max_files=1, max_bytes=None)

    assert not old_file.exists()
    assert new_file.exists()
    assert not temp_file.exists()
