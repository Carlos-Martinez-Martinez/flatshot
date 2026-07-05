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
    upper = _png(tmp_path / "c.PNG")
    (tmp_path / "notes.txt").write_text("ignore", encoding="utf-8")
    Image.new("RGB", (4, 4)).save(tmp_path / "photo.jpg")

    result = FolderScanner().scan_folders([tmp_path])

    assert result.total_folders == 1
    assert result.total_files == 5
    assert result.total_images == 3
    assert result.total_omitted == 2
    assert result.omitted_by_reason == {"unsupported_extension": 2}
    assert result.omitted_by_category == {"ignored": 2}
    assert [image.path for image in result.folders[0].images] == [second, first, upper]
    assert [image.name for image in result.folders[0].images] == ["a.png", "b.png", "c.PNG"]
    assert all(image.size_bytes > 0 for image in result.folders[0].images)
    assert [item.name for item in result.folders[0].omitted] == ["notes.txt", "photo.jpg"]
    assert {item.severity for item in result.folders[0].omitted} == {"ignored"}


def test_scan_reports_subfolders_and_corrupt_png(tmp_path):
    _png(tmp_path / "valid.png")
    (tmp_path / "broken.png").write_bytes(b"not a real png")
    nested = tmp_path / "nested"
    nested.mkdir()
    _png(nested / "inside.png")

    result = FolderScanner().scan_folders([tmp_path])

    assert result.total_files == 2
    assert result.total_images == 1
    assert result.total_omitted == 2
    assert result.omitted_by_reason == {
        "read_error": 1,
        "subfolder_not_scanned": 1,
    }
    assert result.omitted_by_category == {
        "ignored": 1,
        "warning": 1,
    }
    omitted = {item.name: item for item in result.folders[0].omitted}
    assert omitted["broken.png"].detail == "No se pudo leer como PNG válido"
    assert omitted["broken.png"].severity == "warning"
    assert omitted["nested"].detail == "Subcarpeta no escaneada"
    assert omitted["nested"].severity == "ignored"


def test_scan_fast_mode_skips_png_verification(tmp_path):
    _png(tmp_path / "valid.png")
    broken = tmp_path / "broken.png"
    broken.write_bytes(b"not a real png")

    verified = FolderScanner().scan_folders([tmp_path], verify_images=True)
    fast = FolderScanner().scan_folders([tmp_path], verify_images=False)

    assert [image.name for image in verified.folders[0].images] == ["valid.png"]
    assert verified.omitted_by_reason == {"read_error": 1}
    assert [image.name for image in fast.folders[0].images] == ["broken.png", "valid.png"]
    assert fast.total_omitted == 0


def test_scan_fast_mode_handles_large_flat_batches(tmp_path):
    for index in range(1000):
        (tmp_path / f"item-{index:04d}.png").write_bytes(b"not opened in fast mode")

    result = FolderScanner().scan_folders([tmp_path], verify_images=False)

    assert result.total_folders == 1
    assert result.total_files == 1000
    assert result.total_images == 1000
    assert result.total_omitted == 0
    assert result.folders[0].images[0].name == "item-0000.png"
    assert result.folders[0].images[-1].name == "item-0999.png"


def test_scan_recursive_mode_includes_nested_images(tmp_path):
    root_png = _png(tmp_path / "root.png")
    nested = tmp_path / "nested"
    nested.mkdir()
    nested_png = _png(nested / "inside.png")

    default = FolderScanner().scan_folders([tmp_path])
    recursive = FolderScanner().scan_folders([tmp_path], recursive=True)

    assert [image.path for image in default.folders[0].images] == [root_png]
    assert default.omitted_by_reason == {"subfolder_not_scanned": 1}
    assert [image.path for image in recursive.folders[0].images] == [nested_png, root_png]
    assert recursive.total_files == 2
    assert recursive.total_omitted == 0


def test_scan_recursive_mode_does_not_follow_symlinked_directories(tmp_path, monkeypatch):
    root_png = _png(tmp_path / "root.png")
    link = tmp_path / "linked"
    link.mkdir()
    _png(link / "inside.png")

    original_is_symlink = Path.is_symlink

    def fake_is_symlink(path: Path) -> bool:
        return path == link or original_is_symlink(path)

    monkeypatch.setattr(Path, "is_symlink", fake_is_symlink)

    result = FolderScanner().scan_folders([tmp_path], recursive=True)

    assert [image.path for image in result.folders[0].images] == [root_png]
    assert result.omitted_by_reason == {"symlink_not_scanned": 1}
    omitted = result.folders[0].omitted[0]
    assert omitted.path == link
    assert omitted.detail == "Enlace de carpeta no escaneado"


def test_scan_classifies_system_and_temp_files_as_ignored(tmp_path):
    _png(tmp_path / "valid.png")
    (tmp_path / "Thumbs.db").write_bytes(b"cache")
    (tmp_path / "desktop.ini").write_text("[.ShellClassInfo]", encoding="utf-8")
    (tmp_path / "export.tmp").write_text("temp", encoding="utf-8")

    result = FolderScanner().scan_folders([tmp_path])

    assert result.total_images == 1
    assert result.total_omitted == 3
    assert result.omitted_by_reason == {
        "system_file": 2,
        "temporary_or_config_file": 1,
    }
    assert result.omitted_by_category == {"ignored": 3}
    assert {item.name: item.severity for item in result.folders[0].omitted} == {
        "desktop.ini": "ignored",
        "export.tmp": "ignored",
        "Thumbs.db": "ignored",
    }


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
