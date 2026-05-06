from PyQt6.QtCore import QRunnable, QObject, pyqtSignal
from PIL import Image
from pathlib import Path
from flatshot.core.engine import ShadowEngine
from flatshot.core.models import ShadowSettings, CurveData, normalize_shadow_settings, SHADOW_ENGINE_DEFAULT
from flatshot.core.overrides import apply_image_override
import traceback

class PreRenderSignals(QObject):
    finished = pyqtSignal(str, bool)  # key, success
    error = pyqtSignal(str)

class PreRenderWorker(QRunnable):
    """Worker to render an image at full resolution in the background and save to cache."""
    
    def __init__(self, key: str, image_path: str, settings_dict: dict, 
                 curve_dict: dict, target_size: tuple, cache_path: Path, 
                 local_override: dict = None):
        super().__init__()
        self.key = key
        self.image_path = Path(image_path)
        self.settings_dict = settings_dict
        self.curve_dict = curve_dict
        self.target_size = target_size
        self.cache_path = cache_path
        self.local_override = local_override or {}
        self.signals = PreRenderSignals()
        
    def run(self):
        try:
            # Reconstruct models
            settings = apply_image_override(
                normalize_shadow_settings(
                    self.settings_dict,
                    missing_engine=SHADOW_ENGINE_DEFAULT,
                ),
                self.local_override,
            )
            curve_data = CurveData(**self.curve_dict) if self.curve_dict else None
            
            # Load and process
            original = Image.open(self.image_path).convert('RGBA')
            
            # We use full resolution (scale_factor=1.0)
            final_img, diagnostics = ShadowEngine._aplicar_efectos_with_diagnostics(
                original, settings, self.target_size, 
                scale_factor=1.0, curve_data=curve_data
            )
            
            # Save to cache (always as PNG to preserve alpha/quality during intermediate stage)
            # We'll convert to JPG during the final export if needed.
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Use compression 0/False for speed since this is a temporary cache
            final_img.save(self.cache_path, optimize=False, compress_level=0)
            
            self.signals.finished.emit(self.key, True)
            
        except Exception as e:
            # traceback.print_exc()
            self.signals.error.emit(f"Pre-render error for {self.image_path.name}: {str(e)}")
            self.signals.finished.emit(self.key, False)
