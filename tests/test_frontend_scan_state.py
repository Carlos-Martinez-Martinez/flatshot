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

assert.equal(helpers.compactScanStatus({{
  batch: "ready",
  exportableImages: 4,
  ignoredFiles: 2,
}}), "4 exportables · 2 ignorados");
assert.equal(helpers.compactScanStatus({{
  batch: "ready",
  exportableImages: 1,
  ignoredFiles: 0,
}}), "1 exportables");
assert.equal(helpers.compactScanStatus({{
  batch: "empty",
  ignoredFiles: 1,
}}), "0 exportables · 1 ignorado");
assert.equal(helpers.compactScanStatus({{ batch: "empty" }}), "Sin imágenes compatibles");
assert.equal(helpers.compactScanStatus({{ batch: "scanning" }}), "Leyendo imágenes");
assert.equal(helpers.compactScanStatus({{ batch: "none", scanStatus: "" }}), "Sin lote");
assert.equal(helpers.compactScanStatus({{ batch: "none", scanStatus: "Ruta vacía" }}), "Ruta vacía");

assert.equal(helpers.sourceFolderName({{
  batch: "scanning",
  scanningFolderName: "Entrada",
}}), "Entrada");
assert.equal(helpers.sourceFolderName({{ batch: "scanning", scanningFolderName: "" }}), "Carpeta");
assert.equal(helpers.sourceFolderName({{
  batch: "ready",
  folders: [{{ name: "Lote A" }}],
}}), "Lote A");
assert.equal(helpers.sourceFolderName({{
  batch: "ready",
  folders: [{{ name: "" }}],
}}), "Carpeta actual");
assert.equal(helpers.sourceFolderName({{
  batch: "ready",
  folders: [{{ name: "A" }}, {{ name: "B" }}],
}}), "2 carpetas");
assert.equal(helpers.sourceFolderName({{
  batch: "none",
  persistedFolderName: "Ultima",
}}), "Ultima");
assert.equal(helpers.sourceFolderName({{
  batch: "empty",
  folders: [],
  hasBatch: false,
}}), "Carpeta actual");
assert.equal(helpers.sourceFolderName({{
  batch: "none",
  folders: [],
  hasBatch: false,
}}), "Pendiente");

assert.equal(helpers.normalBridgeMessage({{
  bridgeMode: "mock",
  bridgeStatus: "connected",
  devMode: true,
}}), "Modo revisión activo.");
assert.equal(helpers.normalBridgeMessage({{
  bridgeMode: "mock",
  bridgeStatus: "connected",
  devMode: false,
}}), "Elige una carpeta local.");
assert.equal(helpers.normalBridgeMessage({{
  bridgeMode: "bridge",
  bridgeStatus: "connected",
  devMode: true,
}}), "Listo.");
assert.equal(helpers.normalBridgeMessage({{
  bridgeMode: "bridge",
  bridgeStatus: "checking",
  devMode: true,
}}), "Comprobando conexión.");
assert.equal(helpers.normalBridgeMessage({{
  bridgeMode: "bridge",
  bridgeStatus: "disconnected",
  devMode: true,
}}), "Conexión local no disponible.");

assert.equal(helpers.sourcePanelClass({{ batch: "scanning" }}), "scanning");
assert.equal(helpers.sourcePanelClass({{ batch: "ready", hasScanError: true }}), "error");
assert.equal(helpers.sourcePanelClass({{ batch: "ready", isBridgeBatch: true }}), "bridge");
assert.equal(helpers.sourcePanelClass({{ batch: "ready", bridgeMode: "bridge" }}), "bridge");
assert.equal(helpers.sourcePanelClass({{ batch: "ready", bridgeMode: "mock" }}), "");

assert.equal(helpers.sourceBadgeClass({{ isBridgeBatch: true, isMockBatch: false }}), "bridge");
assert.equal(helpers.sourceBadgeClass({{ isBridgeBatch: false, isMockBatch: true }}), "ready");
assert.equal(helpers.sourceBadgeClass({{ isBridgeBatch: false, isMockBatch: false }}), "");
assert.equal(helpers.sourceLabel({{ isBridgeBatch: true, devMode: true }}), "Local");
assert.equal(helpers.sourceLabel({{ isMockBatch: true, devMode: true }}), "Demo");
assert.equal(helpers.sourceLabel({{ isMockBatch: true, devMode: false }}), "Local");
assert.equal(helpers.sourceLabel({{ bridgeMode: "bridge", devMode: true }}), "Local");
assert.equal(helpers.sourceLabel({{ bridgeMode: "mock", devMode: true }}), "Demo");

assert.equal(helpers.sourceTitle({{ hasBatch: true, batch: "ready" }}), "Entrada");
assert.equal(helpers.sourceTitle({{ hasBatch: false, batch: "none" }}), "Seleccionar carpeta");
assert.equal(helpers.sourcePickButtonLabel({{ hasBatch: true, batch: "ready" }}), "Cambiar");
assert.equal(helpers.sourcePickButtonLabel({{ hasBatch: false, batch: "none" }}), "Seleccionar carpeta");
assert.equal(helpers.sourceScanButtonLabel({{ hasBatch: true, batch: "ready" }}), "↻");
assert.equal(helpers.sourceScanButtonLabel({{ hasBatch: false, batch: "none" }}), "Escanear");
assert.equal(helpers.sourceScanButtonTitle({{ hasBatch: true, batch: "ready" }}), "Actualizar lote");
assert.equal(helpers.sourceScanButtonTitle({{ hasBatch: false, batch: "none" }}), "Escanear carpeta");
assert.equal(helpers.bridgeMessageClass("connected"), "bridge-message ready");
assert.equal(helpers.bridgeMessageClass("disconnected"), "bridge-message error");
assert.equal(helpers.bridgeMessageClass("checking"), "bridge-message ");
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
