"""
Export Worker for FlatShot
Handles batch image processing with multiprocessing.
"""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from time import time
from PyQt6.QtCore import QThread, pyqtSignal
from PIL import Image
from flatshot.core.engine import ShadowEngine
from flatshot.core.models import ShadowSettings, ExportConfig, CurveData


def apply_naming_template(template: str, original_name: str, suffix: str, 
                          folder_name: str, index: int) -> str:
    """
    Apply naming template to generate output filename.
    
    Supported placeholders:
    - {original}: Original filename without extension
    - {suffix}: The suffix from export config
    - {folder}: Parent folder name
    - {index}: Zero-padded index (e.g., 001, 002)
    - {index:03d}: Custom padding format
    """
    result = template
    result = result.replace("{original}", original_name)
    result = result.replace("{suffix}", suffix)
    result = result.replace("{folder}", folder_name)
    
    # Handle index with optional format specifier
    if "{index:" in result:
        # Extract format specifier
        import re
        match = re.search(r'\{index:(\d+)d\}', result)
        if match:
            padding = int(match.group(1))
            result = re.sub(r'\{index:\d+d\}', str(index).zfill(padding), result)
    else:
        result = result.replace("{index}", str(index).zfill(3))
    
    return result


def process_single_image(args):
    """Process a single image in a worker process."""
    (img_path, output_folder, settings_dict, target_size, 
     naming_template, suffix, folder_name, index, fmt, curve_data_dict) = args
    
    try:
        # Reconstruct Pydantic models from dicts (pickle serialization fix)
        settings = ShadowSettings(**settings_dict)
        curve_data = CurveData(**curve_data_dict) if curve_data_dict else None
        
        original = Image.open(img_path).convert('RGBA')
        dpi = original.info.get('dpi', (300, 300))
        
        final_img = ShadowEngine.aplicar_efectos(
            original, settings, target_size, 
            scale_factor=1.0, curve_data=curve_data
        )
        
        # Apply naming template
        base_name = apply_naming_template(
            naming_template, img_path.stem, suffix, folder_name, index
        )
        save_name = f"{base_name}.{fmt}"
        save_path = output_folder / save_name
        
        if fmt in ['jpg', 'jpeg']:
            final_img = final_img.convert("RGB")
            final_img.save(save_path, quality=100, subsampling=0, dpi=dpi)
        else:
            final_img.save(save_path, optimize=False, compress_level=0, dpi=dpi)
            
        return True, str(img_path.name)
    except Exception as e:
        return False, f"{img_path.name}: {e}"


class ExportWorker(QThread):
    """Worker thread for batch image export."""
    
    progress_updated = pyqtSignal(int)
    log_updated = pyqtSignal(str)
    image_completed = pyqtSignal(str, bool)  # image_name, success
    finished_process = pyqtSignal(bool, int, int, float)  # success, processed, total, duration

    def __init__(self, input_folder: str, shadow_settings: ShadowSettings, 
                 export_config: ExportConfig, curve_data: CurveData,
                 preset_name: str = None):
        super().__init__()
        self.input_folder = Path(input_folder)
        self.settings = shadow_settings
        self.export_config = export_config
        self.curve_data = curve_data
        self.preset_name = preset_name
        self.is_running = True
        self.executor = None
        self.start_time = None

    def run(self):
        self.start_time = time()
        
        # Find all PNG images
        images = [f for f in self.input_folder.iterdir() 
                  if f.is_file() and f.suffix.lower() == '.png']
        total = len(images)
        
        if total == 0:
            self.finished_process.emit(True, 0, 0, 0.0)
            return

        folder_name = self.export_config.output_folder_name
        suffix = self.export_config.suffix
        fmt = self.export_config.format.lower()
        naming_template = self.export_config.naming_template
        
        # Use dynamic output size from config
        target_size = (self.export_config.output_width, self.export_config.output_height)
        
        # Update settings with export config
        self.settings.transparent_bg = self.export_config.transparent_bg
        self.settings.bg_color = self.export_config.bg_color
        
        output_folder = self.input_folder / folder_name
        output_folder.mkdir(exist_ok=True)

        # Convert Pydantic models to dicts for pickle serialization
        settings_dict = self.settings.model_dump()
        curve_data_dict = self.curve_data.model_dump() if self.curve_data else None
        
        # Parent folder name for {folder} placeholder
        parent_folder_name = self.input_folder.name

        # Build task list
        tasks = []
        for index, img_path in enumerate(sorted(images), start=1):
            tasks.append((
                img_path, output_folder, settings_dict, target_size,
                naming_template, suffix, parent_folder_name, index, 
                fmt, curve_data_dict
            ))

        completed_count = 0
        error_count = 0
        
        with ProcessPoolExecutor() as executor:
            self.executor = executor
            futures = [executor.submit(process_single_image, task) for task in tasks]
            
            for future in as_completed(futures):
                if not self.is_running:
                    self.executor.shutdown(wait=False, cancel_futures=True)
                    break
                    
                success, msg = future.result()
                
                if success:
                    self.image_completed.emit(msg, True)
                else:
                    error_count += 1
                    self.log_updated.emit(f"Error: {msg}")
                    self.image_completed.emit(msg.split(':')[0], False)
                    
                completed_count += 1
                self.progress_updated.emit(int((completed_count / total) * 100))

        duration = time() - self.start_time
        self.finished_process.emit(
            self.is_running and error_count == 0,
            completed_count,
            total,
            duration
        )

    def stop(self):
        """Stop the export process."""
        self.is_running = False
