import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend state checks")
def test_advanced_disclosure_sync_reopens_remembered_section_after_render():
    script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const frontend = {json.dumps(str(FRONTEND_DIR))};

function classList(...classes) {{
  const values = new Set(classes);
  return {{
    contains(name) {{
      return values.has(name);
    }},
  }};
}}

const sections = [
  {{ classList: classList("preset-section"), open: false }},
  {{ classList: classList("appearance-section"), open: false }},
  {{ classList: classList("advanced-block"), open: false }},
  {{ classList: classList("local-adjustment"), open: false }},
];

global.state = {{
  presetEditorOpen: false,
  advancedDisclosureKey: "advanced-block",
}};
global.pendingAdvancedDisclosure = "";
global.$$ = () => sections;
global.setInspectorDisclosureOpenState = (details, open) => {{
  details.open = Boolean(open);
}};

vm.runInThisContext(fs.readFileSync(path.join(frontend, "app-inspector-layout-controller.js"), "utf8"));

syncAdvancedInspectorDetails("advanced");

assert.equal(sections[1].open, false);
assert.equal(sections[2].open, true);
assert.equal(state.advancedDisclosureKey, "advanced-block");
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout


def test_composition_disclosure_is_a_remembered_advanced_section():
    source = (FRONTEND_DIR / "app-inspector-disclosure-controller.js").read_text(encoding="utf-8")

    assert '"composition-section"' in source
