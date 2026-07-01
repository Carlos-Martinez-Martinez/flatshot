function setScenario(scenario) {
  clearTimers();
  thumbnailPreloads.clear();
  thumbnailFallbackQueue.length = 0;
  thumbnailFallbackInFlight.clear();
  clearBridgeExportPoll();
  Object.assign(state, {
    scenario,
    batch: "ready",
    batchSource: "mock",
    selectedImageId: "img-001",
    previewStatus: "ready",
    previewData: null,
    previewError: "",
    thumbnailStatus: {},
    thumbnailErrors: [],
    exportStatus: "ready",
    exportJobId: null,
    exportDestinations: [],
    exportMessages: [],
    exportCompletedItems: [],
    exportIssues: [],
    exportResult: null,
    destinationMode: "source",
    destinationValue: "Salida",
    progress: 0,
    processed: 0,
    errors: [],
    filter: "all",
    search: "",
    fitMode: DEFAULT_VIEW_MODE,
    fitZoom: 100,
    zoom: 100,
    panX: 0,
    panY: 0,
    inspectorTab: "review",
    outputEditMode: false,
    presetEditorOpen: false,
    exportConfirmOpen: false,
    exportConfirmRisks: [],
    exportConfirmOptions: null,
    scanIssues: [],
    scanDiagnostics: mockScanDiagnostics(),
    paused: false,
    statusText: "Listo para exportar",
    scanStatus: "Escenario mock activo",
  });

  if (scenario === "initial") {
    Object.assign(state, {
      batch: "none",
      batchSource: "none",
      selectedImageId: null,
      previewStatus: "empty",
      exportStatus: "blocked",
      statusText: "Sin lote",
      scanStatus: "Sin lote",
      scanDiagnostics: emptyScanDiagnostics(),
    });
  } else if (scenario === "empty-folder") {
    Object.assign(state, {
      batch: "empty",
      batchSource: "mock",
      selectedImageId: null,
      previewStatus: "empty",
      exportStatus: "blocked",
      statusText: "No hay PNG válidos",
      scanStatus: "Carpeta mock vacía",
      scanDiagnostics: emptyScanDiagnostics(),
    });
  } else if (scenario === "preview-loading") {
    Object.assign(state, {
      previewStatus: "loading",
      exportStatus: "ready",
      statusText: "Generando vista",
    });
  } else if (scenario === "preview-warning") {
    Object.assign(state, {
      selectedImageId: "img-003",
      previewStatus: "warning",
      exportStatus: "ready",
      statusText: "Vista con aviso",
    });
  } else if (scenario === "preview-error") {
    Object.assign(state, {
      selectedImageId: "img-004",
      previewStatus: "error",
      exportStatus: "blocked",
      statusText: "Vista no disponible",
    });
  } else if (scenario === "export-blocked") {
    Object.assign(state, {
      destinationMode: "custom",
      destinationValue: "",
      exportStatus: "blocked",
      statusText: "Carpeta de salida sin configurar",
    });
  } else if (scenario === "export-running") {
    Object.assign(state, {
      exportStatus: "running",
      progress: 42,
      processed: 2,
      statusText: `Procesando 2/${exportableImages().length}`,
    });
    render();
    return;
  } else if (scenario === "export-completed") {
    Object.assign(state, {
      exportStatus: "completed",
      progress: 100,
      processed: exportableImages().length,
      exportCompletedItems: exportableImages().map((image) => ({ name: image.name, success: true })),
      exportDestinations: ["Mock / Salida"],
      exportResult: {
        success: true,
        processed: exportableImages().length,
        total: exportableImages().length,
        errors: 0,
        destinations: ["Mock / Salida"],
      },
      statusText: "Exportación completada",
    });
  } else if (scenario === "export-partial") {
    Object.assign(state, {
      exportStatus: "partial",
      progress: 100,
      processed: exportableImages().length,
      exportCompletedItems: [
        { name: "camiseta_001.png", success: true },
        { name: "chaqueta_004.png", success: false },
      ],
      exportDestinations: ["Mock / Salida"],
      exportIssues: [
        { level: "error", title: "chaqueta_004.png", detail: "No se pudo leer alpha." },
        { level: "warning", title: "chaqueta_003.png", detail: "Vista renderizada con fallback." },
      ],
      exportResult: {
        success: false,
        processed: exportableImages().length,
        total: exportableImages().length,
        errors: 1,
        destinations: ["Mock / Salida"],
      },
      errors: [
        { level: "error", title: "chaqueta_004.png", detail: "No se pudo leer alpha." },
        { level: "warning", title: "chaqueta_003.png", detail: "Vista renderizada con fallback." },
      ],
      statusText: "Exportación con errores",
    });
  } else if (scenario === "export-failed") {
    Object.assign(state, {
      exportStatus: "failed",
      progress: 38,
      processed: 2,
      exportIssues: [
        { level: "error", title: "Destino no disponible", detail: "La carpeta ya no existe." },
      ],
      exportResult: {
        success: false,
        processed: 2,
        total: exportableImages().length,
        errors: 1,
        destinations: [],
      },
      errors: [
        { level: "error", title: "Destino no disponible", detail: "La carpeta ya no existe." },
      ],
      statusText: "Exportación fallida",
    });
  }

  render();
}

function loadBatch() {
  if (state.bridgeMode === "bridge") {
    void scanBridgeFolder();
    return;
  }

  clearTimers();
  thumbnailPreloads.clear();
  thumbnailFallbackQueue.length = 0;
  thumbnailFallbackInFlight.clear();
  clearBridgeExportPoll();
  Object.assign(state, {
    scenario: "batch-ready",
    batch: "scanning",
    batchSource: "mock",
    selectedImageId: null,
    previewStatus: "empty",
    previewData: null,
    previewError: "",
    thumbnailStatus: {},
    thumbnailErrors: [],
    exportStatus: "blocked",
    exportJobId: null,
    exportDestinations: [],
    exportMessages: [],
    exportCompletedItems: [],
    exportIssues: [],
    exportResult: null,
    progress: 0,
    processed: 0,
    errors: [],
    scanIssues: [],
    scanDiagnostics: emptyScanDiagnostics(),
    scanStatus: "Escaneando lote mock",
    statusText: "Escaneando carpeta",
  });
  render();
  setTimer(() => {
    Object.assign(state, {
      batch: "ready",
      selectedImageId: "img-001",
      previewStatus: "loading",
      exportStatus: "ready",
      scanDiagnostics: mockScanDiagnostics(),
      statusText: "Generando vista",
    });
    render();
    setTimer(() => {
      Object.assign(state, {
        previewStatus: "ready",
        statusText: "Listo para exportar",
      });
      render();
    }, 550);
  }, 450);
}

function loadMockBatch() {
  if (!devMode) {
    return;
  }
  state.bridgeMode = "mock";
  state.bridgeLastResponse = "Estado mock: lote listo";
  loadBatch();
}

function clearBatch() {
  clearBridgeExportPoll();
  state.outputEditMode = false;
  state.presetEditorOpen = false;
  setScenario("initial");
}

function showEmptyFolder() {
  if (!devMode) {
    return;
  }
  state.bridgeMode = "mock";
  state.bridgeLastResponse = "Estado mock: carpeta vacía";
  setScenario("empty-folder");
}
