from pathlib import Path

from PIL import Image

from flatshot.core.models import ShadowSettings
from flatshot.workers import pre_render_process


def _source(path: Path):
    Image.new("RGBA", (8, 8), (100, 120, 140, 255)).save(path)


def _job(source, cache_path, fmt="JPG"):
    return {
        "key": "cache-key",
        "image_path": str(source),
        "settings_dict": ShadowSettings(opacity=0, blur=0, noise=0).model_dump(),
        "curve_dict": None,
        "target_size": (6, 7),
        "cache_path": str(cache_path),
        "local_override": {},
        "format": fmt,
    }


def test_pre_render_process_writes_export_format_with_atomic_replace(monkeypatch, tmp_path):
    source = tmp_path / "source.png"
    cache_path = tmp_path / "cache.jpg"
    _source(source)
    replaced = []
    real_replace = pre_render_process.os.replace

    def fake_low_priority():
        return None

    def fake_render(_original, _settings, target_size, **_kwargs):
        return Image.new("RGBA", target_size, (10, 20, 30, 128)), object()

    def fake_replace(src, dst):
        replaced.append((Path(src), Path(dst)))
        real_replace(src, dst)

    monkeypatch.setattr(pre_render_process, "_set_low_priority", fake_low_priority)
    monkeypatch.setattr(pre_render_process.ShadowEngine, "_aplicar_efectos_with_diagnostics", fake_render)
    monkeypatch.setattr(pre_render_process.os, "replace", fake_replace)

    success, key, message = pre_render_process.render_pre_render_job(_job(source, cache_path, "JPG"))

    assert success, message
    assert key == "cache-key"
    assert replaced
    assert replaced[0][0].name.startswith(".cache.jpg.")
    assert replaced[0][0].suffix == ".tmp"
    assert replaced[0][1] == cache_path
    assert not list(tmp_path.glob("*.tmp"))
    with Image.open(cache_path) as img:
        assert img.format == "JPEG"
        assert img.mode == "RGB"
        assert img.size == (6, 7)


def test_pre_render_process_removes_temp_file_when_atomic_replace_fails(monkeypatch, tmp_path):
    source = tmp_path / "source.png"
    cache_path = tmp_path / "cache.png"
    _source(source)

    def fake_low_priority():
        return None

    def fake_render(_original, _settings, target_size, **_kwargs):
        return Image.new("RGBA", target_size, (10, 20, 30, 128)), object()

    def fail_replace(_src, _dst):
        raise OSError("replace failed")

    monkeypatch.setattr(pre_render_process, "_set_low_priority", fake_low_priority)
    monkeypatch.setattr(pre_render_process.ShadowEngine, "_aplicar_efectos_with_diagnostics", fake_render)
    monkeypatch.setattr(pre_render_process.os, "replace", fail_replace)

    success, key, message = pre_render_process.render_pre_render_job(_job(source, cache_path, "PNG"))

    assert not success
    assert key == "cache-key"
    assert "replace failed" in message
    assert not cache_path.exists()
    assert not list(tmp_path.glob("*.tmp"))
    assert not list(tmp_path.glob(".*.tmp"))
