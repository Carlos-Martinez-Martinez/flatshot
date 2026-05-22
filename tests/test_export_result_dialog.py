from flatshot.application.app_state import ExportState
from flatshot.ui import export_result_dialog


def _px(value):
    return int(value)


def _open_folder(_path):
    return None


def test_single_export_result_adapter_builds_success_dialog(monkeypatch):
    calls = []
    export_state = ExportState(
        destinations=["C:/salida"],
        variant_labels=["Web RGB230"],
        source_count=2,
    )

    monkeypatch.setattr(
        export_result_dialog,
        "show_export_result_dialog",
        lambda parent, **kwargs: calls.append((parent, kwargs)),
    )

    parent = object()
    export_result_dialog.show_single_export_result_dialog(
        parent,
        export_state=export_state,
        success=True,
        processed=2,
        total=2,
        duration=1.2,
        px=_px,
        open_folder=_open_folder,
    )

    assert calls[0][0] is parent
    assert calls[0][1]["title"] == "Proceso completado"
    assert calls[0][1]["success"] is True
    assert calls[0][1]["destinations"] == ["C:/salida"]
    assert calls[0][1]["summary_lines"] == [
        "2 imágenes procesadas",
        "2/2 archivos exportados en 1.2s",
        "Salidas: Web RGB230",
    ]


def test_queue_export_result_adapter_builds_error_dialog(monkeypatch):
    calls = []
    export_state = ExportState(
        destinations=["C:/salida"],
        variant_labels=["Web RGB230"],
        source_count=3,
        error_message="Error de prueba",
    )

    monkeypatch.setattr(
        export_result_dialog,
        "show_export_result_dialog",
        lambda parent, **kwargs: calls.append((parent, kwargs)),
    )

    parent = object()
    export_result_dialog.show_queue_export_result_dialog(
        parent,
        export_state=export_state,
        completed=1,
        errors=1,
        total_images=3,
        px=_px,
        open_folder=_open_folder,
    )

    assert calls[0][0] is parent
    assert calls[0][1]["title"] == "Cola completada con errores"
    assert calls[0][1]["success"] is False
    assert calls[0][1]["destinations"] == ["C:/salida"]
    assert calls[0][1]["summary_lines"] == [
        "✓ 1 carpetas completadas",
        "✗ 1 carpetas con errores",
        "3 archivos exportados",
        "Error de prueba",
    ]
