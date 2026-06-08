import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "scan-state.js"
INDEX_PATH = FRONTEND_DIR / "index.html"


def test_scan_state_helper_loads_before_app_script():
    html = INDEX_PATH.read_text(encoding="utf-8")

    helper_index = html.index("scan-state.js")
    app_index = html.index("app.js")

    assert helper_index < app_index


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_scan_state_helpers_keep_folder_and_scan_transition_contracts():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

assert.deepEqual(helpers.folderPickStartState(), {{
  batchDetailOpen: false,
  exportConfirmOpen: false,
  bridgeMode: "bridge",
  bridgeStatus: "checking",
  bridgeMessage: "Abriendo selector",
  bridgeLastResponse: "Solicitando /folders/pick",
  scanStatus: "Elige una carpeta",
  statusText: "Elige una carpeta",
}});

assert.deepEqual(helpers.folderPickCancelledState(), {{
  bridgeStatus: "connected",
  bridgeMessage: "Selección cancelada",
  bridgeLastResponse: "folder pick cancelado",
  scanStatus: "Selección cancelada",
  statusText: "Selección cancelada",
}});

assert.deepEqual(helpers.folderPickSelectedState("C:/lote"), {{
  bridgeStatus: "connected",
  bridgeScanPath: "C:/lote",
  bridgeMessage: "Carpeta seleccionada",
  bridgeLastResponse: "folder pick OK",
  scanStatus: "Carpeta seleccionada",
  statusText: "Carpeta seleccionada",
}});

assert.deepEqual(helpers.folderPickErrorState("offline"), {{
  bridgeStatus: "disconnected",
  bridgeMessage: "offline",
  bridgeLastResponse: "error: offline",
  scanStatus: "No se pudo seleccionar",
  scanIssues: [{{ level: "error", title: "Selector no disponible", detail: "offline" }}],
  statusText: "Selector no disponible",
}});

assert.deepEqual(helpers.emptyScanPathState(true), {{
  bridgeStatus: "connected",
  bridgeMessage: "Ruta vacía",
  scanStatus: "Ruta vacía",
  scanIssues: [{{ level: "warning", title: "Ruta vacía", detail: "Pega una carpeta para escanear." }}],
  statusText: "Ruta vacía",
}});

assert.deepEqual(helpers.scanStartState(["C:/a", "C:/b"], {{ totalFiles: 0 }}, "fit"), {{
  batch: "scanning",
  batchSource: "bridge",
  selectedImageId: null,
  previewStatus: "empty",
  previewData: null,
  previewError: "",
  thumbnailStatus: {{}},
  thumbnailErrors: [],
  exportStatus: "blocked",
  progress: 0,
  processed: 0,
  exportJobId: null,
  exportDestinations: [],
  exportMessages: [],
  exportCompletedItems: [],
  exportIssues: [],
  exportResult: null,
  errors: [],
  filter: "all",
  search: "",
  fitMode: "fit",
  fitZoom: 100,
  zoom: 100,
  panX: 0,
  panY: 0,
  scanIssues: [],
  scanDiagnostics: {{ totalFiles: 0 }},
  scanStatus: "Escaneando 2 rutas",
  statusText: "Escaneando ruta",
  bridgeLastResponse: "Solicitando /folders/scan",
}});

assert.deepEqual(helpers.scanFailureState("timeout", {{ totalFiles: 0 }}), {{
  batch: "none",
  batchSource: "none",
  selectedImageId: null,
  previewStatus: "empty",
  previewData: null,
  previewError: "",
  exportStatus: "blocked",
  scanDiagnostics: {{ totalFiles: 0 }},
  bridgeStatus: "disconnected",
  bridgeMessage: "timeout",
  bridgeLastResponse: "error: timeout",
  scanStatus: "Conexión local no disponible",
  scanIssues: [{{ level: "error", title: "Conexión local no disponible", detail: "timeout" }}],
  statusText: "No se pudo escanear",
}});

assert.deepEqual(helpers.scanReadyState({{
  defaultViewMode: "height",
  imageCount: 3,
  localOverride: true,
  scanIssueCount: 1,
  selectedImageId: "img-1",
}}), {{
  batch: "ready",
  selectedImageId: "img-1",
  localOverride: true,
  previewStatus: "loading",
  previewData: null,
  previewError: "",
  fitMode: "height",
  fitZoom: 100,
  zoom: 100,
  panX: 0,
  panY: 0,
  exportStatus: "blocked",
  scanStatus: "Escaneo completado con 1 aviso",
  statusText: "Generando vista",
}});

assert.deepEqual(helpers.scanReadyState({{ imageCount: 3, selectedImageId: "img-1" }}).scanStatus, "3 imágenes encontradas");
assert.deepEqual(helpers.scanEmptyState([]), {{
  batch: "empty",
  selectedImageId: null,
  previewStatus: "empty",
  previewData: null,
  previewError: "",
  exportStatus: "blocked",
  scanStatus: "No se encontraron PNG válidos",
  statusText: "No hay imágenes compatibles",
}});
assert.deepEqual(helpers.scanEmptyState([{{ detail: "Solo subcarpetas" }}]).scanStatus, "Solo subcarpetas");
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
