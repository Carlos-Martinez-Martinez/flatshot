"""Qt-free application state models for FlatShot UI coordination."""
from __future__ import annotations

from dataclasses import dataclass, field

from flatshot.application import presenters
from flatshot.application.contracts import BatchScanResult


BUSY_PROCESSING_MODES = {"processing", "paused", "stopping"}


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
class FlatshotAppState:
    batch: BatchSummary = field(default_factory=BatchSummary)
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
