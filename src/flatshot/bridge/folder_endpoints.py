"""Folder-opening bridge endpoints."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping

from flatshot.bridge.errors import BridgeError, InvalidRequestError
from flatshot.bridge.onboarding_assets import onboarding_assets_folder
from flatshot.bridge.path_policy import TrustedPathPolicy
from flatshot.bridge.serialization import serialize_path


def open_onboarding_assets_folder(folder_opener: Callable[[Path], None]) -> dict[str, Any]:
    folder = onboarding_assets_folder()
    try:
        folder.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise BridgeError("folder_open_unavailable", "No se pudo preparar la carpeta de fondos.", status=503) from exc
    _open_folder(folder, folder_opener, error_message="No se pudo abrir la carpeta de fondos.")
    return {"ok": True, "path": serialize_path(folder)}


def open_folder(
    payload: Mapping[str, Any],
    *,
    path_policy: TrustedPathPolicy,
    folder_opener: Callable[[Path], None],
) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise InvalidRequestError("Expected a JSON object.")
    raw_path = payload.get("path")
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise InvalidRequestError("Field 'path' must be a folder path.")

    folder = Path(raw_path).expanduser()
    path_policy.validate_output_path(folder)
    try:
        if folder.is_file():
            folder = folder.parent
        if not folder.exists() or not folder.is_dir():
            raise BridgeError("folder_not_found", "Carpeta de salida no disponible.", status=404)
    except BridgeError:
        raise
    except OSError as exc:
        raise BridgeError("folder_open_unavailable", "No se pudo comprobar la carpeta de salida.", status=503) from exc

    _open_folder(folder, folder_opener, error_message="No se pudo abrir la carpeta de salida.")
    return {"ok": True, "path": serialize_path(folder)}


def reveal_path(
    payload: Mapping[str, Any],
    *,
    path_policy: TrustedPathPolicy,
    path_revealer: Callable[[Path], None],
) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise InvalidRequestError("Expected a JSON object.")
    raw_path = payload.get("path")
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise InvalidRequestError("Field 'path' must be an output path.")

    path = Path(raw_path).expanduser()
    path_policy.validate_output_path(path)
    try:
        if not path.exists():
            raise BridgeError("output_path_not_found", "Salida no disponible.", status=404)
    except BridgeError:
        raise
    except OSError as exc:
        raise BridgeError("folder_open_unavailable", "No se pudo comprobar la salida.", status=503) from exc

    _reveal_path(path, path_revealer, error_message="No se pudo localizar la salida.")
    return {"ok": True, "path": serialize_path(path)}


def _open_folder(folder: Path, folder_opener: Callable[[Path], None], *, error_message: str) -> None:
    try:
        folder_opener(folder)
    except BridgeError:
        raise
    except Exception as exc:
        raise BridgeError("folder_open_unavailable", error_message, status=503) from exc


def _reveal_path(path: Path, path_revealer: Callable[[Path], None], *, error_message: str) -> None:
    try:
        path_revealer(path)
    except BridgeError:
        raise
    except Exception as exc:
        raise BridgeError("folder_open_unavailable", error_message, status=503) from exc
