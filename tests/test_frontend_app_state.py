import json
import shutil
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "app-state.js"
STORE_HELPER_PATH = FRONTEND_DIR / "state-stores.js"
STORE_ES_MODULE_PATH = FRONTEND_DIR / "state-stores.mjs"
INDEX_PATH = FRONTEND_DIR / "index.html"
APP_GLOBALS_PATH = FRONTEND_DIR / "app-globals.js"


def test_app_state_helper_loads_before_mock_data_and_app():
    html = INDEX_PATH.read_text(encoding="utf-8")

    store_helper_index = html.index("state-stores.js")
    helper_index = html.index("app-state.js")
    mock_data_index = html.index("mock-data.js")
    app_index = html.index("app.js")

    assert store_helper_index < helper_index < mock_data_index < app_index


def test_state_stores_es_module_is_loaded_without_replacing_classic_boot_contract():
    html = INDEX_PATH.read_text(encoding="utf-8")

    module_marker = '<script src="./state-stores.mjs?v=20260704-search-focus" type="module"></script>'

    assert STORE_ES_MODULE_PATH.exists()
    assert module_marker in html
    assert html.index("state-stores.mjs") < html.index("state-stores.js") < html.index("app-state.js")


def test_app_globals_exposes_app_state_helpers():
    source = APP_GLOBALS_PATH.read_text(encoding="utf-8")

    assert "global.appStateHelpers = window.FlatShotAppState;" in source


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_state_stores_es_module_matches_classic_helper_contract():
    script = f"""
const assert = require("node:assert/strict");
const {{ pathToFileURL }} = require("node:url");
const classic = require({json.dumps(str(STORE_HELPER_PATH))});

(async () => {{
  const esm = await import(pathToFileURL({json.dumps(str(STORE_ES_MODULE_PATH))}).href);
  const state = {{
    batch: "ready",
    batchSource: "bridge",
    selectedImageId: "a",
    previewStatus: "ready",
    exportStatus: "blocked",
    activePreset: "Luz",
    inspectorTab: "review",
    bridgeStatus: "connected",
    unknownKey: "excluded",
  }};

  assert.deepEqual(esm.storeNames(), classic.storeNames());
  for (const storeName of classic.storeNames()) {{
    assert.deepEqual(esm.stateStoreFields(storeName), classic.stateStoreFields(storeName));
  }}
  assert.deepEqual(esm.stateStoreSnapshot(state), classic.stateStoreSnapshot(state));
  assert.equal(JSON.stringify(esm.stateStoreSnapshot(state)).includes("unknownKey"), false);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
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


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_app_state_store_snapshots_split_global_state_by_domain():
    script = f"""
const assert = require("node:assert/strict");
const storeHelpers = require({json.dumps(str(STORE_HELPER_PATH))});
globalThis.FlatShotAppStateStores = storeHelpers;
const helpers = require({json.dumps(str(HELPER_PATH))});

const state = {{
  batch: "ready",
  batchSource: "bridge",
  realImages: [{{ id: "a" }}],
  selectedImageId: "a",
  selectedImageIds: ["a"],
  previewStatus: "ready",
  previewData: {{ width: 100 }},
  exportStatus: "blocked",
  exportJobId: "job-1",
  activePreset: "Luz",
  outputProfiles: [{{ id: "web" }}],
  inspectorTab: "review",
  statusText: "Listo",
  bridgeStatus: "connected",
  bridgeUrl: "http://127.0.0.1:8765",
  unknownKey: "not included",
}};

assert.deepEqual(storeHelpers.storeNames(), [
  "batch",
  "selection",
  "preview",
  "export",
  "settings",
  "ui",
  "bridge",
]);
assert.deepEqual(storeHelpers.stateStoreFields("selection"), [
  "selectedImageId",
  "selectedImageIds",
  "selectionAnchorImageId",
  "filter",
  "search",
  "galleryView",
  "galleryScrollTop",
]);

const snapshot = helpers.stateStoreSnapshot(state);
assert.deepEqual(Object.keys(snapshot), storeHelpers.storeNames());
assert.deepEqual(snapshot.batch, {{
  batch: "ready",
  batchSource: "bridge",
  realImages: [{{ id: "a" }}],
}});
assert.deepEqual(snapshot.selection, {{
  selectedImageId: "a",
  selectedImageIds: ["a"],
}});
assert.deepEqual(snapshot.preview, {{
  previewStatus: "ready",
  previewData: {{ width: 100 }},
}});
assert.deepEqual(snapshot.export, {{
  exportStatus: "blocked",
  exportJobId: "job-1",
}});
assert.deepEqual(snapshot.settings, {{
  activePreset: "Luz",
  outputProfiles: [{{ id: "web" }}],
}});
assert.deepEqual(snapshot.ui, {{
  inspectorTab: "review",
  statusText: "Listo",
}});
assert.deepEqual(snapshot.bridge, {{
  bridgeStatus: "connected",
  bridgeUrl: "http://127.0.0.1:8765",
}});
assert.equal(JSON.stringify(snapshot).includes("unknownKey"), false);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout


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
  {{ level: "error", title: "Salida incompleta", detail: "PNG: Falta destino" }},
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
