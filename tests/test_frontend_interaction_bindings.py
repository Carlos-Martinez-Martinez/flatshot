import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "interaction-bindings.js"
INDEX_PATH = FRONTEND_DIR / "index.html"


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
