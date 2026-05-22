from flatshot.application.presenters import (
    can_process_batch,
    format_batch_summary,
    format_destination_batch_label,
    format_destination_summary,
    format_export_summary,
    format_process_button_text,
    format_processing_status,
    is_destination_configured,
)
from flatshot.core.models import ExportConfig, WEB_RGB230, WHITE_RGB255


def test_format_batch_summary_handles_empty_singular_plural_and_adjusted_counts():
    assert format_batch_summary(0, 0, 0) == "Sin lote cargado"
    assert format_batch_summary(1, 0, 0) == "1 carpeta · 0 imágenes"
    assert format_batch_summary(1, 23, 0) == "1 carpeta · 23 imágenes"
    assert format_batch_summary(2, 50, 4) == "2 carpetas · 50 imágenes · 4 ajustadas"


def test_format_export_summary_uses_first_active_output_background_and_count():
    config = ExportConfig(
        format="JPG",
        output_width=1800,
        output_height=2400,
        variants=[WEB_RGB230, WHITE_RGB255.model_copy(update={"enabled": True})],
    )

    assert format_export_summary(config) == "JPG · 1800×2400 · #E6E6E6 · 2 salidas"


def test_format_export_summary_handles_transparent_output():
    transparent = WEB_RGB230.model_copy(update={"transparent_bg": True})
    config = ExportConfig(format="PNG", output_width=1800, output_height=2400, variants=[transparent])

    assert format_export_summary(config) == "PNG · 1800×2400 · transparente · 1 salida"


def test_format_destination_summary_preserves_current_ui_texts():
    subfolder = ExportConfig(output_destination="subfolder", output_folder_name="_SALIDA_PRO")
    custom = ExportConfig(output_destination="custom", custom_output_path="C:/out")
    missing = ExportConfig(output_destination="custom", custom_output_path=None)

    assert format_destination_summary(subfolder).text == "Destino: origen / _SALIDA_PRO"
    assert format_destination_summary(custom).text == "Destino: carpeta personalizada"
    assert format_destination_summary(custom).tooltip == "C:/out"
    assert format_destination_summary(missing).text == "Destino: personalizada sin elegir"


def test_format_destination_batch_label_matches_persistent_batch_label():
    assert format_destination_batch_label(
        ExportConfig(output_destination="subfolder", output_folder_name="_SALIDA_PRO")
    ) == "origen / _SALIDA_PRO"
    assert format_destination_batch_label(
        ExportConfig(output_destination="custom", custom_output_path="C:/out")
    ) == "carpeta personalizada: C:/out"
    assert format_destination_batch_label(
        ExportConfig(output_destination="custom", custom_output_path=None)
    ) == "carpeta personalizada sin elegir"


def test_process_button_text_and_process_availability():
    assert format_process_button_text(0) == "Procesar lote"
    assert format_process_button_text(1) == "Procesar 1 imagen"
    assert format_process_button_text(23) == "Procesar 23 imágenes"

    assert can_process_batch(1, 1, 1)
    assert not can_process_batch(0, 1, 1)
    assert not can_process_batch(1, 0, 1)
    assert not can_process_batch(1, 1, 0)
    assert not can_process_batch(1, 1, 1, is_processing=True)


def test_destination_validation_only_requires_path_for_custom_destination():
    assert is_destination_configured(ExportConfig(output_destination="subfolder"))
    assert is_destination_configured(ExportConfig(output_destination="custom", custom_output_path="C:/out"))
    assert not is_destination_configured(ExportConfig(output_destination="custom", custom_output_path=None))


def test_processing_status_texts_and_progress():
    assert format_processing_status(0, 0, "idle").text == "Añade una carpeta para procesar"
    assert format_processing_status(1, 0, "ready").text == "No hay PNG válidos"
    assert format_processing_status(1, 1, "ready").text == "Listo para procesar"
    assert format_processing_status(1, 1, "processing").text == "Procesando..."
    assert format_processing_status(1, 1, "paused").text == "Pausado"
    assert format_processing_status(1, 1, "stopping").text == "Deteniendo..."

    pre_render = format_processing_status(
        1,
        4,
        "ready",
        pre_render_status=("Generando previews 2/4", 2, 4),
    )
    assert pre_render.text == "Generando previews 2/4"
    assert pre_render.show_progress
    assert pre_render.progress_value == 50
