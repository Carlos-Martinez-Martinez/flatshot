"""Qt-free service for building and validating export configuration."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

from flatshot.core.models import (
    MAX_EXPORT_PIXELS,
    MAX_EXPORT_SIDE,
    ExportConfig,
    ExportVariant,
    normalize_export_variants,
)


class ExportConfigService:
    """Build and validate export configuration without widget dependencies."""

    def build_from_settings(
        self,
        app_settings: Mapping[str, Any],
        *,
        variants: Iterable[ExportVariant] | None = None,
        output_destination_override: str | None = None,
        custom_output_path_override: str | Path | None = None,
    ) -> ExportConfig:
        output_destination = output_destination_override or str(
            app_settings.get("output_destination", "subfolder")
        )
        custom_output_path = (
            str(custom_output_path_override)
            if custom_output_path_override
            else app_settings.get("custom_output_path")
        )

        return ExportConfig(
            output_folder_name=app_settings.get("output_folder_name", "_SALIDA_PRO"),
            suffix=app_settings.get("suffix", "_PRO"),
            format=self._normalize_format(app_settings.get("format", "JPG")),
            transparent_bg=app_settings.get("transparent_bg", False),
            bg_color=app_settings.get("bg_color", (230, 230, 230)),
            variants=list(variants) if variants is not None else app_settings.get("variants", []),
            output_width=int(app_settings.get("output_width", 1800)),
            output_height=int(app_settings.get("output_height", 2400)),
            naming_template=app_settings.get("naming_template", "{original}{suffix}"),
            output_destination=output_destination,
            custom_output_path=str(custom_output_path) if custom_output_path else None,
        )

    def validate(self, config: ExportConfig) -> list[str]:
        errors: list[str] = []
        fmt = self._normalize_format(config.format)
        active_variants = [variant for variant in normalize_export_variants(config) if variant.enabled]

        if fmt not in {"JPG", "PNG"}:
            errors.append("El formato de exportación debe ser JPG o PNG.")
        if int(config.output_width) <= 0 or int(config.output_height) <= 0:
            errors.append("El tamaño de exportación debe ser positivo.")
        if int(config.output_width) > MAX_EXPORT_SIDE or int(config.output_height) > MAX_EXPORT_SIDE:
            errors.append(f"El lado de exportación no puede superar {MAX_EXPORT_SIDE}px.")
        if int(config.output_width) * int(config.output_height) > MAX_EXPORT_PIXELS:
            errors.append(f"El área de exportación no puede superar {MAX_EXPORT_PIXELS:,} píxeles.")
        if config.output_destination not in {"subfolder", "custom"}:
            errors.append("El destino de exportación debe ser subfolder o custom.")
        if config.output_destination == "custom" and not config.custom_output_path:
            errors.append("El destino personalizado requiere una carpeta.")
        if config.output_destination == "subfolder" and not str(config.output_folder_name).strip():
            errors.append("El nombre de la subcarpeta de salida no puede estar vacío.")
        if not str(config.naming_template or "").strip():
            errors.append("La plantilla de nombre no puede estar vacía.")
        if not active_variants:
            errors.append("Activa al menos una salida de exportación.")

        for variant in active_variants:
            variant_format = self._normalize_format(variant.format or config.format)
            destination_mode = variant.output_destination or config.output_destination
            custom_output_path = variant.custom_output_path or config.custom_output_path
            output_folder_name = variant.output_folder_name or config.output_folder_name
            naming_template = variant.naming_template or config.naming_template
            output_width = int(variant.output_width or config.output_width)
            output_height = int(variant.output_height or config.output_height)

            if variant_format not in {"JPG", "PNG"}:
                errors.append(f"{variant.label}: el formato debe ser JPG o PNG.")
            if output_width <= 0 or output_height <= 0:
                errors.append(f"{variant.label}: el tamaño de exportación debe ser positivo.")
            if output_width > MAX_EXPORT_SIDE or output_height > MAX_EXPORT_SIDE:
                errors.append(f"{variant.label}: ningún lado puede superar {MAX_EXPORT_SIDE}px.")
            if output_width * output_height > MAX_EXPORT_PIXELS:
                errors.append(f"{variant.label}: el área supera {MAX_EXPORT_PIXELS:,} píxeles.")
            if destination_mode not in {"subfolder", "custom"}:
                errors.append(f"{variant.label}: el destino debe ser subfolder o custom.")
            if (
                destination_mode == "custom"
                and not custom_output_path
                and variant.output_destination == "custom"
            ):
                errors.append(f"{variant.label}: el destino personalizado requiere una carpeta.")
            if destination_mode == "subfolder" and not str(output_folder_name or "").strip():
                errors.append(f"{variant.label}: la subcarpeta de salida no puede estar vacía.")
            if not str(naming_template or "").strip():
                errors.append(f"{variant.label}: la plantilla de nombre no puede estar vacía.")

        return errors

    def destinations_for_folders(
        self,
        folders: Iterable[str | Path],
        config: ExportConfig,
    ) -> list[Path]:
        active_variants = [variant for variant in normalize_export_variants(config) if variant.enabled]
        destinations: list[Path] = []
        seen: set[str] = set()

        for folder in folders:
            input_folder = Path(folder)
            for variant in active_variants:
                base_destination = variant_base_destination(input_folder, config, variant)
                if base_destination is None:
                    continue
                destination = variant_output_folder(base_destination, variant)
                key = str(destination)
                if key in seen:
                    continue
                seen.add(key)
                destinations.append(destination)

        return destinations

    @staticmethod
    def _normalize_format(value: Any) -> str:
        text = str(value or "JPG").strip().upper().lstrip(".")
        if text == "JPEG":
            return "JPG"
        return text


def variant_base_destination(
    input_folder: Path,
    config: ExportConfig,
    variant: ExportVariant,
) -> Path | None:
    output_destination = variant.output_destination or config.output_destination
    if output_destination == "custom":
        custom_output_path = variant.custom_output_path or config.custom_output_path
        return Path(custom_output_path) if custom_output_path else None
    output_folder_name = variant.output_folder_name or config.output_folder_name
    return input_folder / output_folder_name


def variant_output_folder(base_output_folder: Path, variant: ExportVariant) -> Path:
    if variant.output_subfolder:
        return base_output_folder / variant.output_subfolder
    return base_output_folder
