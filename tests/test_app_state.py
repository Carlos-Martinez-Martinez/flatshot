from pathlib import Path

import flatshot.application.app_state as app_state_module
from flatshot.application.app_state import (
    BatchSummary,
    FlatshotAppState,
    ProcessingState,
    UiViewState,
    build_export_bar_state,
)


def test_app_state_does_not_import_pyqt():
    source = Path(app_state_module.__file__).read_text(encoding="utf-8")

    assert "PyQt6" not in source
    assert "QWidget" not in source
    assert "QApplication" not in source


def test_flatshot_app_state_groups_existing_ui_state_without_widgets():
    view = UiViewState(selected_image="image.png", active_folder="folder")
    batch = BatchSummary(folders_count=1, images_count=2, adjusted_count=1)
    processing = ProcessingState(mode="ready")

    state = FlatshotAppState(
        batch=batch,
        view=view,
        processing=processing,
        selected_image=view.selected_image,
        active_preset="Preset",
    )

    assert state.batch.images_count == 2
    assert state.view.active_folder == "folder"
    assert state.processing.mode == "ready"
    assert state.selected_image == "image.png"
    assert state.active_preset == "Preset"


def test_export_bar_state_for_empty_batch_disables_processing():
    state = build_export_bar_state(
        BatchSummary(),
        active_outputs_count=1,
        mode="idle",
        selected_folders_count=0,
    )

    assert not state.processing
    assert not state.can_process
    assert not state.can_clear_folders
    assert state.can_add_folder
    assert state.process_button_text == "Procesar lote"
    assert state.progress_status_text == "Añade una carpeta para procesar"
    assert not state.show_progress


def test_export_bar_state_for_ready_batch_enables_process_action():
    state = build_export_bar_state(
        BatchSummary(folders_count=2, images_count=23),
        active_outputs_count=1,
        mode="ready",
        selected_folders_count=2,
    )

    assert not state.processing
    assert state.can_process
    assert state.can_clear_folders
    assert state.can_open_export_details
    assert state.can_edit_export_config
    assert state.process_button_text == "Procesar 23 imágenes"
    assert state.progress_status_text == "Listo para procesar"
    assert not state.show_pause
    assert not state.show_stop


def test_export_bar_state_requires_active_outputs():
    state = build_export_bar_state(
        BatchSummary(folders_count=1, images_count=1),
        active_outputs_count=0,
        mode="ready",
        selected_folders_count=1,
    )

    assert not state.can_process
    assert state.progress_status_text == "Listo para procesar"


def test_export_bar_state_for_processing_disables_editing_and_shows_controls():
    state = build_export_bar_state(
        BatchSummary(folders_count=2, images_count=10),
        active_outputs_count=1,
        mode="processing",
        selected_folders_count=2,
        export_status_text="[1/2] carpeta",
    )

    assert state.processing
    assert not state.can_process
    assert not state.can_clear_folders
    assert not state.can_add_folder
    assert not state.can_edit_outputs
    assert state.show_pause
    assert state.show_stop
    assert state.show_progress
    assert state.progress_status_text == "[1/2] carpeta"


def test_export_bar_state_for_paused_and_stopping_statuses():
    paused = build_export_bar_state(
        BatchSummary(folders_count=2, images_count=10),
        active_outputs_count=1,
        mode="paused",
        selected_folders_count=2,
    )
    stopping = build_export_bar_state(
        BatchSummary(folders_count=1, images_count=10),
        active_outputs_count=1,
        mode="stopping",
        selected_folders_count=1,
    )

    assert paused.progress_status_text == "Pausado"
    assert paused.show_pause
    assert stopping.progress_status_text == "Deteniendo..."
    assert not stopping.show_pause
    assert stopping.show_stop


def test_export_bar_state_includes_pre_render_progress_when_not_processing():
    state = build_export_bar_state(
        BatchSummary(folders_count=1, images_count=4),
        active_outputs_count=1,
        mode="ready",
        selected_folders_count=1,
        pre_render_status=("Preparando exportación 2/4", 2, 4),
    )

    assert state.can_process
    assert state.progress_status_text == "Preparando exportación 2/4"
    assert state.show_progress
    assert state.progress_value == 50
