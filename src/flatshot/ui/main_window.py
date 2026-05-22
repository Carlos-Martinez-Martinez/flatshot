"""
Modern Main Window with Professional UI Layout
"""
import sys
import os
import tempfile
import logging
import subprocess
import traceback
import io
from pathlib import Path
from PIL import Image
from PIL import ImageFile
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QProgressBar, QGroupBox, QComboBox, QFrame, QSpinBox, QInputDialog,
    QMessageBox, QSizePolicy, QFileDialog, QApplication, QCheckBox,
    QScrollArea, QSplitter, QToolButton, QButtonGroup, QDialog, QStackedWidget,
    QMenu, QRadioButton, QListWidget, QListWidgetItem, QSlider
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize, QEvent, QFileSystemWatcher
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor, QPainterPath, QAction, QIcon, QFont

from flatshot.core.models import (
    SHADOW_ENGINE_COMPAT,
    SHADOW_ENGINE_DEFAULT,
    SHADOW_ENGINE_LEGACY,
    SHADOW_ENGINE_REALISTIC_V2,
    ShadowSettings,
    ExportConfig,
    ExportVariant,
    CurveData,
    JobItem,
    WEB_RGB230,
    WHITE_RGB255,
    build_variant_settings,
    normalize_export_variants,
    normalize_shadow_settings,
)
from flatshot.core.overrides import (
    LOCAL_OVERRIDE_DEFAULTS,
    apply_image_override,
    has_image_override,
    normalize_image_override,
    override_key,
)
from flatshot.core.scaling import DEFAULT_SCALE_CURVE, normalize_curve_data
from flatshot.application.app_state import (
    BatchSummary,
    ExportState,
    FlatshotAppState,
    PreviewState,
    ProcessingState,
    UiViewState,
    build_custom_preview_state,
    build_empty_preview_state,
    build_batch_summary,
    build_export_bar_state,
    build_export_state,
    build_mockup_preview_state,
    build_pre_render_bar_status,
    build_queue_export_summary_lines,
    build_single_export_summary_lines,
    calculate_queue_overall_progress,
    format_batch_count_text,
    format_custom_preview_button_text,
    processing_state_after_reset,
    processing_state_for_export_start,
    processing_state_for_pause,
    processing_state_for_queue_job,
    processing_state_for_single_export,
    processing_state_for_stop,
    processing_mode_for_batch,
)
from flatshot.application import presenters
from flatshot.application.contracts import PreviewRequest
from flatshot.application.export_config_service import ExportConfigService
from flatshot.application.folder_scanner import FolderScanner
from flatshot.application.preview_service import PreviewService
from flatshot.application.preset_service import PresetService
from flatshot.application.session_service import SessionService
from flatshot.application.settings_service import SettingsService
from flatshot.utils.config import ConfigManager
from flatshot.utils.history_manager import HistoryManager
from flatshot.utils.log_manager import LogManager
from flatshot.utils.session_manager import SessionManager
from flatshot.ui.dialogs import CurveEditorDialog, ExportConfigDialog, ExportVariantsDialog
from flatshot.ui.styles import scale_stylesheet, COLORS
from flatshot.ui.shell import AppShell, WorkflowPanel, CanvasWorkbench, BatchPanel, ExportBar, CommandBar
from flatshot.ui.widgets import SmartSlider, LightAngleWidget, ComparisonCanvas, FloatingToolbar, ModernSplashScreen, CollapsibleSection
from flatshot.ui.queue_widget import QueueWidget
from flatshot.ui.grid_preview import GridPreviewWidget
from flatshot.workers.export_worker import (
    ExportWorker,
    get_enabled_export_variants,
    variant_export_format,
)
from flatshot.workers.queue_worker import QueueWorker
from flatshot.workers.pre_render_scheduler import PreRenderScheduler

import qtawesome as qta

ImageFile.LOAD_TRUNCATED_IMAGES = True

PRE_RENDER_ACTIVITY_EVENTS = {
    QEvent.Type.MouseButtonPress,
    QEvent.Type.MouseButtonRelease,
    QEvent.Type.MouseButtonDblClick,
    QEvent.Type.MouseMove,
    QEvent.Type.Wheel,
    QEvent.Type.KeyPress,
    QEvent.Type.KeyRelease,
    QEvent.Type.ShortcutOverride,
    QEvent.Type.DragEnter,
    QEvent.Type.DragMove,
    QEvent.Type.Drop,
}


def _render_preview_task(pil_img: Image.Image, target_size, settings_dict: dict, curve_dict: dict, scale_ratio: float, is_preview: bool = True):
    """Render preview off the UI thread; safe for ThreadPoolExecutor."""
    result = PreviewService().render_preview(
        PreviewRequest(
            image=pil_img,
            settings=settings_dict,
            curve_data=curve_dict,
            target_size=tuple(target_size),
            scale_factor=scale_ratio,
            is_preview=is_preview,
        )
    )
    return result.width, result.height, result.bytes_rgb, result.warning


from PyQt6.QtCore import QRunnable, QThreadPool, QObject


class PreviewWorkerSignals(QObject):
    """Signals for PreviewWorker to communicate with main thread."""
    finished = pyqtSignal(object, int, object)  # (QImage, quality_level, warning)
    error = pyqtSignal(str)


class PreviewWorker(QRunnable):
    """Worker to render preview in background thread."""
    
    def __init__(self, pil_img: Image.Image, target_size, settings_dict: dict, 
                 curve_dict: dict, scale_ratio: float, quality_level: int):
        super().__init__()
        self.pil_img = pil_img
        self.target_size = target_size
        self.settings_dict = settings_dict
        self.curve_dict = curve_dict
        self.scale_ratio = scale_ratio
        self.quality_level = quality_level
        self.signals = PreviewWorkerSignals()
        # Keep worker alive until signals are delivered in main thread.
        self.setAutoDelete(False)
    
    def run(self):
        """Execute render in background thread."""
        try:
            width, height, im_data, warning = _render_preview_task(
                self.pil_img,
                self.target_size,
                self.settings_dict,
                self.curve_dict,
                self.scale_ratio
            )
            qim = QImage(im_data, width, height, width * 3, QImage.Format.Format_RGB888).copy()
            # The signal will be queued to the main thread
            self.signals.finished.emit(qim, self.quality_level, warning)
        except Exception as e:
            self.signals.error.emit(str(e))



class MainWindow(QMainWindow):
    """
    Main application window with modern dark UI.
    """
    # Project root = .../flatshot (project). Place logs in flatshot/logs
    # parents[3] of src/flatshot/ui/main_window.py points to project root (flatshot/)
    LOG_DIR = Path(__file__).resolve().parents[3] / "logs"
    LOG_FILE = LOG_DIR / "preview.log"
    
    def __init__(self, ui_scale: float = 1.0):
        super().__init__()
        self.ui_scale = self._normalize_scale(ui_scale)
        self.setWindowTitle("FlatShot")
        self.resize(self._px(1350), self._px(880))
        self.setMinimumSize(self._px(980), self._px(700))
        
        # Managers
        self.config_manager = ConfigManager()
        self.history_manager = HistoryManager()
        self.log_manager = LogManager.get_instance()
        self.session_manager = SessionManager()
        self.folder_scanner = FolderScanner()
        self.export_config_service = ExportConfigService()
        self.config_dir = ConfigManager.get_config_dir()
        self.preset_service = PresetService(self.config_dir)
        
        # State
        self.selected_folders = []  # List of Path objects for multi-folder export
        self.mockups = self._generate_mockups()
        self.current_mock = 'dark'
        self.current_qimage = None
        self._preview_pending = False
        self.preview_pool = QThreadPool()
        self.preview_pool.setMaxThreadCount(2)
        self._active_preview_workers = set()
        self.current_base_pil = None  # Cached downsampled PIL for fast preview
        self.current_orig_pixmap = None  # Cached QPixmap for comparison
        # Log where we will write
        self._setup_logger().info(f"[init] log at {self.LOG_FILE}")
        
        # Preview settings - single optimized quality for responsiveness
        self.preview_scale_ratio = 0.45  # Balanced quality/speed (810x1080)
        self.preview_size = (int(1800 * self.preview_scale_ratio), 
                            int(2400 * self.preview_scale_ratio))
        
        # --- Responsiveness infrastructure ---
        # Track whether any SmartSlider is being dragged so we can skip
        # expensive work (grid refresh, disk writes) during interaction.
        self._slider_dragging = False

        # Fast debounce for canvas-only preview (during drag)
        self.preview_timer = QTimer()
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self._start_preview_thread)

        # Deferred grid sync timer — only fires after slider release
        self._grid_sync_timer = QTimer()
        self._grid_sync_timer.setSingleShot(True)
        self._grid_sync_timer.timeout.connect(self._deferred_grid_sync)

        # Deferred settings-save timer — coalesce disk writes
        self._save_settings_timer = QTimer()
        self._save_settings_timer.setSingleShot(True)
        self._save_settings_timer.timeout.connect(self._flush_app_settings)
        
        # Queue worker reference
        self.queue_worker = None
        self.worker = None
        self.export_state = ExportState()
        self.preview_state = PreviewState()
        self.current_custom_path = None
        self._watched_folders = set()
        self._pending_folder_updates = set()
        self.folder_watcher = QFileSystemWatcher(self)
        self.folder_watcher.directoryChanged.connect(self._on_source_folder_changed)
        self._folder_update_timer = QTimer()
        self._folder_update_timer.setSingleShot(True)
        self._folder_update_timer.timeout.connect(self._process_folder_updates)
        
        # Load configuration
        self.presets = self.preset_service.load_flat_presets()
        if not self.presets:
            self.presets = self._get_default_presets()
            
        self.settings_file = self.config_dir / "settings.json"
        self.settings_service = SettingsService(self.settings_file)
        self.app_settings = self._load_app_settings()
        self.export_variants = normalize_export_variants(self.app_settings)
        self.app_settings['variants'] = [variant.model_dump() for variant in self.export_variants]
        saved_preview_variant = self.app_settings.get('current_preview_variant_id')
        variant_ids = {variant.id for variant in self.export_variants}
        self.current_preview_variant_id = (
            saved_preview_variant if saved_preview_variant in variant_ids else self.export_variants[0].id
        )
        self.app_settings['current_preview_variant_id'] = self.current_preview_variant_id
        self.export_bar_mode = "idle"
        self._export_bar_status_text = ""
        self._pre_render_bar_status = None
        self.ui_view_state = UiViewState(
            grid_columns=int(self.app_settings.get('grid_columns', 3)),
            preview_background=self.app_settings.get('preview_bg_color', "#E6E6E6"),
            guides_enabled=bool(self.app_settings.get('preview_grid', False)),
            advanced_open=bool(self.app_settings.get('section_visibility', {}).get('advanced', False)),
        )
        self.batch_summary = BatchSummary()
        self.app_state = FlatshotAppState(
            batch=self.batch_summary,
            export=self.export_state,
            preview=self.preview_state,
            view=self.ui_view_state,
        )

        # --- Background Pre-rendering ---
        self.pre_render_scheduler = PreRenderScheduler(
            idle_ms=int(self.app_settings.get('background_pre_render_idle_ms', 8000)),
            max_cache_bytes=int(self.app_settings.get('background_pre_render_cache_mb', 2048)) * 1024 * 1024,
            busy_callback=self._pre_render_should_pause,
            parent=self,
        )
        self.pre_render_scheduler.status_changed.connect(self._on_pre_render_status)
        self.pre_render_scheduler.error.connect(self._log_error)
        
        curve_dict = self.app_settings.get('scale_curve', DEFAULT_SCALE_CURVE.copy())
        self.scale_curve = normalize_curve_data(curve_dict)
        loaded_overrides = self.app_settings.get('image_overrides', {})
        self.image_overrides = {
            str(key): normalize_image_override(value)
            for key, value in loaded_overrides.items()
            if has_image_override(value)
        } if isinstance(loaded_overrides, dict) else {}
        self._local_override_history = {}
        self._local_override_edit_key = None
        self._syncing_local_override_ui = False
        
        # Build UI
        self._init_menu()
        self._init_ui()
        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)
        self._apply_export_preferences(self._build_export_config_from_settings())
        self._setup_history_tracking()
        self._setup_accessibility_and_tab_order()
        
        # Initial state
        # Restore session if available
        restored = self._restore_session()
        
        if not restored and self.combo_presets.count() > 0:
            self._apply_preset_from_combo()
        elif not restored:
            self._schedule_preview()
        self._push_history()
        if not restored:
            # Only force grid fitting if we don't have a saved session size
            QTimer.singleShot(0, self._show_maximized_workspace)
        else:
            self.showMaximized()
    
    def _normalize_scale(self, scale: float) -> float:
        """Clamp the incoming UI scale to a safe range."""
        try:
            return max(min(scale, 1.0), 0.65)
        except Exception:
            return 1.0
    
    def _px(self, value: int) -> int:
        """Scale a pixel value according to the UI scale."""
        return max(int(round(value * self.ui_scale)), 1)

    def _set_widget_class(self, widget: QWidget, class_name: str):
        """Update a widget class property and refresh its style."""
        if widget is None:
            return
        widget.setProperty("class", class_name)
        try:
            widget.style().unpolish(widget)
            widget.style().polish(widget)
        except Exception:
            pass
            
    # ========== UI INITIALIZATION ==========
    
    def _init_menu(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("Archivo")
        
        calib_action = QAction("Calibrar escala inteligente...", self)
        calib_action.triggered.connect(self._open_scale_calibrator)
        file_menu.addAction(calib_action)
        
        config_action = QAction("Configuración de exportación...", self)
        config_action.setShortcut("Ctrl+,")
        config_action.triggered.connect(self._open_export_config)
        file_menu.addAction(config_action)
        
        file_menu.addSeparator()

        export_presets_action = QAction("Exportar presets...", self)
        export_presets_action.triggered.connect(self._action_export_presets)
        file_menu.addAction(export_presets_action)

        import_presets_action = QAction("Importar presets...", self)
        import_presets_action.triggered.connect(self._action_import_presets)
        file_menu.addAction(import_presets_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Salir", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        preset_menu = menubar.addMenu("Presets")

        save_preset_action = QAction("Guardar preset actual", self)
        save_preset_action.setShortcut("Ctrl+S")
        save_preset_action.triggered.connect(self._action_save_current)
        preset_menu.addAction(save_preset_action)

        new_preset_action = QAction("Crear preset...", self)
        new_preset_action.triggered.connect(self._action_create_new)
        preset_menu.addAction(new_preset_action)

        rename_preset_action = QAction("Renombrar preset...", self)
        rename_preset_action.triggered.connect(self._action_rename)
        preset_menu.addAction(rename_preset_action)

        delete_preset_action = QAction("Eliminar preset", self)
        delete_preset_action.triggered.connect(self._action_delete)
        preset_menu.addAction(delete_preset_action)

        preset_menu.addSeparator()

        preset_import_action = QAction("Importar presets...", self)
        preset_import_action.triggered.connect(self._action_import_presets)
        preset_menu.addAction(preset_import_action)

        preset_export_action = QAction("Exportar presets...", self)
        preset_export_action.triggered.connect(self._action_export_presets)
        preset_menu.addAction(preset_export_action)

        open_preset_folder_action = QAction("Abrir carpeta de presets", self)
        open_preset_folder_action.triggered.connect(self._action_open_presets_folder)
        preset_menu.addAction(open_preset_folder_action)
        
        # View menu
        view_menu = menubar.addMenu("Ver")
        
        grid_action = QAction("Mostrar cuadrícula", self, checkable=True)
        grid_action.triggered.connect(self._on_preview_grid_toggled)
        view_menu.addAction(grid_action)
        
        # Help menu
        help_menu = menubar.addMenu("Ayuda")
        
        shortcuts_action = QAction("Atajos de teclado...", self)
        shortcuts_action.setShortcut("F1")
        shortcuts_action.triggered.connect(self._show_shortcuts_dialog)
        help_menu.addAction(shortcuts_action)
        
        # === SHORTCUTS ===
        save_shortcut = QAction(self)
        save_shortcut.setShortcut("Ctrl+S")
        save_shortcut.triggered.connect(self._action_save_current)
        self.addAction(save_shortcut)
        
        reset_shortcut = QAction(self)
        reset_shortcut.setShortcut("Ctrl+R")
        reset_shortcut.triggered.connect(self._reset_to_defaults)
        self.addAction(reset_shortcut)
        
        mock1_shortcut = QAction(self)
        mock1_shortcut.setShortcut("1")
        mock1_shortcut.triggered.connect(lambda: self._set_mock_color("light"))
        self.addAction(mock1_shortcut)
        
        mock2_shortcut = QAction(self)
        mock2_shortcut.setShortcut("2")
        mock2_shortcut.triggered.connect(lambda: self._set_mock_color("medium"))
        self.addAction(mock2_shortcut)
        
        mock3_shortcut = QAction(self)
        mock3_shortcut.setShortcut("3")
        mock3_shortcut.triggered.connect(lambda: self._set_mock_color("dark"))
        self.addAction(mock3_shortcut)
        
        # Undo/Redo shortcuts
        undo_shortcut = QAction(self)
        undo_shortcut.setShortcut("Ctrl+Z")
        undo_shortcut.triggered.connect(self._action_undo)
        self.addAction(undo_shortcut)
        
        redo_shortcut = QAction(self)
        redo_shortcut.setShortcut("Ctrl+Y")
        redo_shortcut.triggered.connect(self._action_redo)
        self.addAction(redo_shortcut)

        process_shortcut = QAction(self)
        process_shortcut.setShortcut("Ctrl+Return")
        process_shortcut.triggered.connect(self._start_export)
        self.addAction(process_shortcut)

        pause_shortcut = QAction(self)
        pause_shortcut.setShortcut("Ctrl+Shift+P")
        pause_shortcut.triggered.connect(self._toggle_pause)
        self.addAction(pause_shortcut)

        stop_shortcut = QAction(self)
        stop_shortcut.setShortcut("Esc")
        stop_shortcut.triggered.connect(self._stop_export)
        self.addAction(stop_shortcut)
        
        # Edit menu
        edit_menu = menubar.addMenu("Editar")
        
        undo_action = QAction("Deshacer", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self._action_undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("Rehacer", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self._action_redo)
        edit_menu.addAction(redo_action)
        
        # Add View Log to File menu (insert before exit)
        file_menu.insertSeparator(exit_action)
        log_action = QAction("Ver registro de actividad...", self)
        log_action.triggered.connect(self._show_log_viewer)
        file_menu.insertAction(exit_action, log_action)
        
    def _init_ui(self):
        shell = AppShell()
        self.app_shell = shell
        self.setCentralWidget(shell)
        
        # === LEFT PANEL (Controls) ===
        left_panel = self._create_control_panel()
        self.left_panel = left_panel
        
        # === CENTER PANEL (Canvas Preview) ===
        center_panel = self._create_preview_panel()
        self.center_panel = center_panel
        
        # === RIGHT PANEL (Grid Preview) ===
        right_panel = self._create_grid_panel()
        self.right_panel = right_panel
        
        # Splitter for resizable panels (3 columns)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(left_panel)
        self.splitter.addWidget(center_panel)
        self.splitter.addWidget(right_panel)
        self.splitter.setSizes([self._px(320), self._px(960), self._px(640)])
        self.splitter.setStretchFactor(0, 0)  # Controls: fixed
        self.splitter.setStretchFactor(1, 1)  # Canvas: stretch
        self.splitter.setStretchFactor(2, 0)  # Grid: fixed
        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(2, False)
        if isinstance(self.app_settings.get('splitter_sizes'), list):
            try:
                self.splitter.setSizes(self.app_settings.get('splitter_sizes'))
            except Exception:
                pass
        self._splitter_save_timer = QTimer()
        self._splitter_save_timer.setSingleShot(True)
        self._splitter_save_timer.timeout.connect(self._save_splitter_sizes)
        self.splitter.splitterMoved.connect(lambda *_: self._splitter_save_timer.start(250))
        
        shell.main_layout.addWidget(self.splitter, 1)

        export_bar = self._create_export_section()
        self.export_section = export_bar
        self.export_bar = export_bar
        shell.main_layout.addWidget(export_bar, 0)

    def _show_maximized_workspace(self):
        self.showMaximized()
        QTimer.singleShot(0, lambda: self._fit_workspace_to_grid(force=False))

    def _target_grid_panel_width(self, columns: int | None = None) -> int:
        if columns is None:
            columns = int(self.app_settings.get('grid_columns', 1))
        columns = min(max(int(columns), 1), 3)
        targets = {
            1: 420,
            2: 540,
            3: 640,
        }
        return self._px(targets[columns])

    def _apply_grid_panel_width_policy(self, columns: int | None = None):
        if not hasattr(self, 'right_panel'):
            return
        target = self._target_grid_panel_width(columns)
        self.right_panel.setMinimumWidth(target)
        self.right_panel.setMaximumWidth(self._px(740))

    def _fit_workspace_to_grid(self, columns: int | None = None, force: bool = False):
        if not hasattr(self, 'splitter'):
            return
        self._apply_grid_panel_width_policy(columns)
        target_right = self._target_grid_panel_width(columns)
        sizes = self.splitter.sizes()
        if not force and len(sizes) == 3 and sizes[2] >= target_right - self._px(12):
            return

        total = max(self.splitter.width(), self.width(), self._px(1600))
        left = self._px(300)
        center = max(total - left - target_right, self._px(720))
        self.splitter.setSizes([left, center, target_right])
        
    def _create_control_panel(self) -> QWidget:
        """Create the workflow panel with batch-level adjustments."""
        panel = WorkflowPanel()
        panel.setMinimumWidth(self._px(340))
        panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setProperty("class", "panel-scroll")
        
        content = QWidget()
        content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(self._px(12), self._px(16), self._px(12), self._px(14))
        layout.setSpacing(self._px(14))
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetMinimumSize)
        
        header = QLabel("Ajustes del lote")
        header.setProperty("class", "workflow-title")
        layout.addWidget(header)

        flow_hint = QLabel("Importar -> Ajustar -> Revisar -> Exportar")
        flow_hint.setProperty("class", "workflow-subtitle")
        layout.addWidget(flow_hint)
        
        self._sections = {}
        presets_section = self._create_section("PRESET ACTIVO", "presets", default_expanded=True, parent=content)
        if presets_section is not None:
            layout.addWidget(presets_section)
            self._sections["presets"] = presets_section
            self._build_presets_section(presets_section.content_layout)

        essentials = QFrame()
        essentials.setProperty("class", "essential-card")
        essentials_layout = QVBoxLayout(essentials)
        essentials_layout.setContentsMargins(self._px(8), self._px(8), self._px(8), self._px(8))
        essentials_layout.setSpacing(self._px(6))

        essentials_title = QLabel("Controles esenciales")
        essentials_title.setProperty("class", "panel-title")
        essentials_layout.addWidget(essentials_title)
        self._build_essential_controls(essentials_layout)
        layout.addWidget(essentials)

        self.local_adjust_panel = self._create_local_adjustment_bar(orientation="vertical")
        layout.addWidget(self.local_adjust_panel)

        advanced_section = self._create_section("AVANZADO", "advanced", default_expanded=False, parent=content)
        if advanced_section is not None:
            layout.addWidget(advanced_section)
            self._sections["advanced"] = advanced_section
            self._build_lighting_section(advanced_section.content_layout)
            self._build_shadows_section(advanced_section.content_layout)
            self._build_finishing_section(advanced_section.content_layout)

        layout.addStretch()
        scroll.setWidget(content)
        
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)
        panel_layout.addWidget(scroll, 1)
        return panel

    def _on_section_toggled(self, key: str, checked: bool):
        section_state = self.app_settings.get('section_visibility', {})
        section_state[key] = bool(checked)
        self.app_settings['section_visibility'] = section_state
        if key == "advanced":
            self.ui_view_state.advanced_open = bool(checked)
        self._save_app_settings()

    def _create_section(self, title: str, key: str, default_expanded: bool, parent: QWidget) -> CollapsibleSection:
        """Create a collapsible section with Lightroom-like behavior."""
        if parent is None or parent.layout() is None:
            return None
        section_state = self.app_settings.get('section_visibility', {})
        expanded = bool(section_state.get(key, default_expanded))
        section = CollapsibleSection(title, expanded=expanded, parent=parent)
        section.toggled.connect(lambda checked, k=key: self._on_section_toggled(k, checked))
        return section
    
    def _build_presets_section(self, layout: QVBoxLayout):
        """Populate the presets management section."""
        layout.setSpacing(self._px(10))
        
        # Combo box
        self.combo_presets = QComboBox()
        self.combo_presets.setProperty("class", "compact")
        self.combo_presets.addItems(list(self.presets.keys()))
        self.combo_presets.currentIndexChanged.connect(self._apply_preset_from_combo)
        layout.addWidget(self.combo_presets)
        
        # Preset actions use text because they affect persistent settings.
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(self._px(6))
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(self._px(6))
        
        # Icon color for dark theme
        icon_color = COLORS['text_muted']
        icon_color_danger = COLORS['error']
        
        btn_save = QPushButton(qta.icon('fa5s.save', color=icon_color), "Guardar")
        btn_save.setProperty("class", "preset-action")
        btn_save.setToolTip("Guardar preset (Ctrl+S)")
        btn_save.clicked.connect(self._action_save_current)
        btn_layout.addWidget(btn_save)
        
        btn_new = QPushButton(qta.icon('fa5s.plus', color=icon_color), "Nuevo")
        btn_new.setProperty("class", "preset-action")
        btn_new.setToolTip("Crear nuevo preset")
        btn_new.clicked.connect(self._action_create_new)
        btn_layout.addWidget(btn_new)

        actions_layout.addLayout(btn_layout)

        btn_layout_2 = QHBoxLayout()
        btn_layout_2.setSpacing(self._px(6))
        
        btn_rename = QPushButton(qta.icon('fa5s.edit', color=icon_color), "Renombrar")
        btn_rename.setProperty("class", "preset-action")
        btn_rename.setToolTip("Renombrar preset")
        btn_rename.clicked.connect(self._action_rename)
        btn_layout_2.addWidget(btn_rename)
        
        btn_delete = QPushButton(qta.icon('fa5s.trash-alt', color=icon_color_danger), "Eliminar")
        btn_delete.setProperty("class", "preset-action-danger")
        btn_delete.setToolTip("Eliminar preset")
        btn_delete.clicked.connect(self._action_delete)
        btn_layout_2.addWidget(btn_delete)
        
        # Reset to defaults button
        btn_reset = QPushButton(qta.icon('fa5s.undo', color=COLORS['text_muted']), "Reset")
        btn_reset.setProperty("class", "preset-action")
        btn_reset.setToolTip("Restaurar valores por defecto (Ctrl+R)")
        btn_reset.clicked.connect(self._reset_to_defaults)
        btn_layout_2.addWidget(btn_reset)

        btn_more = QToolButton()
        btn_more.setIcon(qta.icon('fa5s.ellipsis-h', color=icon_color))
        btn_more.setToolTip("Más opciones de presets")
        btn_more.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        btn_more.setAutoRaise(True)

        more_menu = QMenu(btn_more)
        import_action = more_menu.addAction("Importar presets...")
        import_action.triggered.connect(self._action_import_presets)
        export_action = more_menu.addAction("Exportar presets...")
        export_action.triggered.connect(self._action_export_presets)
        more_menu.addSeparator()
        open_folder_action = more_menu.addAction("Abrir carpeta de presets")
        open_folder_action.triggered.connect(self._action_open_presets_folder)
        btn_more.setMenu(more_menu)
        btn_layout_2.addWidget(btn_more)
        
        actions_layout.addLayout(btn_layout_2)
        layout.addLayout(actions_layout)
        
        # Status label
        self.lbl_status = QLabel("")
        self.lbl_status.setProperty("class", "muted")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_status)
        
        return

    def _build_essential_controls(self, layout: QVBoxLayout):
        """Expose the controls that affect day-to-day batch balance."""
        self.sl_scale_adjustment = SmartSlider(
            "Tamaño producto", -30, 30, 0, "%",
            "<b>Tamaño global del producto</b><br><br>"
            "Ajuste fino aplicado sobre la escala inteligente del preset.<br>"
            "Úsalo para hacer todo el lote ligeramente más grande o pequeño.",
            scale=self.ui_scale
        )
        self.sl_scale_adjustment.valueChanged.connect(self._schedule_preview)
        layout.addWidget(self.sl_scale_adjustment)

        self.sl_padding = SmartSlider(
            "Margen", 0, 50, 10, "%",
            "<b>Margen / espacio</b><br><br>"
            "Define el aire alrededor del producto dentro del lienzo final.",
            scale=self.ui_scale
        )
        self.sl_padding.valueChanged.connect(self._schedule_preview)
        layout.addWidget(self.sl_padding)

        self.sl_opacity = SmartSlider(
            "Sombra", 0, 100, 30, "%",
            "<b>Intensidad de sombra</b><br><br>"
            "Controla la presencia general de la sombra en el lote.",
            scale=self.ui_scale
        )
        self.sl_opacity.valueChanged.connect(self._schedule_preview)
        layout.addWidget(self.sl_opacity)

        self.sl_blur = SmartSlider(
            "Suavidad", 0, 100, 25, "px",
            "<b>Suavidad de sombra</b><br><br>"
            "Ajusta lo difusa o marcada que se percibe la sombra.",
            scale=self.ui_scale
        )
        self.sl_blur.valueChanged.connect(self._schedule_preview)
        layout.addWidget(self.sl_blur)
    
    def _build_lighting_section(self, layout: QVBoxLayout):
        """Populate the lighting controls section."""
        layout.setSpacing(self._px(12))
        
        # Light angle widget with label
        angle_layout = QHBoxLayout()
        
        angle_label_layout = QVBoxLayout()
        angle_label = QLabel("Dirección de sombra")
        angle_label.setProperty("class", "param-label")
        angle_label.setToolTip(
            "<b>Ángulo de caída de la sombra</b><br><br>"
            "Define hacia dónde cae la sombra.<br>"
            "<b>0°</b> = Arriba<br>"
            "<b>90°</b> = Derecha<br>"
            "<b>180°</b> = Abajo<br>"
            "<b>270°</b> = Izquierda"
        )
        angle_label_layout.addWidget(angle_label)
        
        self.angle_spinbox = QSpinBox()
        self.angle_spinbox.setRange(0, 359)
        self.angle_spinbox.setSuffix("°")
        self.angle_spinbox.setValue(180)
        self.angle_spinbox.setToolTip("Ángulo exacto de caída de sombra en grados (0-359)")
        angle_label_layout.addWidget(self.angle_spinbox)
        angle_label_layout.addStretch()
        
        angle_layout.addLayout(angle_label_layout)
        
        self.light_angle = LightAngleWidget(scale=self.ui_scale)
        self.light_angle.setToolTip(
            "<b>Control circular de ángulo</b><br><br>"
            "Haz clic y arrastra para ajustar hacia dónde cae la sombra."
        )
        self.light_angle.angleChanged.connect(self._on_angle_changed)
        self.angle_spinbox.valueChanged.connect(self._on_angle_spinbox_changed)
        angle_layout.addWidget(self.light_angle)
        angle_layout.addStretch()
        
        layout.addLayout(angle_layout)
        
        # Distance slider
        self.sl_distance = SmartSlider(
            "Distancia", 0, 200, 30, "px",
            "<b>Distancia de proyección</b><br><br>"
            "Controla qué tan lejos se proyecta la sombra del objeto.<br><br>"
            "<b>Valores bajos (0-30):</b> Sombra cercana, objeto parece pegado al fondo<br>"
            "<b>Valores medios (30-80):</b> Efecto natural de elevación<br>"
            "<b>Valores altos (80+):</b> Objeto muy elevado, sombra muy separada",
            scale=self.ui_scale
        )
        self.sl_distance.valueChanged.connect(self._schedule_preview)
        layout.addWidget(self.sl_distance)
        
        return
    
    def _build_shadows_section(self, layout: QVBoxLayout):
        """Populate the shadow controls section."""
        layout.setSpacing(self._px(8))

        self.sl_spread = SmartSlider(
            "Expansión", 0, 10, 0, "px",
            "<b>Expansión de sombra (Spread)</b><br><br>"
            "Agranda la silueta de la sombra más allá del contorno del objeto.<br><br>"
            "<b>0:</b> La sombra sigue exactamente la forma del objeto<br>"
            "<b>1-5:</b> Añade un halo sutil alrededor<br>"
            "<b>5+:</b> Efecto de resplandor oscuro",
            scale=self.ui_scale
        )
        self.sl_spread.valueChanged.connect(self._schedule_preview)
        layout.addWidget(self.sl_spread)
        
        self.sl_fusion = SmartSlider(
            "Sangrado", 0, 20, 2, "px",
            "<b>Sangrado / Fusión (Bleed)</b><br><br>"
            "Controla cómo la sombra se fusiona con el objeto en sus bordes.<br><br>"
            "<b>0-2:</b> Sin fusión, la sombra no invade el objeto<br>"
            "<b>3-8:</b> Fusión natural, simula subsurface scattering<br>"
            "<b>8+:</b> Fusión intensa, sombra oscurece bordes del objeto",
            scale=self.ui_scale
        )
        self.sl_fusion.valueChanged.connect(self._schedule_preview)
        layout.addWidget(self.sl_fusion)
        
        self.sl_contact_blur = SmartSlider(
            "Blur Base", 0, 50, 10, "px",
            "<b>Desenfoque de contacto</b><br><br>"
            "Suavidad de la sombra en la zona de 'contacto' con el suelo.<br><br>"
            "Esta sombra más oscura simula el punto donde el objeto<br>"
            "toca la superficie. Valores bajos = sombra de contacto nítida.",
            scale=self.ui_scale
        )
        self.sl_contact_blur.valueChanged.connect(self._schedule_preview)
        layout.addWidget(self.sl_contact_blur)
        
        self.sl_contraction = SmartSlider(
            "Contracción", 0, 5, 0, "px",
            "<b>Contracción de silueta (Contract)</b><br><br>"
            "Reduce el tamaño de la silueta original de la prenda.<br><br>"
            "Ideal para eliminar halos de color (residuales del fondo original)<br>"
            "que pueden aparecer en los bordes. 1-2px suele ser suficiente.",
            scale=self.ui_scale
        )
        self.sl_contraction.valueChanged.connect(self._schedule_preview)
        layout.addWidget(self.sl_contraction)
        
        return
    
    def _build_finishing_section(self, layout: QVBoxLayout):
        """Populate the finishing touches section."""
        layout.setSpacing(self._px(8))

        self.sl_noise = SmartSlider(
            "Ruido", 0, 50, 0, "%",
            "<b>Textura de ruido (Grain)</b><br><br>"
            "Añade granulado a la sombra para simular imperfecciones.<br><br>"
            "<b>0:</b> Sombra limpia y digital<br>"
            "<b>5-15%:</b> Textura sutil, más realista<br>"
            "<b>15%+:</b> Efecto vintage/película muy visible",
            scale=self.ui_scale
        )
        self.sl_noise.valueChanged.connect(self._schedule_preview)
        layout.addWidget(self.sl_noise)

        # Adaptive zoom checkbox
        self.chk_adaptive = QCheckBox("Compensación óptica inteligente")
        self.chk_adaptive.setChecked(True)
        self.chk_adaptive.setToolTip(
            "<b>Compensación óptica automática</b><br><br>"
            "Ajusta el tamaño del producto según su geometría y su masa visual.<br><br>"
            "Combina la proporción de la silueta con su ocupación real<br>"
            "para equilibrar mejor camisetas, pantalones, prendas oversize<br>"
            "y piezas con huecos o volúmenes distintos.<br><br>"
            "<b>Activado:</b> Tamaño perceptualmente uniforme<br>"
            "<b>Desactivado:</b> Escalado matemático puro"
        )
        self.chk_adaptive.toggled.connect(self._schedule_preview)
        layout.addWidget(self.chk_adaptive)

        engine_row = QHBoxLayout()
        engine_label = QLabel("Motor de sombra")
        engine_label.setProperty("class", "param-label")
        engine_label.setToolTip(
            "<b>Motor de sombra</b><br><br>"
            "<b>Realista V2:</b> más rápido y natural, recomendado.<br>"
            "<b>Clásico:</b> mantiene el aspecto de versiones anteriores."
        )
        engine_row.addWidget(engine_label)

        self.combo_shadow_engine = QComboBox()
        self.combo_shadow_engine.addItem("Realista V2", SHADOW_ENGINE_REALISTIC_V2)
        self.combo_shadow_engine.addItem("Clásico", SHADOW_ENGINE_LEGACY)
        self.combo_shadow_engine.setToolTip(
            "Realista V2: más rápido y natural, recomendado.\n"
            "Clásico: mantiene el aspecto de versiones anteriores."
        )
        self.combo_shadow_engine.currentIndexChanged.connect(self._schedule_preview)
        engine_row.addWidget(self.combo_shadow_engine, 1)
        layout.addLayout(engine_row)
        
        return
    
    def _create_export_section(self) -> QFrame:
        """Create the persistent bottom export bar."""
        bar = ExportBar()
        bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        bar.setMinimumHeight(self._px(88))
        bar.setMaximumHeight(self._px(104))

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(self._px(14), self._px(8), self._px(14), self._px(8))
        layout.setSpacing(self._px(12))
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(self._create_export_input_cluster(), 0)
        layout.addWidget(self._create_export_batch_cluster(), 0)
        layout.addWidget(self._create_export_config_cluster(), 1)
        layout.addWidget(self._create_export_progress_cluster(), 0)
        layout.addWidget(self._create_export_action_cluster(), 0)

        self._create_hidden_export_state_controls(bar)

        self.selected_folders = []
        self.custom_output_path = None
        self.export_details_visible = False
        self._refresh_export_variants_ui()
        self._update_export_bar_state()

        return bar

    def _create_export_input_cluster(self) -> QFrame:
        cluster = QFrame()
        cluster.setProperty("class", "export-cluster")
        cluster.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        layout = QHBoxLayout(cluster)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(self._px(8))

        icon_color = COLORS['text_muted']
        self.btn_add_folder = QPushButton(qta.icon('fa5s.folder-plus', color=icon_color), "Añadir carpeta")
        self.btn_add_folder.setProperty("class", "secondary")
        self.btn_add_folder.setToolTip("Añadir carpeta · Click derecho: carpetas recientes")
        self.btn_add_folder.setAccessibleName("Añadir carpeta")
        self.btn_add_folder.clicked.connect(self._add_folders)
        self.btn_add_folder.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.btn_add_folder.customContextMenuRequested.connect(self._show_recent_folders_menu)
        self.recent_folders_menu = QMenu(self)
        self._update_recent_folders_menu()
        layout.addWidget(self.btn_add_folder)

        self.btn_clear_folders = QPushButton(qta.icon('fa5s.trash-alt', color=COLORS['error']), "Limpiar")
        self.btn_clear_folders.setProperty("class", "ghost")
        self.btn_clear_folders.setToolTip("Limpiar lote cargado")
        self.btn_clear_folders.setAccessibleName("Limpiar lote")
        self.btn_clear_folders.clicked.connect(self._clear_folders)
        self.btn_clear_folders.setEnabled(False)
        layout.addWidget(self.btn_clear_folders)
        return cluster

    def _create_export_batch_cluster(self) -> QFrame:
        cluster = QFrame()
        cluster.setProperty("class", "export-summary")
        cluster.setMinimumWidth(self._px(260))
        cluster.setMaximumWidth(self._px(360))
        layout = QVBoxLayout(cluster)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(self._px(3))

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(self._px(6))
        title = QLabel("Lote")
        title.setProperty("class", "toolbar-section-label")
        header.addWidget(title)
        header.addStretch(1)

        self.btn_export_details = QPushButton(qta.icon('fa5s.list-alt', color=COLORS['text_muted']), "Ver lote")
        self.btn_export_details.setProperty("class", "ghost")
        self.btn_export_details.setFixedHeight(self._px(26))
        self.btn_export_details.setToolTip("Ver carpetas seleccionadas y destino")
        self.btn_export_details.setAccessibleName("Ver lote")
        self.btn_export_details.clicked.connect(self._open_export_details_dialog)
        self.btn_export_details.setEnabled(False)
        header.addWidget(self.btn_export_details)
        layout.addLayout(header)

        self.lbl_folder_summary = QLabel("Sin lote cargado")
        self.lbl_folder_summary.setProperty("class", "export-summary-title")
        self.lbl_folder_summary.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.lbl_folder_summary)
        return cluster

    def _create_export_config_cluster(self) -> QFrame:
        cluster = QFrame()
        cluster.setProperty("class", "export-config")
        cluster.setMinimumWidth(self._px(420))
        cluster.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(cluster)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(self._px(3))

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(self._px(6))
        title = QLabel("Exportación")
        title.setProperty("class", "toolbar-section-label")
        header.addWidget(title)
        header.addStretch(1)

        self.btn_outputs = QPushButton("Salidas")
        self.btn_outputs.setProperty("class", "ghost")
        self.btn_outputs.setFixedHeight(self._px(26))
        self.btn_outputs.setToolTip("Editar versiones de salida")
        self.btn_outputs.setAccessibleName("Editar salidas")
        self.btn_outputs.clicked.connect(self._open_export_variants_dialog)
        header.addWidget(self.btn_outputs)

        self.btn_export_config = QPushButton("Configurar")
        self.btn_export_config.setProperty("class", "secondary")
        self.btn_export_config.setFixedHeight(self._px(26))
        self.btn_export_config.setToolTip("Configurar tamaño, formato, destino y nomenclatura")
        self.btn_export_config.setAccessibleName("Configurar exportación")
        self.btn_export_config.clicked.connect(self._open_export_config)
        header.addWidget(self.btn_export_config)
        layout.addLayout(header)

        self.lbl_export_config_summary = QLabel("")
        self.lbl_export_config_summary.setProperty("class", "export-summary-title")
        self.lbl_export_config_summary.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.lbl_export_config_summary)

        self.lbl_destination_summary = QLabel("")
        self.lbl_destination_summary.setProperty("class", "export-summary-subtitle")
        self.lbl_destination_summary.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.lbl_destination_summary)

        self.lbl_outputs_summary = QLabel("")
        self.lbl_outputs_summary.setProperty("class", "export-summary-subtitle")
        self.lbl_outputs_summary.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.lbl_outputs_summary)
        return cluster

    def _create_export_progress_cluster(self) -> QFrame:
        cluster = QFrame()
        cluster.setProperty("class", "export-progress")
        cluster.setMinimumWidth(self._px(260))
        cluster.setMaximumWidth(self._px(320))
        layout = QVBoxLayout(cluster)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(self._px(5))

        state_title = QLabel("Estado")
        state_title.setProperty("class", "toolbar-section-label")
        layout.addWidget(state_title)

        self.lbl_progress_status = QLabel("Añade una carpeta para procesar")
        self.lbl_progress_status.setProperty("class", "export-summary-subtitle")
        self.lbl_progress_status.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.lbl_progress_status)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(self._px(8))
        self.progress_bar.setMinimumWidth(self._px(220))
        self.progress_bar.setMaximumWidth(self._px(300))
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        return cluster

    def _create_export_action_cluster(self) -> QFrame:
        cluster = QFrame()
        cluster.setProperty("class", "export-actions")
        cluster.setMinimumWidth(self._px(190))
        cluster.setMaximumWidth(self._px(270))
        layout = QHBoxLayout(cluster)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(self._px(8))

        self.btn_process = QPushButton(qta.icon('fa5s.play', color='white'), "Procesar lote")
        self.btn_process.setProperty("class", "primary")
        self.btn_process.setEnabled(False)
        self.btn_process.setMinimumWidth(self._px(185))
        self.btn_process.setToolTip("Iniciar el procesamiento del lote (Ctrl+Enter)")
        self.btn_process.setAccessibleName("Procesar lote")
        self.btn_process.clicked.connect(self._start_export)

        process_controls_widget = QWidget()
        process_controls_layout = QHBoxLayout(process_controls_widget)
        process_controls_layout.setContentsMargins(0, 0, 0, 0)
        process_controls_layout.setSpacing(self._px(6))

        self.btn_pause = QPushButton(qta.icon('fa5s.pause', color='white'), "Pausar")
        self.btn_pause.setProperty("class", "warning-solid")
        self.btn_pause.setToolTip("Pausar/Reanudar el procesamiento (Ctrl+Shift+P)")
        self.btn_pause.setAccessibleName("Pausar procesamiento")
        self.btn_pause.clicked.connect(self._toggle_pause)
        process_controls_layout.addWidget(self.btn_pause)

        self.btn_stop = QPushButton(qta.icon('fa5s.stop', color='white'), "Detener")
        self.btn_stop.setProperty("class", "danger-solid")
        self.btn_stop.setToolTip("Detener el procesamiento en curso (Esc)")
        self.btn_stop.setAccessibleName("Detener procesamiento")
        self.btn_stop.clicked.connect(self._stop_export)
        process_controls_layout.addWidget(self.btn_stop)

        self.process_controls_widget = process_controls_widget
        self.export_action_stack = QStackedWidget()
        self.export_action_stack.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.export_action_stack.setMinimumWidth(self._px(185))
        self.export_action_stack.addWidget(self.btn_process)
        self.export_action_stack.addWidget(self.process_controls_widget)
        layout.addWidget(self.export_action_stack)
        return cluster

    def _create_hidden_export_state_controls(self, parent: QWidget):
        """Keep existing destination/detail state holders without rendering them in the bar."""
        from PyQt6.QtWidgets import QListWidget, QAbstractItemView

        self.folder_list = QListWidget(parent)
        self.folder_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.folder_list.setProperty("class", "list-compact")
        self.folder_list.itemDoubleClicked.connect(self._remove_folder_item)
        self.folder_list.hide()

        self.export_details_container = QWidget(parent)
        self.export_details_container.hide()
        self.dest_group = QFrame(parent)
        self.dest_group.hide()

        self.dest_btn_group = QButtonGroup(self)
        self.rb_dest_subfolder = QRadioButton("Subcarpeta en origen", parent)
        self.rb_dest_subfolder.setChecked(True)
        self.rb_dest_subfolder.hide()
        self.rb_dest_subfolder.toggled.connect(lambda checked: checked and self._update_export_destination_label())
        self.dest_btn_group.addButton(self.rb_dest_subfolder)

        self.rb_dest_custom = QRadioButton("Carpeta personalizada", parent)
        self.rb_dest_custom.hide()
        self.rb_dest_custom.toggled.connect(self._on_dest_custom_toggled)
        self.dest_btn_group.addButton(self.rb_dest_custom)

        self.btn_choose_dest = QPushButton("Elegir...", parent)
        self.btn_choose_dest.hide()
        self.btn_choose_dest.clicked.connect(self._choose_custom_dest)

        self.lbl_custom_dest = QLabel("", parent)
        self.lbl_custom_dest.setProperty("class", "muted")
        self.lbl_custom_dest.hide()
    
    def _create_preview_panel(self) -> QWidget:
        """Create the central canvas workbench with a single unified toolbar."""
        panel = CanvasWorkbench()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        toolbar = CommandBar()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(self._px(10), self._px(6), self._px(10), self._px(6))
        toolbar_layout.setSpacing(self._px(6))

        # --- Section 1: Current image name ---
        self.lbl_current_image = QLabel("Sin imagen")
        self.lbl_current_image.setProperty("class", "command-current")
        self.lbl_current_image.setMinimumWidth(self._px(100))
        self.lbl_current_image.setMaximumWidth(self._px(200))
        self.lbl_current_image.setToolTip("Imagen mostrada en el canvas · ESPACIO = ver original")
        toolbar_layout.addWidget(self.lbl_current_image, 0)

        toolbar_layout.addWidget(self._toolbar_divider())

        # --- Section 2: Mockup selector (input test image) ---
        mock_label = QLabel("Mockup")
        mock_label.setProperty("class", "toolbar-section-label")
        mock_label.setToolTip("Imagen de prueba para ajustar el preset")
        toolbar_layout.addWidget(mock_label)

        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        self.mock_buttons = {}
        for i, (text, mock_id) in enumerate([("Clara", "light"), ("Media", "medium"), ("Oscura", "dark")]):
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setProperty("class", f"segment-{'left' if i == 0 else 'right' if i == 2 else 'middle'}")
            btn.clicked.connect(lambda checked, m=mock_id: self._set_mock_color(m))
            self.btn_group.addButton(btn)
            self.mock_buttons[mock_id] = btn
            toolbar_layout.addWidget(btn)
            if mock_id == 'dark':
                btn.setChecked(True)

        self.btn_custom = QPushButton(qta.icon('fa5s.image', color=COLORS['text_muted']), "")
        self.btn_custom.setCheckable(True)
        self.btn_custom.setToolTip("Tu imagen personalizada")
        self.btn_custom.clicked.connect(lambda: self._set_mock_color('custom_drop'))
        self.btn_custom.hide()
        self.btn_group.addButton(self.btn_custom)
        toolbar_layout.addWidget(self.btn_custom)

        toolbar_layout.addWidget(self._toolbar_divider())

        # --- Section 3: Canvas background color ---
        self.floating_toolbar = FloatingToolbar()
        self.floating_toolbar.gridToggled.connect(self._on_preview_grid_toggled)
        self.floating_toolbar.bgColorChanged.connect(self._on_preview_bg_changed)
        self.floating_toolbar.guideSettingsChanged.connect(self._on_preview_guides_changed)
        toolbar_layout.addWidget(self.floating_toolbar, 1)

        toolbar_layout.addWidget(self._toolbar_divider())

        # --- Section 4: Actions ---
        btn_fit = QPushButton(qta.icon('fa5s.expand-arrows-alt', color=COLORS['text_muted']), "Encajar")
        btn_fit.setProperty("class", "toolbar-btn")
        btn_fit.setToolTip("Resetear zoom y posición (doble clic en canvas)")
        btn_fit.clicked.connect(lambda: self.canvas.resetView() if hasattr(self, "canvas") else None)
        toolbar_layout.addWidget(btn_fit)

        layout.addWidget(toolbar)

        # Canvas
        self.canvas = ComparisonCanvas()
        self.canvas.imageDropped.connect(self._on_image_dropped)
        self.canvas.setToolTip(
            "Rueda: zoom al cursor. Arrastra con zoom para mover. "
            "Doble clic: encajar. Espacio: ver original."
        )
        layout.addWidget(self.canvas, 1)

        # Restore preview UI preferences
        saved_bg = self.app_settings.get('preview_bg_color', "#E6E6E6")
        saved_grid = bool(self.app_settings.get('preview_grid', False))
        saved_guides = self.app_settings.get('preview_guides', {})
        self.canvas.setBackgroundColor(QColor(saved_bg))
        self.canvas.setGridVisible(saved_grid)
        self.canvas.setGuideSettings(saved_guides)
        self.floating_toolbar.set_background(saved_bg, emit=False)
        self.floating_toolbar.set_guide_settings(saved_guides, emit=False)
        self.floating_toolbar.set_grid_enabled(saved_grid, emit=False)
        self._sync_local_override_ui()

        return panel

    def _toolbar_divider(self) -> QFrame:
        """Create a vertical divider for the unified toolbar."""
        d = QFrame()
        d.setProperty("class", "toolbar-separator-v")
        d.setFixedSize(1, self._px(22))
        return d

    def _create_local_adjustment_bar(self, orientation: str = "horizontal") -> QFrame:
        """Create the per-image override controls."""
        panel = QFrame()
        panel.setProperty("class", "local-adjust-panel")
        panel.setToolTip(
            "Ajustes locales para la imagen seleccionada. "
            "Se aplican encima del preset actual y solo afectan a esa imagen."
        )

        vertical = orientation == "vertical"
        layout = QVBoxLayout(panel) if vertical else QHBoxLayout(panel)
        layout.setContentsMargins(self._px(12), self._px(12), self._px(12), self._px(12))
        layout.setSpacing(self._px(10))
        if not vertical:
            layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(self._px(8))

        title = QLabel("Ajuste por imagen")
        title.setProperty("class", "section-title")
        header_layout.addWidget(title)

        self.lbl_local_adjust_state = QLabel("Preset")
        self.lbl_local_adjust_state.setProperty("class", "local-status")
        self.lbl_local_adjust_state.setFixedWidth(self._px(96 if not vertical else 86))
        header_layout.addWidget(self.lbl_local_adjust_state)

        header_layout.addStretch()

        self._local_override_sliders = {}
        self._local_override_value_labels = {}
        self._local_override_controls = []

        slider_specs = [
            ("size_delta", "Tamaño", -20, 20, "%", "Compensa una imagen concreta haciéndola más grande o pequeña."),
            ("shadow_delta", "Sombra", -30, 30, "", "Sube o baja la presencia de sombra solo en esta imagen."),
            ("blur_delta", "Suavidad", -30, 30, "", "Ajusta la difusión de la sombra solo en esta imagen."),
        ]

        for field, label, minimum, maximum, suffix, tooltip in slider_specs:
            row = QHBoxLayout()
            row.setSpacing(self._px(8))
            field_label = QLabel(label)
            field_label.setProperty("class", "mini-label")
            field_label.setToolTip(tooltip)
            field_label.setMinimumWidth(self._px(120))
            field_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            row.addWidget(field_label)
            self._local_override_controls.append(field_label)

            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setProperty("class", "local-slider")
            slider.setRange(minimum, maximum)
            slider.setValue(0)
            slider.setToolTip(tooltip)
            slider.sliderPressed.connect(self._begin_local_override_edit)
            slider.sliderReleased.connect(self._end_local_override_edit)
            slider.valueChanged.connect(
                lambda value, key=field: self._on_local_override_slider_changed(key, value)
            )
            row.addWidget(slider, 1)
            self._local_override_sliders[field] = slider
            self._local_override_controls.append(slider)

            value_label = QLabel("0")
            value_label.setProperty("class", "mini-value")
            value_label.setFixedWidth(self._px(40))
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            value_label.setToolTip(tooltip)
            row.addWidget(value_label)
            self._local_override_value_labels[field] = (value_label, suffix)
            self._local_override_controls.append(value_label)

            if vertical:
                layout.addLayout(row)
            else:
                layout.addLayout(row)

        self.btn_local_undo = QPushButton(qta.icon('fa5s.undo-alt', color=COLORS['text_secondary']), "")
        self.btn_local_undo.setProperty("class", "icon-btn")
        self.btn_local_undo.setToolTip("Volver al ajuste local anterior de esta imagen")
        self.btn_local_undo.clicked.connect(self._undo_local_override)
        header_layout.addWidget(self.btn_local_undo)
        self._local_override_controls.append(self.btn_local_undo)

        self.btn_local_reset = QPushButton(qta.icon('fa5s.eraser', color=COLORS['text_secondary']), "")
        self.btn_local_reset.setProperty("class", "icon-btn")
        self.btn_local_reset.setToolTip("Quitar ajuste local y volver al preset")
        self.btn_local_reset.clicked.connect(self._reset_local_override)
        header_layout.addWidget(self.btn_local_reset)
        self._local_override_controls.append(self.btn_local_reset)

        if vertical:
            layout.insertLayout(0, header_layout)
        else:
            layout.insertLayout(0, header_layout)
            layout.addStretch()

        return panel
    
    def _create_grid_panel(self) -> QWidget:
        """Create the right panel with grid of image previews."""
        panel = BatchPanel()
        panel.setMinimumWidth(self._target_grid_panel_width())
        panel.setMaximumWidth(self._px(740))

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- Compact header toolbar ---
        toolbar = QFrame()
        toolbar.setProperty("class", "panel-header")
        toolbar_layout = QVBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(
            self._px(12), self._px(10), self._px(12), self._px(8)
        )
        toolbar_layout.setSpacing(self._px(6))

        # Row 1: Title + count + columns + filters (all in one row)
        title_row = QHBoxLayout()
        title_row.setSpacing(self._px(6))
        header_label = QLabel("Lote")
        header_label.setProperty("class", "panel-title")
        title_row.addWidget(header_label)

        self.lbl_batch_count = QLabel("0 imágenes")
        self.lbl_batch_count.setProperty("class", "batch-count")
        title_row.addWidget(self.lbl_batch_count)
        title_row.addStretch()

        # Filters inline
        self.batch_filter_group = QButtonGroup(self)
        self.batch_filter_group.setExclusive(True)
        self.batch_filter_buttons = {}
        for text, mode in [("Todas", "all"), ("Ajustadas", "adjusted"), ("Error", "error")]:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setProperty("class", "batch-filter")
            btn.clicked.connect(lambda checked, m=mode: self._on_batch_filter_changed(m))
            self.batch_filter_group.addButton(btn)
            self.batch_filter_buttons[mode] = btn
            title_row.addWidget(btn)
            if mode == "all":
                btn.setChecked(True)

        # Segmented columns selector
        cols_group = QFrame()
        cols_group.setProperty("class", "segmented")
        cols_layout = QHBoxLayout(cols_group)
        cols_layout.setContentsMargins(2, 2, 2, 2)
        cols_layout.setSpacing(0)

        self.grid_cols_group = QButtonGroup(self)
        self.grid_cols_group.setExclusive(True)

        def _build_cols_icon(cols: int) -> QIcon:
            size = self._px(16)
            padding = max(1, size // 8)
            gap = max(1, size // 8)

            def _pix(color: str) -> QPixmap:
                pix = QPixmap(size, size)
                pix.fill(Qt.GlobalColor.transparent)
                painter = QPainter(pix)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(color))
                total_gap = gap * max(cols - 1, 0)
                available = max(size - padding * 2 - total_gap, 2)
                col_width = max(int(available / max(cols, 1)), 2)
                x = padding
                for _ in range(cols):
                    painter.drawRoundedRect(x, padding, col_width, size - padding * 2, 2, 2)
                    x += col_width + gap
                painter.end()
                return pix

            icon = QIcon()
            icon.addPixmap(_pix(COLORS['text_muted']), QIcon.Mode.Normal, QIcon.State.Off)
            icon.addPixmap(_pix("#FFFFFF"), QIcon.Mode.Normal, QIcon.State.On)
            return icon

        self.grid_cols_btn_1 = QPushButton("")
        self.grid_cols_btn_1.setCheckable(True)
        self.grid_cols_btn_1.setProperty("class", "seg-btn-left")
        self.grid_cols_btn_1.setToolTip("1 columna")
        self.grid_cols_btn_1.setIcon(_build_cols_icon(1))

        self.grid_cols_btn_2 = QPushButton("")
        self.grid_cols_btn_2.setCheckable(True)
        self.grid_cols_btn_2.setProperty("class", "seg-btn-middle")
        self.grid_cols_btn_2.setToolTip("2 columnas")
        self.grid_cols_btn_2.setIcon(_build_cols_icon(2))

        self.grid_cols_btn_3 = QPushButton("")
        self.grid_cols_btn_3.setCheckable(True)
        self.grid_cols_btn_3.setProperty("class", "seg-btn-right")
        self.grid_cols_btn_3.setToolTip("3 columnas")
        self.grid_cols_btn_3.setIcon(_build_cols_icon(3))
        for btn in (self.grid_cols_btn_1, self.grid_cols_btn_2, self.grid_cols_btn_3):
            btn.setFixedWidth(self._px(26))
            btn.setFixedHeight(self._px(22))
            btn.setIconSize(QSize(self._px(12), self._px(12)))
            self.grid_cols_group.addButton(btn)
            cols_layout.addWidget(btn)

        title_row.addWidget(cols_group)
        toolbar_layout.addLayout(title_row)

        # Folder selector (hidden by default, shown when multiple folders)
        self.grid_folder_combo = QComboBox()
        self.grid_folder_combo.setProperty("class", "panel-combo")
        self.grid_folder_combo.currentIndexChanged.connect(self._on_grid_folder_changed)
        self.grid_folder_combo.hide()
        toolbar_layout.addWidget(self.grid_folder_combo)

        # Path label (compact, single line with elide)
        self.grid_folder_path = QLabel("")
        self.grid_folder_path.setProperty("class", "panel-path")
        self.grid_folder_path.setWordWrap(False)
        self.grid_folder_path.setMaximumHeight(self._px(22))
        self.grid_folder_path.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.grid_folder_path.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar_layout.addWidget(self.grid_folder_path)
        self.grid_folder_path.installEventFilter(self)

        layout.addWidget(toolbar)

        # Grid preview widget
        self.grid_preview = GridPreviewWidget()
        self.grid_preview.image_selected.connect(self._on_grid_image_selected)
        self.grid_preview.folder_empty.connect(self._on_grid_folder_empty)
        self.grid_preview.set_image_overrides(self.image_overrides)
        layout.addWidget(self.grid_preview, 1)

        # Apply persisted grid settings
        columns = int(self.app_settings.get('grid_columns', 1))
        if columns == 2:
            self.grid_cols_btn_2.setChecked(True)
        elif columns == 3:
            self.grid_cols_btn_3.setChecked(True)
        else:
            self.grid_cols_btn_1.setChecked(True)
        self.grid_preview.set_fixed_columns(columns)
        self.grid_cols_btn_1.clicked.connect(lambda: self._on_grid_columns_changed(1))
        self.grid_cols_btn_2.clicked.connect(lambda: self._on_grid_columns_changed(2))
        self.grid_cols_btn_3.clicked.connect(lambda: self._on_grid_columns_changed(3))

        return panel

    def _setup_accessibility_and_tab_order(self):
        """Improve keyboard ergonomics and screen-reader metadata."""
        # Disable programmatic tab order to avoid issues with Qt object lifetime.
        # Keep accessibility metadata minimal and safe.
        try:
            self.combo_presets.setAccessibleName("Selector de presets")
            self.light_angle.setAccessibleName("Control de ángulo de luz")
            self.grid_folder_combo.setAccessibleName("Selector de carpeta de previews")
        except RuntimeError:
            pass

    def _is_pre_render_activity_event(self, event) -> bool:
        return event.type() in PRE_RENDER_ACTIVITY_EVENTS

    def eventFilter(self, watched, event):
        if self._is_pre_render_activity_event(event) and hasattr(self, "pre_render_scheduler"):
            self.pre_render_scheduler.note_activity("activity")
        if watched is getattr(self, "grid_folder_path", None) and event.type() == QEvent.Type.Resize:
            try:
                idx = self.grid_folder_combo.currentIndex() if hasattr(self, "grid_folder_combo") else 0
                if self.selected_folders:
                    idx = min(max(int(idx), 0), len(self.selected_folders) - 1)
                    self._update_grid_folder_path(self.selected_folders[idx])
                else:
                    self._update_grid_folder_path(None)
            except Exception:
                pass
        return super().eventFilter(watched, event)
    
    def _on_grid_image_selected(self, path: str):
        """Load image from grid into the main canvas."""
        try:
            self._set_custom_image_from_path(path, show_feedback=True)
        except Exception as e:
            self._show_feedback(f"Error al cargar imagen")
            self._log_error(f"[grid-select-error] {path}: {e}")
    
    def _on_grid_folder_changed(self, index: int):
        """Handle folder selection change in grid panel."""
        if index < 0 or index >= len(self.selected_folders):
            return
        folder = self.selected_folders[index]
        self.ui_view_state.active_folder = str(folder)
        self.grid_preview.set_folder(str(folder))
        self.grid_preview.set_image_overrides(self.image_overrides)
        settings = self._get_effective_preview_settings()
        self.grid_preview.set_settings(settings, self.scale_curve)
        label = folder.name
        if hasattr(self, "_grid_folder_labels"):
            label = self._grid_folder_labels.get(str(folder), label)
        self.grid_preview.set_folder_label(label)
        self._update_grid_folder_path(folder)
        self.app_settings['grid_folder_index'] = int(index)
        self._save_app_settings()
        self._schedule_background_pre_render()
    
    def _update_grid_folder_combo(self):
        """Update the folder selector combo in grid panel."""
        if not hasattr(self, 'grid_folder_combo'):
            return
        
        self.grid_folder_combo.blockSignals(True)
        self.grid_folder_combo.clear()
        
        if len(self.selected_folders) <= 1:
            # Hide combo for single or no folder
            self.grid_folder_combo.hide()
            self._grid_folder_labels = {}
            if not self.selected_folders:
                self._update_grid_folder_path(None)
        else:
            display_names = self._build_folder_display_names(self.selected_folders)
            self._grid_folder_labels = display_names
            # Show combo and populate with folder names
            for folder in self.selected_folders:
                self.grid_folder_combo.addItem(f"📁 {display_names.get(str(folder), folder.name)}")
            self.grid_folder_combo.show()
        
        self.grid_folder_combo.blockSignals(False)

    def _update_grid_folder_path(self, folder: Path | None):
        """Update the path label in the grid panel."""
        if not hasattr(self, 'grid_folder_path'):
            return
        if folder is None:
            self.grid_folder_path.setText("Sin carpeta seleccionada")
            return
        full_text = str(folder)
        metrics = self.grid_folder_path.fontMetrics()
        max_width = max(self.grid_folder_path.width() - self._px(4), 120)
        self.grid_folder_path.setText(
            metrics.elidedText(full_text, Qt.TextElideMode.ElideMiddle, max_width)
        )

    def _on_grid_density_changed(self, value: int):
        if not hasattr(self, 'grid_preview'):
            return
        return

    def _on_batch_filter_changed(self, mode: str):
        if hasattr(self, 'grid_preview'):
            self.grid_preview.set_filter_mode(mode)

    def _update_batch_header(self):
        if not hasattr(self, 'lbl_batch_count'):
            return
        self.lbl_batch_count.setText(format_batch_count_text(self.batch_summary))
        self._sync_app_state()

    def _on_grid_columns_changed(self, columns: int):
        if not hasattr(self, 'grid_preview'):
            return
        self.grid_preview.set_fixed_columns(int(columns))
        self.ui_view_state.grid_columns = int(columns)
        self.app_settings['grid_columns'] = int(columns)
        self._fit_workspace_to_grid(columns=int(columns), force=True)
        self.app_settings['splitter_sizes'] = self.splitter.sizes()
        self._save_app_settings()

    def _on_preview_grid_toggled(self, enabled: bool):
        if hasattr(self, 'floating_toolbar'):
            self.floating_toolbar.set_grid_enabled(bool(enabled), emit=False)
        self.canvas.setGridVisible(bool(enabled))
        self.ui_view_state.guides_enabled = bool(enabled)
        self.app_settings['preview_grid'] = bool(enabled)
        self._save_app_settings()

    def _on_preview_bg_changed(self, color: str):
        self.canvas.setBackgroundColor(QColor(color))
        self.ui_view_state.preview_background = color
        self.app_settings['preview_bg_color'] = color
        self._save_app_settings()

    def _on_preview_guides_changed(self, settings: dict):
        self.canvas.setGuideSettings(settings)
        self.app_settings['preview_guides'] = dict(settings)
        self._save_app_settings()

    def _save_splitter_sizes(self):
        if not hasattr(self, "splitter"):
            return
        try:
            self.app_settings['splitter_sizes'] = self.splitter.sizes()
            self._save_app_settings()
        except Exception:
            pass

    def _build_folder_display_names(self, folders: list[Path]) -> dict[str, str]:
        """
        Build human-friendly folder labels.
        If repeated names exist, append the minimal unique parent suffix.
        """
        if not folders:
            return {}

        by_name = {}
        for folder in folders:
            by_name.setdefault(folder.name, []).append(folder)

        result = {}
        for name, paths in by_name.items():
            if len(paths) == 1:
                result[str(paths[0])] = name
                continue

            parent_parts = {}
            for path in paths:
                parts = [p for p in path.parent.parts if p]
                parent_parts[str(path)] = parts

            max_depth = max((len(parts) for parts in parent_parts.values()), default=0)
            chosen = {}

            for depth in range(1, max_depth + 1):
                buckets = {}
                for path in paths:
                    pkey = str(path)
                    parts = parent_parts[pkey]
                    suffix = "\\".join(parts[-depth:]) if parts else "(raíz)"
                    buckets.setdefault(suffix, []).append(pkey)

                for suffix, keys in buckets.items():
                    if len(keys) == 1 and keys[0] not in chosen:
                        chosen[keys[0]] = suffix

                if len(chosen) == len(paths):
                    break

            for path in paths:
                pkey = str(path)
                suffix = chosen.get(pkey)
                if not suffix:
                    suffix = str(path.parent)
                result[pkey] = f"{name}  ·  …\\{suffix}"

        return result

    def _sync_grid_preview_with_folders(self, preferred_index=None):
        """Keep right-side grid preview in sync with selected folders."""
        if not hasattr(self, 'grid_preview'):
            return

        previous_index = self.grid_folder_combo.currentIndex() if hasattr(self, 'grid_folder_combo') else -1
        self._update_grid_folder_combo()

        if not self.selected_folders:
            # Clear gallery when there are no folders selected.
            self.ui_view_state.active_folder = None
            self.grid_preview.set_folder_label("")
            self.grid_preview.set_folder("")
            return

        if preferred_index is None:
            preferred_index = self.app_settings.get('grid_folder_index', previous_index)
        if preferred_index is None or preferred_index < 0:
            preferred_index = 0

        target_index = min(max(int(preferred_index), 0), len(self.selected_folders) - 1)

        if len(self.selected_folders) > 1 and hasattr(self, 'grid_folder_combo'):
            self.grid_folder_combo.blockSignals(True)
            self.grid_folder_combo.setCurrentIndex(target_index)
            self.grid_folder_combo.blockSignals(False)

        folder = self.selected_folders[target_index]
        self.ui_view_state.active_folder = str(folder)
        self.grid_preview.set_folder(str(folder))
        self.grid_preview.set_image_overrides(self.image_overrides)
        settings = self._get_effective_preview_settings()
        self.grid_preview.set_settings(settings, self.scale_curve)
        label = folder.name
        if hasattr(self, "_grid_folder_labels"):
            label = self._grid_folder_labels.get(str(folder), label)
        self.grid_preview.set_folder_label(label)
        self._update_grid_folder_path(folder)
    
    def _on_grid_folder_empty(self):
        """Handle empty folder - reset canvas to show placeholder."""
        # Clear the processed image to show placeholder
        self.canvas.setProcessedImage(None)
        self.canvas.setOriginalImage(None)
        self._update_grid_folder_path(None)
        # Hide custom button if it was showing
        if self.current_mock == 'custom_drop':
            self.current_mock = 'dark'
            self.btn_custom.hide()
            self.mock_buttons['dark'].setChecked(True)
        self.current_custom_path = None
        self._apply_preview_state(build_empty_preview_state(self.current_mock))
        self._sync_local_override_ui()
    
    # ========== BUSINESS LOGIC ==========
    
    def _generate_mockups(self) -> dict:
        """Generate T-shirt shaped mockup images for preview."""
        mocks = {}
        colors = {'light': (245, 245, 245, 255), 'medium': (120, 120, 125, 255), 'dark': (35, 35, 40, 255)}
        size = 800
        
        for key, col in colors.items():
            img = QImage(size, size, QImage.Format.Format_ARGB32)
            img.fill(Qt.GlobalColor.transparent)
            painter = QPainter(img)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(*col))
            
            path = QPainterPath()
            path.moveTo(340, 150)
            path.quadTo(400, 220, 460, 150)
            path.lineTo(600, 200)
            path.lineTo(630, 280)
            path.lineTo(550, 320)
            path.quadTo(530, 330, 530, 360)
            path.lineTo(530, 720)
            path.quadTo(400, 740, 270, 720)
            path.lineTo(270, 360)
            path.quadTo(270, 330, 250, 320)
            path.lineTo(170, 280)
            path.lineTo(200, 200)
            path.lineTo(340, 150)
            painter.drawPath(path)
            painter.end()
            
            # Use bits().asstring() safely by copying to a bytes object immediately
            buffer = bytes(img.bits().asstring(img.sizeInBytes()))
            # Create PIL image from the copied bytes
            pil_img = Image.frombytes("RGBA", (size, size), buffer, "raw", "BGRA", 0, 1)
            # Crop and copy to be absolutely safe
            mocks[key] = pil_img.crop(pil_img.getbbox()).copy()
            
        return mocks

    def _set_custom_image_from_path(self, path: str, show_feedback: bool = False):
        """Load and display a custom image from disk."""
        try:
            pil_img = Image.open(path).convert("RGBA")
            pil_img.load()
            pil_img = pil_img.copy()  # Detach from underlying file
            self.mockups['custom_drop'] = pil_img
            self.current_mock = 'custom_drop'
            self.current_custom_path = path

            # Clear caches to force recalculation for the new image
            self.current_base_pil = None
            self.current_orig_pixmap = None
            self._update_current_assets(pil_img)

            # Show and select the custom image button
            self.btn_custom.show()
            self.btn_custom.setText(format_custom_preview_button_text(path))
            self.btn_custom.setChecked(True)
            self._apply_preview_state(build_custom_preview_state(path))
            self._sync_local_override_ui()

            # Only update canvas, NOT the grid (to avoid reload)
            self._schedule_canvas_only_preview()
            if show_feedback:
                self._show_feedback("Imagen cargada desde grid")
        except Exception as e:
            if show_feedback:
                self._show_feedback("Error al cargar imagen")
            self._log_error(f"[custom-image-error] {path}: {e}")

    def _update_current_assets(self, pil_img: Image.Image):
        """Pre-calculate and cache assets for the current image to ensure zero-lag UI."""
        # 1. Cache a "working" version (max 2000px) for all UI processing
        max_w = 2000
        if pil_img.width > max_w:
            ratio = max_w / pil_img.width
            self.current_base_pil = pil_img.resize((max_w, int(pil_img.height * ratio)), Image.Resampling.BILINEAR)
        else:
            self.current_base_pil = pil_img.copy()

        # 2. Cache the "original" pixmap for A/B comparison (composite on gray)
        if pil_img.mode == 'RGBA':
            bg = Image.new("RGB", pil_img.size, (230, 230, 230))
            bg.paste(pil_img, (0, 0), mask=pil_img)
            comp_img = bg
        else:
            comp_img = pil_img.convert("RGB")
        
        # Scale for display efficiency
        disp_w = 1200
        if comp_img.width > disp_w:
            ratio = disp_w / comp_img.width
            comp_img = comp_img.resize((disp_w, int(comp_img.height * ratio)), Image.Resampling.BILINEAR)
            
        data = comp_img.tobytes("raw", "RGB")
        qim = QImage(data, comp_img.width, comp_img.height, comp_img.width * 3, QImage.Format.Format_RGB888).copy()
        self.current_orig_pixmap = QPixmap.fromImage(qim)
        self.canvas.setOriginalImage(self.current_orig_pixmap)
    
    def _get_default_presets(self) -> dict:
        return {
            "Ropa clara (luz cenital)": {
                'angle': 180, 'distance': 25, 'blur': 30, 'spread': 0,
                'fusion': 1, 'opacity': 20, 'noise': 2, 'padding': 10,
                'contact_blur': 10, 'adaptive_zoom': True,
                'shadow_engine': SHADOW_ENGINE_DEFAULT,
            },
            "Ropa oscura": {
                'angle': 180, 'distance': 20, 'blur': 40, 'spread': 3,
                'fusion': 5, 'opacity': 45, 'noise': 5, 'padding': 10,
                'contact_blur': 12, 'adaptive_zoom': True,
                'shadow_engine': SHADOW_ENGINE_DEFAULT,
            },
        }
    
    def _load_app_settings(self) -> dict:
        return self.settings_service.load()
    
    def _save_app_settings(self):
        """Schedule a coalesced disk write (avoids blocking UI on every slider tick)."""
        self.app_settings['scale_curve'] = self.scale_curve.model_dump()
        self.app_settings['image_overrides'] = self.image_overrides
        if hasattr(self, 'combo_shadow_engine'):
            self.app_settings['shadow_engine'] = self.combo_shadow_engine.currentData() or SHADOW_ENGINE_DEFAULT
        # Coalesce: actual write happens after 400ms of inactivity
        if hasattr(self, '_save_settings_timer'):
            self._save_settings_timer.start(400)
        else:
            self._flush_app_settings()

    def _flush_app_settings(self):
        """Actually write settings to disk (called by coalesced timer)."""
        try:
            self.settings_service.save(self.app_settings)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            
    def _save_presets_to_disk(self):
        self.preset_service.save_flat_presets_preserving_categories(self.presets)

    def _build_export_config_from_settings(self) -> ExportConfig:
        output_destination_override = None

        if hasattr(self, 'rb_dest_custom') and self.rb_dest_custom.isChecked():
            output_destination_override = 'custom'
        elif hasattr(self, 'rb_dest_subfolder') and self.rb_dest_subfolder.isChecked():
            output_destination_override = 'subfolder'

        custom_output_path_override = str(self.custom_output_path) if self.custom_output_path else None
        return self.export_config_service.build_from_settings(
            self.app_settings,
            variants=self.export_variants,
            output_destination_override=output_destination_override,
            custom_output_path_override=custom_output_path_override,
        )

    def _apply_export_preferences(self, config: ExportConfig):
        self._store_export_variants(normalize_export_variants(config), save=False)
        self.custom_output_path = Path(config.custom_output_path) if config.custom_output_path else None
        is_custom = config.output_destination == 'custom'
        self.app_settings['output_destination'] = 'custom' if is_custom else 'subfolder'
        self.app_settings['custom_output_path'] = str(self.custom_output_path) if self.custom_output_path else None
        self.rb_dest_custom.setChecked(is_custom)
        self.rb_dest_subfolder.setChecked(not is_custom)
        self.btn_choose_dest.setEnabled(is_custom)
        if self.custom_output_path:
            self.lbl_custom_dest.setText(f"→ {self.custom_output_path}")
            self.lbl_custom_dest.setVisible(is_custom)
        else:
            self.lbl_custom_dest.clear()
            self.lbl_custom_dest.hide()
        self._update_export_destination_label()

    def _update_export_destination_label(self):
        """Keep the persistent export bar destination summary in sync."""
        text = presenters.format_destination_batch_label(self._build_export_config_from_settings())
        if hasattr(self, 'batch_summary'):
            self.batch_summary.destination_label = text
        self._update_export_bar_state()

    def _elide_text(self, label: QLabel, text: str, minimum_width: int = 80) -> str:
        width = max(label.width(), self._px(minimum_width))
        return label.fontMetrics().elidedText(str(text), Qt.TextElideMode.ElideRight, width)

    def _set_elided_label(self, label: QLabel, text: str, tooltip: str | None = None, minimum_width: int = 80):
        label.setProperty("full_text", str(text))
        label.setProperty("full_tooltip", str(tooltip or text))
        label.setText(self._elide_text(label, text, minimum_width))
        label.setToolTip(str(tooltip or text))

    def _refresh_elided_export_labels(self):
        for label in (
            getattr(self, "lbl_folder_summary", None),
            getattr(self, "lbl_export_config_summary", None),
            getattr(self, "lbl_destination_summary", None),
            getattr(self, "lbl_outputs_summary", None),
            getattr(self, "lbl_progress_status", None),
        ):
            if label is None:
                continue
            text = label.property("full_text")
            if text:
                self._set_elided_label(label, str(text), str(label.property("full_tooltip") or text))

    def _plural(self, count: int, singular: str, plural: str) -> str:
        return presenters.pluralize(count, singular, plural)

    def _format_batch_summary_text(self) -> str:
        return presenters.format_batch_summary(
            getattr(self.batch_summary, "folders_count", 0),
            getattr(self.batch_summary, "images_count", 0),
            getattr(self.batch_summary, "adjusted_count", 0),
        )

    def _format_destination_summary(self) -> tuple[str, str]:
        summary = presenters.format_destination_summary(self._build_export_config_from_settings())
        return summary.text, summary.tooltip

    def _format_export_config_summary(self) -> tuple[str, str]:
        config = self._build_export_config_from_settings()
        summary = presenters.format_export_config_summary(config, self._active_export_variants())
        return summary.text, summary.tooltip

    def _format_outputs_summary(self) -> tuple[str, str]:
        summary = presenters.format_outputs_summary(self._active_export_variants())
        return summary.text, summary.tooltip

    def _process_button_text(self) -> str:
        return presenters.format_process_button_text(getattr(self.batch_summary, "images_count", 0))

    def _sync_app_state(self):
        if not hasattr(self, "app_state"):
            return
        progress_value = self.progress_bar.value() if hasattr(self, "progress_bar") else 0
        active_preset = self.combo_presets.currentText() if hasattr(self, "combo_presets") else None
        self.app_state.batch = self.batch_summary
        self.app_state.export = self.export_state
        self.app_state.view = self.ui_view_state
        self.app_state.processing = ProcessingState(
            mode=self.export_bar_mode,
            status_text=self._export_bar_status_text,
            pre_render_status=self._pre_render_bar_status,
            progress_value=progress_value,
        )
        self.app_state.preview = self.preview_state
        self.app_state.selected_image = self.preview_state.selected_image
        self.app_state.active_preset = active_preset

    def _apply_preview_state(self, preview_state: PreviewState):
        self.preview_state = preview_state
        self.ui_view_state.selected_image = preview_state.selected_image
        if hasattr(self, 'lbl_current_image'):
            self.lbl_current_image.setText(preview_state.label_text)
            self.lbl_current_image.setToolTip(preview_state.tooltip)
        self._sync_app_state()

    def _apply_processing_state(
        self,
        processing_state: ProcessingState,
        *,
        update_progress: bool = False,
        update_pre_render: bool = True,
    ):
        self.export_bar_mode = processing_state.mode
        self._export_bar_status_text = processing_state.status_text
        if update_pre_render:
            self._pre_render_bar_status = processing_state.pre_render_status
        if update_progress and hasattr(self, "progress_bar"):
            self.progress_bar.setValue(processing_state.progress_value)
        self._sync_app_state()

    def _update_export_bar_state(self):
        if not hasattr(self, "btn_process"):
            return

        active_outputs = self._active_export_variants()
        bar_state = build_export_bar_state(
            self.batch_summary,
            active_outputs_count=len(active_outputs),
            mode=self.export_bar_mode,
            selected_folders_count=len(self.selected_folders),
            export_status_text=self._export_bar_status_text,
            pre_render_status=self._pre_render_bar_status,
        )

        self._set_elided_label(self.lbl_folder_summary, self._format_batch_summary_text())

        export_text, export_tooltip = self._format_export_config_summary()
        self._set_elided_label(self.lbl_export_config_summary, export_text, export_tooltip)

        dest_text, dest_tooltip = self._format_destination_summary()
        self._set_elided_label(self.lbl_destination_summary, dest_text, dest_tooltip)

        outputs_text, outputs_tooltip = self._format_outputs_summary()
        self._set_elided_label(self.lbl_outputs_summary, outputs_text, outputs_tooltip)

        self.btn_clear_folders.setEnabled(bar_state.can_clear_folders)
        self.btn_export_details.setEnabled(bar_state.can_open_export_details)
        self.btn_add_folder.setEnabled(bar_state.can_add_folder)
        self.btn_export_config.setEnabled(bar_state.can_edit_export_config)
        self.btn_outputs.setEnabled(bar_state.can_edit_outputs)
        self.btn_process.setEnabled(bar_state.can_process)
        self.btn_process.setText(bar_state.process_button_text)

        if bar_state.progress_value is not None:
            self.progress_bar.setValue(bar_state.progress_value)

        self._set_elided_label(self.lbl_progress_status, bar_state.progress_status_text)
        self.progress_bar.setVisible(bar_state.show_progress)
        if not bar_state.show_progress:
            self.progress_bar.setValue(0)

        self.export_action_stack.setCurrentIndex(1 if bar_state.processing else 0)
        if hasattr(self, "btn_pause"):
            self.btn_pause.setVisible(bar_state.show_pause)
        if hasattr(self, "btn_stop"):
            self.btn_stop.setVisible(bar_state.show_stop)

        tooltip = self._format_outputs_summary()[1]
        self.btn_process.setToolTip(
            f"{bar_state.process_button_text}\n{tooltip}"
            if bar_state.can_process
            else bar_state.progress_status_text
        )
        self._sync_app_state()

    def _variant_hex(self, variant: ExportVariant) -> str:
        return "#{:02X}{:02X}{:02X}".format(*variant.bg_color)

    def _variant_short_label(self, variant: ExportVariant) -> str:
        if variant.id == "web_rgb230":
            return "Web"
        if variant.id == "white_rgb255":
            return "Blanco"
        return variant.label.split()[0] if variant.label else variant.id

    def _format_variant_chip_text(self, variant: ExportVariant) -> str:
        bg_text = "Transp." if variant.transparent_bg else self._variant_hex(variant)
        parts = [self._variant_short_label(variant), bg_text]
        if variant.suffix:
            parts.append(variant.suffix)
        if variant.shadow_opacity_override is not None:
            parts.append(f"sombra {variant.shadow_opacity_override}")
        elif variant.shadow_opacity_delta:
            parts.append(f"sombra {variant.shadow_opacity_delta:+d}")
        return " · ".join(parts)

    def _active_export_variants(self) -> list[ExportVariant]:
        return [variant for variant in self.export_variants if variant.enabled]

    def _active_variant_labels(self) -> list[str]:
        return [variant.label for variant in self._active_export_variants()]

    def _refresh_output_summary_label(self):
        self._update_export_bar_state()

    def _sync_legacy_export_fields_from_variants(self):
        variants = self.export_variants or normalize_export_variants(self.app_settings)
        primary = variants[0]
        self.app_settings['transparent_bg'] = primary.transparent_bg
        self.app_settings['bg_color'] = primary.bg_color
        self.app_settings['suffix'] = primary.suffix

    def _store_export_variants(self, variants: list[ExportVariant], *, save: bool = True):
        self.export_variants = normalize_export_variants({"variants": [variant.model_dump() for variant in variants]})
        if not any(variant.id == self.current_preview_variant_id for variant in self.export_variants):
            self.current_preview_variant_id = self.export_variants[0].id
        self.app_settings['variants'] = [variant.model_dump() for variant in self.export_variants]
        self.app_settings['current_preview_variant_id'] = self.current_preview_variant_id
        self._sync_legacy_export_fields_from_variants()
        if save:
            self._save_app_settings()
        self._refresh_export_variants_ui()
        self._refresh_output_summary_label()

    def _refresh_export_variants_ui(self):
        self._update_export_bar_state()

    def _set_variant_enabled(self, variant_id: str, enabled: bool):
        variants = [
            variant.model_copy(update={"enabled": bool(enabled)}) if variant.id == variant_id else variant
            for variant in self.export_variants
        ]
        self._store_export_variants(variants)

    def _select_preview_variant(self, variant_id: str):
        if not any(variant.id == variant_id for variant in self.export_variants):
            return
        self.current_preview_variant_id = variant_id
        self.app_settings['current_preview_variant_id'] = variant_id
        self._save_app_settings()
        self._refresh_export_variants_ui()
        self._schedule_preview()

    def _add_or_enable_white_variant(self):
        self._add_or_enable_template_variant(WHITE_RGB255.model_copy(update={"enabled": True}))

    def _add_or_enable_web_variant(self):
        self._add_or_enable_template_variant(WEB_RGB230.model_copy(update={"enabled": True}))

    def _add_or_enable_template_variant(self, template: ExportVariant):
        variants = []
        found = False
        for variant in self.export_variants:
            if variant.id == template.id:
                variants.append(variant.model_copy(update={"enabled": True}))
                found = True
            else:
                variants.append(variant)
        if not found:
            variants.append(template)
        self.current_preview_variant_id = template.id
        self._store_export_variants(variants)
        self._schedule_preview()

    def _current_preview_variant(self) -> ExportVariant:
        for variant in self.export_variants:
            if variant.id == self.current_preview_variant_id:
                return variant
        self.current_preview_variant_id = self.export_variants[0].id
        return self.export_variants[0]

    def _get_effective_preview_settings(self, path: str | None = None) -> ShadowSettings:
        return build_variant_settings(
            self._get_effective_shadow_settings(path),
            self._current_preview_variant(),
        )

    def _open_export_variants_dialog(self):
        dlg = ExportVariantsDialog(self.export_variants, self)
        if dlg.exec():
            self._store_export_variants(dlg.get_variants())
            self._schedule_preview()
            self._show_feedback("Salidas actualizadas")

    def _refresh_presets_combo(self, preferred_name: str | None = None):
        current_name = preferred_name or self.combo_presets.currentText()
        self.combo_presets.blockSignals(True)
        self.combo_presets.clear()
        self.combo_presets.addItems(list(self.presets.keys()))
        self.combo_presets.blockSignals(False)

        if self.combo_presets.count() == 0:
            self._show_feedback("No hay presets disponibles")
            return

        target_name = current_name if current_name in self.presets else self.combo_presets.itemText(0)
        self.combo_presets.setCurrentText(target_name)
        self._apply_preset_from_combo()
        
    def _get_shadow_settings(self) -> ShadowSettings:
        shadow_engine = SHADOW_ENGINE_DEFAULT
        if hasattr(self, 'combo_shadow_engine'):
            shadow_engine = self.combo_shadow_engine.currentData() or SHADOW_ENGINE_DEFAULT
        else:
            shadow_engine = self.app_settings.get('shadow_engine', SHADOW_ENGINE_DEFAULT)
        return ShadowSettings(
            angle=self.light_angle.angle(),
            distance=self.sl_distance.value(),
            blur=self.sl_blur.value(),
            spread=self.sl_spread.value(),
            fusion=self.sl_fusion.value(),
            opacity=self.sl_opacity.value(),
            noise=self.sl_noise.value(),
            padding=self.sl_padding.value(),
            contact_blur=self.sl_contact_blur.value(),
            contraction=self.sl_contraction.value(),
            adaptive_zoom=self.chk_adaptive.isChecked(),
            scale_adjustment=self.sl_scale_adjustment.value(),
            shadow_engine=shadow_engine,
        )

    def _current_image_override_key(self) -> str:
        if self.current_mock != 'custom_drop' or not self.current_custom_path:
            return ""
        return override_key(self.current_custom_path)

    def _override_for_path(self, path: str | None) -> dict:
        key = override_key(path)
        return self.image_overrides.get(key, {}) if key else {}

    def _get_effective_shadow_settings(self, path: str | None = None) -> ShadowSettings:
        source_path = path
        if source_path is None and self.current_mock == 'custom_drop':
            source_path = self.current_custom_path
        return apply_image_override(self._get_shadow_settings(), self._override_for_path(source_path))

    def _save_image_overrides(self):
        self.image_overrides = {
            key: normalize_image_override(value)
            for key, value in self.image_overrides.items()
            if has_image_override(value)
        }
        self.app_settings['image_overrides'] = self.image_overrides
        self._save_app_settings()

    def _refresh_image_overrides(self):
        if hasattr(self, 'grid_preview'):
            self.grid_preview.set_image_overrides(self.image_overrides)
        if self.selected_folders:
            scan = self.folder_scanner.scan_folders(self.selected_folders, self.image_overrides)
            self.batch_summary.adjusted_count = scan.adjusted_images
            self._update_batch_header()

    def _format_local_delta(self, value: int, suffix: str = "") -> str:
        if value > 0:
            return f"+{value}{suffix}"
        if value < 0:
            return f"{value}{suffix}"
        return f"0{suffix}" if suffix else "0"

    def _update_local_override_value_labels(self):
        if not hasattr(self, '_local_override_value_labels'):
            return
        for field, (label, suffix) in self._local_override_value_labels.items():
            slider = self._local_override_sliders.get(field)
            if slider:
                label.setText(self._format_local_delta(slider.value(), suffix))

    def _collect_local_override_from_ui(self) -> dict:
        values = dict(LOCAL_OVERRIDE_DEFAULTS)
        for field, slider in getattr(self, '_local_override_sliders', {}).items():
            values[field] = slider.value()
        return normalize_image_override(values)

    def _begin_local_override_edit(self):
        self._remember_local_override_state()

    def _end_local_override_edit(self):
        self._local_override_edit_key = None

    def _remember_local_override_state(self, force: bool = False):
        key = self._current_image_override_key()
        if not key or (self._local_override_edit_key == key and not force):
            return
        stack = self._local_override_history.setdefault(key, [])
        stack.append(dict(self.image_overrides.get(key, {})))
        if len(stack) > 20:
            del stack[:-20]
        self._local_override_edit_key = key

    def _on_local_override_slider_changed(self, field: str, value: int):
        if self._syncing_local_override_ui:
            return
        key = self._current_image_override_key()
        if not key:
            self._sync_local_override_ui()
            return

        self._remember_local_override_state()
        self._update_local_override_value_labels()
        override = self._collect_local_override_from_ui()
        if override:
            self.image_overrides[key] = override
        else:
            self.image_overrides.pop(key, None)

        self._save_image_overrides()
        self._update_local_override_state_label()
        self._refresh_image_overrides()
        self._schedule_canvas_only_preview()

    def _undo_local_override(self):
        key = self._current_image_override_key()
        if not key:
            return
        stack = self._local_override_history.get(key, [])
        if not stack:
            return

        previous = normalize_image_override(stack.pop())
        if previous:
            self.image_overrides[key] = previous
        else:
            self.image_overrides.pop(key, None)
        self._local_override_edit_key = None
        self._save_image_overrides()
        self._sync_local_override_ui()
        self._refresh_image_overrides()
        self._schedule_canvas_only_preview()
        self._show_feedback("Ajuste local anterior")

    def _reset_local_override(self):
        key = self._current_image_override_key()
        if not key or not has_image_override(self.image_overrides.get(key)):
            return
        self._remember_local_override_state(force=True)
        self._local_override_edit_key = None
        self.image_overrides.pop(key, None)
        self._save_image_overrides()
        self._sync_local_override_ui()
        self._refresh_image_overrides()
        self._schedule_canvas_only_preview()
        self._show_feedback("Imagen de nuevo al preset")

    def _update_local_override_state_label(self):
        if not hasattr(self, 'lbl_local_adjust_state'):
            return
        key = self._current_image_override_key()
        enabled = bool(key)
        active = enabled and has_image_override(self.image_overrides.get(key))

        if not enabled:
            self.lbl_local_adjust_state.setText("Sin imagen")
            self.lbl_local_adjust_state.setToolTip("Selecciona una imagen del grid o arrástrala al canvas.")
            self._set_widget_class(self.lbl_local_adjust_state, "local-status")
        elif active:
            self.lbl_local_adjust_state.setText("Ajuste local")
            self.lbl_local_adjust_state.setToolTip("Esta imagen tiene cambios propios encima del preset.")
            self._set_widget_class(self.lbl_local_adjust_state, "local-status-active")
        else:
            self.lbl_local_adjust_state.setText("Preset")
            self.lbl_local_adjust_state.setToolTip("Esta imagen usa el preset sin cambios locales.")
            self._set_widget_class(self.lbl_local_adjust_state, "local-status")

        for widget in getattr(self, '_local_override_controls', []):
            widget.setEnabled(enabled)
        if hasattr(self, 'btn_local_reset'):
            self.btn_local_reset.setEnabled(active)
        if hasattr(self, 'btn_local_undo'):
            self.btn_local_undo.setEnabled(enabled and bool(self._local_override_history.get(key, [])))

    def _sync_local_override_ui(self):
        if not hasattr(self, '_local_override_sliders'):
            return
        key = self._current_image_override_key()
        current = dict(LOCAL_OVERRIDE_DEFAULTS)
        if key:
            current.update(normalize_image_override(self.image_overrides.get(key)))

        self._syncing_local_override_ui = True
        try:
            for field, slider in self._local_override_sliders.items():
                slider.blockSignals(True)
                slider.setValue(int(current.get(field, 0)))
                slider.blockSignals(False)
        finally:
            self._syncing_local_override_ui = False

        self._update_local_override_value_labels()
        self._update_local_override_state_label()
    
    # ========== EVENT HANDLERS ==========
    
    def _schedule_preview(self, *args):
        """Schedule debounced preview update.

        During an active slider drag the canvas preview fires quickly (50ms)
        while the expensive grid refresh is deferred until after release.
        When no drag is active (combo change, checkbox, etc.) both fire
        together with a short debounce.
        """
        self._preview_pending = True
        if self._slider_dragging:
            # Fast canvas-only update; grid will sync on release
            self.preview_timer.start(50)
            self._grid_sync_timer.start(600)
        else:
            self.preview_timer.start(120)
            # Immediate grid sync (debounced inside grid widget already)
            self._grid_sync_timer.start(150)
        
        self._schedule_background_pre_render()

    def _schedule_canvas_only_preview(self, *args):
        """Schedule preview update for canvas only (not grid)."""
        self._preview_pending = True
        if self._slider_dragging:
            self.preview_timer.start(50)
        else:
            self.preview_timer.start(120)
        self._schedule_background_pre_render()

    def _deferred_grid_sync(self):
        """Push current settings to the grid preview widget (heavy operation)."""
        if hasattr(self, 'grid_preview'):
            settings = self._get_effective_preview_settings()
            self.grid_preview.set_settings(settings, self.scale_curve)
            self.grid_preview.set_image_overrides(self.image_overrides)

    def _pre_render_should_pause(self) -> bool:
        if self._slider_dragging:
            return True
        if self.worker and self.worker.isRunning():
            return True
        if self.queue_worker and self.queue_worker.isRunning():
            return True
        if self.preview_pool.activeThreadCount() > 0:
            return True
        if hasattr(self, "grid_preview") and hasattr(self.grid_preview, "is_busy"):
            return self.grid_preview.is_busy()
        return False

    def _cancel_background_pre_render(self):
        if hasattr(self, "pre_render_scheduler"):
            self.pre_render_scheduler.note_activity("activity")

    def _schedule_background_pre_render(self, delay_ms: int | None = None):
        if not hasattr(self, "pre_render_scheduler"):
            return
        enabled = bool(self.app_settings.get('background_pre_render', False))
        if not enabled:
            self.pre_render_scheduler.shutdown(emit_idle=True)
            return
        try:
            export_config = self._build_export_config_from_settings()
            settings = self._get_effective_preview_settings()
            max_cache_mb = int(self.app_settings.get('background_pre_render_cache_mb', 2048))
            self.pre_render_scheduler.update_context(
                enabled=True,
                folders=list(self.selected_folders),
                active_folder=getattr(self.ui_view_state, "active_folder", None),
                current_image_path=self.current_custom_path if self.current_mock == 'custom_drop' else None,
                settings_dict=settings.model_dump(),
                curve_dict=self.scale_curve.model_dump() if self.scale_curve else None,
                target_size=(export_config.output_width, export_config.output_height),
                export_format=variant_export_format(export_config, self._current_preview_variant()),
                image_overrides=self.image_overrides,
                idle_ms=int(self.app_settings.get('background_pre_render_idle_ms', 8000)),
                max_cache_bytes=max_cache_mb * 1024 * 1024,
            )
            if delay_ms is not None:
                self.pre_render_scheduler.schedule(delay_ms)
        except Exception as exc:
            self._log_error(f"[pre-render-schedule-error] {exc}")

    def _on_pre_render_status(self, state: str, prepared: int, total: int):
        if not hasattr(self, "lbl_progress_status"):
            return
        if (self.worker and self.worker.isRunning()) or (self.queue_worker and self.queue_worker.isRunning()):
            return

        self._pre_render_bar_status = build_pre_render_bar_status(state, prepared, total)
        self._update_export_bar_state()
    
    def _start_preview_thread(self):
        """Start an asynchronous preview render using cached assets."""
        try:
            if self.current_mock not in self.mockups:
                return

            # Debounce: if already working, mark as pending and skip
            if self.preview_pool.activeThreadCount() > 0:
                self._preview_pending = True
                return

            self._preview_pending = False
            
            # Use cached assets if available, otherwise initialize them (one-time)
            if self.current_base_pil is None:
                self._update_current_assets(self.mockups[self.current_mock])
            
            # Prepare worker with the cached assets.
            # Passing the PIL image directly; PreviewService will handle rendering/scaling.
            worker = PreviewWorker(
                self.current_base_pil,
                self.preview_size,
                self._get_effective_preview_settings().model_dump(),
                self.scale_curve.model_dump(),
                self.preview_scale_ratio,
                quality_level=1
            )
            self._active_preview_workers.add(worker)
            worker.signals.finished.connect(
                lambda qim, quality, warning, w=worker: self._on_preview_worker_finished(
                    w,
                    qim,
                    quality,
                    warning,
                )
            )
            worker.signals.error.connect(
                lambda message, w=worker: self._on_preview_worker_error(w, message)
            )
            self.preview_pool.start(worker)

        except Exception as e:
            self._log_error(f"[preview-start-error] {e}")
            traceback.print_exc()

    def _on_preview_worker_finished(
        self,
        worker: PreviewWorker,
        qim: QImage,
        quality: int = 1,
        warning: str | None = None,
    ):
        self._release_preview_worker(worker)
        if warning:
            self._log_error(f"[shadow-fallback] {warning}")
            self._show_feedback("Aviso: V2 usó sombra clásica")
        self._update_preview(qim, quality)

    def _on_preview_worker_error(self, worker: PreviewWorker, message: str):
        self._release_preview_worker(worker)
        self._on_preview_error(message)

    def _release_preview_worker(self, worker: PreviewWorker):
        if worker in self._active_preview_workers:
            self._active_preview_workers.remove(worker)
        
    def _update_preview(self, qim: QImage, quality: int = 1):
        try:
            self.current_qimage = qim
            pixmap = QPixmap.fromImage(qim)
            self.canvas.setProcessedImage(pixmap)
        except Exception as ex:
            self._log_error(f"[update-preview-error] {ex}")
            traceback.print_exc()
        finally:
            # Check if another preview was requested while we were busy
            if self._preview_pending:
                self._preview_pending = False
                self.preview_timer.start(10)

    
    def _on_preview_error(self, message: str):
        formatted = f"[preview-error] {message}"
        self._log_error(formatted)
        QMessageBox.warning(
            self,
            "Error de previsualización",
            f"No se pudo generar la vista previa:\n{message}\n\nSe registró en:\n{self.LOG_FILE}",
        )
        if self._preview_pending:
            self._preview_pending = False
            self.preview_timer.start(10)
    
    @staticmethod
    def _setup_logger():
        """Ensure logger writes both to file and stdout."""
        logger = logging.getLogger("flatshot.preview")
        if logger.handlers:
            return logger
        logger.setLevel(logging.DEBUG)
        try:
            MainWindow.LOG_DIR.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(MainWindow.LOG_FILE, encoding="utf-8")
            file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
            logger.addHandler(file_handler)
        except Exception as ex:
            fallback = Path(tempfile.gettempdir()) / "flatshot_preview.log"
            try:
                fh = logging.FileHandler(fallback, encoding="utf-8")
                fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
                logger.addHandler(fh)
                print(f"[log-error] No se pudo crear {MainWindow.LOG_FILE}: {ex} -> usando {fallback}", flush=True)
            except Exception as ex2:
                print(f"[log-error] No se pudo crear log de fallback: {ex2}", flush=True)
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
        logger.addHandler(stream_handler)
        return logger

    def _log_error(self, message: str):
        """Append errors to a local log file for debugging."""
        logger = self._setup_logger()
        logger.error(message)

    def _on_export_log(self, message: str):
        self.export_state.error_message = str(message)
        self._sync_app_state()
        self._log_error(message)

    def _on_angle_changed(self, angle: int):
        self.angle_spinbox.blockSignals(True)
        self.angle_spinbox.setValue(angle)
        self.angle_spinbox.blockSignals(False)
        self._schedule_preview()
        
    def _on_angle_spinbox_changed(self, value: int):
        self.light_angle.setAngle(value)
        
    def _set_mock_color(self, mock_id: str):
        if mock_id == "med":
            mock_id = "medium"
        self.current_mock = mock_id
        if mock_id == 'custom_drop' and self.current_custom_path:
            self._apply_preview_state(build_custom_preview_state(self.current_custom_path))
        elif mock_id == 'custom_drop':
            self._apply_preview_state(build_empty_preview_state(mock_id))
        else:
            self._apply_preview_state(build_mockup_preview_state(mock_id))
        # Clear cache to force re-generation for the mockup
        self.current_base_pil = None
        self.current_orig_pixmap = None
        self._sync_local_override_ui()
        self._schedule_preview()
        
    def _on_image_dropped(self, path: str):
        try:
            logger = self._setup_logger()
            logger.info(f"[drop] {path}")
            # Validate file before full load to avoid crashes on corrupt files
            with Image.open(path) as img_check:
                img_check.verify()
            pil_img = Image.open(path).convert("RGBA")
            pil_img.load()  # Force load to catch decoder issues
            pil_img = pil_img.copy()  # Detach from underlying file
            self.mockups['custom_drop'] = pil_img
            
            # Show and select the custom image button
            self.btn_custom.show()
            self.btn_custom.setText(format_custom_preview_button_text(path, include_suffix=True))
            self.btn_custom.setChecked(True)
            
            self.current_mock = 'custom_drop'
            self.current_custom_path = path
            self._apply_preview_state(build_custom_preview_state(path))
            
            # Update assets and schedule
            self.current_base_pil = None
            self.current_orig_pixmap = None
            self._update_current_assets(pil_img)
            self._sync_local_override_ui()
            
            self._schedule_preview()
            self._show_feedback(f"Imagen cargada")
        except Exception as e:
            self._show_feedback("Error al cargar imagen")
            self._log_error(f"[load-error] {path}: {e}")
            print(f"[load-error] {path}: {e}", flush=True)
    
    def _reset_to_defaults(self):
        """Reset all controls to default values."""
        self.light_angle.setAngle(180)
        self.sl_distance.setValue(30)
        self.sl_blur.setValue(25)
        self.sl_spread.setValue(0)
        self.sl_fusion.setValue(2)
        self.sl_contact_blur.setValue(10)
        self.sl_opacity.setValue(30)
        self.sl_noise.setValue(0)
        self.sl_padding.setValue(10)
        self.sl_contraction.setValue(0)
        self.sl_scale_adjustment.setValue(0)
        self.chk_adaptive.setChecked(True)
        if hasattr(self, 'combo_shadow_engine'):
            engine_idx = self.combo_shadow_engine.findData(SHADOW_ENGINE_DEFAULT)
            if engine_idx >= 0:
                self.combo_shadow_engine.setCurrentIndex(engine_idx)
        
        # Reset scale curve to new optimal defaults
        self.scale_curve = CurveData(**DEFAULT_SCALE_CURVE)
        self._save_app_settings()
        
        self._schedule_preview()
        self._show_feedback("Valores restaurados")
    
    def _show_shortcuts_dialog(self):
        """Show keyboard shortcuts in a styled dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Atajos de teclado")
        dialog.setFixedSize(self._px(380), self._px(500))
        dialog.setProperty("class", "dialog")
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(self._px(12))
        layout.setContentsMargins(
            self._px(20), self._px(20), self._px(20), self._px(20)
        )
        
        # Title with icon
        title_row = QHBoxLayout()
        title_icon = QLabel()
        title_icon.setPixmap(
            qta.icon('fa5s.keyboard', color=COLORS['accent_primary']).pixmap(self._px(24), self._px(24))
        )
        title_row.addWidget(title_icon)
        title = QLabel("Atajos de teclado")
        title.setProperty("class", "dialog-title")
        title_row.addWidget(title)
        title_row.addStretch()
        layout.addLayout(title_row)
        
        # Shortcut groups with icons
        groups = [
            (qta.icon('fa5s.save', color=COLORS['accent_primary']), "Presets", [
                ("Ctrl+S", "Guardar preset"),
                ("Ctrl+R", "Restaurar valores"),
            ]),
            (qta.icon('fa5s.eye', color=COLORS['accent_primary']), "Vista previa", [
                ("1  2  3", "Cambiar mockup"),
                ("Espacio", "Ver original"),
                ("Scroll", "Zoom"),
            ]),
            (qta.icon('fa5s.cogs', color=COLORS['accent_primary']), "Exportación", [
                ("Ctrl+Enter", "Procesar imágenes"),
                ("Ctrl+Shift+P", "Pausar/Reanudar"),
                ("Esc", "Detener procesamiento"),
            ]),
            (qta.icon('fa5s.cog', color=COLORS['accent_primary']), "General", [
                ("Ctrl+,", "Configuración"),
                ("Ctrl+Q", "Salir"),
                ("F1", "Ayuda"),
            ]),
        ]
        
        for icon, group_title, shortcuts in groups:
            # Group header with icon
            header_row = QHBoxLayout()
            icon_lbl = QLabel()
            icon_lbl.setPixmap(icon.pixmap(self._px(14), self._px(14)))
            header_row.addWidget(icon_lbl)
            header = QLabel(group_title)
            header.setProperty("class", "dialog-section")
            header_row.addWidget(header)
            header_row.addStretch()
            layout.addLayout(header_row)
            
            # Shortcuts in group
            for key, desc in shortcuts:
                row = QHBoxLayout()
                row.setSpacing(self._px(12))
                
                key_lbl = QLabel(key)
                key_lbl.setFixedWidth(self._px(70))
                key_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                key_lbl.setProperty("class", "keycap")
                
                desc_lbl = QLabel(desc)
                desc_lbl.setProperty("class", "dialog-text")
                
                row.addWidget(key_lbl)
                row.addWidget(desc_lbl, 1)
                layout.addLayout(row)

        note = QLabel("Tip: doble clic sobre un slider o su valor para volver al valor por defecto.")
        note.setProperty("class", "note")
        note.setWordWrap(True)
        layout.addWidget(note)
        
        layout.addStretch()
        
        # Close button
        btn_close = QPushButton("Cerrar")
        btn_close.setFixedWidth(self._px(100))
        btn_close.setProperty("class", "primary")
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignCenter)
        
        dialog.exec()
            
    def _show_feedback(self, message: str):
        self.lbl_status.setText(f"● {message}")
        QTimer.singleShot(2000, lambda: self.lbl_status.setText(""))
        
    # ========== PRESET ACTIONS ==========
    
    def _apply_preset_from_combo(self):
        name = self.combo_presets.currentText()
        if name in self.presets:
            settings = normalize_shadow_settings(self.presets[name], missing_engine=SHADOW_ENGINE_COMPAT)
            self.presets[name] = settings.model_dump()
            self._apply_settings(settings)
            self._schedule_preview()
            
    def _action_save_current(self):
        current_name = self.combo_presets.currentText()
        if current_name:
            self.presets = self.preset_service.save_current_preset(
                self.presets,
                current_name,
                self._get_shadow_settings().model_dump(),
            )
            self._save_presets_to_disk()
            self._show_feedback("Preset guardado")
            
    def _action_create_new(self):
        name, ok = QInputDialog.getText(self, "Nuevo Preset", "Nombre del preset:")
        name = name.strip() if ok and name else ""
        if ok and name:
            if name in self.presets:
                self._show_feedback("Ese preset ya existe")
                return
            self.presets = self.preset_service.create_preset(
                self.presets,
                name,
                self._get_shadow_settings().model_dump(),
            )
            self._save_presets_to_disk()
            self.combo_presets.addItem(name)
            self.combo_presets.setCurrentText(name)
            self._show_feedback("Preset creado")
            
    def _action_rename(self):
        old_name = self.combo_presets.currentText()
        new_name, ok = QInputDialog.getText(self, "Renombrar preset", "Nuevo nombre:", text=old_name)
        new_name = new_name.strip() if ok and new_name else ""
        if ok and new_name:
            if new_name != old_name and new_name in self.presets:
                self._show_feedback("Ya existe un preset con ese nombre")
                return
            self.presets = self.preset_service.rename_preset(self.presets, old_name, new_name)
            self._save_presets_to_disk()
            self.combo_presets.setItemText(self.combo_presets.currentIndex(), new_name)
            self._show_feedback("Preset renombrado")
            
    def _action_delete(self):
        name = self.combo_presets.currentText()
        if QMessageBox.question(self, "Eliminar Preset", 
                               f"¿Eliminar '{name}'?") == QMessageBox.StandardButton.Yes:
            self.presets = self.preset_service.delete_preset(self.presets, name)
            self._save_presets_to_disk()
            self.combo_presets.removeItem(self.combo_presets.currentIndex())
            self._show_feedback("Preset eliminado")

    def _action_export_presets(self):
        default_name = str(Path.home() / "flatshot_presets.json")
        file_path, _selected_filter = QFileDialog.getSaveFileName(
            self,
            "Exportar presets",
            default_name,
            "Archivo JSON (*.json)",
        )
        if not file_path:
            return
        if not file_path.lower().endswith(".json"):
            file_path = f"{file_path}.json"

        if self.preset_service.export_presets_to_file(file_path):
            self._show_feedback("Presets exportados")
        else:
            QMessageBox.warning(
                self,
                "No se pudieron exportar",
                "FlatShot no ha podido generar el archivo de presets.",
            )

    def _action_import_presets(self):
        current_name = self.combo_presets.currentText()
        file_path, _selected_filter = QFileDialog.getOpenFileName(
            self,
            "Importar presets",
            str(Path.home()),
            "Archivo JSON (*.json)",
        )
        if not file_path:
            return

        message = QMessageBox(self)
        message.setWindowTitle("Importar presets")
        message.setText("¿Cómo quieres aplicar los presets del archivo?")
        message.setInformativeText(
            "Combinar conserva los presets actuales. Reemplazar deja solo los del archivo."
        )
        merge_button = message.addButton("Combinar", QMessageBox.ButtonRole.AcceptRole)
        replace_button = message.addButton("Reemplazar", QMessageBox.ButtonRole.DestructiveRole)
        message.addButton(QMessageBox.StandardButton.Cancel)
        message.exec()

        clicked = message.clickedButton()
        if clicked not in (merge_button, replace_button):
            return

        imported = self.preset_service.import_presets_from_file(
            file_path,
            merge=(clicked == merge_button),
        )
        if imported is None:
            QMessageBox.warning(
                self,
                "Archivo no válido",
                "No se han podido importar los presets. Revisa el archivo seleccionado.",
            )
            return

        self.presets = self.preset_service.get_flat_presets_from_categorized(imported)
        self._refresh_presets_combo(current_name)
        self._show_feedback("Presets importados")

    def _action_open_presets_folder(self):
        self._open_folder_in_explorer(self.config_dir)
             
    # ========== FOLDER & EXPORT ==========
    
    def _add_folders(self):
        """Add one or more folders to the export list."""
        initial = self.app_settings.get('last_input_folder', '')
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de imágenes", initial)
        if folder:
            self._add_folder_to_list(folder)
    
    def _add_folder_to_list(self, folder: str):
        """Add a folder to the selected list and recent history."""
        folder_path = Path(folder)
        if not folder_path.exists() or not folder_path.is_dir():
            self._show_feedback("La carpeta seleccionada no existe")
            return
        # Don't add duplicates
        if folder_path not in self.selected_folders:
            self.selected_folders.append(folder_path)
        
        # Save to recent folders and settings
        self._add_to_recent_folders(folder)
        self.app_settings['last_input_folder'] = folder
        self._save_app_settings()
        
        self._update_folder_ui()

    def _sync_folder_watcher(self):
        """Keep filesystem watcher aligned with selected folders."""
        if not hasattr(self, "folder_watcher"):
            return
        current = {str(f) for f in self.selected_folders if f.exists()}
        to_remove = self._watched_folders - current
        to_add = current - self._watched_folders
        if to_remove:
            try:
                self.folder_watcher.removePaths(list(to_remove))
            except Exception:
                pass
        if to_add:
            try:
                self.folder_watcher.addPaths(list(to_add))
            except Exception:
                pass
        self._watched_folders = current

    def _on_source_folder_changed(self, folder_path: str):
        """Debounced handler for file system changes in watched folders."""
        self._pending_folder_updates.add(folder_path)
        self._folder_update_timer.start(150)

    def _process_folder_updates(self):
        """Refresh UI when source folders change on disk."""
        if not self.selected_folders:
            return
        changed = {Path(p) for p in self._pending_folder_updates}
        self._pending_folder_updates.clear()
        # Refresh counts, grid preview and summary.
        self._update_folder_ui()
        # Refresh custom image if it belongs to a changed folder.
        if self.current_custom_path:
            try:
                custom_path = Path(self.current_custom_path)
                if not custom_path.exists():
                    if self.current_mock == 'custom_drop':
                        self.current_mock = 'dark'
                        self.btn_custom.hide()
                        self.mock_buttons['dark'].setChecked(True)
                        self._schedule_preview()
                    self.current_custom_path = None
                else:
                    for folder in changed:
                        try:
                            if custom_path.is_relative_to(folder):
                                self._set_custom_image_from_path(str(custom_path), show_feedback=False)
                                break
                        except Exception:
                            if str(custom_path).startswith(str(folder)):
                                self._set_custom_image_from_path(str(custom_path), show_feedback=False)
                                break
            except Exception:
                pass
    
    def _add_to_recent_folders(self, folder: str):
        """Add a folder to the recent folders list (max 10)."""
        recent = self.app_settings.get('recent_folders', [])
        # Remove if already in list (to move to front)
        if folder in recent:
            recent.remove(folder)
        # Add to front
        recent.insert(0, folder)
        # Keep only last 10
        self.app_settings['recent_folders'] = recent[:10]
        self._update_recent_folders_menu()
    
    def _update_recent_folders_menu(self):
        """Update the recent folders dropdown menu."""
        if not hasattr(self, 'recent_folders_menu'):
            return
        self.recent_folders_menu.clear()
        recent = self.app_settings.get('recent_folders', [])
        
        if not recent:
            action = self.recent_folders_menu.addAction("(Sin carpetas recientes)")
            action.setEnabled(False)
        else:
            for folder in recent:
                folder_path = Path(folder)
                # Show folder name with parent hint
                display_name = f"📁 {folder_path.name}"
                action = self.recent_folders_menu.addAction(display_name)
                action.setToolTip(folder)
                action.triggered.connect(lambda checked, f=folder: self._add_folder_to_list(f))
    
    def _show_recent_folders_menu(self, pos):
        """Show recent folders context menu at button position."""
        self.recent_folders_menu.exec(self.btn_add_folder.mapToGlobal(pos))
    
    def _clear_folders(self):
        """Clear all selected folders."""
        self.selected_folders.clear()
        self._update_folder_ui()
    
    def _remove_folder_item(self, item):
        """Remove a folder from the list on double-click."""
        row = self.folder_list.row(item)
        if 0 <= row < len(self.selected_folders):
            self.selected_folders.pop(row)
            self._update_folder_ui()
    
    def _update_folder_ui(self):
        """Update UI based on selected folders."""
        from PyQt6.QtWidgets import QListWidgetItem
        if not hasattr(self, 'folder_list') or self.folder_list is None:
            return
        try:
            import sip
            if sip.isdeleted(self.folder_list):
                return
        except Exception:
            pass
        
        try:
            self.folder_list.clear()
        except RuntimeError:
            return

        scan = self.folder_scanner.scan_folders(self.selected_folders, self.image_overrides)

        for folder_result in scan.folders:
            folder = folder_result.folder
            img_count = len(folder_result.images)
            item = QListWidgetItem(f"Carpeta: {folder.name}  -  {img_count} imágenes")
            item.setToolTip(str(folder))
            self.folder_list.addItem(item)
        
        # Show/hide elements in panel (details live in a dialog; keep hidden to avoid resizing)
        self.folder_list.setVisible(False)
        self.dest_group.setVisible(False)
        self.export_details_container.setVisible(False)

        self.batch_summary = build_batch_summary(
            scan,
            destination_label=presenters.format_destination_batch_label(
                self._build_export_config_from_settings()
            ),
        )
        self._update_batch_header()
        self.export_bar_mode = processing_mode_for_batch(self.batch_summary, self.export_bar_mode)
        self._update_export_bar_state()
         
        self._sync_grid_preview_with_folders()
        self._sync_folder_watcher()
        self._schedule_background_pre_render()
    
    def _on_dest_custom_toggled(self, checked: bool):
        """Handle custom destination radio button toggle."""
        self.btn_choose_dest.setEnabled(checked)
        self.app_settings['output_destination'] = 'custom' if checked else 'subfolder'
        if checked and self.custom_output_path:
            self.lbl_custom_dest.show()
        elif not checked:
            self.lbl_custom_dest.hide()
        self._update_export_destination_label()
    
    def _choose_custom_dest(self):
        """Choose a custom output destination folder."""
        initial_dir = str(self.custom_output_path) if self.custom_output_path else str(Path.home())
        folder = QFileDialog.getExistingDirectory(self, "Elegir carpeta de destino", initial_dir)
        if folder:
            self.custom_output_path = Path(folder)
            self.lbl_custom_dest.setText(f"→ {folder}")
            self.lbl_custom_dest.show()
            self.app_settings['custom_output_path'] = str(self.custom_output_path)
            self._update_export_destination_label()

    def _open_export_details_dialog(self):
        """Show export details in a compact dialog to avoid resizing the left panel."""
        from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QAbstractItemView, QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle("Detalles de exportación")
        dialog.setMinimumWidth(self._px(360))
        dialog.setProperty("class", "dialog")

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(self._px(16), self._px(12), self._px(16), self._px(12))
        layout.setSpacing(self._px(10))

        summary = QLabel(str(self.lbl_folder_summary.property("full_text") or self.lbl_folder_summary.text()))
        summary.setProperty("class", "dialog-text")
        layout.addWidget(summary)

        list_widget = QListWidget()
        list_widget.setProperty("class", "list")
        list_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        list_widget.setMaximumHeight(self._px(200))
        layout.addWidget(list_widget)
        display_names = self._build_folder_display_names(self.selected_folders)
        scan_by_folder = {
            str(result.folder): len(result.images)
            for result in self.folder_scanner.scan_folders(self.selected_folders, self.image_overrides).folders
        }

        def _add_folder_item(folder):
            img_count = scan_by_folder.get(str(folder), 0)
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(self._px(8), self._px(4), self._px(8), self._px(4))
            row_layout.setSpacing(self._px(6))

            lbl = QLabel(f"📁 {display_names.get(str(folder), folder.name)}")
            lbl.setToolTip(str(folder))
            count_lbl = QLabel(f"{img_count} imágenes")
            count_lbl.setProperty("class", "muted")
            count_lbl.setToolTip(str(folder))

            btn_remove = QPushButton(qta.icon('fa5s.trash-alt', color=COLORS['error']), "")
            btn_remove.setProperty("class", "icon-btn")
            btn_remove.setToolTip("Quitar carpeta de la lista")
            btn_remove.clicked.connect(lambda _, f=folder: on_remove_folder(f))

            row_layout.addWidget(lbl, 1)
            row_layout.addWidget(count_lbl)
            row_layout.addWidget(btn_remove)

            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, str(folder))
            item.setSizeHint(row_widget.sizeHint())
            list_widget.addItem(item)
            list_widget.setItemWidget(item, row_widget)

        for folder in self.selected_folders:
            _add_folder_item(folder)

        # Destination options (mirror main state)
        dest_box = QGroupBox("Destino")
        dest_layout = QVBoxLayout(dest_box)
        dest_layout.setContentsMargins(self._px(8), self._px(6), self._px(8), self._px(6))
        dest_layout.setSpacing(self._px(4))

        rb_sub = QRadioButton("Subcarpeta en origen")
        rb_sub.setChecked(self.rb_dest_subfolder.isChecked())
        dest_layout.addWidget(rb_sub)

        custom_row = QHBoxLayout()
        rb_custom = QRadioButton("Carpeta personalizada:")
        rb_custom.setChecked(self.rb_dest_custom.isChecked())
        custom_row.addWidget(rb_custom)

        btn_choose = QPushButton("Elegir...")
        btn_choose.setFixedWidth(self._px(80))
        btn_choose.setEnabled(rb_custom.isChecked())
        custom_row.addWidget(btn_choose)
        custom_row.addStretch()
        dest_layout.addLayout(custom_row)

        lbl_custom = QLabel(self.lbl_custom_dest.text())
        lbl_custom.setProperty("class", "muted")
        lbl_custom.setContentsMargins(self._px(20), 0, 0, 0)
        lbl_custom.setVisible(bool(self.lbl_custom_dest.text()))
        dest_layout.addWidget(lbl_custom)

        layout.addWidget(dest_box)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn_close = buttons.button(QDialogButtonBox.StandardButton.Close)
        if btn_close:
            btn_close.setProperty("class", "ghost")
        layout.addWidget(buttons)

        def on_remove_folder(folder):
            if folder in self.selected_folders:
                idx = self.selected_folders.index(folder)
                self.selected_folders.pop(idx)
                for i in range(list_widget.count()):
                    item = list_widget.item(i)
                    if item.data(Qt.ItemDataRole.UserRole) == str(folder):
                        list_widget.takeItem(i)
                        break
                self._update_folder_ui()
                summary.setText(self.lbl_folder_summary.text())

        def on_dest_changed():
            self.rb_dest_subfolder.setChecked(rb_sub.isChecked())
            self.rb_dest_custom.setChecked(rb_custom.isChecked())
            btn_choose.setEnabled(rb_custom.isChecked())

        def on_choose():
            self._choose_custom_dest()
            lbl_custom.setText(self.lbl_custom_dest.text())
            lbl_custom.setVisible(bool(self.lbl_custom_dest.text()))
            summary.setText(self.lbl_folder_summary.text())

        rb_sub.toggled.connect(on_dest_changed)
        rb_custom.toggled.connect(on_dest_changed)
        btn_choose.clicked.connect(on_choose)
        buttons.rejected.connect(dialog.reject)

        dialog.exec()

    def _start_export(self):
        """Start export process for all selected folders."""
        if not self.selected_folders:
            return

        # Stop opportunistic background work to free resources
        if hasattr(self, "pre_render_scheduler"):
            self.pre_render_scheduler.shutdown()
        self.export_state.error_message = ""
        self._sync_app_state()

        # Ensure we are working with the latest on-disk images before exporting.
        self._update_folder_ui()

        # Build export config
        export_config = self._build_export_config_from_settings()
        validation_errors = self.export_config_service.validate(export_config)
        if validation_errors:
            if not presenters.is_destination_configured(export_config):
                QMessageBox.warning(
                    self,
                    "Destino no configurado",
                    "Has seleccionado destino personalizado, pero no hay carpeta elegida.\n"
                    "Selecciona una carpeta de destino o cambia a subcarpeta en origen."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Configuración de exportación no válida",
                    "\n".join(validation_errors)
                )
            self._reset_export_ui()
            return

        active_variants = get_enabled_export_variants(export_config)
        if not active_variants:
            QMessageBox.warning(
                self,
                "Sin salidas activas",
                "Activa al menos una variante de salida antes de procesar."
            )
            self._reset_export_ui()
            return

        # Snapshot image lists at start to keep export consistent.
        snapshot_files = {
            folder: sorted(folder.glob("*.png"))
            for folder in self.selected_folders
        }
        self.export_state = build_export_state(
            destinations={
                str(destination)
                for destination in self.export_config_service.destinations_for_folders(
                    self.selected_folders,
                    export_config,
                )
            },
            variant_labels=[variant.label for variant in active_variants],
            source_count=sum(len(files) for files in snapshot_files.values()),
        )
        self._sync_app_state()

        self._apply_processing_state(
            processing_state_for_export_start(),
            update_progress=True,
        )
        self.btn_pause.setText("Pausar")
        self.btn_pause.setIcon(qta.icon('fa5s.pause', color='white'))
        self._set_widget_class(self.btn_pause, "warning-solid")
        self.btn_stop.setText("Detener")
        self.btn_stop.setEnabled(True)
        self._update_export_bar_state()

        # Single folder - use simple ExportWorker
        if len(self.selected_folders) == 1:
            self.worker = ExportWorker(
                str(self.selected_folders[0]),
                self._get_shadow_settings(),
                export_config,
                self.scale_curve,
                input_files=[str(p) for p in snapshot_files.get(self.selected_folders[0], [])],
                image_overrides=self.image_overrides
            )
            self.worker.progress_updated.connect(self.progress_bar.setValue)
            self.worker.log_updated.connect(self._on_export_log)
            self.worker.finished_process.connect(self._on_export_finished)
            self.worker.finished.connect(self._on_single_worker_thread_finished)
            self._apply_processing_state(
                processing_state_for_single_export(self.selected_folders[0].name),
                update_pre_render=False,
            )
            self._update_export_bar_state()
            self.worker.start()
        else:
            # Multiple folders - use QueueWorker
            jobs = [
                JobItem(folder_path=str(f), input_files=[str(p) for p in snapshot_files.get(f, [])])
                for f in self.selected_folders
            ]
            preset_name = self.combo_presets.currentText()
            
            self.queue_worker = QueueWorker(
                jobs,
                self._get_shadow_settings(),
                export_config,
                self.scale_curve,
                preset_name,
                image_overrides=self.image_overrides
            )
            
            self.queue_worker.job_started.connect(self._on_queue_job_started)
            self.queue_worker.job_progress.connect(self._on_queue_job_progress)
            self.queue_worker.log_message.connect(self._on_export_log)
            self.queue_worker.queue_finished.connect(self._on_queue_finished)
            self.queue_worker.finished.connect(self._on_queue_worker_thread_finished)
            self.queue_worker.start()
    
    def _on_queue_job_started(self, index: int, folder_path: str):
        """Called when a job in the queue starts."""
        self._apply_processing_state(
            processing_state_for_queue_job(index, len(self.selected_folders), folder_path),
            update_pre_render=False,
        )
        self._update_export_bar_state()
    
    def _on_queue_job_progress(self, index: int, progress: int):
        """Called when a job's progress updates."""
        self.progress_bar.setValue(
            calculate_queue_overall_progress(index, progress, len(self.selected_folders))
        )
    
    def _on_queue_finished(self, completed: int, errors: int, total_images: int):
        """Called when all queue jobs are finished."""
        self._reset_export_ui()

        if errors == 0:
            self._show_export_result_dialog(
                title="Cola completada",
                success=True,
                summary_lines=build_queue_export_summary_lines(
                    self.export_state,
                    completed=completed,
                    errors=errors,
                    total_images=total_images,
                ),
                destinations=self.export_state.destinations,
            )
        else:
            self._show_export_result_dialog(
                title="Cola completada con errores",
                success=False,
                summary_lines=build_queue_export_summary_lines(
                    self.export_state,
                    completed=completed,
                    errors=errors,
                    total_images=total_images,
                ),
                destinations=self.export_state.destinations,
            )
        
    def _toggle_pause(self):
        """Toggle pause/resume state of the export queue."""
        if not hasattr(self, 'queue_worker') or not self.queue_worker or not self.queue_worker.isRunning():
            return
            
        if self.queue_worker.is_paused:
            self.queue_worker.resume()
            self._apply_processing_state(
                processing_state_for_pause(False),
                update_pre_render=False,
            )
            self.btn_pause.setText("Pausar")
            self.btn_pause.setIcon(qta.icon('fa5s.pause', color='white'))
            self._set_widget_class(self.btn_pause, "warning-solid")
        else:
            self.queue_worker.pause()
            self._apply_processing_state(
                processing_state_for_pause(True),
                update_pre_render=False,
            )
            self.btn_pause.setText("Reanudar")
            self.btn_pause.setIcon(qta.icon('fa5s.play', color='white'))
            self._set_widget_class(self.btn_pause, "success-solid")
        self._update_export_bar_state()

    def _stop_export(self):
        """Stop current export or queue."""
        if hasattr(self, 'queue_worker') and self.queue_worker and self.queue_worker.isRunning():
            self.queue_worker.stop()
        elif hasattr(self, 'worker') and self.worker:
            self.worker.stop()
        
        self._apply_processing_state(
            processing_state_for_stop(),
            update_pre_render=False,
        )
        self.btn_stop.setText("Deteniendo...")
        self.btn_stop.setEnabled(False)
        self._update_export_bar_state()
    
    def _reset_export_ui(self):
        """Reset export UI to idle state."""
        self.btn_stop.setText("Detener")
        self.btn_stop.setEnabled(True)
        self._apply_processing_state(
            processing_state_after_reset(
                self.batch_summary,
                selected_folders_count=len(self.selected_folders),
            ),
            update_progress=True,
            update_pre_render=False,
        )
        self._update_export_bar_state()
        self._schedule_background_pre_render()
            
    def _on_export_finished(self, success: bool, processed: int = 0, total: int = 0, duration: float = 0.0):
        """Called when single-folder export finishes."""
        self._reset_export_ui()

        if success:
            self._show_export_result_dialog(
                title="Proceso completado",
                success=True,
                summary_lines=build_single_export_summary_lines(
                    self.export_state,
                    success=True,
                    processed=processed,
                    total=total,
                    duration=duration,
                ),
                destinations=self.export_state.destinations,
            )
        else:
            self._show_export_result_dialog(
                title="Proceso incompleto",
                success=False,
                summary_lines=build_single_export_summary_lines(
                    self.export_state,
                    success=False,
                    processed=processed,
                    total=total,
                    duration=duration,
                ),
                destinations=self.export_state.destinations,
            )

    def _on_single_worker_thread_finished(self):
        """Release single-folder worker only after QThread has fully stopped."""
        self.worker = None

    def _on_queue_worker_thread_finished(self):
        """Release queue worker only after QThread has fully stopped."""
        self.queue_worker = None
            
    # ========== DIALOGS ==========
    
    def _open_export_config(self):
        current_config = self._build_export_config_from_settings()
        
        dlg = ExportConfigDialog(current_config, self)
        if dlg.exec():
            new_settings = dlg.get_settings()
            self.app_settings.update(new_settings.model_dump())
            self._apply_export_preferences(new_settings)
            self._save_app_settings()
            self._schedule_preview()
            self._show_feedback("Configuración guardada")
            
    def _open_scale_calibrator(self):
        current_padding = self.sl_padding.value()
        folder = self.selected_folders[0] if self.selected_folders else None
        dlg = CurveEditorDialog(self.scale_curve.model_dump(), folder, current_padding, self)
        if dlg.exec():
            new_curve_dict = dlg.get_current_curve()
            self.scale_curve = CurveData(**new_curve_dict)
            self._save_app_settings()
            self._schedule_preview()
            self._show_feedback("Curva de escala actualizada")
    
    # ========== HISTORY (UNDO/REDO) ==========
    
    def _push_history(self):
        """Push current settings to history stack."""
        settings = self._get_shadow_settings()
        self.history_manager.push(settings)

    def _schedule_history_push(self):
        if not hasattr(self, "_history_timer"):
            return
        self._history_timer.start(350)

    def _setup_history_tracking(self):
        """Register change hooks for undo/redo snapshots."""
        self._history_timer = QTimer(self)
        self._history_timer.setSingleShot(True)
        self._history_timer.timeout.connect(self._push_history)

        sliders = [
            self.sl_distance,
            self.sl_blur,
            self.sl_spread,
            self.sl_fusion,
            self.sl_contact_blur,
            self.sl_contraction,
            self.sl_opacity,
            self.sl_noise,
            self.sl_padding,
            self.sl_scale_adjustment,
        ]
        for control in sliders:
            control.slider.sliderPressed.connect(self._on_slider_drag_started)
            control.slider.sliderReleased.connect(self._on_slider_drag_ended)
            control.slider.sliderReleased.connect(self._schedule_history_push)
            control.spinbox.editingFinished.connect(self._schedule_history_push)

        self.light_angle.angleChanged.connect(self._schedule_history_push)
        self.angle_spinbox.editingFinished.connect(self._schedule_history_push)
        self.chk_adaptive.toggled.connect(self._schedule_history_push)
        if hasattr(self, 'combo_shadow_engine'):
            self.combo_shadow_engine.currentIndexChanged.connect(self._schedule_history_push)

    def _on_slider_drag_started(self):
        """Called when a slider interaction starts."""
        self._slider_dragging = True
        self._cancel_background_pre_render()

    def _on_slider_drag_ended(self):
        """Called when a slider interaction ends."""
        self._slider_dragging = False
        # Sync grid and check for background render
        self._deferred_grid_sync()
        self._schedule_background_pre_render()
    
    def _action_undo(self):
        """Undo to previous settings state."""
        if not self.history_manager.can_undo():
            self._show_feedback("Nada que deshacer")
            return
        
        settings = self.history_manager.undo()
        if settings:
            self._apply_settings(settings)
            self._show_feedback(f"Deshacer ({self.history_manager.current_position}/{self.history_manager.history_size})")
    
    def _action_redo(self):
        """Redo to next settings state."""
        if not self.history_manager.can_redo():
            self._show_feedback("Nada que rehacer")
            return
        
        settings = self.history_manager.redo()
        if settings:
            self._apply_settings(settings)
            self._show_feedback(f"Rehacer ({self.history_manager.current_position}/{self.history_manager.history_size})")
    
    def _apply_settings(self, settings: ShadowSettings):
        """Apply a ShadowSettings object to all controls."""
        settings = normalize_shadow_settings(settings, missing_engine=SHADOW_ENGINE_COMPAT)
        controls = [
            (self.sl_distance, settings.distance),
            (self.sl_blur, settings.blur),
            (self.sl_spread, settings.spread),
            (self.sl_fusion, settings.fusion),
            (self.sl_opacity, settings.opacity),
            (self.sl_noise, settings.noise),
            (self.sl_padding, settings.padding),
            (self.sl_scale_adjustment, settings.scale_adjustment),
            (self.sl_contact_blur, settings.contact_blur),
            (self.sl_contraction, settings.contraction),
        ]

        self.light_angle.blockSignals(True)
        self.angle_spinbox.blockSignals(True)
        self.chk_adaptive.blockSignals(True)
        if hasattr(self, 'combo_shadow_engine'):
            self.combo_shadow_engine.blockSignals(True)
        for control, _ in controls:
            control.slider.blockSignals(True)
            control.spinbox.blockSignals(True)

        try:
            self.light_angle.setAngle(settings.angle)
            self.angle_spinbox.setValue(settings.angle)
            for control, value in controls:
                control.slider.setValue(value)
                control.spinbox.setValue(value)
            self.chk_adaptive.setChecked(settings.adaptive_zoom)
            if hasattr(self, 'combo_shadow_engine'):
                engine_idx = self.combo_shadow_engine.findData(settings.shadow_engine)
                if engine_idx >= 0:
                    self.combo_shadow_engine.setCurrentIndex(engine_idx)
        finally:
            self.light_angle.blockSignals(False)
            self.angle_spinbox.blockSignals(False)
            self.chk_adaptive.blockSignals(False)
            if hasattr(self, 'combo_shadow_engine'):
                self.combo_shadow_engine.blockSignals(False)
            for control, _ in controls:
                control.slider.blockSignals(False)
                control.spinbox.blockSignals(False)

        self._schedule_preview()
    
    # ========== LOG VIEWER ==========
    
    def _show_log_viewer(self):
        """Show dialog with today's activity log."""
        log_path = self.log_manager.get_today_log_path()
        entries = self.log_manager.get_recent_entries(100)
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Registro de actividad")
        dialog.setMinimumSize(self._px(700), self._px(500))
        dialog.setProperty("class", "dialog")
        
        layout = QVBoxLayout(dialog)
        
        # Header
        header = QLabel(f"📋 Log: {log_path.name}")
        header.setProperty("class", "dialog-title")
        layout.addWidget(header)
        
        # Log content
        from PyQt6.QtWidgets import QTextEdit
        log_text = QTextEdit()
        log_text.setProperty("class", "log-view")
        log_text.setReadOnly(True)
        
        if entries:
            log_text.setPlainText("".join(entries))
        else:
            log_text.setPlainText("No hay entradas de registro para hoy.")
        
        # Scroll to bottom
        log_text.moveCursor(log_text.textCursor().End)
        layout.addWidget(log_text)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        btn_open_folder = QPushButton("Abrir carpeta de logs")
        btn_open_folder.setProperty("class", "primary")
        btn_open_folder.clicked.connect(lambda: self._open_folder_in_explorer(log_path.parent))
        btn_layout.addWidget(btn_open_folder)
        
        btn_layout.addStretch()
        
        btn_close = QPushButton("Cerrar")
        btn_close.setProperty("class", "ghost")
        btn_close.clicked.connect(dialog.accept)
        btn_layout.addWidget(btn_close)
        
        layout.addLayout(btn_layout)
        
        dialog.exec()

    def _open_folder_in_explorer(self, folder: Path):
        """Open folder in system file explorer in a cross-platform way."""
        try:
            folder_str = str(folder)
            if sys.platform.startswith("win"):
                # Open Explorer explicitly maximized.
                subprocess.Popen(
                    f'start "" /max explorer "{folder_str}"',
                    shell=True
                )
            elif sys.platform == "darwin":
                subprocess.run(["open", folder_str], check=False)
            else:
                subprocess.run(["xdg-open", folder_str], check=False)
        except Exception as e:
            self._show_feedback("No se pudo abrir la carpeta de logs")
            self._log_error(f"[open-folder-error] {folder}: {e}")

    def _show_export_result_dialog(self, title: str, success: bool, summary_lines: list[str], destinations: list[str]):
        """Show a richer export summary dialog with destination shortcuts."""
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumSize(self._px(640), self._px(420))
        dialog.setProperty("class", "dialog")

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(self._px(16), self._px(14), self._px(16), self._px(14))
        layout.setSpacing(self._px(10))

        icon_name = 'fa5s.check-circle' if success else 'fa5s.exclamation-triangle'
        icon_color = COLORS['success'] if success else COLORS['error']
        header_row = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon(icon_name, color=icon_color).pixmap(self._px(22), self._px(22)))
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
                self._open_folder_in_explorer(Path(valid_destinations[row]))

        btn_open_selected.clicked.connect(_open_selected)
        dest_list.itemDoubleClicked.connect(lambda _: _open_selected())
        btn_close.clicked.connect(dialog.accept)

        dialog.exec()
            
    # ========== WINDOW EVENTS ==========
    
    def resizeEvent(self, event):
        if hasattr(self, 'current_qimage') and self.current_qimage:
            pixmap = QPixmap.fromImage(self.current_qimage)
            self.canvas.setProcessedImage(pixmap)
        super().resizeEvent(event)
        if hasattr(self, "lbl_export_config_summary"):
            self._refresh_elided_export_labels()
            
    def closeEvent(self, event):
        """Save session state before closing and stop background preview tasks."""
        try:
            app = QApplication.instance()
            if app is not None:
                app.removeEventFilter(self)
            if self.queue_worker and self.queue_worker.isRunning():
                self.queue_worker.stop()
                self.queue_worker.wait(3000)
            if self.worker and self.worker.isRunning():
                self.worker.stop()
                self.worker.wait(3000)

            self.preview_timer.stop()
            self.preview_pool.clear()
            self.preview_pool.waitForDone(1500)

            # Gather session data
            output_destination = 'subfolder'
            try:
                import sip
                if hasattr(self, 'rb_dest_custom') and self.rb_dest_custom is not None:
                    if not sip.isdeleted(self.rb_dest_custom) and self.rb_dest_custom.isChecked():
                        output_destination = 'custom'
            except Exception:
                pass

            # Save current shadow settings
            current_settings = self._get_shadow_settings()
            session_data = SessionService.build_session_data(
                geometry=self.saveGeometry().toBase64().data().decode(),
                state=self.saveState().toBase64().data().decode(),
                selected_folders=self.selected_folders,
                current_preset=self.combo_presets.currentText(),
                current_mock=self.current_mock,
                splitter_sizes=self.splitter.sizes(),
                output_folder_name=self.app_settings.get('output_folder_name'),
                suffix=self.app_settings.get('suffix'),
                export_format=self.app_settings.get('format'),
                output_destination=output_destination,
                custom_output_path=self.custom_output_path,
                shadow_settings=current_settings.model_dump(),
            )
            
            self.session_manager.save_session(session_data)
            try:
                self.app_settings['splitter_sizes'] = self.splitter.sizes()
                self._save_app_settings()
                if hasattr(self, "pre_render_scheduler"):
                    self.pre_render_scheduler.shutdown()
                    self.pre_render_scheduler.cache.prune(
                        max_files=1000,
                        max_bytes=int(self.app_settings.get('background_pre_render_cache_mb', 2048)) * 1024 * 1024,
                    )
            except Exception:
                pass
            
        except Exception as e:
            self.log_manager.log_error(f"Error saving session: {e}")
        
        super().closeEvent(event)

    def _restore_session(self) -> bool:
        """Restore application state from saved session."""
        try:
            data = self.session_manager.load_session()
            if not data:
                return False
                
            # Restore geometry and state
            if 'geometry' in data:
                from PyQt6.QtCore import QByteArray
                self.restoreGeometry(QByteArray.fromBase64(data['geometry'].encode()))
            if 'state' in data:
                from PyQt6.QtCore import QByteArray
                self.restoreState(QByteArray.fromBase64(data['state'].encode()))
                
            # Restore splitter sizes
            if 'splitter_sizes' in data and hasattr(self, 'splitter'):
                self.splitter.setSizes(data['splitter_sizes'])
                
            # Restore folders
            if 'selected_folders' in data:
                can_restore = True
                try:
                    import sip
                    if not hasattr(self, 'folder_list') or self.folder_list is None:
                        can_restore = False
                    elif sip.isdeleted(self.folder_list):
                        can_restore = False
                except Exception:
                    pass
                if can_restore:
                    for folder in data['selected_folders']:
                        self._add_folder_to_list(folder)
                    
            # Restore preset
            if 'current_preset' in data:
                index = self.combo_presets.findText(data['current_preset'])
                if index >= 0:
                    self.combo_presets.setCurrentIndex(index)
                    
            # Restore mock
            if 'current_mock' in data:
                saved_mock = data['current_mock']
                if saved_mock == 'med':
                    saved_mock = 'medium'
                if saved_mock in self.mockups:
                    self.current_mock = saved_mock
                    if saved_mock in self.mock_buttons:
                        self.mock_buttons[saved_mock].setChecked(True)
                else:
                    self.current_mock = 'dark'
                    self.mock_buttons['dark'].setChecked(True)
            
            # Restore export config
            if 'export_config' in data:
                exp = data['export_config']
                restored_export = self._build_export_config_from_settings()
                restored_export.output_destination = exp.get('output_destination', restored_export.output_destination)
                restored_export.custom_output_path = exp.get('custom_output_path', restored_export.custom_output_path)
                self._apply_export_preferences(restored_export)
            
            if 'shadow_settings' in data:
                self._apply_settings(
                    normalize_shadow_settings(
                        data['shadow_settings'],
                        missing_engine=SHADOW_ENGINE_COMPAT,
                    )
                )
            else:
                self._schedule_preview()
            return True
                        
        except Exception as e:
            self._log_error(f"Error restoring session: {e}")
        return False

