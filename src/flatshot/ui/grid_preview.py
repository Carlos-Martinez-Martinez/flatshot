"""
Grid Preview Widget for FlatShot
Displays multiple image previews in a grid layout with lazy loading.
"""
from pathlib import Path
from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QSizePolicy, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize, QRunnable, QThreadPool, QObject, QEvent
from PyQt6.QtGui import QPixmap, QImage
from PIL import Image

from flatshot.core.engine import ShadowEngine
from flatshot.core.models import (
    CurveData,
    SHADOW_ENGINE_DEFAULT,
    ShadowSettings,
    normalize_shadow_settings,
)
from flatshot.core.overrides import apply_image_override, has_image_override, override_key


def _render_tile_preview(
    image_path: str,
    settings_dict: dict,
    curve_dict: dict,
    preview_size: tuple[int, int],
):
    """Render a grid tile preview off the UI thread."""
    settings = normalize_shadow_settings(
        settings_dict,
        missing_engine=SHADOW_ENGINE_DEFAULT,
    )
    curve_data = CurveData(**curve_dict) if curve_dict else None

    with Image.open(image_path) as pil_img:
        pil_img = pil_img.convert("RGBA")

        processed_pil = ShadowEngine.aplicar_efectos(
            pil_img,
            settings,
            preview_size,
            scale_factor=0.1,
            curve_data=curve_data,
            is_preview=True,
        )

        def _to_rgb_payload(pil_image: Image.Image):
            if pil_image.mode == "RGBA":
                bg = Image.new("RGB", pil_image.size, settings.bg_color)
                bg.paste(pil_image, (0, 0), mask=pil_image)
                pil_image = bg
            pil_image = pil_image.convert("RGB")
            return pil_image.width, pil_image.height, pil_image.tobytes("raw", "RGB")

        processed_payload = _to_rgb_payload(processed_pil)

        small_orig = pil_img.copy()
        small_orig.thumbnail((preview_size[0], preview_size[1]))
        original_payload = _to_rgb_payload(small_orig)

    return processed_payload, original_payload


class TileRenderSignals(QObject):
    finished = pyqtSignal(int, int, object)  # tile_index, generation, payload
    error = pyqtSignal(int, int, str)        # tile_index, generation, error


class TileRenderWorker(QRunnable):
    def __init__(
        self,
        tile_index: int,
        generation: int,
        image_path: str,
        settings_dict: dict,
        curve_dict: dict,
        preview_size: tuple[int, int],
    ):
        super().__init__()
        self.tile_index = tile_index
        self.generation = generation
        self.image_path = image_path
        self.settings_dict = settings_dict
        self.curve_dict = curve_dict
        self.preview_size = preview_size
        self.signals = TileRenderSignals()
        self.setAutoDelete(False)

    def run(self):
        try:
            payload = _render_tile_preview(
                self.image_path,
                self.settings_dict,
                self.curve_dict,
                self.preview_size,
            )
            self.signals.finished.emit(self.tile_index, self.generation, payload)
        except Exception as exc:
            self.signals.error.emit(self.tile_index, self.generation, str(exc))


class PreviewTile(QFrame):
    """Single preview tile in the grid."""
    
    clicked = pyqtSignal(str)  # Emits file path when clicked
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_path: Optional[str] = None
        self._original_image: Optional[QPixmap] = None
        self._processed_image: Optional[QPixmap] = None
        self._show_original = False
        self._is_loaded = False  # Track if image has been processed
        self._has_override = False
        self._status_key = "processing"
        
        self.setProperty("class", "preview-tile")
        self._tile_width = 150
        self._image_height = 200
        self._label_height = 30
        self._apply_size()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 6)
        layout.setSpacing(4)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.image_label)
        
        meta_row = QWidget()
        meta_layout = QHBoxLayout(meta_row)
        meta_layout.setContentsMargins(2, 0, 2, 0)
        meta_layout.setSpacing(6)

        self.name_label = QLabel()
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.name_label.setProperty("class", "preview-label")
        self.name_label.setWordWrap(False)
        self.name_label.setMinimumHeight(22)
        meta_layout.addWidget(self.name_label, 1)

        self.status_label = QLabel("...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setProperty("class", "tile-status-processing")
        self.status_label.setMinimumWidth(42)
        meta_layout.addWidget(self.status_label, 0)
        layout.addWidget(meta_row)

    def _apply_size(self):
        # Account for layout margins + spacing (top/bottom + inter-item spacing).
        total_height = self._image_height + self._label_height + 16
        self.setFixedSize(self._tile_width, total_height)
        if hasattr(self, "image_label"):
            self.image_label.setMinimumHeight(self._image_height)

    def set_tile_size(self, width: int, image_height: int):
        self._tile_width = max(int(width), 80)
        self._image_height = max(int(image_height), 80)
        # Keep label height proportional but readable
        self._label_height = max(int(self._image_height * 0.22), 30)
        self._apply_size()
        if self.file_path:
            self._set_label_text(self.file_path)
        self._update_display()
    
    def set_image(self, file_path: str, processed: QPixmap, original: QPixmap = None):
        """Set the images for this tile."""
        self.file_path = file_path
        self._processed_image = processed
        self._original_image = original or processed
        self._is_loaded = True
        self._set_label_text(file_path)
        self.set_status("adjusted" if self._has_override else "ok")
        suffix = "\nAjuste local aplicado" if self._has_override else ""
        self.setToolTip(f"{file_path}{suffix}")
        self._update_display()

    def set_override_active(self, active: bool):
        self._has_override = bool(active)
        if self.file_path:
            self._set_label_text(self.file_path)
            suffix = "\nAjuste local aplicado" if self._has_override else ""
            self.setToolTip(f"{self.file_path}{suffix}")
        if self._status_key not in ("processing", "error"):
            self.set_status("adjusted" if self._has_override else "ok")

    def set_status(self, status: str):
        labels = {
            "ok": "OK",
            "adjusted": "Ajustada",
            "error": "Error",
            "processing": "...",
        }
        status = status if status in labels else "ok"
        self._status_key = status
        self.status_label.setText(labels[status])
        self.status_label.setProperty("class", f"tile-status-{status}")
        try:
            self.status_label.style().unpolish(self.status_label)
            self.status_label.style().polish(self.status_label)
        except Exception:
            pass

    def set_error(self, message: str):
        self._is_loaded = False
        self.image_label.setText("Error")
        self.name_label.setText(f"Error: {message[:24]}")
        self.set_status("error")
    
    def _update_display(self):
        """Update the displayed image."""
        img = self._original_image if self._show_original else self._processed_image
        if img:
            scaled = img.scaled(
                self.image_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled)
    
    def set_loading(self):
        """Show loading state."""
        self.image_label.setText("...")
        self._is_loaded = False
        self.set_status("processing")
    
    def set_pending(self, file_path: str):
        """Set pending state with filename but no image yet."""
        self.file_path = file_path
        self._set_label_text(file_path)
        self.image_label.setText("...")
        self._is_loaded = False
        self.set_status("processing")
        suffix = "\nAjuste local aplicado" if self._has_override else ""
        self.setToolTip(f"{file_path}{suffix}")

    def _set_label_text(self, file_path: str):
        text = Path(file_path).stem
        if self._has_override:
            text = f"● {text}"
        metrics = self.name_label.fontMetrics()
        max_width = max(self._tile_width - 12, 60)
        elided = metrics.elidedText(text, Qt.TextElideMode.ElideRight, max_width)
        self.name_label.setText(elided)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.file_path:
            self.clicked.emit(self.file_path)
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self._show_original = True
            self._update_display()
    
    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self._show_original = False
            self._update_display()
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._is_loaded:
            self._update_display()


class GridPreviewWidget(QWidget):
    """Grid of image previews with lazy loading."""
    
    image_selected = pyqtSignal(str)  # Emits file path when image is clicked
    folder_empty = pyqtSignal()  # Emits when folder has no valid images
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.folder_path: Optional[str] = None
        self.settings: Optional[ShadowSettings] = None
        self.curve_data: Optional[CurveData] = None
        self.image_overrides: dict[str, dict] = {}
        self._tiles: List[PreviewTile] = []
        self._images: List[Path] = []
        self._render_generation = 0
        self._completed_tiles = 0
        self._active_workers = set()
        self._pool = QThreadPool()
        self._pool.setMaxThreadCount(2)
        self._thumb_width = 150
        self._thumb_height = 200
        self._tile_spacing = 10
        self._fixed_columns = 1
        self._columns = 1
        self._grid_margins = (10, 10, 14, 12)
        self._folder_label = ""
        self._status_text = ""
        self._status_include_folder = True
        self._filter_mode = "all"
        
        # Chunked loading
        self._current_chunk = 0
        # Keep chunks small to avoid blocking the UI thread with heavy settings.
        self._chunk_size = 1
        self._chunk_timer = QTimer()
        self._chunk_timer.setSingleShot(True)
        self._chunk_timer.timeout.connect(self._process_next_chunk)
        
        # Debounce timer for settings updates
        self._update_timer = QTimer()
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._start_update_previews)

        # Debounce timer for grid reflow
        self._reflow_timer = QTimer()
        self._reflow_timer.setSingleShot(True)
        self._reflow_timer.timeout.connect(self._reflow_tiles)
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll area for grid
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setProperty("class", "preview-scroll")
        self.scroll.viewport().installEventFilter(self)
        
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(self._tile_spacing)
        self.grid_layout.setContentsMargins(*self._grid_margins)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        self.scroll.setWidget(self.grid_container)
        layout.addWidget(self.scroll)
        
        # Info label
        self.info_label = QLabel("Selecciona una carpeta para ver previews")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setProperty("class", "help-text")
        self.info_label.setMinimumHeight(22)
        layout.addWidget(self.info_label)

    def set_folder_label(self, label: str):
        """Set a human-readable folder label for the status bar."""
        self._folder_label = label or ""
        if self._status_text:
            self._set_status(self._status_text, include_folder=self._status_include_folder)
        elif self._folder_label:
            self._set_status("", include_folder=True)

    def _set_status(self, status: str, include_folder: bool = True):
        self._status_text = status
        self._status_include_folder = include_folder
        if include_folder and self._folder_label:
            text = f"{self._folder_label} · {status}" if status else self._folder_label
        else:
            text = status
        self.info_label.setText(text)
    
    def _clear_tiles(self):
        """Remove all tiles from the grid."""
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._tiles.clear()
    
    def _create_tiles_for_images(self):
        """Create exactly as many tiles as there are images."""
        # Clear existing tiles
        self._clear_tiles()
        
        # Create a tile for each image
        for i, img_path in enumerate(self._images):
            tile = PreviewTile()
            tile.clicked.connect(self.image_selected.emit)
            tile.set_override_active(self._image_has_override(str(img_path)))
            tile.set_pending(str(img_path))
            tile.set_tile_size(self._thumb_width, self._thumb_height)
            self._tiles.append(tile)
        
        self._reflow_tiles()
    
    def set_folder(self, folder_path: str):
        """Set the folder to preview images from."""
        self.folder_path = folder_path
        self._load_images()
    
    def set_settings(self, settings: ShadowSettings, curve_data: CurveData):
        """Update the shadow settings and trigger refresh."""
        self.settings = settings
        self.curve_data = curve_data
        # Only update if we have images
        if self._images:
            self._schedule_update()

    def set_image_overrides(self, overrides: dict | None):
        """Update per-image local adjustments and refresh affected previews."""
        incoming = dict(overrides or {})
        changed = incoming != self.image_overrides
        self.image_overrides = incoming
        for i, tile in enumerate(self._tiles):
            if i < len(self._images):
                tile.set_override_active(self._image_has_override(str(self._images[i])))
        if changed and self._images and self.settings:
            self._schedule_update()
        self._reflow_tiles()

    def set_filter_mode(self, mode: str):
        """Filter visible tiles by batch state."""
        mode = mode if mode in ("all", "adjusted", "error") else "all"
        if mode == self._filter_mode:
            return
        self._filter_mode = mode
        self._reflow_tiles()

    def _override_for_path(self, path: str) -> dict:
        return self.image_overrides.get(override_key(path), {})

    def _image_has_override(self, path: str) -> bool:
        return has_image_override(self._override_for_path(path))
    
    def _load_images(self):
        """Load image paths from the folder."""
        # Cancel any ongoing processing
        self._chunk_timer.stop()
        self._update_timer.stop()
        self._render_generation += 1
        
        if not self.folder_path:
            self._images = []
            self._clear_tiles()
            self._set_status("Selecciona una carpeta para ver previews", include_folder=False)
            self.folder_empty.emit()
            return
        
        folder = Path(self.folder_path)
        self._images = sorted(folder.glob("*.png"))
        
        if not self._images:
            self._clear_tiles()
            self._set_status("No se encontraron imágenes PNG")
            self.folder_empty.emit()  # Notify parent to show placeholder
        else:
            self._set_status(f"Cargando {len(self._images)} imágenes...")
            # Create tiles for all images
            self._create_tiles_for_images()
            self._schedule_update()
    
    def _schedule_update(self):
        """Schedule a debounced preview update."""
        self._chunk_timer.stop()  # Cancel any ongoing chunk processing
        self._update_timer.start(300)
    
    def _start_update_previews(self):
        """Start the chunked update process."""
        if not self.settings or not self._images:
            if not self._images:
                self._set_status("No se encontraron imágenes PNG")
            return
        self._render_generation += 1
        self._completed_tiles = 0
        
        # Reset all tiles to pending state
        for i, tile in enumerate(self._tiles):
            if i < len(self._images):
                tile.set_override_active(self._image_has_override(str(self._images[i])))
                tile.set_pending(str(self._images[i]))
        
        # Start processing from beginning
        self._current_chunk = 0
        self._process_next_chunk()
    
    def _process_next_chunk(self):
        """Process the next chunk of images."""
        if not self.settings:
            return
        
        start = self._current_chunk * self._chunk_size
        end = min(start + self._chunk_size, len(self._images))
        
        if start >= len(self._images):
            if self._completed_tiles >= len(self._images):
                self._set_status(f"Mostrando {len(self._images)} imágenes")
            return
        
        preview_size = (self._thumb_width, self._thumb_height)
        generation = self._render_generation
        curve_dict = self.curve_data.model_dump() if self.curve_data else None
        
        for i in range(start, end):
            if i >= len(self._tiles):
                break

            image_path = str(self._images[i])
            effective_settings = apply_image_override(
                self.settings,
                self._override_for_path(image_path),
            )

            worker = TileRenderWorker(
                tile_index=i,
                generation=generation,
                image_path=image_path,
                settings_dict=effective_settings.model_dump(),
                curve_dict=curve_dict,
                preview_size=preview_size,
            )
            self._active_workers.add(worker)
            worker.signals.finished.connect(
                lambda tile_idx, gen, payload, w=worker: self._on_tile_rendered(w, tile_idx, gen, payload)
            )
            worker.signals.error.connect(
                lambda tile_idx, gen, msg, w=worker: self._on_tile_error(w, tile_idx, gen, msg)
            )
            self._pool.start(worker)
        
        # Update progress
        processed = min(end, len(self._images))
        
        # Schedule next chunk or show final message
        self._current_chunk += 1
        if end < len(self._images):
            self._set_status(f"Procesando... {processed}/{len(self._images)}")
            self._chunk_timer.start(20)
        elif self._completed_tiles >= len(self._images):
            self._set_status(f"Mostrando {len(self._images)} imágenes")

    def _on_tile_rendered(self, worker: TileRenderWorker, tile_index: int, generation: int, payload):
        self._active_workers.discard(worker)
        if generation != self._render_generation:
            return
        if tile_index < 0 or tile_index >= len(self._tiles) or tile_index >= len(self._images):
            return

        processed_payload, original_payload = payload
        processed_qpixmap = self._payload_to_qpixmap(processed_payload)
        original_qpixmap = self._payload_to_qpixmap(original_payload)
        self._tiles[tile_index].set_override_active(
            self._image_has_override(str(self._images[tile_index]))
        )
        self._tiles[tile_index].set_image(str(self._images[tile_index]), processed_qpixmap, original_qpixmap)
        if self._filter_mode != "all":
            self._reflow_tiles()

        self._completed_tiles += 1
        if self._completed_tiles >= len(self._images):
            self._set_status(f"Mostrando {len(self._images)} imágenes")
        else:
            self._set_status(f"Generando... {self._completed_tiles}/{len(self._images)}")

    def _on_tile_error(self, worker: TileRenderWorker, tile_index: int, generation: int, message: str):
        self._active_workers.discard(worker)
        if generation != self._render_generation:
            return
        if 0 <= tile_index < len(self._tiles):
            self._tiles[tile_index].set_error(message)
            self._reflow_tiles()

        self._completed_tiles += 1
        if self._completed_tiles >= len(self._images):
            self._set_status(f"Mostrando {len(self._images)} imágenes")

    def _payload_to_qpixmap(self, payload) -> QPixmap:
        width, height, data = payload
        qim = QImage(data, width, height, width * 3, QImage.Format.Format_RGB888)
        return QPixmap.fromImage(qim.copy())
    
    def _pil_to_qpixmap(self, pil_image: Image.Image) -> QPixmap:
        """Convert PIL Image to QPixmap."""
        if pil_image.mode == 'RGBA':
            # Composite on gray background
            bg = Image.new("RGB", pil_image.size, (230, 230, 230))
            bg.paste(pil_image, (0, 0), mask=pil_image)
            pil_image = bg
        
        pil_image = pil_image.convert("RGB")
        data = pil_image.tobytes("raw", "RGB")
        qim = QImage(data, pil_image.width, pil_image.height, pil_image.width * 3, QImage.Format.Format_RGB888)
        return QPixmap.fromImage(qim.copy())
    
    def refresh(self):
        """Force refresh all previews."""
        self._schedule_update()

    def is_busy(self) -> bool:
        """Return whether the grid is actively rendering or scheduled to render."""
        return (
            self._pool.activeThreadCount() > 0
            or self._chunk_timer.isActive()
            or self._update_timer.isActive()
            or self._reflow_timer.isActive()
        )

    def set_fixed_columns(self, columns: int):
        """Set fixed column count (1-3)."""
        columns = max(int(columns), 1)
        self._fixed_columns = min(columns, 3)
        self._reflow_tiles()

    def _calculate_columns(self) -> int:
        if len(self._images) <= 1:
            return 1
        return max(1, self._fixed_columns)

    def _compute_tile_size(self, columns: int) -> tuple[int, int]:
        if not self.scroll or not self.scroll.viewport():
            return self._thumb_width, self._thumb_height
        viewport_width = self.scroll.viewport().width()
        left, top, right, bottom = self._grid_margins
        usable = max(viewport_width - left - right - self._tile_spacing * (columns - 1), 130)
        tile_width = max(int(usable / max(columns, 1)), 90)
        tile_height = int(round(tile_width * 4 / 3))
        return tile_width, tile_height

    def _reflow_tiles(self):
        if not self._tiles:
            return
        columns = self._calculate_columns()
        self._columns = max(columns, 1)
        new_width, new_height = self._compute_tile_size(self._columns)
        size_changed = new_width != self._thumb_width or new_height != self._thumb_height
        if size_changed:
            self._thumb_width = new_width
            self._thumb_height = new_height
            for tile in self._tiles:
                tile.set_tile_size(self._thumb_width, self._thumb_height)
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                self.grid_layout.removeWidget(widget)
        visible_idx = 0
        for tile in self._tiles:
            if not self._tile_matches_filter(tile):
                tile.hide()
                continue
            tile.show()
            row = visible_idx // self._columns
            col = visible_idx % self._columns
            self.grid_layout.addWidget(tile, row, col)
            visible_idx += 1
        self.grid_container.adjustSize()
        if size_changed and self._images:
            self._schedule_update()

    def _tile_matches_filter(self, tile: PreviewTile) -> bool:
        if self._filter_mode == "adjusted":
            return bool(tile._has_override)
        if self._filter_mode == "error":
            return tile._status_key == "error"
        return True

    def eventFilter(self, watched, event):
        if watched == self.scroll.viewport() and event.type() == QEvent.Type.Resize:
            self._reflow_timer.start(30)
        return super().eventFilter(watched, event)

    def closeEvent(self, event):
        """Stop background workers/timers cleanly on widget teardown."""
        self._chunk_timer.stop()
        self._update_timer.stop()
        self._render_generation += 1  # Invalidate pending callbacks.
        self._active_workers.clear()
        self._pool.clear()
        self._pool.waitForDone(1000)
        super().closeEvent(event)

