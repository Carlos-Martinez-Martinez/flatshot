import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "app-state.js"
INDEX_PATH = FRONTEND_DIR / "index.html"
MOCK_DATA_PATH = FRONTEND_DIR / "mock-data.js"


def test_app_state_helper_loads_before_mock_data_and_app():
    html = INDEX_PATH.read_text(encoding="utf-8")

    helper_index = html.index("app-state.js")
    mock_data_index = html.index("mock-data.js")
    app_index = html.index("app.js")

    assert helper_index < mock_data_index < app_index


def test_mock_data_exposes_app_state_helpers():
    source = MOCK_DATA_PATH.read_text(encoding="utf-8")

    assert "global.appStateHelpers = window.FlatShotAppState;" in source


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_app_state_helpers_keep_selection_validation_and_readiness_contracts():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

const mockImages = [{{ id: "m", exportable: true, status: "ready", name: "mock.png" }}];
const realImages = [
  {{ id: "a", exportable: true, status: "ready", name: "shirt.png", detail: "PNG · 800x900" }},
  {{ id: "b", exportable: true, status: "warning", name: "warn.png", width: 1200, height: 1400 }},
  {{ id: "c", exportable: false, status: "error", name: "bad.png" }},
];
const state = {{
  batch: "ready",
  batchSource: "bridge",
  realImages,
  realFolders: [{{ id: "folder" }}],
  selectedImageId: "a",
  exportCompletedItems: [
    {{ name: "shirt.jpg", success: true }},
    {{ name: "bad.png", success: false }},
  ],
  errors: [],
  activePreset: "Luz",
  naming: "{{original}}{{suffix}}",
  destinationMode: "source",
  destinationValue: "Salida",
  exportStatus: "blocked",
  previewStatus: "empty",
}};

assert.equal(helpers.hasBatch(state), true);
assert.equal(helpers.isBridgeBatch(state), true);
assert.deepEqual(helpers.activeImages(state, {{ mockImages }}), realImages);
assert.deepEqual(helpers.activeFolders(state, {{ mockFolders: [] }}), [{{ id: "folder" }}]);
assert.deepEqual(helpers.selectedImage(state, {{ mockImages }}), realImages[0]);
assert.deepEqual(helpers.exportableImages(realImages), realImages.slice(0, 2));
assert.deepEqual(helpers.exportItemState(realImages[0], state.exportCompletedItems), {{ status: "exported", label: "Exportada" }});
assert.deepEqual(helpers.exportItemState(realImages[2], state.exportCompletedItems), {{ status: "error", label: "Error" }});
assert.equal(helpers.exportItemStatusMap(realImages, state.exportCompletedItems).get("c").status, "error");

const issues = helpers.validationIssues({{
  state,
  exportableImages: realImages.slice(0, 2),
  exportOutputProfiles: [
    {{ name: "JPG", raw: {{ ok: true }} }},
    {{ name: "PNG", raw: {{ ok: false }} }},
  ],
  outputProfileValidation: (raw) => raw.ok ? {{ errors: [] }} : {{ errors: ["Falta destino"] }},
  outputProfileRawFromProfile: (profile) => profile.raw,
}});
assert.deepEqual(issues, [
  {{ level: "error", title: "Formato incompleto", detail: "PNG: Falta destino" }},
]);

assert.deepEqual(helpers.imageDimensions({{ detail: "PNG · 1800×2400" }}), {{ width: 1800, height: 2400 }});
assert.equal(helpers.lowResolutionImageCount({{
  images: realImages,
  targets: [{{ width: 1000, height: 1000 }}],
}}), 1);

assert.deepEqual(helpers.uiState({{
  state: {{ ...state, exportStatus: "running" }},
  counts: {{ warnings: 1 }},
  lotCounts: {{ nonBlockingWarnings: 2, blockingErrors: 0 }},
  selectedImage: realImages[0],
  hasBatch: true,
  canExport: true,
}}), {{
  hasBatch: true,
  hasBatchContext: true,
  hasSelectedImage: true,
  isBridgeReady: false,
  canExport: true,
  hasWarnings: true,
  hasBlockingErrors: false,
  isProcessing: true,
  isExporting: true,
}});
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
