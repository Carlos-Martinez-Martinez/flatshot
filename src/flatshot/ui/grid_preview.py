"""
Grid Preview Widget for FlatShot
Displays multiple image previews in a grid layout with lazy loading.
"""
from pathlib import Path
from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QVBoxLayout, QLabel, QScrollArea,
    QSizePolicy, QFrame, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize, QRunnable, QThreadPool, QObject
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor
from PIL import Image

from flatshot.core.engine import ShadowEngine
from flatshot.core.models import ShadowSettings, CurveData


def _render_tile_preview(
    image_path: str,
    settings_dict: dict,
    curve_dict: dict,
    preview_size: tuple[int, int],
):
    """Render a grid tile preview off the UI thread."""
    settings = ShadowSettings(**settings_dict)
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
                bg = Image.new("RGB", pil_image.size, (230, 230, 230))
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
        
        self.setStyleSheet("""
            PreviewTile {
                background-color: #2A2A2A;
                border: 1px solid #3A3A3A;
                border-radius: 4px;
            }
            PreviewTile:hover {
                border-color: #0078D4;
            }
        """)
        self.setFixedHeight(140)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.image_label)
        
        self.name_label = QLabel()
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet("color: #888; font-size: 9px;")
        self.name_label.setWordWrap(True)
        layout.addWidget(self.name_label)
    
    def set_image(self, file_path: str, processed: QPixmap, original: QPixmap = None):
        """Set the images for this tile."""
        self.file_path = file_path
        self._processed_image = processed
        self._original_image = original or processed
        self._is_loaded = True
        self.name_label.setText(Path(file_path).stem[:18])
        self._update_display()
    
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
    
    def set_pending(self, file_path: str):
        """Set pending state with filename but no image yet."""
        self.file_path = file_path
        self.name_label.setText(Path(file_path).stem[:18])
        self.image_label.setText("⏳")
        self._is_loaded = False
    
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
        self._tiles: List[PreviewTile] = []
        self._images: List[Path] = []
        self._render_generation = 0
        self._completed_tiles = 0
        self._active_workers = set()
        self._pool = QThreadPool()
        self._pool.setMaxThreadCount(2)
        
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
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll area for grid
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("QScrollArea { border: none; background-color: #1E1E1E; }")
        
        self.grid_container = QWidget()
        self.grid_layout = QVBoxLayout(self.grid_container)
        self.grid_layout.setSpacing(6)
        self.grid_layout.setContentsMargins(6, 6, 6, 6)
        
        self.scroll.setWidget(self.grid_container)
        layout.addWidget(self.scroll)
        
        # Info label
        self.info_label = QLabel("Selecciona una carpeta para ver previews")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("color: #666; padding: 6px; font-size: 10px;")
        layout.addWidget(self.info_label)
    
    def _clear_tiles(self):
        """Remove all tiles from the grid."""
        for tile in self._tiles:
            self.grid_layout.removeWidget(tile)
            tile.deleteLater()
        self._tiles.clear()
    
    def _create_tiles_for_images(self):
        """Create exactly as many tiles as there are images."""
        # Clear existing tiles
        self._clear_tiles()
        
        # Create a tile for each image
        for i, img_path in enumerate(self._images):
            tile = PreviewTile()
            tile.clicked.connect(self.image_selected.emit)
            tile.set_pending(str(img_path))
            self.grid_layout.addWidget(tile)
            self._tiles.append(tile)
        
        # Add stretch at end
        self.grid_layout.addStretch()
    
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
    
    def _load_images(self):
        """Load image paths from the folder."""
        # Cancel any ongoing processing
        self._chunk_timer.stop()
        self._update_timer.stop()
        self._render_generation += 1
        self._active_workers.clear()
        
        if not self.folder_path:
            self._images = []
            self._clear_tiles()
            self.info_label.setText("Selecciona una carpeta para ver previews")
            return
        
        folder = Path(self.folder_path)
        self._images = sorted(folder.glob("*.png"))
        
        if not self._images:
            self._clear_tiles()
            self.info_label.setText("No se encontraron imágenes PNG")
            self.folder_empty.emit()  # Notify parent to show placeholder
        else:
            self.info_label.setText(f"Cargando {len(self._images)} imágenes...")
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
                self.info_label.setText("No se encontraron imágenes PNG")
            return
        self._render_generation += 1
        self._completed_tiles = 0
        
        # Reset all tiles to pending state
        for i, tile in enumerate(self._tiles):
            if i < len(self._images):
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
                self.info_label.setText(f"Mostrando {len(self._images)} imágenes")
            return
        
        preview_size = (150, 200)
        generation = self._render_generation
        settings_dict = self.settings.model_dump()
        curve_dict = self.curve_data.model_dump() if self.curve_data else None
        
        for i in range(start, end):
            if i >= len(self._tiles):
                break

            worker = TileRenderWorker(
                tile_index=i,
                generation=generation,
                image_path=str(self._images[i]),
                settings_dict=settings_dict,
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
            self.info_label.setText(f"Procesando... {processed}/{len(self._images)}")
            self._chunk_timer.start(20)
        elif self._completed_tiles >= len(self._images):
            self.info_label.setText(f"Mostrando {len(self._images)} imágenes")

    def _on_tile_rendered(self, worker: TileRenderWorker, tile_index: int, generation: int, payload):
        self._active_workers.discard(worker)
        if generation != self._render_generation:
            return
        if tile_index < 0 or tile_index >= len(self._tiles) or tile_index >= len(self._images):
            return

        processed_payload, original_payload = payload
        processed_qpixmap = self._payload_to_qpixmap(processed_payload)
        original_qpixmap = self._payload_to_qpixmap(original_payload)
        self._tiles[tile_index].set_image(str(self._images[tile_index]), processed_qpixmap, original_qpixmap)

        self._completed_tiles += 1
        if self._completed_tiles >= len(self._images):
            self.info_label.setText(f"Mostrando {len(self._images)} imágenes")
        else:
            self.info_label.setText(f"Generando... {self._completed_tiles}/{len(self._images)}")

    def _on_tile_error(self, worker: TileRenderWorker, tile_index: int, generation: int, message: str):
        self._active_workers.discard(worker)
        if generation != self._render_generation:
            return
        if 0 <= tile_index < len(self._tiles):
            self._tiles[tile_index].name_label.setText(f"Error: {message[:15]}")

        self._completed_tiles += 1
        if self._completed_tiles >= len(self._images):
            self.info_label.setText(f"Mostrando {len(self._images)} imágenes")

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

