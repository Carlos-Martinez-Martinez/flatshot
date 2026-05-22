"""Qt-free application state models for FlatShot UI coordination."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from flatshot.application import presenters
from flatshot.application.contracts import BatchScanResult


BUSY_PROCESSING_MODES = {"processing", "paused", "stopping"}
PREVIEW_INITIAL_LABEL = "Sin imagen"
PREVIEW_INITIAL_TOOLTIP = "Imagen mostrada en el canvas · ESPACIO = ver original"
PREVIEW_EMPTY_LABEL = "Sin imagen seleccionada"
PREVIEW_EMPTY_TOOLTIP = ""
PREVIEW_MOCKUP_LABEL = "Mockup de prueba"
PREVIEW_MOCKUP_TOOLTIP = "Vista previa generada para ajustar el preset"


@dataclass
class UiViewState:
    selected_image: str | None = None
    active_folder: str | None = None
    grid_columns: int = 3
    preview_background: str = "#E6E6E6"
    guides_enabled: bool = False
    advanced_open: bool = False


@dataclass
class BatchSummary:
    folders_count: int = 0
    images_count: int = 0
    processed_count: int = 0
    error_count: int = 0
    adjusted_count: int = 0
    destination_label: str = "Subcarpeta en origen"


@dataclass
class ProcessingState:
    mode: str = "idle"
    status_text: str = ""
    pre_render_status: tuple[str, int, int] | None = None
    progress_value: int = 0

    @property
    def is_busy(self) -> bool:
        return self.mode in BUSY_PROCESSING_MODES


@dataclass
class ExportState:
    destinations: list[str] = field(default_factory=list)
    variant_labels: list[str] = field(default_factory=list)
    source_count: int = 0
    file_total: int = 0
    error_message: str = ""


@dataclass
class PreviewState:
    current_mock: str = "dark"
    selected_image: str | None = None
    label_text: str = PREVIEW_INITIAL_LABEL
    tooltip: str = PREVIEW_INITIAL_TOOLTIP
    is_custom_image: bool = False


@dataclass
class FlatshotAppState:
    batch: BatchSummary = field(default_factory=BatchSummary)
    export: ExportState = field(default_factory=ExportState)
    preview: PreviewState = field(default_factory=PreviewState)
    view: UiViewState = field(default_factory=UiViewState)
    processing: ProcessingState = field(default_factory=ProcessingState)
    selected_image: str | None = None
    active_preset: str | None = None


@dataclass(frozen=True)
class ExportBarState:
    processing: bool
    can_clear_folders: bool
    can_open_export_details: bool
    can_add_folder: bool
    can_edit_export_config: bool
    can_edit_outputs: bool
    can_process: bool
    process_button_text: str
    progress_status_text: str
    show_progress: bool
    progress_value: int | None
    show_pause: bool
    show_stop: bool


def build_batch_summary(
    scan: BatchScanResult,
    *,
    destination_label: str,
) -> BatchSummary:
    return BatchSummary(
        folders_count=scan.total_folders,
        images_count=scan.total_images,
        adjusted_count=scan.adjusted_images,
        destination_label=destination_label,
    )


def format_batch_count_text(batch: BatchSummary) -> str:
    if int(batch.folders_count) <= 0:
        return "0 imágenes"
    if int(batch.adjusted_count) > 0:
        return f"{int(batch.images_count)} imágenes · {int(batch.adjusted_count)} ajustadas"
    return f"{int(batch.images_count)} imágenes"


def processing_mode_for_batch(batch: BatchSummary, current_mode: str) -> str:
    if current_mode in BUSY_PROCESSING_MODES:
        return current_mode
    if int(batch.folders_count) > 0 and int(batch.images_count) > 0:
        return "ready"
    return "idle"


def processing_state_for_export_start() -> ProcessingState:
    return ProcessingState(
        mode="processing",
        status_text="Procesando...",
        pre_render_status=None,
        progress_value=0,
    )


def processing_state_for_single_export(folder_name: str) -> ProcessingState:
    return ProcessingState(
        mode="processing",
        status_text=f"Procesando: {folder_name}",
        pre_render_status=None,
        progress_value=0,
    )


def processing_state_for_queue_job(
    index: int,
    total_folders: int,
    folder_path: str | Path,
) -> ProcessingState:
    current = max(0, int(index)) + 1
    total = max(0, int(total_folders))
    folder_name = Path(str(folder_path)).name
    return ProcessingState(
        mode="processing",
        status_text=f"[{current}/{total}] {folder_name}",
        pre_render_status=None,
        progress_value=0,
    )


def processing_state_for_pause(is_paused: bool) -> ProcessingState:
    if is_paused:
        return ProcessingState(
            mode="paused",
            status_text="Pausado",
            pre_render_status=None,
            progress_value=0,
        )
    return processing_state_for_export_start()


def processing_state_for_stop() -> ProcessingState:
    return ProcessingState(
        mode="stopping",
        status_text="Deteniendo...",
        pre_render_status=None,
        progress_value=0,
    )


def processing_state_after_reset(
    batch: BatchSummary,
    *,
    selected_folders_count: int,
) -> ProcessingState:
    mode = "ready" if int(batch.images_count) > 0 and int(selected_folders_count) > 0 else "idle"
    return ProcessingState(mode=mode, status_text="", progress_value=0)


def calculate_queue_overall_progress(index: int, progress: int, total_jobs: int) -> int:
    total = max(1, int(total_jobs))
    current_index = max(0, int(index))
    job_progress = min(100, max(0, int(progress)))
    value = (current_index * 100) // total + job_progress // total
    return min(100, max(0, value))


def build_pre_render_bar_status(
    state: str,
    prepared: int,
    total: int,
) -> tuple[str, int, int] | None:
    prepared_count = int(prepared)
    total_count = int(total)
    if state == "idle" or total_count <= 0:
        return None
    if state == "preparing":
        text = f"Preparando exportación {prepared_count}/{total_count}"
    elif state == "ready":
        text = f"Listo para exportar {prepared_count}/{total_count}"
    elif state == "partial":
        text = f"Caché parcial {prepared_count}/{total_count}"
    else:
        text = (
            "Pausado por actividad"
            if prepared_count <= 0
            else f"Caché parcial {prepared_count}/{total_count}"
        )
    return text, prepared_count, total_count


def build_empty_preview_state(current_mock: str = "dark") -> PreviewState:
    return PreviewState(
        current_mock=str(current_mock or "dark"),
        selected_image=None,
        label_text=PREVIEW_EMPTY_LABEL,
        tooltip=PREVIEW_EMPTY_TOOLTIP,
        is_custom_image=False,
    )


def build_mockup_preview_state(current_mock: str) -> PreviewState:
    mock = "medium" if current_mock == "med" else str(current_mock or "dark")
    return PreviewState(
        current_mock=mock,
        selected_image=None,
        label_text=PREVIEW_MOCKUP_LABEL,
        tooltip=PREVIEW_MOCKUP_TOOLTIP,
        is_custom_image=False,
    )


def build_custom_preview_state(path: str | Path) -> PreviewState:
    path_text = str(path)
    image_path = Path(path_text)
    return PreviewState(
        current_mock="custom_drop",
        selected_image=path_text,
        label_text=image_path.stem,
        tooltip=path_text,
        is_custom_image=True,
    )


def format_custom_preview_button_text(
    path: str | Path,
    *,
    max_length: int = 15,
    include_suffix: bool = False,
) -> str:
    image_path = Path(str(path))
    name = image_path.name if include_suffix else image_path.stem
    limit = max(0, int(max_length))
    return f" {name[:limit]}"


def build_export_state(
    *,
    destinations: Iterable[str],
    variant_labels: Iterable[str],
    source_count: int,
    error_message: str = "",
) -> ExportState:
    labels = [str(label) for label in variant_labels]
    sources = max(0, int(source_count))
    return ExportState(
        destinations=sorted(str(destination) for destination in destinations),
        variant_labels=labels,
        source_count=sources,
        file_total=sources * len(labels),
        error_message=str(error_message),
    )


def format_export_variant_labels(labels: Iterable[str]) -> str:
    return ", ".join(str(label) for label in labels) or "ninguna"


def build_single_export_summary_lines(
    export: ExportState,
    *,
    success: bool,
    processed: int,
    total: int,
    duration: float,
) -> list[str]:
    duration_text = f"{float(duration):.1f}s"
    if success:
        return [
            f"{int(export.source_count)} imágenes procesadas",
            f"{int(processed)}/{int(total)} archivos exportados en {duration_text}",
            f"Salidas: {format_export_variant_labels(export.variant_labels)}",
        ]
    return [
        "Se detuvo o falló el proceso",
        f"{int(processed)}/{int(total)} archivos exportados en {duration_text}",
        export.error_message,
    ]


def build_queue_export_summary_lines(
    export: ExportState,
    *,
    completed: int,
    errors: int,
    total_images: int,
) -> list[str]:
    if int(errors) == 0:
        return [
            f"\u2713 {int(completed)} carpetas procesadas",
            f"{int(export.source_count)} imágenes procesadas",
            f"{int(total_images)} archivos exportados",
            f"Salidas: {format_export_variant_labels(export.variant_labels)}",
        ]
    return [
        f"\u2713 {int(completed)} carpetas completadas",
        f"\u2717 {int(errors)} carpetas con errores",
        f"{int(total_images)} archivos exportados",
        export.error_message,
    ]


def build_export_bar_state(
    batch: BatchSummary,
    *,
    active_outputs_count: int,
    mode: str,
    selected_folders_count: int,
    export_status_text: str = "",
    pre_render_status: tuple[str, int, int] | None = None,
) -> ExportBarState:
    folders = max(0, int(batch.folders_count))
    images = max(0, int(batch.images_count))
    outputs = max(0, int(active_outputs_count))
    selected = max(0, int(selected_folders_count))
    processing = mode in BUSY_PROCESSING_MODES

    status_view = presenters.format_processing_status(
        folders,
        images,
        mode,
        export_status_text=export_status_text,
        pre_render_status=pre_render_status,
    )

    return ExportBarState(
        processing=processing,
        can_clear_folders=folders > 0 and not processing,
        can_open_export_details=folders > 0 and not processing,
        can_add_folder=not processing,
        can_edit_export_config=not processing,
        can_edit_outputs=not processing,
        can_process=presenters.can_process_batch(
            folders,
            images,
            outputs,
            is_processing=processing,
        ),
        process_button_text=presenters.format_process_button_text(images),
        progress_status_text=status_view.text,
        show_progress=status_view.show_progress,
        progress_value=status_view.progress_value,
        show_pause=processing and selected > 1,
        show_stop=processing,
    )
