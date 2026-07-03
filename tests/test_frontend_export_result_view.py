import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "export-result-view.js"
INDEX_PATH = FRONTEND_DIR / "index.html"


def test_export_result_view_helper_loads_before_app_script():
    html = INDEX_PATH.read_text(encoding="utf-8")

    helper_index = html.index("export-result-view.js")
    app_index = html.index("app.js")

    assert helper_index < app_index


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_export_result_view_renders_result_contract():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

assert.equal(helpers.escapeHtml('<a&b"c>'), '&lt;a&amp;b&quot;c&gt;');
assert.equal(helpers.exportResultClass("failed"), "error");
assert.equal(helpers.exportResultClass("partial"), "warning");
assert.equal(helpers.exportResultClass("completed"), "ready");
assert.equal(helpers.exportResultClass("running"), "running");
assert.equal(helpers.exportResultTitle("running", true), "Exportación pausada");
assert.equal(helpers.exportResultTitle("completed"), "Exportación completada");
assert.equal(helpers.exportResultMeta({{ status: "partial", processed: 2, total: 3, errors: 1 }}), "2/3 exportadas · 1 error");
assert.equal(helpers.exportResultMeta({{ status: "failed", processed: 0, total: 3, errors: 0 }}), "No completada");
assert.equal(helpers.currentExportFileLabel({{
  images: [],
  processed: 0,
  statusText: "Preparando lote",
}}), "Preparando lote");
assert.equal(helpers.currentExportFileLabel({{
  images: [],
  processed: 0,
  statusText: "",
}}), "Preparando");
assert.equal(helpers.currentExportFileLabel({{
  images: [{{ name: "a.png" }}, {{ name: "b.png" }}],
  processed: -1,
  statusText: "Procesando",
}}), "a.png");
assert.equal(helpers.currentExportFileLabel({{
  images: [{{ name: "a.png" }}, {{ name: "b.png" }}],
  processed: 1,
  statusText: "Procesando",
}}), "b.png");
assert.equal(helpers.currentExportFileLabel({{
  images: [{{ name: "a.png" }}, {{ name: "b.png" }}],
  processed: 99,
  statusText: "Procesando",
}}), "b.png");
assert.equal(helpers.currentExportFileLabel({{
  images: [{{ name: "" }}],
  processed: 0,
  statusText: "Procesando",
}}), "Procesando");
assert.equal(helpers.outputDestinationToOpen({{
  exportDestinations: ["C:/Estado", "C:/Otro"],
  resultDestinations: ["C:/Resultado"],
}}), "C:/Estado");
assert.equal(helpers.outputDestinationToOpen({{
  exportDestinations: [],
  resultDestinations: ["C:/Resultado", "C:/Otro"],
}}), "C:/Resultado");
assert.equal(helpers.outputDestinationToOpen({{
  exportDestinations: [],
  resultDestinations: [],
}}), "");
assert.equal(helpers.outputDestinationToOpen({{
  exportDestinations: null,
  resultDestinations: null,
}}), "");

assert.equal(
  helpers.exportIssueActionText({{ title: "Destino", detail: "ocupado" }}, {{ existingOutput: true }}),
  "Ya hay archivos en destino. Cambia la carpeta o el nombre final."
);
assert.equal(
  helpers.exportIssueActionText({{ title: "Worker", detail: "fallo" }}),
  "Worker · fallo"
);

const actions = helpers.exportResultActionsHtml({{
  status: "failed",
  issues: [{{ title: "Error" }}],
  destinations: ["C:/Export"],
  canOpenOutput: false,
  canRetry: true,
  canRetryFailed: true,
}});
assert.equal(actions.includes('data-action="review-errors"'), true);
assert.equal(actions.includes('data-action="retry-failed-export"'), true);
assert.equal(actions.includes('data-action="start-export"'), true);

const partialRetry = helpers.exportResultActionsHtml({{
  status: "partial",
  issues: [{{ title: "Error" }}],
  destinations: ["C:/Export"],
  canOpenOutput: true,
  canRetry: true,
  canRetryFailed: true,
}});
assert.equal(partialRetry.includes('data-action="retry-failed-export"'), true);
assert.equal(partialRetry.includes("Reintentar fallidas"), true);

const manyDestinations = helpers.exportResultActionsHtml({{
  status: "completed",
  issues: [],
  destinations: ["a", "b", "c", "d", "e"],
  canOpenOutput: true,
  canRetry: false,
}});
assert.equal(manyDestinations.includes("2 carpetas más"), true);
assert.equal(manyDestinations.includes(">Abrir carpeta principal</button>"), true);
assert.equal(manyDestinations.includes('data-action="copy-output-path"'), true);

const singleDestination = helpers.exportResultActionsHtml({{
  status: "completed",
  issues: [],
  destinations: ["a"],
  canOpenOutput: true,
  canRetry: false,
}});
assert.equal(singleDestination.includes(">Abrir carpeta</button>"), true);
assert.equal(singleDestination.includes(">Copiar ruta</button>"), true);

const html = helpers.exportResultHtml({{
  status: "running",
  title: "Exportando",
  meta: "1/2 imágenes",
  processed: 1,
  total: 2,
  errors: 0,
  destinations: ['C:/Salida/"uno"'],
  destinationFallback: "Salida",
  currentFileLabel: 'camisa <azul>.png',
  issues: [{{ title: "Aviso" }}],
  issueSummary: "Aviso <uno>",
  items: [
    {{ name: "ok.jpg", success: true }},
    {{ name: "bad.jpg", success: false }},
  ],
  actionsHtml: '<div class="result-actions"><button type="button">X</button></div>',
}});
assert.equal(html.includes('class="result-header running"'), true);
assert.equal(html.includes('C:/Salida/&quot;uno&quot;'), true);
assert.equal(html.includes('camisa &lt;azul&gt;.png'), true);
assert.equal(html.includes('Aviso &lt;uno&gt;'), true);
assert.equal(html.includes('class="result-item ready"'), true);
assert.equal(html.includes('class="result-item error"'), true);
assert.equal(html.includes('class="result-actions"'), true);

const fallbackHtml = helpers.exportResultHtml({{
  status: "completed",
  processed: 2,
  total: 2,
  errors: 0,
  destinations: [],
  destinationFallback: "Salida",
}});
assert.equal(fallbackHtml.includes('result-path muted'), true);
assert.equal(fallbackHtml.includes('Salida'), true);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
