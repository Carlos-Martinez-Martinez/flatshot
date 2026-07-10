"""Preset bridge operations for FlatShotBridgeService."""
from __future__ import annotations

from typing import Any, Mapping

from flatshot.application.preset_service import PresetService
from flatshot.bridge.errors import InvalidRequestError
from flatshot.bridge.payload_helpers import preview_settings, required_string
from flatshot.bridge.serialization import categorized_presets_to_dict
from flatshot.core.models import SHADOW_ENGINE_DEFAULT, normalize_shadow_settings


def list_presets(service) -> dict[str, Any]:
    config_dir = service.config_resolver.config_dir(create=False)
    source = "defaults"
    warning = None

    if config_dir.exists() and not config_dir.is_dir():
        categorized = PresetService.get_default_categorized_presets()
        warning = "Config path is not a directory. Default presets returned."
    elif config_dir.exists():
        preset_service = PresetService(config_dir)
        if preset_service.categorized_presets_path.exists():
            categorized = preset_service.load_categorized_presets()
            source = "config"
        elif preset_service.presets_path.exists():
            categorized = preset_service.categorize_flat_presets(preset_service.load_presets())
            source = "legacy-config"
        else:
            categorized = PresetService.get_default_categorized_presets()
    else:
        categorized = PresetService.get_default_categorized_presets()

    payload = categorized_presets_to_dict(categorized)
    payload["source"] = source
    if warning:
        payload["warning"] = warning
    return payload


def save_preset(service, payload: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise InvalidRequestError("Expected a JSON object.")

    name = required_string(payload.get("name"), "name")
    raw_settings = payload.get("settings")
    if not isinstance(raw_settings, Mapping):
        raise InvalidRequestError("Field 'settings' must be an object.")

    try:
        settings = normalize_shadow_settings(
            preview_settings(raw_settings),
            missing_engine=SHADOW_ENGINE_DEFAULT,
        ).model_dump()
    except InvalidRequestError:
        raise
    except Exception as exc:
        raise InvalidRequestError("Field 'settings' contains invalid preset values.") from exc

    preset_service = service._writable_preset_service()
    with preset_service.write_lock:
        flat_presets = preset_service.load_flat_presets()
        updated = PresetService.save_current_preset(flat_presets, name, settings)
        preset_service.save_flat_presets_preserving_categories(updated)

    response = list_presets(service)
    response["ok"] = True
    response["activePreset"] = name
    return response


def delete_preset(service, payload: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise InvalidRequestError("Expected a JSON object.")

    name = required_string(payload.get("name"), "name")
    preset_service = service._writable_preset_service()
    with preset_service.write_lock:
        flat_presets = preset_service.load_flat_presets()
        if len(flat_presets) <= 1:
            raise InvalidRequestError("At least one preset must remain.")

        try:
            updated = PresetService.delete_preset(flat_presets, name)
        except ValueError as exc:
            raise InvalidRequestError(str(exc)) from exc

        preset_service.save_flat_presets_preserving_categories(updated)
    response = list_presets(service)
    response["ok"] = True
    response["activePreset"] = response["items"][0]["name"] if response.get("items") else None
    return response
