"""
Modern Dark Theme Stylesheet for PyQt6
Inspired by DaVinci Resolve, Figma, and VS Code
"""
import re

# Color Palette
COLORS = {
    'bg_primary': '#18191B',
    'bg_secondary': '#202225',
    'bg_tertiary': '#2A2D31',
    'bg_raised': '#2F3237',
    'bg_hover': '#32363C',
    'bg_active': '#3A3F46',
    
    'accent_primary': '#0A84FF',
    'accent_hover': '#3399FF',
    'accent_pressed': '#0070E0',
    'accent_focus_ring': 'rgba(10, 132, 255, 0.35)',
    
    'text_primary': '#F2F2F7',
    'text_secondary': '#C7CBD4',
    'text_muted': '#9AA0A8',
    'text_disabled': '#6C7078',
    
    'border': '#2E3136',
    'border_focus': '#0A84FF',
    'divider': '#2B2E33',
    
    'success': '#34C759',
    'warning': '#FF9F0A',
    'error': '#FF453A',
    
    'shadow': 'rgba(0, 0, 0, 0.35)',
}

MODERN_DARK_STYLESHEET = f"""
/* ===== GLOBAL RESET ===== */
* {{
    font-family: 'Segoe UI', 'Inter', 'Roboto', sans-serif;
    font-size: 13px;
    color: {COLORS['text_primary']};
}}

QMainWindow, QWidget {{
    background-color: {COLORS['bg_primary']};
}}

/* ===== SCROLL BARS ===== */
QScrollBar:vertical {{
    background: {COLORS['bg_secondary']};
    width: 9px;
    margin: 0;
    border-radius: 5px;
}}
QScrollBar::handle:vertical {{
    background: {COLORS['bg_tertiary']};
    min-height: 28px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical:hover {{
    background: {COLORS['bg_hover']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: {COLORS['bg_secondary']};
    height: 9px;
    margin: 0;
    border-radius: 5px;
}}
QScrollBar::handle:horizontal {{
    background: {COLORS['bg_tertiary']};
    min-width: 28px;
    border-radius: 5px;
}}

QScrollArea[class="panel-scroll"] {{
    border: none;
    background-color: {COLORS['bg_primary']};
}}
QScrollArea[class="preview-scroll"] {{
    border: none;
    background-color: {COLORS['bg_primary']};
}}

/* ===== GROUP BOXES ===== */
QGroupBox {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 10px;
    margin-top: 12px;
    padding: 16px 10px 12px 10px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    top: 4px;
    padding: 0 8px;
    color: {COLORS['text_secondary']};
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
}}

/* ===== COLLAPSIBLE SECTIONS ===== */
QFrame[class="section"] {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 10px;
}}
QFrame[class="section-header"] {{
    background-color: {COLORS['bg_secondary']};
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
}}
QWidget[class="section-content"] {{
    background-color: {COLORS['bg_secondary']};
    border-bottom-left-radius: 10px;
    border-bottom-right-radius: 10px;
}}
QWidget[class="sidebar"] {{
    background-color: {COLORS['bg_primary']};
    border-right: 1px solid {COLORS['divider']};
}}
QWidget[class="panel"] {{
    background-color: {COLORS['bg_primary']};
}}
QFrame[class="panel-header"] {{
    background-color: {COLORS['bg_secondary']};
    border-bottom: 1px solid {COLORS['divider']};
}}
QDialog[class="dialog"] {{
    background-color: {COLORS['bg_primary']};
}}
QFrame[class="dialog-card"] {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 10px;
}}
QFrame[class="image-swatch"] {{
    background-color: {COLORS['bg_tertiary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
}}
QToolButton {{
    color: {COLORS['text_secondary']};
    font-weight: 600;
}}
QToolButton[class="section-toggle"] {{
    background: transparent;
    border: none;
    padding: 2px 4px;
    text-align: left;
    min-height: 18px;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    font-size: 11px;
}}
QToolButton[class="section-toggle"]:hover {{
    background-color: {COLORS['bg_hover']};
}}
QToolButton[class="section-toggle"]:pressed {{
    background-color: {COLORS['bg_active']};
}}
QToolButton[class="section-arrow"] {{
    background: transparent;
    border: none;
    padding: 0;
}}
QToolButton::menu-indicator {{
    image: none;
}}

/* ===== LABELS ===== */
QLabel {{
    color: {COLORS['text_primary']};
    background: transparent;
}}
QLabel[class="heading"] {{
    font-size: 18px;
    font-weight: 700;
    color: {COLORS['text_primary']};
    letter-spacing: 0.5px;
    padding-top: 2px;
    padding-bottom: 4px;
}}
QLabel[class="app-title"] {{
    font-size: 18px;
    font-weight: 700;
    color: {COLORS['text_primary']};
    letter-spacing: 0.4px;
    padding: 4px 2px 8px 2px;
}}
QLabel[class="subheading"] {{
    font-size: 12px;
    color: {COLORS['text_secondary']};
}}
QLabel[class="muted"] {{
    font-size: 11px;
    color: {COLORS['text_muted']};
}}
QLabel[class="info-label"] {{
    font-size: 11px;
    color: {COLORS['text_muted']};
    padding: 8px;
}}
QLabel[class="section-title"] {{
    font-size: 11px;
    font-weight: 600;
    color: {COLORS['text_secondary']};
    text-transform: uppercase;
    letter-spacing: 0.6px;
}}
QLabel[class="panel-title"] {{
    font-size: 12px;
    font-weight: 600;
    color: {COLORS['text_secondary']};
    text-transform: uppercase;
    letter-spacing: 1px;
}}
QLabel[class="panel-label"] {{
    font-size: 12px;
    color: {COLORS['text_secondary']};
}}
QLabel[class="panel-path"] {{
    font-size: 12px;
    color: {COLORS['text_muted']};
}}
QLabel[class="help-text"] {{
    font-size: 12px;
    color: {COLORS['text_muted']};
    background-color: {COLORS['bg_secondary']};
    border-top: 1px solid {COLORS['divider']};
    padding: 10px;
}}
QLabel[class="preview-label"] {{
    font-size: 13px;
    color: {COLORS['text_secondary']};
    font-weight: 600;
}}
QLabel[class="dialog-title"] {{
    font-size: 16px;
    font-weight: 700;
    color: {COLORS['text_primary']};
}}
QLabel[class="dialog-section"] {{
    font-size: 11px;
    font-weight: 600;
    color: {COLORS['text_secondary']};
    text-transform: uppercase;
    letter-spacing: 0.6px;
}}
QLabel[class="dialog-text"] {{
    font-size: 12px;
    color: {COLORS['text_secondary']};
}}
QLabel[class="note"] {{
    font-size: 11px;
    color: {COLORS['accent_primary']};
}}
QLabel[class="accent-text"] {{
    font-size: 11px;
    color: {COLORS['accent_primary']};
}}
QLabel[class="success-text"] {{
    font-size: 11px;
    color: {COLORS['success']};
}}
QLabel[class="keycap"] {{
    background-color: {COLORS['bg_raised']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 11px;
    font-weight: 600;
    color: {COLORS['accent_primary']};
}}

QLabel[class="param-label"] {{
    font-size: 12px;
    color: {COLORS['text_secondary']};
}}

/* ===== BUTTONS ===== */
QPushButton {{
    background-color: {COLORS['bg_tertiary']};
    border: 1px solid {COLORS['border']};
    border-radius: 7px;
    padding: 9px 16px;
    font-weight: 500;
    min-height: 28px;
}}
QPushButton:hover {{
    background-color: {COLORS['bg_hover']};
    border-color: {COLORS['border_focus']};
}}
QPushButton:pressed {{
    background-color: {COLORS['bg_active']};
}}
QPushButton:disabled {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_disabled']};
}}
QPushButton[class="primary"] {{
    background-color: {COLORS['accent_primary']};
    border: none;
    color: white;
    font-weight: 600;
    padding: 12px 20px;
    font-size: 14px;
}}
QPushButton[class="primary"]:hover {{
    background-color: {COLORS['accent_hover']};
}}
QPushButton[class="primary"]:pressed {{
    background-color: {COLORS['accent_pressed']};
}}
QPushButton[class="secondary"] {{
    background-color: {COLORS['bg_raised']};
    border: 1px solid {COLORS['border']};
    color: {COLORS['text_primary']};
    font-weight: 600;
}}
QPushButton[class="secondary"]:hover {{
    background-color: {COLORS['bg_hover']};
}}
QPushButton[class="icon-btn"] {{
    background: transparent;
    border: none;
    padding: 5px;
    border-radius: 6px;
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
    max-height: 28px;
}}
QPushButton[class="icon-btn"]:hover {{
    background-color: {COLORS['bg_hover']};
}}
QPushButton[class="icon-btn"]:checked {{
    background-color: {COLORS['accent_primary']};
    color: white;
}}
QPushButton[class="danger"] {{
    color: {COLORS['error']};
}}
QPushButton[class="danger"]:hover {{
    background-color: rgba(244, 67, 54, 0.15);
}}
QPushButton[class="ghost"] {{
    background: transparent;
    border: 1px solid {COLORS['border']};
    color: {COLORS['text_secondary']};
}}
QPushButton[class="ghost"]:hover {{
    background-color: {COLORS['bg_hover']};
}}
QPushButton[class="swatch"] {{
    background-color: {COLORS['bg_tertiary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
}}
QPushButton[class="warning-solid"] {{
    background-color: {COLORS['warning']};
    border: none;
    color: #1A1A1A;
    font-weight: 600;
}}
QPushButton[class="warning-solid"]:hover {{
    background-color: #FFB020;
}}
QPushButton[class="danger-solid"] {{
    background-color: {COLORS['error']};
    border: none;
    color: white;
    font-weight: 600;
}}
QPushButton[class="danger-solid"]:hover {{
    background-color: #FF5C52;
}}
QPushButton[class="success-solid"] {{
    background-color: {COLORS['success']};
    border: none;
    color: #0B1A12;
    font-weight: 600;
}}
QPushButton[class="success-solid"]:hover {{
    background-color: #3DDC71;
}}

/* ===== SEGMENTED CONTROL (COMPACT) ===== */
QFrame[class="segmented"] {{
    background-color: {COLORS['bg_raised']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
}}
QPushButton[class="seg-btn-left"],
QPushButton[class="seg-btn-middle"],
QPushButton[class="seg-btn-right"] {{
    background: transparent;
    border: none;
    color: {COLORS['text_secondary']};
    font-size: 11px;
    font-weight: 600;
    padding: 2px 6px;
    min-width: 24px;
}}
QPushButton[class="seg-btn-middle"],
QPushButton[class="seg-btn-right"] {{
    border-left: 1px solid {COLORS['border']};
}}
QPushButton[class="seg-btn-left"] {{
    border-top-left-radius: 5px;
    border-bottom-left-radius: 5px;
}}
QPushButton[class="seg-btn-right"] {{
    border-top-right-radius: 5px;
    border-bottom-right-radius: 5px;
}}
QPushButton[class="seg-btn-left"]:checked,
QPushButton[class="seg-btn-middle"]:checked,
QPushButton[class="seg-btn-right"]:checked {{
    background-color: {COLORS['accent_primary']};
    color: white;
}}
QPushButton[class="seg-btn-left"]:hover,
QPushButton[class="seg-btn-middle"]:hover,
QPushButton[class="seg-btn-right"]:hover {{
    background-color: {COLORS['bg_hover']};
}}

/* ===== PREVIEW TILES ===== */
QFrame[class="preview-tile"] {{
    background-color: {COLORS['bg_tertiary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
}}
QFrame[class="preview-tile"]:hover {{
    border-color: {COLORS['accent_primary']};
}}

/* ===== TABLES ===== */
QTableWidget[class="table"] {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    gridline-color: {COLORS['divider']};
}}
QTableWidget[class="table"]::item {{
    padding: 6px;
}}
QTableWidget[class="table"]::item:selected {{
    background-color: {COLORS['accent_primary']};
}}
QHeaderView::section {{
    background-color: {COLORS['bg_tertiary']};
    border: none;
    padding: 6px;
    font-weight: 600;
    color: {COLORS['text_secondary']};
}}
QListWidget[class="list"] {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    font-size: 11px;
}}
QListWidget[class="list"]::item {{
    padding: 6px;
    border-bottom: 1px solid {COLORS['divider']};
}}
QListWidget[class="list"]::item:selected {{
    background-color: {COLORS['bg_active']};
}}
QListWidget[class="list-compact"] {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    font-size: 11px;
}}
QListWidget[class="list-compact"]::item {{
    padding: 4px 8px;
    border-bottom: 1px solid {COLORS['divider']};
}}
QListWidget[class="list-compact"]::item:selected {{
    background-color: {COLORS['accent_primary']};
}}
QTextEdit[class="log-view"] {{
    background-color: {COLORS['bg_tertiary']};
    color: {COLORS['text_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    font-family: 'Consolas', monospace;
    font-size: 11px;
}}

/* ===== TOOL BUTTONS ===== */
QToolButton {{
    background: transparent;
    border: none;
    border-radius: 4px;
    padding: 8px;
}}
QToolButton:hover {{
    background-color: {COLORS['bg_hover']};
}}
QToolButton:pressed {{
    background-color: {COLORS['bg_active']};
}}
QToolButton:checked {{
    background-color: {COLORS['accent_primary']};
}}

/* ===== COMBO BOXES ===== */
QComboBox {{
    background-color: {COLORS['bg_tertiary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 9px 12px;
    padding-right: 30px;
    min-height: 26px;
}}
QComboBox:hover {{
    border-color: {COLORS['border_focus']};
}}
QComboBox:focus {{
    border-color: {COLORS['accent_primary']};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {COLORS['text_secondary']};
    margin-right: 8px;
}}
QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 4px;
    selection-background-color: {COLORS['accent_primary']};
}}
QComboBox[class="panel-combo"] {{
    padding: 6px 8px;
    min-height: 22px;
    font-size: 11px;
}}
QComboBox[class="compact"] {{
    padding: 6px 8px;
    min-height: 24px;
    font-size: 12px;
}}
QComboBox[class="toolbar-combo"] {{
    background-color: {COLORS['bg_raised']};
    padding: 4px 22px 4px 8px;
    min-height: 22px;
    font-size: 11px;
}}

/* ===== LINE EDITS ===== */
QLineEdit {{
    background-color: {COLORS['bg_tertiary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px 12px;
    min-height: 24px;
}}
QLineEdit:hover {{
    border-color: {COLORS['border_focus']};
}}
QLineEdit:focus {{
    border-color: {COLORS['accent_primary']};
}}

/* ===== SPIN BOXES ===== */
QSpinBox, QDoubleSpinBox {{
    background-color: {COLORS['bg_tertiary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 6px 8px;
    min-width: 58px;
    min-height: 24px;
}}
QSpinBox:hover, QDoubleSpinBox:hover {{
    border-color: {COLORS['border_focus']};
}}
QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {COLORS['accent_primary']};
}}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    width: 0;
    border: none;
}}

/* ===== SLIDERS ===== */
QSlider {{
    background: transparent;
    border: none;
    outline: none;
}}
QSlider:focus {{
    border: none;
    outline: none;
}}
QSlider::groove:horizontal {{
    border: none;
    height: 4px;
    background: {COLORS['bg_active']};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {COLORS['accent_primary']};
    border: 1px solid rgba(255,255,255,0.15);
    width: 12px;
    height: 12px;
    margin: -4px 0;
    border-radius: 6px;
}}
QSlider::handle:horizontal:hover {{
    background: {COLORS['accent_hover']};
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}
QSlider::sub-page:horizontal {{
    background: {COLORS['accent_primary']};
    border: none;
    border-radius: 2px;
}}
QSlider::add-page:horizontal {{
    background: {COLORS['bg_active']};
    border: none;
    border-radius: 2px;
}}

/* ===== CHECK BOXES ===== */
QCheckBox {{
    spacing: 10px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 2px solid {COLORS['border']};
    background: {COLORS['bg_tertiary']};
}}
QCheckBox::indicator:hover {{
    border-color: {COLORS['accent_primary']};
}}
QCheckBox::indicator:checked {{
    background-color: {COLORS['accent_primary']};
    border-color: {COLORS['accent_primary']};
}}

/* ===== RADIO BUTTONS ===== */
QRadioButton {{
    spacing: 10px;
}}
QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 8px;
    border: 2px solid {COLORS['border']};
    background: {COLORS['bg_tertiary']};
}}
QRadioButton::indicator:hover {{
    border-color: {COLORS['accent_primary']};
}}
QRadioButton::indicator:checked {{
    background-color: {COLORS['accent_primary']};
    border-color: {COLORS['accent_primary']};
}}
QRadioButton::indicator:checked {{
    background-color: {COLORS['accent_primary']};
    border: 4px solid {COLORS['bg_tertiary']};
}}

/* ===== PROGRESS BAR ===== */
QProgressBar {{
    border: none;
    border-radius: 4px;
    background-color: {COLORS['bg_tertiary']};
    height: 6px;
    text-align: center;
}}
QProgressBar::chunk {{
    background-color: {COLORS['accent_primary']};
    border-radius: 4px;
}}

/* ===== MENU BAR ===== */
QMenuBar {{
    background-color: {COLORS['bg_secondary']};
    border-bottom: 1px solid {COLORS['divider']};
    padding: 5px 8px;
}}
QMenuBar::item {{
    background: transparent;
    padding: 6px 12px;
    border-radius: 4px;
}}
QMenuBar::item:selected {{
    background-color: {COLORS['bg_hover']};
}}
QMenu {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 8px 4px;
}}
QMenu::item {{
    padding: 8px 32px 8px 16px;
    border-radius: 4px;
    margin: 2px 4px;
}}
QMenu::item:selected {{
    background-color: {COLORS['bg_hover']};
}}
QMenu::separator {{
    height: 1px;
    background: {COLORS['border']};
    margin: 4px 8px;
}}

/* ===== FRAMES ===== */
QFrame[class="separator"] {{
    background-color: {COLORS['border']};
    max-height: 1px;
    min-height: 1px;
}}
QFrame[class="toolbar-separator"] {{
    background-color: {COLORS['divider']};
    max-height: 1px;
    min-height: 1px;
}}
QFrame[class="toolbar-separator-v"] {{
    background-color: {COLORS['divider']};
    max-width: 1px;
    min-width: 1px;
}}
QFrame[class="card"] {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 10px;
}}
QFrame[class="floating-toolbar"] {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
}}
QFrame[class="toolbar-divider"] {{
    background-color: {COLORS['divider']};
}}
QPushButton[class="toolbar-btn"] {{
    background-color: {COLORS['bg_raised']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 6px 12px;
    min-height: 28px;
    font-weight: 600;
    color: {COLORS['text_secondary']};
}}
QPushButton[class="toolbar-btn"]:hover {{
    background-color: {COLORS['bg_hover']};
}}
QPushButton[class="toolbar-btn"]:checked {{
    background-color: {COLORS['accent_primary']};
    border: none;
    color: white;
}}
QFrame[class="swatch-group"] {{
    background-color: {COLORS['bg_raised']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
}}
QPushButton[class="swatch-btn"] {{
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    min-width: 24px;
    min-height: 24px;
}}
QPushButton[class="swatch-btn"]:checked {{
    border: 2px solid {COLORS['accent_primary']};
}}
QPushButton[class="mini-swatch"] {{
    border: 1px solid {COLORS['border']};
    border-radius: 5px;
    padding: 0;
    min-width: 18px;
    min-height: 18px;
}}
QPushButton[class="mini-swatch"]:checked {{
    border: 2px solid {COLORS['accent_primary']};
}}
QSlider[class="toolbar-slider"] {{
    min-height: 22px;
    max-height: 22px;
}}
QSlider[class="toolbar-slider"]::groove:horizontal {{
    height: 4px;
    background: {COLORS['bg_raised']};
    border-radius: 2px;
}}
QSlider[class="toolbar-slider"]::handle:horizontal {{
    background: {COLORS['text_secondary']};
    border: 1px solid {COLORS['border']};
    width: 12px;
    height: 12px;
    margin: -5px 0;
    border-radius: 6px;
}}
QSlider[class="toolbar-slider"]::handle:horizontal:hover {{
    background: {COLORS['accent_hover']};
}}

/* ===== SPLITTER ===== */
QSplitter::handle {{
    background-color: {COLORS['divider']};
}}
QSplitter::handle:horizontal {{
    width: 1px;
}}
QSplitter::handle:vertical {{
    height: 1px;
}}

/* ===== TOOLTIPS ===== */
QToolTip {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 5px;
    padding: 7px 10px;
    color: {COLORS['text_primary']};
    font-size: 12px;
}}

/* ===== FOCUS VISIBILITY ===== */
QPushButton:focus,
QToolButton:focus,
QComboBox:focus,
QSpinBox:focus,
QDoubleSpinBox:focus,
QCheckBox:focus,
QRadioButton:focus,
QListWidget:focus,
QLineEdit:focus,
QTextEdit:focus,
QPlainTextEdit:focus {{
    border: 1px solid {COLORS['border_focus']};
}}

QPushButton:focus,
QToolButton:focus,
QComboBox:focus,
QSpinBox:focus,
QDoubleSpinBox:focus,
QListWidget:focus,
QLineEdit:focus,
QTextEdit:focus,
QPlainTextEdit:focus {{
    selection-background-color: {COLORS['accent_primary']};
}}

/* ===== STATUS BAR ===== */
QStatusBar {{
    background-color: {COLORS['bg_secondary']};
    border-top: 1px solid {COLORS['divider']};
    padding: 4px;
}}

/* ===== CANVAS / PREVIEW AREA ===== */
QWidget[class="preview-canvas"] {{
    background-color: #2A2A2A;
    border: 1px solid {COLORS['border']};
    border-radius: 10px;
}}

/* ===== SEGMENT BUTTONS (Toggle Group) ===== */
QPushButton[class="segment-left"] {{
    background-color: {COLORS['bg_raised']};
    border: 1px solid {COLORS['border']};
    border-top-right-radius: 0;
    border-bottom-right-radius: 0;
    border-right: none;
}}
QPushButton[class="segment-middle"] {{
    background-color: {COLORS['bg_raised']};
    border: 1px solid {COLORS['border']};
    border-radius: 0;
    border-right: none;
}}
QPushButton[class="segment-right"] {{
    background-color: {COLORS['bg_raised']};
    border: 1px solid {COLORS['border']};
    border-top-left-radius: 0;
    border-bottom-left-radius: 0;
}}
QPushButton[class^="segment"]:checked {{
    background-color: {COLORS['accent_primary']};
    border-color: {COLORS['accent_primary']};
    color: white;
}}
"""


def scale_stylesheet(css: str, scale: float) -> str:
    """
    Scale every pixel-based value in the stylesheet so the UI adapts to
    different screen sizes. If the scale is near 1.0 the original CSS is
    returned untouched.
    """
    if scale <= 0:
        return css
    if abs(scale - 1.0) < 0.01:
        return css

    def _repl(match: re.Match) -> str:
        value = float(match.group(1))
        scaled = max(int(round(value * scale)), 1)
        return f"{scaled}px"

    return re.sub(r"([0-9]*\.?[0-9]+)px", _repl, css)


def get_stylesheet(scale: float = 1.0) -> str:
    """Return the dark theme stylesheet scaled to the requested factor."""
    return scale_stylesheet(MODERN_DARK_STYLESHEET, scale)
