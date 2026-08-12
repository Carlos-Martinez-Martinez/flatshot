import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "export-preflight-view.js"
INDEX_PATH = FRONTEND_DIR / "index.html"


def test_export_preflight_view_helper_loads_before_app_script():
    html = INDEX_PATH.read_text(encoding="utf-8")

    helper_index = html.index("export-preflight-view.js")
    app_index = html.index("app.js")

    assert helper_index < app_index


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_export_preflight_view_renders_issue_and_status_contracts():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

assert.equal(helpers.escapeHtml('<a&b"c>'), '&lt;a&amp;b&quot;c&gt;');

const progress = helpers.progressPanelHtml("Preparando <lote>", 42.4);
assert.equal(progress.includes('class="context-progress"'), true);
assert.equal(progress.includes("Preparando &lt;lote&gt;"), true);
assert.equal(progress.includes("<strong>42%</strong>"), true);

const indeterminate = helpers.progressPanelHtml("Escaneando");
assert.equal(indeterminate.includes("is-indeterminate"), true);
assert.equal(indeterminate.includes("<strong>"), false);

const noWarningSummary = helpers.outputWarningSummaryHtml({{
  issues: [{{ level: "warning", title: "Aviso", detail: "no bloquea" }}],
  visibleWarningCount: 1,
}});
assert.equal(noWarningSummary, "");

const warningSummary = helpers.outputWarningSummaryHtml({{
  issues: [
    {{ level: "error", title: "Destino", detail: "ocupado" }},
    {{ level: "warning", title: "Alpha", detail: "bajo" }},
  ],
  firstIssue: {{ level: "error", title: "camisa.png", detail: 'Ruta "ocupada"', file: "camisa.png", path: "C:/camisa.png" }},
  visibleWarningCount: 3,
}});
assert.equal(warningSummary.includes('class="warning-summary error"'), true);
assert.equal(warningSummary.includes("3 avisos"), true);
assert.equal(warningSummary.includes('title="C:/camisa.png"'), true);
assert.equal(warningSummary.includes("Motivo: Ruta &quot;ocupada&quot;"), true);
assert.equal(warningSummary.includes('data-action="review-errors"'), true);

assert.deepEqual(helpers.issueRows({{
  scanOmissions: [
    {{
      name: "desktop.ini",
      detail: "",
      reasonLabel: "Archivo de sistema",
      severity: "ignored",
      path: "C:/lote/desktop.ini",
    }},
    {{
      name: "foto.psd",
      detail: "Formato no soportado",
      reasonLabel: "Extension no soportada",
      severity: "warning",
      folder: "C:/lote",
    }},
  ],
  images: [
    {{ id: "img-1", name: "ok.png", status: "ready", path: "C:/ok.png" }},
    {{ id: "img-2", name: "aviso.png", status: "warning", detail: "", path: "C:/aviso.png" }},
    {{ id: "img-3", name: "bloqueada.png", status: "ready", exportStatus: "error", path: "C:/bloqueada.png" }},
  ],
  errors: [
    {{ level: "error", title: "Destino", detail: "ocupado" }},
  ],
  statusLabels: {{ ready: "Lista", warning: "Aviso", error: "Error" }},
}}), [
  {{
    level: "info",
    title: "desktop.ini",
    detail: "Motivo: Archivo de sistema",
    path: "C:/lote/desktop.ini",
    actionLabel: "",
  }},
  {{
    level: "warning",
    title: "foto.psd",
    detail: "Motivo: Formato no soportado",
    path: "C:/lote",
    actionLabel: "",
  }},
  {{
    level: "warning",
    title: "aviso.png",
    detail: "Aviso",
    path: "C:/aviso.png",
    imageId: "img-2",
    actionLabel: "Ir a imagen",
  }},
  {{
    level: "error",
    title: "bloqueada.png",
    detail: "Lista",
    path: "C:/bloqueada.png",
    imageId: "img-3",
    actionLabel: "Ir a imagen",
  }},
  {{
    level: "error",
    title: "Destino",
    detail: "ocupado",
    path: "",
    actionLabel: "",
  }},
]);

assert.equal(helpers.issueListHtml({{
  hasActiveBatch: false,
  batch: "none",
  rows: [],
  counts: {{ errors: 0 }},
  warningCount: 0,
}}), "");

const readyHtml = helpers.issueListHtml({{
  hasActiveBatch: true,
  batch: "ready",
  rows: [],
  counts: {{ errors: 0 }},
  warningCount: 0,
}});
assert.equal(readyHtml.includes("Sin avisos"), true);
assert.equal(readyHtml.includes("Todo listo para exportar"), true);
assert.equal(readyHtml.includes("inspector-empty-state"), true);
assert.equal(readyHtml.includes("issue-list-summary ready"), true);

const warningHtml = helpers.issueListHtml({{
  hasActiveBatch: true,
  batch: "ready",
  rows: [
    {{ level: "warning", title: "Alpha <bajo>", detail: 'Ruta "x"', path: "C:/a", imageId: "img-1", actionLabel: "Ir" }},
  ],
  counts: {{ errors: 0 }},
  warningCount: 1,
}});
assert.equal(warningHtml.includes("1 aviso"), true);
assert.equal(warningHtml.includes("Alpha &lt;bajo&gt;"), true);
assert.equal(warningHtml.includes("Ruta &quot;x&quot;"), true);
assert.equal(warningHtml.includes('data-image-id="img-1"'), true);

const blockerHtml = helpers.issueListHtml({{
  hasActiveBatch: true,
  batch: "ready",
  rows: [{{ level: "error", title: "Salida a corregir", detail: "Cambia destino, sufijo o nombre" }}],
  counts: {{ errors: 1 }},
  warningCount: 1,
}});
assert.equal(blockerHtml.includes("1 bloqueo"), true);
assert.equal(blockerHtml.includes("Corrige la salida para continuar."), true);
assert.equal(blockerHtml.includes('data-action="edit-output"'), true);
assert.equal(blockerHtml.includes(">Corregir salida</button>"), true);

const ignoredHtml = helpers.issueListHtml({{
  hasActiveBatch: true,
  batch: "ready",
  rows: [{{ level: "info", title: "desktop.ini", detail: "Ignorado" }}],
  counts: {{ errors: 0 }},
  warningCount: 0,
}});
assert.equal(ignoredHtml.includes("1 ignorado"), true);
assert.equal(ignoredHtml.includes("No afectan a la exportación."), true);

const preflightHtml = helpers.preflightListHtml([
  {{ state: "ok", title: "Imágenes", detail: "2 listas" }},
  {{ state: "error", title: "Destino", detail: "Falta <ruta>" }},
]);
assert.equal(preflightHtml.includes('class="preflight-item ok"'), true);
assert.equal(preflightHtml.includes("Falta &lt;ruta&gt;"), true);

assert.equal(helpers.exportPanelStatusLabel({{ status: "running", paused: true }}), "Pausado");
assert.equal(helpers.exportPanelStatusLabel({{ status: "completed" }}), "Exportado");
assert.equal(helpers.exportPanelStatusLabel({{ status: "partial" }}), "Exportado con avisos");
assert.equal(helpers.exportPanelStatusLabel({{
  status: "idle",
  ready: true,
  issues: [{{ level: "warning" }}],
}}), "1 aviso antes de exportar");
assert.equal(helpers.exportPanelStatusLabel({{
  status: "idle",
  ready: false,
  issues: [{{ level: "error", title: "Carpeta de salida" }}],
}}), "Revisar: Carpeta de salida");
assert.equal(helpers.exportPanelStatusLabel({{
  status: "idle",
  ready: false,
  hasActiveBatch: true,
  issues: [{{ level: "warning", title: "Aviso de alpha" }}],
}}), "Pendiente: Aviso de alpha");
assert.equal(helpers.exportPanelStatusLabel({{
  status: "idle",
  ready: true,
  issues: [],
}}), "Listo para exportar");

assert.equal(helpers.exportPreflightSummary({{
  issues: [{{ level: "error" }}, {{ level: "warning" }}],
  exportable: 3,
  ready: false,
}}), "1 bloqueo · 3 exportables");
assert.equal(helpers.exportPreflightSummary({{
  issues: [{{ level: "warning" }}],
  exportable: 3,
  ready: true,
}}), "1 aviso · 3 exportables");
assert.equal(helpers.exportPreflightSummary({{
  issues: [],
  exportable: 3,
  ready: true,
}}), "3 imágenes listas");

assert.equal(helpers.exportStatusClass({{
  status: "failed",
  ready: true,
  issues: [],
  hasActiveBatch: true,
}}), "error");
assert.equal(helpers.exportStatusClass({{
  status: "idle",
  ready: true,
  issues: [{{ level: "error" }}],
  hasActiveBatch: true,
}}), "error");
assert.equal(helpers.exportStatusClass({{
  status: "running",
  ready: true,
  issues: [],
  hasActiveBatch: true,
}}), "running");
assert.equal(helpers.exportStatusClass({{
  status: "partial",
  ready: true,
  issues: [],
  hasActiveBatch: true,
}}), "warning");
assert.equal(helpers.exportStatusClass({{
  status: "idle",
  ready: false,
  issues: [],
  hasActiveBatch: true,
}}), "warning");
assert.equal(helpers.exportStatusClass({{
  status: "idle",
  ready: true,
  issues: [],
  hasActiveBatch: true,
}}), "ready");
assert.equal(helpers.exportStatusClass({{
  status: "idle",
  ready: false,
  issues: [],
  hasActiveBatch: false,
}}), "pending");

assert.deepEqual(helpers.exportPreflightRows({{
  batch: "none",
  destinationFallback: "Salida",
}}), [
  {{ state: "error", title: "Carpeta de origen", detail: "Elige una carpeta para empezar" }},
  {{ state: "pending", title: "Imágenes exportables", detail: "Pendiente" }},
  {{ state: "pending", title: "Carpeta de salida", detail: "Salida" }},
]);

assert.deepEqual(helpers.exportPreflightRows({{
  batch: "empty",
  ignoredCount: 2,
  ignoredSummary: "2 ignorados",
}}), [
  {{ state: "error", title: "Imágenes exportables", detail: "0 imágenes" }},
  {{ state: "pending", title: "Ignorados", detail: "2 ignorados" }},
  {{ state: "pending", title: "Carpeta de salida", detail: "Pendiente" }},
]);

const readyRows = helpers.exportPreflightRows({{
  batch: "ready",
  exportable: 3,
  warningCount: 1,
  ignoredCount: 1,
  ignoredSummary: "1 ignorado",
  destinationFallback: "C:/Export",
  destinationMissing: false,
  naming: "{{original}}{{suffix}}",
  namingExample: "camisa_PRO.jpg",
  issues: [
    {{ level: "warning", title: "Alpha bajo", detail: "Revisar" }},
    {{ level: "error", title: "Sin lote", detail: "Ignorar duplicado" }},
  ],
  ready: false,
}});
assert.deepEqual(readyRows, [
  {{ state: "ok", title: "Imágenes exportables", detail: "3 imagenes" }},
  {{ state: "warning", title: "Avisos", detail: "1 aviso" }},
  {{ state: "pending", title: "Ignorados", detail: "1 ignorado" }},
  {{ state: "ok", title: "Carpeta de salida", detail: "C:/Export" }},
  {{ state: "ok", title: "Nombre de archivo", detail: "camisa_PRO.jpg" }},
  {{ state: "warning", title: "Alpha bajo", detail: "Revisar" }},
]);

const blockedRows = helpers.exportPreflightRows({{
  batch: "ready",
  exportable: 0,
  warningCount: 0,
  ignoredCount: 0,
  ignoredSummary: "Sin ignorados",
  destinationFallback: "Carpeta de salida sin configurar",
  destinationMissing: true,
  naming: "",
  namingExample: "Sin ejemplo",
  issues: [],
  ready: false,
}});
assert.deepEqual(blockedRows, [
  {{ state: "error", title: "Imágenes exportables", detail: "0 imagenes" }},
  {{ state: "ok", title: "Avisos", detail: "Sin avisos" }},
  {{ state: "ok", title: "Ignorados", detail: "Sin ignorados" }},
  {{ state: "error", title: "Carpeta de salida", detail: "Carpeta de salida sin configurar" }},
  {{ state: "error", title: "Nombre de archivo", detail: "Plantilla vacía" }},
]);

const allReadyRows = helpers.exportPreflightRows({{
  batch: "ready",
  exportable: 1,
  warningCount: 0,
  ignoredCount: 0,
  ignoredSummary: "Sin ignorados",
  destinationFallback: "Salida",
  destinationMissing: false,
  naming: "{{original}}",
  namingExample: "camisa.jpg",
  issues: [],
  ready: true,
}});
assert.equal(allReadyRows.at(-1).title, "Estado");
assert.equal(allReadyRows.at(-1).detail, "Sin bloqueos ni avisos");
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
