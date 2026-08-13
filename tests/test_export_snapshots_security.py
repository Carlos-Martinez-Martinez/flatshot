from types import SimpleNamespace

from flatshot.application.export_snapshots import source_image_items


def test_source_image_items_rejects_symlinked_png(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    link = source / "linked.png"
    link.write_bytes(b"png")
    path_type = type(link)
    original_is_symlink = path_type.is_symlink
    monkeypatch.setattr(path_type, "is_symlink", lambda path: path == link or original_is_symlink(path))

    request = SimpleNamespace(input_files=None, input_folder=source)

    assert source_image_items(request) == []


def test_source_image_items_keeps_regular_top_level_png(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    image = source / "item.png"
    image.write_bytes(b"png")
    request = SimpleNamespace(input_files=None, input_folder=source)

    assert source_image_items(request) == [(image, str(image.resolve()), image)]
