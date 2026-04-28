"""
Custom Widgets for Modern UI
"""
import math
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSlider, QSpinBox,
    QFrame, QPushButton, QSizePolicy, QGraphicsDropShadowEffect, QToolButton,
    QButtonGroup, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QPointF, QRectF, QTimer, QEvent, QSize
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QRadialGradient, 
    QLinearGradient, QFont, QPainterPath, QPixmap, QImage
)
from PIL import Image
import qtawesome as qta
from flatshot.ui.styles import COLORS


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
        layout.setContentsMargins(0, self._px(4), 0, self._px(4))
        layout.setSpacing(self._px(8))
        
        # Label
        self.label = QLabel(label)
        self.label.setProperty("class", "param-label")
        self.label.setMinimumWidth(self._px(120))
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
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
        self.slider.setMinimumWidth(self._px(40))
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
        self.spinbox.setMinimumWidth(self._px(46))
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
        outer.setContentsMargins(self._px(2), self._px(2), self._px(2), self._px(2))
        outer.setSpacing(0)

        self._header = QFrame()
        self._header.setProperty("class", "section-header")
        self._header.setCursor(Qt.CursorShape.PointingHandCursor)
        self._header.setFixedHeight(self._px(28))
        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(self._px(8), self._px(5), self._px(8), self._px(5))
        header_layout.setSpacing(self._px(8))

        self._toggle_btn = QToolButton()
        self._toggle_btn.setProperty("class", "section-arrow")
        self._toggle_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self._toggle_btn.setCheckable(False)
        icon_color = "#AEB4BE"
        self._icon_expanded = qta.icon('fa5s.chevron-down', color=icon_color)
        self._icon_collapsed = qta.icon('fa5s.chevron-right', color=icon_color)
        self._toggle_btn.setIcon(self._icon_expanded if self._expanded else self._icon_collapsed)
        self._toggle_btn.setIconSize(QSize(self._px(10), self._px(10)))
        self._toggle_btn.setFixedSize(self._px(20), self._px(20))
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_btn.clicked.connect(self._on_toggled)
        header_layout.addWidget(self._toggle_btn, 0, Qt.AlignmentFlag.AlignLeft)

        self._title_label = QLabel(self._title)
        self._title_label.setProperty("class", "section-title")
        self._title_label.setCursor(Qt.CursorShape.PointingHandCursor)
        header_layout.addWidget(self._title_label, 1)
        outer.addWidget(self._header)

        self._content = QWidget()
        self._content.setProperty("class", "section-content")
        self._content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(self._px(8), self._px(6), self._px(8), self._px(8))
        self._content_layout.setSpacing(self._px(6))
        outer.addWidget(self._content)

        self.setExpanded(self._expanded, emit_signal=False)
        self._header.mousePressEvent = self._on_header_clicked
        self._title_label.mousePressEvent = self._on_header_clicked

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

    def _on_header_clicked(self, event):
        if event is None:
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self._on_toggled()
            event.accept()
        else:
            event.ignore()

    def sizeHint(self) -> QSize:
        base = super().sizeHint()
        if self._expanded:
            return base
        header_h = self._header.sizeHint().height() + self._px(4)
        return QSize(base.width(), header_h)

    def minimumSizeHint(self) -> QSize:
        base = super().minimumSizeHint()
        if self._expanded:
            return base
        header_h = self._header.sizeHint().height() + self._px(4)
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
        glow_pen = QPen(QColor(COLORS['accent_primary']))
        glow_pen.setWidth(self._px(6))
        glow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setOpacity(0.3)
        painter.setPen(glow_pen)
        painter.drawLine(cx, cy, int(end_x), int(end_y))
        
        # Main indicator line
        painter.setOpacity(1.0)
        indicator_pen = QPen(QColor(COLORS['accent_primary']))
        indicator_pen.setWidth(self._px(3))
        indicator_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(indicator_pen)
        painter.drawLine(cx, cy, int(end_x), int(end_y))
        
        # Indicator dot at end
        painter.setBrush(QBrush(QColor(COLORS['accent_primary'])))
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
        painter.setPen(QColor(COLORS['text_muted']))
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
        self._guide_preset = "thirds"
        self._guide_color = QColor(255, 255, 255)
        self._guide_opacity = 42
        self._badge_opacity = 1.0  # For fade effect
        self._zoom_level = 1.0  # Zoom support
        self._pan_offset = QPointF(0, 0)
        self._panning = False
        self._last_pan_pos = QPointF(0, 0)
        
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
        self._reset_view_if_needed()
        self.update()
        
    def setProcessedImage(self, image: QPixmap):
        self._processed_image = image
        self._reset_view_if_needed()
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

    def setGuideSettings(self, settings: dict):
        self._guide_preset = settings.get("preset", self._guide_preset)
        self._guide_color = QColor(settings.get("color", self._guide_color.name()))
        self._guide_opacity = int(settings.get("opacity", self._guide_opacity))
        self.update()
        
    def setComparisonMode(self, mode: str):
        self._comparison_mode = mode
        self.update()

    def resetView(self):
        self._zoom_level = 1.0
        self._pan_offset = QPointF(0, 0)
        self.update()

    def _reset_view_if_needed(self):
        if self._zoom_level <= 1.01:
            self._pan_offset = QPointF(0, 0)
        
    def wheelEvent(self, event):
        """Zoom around the cursor so inspection stays anchored."""
        current_image = self._original_image if self._show_original else self._processed_image
        if not current_image or current_image.isNull():
            return

        old_rect = self._image_rect(current_image, self._zoom_level, self._pan_offset)
        if old_rect.width() <= 0 or old_rect.height() <= 0:
            return

        cursor = event.position()
        rel_x = min(max((cursor.x() - old_rect.x()) / old_rect.width(), 0.0), 1.0)
        rel_y = min(max((cursor.y() - old_rect.y()) / old_rect.height(), 0.0), 1.0)

        factor = 1.12 if event.angleDelta().y() > 0 else 1 / 1.12
        self._zoom_level = min(6.0, max(1.0, self._zoom_level * factor))
        new_rect = self._image_rect(current_image, self._zoom_level, self._pan_offset)

        desired_x = cursor.x() - (new_rect.width() * rel_x)
        desired_y = cursor.y() - (new_rect.height() * rel_y)
        centered_x = (self.width() - new_rect.width()) / 2
        centered_y = (self.height() - new_rect.height()) / 2
        self._pan_offset = QPointF(desired_x - centered_x, desired_y - centered_y)
        self._clamp_pan(current_image)
        self.update()
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._zoom_level > 1.01:
            self._panning = True
            self._last_pan_pos = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning:
            delta = event.position() - self._last_pan_pos
            self._last_pan_pos = event.position()
            self._pan_offset += delta
            current_image = self._original_image if self._show_original else self._processed_image
            if current_image and not current_image.isNull():
                self._clamp_pan(current_image)
            self.update()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._panning:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.resetView()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # Background
        painter.fillRect(self.rect(), self._bg_color)
        
        # Image
        current_image = self._original_image if self._show_original else self._processed_image
        
        if current_image and not current_image.isNull():
            image_rect = self._image_rect(current_image, self._zoom_level, self._pan_offset)
            painter.drawPixmap(image_rect, current_image, QRectF(current_image.rect()))
            
            # Zoom indicator (if not 100%)
            if abs(self._zoom_level - 1.0) > 0.01:
                self._draw_zoom_indicator(painter)
            
            # A/B indicator
            if self._show_original:
                self._draw_indicator(painter, "ORIGINAL", QColor("#FF9800"))
            else:
                self._draw_indicator(painter, "PROCESADA", QColor(COLORS['success']))
            
            # Grid overlay (drawn OVER the image)
            if self._grid_visible:
                self._draw_grid(painter, image_rect)
        else:
            # Placeholder
            self._draw_placeholder(painter)

    def _image_rect(self, image: QPixmap, zoom_level: float, pan_offset: QPointF) -> QRectF:
        if not image or image.isNull():
            return QRectF()
        fit_scale = min(self.width() / image.width(), self.height() / image.height())
        draw_w = image.width() * fit_scale * zoom_level
        draw_h = image.height() * fit_scale * zoom_level
        x = (self.width() - draw_w) / 2 + pan_offset.x()
        y = (self.height() - draw_h) / 2 + pan_offset.y()
        return QRectF(x, y, draw_w, draw_h)

    def _clamp_pan(self, image: QPixmap):
        if not image or image.isNull():
            return
        rect = self._image_rect(image, self._zoom_level, self._pan_offset)

        def clamp_axis(rect_start, rect_size, viewport_size, current):
            if rect_size <= viewport_size:
                return current - rect_start + (viewport_size - rect_size) / 2
            min_start = viewport_size - rect_size
            max_start = 0
            if rect_start < min_start:
                return current + (min_start - rect_start)
            if rect_start > max_start:
                return current - rect_start
            return current

        self._pan_offset = QPointF(
            clamp_axis(rect.x(), rect.width(), self.width(), self._pan_offset.x()),
            clamp_axis(rect.y(), rect.height(), self.height(), self._pan_offset.y()),
        )
            
    def _draw_grid(self, painter, rect: QRectF):
        """Draw configurable composition guides over the preview image."""
        if rect.isEmpty():
            return
        
        color = QColor(self._guide_color)
        color.setAlpha(max(20, min(220, int(self._guide_opacity * 2.55))))
        pen = QPen(color)
        pen.setWidth(1)
        painter.setPen(pen)

        preset = self._guide_preset
        if preset in ("thirds", "full"):
            for factor in (1 / 3, 2 / 3):
                x = rect.left() + rect.width() * factor
                y = rect.top() + rect.height() * factor
                painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
                painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))

        if preset in ("center", "full"):
            center_pen = QPen(color)
            center_pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(center_pen)
            cx = rect.center().x()
            cy = rect.center().y()
            painter.drawLine(QPointF(cx, rect.top()), QPointF(cx, rect.bottom()))
            painter.drawLine(QPointF(rect.left(), cy), QPointF(rect.right(), cy))

        if preset == "margins":
            for factor in (0.1, 0.9):
                x = rect.left() + rect.width() * factor
                y = rect.top() + rect.height() * factor
                painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
                painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))

        if preset == "grid":
            for factor in (0.25, 0.5, 0.75):
                x = rect.left() + rect.width() * factor
                y = rect.top() + rect.height() * factor
                painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
                painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
            
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
        painter.setPen(QColor(COLORS['text_muted']))
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
    Inline toolbar for canvas controls (guides + canvas background).
    Designed to be embedded in a parent horizontal layout.
    """
    gridToggled = pyqtSignal(bool)
    zoomChanged = pyqtSignal(int)
    bgColorChanged = pyqtSignal(str)
    guideSettingsChanged = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "floating-toolbar-inline")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._guide_settings = {
            "preset": "thirds",
            "color": "#FFFFFF",
            "opacity": 42,
        }
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # --- Guides section ---
        guide_label = QLabel("Guías")
        guide_label.setProperty("class", "toolbar-section-label")
        layout.addWidget(guide_label, 0, Qt.AlignmentFlag.AlignVCenter)

        self.btn_grid = QPushButton(qta.icon('fa5s.th-large', color=COLORS['text_secondary']), "")
        self.btn_grid.setProperty("class", "icon-btn")
        self.btn_grid.setCheckable(True)
        self.btn_grid.setToolTip("Mostrar u ocultar guías de composición")
        self.btn_grid.toggled.connect(self._on_grid_toggled)
        layout.addWidget(self.btn_grid, 0, Qt.AlignmentFlag.AlignVCenter)

        self.cmb_guides = QComboBox()
        self.cmb_guides.setProperty("class", "toolbar-combo")
        self.cmb_guides.setFixedWidth(100)
        self.cmb_guides.setToolTip("Preset de guías")
        for text, value in [
            ("Tercios", "thirds"),
            ("Centro", "center"),
            ("Margen 10%", "margins"),
            ("Cuadrícula", "grid"),
            ("Completo", "full"),
        ]:
            self.cmb_guides.addItem(text, value)
        self.cmb_guides.currentIndexChanged.connect(self._emit_guide_settings)
        layout.addWidget(self.cmb_guides, 0, Qt.AlignmentFlag.AlignVCenter)

        self.guide_opacity = QSlider(Qt.Orientation.Horizontal)
        self.guide_opacity.setProperty("class", "toolbar-slider")
        self.guide_opacity.setRange(15, 90)
        self.guide_opacity.setValue(self._guide_settings["opacity"])
        self.guide_opacity.setFixedWidth(60)
        self.guide_opacity.setToolTip("Transparencia de las guías")
        self.guide_opacity.valueChanged.connect(self._emit_guide_settings)
        layout.addWidget(self.guide_opacity, 0, Qt.AlignmentFlag.AlignVCenter)

        self._guide_buttons = []
        for color, name in [("#FFFFFF", "Blanco"), ("#0A84FF", "Azul"), ("#FF9F0A", "Ámbar")]:
            btn = QPushButton()
            btn.setProperty("class", "mini-swatch")
            btn.setCheckable(True)
            btn.setFixedSize(18, 18)
            btn.setToolTip(f"Guía {name}")
            btn.clicked.connect(lambda checked, c=color: self._select_guide_color(c))
            layout.addWidget(btn, 0, Qt.AlignmentFlag.AlignVCenter)
            self._guide_buttons.append((btn, color))
        self._select_guide_color(self._guide_settings["color"], emit=False)

        # --- Divider ---
        divider = QFrame()
        divider.setProperty("class", "toolbar-separator-v")
        divider.setFixedSize(1, 20)
        layout.addWidget(divider)

        # --- Canvas background section ---
        bg_label = QLabel("Canvas")
        bg_label.setProperty("class", "toolbar-section-label")
        layout.addWidget(bg_label, 0, Qt.AlignmentFlag.AlignVCenter)

        self._bg_group = QButtonGroup(self)
        self._bg_group.setExclusive(True)
        self._bg_buttons = []
        for i, (color, text, name) in enumerate([
            ("#FFFFFF", "Claro", "Fondo blanco"),
            ("#E6E6E6", "Neutro", "Fondo gris"),
            ("#2A2A2A", "Oscuro", "Fondo oscuro"),
        ]):
            seg_class = "segment-left" if i == 0 else ("segment-right" if i == 2 else "segment-middle")
            btn = QPushButton(text)
            btn.setProperty("class", seg_class)
            btn.setCheckable(True)
            btn.setToolTip(name)
            btn.clicked.connect(lambda checked, c=color: self._select_background(c))
            self._bg_group.addButton(btn)
            layout.addWidget(btn, 0, Qt.AlignmentFlag.AlignVCenter)
            self._bg_buttons.append((btn, color))

        # Default selection
        self._select_background("#E6E6E6", emit=False)
    
    def _on_grid_toggled(self, checked: bool):
        """Handle grid button toggle with visual feedback."""
        self.gridToggled.emit(checked)
        self._emit_guide_settings()

    def _select_guide_color(self, color: str, emit: bool = True):
        self._guide_settings["color"] = color
        for btn, value in getattr(self, "_guide_buttons", []):
            btn.setChecked(value == color)
            border = COLORS['accent_primary'] if value == color else COLORS['border']
            btn.setStyleSheet(f"background-color: {value}; border: 1px solid {border};")
        if emit:
            self._emit_guide_settings()

    def _emit_guide_settings(self):
        if hasattr(self, "cmb_guides"):
            self._guide_settings["preset"] = self.cmb_guides.currentData()
        if hasattr(self, "guide_opacity"):
            self._guide_settings["opacity"] = self.guide_opacity.value()
        self.guideSettingsChanged.emit(dict(self._guide_settings))

    def _select_background(self, color: str, emit: bool = True):
        for btn, value in getattr(self, "_bg_buttons", []):
            btn.setChecked(value == color)
        if emit:
            self.bgColorChanged.emit(color)

    def _background_button_style(self, color: str, selected: bool) -> str:
        text_color = "#111318" if color.upper() in {"#FFFFFF", "#E6E6E6"} else COLORS['text_primary']
        border_color = COLORS['accent_primary'] if selected else COLORS['border']
        border_width = 2 if selected else 1
        return (
            f"QPushButton {{ background-color: {color}; color: {text_color}; "
            f"border: {border_width}px solid {border_color}; border-radius: 7px; "
            "padding: 2px 8px; font-size: 11px; font-weight: 700; }}"
            f"QPushButton:hover {{ border: 2px solid {COLORS['accent_hover']}; }}"
        )

    def set_background(self, color: str, emit: bool = False):
        self._select_background(color, emit=emit)

    def set_grid_enabled(self, enabled: bool, emit: bool = False):
        self.btn_grid.blockSignals(not emit)
        self.btn_grid.setChecked(bool(enabled))
        self.btn_grid.blockSignals(False)

    def set_guide_settings(self, settings: dict, emit: bool = False):
        self._guide_settings.update(settings or {})
        preset = self._guide_settings.get("preset", "thirds")
        index = self.cmb_guides.findData(preset)
        if index >= 0:
            self.cmb_guides.blockSignals(True)
            self.cmb_guides.setCurrentIndex(index)
            self.cmb_guides.blockSignals(False)

        self.guide_opacity.blockSignals(True)
        self.guide_opacity.setValue(int(self._guide_settings.get("opacity", 42)))
        self.guide_opacity.blockSignals(False)
        self._select_guide_color(self._guide_settings.get("color", "#FFFFFF"), emit=False)
        if emit:
            self._emit_guide_settings()


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
        painter.setPen(QPen(QColor(COLORS['accent_primary']), 2))
        painter.drawRoundedRect(shadow_rect, 12, 12)
        
        # Content area
        cx = self.width() // 2
        content_top = shadow_margin + 30
        
        # App icon placeholder (using accent color circle)
        painter.setBrush(QBrush(QColor(COLORS['accent_primary'])))
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
        painter.setBrush(QBrush(QColor(COLORS['accent_primary'])))
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
                painter.setPen(QPen(QColor(COLORS['accent_primary']), 2))
                path = QPainterPath()
                if points:
                    path.moveTo(points[0][0], points[0][1])
                    for px, py in points[1:]:
                        path.lineTo(px, py)
                    painter.drawPath(path)
                
                # Draw points
                painter.setBrush(QBrush(QColor(COLORS['accent_primary'])))
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

