"""
Export Worker for FlatShot
Handles batch image processing with multiprocessing.
"""
import os
import threading
import tempfile
import shutil
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
from time import time
from PyQt6.QtCore import QThread, pyqtSignal
from PIL import Image
from flatshot.core.engine import ShadowEngine
from flatshot.core.models import ShadowSettings, ExportConfig, CurveData
from flatshot.core.overrides import apply_image_override, override_key


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
     naming_template, suffix, folder_name, index, fmt, curve_data_dict, local_override) = args
    
    try:
        # Reconstruct Pydantic models from dicts (pickle serialization fix)
        settings = apply_image_override(ShadowSettings(**settings_dict), local_override)
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
                 preset_name: str = None, input_files: list[str] | None = None,
                 image_overrides: dict | None = None):
        super().__init__()
        self.input_folder = Path(input_folder)
        self.settings = shadow_settings
        self.export_config = export_config
        self.curve_data = curve_data
        self.preset_name = preset_name
        self.is_running = True
        self.executor = None
        self.start_time = None
        self._pause_event = threading.Event()
        self._pause_event.set()
        self.input_files = input_files
        self.image_overrides = dict(image_overrides or {})
        self._snapshot_dir = None

    def _copy_stable(self, src: Path, dest: Path):
        """Copy a file while ensuring we capture a stable snapshot."""
        for _ in range(3):
            try:
                before = src.stat()
            except FileNotFoundError:
                return False
            try:
                shutil.copy2(src, dest)
            except Exception:
                return False
            try:
                after = src.stat()
            except FileNotFoundError:
                try:
                    dest.unlink(missing_ok=True)
                except Exception:
                    pass
                return False
            if before.st_mtime_ns == after.st_mtime_ns and before.st_size == after.st_size:
                return True
            try:
                dest.unlink(missing_ok=True)
            except Exception:
                pass
        return False

    def run(self):
        self.start_time = time()
        try:
            # Find all PNG images (or use provided snapshot list)
            if self.input_files is not None:
                source_files = [Path(p) for p in self.input_files]
                source_files = [p for p in source_files if p.is_file() and p.suffix.lower() == '.png']
                # Snapshot contents to a temp folder to keep a stable view
                snap_dir = Path(tempfile.mkdtemp(prefix="flatshot_snap_"))
                self._snapshot_dir = snap_dir
                image_items = []
                for src in source_files:
                    dest = snap_dir / src.name
                    if self._copy_stable(src, dest):
                        image_items.append((dest, override_key(src)))
            else:
                image_items = [
                    (f, override_key(f))
                    for f in self.input_folder.iterdir()
                    if f.is_file() and f.suffix.lower() == '.png'
                ]
            total = len(image_items)
        except Exception as exc:
            self.log_updated.emit(f"Error al leer carpeta '{self.input_folder}': {exc}")
            self.finished_process.emit(False, 0, 0, 0.0)
            return

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
        
        if self.export_config.output_destination == 'custom' and self.export_config.custom_output_path:
            output_folder = Path(self.export_config.custom_output_path)
        else:
            output_folder = self.input_folder / folder_name
        try:
            output_folder.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            self.log_updated.emit(f"No se pudo crear carpeta de salida '{output_folder}': {exc}")
            duration = time() - self.start_time
            self.finished_process.emit(False, 0, total, duration)
            return

        # Convert Pydantic models to dicts for pickle serialization
        settings_dict = self.settings.model_dump()
        curve_data_dict = self.curve_data.model_dump() if self.curve_data else None
        
        # Parent folder name for {folder} placeholder
        parent_folder_name = self.input_folder.name

        # Build task list
        tasks = []
        for index, (img_path, local_key) in enumerate(
            sorted(image_items, key=lambda item: item[0].name),
            start=1,
        ):
            tasks.append((
                img_path, output_folder, settings_dict, target_size,
                naming_template, suffix, parent_folder_name, index, 
                fmt, curve_data_dict, self.image_overrides.get(local_key, {})
            ))

        completed_count = 0
        error_count = 0
        
        max_workers = max(1, (os.cpu_count() or 2) - 1)
        self.log_updated.emit(f"Iniciando exportación con {max_workers} núcleos...")
        
        try:
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                self.executor = executor
                self.log_updated.emit("Grupo de procesos inicializado correctamente.")
                pending_tasks = iter(tasks)
                in_flight = set()

                # Prime the worker pool.
                for _ in range(min(max_workers, total)):
                    try:
                        in_flight.add(executor.submit(process_single_image, next(pending_tasks)))
                    except StopIteration:
                        break

                while in_flight and self.is_running:
                    # Cooperative pause: stop consuming results and stop submitting new work.
                    self._pause_event.wait()
                    if not self.is_running:
                        break

                    done, _ = wait(in_flight, timeout=0.2, return_when=FIRST_COMPLETED)
                    if not done:
                        continue

                    for future in done:
                        in_flight.discard(future)
                        try:
                            success, msg = future.result()
                        except Exception as exc:
                            success, msg = False, f"Worker error: {exc}"

                        if success:
                            self.image_completed.emit(msg, True)
                        else:
                            error_count += 1
                            self.log_updated.emit(f"Error: {msg}")
                            self.image_completed.emit(msg.split(':')[0], False)

                        completed_count += 1
                        self.progress_updated.emit(int((completed_count / total) * 100))

                        # Keep pool busy only while not paused.
                        if self.is_running and self._pause_event.is_set():
                            try:
                                in_flight.add(executor.submit(process_single_image, next(pending_tasks)))
                            except StopIteration:
                                pass
        finally:
            if self._snapshot_dir:
                try:
                    shutil.rmtree(self._snapshot_dir, ignore_errors=True)
                except Exception:
                    pass

            if not self.is_running and self.executor:
                try:
                    self.executor.shutdown(wait=False, cancel_futures=True)
                except Exception:
                    pass

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
        self._pause_event.set()

    def pause(self):
        """Pause dispatching/consuming new image tasks."""
        self._pause_event.clear()

    def resume(self):
        """Resume image processing after a pause."""
        self._pause_event.set()
