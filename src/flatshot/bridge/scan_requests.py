"""Parse folder scan bridge payloads."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from flatshot.bridge.errors import InvalidRequestError
from flatshot.bridge.path_policy import TrustedPathPolicy


def parse_scan_request(payload: Mapping[str, Any], path_policy: TrustedPathPolicy) -> tuple[list[Path], dict, bool, bool]:
    if not isinstance(payload, Mapping):
        raise InvalidRequestError("Expected a JSON object.")

    raw_folders = payload.get("folders")
    if not isinstance(raw_folders, list):
        raise InvalidRequestError("Field 'folders' must be a list of paths.")

    folders: list[Path] = []
    for index, folder in enumerate(raw_folders):
        if not isinstance(folder, str) or not folder.strip():
            raise InvalidRequestError(f"Field 'folders[{index}]' must be a non-empty path string.")
        path = Path(folder).expanduser()
        folders.append(path)
        path_policy.register_root(path)

    image_overrides = payload.get("imageOverrides", {})
    if image_overrides is None:
        image_overrides = {}
    if not isinstance(image_overrides, Mapping):
        raise InvalidRequestError("Field 'imageOverrides' must be an object when provided.")

    scan_mode = str(payload.get("scanMode") or "verified").strip().lower()
    if scan_mode not in {"verified", "fast"}:
        raise InvalidRequestError("Field 'scanMode' must be 'verified' or 'fast'.")
    verify_images = scan_mode != "fast"
    if isinstance(payload.get("verifyImages"), bool):
        verify_images = bool(payload["verifyImages"])

    return folders, dict(image_overrides), verify_images, bool(payload.get("recursive"))
