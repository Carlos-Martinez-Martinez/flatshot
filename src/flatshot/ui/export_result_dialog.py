"""UI-only export result dialogs."""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

import qtawesome as qta

from flatshot.application.app_state import (
    ExportState,
    build_queue_export_summary_lines,
    build_single_export_summary_lines,
)
from flatshot.ui.styles import COLORS


PixelScaler = Callable[[float], int]
OpenFolderCallback = Callable[[Path], None]


def show_single_export_result_dialog(
    parent,
    *,
    export_state: ExportState,
    success: bool,
    processed: int,
    total: int,
    duration: float,
    px: PixelScaler,
    open_folder: OpenFolderCallback,
) -> None:
    title = "Proceso completado" if success else "Proceso incompleto"
    show_export_result_dialog(
        parent,
        title=title,
        success=success,
        summary_lines=build_single_export_summary_lines(
            export_state,
            success=success,
            processed=processed,
            total=total,
            duration=duration,
        ),
        destinations=export_state.destinations,
        px=px,
        open_folder=open_folder,
    )


def show_queue_export_result_dialog(
    parent,
    *,
    export_state: ExportState,
    completed: int,
    errors: int,
    total_images: int,
    px: PixelScaler,
    open_folder: OpenFolderCallback,
) -> None:
    success = int(errors) == 0
    title = "Cola completada" if success else "Cola completada con errores"
    show_export_result_dialog(
        parent,
        title=title,
        success=success,
        summary_lines=build_queue_export_summary_lines(
            export_state,
            completed=completed,
            errors=errors,
            total_images=total_images,
        ),
        destinations=export_state.destinations,
        px=px,
        open_folder=open_folder,
    )


def show_export_result_dialog(
    parent,
    *,
    title: str,
    success: bool,
    summary_lines: list[str],
    destinations: list[str],
    px: PixelScaler,
    open_folder: OpenFolderCallback,
) -> None:
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setMinimumSize(px(640), px(420))
    dialog.setProperty("class", "dialog")

    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(px(16), px(14), px(16), px(14))
    layout.setSpacing(px(10))

    icon_name = "fa5s.check-circle" if success else "fa5s.exclamation-triangle"
    icon_color = COLORS["success"] if success else COLORS["error"]
    header_row = QHBoxLayout()
    icon_label = QLabel()
    icon_label.setPixmap(qta.icon(icon_name, color=icon_color).pixmap(px(22), px(22)))
    header_row.addWidget(icon_label)

    header_title = QLabel(title)
    header_title.setProperty("class", "dialog-title")
    header_row.addWidget(header_title, 1)
    layout.addLayout(header_row)

    for line in summary_lines:
        if not line:
            continue
        summary_label = QLabel(line)
        summary_label.setProperty("class", "dialog-text")
        layout.addWidget(summary_label)

    dest_title = QLabel("Destino(s) de exportación:")
    dest_title.setProperty("class", "dialog-section")
    layout.addWidget(dest_title)

    dest_list = QListWidget()
    dest_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
    dest_list.setProperty("class", "list")

    valid_destinations = []
    for dest in destinations:
        if not dest:
            continue
        valid_destinations.append(dest)
        item = QListWidgetItem(dest)
        item.setToolTip(dest)
        dest_list.addItem(item)

    if not valid_destinations:
        item = QListWidgetItem("(No se registró ruta de destino)")
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
        dest_list.addItem(item)
    else:
        dest_list.setCurrentRow(0)

    layout.addWidget(dest_list, 1)
    hint_lbl = QLabel("Selecciona una ruta y pulsa 'Abrir carpeta'")
    hint_lbl.setProperty("class", "muted")
    layout.addWidget(hint_lbl)

    btn_row = QHBoxLayout()
    btn_open_selected = QPushButton("Abrir carpeta")
    btn_open_selected.setEnabled(bool(valid_destinations))
    btn_open_selected.setProperty("class", "primary")
    btn_row.addWidget(btn_open_selected)

    btn_row.addStretch()
    btn_close = QPushButton("Cerrar")
    btn_close.setProperty("class", "ghost")
    btn_row.addWidget(btn_close)
    layout.addLayout(btn_row)

    def _open_selected():
        row = dest_list.currentRow()
        if row < 0:
            row = 0
        if 0 <= row < len(valid_destinations):
            open_folder(Path(valid_destinations[row]))

    btn_open_selected.clicked.connect(_open_selected)
    dest_list.itemDoubleClicked.connect(lambda _: _open_selected())
    btn_close.clicked.connect(dialog.accept)

    dialog.exec()
