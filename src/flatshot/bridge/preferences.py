"""Desktop UI preference bridge operations."""
from __future__ import annotations

from typing import Any, Mapping

from flatshot.application.settings_service import SettingsService
from flatshot.bridge.errors import InvalidRequestError
from flatshot.bridge.payload_helpers import json_compatible

UI_PREFERENCES_SETTINGS_KEY = "desktop_ui_preferences"


def load_ui_preferences(service) -> dict[str, Any]:
    config_dir = service.config_resolver.config_dir(create=False)
    warning = None
    preferences: dict[str, Any] = {}

    if config_dir.exists() and not config_dir.is_dir():
        warning = "Config path is not a directory. UI preferences not loaded."
    elif config_dir.exists():
        settings = SettingsService(config_dir / "settings.json").load_existing(fallback={})
        raw_preferences = settings.get(UI_PREFERENCES_SETTINGS_KEY, {})
        if isinstance(raw_preferences, Mapping):
            preferences = dict(raw_preferences)

    response: dict[str, Any] = {
        "ok": True,
        "source": "config" if preferences else "defaults",
        "preferences": preferences,
    }
    if warning:
        response["warning"] = warning
    return response


def save_ui_preferences(service, payload: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise InvalidRequestError("Expected a JSON object.")

    settings_service = service._writable_settings_service()
    settings = settings_service.load()
    settings[UI_PREFERENCES_SETTINGS_KEY] = json_compatible(payload)
    settings_service.save(settings)

    response = load_ui_preferences(service)
    response["ok"] = True
    return response
