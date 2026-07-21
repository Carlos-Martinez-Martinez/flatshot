import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "storage.js"
INDEX_PATH = FRONTEND_DIR / "index.html"


def test_storage_helper_loads_before_app_script():
    html = INDEX_PATH.read_text(encoding="utf-8")

    helper_index = html.index("storage.js")
    app_index = html.index("app.js")

    assert helper_index < app_index


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_storage_helper_keeps_persistent_storage_contracts():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

function fakeStorage(initial = {{}}, failing = false) {{
  const data = new Map(Object.entries(initial));
  return {{
    getItem(key) {{
      if (failing) throw new Error("blocked");
      return data.has(key) ? data.get(key) : null;
    }},
    setItem(key, value) {{
      if (failing) throw new Error("blocked");
      data.set(key, String(value));
    }},
    removeItem(key) {{
      if (failing) throw new Error("blocked");
      data.delete(key);
    }},
    dump() {{
      return Object.fromEntries(data.entries());
    }},
  }};
}}

assert.equal(helpers.readValue(fakeStorage({{ name: " FlatShot " }}), "name"), " FlatShot ");
assert.equal(helpers.readValue(fakeStorage(), "missing"), "");
assert.equal(helpers.readValue(fakeStorage({{}}, true), "name"), "");
assert.deepEqual(helpers.readJson(fakeStorage({{ prefs: "{{\\"size\\":\\"1800x2400\\"}}" }}), "prefs", {{}}), {{ size: "1800x2400" }});
assert.deepEqual(helpers.readJson(fakeStorage({{ prefs: "{{" }}), "prefs", {{ fallback: true }}), {{ fallback: true }});

const storage = fakeStorage({{ stale: "value" }});
helpers.writeValue(storage, "name", "  nuevo  ");
helpers.writeValue(storage, "stale", "   ");
helpers.writeJson(storage, "prefs", {{ format: "PNG" }});

assert.deepEqual(storage.dump(), {{
  name: "nuevo",
  prefs: "{{\\"format\\":\\"PNG\\"}}",
}});

assert.doesNotThrow(() => helpers.writeValue(fakeStorage({{}}, true), "name", "FlatShot"));
assert.doesNotThrow(() => helpers.writeJson(fakeStorage({{}}, true), "prefs", {{}}));
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
