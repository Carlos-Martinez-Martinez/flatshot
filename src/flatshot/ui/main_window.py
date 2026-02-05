"""
Modern Main Window with Professional UI Layout
"""
import sys
import os
import json
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
    QMenu, QRadioButton, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor, QPainterPath, QAction, QIcon, QFont

from flatshot.core.engine import ShadowEngine
from flatshot.core.models import ShadowSettings, ExportConfig, CurveData, JobItem
from flatshot.utils.config import ConfigManager
from flatshot.utils.history_manager import HistoryManager
from flatshot.utils.log_manager import LogManager
from flatshot.utils.session_manager import SessionManager
from flatshot.ui.dialogs import CurveEditorDialog, ExportConfigDialog
from flatshot.ui.styles import scale_stylesheet
from flatshot.ui.widgets import SmartSlider, LightAngleWidget, ComparisonCanvas, FloatingToolbar, ModernSplashScreen, CollapsibleSection
from flatshot.ui.queue_widget import QueueWidget
from flatshot.ui.grid_preview import GridPreviewWidget
from flatshot.workers.export_worker import ExportWorker
from flatshot.workers.queue_worker import QueueWorker

# Icon library
import qtawesome as qta

# Allow loading truncated images to avoid decoder aborts
ImageFile.LOAD_TRUNCATED_IMAGES = True


def _render_preview_task(pil_img: Image.Image, target_size, settings_dict: dict, curve_dict: dict, scale_ratio: float, is_preview: bool = True):
    """Render preview off the UI thread; safe for ThreadPoolExecutor."""
    from flatshot.core.engine import ShadowEngine
    from flatshot.core.models import ShadowSettings, CurveData
    settings = ShadowSettings(**settings_dict)
    curve = CurveData(**curve_dict)
    final_pil = ShadowEngine.aplicar_efectos(
        pil_img,
        settings,
        target_size,
        scale_factor=scale_ratio,
        curve_data=curve,
        is_preview=is_preview
    )
    if final_pil.mode == "RGBA":
        bg = Image.new("RGB", final_pil.size, (230, 230, 230))
        bg.paste(final_pil, (0, 0), mask=final_pil)
        final_for_display = bg
    else:
        final_for_display = final_pil
    im_data = final_for_display.convert("RGB").tobytes("raw", "RGB")
    return final_for_display.width, final_for_display.height, im_data


from PyQt6.QtCore import QRunnable, QThreadPool, QObject


class PreviewWorkerSignals(QObject):
    """Signals for PreviewWorker to communicate with main thread."""
    finished = pyqtSignal(object, int)  # (QImage, quality_level)
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
            width, height, im_data = _render_preview_task(
                self.pil_img,
                self.target_size,
                self.settings_dict,
                self.curve_dict,
                self.scale_ratio
            )
            qim = QImage(im_data, width, height, width * 3, QImage.Format.Format_RGB888).copy()
            # The signal will be queued to the main thread
            self.signals.finished.emit(qim, self.quality_level)
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
        
        # Simple debounce timer for preview
        self.preview_timer = QTimer()
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self._start_preview_thread)
        
        # Queue worker reference
        self.queue_worker = None
        self.worker = None
        self._last_export_destinations = []
        
        # Load configuration
        self.presets = ConfigManager.get_flat_presets_from_categorized(
            ConfigManager.load_categorized_presets()
        )
        if not self.presets:
            self.presets = ConfigManager.load_presets()
        if not self.presets:
            self.presets = self._get_default_presets()
            
        self.settings_file = ConfigManager.get_config_dir() / "settings.json"
        self.app_settings = self._load_app_settings()
        
        curve_dict = self.app_settings.get('scale_curve', {
            'xp': [0.15, 0.42, 0.52, 0.85, 1.20],
            'fp': [0.98, 0.98, 0.70, 0.82, 0.80]
        })
        self.scale_curve = CurveData(**curve_dict)
        
        # Build UI
        self._init_menu()
        self._init_ui()
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
        # Always start maximized for better workspace visibility.
        QTimer.singleShot(0, self.showMaximized)
    
    def _normalize_scale(self, scale: float) -> float:
        """Clamp the incoming UI scale to a safe range."""
        try:
            return max(min(scale, 1.0), 0.65)
        except Exception:
            return 1.0
    
    def _px(self, value: int) -> int:
        """Scale a pixel value according to the UI scale."""
        return max(int(round(value * self.ui_scale)), 1)
            
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
        
        exit_action = QAction("Salir", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("Ver")
        
        grid_action = QAction("Mostrar cuadrícula", self, checkable=True)
        grid_action.triggered.connect(lambda checked: self.canvas.setGridVisible(checked))
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
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # === LEFT PANEL (Controls) ===
        left_panel = self._create_control_panel()
        
        # === CENTER PANEL (Canvas Preview) ===
        center_panel = self._create_preview_panel()
        
        # === RIGHT PANEL (Grid Preview) ===
        right_panel = self._create_grid_panel()
        
        # Splitter for resizable panels (3 columns)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(left_panel)
        self.splitter.addWidget(center_panel)
        self.splitter.addWidget(right_panel)
        self.splitter.setSizes([self._px(340), self._px(700), self._px(280)])
        self.splitter.setStretchFactor(0, 0)  # Controls: fixed
        self.splitter.setStretchFactor(1, 1)  # Canvas: stretch
        self.splitter.setStretchFactor(2, 0)  # Grid: fixed
        
        main_layout.addWidget(self.splitter)
        
    def _create_control_panel(self) -> QWidget:
        """Create the left control panel with all settings."""
        panel = QWidget()
        panel.setFixedWidth(self._px(340))  # Compact width to fit on smaller screens
        panel.setStyleSheet("background-color: #1E1E1E;")
        
        # Scroll area for controls
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        content = QWidget()
        content.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(
            self._px(8), self._px(8), self._px(8), self._px(2)
        )  # Minimal margins
        layout.setSpacing(self._px(6))
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetMinimumSize)
        
        # Header
        header = QLabel("FlatShot")
        header.setProperty("class", "heading")
        layout.addWidget(header)
        
        # === PRESETS SECTION ===
        self._sections = {}
        presets_section = self._create_section("PRESETS", "presets", default_expanded=True, parent=content)
        if presets_section is not None:
            layout.addWidget(presets_section)
            self._sections["presets"] = presets_section
            self._build_presets_section(presets_section.content_layout)
        
        # === LIGHTING SECTION ===
        lighting_section = self._create_section("ILUMINACIÓN", "lighting", default_expanded=True, parent=content)
        if lighting_section is not None:
            layout.addWidget(lighting_section)
            self._sections["lighting"] = lighting_section
            self._build_lighting_section(lighting_section.content_layout)
        
        # === SHADOWS SECTION ===
        shadows_section = self._create_section("SOMBRAS", "shadows", default_expanded=True, parent=content)
        if shadows_section is not None:
            layout.addWidget(shadows_section)
            self._sections["shadows"] = shadows_section
            self._build_shadows_section(shadows_section.content_layout)
        
        # === FINISHING SECTION ===
        finishing_section = self._create_section("ACABADO", "finishing", default_expanded=False, parent=content)
        if finishing_section is not None:
            layout.addWidget(finishing_section)
            self._sections["finishing"] = finishing_section
            self._build_finishing_section(finishing_section.content_layout)
        
        layout.addSpacing(self._px(6))

        scroll.setWidget(content)
        
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(self._px(0), self._px(0), self._px(0), self._px(0))
        panel_layout.setSpacing(self._px(4))
        panel_layout.addWidget(scroll, 1)

        # === EXPORT SECTION (Fixed at bottom, always visible) ===
        export_section = self._create_export_section()
        self.export_section = export_section
        if export_section is not None:
            panel_layout.addWidget(export_section, 0)
        
        return panel

    def _on_section_toggled(self, key: str, checked: bool):
        section_state = self.app_settings.get('section_visibility', {})
        section_state[key] = bool(checked)
        self.app_settings['section_visibility'] = section_state
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
        layout.setSpacing(self._px(8))
        
        # Combo box
        self.combo_presets = QComboBox()
        self.combo_presets.addItems(list(self.presets.keys()))
        self.combo_presets.currentIndexChanged.connect(self._apply_preset_from_combo)
        layout.addWidget(self.combo_presets)
        
        # Action buttons row - compact icon-only buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(self._px(4))
        
        # Icon color for dark theme
        icon_color = '#A0A0A0'
        icon_color_danger = '#E57373'
        
        btn_save = QPushButton(qta.icon('fa5s.save', color=icon_color), "")
        btn_save.setProperty("class", "icon-btn")
        btn_save.setToolTip("Guardar preset (Ctrl+S)")
        btn_save.clicked.connect(self._action_save_current)
        btn_layout.addWidget(btn_save)
        
        btn_new = QPushButton(qta.icon('fa5s.plus', color=icon_color), "")
        btn_new.setProperty("class", "icon-btn")
        btn_new.setToolTip("Crear nuevo preset")
        btn_new.clicked.connect(self._action_create_new)
        btn_layout.addWidget(btn_new)
        
        btn_rename = QPushButton(qta.icon('fa5s.edit', color=icon_color), "")
        btn_rename.setProperty("class", "icon-btn")
        btn_rename.setToolTip("Renombrar preset")
        btn_rename.clicked.connect(self._action_rename)
        btn_layout.addWidget(btn_rename)
        
        btn_delete = QPushButton(qta.icon('fa5s.trash-alt', color=icon_color_danger), "")
        btn_delete.setProperty("class", "icon-btn")
        btn_delete.setToolTip("Eliminar preset")
        btn_delete.clicked.connect(self._action_delete)
        btn_layout.addWidget(btn_delete)
        
        # Spacer
        btn_layout.addSpacing(self._px(8))
        
        # Reset to defaults button
        btn_reset = QPushButton(qta.icon('fa5s.undo', color='#A0A0A0'), "")
        btn_reset.setProperty("class", "icon-btn")
        btn_reset.setToolTip("Restaurar valores por defecto (Ctrl+R)")
        btn_reset.clicked.connect(self._reset_to_defaults)
        btn_layout.addWidget(btn_reset)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Status label
        self.lbl_status = QLabel("")
        self.lbl_status.setProperty("class", "subheading")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_status)
        
        return
    
    def _build_lighting_section(self, layout: QVBoxLayout):
        """Populate the lighting controls section."""
        layout.setSpacing(self._px(10))
        
        # Light angle widget with label
        angle_layout = QHBoxLayout()
        
        angle_label_layout = QVBoxLayout()
        angle_label = QLabel("Fuente de luz")
        angle_label.setProperty("class", "param-label")
        angle_label.setToolTip(
            "<b>Ángulo de la fuente de luz</b><br><br>"
            "Define desde qué dirección viene la luz.<br>"
            "<b>0°</b> = Luz desde arriba<br>"
            "<b>90°</b> = Luz desde la derecha<br>"
            "<b>180°</b> = Luz desde abajo (cenital invertida)<br>"
            "<b>270°</b> = Luz desde la izquierda"
        )
        angle_label_layout.addWidget(angle_label)
        
        self.angle_spinbox = QSpinBox()
        self.angle_spinbox.setRange(0, 359)
        self.angle_spinbox.setSuffix("°")
        self.angle_spinbox.setValue(180)
        self.angle_spinbox.setToolTip("Ángulo exacto en grados (0-359)")
        angle_label_layout.addWidget(self.angle_spinbox)
        angle_label_layout.addStretch()
        
        angle_layout.addLayout(angle_label_layout)
        
        self.light_angle = LightAngleWidget(scale=self.ui_scale)
        self.light_angle.setToolTip(
            "<b>Control circular de ángulo</b><br><br>"
            "Haz clic y arrastra para ajustar la dirección de la luz."
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
        layout.setSpacing(self._px(6))
        
        self.sl_blur = SmartSlider(
            "Desenfoque", 0, 100, 25, "px",
            "<b>Desenfoque principal (Blur)</b><br><br>"
            "Suaviza los bordes de la sombra proyectada.<br><br>"
            "<b>0-15:</b> Sombra dura y definida (luz intensa)<br>"
            "<b>15-40:</b> Sombra natural y suave<br>"
            "<b>40+:</b> Sombra muy difusa (luz ambiental)",
            scale=self.ui_scale
        )
        self.sl_blur.valueChanged.connect(self._schedule_preview)
        layout.addWidget(self.sl_blur)
        
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
        layout.setSpacing(self._px(6))
        
        self.sl_opacity = SmartSlider(
            "Opacidad", 0, 100, 30, "%",
            "<b>Opacidad / Intensidad</b><br><br>"
            "Controla qué tan oscura es la sombra en general.<br><br>"
            "<b>10-25%:</b> Sombra sutil, ideal para fondos claros<br>"
            "<b>25-50%:</b> Sombra visible y natural<br>"
            "<b>50%+:</b> Sombra intensa, dramática",
            scale=self.ui_scale
        )
        self.sl_opacity.valueChanged.connect(self._schedule_preview)
        layout.addWidget(self.sl_opacity)
        
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
        
        self.sl_padding = SmartSlider(
            "Margen", 0, 50, 10, "%",
            "<b>Margen / Espacio (Padding)</b><br><br>"
            "Define el espacio vacío alrededor del producto.<br><br>"
            "<b>5-10%:</b> Producto ocupa casi todo el lienzo<br>"
            "<b>10-20%:</b> Espacio equilibrado para e-commerce<br>"
            "<b>20%+:</b> Producto pequeño con mucho 'aire'",
            scale=self.ui_scale
        )
        self.sl_padding.valueChanged.connect(self._schedule_preview)
        layout.addWidget(self.sl_padding)
        
        # Adaptive zoom checkbox
        self.chk_adaptive = QCheckBox("Compensación óptica inteligente")
        self.chk_adaptive.setChecked(True)
        self.chk_adaptive.setToolTip(
            "<b>Compensación óptica automática</b><br><br>"
            "Ajusta el tamaño del producto según su proporción (aspect ratio).<br><br>"
            "Los productos más anchos se escalan ligeramente diferente<br>"
            "que los más verticales, para que visualmente ocupen<br>"
            "un espacio similar en la imagen final.<br><br>"
            "<b>Activado:</b> Tamaño perceptualmente uniforme<br>"
            "<b>Desactivado:</b> Escalado matemático puro"
        )
        self.chk_adaptive.toggled.connect(self._schedule_preview)
        layout.addWidget(self.chk_adaptive)
        
        return
    
    def _create_export_section(self) -> QGroupBox:
        """Create the export controls section with multi-folder support."""
        group = QGroupBox("EXPORTAR")
        group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(group)
        layout.setSpacing(self._px(6))
        
        # Folder selection buttons
        folder_btn_layout = QHBoxLayout()
        folder_btn_layout.setSpacing(self._px(4))
        
        icon_color = '#A0A0A0'
        
        # Add folder button with right-click context menu for recent folders
        self.btn_add_folder = QPushButton(qta.icon('fa5s.folder-plus', color=icon_color), " Añadir carpeta")
        self.btn_add_folder.setToolTip("Añadir carpeta · Click derecho: carpetas recientes")
        self.btn_add_folder.clicked.connect(self._add_folders)
        self.btn_add_folder.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.btn_add_folder.customContextMenuRequested.connect(self._show_recent_folders_menu)
        self.recent_folders_menu = QMenu(self)
        self._update_recent_folders_menu()
        folder_btn_layout.addWidget(self.btn_add_folder)
        
        self.btn_clear_folders = QPushButton(qta.icon('fa5s.trash-alt', color='#E57373'), "")
        self.btn_clear_folders.setProperty("class", "icon-btn")
        self.btn_clear_folders.setToolTip("Limpiar lista de carpetas")
        self.btn_clear_folders.clicked.connect(self._clear_folders)
        self.btn_clear_folders.setEnabled(False)
        folder_btn_layout.addWidget(self.btn_clear_folders)
        
        folder_btn_layout.addStretch()

        # Button to open details dialog (keeps panel height stable)
        self.btn_export_details = QPushButton(qta.icon('fa5s.list-alt', color=icon_color), " Ver lista")
        self.btn_export_details.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.btn_export_details.setMinimumWidth(self._px(92))
        self.btn_export_details.setToolTip("Ver carpetas seleccionadas y destino de exportación")
        self.btn_export_details.clicked.connect(self._open_export_details_dialog)
        folder_btn_layout.addWidget(self.btn_export_details)
        layout.addLayout(folder_btn_layout)
        
        # Details container (folder list + destination options) collapsible
        details_container = QWidget()
        details_layout = QVBoxLayout(details_container)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(self._px(4))

        # Folder list (compact table)
        from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QAbstractItemView
        self.folder_list = QListWidget()
        self.folder_list.setMaximumHeight(self._px(90))
        self.folder_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.folder_list.setStyleSheet(scale_stylesheet("""
            QListWidget {
                background-color: #1A1A1A;
                border: 1px solid #3A3A3A;
                border-radius: 4px;
                font-size: 11px;
            }
            QListWidget::item {
                padding: 4px 8px;
                border-bottom: 1px solid #2A2A2A;
            }
            QListWidget::item:selected {
                background-color: #0078D4;
            }
        """, self.ui_scale))
        self.folder_list.itemDoubleClicked.connect(self._remove_folder_item)
        self.folder_list.hide()  # Hidden until folders are added
        details_layout.addWidget(self.folder_list)

        # Destination options
        dest_group = QFrame()
        dest_layout = QVBoxLayout(dest_group)
        dest_layout.setContentsMargins(0, self._px(4), 0, self._px(4))
        dest_layout.setSpacing(self._px(4))

        from PyQt6.QtWidgets import QRadioButton, QButtonGroup
        self.dest_btn_group = QButtonGroup(self)

        self.rb_dest_subfolder = QRadioButton("Subcarpeta en origen")
        self.rb_dest_subfolder.setChecked(True)
        self.rb_dest_subfolder.setToolTip("Crea una subcarpeta (ej: _SALIDA_PRO) dentro de cada carpeta de origen")
        self.dest_btn_group.addButton(self.rb_dest_subfolder)
        dest_layout.addWidget(self.rb_dest_subfolder)

        custom_row = QHBoxLayout()
        self.rb_dest_custom = QRadioButton("Carpeta personalizada:")
        self.rb_dest_custom.setToolTip("Exportar todas las imágenes a una única carpeta")
        self.rb_dest_custom.toggled.connect(self._on_dest_custom_toggled)
        self.dest_btn_group.addButton(self.rb_dest_custom)
        custom_row.addWidget(self.rb_dest_custom)

        self.btn_choose_dest = QPushButton("Elegir...")
        self.btn_choose_dest.setFixedWidth(self._px(80))
        self.btn_choose_dest.setEnabled(False)
        self.btn_choose_dest.clicked.connect(self._choose_custom_dest)
        custom_row.addWidget(self.btn_choose_dest)
        custom_row.addStretch()
        dest_layout.addLayout(custom_row)

        self.lbl_custom_dest = QLabel("")
        self.lbl_custom_dest.setStyleSheet(scale_stylesheet(
            "color: #888; font-size: 10px; margin-left: 20px;", self.ui_scale
        ))
        self.lbl_custom_dest.hide()
        dest_layout.addWidget(self.lbl_custom_dest)

        dest_group.hide()  # Hidden until folders are added
        self.dest_group = dest_group
        details_layout.addWidget(dest_group)

        details_container.hide()  # we keep it hidden; dialog will present details
        self.export_details_container = details_container
        layout.addWidget(details_container)

        # Summary label (shows when no folders or summary)
        self.lbl_folder_summary = QLabel("Ninguna carpeta seleccionada")
        self.lbl_folder_summary.setProperty("class", "subheading")
        layout.addWidget(self.lbl_folder_summary)
        
        # Process button
        self.btn_process = QPushButton(qta.icon('fa5s.play', color='white'), " PROCESAR IMÁGENES")
        self.btn_process.setProperty("class", "primary")
        self.btn_process.setEnabled(False)
        self.btn_process.setToolTip("Iniciar el procesamiento de todas las imágenes (Ctrl+Enter)")
        self.btn_process.clicked.connect(self._start_export)
        layout.addWidget(self.btn_process)
        
        # Process control buttons (hidden by default)
        self.process_controls_layout = QHBoxLayout()
        self.process_controls_layout.setSpacing(self._px(4))
        
        self.btn_pause = QPushButton(qta.icon('fa5s.pause', color='white'), " PAUSAR")
        self.btn_pause.setStyleSheet("background-color: #F57C00; color: white; font-weight: 600;")
        self.btn_pause.setToolTip("Pausar/Reanudar el procesamiento (Ctrl+Shift+P)")
        self.btn_pause.clicked.connect(self._toggle_pause)
        self.process_controls_layout.addWidget(self.btn_pause)
        
        self.btn_stop = QPushButton(qta.icon('fa5s.stop', color='white'), " DETENER")
        self.btn_stop.setStyleSheet("background-color: #C62828; color: white; font-weight: 600;")
        self.btn_stop.setToolTip("Detener el procesamiento en curso (Esc)")
        self.btn_stop.clicked.connect(self._stop_export)
        self.process_controls_layout.addWidget(self.btn_stop)
        
        # Container for controls to manage visibility easily
        self.process_controls_widget = QWidget()
        self.process_controls_widget.setLayout(self.process_controls_layout)
        self.process_controls_widget.hide()
        layout.addWidget(self.process_controls_widget)
        
        # Progress section
        self.lbl_progress_status = QLabel("")
        self.lbl_progress_status.setStyleSheet(
            scale_stylesheet("color: #888; font-size: 10px;", self.ui_scale)
        )
        self.lbl_progress_status.hide()
        layout.addWidget(self.lbl_progress_status)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(self._px(6))
        layout.addWidget(self.progress_bar)
        
        # Initialize folder list state
        self.selected_folders = []  # List of Path objects
        self.custom_output_path = None
        self.export_details_visible = False  # kept for compatibility; details shown in dialog
        
        return group
    
    def _create_preview_panel(self) -> QWidget:
        """Create the right preview panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(self._px(4))
        
        # Toolbar
        toolbar = QFrame()
        toolbar.setStyleSheet("background-color: #242424; border-bottom: 1px solid #3A3A3A;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(
            self._px(12), self._px(8), self._px(12), self._px(8)
        )
        toolbar_layout.setSpacing(self._px(8))
        
        # Mock selection buttons
        mock_label = QLabel("Vista previa:")
        mock_label.setProperty("class", "subheading")
        toolbar_layout.addWidget(mock_label)
        
        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)
        
        # Predefined mockup buttons
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
        
        # Custom image button (hidden until image is dropped)
        self.btn_custom = QPushButton(qta.icon('fa5s.image', color='#A0A0A0'), " Imagen")
        self.btn_custom.setCheckable(True)
        self.btn_custom.setToolTip("Tu imagen personalizada")
        self.btn_custom.clicked.connect(lambda: self._set_mock_color('custom_drop'))
        self.btn_custom.hide()  # Hidden by default
        self.btn_group.addButton(self.btn_custom)
        toolbar_layout.addWidget(self.btn_custom)
                
        toolbar_layout.addStretch()
        
        # Floating toolbar
        self.floating_toolbar = FloatingToolbar()
        self.floating_toolbar.gridToggled.connect(lambda v: self.canvas.setGridVisible(v))
        self.floating_toolbar.bgColorChanged.connect(
            lambda c: self.canvas.setBackgroundColor(QColor(c))
        )
        toolbar_layout.addWidget(self.floating_toolbar)
        
        layout.addWidget(toolbar)
        
        # Canvas
        self.canvas = ComparisonCanvas()
        self.canvas.imageDropped.connect(self._on_image_dropped)
        layout.addWidget(self.canvas, 1)
        
        # Help text
        help_text = QLabel("Mantén ESPACIO para ver el original | Arrastra una imagen para probarla")
        help_text.setProperty("class", "subheading")
        help_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        help_text.setStyleSheet(
            scale_stylesheet("padding: 6px; background-color: #242424;", self.ui_scale)
        )
        layout.addWidget(help_text)
        
        return panel
    
    def _create_grid_panel(self) -> QWidget:
        """Create the right panel with grid of image previews."""
        panel = QWidget()
        panel.setMinimumWidth(self._px(200))
        panel.setMaximumWidth(self._px(350))
        panel.setStyleSheet("background-color: #1A1A1A;")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header toolbar
        toolbar = QFrame()
        toolbar.setStyleSheet("background-color: #242424; border-bottom: 1px solid #3A3A3A;")
        toolbar_layout = QVBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(
            self._px(8), self._px(6), self._px(8), self._px(6)
        )
        toolbar_layout.setSpacing(self._px(4))
        
        header_label = QLabel("📋 Previews")
        header_label.setProperty("class", "subheading")
        toolbar_layout.addWidget(header_label)
        
        # Folder selector (hidden by default, shown when multiple folders)
        self.grid_folder_combo = QComboBox()
        self.grid_folder_combo.setStyleSheet("font-size: 10px;")
        self.grid_folder_combo.currentIndexChanged.connect(self._on_grid_folder_changed)
        self.grid_folder_combo.hide()  # Hidden until multiple folders added
        toolbar_layout.addWidget(self.grid_folder_combo)
        
        layout.addWidget(toolbar)
        
        # Grid preview widget
        self.grid_preview = GridPreviewWidget()
        self.grid_preview.image_selected.connect(self._on_grid_image_selected)
        self.grid_preview.folder_empty.connect(self._on_grid_folder_empty)
        layout.addWidget(self.grid_preview, 1)
        
        # Info bar at bottom
        self.grid_info_label = QLabel("Selecciona carpeta para previsualizar")
        self.grid_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.grid_info_label.setStyleSheet(
            scale_stylesheet("color: #666; padding: 6px; font-size: 10px;", self.ui_scale)
        )
        layout.addWidget(self.grid_info_label)
        
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
    
    def _on_grid_image_selected(self, path: str):
        """Load image from grid into the main canvas."""
        try:
            pil_img = Image.open(path).convert("RGBA")
            pil_img.load()
            pil_img = pil_img.copy()  # Detach from underlying file
            self.mockups['custom_drop'] = pil_img
            self.current_mock = 'custom_drop'
            
            # Clear caches to force recalculation for the new image
            self.current_base_pil = None
            self.current_orig_pixmap = None
            self._update_current_assets(pil_img)
            
            # Show and select the custom image button
            self.btn_custom.show()
            self.btn_custom.setText(f" {Path(path).stem[:15]}")
            self.btn_custom.setChecked(True)
            
            # Only update canvas, NOT the grid (to avoid reload)
            self._schedule_canvas_only_preview()
            self._show_feedback(f"Imagen cargada desde grid")
        except Exception as e:
            self._show_feedback(f"Error al cargar imagen")
            self._log_error(f"[grid-select-error] {path}: {e}")
    
    def _on_grid_folder_changed(self, index: int):
        """Handle folder selection change in grid panel."""
        if index < 0 or index >= len(self.selected_folders):
            return
        folder = self.selected_folders[index]
        self.grid_preview.set_folder(str(folder))
        settings = self._get_shadow_settings()
        self.grid_preview.set_settings(settings, self.scale_curve)
        self.grid_info_label.setText(f"📂 {folder.name}")
    
    def _update_grid_folder_combo(self):
        """Update the folder selector combo in grid panel."""
        if not hasattr(self, 'grid_folder_combo'):
            return
        
        self.grid_folder_combo.blockSignals(True)
        self.grid_folder_combo.clear()
        
        if len(self.selected_folders) <= 1:
            # Hide combo for single or no folder
            self.grid_folder_combo.hide()
        else:
            display_names = self._build_folder_display_names(self.selected_folders)
            # Show combo and populate with folder names
            for folder in self.selected_folders:
                self.grid_folder_combo.addItem(f"📁 {display_names.get(str(folder), folder.name)}")
            self.grid_folder_combo.show()
        
        self.grid_folder_combo.blockSignals(False)

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
            self.grid_preview.set_folder("")
            self.grid_info_label.setText("Selecciona carpeta para previsualizar")
            return

        if preferred_index is None:
            preferred_index = previous_index
        if preferred_index is None or preferred_index < 0:
            preferred_index = 0

        target_index = min(max(int(preferred_index), 0), len(self.selected_folders) - 1)

        if len(self.selected_folders) > 1 and hasattr(self, 'grid_folder_combo'):
            self.grid_folder_combo.blockSignals(True)
            self.grid_folder_combo.setCurrentIndex(target_index)
            self.grid_folder_combo.blockSignals(False)

        folder = self.selected_folders[target_index]
        self.grid_preview.set_folder(str(folder))
        settings = self._get_shadow_settings()
        self.grid_preview.set_settings(settings, self.scale_curve)
        self.grid_info_label.setText(f"📂 {folder.name}")
    
    def _on_grid_folder_empty(self):
        """Handle empty folder - reset canvas to show placeholder."""
        # Clear the processed image to show placeholder
        self.canvas.setProcessedImage(None)
        self.canvas.setOriginalImage(None)
        # Hide custom button if it was showing
        if self.current_mock == 'custom_drop':
            self.current_mock = 'dark'
            self.btn_custom.hide()
            self.mock_buttons['dark'].setChecked(True)
    
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
                'contact_blur': 10, 'adaptive_zoom': True
            },
            "Ropa oscura": {
                'angle': 180, 'distance': 20, 'blur': 40, 'spread': 3,
                'fusion': 5, 'opacity': 45, 'noise': 5, 'padding': 10,
                'contact_blur': 12, 'adaptive_zoom': True
            },
        }
    
    def _load_app_settings(self) -> dict:
        defaults = {
            'output_folder_name': '_SALIDA_PRO',
            'suffix': '_PRO',
            'format': 'JPG',
            'transparent_bg': False,
            'bg_color': (230, 230, 230),
            'last_input_folder': '',
            'scale_curve': {
                'xp': [0.0, 0.35, 0.60, 0.85, 1.10, 1.40, 3.0],
                'fp': [0.80, 0.80, 0.90, 1.00, 0.95, 0.90, 0.90]
            },
            'section_visibility': {
                'presets': True,
                'lighting': True,
                'shadows': True,
                'finishing': False,
                'export': True,
            },
        }
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    loaded = json.load(f)
                    if 'bg_color' in loaded and isinstance(loaded['bg_color'], list):
                        loaded['bg_color'] = tuple(loaded['bg_color'])
                    return {**defaults, **loaded}
            except:
                return defaults
        return defaults
    
    def _save_app_settings(self):
        self.app_settings['scale_curve'] = self.scale_curve.model_dump()
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.app_settings, f, indent=4)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            
    def _save_presets_to_disk(self):
        # Keep legacy file for backward compatibility.
        ConfigManager.save_presets(self.presets)

        # Keep categorized presets in sync so CLI and GUI see the same data.
        categorized = ConfigManager.load_categorized_presets()
        category_names = set()
        for category in categorized.categories.values():
            for preset_name in list(category.presets.keys()):
                category_names.add(preset_name)
                if preset_name in self.presets:
                    category.presets[preset_name] = self.presets[preset_name]
                else:
                    del category.presets[preset_name]

        categorized.uncategorized = {
            name: settings
            for name, settings in self.presets.items()
            if name not in category_names
        }
        ConfigManager.save_categorized_presets(categorized)
        
    def _get_shadow_settings(self) -> ShadowSettings:
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
            adaptive_zoom=self.chk_adaptive.isChecked()
        )
    
    # ========== EVENT HANDLERS ==========
    
    def _schedule_preview(self, *args):
        """Schedule debounced preview update."""
        self._preview_pending = True
        self.preview_timer.start(200)
        # Also update grid preview with current settings
        if hasattr(self, 'grid_preview'):
            settings = self._get_shadow_settings()
            self.grid_preview.set_settings(settings, self.scale_curve)
    
    def _schedule_canvas_only_preview(self, *args):
        """Schedule preview update for canvas only (not grid)."""
        self._preview_pending = True
        self.preview_timer.start(200)
    
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
            # Passing the PIL image directly; ShadowEngine will handle copying/scaling.
            worker = PreviewWorker(
                self.current_base_pil,
                self.preview_size,
                self._get_shadow_settings().model_dump(),
                self.scale_curve.model_dump(),
                self.preview_scale_ratio,
                quality_level=1
            )
            self._active_preview_workers.add(worker)
            worker.signals.finished.connect(
                lambda qim, quality, w=worker: self._on_preview_worker_finished(w, qim, quality)
            )
            worker.signals.error.connect(
                lambda message, w=worker: self._on_preview_worker_error(w, message)
            )
            self.preview_pool.start(worker)

        except Exception as e:
            self._log_error(f"[preview-start-error] {e}")
            traceback.print_exc()

    def _on_preview_worker_finished(self, worker: PreviewWorker, qim: QImage, quality: int = 1):
        self._release_preview_worker(worker)
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
        # Clear cache to force re-generation for the mockup
        self.current_base_pil = None
        self.current_orig_pixmap = None
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
            self.btn_custom.setText(f" {os.path.basename(path)[:15]}")
            self.btn_custom.setChecked(True)
            
            self.current_mock = 'custom_drop'
            
            # Update assets and schedule
            self.current_base_pil = None
            self.current_orig_pixmap = None
            self._update_current_assets(pil_img)
            
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
        self.chk_adaptive.setChecked(True)
        
        # Reset scale curve to new optimal defaults
        self.scale_curve = CurveData(
            xp=[0.0, 0.35, 0.60, 0.85, 1.10, 1.40, 3.0],
            fp=[0.80, 0.80, 0.90, 1.00, 0.95, 0.90, 0.90]
        )
        self._save_app_settings()
        
        self._schedule_preview()
        self._show_feedback("Valores restaurados")
    
    def _show_shortcuts_dialog(self):
        """Show keyboard shortcuts in a styled dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Atajos de teclado")
        dialog.setFixedSize(self._px(380), self._px(500))
        dialog.setStyleSheet(scale_stylesheet("""
            QDialog { background-color: #1E1E1E; }
            QLabel { color: #E8E8E8; font-size: 12px; }
        """, self.ui_scale))
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(self._px(12))
        layout.setContentsMargins(
            self._px(20), self._px(20), self._px(20), self._px(20)
        )
        
        # Title with icon
        title_row = QHBoxLayout()
        title_icon = QLabel()
        title_icon.setPixmap(
            qta.icon('fa5s.keyboard', color='#0078D4').pixmap(self._px(24), self._px(24))
        )
        title_row.addWidget(title_icon)
        title = QLabel("Atajos de teclado")
        title.setStyleSheet(
            scale_stylesheet("font-size: 16px; font-weight: bold; color: #0078D4;", self.ui_scale)
        )
        title_row.addWidget(title)
        title_row.addStretch()
        layout.addLayout(title_row)
        
        # Shortcut groups with icons
        groups = [
            (qta.icon('fa5s.save', color='#61AFEF'), "Presets", [
                ("Ctrl+S", "Guardar preset"),
                ("Ctrl+R", "Restaurar valores"),
            ]),
            (qta.icon('fa5s.eye', color='#61AFEF'), "Vista previa", [
                ("1  2  3", "Cambiar mockup"),
                ("Espacio", "Ver original"),
                ("Scroll", "Zoom"),
            ]),
            (qta.icon('fa5s.cogs', color='#61AFEF'), "Exportación", [
                ("Ctrl+Enter", "Procesar imágenes"),
                ("Ctrl+Shift+P", "Pausar/Reanudar"),
                ("Esc", "Detener procesamiento"),
            ]),
            (qta.icon('fa5s.cog', color='#61AFEF'), "General", [
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
            header.setStyleSheet(
                scale_stylesheet("font-weight: 600; color: #888; font-size: 11px;", self.ui_scale)
            )
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
                key_lbl.setStyleSheet(scale_stylesheet("""
                    background: #2A2A2A; 
                    padding: 4px 8px; 
                    border-radius: 4px;
                    border: 1px solid #3A3A3A;
                    font-family: 'Segoe UI', sans-serif;
                    font-size: 11px;
                    font-weight: bold;
                    color: #61AFEF;
                """, self.ui_scale))
                
                desc_lbl = QLabel(desc)
                desc_lbl.setStyleSheet(
                    scale_stylesheet("color: #AAA; font-size: 12px;", self.ui_scale)
                )
                
                row.addWidget(key_lbl)
                row.addWidget(desc_lbl, 1)
                layout.addLayout(row)

        note = QLabel("Tip: doble clic sobre un slider o su valor para volver al valor por defecto.")
        note.setStyleSheet(scale_stylesheet("color: #7EA9D6; font-size: 11px;", self.ui_scale))
        note.setWordWrap(True)
        layout.addWidget(note)
        
        layout.addStretch()
        
        # Close button
        btn_close = QPushButton("Cerrar")
        btn_close.setFixedWidth(self._px(100))
        btn_close.setStyleSheet(scale_stylesheet("""
            QPushButton {
                background: #0078D4;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: 600;
                font-size: 12px;
            }
            QPushButton:hover { background: #1084D8; }
        """, self.ui_scale))
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
            d = self.presets[name]
            self.light_angle.setAngle(d.get('angle', 180))
            self.sl_distance.setValue(d.get('distance', 30))
            self.sl_blur.setValue(d.get('blur', 25))
            self.sl_spread.setValue(d.get('spread', 0))
            self.sl_fusion.setValue(d.get('fusion', 2))
            self.sl_opacity.setValue(d.get('opacity', 30))
            self.sl_noise.setValue(d.get('noise', 0))
            self.sl_padding.setValue(d.get('padding', 10))
            self.sl_contact_blur.setValue(d.get('contact_blur', 10))
            self.sl_contraction.setValue(d.get('contraction', 0))
            self.chk_adaptive.setChecked(d.get('adaptive_zoom', True))
            self._schedule_preview()
            
    def _action_save_current(self):
        current_name = self.combo_presets.currentText()
        if current_name:
            self.presets[current_name] = self._get_shadow_settings().model_dump()
            self._save_presets_to_disk()
            self._show_feedback("Preset guardado")
            
    def _action_create_new(self):
        name, ok = QInputDialog.getText(self, "Nuevo Preset", "Nombre del preset:")
        name = name.strip() if ok and name else ""
        if ok and name:
            if name in self.presets:
                self._show_feedback("Ese preset ya existe")
                return
            self.presets[name] = self._get_shadow_settings().model_dump()
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
            self.presets[new_name] = self.presets.pop(old_name)
            self._save_presets_to_disk()
            self.combo_presets.setItemText(self.combo_presets.currentIndex(), new_name)
            self._show_feedback("Preset renombrado")
            
    def _action_delete(self):
        name = self.combo_presets.currentText()
        if QMessageBox.question(self, "Eliminar Preset", 
                               f"¿Eliminar '{name}'?") == QMessageBox.StandardButton.Yes:
            del self.presets[name]
            self._save_presets_to_disk()
            self.combo_presets.removeItem(self.combo_presets.currentIndex())
            self._show_feedback("Preset eliminado")
            
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
        total_images = 0
        
        for folder in self.selected_folders:
            img_count = len(list(folder.glob("*.png")))
            total_images += img_count
            item = QListWidgetItem(f"📁 {folder.name}  —  {img_count} imágenes")
            item.setToolTip(str(folder))
            self.folder_list.addItem(item)
        
        has_folders = len(self.selected_folders) > 0
        
        # Show/hide elements in panel (details live in a dialog; keep hidden to avoid resizing)
        self.folder_list.setVisible(False)
        self.dest_group.setVisible(False)
        self.btn_clear_folders.setEnabled(has_folders)
        self.btn_process.setEnabled(has_folders and total_images > 0)
        self.export_details_container.setVisible(False)
        self.btn_export_details.setEnabled(has_folders)
        
        # Update summary label
        if not has_folders:
            self.lbl_folder_summary.setText("Ninguna carpeta seleccionada")
            self.lbl_folder_summary.show()
        elif len(self.selected_folders) == 1:
            self.lbl_folder_summary.setText(f"📊 {total_images} imágenes")
            self.lbl_folder_summary.show()
        else:
            self.lbl_folder_summary.setText(f"📊 {len(self.selected_folders)} carpetas • {total_images} imágenes")
            self.lbl_folder_summary.show()
        
        # Update process button text
        if total_images > 0:
            self.btn_process.setText(f" PROCESAR {total_images} IMÁGENES")
        else:
            self.btn_process.setText(" PROCESAR IMÁGENES")
        # Keep details button text/icon unchanged
        
        self._sync_grid_preview_with_folders()
    
    def _on_dest_custom_toggled(self, checked: bool):
        """Handle custom destination radio button toggle."""
        self.btn_choose_dest.setEnabled(checked)
        if not checked:
            self.lbl_custom_dest.hide()
    
    def _choose_custom_dest(self):
        """Choose a custom output destination folder."""
        folder = QFileDialog.getExistingDirectory(self, "Elegir carpeta de destino")
        if folder:
            self.custom_output_path = Path(folder)
            self.lbl_custom_dest.setText(f"→ {folder}")
            self.lbl_custom_dest.show()

    def _open_export_details_dialog(self):
        """Show export details in a compact dialog to avoid resizing the left panel."""
        from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QAbstractItemView, QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle("Detalles de exportación")
        dialog.setMinimumWidth(self._px(360))
        dialog.setStyleSheet(scale_stylesheet("""
            QDialog { background-color: #1E1E1E; }
        """, self.ui_scale))

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(self._px(16), self._px(12), self._px(16), self._px(12))
        layout.setSpacing(self._px(10))

        summary = QLabel(self.lbl_folder_summary.text())
        summary.setProperty("class", "subheading")
        layout.addWidget(summary)

        list_widget = QListWidget()
        list_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        list_widget.setMaximumHeight(self._px(200))
        list_widget.setStyleSheet(scale_stylesheet("""
            QListWidget {
                background-color: #1A1A1A;
                border: 1px solid #3A3A3A;
                border-radius: 4px;
                font-size: 11px;
            }
            QListWidget::item {
                border-bottom: 1px solid #2A2A2A;
                margin: 0;
            }
            QListWidget::item:selected {
                background-color: #222;
            }
        """, self.ui_scale))
        layout.addWidget(list_widget)
        display_names = self._build_folder_display_names(self.selected_folders)

        def _add_folder_item(folder):
            img_count = len(list(folder.glob("*.png")))
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(self._px(8), self._px(4), self._px(8), self._px(4))
            row_layout.setSpacing(self._px(6))

            lbl = QLabel(f"📁 {display_names.get(str(folder), folder.name)}")
            lbl.setToolTip(str(folder))
            count_lbl = QLabel(f"{img_count} imágenes")
            count_lbl.setStyleSheet(scale_stylesheet("color: #888; font-size: 10px;", self.ui_scale))
            count_lbl.setToolTip(str(folder))

            btn_remove = QPushButton(qta.icon('fa5s.trash-alt', color='#E57373'), "")
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
        lbl_custom.setStyleSheet(scale_stylesheet(
            "color: #888; font-size: 10px; margin-left: 20px;", self.ui_scale
        ))
        lbl_custom.setVisible(bool(self.lbl_custom_dest.text()))
        dest_layout.addWidget(lbl_custom)

        layout.addWidget(dest_box)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
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
        
        self.btn_process.hide()
        self.btn_add_folder.setEnabled(False)
        self.btn_clear_folders.setEnabled(False)
        self.process_controls_widget.show()
        self.lbl_progress_status.show()
        
        # Reset pause button state
        self.btn_pause.setText(" PAUSAR")
        self.btn_pause.setIcon(qta.icon('fa5s.pause', color='white'))
        self.btn_pause.setStyleSheet("background-color: #F57C00; color: white; font-weight: 600;")
        
        # Only show pause button for queue (multiple folders)
        if len(self.selected_folders) > 1:
            self.btn_pause.show()
        else:
            self.btn_pause.hide()
        
        # Build export config
        use_custom_dest = self.rb_dest_custom.isChecked()
        custom_output = str(self.custom_output_path) if self.custom_output_path else None
        if use_custom_dest and not custom_output:
            QMessageBox.warning(
                self,
                "Destino no configurado",
                "Has seleccionado destino personalizado, pero no hay carpeta elegida.\n"
                "Selecciona una carpeta de destino o cambia a subcarpeta en origen."
            )
            self._reset_export_ui()
            return

        export_config = ExportConfig(
            output_folder_name=self.app_settings.get('output_folder_name', '_SALIDA_PRO'),
            suffix=self.app_settings.get('suffix', '_PRO'),
            format=self.app_settings.get('format', 'JPG'),
            transparent_bg=self.app_settings.get('transparent_bg', False),
            bg_color=self.app_settings.get('bg_color', (230, 230, 230)),
            output_width=self.app_settings.get('output_width', 1800),
            output_height=self.app_settings.get('output_height', 2400),
            naming_template=self.app_settings.get('naming_template', '{original}{suffix}'),
            output_destination='custom' if use_custom_dest else 'subfolder',
            custom_output_path=custom_output
        )

        if export_config.output_destination == 'custom':
            self._last_export_destinations = [str(Path(export_config.custom_output_path))]
        else:
            self._last_export_destinations = [
                str(Path(folder) / export_config.output_folder_name)
                for folder in self.selected_folders
            ]
        
        # Single folder - use simple ExportWorker
        if len(self.selected_folders) == 1:
            self.worker = ExportWorker(
                str(self.selected_folders[0]),
                self._get_shadow_settings(),
                export_config,
                self.scale_curve
            )
            self.worker.progress_updated.connect(self.progress_bar.setValue)
            self.worker.log_updated.connect(self._log_error)
            self.worker.finished_process.connect(self._on_export_finished)
            self.worker.finished.connect(self._on_single_worker_thread_finished)
            self.lbl_progress_status.setText(f"Procesando: {self.selected_folders[0].name}")
            self.worker.start()
        else:
            # Multiple folders - use QueueWorker
            jobs = [JobItem(folder_path=str(f)) for f in self.selected_folders]
            preset_name = self.combo_presets.currentText()
            
            self.queue_worker = QueueWorker(
                jobs,
                self._get_shadow_settings(),
                export_config,
                self.scale_curve,
                preset_name
            )
            
            self.queue_worker.job_started.connect(self._on_queue_job_started)
            self.queue_worker.job_progress.connect(self._on_queue_job_progress)
            self.queue_worker.queue_finished.connect(self._on_queue_finished)
            self.queue_worker.finished.connect(self._on_queue_worker_thread_finished)
            self.queue_worker.start()
    
    def _on_queue_job_started(self, index: int, folder_path: str):
        """Called when a job in the queue starts."""
        folder_name = Path(folder_path).name
        self.lbl_progress_status.setText(f"[{index+1}/{len(self.selected_folders)}] {folder_name}")
    
    def _on_queue_job_progress(self, index: int, progress: int):
        """Called when a job's progress updates."""
        # Calculate overall progress across all jobs
        base_progress = (index * 100) // len(self.selected_folders)
        job_contribution = progress // len(self.selected_folders)
        self.progress_bar.setValue(base_progress + job_contribution)
    
    def _on_queue_finished(self, completed: int, errors: int, total_images: int):
        """Called when all queue jobs are finished."""
        self._reset_export_ui()

        if errors == 0:
            self._show_export_result_dialog(
                title="Cola completada",
                success=True,
                summary_lines=[
                    f"✓ {completed} carpetas procesadas",
                    f"{total_images} imágenes exportadas",
                ],
                destinations=self._last_export_destinations,
            )
        else:
            self._show_export_result_dialog(
                title="Cola completada con errores",
                success=False,
                summary_lines=[
                    f"✓ {completed} carpetas completadas",
                    f"✗ {errors} carpetas con errores",
                ],
                destinations=self._last_export_destinations,
            )
        
    def _toggle_pause(self):
        """Toggle pause/resume state of the export queue."""
        if not hasattr(self, 'queue_worker') or not self.queue_worker or not self.queue_worker.isRunning():
            return
            
        if self.queue_worker.is_paused:
            self.queue_worker.resume()
            self.btn_pause.setText(" PAUSAR")
            self.btn_pause.setIcon(qta.icon('fa5s.pause', color='white'))
            self.btn_pause.setStyleSheet("background-color: #F57C00; color: white; font-weight: 600;")
            self.lbl_progress_status.setText("Procesando...")
        else:
            self.queue_worker.pause()
            self.btn_pause.setText(" REANUDAR")
            self.btn_pause.setIcon(qta.icon('fa5s.play', color='white'))
            self.btn_pause.setStyleSheet("background-color: #43A047; color: white; font-weight: 600;")
            self.lbl_progress_status.setText("⏸️ Pausado (terminando imagen actual...)")

    def _stop_export(self):
        """Stop current export or queue."""
        if hasattr(self, 'queue_worker') and self.queue_worker and self.queue_worker.isRunning():
            self.queue_worker.stop()
        elif hasattr(self, 'worker') and self.worker:
            self.worker.stop()
        
        self.btn_stop.setText(" Deteniendo...")
        self.btn_stop.setEnabled(False)
    
    def _reset_export_ui(self):
        """Reset export UI to idle state."""
        self.process_controls_widget.hide()
        self.btn_stop.setText(" DETENER")
        self.btn_stop.setEnabled(True)
        self.btn_process.show()
        self.btn_add_folder.setEnabled(True)
        self.btn_clear_folders.setEnabled(True)
        self.progress_bar.setValue(0)
        self.lbl_progress_status.hide()
            
    def _on_export_finished(self, success: bool, processed: int = 0, total: int = 0, duration: float = 0.0):
        """Called when single-folder export finishes."""
        self._reset_export_ui()

        if success:
            self._show_export_result_dialog(
                title="Proceso completado",
                success=True,
                summary_lines=[
                    "Proceso completado con éxito",
                    f"{processed}/{total} imágenes en {duration:.1f}s",
                ],
                destinations=self._last_export_destinations,
            )
        else:
            self._show_export_result_dialog(
                title="Proceso incompleto",
                success=False,
                summary_lines=[
                    "Se detuvo o falló el proceso",
                    f"{processed}/{total} imágenes en {duration:.1f}s",
                ],
                destinations=self._last_export_destinations,
            )

    def _on_single_worker_thread_finished(self):
        """Release single-folder worker only after QThread has fully stopped."""
        self.worker = None

    def _on_queue_worker_thread_finished(self):
        """Release queue worker only after QThread has fully stopped."""
        self.queue_worker = None
            
    # ========== DIALOGS ==========
    
    def _open_export_config(self):
        current_config = ExportConfig(
            output_folder_name=self.app_settings.get('output_folder_name', '_SALIDA_PRO'),
            suffix=self.app_settings.get('suffix', '_PRO'),
            format=self.app_settings.get('format', 'JPG'),
            transparent_bg=self.app_settings.get('transparent_bg', False),
            bg_color=self.app_settings.get('bg_color', (230, 230, 230)),
            output_width=self.app_settings.get('output_width', 1800),
            output_height=self.app_settings.get('output_height', 2400),
            naming_template=self.app_settings.get('naming_template', '{original}{suffix}')
        )
        
        dlg = ExportConfigDialog(current_config, self)
        if dlg.exec():
            new_settings = dlg.get_settings()
            self.app_settings.update(new_settings.model_dump())
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
        ]
        for control in sliders:
            control.slider.sliderReleased.connect(self._schedule_history_push)
            control.spinbox.editingFinished.connect(self._schedule_history_push)

        self.light_angle.angleChanged.connect(self._schedule_history_push)
        self.angle_spinbox.editingFinished.connect(self._schedule_history_push)
        self.chk_adaptive.toggled.connect(self._schedule_history_push)
    
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
        # Block signals to avoid triggering preview multiple times
        self.light_angle.blockSignals(True)
        self.sl_distance.slider.blockSignals(True)
        self.sl_blur.slider.blockSignals(True)
        self.sl_spread.slider.blockSignals(True)
        self.sl_fusion.slider.blockSignals(True)
        self.sl_opacity.slider.blockSignals(True)
        self.sl_noise.slider.blockSignals(True)
        self.sl_padding.slider.blockSignals(True)
        self.sl_contact_blur.slider.blockSignals(True)
        self.sl_contraction.slider.blockSignals(True)
        self.chk_adaptive.blockSignals(True)
        
        self.light_angle.setAngle(settings.angle)
        self.angle_spinbox.setValue(settings.angle)
        self.sl_distance.setValue(settings.distance)
        self.sl_blur.setValue(settings.blur)
        self.sl_spread.setValue(settings.spread)
        self.sl_fusion.setValue(settings.fusion)
        self.sl_opacity.setValue(settings.opacity)
        self.sl_noise.setValue(settings.noise)
        self.sl_padding.setValue(settings.padding)
        self.sl_contact_blur.setValue(settings.contact_blur)
        self.sl_contraction.setValue(settings.contraction)
        self.chk_adaptive.setChecked(settings.adaptive_zoom)
        
        # Restore signals
        self.light_angle.blockSignals(False)
        self.sl_distance.slider.blockSignals(False)
        self.sl_blur.slider.blockSignals(False)
        self.sl_spread.slider.blockSignals(False)
        self.sl_fusion.slider.blockSignals(False)
        self.sl_opacity.slider.blockSignals(False)
        self.sl_noise.slider.blockSignals(False)
        self.sl_padding.slider.blockSignals(False)
        self.sl_contact_blur.slider.blockSignals(False)
        self.sl_contraction.slider.blockSignals(False)
        self.chk_adaptive.blockSignals(False)
        
        self._schedule_preview()
    
    # ========== LOG VIEWER ==========
    
    def _show_log_viewer(self):
        """Show dialog with today's activity log."""
        log_path = self.log_manager.get_today_log_path()
        entries = self.log_manager.get_recent_entries(100)
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Registro de actividad")
        dialog.setMinimumSize(self._px(700), self._px(500))
        dialog.setStyleSheet("QDialog { background-color: #1E1E1E; }")
        
        layout = QVBoxLayout(dialog)
        
        # Header
        header = QLabel(f"📋 Log: {log_path.name}")
        header.setStyleSheet("font-weight: bold; font-size: 14px; color: #0078D4; padding: 8px;")
        layout.addWidget(header)
        
        # Log content
        from PyQt6.QtWidgets import QTextEdit
        log_text = QTextEdit()
        log_text.setReadOnly(True)
        log_text.setStyleSheet("""
            QTextEdit {
                background-color: #21252B;
                color: #ABB2BF;
                font-family: 'Consolas', monospace;
                font-size: 11px;
                border: 1px solid #3A3A3A;
                border-radius: 4px;
            }
        """)
        
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
        btn_open_folder.clicked.connect(lambda: self._open_folder_in_explorer(log_path.parent))
        btn_layout.addWidget(btn_open_folder)
        
        btn_layout.addStretch()
        
        btn_close = QPushButton("Cerrar")
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
        dialog.setStyleSheet("QDialog { background-color: #1E1E1E; }")

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(self._px(16), self._px(14), self._px(16), self._px(14))
        layout.setSpacing(self._px(10))

        icon_name = 'fa5s.check-circle' if success else 'fa5s.exclamation-triangle'
        icon_color = '#4CAF50' if success else '#F44336'
        header_row = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon(icon_name, color=icon_color).pixmap(self._px(22), self._px(22)))
        header_row.addWidget(icon_label)

        header_title = QLabel(title)
        header_title.setStyleSheet(scale_stylesheet("font-size: 16px; font-weight: 700; color: #E8E8E8;", self.ui_scale))
        header_row.addWidget(header_title, 1)
        layout.addLayout(header_row)

        for line in summary_lines:
            summary_label = QLabel(line)
            summary_label.setStyleSheet(scale_stylesheet("color: #AAB2BF; font-size: 12px;", self.ui_scale))
            layout.addWidget(summary_label)

        layout.addWidget(QLabel("Destino(s) de exportación:"))
        dest_list = QListWidget()
        dest_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        dest_list.setStyleSheet(scale_stylesheet("""
            QListWidget {
                background-color: #181A1F;
                border: 1px solid #3A3A3A;
                border-radius: 6px;
                font-size: 11px;
            }
            QListWidget::item {
                padding: 6px;
                border-bottom: 1px solid #2A2A2A;
            }
            QListWidget::item:selected {
                background-color: #2A3A4A;
            }
        """, self.ui_scale))

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
        hint_lbl.setStyleSheet(scale_stylesheet("color: #777; font-size: 10px;", self.ui_scale))
        layout.addWidget(hint_lbl)

        btn_row = QHBoxLayout()
        btn_open_selected = QPushButton("Abrir carpeta")
        btn_open_selected.setEnabled(bool(valid_destinations))
        btn_row.addWidget(btn_open_selected)

        btn_row.addStretch()
        btn_close = QPushButton("Cerrar")
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
            
    def closeEvent(self, event):
        """Save session state before closing and stop background preview tasks."""
        try:
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

            session_data = {
                'geometry': self.saveGeometry().toBase64().data().decode(),
                'state': self.saveState().toBase64().data().decode(),
                'selected_folders': [str(f) for f in self.selected_folders],
                'current_preset': self.combo_presets.currentText(),
                'current_mock': self.current_mock,
                'splitter_sizes': self.splitter.sizes(),
                'export_config': {
                    'output_folder_name': self.app_settings.get('output_folder_name'),
                    'suffix': self.app_settings.get('suffix'),
                    'format': self.app_settings.get('format'),
                    'output_destination': output_destination,
                    'custom_output_path': str(self.custom_output_path) if self.custom_output_path else None
                }
            }
            
            # Save current shadow settings
            current_settings = self._get_shadow_settings()
            session_data['shadow_settings'] = current_settings.model_dump()
            
            self.session_manager.save_session(session_data)
            
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
                if 'output_destination' in exp:
                    is_custom = exp['output_destination'] == 'custom'
                    if hasattr(self, 'rb_dest_custom'):
                        self.rb_dest_custom.setChecked(is_custom)
                        self.rb_dest_subfolder.setChecked(not is_custom)
                if 'custom_output_path' in exp and exp['custom_output_path']:
                    self.custom_output_path = Path(exp['custom_output_path'])
                    if hasattr(self, 'lbl_custom_dest'):
                        self.lbl_custom_dest.setText(str(self.custom_output_path))
            
            if 'shadow_settings' in data:
                self._apply_settings(ShadowSettings(**data['shadow_settings']))
            else:
                self._schedule_preview()
            return True
                        
        except Exception as e:
            self._log_error(f"Error restoring session: {e}")
        return False

