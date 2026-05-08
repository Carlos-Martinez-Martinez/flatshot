"""Process-isolated pre-render jobs for export cache generation."""

from __future__ import annotations

import os
import uuid
from pathlib import Path

from PIL import Image

from flatshot.core.engine import ShadowEngine
from flatshot.core.models import CurveData, SHADOW_ENGINE_DEFAULT, normalize_shadow_settings
from flatshot.core.overrides import apply_image_override
from flatshot.utils.render_cache import RenderCache


def _set_low_priority() -> None:
    """Best-effort low priority for opportunistic cache work."""
    if os.name == "nt":
        try:
            import ctypes

            idle_priority_class = 0x00000040
            kernel32 = ctypes.windll.kernel32
            kernel32.SetPriorityClass(kernel32.GetCurrentProcess(), idle_priority_class)
        except Exception:
            pass
    else:
        try:
            os.nice(10)
        except Exception:
            pass


def render_pre_render_job(job: dict) -> tuple[bool, str, str | None]:
    """
    Render one image into the export cache.

    Returns ``(success, key, message)``. The cache write is atomic: incomplete
    files stay as hidden ``.tmp`` sidecars and never count as cache hits.
    """
    _set_low_priority()

    key = str(job["key"])
    image_path = Path(job["image_path"])
    cache_path = Path(job["cache_path"])
    fmt = RenderCache.normalize_format(job.get("format"))
    temp_path = RenderCache().get_temp_path(cache_path, f"{os.getpid()}-{uuid.uuid4().hex}")

    try:
        settings = apply_image_override(
            normalize_shadow_settings(
                job.get("settings_dict"),
                missing_engine=SHADOW_ENGINE_DEFAULT,
            ),
            job.get("local_override") or {},
        )
        curve_dict = job.get("curve_dict")
        curve_data = CurveData(**curve_dict) if curve_dict else None
        target_size = tuple(job["target_size"])

        with Image.open(image_path) as opened:
            original = opened.convert("RGBA")
            dpi = opened.info.get("dpi", (300, 300))

        final_img, _diagnostics = ShadowEngine._aplicar_efectos_with_diagnostics(
            original,
            settings,
            target_size,
            scale_factor=1.0,
            curve_data=curve_data,
        )

        cache_path.parent.mkdir(parents=True, exist_ok=True)
        if fmt == "jpg":
            final_img = final_img.convert("RGB")
            final_img.save(
                temp_path,
                format="JPEG",
                quality=100,
                subsampling=0,
                dpi=dpi,
            )
        else:
            final_img.save(
                temp_path,
                format="PNG",
                optimize=False,
                compress_level=0,
                dpi=dpi,
            )

        os.replace(temp_path, cache_path)
        return True, key, None
    except Exception as exc:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass
        return False, key, str(exc)


def run_pre_render_job(job: dict, result_queue) -> None:
    """Multiprocessing entry point."""
    result_queue.put(render_pre_render_job(job))
