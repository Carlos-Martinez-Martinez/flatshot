"""
Queue Widget for FlatShot
Provides UI for managing the job queue.
"""
from pathlib import Path
from typing import List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QProgressBar, QFileDialog, QLabel,
    QAbstractItemView, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QAction
import qtawesome as qta

from flatshot.core.models import JobItem
from flatshot.ui.styles import COLORS


class QueueWidget(QWidget):
    """Widget for managing the processing queue."""
    
    # Signals
    start_queue = pyqtSignal()
    pause_queue = pyqtSignal()
    resume_queue = pyqtSignal()
    stop_queue = pyqtSignal()
    jobs_changed = pyqtSignal(list)  # Emits list of JobItem
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.jobs: List[JobItem] = []
        self._is_processing = False
        self._is_paused = False
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Header with action buttons
        header = QHBoxLayout()
        header.setSpacing(4)
        
        icon_color = COLORS['text_muted']
        
        self.btn_add = QPushButton(qta.icon('fa5s.folder-plus', color=icon_color), " Añadir")
        self.btn_add.setProperty("class", "secondary")
        self.btn_add.setToolTip("Añadir carpeta a la cola")
        self.btn_add.clicked.connect(self._add_folder)
        header.addWidget(self.btn_add)
        
        self.btn_remove = QPushButton(qta.icon('fa5s.times', color=COLORS['error']), "")
        self.btn_remove.setProperty("class", "icon-btn")
        self.btn_remove.setToolTip("Quitar seleccionado")
        self.btn_remove.clicked.connect(self._remove_selected)
        header.addWidget(self.btn_remove)
        
        self.btn_clear = QPushButton(qta.icon('fa5s.trash-alt', color=COLORS['error']), "")
        self.btn_clear.setProperty("class", "icon-btn")
        self.btn_clear.setToolTip("Limpiar cola")
        self.btn_clear.clicked.connect(self._clear_queue)
        header.addWidget(self.btn_clear)
        
        header.addStretch()
        
        self.lbl_count = QLabel("0 carpetas")
        self.lbl_count.setProperty("class", "muted")
        header.addWidget(self.lbl_count)
        
        layout.addLayout(header)
        
        # Table for jobs
        self.table = QTableWidget()
        self.table.setProperty("class", "table")
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Carpeta", "Imágenes", "Estado", "Progreso"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 70)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 120)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)
        
        # Control buttons
        controls = QHBoxLayout()
        controls.setSpacing(8)
        
        self.btn_start = QPushButton(qta.icon('fa5s.play', color='white'), " INICIAR COLA")
        self.btn_start.setProperty("class", "primary")
        self.btn_start.setEnabled(False)
        self.btn_start.clicked.connect(self._on_start)
        controls.addWidget(self.btn_start)
        
        self.btn_pause = QPushButton(qta.icon('fa5s.pause', color='white'), " PAUSAR")
        self.btn_pause.setProperty("class", "warning-solid")
        self.btn_pause.clicked.connect(self._on_pause)
        self.btn_pause.hide()
        controls.addWidget(self.btn_pause)
        
        self.btn_stop = QPushButton(qta.icon('fa5s.stop', color='white'), " DETENER")
        self.btn_stop.setProperty("class", "danger-solid")
        self.btn_stop.clicked.connect(self._on_stop)
        self.btn_stop.hide()
        controls.addWidget(self.btn_stop)
        
        layout.addLayout(controls)
        
        # Overall progress
        self.progress_overall = QProgressBar()
        self.progress_overall.setTextVisible(True)
        self.progress_overall.setFormat("Cola: %p%")
        self.progress_overall.setFixedHeight(12)
        layout.addWidget(self.progress_overall)
    
    def _add_folder(self):
        """Add a folder to the queue."""
        folder = QFileDialog.getExistingDirectory(
            self, "Seleccionar carpeta de imágenes"
        )
        if folder:
            self.add_folder(folder)
    
    def add_folder(self, folder_path: str):
        """Add a folder path to the queue."""
        # Check if already in queue
        for job in self.jobs:
            if job.folder_path == folder_path:
                return
        
        # Count images
        image_count = len(list(Path(folder_path).glob("*.png")))
        
        job = JobItem(
            folder_path=folder_path,
            total_images=image_count
        )
        self.jobs.append(job)
        self._refresh_table()
        self.jobs_changed.emit(self.jobs)
    
    def _remove_selected(self):
        """Remove selected jobs from queue."""
        rows = set()
        for item in self.table.selectedItems():
            rows.add(item.row())
        
        # Remove in reverse order to maintain indices
        for row in sorted(rows, reverse=True):
            if row < len(self.jobs):
                self.jobs.pop(row)
        
        self._refresh_table()
        self.jobs_changed.emit(self.jobs)
    
    def _clear_queue(self):
        """Clear all jobs from queue."""
        self.jobs.clear()
        self._refresh_table()
        self.jobs_changed.emit(self.jobs)
    
    def _refresh_table(self):
        """Refresh the table display."""
        self.table.setRowCount(len(self.jobs))
        
        for row, job in enumerate(self.jobs):
            # Folder name
            folder_name = Path(job.folder_path).name
            folder_item = QTableWidgetItem(folder_name)
            folder_item.setToolTip(job.folder_path)
            folder_item.setFlags(folder_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, folder_item)
            
            # Image count
            count_item = QTableWidgetItem(str(job.total_images))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            count_item.setFlags(count_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, count_item)
            
            # Status
            status_text = {
                'pending': '⏳ Pendiente',
                'processing': '🔄 Procesando',
                'completed': '✓ Completado',
                'error': '✗ Error',
                'cancelled': '⊘ Cancelado'
            }.get(job.status, job.status)
            
            status_item = QTableWidgetItem(status_text)
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # Color by status
            if job.status == 'completed':
                status_item.setForeground(QColor(COLORS['success']))
            elif job.status == 'error':
                status_item.setForeground(QColor(COLORS['error']))
            elif job.status == 'processing':
                status_item.setForeground(QColor('#2196F3'))
            
            self.table.setItem(row, 2, status_item)
            
            # Progress
            progress = QProgressBar()
            progress.setValue(job.progress)
            progress.setFixedHeight(18)
            self.table.setCellWidget(row, 3, progress)
        
        # Update count label
        total_images = sum(j.total_images for j in self.jobs)
        self.lbl_count.setText(f"{len(self.jobs)} carpetas • {total_images} imágenes")
        
        # Enable/disable start button
        can_start = len(self.jobs) > 0 and not self._is_processing
        self.btn_start.setEnabled(can_start)
    
    def _show_context_menu(self, pos):
        """Show context menu for table."""
        menu = QMenu(self)
        
        remove_action = QAction("Quitar de la cola", self)
        remove_action.triggered.connect(self._remove_selected)
        menu.addAction(remove_action)
        
        menu.exec(self.table.mapToGlobal(pos))
    
    def _on_start(self):
        """Handle start button click."""
        if self._is_paused:
            self._is_paused = False
            self.btn_pause.setText(" PAUSAR")
            self.resume_queue.emit()
        else:
            self._is_processing = True
            self._update_ui_for_processing()
            self.start_queue.emit()
    
    def _on_pause(self):
        """Handle pause button click."""
        if self._is_paused:
            self._is_paused = False
            self.btn_pause.setText(" PAUSAR")
            self.resume_queue.emit()
        else:
            self._is_paused = True
            self.btn_pause.setText(" REANUDAR")
            self.pause_queue.emit()
    
    def _on_stop(self):
        """Handle stop button click."""
        self.stop_queue.emit()
    
    def _update_ui_for_processing(self):
        """Update UI when processing starts."""
        self.btn_start.hide()
        self.btn_pause.show()
        self.btn_stop.show()
        self.btn_add.setEnabled(False)
        self.btn_remove.setEnabled(False)
        self.btn_clear.setEnabled(False)
    
    def update_job_progress(self, index: int, progress: int):
        """Update progress for a specific job."""
        if 0 <= index < len(self.jobs):
            self.jobs[index].progress = progress
            # Update progress bar in table
            if self.table.cellWidget(index, 3):
                self.table.cellWidget(index, 3).setValue(progress)
    
    def update_job_status(self, index: int, status: str):
        """Update status for a specific job."""
        if 0 <= index < len(self.jobs):
            self.jobs[index].status = status
            self._refresh_table()
    
    def update_overall_progress(self, completed: int, total: int):
        """Update overall queue progress."""
        if total > 0:
            self.progress_overall.setValue(int((completed / total) * 100))
    
    def on_queue_finished(self):
        """Called when queue processing finishes."""
        self._is_processing = False
        self._is_paused = False
        self.btn_start.show()
        self.btn_pause.hide()
        self.btn_stop.hide()
        self.btn_add.setEnabled(True)
        self.btn_remove.setEnabled(True)
        self.btn_clear.setEnabled(True)
        self._refresh_table()
    
    def get_jobs(self) -> List[JobItem]:
        """Get current job list."""
        return self.jobs
