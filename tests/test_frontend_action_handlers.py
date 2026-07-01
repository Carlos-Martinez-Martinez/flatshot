import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "action-handlers.js"
INDEX_PATH = FRONTEND_DIR / "index.html"


def test_action_handler_helper_loads_before_app_script():
    html = INDEX_PATH.read_text(encoding="utf-8")

    helper_index = html.index("action-handlers.js")
    app_index = html.index("app.js")

    assert helper_index < app_index


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_action_dispatcher_invokes_known_handlers_and_fallback():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

const calls = [];
const dispatcher = helpers.createActionDispatcher({{
  "load-batch": (target, action) => calls.push(["load", target.id, action]),
  "start-export": () => calls.push(["export"]),
}}, (action, target) => calls.push(["fallback", action, target.id]));

dispatcher("load-batch", {{ id: "button-1" }});
dispatcher("start-export", {{ id: "button-2" }});
dispatcher("missing", {{ id: "button-3" }});

assert.deepEqual(calls, [
  ["load", "button-1", "load-batch"],
  ["export"],
  ["fallback", "missing", "button-3"],
]);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
