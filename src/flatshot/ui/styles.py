"""
Modern Dark Theme Stylesheet for PyQt6
Inspired by DaVinci Resolve, Figma, and VS Code
"""
import re

# Color Palette
COLORS = {
    'bg_primary': '#1A1A1A',
    'bg_secondary': '#242424',
    'bg_tertiary': '#2D2D2D',
    'bg_hover': '#3A3A3A',
    'bg_active': '#404040',
    
    'accent_primary': '#0078D4',
    'accent_hover': '#1A8CFF',
    'accent_pressed': '#005A9E',
    'accent_focus_ring': 'rgba(0, 120, 212, 0.28)',
    
    'text_primary': '#E8E8E8',
    'text_secondary': '#B7BDC8',
    'text_disabled': '#666666',
    
    'border': '#3A3A3A',
    'border_focus': '#0078D4',
    
    'success': '#4CAF50',
    'warning': '#FF9800',
    'error': '#F44336',
    
    'shadow': 'rgba(0, 0, 0, 0.3)',
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
    width: 11px;
    margin: 0;
    border-radius: 5px;
}}
QScrollBar::handle:vertical {{
    background: {COLORS['bg_tertiary']};
    min-height: 30px;
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
    height: 11px;
    margin: 0;
    border-radius: 5px;
}}
QScrollBar::handle:horizontal {{
    background: {COLORS['bg_tertiary']};
    min-width: 30px;
    border-radius: 5px;
}}

/* ===== GROUP BOXES ===== */
QGroupBox {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 9px;
    margin-top: 14px;
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
    border-radius: 8px;
}}
QFrame[class="section-header"] {{
    background-color: {COLORS['bg_secondary']};
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
}}
QToolButton {{
    color: {COLORS['text_secondary']};
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
}}
QToolButton[class="section-toggle"] {{
    background: transparent;
    border: none;
    padding: 4px 6px;
    text-align: left;
    min-height: 20px;
}}
QToolButton[class="section-toggle"]:hover {{
    background-color: {COLORS['bg_hover']};
}}
QToolButton[class="section-toggle"]:pressed {{
    background-color: {COLORS['bg_active']};
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
    font-size: 20px;
    font-weight: 700;
    color: {COLORS['text_primary']};
    letter-spacing: 0.5px;
    padding-top: 2px;
    padding-bottom: 4px;
}}
QLabel[class="subheading"] {{
    font-size: 12px;
    color: {COLORS['text_secondary']};
}}
QLabel[class="param-label"] {{
    font-size: 13px;
    color: {COLORS['text_secondary']};
}}

/* ===== BUTTONS ===== */
QPushButton {{
    background-color: {COLORS['bg_tertiary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
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
    padding: 12px 24px;
    font-size: 14px;
}}
QPushButton[class="primary"]:hover {{
    background-color: {COLORS['accent_hover']};
}}
QPushButton[class="primary"]:pressed {{
    background-color: {COLORS['accent_pressed']};
}}
QPushButton[class="icon-btn"] {{
    background: transparent;
    border: none;
    padding: 5px;
    border-radius: 4px;
    min-width: 32px;
    max-width: 32px;
    min-height: 32px;
    max-height: 32px;
}}
QPushButton[class="icon-btn"]:hover {{
    background-color: {COLORS['bg_hover']};
}}
QPushButton[class="danger"] {{
    color: {COLORS['error']};
}}
QPushButton[class="danger"]:hover {{
    background-color: rgba(244, 67, 54, 0.15);
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
    min-height: 24px;
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

/* ===== LINE EDITS ===== */
QLineEdit {{
    background-color: {COLORS['bg_tertiary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px 10px;
    min-height: 22px;
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
    border-radius: 5px;
    padding: 5px 7px;
    min-width: 58px;
    min-height: 22px;
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
    height: 5px;
    background: {COLORS['bg_active']};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {COLORS['accent_primary']};
    border: none;
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
}}
QSlider::handle:horizontal:hover {{
    background: {COLORS['accent_hover']};
    width: 18px;
    height: 18px;
    margin: -7px 0;
    border-radius: 9px;
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
    width: 20px;
    height: 20px;
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
    width: 18px;
    height: 18px;
    border-radius: 10px;
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
    height: 8px;
    text-align: center;
}}
QProgressBar::chunk {{
    background-color: {COLORS['accent_primary']};
    border-radius: 4px;
}}

/* ===== MENU BAR ===== */
QMenuBar {{
    background-color: {COLORS['bg_secondary']};
    border-bottom: 1px solid {COLORS['border']};
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
QFrame[class="card"] {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
}}

/* ===== SPLITTER ===== */
QSplitter::handle {{
    background-color: {COLORS['border']};
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
    border-top: 1px solid {COLORS['border']};
    padding: 4px;
}}

/* ===== CANVAS / PREVIEW AREA ===== */
QLabel[class="preview-canvas"] {{
    background-color: #2A2A2A;
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
}}

/* ===== SEGMENT BUTTONS (Toggle Group) ===== */
QPushButton[class="segment-left"] {{
    border-top-right-radius: 0;
    border-bottom-right-radius: 0;
    border-right: none;
}}
QPushButton[class="segment-middle"] {{
    border-radius: 0;
    border-right: none;
}}
QPushButton[class="segment-right"] {{
    border-top-left-radius: 0;
    border-bottom-left-radius: 0;
}}
QPushButton[class^="segment"]:checked {{
    background-color: {COLORS['accent_primary']};
    border-color: {COLORS['accent_primary']};
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
