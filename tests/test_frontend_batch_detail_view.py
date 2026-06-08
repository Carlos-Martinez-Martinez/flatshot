import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "batch-detail-view.js"
INDEX_PATH = FRONTEND_DIR / "index.html"


def test_batch_detail_view_helper_loads_before_app_script():
    html = INDEX_PATH.read_text(encoding="utf-8")

    helper_index = html.index("batch-detail-view.js")
    app_index = html.index("app.js")

    assert helper_index < app_index


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_batch_detail_row_html_keeps_existing_contract():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

assert.equal(helpers.escapeHtml("<a&b\\"c>"), "&lt;a&amp;b&quot;c&gt;");

const row = helpers.batchDetailRowHtml("Ruta", "C:/lote & salida", "Ruta <completa>");
assert.equal(row.includes('class="batch-detail-row"'), true);
assert.equal(row.includes('<span>Ruta</span>'), true);
assert.equal(row.includes('<strong title="Ruta &lt;completa&gt;">C:/lote &amp; salida</strong>'), true);

const empty = helpers.batchDetailRowHtml("Estado", "");
assert.equal(empty.includes('<strong title="Pendiente">Pendiente</strong>'), true);

const missing = helpers.batchDetailRowHtml("Valor", null);
assert.equal(missing.includes('<strong title="Pendiente">Pendiente</strong>'), true);

const folder = helpers.folderItemHtml({{
  name: "Carpeta <A>",
  detail: "2 imágenes & 1 aviso",
  path: "C:/lote/A",
  count: "2",
  status: "warning",
}});
assert.equal(folder.includes('class="folder-item empty"'), true);
assert.equal(folder.includes('title="C:/lote/A"'), true);
assert.equal(folder.includes('<strong>Carpeta &lt;A&gt;</strong>'), true);
assert.equal(folder.includes('<small>2 imágenes &amp; 1 aviso</small>'), true);
assert.equal(folder.includes('class="state-chip warning"'), true);

const errorFolder = helpers.folderItemHtml({{
  name: "Error",
  detail: "No accesible",
  count: "!",
  status: "error",
}});
assert.equal(errorFolder.includes('class="folder-item error"'), true);
assert.equal(errorFolder.includes('title="No accesible"'), true);
assert.equal(errorFolder.includes('class="state-chip error"'), true);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
