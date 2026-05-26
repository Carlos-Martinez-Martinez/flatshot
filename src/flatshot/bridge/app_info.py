"""Bridge metadata and static capability contracts."""
from __future__ import annotations

from flatshot import __version__ as FLATSHOT_VERSION

BRIDGE_VERSION = "0.1.0"
BRIDGE_SERVICE_NAME = "flatshot-bridge"
BRIDGE_MODE = "development"


def app_info() -> dict:
    return {
        "name": "FlatShot",
        "version": FLATSHOT_VERSION,
        "bridgeVersion": BRIDGE_VERSION,
        "engine": "python",
        "ui": "modern-desktop-prototype",
    }


def capabilities() -> dict:
    return {
        "folderScan": True,
        "presetsRead": True,
        "presetsWrite": True,
        "previewRender": True,
        "thumbnailRender": True,
        "exportRun": True,
        "exportProgress": True,
        "nativeFolderPicker": False,
    }
