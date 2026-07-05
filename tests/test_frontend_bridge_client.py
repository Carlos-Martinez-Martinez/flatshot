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
assert.equal(
  helpers.thumbnailUrl("http://127.0.0.1:8765/", "C:/lote/a b.png", 96, "secret"),
  "http://127.0.0.1:8765/images/thumbnail?path=C%3A%2Flote%2Fa%20b.png&size=96&token=secret"
);
assert.equal(
  helpers.thumbnailUrl("http://127.0.0.1:8765/", "", 96, "secret", "img_abc"),
  "http://127.0.0.1:8765/images/thumbnail?imageId=img_abc&size=96&token=secret"
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
  assert.equal(options.headers["X-FlatShot-Token"], "secret");
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
  authToken: "secret",
}}).then((payload) => {{
  assert.deepEqual(payload, {{ ok: true, calls: 1 }});
}}).catch((error) => {{
  console.error(error);
  process.exitCode = 1;
}});

global.fetch = async () => ({{
  ok: false,
  status: 507,
  json: async () => ({{
    error: {{
      code: "export_insufficient_space",
      message: "No hay espacio suficiente para preparar la exportación.",
    }},
  }}),
}});

helpers.request("http://127.0.0.1:8765/", "/exports/run", {{
  method: "POST",
  body: JSON.stringify({{}}),
  retries: 0,
  timeoutMs: 1000,
}}).then(() => {{
  throw new Error("expected bridge request to fail");
}}).catch((error) => {{
  try {{
    assert.equal(error.message, "No hay espacio suficiente para preparar la exportación.");
    assert.equal(error.bridgeCode, "export_insufficient_space");
    assert.equal(error.status, 507);
  }} catch (assertionError) {{
    console.error(assertionError);
    process.exitCode = 1;
  }}
}});

global.fetch = async (url, options) => {{
  assert.equal(url, "http://127.0.0.1:8765/preview/render-image");
  assert.equal(options.method, "POST");
  assert.ok(options.signal, "preview request should be abortable");
  assert.equal(options.headers["X-FlatShot-Token"], "secret");
  assert.deepEqual(JSON.parse(options.body), {{
    imageId: "img_a",
    targetWidth: 320,
    targetHeight: 240,
    settings: {{ opacity: 20 }},
    localOverride: {{}},
    curveData: {{ xp: [0, 1], fp: [0.9, 1.1] }},
  }});
  return {{
    ok: true,
    headers: {{
      get: (name) => ({{
        "X-FlatShot-Width": "320",
        "X-FlatShot-Height": "240",
        "X-FlatShot-Warning": "fallback",
      }}[name] || null),
    }},
    blob: async () => "blob-payload",
  }};
}};

helpers.requestPreviewImage("http://127.0.0.1:8765/", {{
  imageId: "img_a",
  imagePath: "C:/lote/a.png",
  targetSize: {{ targetWidth: 320, targetHeight: 240 }},
  settings: {{ opacity: 20 }},
  curveData: {{ xp: [0, 1], fp: [0.9, 1.1] }},
  timeoutMs: 1000,
  authToken: "secret",
}}).then((payload) => {{
  assert.deepEqual(payload, {{
    blob: "blob-payload",
    width: 320,
    height: 240,
    warning: "fallback",
  }});
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
