import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "interaction-bindings.js"
INDEX_PATH = FRONTEND_DIR / "index.html"
APP_DOCUMENT_EVENTS_PATH = FRONTEND_DIR / "app-document-events.js"


def test_interaction_bindings_load_before_app_script():
    html = INDEX_PATH.read_text(encoding="utf-8")

    helper_index = html.index("interaction-bindings.js")
    app_index = html.index("app.js")

    assert helper_index < app_index


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_interaction_bindings_exports_wiring_contract():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

assert.equal(typeof helpers.wireFlatShotInteractions, "function");
assert.equal(typeof helpers.createFlatShotInteractionHandlers, "function");
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
def test_interaction_bindings_initialize_onboarding_after_startup_render():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

const calls = [];
const fakeElement = {{
  addEventListener() {{}},
}};
const fakeDocument = {{
  addEventListener() {{}},
}};
const fakeWindow = {{
  addEventListener() {{}},
}};

helpers.wireFlatShotInteractions({{
  document: fakeDocument,
  window: fakeWindow,
  $() {{ return fakeElement; }},
  $$() {{ return []; }},
  onboardingBackgroundHelpers: {{
    initialize() {{
      calls.push("onboarding");
    }},
  }},
  handlers: {{
    startup() {{
      calls.push("startup");
    }},
    initViewerResizeObserver() {{
      calls.push("resize");
    }},
  }},
}});

assert.deepEqual(calls.slice(0, 2), ["startup", "onboarding"]);
assert.equal(calls.includes("resize"), true);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout


def test_interaction_bindings_wire_focusout_for_commit_on_blur():
    source = HELPER_PATH.read_text(encoding="utf-8")

    assert 'documentRef.addEventListener("focusout", handlers.documentFocusOut);' in source


def test_document_click_normalizes_non_element_targets_for_action_buttons():
    source = APP_DOCUMENT_EVENTS_PATH.read_text(encoding="utf-8")

    click_start = source.index("function handleDocumentClick(event)")
    click_end = source.index("function handleDocumentToggle", click_start)
    click_block = source[click_start:click_end]

    assert "function eventElementTarget(event)" in source
    assert "const target = eventElementTarget(event);" in click_block
    assert "if (!target) {" in click_block
    assert "target.closest(\"[data-action]\")" in click_block
    assert "event.target.closest" not in click_block
