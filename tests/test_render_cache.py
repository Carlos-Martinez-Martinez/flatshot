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
