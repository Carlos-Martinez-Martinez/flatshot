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

const problem = helpers.batchDetailProblemHtml({{
  tone: "warning",
  title: "Archivo <raro>.txt",
  titleAttr: 'C:/Entrada/"raro".txt',
  detail: "Extensión & no admitida",
}});
assert.equal(problem.includes('class="batch-detail-problem warning"'), true);
assert.equal(problem.includes('title="C:/Entrada/&quot;raro&quot;.txt"'), true);
assert.equal(problem.includes('Archivo &lt;raro&gt;.txt'), true);
assert.equal(problem.includes('Extensión &amp; no admitida'), true);

const clearProblem = helpers.batchDetailProblemHtml({{
  tone: "clear",
  title: "Archivo ignorado",
  detail: "Temporal",
}});
assert.equal(clearProblem.includes('class="batch-detail-problem clear"'), true);
assert.equal(clearProblem.includes('title="Archivo ignorado"'), true);

const output = helpers.batchDetailOutputHtml({{
  index: 1,
  name: "Web <gris>",
  active: true,
  summary: "JPG · 1800 × 2400",
  destination: 'C:/Salida/"web"',
  example: "camisa <azul>.jpg",
}});
assert.equal(output.includes('class="batch-detail-output"'), true);
assert.equal(output.includes('class="batch-detail-output__main"'), true);
assert.equal(output.includes('class="batch-detail-output__details"'), true);
assert.equal(output.includes("<span>2.</span>"), true);
assert.equal(output.includes('title="Web &lt;gris&gt;"'), true);
assert.equal(output.includes("Web &lt;gris&gt;"), true);
assert.equal(output.includes("<em>Principal</em>"), false);
assert.equal(output.includes("JPG · 1800 × 2400"), true);
assert.equal(output.includes('<span>Destino</span>'), true);
assert.equal(output.includes('title="C:/Salida/&quot;web&quot;"'), true);
assert.equal(output.includes("camisa &lt;azul&gt;.jpg"), true);

const secondaryOutput = helpers.batchDetailOutputHtml({{
  index: 0,
  name: "PNG",
  active: false,
  summary: "PNG",
  destination: "Salida",
  example: "camisa.png",
}});
assert.equal(secondaryOutput.includes("<span>1.</span>"), true);
assert.equal(secondaryOutput.includes("<em>Principal</em>"), false);

const ignoredSection = helpers.batchDetailIgnoredSectionHtml({{
  count: 2,
  rowsHtml: clearProblem,
}});
assert.equal(ignoredSection.includes('batch-detail-section--collapsed'), true);
assert.equal(ignoredSection.includes("<h3>Ignorados técnicos</h3>"), true);
assert.equal(ignoredSection.includes("<span>2 archivos</span>"), true);
assert.equal(ignoredSection.includes('class="batch-detail-reasons"'), true);
assert.equal(ignoredSection.includes('class="batch-detail-problem clear"'), true);
assert.equal(helpers.batchDetailIgnoredSectionHtml({{ count: 0, rowsHtml: "" }}), "");

const grid = helpers.batchDetailGridHtml({{
  files: 5,
  valid: 4,
  counts: {{
    exportableImages: 3,
    ignoredFiles: 1,
    nonExportableImages: 1,
  }},
  issueCount: 2,
  sourceFolderName: "Entrada <uno>",
  sourcePath: 'C:/Entrada/"uno"',
  stateTitle: "Listo",
  outputRowsHtml: output,
  ignoredSectionHtml: ignoredSection,
  issueRowsHtml: problem,
}});
assert.equal(grid.includes('batch-detail-grid batch-detail-grid--compact'), true);
assert.equal(grid.includes('class="batch-detail-overview"'), true);
assert.equal(grid.includes('class="batch-detail-metric"'), true);
assert.equal(grid.includes("<span>Encontrados</span>"), true);
assert.equal(grid.includes("<h3>Entrada</h3>"), true);
assert.equal(grid.includes("<h3>Lote</h3>"), false);
assert.equal(grid.includes("<h3>Salidas activas</h3>"), true);
assert.equal(grid.includes("<h3>Incidencias</h3>"), true);
assert.equal(grid.includes("Entrada &lt;uno&gt;"), true);
assert.equal(grid.includes('title="C:/Entrada/&quot;uno&quot;"'), true);
assert.equal(grid.includes('class="batch-detail-output"'), true);
assert.equal(grid.includes('class="batch-detail-problem warning"'), true);

const emptyGrid = helpers.batchDetailGridHtml({{ counts: {{}} }});
assert.equal(emptyGrid.includes("Sin salidas activas."), true);
assert.equal(emptyGrid.includes("Sin incidencias."), true);
assert.equal(emptyGrid.includes("batch-detail-secondary--single"), true);

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
