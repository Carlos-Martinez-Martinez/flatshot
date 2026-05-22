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
from flatshot.core.models import (
    CurveData,
    ExportConfig,
    ExportVariant,
    SHADOW_ENGINE_DEFAULT,
    ShadowSettings,
    build_variant_settings,
    normalize_export_variants,
    normalize_shadow_settings,
)
from flatshot.core.overrides import apply_image_override, override_key
from flatshot.utils.render_cache import RenderCache


def apply_naming_template(
    template: str,
    original_name: str,
    suffix: str,
    folder_name: str,
    index: int,
    variant_label: str = "",
    variant_id: str = "",
    bg: str = "",
) -> str:
    """
    Apply naming template to generate output filename.
    
    Supported placeholders:
    - {original}: Original filename without extension
    - {suffix}: The suffix from export config
    - {folder}: Parent folder name
    - {variant}: Output variant label
    - {variant_id}: Output variant id
    - {bg}: Output background as RRGGBB
    - {index}: Zero-padded index (e.g., 001, 002)
    - {index:03d}: Custom padding format
    """
    result = template
    result = result.replace("{original}", original_name)
    result = result.replace("{suffix}", suffix)
    result = result.replace("{folder}", folder_name)
    result = result.replace("{variant}", _safe_filename_token(variant_label))
    result = result.replace("{variant_id}", _safe_filename_token(variant_id))
    result = result.replace("{bg}", _safe_filename_token(bg))
    
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


def _safe_filename_token(value: str) -> str:
    text = str(value or "").strip()
    for char in '<>:"/\\|?*':
        text = text.replace(char, "_")
    text = "".join("_" if ord(ch) < 32 else ch for ch in text)
    return text.strip(" .")


def variant_bg_token(variant: ExportVariant) -> str:
    return "{:02X}{:02X}{:02X}".format(*variant.bg_color)


def get_enabled_export_variants(export_config: ExportConfig) -> list[ExportVariant]:
    return [variant for variant in normalize_export_variants(export_config) if variant.enabled]


def variant_export_format(export_config: ExportConfig, variant: ExportVariant) -> str:
    return RenderCache.normalize_format(variant.format or export_config.format)


def variant_output_folder(base_output_folder: Path, variant: ExportVariant) -> Path:
    if variant.output_subfolder:
        return base_output_folder / variant.output_subfolder
    return base_output_folder


def build_variant_output_path(
    base_output_folder: Path,
    export_config: ExportConfig,
    variant: ExportVariant,
    original_name: str,
    folder_name: str,
    index: int,
) -> tuple[Path, str]:
    fmt = variant_export_format(export_config, variant)
    output_folder = variant_output_folder(base_output_folder, variant)
    base_name = apply_naming_template(
        export_config.naming_template,
        original_name,
        variant.suffix,
        folder_name,
        index,
        variant_label=variant.label,
        variant_id=variant.id,
        bg=variant_bg_token(variant),
    )
    return output_folder / f"{base_name}.{fmt}", fmt


def _path_collision_key(path: Path) -> str:
    return os.path.normcase(os.path.abspath(str(path)))


def validate_output_path_collisions(planned_outputs: list[dict]) -> None:
    seen: dict[str, dict] = {}
    for item in planned_outputs:
        key = _path_collision_key(Path(item["save_path"]))
        previous = seen.get(key)
        if previous is None:
            seen[key] = item
            continue

        current_variant = item["variant"]
        previous_variant = previous["variant"]
        if current_variant.id != previous_variant.id:
            raise ValueError(
                "Las variantes "
                f"{previous_variant.label} y {current_variant.label} generarían el mismo archivo. "
                "Cambia el sufijo o la subcarpeta."
            )

        raise ValueError(
            f"Dos entradas generarían el mismo archivo: {Path(item['save_path']).name}. "
            "Cambia la plantilla de nombre, el sufijo o la subcarpeta."
        )


def process_single_image(args):
    """Process a single image in a worker process."""
    if len(args) == 8:
        (
            img_path,
            save_path,
            settings_dict,
            target_size,
            fmt,
            curve_data_dict,
            local_override,
            display_name,
        ) = args
    else:
        (
            img_path,
            output_folder,
            settings_dict,
            target_size,
            naming_template,
            suffix,
            folder_name,
            index,
            fmt,
            curve_data_dict,
            local_override,
        ) = args
        base_name = apply_naming_template(naming_template, img_path.stem, suffix, folder_name, index)
        save_path = Path(output_folder) / f"{base_name}.{fmt}"
        display_name = str(img_path.name)
    
    try:
        # Reconstruct Pydantic models from dicts (pickle serialization fix).
        settings = apply_image_override(
            normalize_shadow_settings(
                settings_dict,
                missing_engine=SHADOW_ENGINE_DEFAULT,
            ),
            local_override,
        )
        curve_data = CurveData(**curve_data_dict) if curve_data_dict else None
        
        original = Image.open(img_path).convert('RGBA')
        dpi = original.info.get('dpi', (300, 300))
        
        final_img, diagnostics = ShadowEngine._aplicar_efectos_with_diagnostics(
            original, settings, target_size, 
            scale_factor=1.0, curve_data=curve_data
        )
        warning = diagnostics.warning if diagnostics.fallback_used else None
        
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        if fmt in ['jpg', 'jpeg']:
            final_img = final_img.convert("RGB")
            final_img.save(save_path, quality=100, subsampling=0, dpi=dpi)
        else:
            final_img.save(save_path, optimize=False, compress_level=0, dpi=dpi)
            
        return True, display_name, warning
    except Exception as e:
        return False, f"{img_path.name}: {e}", None


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
        completed_count = 0
        error_count = 0
        total = 0
        
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
                        image_items.append((dest, override_key(src), src))
            else:
                image_items = [
                    (f, override_key(f), f)
                    for f in self.input_folder.iterdir()
                    if f.is_file() and f.suffix.lower() == '.png'
                ]
            
            source_total = len(image_items)
            if source_total == 0:
                self.finished_process.emit(True, 0, 0, 0.0)
                return

            enabled_variants = get_enabled_export_variants(self.export_config)
            total = source_total * len(enabled_variants)
            if not enabled_variants:
                self.log_updated.emit("No hay variantes de salida activas. Activa al menos una salida.")
                duration = time() - self.start_time
                self.finished_process.emit(False, 0, 0, duration)
                return

            self.log_updated.emit(
                "Salidas activas: " + ", ".join(variant.label for variant in enabled_variants)
            )

            # Use dynamic output size from config
            target_size = (self.export_config.output_width, self.export_config.output_height)

            if self.export_config.output_destination == 'custom' and self.export_config.custom_output_path:
                base_output_folder = Path(self.export_config.custom_output_path)
            else:
                base_output_folder = self.input_folder / self.export_config.output_folder_name

            # Convert Pydantic models to dicts for pickle serialization
            curve_data_dict = self.curve_data.model_dump() if self.curve_data else None
            parent_folder_name = self.input_folder.name

            # Initialize RenderCache
            cache = RenderCache()

            # Build task list
            tasks = []
            cached_tasks = []
            planned_outputs = []
            
            for index, (img_path, local_key, cache_identity_path) in enumerate(
                sorted(image_items, key=lambda item: item[0].name),
                start=1,
            ):
                local_override = self.image_overrides.get(local_key, {})

                for variant in enabled_variants:
                    variant_settings = build_variant_settings(self.settings, variant)
                    settings_dict = variant_settings.model_dump()
                    save_path, fmt = build_variant_output_path(
                        base_output_folder,
                        self.export_config,
                        variant,
                        img_path.stem,
                        parent_folder_name,
                        index,
                    )
                    display_name = f"{img_path.name} · {variant.label}"

                    task_args = (
                        img_path,
                        save_path,
                        settings_dict,
                        target_size,
                        fmt,
                        curve_data_dict,
                        local_override,
                        display_name,
                    )

                    key = cache.get_cache_key(
                        str(cache_identity_path),
                        settings_dict,
                        curve_data_dict,
                        target_size,
                        local_override,
                        fmt,
                    )

                    planned_outputs.append(
                        {
                            "save_path": save_path,
                            "variant": variant,
                            "image_path": img_path,
                        }
                    )
                    if cache.exists(key, fmt, validate=True):
                        cached_tasks.append(
                            {
                                "img_path": img_path,
                                "key": key,
                                "fmt": fmt,
                                "save_path": save_path,
                                "task_args": task_args,
                                "display_name": display_name,
                            }
                        )
                    else:
                        tasks.append(task_args)

            try:
                validate_output_path_collisions(planned_outputs)
                for folder in sorted(
                    {Path(item["save_path"]).parent for item in planned_outputs},
                    key=lambda path: str(path),
                ):
                    folder.mkdir(parents=True, exist_ok=True)
            except Exception as exc:
                self.log_updated.emit(str(exc))
                duration = time() - self.start_time
                self.finished_process.emit(False, 0, total, duration)
                return

            # Handle cached tasks first
            if cached_tasks:
                self.log_updated.emit(f"Exportando {len(cached_tasks)} archivos desde caché...")
                for cached in cached_tasks:
                    if not self.is_running: break
                    self._pause_event.wait()
                     
                    try:
                        cache_path = cache.get_cached_path(cached["key"], cached["fmt"])
                        save_path = Path(cached["save_path"])
                        save_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(cache_path, save_path)
                         
                        completed_count += 1
                        self.image_completed.emit(cached["display_name"], True)
                        self.progress_updated.emit(int((completed_count / total) * 100))
                    except Exception as e:
                        self.log_updated.emit(
                            f"Caché no válida para {cached['display_name']}; renderizando normal ({e})"
                        )
                        success, msg, warning = process_single_image(cached["task_args"])
                        if success:
                            if warning: self.log_updated.emit(f"Aviso: {msg}: {warning}")
                            self.image_completed.emit(msg, True)
                        else:
                            error_count += 1
                            self.log_updated.emit(f"Error: {msg}")
                            self.image_completed.emit(msg.split(':')[0], False)
                        completed_count += 1
                        self.progress_updated.emit(int((completed_count / total) * 100))

            # Proceed with remaining tasks
            if tasks and self.is_running:
                max_workers = max(1, (os.cpu_count() or 2) - 1)
                self.log_updated.emit(f"Procesando {len(tasks)} archivos restantes con {max_workers} núcleos...")
                
                try:
                    with ProcessPoolExecutor(max_workers=max_workers) as executor:
                        self.executor = executor
                        pending_tasks = iter(tasks)
                        in_flight = set()

                        for _ in range(min(max_workers, len(tasks))):
                            try:
                                in_flight.add(executor.submit(process_single_image, next(pending_tasks)))
                            except StopIteration:
                                break

                        while in_flight and self.is_running:
                            self._pause_event.wait()
                            if not self.is_running: break

                            done, _ = wait(in_flight, timeout=0.2, return_when=FIRST_COMPLETED)
                            if not done: continue

                            for future in done:
                                in_flight.discard(future)
                                try:
                                    success, msg, warning = future.result()
                                except Exception as exc:
                                    success, msg, warning = False, f"Worker error: {exc}", None

                                if success:
                                    if warning: self.log_updated.emit(f"Aviso: {msg}: {warning}")
                                    self.image_completed.emit(msg, True)
                                else:
                                    error_count += 1
                                    self.log_updated.emit(f"Error: {msg}")
                                    self.image_completed.emit(msg.split(':')[0], False)

                                completed_count += 1
                                self.progress_updated.emit(int((completed_count / total) * 100))

                                if self.is_running and self._pause_event.is_set():
                                    try:
                                        in_flight.add(executor.submit(process_single_image, next(pending_tasks)))
                                    except StopIteration:
                                        pass
                except Exception as exc:
                    self.log_updated.emit(f"Error en el proceso de exportación: {exc}")

        except Exception as exc:
            self.log_updated.emit(f"Error crítico en ExportWorker: {exc}")
        finally:
            if self._snapshot_dir:
                shutil.rmtree(self._snapshot_dir, ignore_errors=True)
            if self.executor:
                self.executor.shutdown(wait=False, cancel_futures=True)

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
