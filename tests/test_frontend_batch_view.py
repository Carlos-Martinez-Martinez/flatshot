import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "batch-view.js"
INDEX_PATH = FRONTEND_DIR / "index.html"


def test_batch_view_helper_loads_before_app_script():
    html = INDEX_PATH.read_text(encoding="utf-8")

    helper_index = html.index("batch-view.js")
    app_index = html.index("app.js")

    assert helper_index < app_index


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_batch_view_helpers_keep_labels_and_omission_summaries():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

assert.equal(helpers.warningCountLabel(1), "1 aviso");
assert.equal(helpers.warningCountLabel(2), "2 avisos");
assert.equal(helpers.imageCountLabel(1), "1 imagen");
assert.equal(helpers.imageCountLabel(3), "3 imágenes");
assert.equal(helpers.exportActionLabel(4, 1), "Exportar 4 imágenes");
assert.equal(helpers.exportActionLabel(4, 2), "Exportar 8 archivos");
assert.equal(helpers.outputCountLabel(1), "1 salida");
assert.equal(helpers.outputCountLabel(3), "3 salidas");

assert.equal(helpers.detectedFormatLabel([]), "PNG");
assert.equal(helpers.detectedFormatLabel([{{ name: "a.png" }}, {{ name: "b.png" }}]), "PNG");
assert.equal(helpers.detectedFormatLabel([{{ name: "a.png" }}, {{ name: "b.jpg" }}]), "PNG/JPG");
assert.equal(helpers.detectedFormatLabel([{{ suffix: "webp" }}]), "WEBP");

assert.equal(helpers.batchSummaryLabel({{ batch: "none", count: 9, warnings: 2 }}), "Sin lote");
assert.equal(helpers.batchSummaryLabel({{ batch: "scanning", count: 9, warnings: 2 }}), "Escaneando");
assert.equal(helpers.batchSummaryLabel({{ batch: "empty", count: 0, warnings: 0 }}), "Sin imágenes");
assert.equal(helpers.batchSummaryLabel({{ batch: "ready", count: 3, warnings: 0 }}), "3 imágenes");
assert.equal(helpers.batchSummaryLabel({{ batch: "ready", count: 3, warnings: 1 }}), "3 imágenes · 1 aviso");

assert.equal(helpers.readyBatchSummaryText({{ filesFound: null, exportableImages: 4 }}, "PNG", "4 imágenes listas"), "Leyendo archivos");
assert.equal(helpers.readyBatchSummaryText({{ filesFound: 7, exportableImages: 4 }}, "PNG", "4 imágenes listas"), "PNG · 7 archivos · 4 imágenes listas");
assert.equal(helpers.readyBatchSummaryText({{ filesFound: 0, exportableImages: 0 }}, "PNG", "0 imágenes listas"), "PNG · 0 imágenes listas");

assert.equal(helpers.bridgeScanMessage(0, 0), "No se encontraron PNG válidos");
assert.equal(helpers.bridgeScanMessage(5, 0), "5 imágenes encontradas");
assert.equal(helpers.bridgeScanMessage(5, 1), "Escaneo completado con 1 aviso");
assert.equal(helpers.bridgeScanMessage(5, 2), "Escaneo completado con 2 avisos");

assert.equal(helpers.omissionReasonLabel("system_file"), "Archivo del sistema");
assert.equal(helpers.omissionReasonLabel("temporary_or_config_file"), "Archivo temporal o de configuración");
assert.equal(helpers.omissionReasonLabel("unsupported_extension"), "Extensión no admitida");
assert.equal(helpers.omissionReasonLabel("read_error"), "Error de lectura");
assert.equal(helpers.omissionReasonLabel("subfolder_not_scanned"), "Subcarpeta no escaneada");
assert.equal(helpers.omissionReasonLabel("unknown"), "Ignorado");

assert.equal(helpers.omittedSummaryText({{ totalOmitted: 0 }}), "Sin ignorados");
assert.equal(helpers.omittedSummaryText({{ totalOmitted: 3, omittedByReason: {{ system_file: 1, read_error: 2 }} }}), "1 archivo del sistema · 2 error de lectura");
assert.equal(helpers.omittedSummaryText({{ totalOmitted: 3, omittedByReason: {{}} }}), "3 ignorados");
assert.equal(helpers.omissionSummaryText([], "Sin avisos de archivos"), "Sin avisos de archivos");
assert.equal(helpers.omissionSummaryText([
  {{ reason: "read_error" }},
  {{ reason: "read_error" }},
  {{ reason: "unsupported_extension" }},
], "Sin avisos"), "2 error de lectura · 1 extensión no admitida");

assert.equal(helpers.batchBackgroundLabel("transparent"), "transparente");
assert.equal(helpers.batchBackgroundLabel("white"), "blanco");
assert.equal(helpers.batchBackgroundLabel("rgb230"), "gris claro");

assert.equal(helpers.escapeHtml('<a&b"c>'), '&lt;a&amp;b&quot;c&gt;');
assert.equal(helpers.sourceInputDetail("none", 3, 2), "Pendiente");
assert.equal(helpers.sourceInputDetail("scanning", 3, 2), "Leyendo imágenes");
assert.equal(helpers.sourceInputDetail("ready", 3, 2), "3 archivos encontrados · 2 imágenes listas");
assert.equal(helpers.batchSummaryToneClass("error"), "is-error");
assert.equal(helpers.batchSummaryToneClass("warning"), "is-warning");
assert.equal(helpers.batchSummaryToneClass("busy"), "is-busy");
assert.equal(helpers.batchSummaryToneClass("ready"), "is-ready");
assert.equal(helpers.batchSummaryToneClass("idle"), "is-idle");

const metric = helpers.batchMetricHtml("Archivos <encontrados>", '7 "total"');
assert.equal(metric.includes("Archivos &lt;encontrados&gt;"), true);
assert.equal(metric.includes('title="7 &quot;total&quot;"'), true);

const diagnostics = helpers.diagnosticsHtml({{
  hasScanError: true,
  diagnostics: {{
    totalOmitted: 2,
    omittedByReason: {{ read_error: 1, unsupported_extension: 1 }},
    omitted: [
      {{ name: "bad <one>.txt", path: 'C:/bad "one".txt', reason: "unsupported_extension" }},
      {{ name: "fail.png", path: "C:/fail.png", detail: "No abre" }},
    ],
  }},
}});
assert.equal(diagnostics.includes('class="batch-diagnostics" open'), true);
assert.equal(diagnostics.includes("Ver diagnóstico"), true);
assert.equal(diagnostics.includes("Error de lectura"), true);
assert.equal(diagnostics.includes("bad &lt;one&gt;.txt"), true);
assert.equal(diagnostics.includes('title="C:/bad &quot;one&quot;.txt"'), true);

const summary = helpers.batchSummaryHtml({{
  batch: "ready",
  visible: {{
    tone: "warning",
    title: "Lote <actual>",
    subtitle: '4 listas "ok"',
    nextStep: "Revisar salida",
  }},
  counts: {{
    filesFound: 6,
    validImages: 4,
    readyImages: 4,
    nonExportableImages: 1,
    ignoredFiles: 1,
    reviewIssues: 2,
    blockingErrors: 0,
    nonBlockingWarnings: 2,
  }},
  diagnostics: {{ totalOmitted: 0, omittedByReason: {{}}, omitted: [] }},
  sourcePath: 'C:/Lote/"uno"',
  sourceFolderName: "Lote uno",
  outputLine: "JPG 1800×2400",
  destinationLine: "_SALIDA_PRO",
  outputProfileName: "Marketplace",
  namingExample: 'camisa <azul>.jpg',
  namingLabel: "original + _PRO",
  warningsLabel: "2 avisos",
  ignoredLabel: "1 ignorado",
}});
assert.equal(summary.includes("batch-summary-card is-warning"), true);
assert.equal(summary.includes("Lote &lt;actual&gt;"), true);
assert.equal(summary.includes('title="C:/Lote/&quot;uno&quot;"'), true);
assert.equal(summary.includes("6 archivos encontrados · 4 imágenes listas"), true);
assert.equal(summary.includes("JPG 1800×2400 · _SALIDA_PRO"), true);
assert.equal(summary.includes("camisa &lt;azul&gt;.jpg"), true);
assert.equal(summary.includes("Avisos en la galería"), true);

const blockedSummary = helpers.batchSummaryHtml({{
  batch: "ready",
  visible: {{ tone: "error", title: "Bloqueado", subtitle: "Error", nextStep: "Corregir" }},
  counts: {{
    filesFound: null,
    validImages: null,
    readyImages: 0,
    nonExportableImages: 1,
    ignoredFiles: 0,
    reviewIssues: 1,
    blockingErrors: 1,
    nonBlockingWarnings: 0,
  }},
  diagnostics: {{
    totalOmitted: 0,
    omittedByReason: {{}},
    omitted: [],
  }},
  hasScanError: true,
}});
assert.equal(blockedSummary.includes("batch-summary-card is-error"), true);
assert.equal(blockedSummary.includes("Leyendo archivos encontrados · Leyendo imágenes listas"), true);
assert.equal(blockedSummary.includes('class="batch-diagnostics" open'), true);
assert.equal(blockedSummary.includes("Diagnóstico"), true);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
