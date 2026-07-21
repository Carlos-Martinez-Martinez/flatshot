import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "number-utils.js"
INDEX_PATH = FRONTEND_DIR / "index.html"


def test_number_utils_loads_before_app_script():
    html = INDEX_PATH.read_text(encoding="utf-8")

    helper_index = html.index("number-utils.js")
    app_index = html.index("app.js")

    assert helper_index < app_index


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_number_utils_clamp_and_scene_rounding_contracts():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

assert.equal(helpers.clampNumber("5", 0, 10, 3), 5);
assert.equal(helpers.clampNumber("-2", 0, 10, 3), 0);
assert.equal(helpers.clampNumber("12", 0, 10, 3), 10);
assert.equal(helpers.clampNumber("not-a-number", 0, 10, 3), 3);
assert.equal(helpers.clampNumber(Infinity, 0, 10, 3), 3);

assert.equal(helpers.roundedSceneValue(0.12349, 0, 1, 0), 0.123);
assert.equal(helpers.roundedSceneValue(2, 0, 1, 0), 1);
assert.equal(helpers.roundedSceneValue("bad", -1, 1, 0.4567), 0.457);

assert.deepEqual(helpers.parseIntegerInput("", {{ min: 0, max: 100, fallback: 20 }}), {{
  valid: false,
  partial: true,
  value: 20,
}});
assert.deepEqual(helpers.parseIntegerInput("-", {{ min: 0, max: 100, fallback: 20 }}), {{
  valid: false,
  partial: true,
  value: 20,
}});
assert.deepEqual(helpers.parseIntegerInput("45.6", {{ min: 0, max: 100, fallback: 20 }}), {{
  valid: true,
  partial: false,
  value: 46,
}});
assert.deepEqual(helpers.parseIntegerInput("999", {{ min: 0, max: 100, fallback: 20 }}), {{
  valid: true,
  partial: false,
  value: 100,
}});
assert.deepEqual(helpers.parseIntegerInput("bad", {{ min: 0, max: 100, fallback: 20 }}), {{
  valid: false,
  partial: false,
  value: 20,
}});
assert.equal(helpers.isPartialNumericInput("+"), true);
assert.equal(helpers.isPartialNumericInput("12"), false);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
