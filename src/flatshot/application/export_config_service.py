"""Qt-free service for building and validating export configuration."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

from flatshot.core.models import ExportConfig, ExportVariant, normalize_export_variants


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

        if fmt not in {"JPG", "PNG"}:
            errors.append("El formato de exportación debe ser JPG o PNG.")
        if int(config.output_width) <= 0 or int(config.output_height) <= 0:
            errors.append("El tamaño de exportación debe ser positivo.")
        if config.output_destination not in {"subfolder", "custom"}:
            errors.append("El destino de exportación debe ser subfolder o custom.")
        if config.output_destination == "custom" and not config.custom_output_path:
            errors.append("El destino personalizado requiere una carpeta.")
        if config.output_destination == "subfolder" and not str(config.output_folder_name).strip():
            errors.append("El nombre de la subcarpeta de salida no puede estar vacío.")
        if not str(config.naming_template or "").strip():
            errors.append("La plantilla de nombre no puede estar vacía.")

        return errors

    def destinations_for_folders(
        self,
        folders: Iterable[str | Path],
        config: ExportConfig,
    ) -> list[Path]:
        base_destinations = self._base_destinations(folders, config)
        active_variants = [variant for variant in normalize_export_variants(config) if variant.enabled]
        destinations: list[Path] = []

        for base_destination in base_destinations:
            for variant in active_variants:
                destinations.append(self._variant_output_folder(base_destination, variant))

        return destinations

    def _base_destinations(
        self,
        folders: Iterable[str | Path],
        config: ExportConfig,
    ) -> list[Path]:
        if config.output_destination == "custom":
            return [Path(config.custom_output_path)] if config.custom_output_path else []
        return [Path(folder) / config.output_folder_name for folder in folders]

    @staticmethod
    def _variant_output_folder(base_output_folder: Path, variant: ExportVariant) -> Path:
        if variant.output_subfolder:
            return base_output_folder / variant.output_subfolder
        return base_output_folder

    @staticmethod
    def _normalize_format(value: Any) -> str:
        text = str(value or "JPG").strip().upper().lstrip(".")
        if text == "JPEG":
            return "JPG"
        return text
