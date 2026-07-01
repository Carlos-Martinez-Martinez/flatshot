import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "bridge-client.js"
INDEX_PATH = FRONTEND_DIR / "index.html"


def test_bridge_client_helper_loads_before_app_script():
    html = INDEX_PATH.read_text(encoding="utf-8")

    helper_index = html.index("bridge-client.js")
    app_index = html.index("app.js")

    assert helper_index < app_index


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_bridge_client_helpers_keep_url_error_and_request_contracts():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

assert.equal(helpers.normalizedBridgeUrl(" http://127.0.0.1:8765/// ", ""), "http://127.0.0.1:8765");
assert.equal(helpers.normalizedBridgeUrl("", "http://127.0.0.1:8765/"), "http://127.0.0.1:8765");
assert.equal(
  helpers.thumbnailUrl("http://127.0.0.1:8765/", "C:/lote/a b.png", 96),
  "http://127.0.0.1:8765/images/thumbnail?path=C%3A%2Flote%2Fa%20b.png&size=96"
);
assert.equal(helpers.thumbnailUrl("http://127.0.0.1:8765", "", 96), "");
assert.equal(helpers.errorMessage({{ name: "AbortError" }}), "La conexión local tardó demasiado. Verifica que FlatShot esté funcionando.");
assert.equal(helpers.errorMessage(new Error("HTTP 500")), "Error del servidor local: HTTP 500");
assert.equal(helpers.errorMessage(new Error("offline")), "Conexión local no disponible: offline");

let calls = 0;
global.fetch = async (url, options) => {{
  calls += 1;
  assert.equal(url, "http://127.0.0.1:8765/health");
  assert.equal(options.headers["Content-Type"], "application/json");
  return {{
    ok: true,
    json: async () => ({{ ok: true, calls }}),
  }};
}};

helpers.request("http://127.0.0.1:8765/", "/health", {{
  method: "POST",
  body: JSON.stringify({{ ping: true }}),
  retries: 0,
  timeoutMs: 1000,
}}).then((payload) => {{
  assert.deepEqual(payload, {{ ok: true, calls: 1 }});
}}).catch((error) => {{
  console.error(error);
  process.exitCode = 1;
}});
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
