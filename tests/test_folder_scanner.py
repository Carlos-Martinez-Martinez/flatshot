from pathlib import Path

from PIL import Image

from flatshot.application.folder_scanner import FolderScanner
from flatshot.core.overrides import override_key


def _png(path: Path) -> Path:
    Image.new("RGBA", (4, 4), (255, 0, 0, 255)).save(path)
    return path


def test_scan_empty_folder_list():
    result = FolderScanner().scan_folders([])

    assert result.folders == []
    assert result.total_folders == 0
    assert result.total_images == 0
    assert result.adjusted_images == 0
    assert result.errors == []


def test_scan_missing_folder_returns_error_without_raising(tmp_path):
    missing = tmp_path / "missing"

    result = FolderScanner().scan_folders([missing])

    assert result.total_folders == 1
    assert result.total_images == 0
    assert result.folders[0].folder == missing
    assert not result.folders[0].exists
    assert result.errors


def test_scan_folder_counts_png_and_ignores_non_png(tmp_path):
    first = _png(tmp_path / "b.png")
    second = _png(tmp_path / "a.png")
    (tmp_path / "notes.txt").write_text("ignore", encoding="utf-8")
    Image.new("RGB", (4, 4)).save(tmp_path / "photo.jpg")

    result = FolderScanner().scan_folders([tmp_path])

    assert result.total_folders == 1
    assert result.total_images == 2
    assert [image.path for image in result.folders[0].images] == [second, first]
    assert [image.name for image in result.folders[0].images] == ["a.png", "b.png"]
    assert all(image.size_bytes > 0 for image in result.folders[0].images)


def test_scan_multiple_folders_accumulates_totals(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    _png(first / "one.png")
    _png(second / "two.png")
    _png(second / "three.png")

    result = FolderScanner().scan_folders([first, second])

    assert result.total_folders == 2
    assert result.total_images == 3
    assert [len(folder.images) for folder in result.folders] == [1, 2]


def test_scan_counts_local_overrides(tmp_path):
    adjusted = _png(tmp_path / "adjusted.png")
    plain = _png(tmp_path / "plain.png")
    overrides = {
        override_key(str(adjusted)): {"size_delta": 4},
        override_key(str(plain)): {"size_delta": 0},
    }

    result = FolderScanner().scan_folders([tmp_path], overrides)

    assert result.total_images == 2
    assert result.adjusted_images == 1
    by_name = {image.name: image for image in result.folders[0].images}
    assert by_name["adjusted.png"].has_local_override
    assert not by_name["plain.png"].has_local_override


def test_scan_path_that_is_not_directory_returns_error(tmp_path):
    source_file = tmp_path / "file.png"
    source_file.write_text("not a folder", encoding="utf-8")

    result = FolderScanner().scan_folders([source_file])

    assert result.total_folders == 1
    assert result.total_images == 0
    assert result.folders[0].exists
    assert not result.folders[0].is_dir
    assert result.errors
