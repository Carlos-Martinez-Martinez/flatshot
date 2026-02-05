"""
Custom Widgets for Modern UI
"""
import math
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSlider, QSpinBox,
    QFrame, QPushButton, QSizePolicy, QGraphicsDropShadowEffect, QToolButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRectF, QTimer, QEvent, QSize
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QRadialGradient, 
    QLinearGradient, QFont, QPainterPath, QPixmap, QImage
)
from PIL import Image
import qtawesome as qta


class SmartSlider(QWidget):
    """
    Composite slider widget with:
    - Parameter label with optional tooltip
    - Horizontal slider
    - Synchronized spinbox
    """
    valueChanged = pyqtSignal(int)
    defaultReset = pyqtSignal(int)
    
    def __init__(self, label: str, min_val: int = 0, max_val: int = 100, 
                 default: int = 50, suffix: str = "", tooltip: str = "",
                 scale: float = 1.0, parent=None):
        super().__init__(parent)
        self.suffix = suffix
        self._default = default
        self._label_text = label
        self._scale = max(scale, 0.1)
        self._setup_ui(label, min_val, max_val, default, tooltip)
        
    def _px(self, value: int) -> int:
        return max(int(round(value * self._scale)), 1)
        
    def _setup_ui(self, label: str, min_val: int, max_val: int, default: int, tooltip: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, self._px(1), 0, self._px(1))
        layout.setSpacing(self._px(5))
        
        # Label
        self.label = QLabel(label)
        self.label.setProperty("class", "param-label")
        self.label.setFixedWidth(self._px(70))  # Compact label
        base_tooltip = tooltip.strip() if tooltip else ""
        reset_hint = "<br><br><span style='color:#7EA9D6'>Tip: doble clic para restaurar el valor por defecto.</span>"
        final_tooltip = f"{base_tooltip}{reset_hint}" if base_tooltip else "Doble clic para restaurar el valor por defecto."
        self.label.setToolTip(final_tooltip)
        self.setToolTip(final_tooltip)
        layout.addWidget(self.label)
        
        # Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(min_val, max_val)
        self.slider.setValue(default)
        self.slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.slider.setSingleStep(1)
        self.slider.setPageStep(max(1, (max_val - min_val) // 10))
        self.slider.setMinimumWidth(self._px(60))
        # Avoid intrusive focus frames on sliders; keyboard editing is done via spinbox.
        self.slider.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.slider.installEventFilter(self)
        layout.addWidget(self.slider, 1)  # Takes remaining space
        
        # SpinBox
        self.spinbox = QSpinBox()
        self.spinbox.setRange(min_val, max_val)
        self.spinbox.setValue(default)
        self.spinbox.setSuffix(self.suffix)
        self.spinbox.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spinbox.setMinimumWidth(self._px(55))
        self.spinbox.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.spinbox.installEventFilter(self)
        layout.addWidget(self.spinbox, 0)  # stretch factor 0 to not expand
        
        # Bidirectional sync
        self.slider.valueChanged.connect(self._on_slider_changed)
        self.spinbox.valueChanged.connect(self._on_spinbox_changed)
        self.setAccessibleName(f"Control {self._label_text}")
        self.slider.setAccessibleName(f"{self._label_text} slider")
        self.spinbox.setAccessibleName(f"{self._label_text} valor")
        
    def _on_slider_changed(self, value: int):
        self.spinbox.blockSignals(True)
        self.spinbox.setValue(value)
        self.spinbox.blockSignals(False)
        self.valueChanged.emit(value)
        
    def _on_spinbox_changed(self, value: int):
        self.slider.blockSignals(True)
        self.slider.setValue(value)
        self.slider.blockSignals(False)
        self.valueChanged.emit(value)
        
    def value(self) -> int:
        return self.slider.value()
    
    def setValue(self, value: int):
        self.slider.setValue(value)

    def reset_to_default(self):
        """Reset control to its initial default value."""
        if hasattr(self, "slider"):
            self.setValue(self._default)
            self.defaultReset.emit(self._default)

    def eventFilter(self, watched, event):
        slider = getattr(self, "slider", None)
        spinbox = getattr(self, "spinbox", None)
        targets = tuple(w for w in (slider, spinbox) if w is not None)
        if targets and watched in targets and event.type() == QEvent.Type.MouseButtonDblClick:
            self.reset_to_default()
            return True
        return super().eventFilter(watched, event)


class CollapsibleSection(QFrame):
    """Lightroom-like collapsible section with arrow header and compact collapsed height."""

    toggled = pyqtSignal(bool)

    def __init__(self, title: str, expanded: bool = True, parent=None):
        super().__init__(parent)
        self._scale = getattr(parent, "ui_scale", 1.0)
        self._title = title
        self._expanded = bool(expanded)
        self.setProperty("class", "section")
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QFrame()
        header.setProperty("class", "section-header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(4, 2, 4, 2)
        header_layout.setSpacing(6)

        self._toggle_btn = QToolButton()
        self._toggle_btn.setProperty("class", "section-toggle")
        self._toggle_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self._toggle_btn.setCheckable(False)
        icon_color = "#AEB4BE"
        self._icon_expanded = qta.icon('fa5s.chevron-down', color=icon_color)
        self._icon_collapsed = qta.icon('fa5s.chevron-right', color=icon_color)
        self._toggle_btn.setIcon(self._icon_expanded if self._expanded else self._icon_collapsed)
        self._toggle_btn.setIconSize(QSize(self._px(10), self._px(10)))
        self._toggle_btn.setText(self._title)
        self._toggle_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._toggle_btn.setStyleSheet("text-align: left; padding-left: 2px;")
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_btn.setMinimumHeight(self._px(22))
        self._toggle_btn.clicked.connect(self._on_toggled)
        header_layout.addWidget(self._toggle_btn, 1)
        outer.addWidget(header)

        self._content = QWidget()
        self._content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(8, 4, 8, 6)
        self._content_layout.setSpacing(6)
        outer.addWidget(self._content)

        self.setExpanded(self._expanded, emit_signal=False)

    def _px(self, value: int) -> int:
        return max(int(round(value * self._scale)), 1)

    @property
    def content_layout(self) -> QVBoxLayout:
        return self._content_layout

    def setExpanded(self, expanded: bool, emit_signal: bool = True):
        self._expanded = bool(expanded)
        if self._expanded:
            self._content.setVisible(True)
            self._content.setMaximumHeight(16777215)
        else:
            self._content.setVisible(False)
            self._content.setMaximumHeight(0)
        self._toggle_btn.setIcon(self._icon_expanded if self._expanded else self._icon_collapsed)
        if emit_signal:
            self.toggled.emit(self._expanded)
        self.updateGeometry()

    def _on_toggled(self):
        self.setExpanded(not self._expanded)

    def sizeHint(self) -> QSize:
        base = super().sizeHint()
        if self._expanded:
            return base
        header_h = self._toggle_btn.sizeHint().height() + 12
        return QSize(base.width(), header_h)

    def minimumSizeHint(self) -> QSize:
        base = super().minimumSizeHint()
        if self._expanded:
            return base
        header_h = self._toggle_btn.sizeHint().height() + 12
        return QSize(base.width(), header_h)


class LightAngleWidget(QWidget):
    """
    Circular widget for selecting light angle with visual feedback.
    Features a radar-like dial with direction indicator.
    """
    angleChanged = pyqtSignal(int)
    
    def __init__(self, parent=None, scale: float = 1.0):
        super().__init__(parent)
        self._angle = 180  # degrees, 0 = top
        self._dragging = False
        self._scale = max(scale, 0.1)
        size = self._px(110)
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _px(self, value: int) -> int:
        return max(int(round(value * self._scale)), 1)
        
    def angle(self) -> int:
        return self._angle
    
    def setAngle(self, angle: int):
        angle = angle % 360
        if self._angle != angle:
            self._angle = angle
            self.update()
            self.angleChanged.emit(self._angle)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2
        radius = min(w, h) // 2 - self._px(8)
        
        # Background circle with gradient
        bg_gradient = QRadialGradient(cx, cy, radius)
        bg_gradient.setColorAt(0, QColor("#3A3A3A"))
        bg_gradient.setColorAt(1, QColor("#2A2A2A"))
        painter.setBrush(QBrush(bg_gradient))
        painter.setPen(QPen(QColor("#4A4A4A"), self._px(2)))
        painter.drawEllipse(QPoint(cx, cy), radius, radius)
        
        # Inner circle
        inner_radius = radius - self._px(20)
        painter.setPen(QPen(QColor("#3A3A3A"), self._px(1)))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPoint(cx, cy), inner_radius, inner_radius)
        
        # Direction ticks (N, E, S, W) with labels
        painter.setPen(QPen(QColor("#666666"), self._px(2)))
        directions = [(0, "↑"), (90, "→"), (180, "↓"), (270, "←")]
        for angle, label in directions:
            rad = math.radians(angle - 90)
            x1 = cx + (radius - self._px(6)) * math.cos(rad)
            y1 = cy + (radius - self._px(6)) * math.sin(rad)
            x2 = cx + (radius - self._px(12)) * math.cos(rad)
            y2 = cy + (radius - self._px(12)) * math.sin(rad)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        
        # Light direction indicator (main line)
        angle_rad = math.radians(self._angle - 90)
        end_x = cx + (radius - self._px(8)) * math.cos(angle_rad)
        end_y = cy + (radius - self._px(8)) * math.sin(angle_rad)
        
        # Glow effect for indicator
        glow_pen = QPen(QColor("#0078D4"))
        glow_pen.setWidth(self._px(6))
        glow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setOpacity(0.3)
        painter.setPen(glow_pen)
        painter.drawLine(cx, cy, int(end_x), int(end_y))
        
        # Main indicator line
        painter.setOpacity(1.0)
        indicator_pen = QPen(QColor("#0078D4"))
        indicator_pen.setWidth(self._px(3))
        indicator_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(indicator_pen)
        painter.drawLine(cx, cy, int(end_x), int(end_y))
        
        # Indicator dot at end
        painter.setBrush(QBrush(QColor("#0078D4")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPoint(int(end_x), int(end_y)), self._px(6), self._px(6))
        
        # Center dot
        painter.setBrush(QBrush(QColor("#E8E8E8")))
        painter.drawEllipse(QPoint(cx, cy), self._px(4), self._px(4))
        
        # Angle text
        font = QFont("Segoe UI", 9)
        font.setBold(True)
        base_size = font.pointSizeF()
        if base_size <= 0:
            base_size = 9.0
        font.setPointSizeF(max(base_size * self._scale, 1.0))
        painter.setFont(font)
        painter.setPen(QColor("#A0A0A0"))
        text = f"{self._angle}°"
        text_rect = painter.fontMetrics().boundingRect(text)
        painter.drawText(cx - text_rect.width() // 2, cy + radius + self._px(18), text)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._update_angle_from_pos(event.position())
            
    def mouseMoveEvent(self, event):
        if self._dragging:
            self._update_angle_from_pos(event.position())
            
    def mouseReleaseEvent(self, event):
        self._dragging = False
        
    def _update_angle_from_pos(self, pos):
        cx, cy = self.width() / 2, self.height() / 2
        dx = pos.x() - cx
        dy = pos.y() - cy
        angle = math.degrees(math.atan2(dy, dx)) + 90
        if angle < 0:
            angle += 360
        self.setAngle(int(angle))


class ComparisonCanvas(QWidget):
    """
    Image preview widget with A/B comparison functionality.
    Supports:
    - Before/After toggle with spacebar
    - Slider comparison mode
    - Drag & Drop for images
    """
    imageDropped = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._original_image: QPixmap = None
        self._processed_image: QPixmap = None
        self._show_original = False
        self._comparison_mode = 'toggle'  # 'toggle' or 'slider'
        self._slider_pos = 0.5  # 0-1, position of comparison slider
        self._bg_color = QColor("#2A2A2A")
        self._grid_visible = False
        self._badge_opacity = 1.0  # For fade effect
        self._zoom_level = 1.0  # Zoom support
        
        self.setAcceptDrops(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setProperty("class", "preview-canvas")
        self.setMinimumSize(400, 400)
        
        # Placeholder text
        self._placeholder_text = "Arrastra una imagen aquí\no selecciona una carpeta"
        
        # Badge fade timer
        self._fade_timer = QTimer(self)
        self._fade_timer.timeout.connect(self._fade_badge)
        
    def setOriginalImage(self, image: QPixmap):
        self._original_image = image
        self.update()
        
    def setProcessedImage(self, image: QPixmap):
        self._processed_image = image
        self._badge_opacity = 1.0  # Reset badge visibility
        self._fade_timer.start(2000)  # Start fade after 2s
        self.update()
        
    def _fade_badge(self):
        self._fade_timer.stop()
        self._badge_opacity = 0.4  # Semi-transparent
        self.update()
        
    def setBackgroundColor(self, color: QColor):
        self._bg_color = color
        self.update()
        
    def setGridVisible(self, visible: bool):
        self._grid_visible = visible
        self.update()
        
    def setComparisonMode(self, mode: str):
        self._comparison_mode = mode
        self.update()
        
    def wheelEvent(self, event):
        """Handle mouse wheel for zooming."""
        delta = event.angleDelta().y()
        if delta > 0:
            self._zoom_level = min(3.0, self._zoom_level * 1.1)
        else:
            self._zoom_level = max(0.5, self._zoom_level / 1.1)
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # Background
        painter.fillRect(self.rect(), self._bg_color)
        
        # Image
        current_image = self._original_image if self._show_original else self._processed_image
        
        if current_image and not current_image.isNull():
            # Scale to fit with zoom
            base_size = self.size()
            target_width = int(base_size.width() * self._zoom_level)
            target_height = int(base_size.height() * self._zoom_level)
            
            scaled = current_image.scaled(
                target_width, target_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
            
            # Zoom indicator (if not 100%)
            if abs(self._zoom_level - 1.0) > 0.01:
                self._draw_zoom_indicator(painter)
            
            # A/B indicator
            if self._show_original:
                self._draw_indicator(painter, "ORIGINAL", QColor("#FF9800"))
            else:
                self._draw_indicator(painter, "PROCESADA", QColor("#4CAF50"))
            
            # Grid overlay (drawn OVER the image)
            if self._grid_visible:
                self._draw_grid(painter)
        else:
            # Placeholder
            self._draw_placeholder(painter)
            
    def _draw_grid(self, painter):
        """Draw rule-of-thirds grid overlay for composition help."""
        w, h = self.width(), self.height()
        
        # Semi-transparent lines
        pen = QPen(QColor(255, 255, 255, 80))
        pen.setWidth(1)
        painter.setPen(pen)
        
        # Rule of thirds - vertical lines
        x1 = w // 3
        x2 = 2 * w // 3
        painter.drawLine(x1, 0, x1, h)
        painter.drawLine(x2, 0, x2, h)
        
        # Rule of thirds - horizontal lines
        y1 = h // 3
        y2 = 2 * h // 3
        painter.drawLine(0, y1, w, y1)
        painter.drawLine(0, y2, w, y2)
        
        # Center crosshair (thinner, dotted)
        center_pen = QPen(QColor(0, 120, 212, 120))
        center_pen.setWidth(1)
        center_pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(center_pen)
        
        cx, cy = w // 2, h // 2
        painter.drawLine(cx, 0, cx, h)  # Vertical center
        painter.drawLine(0, cy, w, cy)  # Horizontal center
            
    def _draw_indicator(self, painter, text: str, color: QColor):
        painter.setOpacity(self._badge_opacity)
        
        font = QFont("Segoe UI", 9)
        font.setBold(True)
        painter.setFont(font)
        
        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(text) + 12
        text_height = metrics.height() + 6
        
        # Background pill (smaller, subtler)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        rect = QRectF(10, 10, text_width, text_height)
        painter.drawRoundedRect(rect, text_height / 2, text_height / 2)
        
        # Text
        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
        
        painter.setOpacity(1.0)  # Reset
    
    def _draw_zoom_indicator(self, painter):
        """Draw zoom level indicator in bottom-right corner."""
        text = f"{int(self._zoom_level * 100)}%"
        font = QFont("Segoe UI", 9)
        painter.setFont(font)
        
        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(text) + 10
        text_height = metrics.height() + 4
        
        # Position in bottom-right
        x = self.width() - text_width - 10
        y = self.height() - text_height - 10
        
        # Background
        painter.setBrush(QBrush(QColor(30, 30, 30, 180)))
        painter.setPen(Qt.PenStyle.NoPen)
        rect = QRectF(x, y, text_width, text_height)
        painter.drawRoundedRect(rect, 4, 4)
        
        # Text
        painter.setPen(QColor("#A0A0A0"))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
        
    def _draw_placeholder(self, painter):
        # Dashed border
        pen = QPen(QColor("#4A4A4A"))
        pen.setStyle(Qt.PenStyle.DashLine)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        margin = 20
        painter.drawRoundedRect(margin, margin, 
                               self.width() - 2*margin, 
                               self.height() - 2*margin, 12, 12)
        
        # Icon placeholder
        icon_size = 48
        cx, cy = self.width() // 2, self.height() // 2 - 30
        painter.setPen(QPen(QColor("#666666"), 3))
        painter.drawRect(cx - icon_size//2, cy - icon_size//2, icon_size, icon_size)
        
        # Arrow down
        painter.drawLine(cx, cy + icon_size//2 - 10, cx, cy + icon_size//2 + 5)
        painter.drawLine(cx - 8, cy + icon_size//2 - 3, cx, cy + icon_size//2 + 5)
        painter.drawLine(cx + 8, cy + icon_size//2 - 3, cx, cy + icon_size//2 + 5)
        
        # Text
        font = QFont("Segoe UI", 12)
        painter.setFont(font)
        painter.setPen(QColor("#666666"))
        lines = self._placeholder_text.split('\n')
        y_offset = cy + icon_size//2 + 35
        for line in lines:
            rect = painter.fontMetrics().boundingRect(line)
            painter.drawText(cx - rect.width()//2, y_offset, line)
            y_offset += rect.height() + 4
            
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self._show_original = True
            self.update()
        super().keyPressEvent(event)
        
    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self._show_original = False
            self.update()
        super().keyReleaseEvent(event)
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].toLocalFile().lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                event.acceptProposedAction()
                return
        event.ignore()
        
    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            self.imageDropped.emit(path)


class FloatingToolbar(QFrame):
    """
    Floating toolbar for canvas controls.
    """
    gridToggled = pyqtSignal(bool)
    zoomChanged = pyqtSignal(int)
    bgColorChanged = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "card")
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)
        
        # Grid button
        self.btn_grid = QPushButton("⊞")
        self.btn_grid.setProperty("class", "icon-btn")
        self.btn_grid.setCheckable(True)
        self.btn_grid.setToolTip("Guías de composición (regla de tercios)")
        self.btn_grid.toggled.connect(self._on_grid_toggled)
        layout.addWidget(self.btn_grid)
        
        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("background-color: #3A3A3A;")
        sep.setFixedWidth(1)
        layout.addWidget(sep)
        
        # Background color buttons
        for color, name in [("#FFFFFF", "Blanco"), ("#E6E6E6", "Gris"), ("#2A2A2A", "Oscuro")]:
            btn = QPushButton()
            btn.setProperty("class", "icon-btn")
            btn.setFixedSize(24, 24)
            btn.setStyleSheet(f"background-color: {color}; border-radius: 4px; border: 1px solid #4A4A4A;")
            btn.setToolTip(f"Fondo {name}")
            btn.clicked.connect(lambda checked, c=color: self.bgColorChanged.emit(c))
            layout.addWidget(btn)
    
    def _on_grid_toggled(self, checked: bool):
        """Handle grid button toggle with visual feedback."""
        if checked:
            self.btn_grid.setStyleSheet("background-color: #0078D4; border-radius: 4px;")
            self.btn_grid.setText("⊞ ON")
        else:
            self.btn_grid.setStyleSheet("")
            self.btn_grid.setText("⊞")
        self.gridToggled.emit(checked)


class ModernSplashScreen(QWidget):
    """
    Modern splash screen with loading animation.
    """
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(450, 320)
        
        self._status_text = "Cargando recursos..."
        self._progress = 0
        self._dots = 0
        self._start_time = None
        self._min_display_ms = 2000  # 2 seconds minimum
        
        # Center on screen
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2
        )
        
        # Animation timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(120)
        
        # Track start time
        from time import time
        self._start_time = time() * 1000
        
    def _animate(self):
        self._dots = (self._dots + 1) % 4
        # Calculate progress based on elapsed time
        from time import time
        elapsed = time() * 1000 - self._start_time
        self._progress = min(100, int((elapsed / self._min_display_ms) * 100))
        self.update()
        
    def update_status(self, text: str, progress: int = 0):
        self._status_text = text
        self._progress = progress
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Shadow
        shadow_margin = 20
        shadow_rect = self.rect().adjusted(shadow_margin, shadow_margin, -shadow_margin, -shadow_margin)
        
        # Background with gradient
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor("#1E1E1E"))
        gradient.setColorAt(1, QColor("#151515"))
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor("#0078D4"), 2))
        painter.drawRoundedRect(shadow_rect, 12, 12)
        
        # Content area
        cx = self.width() // 2
        content_top = shadow_margin + 30
        
        # App icon placeholder (using accent color circle)
        painter.setBrush(QBrush(QColor("#0078D4")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(cx - 30, content_top, 60, 60)
        
        # Icon letter
        font = QFont("Segoe UI", 24)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(cx - 30, content_top, 60, 60, Qt.AlignmentFlag.AlignCenter, "F")
        
        # App name
        font.setPointSize(20)
        painter.setFont(font)
        painter.setPen(QColor("#E8E8E8"))
        painter.drawText(cx - 150, content_top + 75, 300, 35, Qt.AlignmentFlag.AlignCenter, 
                        "FlatShot")
        
        # Subtitle
        font.setPointSize(10)
        font.setBold(False)
        painter.setFont(font)
        painter.setPen(QColor("#888888"))
        painter.drawText(cx - 150, content_top + 105, 300, 25, Qt.AlignmentFlag.AlignCenter, 
                        "Estandarizador de prendas en percha")
        
        # Progress bar background
        bar_y = content_top + 145
        bar_width = 260
        bar_height = 4
        painter.setBrush(QBrush(QColor("#2A2A2A")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(cx - bar_width//2, bar_y, bar_width, bar_height, 2, 2)
        
        # Progress bar fill
        fill_width = int(bar_width * (self._progress / 100))
        painter.setBrush(QBrush(QColor("#0078D4")))
        painter.drawRoundedRect(cx - bar_width//2, bar_y, fill_width, bar_height, 2, 2)
        
        # Status text
        font.setPointSize(9)
        painter.setFont(font)
        painter.setPen(QColor("#666666"))
        dots = "." * self._dots
        painter.drawText(cx - 150, bar_y + 15, 300, 25, Qt.AlignmentFlag.AlignCenter, 
                        f"{self._status_text}{dots}")
        
        # Version
        painter.setPen(QColor("#444444"))
        painter.drawText(cx - 150, self.height() - 50, 300, 20, Qt.AlignmentFlag.AlignCenter, 
                        "v1.0.0")
        
    def finish(self, main_window):
        """Finish splash and show main window after minimum display time."""
        from time import time
        elapsed = time() * 1000 - self._start_time
        remaining = max(0, self._min_display_ms - elapsed)
        
        def show_main():
            self._timer.stop()
            self.close()
            main_window.showMaximized()
        
        if remaining > 0:
            QTimer.singleShot(int(remaining), show_main)
        else:
            show_main()


class CurveGraphWidget(QWidget):
    """
    Widget for displaying the scale adjustment curve.
    Shows the relationship between aspect ratio and scale factor.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = {'xp': [0.35, 0.60, 0.85, 1.10, 1.40], 'fp': [0.98, 0.75, 0.85, 0.90, 0.95]}
        self.setMinimumHeight(120)
        self.setMaximumHeight(150)
        
    def update_data(self, curve_dict):
        self._data = curve_dict
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        margin = 40
        
        # Background
        painter.fillRect(self.rect(), QColor("#1E1E1E"))
        
        # Graph area
        graph_rect = QRectF(margin, 10, w - 2*margin, h - 30)
        painter.fillRect(graph_rect, QColor("#242424"))
        
        # Grid lines
        painter.setPen(QPen(QColor("#3A3A3A"), 1))
        for i in range(5):
            x = graph_rect.left() + (graph_rect.width() * i / 4)
            painter.drawLine(int(x), int(graph_rect.top()), int(x), int(graph_rect.bottom()))
        for i in range(3):
            y = graph_rect.top() + (graph_rect.height() * i / 2)
            painter.drawLine(int(graph_rect.left()), int(y), int(graph_rect.right()), int(y))
            
        # Draw curve
        if 'xp' in self._data and 'fp' in self._data:
            xp = self._data['xp']
            fp = self._data['fp']
            
            if len(xp) > 1 and len(fp) > 1:
                # Normalize to graph coordinates
                x_min, x_max = min(xp), max(xp)
                y_min, y_max = 0.5, 1.2
                
                points = []
                for x, y in zip(xp, fp):
                    px = graph_rect.left() + (x - x_min) / (x_max - x_min) * graph_rect.width()
                    py = graph_rect.bottom() - (y - y_min) / (y_max - y_min) * graph_rect.height()
                    points.append((int(px), int(py)))
                
                # Draw curve line
                painter.setPen(QPen(QColor("#0078D4"), 2))
                path = QPainterPath()
                if points:
                    path.moveTo(points[0][0], points[0][1])
                    for px, py in points[1:]:
                        path.lineTo(px, py)
                    painter.drawPath(path)
                
                # Draw points
                painter.setBrush(QBrush(QColor("#0078D4")))
                painter.setPen(Qt.PenStyle.NoPen)
                for px, py in points:
                    painter.drawEllipse(QPoint(px, py), 4, 4)
                    
        # Axis labels
        font = QFont("Segoe UI", 8)
        painter.setFont(font)
        painter.setPen(QColor("#888888"))
        
        # X-axis label
        painter.drawText(int(w/2 - 40), int(h - 5), "Aspect Ratio →")
        
        # Y-axis label (scale factor)
        painter.save()
        painter.translate(15, h/2 + 30)
        painter.rotate(-90)
        painter.drawText(0, 0, "Scale Factor →")
        painter.restore()

