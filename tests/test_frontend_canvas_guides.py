import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "canvas-guides.js"
INDEX_PATH = FRONTEND_DIR / "index.html"
APP_GLOBALS_PATH = FRONTEND_DIR / "app-globals.js"


def test_canvas_guides_helper_loads_before_mock_data_and_app():
    html = INDEX_PATH.read_text(encoding="utf-8")

    helper_index = html.index("canvas-guides.js")
    mock_data_index = html.index("mock-data.js")
    app_index = html.index("app.js")

    assert helper_index < mock_data_index < app_index


def test_app_globals_exposes_canvas_guide_helpers():
    source = APP_GLOBALS_PATH.read_text(encoding="utf-8")

    assert "global.guideHelpers = window.FlatShotCanvasGuides;" in source


def test_canvas_guides_storage_keys_are_defined():
    source = (FRONTEND_DIR / "mock-data.js").read_text(encoding="utf-8")

    assert 'guideSystems: "flatshot.guideSystems"' in source
    assert 'activeGuideSystems: "flatshot.activeGuideSystemIds"' in source
    assert 'guidesVisible: "flatshot.guidesVisible"' in source


def test_guide_preferences_are_ui_preferences_not_export_preferences():
    source = (FRONTEND_DIR / "app-bridge-ui-preferences.js").read_text(encoding="utf-8")

    payload_start = source.index("function uiPreferencesPayload()")
    payload_end = source.index("function cacheUiPreferences", payload_start)
    payload_block = source[payload_start:payload_end]
    export_start = payload_block.index("exportPreferences:")
    export_block = payload_block[export_start:]

    assert "guideSystems:" in payload_block
    assert "activeGuideSystemIds:" in payload_block
    assert "guidesVisible:" in payload_block
    assert "guideSystems:" not in export_block
    assert "activeGuideSystemIds:" not in export_block
    assert "guidesVisible:" not in export_block


def test_canvas_guides_toolbar_overlay_and_controller_are_wired():
    html = INDEX_PATH.read_text(encoding="utf-8")
    loader = (FRONTEND_DIR / "app-loader.js").read_text(encoding="utf-8")

    assert 'class="viewer-control-group viewer-guides"' in html
    assert 'id="guide-overlay"' in html
    assert 'data-action="toggle-guides"' in html
    assert 'data-guide-system-list' in html
    assert 'class="viewer-guides-menu"' in html
    assert loader.index("app-canvas-guides-controller.js") < loader.index("app-preview-controller.js")


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_canvas_guide_helpers_normalize_and_expand_rules():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

const systems = helpers.normalizeGuideSystemList([
  {{
    id: "center",
    name: "Centro roto",
    color: "#ffffff",
    rules: [{{ type: "line", axis: "x", position: 0.2 }}],
  }},
  {{
    id: "market",
    name: "Marketplace",
    color: "#ABCDEF",
    opacity: 2,
    thickness: 9,
    rules: [
      {{ id: "top", type: "mirror-pair", axis: "y", inset: 0.12 }},
      {{ id: "thirds", type: "division", axis: "x", mode: "equal", parts: 3 }},
      {{ id: "custom", type: "division", axis: "y", mode: "custom", positions: [0.78, 0.22, 0.22] }},
      {{ id: "bad", type: "mirror-pair", axis: "x", inset: 0.6 }},
    ],
  }},
]);

assert.equal(systems[0].id, "center");
assert.equal(systems[0].system, true);
assert.equal(systems[0].name, "Centro");
assert.equal(systems.at(-1).id, "market");
assert.equal(systems.at(-1).color, "#abcdef");
assert.equal(systems.at(-1).opacity, 1);
assert.equal(systems.at(-1).thickness, 4);
assert.equal(systems.at(-1).rules.length, 3);

const activeIds = helpers.normalizeActiveGuideSystemIds(["market", "missing", "market"], systems);
assert.deepEqual(activeIds, ["market"]);

const lines = helpers.guideLinesForSystems(systems, activeIds).map((line) => `${{line.axis}}:${{line.position}}`);
assert.deepEqual(lines, ["y:0.12", "y:0.88", "x:0.3333", "x:0.6667", "y:0.22", "y:0.78"]);
assert.equal(helpers.formatPercent(0.33333), "33.33%");
assert.equal(helpers.parsePercent("12.5%"), 0.125);

const storage = helpers.guideSystemsForStorage(systems);
assert.deepEqual(storage.map((system) => system.id), ["market"]);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
