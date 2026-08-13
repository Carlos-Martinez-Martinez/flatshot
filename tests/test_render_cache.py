import os
from pathlib import Path

from PIL import Image
import pytest

from flatshot.utils.render_cache import RenderCache


def test_render_cache_uses_configured_portable_cache_dir(tmp_path, monkeypatch):
    cache_dir = tmp_path / "portable" / "render_cache"
    monkeypatch.setenv(RenderCache.CACHE_DIR_ENV_VAR, str(cache_dir))

    cache = RenderCache()

    assert cache.cache_dir == cache_dir
    assert cache.cache_dir.exists()
    assert (cache.cache_dir / RenderCache.OWNER_MARKER).is_file()


def test_render_cache_rejects_configured_directory_with_unrelated_files(tmp_path, monkeypatch):
    cache_dir = tmp_path / "shared"
    cache_dir.mkdir()
    unrelated = cache_dir / "notes.tmp"
    unrelated.write_text("keep", encoding="utf-8")
    monkeypatch.setenv(RenderCache.CACHE_DIR_ENV_VAR, str(cache_dir))

    with pytest.raises(ValueError, match="dedicated FlatShot cache"):
        RenderCache()

    assert unrelated.read_text(encoding="utf-8") == "keep"


def test_render_cache_rejects_invalid_owner_marker(tmp_path, monkeypatch):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    marker = cache_dir / RenderCache.OWNER_MARKER
    marker.write_text("not-flatshot\n", encoding="utf-8")
    monkeypatch.setenv(RenderCache.CACHE_DIR_ENV_VAR, str(cache_dir))

    with pytest.raises(ValueError, match="dedicated FlatShot cache"):
        RenderCache()

    assert marker.read_text(encoding="utf-8") == "not-flatshot\n"


def test_render_cache_rejects_owner_marker_symlink_without_touching_target(tmp_path, monkeypatch):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    target = tmp_path / "outside.txt"
    target.write_text("keep", encoding="utf-8")
    marker = cache_dir / RenderCache.OWNER_MARKER
    try:
        marker.symlink_to(target)
    except OSError as exc:
        pytest.skip(f"Symlinks are unavailable: {exc}")
    monkeypatch.setenv(RenderCache.CACHE_DIR_ENV_VAR, str(cache_dir))

    with pytest.raises(ValueError, match="dedicated FlatShot cache"):
        RenderCache()

    assert target.read_text(encoding="utf-8") == "keep"


def test_render_cache_publishes_only_a_complete_owner_marker(tmp_path, monkeypatch):
    cache_dir = tmp_path / "cache"
    marker = cache_dir / RenderCache.OWNER_MARKER
    original_replace = os.replace
    observed_content = []

    def inspect_replace(source, destination):
        observed_content.append(Path(source).read_text(encoding="utf-8"))
        original_replace(source, destination)

    monkeypatch.setenv(RenderCache.CACHE_DIR_ENV_VAR, str(cache_dir))
    monkeypatch.setattr("flatshot.utils.render_cache.os.replace", inspect_replace)

    RenderCache()

    assert observed_content == [RenderCache.OWNER_MARKER_CONTENT]
    assert marker.read_text(encoding="utf-8") == RenderCache.OWNER_MARKER_CONTENT


def test_render_cache_cleanup_never_deletes_generic_temp_files(tmp_path, monkeypatch):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    (cache_dir / RenderCache.OWNER_MARKER).write_text("flatshot-render-cache-v1\n", encoding="utf-8")
    unrelated = cache_dir / "notes.tmp"
    unrelated.write_text("keep", encoding="utf-8")
    sidecar = cache_dir / f".{('a' * 64)}.png.job.tmp"
    sidecar.write_bytes(b"partial")
    monkeypatch.setenv(RenderCache.CACHE_DIR_ENV_VAR, str(cache_dir))

    RenderCache()

    assert unrelated.read_text(encoding="utf-8") == "keep"
    assert not sidecar.exists()


def test_render_cache_version_tracks_export_quality_pipeline():
    assert RenderCache.CACHE_VERSION >= 5


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


def test_render_cache_key_changes_when_content_changes_with_same_size_and_mtime(tmp_path):
    source = tmp_path / "source.bin"
    source.write_bytes(b"A" * 32)
    fixed_ns = 1_700_000_000_000_000_000
    import os

    os.utime(source, ns=(fixed_ns, fixed_ns))
    cache = RenderCache()
    settings = {"opacity": 20}
    curve = {"xp": [0.0, 1.0], "fp": [1.0, 1.0]}

    before_key = cache.get_cache_key(str(source), settings, curve, (1800, 2400))
    source.write_bytes(b"B" * 32)
    os.utime(source, ns=(fixed_ns, fixed_ns))
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


def test_render_cache_key_changes_with_jpg_size_limit(tmp_path):
    source = tmp_path / "source.png"
    Image.new("RGBA", (8, 8), (255, 0, 0, 255)).save(source)

    cache = RenderCache()
    settings = {"opacity": 20, "transparent_bg": False}
    curve = {"xp": [0.0, 1.0], "fp": [1.0, 1.0]}

    base_key = cache.get_cache_key(str(source), settings, curve, (1800, 2400), {}, "jpg")
    limited_key = cache.get_cache_key(
        str(source),
        settings,
        curve,
        (1800, 2400),
        {},
        "jpg",
        export_options={"max_file_size_kb": 120},
    )

    assert base_key != limited_key


def test_render_cache_key_changes_with_export_variant_background_and_opacity(tmp_path):
    source = tmp_path / "source.png"
    Image.new("RGBA", (8, 8), (255, 0, 0, 255)).save(source)

    cache = RenderCache()
    curve = {"xp": [0.0, 1.0], "fp": [1.0, 1.0]}
    rgb230 = {"opacity": 20, "transparent_bg": False, "bg_color": (230, 230, 230)}
    rgb255 = {"opacity": 20, "transparent_bg": False, "bg_color": (255, 255, 255)}
    rgb255_shadow = {"opacity": 15, "transparent_bg": False, "bg_color": (255, 255, 255)}

    key_rgb230 = cache.get_cache_key(str(source), rgb230, curve, (1800, 2400), {}, "jpg")

    key_rgb255 = cache.get_cache_key(str(source), rgb255, curve, (1800, 2400), {}, "jpg")
    key_rgb255_shadow = cache.get_cache_key(str(source), rgb255_shadow, curve, (1800, 2400), {}, "jpg")

    assert key_rgb230 != key_rgb255
    assert key_rgb255 != key_rgb255_shadow


def test_render_cache_key_changes_with_lighting_scene(tmp_path):
    source = tmp_path / "source.png"
    Image.new("RGBA", (8, 8), (255, 0, 0, 255)).save(source)

    cache = RenderCache()
    curve = {"xp": [0.0, 1.0], "fp": [1.0, 1.0]}
    base_scene = {
        "main": {
            "type": "softbox",
            "x": -0.25,
            "y": -0.65,
            "height": 0.65,
            "size": 0.55,
            "intensity": 0.85,
        },
        "ambient_intensity": 0.25,
    }
    moved_scene = {
        **base_scene,
        "main": {**base_scene["main"], "x": 0.45},
    }
    softbox_settings = {"shadow_engine": "studio_2_5d", "lighting_scene": base_scene}
    moved_settings = {"shadow_engine": "studio_2_5d", "lighting_scene": moved_scene}
    spot_settings = {
        "shadow_engine": "studio_2_5d",
        "lighting_scene": {**base_scene, "main": {**base_scene["main"], "type": "spot"}},
    }

    key_softbox = cache.get_cache_key(str(source), softbox_settings, curve, (1800, 2400), {}, "jpg")

    assert key_softbox != cache.get_cache_key(str(source), moved_settings, curve, (1800, 2400), {}, "jpg")
    assert key_softbox != cache.get_cache_key(str(source), spot_settings, curve, (1800, 2400), {}, "jpg")


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

    old_file = cache.cache_dir / f"{('a' * 64)}.png"
    new_file = cache.cache_dir / f"{('b' * 64)}.png"
    temp_file = cache.cache_dir / f".{('c' * 64)}.png.job.tmp"
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
