const mockFolders = [
  {
    id: "camisetas",
    name: "Camisetas Mayo",
    path: "D:/Produccion/Camisetas Mayo",
    count: 18,
    status: "ready",
    detail: "18 PNG",
  },
  {
    id: "chaquetas",
    name: "Chaquetas Lookbook",
    path: "D:/Produccion/Chaquetas Lookbook",
    count: 6,
    status: "warning",
    detail: "1 aviso",
  },
];

const mockImages = [
  {
    id: "img-001",
    folderId: "camisetas",
    name: "camiseta_001.png",
    detail: "1800x2400 · 1.4 MB",
    status: "ready",
    tone: "tone-a",
    exportable: true,
  },
  {
    id: "img-002",
    folderId: "camisetas",
    name: "camiseta_002.png",
    detail: "Ajuste local · 1.2 MB",
    status: "adjusted",
    tone: "tone-b",
    exportable: true,
  },
  {
    id: "img-003",
    folderId: "chaquetas",
    name: "chaqueta_003.png",
    detail: "Preview con aviso",
    status: "warning",
    tone: "tone-c",
    exportable: true,
  },
  {
    id: "img-004",
    folderId: "chaquetas",
    name: "chaqueta_004.png",
    detail: "Error de alpha",
    status: "error",
    tone: "tone-d",
    exportable: false,
  },
  {
    id: "img-005",
    folderId: "camisetas",
    name: "sudadera_005.png",
    detail: "Lista",
    status: "ready",
    tone: "tone-e",
    exportable: true,
  },
];

const mockPresets = [
  "Luz cenital",
  "Estándar oscuro",
  "Complementos",
  "Sin sombra",
];

const defaultBridgeUrl = "http://127.0.0.1:8765";
const devMode = new URLSearchParams(window.location.search).get("dev") === "1";
document.documentElement.classList.toggle("dev-mode", devMode);

const statusLabels = {
  ready: "Lista",
  adjusted: "Ajustada",
  warning: "Aviso",
  error: "Error",
};

const scenarioLabels = {
  initial: "Sin lote",
  "batch-ready": "Lote listo",
  "empty-folder": "Carpeta vacía",
  "preview-loading": "Preview cargando",
  "preview-warning": "Preview con aviso",
  "preview-error": "Error de preview",
  "export-blocked": "Destino sin configurar",
  "export-ready": "Exportación lista",
  "export-running": "Exportación en curso",
  "export-completed": "Exportación completada",
  "export-partial": "Completada con errores",
  "export-failed": "Exportación fallida",
};

const shadowSettingKeys = [
  "angle",
  "distance",
  "blur",
  "spread",
  "fusion",
  "opacity",
  "noise",
  "padding",
  "contact_blur",
  "contraction",
  "adaptive_zoom",
  "scale_adjustment",
  "shadow_engine",
  "transparent_bg",
  "bg_color",
];

const advancedSettingKeys = [
  "spread",
  "noise",
  "contact_blur",
  "scale_adjustment",
  "fusion",
  "angle",
  "contraction",
  "adaptive_zoom",
  "shadow_engine",
];

const defaultSettings = {
  angle: 180,
  opacity: 20,
  blur: 30,
  distance: 25,
  spread: 0,
  fusion: 1,
  noise: 2,
  padding: 10,
  contact_blur: 10,
  contraction: 0,
  adaptive_zoom: true,
  scale_adjustment: 0,
  shadow_engine: "realistic_v2",
  transparent_bg: false,
  bg_color: [230, 230, 230],
};

const mockPresetSettings = {
  "Luz cenital": { ...defaultSettings },
  "Estándar oscuro": {
    ...defaultSettings,
    distance: 20,
    blur: 40,
    spread: 3,
    fusion: 5,
    opacity: 45,
    noise: 5,
    contact_blur: 12,
  },
  Complementos: {
    ...defaultSettings,
    distance: 18,
    blur: 22,
    opacity: 26,
    padding: 8,
    scale_adjustment: 4,
  },
  "Sin sombra": {
    ...defaultSettings,
    distance: 0,
    blur: 0,
    spread: 0,
    fusion: 0,
    opacity: 0,
    noise: 0,
    contact_blur: 0,
  },
};

const state = {
  scenario: "initial",
  batch: "none",
  batchSource: "none",
  selectedImageId: null,
  previewStatus: "empty",
  previewRequestId: 0,
  previewData: null,
  previewError: "",
  previewMode: "processed",
  previewBg: "rgb230",
  zoom: 100,
  fitMode: "fit",
  filter: "all",
  search: "",
  inspectorTab: "adjustments",
  inspectorCollapsed: false,
  activePreset: "Luz cenital",
  settings: { ...defaultSettings },
  presetDirty: false,
  presetSource: "Bridge local",
  localOverride: false,
  exportStatus: "blocked",
  exportJobId: null,
  exportDestinations: [],
  exportMessages: [],
  exportCompletedItems: [],
  exportIssues: [],
  exportResult: null,
  exportPollTimer: null,
  destinationMode: "source",
  destinationValue: "_SALIDA_PRO",
  format: "JPG",
  size: "1800x2400",
  background: "rgb230",
  naming: "{original}{suffix}",
  progress: 0,
  processed: 0,
  errors: [],
  paused: false,
  statusText: "Añade una carpeta",
  bridgeMode: "bridge",
  bridgeUrl: defaultBridgeUrl,
  bridgeStatus: "idle",
  bridgeMessage: "Selecciona una carpeta local",
  bridgeLastResponse: "Bridge pendiente",
  bridgeCapabilitiesSummary: "Sin comprobar",
  bridgeCapabilities: null,
  bridgePresets: [],
  bridgePresetSource: "unavailable",
  bridgePresetWarning: "",
  bridgeScanPath: "",
  scanStatus: "Selecciona una carpeta con PNG.",
  scanIssues: [],
  scanDiagnostics: {
    totalFiles: 0,
    totalImages: 0,
    totalOmitted: 0,
    omittedByReason: {},
    omitted: [],
  },
  realFolders: [],
  realImages: [],
};

const timers = new Set();

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function setTimer(callback, delay) {
  const timer = window.setTimeout(() => {
    timers.delete(timer);
    callback();
  }, delay);
  timers.add(timer);
  return timer;
}

function clearTimers() {
  timers.forEach((timer) => window.clearTimeout(timer));
  timers.clear();
}

function selectedImage() {
  return activeImages().find((image) => image.id === state.selectedImageId)
    || mockImages.find((image) => image.id === state.selectedImageId)
    || null;
}

function hasBatch() {
  return state.batch === "ready" || state.batch === "scanning";
}

function isBridgeBatch() {
  return state.batchSource === "bridge";
}

function isMockBatch() {
  return state.batchSource === "mock";
}

function activeImages() {
  if (state.batch !== "ready") {
    return [];
  }
  if (isBridgeBatch()) {
    return state.realImages;
  }
  return isMockBatch() ? mockImages : [];
}

function activeFolders() {
  if (state.batch !== "ready") {
    return [];
  }
  if (isBridgeBatch()) {
    return state.realFolders;
  }
  return isMockBatch() ? mockFolders : [];
}

function activePresets() {
  return activePresetItems().map((preset) => preset.name);
}

function activePresetItems() {
  if (state.bridgeMode === "bridge" && state.bridgePresets.length) {
    return state.bridgePresets;
  }
  return mockPresets.map((name) => ({
    name,
    category: devMode ? "Mock" : "Fallback local",
    categoryId: devMode ? "mock" : "fallback",
    settings: normalizeSettings(mockPresetSettings[name]),
    source: devMode ? "mock" : "fallback",
  }));
}

function activePresetItem() {
  return activePresetItems().find((preset) => preset.name === state.activePreset) || null;
}

function exportableImages() {
  return activeImages().filter((image) => image.exportable);
}

function exportItemState(image) {
  const items = Array.isArray(state.exportCompletedItems) ? state.exportCompletedItems : [];
  if (!items.length || !image?.name) {
    return null;
  }
  const sourceName = image.name.toLowerCase();
  const sourceStem = sourceName.replace(/\.[^.]+$/, "");
  const matches = items.filter((item) => {
    const itemName = String(item.name || "").toLowerCase();
    return itemName === sourceName
      || itemName === sourceStem
      || itemName.startsWith(`${sourceStem}.`)
      || itemName.startsWith(`${sourceStem}_`);
  });
  if (matches.some((item) => item.success === false)) {
    return { status: "error", label: "Error" };
  }
  if (matches.some((item) => item.success === true)) {
    return { status: "exported", label: "Exportada" };
  }
  return null;
}

function filteredImages() {
  const term = state.search.trim().toLowerCase();
  return activeImages().filter((image) => {
    if (term && !image.name.toLowerCase().includes(term)) {
      return false;
    }
    if (state.filter === "valid") {
      return image.status === "ready" || image.status === "adjusted";
    }
    if (state.filter === "warnings") {
      return image.status === "warning";
    }
    if (state.filter === "errors") {
      return image.status === "error" || exportItemState(image)?.status === "error";
    }
    return true;
  });
}

function filterDisplayName(filter = state.filter) {
  const labels = {
    all: "todas",
    valid: "válidas",
    warnings: "avisos",
    errors: "errores",
  };
  return labels[filter] || "imágenes";
}

function filterStatusText(filter = state.filter) {
  if (filter === "all") {
    return "Mostrando todo";
  }
  return `Mostrando ${filterDisplayName(filter)}`;
}

function validationIssues() {
  const issues = [];
  if (state.batch === "none") {
    issues.push({ level: "warning", title: "Sin lote", detail: "Añade una carpeta." });
  }
  if (state.batch === "empty") {
    issues.push({ level: "warning", title: "No hay PNG válidos", detail: "Elige otra carpeta." });
  }
  if (exportableImages().length === 0 && state.batch === "ready") {
    issues.push({ level: "error", title: "Sin imágenes exportables", detail: "Revisa los errores." });
  }
  if (!state.naming.trim()) {
    issues.push({ level: "error", title: "Naming vacío", detail: "Define una plantilla." });
  }
  if (state.destinationMode === "custom" && !state.destinationValue.trim()) {
    issues.push({ level: "error", title: "Destino sin configurar", detail: "Elige una carpeta." });
  }
  return issues;
}

function preflightIssues() {
  const issues = [...validationIssues(), ...state.errors];
  const omitted = Number(state.scanDiagnostics?.totalOmitted || 0);
  const warningImages = activeImages().filter((image) => image.status === "warning").length;
  const errorImages = activeImages().filter((image) => image.status === "error" || exportItemState(image)?.status === "error").length;

  if (omitted > 0 && hasBatch()) {
    issues.push({
      level: "warning",
      title: "Imágenes omitidas",
      detail: omittedSummaryText(state.scanDiagnostics),
    });
  }
  if (warningImages > 0) {
    issues.push({
      level: "warning",
      title: "Imágenes con aviso",
      detail: `${warningImages} imagen${warningImages === 1 ? "" : "es"} requiere${warningImages === 1 ? "" : "n"} revisión.`,
    });
  }
  if (errorImages > 0 && exportableImages().length > 0) {
    issues.push({
      level: "warning",
      title: "Imágenes no exportables",
      detail: `${errorImages} imagen${errorImages === 1 ? "" : "es"} quedará${errorImages === 1 ? "" : "n"} fuera de la salida.`,
    });
  }

  return issues;
}

function preflightCounts() {
  const issues = preflightIssues();
  return {
    errors: issues.filter((issue) => issue.level === "error").length,
    warnings: issues.filter((issue) => issue.level !== "error").length,
  };
}

function isExportReady() {
  return validationIssues().filter((issue) => issue.level === "error" || issue.title !== "Sin lote").length === 0
    && hasBatch()
    && exportableImages().length > 0;
}

function setScenario(scenario) {
  clearTimers();
  clearBridgeExportPoll();
  Object.assign(state, {
    scenario,
    batch: "ready",
    batchSource: "mock",
    selectedImageId: "img-001",
    previewStatus: "ready",
    previewData: null,
    previewError: "",
    exportStatus: "ready",
    exportJobId: null,
    exportDestinations: [],
    exportMessages: [],
    exportCompletedItems: [],
    exportIssues: [],
    exportResult: null,
    destinationMode: "source",
    destinationValue: "_SALIDA_PRO",
    progress: 0,
    processed: 0,
    errors: [],
    filter: "all",
    search: "",
    scanIssues: [],
    scanDiagnostics: mockScanDiagnostics(),
    paused: false,
    statusText: "Listo para procesar",
    scanStatus: "Escenario mock activo",
  });

  if (scenario === "initial") {
    Object.assign(state, {
      batch: "none",
      batchSource: "none",
      selectedImageId: null,
      previewStatus: "empty",
      exportStatus: "blocked",
      statusText: "Añade una carpeta",
      scanStatus: "Selecciona una carpeta con PNG.",
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
      statusText: "Generando preview",
    });
  } else if (scenario === "preview-warning") {
    Object.assign(state, {
      selectedImageId: "img-003",
      previewStatus: "warning",
      exportStatus: "ready",
      statusText: "Preview con aviso",
    });
  } else if (scenario === "preview-error") {
    Object.assign(state, {
      selectedImageId: "img-004",
      previewStatus: "error",
      exportStatus: "blocked",
      statusText: "Preview no disponible",
    });
  } else if (scenario === "export-blocked") {
    Object.assign(state, {
      destinationMode: "custom",
      destinationValue: "",
      exportStatus: "blocked",
      statusText: "Destino sin configurar",
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
      exportDestinations: ["Mock / _SALIDA_PRO"],
      exportResult: {
        success: true,
        processed: exportableImages().length,
        total: exportableImages().length,
        errors: 0,
        destinations: ["Mock / _SALIDA_PRO"],
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
      exportDestinations: ["Mock / _SALIDA_PRO"],
      exportIssues: [
        { level: "error", title: "chaqueta_004.png", detail: "No se pudo leer alpha." },
        { level: "warning", title: "chaqueta_003.png", detail: "Preview renderizada con fallback." },
      ],
      exportResult: {
        success: false,
        processed: exportableImages().length,
        total: exportableImages().length,
        errors: 1,
        destinations: ["Mock / _SALIDA_PRO"],
      },
      errors: [
        { level: "error", title: "chaqueta_004.png", detail: "No se pudo leer alpha." },
        { level: "warning", title: "chaqueta_003.png", detail: "Preview renderizada con fallback." },
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
  clearBridgeExportPoll();
  Object.assign(state, {
    scenario: "batch-ready",
    batch: "scanning",
    batchSource: "mock",
    selectedImageId: null,
    previewStatus: "empty",
    previewData: null,
    previewError: "",
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
      statusText: "Generando preview",
    });
    render();
    setTimer(() => {
      Object.assign(state, {
        previewStatus: "ready",
        statusText: "Listo para procesar",
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

function selectImage(imageId) {
  const image = activeImages().find((item) => item.id === imageId);
  if (!image) {
    return;
  }
  clearTimers();
  state.selectedImageId = image.id;
  state.localOverride = image.status === "adjusted";
  state.fitMode = "fit";
  state.zoom = 100;
  if (image.source === "bridge") {
    void requestBridgePreview(image);
    return;
  }
  state.previewStatus = "loading";
  state.previewData = null;
  state.previewError = "";
  state.statusText = "Generando preview";
  render();
  setTimer(() => {
    state.previewStatus = image.status === "error" ? "error" : image.status === "warning" ? "warning" : "ready";
    state.statusText = state.previewStatus === "error" ? "Preview no disponible" : "Preview lista";
    render();
  }, 380);
}

function selectAdjacentImage(delta) {
  const images = filteredImages();
  if (!images.length) {
    return;
  }
  const currentIndex = images.findIndex((image) => image.id === state.selectedImageId);
  const startIndex = currentIndex >= 0 ? currentIndex : 0;
  const nextIndex = Math.max(0, Math.min(images.length - 1, startIndex + delta));
  selectImage(images[nextIndex].id);
}

function normalizeSettings(settings = {}) {
  const source = settings && typeof settings === "object" ? settings : {};
  const normalized = { ...defaultSettings };
  shadowSettingKeys.forEach((key) => {
    if (source[key] === undefined || source[key] === null) {
      return;
    }
    if (key === "adaptive_zoom" || key === "transparent_bg") {
      normalized[key] = Boolean(source[key]);
      return;
    }
    if (key === "shadow_engine") {
      normalized[key] = source[key] === "legacy" ? "legacy" : "realistic_v2";
      return;
    }
    if (key === "bg_color") {
      normalized[key] = Array.isArray(source[key]) && source[key].length === 3
        ? source[key].map((channel) => Number(channel))
        : defaultSettings.bg_color;
      return;
    }
    normalized[key] = Number(source[key]);
  });
  return normalized;
}

function presetItemByName(name) {
  return activePresetItems().find((preset) => preset.name === name) || null;
}

function applyPresetSettings(name, options = {}) {
  const preset = presetItemByName(name);
  if (!preset) {
    return false;
  }
  state.activePreset = preset.name;
  state.settings = normalizeSettings(preset.settings);
  state.presetDirty = false;
  state.presetSource = preset.source === "bridge"
    ? `Bridge local · ${preset.category || "Preset"}`
    : devMode ? "Mock" : "Fallback local";
  const advanced = $("#advanced-settings");
  if (advanced) {
    advanced.open = false;
  }
  state.statusText = options.statusText || `Preset: ${preset.name}`;
  if (options.refresh !== false) {
    refreshPreviewAfterSettingChange();
  }
  return true;
}

function resetActivePresetSettings() {
  if (applyPresetSettings(state.activePreset, { statusText: "Ajustes restaurados" })) {
    return;
  }
  state.settings = { ...defaultSettings };
  state.presetDirty = false;
  state.presetSource = state.bridgeMode === "bridge" || !devMode ? "Bridge local · defaults" : "Mock";
  state.statusText = "Ajustes restaurados";
  refreshPreviewAfterSettingChange();
}

function markPresetDirty() {
  state.presetDirty = true;
  state.presetSource = state.bridgeMode === "bridge" || !devMode ? "Bridge local · modificado" : "Mock · modificado";
  refreshPreviewAfterSettingChange();
}

function refreshPreviewAfterSettingChange() {
  if (selectedImage()?.source === "bridge") {
    state.previewStatus = "loading";
    state.previewData = null;
    state.previewError = "";
    state.statusText = "Generando preview";
    render();
    clearTimers();
    setTimer(() => {
      const image = selectedImage();
      if (image?.source === "bridge") {
        void requestBridgePreview(image);
      }
    }, 360);
    return;
  }
  if (hasBatch() && state.previewStatus !== "error") {
    state.previewStatus = "loading";
    state.statusText = "Generando preview";
    render();
    clearTimers();
    setTimer(() => {
      state.previewStatus = selectedImage()?.status === "warning" ? "warning" : "ready";
      state.statusText = "Preview lista";
      render();
    }, 420);
  } else {
    render();
  }
}

function startExport(options = {}) {
  clearTimers();
  if (!isExportReady()) {
    state.exportStatus = "blocked";
    state.statusText = validationIssues()[0]?.title || "Configura exportación";
    render();
    return;
  }

  if (isBridgeBatch()) {
    void startBridgeExport();
    return;
  }

  if (!devMode) {
    Object.assign(state, {
      exportStatus: "blocked",
      errors: [{
        level: "error",
        title: "Lote real requerido",
        detail: "Selecciona una carpeta local antes de exportar.",
      }],
      statusText: "Selecciona una carpeta local",
    });
    render();
    return;
  }

  Object.assign(state, {
    scenario: options.keepScenario ? "export-running" : state.scenario,
    exportStatus: "running",
    progress: 0,
    processed: 0,
    exportJobId: null,
    exportDestinations: [],
    exportMessages: [],
    exportCompletedItems: [],
    exportIssues: [],
    exportResult: null,
    errors: [],
    paused: false,
    statusText: "Preparando exportación",
  });
  render();
  scheduleExportStep();
}

async function startBridgeExport() {
  clearBridgeExportPoll();
  Object.assign(state, {
    exportStatus: "running",
    progress: 0,
    processed: 0,
    exportJobId: null,
    exportDestinations: [],
    exportMessages: [],
    exportCompletedItems: [],
    exportIssues: [],
    exportResult: null,
    errors: [],
    paused: false,
    statusText: "Preparando exportación",
  });
  render();

  try {
    const response = await bridgeRequest("/exports/run", {
      method: "POST",
      body: JSON.stringify(bridgeExportPayload()),
      timeoutMs: 10000,
    });
    applyBridgeExportStatus(response);
    render();
    scheduleBridgeExportPoll();
  } catch (error) {
    const message = bridgeErrorMessage(error);
    Object.assign(state, {
      exportStatus: "failed",
      progress: 0,
      processed: 0,
      exportIssues: [{ level: "error", title: "Exportación fallida", detail: message }],
      exportResult: null,
      errors: [{ level: "error", title: "Exportación fallida", detail: message }],
      statusText: "Exportación fallida",
    });
    render();
  }
}

function bridgeExportPayload() {
  return {
    imagePaths: exportableImages()
      .filter((image) => image.source === "bridge" && image.path)
      .map((image) => image.path),
    presetName: state.activePreset,
    settings: bridgePreviewSettings(),
    export: {
      format: state.format,
      size: state.size,
      background: state.background,
      destinationMode: state.destinationMode,
      destinationValue: state.destinationValue,
      outputFolderName: state.destinationMode === "source" ? state.destinationValue : "_SALIDA_PRO",
      customOutputPath: state.destinationMode === "custom" ? state.destinationValue : "",
      namingTemplate: state.naming,
      suffix: "_PRO",
    },
  };
}

function scheduleBridgeExportPoll() {
  clearBridgeExportPoll();
  if (!state.exportJobId || !["running", "paused", "cancelling"].includes(state.exportStatus)) {
    return;
  }
  state.exportPollTimer = window.setTimeout(async () => {
    state.exportPollTimer = null;
    try {
      const response = await bridgeRequest(`/exports/jobs/${encodeURIComponent(state.exportJobId)}`, {
        timeoutMs: 5000,
      });
      applyBridgeExportStatus(response);
      render();
      scheduleBridgeExportPoll();
    } catch (error) {
      const message = bridgeErrorMessage(error);
      Object.assign(state, {
        exportStatus: "failed",
        paused: false,
        errors: [{ level: "error", title: "Progreso no disponible", detail: message }],
        statusText: "Progreso no disponible",
      });
      render();
    }
  }, 450);
}

function clearBridgeExportPoll() {
  if (state.exportPollTimer) {
    window.clearTimeout(state.exportPollTimer);
    state.exportPollTimer = null;
  }
}

function applyBridgeExportStatus(payload) {
  state.exportJobId = payload.jobId || state.exportJobId;
  state.exportDestinations = Array.isArray(payload.destinations) ? payload.destinations : state.exportDestinations;
  state.exportMessages = Array.isArray(payload.messages) ? payload.messages : state.exportMessages;
  state.exportCompletedItems = Array.isArray(payload.completedItems) ? payload.completedItems : state.exportCompletedItems;
  state.exportIssues = Array.isArray(payload.issues) ? payload.issues.map(normalizeBridgeIssue) : state.exportIssues;
  state.exportResult = payload.result || state.exportResult;
  state.progress = Number(payload.progress?.percent) || 0;
  state.processed = Number(payload.progress?.processed) || 0;
  state.paused = payload.status === "paused";

  if (payload.status === "completed") {
    state.exportStatus = "completed";
    state.progress = 0;
    state.statusText = `Exportación completada · ${state.processed}/${payload.progress?.total || state.processed}`;
  } else if (payload.status === "partial") {
    state.exportStatus = "partial";
    state.progress = 0;
    state.statusText = "Exportación con avisos";
  } else if (payload.status === "failed" || payload.status === "cancelled") {
    state.exportStatus = "failed";
    state.progress = 0;
    state.paused = false;
    state.statusText = payload.status === "cancelled" ? "Exportación cancelada" : "Exportación fallida";
  } else if (payload.status === "paused") {
    state.exportStatus = "running";
    state.statusText = "Pausado";
  } else if (payload.status === "cancelling") {
    state.exportStatus = "running";
    state.statusText = "Deteniendo...";
  } else {
    state.exportStatus = "running";
    state.statusText = `Procesando ${state.processed}/${payload.progress?.total || "..."}`;
  }

  const failedItems = state.exportCompletedItems.filter((item) => !item.success);
  if (["partial", "failed", "cancelled"].includes(payload.status) || failedItems.length || state.exportIssues.length) {
    const messageItems = (payload.messages || []).slice(-4).map((message) => ({
      level: payload.status === "partial" ? "warning" : "error",
      title: "Exportación",
      detail: message,
    }));
    const itemErrors = failedItems.slice(-4).map((item) => ({
      level: "error",
      title: item.name || "Imagen",
      detail: "No se pudo exportar.",
    }));
    state.errors = state.exportIssues.length ? state.exportIssues : [...itemErrors, ...messageItems];
  } else {
    state.errors = [];
  }
}

function normalizeBridgeIssue(issue) {
  const source = issue && typeof issue === "object" ? issue : {};
  return {
    level: source.level === "error" ? "error" : "warning",
    title: String(source.title || "Exportación"),
    detail: String(source.detail || "Revisa el resultado."),
  };
}

function scheduleExportStep() {
  setTimer(() => {
    if (state.exportStatus !== "running") {
      return;
    }
    if (state.paused) {
      scheduleExportStep();
      return;
    }
    const total = exportableImages().length;
    state.progress = Math.min(100, state.progress + 9);
    state.processed = Math.min(total, Math.max(1, Math.round((state.progress / 100) * total)));
    state.statusText = `Procesando ${state.processed}/${total}`;

    if (state.progress >= 100) {
      state.exportStatus = "completed";
      state.progress = 0;
      state.processed = total;
      state.exportCompletedItems = exportableImages().map((image) => ({ name: image.name, success: true }));
      state.exportDestinations = ["Mock / _SALIDA_PRO"];
      state.exportIssues = [];
      state.exportResult = {
        success: true,
        processed: total,
        total,
        errors: 0,
        destinations: ["Mock / _SALIDA_PRO"],
      };
      state.statusText = "Exportación completada";
      render();
      return;
    }

    render();
    scheduleExportStep();
  }, 220);
}

function pauseExport() {
  if (state.exportStatus !== "running") {
    return;
  }
  if (isBridgeBatch() && state.exportJobId) {
    void controlBridgeExport(state.paused ? "resume" : "pause");
    return;
  }
  state.paused = !state.paused;
  state.statusText = state.paused ? "Pausado" : `Procesando ${state.processed}/${exportableImages().length}`;
  render();
}

function stopExport() {
  if (state.exportStatus !== "running") {
    return;
  }
  if (isBridgeBatch() && state.exportJobId) {
    void controlBridgeExport("cancel");
    return;
  }
  clearTimers();
  clearBridgeExportPoll();
  Object.assign(state, {
    exportStatus: "failed",
    paused: false,
    errors: [{ level: "error", title: "Exportación detenida", detail: "No se generaron más archivos." }],
    statusText: "Exportación fallida",
  });
  render();
}

async function controlBridgeExport(action) {
  if (!state.exportJobId) {
    return;
  }
  try {
    const response = await bridgeRequest(`/exports/jobs/${encodeURIComponent(state.exportJobId)}/${action}`, {
      method: "POST",
      body: JSON.stringify({}),
      timeoutMs: 5000,
    });
    applyBridgeExportStatus(response);
  } catch (error) {
    const message = bridgeErrorMessage(error);
    state.errors = [{ level: "error", title: "Control no disponible", detail: message }];
    state.statusText = "Control no disponible";
  }
  render();
  scheduleBridgeExportPoll();
}

function reviewErrors() {
  if (!hasBatch()) {
    return;
  }
  state.filter = "errors";
  state.statusText = state.errors.length ? "Revisa errores de exportación" : "Mostrando errores";
  render();
}

function clearFilter() {
  state.filter = "all";
  state.search = "";
  state.statusText = "Mostrando todo";
  render();
}

function normalizedBridgeUrl() {
  return (state.bridgeUrl || defaultBridgeUrl).trim().replace(/\/+$/, "");
}

async function bridgeRequest(path, options = {}) {
  const controller = new AbortController();
  const timeoutMs = options.timeoutMs || 3500;
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);
  const headers = options.body
    ? { "Content-Type": "application/json", ...(options.headers || {}) }
    : { ...(options.headers || {}) };
  const { timeoutMs: _timeoutMs, ...fetchOptions } = options;

  try {
    const response = await fetch(`${normalizedBridgeUrl()}${path}`, {
      ...fetchOptions,
      headers,
      signal: controller.signal,
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.error?.message || `HTTP ${response.status}`);
    }
    return payload;
  } finally {
    window.clearTimeout(timer);
  }
}

async function requestBridgePreview(image) {
  const requestId = state.previewRequestId + 1;
  state.previewRequestId = requestId;
  state.previewStatus = "loading";
  state.previewData = null;
  state.previewError = "";
  state.statusText = "Generando preview";
  render();

  try {
    const response = await bridgeRequest("/preview/render", {
      method: "POST",
      body: JSON.stringify({
        imagePath: image.path,
        ...previewTargetSize(),
        settings: bridgePreviewSettings(),
      }),
      timeoutMs: 20000,
    });

    if (isStalePreviewResponse(requestId, image)) {
      return;
    }

    state.previewData = previewResponseToData(response);
    state.previewStatus = response.warning ? "warning" : "ready";
    state.statusText = response.warning ? "Preview con aviso" : "Preview lista";
  } catch (error) {
    if (isStalePreviewResponse(requestId, image)) {
      return;
    }
    const message = bridgeErrorMessage(error);
    state.previewStatus = "error";
    state.previewData = null;
    state.previewError = message;
    state.statusText = "Preview no disponible";
  }

  render();
}

function isStalePreviewResponse(requestId, image) {
  return requestId !== state.previewRequestId || state.selectedImageId !== image.id;
}

function previewResponseToData(response) {
  return {
    src: `data:${response.image.mimeType};base64,${response.image.dataBase64}`,
    width: response.image.width,
    height: response.image.height,
    sourceName: response.source?.name || selectedImage()?.name || "imagen.png",
    sourcePath: response.source?.path || selectedImage()?.path || "",
    warning: response.warning || "",
    renderTimeMs: Number(response.renderTimeMs) || 0,
  };
}

function bridgePreviewSettings() {
  return {
    ...normalizeSettings(state.settings),
    presetName: state.activePreset,
    transparentBg: state.background === "transparent",
    bgColor: backgroundColorTuple(state.background),
  };
}

function previewTargetSize() {
  const match = /^(\d+)x(\d+)$/.exec(state.size);
  if (!match) {
    return { targetWidth: 900, targetHeight: 900 };
  }
  const width = Number(match[1]);
  const height = Number(match[2]);
  const scale = Math.min(900 / Math.max(width, height), 1);
  return {
    targetWidth: Math.max(1, Math.round(width * scale)),
    targetHeight: Math.max(1, Math.round(height * scale)),
  };
}

function backgroundColorTuple(value) {
  if (value === "white") {
    return [255, 255, 255];
  }
  return [230, 230, 230];
}

async function checkBridge() {
  state.bridgeMode = "bridge";
  state.bridgeStatus = "checking";
  state.bridgeMessage = "Comprobando bridge";
  state.bridgeLastResponse = "Solicitando /health";
  state.statusText = "Comprobando bridge";
  render();

  try {
    const health = await bridgeRequest("/health");
    const capabilities = await bridgeRequest("/capabilities");
    const presetPayload = await bridgeRequest("/presets");
    state.bridgeStatus = "connected";
    state.bridgeCapabilities = capabilities;
    state.bridgeCapabilitiesSummary = capabilitiesSummary(capabilities);
    state.bridgeMessage = `${health.service} conectado`;
    state.bridgeLastResponse = "health OK";
    state.scanStatus = "Bridge conectado";
    if (state.batch === "none") {
      state.scanIssues = [];
    }
    state.statusText = "Bridge conectado";
    applyBridgePresets(presetPayload);
  } catch (error) {
    const message = bridgeErrorMessage(error);
    state.bridgeStatus = "disconnected";
    state.bridgeCapabilities = null;
    state.bridgeCapabilitiesSummary = "Sin comprobar";
    state.bridgeMessage = message;
    state.bridgeLastResponse = `error: ${message}`;
    state.scanStatus = "Bridge desconectado";
    state.statusText = "Bridge sin conexión";
  }

  render();
}

async function pickBridgeFolder() {
  state.bridgeMode = "bridge";
  state.bridgeStatus = "checking";
  state.bridgeMessage = "Abriendo selector";
  state.bridgeLastResponse = "Solicitando /folders/pick";
  state.scanStatus = "Selecciona una carpeta";
  state.statusText = "Selecciona una carpeta";
  render();

  try {
    const selected = await bridgeRequest("/folders/pick", {
      method: "POST",
      body: JSON.stringify({ initialPath: parseFolderInput(state.bridgeScanPath)[0] || "" }),
      timeoutMs: 300000,
    });
    state.bridgeStatus = "connected";
    if (!selected.selected || !selected.path) {
      state.bridgeMessage = "Selección cancelada";
      state.bridgeLastResponse = "folder pick cancelado";
      state.scanStatus = "Selección cancelada";
      state.statusText = "Selección cancelada";
      render();
      return;
    }

    state.bridgeScanPath = selected.path;
    state.bridgeMessage = "Carpeta seleccionada";
    state.bridgeLastResponse = "folder pick OK";
    state.scanStatus = "Carpeta seleccionada";
    state.statusText = "Carpeta seleccionada";
    render();
    await scanBridgeFolder();
  } catch (error) {
    const message = bridgeErrorMessage(error);
    state.bridgeStatus = "disconnected";
    state.bridgeMessage = message;
    state.bridgeLastResponse = `error: ${message}`;
    state.scanStatus = "No se pudo seleccionar";
    state.scanIssues = [{ level: "error", title: "Selector no disponible", detail: message }];
    state.statusText = "Selector no disponible";
    render();
  }
}

function applyBridgePresets(payload) {
  const items = Array.isArray(payload.items)
    ? payload.items.map(normalizePresetItem).filter(Boolean)
    : [];
  state.bridgePresets = items;
  state.bridgePresetSource = payload.source || "unavailable";
  state.bridgePresetWarning = payload.warning || "";
  if (!items.length) {
    state.presetSource = "Bridge local · sin presets";
    return;
  }

  const names = items.map((item) => item.name);
  if (state.bridgeMode === "bridge") {
    if (!names.includes(state.activePreset)) {
      state.activePreset = names[0];
    }
    applyPresetSettings(state.activePreset, { refresh: false, statusText: state.statusText });
  }
}

function normalizePresetItem(item) {
  if (!item || typeof item !== "object" || !item.name) {
    return null;
  }
  return {
    name: String(item.name),
    categoryId: String(item.categoryId || "uncategorized"),
    category: String(item.category || "Sin categoría"),
    settings: normalizeSettings(item.settings),
    source: "bridge",
  };
}

async function scanBridgeFolder() {
  state.bridgeMode = "bridge";
  const folders = parseFolderInput(state.bridgeScanPath);
  if (!folders.length) {
    state.bridgeStatus = state.bridgeStatus === "connected" ? "connected" : "disconnected";
    state.bridgeMessage = "Ruta vacía";
    state.scanStatus = "Ruta vacía";
    state.scanIssues = [{ level: "warning", title: "Ruta vacía", detail: "Pega una carpeta para escanear." }];
    state.statusText = "Ruta vacía";
    render();
    return;
  }

  clearTimers();
  clearBridgeExportPoll();
  Object.assign(state, {
    batch: "scanning",
    batchSource: "bridge",
    selectedImageId: null,
    previewStatus: "empty",
    previewData: null,
    previewError: "",
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
    scanIssues: [],
    scanDiagnostics: emptyScanDiagnostics(),
    scanStatus: folders.length === 1 ? "Escaneando ruta" : `Escaneando ${folders.length} rutas`,
    statusText: "Escaneando ruta",
  });
  state.bridgeLastResponse = "Solicitando /folders/scan";
  render();

  try {
    if (!state.bridgePresets.length) {
      const presetPayload = await bridgeRequest("/presets");
      applyBridgePresets(presetPayload);
    }
    const response = await bridgeRequest("/folders/scan", {
      method: "POST",
      body: JSON.stringify({ folders }),
    });
    applyBridgeScanResult(response);
  } catch (error) {
    const message = bridgeErrorMessage(error);
    Object.assign(state, {
      batch: "none",
      batchSource: "none",
      selectedImageId: null,
      previewStatus: "empty",
      previewData: null,
      previewError: "",
      exportStatus: "blocked",
      scanDiagnostics: emptyScanDiagnostics(),
      bridgeStatus: "disconnected",
      bridgeMessage: message,
      bridgeLastResponse: `error: ${message}`,
      scanStatus: "Bridge desconectado",
      scanIssues: [{ level: "error", title: "Bridge desconectado", detail: message }],
      statusText: "No se pudo escanear",
    });
  }

  render();
}

function applyBridgeScanResult(response) {
  state.scanDiagnostics = scanDiagnosticsFromResponse(response);
  state.realFolders = (response.folders || []).map(bridgeFolderToItem);
  state.realImages = (response.folders || []).flatMap((folder, folderIndex) =>
    (folder.images || []).map((image, imageIndex) => bridgeImageToItem(image, folderIndex, imageIndex))
  );
  const folderWarnings = state.realFolders.filter((folder) => folder.status === "warning" || folder.status === "error").length;
  const responseErrors = Array.isArray(response.errors) ? response.errors : [];
  state.bridgeStatus = "connected";
  state.batchSource = "bridge";
  state.bridgeMessage = bridgeScanMessage(response.totalImages || 0, folderWarnings + responseErrors.length);
  state.bridgeLastResponse = `scan OK · ${response.totalImages || 0} imágenes`;
  state.scanIssues = [
    ...state.realFolders
      .filter((folder) => folder.status === "warning" || folder.status === "error")
      .map((folder) => ({
        level: folder.status === "error" ? "error" : "warning",
        title: folder.name,
        detail: folder.detail,
      })),
    ...responseErrors.map((detail) => ({ level: "error", title: "Escaneo", detail })),
  ];
  if (state.scanDiagnostics.totalOmitted > 0) {
    state.scanIssues.push({
      level: "warning",
      title: "Archivos omitidos",
      detail: omittedSummaryText(state.scanDiagnostics),
    });
  }

  if (state.realImages.length) {
    state.batch = "ready";
    state.selectedImageId = state.realImages[0].id;
    state.previewStatus = "loading";
    state.previewData = null;
    state.previewError = "";
    state.exportStatus = "blocked";
    state.scanStatus = state.scanIssues.length
      ? `Escaneo completado con ${state.scanIssues.length} aviso${state.scanIssues.length === 1 ? "" : "s"}`
      : `${state.realImages.length} imágenes encontradas`;
    state.statusText = "Generando preview";
    void requestBridgePreview(state.realImages[0]);
    return;
  }

  state.batch = "empty";
  state.selectedImageId = null;
  state.previewStatus = "empty";
  state.previewData = null;
  state.previewError = "";
  state.exportStatus = "blocked";
  state.scanStatus = state.scanIssues.length ? state.scanIssues[0].detail : "No se encontraron PNG";
  state.statusText = state.scanIssues.length ? "Revisa carpeta" : "No hay PNG válidos";
}

function parseFolderInput(value) {
  return String(value || "")
    .split(/[;\n\r]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function bridgeScanMessage(totalImages, warningCount) {
  if (warningCount) {
    return `Escaneo completado con ${warningCount} aviso${warningCount === 1 ? "" : "s"}`;
  }
  if (totalImages === 0) {
    return "No se encontraron PNG";
  }
  return `${totalImages} imágenes encontradas`;
}

function omittedSummaryText(diagnostics = state.scanDiagnostics) {
  if (!diagnostics.totalOmitted) {
    return "Sin omisiones";
  }
  return Object.entries(diagnostics.omittedByReason || {})
    .map(([reason, count]) => `${count} ${omissionReasonLabel(reason).toLowerCase()}`)
    .join(" · ") || `${diagnostics.totalOmitted} omitidas`;
}

function omissionReasonLabel(reason) {
  if (reason === "unsupported_extension") {
    return "Extensión no admitida";
  }
  if (reason === "read_error") {
    return "Error de lectura";
  }
  if (reason === "subfolder_not_scanned") {
    return "Subcarpeta no escaneada";
  }
  return "Omitida";
}

function bridgeFolderToItem(folder, index) {
  const hasErrors = Array.isArray(folder.errors) && folder.errors.length > 0;
  const count = Array.isArray(folder.images) ? folder.images.length : 0;
  const omittedCount = Number(folder.omittedCount) || 0;
  const exists = folder.exists !== false;
  const isDir = folder.isDir !== false;
  const status = hasErrors
    ? count ? "warning" : "error"
    : omittedCount ? "warning" : count ? "ready" : exists && isDir ? "empty" : "error";
  return {
    id: `bridge-folder-${index}`,
    name: basename(folder.path) || `Carpeta ${index + 1}`,
    path: folder.path,
    count,
    source: "bridge",
    exists,
    isDir,
    status,
    detail: hasErrors
      ? folder.errors[0]
      : omittedCount
        ? `${count} PNG · ${omittedCount} omitidas`
        : count ? `${count} PNG` : "No se encontraron PNG",
    filesFound: Number(folder.filesFound) || count,
    omittedCount,
  };
}

function bridgeImageToItem(image, folderIndex, imageIndex) {
  return {
    id: `bridge-${folderIndex}-${imageIndex}`,
    folderId: `bridge-folder-${folderIndex}`,
    name: image.name,
    detail: `${formatBytes(image.sizeBytes)} · Bridge local`,
    status: image.hasLocalOverride ? "adjusted" : "ready",
    tone: `tone-${["a", "b", "c", "d", "e"][imageIndex % 5]}`,
    exportable: true,
    source: "bridge",
    path: image.path,
  };
}

function basename(path) {
  return String(path || "").split(/[\\/]/).filter(Boolean).pop() || "";
}

function formatBytes(bytes) {
  const value = Number(bytes) || 0;
  if (value >= 1024 * 1024) {
    return `${(value / (1024 * 1024)).toFixed(1)} MB`;
  }
  if (value >= 1024) {
    return `${Math.round(value / 1024)} KB`;
  }
  return `${value} B`;
}

function bridgeErrorMessage(error) {
  if (error?.name === "AbortError") {
    return "Bridge no responde";
  }
  return error?.message || "Bridge no disponible";
}

function capabilitiesSummary(capabilities) {
  if (!capabilities) {
    return "Sin comprobar";
  }
  const available = [];
  if (capabilities.folderScan) {
    available.push("scan");
  }
  if (capabilities.presetsRead) {
    available.push("presets");
  }
  if (capabilities.previewRender) {
    available.push("preview");
  }
  if (capabilities.exportRun) {
    available.push("export");
  }
  return available.length ? available.join(" · ") : "Sin capacidades activas";
}

function showReviewScenario(scenario) {
  if (!devMode) {
    return;
  }
  state.bridgeMode = "mock";
  state.bridgeLastResponse = `Estado mock: ${scenarioLabels[scenario] || scenario}`;
  setScenario(scenario);
}

function primaryAction() {
  if (!hasBatch()) {
    void pickBridgeFolder();
    return;
  }
  if (state.exportStatus === "completed" || state.exportStatus === "partial") {
    clearBatch();
    return;
  }
  startExport();
}

function statusMode() {
  if (state.exportStatus === "failed" || state.previewStatus === "error" || state.scanIssues.some((issue) => issue.level === "error")) {
    return "error";
  }
  if (state.exportStatus === "running" || state.previewStatus === "loading" || state.batch === "scanning") {
    return "busy";
  }
  if (state.exportStatus === "partial" || state.previewStatus === "warning" || validationIssues().length) {
    return "busy";
  }
  return "ready";
}

function render() {
  renderShell();
  renderTop();
  renderDevelopmentStatus();
  renderBridge();
  renderBatch();
  renderPreview();
  renderSettings();
  renderExport();
  renderInspector();
  renderFooter();
}

function renderShell() {
  const shell = $(".app-shell");
  shell.classList.toggle("dev-mode", devMode);
  shell.classList.toggle("has-batch", hasBatch() || state.batch === "empty");
  shell.classList.toggle("is-scanning", state.batch === "scanning");
  shell.classList.toggle("inspector-collapsed", state.inspectorCollapsed);
}

function renderDevelopmentStatus() {
  $("#dev-mode-label").textContent = state.bridgeMode === "bridge" ? "Bridge local" : "Mock";
  $("#dev-bridge-label").textContent = bridgeStatusLabel();
  $("#dev-bridge-url-label").textContent = state.bridgeUrl || defaultBridgeUrl;
  $("#dev-last-response").textContent = state.bridgeLastResponse;
}

function renderTop() {
  $("#demo-scenario").value = scenarioLabels[state.scenario] ? state.scenario : "batch-ready";
  $("#app-mode").value = state.bridgeMode;
  $("#bridge-url").value = state.bridgeUrl;
  $("#active-batch-label").textContent = hasBatch()
    ? `${activeImages().length} imágenes${state.scanDiagnostics.totalOmitted ? ` · ${state.scanDiagnostics.totalOmitted} omitidas` : ""}`
    : state.batch === "empty"
      ? "Carpeta sin PNG"
      : "Sin lote";
  $("#top-status-text").textContent = topStatusText();
  $("#status-dot").className = `status-dot ${statusMode()}`;
  const preflight = $("#top-preflight-status");
  if (preflight) {
    preflight.textContent = preflightStatusLabel();
    preflight.className = `preflight-chip ${preflightStatusClass()}`;
  }
}

function topStatusText() {
  const image = selectedImage();
  if (state.batch === "scanning") {
    return "Escaneando carpeta";
  }
  if (!hasBatch()) {
    return state.batch === "empty" ? "No hay PNG válidos" : "Añade una carpeta";
  }
  if (state.exportStatus === "running") {
    const total = exportableImages().length;
    return state.paused ? "Pausado" : `Procesando ${state.processed}/${total}`;
  }
  if (state.previewStatus === "loading") {
    return "Generando preview";
  }
  if (state.previewStatus === "error") {
    return "Preview no disponible";
  }
  if (state.previewStatus === "warning") {
    return "Preview con aviso";
  }
  if (image?.source === "bridge" && state.previewStatus === "ready") {
    return "Preview real";
  }
  if (image && state.previewStatus === "ready") {
    return devMode ? "Preview simulada" : "Preview lista";
  }
  if (state.bridgeMode === "bridge" && state.bridgeStatus === "disconnected") {
    return "Revisa el bridge";
  }
  return state.statusText;
}

function preflightStatusLabel() {
  if (state.exportStatus === "running") {
    return state.paused ? "Pausado" : "Procesando";
  }
  if (state.exportStatus === "completed") {
    return "Completada";
  }
  if (state.exportStatus === "partial") {
    return "Con avisos";
  }
  if (state.exportStatus === "failed") {
    return "Bloqueado";
  }
  const ready = isExportReady();
  const counts = preflightCounts();
  if (!ready && counts.errors > 0) {
    return "Bloqueado";
  }
  if (!ready) {
    return "Bloqueado";
  }
  if (counts.warnings > 0) {
    return `${counts.warnings} aviso${counts.warnings === 1 ? "" : "s"}`;
  }
  return "Preflight listo";
}

function preflightStatusClass() {
  if (state.exportStatus === "failed") {
    return "error";
  }
  if (state.exportStatus === "running" || state.exportStatus === "partial") {
    return "warning";
  }
  const ready = isExportReady();
  const counts = preflightCounts();
  if (!ready || counts.errors > 0) {
    return "error";
  }
  if (counts.warnings > 0) {
    return "warning";
  }
  return "ready";
}

function renderBridge() {
  const chip = $("#bridge-status");
  const sourcePanel = $("#source-panel");
  const sourceBadge = $("#scan-source-badge");
  const message = $("#bridge-message");

  chip.className = `bridge-chip ${bridgeStatusClass()}`;
  chip.textContent = bridgeStatusLabel();
  sourcePanel.className = `source-panel ${sourcePanelClass()}`;
  sourceBadge.className = `state-chip ${isBridgeBatch() ? "bridge" : isMockBatch() ? "ready" : ""}`;
  sourceBadge.textContent = sourceLabel();
  $("#source-title").textContent = hasBatch() || state.batch === "empty" ? "Cambiar carpeta" : "Selecciona una carpeta";
  $("#scan-status").textContent = state.scanStatus;
  $("#bridge-scan-path").value = state.bridgeScanPath;
  $("#bridge-pick-folder").disabled = state.bridgeStatus === "checking" || state.batch === "scanning";
  $("#bridge-scan-folder").disabled = state.bridgeStatus === "checking" || state.batch === "scanning";
  $("#bridge-last-response").textContent = state.bridgeLastResponse;
  $("#bridge-capabilities").textContent = state.bridgeCapabilitiesSummary;
  message.textContent = normalBridgeMessage();
  message.className = `bridge-message ${state.bridgeStatus === "connected" ? "ready" : state.bridgeStatus === "disconnected" ? "error" : ""}`;
  renderBatchSummary();
}

function normalBridgeMessage() {
  if (state.bridgeMode !== "bridge") {
    return devMode ? "Modo revisión con datos simulados." : "Selecciona una carpeta local.";
  }
  if (state.bridgeStatus === "connected") {
    return "Bridge conectado.";
  }
  if (state.bridgeStatus === "checking") {
    return "Comprobando bridge.";
  }
  if (state.bridgeStatus === "disconnected") {
    return "Bridge desconectado. Reintenta.";
  }
  return "Selecciona una carpeta local.";
}

function sourcePanelClass() {
  if (state.batch === "scanning") {
    return "scanning";
  }
  if (state.scanIssues.some((issue) => issue.level === "error")) {
    return "error";
  }
  if (isBridgeBatch() || state.bridgeMode === "bridge") {
    return "bridge";
  }
  return "";
}

function sourceLabel() {
  if (isBridgeBatch()) {
    return "Carpeta local";
  }
  if (isMockBatch()) {
    return devMode ? "Mock" : "Carpeta local";
  }
  return state.bridgeMode === "bridge" || !devMode ? "Carpeta local" : "Mock";
}

function emptyScanDiagnostics() {
  return {
    totalFiles: 0,
    totalImages: 0,
    totalOmitted: 0,
    omittedByReason: {},
    omitted: [],
  };
}

function mockScanDiagnostics() {
  return {
    totalFiles: mockImages.length,
    totalImages: mockImages.length,
    totalOmitted: 0,
    omittedByReason: {},
    omitted: [],
  };
}

function scanDiagnosticsFromResponse(response) {
  const omitted = (response.folders || []).flatMap((folder) =>
    (folder.omitted || []).map((item) => ({
      ...item,
      folder: folder.path,
    }))
  );
  return {
    totalFiles: Number(response.totalFiles) || Number(response.totalImages) || 0,
    totalImages: Number(response.totalImages) || 0,
    totalOmitted: Number(response.totalOmitted) || omitted.length,
    omittedByReason: response.omittedByReason || {},
    omitted,
  };
}

function renderBatchSummary() {
  const summary = $("#batch-summary");
  const images = activeImages();
  const folders = state.batch === "ready"
    ? activeFolders()
    : state.batch === "empty" && isBridgeBatch()
      ? state.realFolders
      : state.batch === "empty" && isMockBatch()
        ? [{ status: "empty" }]
        : [];
  const issueCount = state.scanIssues.length + images.filter((image) => image.status === "warning" || image.status === "error").length;
  const note = batchSummaryNote(images.length, folders.length, issueCount);
  const diagnostics = state.scanDiagnostics || emptyScanDiagnostics();
  const filesLabel = state.batch === "scanning" ? "..." : diagnostics.totalFiles;
  const omittedLabel = state.batch === "scanning" ? "..." : diagnostics.totalOmitted;

  summary.innerHTML = `
    <div class="summary-grid">
      <div class="summary-metric">
        <span>Archivos</span>
        <strong>${escapeHtml(filesLabel)}</strong>
      </div>
      <div class="summary-metric">
        <span>Válidas</span>
        <strong>${state.batch === "scanning" ? "..." : images.length}</strong>
      </div>
      <div class="summary-metric">
        <span>Omitidas</span>
        <strong>${escapeHtml(omittedLabel)}</strong>
      </div>
    </div>
    <div class="summary-note" title="${escapeHtml(note)}">${escapeHtml(note)}</div>
    ${diagnostics.totalOmitted ? diagnosticsHtml(diagnostics) : ""}
  `;
}

function diagnosticsHtml(diagnostics) {
  const reasonRows = Object.entries(diagnostics.omittedByReason || {}).map(([reason, count]) => `
    <div class="diagnostic-row">
      <span>${escapeHtml(omissionReasonLabel(reason))}</span>
      <strong>${escapeHtml(count)}</strong>
    </div>
  `).join("");
  const sampleRows = (diagnostics.omitted || []).slice(0, 5).map((item) => `
    <li title="${escapeHtml(item.path || item.name)}">
      <span>${escapeHtml(item.name)}</span>
      <small>${escapeHtml(item.detail || omissionReasonLabel(item.reason))}</small>
    </li>
  `).join("");
  return `
    <details class="batch-diagnostics">
      <summary>Ver diagnóstico</summary>
      <div class="diagnostic-reasons">${reasonRows}</div>
      ${sampleRows ? `<ul>${sampleRows}</ul>` : ""}
    </details>
  `;
}

function batchSummaryNote(imageCount, folderCount, issueCount) {
  if (state.batch === "scanning") {
    return isBridgeBatch() || !devMode ? "Leyendo PNG reales desde bridge." : "Leyendo lote mock.";
  }
  if (isBridgeBatch()) {
    if (state.batch === "empty") {
      return state.scanDiagnostics.totalOmitted
        ? `0 imágenes válidas · ${state.scanDiagnostics.totalOmitted} omitida${state.scanDiagnostics.totalOmitted === 1 ? "" : "s"}`
        : state.scanIssues[0]?.detail || "Carpeta real sin PNG válidos.";
    }
    if (state.scanDiagnostics.totalOmitted) {
      return `${imageCount} imágenes válidas · ${state.scanDiagnostics.totalOmitted} omitida${state.scanDiagnostics.totalOmitted === 1 ? "" : "s"}`;
    }
    return issueCount
      ? `${imageCount} imágenes reales · ${issueCount} aviso${issueCount === 1 ? "" : "s"}`
      : `${imageCount} imágenes reales desde ${folderCount} carpeta${folderCount === 1 ? "" : "s"}`;
  }
  if (isMockBatch()) {
    return devMode
      ? (state.batch === "empty" ? "Escenario mock: carpeta vacía." : "Escenario mock para revisión visual.")
      : "Selecciona una carpeta local.";
  }
  return "Sin lote cargado.";
}

function bridgeStatusClass() {
  if (state.bridgeMode !== "bridge" && devMode) {
    return "idle";
  }
  return state.bridgeStatus;
}

function bridgeStatusLabel() {
  if (state.bridgeMode !== "bridge" && devMode) {
    return "Mock";
  }
  if (state.bridgeStatus === "connected") {
    return "Bridge conectado";
  }
  if (state.bridgeStatus === "checking") {
    return "Comprobando bridge";
  }
  if (state.bridgeStatus === "disconnected") {
    return "Bridge desconectado";
  }
  return "Bridge pendiente";
}

function renderBatch() {
  const images = activeImages();
  const adjusted = images.filter((image) => image.status === "adjusted").length;
  const valid = images.filter((image) => image.status === "ready" || image.status === "adjusted").length;
  const warnings = images.filter((image) => image.status === "warning").length;
  const errors = images.filter((image) => image.status === "error" || exportItemState(image)?.status === "error").length;

  if (state.batch === "none") {
    $("#batch-count").textContent = "0 imágenes";
    $("#batch-pill").textContent = "Sin carpeta";
    $("#folder-list").innerHTML = "";
    $("#image-list").innerHTML = "";
    $("#batch-empty-note").textContent = state.scanIssues[0]?.detail || "Selecciona una carpeta para empezar.";
    $("#image-search").value = state.search;
    renderFilterButtons();
    return;
  }

  if (state.batch === "scanning") {
    $("#batch-count").textContent = "Escaneando";
    $("#batch-pill").textContent = isBridgeBatch() || !devMode ? "Carpeta local" : "Carpeta mock";
    $("#folder-list").innerHTML = folderItemHtml({
      id: "scan",
      name: isBridgeBatch() || !devMode ? basename(parseFolderInput(state.bridgeScanPath)[0]) || "Ruta bridge" : "Camisetas Mayo",
      path: state.bridgeScanPath,
      detail: isBridgeBatch() || !devMode ? "Leyendo PNG reales" : "Leyendo PNG",
      count: "...",
      status: "ready",
    });
    $("#image-list").innerHTML = "";
    $("#batch-empty-note").textContent = "Escaneando carpeta";
    renderFilterButtons();
    return;
  }

  if (state.batch === "empty") {
    const emptyFolders = isBridgeBatch() && state.realFolders.length
      ? state.realFolders
      : [{
          id: "empty",
          name: "Carpeta vacía",
          detail: "No hay PNG válidos",
          count: "0",
          status: "empty",
        }];
    $("#batch-count").textContent = "0 PNG";
    $("#batch-pill").textContent = state.scanDiagnostics.totalOmitted
      ? `${state.scanDiagnostics.totalOmitted} omitida${state.scanDiagnostics.totalOmitted === 1 ? "" : "s"}`
      : isBridgeBatch() ? "Carpeta local" : "Sin imágenes";
    $("#folder-list").innerHTML = emptyFolders.map(folderItemHtml).join("");
    $("#image-list").innerHTML = "";
    $("#batch-empty-note").textContent = state.scanDiagnostics.totalOmitted
      ? `No hay PNG válidos. ${omittedSummaryText(state.scanDiagnostics)}.`
      : state.scanStatus || "No hay PNG válidos.";
    renderFilterButtons();
    return;
  }

  $("#batch-count").textContent = `${images.length} imágenes`;
  $("#batch-pill").textContent = isBridgeBatch()
    ? state.scanDiagnostics.totalOmitted ? `${state.scanDiagnostics.totalOmitted} omitida${state.scanDiagnostics.totalOmitted === 1 ? "" : "s"}` : "Carpeta local"
    : errors ? `${errors} error${errors === 1 ? "" : "es"}` : adjusted ? `${adjusted} ajustada${adjusted === 1 ? "" : "s"}` : warnings ? `${warnings} aviso${warnings === 1 ? "" : "s"}` : "Listas";
  $("#folder-list").innerHTML = activeFolders().map(folderItemHtml).join("");
  $("#image-search").value = state.search;
  renderFilterButtons();

  const visible = filteredImages();
  $("#image-list").innerHTML = visible.map(imageItemHtml).join("");
  $("#batch-empty-note").innerHTML = visible.length ? "" : filteredEmptyHtml(images.length, valid, warnings, errors);
}

function filteredEmptyHtml(total, valid, warnings, errors) {
  if (!total) {
    return "No hay imágenes en este lote.";
  }
  const labels = {
    valid: "válidas",
    warnings: "con avisos",
    errors: "con errores",
  };
  if (state.search.trim()) {
    const searchDetail = state.filter === "all"
      ? "La búsqueda no coincide con ninguna imagen."
      : "La búsqueda no coincide con el filtro actual.";
    return `
      <strong>No hay resultados.</strong>
      <span>${escapeHtml(searchDetail)}</span>
      <button type="button" data-action="clear-filter">Ver todas</button>
    `;
  }
  const counts = { valid, warnings, errors };
  const label = labels[state.filter] || "con este filtro";
  const count = counts[state.filter] || 0;
  return `
    <strong>No hay imágenes ${escapeHtml(label)}.</strong>
    <small>${escapeHtml(total)} imágenes en el lote · ${escapeHtml(count)} en este filtro</small>
    <button type="button" data-action="clear-filter">Ver todas</button>
  `;
}

function folderItemHtml(folder) {
  const className = folder.status === "warning" ? "empty" : folder.status === "error" ? "error" : folder.status || "";
  return `
    <div class="folder-item ${className}" title="${escapeHtml(folder.path || folder.detail)}">
      <div>
        <strong>${escapeHtml(folder.name)}</strong>
        <small>${escapeHtml(folder.detail)}</small>
      </div>
      <span class="state-chip ${folder.status === "warning" ? "warning" : folder.status === "error" ? "error" : ""}">
        ${escapeHtml(folder.count)}
      </span>
    </div>
  `;
}

function imageItemHtml(image) {
  const selected = image.id === state.selectedImageId ? "active" : "";
  const exportState = exportItemState(image);
  const effectiveStatus = exportState?.status || image.status;
  const chipClass = effectiveStatus === "warning" ? "warning" : effectiveStatus === "error" ? "error" : effectiveStatus === "exported" ? "exported" : "";
  const chipLabel = exportState?.label || statusLabels[image.status];
  const title = image.path || image.name;
  return `
    <button type="button" class="image-item ${selected} ${chipClass}" data-image-id="${escapeHtml(image.id)}" title="${escapeHtml(title)}">
      <span class="thumb ${escapeHtml(image.tone)}"></span>
      <span class="image-copy">
        <strong>${escapeHtml(image.name)}</strong>
        <small>${escapeHtml(image.detail)}</small>
      </span>
      <span class="state-chip ${chipClass}">${escapeHtml(chipLabel)}</span>
    </button>
  `;
}

function renderFilterButtons() {
  $$(".batch-filter button").forEach((button) => {
    button.classList.toggle("active", button.dataset.filter === state.filter);
  });
}

function renderPreview() {
  const image = selectedImage();
  const isBridgeImage = image?.source === "bridge";
  const previewControlsDisabled = !image || state.previewStatus === "empty" || state.previewStatus === "error";
  const compareControlsDisabled = !image || isBridgeImage || state.previewStatus === "empty" || state.previewStatus === "error";
  $("#preview-name").textContent = image ? image.name : "Sin imagen seleccionada";
  $("#preview-subtitle").textContent = previewSubtitle(image);
  $("#zoom-label").textContent = state.fitMode === "fit" ? "Fit" : `${state.zoom}%`;
  const visibleImages = filteredImages();
  const visibleIndex = visibleImages.findIndex((item) => item.id === state.selectedImageId);
  $("#viewer-position").textContent = visibleIndex >= 0
    ? `Imagen ${visibleIndex + 1} de ${visibleImages.length}`
    : activeImages().length ? "Fuera del filtro" : "Sin imagen";
  $("#preview-meta").textContent = isBridgeImage
    ? bridgePreviewMeta()
    : image ? `${state.format} · ${state.size} · ${backgroundLabel(state.background)}` : "Sin imagen";
  $("#canvas-area").className = `canvas-area bg-${state.previewBg === "transparent" ? "transparent" : state.previewBg}`;
  $$(".preview-toolbar [data-preview-mode]").forEach((button) => {
    button.classList.toggle("active", button.dataset.previewMode === state.previewMode);
    button.disabled = button.dataset.previewMode === "processed"
      ? previewControlsDisabled
      : compareControlsDisabled;
  });
  $$(".background-switch [data-preview-bg]").forEach((button) => {
    button.classList.toggle("active", button.dataset.previewBg === state.previewBg);
    button.disabled = previewControlsDisabled;
  });
  $$("[data-action='zoom-fit'], [data-action='zoom-100'], [data-action='zoom-out'], [data-action='zoom-in'], [data-action='force-preview-error']").forEach((button) => {
    button.disabled = previewControlsDisabled;
  });
  $$("[data-action='previous-image'], [data-action='next-image']").forEach((button) => {
    button.disabled = visibleImages.length < 2;
  });

  const canvas = $("#preview-canvas");
  canvas.className = `preview-canvas ${state.previewMode} bg-${state.previewBg} ${state.fitMode === "fit" ? "fit-mode" : "zoom-mode"}`;
  canvas.style.setProperty("--preview-scale", state.fitMode === "fit" ? "1" : String(state.zoom / 100));

  if (!image || state.previewStatus === "empty") {
    canvas.innerHTML = previewStateHtml("Sin imagen seleccionada", "El lote aparecerá aquí.");
    return;
  }

  if (isBridgeImage) {
    canvas.innerHTML = realPreviewHtml(image);
    return;
  }

  if (state.previewStatus === "loading") {
    canvas.innerHTML = `
      <div class="preview-state">
        <span class="loader" aria-hidden="true"></span>
        <strong>Generando preview</strong>
        <span>${escapeHtml(image.name)}</span>
      </div>
    `;
    return;
  }

  if (state.previewStatus === "error") {
    canvas.innerHTML = previewStateHtml("Preview no disponible", "Revisa alpha o archivo fuente.");
    return;
  }

  canvas.innerHTML = `
    <div class="mock-product" aria-hidden="true">
      <div class="mock-shadow"></div>
      <div class="mock-body"></div>
    </div>
    ${state.previewStatus === "warning" ? '<div class="preview-warning-card">Render con fallback. Revisa antes de exportar.</div>' : ""}
  `;
}

function realPreviewHtml(image) {
  if (state.previewStatus === "loading") {
    return `
      <div class="preview-state">
        <span class="loader" aria-hidden="true"></span>
        <strong>Generando preview</strong>
        <span>${escapeHtml(image.name)}</span>
      </div>
    `;
  }

  if (state.previewStatus === "error") {
    return previewStateHtml("Preview no disponible", state.previewError || "Revisa la imagen fuente.");
  }

  if (state.previewData?.src) {
    return `
      <img class="preview-image" src="${escapeHtml(state.previewData.src)}" alt="Preview real de ${escapeHtml(image.name)}" />
      ${state.previewData.warning ? `<div class="preview-warning-card">${escapeHtml(state.previewData.warning)}</div>` : ""}
    `;
  }

  return `
    <div class="real-preview-placeholder">
      <span class="state-chip bridge">Bridge local</span>
      <strong>Preview real pendiente</strong>
      <span>Imagen seleccionada: ${escapeHtml(image.name)}</span>
      <small class="path-line">Ruta: ${escapeHtml(image.path || "Sin ruta")}</small>
      <small>Genera la preview al seleccionar la imagen.</small>
    </div>
  `;
}

function bridgePreviewMeta() {
  if (state.previewStatus === "loading") {
    return "Bridge local · Generando preview";
  }
  if (state.previewStatus === "error") {
    return state.previewError || "Bridge local · Preview no disponible";
  }
  if (state.previewData) {
    const warning = state.previewData.warning ? " · Aviso" : "";
    return `Preview real · ${previewSettingsLabel()}${warning}`;
  }
  return "Bridge local · Preview pendiente";
}

function previewSettingsLabel() {
  if (state.bridgeMode === "bridge" && activePresetItem()?.source === "bridge") {
    return state.presetDirty ? "Ajustes reales modificados" : "Preset real";
  }
  return state.presetDirty ? "Ajustes modificados" : "Ajustes";
}

function previewStateHtml(title, detail) {
  return `
    <div class="preview-state">
      <strong>${escapeHtml(title)}</strong>
      <span>${escapeHtml(detail)}</span>
    </div>
  `;
}

function previewSubtitle(image) {
  if (!image) {
    return "Sin preview";
  }
  if (image.source === "bridge") {
    if (state.previewStatus === "loading") {
      return "Generando preview";
    }
    if (state.previewStatus === "warning") {
      return "Preview real con aviso";
    }
    if (state.previewStatus === "error") {
      return "Preview no disponible";
    }
    if (state.previewStatus === "ready") {
      return "Preview real";
    }
    return "Preview pendiente";
  }
  if (state.previewStatus === "loading") {
    return "Generando preview";
  }
  if (state.previewStatus === "warning") {
    return "Preview con aviso";
  }
  if (state.previewStatus === "error") {
    return "Preview no disponible";
  }
  return image.detail;
}

function renderSettings() {
  $("#active-preset").textContent = state.activePreset;
  $("#preset-source").textContent = presetSourceLabel();
  $("#preset-dirty").textContent = state.presetDirty ? "Sin guardar" : "Sin cambios";
  $("#preset-dirty").classList.toggle("dirty", state.presetDirty);
  $("#preset-list").innerHTML = activePresetItems().map((preset) => `
    <button type="button" class="preset-chip ${preset.name === state.activePreset ? "active" : ""}" data-preset="${escapeHtml(preset.name)}" title="${escapeHtml(preset.category)}">
      ${escapeHtml(preset.name)}
    </button>
  `).join("");

  Object.entries(state.settings).forEach(([key, value]) => {
    const input = $(`[data-setting="${key}"]`);
    const output = $(`#${key}-output`);
    if (input) {
      if (input.type === "checkbox") {
        input.checked = Boolean(value);
      } else {
        input.value = value;
      }
    }
    if (output) {
      output.textContent = value;
    }
  });

  const image = selectedImage();
  const localActive = state.localOverride || image?.status === "adjusted";
  $("#local-adjustment").classList.toggle("active", localActive);
  $("#local-adjustment-text").textContent = devMode
    ? (localActive ? "Ajuste local activo" : "Sin ajuste local")
    : "Fuera del MVP";
  $("#save-preset").disabled = state.bridgeMode === "bridge";
  $("#save-preset").title = state.bridgeMode === "bridge"
    ? "Guardado de presets fuera del MVP web/bridge actual"
    : "";
  $("#save-preset").textContent = state.bridgeMode === "bridge" ? "Guardar no disponible" : "Guardar preset";
  const advanced = $("#advanced-settings");
  if (advanced && advancedSettingsDirty()) {
    advanced.open = true;
  }
}

function advancedSettingsDirty() {
  if (!state.presetDirty) {
    return false;
  }
  const presetSettings = normalizeSettings(activePresetItem()?.settings || defaultSettings);
  return advancedSettingKeys.some((key) => state.settings[key] !== presetSettings[key]);
}

function renderInspector() {
  $$(".settings-panel [data-inspector-tab]").forEach((button) => {
    button.classList.toggle("active", button.dataset.inspectorTab === state.inspectorTab);
  });
  $$(".settings-panel [data-inspector-section]").forEach((section) => {
    section.classList.toggle("is-hidden", section.dataset.inspectorSection !== state.inspectorTab);
  });
}

function presetSourceLabel() {
  if (state.bridgeMode === "bridge") {
    const source = state.bridgePresetSource === "config"
      ? "Config"
      : state.bridgePresetSource === "legacy-config"
        ? "Config legacy"
        : state.bridgePresetSource === "defaults"
          ? "Defaults"
          : "Bridge local";
    if (state.bridgePresetWarning) {
      return `${source} · aviso`;
    }
    return state.presetDirty ? `${source} · modificado` : source;
  }
  return devMode
    ? (state.presetDirty ? "Mock · modificado" : "Mock")
    : (state.presetDirty ? "Fallback local · modificado" : "Fallback local");
}

function renderExport() {
  $("#format-select").value = state.format;
  $("#size-select").value = state.size;
  $("#background-select").value = state.background;
  $("#destination-mode").value = state.destinationMode;
  $("#destination-input").value = state.destinationValue;
  $("#naming-input").value = state.naming;

  const issues = preflightIssues();
  const exportable = exportableImages().length;
  const outputCount = exportable;
  const ready = isExportReady();
  const destinationText = state.destinationMode === "custom" ? state.destinationValue || "Sin configurar" : `origen / ${state.destinationValue}`;
  const statusText = exportPanelStatusLabel(ready, issues);

  $("#export-readiness").textContent = statusText;
  $("#export-count").textContent = `${outputCount} imágenes`;
  $("#export-count").classList.toggle("dirty", !ready);

  $("#export-summary").innerHTML = `
    <div class="summary-line"><span>Formato</span><strong>${escapeHtml(state.format)} · ${escapeHtml(state.size)}</strong></div>
    <div class="summary-line"><span>Fondo</span><strong>${escapeHtml(backgroundLabel(state.background))}</strong></div>
    <div class="summary-line"><span>Destino</span><strong>${escapeHtml(destinationText)}</strong></div>
    <div class="summary-line"><span>Naming</span><strong>${escapeHtml(state.naming || "Sin plantilla")}</strong></div>
    <div class="summary-line output-example"><span>Ejemplo</span><strong>${escapeHtml(namingExample())}</strong></div>
    <div class="summary-line"><span>Preflight</span><strong>${escapeHtml(exportPreflightSummary(issues, exportable, ready))}</strong></div>
  `;

  renderExportResult();

  $("#issue-list").innerHTML = issues.map((issue) => `
    <div class="issue-item ${issue.level === "error" ? "error" : ""}">
      <strong>${escapeHtml(issue.title)}</strong>
      <span>${escapeHtml(issue.detail)}</span>
    </div>
  `).join("");
}

function exportPanelStatusLabel(ready, issues = preflightIssues()) {
  if (state.exportStatus === "running") {
    return state.paused ? "Salida pausada" : "Exportando";
  }
  if (state.exportStatus === "completed") {
    return "Salida completada";
  }
  if (state.exportStatus === "partial") {
    return "Salida con avisos";
  }
  if (state.exportStatus === "failed") {
    return "Salida bloqueada";
  }
  if (issues.some((issue) => issue.level === "error")) {
    return "Salida bloqueada";
  }
  if (state.batch === "empty" || (hasBatch() && !ready)) {
    return "Salida bloqueada";
  }
  if (ready && issues.length) {
    return "Salida con avisos";
  }
  return ready ? "Salida lista" : "Configura salida";
}

function exportPreflightSummary(issues, exportable, ready) {
  const errors = issues.filter((issue) => issue.level === "error").length;
  const warnings = issues.length - errors;
  if (errors) {
    return `${errors} bloqueo${errors === 1 ? "" : "s"} · ${exportable} exportables`;
  }
  if (warnings) {
    return `${warnings} aviso${warnings === 1 ? "" : "s"} · ${exportable} exportables`;
  }
  return ready ? `${exportable} imágenes listas` : "Pendiente";
}

function namingExample() {
  if (!state.naming.trim()) {
    return "Sin ejemplo";
  }
  const image = exportableImages()[0] || selectedImage();
  const originalName = image?.name || "imagen_001.png";
  const original = originalName.replace(/\.[^.]+$/, "");
  const folder = activeFolders()[0]?.name || "lote";
  let example = state.naming
    .replaceAll("{original}", original)
    .replaceAll("{suffix}", "_PRO")
    .replaceAll("{folder}", folder);
  example = example.replace(/\{index(?::0?(\d+)d)?\}/g, (_match, width) => {
    const digits = Number(width) || 1;
    return String(1).padStart(digits, "0");
  });
  if (!/\.[a-z0-9]+$/i.test(example)) {
    example = `${example}.${state.format.toLowerCase()}`;
  }
  return example;
}

function renderExportResult() {
  const target = $("#export-result");
  const resultStatuses = ["running", "completed", "partial", "failed"];
  const shouldShow = resultStatuses.includes(state.exportStatus) || state.exportJobId || state.exportResult;
  if (!shouldShow) {
    target.innerHTML = "";
    return;
  }

  const total = Number(state.exportResult?.total ?? exportableImages().length ?? 0);
  const processed = Number(state.exportResult?.processed ?? state.processed ?? 0);
  const errors = Number(state.exportResult?.errors ?? state.exportIssues.filter((issue) => issue.level === "error").length ?? 0);
  const destinations = state.exportDestinations.length
    ? state.exportDestinations
    : Array.isArray(state.exportResult?.destinations)
      ? state.exportResult.destinations
      : [];
  const issues = state.exportIssues.length ? state.exportIssues : state.errors;
  const items = Array.isArray(state.exportCompletedItems) ? state.exportCompletedItems.slice(-8) : [];
  const title = exportResultTitle();
  const resultClass = state.exportStatus === "failed"
    ? "error"
    : state.exportStatus === "partial"
      ? "warning"
      : state.exportStatus === "completed"
        ? "ready"
        : "running";

  const destinationHtml = destinations.length
    ? destinations.slice(0, 3).map((path) => `
      <div class="result-path" title="${escapeHtml(path)}">
        <span>Destino</span>
        <strong>${escapeHtml(path)}</strong>
      </div>
    `).join("")
    : `<div class="result-path muted"><span>Destino</span><strong>${escapeHtml(destinationFallbackLabel())}</strong></div>`;

  const issuesHtml = issues.length ? `
    <div class="result-issues">
      <strong>${errors ? `${errors} error${errors === 1 ? "" : "es"}` : `${issues.length} aviso${issues.length === 1 ? "" : "s"}`}</strong>
      <span>${escapeHtml(issues[0].title)} · ${escapeHtml(issues[0].detail)}</span>
    </div>
  ` : "";

  const itemsHtml = items.length ? `
    <div class="result-items" aria-label="Archivos procesados">
      ${items.map((item) => `
        <span class="result-item ${item.success ? "ready" : "error"}" title="${escapeHtml(item.name || "Archivo")}">
          ${escapeHtml(item.name || "Archivo")}
        </span>
      `).join("")}
    </div>
  ` : "";

  target.innerHTML = `
    <div class="result-header ${resultClass}">
      <strong>${escapeHtml(title)}</strong>
      <span>${escapeHtml(processed)}/${escapeHtml(total)} archivos</span>
    </div>
    ${destinationHtml}
    ${issuesHtml}
    ${itemsHtml}
  `;
}

function exportResultTitle() {
  if (state.exportStatus === "running") {
    return state.paused ? "Exportación pausada" : "Exportando";
  }
  if (state.exportStatus === "completed") {
    return "Exportación completada";
  }
  if (state.exportStatus === "partial") {
    return "Completada con avisos";
  }
  if (state.exportStatus === "failed") {
    return "Exportación fallida";
  }
  return "Resultado";
}

function destinationFallbackLabel() {
  if (state.destinationMode === "custom") {
    return state.destinationValue || "Destino sin configurar";
  }
  return `origen / ${state.destinationValue}`;
}

function exportStatusLabel(ready) {
  if (state.exportStatus === "running") {
    return state.paused ? "Pausada" : "Procesando";
  }
  if (state.exportStatus === "completed") {
    return "Completada";
  }
  if (state.exportStatus === "partial") {
    return "Con errores";
  }
  if (state.exportStatus === "failed") {
    return "Fallida";
  }
  return ready ? "Lista" : "Configura exportación";
}

function backgroundLabel(value) {
  if (value === "transparent") {
    return "Transparente";
  }
  if (value === "white") {
    return "Blanco";
  }
  return "RGB230";
}

function renderFooter() {
  const exportable = exportableImages().length;
  const issues = [...validationIssues(), ...state.errors];
  const ready = isExportReady();
  const images = activeImages();
  const selectedIndex = images.findIndex((image) => image.id === state.selectedImageId);
  const selectedText = selectedIndex >= 0 ? ` · Imagen ${selectedIndex + 1}/${images.length}` : "";
  const warningText = issues.length ? ` · ${issues.length} aviso${issues.length === 1 ? "" : "s"}` : "";

  $("#footer-batch").textContent = hasBatch()
    ? `${images.length} imágenes${selectedText}${warningText}`
    : state.batch === "empty"
      ? `0 PNG · ${sourceLabel()}`
      : "Sin lote";
  $("#footer-preview").textContent = previewFooterLabel();
  $("#footer-export").textContent = exportPanelStatusLabel(ready, preflightIssues());
  $("#footer-destination").textContent = !hasBatch()
    ? "Sin destino"
    : state.destinationMode === "custom"
      ? state.destinationValue || "Sin configurar"
      : `origen / ${state.destinationValue}`;
  $("#bottom-status").textContent = state.statusText;
  $("#progress-fill").style.width = `${state.progress}%`;
  $("#progress-fill").className = state.exportStatus === "failed" ? "error" : state.exportStatus === "partial" ? "warning" : "";
  $(".progress-track").classList.toggle("is-idle", state.exportStatus !== "running");

  const hasReviewIssues = (hasBatch() || state.batch === "empty") && (
    issues.some((issue) => issue.title !== "Sin lote")
    || activeImages().some((image) => image.status === "error" || image.status === "warning" || exportItemState(image)?.status === "error")
  );
  $("#review-errors").classList.toggle("is-hidden", !hasReviewIssues);
  $("#review-errors").disabled = !hasReviewIssues;
  $("#pause-export").classList.toggle("is-hidden", state.exportStatus !== "running");
  $("#pause-export").textContent = state.paused ? "Reanudar" : "Pausar";
  $("#stop-export").classList.toggle("is-hidden", state.exportStatus !== "running");
  $("#open-output").classList.add("is-hidden");
  $("#open-output").disabled = true;
  $("#primary-action").classList.add("is-hidden");

  const primaryButtons = [$("#primary-action"), $("#top-primary-action")].filter(Boolean);
  const primaryDisabled = state.exportStatus === "running"
    || (hasBatch() && !ready && validationIssues().some((issue) => issue.level === "error"));
  let primaryText = "";
  if (!hasBatch()) {
    primaryText = "Seleccionar carpeta";
  } else if (state.exportStatus === "completed" || state.exportStatus === "partial") {
    primaryText = "Nuevo lote";
  } else if (!ready) {
    primaryText = "Preparar salida";
  } else {
    primaryText = `Exportar ${exportable}`;
  }
  primaryButtons.forEach((primary) => {
    primary.disabled = primaryDisabled;
    primary.textContent = primaryText;
  });
}

function previewFooterLabel() {
  if (selectedImage()?.source === "bridge") {
    if (state.previewStatus === "loading") {
      return "Generando";
    }
    if (state.previewStatus === "warning") {
      return "Con aviso";
    }
    if (state.previewStatus === "error") {
      return "Error";
    }
    if (state.previewStatus === "ready") {
      return "Real";
    }
    return "Pendiente";
  }
  if (state.previewStatus === "loading") {
    return "Generando";
  }
  if (state.previewStatus === "warning") {
    return "Con aviso";
  }
  if (state.previewStatus === "error") {
    return "Error";
  }
  if (state.previewStatus === "ready") {
    return "Lista";
  }
  return "Sin imagen";
}

function handleAction(action) {
  if (action === "load-batch") {
    loadBatch();
  } else if (action === "load-mock-batch") {
    loadMockBatch();
  } else if (action === "check-bridge") {
    void checkBridge();
  } else if (action === "toggle-inspector") {
    state.inspectorCollapsed = !state.inspectorCollapsed;
    state.statusText = state.inspectorCollapsed ? "Inspector oculto" : "Inspector visible";
    render();
  } else if (action === "pick-bridge-folder") {
    void pickBridgeFolder();
  } else if (action === "scan-bridge-folder") {
    void scanBridgeFolder();
  } else if (action === "clear-batch") {
    clearBatch();
  } else if (action === "show-empty-folder") {
    showEmptyFolder();
  } else if (action === "force-preview-error") {
    if (hasBatch()) {
      state.previewStatus = "error";
      state.statusText = "Preview no disponible";
      render();
    }
  } else if (action === "previous-image") {
    selectAdjacentImage(-1);
  } else if (action === "next-image") {
    selectAdjacentImage(1);
  } else if (action === "clear-filter") {
    clearFilter();
  } else if (action === "zoom-fit") {
    state.fitMode = "fit";
    state.zoom = 100;
    state.statusText = "Imagen ajustada";
    render();
  } else if (action === "zoom-100") {
    state.fitMode = "manual";
    state.zoom = 100;
    state.statusText = "Zoom 100%";
    render();
  } else if (action === "zoom-in") {
    state.fitMode = "manual";
    state.zoom = Math.min(160, state.zoom + 10);
    render();
  } else if (action === "zoom-out") {
    state.fitMode = "manual";
    state.zoom = Math.max(70, state.zoom - 10);
    render();
  } else if (action === "reset-settings") {
    resetActivePresetSettings();
  } else if (action === "save-preset") {
    if (state.bridgeMode === "bridge") {
      state.statusText = "Guardado de presets fuera del MVP";
      render();
      return;
    }
    state.presetDirty = false;
    state.presetSource = "Mock";
    state.statusText = "Preset guardado";
    render();
  } else if (action === "toggle-local-adjustment") {
    if (!devMode) {
      state.statusText = "Ajuste por imagen fuera del MVP";
      render();
      return;
    }
    state.localOverride = !state.localOverride;
    state.statusText = state.localOverride ? "Ajuste local activo" : "Ajuste local quitado";
    render();
  } else if (action === "pause-export") {
    pauseExport();
  } else if (action === "stop-export") {
    stopExport();
  } else if (action === "review-errors") {
    reviewErrors();
  } else if (action === "open-output") {
    state.statusText = "Apertura nativa fuera del MVP";
    render();
  } else if (action === "primary") {
    primaryAction();
  }
}

document.addEventListener("click", (event) => {
  const actionTarget = event.target.closest("[data-action]");
  if (actionTarget) {
    handleAction(actionTarget.dataset.action);
    return;
  }

  const imageTarget = event.target.closest("[data-image-id]");
  if (imageTarget) {
    selectImage(imageTarget.dataset.imageId);
    return;
  }

  const reviewTarget = event.target.closest("[data-review-scenario]");
  if (reviewTarget) {
    showReviewScenario(reviewTarget.dataset.reviewScenario);
    return;
  }

  const filterTarget = event.target.closest("[data-filter]");
  if (filterTarget) {
    state.filter = filterTarget.dataset.filter;
    state.statusText = filterStatusText(state.filter);
    render();
    return;
  }

  const modeTarget = event.target.closest("[data-preview-mode]");
  if (modeTarget) {
    state.previewMode = modeTarget.dataset.previewMode;
    state.statusText = modeTarget.textContent.trim();
    render();
    return;
  }

  const bgTarget = event.target.closest("[data-preview-bg]");
  if (bgTarget) {
    state.previewBg = bgTarget.dataset.previewBg;
    state.statusText = `Fondo: ${bgTarget.textContent.trim()}`;
    render();
    return;
  }

  const presetTarget = event.target.closest("[data-preset]");
  if (presetTarget) {
    applyPresetSettings(presetTarget.dataset.preset);
  }

  const inspectorTarget = event.target.closest("[data-inspector-tab]");
  if (inspectorTarget) {
    state.inspectorTab = inspectorTarget.dataset.inspectorTab;
    render();
  }
});

$("#demo-scenario").addEventListener("change", (event) => {
  if (!devMode) {
    return;
  }
  state.bridgeMode = "mock";
  state.bridgeLastResponse = `Estado mock: ${scenarioLabels[event.target.value] || event.target.value}`;
  setScenario(event.target.value);
});

$("#app-mode").addEventListener("change", (event) => {
  if (!devMode && event.target.value !== "bridge") {
    event.target.value = "bridge";
    state.bridgeMode = "bridge";
    render();
    return;
  }
  state.bridgeMode = event.target.value;
  state.statusText = state.bridgeMode === "bridge" ? "Bridge local" : "Modo mock";
  state.bridgeLastResponse = state.bridgeMode === "bridge" ? "Bridge pendiente" : "Mock activo";
  state.scanStatus = state.bridgeMode === "bridge" ? "Selecciona una carpeta con PNG." : "Escenarios mock activos.";
  render();
});

$("#bridge-url").addEventListener("input", (event) => {
  state.bridgeUrl = event.target.value || defaultBridgeUrl;
  state.bridgeStatus = "idle";
  state.bridgeMessage = "Comprueba conexión";
  state.bridgeLastResponse = "URL pendiente";
  state.scanStatus = "Comprueba bridge";
  render();
});

$("#bridge-scan-path").addEventListener("input", (event) => {
  state.bridgeScanPath = event.target.value;
});

$("#image-search").addEventListener("input", (event) => {
  state.search = event.target.value;
  render();
});

$$("[data-setting]").forEach((input) => {
  const updateSetting = (event) => {
    const key = event.target.dataset.setting;
    const nextValue = settingInputValue(event.target);
    if (state.settings[key] === nextValue) {
      return;
    }
    state.settings[key] = nextValue;
    markPresetDirty();
  };
  input.addEventListener("input", updateSetting);
  input.addEventListener("change", updateSetting);
});

function settingInputValue(input) {
  if (input.type === "checkbox") {
    return input.checked;
  }
  if (input.tagName === "SELECT") {
    return input.value;
  }
  return Number(input.value);
}

$("#format-select").addEventListener("change", (event) => {
  state.format = event.target.value;
  state.statusText = `Formato: ${state.format}`;
  render();
});

$("#size-select").addEventListener("change", (event) => {
  state.size = event.target.value;
  state.statusText = `Tamaño: ${state.size}`;
  const image = selectedImage();
  if (image?.source === "bridge") {
    void requestBridgePreview(image);
    return;
  }
  render();
});

$("#background-select").addEventListener("change", (event) => {
  state.background = event.target.value;
  state.previewBg = event.target.value;
  state.statusText = `Fondo: ${backgroundLabel(state.background)}`;
  const image = selectedImage();
  if (image?.source === "bridge") {
    void requestBridgePreview(image);
    return;
  }
  render();
});

$("#destination-mode").addEventListener("change", (event) => {
  state.destinationMode = event.target.value;
  state.destinationValue = state.destinationMode === "custom" ? "" : "_SALIDA_PRO";
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = state.destinationMode === "custom" ? "Destino sin configurar" : "Destino: origen";
  render();
});

$("#destination-input").addEventListener("input", (event) => {
  state.destinationValue = event.target.value;
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = state.destinationValue.trim() ? "Destino configurado" : "Destino sin configurar";
  render();
});

$("#naming-input").addEventListener("input", (event) => {
  state.naming = event.target.value;
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = state.naming.trim() ? "Naming actualizado" : "Naming vacío";
  render();
});

setScenario("initial");
