import json
import shutil
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "session-snapshot.js"
INDEX_PATH = FRONTEND_DIR / "index.html"
APP_GLOBALS_PATH = FRONTEND_DIR / "app-globals.js"


def test_session_snapshot_helper_loads_before_mock_data_and_app():
    html = INDEX_PATH.read_text(encoding="utf-8")

    helper_index = html.index("session-snapshot.js")
    mock_data_index = html.index("mock-data.js")
    app_index = html.index("app.js")

    assert helper_index < mock_data_index < app_index


def test_app_globals_exposes_session_snapshot_helpers():
    source = APP_GLOBALS_PATH.read_text(encoding="utf-8")

    assert "global.sessionSnapshotHelpers = window.FlatShotSessionSnapshot;" in source


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_session_snapshot_helpers_keep_snapshot_contracts():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

const state = {{
  batch: "ready",
  batchSource: "bridge",
  selectedImageId: "img-1",
  previewMode: "compare",
  previewBg: "rgb:12,34,56",
  guidesVisible: true,
  activeGuideSystemIds: ["center"],
  guideSystemOrderIds: ["center"],
  hiddenGuideSystemIds: ["margins"],
  guideSystems: [{{ id: "center", name: "Centro" }}],
  zoom: 125,
  fitZoom: 80,
  fitMode: "width",
  panX: 10,
  panY: -5,
  filter: "warnings",
  search: "camisa",
  galleryView: "list",
  inspectorTab: "output",
  inspectorCollapsed: true,
  activePreset: "Luz",
  presetOutputSettings: {{ a: 1 }},
  settings: {{ opacity: 20 }},
  presetDirty: true,
  presetSource: "Bridge",
  localOverride: true,
  outputProfiles: [{{ id: "p", enabled: true }}],
  backgroundPresets: [{{ id: "b" }}],
  activeOutputProfileId: "p",
  outputProfileEditorId: "p",
  outputProfileDraft: {{ id: "p" }},
  destinationMode: "source",
  destinationValue: "Salida",
  format: "JPG",
  size: "1800x2400",
  background: "rgb230",
  naming: "{{original}}",
  suffix: "_PRO",
  appSettingsOpen: false,
  batchDetailOpen: true,
  bridgeMode: "bridge",
  bridgeUrl: "http://127.0.0.1:8765",
  bridgeStatus: "connected",
  bridgeMessage: "OK",
  bridgeLastResponse: "health OK",
  bridgeCapabilitiesSummary: "cap",
  bridgeCapabilities: {{ ok: true }},
  bridgePresets: [{{ name: "Luz" }}],
  bridgePresetSource: "bridge",
  bridgePresetWarning: "",
  bridgeScanPath: "C:/in",
  scanStatus: "Escaneado",
  scanIssues: [{{ level: "warning" }}],
  scanDiagnostics: {{ totalFiles: 1 }},
  realFolders: [{{ id: "f" }}],
  realImages: [{{ id: "img-1", path: "C:/in/a.png" }}],
  imageOverrides: {{ "img-1": {{ size_delta: 5 }} }},
  omitted: "not copied",
}};

const snapshot = helpers.buildSessionSnapshot({{
  state,
  selectedImagePath: "C:/selected.png",
  fallbackSelectedImagePath: "C:/fallback.png",
  savedAt: 123,
}});
assert.equal(snapshot.version, 1);
assert.equal(snapshot.savedAt, 123);
assert.equal(snapshot.state.selectedImagePath, "C:/selected.png");
assert.equal(snapshot.state.guidesVisible, true);
assert.deepEqual(snapshot.state.activeGuideSystemIds, ["center"]);
assert.deepEqual(snapshot.state.guideSystemOrderIds, ["center"]);
assert.deepEqual(snapshot.state.hiddenGuideSystemIds, ["margins"]);
assert.deepEqual(snapshot.state.guideSystems, [{{ id: "center", name: "Centro" }}]);
assert.equal(snapshot.state.omitted, undefined);
assert.equal(snapshot.state.realImages.length, 1);
assert.equal(helpers.isSessionSnapshot(snapshot), true);
assert.equal(helpers.isSessionSnapshot({{ version: 2, state: {{}} }}), false);
assert.deepEqual(helpers.safeObject(null), {{}});
assert.deepEqual(helpers.safeObject([1, 2]), {{}});
assert.deepEqual(helpers.safeObject({{ ok: true }}), {{ ok: true }});

const restored = helpers.restoreSessionState(snapshot.state, {{
  currentState: {{ previewBg: "rgb230", activePreset: "Fallback" }},
  initialBridgeUrl: "http://runtime",
  defaultBridgeUrl: "http://default",
  defaultViewMode: "height",
  batchFilters: {{ all: "all", warnings: "warnings" }},
  viewModeLabels: {{ height: "Alto", width: "Ancho" }},
  defaultOutputProfiles: [{{ id: "fallback", enabled: true, format: "JPG", background: "rgb230", destinationMode: "source", destinationValue: "Salida", naming: "{{original}}", suffix: "_PRO" }}],
  normalizeBackgroundPresetList: (items) => items,
  normalizeGuideSystemList: (items) => items,
  normalizeActiveGuideSystemIds: (ids) => ids,
  normalizeGuideSystemOrderIds: (ids) => ids,
  normalizeHiddenGuideSystemIds: (ids) => ids,
  normalizeOutputProfileList: (items) => items,
  normalizePreviewBackgroundValue: (value) => value,
  normalizeSettings: (settings) => ({{ normalized: settings }}),
  normalizePresetItem: (item) => item && {{ ...item, normalized: true }},
  normalizeBridgeIssue: (issue) => ({{ ...issue, normalized: true }}),
  normalizeExportFormat: (value) => String(value).toUpperCase(),
  parseOutputSize: (value) => ({{ normalized: value }}),
  normalizeBackgroundValue: (value) => value,
  clampNumber: (value, min, max, fallback) => Number.isFinite(Number(value)) ? Math.max(min, Math.min(max, Number(value))) : fallback,
  resolveRuntimeBridgeUrl: ({{
    restoredBridgeUrl,
  }}) => restoredBridgeUrl || "http://resolved",
  emptyScanDiagnostics: () => ({{ totalFiles: 0, totalImages: 0, totalOmitted: 0, omitted: [] }}),
}});

assert.equal(restored.selectedPath, "C:/selected.png");
assert.equal(restored.patch.batch, "ready");
assert.equal(restored.patch.batchSource, "bridge");
assert.equal(restored.patch.previewBg, "rgb:12,34,56");
assert.equal(restored.patch.guidesVisible, true);
assert.deepEqual(restored.patch.activeGuideSystemIds, ["center"]);
assert.deepEqual(restored.patch.guideSystemOrderIds, ["center"]);
assert.deepEqual(restored.patch.hiddenGuideSystemIds, ["margins"]);
assert.deepEqual(restored.patch.guideSystems, [{{ id: "center", name: "Centro" }}]);
assert.equal(restored.patch.settings.normalized.opacity, 20);
assert.equal(restored.patch.bridgeUrl, "http://127.0.0.1:8765");
assert.equal(restored.patch.bridgePresets[0].normalized, true);
assert.equal(restored.patch.scanIssues[0].normalized, true);
assert.equal(restored.patch.exportStatus, "blocked");
assert.deepEqual(restored.patch.thumbnailErrors, []);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
