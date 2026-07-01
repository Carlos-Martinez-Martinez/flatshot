"""Export render-task planning helpers."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from flatshot.application.contracts import ExportJobRequest
from flatshot.application.export_config_service import variant_base_destination as variant_base_output_folder
from flatshot.application.export_naming import (
    build_variant_output_path,
    get_enabled_export_variants,
    variant_target_size,
)
from flatshot.core.models import ExportVariant, build_variant_settings
from flatshot.utils.render_cache import RenderCache


@dataclass
class ExportRenderTask:
    img_path: Path
    key: str
    fmt: str
    save_path: Path
    cache_path: Path
    task_args: tuple
    display_name: str

@dataclass
class ExportPlan:
    source_total: int
    total: int
    enabled_variants: list[ExportVariant]
    planned_outputs: list[dict]
    render_tasks: list[ExportRenderTask]
    cached_tasks: list[ExportRenderTask]

def build_export_plan(
    request: ExportJobRequest,
    image_items: list[tuple[Path, str, Path]],
    cache: RenderCache,
) -> ExportPlan:
    enabled_variants = get_enabled_export_variants(request.export_config)
    curve_data_dict = request.curve_data.model_dump() if request.curve_data else None
    parent_folder_name = request.input_folder.name
    render_tasks: list[ExportRenderTask] = []
    cached_tasks: list[ExportRenderTask] = []
    planned_outputs: list[dict] = []

    for index, (img_path, local_key, cache_identity_path) in enumerate(
        sorted(image_items, key=lambda item: item[0].name),
        start=1,
    ):
        local_override = dict(request.image_overrides or {}).get(local_key, {})

        for variant in enabled_variants:
            variant_settings = build_variant_settings(request.settings, variant)
            settings_dict = variant_settings.model_dump()
            target_size = variant_target_size(request.export_config, variant)
            variant_base_folder = variant_base_output_folder(
                request.input_folder,
                request.export_config,
                variant,
            )
            save_path, fmt = build_variant_output_path(
                variant_base_folder,
                request.export_config,
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
            render_task = ExportRenderTask(
                img_path=img_path,
                key=key,
                fmt=fmt,
                save_path=save_path,
                cache_path=cache.get_cached_path(key, fmt),
                task_args=task_args,
                display_name=display_name,
            )
            planned_outputs.append(
                {
                    "save_path": save_path,
                    "variant": variant,
                    "image_path": img_path,
                }
            )
            if cache.exists(key, fmt, validate=True):
                cached_tasks.append(render_task)
            else:
                render_tasks.append(render_task)

    return ExportPlan(
        source_total=len(image_items),
        total=len(image_items) * len(enabled_variants),
        enabled_variants=enabled_variants,
        planned_outputs=planned_outputs,
        render_tasks=render_tasks,
        cached_tasks=cached_tasks,
    )
