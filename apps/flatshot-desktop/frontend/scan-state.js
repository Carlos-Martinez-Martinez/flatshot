(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotScanState = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  function folderPickStartState() {
    return {
      batchDetailOpen: false,
      exportConfirmOpen: false,
      bridgeMode: "bridge",
      bridgeStatus: "checking",
      bridgeMessage: "Abriendo selector",
      bridgeLastResponse: "Solicitando /folders/pick",
      scanStatus: "Elige una carpeta",
      statusText: "Elige una carpeta",
    };
  }

  function folderPickCancelledState() {
    return {
      bridgeStatus: "connected",
      bridgeMessage: "Selección cancelada",
      bridgeLastResponse: "folder pick cancelado",
      scanStatus: "Selección cancelada",
      statusText: "Selección cancelada",
    };
  }

  function folderPickSelectedState(path) {
    return {
      bridgeStatus: "connected",
      bridgeScanPath: path,
      bridgeMessage: "Carpeta seleccionada",
      bridgeLastResponse: "folder pick OK",
      scanStatus: "Carpeta seleccionada",
      statusText: "Carpeta seleccionada",
    };
  }

  function folderPickErrorState(message) {
    return {
      bridgeStatus: "disconnected",
      bridgeMessage: message,
      bridgeLastResponse: `error: ${message}`,
      scanStatus: "No se pudo seleccionar",
      scanIssues: [{ level: "error", title: "Selector no disponible", detail: message }],
      statusText: "Selector no disponible",
    };
  }

  function emptyScanPathState(isConnected) {
    return {
      bridgeStatus: isConnected ? "connected" : "disconnected",
      bridgeMessage: "Ruta vacía",
      scanStatus: "Ruta vacía",
      scanIssues: [{ level: "warning", title: "Ruta vacía", detail: "Pega una carpeta para escanear." }],
      statusText: "Ruta vacía",
    };
  }

  function scanStartState(folders = [], emptyDiagnostics = {}, defaultViewMode = "height") {
    return {
      batch: "scanning",
      batchSource: "bridge",
      selectedImageId: null,
      previewStatus: "empty",
      previewData: null,
      previewError: "",
      thumbnailStatus: {},
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
      fitMode: defaultViewMode,
      fitZoom: 100,
      zoom: 100,
      panX: 0,
      panY: 0,
      scanIssues: [],
      scanDiagnostics: emptyDiagnostics,
      scanStatus: folders.length === 1 ? "Escaneando ruta" : `Escaneando ${folders.length} rutas`,
      statusText: "Escaneando ruta",
      bridgeLastResponse: "Solicitando /folders/scan",
    };
  }

  function scanFailureState(message, emptyDiagnostics = {}) {
    return {
      batch: "none",
      batchSource: "none",
      selectedImageId: null,
      previewStatus: "empty",
      previewData: null,
      previewError: "",
      exportStatus: "blocked",
      scanDiagnostics: emptyDiagnostics,
      bridgeStatus: "disconnected",
      bridgeMessage: message,
      bridgeLastResponse: `error: ${message}`,
      scanStatus: "Conexión local no disponible",
      scanIssues: [{ level: "error", title: "Conexión local no disponible", detail: message }],
      statusText: "No se pudo escanear",
    };
  }

  function scanReadyState(options = {}) {
    const scanIssueCount = Number(options.scanIssueCount) || 0;
    const imageCount = Number(options.imageCount) || 0;
    return {
      batch: "ready",
      selectedImageId: options.selectedImageId,
      localOverride: Boolean(options.localOverride),
      previewStatus: "loading",
      previewData: null,
      previewError: "",
      fitMode: options.defaultViewMode || "height",
      fitZoom: 100,
      zoom: 100,
      panX: 0,
      panY: 0,
      exportStatus: "blocked",
      scanStatus: scanIssueCount
        ? `Escaneo completado con ${scanIssueCount} aviso${scanIssueCount === 1 ? "" : "s"}`
        : `${imageCount} imágenes encontradas`,
      statusText: "Generando vista",
    };
  }

  function scanEmptyState(scanIssues = []) {
    return {
      batch: "empty",
      selectedImageId: null,
      previewStatus: "empty",
      previewData: null,
      previewError: "",
      exportStatus: "blocked",
      scanStatus: scanIssues.length ? scanIssues[0].detail : "No se encontraron PNG válidos",
      statusText: scanIssues.length ? "Revisa carpeta" : "No hay imágenes compatibles",
    };
  }

  function countText(count, singular, plural = `${singular}s`) {
    const value = Number(count) || 0;
    return `${value} ${value === 1 ? singular : plural}`;
  }

  function compactScanStatus(options = {}) {
    const ignoredFiles = Number(options.ignoredFiles) || 0;
    if (options.batch === "ready") {
      return ignoredFiles
        ? `${Number(options.exportableImages) || 0} exportables · ${countText(ignoredFiles, "ignorado", "ignorados")}`
        : `${Number(options.exportableImages) || 0} exportables`;
    }
    if (options.batch === "empty") {
      return ignoredFiles ? `0 exportables · ${countText(ignoredFiles, "ignorado", "ignorados")}` : "Sin imágenes compatibles";
    }
    if (options.batch === "scanning") {
      return "Leyendo imágenes";
    }
    return options.scanStatus || "Sin lote";
  }

  function sourceFolderName(options = {}) {
    const batch = options.batch || "none";
    const folders = Array.isArray(options.folders) ? options.folders : [];
    if (batch === "scanning") {
      return options.scanningFolderName || "Carpeta";
    }
    if (folders.length === 1) {
      return folders[0].name || "Carpeta actual";
    }
    if (folders.length > 1) {
      return `${folders.length} carpetas`;
    }
    if (options.persistedFolderName) {
      return options.persistedFolderName || "Carpeta actual";
    }
    return options.hasBatch || batch === "empty" ? "Carpeta actual" : "Pendiente";
  }

  function normalBridgeMessage(options = {}) {
    if (options.bridgeMode !== "bridge") {
      return options.devMode ? "Modo revisión activo." : "Elige una carpeta local.";
    }
    if (options.bridgeStatus === "connected") {
      return "Listo.";
    }
    if (options.bridgeStatus === "checking") {
      return "Comprobando conexión.";
    }
    if (options.bridgeStatus === "disconnected") {
      return "Conexión local no disponible.";
    }
    return "Elige una carpeta local.";
  }

  function sourcePanelClass(options = {}) {
    if (options.batch === "scanning") {
      return "scanning";
    }
    if (options.hasScanError) {
      return "error";
    }
    if (options.isBridgeBatch || options.bridgeMode === "bridge") {
      return "bridge";
    }
    return "";
  }

  function sourceBadgeClass(options = {}) {
    if (options.isBridgeBatch) {
      return "bridge";
    }
    if (options.isMockBatch) {
      return "ready";
    }
    return "";
  }

  function sourceLabel(options = {}) {
    if (options.isBridgeBatch) {
      return "Local";
    }
    if (options.isMockBatch) {
      return options.devMode ? "Demo" : "Local";
    }
    return options.bridgeMode === "bridge" || !options.devMode ? "Local" : "Demo";
  }

  function sourceTitle(options = {}) {
    return options.hasBatch || options.batch === "empty" ? "Entrada" : "Seleccionar carpeta";
  }

  function sourcePickButtonLabel(options = {}) {
    return options.hasBatch || options.batch === "empty" ? "Cambiar" : "Seleccionar carpeta";
  }

  function sourceScanButtonLabel(options = {}) {
    return options.hasBatch || options.batch === "empty" ? "↻" : "Escanear";
  }

  function sourceScanButtonTitle(options = {}) {
    return options.hasBatch || options.batch === "empty" ? "Actualizar lote" : "Escanear carpeta";
  }

  function bridgeMessageClass(bridgeStatus) {
    return `bridge-message ${bridgeStatus === "connected" ? "ready" : bridgeStatus === "disconnected" ? "error" : ""}`;
  }

  return {
    bridgeMessageClass,
    compactScanStatus,
    emptyScanPathState,
    folderPickCancelledState,
    folderPickErrorState,
    folderPickSelectedState,
    folderPickStartState,
    normalBridgeMessage,
    scanEmptyState,
    scanFailureState,
    scanReadyState,
    scanStartState,
    sourceBadgeClass,
    sourceFolderName,
    sourceLabel,
    sourcePanelClass,
    sourcePickButtonLabel,
    sourceScanButtonLabel,
    sourceScanButtonTitle,
    sourceTitle,
  };
});
