import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "scan-state.js"
SCAN_RESULT_PAGES_PATH = FRONTEND_DIR / "scan-result-pages.js"
INDEX_PATH = FRONTEND_DIR / "index.html"
APP_BRIDGE_SCAN_CONTROLLER_PATH = FRONTEND_DIR / "app-bridge-scan-controller.js"


def test_scan_state_helper_loads_before_app_script():
    html = INDEX_PATH.read_text(encoding="utf-8")

    helper_index = html.index("scan-state.js")
    app_index = html.index("app.js")

    assert helper_index < app_index


def test_bridge_scan_controller_collects_completed_scan_results_in_pages():
    source = APP_BRIDGE_SCAN_CONTROLLER_PATH.read_text(encoding="utf-8")

    assert "collectBridgeScanJobResultPages" in source
    assert "scanResultPageHelpers.scanJobStatusUrl(jobId, 0)" in source
    assert "scanResultPageHelpers.nextScanResultOffset(page)" in source
    assert "scanResultPageHelpers.mergeBridgeScanResultPages" in source


def test_scan_result_pages_helper_loads_before_app_script():
    html = INDEX_PATH.read_text(encoding="utf-8")

    helper_index = html.index("scan-result-pages.js")
    app_index = html.index("app.js")

    assert helper_index < app_index


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_scan_result_pages_helper_merges_pages_and_builds_urls():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(SCAN_RESULT_PAGES_PATH))});

assert.equal(
  helpers.scanJobStatusUrl("job 1", 500),
  "/folders/scan/jobs/job%201?imageOffset=500&imageLimit=500",
);
assert.equal(helpers.scanJobCancelUrl("job 1"), "/folders/scan/jobs/job%201/cancel");
assert.deepEqual(helpers.scanJobPayload(["C:/a"], {{ imageOverrides: {{ one: true }}, scanRecursive: true }}), {{
  folders: ["C:/a"],
  imageOverrides: {{ one: true }},
  recursive: true,
  scanMode: "verified",
}});
assert.equal(helpers.isScanCancelledError(new Error("Escaneo cancelado.")), true);
assert.equal(helpers.isScanJobUnsupportedError(new Error("HTTP 405")), true);
assert.equal(helpers.nextScanResultOffset({{ imageOffset: 500, imageCount: 125 }}), 625);

const merged = helpers.mergeBridgeScanResultPages(
  {{
    totalImages: 3,
    folders: [
      {{ path: "C:/a", images: [{{ name: "a-0.png" }}], validImages: 2 }},
      {{ path: "C:/b", images: [], validImages: 1 }},
    ],
    page: {{ imageOffset: 0, imageLimit: 1, imageCount: 1, totalImages: 3, hasMore: true }},
  }},
  {{
    totalImages: 3,
    folders: [
      {{ path: "C:/a", images: [{{ name: "a-1.png" }}], validImages: 2 }},
      {{ path: "C:/b", images: [{{ name: "b-0.png" }}], validImages: 1 }},
    ],
    page: {{ imageOffset: 1, imageLimit: 2, imageCount: 2, totalImages: 3, hasMore: false }},
  }},
);

assert.deepEqual(merged.page, {{ imageOffset: 1, imageLimit: 2, imageCount: 2, totalImages: 3, hasMore: false }});
assert.deepEqual(merged.folders[0].images.map((image) => image.name), ["a-0.png", "a-1.png"]);
assert.deepEqual(merged.folders[1].images.map((image) => image.name), ["b-0.png"]);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout


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
  bridgeMessage: "Ruta lista",
  bridgeLastResponse: "folder pick OK",
  scanStatus: "Ruta lista para escanear",
  statusText: "Ruta lista para escanear",
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
  scanIssues: [{{ level: "warning", title: "Ruta vacía", detail: "Introduce o selecciona una carpeta para escanear." }}],
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
  scanJobId: null,
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
  bridgeLastResponse: "Solicitando /folders/scan/jobs",
}});

assert.deepEqual(helpers.scanCancelledState({{ totalFiles: 0 }}), {{
  batch: "none",
  batchSource: "none",
  selectedImageId: null,
  previewStatus: "empty",
  previewData: null,
  previewError: "",
  exportStatus: "blocked",
  progress: 0,
  processed: 0,
  scanJobId: null,
  scanDiagnostics: {{ totalFiles: 0 }},
  bridgeStatus: "connected",
  bridgeMessage: "Escaneo cancelado",
  bridgeLastResponse: "scan cancelado",
  scanStatus: "Escaneo cancelado",
  scanIssues: [],
  statusText: "Escaneo cancelado",
}});

assert.deepEqual(helpers.scanJobProgressState({{
  jobId: "scan-1",
  status: "running",
  progress: {{ processed: 7, total: 20, percent: 35 }},
}}), {{
  progress: 35,
  processed: 7,
  scanStatus: "Escaneando 7/20",
  statusText: "Escaneando 7/20",
  bridgeLastResponse: "scan job scan-1 · running",
}});

assert.deepEqual(helpers.scanJobProgressState({{
  jobId: "scan-1",
  status: "cancelling",
  progress: {{ processed: 7, total: 20, percent: 35 }},
}}), {{
  progress: 35,
  processed: 7,
  scanStatus: "Deteniendo escaneo...",
  statusText: "Deteniendo escaneo...",
  bridgeLastResponse: "scan job scan-1 · cancelling",
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
assert.equal(helpers.sourcePickButtonLabel({{ hasBatch: false, batch: "none" }}), "Buscar carpeta");
assert.equal(helpers.sourceScanButtonLabel({{ hasBatch: true, batch: "ready" }}), "↻");
assert.equal(helpers.sourceScanButtonLabel({{ hasBatch: false, batch: "none" }}), "Escanear");
assert.equal(helpers.sourceScanButtonTitle({{ hasBatch: true, batch: "ready" }}), "Actualizar lote");
assert.equal(helpers.sourceScanButtonTitle({{ hasBatch: false, batch: "none" }}), "Escanear carpeta");
assert.equal(helpers.bridgeMessageClass("connected"), "bridge-message ready");
assert.equal(helpers.bridgeMessageClass("disconnected"), "bridge-message error");
assert.equal(helpers.bridgeMessageClass("checking"), "bridge-message ");

assert.equal(helpers.bridgeStatusClass({{
  bridgeMode: "mock",
  bridgeStatus: "connected",
  devMode: true,
}}), "idle");
assert.equal(helpers.bridgeStatusClass({{
  bridgeMode: "mock",
  bridgeStatus: "connected",
  devMode: false,
}}), "connected");
assert.equal(helpers.bridgeStatusClass({{
  bridgeMode: "bridge",
  bridgeStatus: "checking",
  devMode: true,
}}), "checking");
assert.equal(helpers.bridgeStatusClass({{
  bridgeMode: "bridge",
  bridgeStatus: "",
  devMode: true,
}}), "idle");

assert.equal(helpers.bridgeStatusLabel({{
  bridgeMode: "mock",
  bridgeStatus: "connected",
  devMode: true,
}}), "Demo");
assert.equal(helpers.bridgeStatusLabel({{
  bridgeMode: "bridge",
  bridgeStatus: "connected",
  devMode: true,
}}), "Listo");
assert.equal(helpers.bridgeStatusLabel({{
  bridgeMode: "bridge",
  bridgeStatus: "checking",
  devMode: true,
}}), "Comprobando");
assert.equal(helpers.bridgeStatusLabel({{
  bridgeMode: "bridge",
  bridgeStatus: "disconnected",
  devMode: true,
}}), "Sin conexión local");
assert.equal(helpers.bridgeStatusLabel({{
  bridgeMode: "bridge",
  bridgeStatus: "idle",
  devMode: true,
}}), "Pendiente");

assert.deepEqual(helpers.sourcePanelViewState({{
  batch: "ready",
  bridgeMode: "bridge",
  bridgeStatus: "connected",
  devMode: true,
  exportableImages: 4,
  folders: [{{ name: "Lote A" }}],
  hasBatch: true,
  hasScanError: false,
  ignoredFiles: 2,
  isBridgeBatch: true,
  isMockBatch: false,
  persistedFolderName: "Ultima",
  scanStatus: "Listo",
  scanningFolderName: "",
}}), {{
  panelClass: "bridge",
  badgeClass: "bridge",
  badgeLabel: "Local",
  title: "Entrada",
  folderName: "Lote A",
  scanStatus: "4 exportables · 2 ignorados",
  pickButtonLabel: "Cambiar",
  scanButtonLabel: "↻",
  scanButtonTitle: "Actualizar lote",
  controlsDisabled: false,
  message: "Listo.",
  messageClass: "bridge-message ready",
}});

assert.deepEqual(helpers.sourcePanelViewState({{
  batch: "scanning",
  bridgeMode: "bridge",
  bridgeStatus: "checking",
  devMode: true,
  exportableImages: 0,
  folders: [],
  hasBatch: false,
  hasScanError: false,
  ignoredFiles: 0,
  isBridgeBatch: false,
  isMockBatch: false,
  persistedFolderName: "",
  scanStatus: "Escaneando ruta",
  scanningFolderName: "Entrada",
}}), {{
  panelClass: "scanning",
  badgeClass: "",
  badgeLabel: "Local",
  title: "Seleccionar carpeta",
  folderName: "Entrada",
  scanStatus: "Leyendo imágenes",
  pickButtonLabel: "Buscar carpeta",
  scanButtonLabel: "Escanear",
  scanButtonTitle: "Escanear carpeta",
  controlsDisabled: true,
  message: "Comprobando conexión.",
  messageClass: "bridge-message ",
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
