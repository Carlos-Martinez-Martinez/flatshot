"""Worker-side export helpers used by ExportRunner."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Callable

from PIL import Image

from flatshot.application.image_encoding import save_export_image
from flatshot.core.engine import ShadowEngine
from flatshot.core.models import SHADOW_ENGINE_DEFAULT, CurveData, normalize_shadow_settings
from flatshot.core.overrides import apply_image_override


def process_single_image(args):
    """Process a single image in a worker process."""
    (
        img_path,
        save_path,
        settings_dict,
        target_size,
        fmt,
        curve_data_dict,
        local_override,
        display_name,
        *optional_export_options,
    ) = args
    export_options = optional_export_options[0] if optional_export_options else {}
    if not isinstance(export_options, dict):
        export_options = {}

    try:
        settings = apply_image_override(
            normalize_shadow_settings(
                settings_dict,
                missing_engine=SHADOW_ENGINE_DEFAULT,
            ),
            local_override,
        )
        curve_data = CurveData(**curve_data_dict) if curve_data_dict else None

        original = Image.open(img_path).convert("RGBA")
        dpi = original.info.get("dpi", (300, 300))

        final_img, diagnostics = ShadowEngine._aplicar_efectos_with_diagnostics(
            original,
            settings,
            target_size,
            scale_factor=1.0,
            curve_data=curve_data,
        )
        warning = diagnostics.warning if diagnostics.fallback_used else None

        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        encoding_warning = save_export_image(
            final_img,
            save_path,
            fmt,
            dpi=dpi,
            max_file_size_kb=export_options.get("max_file_size_kb"),
        )
        if warning and encoding_warning:
            warning = f"{warning} {encoding_warning}"
        elif encoding_warning:
            warning = encoding_warning

        return True, display_name, warning
    except Exception as e:
        return False, f"{img_path.name}: {e}", None


def copy_stable(src: Path, dest: Path, copy_file: Callable = shutil.copy2) -> bool:
    """Copy a file while ensuring we capture a stable snapshot."""
    for _ in range(3):
        try:
            before = src.stat()
        except FileNotFoundError:
            return False
        try:
            copy_file(src, dest)
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
