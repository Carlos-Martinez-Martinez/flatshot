"""Pure presentation helpers for UI-facing FlatShot state."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from flatshot.core.models import ExportConfig, ExportVariant, normalize_export_variants


@dataclass(frozen=True)
class TextPresentation:
    text: str
    tooltip: str = ""


@dataclass(frozen=True)
class ProcessingStatusPresentation:
    text: str
    show_progress: bool = False
    progress_value: int | None = None


def pluralize(count: int, singular: str, plural: str) -> str:
    return singular if int(count) == 1 else plural


def rgb_to_hex(color: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*color)


def active_export_variants(config: ExportConfig) -> list[ExportVariant]:
    return [variant for variant in normalize_export_variants(config) if variant.enabled]


def format_batch_summary(folders_count: int, images_count: int, adjusted_count: int = 0) -> str:
    folders = max(0, int(folders_count))
    images = max(0, int(images_count))
    adjusted = max(0, int(adjusted_count))
    if folders <= 0:
        return "Sin lote cargado"

    folder_text = f"{folders} {pluralize(folders, 'carpeta', 'carpetas')}"
    image_text = f"{images} {pluralize(images, 'imagen', 'imágenes')}"
    if adjusted:
        return f"{folder_text} · {image_text} · {adjusted} ajustadas"
    return f"{folder_text} · {image_text}"


def format_process_button_text(images_count: int) -> str:
    images = max(0, int(images_count))
    if images == 1:
        return "Procesar 1 imagen"
    if images > 1:
        return f"Procesar {images} imágenes"
    return "Procesar lote"


def is_destination_configured(config: ExportConfig) -> bool:
    if config.output_destination != "custom":
        return True
    return bool(config.custom_output_path)


def format_destination_batch_label(config: ExportConfig) -> str:
    if config.output_destination == "custom":
        if config.custom_output_path:
            return f"carpeta personalizada: {config.custom_output_path}"
        return "carpeta personalizada sin elegir"
    return f"origen / {config.output_folder_name}"


def format_destination_summary(config: ExportConfig) -> TextPresentation:
    if config.output_destination == "custom":
        if config.custom_output_path:
            return TextPresentation("Destino: carpeta personalizada", str(config.custom_output_path))
        return TextPresentation(
            "Destino: personalizada sin elegir",
            "Elige una carpeta personalizada o usa subcarpeta en origen.",
        )

    folder_name = config.output_folder_name
    return TextPresentation(
        f"Destino: origen / {folder_name}",
        f"Se creará {folder_name} dentro de cada carpeta de origen.",
    )


def format_export_summary(
    config: ExportConfig,
    variants: Iterable[ExportVariant] | None = None,
) -> str:
    active = list(variants) if variants is not None else active_export_variants(config)
    fmt = str(config.format).upper()
    size = f"{config.output_width}×{config.output_height}"

    if active:
        first = active[0]
        bg_text = "transparente" if first.transparent_bg else rgb_to_hex(first.bg_color)
        output_count = f"{len(active)} {pluralize(len(active), 'salida', 'salidas')}"
    else:
        bg_text = "sin salida activa"
        output_count = "0 salidas"

    return f"{fmt} · {size} · {bg_text} · {output_count}"


def format_export_config_summary(
    config: ExportConfig,
    variants: Iterable[ExportVariant] | None = None,
) -> TextPresentation:
    active = list(variants) if variants is not None else active_export_variants(config)
    fmt = str(config.format).upper()
    size = f"{config.output_width}×{config.output_height}"
    if active:
        first = active[0]
        bg_text = "transparente" if first.transparent_bg else rgb_to_hex(first.bg_color)
    else:
        bg_text = "sin salida activa"

    return TextPresentation(
        format_export_summary(config, active),
        (
            f"Formato general: {fmt}\n"
            f"Tamaño: {size} px\n"
            f"Fondo mostrado: {bg_text}\n"
            f"Plantilla: {config.naming_template}"
        ),
    )


def format_outputs_summary(variants: Iterable[ExportVariant]) -> TextPresentation:
    active = list(variants)
    if not active:
        return TextPresentation("Salidas: ninguna activa", "Activa al menos una versión de salida.")

    compact = " + ".join(variant.label for variant in active)
    detail_lines = []
    for variant in active:
        bg = "transparente" if variant.transparent_bg else rgb_to_hex(variant.bg_color)
        suffix = variant.suffix or "(sin sufijo)"
        shadow = ""
        if variant.shadow_opacity_override is not None:
            shadow = f" · sombra {variant.shadow_opacity_override}"
        elif variant.shadow_opacity_delta:
            shadow = f" · sombra {variant.shadow_opacity_delta:+d}"
        detail_lines.append(f"{variant.label}: {bg} · {suffix}{shadow}")

    return TextPresentation(f"Salidas: {compact}", "\n".join(detail_lines))


def can_process_batch(
    folders_count: int,
    images_count: int,
    active_outputs_count: int,
    *,
    is_processing: bool = False,
) -> bool:
    return (
        int(folders_count) > 0
        and int(images_count) > 0
        and int(active_outputs_count) > 0
        and not is_processing
    )


def format_processing_status(
    folders_count: int,
    images_count: int,
    mode: str,
    *,
    export_status_text: str = "",
    pre_render_status: tuple[str, int, int] | None = None,
) -> ProcessingStatusPresentation:
    folders = int(folders_count)
    images = int(images_count)

    if folders <= 0:
        return ProcessingStatusPresentation("Añade una carpeta para procesar")
    if images <= 0:
        return ProcessingStatusPresentation("No hay PNG válidos")
    if mode == "processing":
        return ProcessingStatusPresentation(export_status_text or "Procesando...", True)
    if mode == "paused":
        return ProcessingStatusPresentation("Pausado", True)
    if mode == "stopping":
        return ProcessingStatusPresentation("Deteniendo...", True)
    if pre_render_status:
        status, prepared, total = pre_render_status
        if total > 0:
            return ProcessingStatusPresentation(status, True, int((prepared / total) * 100))
        return ProcessingStatusPresentation(status, False)

    return ProcessingStatusPresentation("Listo para procesar")
