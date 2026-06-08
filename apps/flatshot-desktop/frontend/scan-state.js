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

  return {
    emptyScanPathState,
    folderPickCancelledState,
    folderPickErrorState,
    folderPickSelectedState,
    folderPickStartState,
    scanEmptyState,
    scanFailureState,
    scanReadyState,
    scanStartState,
  };
});
