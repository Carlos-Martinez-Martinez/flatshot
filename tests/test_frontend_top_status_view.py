import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "top-status-view.js"
INDEX_PATH = FRONTEND_DIR / "index.html"


def test_top_status_view_helper_loads_before_app_script():
    html = INDEX_PATH.read_text(encoding="utf-8")

    helper_index = html.index("top-status-view.js")
    app_index = html.index("app.js")

    assert helper_index < app_index


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_top_status_view_renders_header_status_contracts():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

assert.equal(helpers.escapeHtml('<a&b"c>'), '&lt;a&amp;b&quot;c&gt;');

assert.equal(helpers.topStatusSummaryHtml({{ hasBatch: false }}), "");
assert.equal(helpers.topStatusSummaryHtml({{ hasBatch: true, exportStatus: "running" }}), "");
const chips = helpers.topStatusSummaryHtml({{
  hasBatch: true,
  exportStatus: "idle",
  formatLabel: 'PNG <alfa>',
  filesFound: 12,
  readyLabel: "10 listas",
  ignoredFiles: 1,
  nonBlockingWarnings: 2,
}});
assert.equal(chips.includes('class="top-status-chips"'), true);
assert.equal(chips.includes("PNG &lt;alfa&gt;"), true);
assert.equal(chips.includes("12 archivos"), true);
assert.equal(chips.includes("1 ignorado"), true);
assert.equal(chips.includes("2 avisos"), true);

assert.equal(helpers.compactHeaderStatusText({{
  exportStatus: "running",
  paused: true,
  processed: 3,
  plannedTotal: 8,
  exportableImages: 4,
}}), "Pausado · 3/8");
assert.equal(helpers.compactHeaderStatusText({{
  exportStatus: "completed",
  exportResultProcessed: 5,
  exportResultTotal: 5,
  exportableImages: 5,
}}), "Exportado · 5/5");
assert.equal(helpers.compactHeaderStatusText({{
  exportStatus: "partial",
  exportResultProcessed: 4,
  exportResultTotal: 5,
  exportableImages: 5,
}}), "Exportado con avisos · 4/5");
assert.equal(helpers.compactHeaderStatusText({{ exportStatus: "failed" }}), "Exportación fallida");
assert.equal(helpers.compactHeaderStatusText({{ batch: "scanning" }}), "Escaneando...");
assert.equal(helpers.compactHeaderStatusText({{ batch: "none" }}), "Sin lote");
assert.equal(helpers.compactHeaderStatusText({{
  batch: "empty",
  filesFound: 6,
  ignoredFiles: 2,
}}), "6 archivos · no hay PNG válidos · 2 ignorados");
assert.equal(helpers.compactHeaderStatusText({{
  batch: "ready",
  formatLabel: "PNG",
  filesFound: 6,
  readyLabel: "4 imágenes listas",
  ignoredFiles: 1,
  nonBlockingWarnings: 1,
}}), "PNG · 6 archivos · 4 imágenes listas · 1 aviso · 1 ignorado");

assert.equal(helpers.topStatusText({{ batch: "scanning" }}), "Escaneando carpeta");
assert.equal(helpers.topStatusText({{ batch: "empty" }}), "No hay PNG válidos");
assert.equal(helpers.topStatusText({{
  batch: "ready",
  compactHeaderStatus: "PNG · 6 archivos",
}}), "PNG · 6 archivos");
assert.equal(helpers.topStatusText({{
  batch: "loading",
  bridgeMode: "bridge",
  bridgeStatus: "disconnected",
}}), "Conexión local no disponible");
assert.equal(helpers.topStatusText({{
  batch: "loading",
  statusText: "Preparando",
}}), "Preparando");

assert.equal(helpers.preflightStatusLabel({{ exportStatus: "running", paused: true }}), "Salida pausada");
assert.equal(helpers.preflightStatusLabel({{ exportStatus: "completed" }}), "Salida completada");
assert.equal(helpers.preflightStatusLabel({{ exportStatus: "partial" }}), "Avisos");
assert.equal(helpers.preflightStatusLabel({{ exportStatus: "failed" }}), "Revisar");
assert.equal(helpers.preflightStatusLabel({{ ready: false, errors: 1 }}), "Revisar");
assert.equal(helpers.preflightStatusLabel({{ ready: false, errors: 0 }}), "Pendiente");
assert.equal(helpers.preflightStatusLabel({{ ready: true, warnings: 2 }}), "2 avisos");
assert.equal(helpers.preflightStatusLabel({{ ready: true, warnings: 0 }}), "Listo");

assert.equal(helpers.preflightStatusClass({{ exportStatus: "failed" }}), "error");
assert.equal(helpers.preflightStatusClass({{ exportStatus: "running", ready: true }}), "warning");
assert.equal(helpers.preflightStatusClass({{ ready: false, errors: 0 }}), "error");
assert.equal(helpers.preflightStatusClass({{ ready: true, warnings: 1 }}), "warning");
assert.equal(helpers.preflightStatusClass({{ ready: true, warnings: 0 }}), "ready");

assert.equal(helpers.topPrimaryHint({{
  primaryAction: {{ action: "start-export", label: "Procesar 4 imágenes" }},
  title: "Listo",
}}), "Procesar 4 imágenes. Atajo: Ctrl+E");
assert.equal(helpers.topPrimaryHint({{
  primaryAction: {{ action: "pick-bridge-folder", label: "Seleccionar carpeta" }},
}}), "Seleccionar carpeta de entrada");
assert.equal(helpers.topPrimaryHint({{
  primaryAction: {{ action: "review-warnings", label: "Revisar" }},
}}), "Revisar avisos del lote");
assert.equal(helpers.topPrimaryHint({{
  primaryAction: {{ action: "open-output", label: "Abrir" }},
}}), "Abrir carpeta de salida");
assert.equal(helpers.topPrimaryHint({{
  primaryAction: {{ label: "Continuar" }},
  title: "Fallback",
}}), "Continuar");
assert.equal(helpers.topPrimaryHint({{
  primaryAction: {{}},
  title: "Fallback",
}}), "Fallback");

assert.equal(helpers.statusBarText({{
  batch: "none",
}}), "Sin lote · Elige una carpeta para empezar");
assert.equal(helpers.statusBarText({{
  batch: "scanning",
  scanStatus: "Leyendo carpeta",
}}), "Escaneando · Leyendo carpeta");
assert.equal(helpers.statusBarText({{
  batch: "empty",
  scanStatus: "",
}}), "0 imágenes · Cambia de carpeta");
assert.equal(helpers.statusBarText({{
  exportStatus: "running",
  paused: false,
  processed: 2,
  plannedTotal: 8,
  exportableImageCount: 4,
  statusText: "Procesando 2/8",
}}), "Exportando 2/8 · Procesando 2/8");
assert.equal(helpers.statusBarText({{
  exportStatus: "running",
  paused: true,
  processed: 2,
  plannedTotal: 0,
  exportableImageCount: 4,
  statusText: "Pausado",
}}), "Pausado 2/4 · Pausado");
assert.equal(helpers.statusBarText({{
  exportStatus: "completed",
  exportResultProcessed: 7,
  exportResultTotal: 8,
  exportableImageCount: 4,
}}), "Última exportación completada · 7/8 archivos");
assert.equal(helpers.statusBarText({{
  exportStatus: "partial",
  processed: 5,
  exportResultTotal: 8,
  exportableImageCount: 4,
}}), "Última exportación con avisos · 5/8 archivos");
assert.equal(helpers.statusBarText({{
  exportStatus: "failed",
  firstErrorDetail: "Destino ocupado",
}}), "Exportación fallida · Destino ocupado");
assert.equal(helpers.statusBarText({{
  batch: "ready",
  counts: {{ exportableImages: 3, nonBlockingWarnings: 1 }},
  imageCount: 5,
  selectedIndex: 1,
  outputCount: 1,
  destinationMode: "source",
  destinationValue: "_SALIDA_PRO",
}}), "3 exportables · Imagen 2/5 · 1 aviso · Salida: origen / _SALIDA_PRO");
assert.equal(helpers.statusBarText({{
  batch: "ready",
  counts: {{ exportableImages: 3, nonBlockingWarnings: 0 }},
  imageCount: 5,
  selectedIndex: -1,
  outputCount: 2,
  destinationMode: "custom",
  destinationValue: "C:/Export",
}}), "3 exportables · Sin selección · Salida: 2 salidas");
assert.equal(helpers.statusBarText({{
  batch: "ready",
  counts: {{ exportableImages: 3, nonBlockingWarnings: 0 }},
  imageCount: 5,
  selectedIndex: 0,
  outputCount: 1,
  destinationMode: "custom",
  destinationValue: "",
}}), "3 exportables · Imagen 1/5 · Salida: sin destino");
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
