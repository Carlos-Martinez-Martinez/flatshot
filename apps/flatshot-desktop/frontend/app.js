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
    detail: "Vista con aviso",
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
const STORAGE_KEYS = {
  bridgeScanPath: "flatshot.bridgeScanPath",
  selectedImagePath: "flatshot.selectedImagePath",
  outputProfiles: "flatshot.outputProfiles",
  activeOutputProfile: "flatshot.activeOutputProfile",
};
document.documentElement.classList.toggle("dev-mode", devMode);

const statusLabels = {
  ready: "Lista",
  adjusted: "Ajustada",
  warning: "Aviso",
  error: "Error",
};

const DEFAULT_VIEW_MODE = "height";
const VIEW_MODE_LABELS = {
  fit: "Encajar",
  height: "Altura",
  width: "Anchura",
  manual: "Manual",
};

const scenarioLabels = {
  initial: "Sin lote",
  "batch-ready": "Lote listo",
  "empty-folder": "Carpeta vacía",
  "preview-loading": "Vista cargando",
  "preview-warning": "Vista con aviso",
  "preview-error": "Error de vista",
  "export-blocked": "Carpeta de salida sin configurar",
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

const localOverrideKeys = ["size_delta", "shadow_delta", "blur_delta"];
const localOverrideLimits = {
  size_delta: [-30, 30],
  shadow_delta: [-40, 40],
  blur_delta: [-40, 40],
};

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

const defaultOutputProfiles = [
  {
    id: "jpg-rgb230-1800x2400",
    name: "JPG gris claro 1800x2400",
    format: "JPG",
    width: 1800,
    height: 2400,
    background: "rgb230",
    destinationMode: "source",
    destinationValue: "_SALIDA_PRO",
    naming: "{original}{suffix}",
    suffix: "_PRO",
  },
  {
    id: "png-transparent-1800x2400",
    name: "PNG transparente 1800x2400",
    format: "PNG",
    width: 1800,
    height: 2400,
    background: "transparent",
    destinationMode: "source",
    destinationValue: "_SALIDA_PRO",
    naming: "{original}{suffix}",
    suffix: "_PRO",
  },
  {
    id: "jpg-white-2000x2000",
    name: "JPG blanco 2000x2000",
    format: "JPG",
    width: 2000,
    height: 2000,
    background: "white",
    destinationMode: "source",
    destinationValue: "_SALIDA_PRO",
    naming: "{original}{suffix}",
    suffix: "_PRO",
  },
];
const initialOutputProfiles = readOutputProfiles();
const initialOutputProfileId = readPersistentValue(STORAGE_KEYS.activeOutputProfile);
const initialOutputProfile = initialOutputProfiles.find((profile) => profile.id === initialOutputProfileId)
  || initialOutputProfiles[0]
  || defaultOutputProfiles[0];

const state = {
  scenario: "initial",
  batch: "none",
  batchSource: "none",
  selectedImageId: null,
  previewStatus: "empty",
  previewRequestId: 0,
  previewData: null,
  previewError: "",
  thumbnailStatus: {},
  thumbnailErrors: [],
  previewMode: "processed",
  previewBg: "rgb230",
  zoom: 100,
  fitZoom: 100,
  fitMode: DEFAULT_VIEW_MODE,
  panX: 0,
  panY: 0,
  filter: "all",
  search: "",
  galleryView: "thumbs",
  inspectorTab: "review",
  inspectorCollapsed: false,
  outputEditMode: false,
  presetEditorOpen: false,
  activePreset: "Luz cenital",
  presetOutputSettings: {},
  settings: { ...defaultSettings },
  presetDirty: false,
  presetSource: "Salida",
  localOverride: false,
  exportStatus: "blocked",
  exportJobId: null,
  exportDestinations: [],
  exportMessages: [],
  exportCompletedItems: [],
  exportIssues: [],
  exportResult: null,
  exportPollTimer: null,
  outputDraft: null,
  appSettingsOpen: false,
  batchDetailOpen: false,
  outputProfiles: initialOutputProfiles,
  activeOutputProfileId: initialOutputProfile.id,
  outputProfileEditorId: initialOutputProfile.id,
  outputProfileDraft: null,
  destinationMode: initialOutputProfile.destinationMode,
  destinationValue: initialOutputProfile.destinationValue,
  format: initialOutputProfile.format,
  size: outputProfileSize(initialOutputProfile),
  background: initialOutputProfile.background,
  naming: initialOutputProfile.naming,
  suffix: initialOutputProfile.suffix,
  progress: 0,
  processed: 0,
  errors: [],
  paused: false,
  statusText: "Sin lote",
  bridgeMode: "bridge",
  bridgeUrl: defaultBridgeUrl,
  bridgeStatus: "idle",
  bridgeMessage: "Sin lote",
  bridgeLastResponse: "Bridge pendiente",
  bridgeCapabilitiesSummary: "Sin comprobar",
  bridgeCapabilities: null,
  bridgePresets: [],
  bridgePresetSource: "unavailable",
  bridgePresetWarning: "",
  bridgeScanPath: readPersistentValue(STORAGE_KEYS.bridgeScanPath),
  scanStatus: "Sin lote",
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
  imageOverrides: {},
};

const timers = new Set();
const thumbnailPreloads = new Map();
const thumbnailFallbackQueue = [];
const thumbnailFallbackInFlight = new Set();
const MAX_THUMBNAIL_FALLBACKS = 3;
let fitZoomFrame = 0;
let viewerResizeObserver = null;
let inspectorScrollTopBeforeToggle = 0;
const inspectorDisclosureTimers = new WeakMap();
const INSPECTOR_DISCLOSURE_MS = 220;
const viewerPanState = {
  active: false,
  pointerId: null,
  startX: 0,
  startY: 0,
  originX: 0,
  originY: 0,
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

function readPersistentValue(key) {
  try {
    return window.localStorage.getItem(key) || "";
  } catch (error) {
    return "";
  }
}

function readPersistentJson(key, fallback) {
  const raw = readPersistentValue(key);
  if (!raw) {
    return fallback;
  }
  try {
    return JSON.parse(raw);
  } catch (error) {
    return fallback;
  }
}

function writePersistentValue(key, value) {
  const normalized = String(value || "").trim();
  try {
    if (normalized) {
      window.localStorage.setItem(key, normalized);
    } else {
      window.localStorage.removeItem(key);
    }
  } catch (error) {
    // Persistence is a convenience; the app must still work if storage is blocked.
  }
}

function writePersistentJson(key, value) {
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    // Settings persistence is local convenience; runtime state remains usable.
  }
}

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

function normalizeOutputProfile(profile, index = 0) {
  const source = profile && typeof profile === "object" ? profile : {};
  const width = Math.max(1, Number.parseInt(source.width, 10) || 1800);
  const height = Math.max(1, Number.parseInt(source.height, 10) || 2400);
  const format = normalizeExportFormat(source.format);
  const background = ["rgb230", "white", "transparent"].includes(source.background)
    ? source.background
    : "rgb230";
  const destinationMode = source.destinationMode === "custom" ? "custom" : "source";
  return {
    id: String(source.id || uniqueOutputProfileId("formato", index)).trim(),
    name: outputProfileNameForDisplay(String(source.name || `Formato ${index + 1}`).trim()),
    format,
    width,
    height,
    background,
    destinationMode,
    destinationValue: String(source.destinationValue || (destinationMode === "custom" ? "" : "_SALIDA_PRO")),
    naming: String(source.naming || "{original}{suffix}"),
    suffix: source.suffix === undefined || source.suffix === null ? "_PRO" : String(source.suffix),
  };
}

function outputProfileNameForDisplay(name) {
  return String(name || "")
    .replace(/\bRGB\s*230\b/gi, "gris claro")
    .replace(/\bRGB230\b/gi, "gris claro");
}

function normalizeExportFormat(value) {
  const text = String(value || "JPG").trim().toUpperCase().replace(/^\./, "");
  if (text === "JPEG") {
    return "JPG";
  }
  return text === "PNG" ? "PNG" : "JPG";
}

function readOutputProfiles() {
  const saved = readPersistentJson(STORAGE_KEYS.outputProfiles, null);
  const profiles = Array.isArray(saved) ? saved : defaultOutputProfiles;
  const normalized = profiles.map(normalizeOutputProfile).filter((profile) => profile.name);
  return normalized.length ? dedupeOutputProfileIds(normalized) : defaultOutputProfiles.map(normalizeOutputProfile);
}

function dedupeOutputProfileIds(profiles) {
  const seen = new Set();
  return profiles.map((profile, index) => {
    let id = profile.id || uniqueOutputProfileId(profile.name, index);
    while (seen.has(id)) {
      id = uniqueOutputProfileId(profile.name, index + seen.size);
    }
    seen.add(id);
    return { ...profile, id };
  });
}

function uniqueOutputProfileId(name = "formato", seed = Date.now()) {
  const base = String(name)
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    || "formato";
  return `${base}-${String(seed).replace(/\D/g, "").slice(-6) || Date.now()}`;
}

function outputProfileSize(profile) {
  return `${Math.max(1, Number(profile?.width) || 1800)}x${Math.max(1, Number(profile?.height) || 2400)}`;
}

function parseOutputSize(value) {
  const match = /^(\d+)\s*[x×]\s*(\d+)$/i.exec(String(value || "").trim());
  if (!match) {
    return { width: 1800, height: 2400, normalized: "1800x2400" };
  }
  const width = Math.max(1, Number.parseInt(match[1], 10) || 1800);
  const height = Math.max(1, Number.parseInt(match[2], 10) || 2400);
  return { width, height, normalized: `${width}x${height}` };
}

function activeOutputProfile() {
  return state.outputProfiles.find((profile) => profile.id === state.activeOutputProfileId)
    || state.outputProfiles[0]
    || defaultOutputProfiles[0];
}

function currentOutputProfileData() {
  const size = parseOutputSize(state.size);
  return normalizeOutputProfile({
    id: state.activeOutputProfileId || uniqueOutputProfileId("actual"),
    name: activeOutputProfile()?.name || "Formato actual",
    format: state.format,
    width: size.width,
    height: size.height,
    background: state.background,
    destinationMode: state.destinationMode,
    destinationValue: state.destinationValue,
    naming: state.naming,
    suffix: state.suffix,
  });
}

function outputMatchesProfile(profile = activeOutputProfile()) {
  if (!profile) {
    return false;
  }
  const current = currentOutputProfileData();
  return current.format === profile.format
    && current.width === profile.width
    && current.height === profile.height
    && current.background === profile.background
    && current.destinationMode === profile.destinationMode
    && current.destinationValue === profile.destinationValue
    && current.naming === profile.naming
    && current.suffix === profile.suffix;
}

function persistOutputProfiles() {
  writePersistentJson(STORAGE_KEYS.outputProfiles, state.outputProfiles);
  writePersistentValue(STORAGE_KEYS.activeOutputProfile, state.activeOutputProfileId);
}

function applyOutputProfile(profileId, options = {}) {
  const profile = state.outputProfiles.find((item) => item.id === profileId);
  if (!profile) {
    return false;
  }
  state.activeOutputProfileId = profile.id;
  state.format = profile.format;
  state.size = outputProfileSize(profile);
  state.background = profile.background;
  state.previewBg = profile.background;
  state.destinationMode = profile.destinationMode;
  state.destinationValue = profile.destinationValue;
  state.naming = profile.naming;
  state.suffix = profile.suffix;
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = options.statusText || `Formato: ${profile.name}`;
  persistOutputProfiles();
  if (options.render !== false) {
    render();
  }
  return true;
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
    category: devMode ? "Demo" : "Ajuste local",
    categoryId: devMode ? "mock" : "fallback",
    settings: normalizeSettings(mockPresetSettings[name]),
    source: devMode ? "demo" : "fallback",
  }));
}

function activePresetItem() {
  return activePresetItems().find((preset) => preset.name === state.activePreset) || null;
}

function exportableImages() {
  return activeImages().filter((image) => image.exportable);
}

function countText(count, singular, plural = `${singular}s`) {
  const value = Number(count) || 0;
  return `${value} ${value === 1 ? singular : plural}`;
}

function blockingValidationIssues() {
  return validationIssues().filter((issue) => issue.level === "error" && issue.title !== "Sin lote");
}

function batchCounts() {
  const images = activeImages();
  const diagnostics = state.scanDiagnostics || emptyScanDiagnostics();
  const omittedFiles = Number(diagnostics.totalOmitted || 0);
  const filesFound = state.batch === "scanning"
    ? null
    : Math.max(
      Number(diagnostics.totalFiles || 0),
      Number(diagnostics.totalImages || 0) + omittedFiles,
      images.length + omittedFiles
    );
  const validImages = state.batch === "scanning"
    ? null
    : Math.max(Number(diagnostics.totalImages || 0), images.length);
  const exportables = exportableImages();
  const exportedErrors = new Set(
    images
      .filter((image) => exportItemState(image)?.status === "error")
      .map((image) => image.id)
  );
  const exportableWarningImages = exportables.filter((image) => image.status === "warning").length;
  const nonExportableImages = images.filter((image) =>
    !image.exportable || image.status === "error" || exportedErrors.has(image.id)
  ).length;
  const warningImages = exportableWarningImages + nonExportableImages;
  const readyImages = exportables.filter((image) =>
    !["warning", "error"].includes(image.status) && !exportedErrors.has(image.id)
  ).length;
  const stateErrors = state.errors.filter((issue) => issue.level === "error").length;
  const stateWarnings = state.errors.length - stateErrors;
  const blockingErrors = blockingValidationIssues().length + (state.exportStatus === "failed" ? 1 : 0);

  return {
    filesFound,
    validImages,
    exportableImages: exportables.length,
    readyImages,
    warningImages,
    omittedFiles,
    nonExportableImages,
    blockingErrors,
    nonBlockingWarnings: omittedFiles + warningImages + stateWarnings,
  };
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
    if (term && !imageSearchText(image).includes(term)) {
      return false;
    }
    if (state.filter === "valid") {
      return image.status === "ready" || image.status === "adjusted";
    }
    if (state.filter === "warnings") {
      return image.status === "warning" || image.status === "error" || exportItemState(image)?.status === "error";
    }
    if (state.filter === "omitted") {
      return false;
    }
    return true;
  });
}

function imageSearchText(image) {
  const name = String(image?.name || "");
  const stem = imageFileStem(name);
  const path = String(image?.path || "");
  const tokens = stem.split(/[^a-z0-9]+/i).filter(Boolean);
  return [name, stem, path, ...tokens].join(" ").toLowerCase();
}

function filterDisplayName(filter = state.filter) {
  const labels = {
    all: "todas",
    valid: "listas",
    warnings: "con aviso",
    omitted: "omitidas",
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
    issues.push({ level: "error", title: "Sin lote", detail: "Elige una carpeta con imágenes para iniciar el lote." });
  }
  if (state.batch === "empty") {
    issues.push({ level: "warning", title: "No hay imágenes válidas", detail: "Elige otra carpeta o revisa el detalle técnico." });
  }
  if (exportableImages().length === 0 && state.batch === "ready") {
    issues.push({ level: "error", title: "Sin imágenes exportables", detail: "Revisa los errores." });
  }
  if (!state.naming.trim()) {
    issues.push({ level: "error", title: "Nombre de archivo vacío", detail: "Define una plantilla de nombre." });
  }
  if (state.destinationMode === "custom" && !state.destinationValue.trim()) {
    issues.push({ level: "error", title: "Carpeta de salida sin configurar", detail: "Elige una carpeta de salida." });
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
      title: `${omitted} omitida${omitted === 1 ? "" : "s"}`,
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

function uiState() {
  const counts = preflightCounts();
  const lotCounts = batchCounts();
  const image = selectedImage();
  return {
    hasBatch: hasBatch(),
    hasBatchContext: hasBatch() || state.batch === "empty" || state.batch === "scanning",
    hasSelectedImage: Boolean(image),
    isBridgeReady: state.bridgeMode === "bridge" && state.bridgeStatus === "connected",
    canExport: isExportReady(),
    hasWarnings: lotCounts.nonBlockingWarnings > 0 || counts.warnings > 0,
    hasBlockingErrors: lotCounts.blockingErrors > 0,
    isProcessing: state.batch === "scanning" || state.previewStatus === "loading" || state.exportStatus === "running",
    isExporting: state.exportStatus === "running",
  };
}

function visibleWarningCount() {
  return batchCounts().nonBlockingWarnings;
}

function warningCountLabel(count = visibleWarningCount()) {
  return `${count} aviso${count === 1 ? "" : "s"}`;
}

function imageCountLabel(count) {
  return `${count} ${count === 1 ? "imagen" : "imágenes"}`;
}

function detectedFormatLabel(images = activeImages()) {
  if (!images.length) {
    return "PNG";
  }
  const suffixes = Array.from(new Set(images.map((image) =>
    String(image.name || image.suffix || "")
      .split(".")
      .pop()
      ?.toUpperCase()
      || "PNG"
  )));
  if (suffixes.length === 1) {
    return suffixes[0];
  }
  return "PNG/JPG";
}

function outputPresetLabel() {
  return state.activePreset || "Salida";
}

function firstOmittedItem() {
  const omitted = state.scanDiagnostics?.omitted;
  return Array.isArray(omitted) && omitted.length ? omitted[0] : null;
}

function firstActionableIssue() {
  const omitted = firstOmittedItem();
  if (omitted) {
    return {
      level: "warning",
      title: "Archivo omitido",
      file: omitted.name || "Archivo",
      detail: omissionReasonLabel(omitted.reason),
      path: omitted.path || omitted.folder || "",
    };
  }

  const imageIssue = activeImages().find((image) => image.status === "error")
    || activeImages().find((image) => image.status === "warning")
    || activeImages().find((image) => exportItemState(image)?.status === "error");
  if (imageIssue) {
    return {
      level: imageIssue.status === "error" || exportItemState(imageIssue)?.status === "error" ? "error" : "warning",
      title: imageIssue.status === "error" ? "Imagen no exportable" : "Imagen con aviso",
      file: imageIssue.name,
      detail: imageIssue.detail || statusLabels[imageIssue.status] || "Revisar imagen",
      path: imageIssue.path || "",
    };
  }

  const issue = state.errors[0] || preflightIssues().find((item) => item.title !== "Sin lote") || null;
  return issue
    ? {
        level: issue.level,
        title: issue.title,
        file: "",
        detail: issue.detail,
        path: "",
      }
    : null;
}

function batchSummaryLabel() {
  const count = activeImages().length;
  if (state.batch === "none") {
    return "Sin lote";
  }
  if (state.batch === "scanning") {
    return "Escaneando";
  }
  if (state.batch === "empty") {
    return "Sin imágenes";
  }
  const warnings = visibleWarningCount();
  return `${imageCountLabel(count)}${warnings ? ` · ${warningCountLabel(warnings)}` : ""}`;
}

function firstBlockingIssue() {
  return preflightIssues().find((issue) => issue.level === "error")
    || preflightIssues()[0]
    || null;
}

function getVisibleAppState() {
  const counts = batchCounts();
  const blockers = blockingValidationIssues();
  const hasWarnings = counts.nonBlockingWarnings > 0;
  const output = batchOutputLine();
  const destination = batchDestinationLine();
  const summary = readyBatchSummaryText(counts);

  if (state.exportStatus === "running") {
    const total = counts.exportableImages;
    return {
      id: "exporting",
      tone: "busy",
      title: state.paused ? "Exportación pausada" : "Exportando lote",
      subtitle: state.paused ? `Pausado · ${state.processed}/${total}` : `Procesando ${state.processed}/${total}`,
      topSummary: compactHeaderStatusText(),
      primaryAction: { label: state.paused ? "Exportación pausada" : "Exportando...", action: "", enabled: false },
      secondaryAction: { label: "Detener", action: "stop-export", enabled: true },
      nextStep: state.paused ? "Reanudar o detener" : "Esperar a que termine la exportación",
      counts,
    };
  }

  if (state.exportStatus === "completed" || state.exportStatus === "partial") {
    const processed = Number(state.exportResult?.processed ?? state.processed ?? counts.exportableImages);
    const total = Number(state.exportResult?.total ?? counts.exportableImages);
    return {
      id: "export_done",
      tone: state.exportStatus === "partial" ? "warning" : "ready",
      title: state.exportStatus === "partial" ? "Exportación finalizada con avisos" : "Exportación finalizada",
      subtitle: `${processed}/${total} imágenes exportadas · ${destination}`,
      topSummary: compactHeaderStatusText(),
      primaryAction: { label: "Abrir carpeta de salida", action: "open-output", enabled: Boolean(outputDestinationToOpen()) },
      secondaryAction: { label: "Exportar de nuevo", action: "start-export", enabled: isExportReady() },
      nextStep: outputDestinationToOpen() ? "Abrir carpeta de salida" : "Revisar resultado de exportación",
      counts,
    };
  }

  if (state.exportStatus === "failed") {
    const issue = firstBlockingIssue();
    return {
      id: "ready_with_blockers",
      tone: "error",
      title: "Exportación con errores",
      subtitle: issue?.detail || "Revisa el detalle antes de continuar.",
      topSummary: compactHeaderStatusText(),
      primaryAction: { label: "Ver detalle técnico", action: "review-warnings", enabled: true },
      secondaryAction: isExportReady() ? { label: "Exportar de nuevo", action: "start-export", enabled: true } : null,
      nextStep: "Revisar errores",
      counts,
    };
  }

  if (state.batch === "scanning") {
    return {
      id: "scanning",
      tone: "busy",
      title: "Leyendo carpeta",
      subtitle: state.scanStatus || "Preparando el lote.",
      topSummary: compactHeaderStatusText(),
      primaryAction: { label: "Escaneando...", action: "", enabled: false },
      secondaryAction: null,
      nextStep: "Esperar a que termine la lectura",
      counts,
    };
  }

  if (state.batch === "none") {
    return {
      id: "no_folder",
      tone: "idle",
      title: "Sin carpeta seleccionada",
      subtitle: "Selecciona una carpeta local con imágenes PNG o JPG.",
      topSummary: compactHeaderStatusText(),
      primaryAction: { label: "Seleccionar carpeta", action: "pick-bridge-folder", enabled: state.bridgeStatus !== "checking" },
      secondaryAction: null,
      nextStep: "Seleccionar carpeta",
      counts,
    };
  }

  if (state.batch === "empty") {
    const hasFoundFiles = counts.filesFound > 0 || counts.omittedFiles > 0;
    return {
      id: hasFoundFiles ? "scan_empty" : "batch_empty",
      tone: "warning",
      title: hasFoundFiles ? "Carpeta sin imágenes válidas" : "Lote vacío",
      subtitle: hasFoundFiles
        ? `${countText(counts.filesFound, "archivo encontrado", "archivos encontrados")} · ${countText(counts.omittedFiles, "omitido", "omitidos")}`
        : "No hay archivos compatibles en esta carpeta.",
      topSummary: compactHeaderStatusText(),
      primaryAction: { label: "Elegir otra carpeta", action: "pick-bridge-folder", enabled: state.bridgeStatus !== "checking" },
      secondaryAction: counts.omittedFiles ? { label: "Ver detalle técnico", action: "review-warnings", enabled: true } : null,
      nextStep: "Elegir otra carpeta",
      counts,
    };
  }

  if (blockers.length) {
    const issue = blockers[0];
    return {
      id: "ready_with_blockers",
      tone: "error",
      title: "Lote con errores bloqueantes",
      subtitle: issue.detail || "Hay un problema que impide exportar.",
      topSummary: compactHeaderStatusText(),
      primaryAction: { label: "Resolver problemas", action: "review-output", enabled: true },
      secondaryAction: null,
      nextStep: "Resolver problemas",
      counts,
    };
  }

  if (hasWarnings) {
    return {
      id: counts.omittedFiles ? "ready_with_omitted" : "ready_with_warnings",
      tone: "warning",
      title: counts.omittedFiles ? "Lote preparado con archivos omitidos" : "Lote preparado con avisos",
      subtitle: `${summary} · ${countText(counts.nonBlockingWarnings, "aviso", "avisos")} no bloqueante${counts.nonBlockingWarnings === 1 ? "" : "s"}`,
      topSummary: compactHeaderStatusText(),
      primaryAction: { label: "Revisar avisos", action: "review-warnings", enabled: true },
      secondaryAction: isExportReady() ? { label: "Exportar igualmente", action: "start-export", enabled: true } : null,
      nextStep: "Revisar avisos",
      counts,
    };
  }

  return {
    id: "ready_clean",
    tone: "ready",
    title: "Listo para exportar",
    subtitle: `${summary} · ${output} · ${destination}`,
    topSummary: compactHeaderStatusText(),
    primaryAction: { label: `Exportar ${counts.exportableImages} imágenes`, action: "start-export", enabled: isExportReady() },
    secondaryAction: null,
    nextStep: `Exportar ${counts.exportableImages} imágenes`,
    counts,
  };
}

function readyBatchSummaryText(counts = batchCounts()) {
  const format = detectedFormatLabel(activeImages());
  if (counts.filesFound === null) {
    return "Leyendo archivos";
  }
  if (counts.filesFound > 0 || counts.exportableImages > 0) {
    return `${format} · ${counts.filesFound} archivos · ${counts.exportableImages} exportables`;
  }
  return `${format} · 0 exportables`;
}

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
    destinationValue: "_SALIDA_PRO",
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
      statusText: "No hay imágenes válidas",
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
        { level: "warning", title: "chaqueta_003.png", detail: "Vista renderizada con fallback." },
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

function selectImage(imageId) {
  const image = activeImages().find((item) => item.id === imageId);
  if (!image) {
    return;
  }
  rememberSelectedImage(image);
  clearTimers();
  state.selectedImageId = image.id;
  state.localOverride = hasCurrentImageOverride(image) || image.status === "adjusted";
  state.fitZoom = 100;
  resetViewerPan();
  if (image.source === "bridge") {
    void requestBridgePreview(image);
    return;
  }
  state.previewStatus = "loading";
  state.previewData = null;
  state.previewError = "";
  state.statusText = "Generando vista";
  render();
  setTimer(() => {
    state.previewStatus = image.status === "error" ? "error" : image.status === "warning" ? "warning" : "ready";
    state.statusText = state.previewStatus === "error" ? "Vista no disponible" : "Vista lista";
    render();
  }, 380);
}

function rememberSelectedImage(image) {
  if (image?.source === "bridge" && image.path) {
    writePersistentValue(STORAGE_KEYS.selectedImagePath, image.path);
  }
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

function imageOverrideKey(image = selectedImage()) {
  return image?.path || image?.id || "";
}

function clampLocalOverrideValue(key, value) {
  const [minimum, maximum] = localOverrideLimits[key] || [-100, 100];
  const parsed = Number(value);
  const numeric = Number.isFinite(parsed) ? Math.round(parsed) : 0;
  return Math.max(minimum, Math.min(maximum, numeric));
}

function normalizeLocalOverride(override = {}) {
  const normalized = {};
  localOverrideKeys.forEach((key) => {
    const value = clampLocalOverrideValue(key, override?.[key]);
    if (value) {
      normalized[key] = value;
    }
  });
  return normalized;
}

function currentImageOverride(image = selectedImage()) {
  const key = imageOverrideKey(image);
  return key ? normalizeLocalOverride(state.imageOverrides[key]) : {};
}

function hasCurrentImageOverride(image = selectedImage()) {
  return Object.keys(currentImageOverride(image)).length > 0;
}

function setCurrentImageOverrideValue(key, value) {
  const image = selectedImage();
  const overrideKey = imageOverrideKey(image);
  if (!image || !overrideKey || !localOverrideKeys.includes(key)) {
    return;
  }
  const next = {
    ...currentImageOverride(image),
    [key]: clampLocalOverrideValue(key, value),
  };
  const normalized = normalizeLocalOverride(next);
  if (Object.keys(normalized).length) {
    state.imageOverrides[overrideKey] = normalized;
  } else {
    delete state.imageOverrides[overrideKey];
  }
  state.localOverride = Object.keys(normalized).length > 0;
  state.statusText = state.localOverride ? "Ajuste local activo" : "Ajuste local quitado";
  refreshPreviewAfterSettingChange();
}

function resetCurrentImageOverride() {
  const key = imageOverrideKey();
  if (!key) {
    return;
  }
  delete state.imageOverrides[key];
  state.localOverride = false;
  state.statusText = "Ajuste local quitado";
  refreshPreviewAfterSettingChange();
}

function isViewerNavigationAvailable() {
  return Boolean(selectedImage()) && !["empty", "error", "loading"].includes(state.previewStatus);
}

function applyViewerPanDom() {
  const canvas = $("#preview-canvas");
  if (!canvas) {
    return;
  }
  canvas.style.setProperty("--canvas-pan-x", `${Math.round(state.panX)}px`);
  canvas.style.setProperty("--canvas-pan-y", `${Math.round(state.panY)}px`);
}

function resetViewerPan() {
  state.panX = 0;
  state.panY = 0;
  applyViewerPanDom();
}

function isAutoViewerMode(mode = state.fitMode) {
  return ["fit", "height", "width"].includes(mode);
}

function viewerModeLabel(mode = state.fitMode) {
  return VIEW_MODE_LABELS[mode] || VIEW_MODE_LABELS.manual;
}

function viewerModeClass(mode = state.fitMode) {
  if (mode === "height") {
    return "fit-height-mode";
  }
  if (mode === "width") {
    return "fit-width-mode";
  }
  return mode === "fit" ? "fit-mode" : "zoom-mode";
}

function currentViewerZoom() {
  return isAutoViewerMode() ? state.fitZoom : state.zoom;
}

function clampViewerZoom(value) {
  return Math.max(25, Math.min(320, Math.round(value)));
}

function setViewerZoom(nextZoom, anchorEvent = null) {
  const zoom = clampViewerZoom(nextZoom);
  const previousZoom = Math.max(1, currentViewerZoom());
  if (anchorEvent) {
    const canvas = $("#preview-canvas");
    const rect = canvas?.getBoundingClientRect();
    if (rect?.width && rect?.height) {
      const originX = anchorEvent.clientX - (rect.left + rect.width / 2);
      const originY = anchorEvent.clientY - (rect.top + rect.height / 2);
      const ratio = zoom / previousZoom;
      state.panX = originX - (originX - state.panX) * ratio;
      state.panY = originY - (originY - state.panY) * ratio;
    }
  }
  state.fitMode = "manual";
  state.zoom = zoom;
  state.statusText = zoom === 100 ? "Zoom 100%" : `Zoom ${zoom}%`;
  render();
}

function setViewerMode(mode) {
  if (!["fit", "height", "width"].includes(mode)) {
    return;
  }
  state.fitMode = mode;
  resetViewerPan();
  state.statusText = `Vista: ${viewerModeLabel(mode)}`;
  render();
}

function toggleViewerZoomMode() {
  if (!isViewerNavigationAvailable()) {
    return;
  }
  if (state.fitMode === "manual" && state.zoom === 100) {
    setViewerMode(DEFAULT_VIEW_MODE);
    return;
  }
  resetViewerPan();
  setViewerZoom(100);
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

function updatePresetCache(name, settings) {
  const normalized = normalizeSettings(settings);
  const bridgeIndex = state.bridgePresets.findIndex((preset) => preset.name === name);
  if (bridgeIndex >= 0) {
    state.bridgePresets[bridgeIndex] = {
      ...state.bridgePresets[bridgeIndex],
      settings: normalized,
    };
  }
  const preset = presetItemByName(name);
  if (preset) {
    preset.settings = normalized;
  }
  if (!mockPresets.includes(name) && state.bridgeMode !== "bridge") {
    mockPresets.push(name);
  }
  mockPresetSettings[name] = normalized;
}

function removePresetFromCache(name) {
  state.bridgePresets = state.bridgePresets.filter((preset) => preset.name !== name);
  const mockIndex = mockPresets.indexOf(name);
  if (mockIndex >= 0) {
    mockPresets.splice(mockIndex, 1);
  }
  delete mockPresetSettings[name];
  delete state.presetOutputSettings[name];
}

function applyPresetSettings(name, options = {}) {
  const preset = presetItemByName(name);
  if (!preset) {
    return false;
  }
  state.activePreset = preset.name;
  state.settings = normalizeSettings(preset.settings);
  if (state.presetOutputSettings[preset.name]) {
    Object.assign(state, state.presetOutputSettings[preset.name]);
  }
  state.presetDirty = false;
  state.presetSource = preset.category || "Salida";
  const advanced = $("#advanced-settings");
  if (advanced) {
    advanced.open = false;
  }
  state.statusText = options.statusText || `Ajuste: ${preset.name}`;
  if (options.refresh !== false) {
    refreshPreviewAfterSettingChange();
  }
  return true;
}

function resetActivePresetSettings() {
  if (applyPresetSettings(state.activePreset, { statusText: "Ajuste restaurado" })) {
    return;
  }
  state.settings = { ...defaultSettings };
  state.presetDirty = false;
  state.presetSource = "Salida";
  state.statusText = "Ajuste restaurado";
  refreshPreviewAfterSettingChange();
}

function markPresetDirty() {
  state.presetDirty = true;
  state.presetSource = "Modificado";
  refreshPreviewAfterSettingChange();
}

function refreshPreviewAfterSettingChange() {
  if (selectedImage()?.source === "bridge") {
    state.previewStatus = "loading";
    state.previewData = null;
    state.previewError = "";
    state.statusText = "Generando vista";
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
    state.statusText = "Generando vista";
    render();
    clearTimers();
    setTimer(() => {
      state.previewStatus = selectedImage()?.status === "warning" ? "warning" : "ready";
      state.statusText = "Vista lista";
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
    state.statusText = validationIssues()[0]?.title || "Configura salida";
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
        detail: "Elige una carpeta local antes de exportar.",
      }],
      statusText: "Elige una carpeta local",
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
    imageOverrides: state.imageOverrides,
    export: {
      format: state.format,
      size: state.size,
      background: state.background,
      destinationMode: state.destinationMode,
      destinationValue: state.destinationValue,
      outputFolderName: state.destinationMode === "source" ? state.destinationValue : "_SALIDA_PRO",
      customOutputPath: state.destinationMode === "custom" ? state.destinationValue : "",
      namingTemplate: state.naming,
      suffix: state.suffix,
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
  reviewWarnings();
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

function bridgeThumbnailUrl(path, size = 128) {
  if (!path) {
    return "";
  }
  return `${normalizedBridgeUrl()}/images/thumbnail?path=${encodeURIComponent(path)}&size=${encodeURIComponent(size)}`;
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
  state.statusText = "Generando vista";
  render();

  try {
    const response = await bridgeRequest("/preview/render", {
      method: "POST",
      body: JSON.stringify({
        imagePath: image.path,
        ...previewTargetSize(),
        settings: bridgePreviewSettings(),
        localOverride: currentImageOverride(image),
      }),
      timeoutMs: 20000,
    });

    if (isStalePreviewResponse(requestId, image)) {
      return;
    }

    state.previewData = previewResponseToData(response);
    state.previewStatus = response.warning ? "warning" : "ready";
    state.statusText = response.warning ? "Vista con aviso" : "Vista lista";
  } catch (error) {
    if (isStalePreviewResponse(requestId, image)) {
      return;
    }
    const message = bridgeErrorMessage(error);
    state.previewStatus = "error";
    state.previewData = null;
    state.previewError = message;
    state.statusText = "Vista no disponible";
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
    state.scanStatus = "Conexión local lista";
    if (state.batch === "none") {
      state.scanIssues = [];
    }
    state.statusText = "Listo";
    applyBridgePresets(presetPayload);
  } catch (error) {
    const message = bridgeErrorMessage(error);
    state.bridgeStatus = "disconnected";
    state.bridgeCapabilities = null;
    state.bridgeCapabilitiesSummary = "Sin comprobar";
    state.bridgeMessage = message;
    state.bridgeLastResponse = `error: ${message}`;
    state.scanStatus = "Conexión local no disponible";
    state.statusText = "Conexión local no disponible";
  }

  render();
}

async function pickBridgeFolder() {
  state.batchDetailOpen = false;
  state.bridgeMode = "bridge";
  state.bridgeStatus = "checking";
  state.bridgeMessage = "Abriendo selector";
  state.bridgeLastResponse = "Solicitando /folders/pick";
  state.scanStatus = "Elige una carpeta";
  state.statusText = "Elige una carpeta";
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
    persistBridgeScanPath();
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
    state.presetSource = "Sin ajustes";
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
  persistBridgeScanPath(folders[0]);

  clearTimers();
  thumbnailPreloads.clear();
  thumbnailFallbackQueue.length = 0;
  thumbnailFallbackInFlight.clear();
  clearBridgeExportPoll();
  Object.assign(state, {
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
    fitMode: DEFAULT_VIEW_MODE,
    fitZoom: 100,
    zoom: 100,
    panX: 0,
    panY: 0,
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
      body: JSON.stringify({ folders, imageOverrides: state.imageOverrides }),
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
      scanStatus: "Conexión local no disponible",
      scanIssues: [{ level: "error", title: "Conexión local no disponible", detail: message }],
      statusText: "No se pudo escanear",
    });
  }

  render();
}

function persistBridgeScanPath(path = parseFolderInput(state.bridgeScanPath)[0] || "") {
  writePersistentValue(STORAGE_KEYS.bridgeScanPath, path);
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
    const rememberedPath = readPersistentValue(STORAGE_KEYS.selectedImagePath);
    const rememberedImage = rememberedPath
      ? state.realImages.find((image) => image.path === rememberedPath)
      : null;
    const selectedImage = rememberedImage || state.realImages[0];
    state.batch = "ready";
    state.selectedImageId = selectedImage.id;
    state.localOverride = hasCurrentImageOverride(selectedImage) || selectedImage.status === "adjusted";
    rememberSelectedImage(selectedImage);
    state.previewStatus = "loading";
    state.previewData = null;
    state.previewError = "";
    state.fitMode = DEFAULT_VIEW_MODE;
    state.fitZoom = 100;
    state.zoom = 100;
    state.panX = 0;
    state.panY = 0;
    state.exportStatus = "blocked";
    state.scanStatus = state.scanIssues.length
      ? `Escaneo completado con ${state.scanIssues.length} aviso${state.scanIssues.length === 1 ? "" : "s"}`
      : `${state.realImages.length} imágenes encontradas`;
    state.statusText = "Generando vista";
    void requestBridgePreview(selectedImage);
    return;
  }

  state.batch = "empty";
  state.selectedImageId = null;
  state.previewStatus = "empty";
  state.previewData = null;
  state.previewError = "";
  state.exportStatus = "blocked";
  state.scanStatus = state.scanIssues.length ? state.scanIssues[0].detail : "No se encontraron PNG ni JPG";
  state.statusText = state.scanIssues.length ? "Revisa carpeta" : "No hay imágenes compatibles";
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
    return "No se encontraron PNG ni JPG";
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
        ? `${count} imágenes · ${omittedCount} omitidas`
        : count ? `${count} imágenes` : "No se encontraron imágenes",
    filesFound: Number(folder.filesFound) || count,
    omittedCount,
  };
}

function bridgeImageToItem(image, folderIndex, imageIndex) {
  const suffix = String(image.suffix || "").replace(".", "").toUpperCase() || "PNG";
  const detail = `${suffix} · ${formatBytes(image.sizeBytes)}`;
  return {
    id: `bridge-${folderIndex}-${imageIndex}`,
    folderId: `bridge-folder-${folderIndex}`,
    name: image.name,
    detail,
    status: image.hasLocalOverride ? "adjusted" : "ready",
    exportable: true,
    source: "bridge",
    path: image.path,
    thumbnailUrl: bridgeThumbnailUrl(image.path),
    originalUrl: "",
  };
}

function basename(path) {
  return String(path || "").split(/[\\/]/).filter(Boolean).pop() || "";
}

function imageFileStem(name) {
  return basename(name).replace(/\.[^.\\/]+$/, "") || basename(name) || "Imagen";
}

function imageFileType(image) {
  const fromName = String(image?.name || "").split(".").pop();
  if (fromName && fromName !== image?.name) {
    return fromName.toUpperCase();
  }
  const fromDetail = String(image?.detail || "").split("·")[0]?.trim();
  return fromDetail || state.format || "Imagen";
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
    return "La conexión local no responde";
  }
  return error?.message || "Conexión local no disponible";
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
  const visible = getVisibleAppState();
  runVisibleAction(visible.primaryAction?.action);
}

function runVisibleAction(action) {
  if (!action) {
    return;
  }
  if (action === "pick-bridge-folder") {
    void pickBridgeFolder();
  } else if (action === "review-warnings") {
    reviewWarnings();
  } else if (action === "review-output") {
    reviewOutput();
  } else if (action === "start-export") {
    startExport();
  } else if (action === "open-output") {
    openOutputFolder();
  } else if (action === "stop-export") {
    stopExport();
  }
}

function reviewWarnings() {
  const counts = batchCounts();
  const blockingCount = preflightCounts().errors;
  state.inspectorTab = "warnings";
  if (counts.warningImages || counts.nonExportableImages) {
    state.filter = "warnings";
  } else if (counts.omittedFiles) {
    state.filter = "omitted";
  }
  const issueCount = counts.nonBlockingWarnings + blockingCount;
  state.statusText = issueCount
    ? `${countText(issueCount, "aviso", "avisos")} para revisar`
    : "Sin avisos";
  render();
}

function reviewOutput() {
  state.inspectorTab = "output";
  state.statusText = firstBlockingIssue()?.title || "Revisa salida";
  render();
}

function outputDestinationToOpen() {
  if (state.exportDestinations.length) {
    return state.exportDestinations[0];
  }
  if (Array.isArray(state.exportResult?.destinations) && state.exportResult.destinations.length) {
    return state.exportResult.destinations[0];
  }
  return "";
}

function openOutputFolder() {
  const destination = outputDestinationToOpen();
  if (!destination) {
    state.statusText = "No hay carpeta de salida registrada";
    render();
    return;
  }
  const opened = window.open(pathToFileUrl(destination), "_blank", "noopener");
  state.statusText = opened ? "Carpeta de salida abierta" : "No se pudo abrir la carpeta de salida";
  render();
}

function pathToFileUrl(path) {
  const normalized = String(path || "").replaceAll("\\", "/");
  if (/^[a-z]:\//i.test(normalized)) {
    return `file:///${encodeURI(normalized)}`;
  }
  if (normalized.startsWith("/")) {
    return `file://${encodeURI(normalized)}`;
  }
  return encodeURI(normalized);
}

function statusMode() {
  if (state.batch === "none" && state.bridgeStatus === "idle") {
    return "";
  }
  if (state.exportStatus === "failed" || state.previewStatus === "error" || state.scanIssues.some((issue) => issue.level === "error")) {
    return "error";
  }
  if (state.exportStatus === "running" || state.previewStatus === "loading" || state.batch === "scanning") {
    return "busy";
  }
  if (state.bridgeMode === "bridge" && state.bridgeStatus !== "connected") {
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
  renderBatchDetail();
  renderAppSettings();
  renderInspector();
  renderFooter();
  syncOpenInspectorDisclosureHeights();
  keepActiveThumbnailVisible();
}

function syncOpenInspectorDisclosureHeights() {
  window.requestAnimationFrame(() => {
    $$(".settings-panel details.inspector-disclosure[open]").forEach((details) => {
      if (!details.classList.contains("is-closing")) {
        setInspectorDisclosureHeight(details);
      }
    });
  });
}

function inspectorDisclosureBody(details) {
  return details?.querySelector?.(".inspector-disclosure__body") || null;
}

function setInspectorDisclosureHeight(details, height = null) {
  const body = inspectorDisclosureBody(details);
  if (!body) {
    return;
  }
  let nextHeight = height;
  if (nextHeight === null) {
    const wasOpening = details.classList.contains("is-opening");
    const wasClosing = details.classList.contains("is-closing");
    if (wasOpening || wasClosing) {
      details.classList.remove("is-opening", "is-closing");
    }
    const previousHeight = body.style.getPropertyValue("--inspector-disclosure-height");
    body.style.setProperty("--inspector-disclosure-height", "none");
    const bodyRect = body.getBoundingClientRect();
    const bodyStyle = getComputedStyle(body);
    const paddingBottom = Number.parseFloat(bodyStyle.paddingBottom) || 0;
    const childBottom = Array.from(body.children).reduce((max, child) => {
      const rect = child.getBoundingClientRect();
      return Math.max(max, rect.bottom - bodyRect.top);
    }, 0);
    nextHeight = Math.max(body.scrollHeight, Math.ceil(childBottom + paddingBottom));
    if (previousHeight) {
      body.style.setProperty("--inspector-disclosure-height", previousHeight);
    } else {
      body.style.removeProperty("--inspector-disclosure-height");
    }
    if (wasOpening) {
      details.classList.add("is-opening");
    }
    if (wasClosing) {
      details.classList.add("is-closing");
    }
  }
  body.style.setProperty("--inspector-disclosure-height", `${Math.max(0, Math.round(nextHeight))}px`);
}

function restoreInspectorScroll(panel, scrollTop = inspectorScrollTopBeforeToggle) {
  if (!panel) {
    return;
  }
  const restore = () => {
    panel.scrollTop = scrollTop;
  };
  restore();
  window.requestAnimationFrame(() => {
    restore();
    window.requestAnimationFrame(restore);
    window.setTimeout(restore, 0);
    window.setTimeout(restore, INSPECTOR_DISCLOSURE_MS);
  });
}

function closeInspectorDisclosure(details, panel = $(".settings-panel"), scrollTop = inspectorScrollTopBeforeToggle) {
  if (!details?.open || details.classList.contains("is-closing")) {
    return;
  }
  const previousTimer = inspectorDisclosureTimers.get(details);
  if (previousTimer) {
    window.clearTimeout(previousTimer);
  }

  setInspectorDisclosureHeight(details);
  details.classList.remove("is-opening", "is-open");
  details.classList.add("is-closing");
  window.requestAnimationFrame(() => {
    setInspectorDisclosureHeight(details, 0);
    restoreInspectorScroll(panel, scrollTop);
  });

  const timer = window.setTimeout(() => {
    details.open = false;
    details.classList.remove("is-closing");
    const body = inspectorDisclosureBody(details);
    body?.style.removeProperty("--inspector-disclosure-height");
    inspectorDisclosureTimers.delete(details);
    restoreInspectorScroll(panel, scrollTop);
  }, INSPECTOR_DISCLOSURE_MS);
  inspectorDisclosureTimers.set(details, timer);
}

function openInspectorDisclosure(details, panel = $(".settings-panel"), scrollTop = inspectorScrollTopBeforeToggle) {
  if (!details) {
    return;
  }
  $$(".settings-panel details.inspector-disclosure").forEach((other) => {
    if (other !== details && other.open) {
      closeInspectorDisclosure(other, panel, scrollTop);
    }
  });

  const previousTimer = inspectorDisclosureTimers.get(details);
  if (previousTimer) {
    window.clearTimeout(previousTimer);
    inspectorDisclosureTimers.delete(details);
  }
  details.open = true;
  details.classList.remove("is-closing", "is-open");
  details.classList.add("is-opening");
  setInspectorDisclosureHeight(details, 0);
  restoreInspectorScroll(panel, scrollTop);
  window.requestAnimationFrame(() => {
    setInspectorDisclosureHeight(details);
    restoreInspectorScroll(panel, scrollTop);
  });
  const timer = window.setTimeout(() => {
    details.classList.remove("is-opening");
    details.classList.add("is-open");
    const body = inspectorDisclosureBody(details);
    body?.style.setProperty("--inspector-disclosure-height", "none");
    inspectorDisclosureTimers.delete(details);
    restoreInspectorScroll(panel, scrollTop);
  }, INSPECTOR_DISCLOSURE_MS);
  inspectorDisclosureTimers.set(details, timer);
}

function toggleInspectorDisclosure(details) {
  const panel = $(".settings-panel");
  inspectorScrollTopBeforeToggle = panel?.scrollTop || 0;
  const shouldOpen = !details.open || details.classList.contains("is-closing");
  if (shouldOpen) {
    openInspectorDisclosure(details, panel, inspectorScrollTopBeforeToggle);
  } else {
    closeInspectorDisclosure(details, panel, inspectorScrollTopBeforeToggle);
  }
}

function renderShell() {
  const shell = $(".app-shell");
  const gallery = $(".gallery-column");
  const derived = uiState();
  const visible = getVisibleAppState();
  const hasStatusFooter = state.batch === "scanning"
    || state.exportStatus === "running"
    || state.exportStatus === "completed"
    || state.exportStatus === "partial"
    || state.exportStatus === "failed";
  shell.classList.toggle("dev-mode", devMode);
  shell.classList.toggle("no-batch", state.batch === "none");
  shell.classList.toggle("empty-batch", state.batch === "empty");
  shell.classList.toggle("has-batch", derived.hasBatchContext);
  shell.classList.toggle("has-selected-image", derived.hasSelectedImage);
  shell.classList.toggle("no-selected-image", !derived.hasSelectedImage);
  shell.classList.toggle("can-export", derived.canExport);
  shell.classList.toggle("is-exporting", derived.isExporting);
  shell.classList.toggle("is-scanning", state.batch === "scanning");
  shell.classList.toggle("has-status-footer", hasStatusFooter);
  shell.classList.toggle("export-completed", ["completed", "partial", "failed"].includes(state.exportStatus));
  shell.classList.toggle("inspector-collapsed", state.inspectorCollapsed);
  shell.dataset.uiState = visible.id;
  if (gallery) {
    gallery.dataset.galleryView = state.galleryView;
  }
}

function keepActiveThumbnailVisible() {
  window.requestAnimationFrame(() => {
    const active = $("#image-list .image-item.active");
    if (!active) {
      return;
    }
    active.scrollIntoView({ block: "nearest", inline: "center" });
  });
}

function renderDevelopmentStatus() {
  $("#dev-mode-label").textContent = state.bridgeMode === "bridge" ? "Bridge local" : "Mock";
  $("#dev-bridge-label").textContent = bridgeStatusLabel();
  $("#dev-bridge-url-label").textContent = state.bridgeUrl || defaultBridgeUrl;
  $("#dev-last-response").textContent = state.bridgeLastResponse;
  updatePreviewDebugPanel();
}

function updatePreviewDebugPanel() {
  const image = selectedImage();
  const previewImage = $("#preview-canvas .preview-image");
  const thumbSrc = image ? imageThumbnailSrc(image) : "";
  const rendered = previewImage?.getBoundingClientRect();
  const naturalWidth = Number(previewImage?.naturalWidth || state.previewData?.width || 0);
  const naturalHeight = Number(previewImage?.naturalHeight || state.previewData?.height || 0);
  const stats = thumbnailStats();

  setDebugText("debug-original-url", image?.originalUrl || image?.path || "-");
  setDebugText("debug-preview-url", state.previewData?.src ? debugUrlLabel(state.previewData.src) : "-");
  setDebugText("debug-thumbnail-url", thumbSrc || "-");
  setDebugText("debug-natural-size", naturalWidth && naturalHeight ? `${naturalWidth} x ${naturalHeight}` : "-");
  setDebugText("debug-rendered-size", rendered ? `${Math.round(rendered.width)} x ${Math.round(rendered.height)}` : "-");
  setDebugText("debug-load-status", state.previewStatus || "-");
  setDebugText("debug-preview-error", state.previewError || "-");
  setDebugText("debug-thumbnail-stats", `${stats.loaded}/${stats.total} cargadas · ${stats.failed} fallidas · ${stats.pending} pendientes`);
}

function setDebugText(id, value) {
  const target = $(`#${id}`);
  if (target) {
    target.textContent = value;
    target.title = value;
  }
}

function debugUrlLabel(value) {
  const text = String(value || "");
  if (text.startsWith("data:")) {
    const comma = text.indexOf(",");
    return comma > 0 ? `${text.slice(0, comma)}...` : "data URL";
  }
  return text.length > 120 ? `${text.slice(0, 117)}...` : text;
}

function thumbnailStats() {
  const images = activeImages();
  const total = images.length;
  let loaded = 0;
  let failed = 0;
  images.forEach((image) => {
    const src = imageThumbnailSrc(image);
    const status = state.thumbnailStatus[image.id];
    if (status?.src === src && status.status === "loaded") {
      loaded += 1;
    } else if (status?.src === src && status.status === "error") {
      failed += 1;
    }
  });
  return {
    total,
    loaded,
    failed,
    pending: Math.max(0, total - loaded - failed),
  };
}

function renderTop() {
  const visible = getVisibleAppState();
  $("#demo-scenario").value = scenarioLabels[state.scenario] ? state.scenario : "batch-ready";
  $("#app-mode").value = state.bridgeMode;
  $("#bridge-url").value = state.bridgeUrl;
  $("#active-batch-label").textContent = visible.title;
  $("#top-status-text").textContent = visible.topSummary || compactHeaderStatusText();
  $("#top-status-text").title = visible.subtitle || visible.topSummary || "";
  $("#status-dot").className = `status-dot ${statusMode()}`;
  const detailButton = $("[data-action='open-batch-detail']");
  if (detailButton) {
    detailButton.title = state.batch === "none" ? "Ver configuración inicial" : "Ver detalle del lote";
  }
  const preflight = $("#top-preflight-status");
  if (preflight) {
    preflight.textContent = preflightStatusLabel();
    preflight.className = `preflight-chip ${preflightStatusClass()}`;
  }
  const secondary = $("#top-secondary-action");
  if (secondary) {
    const action = visible.secondaryAction;
    secondary.hidden = !action;
    secondary.disabled = !action?.enabled;
    secondary.textContent = action?.label || "";
    secondary.dataset.stateAction = action?.action || "";
    secondary.title = action?.label || "";
  }
}

function compactHeaderStatusText() {
  const counts = batchCounts();
  if (state.exportStatus === "running") {
    const total = counts.exportableImages;
    return state.paused ? `Pausado · ${state.processed}/${total}` : `Exportando ${state.processed}/${total}`;
  }
  if (state.exportStatus === "completed" || state.exportStatus === "partial") {
    const processed = Number(state.exportResult?.processed ?? state.processed ?? counts.exportableImages);
    const total = Number(state.exportResult?.total ?? counts.exportableImages);
    return state.exportStatus === "partial" ? `Exportado con avisos · ${processed}/${total}` : `Exportado · ${processed}/${total}`;
  }
  if (state.exportStatus === "failed") {
    return "Exportación fallida";
  }
  if (state.batch === "scanning") {
    return "Escaneando...";
  }
  if (state.batch === "none") {
    return "Sin lote";
  }
  if (state.batch === "empty") {
    const files = counts.filesFound || 0;
    const omitted = counts.omittedFiles || 0;
    return omitted ? `${files} archivos · 0 exportables · ${omitted} omitidos` : "0 exportables";
  }
  const parts = [
    detectedFormatLabel(activeImages()),
    `${counts.filesFound || activeImages().length} archivos`,
    `${counts.exportableImages} exportables`,
  ];
  if (counts.nonBlockingWarnings) {
    parts.push(`${counts.nonBlockingWarnings} aviso${counts.nonBlockingWarnings === 1 ? "" : "s"}`);
  }
  return parts.join(" · ");
}

function topStatusText() {
  const images = activeImages();
  const warnings = visibleWarningCount();
  if (state.batch === "scanning") {
    return "Escaneando carpeta";
  }
  if (state.batch === "none") {
    return "Sin lote";
  }
  if (state.batch === "empty") {
    return "No hay imágenes válidas";
  }
  if (state.exportStatus === "running") {
    const total = exportableImages().length;
    return state.paused ? `Pausado · ${state.processed}/${total}` : `Exportando ${state.processed}/${total}`;
  }
  if (state.batch === "ready") {
    return compactHeaderStatusText();
  }
  if (state.bridgeMode === "bridge" && state.bridgeStatus === "disconnected") {
    return "Conexión local no disponible";
  }
  return state.statusText;
}

function preflightStatusLabel() {
  if (state.exportStatus === "running") {
    return state.paused ? "Salida pausada" : "Exportando";
  }
  if (state.exportStatus === "completed") {
    return "Salida completada";
  }
  if (state.exportStatus === "partial") {
    return "Avisos";
  }
  if (state.exportStatus === "failed") {
    return "Revisar";
  }
  const ready = isExportReady();
  const counts = preflightCounts();
  if (!ready && counts.errors > 0) {
    return "Revisar";
  }
  if (!ready) {
    return "Pendiente";
  }
  if (counts.warnings > 0) {
    return `${counts.warnings} aviso${counts.warnings === 1 ? "" : "s"}`;
  }
  return "Listo";
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
  sourcePanel.className = `source-panel batch-rail__source ${sourcePanelClass()}`;
  sourceBadge.className = `state-chip ${isBridgeBatch() ? "bridge" : isMockBatch() ? "ready" : ""}`;
  sourceBadge.textContent = sourceLabel();
  $("#source-title").textContent = hasBatch() || state.batch === "empty" ? "Entrada" : "Seleccionar carpeta";
  const sourceName = $("#source-folder-name");
  if (sourceName) {
    sourceName.textContent = sourceFolderName();
    sourceName.title = sourceFolderName();
  }
  $("#scan-status").textContent = compactScanStatus();
  $("#bridge-scan-path").value = state.bridgeScanPath;
  $("#bridge-pick-folder").textContent = hasBatch() || state.batch === "empty" ? "Cambiar" : "Seleccionar carpeta";
  $("#bridge-scan-folder").textContent = hasBatch() || state.batch === "empty" ? "↻" : "Escanear";
  $("#bridge-scan-folder").title = hasBatch() || state.batch === "empty" ? "Actualizar lote" : "Escanear carpeta";
  $("#bridge-scan-folder").setAttribute("aria-label", $("#bridge-scan-folder").title);
  $("#bridge-pick-folder").disabled = state.bridgeStatus === "checking" || state.batch === "scanning";
  $("#bridge-scan-folder").disabled = state.bridgeStatus === "checking" || state.batch === "scanning";
  $("#bridge-last-response").textContent = state.bridgeLastResponse;
  $("#bridge-capabilities").textContent = state.bridgeCapabilitiesSummary;
  message.textContent = normalBridgeMessage();
  message.className = `bridge-message ${state.bridgeStatus === "connected" ? "ready" : state.bridgeStatus === "disconnected" ? "error" : ""}`;
  renderBatchSummary();
}

function compactScanStatus() {
  const counts = batchCounts();
  if (state.batch === "ready") {
    return counts.omittedFiles
      ? `${counts.exportableImages} exportables · ${countText(counts.omittedFiles, "omitido", "omitidos")}`
      : `${counts.exportableImages} exportables`;
  }
  if (state.batch === "empty") {
    return counts.omittedFiles ? `0 exportables · ${countText(counts.omittedFiles, "omitido", "omitidos")}` : "Sin imágenes compatibles";
  }
  if (state.batch === "scanning") {
    return "Leyendo imágenes";
  }
  return state.scanStatus || "Sin lote";
}

function sourceFolderName() {
  if (state.batch === "scanning") {
    return basename(parseFolderInput(state.bridgeScanPath)[0]) || "Carpeta";
  }
  const folders = state.batch === "ready"
    ? activeFolders()
    : state.batch === "empty" && isBridgeBatch()
      ? state.realFolders
      : [];
  if (folders.length === 1) {
    return folders[0].name || "Carpeta actual";
  }
  if (folders.length > 1) {
    return `${folders.length} carpetas`;
  }
  const persistedPath = parseFolderInput(state.bridgeScanPath)[0];
  if (persistedPath) {
    return basename(persistedPath) || "Carpeta actual";
  }
  return hasBatch() || state.batch === "empty" ? "Carpeta actual" : "Pendiente";
}

function normalBridgeMessage() {
  if (state.bridgeMode !== "bridge") {
    return devMode ? "Modo revisión activo." : "Elige una carpeta local.";
  }
  if (state.bridgeStatus === "connected") {
    return "Listo.";
  }
  if (state.bridgeStatus === "checking") {
    return "Comprobando conexión.";
  }
  if (state.bridgeStatus === "disconnected") {
    return "Conexión local no disponible.";
  }
  return "Elige una carpeta local.";
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
    return "Local";
  }
  if (isMockBatch()) {
    return devMode ? "Demo" : "Local";
  }
  return state.bridgeMode === "bridge" || !devMode ? "Local" : "Demo";
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
  const visible = getVisibleAppState();
  const counts = visible.counts;
  const diagnostics = state.scanDiagnostics || emptyScanDiagnostics();
  const tone = batchSummaryToneFromVisible(visible);
  const sourcePath = state.batch === "ready"
    ? activeFolders()[0]?.path || state.bridgeScanPath
    : state.batch === "empty" && state.realFolders.length
      ? state.realFolders[0]?.path || state.bridgeScanPath
      : state.bridgeScanPath;
  const filesLabel = counts.filesFound === null ? "Leyendo" : counts.filesFound;
  const validLabel = counts.validImages === null ? "Leyendo" : counts.validImages;
  const outputLine = batchOutputLine();
  const destinationLine = batchDestinationLine();
  const warningsLabel = counts.nonBlockingWarnings ? countText(counts.nonBlockingWarnings, "aviso", "avisos") : "Sin avisos";

  summary.innerHTML = `
    <div class="batch-summary-card ${tone}">
      <div class="batch-summary-section">
        <span class="batch-rail__section-title">Entrada</span>
        <strong title="${escapeHtml(sourcePath || visible.subtitle)}">${escapeHtml(sourceFolderName())}</strong>
        <small title="${escapeHtml(sourcePath || visible.subtitle)}">${escapeHtml(sourceInputDetail(filesLabel, validLabel))}</small>
      </div>

      <div class="batch-metric-grid" aria-label="Datos del lote">
        ${batchMetricHtml("Archivos encontrados", filesLabel)}
        ${batchMetricHtml("Imágenes válidas", validLabel)}
        ${batchMetricHtml("Imágenes exportables", counts.exportableImages)}
        ${batchMetricHtml("Archivos omitidos", counts.omittedFiles)}
      </div>

      <div class="batch-summary-section">
        <span class="batch-rail__section-title">Estado del lote</span>
        <strong>${escapeHtml(visible.title)}</strong>
        <small title="${escapeHtml(visible.subtitle)}">${escapeHtml(visible.subtitle)}</small>
      </div>

      <div class="batch-summary-lines batch-summary-lines--compact">
        <div class="batch-summary__line">
          <span>Listas</span>
          <strong>${escapeHtml(counts.readyImages)}</strong>
        </div>
        <div class="batch-summary__line">
          <span>Con aviso</span>
          <strong>${escapeHtml(counts.warningImages)}</strong>
        </div>
        <div class="batch-summary__line">
          <span>Bloqueos</span>
          <strong>${escapeHtml(counts.blockingErrors)}</strong>
        </div>
      </div>

      <div class="batch-summary-section">
        <span class="batch-rail__section-title">Salida</span>
        <strong title="${escapeHtml(outputLine)}">${escapeHtml(outputProfileDisplayName())}</strong>
        <small title="${escapeHtml(`${outputLine} · ${destinationLine}`)}">${escapeHtml(`${outputLine} · ${destinationLine}`)}</small>
      </div>

      <div class="batch-summary-lines">
        <div class="batch-summary__line">
          <span>Nombre de archivo</span>
          <strong title="${escapeHtml(namingExample())}">${escapeHtml(namingHumanLabel())}</strong>
        </div>
        <div class="batch-summary__line">
          <span>Avisos</span>
          <strong>${escapeHtml(warningsLabel)}</strong>
        </div>
      </div>

      <div class="batch-next">
        <span>Siguiente</span>
        <strong>${escapeHtml(visible.nextStep)}</strong>
      </div>
      ${diagnostics.totalOmitted || counts.blockingErrors ? diagnosticsHtml(diagnostics) : `<div class="diagnostic-ok">${counts.nonBlockingWarnings ? "Avisos en la galería" : "Sin avisos"}</div>`}
    </div>
  `;
}

function sourceInputDetail(filesLabel, validLabel) {
  if (state.batch === "none") {
    return "Pendiente";
  }
  if (state.batch === "scanning") {
    return "Leyendo imágenes";
  }
  return `${filesLabel} archivos encontrados · ${validLabel} imágenes válidas`;
}

function batchSummaryToneFromVisible(visible) {
  if (visible.tone === "error") {
    return "is-error";
  }
  if (visible.tone === "warning") {
    return "is-warning";
  }
  if (visible.tone === "busy") {
    return "is-busy";
  }
  if (visible.tone === "ready") {
    return "is-ready";
  }
  return "is-idle";
}

function batchMetricHtml(label, value) {
  return `
    <div class="batch-metric">
      <span>${escapeHtml(label)}</span>
      <strong title="${escapeHtml(value)}">${escapeHtml(value)}</strong>
    </div>
  `;
}

function batchOutputLine() {
  return `${state.format} · ${state.size.replace("x", " × ")} · ${batchBackgroundLabel(state.background)}`;
}

function batchBackgroundLabel(value) {
  if (value === "transparent") {
    return "Transparente";
  }
  if (value === "white") {
    return "Blanco";
  }
  return "Gris claro · RGB 230";
}

function batchDestinationLine() {
  if (state.destinationMode === "custom") {
    return state.destinationValue || "Sin destino";
  }
  return state.destinationValue ? `Junto al origen · ${state.destinationValue}` : "Junto al origen";
}

function diagnosticsHtml(diagnostics) {
  const open = state.scanIssues.some((issue) => issue.level === "error") ? " open" : "";
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
    <details class="batch-diagnostics"${open}>
      <summary>${escapeHtml(diagnostics.totalOmitted ? "Ver detalle técnico" : "Detalle técnico")}</summary>
      <div class="diagnostic-reasons">${reasonRows}</div>
      ${sampleRows ? `<ul>${sampleRows}</ul>` : ""}
    </details>
  `;
}

function renderBatchDetail() {
  const modal = $("#batch-detail-modal");
  if (!modal) {
    return;
  }
  modal.classList.toggle("is-hidden", !state.batchDetailOpen);
  modal.setAttribute("aria-hidden", state.batchDetailOpen ? "false" : "true");
  if (!state.batchDetailOpen) {
    return;
  }
  const body = $("#batch-detail-body");
  if (body) {
    body.innerHTML = batchDetailHtml();
  }
}

function batchDetailHtml() {
  const counts = batchCounts();
  const diagnostics = state.scanDiagnostics || emptyScanDiagnostics();
  const sourcePath = state.batch === "ready"
    ? activeFolders()[0]?.path || state.bridgeScanPath
    : state.batch === "empty" && state.realFolders.length
      ? state.realFolders[0]?.path || state.bridgeScanPath
      : state.bridgeScanPath;
  const files = counts.filesFound === null ? "Leyendo" : counts.filesFound;
  const valid = counts.validImages === null ? "Leyendo" : counts.validImages;
  const issueRowsHtml = issueRows().slice(0, 8).map((row) => `
    <div class="batch-detail-problem ${row.level === "error" ? "error" : "warning"}">
      <strong title="${escapeHtml(row.path || row.title)}">${escapeHtml(row.title)}</strong>
      <span>${escapeHtml(row.detail || "Revisar")}</span>
    </div>
  `).join("");
  const reasonRows = Object.entries(diagnostics.omittedByReason || {}).map(([reason, count]) => `
    <div class="batch-detail-row">
      <span>${escapeHtml(omissionReasonLabel(reason))}</span>
      <strong>${escapeHtml(count)}</strong>
    </div>
  `).join("");

  return `
    <div class="batch-detail-grid">
      <section class="batch-detail-section">
        <h3>Entrada</h3>
        ${batchDetailRowHtml("Tipo", sourceLabel())}
        ${batchDetailRowHtml("Carpeta", sourceFolderName(), sourcePath)}
        ${batchDetailRowHtml("Ruta", sourcePath || "Pendiente", sourcePath)}
      </section>

      <section class="batch-detail-section">
        <h3>Conteo</h3>
        ${batchDetailRowHtml("Archivos encontrados", files)}
        ${batchDetailRowHtml("Imágenes válidas", valid)}
        ${batchDetailRowHtml("Exportables", counts.exportableImages)}
        ${batchDetailRowHtml("Listas", counts.readyImages)}
        ${batchDetailRowHtml("Avisos", counts.warningImages)}
        ${batchDetailRowHtml("Omitidas", counts.omittedFiles)}
        ${batchDetailRowHtml("Bloqueos", counts.blockingErrors)}
      </section>

      <section class="batch-detail-section">
        <h3>Salida</h3>
        ${batchDetailRowHtml("Formato activo", outputProfileDisplayName())}
        ${batchDetailRowHtml("Archivo", state.format)}
        ${batchDetailRowHtml("Tamaño", outputSizeDisplay())}
        ${batchDetailRowHtml("Fondo", backgroundLabel(state.background))}
        ${batchDetailRowHtml("Carpeta de salida", batchDestinationLine())}
        ${batchDetailRowHtml("Nombre de archivo", namingHumanLabel())}
      </section>

      <section class="batch-detail-section">
        <h3>Avisos</h3>
        ${issueRowsHtml || '<span class="batch-detail-muted">Sin avisos.</span>'}
        ${reasonRows ? `<div class="batch-detail-reasons">${reasonRows}</div>` : ""}
      </section>
    </div>
  `;
}

function batchDetailRowHtml(label, value, title = "") {
  const text = value === null || value === undefined || value === "" ? "Pendiente" : String(value);
  return `
    <div class="batch-detail-row">
      <span>${escapeHtml(label)}</span>
      <strong title="${escapeHtml(title || text)}">${escapeHtml(text)}</strong>
    </div>
  `;
}

function pluralizeCount(count, singular) {
  const value = Number(count) || 0;
  const irregular = {
    imagen: "imágenes",
    correcta: "correctas",
    lista: "listas",
  };
  const plural = irregular[singular] || (singular.endsWith("s") ? singular : `${singular}s`);
  return `${value} ${value === 1 ? singular : plural}`;
}

function bridgeStatusClass() {
  if (state.bridgeMode !== "bridge" && devMode) {
    return "idle";
  }
  return state.bridgeStatus;
}

function bridgeStatusLabel() {
  if (state.bridgeMode !== "bridge" && devMode) {
    return "Demo";
  }
  if (state.bridgeStatus === "connected") {
    return "Listo";
  }
  if (state.bridgeStatus === "checking") {
    return "Comprobando";
  }
  if (state.bridgeStatus === "disconnected") {
    return "Sin conexión local";
  }
  return "Pendiente";
}

function renderBatch() {
  const images = activeImages();
  const adjusted = images.filter((image) => image.status === "adjusted").length;
  const valid = images.filter((image) => image.status === "ready" || image.status === "adjusted").length;
  const warnings = images.filter((image) => image.status === "warning").length;
  const errors = images.filter((image) => image.status === "error" || exportItemState(image)?.status === "error").length;
  const omitted = Number(state.scanDiagnostics?.totalOmitted || 0);
  const warningCount = omitted + warnings + errors;
  const filmstripCount = $("#filmstrip-count");
  $("#image-search").value = state.search;
  updateBatchSearchClear();
  renderGalleryViewButtons();

  if (state.batch === "none") {
    $("#batch-count").textContent = "Sin lote";
    setBatchPill("Sin carpeta", "muted");
    setGalleryTitle(0);
    $("#batch-visible-count").textContent = "";
    $("#folder-list").innerHTML = "";
    $("#image-list").innerHTML = "";
    $("#batch-empty-note").innerHTML = "";
    if (filmstripCount) {
      filmstripCount.textContent = "Sin lote";
    }
    renderFilterButtons();
    return;
  }

  if (state.batch === "scanning") {
    $("#batch-count").textContent = "Escaneando";
    setBatchPill("Escaneando", "active");
    setGalleryTitle(0);
    $("#batch-visible-count").textContent = "";
    $("#folder-list").innerHTML = folderItemHtml({
      id: "scan",
      name: isBridgeBatch() || !devMode ? basename(parseFolderInput(state.bridgeScanPath)[0]) || "Ruta" : "Camisetas Mayo",
      path: state.bridgeScanPath,
      detail: "Leyendo imágenes",
      count: "...",
      status: "ready",
    });
    $("#image-list").innerHTML = "";
    $("#batch-empty-note").innerHTML = "";
    if (filmstripCount) {
      filmstripCount.textContent = "Escaneando";
    }
    renderFilterButtons();
    return;
  }

  if (state.batch === "empty") {
    const emptyFolders = isBridgeBatch() && state.realFolders.length
      ? state.realFolders
      : [{
          id: "empty",
          name: "Carpeta vacía",
          detail: "No hay imágenes válidas",
          count: "0",
          status: "empty",
        }];
    $("#batch-count").textContent = "Sin imágenes";
    setBatchPill(
      state.scanDiagnostics.totalOmitted
        ? `${state.scanDiagnostics.totalOmitted} omitida${state.scanDiagnostics.totalOmitted === 1 ? "" : "s"}`
        : "Sin imágenes",
      state.scanDiagnostics.totalOmitted ? "warning" : "muted"
    );
    setGalleryTitle(0);
    $("#batch-visible-count").textContent = "";
    $("#folder-list").innerHTML = emptyFolders.map(folderItemHtml).join("");
    $("#image-list").innerHTML = "";
    $("#batch-empty-note").innerHTML = emptyBatchNoteHtml();
    if (filmstripCount) {
      filmstripCount.textContent = "Sin imágenes";
    }
    renderFilterButtons();
    return;
  }

  const exportable = exportableImages().length;
  $("#batch-count").textContent = exportable ? `${exportable} exportables` : "Sin exportables";
  setBatchPill(
    warningCount
      ? warningCountLabel(warningCount)
      : adjusted ? `${pluralizeCount(adjusted, "ajustada")}` : "Listo",
    warningCount ? "warning" : adjusted ? "active" : "ready"
  );
  $("#folder-list").innerHTML = batchFormatHtml(images, omitted);
  ensureGalleryFilterAvailable(images);
  renderFilterButtons();

  const visible = filteredImages();
  setGalleryTitle(images.length);
  $("#batch-visible-count").textContent = visible.length === images.length ? "" : `${visible.length}/${images.length}`;
  $("#image-list").innerHTML = visible.map(imageItemHtml).join("");
  queueThumbnailPreload();
  $("#batch-empty-note").innerHTML = visible.length ? "" : filteredEmptyHtml(images.length, valid, warnings, errors);
  if (filmstripCount) {
    filmstripCount.textContent = state.filter === "omitted"
      ? `${Number(state.scanDiagnostics?.totalOmitted || 0)} omitida${Number(state.scanDiagnostics?.totalOmitted || 0) === 1 ? "" : "s"}`
      : visible.length === images.length
      ? `${images.length} imágenes`
      : `${visible.length} de ${images.length}`;
  }
}

function setGalleryTitle(count) {
  const title = $("#gallery-title");
  if (title) {
    title.textContent = imageCountLabel(Number(count) || 0);
  }
}

function setBatchPill(label, tone = "muted") {
  const pill = $("#batch-pill");
  pill.textContent = label;
  pill.className = `batch-rail__badge is-${tone}`;
}

function updateBatchSearchClear() {
  const clearButton = $("#image-search-clear");
  if (!clearButton) {
    return;
  }
  const hasSearch = Boolean(state.search.trim());
  clearButton.classList.toggle("is-visible", hasSearch);
  clearButton.disabled = !hasSearch;
}

function filteredEmptyHtml(total, valid, warnings, errors) {
  if (!total) {
    return "No hay imágenes en este lote.";
  }
  const labels = {
    valid: "listas",
    warnings: "con avisos",
    omitted: "omitidas",
  };
  if (state.search.trim()) {
    const term = state.search.trim();
    const searchDetail = state.filter === "all"
      ? `No hay imágenes que coincidan con "${term}".`
      : `No hay imágenes que coincidan con "${term}" en el filtro actual.`;
    return `
      <strong>No hay imágenes que coincidan</strong>
      <span>${escapeHtml(searchDetail)}</span>
      <button type="button" data-action="clear-filter">Limpiar búsqueda</button>
    `;
  }
  const counts = { valid, warnings, omitted: Number(state.scanDiagnostics?.totalOmitted || 0) };
  const label = labels[state.filter] || "con este filtro";
  const count = counts[state.filter] || 0;
  if (state.filter === "omitted") {
    return omittedEmptyHtml();
  }
  return `
    <strong>No hay imágenes ${escapeHtml(label)}.</strong>
    <small>${escapeHtml(total)} imágenes en el lote · ${escapeHtml(count)} en este filtro</small>
    <button type="button" data-action="clear-filter">Ver todas</button>
  `;
}

function emptyBatchNoteHtml() {
  const detail = state.scanDiagnostics.totalOmitted
    ? `Esta carpeta no contiene imágenes compatibles. ${omittedSummaryText(state.scanDiagnostics)}.`
    : state.scanStatus || "Esta carpeta no contiene imágenes compatibles.";
  return `
    <strong>No se encontraron imágenes compatibles</strong>
    <span>${escapeHtml(detail)}</span>
    <button type="button" class="primary" data-action="pick-bridge-folder">Elegir otra carpeta</button>
  `;
}

function omittedEmptyHtml() {
  const omitted = state.scanDiagnostics?.omitted || [];
  if (!omitted.length) {
    return `
      <strong>No hay archivos omitidos</strong>
      <small>${escapeHtml(activeImages().length)} imágenes en el lote</small>
      <button type="button" data-action="clear-filter">Ver todas</button>
    `;
  }
  const first = omitted[0];
  return `
    <strong>${escapeHtml(omitted.length)} archivo${omitted.length === 1 ? "" : "s"} omitido${omitted.length === 1 ? "" : "s"}</strong>
    <span title="${escapeHtml(first.path || first.name)}">${escapeHtml(first.name || "Archivo")}</span>
    <small>Motivo: ${escapeHtml(first.detail || omissionReasonLabel(first.reason))}</small>
    <button type="button" data-action="clear-filter">Ver todas</button>
  `;
}

function batchFormatHtml(images, omittedCount = 0) {
  return "";
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

function imageThumbnailSrc(image) {
  if (!image) {
    return "";
  }
  if (image.source === "bridge") {
    return image.path ? bridgeThumbnailUrl(image.path) : "";
  }
  return mockThumbnailDataUrl(image);
}

function mockThumbnailDataUrl(image) {
  const palettes = {
    "tone-a": ["#f8f1e8", "#b7d6c8", "#34534a"],
    "tone-b": ["#f8e1dc", "#dfe9ec", "#723d45"],
    "tone-c": ["#ded8cf", "#8db9ad", "#33423f"],
    "tone-d": ["#f2e6bd", "#c7d7ea", "#67510f"],
    "tone-e": ["#e3ecfa", "#b7d2c9", "#294d63"],
  };
  const [bgA, bgB, ink] = palettes[image?.tone] || palettes["tone-a"];
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96">
      <defs>
        <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="${bgA}"/>
          <stop offset="1" stop-color="${bgB}"/>
        </linearGradient>
      </defs>
      <rect width="96" height="96" rx="8" fill="url(#bg)"/>
      <path d="M34 18h28l13 12-9 11-6-4v38H36V37l-6 4-9-11 13-12z" fill="#fff" fill-opacity=".86"/>
      <path d="M34 18h28l13 12-9 11-6-4v38H36V37l-6 4-9-11 13-12z" fill="none" stroke="${ink}" stroke-opacity=".34" stroke-width="2"/>
    </svg>
  `;
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg.trim())}`;
}

function thumbnailState(image, src) {
  if (!src) {
    return { status: "error", error: "Sin preview" };
  }
  const stored = state.thumbnailStatus[image.id];
  if (stored?.src === src || stored?.sourceSrc === src) {
    return stored;
  }
  return { status: "loading", src, error: "" };
}

function thumbnailHtml(image) {
  const src = imageThumbnailSrc(image);
  const current = thumbnailState(image, src);
  const status = current.status || "loading";
  const error = current.error || "Sin preview";
  const alt = `Miniatura de ${image.name}`;
  const displaySrc = current.resolvedSrc || current.src || src;
  return `
    <span class="thumb is-${escapeHtml(status)}" data-thumb-id="${escapeHtml(image.id)}">
      ${displaySrc ? `<img class="thumb-image" src="${escapeHtml(displaySrc)}" alt="${escapeHtml(alt)}" loading="eager" data-image-id="${escapeHtml(image.id)}" />` : ""}
      <span class="thumb-skeleton" aria-hidden="true"></span>
      <span class="thumb-error">${escapeHtml(error)}</span>
    </span>
  `;
}

function queueThumbnailPreload() {
  if (!hasBatch()) {
    return;
  }
  window.requestAnimationFrame(() => preloadBatchThumbnails());
}

function preloadBatchThumbnails() {
  activeImages().forEach((image) => {
    const src = imageThumbnailSrc(image);
    const current = state.thumbnailStatus[image.id];
    const key = `${image.id}|${src}`;
    if (!src || (current?.src === src && ["loaded", "error"].includes(current.status)) || thumbnailPreloads.has(key)) {
      return;
    }

    const preloader = new Image();
    thumbnailPreloads.set(key, preloader);
    preloader.onload = () => {
      markThumbnailLoaded(image.id, src, preloader.naturalWidth, preloader.naturalHeight);
      thumbnailPreloads.delete(key);
    };
    preloader.onerror = () => {
      markThumbnailError(image.id, src);
      thumbnailPreloads.delete(key);
    };
    preloader.src = src;
  });
}

function markThumbnailLoaded(imageId, sourceSrc, naturalWidth, naturalHeight, resolvedSrc = sourceSrc) {
  if (!activeImages().some((image) => image.id === imageId)) {
    return;
  }
  state.thumbnailStatus[imageId] = {
    status: "loaded",
    src: sourceSrc,
    sourceSrc,
    resolvedSrc,
    naturalWidth,
    naturalHeight,
    error: "",
  };
  applyThumbnailDomStatus(imageId, "loaded", resolvedSrc);
  updatePreviewDebugPanel();
}

function markThumbnailError(imageId, src) {
  const current = state.thumbnailStatus[imageId];
  if ((current?.sourceSrc === src || current?.src === src) && current.status === "loaded") {
    return;
  }
  if (requestThumbnailFallback(imageId, src)) {
    return;
  }
  commitThumbnailError(imageId, src);
}

function commitThumbnailError(imageId, src, detail = "") {
  const current = state.thumbnailStatus[imageId];
  if ((current?.sourceSrc === src || current?.src === src) && current.status === "loaded") {
    return;
  }
  if (!activeImages().some((image) => image.id === imageId)) {
    return;
  }
  const error = detail ? `Preview no disponible: ${detail}` : `Preview no disponible: ${src}`;
  state.thumbnailStatus[imageId] = {
    status: "error",
    src,
    sourceSrc: src,
    error,
  };
  state.thumbnailErrors = [
    { imageId, src, error },
    ...state.thumbnailErrors.filter((item) => item.imageId !== imageId),
  ].slice(0, 20);
  applyThumbnailDomStatus(imageId, "error");
  state.bridgeLastResponse = `thumbnail error: ${basename(src) || imageId}`;
  updatePreviewDebugPanel();
}

function requestThumbnailFallback(imageId, sourceSrc) {
  const image = activeImages().find((item) => item.id === imageId);
  if (!image || image.source !== "bridge" || !image.path) {
    return false;
  }

  const current = state.thumbnailStatus[imageId];
  if (current?.sourceSrc === sourceSrc && current.status === "loaded") {
    return false;
  }
  if (current?.sourceSrc === sourceSrc && current.fallbackAttempted && current.status === "loading") {
    return true;
  }
  if (thumbnailFallbackInFlight.has(imageId) || thumbnailFallbackQueue.some((item) => item.imageId === imageId)) {
    return true;
  }

  state.thumbnailStatus[imageId] = {
    status: "loading",
    src: sourceSrc,
    sourceSrc,
    fallbackAttempted: true,
    error: "",
  };
  applyThumbnailDomStatus(imageId, "loading");
  thumbnailFallbackQueue.push({ imageId, sourceSrc });
  processThumbnailFallbackQueue();
  return true;
}

function processThumbnailFallbackQueue() {
  while (thumbnailFallbackInFlight.size < MAX_THUMBNAIL_FALLBACKS && thumbnailFallbackQueue.length) {
    const item = thumbnailFallbackQueue.shift();
    thumbnailFallbackInFlight.add(item.imageId);
    void renderFallbackThumbnail(item)
      .catch((error) => {
        commitThumbnailError(item.imageId, item.sourceSrc, bridgeErrorMessage(error));
      })
      .finally(() => {
        thumbnailFallbackInFlight.delete(item.imageId);
        processThumbnailFallbackQueue();
      });
  }
}

async function renderFallbackThumbnail({ imageId, sourceSrc }) {
  const image = activeImages().find((item) => item.id === imageId);
  if (!image) {
    return;
  }

  const response = await bridgeRequest("/preview/render", {
    method: "POST",
    body: JSON.stringify({
      imagePath: image.path,
      targetWidth: 160,
      targetHeight: 160,
      settings: bridgePreviewSettings(),
      localOverride: currentImageOverride(image),
    }),
    timeoutMs: 20000,
  });
  const data = previewResponseToData(response);
  markThumbnailLoaded(imageId, sourceSrc, data.width, data.height, data.src);
}

function applyThumbnailDomStatus(imageId, status, resolvedSrc = "") {
  const wrapper = Array.from(document.querySelectorAll(".thumb[data-thumb-id]"))
    .find((item) => item.dataset.thumbId === imageId);
  if (!wrapper) {
    return;
  }
  if (resolvedSrc) {
    const image = wrapper.querySelector(".thumb-image");
    if (image && image.getAttribute("src") !== resolvedSrc) {
      image.src = resolvedSrc;
    }
  }
  wrapper.classList.remove("is-loading", "is-loaded", "is-error");
  wrapper.classList.add(`is-${status}`);
  if (status === "error") {
    const label = wrapper.querySelector(".thumb-error");
    if (label) {
      label.textContent = "Sin preview";
    }
  }
}

function imageItemHtml(image) {
  const selected = image.id === state.selectedImageId ? "active" : "";
  const exportState = exportItemState(image);
  const imageStatus = hasCurrentImageOverride(image) ? "adjusted" : image.status;
  const effectiveStatus = exportState?.status || imageStatus;
  const chipClass = effectiveStatus === "warning" ? "warning" : effectiveStatus === "error" ? "error" : effectiveStatus === "exported" ? "exported" : imageStatus === "adjusted" ? "adjusted" : "ready";
  const chipLabel = exportState?.label || assetStatusLabel(imageStatus);
  const title = image.path || image.name;
  const detail = image.detail === "Lista" ? "" : image.detail;
  const displayName = imageFileStem(image.name);
  const fileType = imageFileType(image);
  const compactDetail = compactImageDetail(detail);
  const metadata = !compactDetail
    ? fileType
    : compactDetail.toUpperCase().startsWith(fileType)
    ? compactDetail
    : `${fileType} · ${compactDetail}`;
  const thumbState = thumbnailState(image, imageThumbnailSrc(image));
  const previewNote = thumbState.status === "error" ? " · sin preview" : "";
  const statusText = chipLabel ? ` · ${chipLabel}` : "";
  const stateIcon = assetStatusIcon(effectiveStatus);
  return `
    <button type="button" class="image-item asset-row ${selected} ${chipClass}" data-image-id="${escapeHtml(image.id)}" title="${escapeHtml(title)}" aria-pressed="${selected ? "true" : "false"}" aria-label="${escapeHtml(`${image.name}${statusText}`)}">
      ${thumbnailHtml(image)}
      <span class="image-copy">
        <strong>${escapeHtml(displayName)}</strong>
        <small>${escapeHtml(`${metadata}${previewNote}`)}</small>
      </span>
      <span class="asset-state ${chipClass}" title="${escapeHtml(chipLabel || "Lista")}">
        <span aria-hidden="true">${escapeHtml(stateIcon)}</span>
        <em>${escapeHtml(chipLabel || "Lista")}</em>
      </span>
    </button>
  `;
}

function compactImageDetail(detail) {
  return String(detail || "")
    .replace(/^PNG\s*·\s*/i, "")
    .replace(/^JPG\s*·\s*/i, "")
    .replace(/^JPEG\s*·\s*/i, "")
    .replace(/^Lista$/i, "")
    .trim();
}

function assetStatusLabel(status) {
  if (status === "ready") {
    return "Lista";
  }
  if (status === "adjusted") {
    return "Ajustada";
  }
  return statusLabels[status] || "Lista";
}

function assetStatusIcon(status) {
  if (status === "warning") {
    return "!";
  }
  if (status === "error") {
    return "×";
  }
  if (status === "exported") {
    return "✓";
  }
  if (status === "adjusted") {
    return "*";
  }
  return "✓";
}

function galleryFilterCounts(images = activeImages()) {
  return {
    all: images.length,
    valid: images.filter((image) => image.status === "ready" || image.status === "adjusted").length,
    warnings: images.filter((image) => image.status === "warning" || image.status === "error" || exportItemState(image)?.status === "error").length,
    omitted: Number(state.scanDiagnostics?.totalOmitted || 0),
  };
}

function galleryFilterVisible(filter, counts = galleryFilterCounts()) {
  if (filter === "all") {
    return true;
  }
  if (filter === "valid") {
    return counts.valid > 0 && counts.valid !== counts.all;
  }
  if (filter === "warnings") {
    return counts.warnings > 0;
  }
  if (filter === "omitted") {
    return counts.omitted > 0;
  }
  return false;
}

function ensureGalleryFilterAvailable(images = activeImages()) {
  const counts = galleryFilterCounts(images);
  if (!galleryFilterVisible(state.filter, counts)) {
    state.filter = "all";
  }
}

function renderFilterButtons() {
  const images = activeImages();
  const counts = galleryFilterCounts(images);
  const labels = {
    all: "Todas",
    valid: "Listas",
    warnings: "Avisos",
    omitted: "Omitidas",
  };
  const hasWarnings = counts.warnings > 0;
  const order = hasWarnings
    ? { warnings: 1, all: 2, omitted: 3, valid: 4 }
    : { all: 1, omitted: 2, valid: 3, warnings: 4 };
  $$(".batch-filter button").forEach((button) => {
    const filter = button.dataset.filter;
    const count = counts[filter] || 0;
    button.innerHTML = `${escapeHtml(labels[filter])} <span>${escapeHtml(count)}</span>`;
    button.title = `${labels[filter]} ${count}`;
    button.style.order = String(order[filter] || 9);
    button.classList.toggle("active", button.dataset.filter === state.filter);
    const empty = filter !== "all" && !count;
    button.classList.toggle("is-empty", empty);
    button.hidden = !galleryFilterVisible(filter, counts);
  });
}

function renderGalleryViewButtons() {
  $$("[data-gallery-view]").forEach((button) => {
    const active = button.dataset.galleryView === state.galleryView;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", active ? "true" : "false");
  });
}

function renderPreview() {
  const image = selectedImage();
  const isBridgeImage = image?.source === "bridge";
  const previewControlsDisabled = !image || state.previewStatus === "empty" || state.previewStatus === "error";
  const compareControlsDisabled = !image || isBridgeImage || state.previewStatus === "empty" || state.previewStatus === "error";
  $("#preview-name").textContent = image
    ? image.name
    : state.batch === "none"
      ? "Seleccionar carpeta de imágenes"
      : state.batch === "empty"
        ? "No se encontraron imágenes compatibles"
        : state.batch === "scanning"
          ? "Escaneando carpeta"
          : "Selecciona una imagen";
  $("#preview-subtitle").textContent = previewSubtitle(image);
  $("#zoom-label").textContent = `${currentViewerZoom()}%`;
  const visibleImages = filteredImages();
  const visibleIndex = visibleImages.findIndex((item) => item.id === state.selectedImageId);
  $("#viewer-position").textContent = visibleIndex >= 0
    ? `${visibleIndex + 1} / ${visibleImages.length}`
    : activeImages().length ? "Fuera del filtro" : "Sin imagen";
  $("#preview-meta").textContent = isBridgeImage
    ? bridgePreviewMeta()
    : image ? state.activePreset : "Sin lote";
  const outputContext = $("#preview-output-context");
  if (outputContext) {
    outputContext.innerHTML = previewOutputContextHtml(image);
  }
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
  $$("[data-action='zoom-fit'], [data-action='zoom-height'], [data-action='zoom-width'], [data-action='zoom-100'], [data-action='zoom-out'], [data-action='zoom-in'], [data-action='force-preview-error']").forEach((button) => {
    button.disabled = previewControlsDisabled;
  });
  $$("[data-action='zoom-fit'], [data-action='zoom-height'], [data-action='zoom-width'], [data-action='zoom-100']").forEach((button) => {
    const expectedMode = button.dataset.action === "zoom-fit"
      ? "fit"
      : button.dataset.action === "zoom-height"
        ? "height"
        : button.dataset.action === "zoom-width"
          ? "width"
          : "manual";
    const active = expectedMode === "manual"
      ? state.fitMode === "manual" && state.zoom === 100
      : state.fitMode === expectedMode;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", button.classList.contains("active") ? "true" : "false");
  });
  $$("[data-action='previous-image'], [data-action='next-image']").forEach((button) => {
    button.disabled = visibleImages.length < 2;
  });

  const previewPanel = $("#preview-panel");
  if (previewPanel) {
    previewPanel.className = `preview-panel preview-panel--${previewOrientation()}`;
  }
  const canvas = $("#preview-canvas");
  canvas.className = `preview-canvas ${state.previewMode} bg-${state.previewBg} ${viewerModeClass()}`;
  canvas.style.setProperty("--preview-scale", isAutoViewerMode() ? "1" : String(state.zoom / 100));
  applyViewerPanDom();

  if (state.batch === "none") {
    canvas.innerHTML = initialStateHtml();
    queueFitZoomRefresh();
    return;
  }

  if (state.batch === "scanning") {
    canvas.innerHTML = scanningStateHtml();
    queueFitZoomRefresh();
    return;
  }

  if (state.batch === "empty") {
    canvas.innerHTML = emptyStateHtml({
      variant: "warning",
      title: "No se encontraron imágenes compatibles",
      detail: state.scanDiagnostics.totalOmitted
        ? omittedSummaryText(state.scanDiagnostics)
        : "Esta carpeta no contiene imágenes compatibles.",
      actionLabel: "Elegir otra carpeta",
      action: "pick-bridge-folder",
      meta: state.scanStatus || "Revisa el detalle técnico del lote",
    });
    queueFitZoomRefresh();
    return;
  }

  if (!image || state.previewStatus === "empty") {
    canvas.innerHTML = emptyStateHtml({
      variant: "inline",
      title: "Selecciona una imagen",
      detail: "Elige una miniatura del lote para revisar la imagen.",
      actionLabel: activeImages().length ? "Seleccionar primera" : "",
      action: activeImages().length ? "select-first-image" : "",
      meta: activeImages().length ? `${activeImages().length} imágenes en el lote` : "",
    });
    queueFitZoomRefresh();
    return;
  }

  if (isBridgeImage) {
    canvas.innerHTML = realPreviewHtml(image);
    queueFitZoomRefresh();
    return;
  }

  if (state.previewStatus === "loading") {
    canvas.innerHTML = `
      <div class="preview-state">
        <span class="loader" aria-hidden="true"></span>
        <strong>Generando vista</strong>
        <span>${escapeHtml(image.name)}</span>
      </div>
    `;
    queueFitZoomRefresh();
    return;
  }

  if (state.previewStatus === "error") {
    canvas.innerHTML = previewStateHtml("Vista no disponible", "Revisa alpha o archivo fuente.");
    queueFitZoomRefresh();
    return;
  }

  canvas.innerHTML = `
    <div class="mock-product" aria-hidden="true">
      <div class="mock-shadow"></div>
      <div class="mock-body"></div>
    </div>
    ${state.previewStatus === "warning" ? '<div class="preview-warning-card">Render con fallback. Revisa antes de exportar.</div>' : ""}
  `;
  queueFitZoomRefresh();
}

function queueFitZoomRefresh() {
  if (fitZoomFrame) {
    window.cancelAnimationFrame(fitZoomFrame);
  }
  fitZoomFrame = window.requestAnimationFrame(() => {
    fitZoomFrame = 0;
    updateFitZoomReadout();
  });
}

function updateFitZoomReadout() {
  const label = $("#zoom-label");
  if (!label) {
    return;
  }
  if (!isAutoViewerMode()) {
    label.textContent = `${state.zoom}%`;
    return;
  }

  const zoom = calculateFitZoom();
  state.fitZoom = zoom;
  label.textContent = `${zoom}%`;
}

function calculateFitZoom() {
  const canvas = $("#preview-canvas");
  if (!canvas) {
    return 100;
  }
  const image = canvas.querySelector(".preview-image");
  const naturalWidth = Number(image?.naturalWidth || image?.getAttribute("width") || state.previewData?.width || 0);
  const naturalHeight = Number(image?.naturalHeight || image?.getAttribute("height") || state.previewData?.height || 0);
  if (!naturalWidth || !naturalHeight || !canvas.clientWidth || !canvas.clientHeight) {
    return 100;
  }
  const availableWidth = Math.max(1, canvas.clientWidth - 48);
  const availableHeight = Math.max(1, canvas.clientHeight - 48);
  canvas.style.setProperty("--fit-width", `${availableWidth}px`);
  canvas.style.setProperty("--fit-height", `${availableHeight}px`);
  const widthFit = availableWidth / naturalWidth;
  const heightFit = availableHeight / naturalHeight;
  const fit = state.fitMode === "width"
    ? widthFit
    : state.fitMode === "height"
      ? Math.min(heightFit, widthFit)
      : Math.min(widthFit, heightFit);
  return Math.max(1, Math.min(100, Math.round(fit * 100)));
}

function realPreviewHtml(image) {
  if (state.previewStatus === "loading") {
    return `
      <div class="preview-state">
        <span class="loader" aria-hidden="true"></span>
        <strong>Generando vista</strong>
        <span>${escapeHtml(image.name)}</span>
      </div>
    `;
  }

  if (state.previewStatus === "error") {
    return previewStateHtml("Vista no disponible", state.previewError || "Revisa la imagen fuente.");
  }

  if (state.previewData?.src) {
    const width = Number(state.previewData.width) || 0;
    const height = Number(state.previewData.height) || 0;
    const zoomWidth = width ? Math.max(1, Math.round(width * state.zoom / 100)) : "";
    const zoomHeight = height ? Math.max(1, Math.round(height * state.zoom / 100)) : "";
    const sizeStyle = zoomWidth && zoomHeight ? ` style="width: ${zoomWidth}px; height: ${zoomHeight}px;" width="${width}" height="${height}"` : "";
    return `
      <img class="preview-image" src="${escapeHtml(state.previewData.src)}" alt="Vista previa de ${escapeHtml(image.name)}"${sizeStyle} />
      ${state.previewData.warning ? `<div class="preview-warning-card">${escapeHtml(state.previewData.warning)}</div>` : ""}
    `;
  }

  return `
    <div class="real-preview-placeholder">
      <strong>Vista pendiente</strong>
      <span>Imagen seleccionada: ${escapeHtml(image.name)}</span>
      <small class="path-line">Ruta: ${escapeHtml(image.path || "Sin ruta")}</small>
      <small>Genera la vista al seleccionar la imagen.</small>
    </div>
  `;
}

function bridgePreviewMeta() {
  if (state.previewStatus === "loading") {
    return "Generando vista";
  }
  if (state.previewStatus === "error") {
    return state.previewError || "Vista no disponible";
  }
  if (state.previewData) {
    return state.previewData.warning ? "Vista con aviso" : state.activePreset;
  }
  return "Vista pendiente";
}

function previewSettingsLabel() {
  if (state.bridgeMode === "bridge" && activePresetItem()?.source === "bridge") {
    return state.presetDirty ? "Aspecto modificado" : "Salida";
  }
  return state.presetDirty ? "Aspecto modificado" : "Aspecto";
}

function previewModeLabel() {
  if (state.previewMode === "original") {
    return "Original";
  }
  if (state.previewMode === "compare") {
    return "Comparación";
  }
  return "Vista";
}

function previewOutputContextHtml(image) {
  if (!image || state.batch !== "ready") {
    return "";
  }
  const outputLine = viewerOutputCompactLabel();
  const modeLine = state.previewMode === "original"
    ? "Original"
    : state.previewMode === "compare"
      ? "Comparar"
      : "";
  return `
    <strong title="${escapeHtml(outputLine)}">${escapeHtml(modeLine ? `${modeLine} · ${outputLine}` : outputLine)}</strong>
  `;
}

function outputSizeDisplay() {
  const size = parseOutputSize(state.size);
  return `${size.width}×${size.height}`;
}

function viewerOutputCompactLabel() {
  return `${state.format} · ${outputSizeDisplay()} · ${backgroundLabel(state.background)}`;
}

function previewStateHtml(title, detail) {
  return emptyStateHtml({ variant: "inline", title, detail });
}

function emptyStateHtml({ variant = "inline", title, detail, actionLabel = "", action = "", meta = "" }) {
  const actionHtml = actionLabel && action
    ? `<button type="button" class="primary" data-action="${escapeHtml(action)}">${escapeHtml(actionLabel)}</button>`
    : "";
  const metaHtml = meta ? `<small>${escapeHtml(meta)}</small>` : "";
  return `
    <div class="empty-state ${escapeHtml(variant)}">
      <span class="empty-icon" aria-hidden="true"></span>
      <strong>${escapeHtml(title)}</strong>
      <span>${escapeHtml(detail)}</span>
      ${actionHtml}
      ${metaHtml}
    </div>
  `;
}

function initialStateHtml() {
  return `
    <div class="empty-state onboarding initial-onboarding">
      <span class="empty-icon" aria-hidden="true"></span>
      <strong>Seleccionar carpeta de imágenes</strong>
      <span>PNG o JPG. Después podrás revisar y exportar el lote.</span>
      <button type="button" class="primary" data-action="pick-bridge-folder">Seleccionar carpeta</button>
      <details class="manual-path-inline">
        <summary>Usar ruta manual</summary>
        <label class="text-field">
          <span>Carpeta</span>
          <input id="onboarding-scan-path" type="text" value="${escapeHtml(state.bridgeScanPath)}" placeholder="C:/ruta/lote" />
        </label>
        <button type="button" data-action="scan-bridge-folder">Escanear carpeta</button>
      </details>
      <small>Ajuste por defecto: ${escapeHtml(outputPresetLabel())} · ${escapeHtml(state.format)} · ${escapeHtml(backgroundLabel(state.background))}</small>
    </div>
  `;
}

function scanningStateHtml() {
  return `
    <div class="empty-state inline scanning-state">
      <span class="loader" aria-hidden="true"></span>
      <strong>Escaneando carpeta...</strong>
      <span>${escapeHtml(state.scanStatus || "Leyendo imágenes")}</span>
    </div>
  `;
}

function previewOrientation() {
  const width = Number(state.previewData?.width || 0);
  const height = Number(state.previewData?.height || 0);
  if (!width || !height) {
    return "portrait";
  }
  if (height > width * 1.08) {
    return "portrait";
  }
  if (width > height * 1.08) {
    return "landscape";
  }
  return "square";
}

function previewSubtitle(image) {
  if (!image) {
    if (state.batch === "none") {
      return "Sin lote";
    }
    if (state.batch === "empty") {
      return state.scanStatus || "No hay imágenes válidas";
    }
    if (state.batch === "scanning") {
      return state.scanStatus || "Escaneando";
    }
    return "Sin selección";
  }
  if (image.source === "bridge") {
    if (state.previewStatus === "loading") {
      return "Generando vista";
    }
    if (state.previewStatus === "warning") {
      return "Vista con aviso";
    }
    if (state.previewStatus === "error") {
      return "Vista no disponible";
    }
    if (state.previewStatus === "ready") {
      return viewerOutputCompactLabel();
    }
    return viewerOutputCompactLabel();
  }
  if (state.previewStatus === "loading") {
    return "Generando vista";
  }
  if (state.previewStatus === "warning") {
    return "Vista con aviso";
  }
  if (state.previewStatus === "error") {
    return "Vista no disponible";
  }
  return state.previewStatus === "ready" ? viewerOutputCompactLabel() : image.detail;
}

function renderSettings() {
  renderReviewPanel();
  $("#active-preset").textContent = state.activePreset;
  $("#preset-source").textContent = presetSourceLabel();
  $("#preset-dirty").textContent = state.presetDirty ? "Sin guardar" : "Sin cambios";
  $("#preset-dirty").classList.toggle("dirty", state.presetDirty);
  const presetItems = activePresetItems();
  const presetCount = $("#preset-count");
  if (presetCount) {
    presetCount.textContent = `${presetItems.length}`;
  }
  $("#preset-list").innerHTML = presetItems.length
    ? presetItems.map((preset) => {
      const active = preset.name === state.activePreset;
      return `
      <button type="button" class="preset-chip${active ? " active" : ""}" data-preset="${escapeHtml(preset.name)}" aria-pressed="${active ? "true" : "false"}" title="${escapeHtml(active ? `${preset.name} activo` : `Cambiar a ${preset.name}`)}">
        <span class="preset-chip__name">${escapeHtml(preset.name)}</span>
        <span class="preset-chip__meta">${escapeHtml(active ? "Activo" : preset.category || "Ajuste")}</span>
      </button>
    `;
    }).join("")
    : '<span class="preset-empty">No hay ajustes guardados</span>';

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
  const localOverride = currentImageOverride(image);
  const localActive = Object.keys(localOverride).length > 0 || image?.status === "adjusted";
  $("#local-adjustment").classList.toggle("active", localActive);
  $("#local-adjustment-text").textContent = localActive ? "Ajuste local activo" : "Sin ajuste local";
  localOverrideKeys.forEach((key) => {
    const value = Number(localOverride[key] || 0);
    const input = $(`[data-local-setting="${key}"]`);
    const output = $(`#local-${key}-output`);
    if (input) {
      input.value = value;
    }
    if (output) {
      output.textContent = value > 0 ? `+${value}` : String(value);
    }
  });
  $("#save-preset").disabled = false;
  $("#save-preset").title = "Guardar el ajuste activo";
  $("#save-preset").textContent = state.presetDirty ? "Guardar cambios" : "Guardar";
  const deletePresetButton = $("#delete-preset");
  if (deletePresetButton) {
    const canDeletePreset = presetItems.length > 1;
    deletePresetButton.disabled = !canDeletePreset;
    deletePresetButton.title = canDeletePreset ? "Eliminar el ajuste activo" : "Debe quedar al menos un ajuste";
  }
  const advanced = $("#advanced-settings");
  const advancedSummaryTitle = advanced?.querySelector("summary strong");
  if (advancedSummaryTitle) {
    const dirtyCount = advancedDirtyCount();
    advancedSummaryTitle.textContent = dirtyCount ? `Avanzado · ${dirtyCount} cambio${dirtyCount === 1 ? "" : "s"}` : "Avanzado";
  }
}

function renderReviewPanel() {
  const target = $("#review-summary");
  if (!target) {
    return;
  }
  target.innerHTML = reviewPanelHtml();
}

function reviewPanelHtml() {
  const image = selectedImage();
  if (!image) {
    return emptyStateHtml({
      variant: "inline",
      title: "Selecciona una imagen",
      detail: "Elige una miniatura para revisar la salida.",
      actionLabel: activeImages().length ? "Seleccionar primera imagen" : "",
      action: activeImages().length ? "select-first-image" : "",
    });
  }

  const reviewState = imageReviewState(image);
  const issues = imageReviewIssues(image);
  const outputName = outputNameForImage(image);
  const hasLocal = hasCurrentImageOverride(image) || image.status === "adjusted";
  const images = activeImages();
  const selectedIndex = images.findIndex((item) => item.id === image.id);
  const canNavigate = images.length > 1;
  const outputDetail = viewerOutputCompactLabel();
  const issueList = issues.length ? `
    <div class="review-issue-list">
      ${issues.map((issue) => `
        <div class="review-issue ${issue.level === "error" ? "error" : "warning"}">
          <strong>${escapeHtml(issue.title)}</strong>
          <span>${escapeHtml(issue.detail)}</span>
        </div>
      `).join("")}
    </div>
  ` : "";

  return `
    <div class="review-card review-card--compact ${escapeHtml(reviewState.tone)}">
      <div class="review-card__header">
        <div>
          <strong title="${escapeHtml(image.path || image.name)}">${escapeHtml(image.name)}</strong>
          <small>${escapeHtml(selectedIndex >= 0 ? `${selectedIndex + 1} de ${images.length}` : "Fuera del filtro")}</small>
        </div>
        <span class="status-badge ${escapeHtml(reviewState.tone)}">${escapeHtml(reviewState.label)}</span>
      </div>
    </div>

    <div class="review-output-card review-output-card--compact">
      <strong title="${escapeHtml(outputName)}">${escapeHtml(outputName)}</strong>
      <small>${escapeHtml(outputDetail)}</small>
    </div>

    ${issueList}

    <div class="inspector-actionbar review-actions">
      <button type="button" data-action="previous-image"${canNavigate ? "" : " disabled"}>Anterior</button>
      <button type="button" data-action="next-image"${canNavigate ? "" : " disabled"}>Siguiente</button>
      ${issues.length ? '<button type="button" class="primary" data-action="review-errors">Ver avisos</button>' : ""}
      <button type="button" data-action="open-app-settings">Cambiar formato</button>
      ${hasLocal ? '<button type="button" data-action="reset-local-adjustment">Quitar ajuste local</button>' : '<button type="button" data-action="open-advanced">Ajustar imagen</button>'}
    </div>
  `;
}

function imageReviewState(image) {
  const exportState = exportItemState(image);
  const status = exportState?.status || (hasCurrentImageOverride(image) ? "adjusted" : image.status);
  if (status === "error") {
    return {
      tone: "error",
      label: exportState?.label || "Error",
      detail: image.exportable === false ? "No exportable" : image.detail || "Revisar antes de exportar",
    };
  }
  if (status === "warning") {
    return {
      tone: "warning",
      label: "Aviso",
      detail: image.detail || "Revisar antes de exportar",
    };
  }
  if (status === "exported") {
    return { tone: "ready", label: "Exportada", detail: "Exportación completada" };
  }
  if (status === "adjusted") {
    return { tone: "active", label: "Ajustada", detail: "Ajuste por imagen activo" };
  }
  return { tone: "ready", label: "Lista", detail: "Lista para exportar" };
}

function imageReviewIssues(image) {
  const issues = [];
  const exportState = exportItemState(image);
  if (image.status === "warning") {
    issues.push({
      level: "warning",
      title: "Aviso de imagen",
      detail: image.detail || "Conviene revisar esta imagen antes de exportar.",
    });
  }
  if (image.status === "error" || image.exportable === false) {
    issues.push({
      level: "error",
      title: "Imagen no exportable",
      detail: image.detail || "Esta imagen quedará fuera de la salida.",
    });
  }
  if (exportState?.status === "error") {
    issues.push({
      level: "error",
      title: "Error de exportación",
      detail: exportState.label || "No se pudo exportar esta imagen.",
    });
  }
  if (image.id === state.selectedImageId && state.previewStatus === "warning" && state.previewData?.warning) {
    issues.push({
      level: "warning",
      title: "Vista con aviso",
      detail: state.previewData.warning,
    });
  }
  if (image.id === state.selectedImageId && state.previewStatus === "error") {
    issues.push({
      level: "error",
      title: "Vista no disponible",
      detail: state.previewError || "No se pudo generar la vista previa.",
    });
  }
  return issues;
}

function outputNameForImage(image, index = 1) {
  if (!state.naming.trim()) {
    return "Nombre de archivo pendiente";
  }
  const original = imageFileStem(image?.name || "imagen_001.png");
  const folder = activeFolders().find((item) => item.id === image?.folderId)?.name
    || activeFolders()[0]?.name
    || "lote";
  let outputName = state.naming
    .replaceAll("{original}", original)
    .replaceAll("{suffix}", state.suffix || "_PRO")
    .replaceAll("{folder}", folder);
  outputName = outputName.replace(/\{index(?::0?(\d+)d)?\}/g, (_match, width) => {
    const digits = Number(width) || 1;
    return String(index).padStart(digits, "0");
  });
  if (!/\.[a-z0-9]+$/i.test(outputName)) {
    outputName = `${outputName}.${state.format.toLowerCase()}`;
  }
  return outputName;
}

function advancedDirtyCount() {
  if (!state.presetDirty) {
    return 0;
  }
  const presetSettings = normalizeSettings(activePresetItem()?.settings || defaultSettings);
  return advancedSettingKeys.filter((key) => state.settings[key] !== presetSettings[key]).length;
}

function advancedSettingsDirty() {
  return advancedDirtyCount() > 0;
}

function renderInspector() {
  const image = selectedImage();
  const contextOnly = state.batch === "none" || state.batch === "empty" || state.batch === "scanning" || !image;
  const panel = $(".settings-panel");
  const validTabs = ["review", "output", "warnings", "advanced"];
  if (!validTabs.includes(state.inspectorTab)) {
    state.inspectorTab = "review";
  }
  panel.classList.toggle("is-editing-output", state.outputEditMode);
  panel.classList.toggle("is-editing-preset", state.presetEditorOpen || state.inspectorTab === "advanced");
  const start = $("#inspector-start");
  start.classList.toggle("is-hidden", !contextOnly);
  if (contextOnly) {
    start.innerHTML = contextualInspectorHtml();
  } else {
    start.innerHTML = "";
  }
  $(".inspector-tabs").classList.toggle("is-hidden", contextOnly);
  $$(".settings-panel [data-inspector-tab]").forEach((button) => {
    button.classList.toggle("active", button.dataset.inspectorTab === state.inspectorTab);
  });
  $$(".settings-panel [data-inspector-section]").forEach((section) => {
    const sectionName = section.dataset.inspectorSection;
    section.classList.toggle(
      "is-hidden",
      contextOnly
        || sectionName !== state.inspectorTab
    );
  });
}

function contextualInspectorHtml() {
  if (state.batch === "scanning") {
    return `
      <div class="context-panel">
        <div class="context-header">
          <span class="eyebrow">Preparación</span>
          <strong>Escaneando carpeta</strong>
          <small>${escapeHtml(state.scanStatus || "Leyendo imágenes")}</small>
        </div>
        ${progressPanelHtml("Preparando lote")}
        ${preflightListHtml([
          { state: "pending", title: "Carpeta seleccionada", detail: "Leyendo origen" },
          { state: "pending", title: "Imágenes listas", detail: "Contando archivos" },
          { state: "pending", title: "Destino", detail: "Se configurará después" },
        ])}
      </div>
    `;
  }

  if (state.batch === "none") {
    return `
      <div class="context-panel">
        <div class="context-header">
          <span class="eyebrow">Preparación</span>
          <strong>Seleccionar carpeta</strong>
          <small>El ajuste activo y la salida se preparan automáticamente.</small>
        </div>
        ${preflightListHtml([
          { state: "pending", title: "Carpeta seleccionada", detail: "Pendiente" },
          { state: "pending", title: "Imágenes listas", detail: "Pendiente" },
          { state: "pending", title: "Destino de salida", detail: "Origen / _SALIDA_PRO" },
        ])}
        <div class="default-stack">
          <span>Valores por defecto</span>
          <strong>${escapeHtml(state.format)} · ${escapeHtml(state.size)} · ${escapeHtml(backgroundLabel(state.background))}</strong>
          <small>Ajuste ${escapeHtml(state.activePreset)}</small>
        </div>
        <button type="button" class="primary" data-action="pick-bridge-folder">Seleccionar carpeta</button>
      </div>
    `;
  }

  if (state.batch === "empty") {
    return `
      <div class="context-panel warning">
        <div class="context-header">
          <span class="eyebrow">Salida</span>
          <strong>Exportación bloqueada</strong>
          <small>${escapeHtml(state.scanStatus || "La carpeta no contiene imágenes procesables.")}</small>
        </div>
        ${preflightListHtml([
          { state: "warning", title: "Carpeta revisada", detail: state.scanDiagnostics.totalFiles ? `${state.scanDiagnostics.totalFiles} archivos encontrados` : "Sin archivos compatibles" },
          { state: "error", title: "Imágenes exportables", detail: "0 imágenes" },
          { state: state.scanDiagnostics.totalOmitted ? "warning" : "pending", title: "Avisos", detail: omittedSummaryText(state.scanDiagnostics) },
          { state: "pending", title: "Destino", detail: "Pendiente hasta cargar un lote" },
        ])}
        <button type="button" class="primary" data-action="pick-bridge-folder">Elegir otra carpeta</button>
      </div>
    `;
  }

  return `
    <div class="context-panel">
      <div class="context-header">
        <strong>Selecciona una imagen</strong>
        <small>${escapeHtml(compactHeaderStatusText())}</small>
      </div>
      <button type="button" class="primary" data-action="select-first-image">Seleccionar primera imagen</button>
    </div>
  `;
}

function progressPanelHtml(label, value = null) {
  const valueHtml = value === null ? "" : `<strong>${escapeHtml(Math.round(value))}%</strong>`;
  return `
    <div class="context-progress${value === null ? " is-indeterminate" : ""}">
      <span>${escapeHtml(label)}</span>
      ${valueHtml}
    </div>
  `;
}

function presetSourceLabel() {
  if (state.bridgeMode === "bridge") {
    const source = state.bridgePresetSource === "config"
      ? "Config"
      : state.bridgePresetSource === "legacy-config"
        ? "Config legacy"
        : state.bridgePresetSource === "defaults"
          ? "Defaults"
          : "Salida";
    if (state.bridgePresetWarning) {
      return `${source} · aviso`;
    }
    return state.presetDirty ? `${source} · modificado` : source;
  }
  return state.presetDirty ? "Modificado" : "Salida";
}

function renderExport() {
  renderOutputProfileSelect();
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
  const destinationText = destinationCompactLabel();
  const warningCount = visibleWarningCount();
  $("#export-readiness").textContent = state.outputEditMode ? "Editar salida" : outputProfileDisplayName();
  $("#export-count").textContent = outputCount ? `${outputCount} img` : "Pendiente";
  $("#export-count").classList.toggle("dirty", !ready);
  const warningsReadiness = $("#warnings-readiness");
  if (warningsReadiness) {
    warningsReadiness.textContent = warningCount ? `${warningCount} aviso${warningCount === 1 ? "" : "s"} del lote` : "Sin avisos";
  }
  const warningsTab = $("[data-inspector-tab='warnings']");
  if (warningsTab) {
    warningsTab.textContent = warningCount ? `Avisos ${warningCount}` : "Avisos";
  }

  const warningSummary = outputWarningSummary(issues);
  const editActions = state.outputEditMode ? `
    <div class="inspector-actionbar">
      <button type="button" class="primary" data-action="apply-output-edit">Aplicar salida</button>
      <button type="button" data-action="cancel-output-edit">Cancelar</button>
      <button type="button" class="btn-linklike" data-action="open-app-settings">Formatos</button>
    </div>
  ` : "";
  const presetActions = !state.outputEditMode ? `
    <div class="inspector-actionbar">
      <button type="button" class="primary" data-action="open-app-settings">Cambiar formato</button>
      <button type="button" data-action="edit-output">Editar campos</button>
    </div>
  ` : "";

  $("#export-summary").innerHTML = state.outputEditMode ? `
    <div class="compact-panel">
      <div>
        <span>Salida</span>
        <strong>${escapeHtml(outputProfileDisplayName())}</strong>
      </div>
      <small>${escapeHtml(presetSummaryLine())}</small>
    </div>
    ${editActions}
  ` : `
    <div class="preset-summary-card">
      <div class="preset-summary-main">
        <span>Salida</span>
        <strong>${escapeHtml(outputProfileDisplayName())}</strong>
      </div>
      <div class="preset-summary-row">
        <span>Formato</span>
        <strong>${escapeHtml(state.format)}</strong>
      </div>
      <div class="preset-summary-row">
        <span>Tamaño</span>
        <strong>${escapeHtml(state.size.replace("x", " × "))}</strong>
      </div>
      <div class="preset-summary-row">
        <span>Fondo</span>
        <strong>${escapeHtml(backgroundLabel(state.background))}</strong>
      </div>
      <div class="preset-summary-row">
        <span>Destino</span>
        <strong title="${escapeHtml(destinationText)}">${escapeHtml(destinationText)}</strong>
      </div>
      <div class="preset-summary-row">
        <span>Nombre final</span>
        <strong>${escapeHtml(namingHumanLabel())}</strong>
      </div>
      <div class="preset-summary-row">
        <span>Ejemplo</span>
        <strong title="${escapeHtml(namingExample())}">${escapeHtml(namingExample())}</strong>
      </div>
    </div>
    ${warningSummary}
    ${presetActions}
  `;

  renderExportResult();

  $("#issue-list").innerHTML = issueListHtml();
}

function renderOutputProfileSelect() {
  const select = $("#output-profile-select");
  if (!select) {
    return;
  }
  const customLabel = outputMatchesProfile() ? "" : '<option value="__custom">Personalizado sin guardar</option>';
  select.innerHTML = `
    ${state.outputProfiles.map((profile) => `
      <option value="${escapeHtml(profile.id)}">${escapeHtml(profile.name)}</option>
    `).join("")}
    ${customLabel}
  `;
  select.value = outputMatchesProfile() ? state.activeOutputProfileId : "__custom";
}

function outputProfileDisplayName() {
  const profile = activeOutputProfile();
  if (!profile || !outputMatchesProfile(profile)) {
    return "Salida personalizada";
  }
  return profile.name;
}

function outputProfileManagerRows() {
  const draft = state.outputProfileDraft;
  if (!draft || state.outputProfiles.some((profile) => profile.id === draft.id)) {
    return state.outputProfiles;
  }
  return [...state.outputProfiles, draft];
}

function outputProfileSummaryLine(profile) {
  if (!profile) {
    return "Formato sin configurar";
  }
  return `${profile.format} · ${outputProfileSize(profile).replace("x", " × ")} · ${backgroundLabel(profile.background)}`;
}

function profileDestinationLabel(profile) {
  if (!profile) {
    return "Sin destino";
  }
  if (profile.destinationMode === "custom") {
    return profile.destinationValue || "Carpeta personalizada";
  }
  return profile.destinationValue || "_SALIDA_PRO";
}

function profileDestinationPreviewLabel(profile) {
  const destination = profileDestinationLabel(profile);
  if (profile?.destinationMode === "custom") {
    return destination;
  }
  return destination ? destination : "junto al origen";
}

function ensureOutputProfileDraft() {
  const current = state.outputProfiles.find((profile) => profile.id === state.outputProfileEditorId)
    || state.outputProfileDraft
    || activeOutputProfile()
    || normalizeOutputProfile(defaultOutputProfiles[0]);
  if (!state.outputProfileEditorId) {
    state.outputProfileEditorId = current.id;
  }
  if (!state.outputProfileDraft || state.outputProfileDraft.id !== state.outputProfileEditorId) {
    state.outputProfileDraft = { ...current };
  }
  return state.outputProfileDraft;
}

function setOutputProfileFormValues(profile) {
  const pairs = [
    ["profile-name-input", profile.name],
    ["profile-format-input", profile.format],
    ["profile-background-input", profile.background],
    ["profile-width-input", profile.width],
    ["profile-height-input", profile.height],
    ["profile-destination-mode-input", profile.destinationMode],
    ["profile-suffix-input", profile.suffix],
    ["profile-destination-input", profile.destinationValue],
    ["profile-naming-input", profile.naming],
  ];
  pairs.forEach(([id, value]) => {
    const input = $(`#${id}`);
    if (input && input.value !== String(value ?? "")) {
      input.value = value ?? "";
    }
  });
}

function outputProfileFormRawData() {
  const current = ensureOutputProfileDraft();
  const value = (id, fallback = "") => {
    const input = $(`#${id}`);
    return input ? String(input.value ?? "") : String(fallback ?? "");
  };
  return {
    id: current.id,
    name: value("profile-name-input", current.name),
    format: value("profile-format-input", current.format),
    background: value("profile-background-input", current.background),
    width: value("profile-width-input", current.width),
    height: value("profile-height-input", current.height),
    destinationMode: value("profile-destination-mode-input", current.destinationMode),
    destinationValue: value("profile-destination-input", current.destinationValue),
    naming: value("profile-naming-input", current.naming),
    suffix: value("profile-suffix-input", current.suffix),
  };
}

function outputProfileDraftFromForm() {
  const current = ensureOutputProfileDraft();
  const raw = outputProfileFormRawData();
  return normalizeOutputProfile({
    id: current.id,
    name: raw.name,
    format: raw.format,
    background: raw.background,
    width: raw.width,
    height: raw.height,
    destinationMode: raw.destinationMode,
    destinationValue: raw.destinationValue,
    naming: raw.naming,
    suffix: raw.suffix,
  });
}

function updateOutputProfileDraftFromForm() {
  if (!state.appSettingsOpen) {
    return;
  }
  state.outputProfileDraft = outputProfileDraftFromForm();
}

function selectOutputProfileDraft(profileId) {
  if (state.appSettingsOpen && outputProfileHasUnsavedChanges() && !confirmDiscardOutputDraft("cambiar de formato")) {
    return;
  }
  const profile = outputProfileManagerRows().find((item) => item.id === profileId);
  if (!profile) {
    return;
  }
  state.outputProfileEditorId = profile.id;
  state.outputProfileDraft = { ...profile };
  state.statusText = `Editando formato: ${profile.name}`;
  render();
}

function newOutputProfile() {
  if (state.appSettingsOpen && outputProfileHasUnsavedChanges() && !confirmDiscardOutputDraft("crear un formato nuevo")) {
    return;
  }
  const source = currentOutputProfileData();
  const id = uniqueOutputProfileId("formato", Date.now());
  state.outputProfileEditorId = id;
  state.outputProfileDraft = {
    ...source,
    id,
    name: "Nuevo formato",
  };
  state.appSettingsOpen = true;
  state.statusText = "Nuevo formato de salida";
  render();
}

function duplicateOutputProfile() {
  if (state.appSettingsOpen && outputProfileHasUnsavedChanges() && !confirmDiscardOutputDraft("duplicar otro formato")) {
    return;
  }
  const source = state.outputProfileDraft || activeOutputProfile() || currentOutputProfileData();
  const id = uniqueOutputProfileId(source.name || "formato", Date.now());
  state.outputProfileEditorId = id;
  state.outputProfileDraft = {
    ...source,
    id,
    name: `${source.name || "Formato"} copia`,
  };
  state.appSettingsOpen = true;
  state.statusText = "Formato duplicado";
  render();
}

function commitOutputProfileDraft() {
  const validation = outputProfileValidation();
  if (validation.errors.length) {
    state.statusText = validation.errors[0];
    renderOutputProfileModalState();
    return null;
  }
  const draft = outputProfileDraftFromForm();
  const saved = normalizeOutputProfile({
    ...draft,
    name: draft.name.trim() || "Formato sin nombre",
  });
  const index = state.outputProfiles.findIndex((profile) => profile.id === saved.id);
  if (index >= 0) {
    state.outputProfiles[index] = saved;
  } else {
    state.outputProfiles.push(saved);
  }
  state.outputProfiles = dedupeOutputProfileIds(state.outputProfiles.map(normalizeOutputProfile));
  state.outputProfileEditorId = saved.id;
  state.outputProfileDraft = { ...saved };
  persistOutputProfiles();
  return state.outputProfiles.find((profile) => profile.id === saved.id) || saved;
}

function saveOutputProfile(options = {}) {
  const saved = commitOutputProfileDraft();
  if (!saved) {
    return null;
  }
  state.statusText = `Formato guardado: ${saved.name}`;
  if (options.render !== false) {
    render();
  }
  return saved;
}

function applyManagedOutputProfile() {
  const saved = saveOutputProfile({ render: false });
  if (!saved) {
    return;
  }
  state.appSettingsOpen = false;
  applyOutputProfile(saved.id, { statusText: `Salida: ${saved.name}` });
}

function deleteManagedOutputProfile() {
  const draft = ensureOutputProfileDraft();
  const exists = state.outputProfiles.some((profile) => profile.id === draft.id);
  if (!exists) {
    const fallback = activeOutputProfile() || state.outputProfiles[0];
    state.outputProfileEditorId = fallback?.id || "";
    state.outputProfileDraft = fallback ? { ...fallback } : null;
    state.statusText = "Formato descartado";
    render();
    return;
  }
  if (state.outputProfiles.length <= 1) {
    state.statusText = "Debe quedar al menos un formato";
    render();
    return;
  }
  const deletedName = draft.name;
  const confirmed = window.confirm(
    `Eliminar formato "${deletedName}"?\n\nEste formato se eliminará de los formatos guardados. No se eliminarán imágenes ni exportaciones anteriores.`
  );
  if (!confirmed) {
    return;
  }
  state.outputProfiles = state.outputProfiles.filter((profile) => profile.id !== draft.id);
  if (state.activeOutputProfileId === draft.id) {
    const next = state.outputProfiles[0];
    state.activeOutputProfileId = next.id;
    state.format = next.format;
    state.size = outputProfileSize(next);
    state.background = next.background;
    state.previewBg = next.background;
    state.destinationMode = next.destinationMode;
    state.destinationValue = next.destinationValue;
    state.naming = next.naming;
    state.suffix = next.suffix;
  }
  const nextDraft = state.outputProfiles.find((profile) => profile.id === state.activeOutputProfileId)
    || state.outputProfiles[0];
  state.outputProfileEditorId = nextDraft.id;
  state.outputProfileDraft = { ...nextDraft };
  persistOutputProfiles();
  state.statusText = `Formato eliminado: ${deletedName}`;
  render();
}

function resetOutputProfileDraft() {
  const original = state.outputProfiles.find((profile) => profile.id === state.outputProfileEditorId)
    || activeOutputProfile()
    || normalizeOutputProfile(defaultOutputProfiles[0]);
  state.outputProfileDraft = { ...original };
  state.outputProfileEditorId = original.id;
  state.statusText = "Cambios del formato descartados";
  render();
}

function openAppSettings() {
  state.batchDetailOpen = false;
  const activeProfile = activeOutputProfile();
  const profile = outputMatchesProfile(activeProfile)
    ? activeProfile
    : {
      ...currentOutputProfileData(),
      id: uniqueOutputProfileId("salida-personalizada", Date.now()),
      name: "Salida personalizada",
    };
  state.appSettingsOpen = true;
  state.outputProfileEditorId = profile.id;
  state.outputProfileDraft = { ...profile };
  state.statusText = "Configuración de salida";
  render();
}

function closeAppSettings() {
  if (state.appSettingsOpen && outputProfileHasUnsavedChanges() && !confirmDiscardOutputDraft("cerrar sin guardar")) {
    return;
  }
  state.appSettingsOpen = false;
  state.outputProfileDraft = null;
  state.statusText = "Configuración cerrada";
  render();
}

function openBatchDetail() {
  state.batchDetailOpen = true;
  state.statusText = "Detalle del lote";
  render();
}

function closeBatchDetail() {
  state.batchDetailOpen = false;
  state.statusText = hasBatch() ? "Lote cargado" : "Sin lote";
  render();
}

function confirmDiscardOutputDraft(actionLabel) {
  return window.confirm(
    `Hay cambios sin guardar.\n\nPuedes guardar los cambios, aplicar el formato al lote o ${actionLabel}.`
  );
}

function outputProfileHasUnsavedChanges() {
  if (!state.appSettingsOpen) {
    return false;
  }
  const raw = outputProfileFormRawData();
  const saved = state.outputProfiles.find((profile) => profile.id === raw.id);
  if (!saved) {
    return true;
  }
  return !sameOutputProfileRaw(saved, raw);
}

function sameOutputProfile(a, b) {
  if (!a || !b) {
    return false;
  }
  return a.name === b.name
    && a.format === b.format
    && a.width === b.width
    && a.height === b.height
    && a.background === b.background
    && a.destinationMode === b.destinationMode
    && a.destinationValue === b.destinationValue
    && a.naming === b.naming
    && a.suffix === b.suffix;
}

function sameOutputProfileRaw(profile, raw) {
  if (!profile || !raw) {
    return false;
  }
  const destinationMode = raw.destinationMode === "custom" ? "custom" : "source";
  return String(profile.name || "").trim() === String(raw.name || "").trim()
    && profile.format === normalizeExportFormat(raw.format)
    && profile.background === raw.background
    && String(profile.width) === String(raw.width || "").trim()
    && String(profile.height) === String(raw.height || "").trim()
    && profile.destinationMode === destinationMode
    && String(profile.destinationValue || "") === String(raw.destinationValue || "")
    && String(profile.naming || "") === String(raw.naming || "")
    && String(profile.suffix || "") === String(raw.suffix || "");
}

function outputProfileValidation(raw = outputProfileFormRawData()) {
  const errors = [];
  const warnings = [];
  const fields = {};
  const width = Number.parseInt(raw.width, 10);
  const height = Number.parseInt(raw.height, 10);
  const invalidFilenameChars = /[<>:"/\\|?*]/;
  const addError = (field, message) => {
    errors.push(message);
    if (field) {
      fields[field] = "error";
    }
  };
  const addWarning = (field, message) => {
    warnings.push(message);
    if (field && fields[field] !== "error") {
      fields[field] = "warning";
    }
  };

  if (!String(raw.name || "").trim()) {
    addError("name", "Pon un nombre al formato.");
  }
  if (!["JPG", "PNG"].includes(normalizeExportFormat(raw.format))) {
    addError("format", "Elige JPG o PNG como tipo de archivo.");
  }
  if (!["rgb230", "white", "transparent"].includes(raw.background)) {
    addError("background", "Elige un fondo de salida válido.");
  }
  if (!String(raw.width || "").trim() || !Number.isInteger(width) || width <= 0) {
    addError("width", "La anchura debe ser un número mayor que 0.");
  }
  if (!String(raw.height || "").trim() || !Number.isInteger(height) || height <= 0) {
    addError("height", "La altura debe ser un número mayor que 0.");
  }
  if (invalidFilenameChars.test(String(raw.suffix || ""))) {
    addError("suffix", "El sufijo contiene caracteres no válidos.");
  }
  if (!String(raw.naming || "").trim()) {
    addError("naming", "Define el nombre de archivo.");
  } else if (invalidFilenameChars.test(String(raw.naming || "").replaceAll("{original}", "").replaceAll("{suffix}", "").replaceAll("{folder}", "").replace(/\{index(?::0?\d+d)?\}/g, ""))) {
    addError("naming", "El nombre de archivo contiene caracteres no válidos.");
  } else if (!String(raw.naming || "").includes("{original}")) {
    addWarning("naming", "Incluye {original} para mantener la referencia del archivo.");
  }
  if (raw.destinationMode === "custom") {
    if (!String(raw.destinationValue || "").trim()) {
      addError("destinationValue", "Indica una carpeta de salida personalizada.");
    }
  } else if (raw.destinationMode !== "source") {
    addError("destinationMode", "Elige una ubicación de salida válida.");
  } else {
    const destination = String(raw.destinationValue || "").trim();
    if (!destination) {
      addError("destinationValue", "Indica una subcarpeta de salida.");
    } else if (destination.includes("..") || /[<>:"|?*]/.test(destination)) {
      addError("destinationValue", "La subcarpeta de salida contiene caracteres no válidos.");
    }
  }
  return { errors: Array.from(new Set(errors)), warnings: Array.from(new Set(warnings)), fields };
}

function outputProfileEditorHeadingHtml(profile, validation, dirty) {
  const active = profile.id === state.activeOutputProfileId;
  const status = dirty
    ? "Cambios sin guardar"
    : active
      ? "Activo en este lote"
      : "Formato guardado";
  return `
    <div class="format-editor-title">
      <div>
        <span class="eyebrow">Formato editado</span>
        <strong>${escapeHtml(profile.name || "Formato sin nombre")}</strong>
        <small>${escapeHtml(outputProfileSummaryLine(profile))}</small>
      </div>
      <span class="status-badge ${validation.errors.length ? "error" : dirty ? "warning" : active ? "ready" : ""}">${escapeHtml(validation.errors.length ? "Revisar campos" : status)}</span>
    </div>
  `;
}

function outputProfilePreviewHtml(profile) {
  const image = selectedImage();
  const originalName = image?.name || "imagen_original.png";
  const resultName = outputNameForProfile(profile, image);
  const destination = profileDestinationPreviewLabel(profile);
  const resultPath = destination && destination !== "junto al origen"
    ? `${destination.replace(/[\\/]$/, "")}/${resultName}`
    : resultName;
  return `
    <div class="format-preview-heading">
      <span class="eyebrow">Ejemplo de exportación</span>
      <strong>${escapeHtml(resultName)}</strong>
    </div>
    <div class="format-preview-grid">
      <div>
        <span>Original</span>
        <strong title="${escapeHtml(originalName)}">${escapeHtml(originalName)}</strong>
      </div>
      <div>
        <span>Resultado</span>
        <strong title="${escapeHtml(resultPath)}">${escapeHtml(resultPath)}</strong>
      </div>
      <div>
        <span>Formato</span>
        <strong>${escapeHtml(outputProfileSummaryLine(profile))}</strong>
      </div>
      <div>
        <span>Destino</span>
        <strong title="${escapeHtml(destination)}">${escapeHtml(destination)}</strong>
      </div>
    </div>
  `;
}

function outputNameForProfile(profile, image = selectedImage(), index = 1) {
  const original = imageFileStem(image?.name || "imagen_original.png");
  const folder = activeFolders().find((item) => item.id === image?.folderId)?.name
    || activeFolders()[0]?.name
    || "lote";
  let outputName = String(profile.naming || "{original}{suffix}")
    .replaceAll("{original}", original)
    .replaceAll("{suffix}", profile.suffix || "")
    .replaceAll("{folder}", folder);
  outputName = outputName.replace(/\{index(?::0?(\d+)d)?\}/g, (_match, width) => {
    const digits = Number(width) || 1;
    return String(index).padStart(digits, "0");
  });
  if (!/\.[a-z0-9]+$/i.test(outputName)) {
    outputName = `${outputName}.${profile.format.toLowerCase()}`;
  }
  return outputName;
}

function outputProfileValidationHtml(validation) {
  if (!validation.errors.length && !validation.warnings.length) {
    return "";
  }
  const rows = [
    ...validation.errors.map((message) => ({ tone: "error", message })),
    ...validation.warnings.map((message) => ({ tone: "warning", message })),
  ];
  return `
    <strong>${validation.errors.length ? "Revisa el formato" : "Aviso"}</strong>
    ${rows.map((row) => `<span class="${escapeHtml(row.tone)}">${escapeHtml(row.message)}</span>`).join("")}
  `;
}

function renderOutputProfileModalState() {
  const raw = outputProfileFormRawData();
  const profile = outputProfileDraftFromForm();
  state.outputProfileDraft = profile;
  const validation = outputProfileValidation(raw);
  const dirty = outputProfileHasUnsavedChanges();
  const heading = $("#output-profile-editor-heading");
  if (heading) {
    heading.innerHTML = outputProfileEditorHeadingHtml(profile, validation, dirty);
  }
  const preview = $("#output-profile-preview");
  if (preview) {
    preview.innerHTML = outputProfilePreviewHtml(profile);
  }
  const validationTarget = $("#output-profile-validation");
  if (validationTarget) {
    validationTarget.innerHTML = outputProfileValidationHtml(validation);
    validationTarget.hidden = !validation.errors.length && !validation.warnings.length;
  }
  updateOutputProfileFieldStates(validation, raw);
  updateOutputProfileFooterState(validation, dirty);
}

function updateOutputProfileFieldStates(validation, raw) {
  const fieldIds = {
    name: "profile-name-input",
    format: "profile-format-input",
    background: "profile-background-input",
    width: "profile-width-input",
    height: "profile-height-input",
    destinationMode: "profile-destination-mode-input",
    destinationValue: "profile-destination-input",
    naming: "profile-naming-input",
    suffix: "profile-suffix-input",
  };
  Object.entries(fieldIds).forEach(([field, id]) => {
    const input = $(`#${id}`);
    if (!input) {
      return;
    }
    const tone = validation.fields[field];
    input.classList.toggle("is-invalid", tone === "error");
    input.classList.toggle("has-warning", tone === "warning");
    input.setAttribute("aria-invalid", tone === "error" ? "true" : "false");
  });

  const destinationInput = $("#profile-destination-input");
  if (destinationInput) {
    destinationInput.placeholder = raw.destinationMode === "custom"
      ? "Ej. C:\\Exports\\FlatShot"
      : "_SALIDA_PRO";
  }
}

function updateOutputProfileFooterState(validation, dirty) {
  const draft = ensureOutputProfileDraft();
  const isPersisted = state.outputProfiles.some((profile) => profile.id === draft.id);
  const deleteButton = $("[data-action='delete-output-profile']");
  if (deleteButton) {
    deleteButton.disabled = isPersisted && state.outputProfiles.length <= 1;
    deleteButton.title = deleteButton.disabled ? "Debe quedar al menos un formato" : "Eliminar formato seleccionado";
  }
  const resetButton = $("[data-action='reset-output-profile-draft']");
  if (resetButton) {
    resetButton.disabled = !dirty;
  }
  const saveButton = $("[data-action='save-output-profile']");
  if (saveButton) {
    saveButton.disabled = validation.errors.length > 0 || !dirty;
  }
  const applyButton = $("[data-action='apply-output-profile']");
  if (applyButton) {
    applyButton.disabled = validation.errors.length > 0;
    applyButton.textContent = dirty ? "Guardar y aplicar" : "Aplicar al lote";
  }
  const footerNote = $("#output-profile-unsaved");
  if (footerNote) {
    footerNote.textContent = validation.errors.length
      ? validation.errors[0]
      : dirty
        ? "Cambios sin guardar"
        : "Sin cambios pendientes";
    footerNote.className = `settings-footer-note ${validation.errors.length ? "error" : dirty ? "warning" : ""}`;
  }
}

function renderAppSettings() {
  const modal = $("#app-settings-modal");
  if (!modal) {
    return;
  }
  modal.classList.toggle("is-hidden", !state.appSettingsOpen);
  modal.setAttribute("aria-hidden", state.appSettingsOpen ? "false" : "true");
  if (!state.appSettingsOpen) {
    return;
  }

  const draft = ensureOutputProfileDraft();
  const rows = outputProfileManagerRows();
  $("#output-profile-list").innerHTML = rows.map((profile) => {
    const selected = profile.id === draft.id;
    const active = profile.id === state.activeOutputProfileId;
    const unsaved = !state.outputProfiles.some((item) => item.id === profile.id);
    return `
      <button type="button" class="output-profile-option${selected ? " selected" : ""}${active ? " active" : ""}" data-output-profile-id="${escapeHtml(profile.id)}">
        <span>
          <strong>${escapeHtml(profile.name)}</strong>
          <small>${escapeHtml(outputProfileSummaryLine(profile))}</small>
          <small>${escapeHtml(profileDestinationLabel(profile))}</small>
        </span>
        <em>${escapeHtml(unsaved ? "Sin guardar" : active ? "En uso" : profileDestinationLabel(profile))}</em>
      </button>
    `;
  }).join("");
  setOutputProfileFormValues(draft);
  renderOutputProfileModalState();
}

function presetSummaryLine() {
  return `${state.format} · ${state.size} · ${backgroundLabel(state.background)}`;
}

function destinationCompactLabel() {
  if (state.destinationMode === "custom") {
    return state.destinationValue || "Sin destino";
  }
  return state.destinationValue || "_SALIDA_PRO";
}

function namingHumanLabel() {
  if (state.naming === "{original}{suffix}") {
    return state.suffix ? `original + ${state.suffix}` : "original";
  }
  return state.naming || "Sin plantilla";
}

function outputWarningSummary(issues) {
  const warnings = issues.filter((issue) => issue.title !== "Sin lote");
  if (!warnings.length) {
    return "";
  }
  const hasBlocking = warnings.some((issue) => issue.level === "error");
  if (!hasBlocking) {
    return "";
  }
  const first = firstActionableIssue() || warnings[0];
  const count = Math.max(warnings.length, visibleWarningCount());
  const fileLine = first.file ? `<span title="${escapeHtml(first.path || first.file)}">${escapeHtml(first.file)}</span>` : "";
  const detail = first.file ? `Motivo: ${first.detail}` : `${first.title}${first.detail ? `: ${first.detail}` : ""}`;
  return `
    <div class="warning-summary ${warnings.some((issue) => issue.level === "error") ? "error" : ""}">
      <strong>${count} aviso${count === 1 ? "" : "s"}</strong>
      ${fileLine}
      <span>${escapeHtml(detail)}</span>
      <button type="button" data-action="review-errors">Revisar aviso</button>
    </div>
  `;
}

function issueListHtml() {
  if (!hasBatch() && state.batch !== "empty") {
    return "";
  }
  const rows = issueRows();
  const counts = preflightCounts();
  const warningCount = visibleWarningCount();
  const canExportWithWarnings = isExportReady() && warningCount > 0 && counts.errors === 0 && state.exportStatus !== "running";
  const footerAction = canExportWithWarnings
    ? '<button type="button" class="primary" data-action="start-export">Exportar igualmente</button>'
    : counts.errors
      ? '<button type="button" class="primary" data-action="edit-output">Revisar salida</button>'
      : "";
  if (!rows.length) {
    return `
      <div class="issue-list-summary ready issue-list-summary--compact">
        <strong>Sin avisos</strong>
      </div>
    `;
  }
  return `
    <div class="issue-list-summary ${counts.errors ? "error" : "warning"}">
      <strong>${escapeHtml(counts.errors ? `${counts.errors} bloqueo${counts.errors === 1 ? "" : "s"}` : `${warningCount || rows.length} aviso${(warningCount || rows.length) === 1 ? "" : "s"}`)}</strong>
      <span>${escapeHtml(counts.errors ? "Resuelve los bloqueos antes de exportar." : "Puedes revisar las imágenes o exportar igualmente.")}</span>
    </div>
    ${rows.slice(0, 8).map(issueItemHtml).join("")}
    ${footerAction ? `<div class="inspector-actionbar warning-actions">${footerAction}</div>` : ""}
  `;
}

function issueRows() {
  const rows = [];
  (state.scanDiagnostics?.omitted || []).slice(0, 4).forEach((item) => {
    rows.push({
      level: "warning",
      title: item.name || "Archivo omitido",
      detail: `Motivo: ${item.detail || omissionReasonLabel(item.reason)}`,
      path: item.path || item.folder || "",
      actionLabel: "",
    });
  });
  activeImages()
    .filter((image) => image.status === "warning" || image.status === "error" || exportItemState(image)?.status === "error")
    .forEach((image) => {
      rows.push({
        level: image.status === "error" || exportItemState(image)?.status === "error" ? "error" : "warning",
        title: image.name,
        detail: image.detail || statusLabels[image.status] || "Revisar imagen",
        path: image.path || "",
        imageId: image.id,
        actionLabel: "Ir a imagen",
      });
    });
  state.errors.slice(0, 4).forEach((issue) => {
    rows.push({
      level: issue.level,
      title: issue.title,
      detail: issue.detail,
      path: "",
      actionLabel: "",
    });
  });
  return rows;
}

function issueItemHtml(row) {
  const action = row.imageId
    ? `<button type="button" data-action="select-image-id" data-image-id="${escapeHtml(row.imageId)}">${escapeHtml(row.actionLabel || "Ir a imagen")}</button>`
    : "";
  return `
    <div class="issue-item ${row.level === "error" ? "error" : "warning"}" title="${escapeHtml(row.path || row.detail || row.title)}">
      <div>
        <strong>${escapeHtml(row.title)}</strong>
        <span>${escapeHtml(row.detail || "Revisar")}</span>
      </div>
      ${action}
    </div>
  `;
}

function exportStatusClass(ready, issues = preflightIssues()) {
  if (state.exportStatus === "failed" || issues.some((issue) => issue.level === "error")) {
    return "error";
  }
  if (state.exportStatus === "running") {
    return "running";
  }
  if (state.exportStatus === "partial" || issues.length || (hasBatch() && !ready)) {
    return "warning";
  }
  return ready ? "ready" : "pending";
}

function exportPreflightRows(issues, exportable, ready) {
  if (state.batch === "none") {
    return [
      { state: "error", title: "Carpeta de origen", detail: "Elige una carpeta para empezar" },
      { state: "pending", title: "Imágenes exportables", detail: "Pendiente" },
      { state: "pending", title: "Carpeta de salida", detail: destinationFallbackLabel() },
    ];
  }
  if (state.batch === "empty") {
    return [
      { state: "error", title: "Imágenes exportables", detail: "0 imágenes" },
      { state: state.scanDiagnostics.totalOmitted ? "warning" : "pending", title: "Avisos", detail: omittedSummaryText(state.scanDiagnostics) },
      { state: "pending", title: "Carpeta de salida", detail: "Pendiente" },
    ];
  }
  const rows = [
    { state: exportable > 0 ? "ok" : "error", title: "Imágenes exportables", detail: `${exportable} imagen${exportable === 1 ? "" : "es"}` },
    { state: state.scanDiagnostics.totalOmitted ? "warning" : "ok", title: "Avisos", detail: state.scanDiagnostics.totalOmitted ? omittedSummaryText(state.scanDiagnostics) : "Sin avisos" },
    { state: state.destinationMode === "custom" && !state.destinationValue.trim() ? "error" : "ok", title: "Carpeta de salida", detail: destinationFallbackLabel() },
    { state: state.naming.trim() ? "ok" : "error", title: "Nombre de archivo", detail: state.naming.trim() ? namingExample() : "Plantilla vacía" },
  ];
  issues
    .filter((issue) => !["Sin lote", "No hay imágenes válidas", "Nombre de archivo vacío", "Carpeta de salida sin configurar", "Sin imágenes exportables"].includes(issue.title))
    .forEach((issue) => {
      rows.push({ state: issue.level === "error" ? "error" : "warning", title: issue.title, detail: issue.detail });
    });
  if (ready && !issues.length) {
    rows.push({ state: "ok", title: "Preflight", detail: "Sin bloqueos ni avisos" });
  }
  return rows;
}

function preflightListHtml(rows) {
  return `
    <div class="preflight-list">
      ${rows.map((row) => `
        <div class="preflight-item ${escapeHtml(row.state)}">
          <span aria-hidden="true"></span>
          <div>
            <strong>${escapeHtml(row.title)}</strong>
            <small title="${escapeHtml(row.detail)}">${escapeHtml(row.detail)}</small>
          </div>
        </div>
      `).join("")}
    </div>
  `;
}

function exportPanelStatusLabel(ready, issues = preflightIssues()) {
  if (state.exportStatus === "running") {
    return state.paused ? "Pausado" : "Exportando";
  }
  if (state.exportStatus === "completed") {
    return "Exportado";
  }
  if (state.exportStatus === "partial") {
    return "Exportado con avisos";
  }
  if (state.exportStatus === "failed") {
    return "Revisar antes de exportar";
  }
  if (issues.some((issue) => issue.level === "error")) {
    return "Revisar antes de exportar";
  }
  if (state.batch === "empty" || (hasBatch() && !ready)) {
    return "Pendiente";
  }
  if (ready && issues.length) {
    return `${issues.length} aviso${issues.length === 1 ? "" : "s"} antes de exportar`;
  }
  return ready ? "Listo para exportar" : "Configura salida";
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
    .replaceAll("{suffix}", state.suffix || "_PRO")
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
    return state.destinationValue || "Carpeta de salida sin configurar";
  }
  return state.destinationValue || "_SALIDA_PRO";
}

function beginOutputEdit() {
  state.outputDraft = {
    format: state.format,
    size: state.size,
    background: state.background,
    destinationMode: state.destinationMode,
    destinationValue: state.destinationValue,
    naming: state.naming,
    suffix: state.suffix,
  };
  state.outputEditMode = true;
  state.presetEditorOpen = false;
  state.inspectorTab = "output";
  state.statusText = "Editando salida";
  render();
}

function applyOutputEdit() {
  state.outputDraft = null;
  state.outputEditMode = false;
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = "Salida actualizada";
  render();
}

function cancelOutputEdit() {
  if (state.outputDraft) {
    Object.assign(state, state.outputDraft);
  }
  state.outputDraft = null;
  state.outputEditMode = false;
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = "Edición cancelada";
  render();
}

async function saveCurrentPreset() {
  const presetName = state.activePreset;
  const presetSettings = normalizeSettings(state.settings);
  const outputSettings = {
    format: state.format,
    size: state.size,
    background: state.background,
    destinationMode: state.destinationMode,
    destinationValue: state.destinationValue,
    naming: state.naming,
    suffix: state.suffix,
  };
  state.presetOutputSettings[presetName] = outputSettings;

  if (state.bridgeMode === "bridge") {
    state.statusText = "Guardando ajuste";
    render();
    try {
      const payload = await bridgeRequest("/presets/save", {
        method: "POST",
        body: JSON.stringify({
          name: presetName,
          settings: presetSettings,
        }),
        timeoutMs: 8000,
      });
      applyBridgePresets(payload);
    } catch (error) {
      state.presetDirty = true;
      state.statusText = `No se pudo guardar el ajuste: ${bridgeErrorMessage(error)}`;
      render();
      return;
    }
  }

  updatePresetCache(presetName, presetSettings);

  state.presetDirty = false;
  state.presetSource = "Salida";
  state.outputDraft = null;
  state.outputEditMode = false;
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = "Ajuste guardado";
  render();
}

function presetsExportPayload() {
  const categories = {};
  const uncategorized = {};
  activePresetItems().forEach((preset) => {
    const settings = normalizeSettings(preset.settings);
    const categoryId = preset.categoryId && preset.categoryId !== "uncategorized"
      ? preset.categoryId
      : "";
    if (!categoryId) {
      uncategorized[preset.name] = settings;
      return;
    }
    if (!categories[categoryId]) {
      categories[categoryId] = {
        name: preset.category || categoryId,
        presets: {},
      };
    }
    categories[categoryId].presets[preset.name] = settings;
  });
  return {
    flatshot_export: {
      type: "presets",
      version: 1,
      exported_at: new Date().toISOString(),
      preset_count: activePresetItems().length,
    },
    presets: {
      categories,
      uncategorized,
    },
  };
}

function exportPresetCollection() {
  const payload = presetsExportPayload();
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  const stamp = new Date().toISOString().slice(0, 10).replaceAll("-", "");
  link.href = url;
  link.download = `flatshot-ajustes-${stamp}.json`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
  state.statusText = `${payload.flatshot_export.preset_count} ajustes exportados`;
  render();
}

async function deleteActivePreset() {
  const presets = activePresetItems();
  if (presets.length <= 1) {
    state.statusText = "Debe quedar al menos un ajuste";
    render();
    return;
  }
  const presetName = state.activePreset;
  const nextPreset = presets.find((preset) => preset.name !== presetName)?.name || presets[0]?.name;
  if (!window.confirm(`Eliminar el ajuste "${presetName}"?`)) {
    return;
  }

  if (state.bridgeMode === "bridge") {
    state.statusText = "Eliminando ajuste";
    render();
    try {
      const payload = await bridgeRequest("/presets/delete", {
        method: "POST",
        body: JSON.stringify({ name: presetName }),
        timeoutMs: 8000,
      });
      applyBridgePresets(payload);
      const preferred = payload.activePreset || nextPreset;
      if (preferred) {
        applyPresetSettings(preferred, { refresh: false, statusText: `Ajuste eliminado: ${presetName}` });
      }
    } catch (error) {
      state.statusText = `No se pudo eliminar el ajuste: ${bridgeErrorMessage(error)}`;
      render();
      return;
    }
  } else {
    removePresetFromCache(presetName);
    if (nextPreset) {
      applyPresetSettings(nextPreset, { refresh: false, statusText: `Ajuste eliminado: ${presetName}` });
    }
  }

  state.presetDirty = false;
  state.outputDraft = null;
  state.outputEditMode = false;
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  render();
}

function openPresetEditor() {
  state.presetEditorOpen = true;
  state.outputEditMode = false;
  state.inspectorTab = "advanced";
  state.statusText = "Cambia o ajusta el ajuste activo";
  render();
}

function closePresetEditor() {
  state.presetEditorOpen = false;
  state.inspectorTab = "output";
  state.statusText = "Ajuste aplicado";
  render();
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
  return ready ? "Lista" : "Configura salida";
}

function backgroundLabel(value) {
  if (value === "transparent") {
    return "Transparente";
  }
  if (value === "white") {
    return "Blanco";
  }
  return "Gris claro · RGB 230";
}

function renderFooter() {
  const issues = [...validationIssues(), ...state.errors];
  const visible = getVisibleAppState();
  const counts = batchCounts();
  $("#footer-statusline").textContent = statusBarText();
  $("#bottom-status").textContent = state.statusText;
  $("#progress-fill").style.width = `${state.progress}%`;
  $("#progress-fill").className = state.exportStatus === "failed" ? "error" : state.exportStatus === "partial" ? "warning" : "";
  $(".progress-track").classList.toggle("is-idle", state.exportStatus !== "running");

  const hasReviewIssues = (hasBatch() || state.batch === "empty") && (
    issues.some((issue) => issue.title !== "Sin lote")
    || counts.omittedFiles > 0
    || activeImages().some((image) => image.status === "error" || image.status === "warning" || exportItemState(image)?.status === "error")
  );
  $("#review-errors").classList.toggle("is-hidden", !hasReviewIssues);
  $("#review-errors").disabled = !hasReviewIssues;
  $("#review-errors").textContent = "Ver avisos";
  $("#pause-export").classList.toggle("is-hidden", state.exportStatus !== "running");
  $("#pause-export").textContent = state.paused ? "Reanudar" : "Pausar";
  $("#stop-export").classList.toggle("is-hidden", state.exportStatus !== "running");
  $("#open-output").classList.add("is-hidden");
  $("#open-output").disabled = true;
  $("#primary-action").classList.add("is-hidden");

  const primaryButtons = [$("#primary-action"), $("#top-primary-action")].filter(Boolean);
  const primaryActionState = visible.primaryAction || {};
  primaryButtons.forEach((button) => {
    button.disabled = primaryActionState.enabled === false;
    button.textContent = primaryActionState.label || "Seleccionar carpeta";
    button.title = visible.subtitle || primaryActionState.label || "";
  });
}

function statusBarText() {
  const images = activeImages();
  const counts = batchCounts();
  const selectedIndex = images.findIndex((image) => image.id === state.selectedImageId);
  const selectedText = selectedIndex >= 0 ? `Imagen ${selectedIndex + 1}/${images.length}` : "Sin selección";
  const destination = state.destinationMode === "custom"
    ? state.destinationValue || "sin destino"
    : `origen / ${state.destinationValue}`;

  if (state.exportStatus === "running") {
    const total = exportableImages().length;
    return `${state.paused ? "Pausado" : "Exportando"} ${state.processed}/${total} · ${state.statusText}`;
  }
  if (state.exportStatus === "completed") {
    const total = Number(state.exportResult?.total ?? exportableImages().length ?? 0);
    const processed = Number(state.exportResult?.processed ?? total);
    return `Última exportación completada · ${processed}/${total} archivos`;
  }
  if (state.exportStatus === "partial") {
    const total = Number(state.exportResult?.total ?? exportableImages().length ?? 0);
    const processed = Number(state.exportResult?.processed ?? state.processed ?? 0);
    return `Última exportación con avisos · ${processed}/${total} archivos`;
  }
  if (state.exportStatus === "failed") {
    return `Exportación fallida · ${state.errors[0]?.detail || "Revisa avisos"}`;
  }
  if (state.batch === "none") {
    return "Sin lote · Elige una carpeta para empezar";
  }
  if (state.batch === "scanning") {
    return `Escaneando · ${state.scanStatus}`;
  }
  if (state.batch === "empty") {
    return `0 imágenes · ${state.scanStatus || "Cambia de carpeta"}`;
  }
  const warningText = counts.nonBlockingWarnings ? ` · ${countText(counts.nonBlockingWarnings, "aviso", "avisos")}` : "";
  return `${counts.exportableImages} exportables · ${selectedText}${warningText} · Salida: ${destination}`;
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

function handleAction(action, target = null) {
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
      state.statusText = "Vista no disponible";
      render();
    }
  } else if (action === "previous-image") {
    selectAdjacentImage(-1);
  } else if (action === "next-image") {
    selectAdjacentImage(1);
  } else if (action === "clear-filter") {
    clearFilter();
  } else if (action === "clear-search") {
    state.search = "";
    state.statusText = filterStatusText(state.filter);
    render();
  } else if (action === "select-first-image") {
    const image = filteredImages()[0] || activeImages()[0];
    if (image) {
      selectImage(image.id);
    }
  } else if (action === "select-image-id") {
    const imageId = target?.dataset?.imageId;
    if (imageId) {
      state.inspectorTab = "review";
      selectImage(imageId);
    }
  } else if (action === "open-advanced") {
    state.inspectorTab = "advanced";
    state.statusText = "Ajustes avanzados";
    render();
  } else if (action === "edit-output") {
    beginOutputEdit();
  } else if (action === "apply-output-edit") {
    applyOutputEdit();
  } else if (action === "cancel-output-edit") {
    cancelOutputEdit();
  } else if (action === "open-app-settings") {
    openAppSettings();
  } else if (action === "close-app-settings") {
    closeAppSettings();
  } else if (action === "open-batch-detail") {
    openBatchDetail();
  } else if (action === "close-batch-detail") {
    closeBatchDetail();
  } else if (action === "new-output-profile") {
    newOutputProfile();
  } else if (action === "duplicate-output-profile") {
    duplicateOutputProfile();
  } else if (action === "reset-output-profile-draft") {
    resetOutputProfileDraft();
  } else if (action === "delete-output-profile") {
    deleteManagedOutputProfile();
  } else if (action === "save-output-profile") {
    saveOutputProfile();
  } else if (action === "apply-output-profile") {
    applyManagedOutputProfile();
  } else if (action === "open-preset-editor") {
    openPresetEditor();
  } else if (action === "close-preset-editor") {
    closePresetEditor();
  } else if (action === "zoom-fit") {
    setViewerMode("fit");
  } else if (action === "zoom-height") {
    setViewerMode("height");
  } else if (action === "zoom-width") {
    setViewerMode("width");
  } else if (action === "zoom-100") {
    resetViewerPan();
    setViewerZoom(100);
  } else if (action === "zoom-in") {
    setViewerZoom(Math.round(currentViewerZoom() / 10) * 10 + 10);
  } else if (action === "zoom-out") {
    setViewerZoom(Math.round(currentViewerZoom() / 10) * 10 - 10);
  } else if (action === "reset-settings") {
    resetActivePresetSettings();
  } else if (action === "save-preset") {
    void saveCurrentPreset();
  } else if (action === "export-presets") {
    exportPresetCollection();
  } else if (action === "delete-preset") {
    void deleteActivePreset();
  } else if (action === "toggle-local-adjustment") {
    state.localOverride = !state.localOverride;
    state.statusText = state.localOverride ? "Ajuste local activo" : "Ajuste local quitado";
    render();
  } else if (action === "reset-local-adjustment") {
    resetCurrentImageOverride();
  } else if (action === "pause-export") {
    pauseExport();
  } else if (action === "stop-export") {
    stopExport();
  } else if (action === "start-export") {
    startExport();
  } else if (action === "review-errors") {
    reviewWarnings();
  } else if (action === "open-output") {
    openOutputFolder();
  } else if (action === "primary") {
    primaryAction();
  } else if (action === "secondary-primary") {
    runVisibleAction(getVisibleAppState().secondaryAction?.action);
  }
}

document.addEventListener("load", (event) => {
  const target = event.target;
  if (target instanceof HTMLImageElement && target.classList.contains("thumb-image")) {
    recordThumbnailLoad(target);
  }
  if (target instanceof HTMLImageElement && target.classList.contains("preview-image")) {
    updatePreviewDebugPanel();
  }
}, true);

document.addEventListener("error", (event) => {
  const target = event.target;
  if (target instanceof HTMLImageElement && target.classList.contains("thumb-image")) {
    recordThumbnailError(target);
  }
  if (target instanceof HTMLImageElement && target.classList.contains("preview-image")) {
    state.previewStatus = "error";
    state.previewError = "No se pudo cargar la preview renderizada";
    state.statusText = "Vista no disponible";
    render();
  }
}, true);

function recordThumbnailLoad(imageElement) {
  const imageId = imageElement.dataset.imageId;
  if (!imageId) {
    return;
  }
  const loadedSrc = imageElement.currentSrc || imageElement.src;
  const current = state.thumbnailStatus[imageId];
  markThumbnailLoaded(
    imageId,
    current?.sourceSrc || loadedSrc,
    imageElement.naturalWidth,
    imageElement.naturalHeight,
    loadedSrc
  );
}

function recordThumbnailError(imageElement) {
  const imageId = imageElement.dataset.imageId;
  const src = imageElement.currentSrc || imageElement.src;
  if (!imageId) {
    return;
  }
  markThumbnailError(imageId, src);
}

document.addEventListener("pointerdown", (event) => {
  if (event.target.closest?.(".settings-panel details > summary")) {
    inspectorScrollTopBeforeToggle = $(".settings-panel")?.scrollTop || 0;
  }
}, true);

document.addEventListener("click", (event) => {
  const disclosureSummary = event.target.closest?.(".settings-panel details.inspector-disclosure > summary");
  if (!disclosureSummary) {
    return;
  }
  const panel = $(".settings-panel");
  const details = disclosureSummary.closest("details");
  inspectorScrollTopBeforeToggle = panel?.scrollTop || 0;
  event.preventDefault();
  event.stopImmediatePropagation();
  toggleInspectorDisclosure(details);
  disclosureSummary.blur();
}, true);

document.addEventListener("click", (event) => {
  const disclosureSummary = event.target.closest(".settings-panel details > summary");
  if (disclosureSummary) {
    const details = disclosureSummary.closest("details");
    if (details?.classList.contains("inspector-disclosure")) {
      event.preventDefault();
      toggleInspectorDisclosure(details);
      return;
    }
  }

  if (event.target.id === "app-settings-modal") {
    closeAppSettings();
    return;
  }

  if (event.target.id === "batch-detail-modal") {
    closeBatchDetail();
    return;
  }

  const actionTarget = event.target.closest("[data-action]");
  if (actionTarget) {
    handleAction(actionTarget.dataset.action, actionTarget);
    return;
  }

  const outputProfileTarget = event.target.closest("[data-output-profile-id]");
  if (outputProfileTarget) {
    selectOutputProfileDraft(outputProfileTarget.dataset.outputProfileId);
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

  const galleryViewTarget = event.target.closest("[data-gallery-view]");
  if (galleryViewTarget) {
    state.galleryView = galleryViewTarget.dataset.galleryView === "list" ? "list" : "thumbs";
    state.statusText = state.galleryView === "list" ? "Galería en lista" : "Galería en miniaturas";
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
    if (state.inspectorTab === "output") {
      state.presetEditorOpen = false;
    }
    render();
  }
});

document.addEventListener("toggle", (event) => {
  if (!event.target.matches?.(".settings-panel details.inspector-disclosure")) {
    return;
  }
  const panel = $(".settings-panel");
  if (!panel) {
    return;
  }
  const restoreScroll = () => {
    panel.scrollTop = inspectorScrollTopBeforeToggle;
  };
  window.requestAnimationFrame(() => {
    restoreScroll();
    window.requestAnimationFrame(restoreScroll);
    window.setTimeout(restoreScroll, 0);
    window.setTimeout(restoreScroll, 80);
    window.setTimeout(restoreScroll, 180);
  });
}, true);

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
  state.statusText = state.bridgeMode === "bridge" ? "Conexión local" : "Modo demo";
  state.bridgeLastResponse = state.bridgeMode === "bridge" ? "Conexión pendiente" : "Demo activo";
  state.scanStatus = state.bridgeMode === "bridge" ? "Sin lote" : "Escenarios mock activos.";
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

document.addEventListener("input", (event) => {
  if (event.target.id === "onboarding-scan-path") {
    state.bridgeScanPath = event.target.value;
    const sidebarInput = $("#bridge-scan-path");
    if (sidebarInput) {
      sidebarInput.value = state.bridgeScanPath;
    }
  }
  const localKey = event.target?.dataset?.localSetting;
  if (localKey) {
    setCurrentImageOverrideValue(localKey, event.target.value);
  }
  if (event.target.closest?.("#output-profile-form")) {
    updateOutputProfileDraftFromForm();
    renderOutputProfileModalState();
  }
});

document.addEventListener("change", (event) => {
  if (event.target.closest?.("#output-profile-form")) {
    updateOutputProfileDraftFromForm();
    renderOutputProfileModalState();
  }
});

document.addEventListener("submit", (event) => {
  if (event.target.id === "output-profile-form") {
    event.preventDefault();
    saveOutputProfile();
  }
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
  state.format = normalizeExportFormat(event.target.value);
  state.statusText = `Formato: ${state.format}`;
  render();
});

$("#output-profile-select").addEventListener("change", (event) => {
  if (event.target.value === "__custom") {
    return;
  }
  applyOutputProfile(event.target.value);
});

$("#size-select").addEventListener("input", (event) => {
  state.size = event.target.value;
});

$("#size-select").addEventListener("change", (event) => {
  state.size = parseOutputSize(event.target.value).normalized;
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
  state.statusText = state.destinationMode === "custom" ? "Carpeta de salida sin configurar" : "Salida junto al origen";
  render();
});

$("#destination-input").addEventListener("input", (event) => {
  state.destinationValue = event.target.value;
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = state.destinationValue.trim() ? "Carpeta de salida configurada" : "Carpeta de salida sin configurar";
  render();
});

$("#naming-input").addEventListener("input", (event) => {
  state.naming = event.target.value;
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = state.naming.trim() ? "Nombre de archivo actualizado" : "Nombre de archivo vacío";
  render();
});

document.addEventListener("keydown", (event) => {
  const target = event.target;
  const isTyping = target instanceof HTMLInputElement
    || target instanceof HTMLTextAreaElement
    || target instanceof HTMLSelectElement
    || target?.isContentEditable;
  const command = event.ctrlKey || event.metaKey;

  if (command && event.key.toLowerCase() === "f") {
    event.preventDefault();
    const search = $("#image-search");
    if (search && hasBatch()) {
      search.focus();
      search.select();
    }
    return;
  }

  if (command && event.key.toLowerCase() === "e") {
    event.preventDefault();
    if (isExportReady() && state.exportStatus !== "running") {
      startExport();
    }
    return;
  }

  if (event.key === "Escape") {
    if (state.batchDetailOpen) {
      closeBatchDetail();
      event.preventDefault();
      return;
    }
    if (state.appSettingsOpen) {
      closeAppSettings();
      event.preventDefault();
      return;
    }
    const openDetails = Array.from(document.querySelectorAll("details[open]")).reverse()[0];
    if (openDetails) {
      openDetails.open = false;
      event.preventDefault();
    }
    return;
  }

  if (isTyping) {
    return;
  }

  const key = event.key.toLowerCase();
  if (event.key === "ArrowLeft") {
    event.preventDefault();
    selectAdjacentImage(-1);
  } else if (event.key === "ArrowRight") {
    event.preventDefault();
    selectAdjacentImage(1);
  } else if (key === "f" && isViewerNavigationAvailable()) {
    event.preventDefault();
    setViewerMode("fit");
  } else if (key === "1" && isViewerNavigationAvailable()) {
    event.preventDefault();
    resetViewerPan();
    setViewerZoom(100);
  }
});

function handleViewerWheel(event) {
  if (!isViewerNavigationAvailable()) {
    return;
  }
  event.preventDefault();
  const baseZoom = currentViewerZoom();
  const direction = event.deltaY < 0 ? 1 : -1;
  const step = event.shiftKey ? 5 : 10;
  setViewerZoom(baseZoom + direction * step, event);
}

function handleViewerPointerDown(event) {
  if (
    event.button !== 0
    || !isViewerNavigationAvailable()
    || event.target.closest("button, input, textarea, select, summary, a")
  ) {
    return;
  }
  const canvas = $("#preview-canvas");
  viewerPanState.active = true;
  viewerPanState.pointerId = event.pointerId;
  viewerPanState.startX = event.clientX;
  viewerPanState.startY = event.clientY;
  viewerPanState.originX = state.panX;
  viewerPanState.originY = state.panY;
  canvas?.classList.add("is-panning");
  try {
    canvas?.setPointerCapture(event.pointerId);
  } catch (error) {
    // Pointer capture is optional; document-level listeners continue the drag.
  }
}

function handleViewerPointerMove(event) {
  if (!viewerPanState.active || event.pointerId !== viewerPanState.pointerId) {
    return;
  }
  state.panX = viewerPanState.originX + event.clientX - viewerPanState.startX;
  state.panY = viewerPanState.originY + event.clientY - viewerPanState.startY;
  applyViewerPanDom();
}

function handleViewerPointerEnd(event) {
  if (!viewerPanState.active || event.pointerId !== viewerPanState.pointerId) {
    return;
  }
  const canvas = $("#preview-canvas");
  viewerPanState.active = false;
  canvas?.classList.remove("is-panning");
  try {
    if (viewerPanState.pointerId !== null) {
      canvas?.releasePointerCapture(viewerPanState.pointerId);
    }
  } catch (error) {
    // Release can fail if the pointer was already released by the browser.
  }
  viewerPanState.pointerId = null;
}

function initViewerCanvasNavigation() {
  const canvas = $("#preview-canvas");
  if (!canvas) {
    return;
  }
  canvas.addEventListener("wheel", handleViewerWheel, { passive: false });
  canvas.addEventListener("dblclick", (event) => {
    if (event.target.closest("button, input, textarea, select, summary, a")) {
      return;
    }
    event.preventDefault();
    toggleViewerZoomMode();
  });
  canvas.addEventListener("pointerdown", handleViewerPointerDown);
  document.addEventListener("pointermove", handleViewerPointerMove);
  document.addEventListener("pointerup", handleViewerPointerEnd);
  document.addEventListener("pointercancel", handleViewerPointerEnd);
}

function initViewerResizeObserver() {
  const canvas = $("#preview-canvas");
  if (!canvas || !("ResizeObserver" in window)) {
    return;
  }
  viewerResizeObserver = new ResizeObserver(() => updateFitZoomReadout());
  viewerResizeObserver.observe(canvas);
}

function restorePersistentBridgeSession() {
  const path = parseFolderInput(state.bridgeScanPath)[0];
  if (!path || state.bridgeMode !== "bridge") {
    return;
  }
  state.bridgeScanPath = path;
  state.scanStatus = `Última carpeta: ${basename(path)}`;
  state.statusText = "Restaurando último lote";
  render();
  void scanBridgeFolder();
}

initViewerCanvasNavigation();
initViewerResizeObserver();
setScenario("initial");
restorePersistentBridgeSession();
