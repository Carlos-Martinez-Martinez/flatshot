"""Build export requests from bridge payloads."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from flatshot.application.contracts import ExportJobRequest
from flatshot.application.export_runner import OutputPathValidationError, validate_export_requests_outputs
from flatshot.bridge.errors import BridgeError, InvalidRequestError
from flatshot.bridge.payload_helpers import (
    backgroundColorTuple,
    export_size,
    optional_string,
    preview_settings,
)
from flatshot.bridge.validation import export_image_paths
from flatshot.core.models import SHADOW_ENGINE_DEFAULT, ExportConfig, normalize_shadow_settings
from flatshot.core.overrides import normalize_image_override


def build_export_requests(service, payload: Mapping[str, Any]) -> tuple[list[ExportJobRequest], ExportConfig]:
    if not isinstance(payload, Mapping):
        raise InvalidRequestError("Expected a JSON object.")

    image_paths = export_image_paths(payload.get("imagePaths"))
    for image_path in image_paths:
        service._validate_image_path_access(image_path)
    settings = normalize_shadow_settings(
        preview_settings(payload.get("settings", {})),
        missing_engine=SHADOW_ENGINE_DEFAULT,
    )
    raw_image_overrides = payload.get("imageOverrides", {})
    if raw_image_overrides is None:
        raw_image_overrides = {}
    if not isinstance(raw_image_overrides, Mapping):
        raise InvalidRequestError("Field 'imageOverrides' must be an object when provided.")
    image_overrides = {
        str(key): normalized
        for key, value in raw_image_overrides.items()
        if (normalized := normalize_image_override(value))
    }
    export_config = build_export_config(service.export_config_service, payload.get("export", {}))
    errors = service.export_config_service.validate(export_config)
    if errors:
        raise InvalidRequestError(errors[0])

    grouped: dict[Path, list[Path]] = {}
    for image_path in image_paths:
        grouped.setdefault(image_path.parent, []).append(image_path)

    return (
        [
            ExportJobRequest(
                input_folder=folder,
                input_files=sorted(paths),
                settings=settings,
                export_config=export_config,
                curve_data=None,
                preset_name=optional_string(payload.get("presetName")),
                image_overrides=image_overrides,
            )
            for folder, paths in sorted(grouped.items(), key=lambda item: str(item[0]))
        ],
        export_config,
    )


def validate_export_outputs(requests: list[ExportJobRequest]) -> None:
    try:
        validate_export_requests_outputs(requests)
    except OutputPathValidationError as exc:
        raise BridgeError("export_output_collision", str(exc), status=409) from exc


def build_export_config(export_config_service, raw_export: Any) -> ExportConfig:
    if raw_export is None:
        raw_export = {}
    if not isinstance(raw_export, Mapping):
        raise InvalidRequestError("Field 'export' must be an object when provided.")

    width, height = export_size(raw_export)
    background = str(raw_export.get("background", "rgb230"))
    destination_mode = str(raw_export.get("destinationMode", "source"))
    destination_value = optional_string(raw_export.get("destinationValue"))
    output_destination = "custom" if destination_mode == "custom" else "subfolder"
    custom_output_path = optional_string(raw_export.get("customOutputPath")) or (
        destination_value if output_destination == "custom" else None
    )
    output_folder_name = (
        optional_string(raw_export.get("outputFolderName"))
        or (destination_value if output_destination == "subfolder" else None)
        or "_SALIDA_PRO"
    )

    settings = {
        "format": raw_export.get("format", "JPG"),
        "output_width": width,
        "output_height": height,
        "transparent_bg": background == "transparent",
        "bg_color": backgroundColorTuple(background),
        "output_folder_name": output_folder_name,
        "suffix": raw_export.get("suffix", "_PRO"),
        "naming_template": raw_export.get("namingTemplate", "{original}{suffix}"),
        "output_destination": output_destination,
        "custom_output_path": custom_output_path,
        "variants": raw_export.get("variants", []),
    }
    return export_config_service.build_from_settings(settings)
