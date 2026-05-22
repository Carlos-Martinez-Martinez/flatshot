from pathlib import Path

from flatshot.application.export_run_planner import ExportRunPlanner
from flatshot.core.models import ExportConfig, WEB_RGB230, WHITE_RGB255


def _touch(path: Path) -> Path:
    path.write_bytes(b"data")
    return path


def test_prepare_snapshots_png_files_without_non_png(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    first = _touch(source / "a.png")
    second = _touch(source / "b.png")
    _touch(source / "ignored.jpg")

    plan = ExportRunPlanner().prepare([source], ExportConfig())

    assert plan.folders[0].folder == source
    assert plan.folders[0].input_files == [first, second]
    assert plan.input_files_for(source) == [first, second]
    assert plan.source_count == 2
    assert plan.file_total == 2


def test_prepare_multiple_folders_preserves_folder_order_and_counts(tmp_path):
    first_folder = tmp_path / "first"
    second_folder = tmp_path / "second"
    first_folder.mkdir()
    second_folder.mkdir()
    first_image = _touch(first_folder / "one.png")
    second_image = _touch(second_folder / "two.png")

    plan = ExportRunPlanner().prepare([first_folder, second_folder], ExportConfig())

    assert [folder_plan.folder for folder_plan in plan.folders] == [first_folder, second_folder]
    assert plan.input_files_for(first_folder) == [first_image]
    assert plan.input_files_for(second_folder) == [second_image]
    assert plan.source_count == 2


def test_prepare_empty_folder_has_no_sources_but_keeps_destination(tmp_path):
    source = tmp_path / "empty"
    source.mkdir()

    plan = ExportRunPlanner().prepare(
        [source],
        ExportConfig(output_folder_name="_OUT"),
    )

    assert plan.input_files_for(source) == []
    assert plan.source_count == 0
    assert plan.file_total == 0
    assert plan.destinations == [source / "_OUT"]


def test_prepare_uses_enabled_variants_for_destinations_labels_and_file_total(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    _touch(source / "a.png")
    _touch(source / "b.png")
    white = WHITE_RGB255.model_copy(update={"enabled": True, "output_subfolder": "white"})
    disabled = WEB_RGB230.model_copy(update={"id": "disabled", "enabled": False})
    config = ExportConfig(
        output_folder_name="_OUT",
        variants=[WEB_RGB230, white, disabled],
    )

    plan = ExportRunPlanner().prepare([source], config)

    assert plan.active_variants == [WEB_RGB230, white]
    assert plan.variant_labels == ["Web RGB230", "Blanco RGB255"]
    assert plan.source_count == 2
    assert plan.file_total == 4
    assert plan.destinations == [source / "_OUT", source / "_OUT" / "white"]


def test_prepare_accepts_precomputed_active_variants(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    _touch(source / "a.png")
    disabled_config = ExportConfig(
        variants=[WEB_RGB230.model_copy(update={"enabled": False})],
    )

    plan = ExportRunPlanner().prepare(
        [source],
        disabled_config,
        active_variants=[WEB_RGB230],
    )

    assert plan.active_variants == [WEB_RGB230]
    assert plan.variant_labels == ["Web RGB230"]
    assert plan.file_total == 1


def test_prepare_uses_custom_destination_with_variant_subfolders(tmp_path):
    source = tmp_path / "source"
    custom = tmp_path / "exports"
    source.mkdir()
    _touch(source / "a.png")
    white = WHITE_RGB255.model_copy(update={"enabled": True, "output_subfolder": "white"})
    config = ExportConfig(
        output_destination="custom",
        custom_output_path=str(custom),
        variants=[WEB_RGB230, white],
    )

    plan = ExportRunPlanner().prepare([source], config)

    assert plan.destinations == [custom, custom / "white"]


def test_input_files_for_unknown_folder_returns_empty_list(tmp_path):
    source = tmp_path / "source"
    source.mkdir()

    plan = ExportRunPlanner().prepare([source], ExportConfig())

    assert plan.input_files_for(tmp_path / "missing") == []
