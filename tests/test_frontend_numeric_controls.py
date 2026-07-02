import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend event checks")
def test_document_number_input_defers_commit_until_change():
    script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const frontend = {json.dumps(str(FRONTEND_DIR))};

let settingCommits = [];
let localCommits = [];
global.syncRangeFill = () => {{}};
global.updateSettingFromNumberInput = (target, options = {{}}) => {{
  settingCommits.push({{ value: target.value, commit: Boolean(options.commit) }});
}};
global.updateLocalOverrideFromNumberInput = (target, options = {{}}) => {{
  localCommits.push({{ value: target.value, commit: Boolean(options.commit) }});
}};
global.updateBackgroundPresetEditorFromFields = () => {{}};
global.updateOutputProfileDraftFromForm = () => {{}};
global.renderOutputProfileModalState = () => {{}};
global.applyOutputProfile = () => {{}};
global.applyPresetSettings = () => {{}};
global.backgroundPresetHelpers = {{ normalizePreviewBackgroundValue: () => "rgb230", previewBackgroundLabel: () => "gris claro" }};
global.backgroundHelperOptions = () => {{}};
global.previewCustomBackgroundValue = () => "rgb230";
global.settingsViewHelpers = {{ backgroundLabel: () => "gris claro" }};
global.render = () => {{}};
global.$ = () => null;
global.state = {{ bridgeScanPath: "", previewBg: "rgb230", statusText: "" }};

vm.runInThisContext(fs.readFileSync(path.join(frontend, "app-document-events.js"), "utf8"));

function target(dataset, value = "42") {{
  return {{
    id: "",
    value,
    dataset,
    matches: () => false,
    closest: () => null,
  }};
}}

const settingTarget = target({{ settingNumber: "opacity" }});
handleDocumentInput({{ target: settingTarget }});
assert.equal(settingCommits.length, 0);
handleDocumentChange({{ target: settingTarget }});
assert.deepEqual(settingCommits, [{{ value: "42", commit: true }}]);

const localTarget = target({{ localSettingNumber: "size_delta" }}, "-4");
handleDocumentInput({{ target: localTarget }});
assert.equal(localCommits.length, 0);
handleDocumentChange({{ target: localTarget }});
assert.deepEqual(localCommits, [{{ value: "-4", commit: true }}]);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend event checks")
def test_numeric_control_keyboard_commit_and_cancel_prevent_global_escape():
    script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const frontend = {json.dumps(str(FRONTEND_DIR))};

class HTMLInputElement {{}}
class HTMLTextAreaElement {{}}
class HTMLSelectElement {{}}
global.HTMLInputElement = HTMLInputElement;
global.HTMLTextAreaElement = HTMLTextAreaElement;
global.HTMLSelectElement = HTMLSelectElement;
global.trapOpenModalFocus = () => false;
global.$ = () => null;
global.state = {{
  appSettingsOpen: false,
  batchDetailOpen: false,
  exportConfirmOpen: false,
  exportStatus: "idle",
}};
global.isExportReady = () => false;
global.startExport = () => {{}};
global.closeExportConfirm = () => {{}};
global.closeBatchDetail = () => {{}};
global.closeAppSettings = () => {{}};
global.confirmExportFromModal = () => {{}};
global.selectAdjacentImage = () => {{}};
global.selectEdgeImage = () => {{}};
global.isNumericControlInput = (target) => Boolean(target?.dataset?.settingNumber);
let commits = 0;
let cancels = 0;
global.commitNumericControlInput = () => {{
  commits += 1;
  return true;
}};
global.cancelNumericControlInput = () => {{
  cancels += 1;
  return true;
}};
const openDetails = {{ open: true }};
global.document = {{
  querySelectorAll: () => [openDetails],
}};

vm.runInThisContext(fs.readFileSync(path.join(frontend, "app-viewer-events.js"), "utf8"));

const numericTarget = new HTMLInputElement();
numericTarget.dataset = {{ settingNumber: "opacity" }};
numericTarget.isContentEditable = false;

let enterPrevented = false;
handleDocumentKeydown({{
  key: "Enter",
  target: numericTarget,
  ctrlKey: false,
  metaKey: false,
  preventDefault: () => {{ enterPrevented = true; }},
}});
assert.equal(commits, 1);
assert.equal(enterPrevented, true);

let escapePrevented = false;
handleDocumentKeydown({{
  key: "Escape",
  target: numericTarget,
  ctrlKey: false,
  metaKey: false,
  preventDefault: () => {{ escapePrevented = true; }},
}});
assert.equal(cancels, 1);
assert.equal(escapePrevented, true);
assert.equal(openDetails.open, true);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend event checks")
def test_lighting_number_input_defers_commit_until_change():
    script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const frontend = {json.dumps(str(FRONTEND_DIR))};

global.numberHelpers = require(path.join(frontend, "number-utils.js"));
global.cloneLightingScene = (scene) => JSON.parse(JSON.stringify(scene));
global.lightingScenesEqual = (first, second) => JSON.stringify(first) === JSON.stringify(second);
global.state = {{
  settings: {{
    lighting_scene: {{
      main: {{ type: "softbox", x: 0, y: 0, height: 0.65, size: 0.55, intensity: 0.85 }},
      ambient_intensity: 0.25,
    }},
  }},
}};
let dirtyCount = 0;
global.markPresetDirty = () => {{
  dirtyCount += 1;
}};

vm.runInThisContext(fs.readFileSync(path.join(frontend, "app-form-events.js"), "utf8"));

const input = {{
  value: "77",
  min: "0",
  max: "100",
  disabled: false,
  dataset: {{ lightingNumberField: "main.height" }},
}};

handleLightingNumberFieldInput({{ type: "input", target: input }});
assert.equal(state.settings.lighting_scene.main.height, 0.65);
assert.equal(dirtyCount, 0);

handleLightingNumberFieldInput({{ type: "change", target: input }});
assert.equal(state.settings.lighting_scene.main.height, 0.77);
assert.equal(input.value, "77");
assert.equal(dirtyCount, 1);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
