import shutil
from pathlib import Path

from PIL import Image

from flatshot.application.contracts import ExportJobRequest
from flatshot.application.export_runner import ExportRunner
from flatshot.core.models import CurveData, ExportConfig, ShadowSettings
from flatshot.utils.render_cache import RenderCache
from tests.helpers import InlineExecutor


def _use_isolated_cache(monkeypatch, cache_dir):
    def init(self):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(RenderCache, "__init__", init)


def _curve():
    return CurveData(xp=[0.0, 1.0], fp=[1.0, 1.0])


def _source(folder):
    source = folder / "source.png"
    Image.new("RGBA", (8, 8), (120, 80, 40, 255)).save(source)
    return source


def _cache_key(source, settings, config, curve):
    settings.transparent_bg = config.transparent_bg
    settings.bg_color = config.bg_color
    return RenderCache().get_cache_key(
        str(source),
        settings.model_dump(),
        curve.model_dump(),
        (config.output_width, config.output_height),
        {},
        config.format,
    )


def test_export_uses_valid_export_ready_cache(monkeypatch, tmp_path):
    _use_isolated_cache(monkeypatch, tmp_path / "cache")
    source = _source(tmp_path)
    settings = ShadowSettings(opacity=0, blur=0, noise=0)
    config = ExportConfig(format="PNG", output_width=8, output_height=8)
    curve = _curve()
    key = _cache_key(source, settings, config, curve)
    cache_path = RenderCache().get_cached_path(key, "png")
    Image.new("RGBA", (8, 8), (1, 2, 3, 255)).save(cache_path)

    def fail_process(_args):
        raise AssertionError("normal render should not run for valid cache")

    runner = ExportRunner(executor_factory=InlineExecutor, image_processor=fail_process)
    runner.run(
        ExportJobRequest(
            input_folder=tmp_path,
            settings=settings,
            export_config=config,
            curve_data=curve,
        )
    )

    output = tmp_path / "_SALIDA_PRO" / "source_PRO.png"
    assert output.exists()
    with Image.open(output) as img:
        assert img.getpixel((0, 0)) == (1, 2, 3, 255)


def test_export_falls_back_to_normal_render_when_cache_copy_fails(monkeypatch, tmp_path):
    _use_isolated_cache(monkeypatch, tmp_path / "cache")
    source = _source(tmp_path)
    settings = ShadowSettings(opacity=0, blur=0, noise=0)
    config = ExportConfig(format="PNG", output_width=8, output_height=8)
    curve = _curve()
    key = _cache_key(source, settings, config, curve)
    cache_path = RenderCache().get_cached_path(key, "png")
    Image.new("RGBA", (8, 8), (1, 2, 3, 255)).save(cache_path)

    def fail_copy(_src, _dest):
        raise OSError("copy failed")

    def fake_process(args):
        img_path, save_path, _settings, _target_size, _fmt, _curve, _override, _display_name = args
        Image.new("RGBA", (8, 8), (4, 5, 6, 255)).save(save_path)
        return True, img_path.name, None

    runner = ExportRunner(executor_factory=InlineExecutor, image_processor=fake_process, copy_file=fail_copy)
    runner.run(
        ExportJobRequest(
            input_folder=tmp_path,
            settings=settings,
            export_config=config,
            curve_data=curve,
        )
    )

    output = tmp_path / "_SALIDA_PRO" / "source_PRO.png"
    assert output.exists()
    with Image.open(output) as img:
        assert img.getpixel((0, 0)) == (4, 5, 6, 255)


def test_cache_copy_failure_after_partial_write_does_not_block_fallback_render(monkeypatch, tmp_path):
    _use_isolated_cache(monkeypatch, tmp_path / "cache")
    source = _source(tmp_path)
    settings = ShadowSettings(opacity=0, blur=0, noise=0)
    config = ExportConfig(format="PNG", output_width=8, output_height=8)
    curve = _curve()
    key = _cache_key(source, settings, config, curve)
    cache_path = RenderCache().get_cached_path(key, "png")
    Image.new("RGBA", (8, 8), (1, 2, 3, 255)).save(cache_path)
    output = tmp_path / "_SALIDA_PRO" / "source_PRO.png"

    def partial_copy(src, dest):
        dest = Path(dest)
        if dest.parent == output.parent:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(b"partial")
            raise OSError("cache copy interrupted")
        return shutil.copy2(src, dest)

    def fake_process(args):
        _img_path, save_path, _settings, _target_size, _fmt, _curve, _override, _display_name = args
        if Path(save_path).exists():
            return False, "source.png: already exists", None
        Image.new("RGBA", (8, 8), (4, 5, 6, 255)).save(save_path)
        return True, "source.png", None

    result = ExportRunner(
        executor_factory=InlineExecutor,
        image_processor=fake_process,
        copy_file=partial_copy,
    ).run(
        ExportJobRequest(
            input_folder=tmp_path,
            settings=settings,
            export_config=config,
            curve_data=curve,
        )
    )

    assert result.success
    with Image.open(output) as img:
        assert img.getpixel((0, 0)) == (4, 5, 6, 255)


def test_cache_hit_refuses_destination_created_after_preflight(monkeypatch, tmp_path):
    _use_isolated_cache(monkeypatch, tmp_path / "cache")
    source = _source(tmp_path)
    settings = ShadowSettings(opacity=0, blur=0, noise=0)
    config = ExportConfig(format="PNG", output_width=8, output_height=8)
    curve = _curve()
    key = _cache_key(source, settings, config, curve)
    cache_path = RenderCache().get_cached_path(key, "png")
    Image.new("RGBA", (8, 8), (1, 2, 3, 255)).save(cache_path)
    output = tmp_path / "_SALIDA_PRO" / "source_PRO.png"

    def concurrent_copy(src, dest):
        dest = Path(dest)
        result = shutil.copy2(src, dest)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"sentinel")
        return result

    result = ExportRunner(
        executor_factory=InlineExecutor,
        copy_file=concurrent_copy,
    ).run(
        ExportJobRequest(
            input_folder=tmp_path,
            settings=settings,
            export_config=config,
            curve_data=curve,
        )
    )

    assert not result.success
    assert output.read_bytes() == b"sentinel"
