import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "bridge-url.js"
INDEX_PATH = FRONTEND_DIR / "index.html"


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_bridge_url_helpers_prefer_current_launcher_url_over_restored_session():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

assert.equal(
  helpers.initialBridgeUrlFromSearch("?bridge=http%3A%2F%2F127.0.0.1%3A8766", "http://127.0.0.1:8765"),
  "http://127.0.0.1:8766"
);

assert.equal(
  helpers.initialBridgeUrlFromSearch("", "http://127.0.0.1:8765"),
  "http://127.0.0.1:8765"
);

assert.equal(
  helpers.initialBridgeTokenFromSearch("?bridgeToken=abc123"),
  "abc123"
);

assert.equal(
  helpers.initialBridgeTokenFromSearch("?bridgeToken=%20%20"),
  ""
);

assert.equal(
  helpers.initialBridgeTokenFromHash("#bridgeToken=abc123"),
  "abc123"
);

assert.equal(
  helpers.initialBridgeToken("?bridgeToken=legacy", "#bridgeToken=launcher"),
  "launcher"
);

assert.equal(
  helpers.resolveRuntimeBridgeUrl({{
    currentBridgeUrl: "http://127.0.0.1:8765",
    restoredBridgeUrl: "http://127.0.0.1:8766",
    defaultBridgeUrl: "http://127.0.0.1:8765",
  }}),
  "http://127.0.0.1:8765"
);

assert.equal(
  helpers.resolveRuntimeBridgeUrl({{
    currentBridgeUrl: "http://127.0.0.1:8767/",
    restoredBridgeUrl: "http://127.0.0.1:8766",
    defaultBridgeUrl: "http://127.0.0.1:8765",
  }}),
  "http://127.0.0.1:8767"
);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout


def test_bridge_url_helper_loads_before_mock_data_and_app():
    html = INDEX_PATH.read_text(encoding="utf-8")

    helper_index = html.index("bridge-url.js")
    mock_index = html.index("mock-data.js")
    app_index = html.index("app.js")

    assert helper_index < mock_index < app_index
