import json
import shutil
import subprocess
from pathlib import Path

import pytest


STARTUP = Path(__file__).resolve().parents[1] / "apps/flatshot-desktop/frontend/app-startup.js"


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required")
def test_viewer_resize_defers_geometry_writes_and_coalesces_notifications():
    script = f"""
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
let notify;
const frames = [];
const writes = [];
const canvas = {{}};
class ResizeObserver {{
  constructor(callback) {{ notify = callback; }}
  observe(target) {{ assert.equal(target, canvas); }}
}}
const context = {{
  $: selector => selector === '#canvas-area' ? canvas : null,
  window: {{ ResizeObserver }},
  ResizeObserver,
  requestAnimationFrame(callback) {{ frames.push(callback); return frames.length; }},
  syncPreviewWorkspaceGeometry() {{ writes.push('geometry'); }},
  updateFitZoomReadout() {{ writes.push('zoom'); }},
}};
vm.createContext(context);
vm.runInContext(fs.readFileSync({json.dumps(str(STARTUP))}, 'utf8'), context);
context.initViewerResizeObserver();
notify();
notify();
assert.deepEqual(writes, [], 'do not change layout during ResizeObserver delivery');
assert.equal(frames.length, 1, 'coalesce notifications into one animation frame');
frames.shift()();
assert.deepEqual(writes, ['geometry', 'zoom']);
notify();
assert.equal(frames.length, 1, 'later resizes must still update');
frames.shift()();
assert.deepEqual(writes, ['geometry', 'zoom', 'geometry', 'zoom']);
"""
    result = subprocess.run(["node", "-e", script], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
