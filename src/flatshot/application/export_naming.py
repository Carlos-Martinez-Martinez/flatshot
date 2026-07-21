"""Export naming, output path planning, and collision validation."""
from __future__ import annotations

import os
from pathlib import Path

from flatshot.application.contracts import ExportJobRequest
from flatshot.application.export_config_service import (
    variant_base_destination as variant_base_output_folder,
)
from flatshot.application.export_config_service import (
    variant_output_folder,
)
from flatshot.core.models import ExportConfig, ExportVariant, normalize_export_variants
from flatshot.utils.render_cache import RenderCache

EXPORT_OUTPUT_COLLISION_MESSAGE = (
    "Hay archivos de salida repetidos o ya existentes. "
    "Cambia el destino, el sufijo o el patrón de nombre antes de exportar."
)
EXPORT_OUTPUT_NAME_MESSAGE = (
    f"{EXPORT_OUTPUT_COLLISION_MESSAGE} "
    "El nombre de salida no puede contener separadores de ruta ni partes relativas."
)

class OutputPathValidationError(ValueError):
    """Raised when planned export outputs are not safe to write."""

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

    if "{index:" in result:
        import re

        match = re.search(r"\{index:(\d+)d\}", result)
        if match:
            padding = int(match.group(1))
            result = re.sub(r"\{index:\d+d\}", str(index).zfill(padding), result)
    else:
        result = result.replace("{index}", str(index).zfill(3))

    return result

def _safe_filename_token(value: str) -> str:
    text = str(value or "").strip()
    for char in '<>:"/\\|?*':
        text = text.replace(char, "_")
    text = "".join("_" if ord(ch) < 32 else ch for ch in text)
    return text.strip(" .")

def _validate_output_filename(value: str) -> str:
    text = str(value or "")
    if not text.strip() or text in {".", ".."}:
        raise OutputPathValidationError(EXPORT_OUTPUT_NAME_MESSAGE)
    if Path(text).name != text:
        raise OutputPathValidationError(EXPORT_OUTPUT_NAME_MESSAGE)
    if any(char in text for char in '<>:"/\\|?*'):
        raise OutputPathValidationError(EXPORT_OUTPUT_NAME_MESSAGE)
    if any(ord(ch) < 32 for ch in text):
        raise OutputPathValidationError(EXPORT_OUTPUT_NAME_MESSAGE)
    return text

def variant_bg_token(variant: ExportVariant) -> str:
    return "{:02X}{:02X}{:02X}".format(*variant.bg_color)

def get_enabled_export_variants(export_config: ExportConfig) -> list[ExportVariant]:
    return [variant for variant in normalize_export_variants(export_config) if variant.enabled]

def variant_export_format(export_config: ExportConfig, variant: ExportVariant) -> str:
    return RenderCache.normalize_format(variant.format or export_config.format)

def variant_naming_template(export_config: ExportConfig, variant: ExportVariant) -> str:
    return variant.naming_template or export_config.naming_template

def variant_target_size(export_config: ExportConfig, variant: ExportVariant) -> tuple[int, int]:
    return (
        int(variant.output_width or export_config.output_width),
        int(variant.output_height or export_config.output_height),
    )

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
        variant_naming_template(export_config, variant),
        original_name,
        variant.suffix,
        folder_name,
        index,
        variant_label=variant.label,
        variant_id=variant.id,
        bg=variant_bg_token(variant),
    )
    base_name = _validate_output_filename(base_name)
    return output_folder / f"{base_name}.{fmt}", fmt

def _path_collision_key(path: Path) -> str:
    return os.path.normcase(os.path.abspath(str(path)))

def validate_output_path_collisions(planned_outputs: list[dict], *, check_existing: bool = True) -> None:
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
            raise OutputPathValidationError(
                f"{EXPORT_OUTPUT_COLLISION_MESSAGE} "
                "Las variantes "
                f"{previous_variant.label} y {current_variant.label} generarían el mismo archivo. "
                "Cambia el sufijo o la subcarpeta."
            )

        raise OutputPathValidationError(
            f"{EXPORT_OUTPUT_COLLISION_MESSAGE} "
            f"Dos entradas generarían el mismo archivo: {Path(item['save_path']).name}. "
            "Cambia la plantilla de nombre, el sufijo o la subcarpeta."
        )

    if not check_existing:
        return

    for item in planned_outputs:
        save_path = Path(item["save_path"])
        try:
            exists = save_path.exists()
        except OSError as exc:
            raise OutputPathValidationError(
                f"{EXPORT_OUTPUT_COLLISION_MESSAGE} "
                f"No se pudo comprobar la salida {save_path.name}."
            ) from exc
        if exists:
            raise OutputPathValidationError(
                f"{EXPORT_OUTPUT_COLLISION_MESSAGE} "
                f"Ya existe una salida llamada {save_path.name}."
            )

def planned_output_paths_for_request(request: ExportJobRequest) -> list[dict]:
    """Plan the output paths for a single request without touching the filesystem."""
    if request.input_files is not None:
        image_paths = [Path(p) for p in request.input_files]
        image_paths = [p for p in image_paths if p.is_file() and p.suffix.lower() == ".png"]
    else:
        image_paths = [
            path
            for path in request.input_folder.iterdir()
            if path.is_file() and path.suffix.lower() == ".png"
        ]

    enabled_variants = get_enabled_export_variants(request.export_config)
    parent_folder_name = request.input_folder.name
    planned_outputs: list[dict] = []

    for index, img_path in enumerate(sorted(image_paths, key=lambda path: path.name), start=1):
        for variant in enabled_variants:
            base_output_folder = variant_base_output_folder(
                request.input_folder,
                request.export_config,
                variant,
            )
            save_path, fmt = build_variant_output_path(
                base_output_folder,
                request.export_config,
                variant,
                img_path.stem,
                parent_folder_name,
                index,
            )
            planned_outputs.append(
                {
                    "save_path": save_path,
                    "variant": variant,
                    "image_path": img_path,
                    "format": fmt,
                    "input_folder": request.input_folder,
                }
            )

    return planned_outputs

def planned_output_paths_for_requests(requests: list[ExportJobRequest]) -> list[dict]:
    planned_outputs: list[dict] = []
    for request in requests:
        planned_outputs.extend(planned_output_paths_for_request(request))
    return planned_outputs

def validate_export_requests_outputs(
    requests: list[ExportJobRequest],
    *,
    check_existing: bool = True,
) -> list[dict]:
    planned_outputs = planned_output_paths_for_requests(requests)
    validate_output_path_collisions(planned_outputs, check_existing=check_existing)
    return planned_outputs
