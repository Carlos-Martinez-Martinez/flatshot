import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
INDEX_PATH = FRONTEND_DIR / "index.html"


def test_dev_visual_scenarios_live_in_qa_lab_not_primary_batch_ui():
    html = INDEX_PATH.read_text(encoding="utf-8")

    assert 'data-action="load-mock-batch"' not in html
    assert '<details class="review-panel dev-only">' not in html
    assert 'data-action="open-qa-lab"' in html
    assert 'id="qa-lab-modal"' in html
    assert "QA Lab" in html
    assert "Estados visuales" in html
    assert "Estados simulados" in html
    assert 'data-review-scenario="batch-ready"' in html
    assert 'data-action="close-qa-lab"' in html


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend workflow checks")
def test_load_batch_always_uses_bridge_scan_flow():
    script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const frontend = {json.dumps(str(FRONTEND_DIR))};

global.state = {{
  bridgeMode: "mock",
  batch: "none",
  selectedImageId: null,
  statusText: "Sin lote",
}};
global.clearTimers = () => {{}};
global.thumbnailPreloads = {{ clear: () => {{ throw new Error("mock branch should not clear thumbnails"); }} }};
global.thumbnailFallbackQueue = [];
global.thumbnailFallbackInFlight = {{ clear: () => {{ throw new Error("mock branch should not clear fallback state"); }} }};
global.clearBridgeExportPoll = () => {{}};
global.emptyScanDiagnostics = () => ({{ totalFiles: 0 }});
global.mockScanDiagnostics = () => ({{ totalFiles: 1 }});
global.DEFAULT_VIEW_MODE = "height";
global.render = () => {{ throw new Error("mock branch should not render directly"); }};
global.setTimer = () => {{ throw new Error("mock branch should not schedule timers"); }};
global.exportableImages = () => [];
let scanCalls = 0;
global.scanBridgeFolder = () => {{
  scanCalls += 1;
}};

vm.runInThisContext(fs.readFileSync(path.join(frontend, "app-batch-workflow.js"), "utf8"));

loadBatch();

assert.equal(scanCalls, 1);
assert.equal(state.bridgeMode, "mock");
assert.equal(state.batch, "none");
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend modal checks")
def test_qa_lab_modal_open_close_state_is_isolated():
    script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const frontend = {json.dumps(str(FRONTEND_DIR))};

global.state = {{
  appSettingsOpen: true,
  batchDetailOpen: true,
  exportConfirmOpen: true,
  qaLabOpen: false,
  statusText: "",
}};
global.document = {{ activeElement: null, body: {{}} }};
global.HTMLElement = class HTMLElement {{}};
global.$ = () => null;
global.render = () => {{}};
global.queueModalFocus = () => {{}};
global.rememberModalFocusReturn = () => {{}};
global.releaseModalFocusBeforeHide = () => {{}};
global.hasBatch = () => false;

vm.runInThisContext(fs.readFileSync(path.join(frontend, "app-modal-controller.js"), "utf8"));

openQaLab();
assert.equal(state.qaLabOpen, true);
assert.equal(state.appSettingsOpen, false);
assert.equal(state.batchDetailOpen, false);
assert.equal(state.exportConfirmOpen, false);
assert.equal(state.statusText, "QA Lab");

closeQaLab();
assert.equal(state.qaLabOpen, false);
assert.equal(state.statusText, "QA Lab cerrado");
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
