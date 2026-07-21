import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
CONTROLLER_PATH = FRONTEND_DIR / "app-bridge-scan-controller.js"


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend flow checks")
def test_folder_picker_scans_the_selected_path_immediately():
    script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

global.state = {{
  bridgeScanPath: "C:/old",
  bridgeStatus: "idle",
  scanStatus: "Sin lote",
  statusText: "Sin lote",
}};
global.scanStateHelpers = {{
  folderPickStartState: () => ({{
    bridgeStatus: "checking",
    bridgeLastResponse: "Solicitando /folders/pick",
    scanStatus: "Elige una carpeta",
    statusText: "Elige una carpeta",
  }}),
  folderPickCancelledState: () => ({{}}),
  folderPickSelectedState: (path) => ({{
    bridgeStatus: "connected",
    bridgeScanPath: path,
    bridgeMessage: "Carpeta seleccionada",
    bridgeLastResponse: "folder pick OK",
    scanStatus: "Carpeta lista para escanear",
    statusText: "Carpeta lista para escanear",
  }}),
  folderPickErrorState: (message) => ({{ statusText: message }}),
}};
global.bridgeRequest = async (path) => {{
  assert.equal(path, "/folders/pick");
  return {{ selected: true, path: "C:/new batch" }};
}};
global.renderCalls = 0;
global.render = () => {{ renderCalls += 1; }};
global.window = {{ localStorage: {{}} }};
global.storageHelpers = {{
  writeValue: (storage, key, value) => {{
    assert.equal(storage, global.window.localStorage);
    global.persisted = [key, value];
  }},
}};
global.STORAGE_KEYS = {{ bridgeScanPath: "bridgeScanPath" }};
global.scheduleBridgeUiPreferencesSave = () => {{ global.savedPrefs = true; }};
global.bridgeErrorMessage = (error) => error.message;
vm.runInThisContext(fs.readFileSync({json.dumps(str(CONTROLLER_PATH))}, "utf8"));
let scanCalls = 0;
global.scanBridgeFolder = async () => {{ scanCalls += 1; }};

(async () => {{
  await pickBridgeFolder();
  assert.equal(state.bridgeScanPath, "C:/new batch");
  assert.equal(state.statusText, "Carpeta lista para escanear");
  assert.deepEqual(global.persisted, ["bridgeScanPath", "C:/new batch"]);
  assert.equal(global.savedPrefs, true);
  assert.equal(renderCalls, 2);
  assert.equal(scanCalls, 1);
}})().catch((error) => {{
  console.error(error);
  process.exitCode = 1;
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
