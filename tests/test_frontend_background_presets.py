import json
import shutil
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "background-presets.js"
INDEX_PATH = FRONTEND_DIR / "index.html"
APP_GLOBALS_PATH = FRONTEND_DIR / "app-globals.js"


def test_background_preset_helper_loads_before_mock_data_and_app():
    html = INDEX_PATH.read_text(encoding="utf-8")

    helper_index = html.index("background-presets.js")
    mock_data_index = html.index("mock-data.js")
    app_index = html.index("app.js")

    assert helper_index < mock_data_index < app_index


def test_app_globals_exposes_background_preset_helpers():
    source = APP_GLOBALS_PATH.read_text(encoding="utf-8")

    assert "global.backgroundPresetHelpers = window.FlatShotBackgroundPresets;" in source


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_background_preset_helpers_keep_preview_and_preset_contracts():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

const defaultPresets = [
  {{ id: "rgb230", name: "Gris claro", kind: "rgb", rgb: [230, 230, 230] }},
  {{ id: "white", name: "Blanco", kind: "rgb", rgb: [255, 255, 255] }},
  {{ id: "transparent", name: "Transparente", kind: "transparent", rgb: [230, 230, 230] }},
];

assert.equal(helpers.normalizePreviewBackgroundValue("soft-black"), "soft-black");
assert.equal(helpers.normalizePreviewBackgroundValue("rgb:12,34,56"), "rgb:12,34,56");
assert.equal(helpers.normalizePreviewBackgroundValue("bad"), "rgb230");
assert.equal(helpers.backgroundCssColor("rgb:12,34,56"), "rgb(12, 34, 56)");
assert.equal(helpers.backgroundCssColor("soft-black"), "rgb(32, 34, 37)");
assert.equal(helpers.backgroundVisualMode("transparent"), "transparent");
assert.equal(helpers.backgroundVisualMode("rgb:12,34,56"), "custom");
assert.deepEqual(helpers.previewCustomRgbChannels("soft-black"), [32, 34, 37]);
assert.deepEqual(helpers.previewCustomRgbChannels("white"), [255, 255, 255]);
assert.equal(helpers.previewBackgroundLabel("rgb:12,34,56", {{ backgroundLabel: () => "fallback" }}), "RGB 12, 34, 56");
assert.equal(helpers.previewBackgroundLabel("soft-black", {{ backgroundLabel: () => "fallback" }}), "negro suave");
assert.equal(helpers.previewBackgroundLabel("white", {{ backgroundLabel: (value) => `label:${{value}}` }}), "label:white");

const normalized = helpers.normalizeBackgroundPresetList([
  {{ id: "dup", name: "Canal", value: "rgb:10,20,30" }},
  {{ id: "dup", name: "Canal copia", rgb: [260, -1, 5] }},
  {{ name: "Trans", kind: "transparent" }},
], {{ defaultPresets }});
assert.deepEqual(normalized, [
  {{ id: "rgb230", kind: "rgb", name: "Gris claro", rgb: [230, 230, 230], system: true }},
  {{ id: "white", kind: "rgb", name: "Blanco", rgb: [255, 255, 255], system: true }},
  {{ id: "transparent", kind: "transparent", name: "Transparente", rgb: [230, 230, 230], system: true }},
  {{ id: "dup", kind: "rgb", name: "Canal", rgb: [10, 20, 30] }},
  {{ id: "dup-2", kind: "rgb", name: "Canal copia", rgb: [255, 0, 5] }},
  {{ id: "trans-2", kind: "transparent", name: "Trans", rgb: [230, 230, 230] }},
]);

const restored = helpers.normalizeBackgroundPresetList([
  {{ id: "white", name: "Blanco roto", kind: "rgb", rgb: [230, 230, 230] }},
  {{ id: "rgb230", name: "Gris roto", kind: "rgb", rgb: [245, 0, 0] }},
  {{ id: "transparent", name: "Trans roto", kind: "rgb", rgb: [1, 2, 3] }},
  {{ id: "marketplace", name: "Marketplace", kind: "rgb", rgb: [248, 248, 248] }},
], {{ defaultPresets }});
assert.deepEqual(restored, [
  {{ id: "rgb230", kind: "rgb", name: "Gris claro", rgb: [230, 230, 230], system: true }},
  {{ id: "white", kind: "rgb", name: "Blanco", rgb: [255, 255, 255], system: true }},
  {{ id: "transparent", kind: "transparent", name: "Transparente", rgb: [230, 230, 230], system: true }},
  {{ id: "marketplace", kind: "rgb", name: "Marketplace", rgb: [248, 248, 248] }},
]);
assert.equal(helpers.isSystemBackgroundPreset(restored[0], {{ defaultPresets }}), true);
assert.equal(helpers.isSystemBackgroundPreset(restored[3], {{ defaultPresets }}), false);
assert.deepEqual(helpers.backgroundPresetsForStorage(restored, {{ defaultPresets }}), [
  {{ id: "marketplace", kind: "rgb", name: "Marketplace", rgb: [248, 248, 248] }},
]);

assert.equal(helpers.backgroundPresetValue(restored[0]), "rgb230");
assert.equal(helpers.backgroundPresetValue(restored[1]), "white");
assert.equal(helpers.backgroundPresetValue(restored[2]), "transparent");
assert.equal(helpers.backgroundPresetValue({{ id: "custom", kind: "rgb", rgb: [12, 34, 56] }}), "rgb:12,34,56");
assert.equal(helpers.backgroundPresetLabel(null), "Fondo");

const html = helpers.backgroundSelectOptionsHtml("rgb:12,34,56", {{
  presets: defaultPresets,
  escapeHtml: (value) => String(value).replaceAll("&", "&amp;"),
  backgroundLabel: (value) => `Etiqueta ${{value}}`,
}});
assert.equal(html.includes("Actual · Etiqueta rgb:12,34,56"), true);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
