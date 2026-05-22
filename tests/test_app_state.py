from pathlib import Path

import flatshot.application.app_state as app_state_module
from flatshot.application.app_state import (
    BatchSummary,
    ExportState,
    FlatshotAppState,
    PreviewState,
    ProcessingState,
    UiViewState,
    build_batch_summary,
    build_custom_preview_state,
    build_empty_preview_state,
    build_export_state,
    build_export_bar_state,
    build_mockup_preview_state,
    build_pre_render_bar_status,
    build_queue_export_summary_lines,
    build_single_export_summary_lines,
    calculate_queue_overall_progress,
    format_batch_count_text,
    format_custom_preview_button_text,
    format_export_variant_labels,
    processing_state_after_reset,
    processing_state_for_export_start,
    processing_state_for_pause,
    processing_state_for_queue_job,
    processing_state_for_single_export,
    processing_state_for_stop,
    processing_mode_for_batch,
)
from flatshot.application.contracts import BatchScanResult


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
        export=ExportState(destinations=["C:/out"]),
        preview=PreviewState(selected_image="image.png", label_text="image"),
        view=view,
        processing=processing,
        selected_image=view.selected_image,
        active_preset="Preset",
    )

    assert state.batch.images_count == 2
    assert state.export.destinations == ["C:/out"]
    assert state.preview.label_text == "image"
    assert state.view.active_folder == "folder"
    assert state.processing.mode == "ready"
    assert state.selected_image == "image.png"
    assert state.active_preset == "Preset"


def test_preview_state_helpers_preserve_preview_labels_and_selection(tmp_path):
    image = tmp_path / "camiseta larga.png"
    image.write_bytes(b"")

    custom = build_custom_preview_state(image)
    mockup = build_mockup_preview_state("med")
    empty = build_empty_preview_state()

    assert custom.current_mock == "custom_drop"
    assert custom.selected_image == str(image)
    assert custom.label_text == "camiseta larga"
    assert custom.tooltip == str(image)
    assert custom.is_custom_image

    assert mockup.current_mock == "medium"
    assert mockup.selected_image is None
    assert mockup.label_text == "Mockup de prueba"
    assert mockup.tooltip == "Vista previa generada para ajustar el preset"
    assert not mockup.is_custom_image

    assert empty.current_mock == "dark"
    assert empty.selected_image is None
    assert empty.label_text == "Sin imagen seleccionada"
    assert empty.tooltip == ""


def test_custom_preview_button_text_preserves_existing_truncation_modes(tmp_path):
    image = tmp_path / "nombre-muy-largo.png"
    dropped = tmp_path / "drop.png"

    assert format_custom_preview_button_text(image) == " nombre-muy-larg"
    assert format_custom_preview_button_text(dropped, include_suffix=True) == " drop.png"
    assert format_custom_preview_button_text(image, max_length=4) == " nomb"


def test_build_batch_summary_from_scan_result():
    scan = BatchScanResult(total_folders=2, total_images=5, adjusted_images=1)

    summary = build_batch_summary(scan, destination_label="origen / _SALIDA_PRO")

    assert summary == BatchSummary(
        folders_count=2,
        images_count=5,
        adjusted_count=1,
        destination_label="origen / _SALIDA_PRO",
    )


def test_format_batch_count_text_preserves_existing_header_texts():
    assert format_batch_count_text(BatchSummary()) == "0 imágenes"
    assert format_batch_count_text(BatchSummary(folders_count=1, images_count=0)) == "0 imágenes"
    assert format_batch_count_text(BatchSummary(folders_count=1, images_count=1)) == "1 imágenes"
    assert (
        format_batch_count_text(BatchSummary(folders_count=2, images_count=50, adjusted_count=4))
        == "50 imágenes · 4 ajustadas"
    )


def test_processing_mode_for_batch_keeps_busy_modes_and_derives_idle_ready():
    empty = BatchSummary()
    ready = BatchSummary(folders_count=1, images_count=1)

    assert processing_mode_for_batch(empty, "ready") == "idle"
    assert processing_mode_for_batch(BatchSummary(folders_count=1, images_count=0), "ready") == "idle"
    assert processing_mode_for_batch(ready, "idle") == "ready"
    assert processing_mode_for_batch(empty, "processing") == "processing"
    assert processing_mode_for_batch(empty, "paused") == "paused"
    assert processing_mode_for_batch(empty, "stopping") == "stopping"


def test_processing_state_helpers_preserve_export_status_texts(tmp_path):
    folder = tmp_path / "folder"

    start = processing_state_for_export_start()
    single = processing_state_for_single_export("folder")
    queue = processing_state_for_queue_job(0, 2, folder)
    paused = processing_state_for_pause(True)
    resumed = processing_state_for_pause(False)
    stopping = processing_state_for_stop()
    ready_reset = processing_state_after_reset(
        BatchSummary(folders_count=1, images_count=2),
        selected_folders_count=1,
    )
    idle_reset = processing_state_after_reset(
        BatchSummary(folders_count=1, images_count=0),
        selected_folders_count=1,
    )

    assert start == ProcessingState(mode="processing", status_text="Procesando...", progress_value=0)
    assert single.mode == "processing"
    assert single.status_text == "Procesando: folder"
    assert queue.status_text == "[1/2] folder"
    assert paused.mode == "paused"
    assert paused.status_text == "Pausado"
    assert resumed.mode == "processing"
    assert resumed.status_text == "Procesando..."
    assert stopping.mode == "stopping"
    assert stopping.status_text == "Deteniendo..."
    assert ready_reset.mode == "ready"
    assert ready_reset.status_text == ""
    assert ready_reset.progress_value == 0
    assert idle_reset.mode == "idle"


def test_queue_overall_progress_preserves_existing_calculation():
    assert calculate_queue_overall_progress(0, 0, 2) == 0
    assert calculate_queue_overall_progress(0, 50, 2) == 25
    assert calculate_queue_overall_progress(1, 0, 2) == 50
    assert calculate_queue_overall_progress(1, 50, 2) == 75
    assert calculate_queue_overall_progress(1, 100, 2) == 100
    assert calculate_queue_overall_progress(0, 50, 0) == 50


def test_pre_render_bar_status_preserves_existing_texts():
    assert build_pre_render_bar_status("idle", 0, 0) is None
    assert build_pre_render_bar_status("preparing", 2, 4) == (
        "Preparando exportación 2/4",
        2,
        4,
    )
    assert build_pre_render_bar_status("ready", 4, 4) == ("Listo para exportar 4/4", 4, 4)
    assert build_pre_render_bar_status("partial", 1, 4) == ("Caché parcial 1/4", 1, 4)
    assert build_pre_render_bar_status("paused", 0, 4) == ("Pausado por actividad", 0, 4)
    assert build_pre_render_bar_status("paused", 1, 4) == ("Caché parcial 1/4", 1, 4)


def test_build_export_state_sorts_destinations_and_counts_total_outputs():
    state = build_export_state(
        destinations=["C:/z", "C:/a"],
        variant_labels=["Web", "Blanco"],
        source_count=3,
    )

    assert state.destinations == ["C:/a", "C:/z"]
    assert state.variant_labels == ["Web", "Blanco"]
    assert state.source_count == 3
    assert state.file_total == 6
    assert state.error_message == ""


def test_export_variant_labels_fallback():
    assert format_export_variant_labels(["Web", "Blanco"]) == "Web, Blanco"
    assert format_export_variant_labels([]) == "ninguna"


def test_single_export_summary_lines_preserve_existing_texts():
    state = ExportState(
        variant_labels=["Web"],
        source_count=4,
        error_message="falló",
    )

    assert build_single_export_summary_lines(
        state,
        success=True,
        processed=4,
        total=4,
        duration=1.25,
    ) == [
        "4 imágenes procesadas",
        "4/4 archivos exportados en 1.2s",
        "Salidas: Web",
    ]
    assert build_single_export_summary_lines(
        state,
        success=False,
        processed=1,
        total=4,
        duration=2.0,
    ) == [
        "Se detuvo o falló el proceso",
        "1/4 archivos exportados en 2.0s",
        "falló",
    ]


def test_queue_export_summary_lines_preserve_existing_texts():
    state = ExportState(
        variant_labels=["Web", "Blanco"],
        source_count=8,
        error_message="error de cola",
    )

    assert build_queue_export_summary_lines(
        state,
        completed=2,
        errors=0,
        total_images=16,
    ) == [
        "✓ 2 carpetas procesadas",
        "8 imágenes procesadas",
        "16 archivos exportados",
        "Salidas: Web, Blanco",
    ]
    assert build_queue_export_summary_lines(
        state,
        completed=1,
        errors=1,
        total_images=8,
    ) == [
        "✓ 1 carpetas completadas",
        "✗ 1 carpetas con errores",
        "8 archivos exportados",
        "error de cola",
    ]


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
