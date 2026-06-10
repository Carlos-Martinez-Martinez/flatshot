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

const urlParams = new URLSearchParams(window.location.search);
const defaultBridgeUrl = "http://127.0.0.1:8765";
const initialBridgeUrl = urlParams.get("bridge") || defaultBridgeUrl;
const devMode = urlParams.get("dev") === "1";
const formatterHelpers = window.FlatShotFormatters;
const outputProfileHelpers = window.FlatShotOutputProfiles;
const outputProfileViewHelpers = window.FlatShotOutputProfileView;
const exportPayloadHelpers = window.FlatShotExportPayload;
const exportStateHelpers = window.FlatShotExportState;
const exportSummaryViewHelpers = window.FlatShotExportSummaryView;
const exportResultViewHelpers = window.FlatShotExportResultView;
const exportPreflightViewHelpers = window.FlatShotExportPreflightView;
const topStatusViewHelpers = window.FlatShotTopStatusView;
const preflightHelpers = window.FlatShotPreflight;
const batchViewHelpers = window.FlatShotBatchView;
const scanStateHelpers = window.FlatShotScanState;
const exportConfirmViewHelpers = window.FlatShotExportConfirmView;
const emptyStateViewHelpers = window.FlatShotEmptyStateView;
const batchDetailViewHelpers = window.FlatShotBatchDetailView;
const galleryHelpers = window.FlatShotGallery;
const previewViewHelpers = window.FlatShotPreviewView;
const previewStateHelpers = window.FlatShotPreviewState;
const settingsViewHelpers = window.FlatShotSettingsView;
const inspectorOutputViewHelpers = window.FlatShotInspectorOutputView;
const inspectorReviewViewHelpers = window.FlatShotInspectorReviewView;
const inspectorContextViewHelpers = window.FlatShotInspectorContextView;
const STORAGE_KEYS = {
  bridgeScanPath: "flatshot.bridgeScanPath",
  selectedImagePath: "flatshot.selectedImagePath",
  outputProfiles: "flatshot.outputProfiles",
  activeOutputProfile: "flatshot.activeOutputProfile",
  sessionSnapshot: "flatshot.liveReloadSession.v1",
};
document.documentElement.classList.toggle("dev-mode", devMode);

const statusLabels = {
  ready: "Lista",
  adjusted: "Ajustada",
  warning: "Aviso",
  error: "Error",
};

const BATCH_FILTERS = {
  all: "all",
  valid: "valid",
  warnings: "warnings",
  excluded: "excluded",
};
const IGNORED_OMISSION_REASONS = new Set([
  "system_file",
  "temporary_or_config_file",
  "unsupported_extension",
  "subfolder_not_scanned",
]);
const ACTIONABLE_OMISSION_REASONS = new Set([
  "read_error",
]);

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
    enabled: true,
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
    enabled: false,
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
    enabled: false,
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
const initialOutputProfileId = readPersistentValue(STORAGE_KEYS.activeOutputProfile);
const initialOutputProfiles = readOutputProfiles(initialOutputProfileId);
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
  exportConfirmOpen: false,
  exportConfirmRisks: [],
  exportConfirmOptions: null,
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
  bridgeUrl: initialBridgeUrl,
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
let modalFocusReturnTarget = null;
let sessionSnapshotPersistenceEnabled = false;
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

function readSessionSnapshot() {
  let raw = "";
  try {
    raw = window.sessionStorage.getItem(STORAGE_KEYS.sessionSnapshot) || "";
  } catch (error) {
    return null;
  }
  if (!raw) {
    return null;
  }
  try {
    const snapshot = JSON.parse(raw);
    return snapshot?.version === 1 && snapshot.state && typeof snapshot.state === "object"
      ? snapshot
      : null;
  } catch (error) {
    return null;
  }
}

function writeSessionSnapshot() {
  try {
    window.sessionStorage.setItem(STORAGE_KEYS.sessionSnapshot, JSON.stringify(buildSessionSnapshot()));
  } catch (error) {
    // Live-reload state is best effort; the app still works without session storage.
  }
}

function buildSessionSnapshot() {
  const selected = selectedImage();
  return {
    version: 1,
    savedAt: Date.now(),
    state: {
      batch: state.batch,
      batchSource: state.batchSource,
      selectedImageId: state.selectedImageId,
      selectedImagePath: selected?.path || readPersistentValue(STORAGE_KEYS.selectedImagePath),
      previewMode: state.previewMode,
      previewBg: state.previewBg,
      zoom: state.zoom,
      fitZoom: state.fitZoom,
      fitMode: state.fitMode,
      panX: state.panX,
      panY: state.panY,
      filter: state.filter,
      search: state.search,
      galleryView: state.galleryView,
      inspectorTab: state.inspectorTab,
      inspectorCollapsed: state.inspectorCollapsed,
      activePreset: state.activePreset,
      presetOutputSettings: state.presetOutputSettings,
      settings: state.settings,
      presetDirty: state.presetDirty,
      presetSource: state.presetSource,
      localOverride: state.localOverride,
      outputProfiles: state.outputProfiles,
      activeOutputProfileId: state.activeOutputProfileId,
      outputProfileEditorId: state.outputProfileEditorId,
      outputProfileDraft: state.outputProfileDraft,
      destinationMode: state.destinationMode,
      destinationValue: state.destinationValue,
      format: state.format,
      size: state.size,
      background: state.background,
      naming: state.naming,
      suffix: state.suffix,
      appSettingsOpen: state.appSettingsOpen,
      batchDetailOpen: state.batchDetailOpen,
      bridgeMode: state.bridgeMode,
      bridgeUrl: state.bridgeUrl,
      bridgeStatus: state.bridgeStatus,
      bridgeMessage: state.bridgeMessage,
      bridgeLastResponse: state.bridgeLastResponse,
      bridgeCapabilitiesSummary: state.bridgeCapabilitiesSummary,
      bridgeCapabilities: state.bridgeCapabilities,
      bridgePresets: state.bridgePresets,
      bridgePresetSource: state.bridgePresetSource,
      bridgePresetWarning: state.bridgePresetWarning,
      bridgeScanPath: state.bridgeScanPath,
      scanStatus: state.scanStatus,
      scanIssues: state.scanIssues,
      scanDiagnostics: state.scanDiagnostics,
      realFolders: state.realFolders,
      realImages: state.realImages,
      imageOverrides: state.imageOverrides,
    },
  };
}

function restoreSessionSnapshot() {
  const snapshot = readSessionSnapshot();
  if (!snapshot) {
    return false;
  }

  const restored = snapshot.state;
  const outputProfiles = Array.isArray(restored.outputProfiles)
    ? normalizeOutputProfileList(restored.outputProfiles, restored.activeOutputProfileId)
    : state.outputProfiles;
  const selectedPath = String(restored.selectedImagePath || "");
  const realFolders = Array.isArray(restored.realFolders) ? restored.realFolders : [];
  const realImages = Array.isArray(restored.realImages) ? restored.realImages : [];

  Object.assign(state, {
    batch: restored.batch === "empty" ? "empty" : realImages.length ? "ready" : "none",
    batchSource: realImages.length || restored.batch === "empty" ? "bridge" : "none",
    scenario: "initial",
    selectedImageId: null,
    previewStatus: "empty",
    previewData: null,
    previewError: "",
    previewMode: ["processed", "original", "compare"].includes(restored.previewMode) ? restored.previewMode : "processed",
    previewBg: restored.previewBg || state.previewBg,
    zoom: clampNumber(restored.zoom, 25, 400, 100),
    fitZoom: clampNumber(restored.fitZoom, 25, 400, 100),
    fitMode: VIEW_MODE_LABELS[restored.fitMode] ? restored.fitMode : DEFAULT_VIEW_MODE,
    panX: clampNumber(restored.panX, -10000, 10000, 0),
    panY: clampNumber(restored.panY, -10000, 10000, 0),
    filter: Object.values(BATCH_FILTERS).includes(restored.filter) ? restored.filter : BATCH_FILTERS.all,
    search: String(restored.search || ""),
    galleryView: restored.galleryView === "list" ? "list" : "thumbs",
    inspectorTab: ["review", "output", "warnings", "advanced"].includes(restored.inspectorTab) ? restored.inspectorTab : "review",
    inspectorCollapsed: Boolean(restored.inspectorCollapsed),
    activePreset: String(restored.activePreset || state.activePreset),
    presetOutputSettings: safeObject(restored.presetOutputSettings),
    settings: normalizeSettings(restored.settings),
    presetDirty: Boolean(restored.presetDirty),
    presetSource: String(restored.presetSource || "Salida"),
    localOverride: Boolean(restored.localOverride),
    outputProfiles,
    activeOutputProfileId: outputProfiles.some((profile) => profile.id === restored.activeOutputProfileId)
      ? restored.activeOutputProfileId
      : outputProfiles[0]?.id || state.activeOutputProfileId,
    outputProfileEditorId: restored.outputProfileEditorId || restored.activeOutputProfileId || outputProfiles[0]?.id,
    outputProfileDraft: restored.outputProfileDraft && typeof restored.outputProfileDraft === "object"
      ? restored.outputProfileDraft
      : null,
    destinationMode: restored.destinationMode === "custom" ? "custom" : "source",
    destinationValue: String(restored.destinationValue || "_SALIDA_PRO"),
    format: normalizeExportFormat(restored.format),
    size: parseOutputSize(restored.size).normalized,
    background: ["rgb230", "white", "transparent"].includes(restored.background) ? restored.background : "rgb230",
    naming: String(restored.naming || "{original}{suffix}"),
    suffix: restored.suffix === undefined || restored.suffix === null ? "_PRO" : String(restored.suffix),
    appSettingsOpen: Boolean(restored.appSettingsOpen),
    batchDetailOpen: Boolean(restored.batchDetailOpen),
    exportConfirmOpen: false,
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
    paused: false,
    bridgeMode: "bridge",
    bridgeUrl: String(restored.bridgeUrl || initialBridgeUrl || defaultBridgeUrl),
    bridgeStatus: restored.bridgeStatus === "connected" ? "connected" : "idle",
    bridgeMessage: String(restored.bridgeMessage || "Estado restaurado"),
    bridgeLastResponse: String(restored.bridgeLastResponse || "Estado restaurado tras recarga"),
    bridgeCapabilitiesSummary: String(restored.bridgeCapabilitiesSummary || "Restaurado"),
    bridgeCapabilities: restored.bridgeCapabilities || null,
    bridgePresets: Array.isArray(restored.bridgePresets) ? restored.bridgePresets.map(normalizePresetItem).filter(Boolean) : [],
    bridgePresetSource: String(restored.bridgePresetSource || "unavailable"),
    bridgePresetWarning: String(restored.bridgePresetWarning || ""),
    bridgeScanPath: String(restored.bridgeScanPath || ""),
    scanStatus: String(restored.scanStatus || "Estado restaurado"),
    scanIssues: Array.isArray(restored.scanIssues) ? restored.scanIssues.map(normalizeBridgeIssue) : [],
    scanDiagnostics: restored.scanDiagnostics && typeof restored.scanDiagnostics === "object"
      ? restored.scanDiagnostics
      : emptyScanDiagnostics(),
    realFolders,
    realImages,
    imageOverrides: safeObject(restored.imageOverrides),
    thumbnailStatus: {},
    thumbnailErrors: [],
    statusText: "Estado restaurado",
  });

  if (state.batch === "ready") {
    const selected = selectedPath
      ? state.realImages.find((image) => image.path === selectedPath)
      : state.realImages.find((image) => image.id === restored.selectedImageId);
    const nextImage = selected || state.realImages[0];
    state.selectedImageId = nextImage?.id || null;
    state.localOverride = hasCurrentImageOverride(nextImage) || nextImage?.status === "adjusted";
    state.exportStatus = isExportReady() ? "ready" : "blocked";
    if (nextImage?.path) {
      writePersistentValue(STORAGE_KEYS.selectedImagePath, nextImage.path);
      Object.assign(state, previewStateHelpers.previewLoadingState({ statusText: "Restaurando vista" }));
      setTimer(() => requestBridgePreview(nextImage), 0);
    }
  } else if (state.batch === "empty") {
    state.exportStatus = "blocked";
    state.statusText = state.scanStatus || "No hay imágenes compatibles";
  }

  return true;
}

function safeObject(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : {};
}

function clampNumber(value, min, max, fallback) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return fallback;
  }
  return Math.min(max, Math.max(min, numeric));
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
  return outputProfileHelpers.normalizeOutputProfile(profile, index);
}

function outputProfileNameForDisplay(name) {
  return outputProfileHelpers.outputProfileNameForDisplay(name);
}

function normalizeExportFormat(value) {
  return outputProfileHelpers.normalizeExportFormat(value);
}

function readOutputProfiles(activeProfileId = "") {
  const saved = readPersistentJson(STORAGE_KEYS.outputProfiles, null);
  const profiles = Array.isArray(saved) ? saved : defaultOutputProfiles;
  const normalized = normalizeOutputProfileList(profiles, activeProfileId);
  return normalized.length ? normalized : normalizeOutputProfileList(defaultOutputProfiles, activeProfileId);
}

function normalizeOutputProfileList(profiles, activeProfileId = "") {
  return outputProfileHelpers.normalizeOutputProfileList(profiles, activeProfileId);
}

function dedupeOutputProfileIds(profiles) {
  return outputProfileHelpers.dedupeOutputProfileIds(profiles);
}

function uniqueOutputProfileId(name = "formato", seed = Date.now()) {
  return outputProfileHelpers.uniqueOutputProfileId(name, seed);
}

function outputProfileSize(profile) {
  return outputProfileHelpers.outputProfileSize(profile);
}

function parseOutputSize(value) {
  return outputProfileHelpers.parseOutputSize(value);
}

function activeOutputProfile() {
  return state.outputProfiles.find((profile) => profile.id === state.activeOutputProfileId)
    || state.outputProfiles[0]
    || defaultOutputProfiles[0];
}

function enabledOutputProfiles() {
  return state.outputProfiles.filter((profile) => profile.enabled);
}

function exportOutputProfiles() {
  const current = { ...currentOutputProfileData(), enabled: true };
  const activeId = state.activeOutputProfileId;
  const profiles = [];
  const seen = new Set();
  const pushProfile = (profile) => {
    if (!profile || seen.has(profile.id)) {
      return;
    }
    seen.add(profile.id);
    profiles.push(profile);
  };

  state.outputProfiles.forEach((profile) => {
    if (!profile.enabled && profile.id !== activeId) {
      return;
    }
    if (profile.id === activeId && !outputMatchesProfile(profile)) {
      pushProfile(current);
      return;
    }
    if (profile.enabled) {
      pushProfile(profile);
    }
  });

  if (!profiles.length) {
    pushProfile(current);
  }
  return profiles;
}

function exportOutputCount() {
  return exportOutputProfiles().length;
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
  profile.enabled = true;
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

function setOutputProfileEnabled(profileId, enabled) {
  const profile = state.outputProfiles.find((item) => item.id === profileId);
  if (!profile) {
    return;
  }
  const currentlyEnabled = profile.enabled;
  if (!enabled && currentlyEnabled && enabledOutputProfiles().length <= 1) {
    state.statusText = "Debe quedar al menos una salida activa";
    render();
    return;
  }

  profile.enabled = Boolean(enabled);
  if (profile.enabled) {
    applyOutputProfile(profile.id, { render: false, statusText: `Salida activa: ${profile.name}` });
  } else if (state.activeOutputProfileId === profile.id) {
    const next = enabledOutputProfiles()[0];
    if (next) {
      applyOutputProfile(next.id, { render: false, statusText: `Salida principal: ${next.name}` });
    }
  }

  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = profile.enabled ? `Salida activa: ${profile.name}` : `Salida desactivada: ${profile.name}`;
  persistOutputProfiles();
  render();
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
  return preflightHelpers.countText(count, singular, plural);
}

function readyImagesText(count) {
  return preflightHelpers.readyImagesText(count);
}

function ignoredNeutralText(count = batchCounts().ignoredFiles) {
  return preflightHelpers.ignoredNeutralText(count);
}

function ignoredImagesText(count = batchCounts().ignoredFiles) {
  return preflightHelpers.ignoredImagesText(count);
}

function blockingValidationIssues() {
  return validationIssues().filter((issue) => issue.level === "error" && issue.title !== "Sin lote");
}

function scanOmissions() {
  const omitted = state.scanDiagnostics?.omitted;
  return Array.isArray(omitted) ? omitted : [];
}

function omissionReasonOptions() {
  return {
    ignoredReasons: IGNORED_OMISSION_REASONS,
    actionableReasons: ACTIONABLE_OMISSION_REASONS,
  };
}

function omissionSeverity(item) {
  return preflightHelpers.omissionSeverity(item, omissionReasonOptions());
}

function ignoredOmissions() {
  return preflightHelpers.splitOmissions(scanOmissions(), omissionReasonOptions()).ignored;
}

function actionableOmissions() {
  return preflightHelpers.splitOmissions(scanOmissions(), omissionReasonOptions()).actionable;
}

function imageWarningCount(images = activeImages()) {
  return preflightHelpers.imageWarningCount(images);
}

function excludedImageCount(images = activeImages()) {
  return preflightHelpers.excludedImageCount(images, exportItemStatusMap(images));
}

function exportItemStatusMap(images = activeImages()) {
  return new Map(images.map((image) => [image.id, exportItemState(image)]));
}

function batchCounts() {
  const images = activeImages();
  const diagnostics = state.scanDiagnostics || emptyScanDiagnostics();
  const exportables = exportableImages();
  return preflightHelpers.calculateBatchCounts({
    batch: state.batch,
    images,
    exportables,
    diagnostics,
    omissions: scanOmissions(),
    exportItemStatuses: exportItemStatusMap(images),
    stateErrors: state.errors,
    exportStatus: state.exportStatus,
    blockingValidationIssueCount: blockingValidationIssues().length,
    ...omissionReasonOptions(),
  });
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
  const images = activeImages();
  return galleryHelpers.filteredImages(images, {
    exportItemStatuses: exportItemStatusMap(images),
    filter: state.filter,
    filters: BATCH_FILTERS,
    search: state.search,
  });
}

function filterStatusText(filter = state.filter) {
  return galleryHelpers.filterStatusText(filter);
}

function validationIssues() {
  const issues = [];
  if (state.batch === "none") {
    issues.push({ level: "error", title: "Sin lote", detail: "Selecciona una carpeta." });
  }
  if (state.batch === "empty") {
    issues.push({ level: "warning", title: "No hay PNG válidos", detail: "Elige otra carpeta." });
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
  exportOutputProfiles()
    .filter((profile) => profile.id !== state.activeOutputProfileId)
    .forEach((profile) => {
      outputProfileValidation(outputProfileRawFromProfile(profile)).errors.forEach((message) => {
        issues.push({
          level: "error",
          title: "Salida sin configurar",
          detail: `${profile.name}: ${message}`,
        });
      });
    });
  return issues;
}

function preflightIssues() {
  const counts = batchCounts();
  return preflightHelpers.buildPreflightIssues({
    validationIssues: validationIssues(),
    stateErrors: state.errors,
    counts,
    actionableOmissions: actionableOmissions(),
    hasBatch: hasBatch(),
    warningImages: imageWarningCount(),
    errorImages: excludedImageCount(),
    exportableCount: exportableImages().length,
    actionableOmissionSummary: actionableOmissionSummaryText(),
  });
}

function preflightCounts() {
  return preflightHelpers.preflightCounts(preflightIssues());
}

function exportConfirmationRisks() {
  const counts = batchCounts();
  const risks = [];
  const exportableWarningImages = exportableImages().filter((image) => image.status === "warning").length;
  const actionableOmitted = actionableOmissions();

  validationIssues()
    .filter((issue) => issue.level === "error" && issue.title !== "Sin lote")
    .forEach((issue) => {
      risks.push({
        id: `blocker-${issue.title}`,
        level: "error",
        blocking: true,
        title: issue.title,
        detail: issue.detail || "Resuelve este punto antes de exportar.",
      });
    });

  if (actionableOmitted.length > 0) {
    risks.push({
      id: "omitted-file-incidents",
      level: "warning",
      title: `${actionableOmitted.length} archivo${actionableOmitted.length === 1 ? "" : "s"} a revisar`,
      detail: actionableOmissionSummaryText(),
    });
  }

  if (exportableWarningImages > 0) {
    risks.push({
      id: "image-warnings",
      level: "warning",
      title: `${countText(exportableWarningImages, "imagen", "imágenes")} con aviso`,
      detail: "Se exportarán, pero conviene revisarlas si el lote es de producción.",
    });
  }

  if (counts.nonExportableImages > 0) {
    risks.push({
      id: "non-exportable-images",
      level: "warning",
      title: `${countText(counts.nonExportableImages, "imagen", "imágenes")} excluida${counts.nonExportableImages === 1 ? "" : "s"}`,
      detail: "No se incluirán en la exportación.",
    });
  }

  const existingOutputIssue = [...state.errors, ...state.exportIssues].find(issueMentionsExistingOutput);
  if (existingOutputIssue) {
    risks.push({
      id: "existing-output-blocker",
      level: "error",
      blocking: true,
      title: "Archivos ya existentes",
      detail: "Cambia el destino o el nombre de archivo antes de exportar de nuevo.",
    });
  } else if (hasPreviousExportDestination()) {
    risks.push({
      id: "previous-export-destination",
      level: "warning",
      title: "Destino usado en la exportación anterior",
      detail: "Si ya existen archivos con el mismo nombre, el motor local no debe sobrescribirlos sin validación.",
    });
  }

  const lowResolutionCount = lowResolutionImageCount();
  if (lowResolutionCount > 0) {
    risks.push({
      id: "low-resolution",
      level: "warning",
      title: `${countText(lowResolutionCount, "imagen", "imágenes")} por debajo del tamaño de salida`,
      detail: "La imagen puede ampliarse para llegar al tamaño configurado.",
    });
  }

  if (advancedSettingsDirty()) {
    risks.push({
      id: "advanced-settings",
      level: "warning",
      title: "Ajustes avanzados modificados",
      detail: "La exportación usará esos valores.",
    });
  }

  if (state.exportStatus === "failed" && state.errors.some((issue) => issue.level === "error" && !issueMentionsExistingOutput(issue))) {
    risks.push({
      id: "previous-export-errors",
      level: "warning",
      title: "Errores en la última exportación",
      detail: "Puedes reintentar, pero revisa el resultado si vuelve a fallar.",
    });
  }

  state.errors
    .filter((issue) => issue.level !== "error" && !issueMentionsExistingOutput(issue))
    .slice(0, 2)
    .forEach((issue, index) => {
      risks.push({
        id: `state-warning-${index}-${issue.title}`,
        level: "warning",
        title: issue.title || "Aviso",
        detail: issue.detail || "Revisa este punto antes de exportar.",
      });
    });

  return dedupeExportRisks(risks);
}

function dedupeExportRisks(risks) {
  return preflightHelpers.dedupeExportRisks(risks);
}

function issueMentionsExistingOutput(issue) {
  return preflightHelpers.issueMentionsExistingOutput(issue);
}

function hasPreviousExportDestination() {
  return ["completed", "partial"].includes(state.exportStatus) && Boolean(outputDestinationToOpen());
}

function imageDimensions(image) {
  const width = Number(image?.width || image?.naturalWidth || image?.sourceWidth || 0);
  const height = Number(image?.height || image?.naturalHeight || image?.sourceHeight || 0);
  if (width > 0 && height > 0) {
    return { width, height };
  }
  const detail = String(image?.detail || "");
  const match = /(\d{2,5})\s*[x×]\s*(\d{2,5})/i.exec(detail);
  if (!match) {
    return null;
  }
  return {
    width: Number.parseInt(match[1], 10),
    height: Number.parseInt(match[2], 10),
  };
}

function lowResolutionImageCount() {
  const targets = exportOutputProfiles().map((profile) => parseOutputSize(outputProfileSize(profile)));
  return exportableImages().filter((image) => {
    const dimensions = imageDimensions(image);
    return dimensions && targets.some((target) => dimensions.width < target.width || dimensions.height < target.height);
  }).length;
}

function isExportReady() {
  return preflightHelpers.isExportReady({
    validationIssues: validationIssues(),
    hasBatch: hasBatch(),
    exportableCount: exportableImages().length,
  });
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

function exportActionLabel(imageCount = batchCounts().exportableImages) {
  return batchViewHelpers.exportActionLabel(imageCount, exportOutputCount());
}

function plannedExportTotal() {
  return exportableImages().length * exportOutputCount();
}

function firstOmittedItem() {
  const omitted = actionableOmissions();
  return omitted.length ? omitted[0] : null;
}

function firstActionableIssue() {
  const omitted = firstOmittedItem();
  if (omitted) {
    return {
      level: "warning",
      title: "Archivo a revisar",
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
  return batchViewHelpers.batchSummaryLabel({
    batch: state.batch,
    count: activeImages().length,
    warnings: visibleWarningCount(),
  });
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
    const total = plannedExportTotal() || counts.exportableImages;
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
      primaryAction: { label: "Abrir destino", action: "open-output", enabled: Boolean(outputDestinationToOpen()) },
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
      primaryAction: { label: "Ver error", action: "review-warnings", enabled: true },
      secondaryAction: isExportReady() ? { label: "Exportar de nuevo", action: "start-export", enabled: true } : null,
      nextStep: "Revisar error",
      counts,
    };
  }

  if (state.batch === "scanning") {
    return {
      id: "scanning",
      tone: "busy",
      title: "Escaneando carpeta...",
      subtitle: state.scanStatus || "Leyendo imágenes",
      topSummary: compactHeaderStatusText(),
      primaryAction: { label: "Escaneando", action: "", enabled: false },
      secondaryAction: null,
      nextStep: "Escaneando carpeta",
      counts,
    };
  }

  if (state.batch === "none") {
    return {
      id: "no_folder",
      tone: "idle",
      title: "Sin lote",
      subtitle: "Selecciona una carpeta para empezar",
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
      title: "No hay PNG válidos",
      subtitle: hasFoundFiles
        ? `${countText(counts.filesFound, "archivo encontrado", "archivos encontrados")}${counts.ignoredFiles ? ` · ${ignoredNeutralText(counts.ignoredFiles)}` : ""}`
        : "No hay archivos compatibles en esta carpeta.",
      topSummary: compactHeaderStatusText(),
      primaryAction: { label: "Elegir otra carpeta", action: "pick-bridge-folder", enabled: state.bridgeStatus !== "checking" },
      secondaryAction: counts.reviewIssues ? { label: "Revisar avisos", action: "review-warnings", enabled: true } : null,
      nextStep: "Elegir otra carpeta",
      counts,
    };
  }

  if (blockers.length) {
    const issue = blockers[0];
    return {
      id: "ready_with_blockers",
      tone: "error",
      title: "Exportación bloqueada",
      subtitle: issue.detail || "Hay un problema que impide exportar.",
      topSummary: compactHeaderStatusText(),
      primaryAction: { label: "Revisar errores", action: "review-output", enabled: true },
      secondaryAction: null,
      nextStep: "Resolver problemas",
      counts,
    };
  }

  if (hasWarnings) {
    return {
      id: "ready_with_warnings",
      tone: "warning",
      title: "Lote listo",
      subtitle: `${summary} · ${countText(counts.nonBlockingWarnings, "aviso", "avisos")}`,
      topSummary: compactHeaderStatusText(),
      primaryAction: { label: exportActionLabel(counts.exportableImages), action: "start-export", enabled: isExportReady() },
      secondaryAction: { label: "Revisar avisos", action: "review-warnings", enabled: true },
      nextStep: exportActionLabel(counts.exportableImages),
      counts,
    };
  }

  return {
    id: counts.ignoredFiles ? "ready_with_omitted" : "ready",
    tone: "ready",
    title: "Lote listo",
    subtitle: `${summary}${counts.ignoredFiles ? ` · ${ignoredNeutralText(counts.ignoredFiles)}` : ""} · ${output} · ${destination}`,
    topSummary: compactHeaderStatusText(),
    primaryAction: { label: exportActionLabel(counts.exportableImages), action: "start-export", enabled: isExportReady() },
    secondaryAction: null,
    nextStep: exportActionLabel(counts.exportableImages),
    counts,
  };
}

function readyBatchSummaryText(counts = batchCounts()) {
  const readyText = readyImagesText(counts.filesFound > 0 || counts.exportableImages > 0 ? counts.exportableImages : 0);
  return batchViewHelpers.readyBatchSummaryText(counts, batchViewHelpers.detectedFormatLabel(activeImages()), readyText);
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
  Object.assign(state, previewStateHelpers.previewLoadingState());
  render();
  setTimer(() => {
    Object.assign(state, previewStateHelpers.previewImageStatusState(image.status));
    render();
  }, 380);
}

function rememberSelectedImage(image) {
  if (image?.source === "bridge" && image.path) {
    writePersistentValue(STORAGE_KEYS.selectedImagePath, image.path);
  }
}

function selectAdjacentImage(delta, options = {}) {
  const images = filteredImages();
  if (!images.length) {
    return;
  }
  const currentIndex = images.findIndex((image) => image.id === state.selectedImageId);
  const startIndex = currentIndex >= 0 ? currentIndex : 0;
  const nextIndex = Math.max(0, Math.min(images.length - 1, startIndex + delta));
  selectImage(images[nextIndex].id);
  if (options.focus) {
    queueImageFocus(images[nextIndex].id);
  }
}

function selectEdgeImage(edge, options = {}) {
  const images = filteredImages();
  if (!images.length) {
    return;
  }
  const image = edge === "last" ? images[images.length - 1] : images[0];
  selectImage(image.id);
  if (options.focus) {
    queueImageFocus(image.id);
  }
}

function clearPreviewSelection() {
  state.previewRequestId += 1;
  clearTimers();
  state.selectedImageId = null;
  state.localOverride = false;
  Object.assign(state, previewStateHelpers.previewEmptyState());
  state.fitZoom = 100;
  resetViewerPan();
}

function ensureGallerySelectionForFilter() {
  const visible = filteredImages();
  if (visible.some((image) => image.id === state.selectedImageId)) {
    return false;
  }
  if (visible.length) {
    selectImage(visible[0].id);
    return true;
  }
  if (state.filter !== BATCH_FILTERS.all || state.search.trim()) {
    clearPreviewSelection();
  }
  return false;
}

function applyGalleryFilter(filter) {
  state.filter = filter || BATCH_FILTERS.all;
  state.statusText = filterStatusText(state.filter);
  if (ensureGallerySelectionForFilter()) {
    return;
  }
  render();
}

function queueImageFocus(imageId = state.selectedImageId) {
  if (!imageId) {
    return;
  }
  window.requestAnimationFrame(() => {
    const button = $$("#image-list [data-image-id]").find((item) => item.dataset.imageId === imageId);
    button?.focus({ preventScroll: true });
  });
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
  if (!viewerPanState.active) {
    clampViewerPan();
  }
  canvas.style.setProperty("--canvas-pan-x", `${Math.round(state.panX)}px`);
  canvas.style.setProperty("--canvas-pan-y", `${Math.round(state.panY)}px`);
}

function resetViewerPan() {
  state.panX = 0;
  state.panY = 0;
  applyViewerPanDom();
}

function viewerPanBounds() {
  const canvas = $("#preview-canvas");
  const target = canvas?.querySelector(".preview-image, .mock-product");
  if (!canvas || !target || isAutoViewerMode()) {
    return { minX: 0, maxX: 0, minY: 0, maxY: 0 };
  }
  const canvasRect = canvas.getBoundingClientRect();
  const targetRect = target.getBoundingClientRect();
  if (!canvasRect.width || !canvasRect.height || !targetRect.width || !targetRect.height) {
    return { minX: 0, maxX: 0, minY: 0, maxY: 0 };
  }
  const minVisibleX = Math.min(96, Math.max(32, Math.min(canvasRect.width, targetRect.width) * 0.25));
  const minVisibleY = Math.min(96, Math.max(32, Math.min(canvasRect.height, targetRect.height) * 0.25));
  const maxX = Math.max(0, Math.round((canvasRect.width + targetRect.width) / 2 - minVisibleX));
  const maxY = Math.max(0, Math.round((canvasRect.height + targetRect.height) / 2 - minVisibleY));
  return { minX: -maxX, maxX, minY: -maxY, maxY };
}

function clampViewerPan() {
  const bounds = viewerPanBounds();
  state.panX = Math.max(bounds.minX, Math.min(bounds.maxX, state.panX));
  state.panY = Math.max(bounds.minY, Math.min(bounds.maxY, state.panY));
}

function isAutoViewerMode(mode = state.fitMode) {
  return previewStateHelpers.isAutoViewerMode(mode);
}

function viewerModeLabel(mode = state.fitMode) {
  return previewStateHelpers.viewerModeLabel(mode, VIEW_MODE_LABELS);
}

function viewerModeClass(mode = state.fitMode) {
  return previewStateHelpers.viewerModeClass(mode);
}

function currentViewerZoom() {
  return isAutoViewerMode() ? state.fitZoom : state.zoom;
}

function clampViewerZoom(value) {
  return previewStateHelpers.clampViewerZoom(value);
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
  window.requestAnimationFrame(() => {
    clampViewerPan();
    applyViewerPanDom();
  });
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
    Object.assign(state, previewStateHelpers.previewLoadingState());
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
    Object.assign(state, previewStateHelpers.previewLoadingState({ clearData: false }));
    render();
    clearTimers();
    setTimer(() => {
      Object.assign(state, previewStateHelpers.previewImageStatusState(selectedImage()?.status, { errorAsReady: true }));
      render();
    }, 420);
  } else {
    render();
  }
}

function startExport(options = {}) {
  if (state.appSettingsOpen && outputProfileHasUnsavedChanges() && !confirmDiscardOutputDraft("exportar sin aplicar esos cambios")) {
    return;
  }
  clearTimers();
  if (!isExportReady()) {
    state.exportStatus = "blocked";
    state.statusText = validationIssues()[0]?.title || "Configura salida";
    render();
    return;
  }

  const risks = exportConfirmationRisks();
  if (!options.confirmed && risks.length) {
    openExportConfirm(risks, options);
    return;
  }
  if (risks.some((risk) => risk.blocking)) {
    openExportConfirm(risks, options);
    return;
  }
  closeExportConfirm({ renderAfter: false });

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

  Object.assign(state, exportStateHelpers.exportStartState({
    scenario: options.keepScenario ? "export-running" : state.scenario,
    resetConfirm: true,
  }));
  render();
  scheduleExportStep();
}

async function startBridgeExport() {
  clearBridgeExportPoll();
  cancelThumbnailWork();
  Object.assign(state, exportStateHelpers.exportStartState());
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
    Object.assign(state, exportStateHelpers.bridgeRunFailureState(message));
    render();
  }
}

function bridgeExportPayload() {
  return exportPayloadHelpers.buildBridgeExportPayload({
    activeOutputProfileId: state.activeOutputProfileId,
    fallbackProfile: currentOutputProfileData(),
    imageOverrides: state.imageOverrides,
    images: exportableImages(),
    presetName: state.activePreset,
    profiles: exportOutputProfiles(),
    settings: bridgePreviewSettings(),
  });
}

function exportVariantPayloadFromProfile(profile, index, seenVariantIds = new Set()) {
  return outputProfileHelpers.exportVariantPayloadFromProfile(profile, index, seenVariantIds);
}

function exportVariantId(profile, index, seenVariantIds = new Set()) {
  return outputProfileHelpers.exportVariantId(profile, index, seenVariantIds);
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
      Object.assign(state, exportStateHelpers.bridgeProgressUnavailableState(message));
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
  Object.assign(state, exportStateHelpers.bridgeStatusPatch(payload, state));
  state.errors = exportStateHelpers.bridgeStatusErrors(payload, state.exportCompletedItems, state.exportIssues);
}

function normalizeBridgeIssue(issue) {
  return exportStateHelpers.normalizeBridgeIssue(issue);
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
    const total = plannedExportTotal() || exportableImages().length;
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
  Object.assign(state, exportStateHelpers.stoppedExportState());
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

function clearFilter() {
  state.filter = BATCH_FILTERS.all;
  state.search = "";
  state.statusText = "Mostrando todo";
  if (ensureGallerySelectionForFilter()) {
    return;
  }
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
  Object.assign(state, previewStateHelpers.previewLoadingState());
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

    Object.assign(state, previewStateHelpers.previewBridgeResultState(previewResponseToData(response), response.warning));
  } catch (error) {
    if (isStalePreviewResponse(requestId, image)) {
      return;
    }
    const message = bridgeErrorMessage(error);
    Object.assign(state, previewStateHelpers.previewErrorState(message));
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
  return outputProfileHelpers.backgroundColorTuple(value);
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
  Object.assign(state, scanStateHelpers.folderPickStartState());
  render();

  try {
    const selected = await bridgeRequest("/folders/pick", {
      method: "POST",
      body: JSON.stringify({ initialPath: parseFolderInput(state.bridgeScanPath)[0] || "" }),
      timeoutMs: 300000,
    });
    if (!selected.selected || !selected.path) {
      Object.assign(state, scanStateHelpers.folderPickCancelledState());
      render();
      return;
    }

    Object.assign(state, scanStateHelpers.folderPickSelectedState(selected.path));
    persistBridgeScanPath();
    render();
    await scanBridgeFolder();
  } catch (error) {
    const message = bridgeErrorMessage(error);
    Object.assign(state, scanStateHelpers.folderPickErrorState(message));
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
    Object.assign(state, scanStateHelpers.emptyScanPathState(state.bridgeStatus === "connected"));
    render();
    return;
  }
  persistBridgeScanPath(folders[0]);

  clearTimers();
  thumbnailPreloads.clear();
  thumbnailFallbackQueue.length = 0;
  thumbnailFallbackInFlight.clear();
  clearBridgeExportPoll();
  Object.assign(state, scanStateHelpers.scanStartState(folders, emptyScanDiagnostics(), DEFAULT_VIEW_MODE));
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
    Object.assign(state, scanStateHelpers.scanFailureState(message, emptyScanDiagnostics()));
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
  state.bridgeMessage = batchViewHelpers.bridgeScanMessage(response.totalImages || 0, folderWarnings + responseErrors.length);
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
  if (actionableOmissions().length > 0) {
    state.scanIssues.push({
      level: "warning",
      title: "Archivos a revisar",
      detail: actionableOmissionSummaryText(),
    });
  }

  if (state.realImages.length) {
    const rememberedPath = readPersistentValue(STORAGE_KEYS.selectedImagePath);
    const rememberedImage = rememberedPath
      ? state.realImages.find((image) => image.path === rememberedPath)
      : null;
    const selectedImage = rememberedImage || state.realImages[0];
    Object.assign(state, scanStateHelpers.scanReadyState({
      defaultViewMode: DEFAULT_VIEW_MODE,
      imageCount: state.realImages.length,
      localOverride: hasCurrentImageOverride(selectedImage) || selectedImage.status === "adjusted",
      scanIssueCount: state.scanIssues.length,
      selectedImageId: selectedImage.id,
    }));
    rememberSelectedImage(selectedImage);
    void requestBridgePreview(selectedImage);
    return;
  }

  Object.assign(state, scanStateHelpers.scanEmptyState(state.scanIssues));
}

function parseFolderInput(value) {
  return String(value || "")
    .split(/[;\n\r]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function omissionReasonLabel(reason) {
  return batchViewHelpers.omissionReasonLabel(reason);
}

function actionableOmissionSummaryText() {
  return batchViewHelpers.omissionSummaryText(actionableOmissions(), "Sin avisos de archivos");
}

function ignoredSummaryText() {
  return batchViewHelpers.omissionSummaryText(ignoredOmissions(), "Sin archivos ignorados");
}

function folderActionableOmissionCount(folder) {
  return (folder.omitted || []).filter((item) => omissionSeverity(item) !== "ignored").length;
}

function bridgeFolderToItem(folder, index) {
  const hasErrors = Array.isArray(folder.errors) && folder.errors.length > 0;
  const count = Array.isArray(folder.images) ? folder.images.length : 0;
  const omittedCount = Number(folder.omittedCount) || 0;
  const actionableOmitted = folderActionableOmissionCount(folder);
  const exists = folder.exists !== false;
  const isDir = folder.isDir !== false;
  const status = hasErrors
    ? count ? "warning" : "error"
    : actionableOmitted ? "warning" : count ? "ready" : exists && isDir ? "empty" : "error";
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
      : actionableOmitted
        ? `${count} imágenes · ${actionableOmitted} avisos`
        : omittedCount
          ? `${count} imágenes · ${omittedCount} ignorados`
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
  return formatterHelpers.basename(path);
}

function imageFileStem(name) {
  return formatterHelpers.imageFileStem(name);
}

function imageFileType(image) {
  return formatterHelpers.imageFileType(image, state.format || "Imagen");
}

function formatBytes(bytes) {
  return formatterHelpers.formatBytes(bytes);
}

function bridgeErrorMessage(error) {
  if (error?.name === "AbortError") {
    return "La conexión local no responde";
  }
  return error?.message || "Conexión local no disponible";
}

function capabilitiesSummary(capabilities) {
  return formatterHelpers.capabilitiesSummary(capabilities);
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
  if (counts.warningImages) {
    state.filter = "warnings";
  } else if (counts.nonExportableImages) {
    state.filter = "excluded";
  }
  ensureGallerySelectionForFilter();
  const issueCount = counts.reviewIssues + blockingCount;
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
  return exportResultViewHelpers.outputDestinationToOpen({
    exportDestinations: state.exportDestinations,
    resultDestinations: state.exportResult?.destinations,
  });
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
  return formatterHelpers.pathToFileUrl(path);
}

function statusMode() {
  return topStatusViewHelpers.statusMode({
    batch: state.batch,
    bridgeMode: state.bridgeMode,
    bridgeStatus: state.bridgeStatus,
    exportStatus: state.exportStatus,
    hasScanError: state.scanIssues.some((issue) => issue.level === "error"),
    hasValidationIssues: Boolean(validationIssues().length),
    previewStatus: state.previewStatus,
  });
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
  renderExportConfirm();
  renderAppSettings();
  renderInspector();
  renderFooter();
  renderAccessibilityHints();
  renderDesignSystemComponents();
  syncOpenInspectorDisclosureHeights();
  keepActiveThumbnailVisible();
  if (sessionSnapshotPersistenceEnabled) {
    writeSessionSnapshot();
  }
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
  const hasStatusFooter = state.exportStatus === "running"
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
  shell.classList.toggle("is-output-editing", state.outputEditMode);
  shell.classList.toggle("is-settings-open", state.appSettingsOpen);
  shell.classList.toggle("has-status-footer", hasStatusFooter);
  shell.classList.toggle("export-completed", ["completed", "partial", "failed"].includes(state.exportStatus));
  shell.classList.toggle("inspector-collapsed", state.inspectorCollapsed);
  shell.dataset.uiState = visible.id;
  if (gallery) {
    gallery.dataset.galleryView = state.galleryView;
    gallery.dataset.outputBg = activeOutputProfile()?.background || state.background || "rgb230";
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
  return formatterHelpers.debugUrlLabel(value);
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
  const counts = batchCounts();
  $("#demo-scenario").value = scenarioLabels[state.scenario] ? state.scenario : "batch-ready";
  $("#app-mode").value = state.bridgeMode;
  $("#bridge-url").value = state.bridgeUrl;
  $("#active-batch-label").textContent = "";
  const topStatus = $("#top-status-text");
  topStatus.textContent = visible.topSummary || compactHeaderStatusText();
  topStatus.title = visible.subtitle || visible.topSummary || "";
  $("#status-dot").className = `status-dot ${statusMode()}`;
  const hasBatchDetail = hasBatch() || state.batch === "empty"
    || counts.reviewIssues > 0
    || counts.ignoredFiles > 0
    || counts.blockingErrors > 0
    || ["partial", "failed"].includes(state.exportStatus);
  const detailButton = $("[data-action='open-batch-detail']");
  if (detailButton) {
    detailButton.hidden = !hasBatchDetail;
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
  const canChangeBatch = state.batch !== "none" && state.batch !== "scanning" && state.exportStatus !== "running";
  const folderButton = $(".top-folder-action");
  if (folderButton) {
    folderButton.hidden = !canChangeBatch;
    folderButton.disabled = !canChangeBatch;
    folderButton.title = "Seleccionar otra carpeta";
  }
  const formatButton = $(".top-format-action");
  if (formatButton) {
    const showFormat = state.batch !== "none" && state.batch !== "scanning";
    formatButton.hidden = !showFormat;
    formatButton.disabled = !showFormat || state.exportStatus === "running";
    formatButton.title = "Editar salida";
  }
  const resetButton = $(".top-reset-action");
  if (resetButton) {
    resetButton.hidden = state.batch === "none" || state.batch === "scanning";
    resetButton.disabled = state.exportStatus === "running";
    resetButton.title = "Volver al estado inicial";
  }
  const moreMenu = $(".top-more-menu");
  if (moreMenu) {
    moreMenu.hidden = true;
  }
}

function compactHeaderStatusText() {
  const counts = batchCounts();
  const images = activeImages();
  return topStatusViewHelpers.compactHeaderStatusText({
    batch: state.batch,
    exportResultProcessed: state.exportResult?.processed,
    exportResultTotal: state.exportResult?.total,
    exportStatus: state.exportStatus,
    exportableImages: counts.exportableImages,
    filesFound: counts.filesFound,
    formatLabel: batchViewHelpers.detectedFormatLabel(images),
    ignoredFiles: counts.ignoredFiles,
    imageCount: images.length,
    nonBlockingWarnings: counts.nonBlockingWarnings,
    paused: state.paused,
    plannedTotal: plannedExportTotal(),
    processed: state.processed,
    readyLabel: readyImagesText(counts.exportableImages),
  });
}

function topStatusText() {
  return topStatusViewHelpers.topStatusText({
    batch: state.batch,
    bridgeMode: state.bridgeMode,
    bridgeStatus: state.bridgeStatus,
    compactHeaderStatus: compactHeaderStatusText(),
    exportStatus: state.exportStatus,
    exportableImages: exportableImages().length,
    paused: state.paused,
    plannedTotal: plannedExportTotal(),
    processed: state.processed,
    statusText: state.statusText,
  });
}

function preflightStatusLabel() {
  const ready = isExportReady();
  const counts = preflightCounts();
  return topStatusViewHelpers.preflightStatusLabel({
    errors: counts.errors,
    exportStatus: state.exportStatus,
    paused: state.paused,
    ready,
    warnings: counts.warnings,
  });
}

function preflightStatusClass() {
  const ready = isExportReady();
  const counts = preflightCounts();
  return topStatusViewHelpers.preflightStatusClass({
    errors: counts.errors,
    exportStatus: state.exportStatus,
    ready,
    warnings: counts.warnings,
  });
}

function renderBridge() {
  const chip = $("#bridge-status");
  const sourcePanel = $("#source-panel");
  const sourceBadge = $("#scan-source-badge");
  const message = $("#bridge-message");
  const counts = batchCounts();
  const viewState = scanStateHelpers.sourcePanelViewState({
    batch: state.batch,
    bridgeMode: state.bridgeMode,
    bridgeStatus: state.bridgeStatus,
    devMode,
    exportableImages: counts.exportableImages,
    folders: sourceFoldersForDisplay(),
    hasBatch: hasBatch(),
    hasScanError: state.scanIssues.some((issue) => issue.level === "error"),
    ignoredFiles: counts.ignoredFiles,
    isBridgeBatch: isBridgeBatch(),
    isMockBatch: isMockBatch(),
    persistedFolderName: persistedScanFolderName(),
    scanStatus: state.scanStatus,
    scanningFolderName: scanningScanFolderName(),
  });

  chip.className = `bridge-chip ${bridgeStatusClass()}`;
  chip.textContent = bridgeStatusLabel();
  sourcePanel.className = `source-panel batch-rail__source ${viewState.panelClass}`;
  sourceBadge.className = `state-chip ${viewState.badgeClass}`;
  sourceBadge.textContent = viewState.badgeLabel;
  $("#source-title").textContent = viewState.title;
  const sourceName = $("#source-folder-name");
  if (sourceName) {
    sourceName.textContent = viewState.folderName;
    sourceName.title = viewState.folderName;
  }
  $("#scan-status").textContent = viewState.scanStatus;
  $("#bridge-scan-path").value = state.bridgeScanPath;
  $("#bridge-pick-folder").textContent = viewState.pickButtonLabel;
  $("#bridge-scan-folder").textContent = viewState.scanButtonLabel;
  $("#bridge-scan-folder").title = viewState.scanButtonTitle;
  $("#bridge-scan-folder").setAttribute("aria-label", $("#bridge-scan-folder").title);
  $("#bridge-pick-folder").disabled = viewState.controlsDisabled;
  $("#bridge-scan-folder").disabled = viewState.controlsDisabled;
  $("#bridge-last-response").textContent = state.bridgeLastResponse;
  $("#bridge-capabilities").textContent = state.bridgeCapabilitiesSummary;
  message.textContent = viewState.message;
  message.className = viewState.messageClass;
  renderBatchSummary();
}

function sourceFoldersForDisplay() {
  if (state.batch === "ready") {
    return activeFolders();
  }
  if (state.batch === "empty" && isBridgeBatch()) {
    return state.realFolders;
  }
  return [];
}

function persistedScanFolderName() {
  const persistedPath = parseFolderInput(state.bridgeScanPath)[0];
  return persistedPath ? basename(persistedPath) || "Carpeta actual" : "";
}

function scanningScanFolderName() {
  return basename(parseFolderInput(state.bridgeScanPath)[0]);
}

function sourceFolderName() {
  if (state.batch === "scanning") {
    return scanStateHelpers.sourceFolderName({
      batch: state.batch,
      scanningFolderName: scanningScanFolderName(),
    });
  }
  return scanStateHelpers.sourceFolderName({
    batch: state.batch,
    folders: sourceFoldersForDisplay(),
    hasBatch: hasBatch(),
    persistedFolderName: persistedScanFolderName(),
  });
}

function emptyScanDiagnostics() {
  return {
    totalFiles: 0,
    totalImages: 0,
    totalOmitted: 0,
    omittedByReason: {},
    omittedByCategory: {},
    omitted: [],
  };
}

function mockScanDiagnostics() {
  return {
    totalFiles: mockImages.length,
    totalImages: mockImages.length,
    totalOmitted: 0,
    omittedByReason: {},
    omittedByCategory: {},
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
    omittedByCategory: response.omittedByCategory || {},
    omitted,
  };
}

function renderBatchSummary() {
  const summary = $("#batch-summary");
  const visible = getVisibleAppState();
  const counts = visible.counts;
  const diagnostics = state.scanDiagnostics || emptyScanDiagnostics();
  const sourcePath = state.batch === "ready"
    ? activeFolders()[0]?.path || state.bridgeScanPath
    : state.batch === "empty" && state.realFolders.length
      ? state.realFolders[0]?.path || state.bridgeScanPath
      : state.bridgeScanPath;
  const outputLine = batchOutputLine();
  const destinationLine = batchDestinationLine();
  const warningsLabel = counts.nonBlockingWarnings ? countText(counts.nonBlockingWarnings, "aviso", "avisos") : "Sin avisos";
  const ignoredLabel = counts.ignoredFiles ? countText(counts.ignoredFiles, "ignorado", "ignorados") : "Sin ignorados";

  summary.innerHTML = batchViewHelpers.batchSummaryHtml({
    batch: state.batch,
    counts,
    destinationLine,
    diagnostics,
    hasScanError: state.scanIssues.some((issue) => issue.level === "error"),
    ignoredLabel,
    namingExample: namingExample(),
    namingLabel: namingHumanLabel(),
    outputLine,
    outputProfileName: outputProfileDisplayName(),
    sourceFolderName: sourceFolderName(),
    sourcePath,
    visible,
    warningsLabel,
  });
}

function batchOutputLine() {
  const profiles = exportOutputProfiles();
  return batchViewHelpers.batchOutputLine({
    background: state.background,
    format: state.format,
    profileLines: profiles.length > 1
      ? profiles.map((profile) => `${profile.format} ${outputProfileSize(profile).replace("x", "×")}`)
      : [],
    size: state.size,
  });
}

function outputProfilesSummaryLabel(profiles = exportOutputProfiles()) {
  return batchViewHelpers.outputProfilesSummaryLabel({
    backgroundLabel: backgroundLabel(state.background),
    format: state.format,
    profileLabels: profiles.length > 1 ? profiles.map((profile) => `${profile.name} (${profile.format})`) : [],
    sizeLabel: outputSizeDisplay(),
  });
}

function batchDestinationLine() {
  const profiles = exportOutputProfiles();
  return batchViewHelpers.batchDestinationLine({
    destinationMode: state.destinationMode,
    destinationValue: state.destinationValue,
    profileDestinations: profiles.length > 1 ? profiles.map(profileDestinationPreviewLabel) : [],
  });
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

function renderExportConfirm() {
  const modal = $("#export-confirm-modal");
  if (!modal) {
    return;
  }
  modal.classList.toggle("is-hidden", !state.exportConfirmOpen);
  modal.setAttribute("aria-hidden", state.exportConfirmOpen ? "false" : "true");
  if (!state.exportConfirmOpen) {
    return;
  }

  const risks = state.exportConfirmRisks.length ? state.exportConfirmRisks : exportConfirmationRisks();
  const body = $("#export-confirm-body");
  if (body) {
    body.innerHTML = exportConfirmHtml(risks);
  }
  const modalState = exportConfirmViewHelpers.exportConfirmModalState({
    actionText: exportActionLabel(batchCounts().exportableImages),
    risks,
  });
  const action = $("#export-confirm-action");
  if (action) {
    action.textContent = modalState.actionText;
    action.classList.toggle("danger", modalState.actionDanger);
  }
  const subtitle = $("#export-confirm-subtitle");
  if (subtitle) {
    subtitle.textContent = modalState.subtitle;
  }
}

function exportConfirmHtml(risks) {
  const counts = batchCounts();
  const exportable = counts.exportableImages;
  const summaryRows = [
    ["Imágenes", `${exportable} exportable${exportable === 1 ? "" : "s"}`],
    ["Salidas", outputProfilesSummaryLabel()],
    ["Destino", destinationFallbackLabel()],
    ["Nombre", namingExample()],
  ];
  return exportConfirmViewHelpers.exportConfirmHtml({ risks, summaryRows });
}

function batchDetailHtml() {
  const counts = batchCounts();
  const sourcePath = state.batch === "ready"
    ? activeFolders()[0]?.path || state.bridgeScanPath
    : state.batch === "empty" && state.realFolders.length
      ? state.realFolders[0]?.path || state.bridgeScanPath
      : state.bridgeScanPath;
  const files = counts.filesFound === null ? "Leyendo" : counts.filesFound;
  const valid = counts.validImages === null ? "Leyendo" : counts.validImages;
  const ignoredItems = ignoredOmissions();
  const ignoredRowsHtml = ignoredItems.slice(0, 8).map((item) => batchDetailViewHelpers.batchDetailProblemHtml({
    detail: item.detail || omissionReasonLabel(item.reason),
    title: item.name || "Archivo ignorado",
    titleAttr: item.path || item.name,
    tone: "clear",
  })).join("");
  const issueRowsHtml = actionableIssueRows().slice(0, 8).map((row) => batchDetailViewHelpers.batchDetailProblemHtml({
    detail: row.detail || "Revisar",
    title: row.title,
    titleAttr: row.path || row.title,
    tone: row.level === "error" ? "error" : "warning",
  })).join("");
  const outputRowsHtml = exportOutputProfiles().map((profile, index) => batchDetailViewHelpers.batchDetailOutputHtml({
    active: profile.id === state.activeOutputProfileId,
    destination: profileDestinationPreviewLabel(profile),
    example: outputNameForProfile(profile),
    index,
    name: profile.name,
    summary: outputProfileSummaryLine(profile),
  })).join("");
  const ignoredSectionHtml = batchDetailViewHelpers.batchDetailIgnoredSectionHtml({
    count: ignoredItems.length,
    rowsHtml: ignoredRowsHtml,
  });

  return batchDetailViewHelpers.batchDetailGridHtml({
    counts,
    files,
    ignoredSectionHtml,
    issueCount: actionableIssueRows().length,
    issueRowsHtml,
    outputRowsHtml,
    sourceFolderName: sourceFolderName(),
    sourcePath,
    stateTitle: getVisibleAppState().title,
    valid,
  });
}

function bridgeStatusClass() {
  return scanStateHelpers.bridgeStatusClass({
    bridgeMode: state.bridgeMode,
    bridgeStatus: state.bridgeStatus,
    devMode,
  });
}

function bridgeStatusLabel() {
  return scanStateHelpers.bridgeStatusLabel({
    bridgeMode: state.bridgeMode,
    bridgeStatus: state.bridgeStatus,
    devMode,
  });
}

function renderBatch() {
  const images = activeImages();
  const counts = batchCounts();
  const adjusted = images.filter((image) => image.status === "adjusted").length;
  const valid = images.filter((image) => image.status === "ready" || image.status === "adjusted").length;
  const warnings = images.filter((image) => image.status === "warning").length;
  const errors = images.filter((image) => image.status === "error" || exportItemState(image)?.status === "error").length;
  const ignored = counts.ignoredFiles;
  const issueCount = counts.reviewIssues;
  const filmstripCount = $("#filmstrip-count");
  $("#image-search").value = state.search;
  updateBatchSearchClear();
  renderGalleryViewButtons();

  if (state.batch === "none") {
    $("#batch-count").textContent = "Sin lote";
    setBatchPill("Sin carpeta", "muted");
    setGalleryTitle(0, "Sin lote");
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

  const sidebarSummaryText = batchViewHelpers.sidebarLotSummaryText({
    batch: state.batch,
    hasBatch: hasBatch(),
    nonBlockingWarnings: counts.nonBlockingWarnings,
    readyLabel: readyImagesText(counts.exportableImages),
    scanStatus: state.scanStatus,
  });

  if (state.batch === "scanning") {
    $("#batch-count").textContent = "Escaneando";
    setBatchPill("Escaneando", "active");
    setGalleryTitle(0, "Escaneando");
    $("#batch-visible-count").textContent = sidebarSummaryText;
    $("#folder-list").innerHTML = batchDetailViewHelpers.folderItemHtml({
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
          detail: "No hay PNG válidos",
          count: "0",
          status: "empty",
        }];
    $("#batch-count").textContent = "Sin imágenes";
    setBatchPill("Sin imágenes", "muted");
    setGalleryTitle(0, "No hay PNG válidos");
    $("#batch-visible-count").textContent = sidebarSummaryText;
    $("#folder-list").innerHTML = emptyFolders.map((folder) => batchDetailViewHelpers.folderItemHtml(folder)).join("");
    $("#image-list").innerHTML = "";
    $("#batch-empty-note").innerHTML = emptyBatchNoteHtml();
    if (filmstripCount) {
      filmstripCount.textContent = "Sin imágenes";
    }
    renderFilterButtons();
    return;
  }

  const exportable = exportableImages().length;
  $("#batch-count").textContent = exportable ? readyImagesText(exportable) : "Sin exportables";
  const batchPillState = batchViewHelpers.batchPillState({
    adjustedCount: adjusted,
    issueCount,
  });
  setBatchPill(batchPillState.label, batchPillState.tone);
  $("#folder-list").innerHTML = "";
  ensureGalleryFilterAvailable(images);
  renderFilterButtons();

  const visible = filteredImages();
  setGalleryTitle(exportable);
  $("#batch-visible-count").textContent = visible.length === images.length
    ? ""
    : `${visible.length}/${images.length}`;
  $("#image-list").innerHTML = visible.map(imageItemHtml).join("");
  queueThumbnailPreload();
  $("#batch-empty-note").innerHTML = visible.length ? "" : filteredEmptyHtml(images.length, valid, warnings, errors);
  if (filmstripCount) {
    filmstripCount.textContent = visible.length === images.length
      ? `${images.length} imágenes`
      : `${visible.length} de ${images.length}`;
  }
}

function setGalleryTitle(count, label = "") {
  const title = $("#gallery-title");
  if (title) {
    title.textContent = label || readyImagesText(Number(count) || 0);
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
  return galleryHelpers.filteredEmptyHtml({
    errors,
    filter: state.filter,
    search: state.search,
    total,
    valid,
    warnings,
  });
}

function filterEmptyDetail() {
  return galleryHelpers.filterEmptyDetail({
    filter: state.filter,
    search: state.search,
  });
}

function emptyBatchNoteHtml() {
  return galleryHelpers.emptyBatchNoteHtml({
    ignored: ignoredOmissions().length,
    ignoredSummary: ignoredSummaryText(),
    scanStatus: state.scanStatus,
  });
}

function imageThumbnailSrc(image) {
  if (!image) {
    return "";
  }
  if (image.source === "bridge") {
    return image.path ? bridgeThumbnailUrl(image.path) : "";
  }
  return galleryHelpers.mockThumbnailDataUrl(image);
}

function thumbnailState(image, src) {
  return galleryHelpers.thumbnailState({
    src,
    stored: state.thumbnailStatus[image.id],
  });
}

function queueThumbnailPreload() {
  if (!hasBatch() || state.exportStatus === "running") {
    return;
  }
  window.requestAnimationFrame(() => preloadBatchThumbnails());
}

function preloadBatchThumbnails() {
  if (state.exportStatus === "running") {
    return;
  }
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

function cancelThumbnailWork() {
  thumbnailPreloads.forEach((preloader) => {
    preloader.onload = null;
    preloader.onerror = null;
    preloader.src = "";
  });
  thumbnailPreloads.clear();
  thumbnailFallbackQueue.length = 0;
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
  if (state.exportStatus === "running") {
    return false;
  }
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
  const exportState = exportItemState(image);
  const imageStatus = hasCurrentImageOverride(image) ? "adjusted" : image.status;
  const thumbnailSrc = imageThumbnailSrc(image);
  return galleryHelpers.imageItemHtml({
    exportState,
    fileType: imageFileType(image),
    image,
    imageStatus,
    selected: image.id === state.selectedImageId,
    statusLabels,
    thumbState: thumbnailState(image, thumbnailSrc),
    thumbnailSrc,
  });
}

function galleryFilterCounts(images = activeImages()) {
  return galleryHelpers.galleryFilterCounts(images, exportItemStatusMap(images));
}

function ensureGalleryFilterAvailable(images = activeImages()) {
  const nextFilter = galleryHelpers.resolveAvailableFilter(state.filter, images, exportItemStatusMap(images));
  if (nextFilter !== state.filter) {
    state.filter = nextFilter;
  }
}

function renderFilterButtons() {
  const images = activeImages();
  const counts = galleryFilterCounts(images);
  const buttonStates = galleryHelpers.galleryFilterButtonStates({
    activeFilter: state.filter,
    counts,
  });
  const visibleCount = buttonStates.filter((item) => !item.hidden).length;
  const filterGroup = $(".gallery-filter");
  if (filterGroup) {
    filterGroup.hidden = visibleCount <= 1;
  }
  $$(".batch-filter button").forEach((button) => {
    const filter = button.dataset.filter;
    const buttonState = buttonStates.find((item) => item.filter === filter);
    if (!buttonState) {
      return;
    }
    button.innerHTML = `${escapeHtml(buttonState.label)} <span>${escapeHtml(buttonState.count)}</span>`;
    button.title = buttonState.title;
    button.style.order = String(buttonState.order);
    button.classList.toggle("active", buttonState.active);
    button.classList.toggle("is-empty", buttonState.empty);
    button.hidden = buttonState.hidden;
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
  const visibleImages = filteredImages();
  const filterIsEmpty = hasBatch() && activeImages().length > 0 && visibleImages.length === 0;
  const isBridgeImage = image?.source === "bridge";
  const previewControlsDisabled = !image || state.previewStatus === "empty" || state.previewStatus === "error";
  const compareControlsDisabled = !image || isBridgeImage || state.previewStatus === "empty" || state.previewStatus === "error";
  const previewName = image
    ? image.name
    : filterIsEmpty
      ? "Sin imágenes en este filtro"
    : state.batch === "none"
      ? "Selecciona una carpeta"
      : state.batch === "empty"
        ? "No se encontraron imágenes compatibles"
        : state.batch === "scanning"
          ? "Escaneando carpeta..."
          : "Selecciona una imagen";
  $("#preview-name").textContent = previewName;
  $("#preview-name").title = previewName;
  $("#preview-subtitle").textContent = previewSubtitle(image);
  $("#zoom-label").textContent = `${currentViewerZoom()}%`;
  const visibleIndex = visibleImages.findIndex((item) => item.id === state.selectedImageId);
  $("#viewer-position").textContent = visibleIndex >= 0
    ? `${visibleIndex + 1} / ${visibleImages.length}`
    : activeImages().length ? "Sin selección" : "Sin imagen";
  $("#preview-meta").textContent = isBridgeImage
    ? bridgePreviewMeta()
    : image ? state.activePreset : "Sin lote";
  const outputContext = $("#preview-output-context");
  if (outputContext) {
    outputContext.innerHTML = "";
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
        ? ignoredSummaryText()
        : "Esta carpeta no contiene imágenes compatibles.",
      actionLabel: "",
      action: "",
      meta: state.scanStatus || "",
    });
    queueFitZoomRefresh();
    return;
  }

  if (filterIsEmpty) {
    canvas.innerHTML = emptyStateHtml({
      variant: "inline",
      title: "No hay imágenes en este filtro",
      detail: filterEmptyDetail(),
      actionLabel: "Ver todas",
      action: "clear-filter",
      meta: `${activeImages().length} imágenes en el lote`,
    });
    queueFitZoomRefresh();
    return;
  }

  if (!image || state.previewStatus === "empty") {
    canvas.innerHTML = emptyStateHtml({
      variant: "inline",
      title: "Selecciona una imagen",
      detail: "Elige una miniatura para revisar.",
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
    canvas.innerHTML = previewViewHelpers.previewLoadingHtml(image.name);
    queueFitZoomRefresh();
    return;
  }

  if (state.previewStatus === "error") {
    canvas.innerHTML = previewStateHtml("Vista no disponible", "Revisa alpha o archivo fuente.");
    queueFitZoomRefresh();
    return;
  }

  canvas.innerHTML = previewViewHelpers.mockPreviewHtml({
    warning: state.previewStatus === "warning" ? "Render con fallback. Revisa antes de exportar." : "",
  });
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
    return previewViewHelpers.previewLoadingHtml(image.name);
  }

  if (state.previewStatus === "error") {
    return previewStateHtml("Vista no disponible", state.previewError || "Revisa la imagen fuente.");
  }

  if (state.previewData?.src) {
    return previewViewHelpers.realPreviewImageHtml({
      src: state.previewData.src,
      imageName: image.name,
      width: state.previewData.width,
      height: state.previewData.height,
      zoom: state.zoom,
      warning: state.previewData.warning,
    });
  }

  return previewViewHelpers.realPreviewPlaceholderHtml({
    imageName: image.name,
    imagePath: image.path,
  });
}

function bridgePreviewMeta() {
  return previewStateHelpers.bridgePreviewMeta({
    activePreset: state.activePreset,
    previewData: state.previewData,
    previewError: state.previewError,
    previewStatus: state.previewStatus,
  });
}

function previewSettingsLabel() {
  return previewStateHelpers.previewSettingsLabel({
    activePresetSource: activePresetItem()?.source,
    bridgeMode: state.bridgeMode,
    presetDirty: state.presetDirty,
  });
}

function outputSizeDisplay() {
  const size = parseOutputSize(state.size);
  return `${size.width}×${size.height}`;
}

function viewerOutputCompactLabel() {
  return previewViewHelpers.viewerOutputCompactLabel({
    backgroundLabel: backgroundLabel(state.background),
    format: state.format,
    sizeLabel: outputSizeDisplay(),
  });
}

function previewStateHtml(title, detail) {
  return emptyStateHtml({ variant: "inline", title, detail });
}

function emptyStateHtml({ variant = "inline", title, detail, actionLabel = "", action = "", meta = "" }) {
  return emptyStateViewHelpers.emptyStateHtml({ variant, title, detail, actionLabel, action, meta });
}

function initialStateHtml() {
  return emptyStateViewHelpers.initialStateHtml({
    bridgeScanPath: state.bridgeScanPath,
    devMode,
  });
}

function scanningStateHtml() {
  return previewViewHelpers.scanningStateHtml(state.scanStatus);
}

function previewOrientation() {
  return previewStateHelpers.previewOrientation(state.previewData);
}

function previewSubtitle(image) {
  const filterIsEmpty = !image && hasBatch() && activeImages().length && !filteredImages().length;
  return previewStateHelpers.previewSubtitle({
    batch: state.batch,
    filterEmptyDetail: filterIsEmpty ? filterEmptyDetail() : "",
    filterIsEmpty,
    hasImage: Boolean(image),
    imageDetail: image?.detail,
    imageSource: image?.source,
    previewStatus: state.previewStatus,
    scanStatus: state.scanStatus,
  });
}

function renderSettings() {
  renderReviewPanel();
  const activePreset = $("#active-preset");
  if (activePreset) {
    activePreset.textContent = state.activePreset;
  }
  $("#preset-source").textContent = `${state.activePreset} · ${presetSourceLabel()}`;
  $("#preset-dirty").textContent = settingsViewHelpers.presetDirtyLabel(state.presetDirty);
  $("#preset-dirty").classList.toggle("dirty", state.presetDirty);
  const presetItems = activePresetItems();
  const presetCount = $("#preset-count");
  if (presetCount) {
    presetCount.textContent = `${presetItems.length}`;
  }
  $("#preset-list").innerHTML = settingsViewHelpers.presetListHtml(presetItems, state.activePreset);

  Object.entries(state.settings).forEach(([key, value]) => {
    const input = $(`[data-setting="${key}"]`);
    const output = $(`#${key}-output`);
    const numberInput = $(`[data-setting-number="${key}"]`);
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
    if (numberInput && document.activeElement !== numberInput) {
      numberInput.value = value;
    }
  });

  const image = selectedImage();
  const localOverride = currentImageOverride(image);
  const localActive = Object.keys(localOverride).length > 0 || image?.status === "adjusted";
  $("#local-adjustment").classList.toggle("active", localActive);
  $("#local-adjustment-text").textContent = settingsViewHelpers.localAdjustmentText(localActive);
  localOverrideKeys.forEach((key) => {
    const value = Number(localOverride[key] || 0);
    const input = $(`[data-local-setting="${key}"]`);
    const output = $(`#local-${key}-output`);
    const numberInput = $(`[data-local-setting-number="${key}"]`);
    if (input) {
      input.value = value;
    }
    if (output) {
      output.textContent = settingsViewHelpers.localSettingOutputText(value);
    }
    if (numberInput && document.activeElement !== numberInput) {
      numberInput.value = value;
    }
  });
  const savePresetButton = $("#save-preset");
  const savePresetState = settingsViewHelpers.savePresetButtonState(state.presetDirty);
  savePresetButton.disabled = savePresetState.disabled;
  savePresetButton.title = savePresetState.title;
  savePresetButton.textContent = savePresetState.text;
  savePresetButton.classList.toggle("primary", savePresetState.primary);
  const deletePresetButton = $("#delete-preset");
  if (deletePresetButton) {
    const deletePresetState = settingsViewHelpers.deletePresetButtonState(presetItems.length);
    deletePresetButton.disabled = deletePresetState.disabled;
    deletePresetButton.title = deletePresetState.title;
  }
  const advanced = $("#advanced-settings");
  const advancedSummaryTitle = advanced?.querySelector("summary strong");
  if (advancedSummaryTitle) {
    advancedSummaryTitle.textContent = settingsViewHelpers.advancedSummaryTitle(advancedDirtyCount());
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
    return inspectorReviewViewHelpers.reviewPanelHtml({
      lotSummaryHtml: lotInspectorSummaryHtml(),
      emptyStateHtml: emptyStateHtml({
      variant: "inline",
      title: "Selecciona una imagen",
      detail: "Elige una miniatura para revisar la salida.",
      actionLabel: activeImages().length ? "Seleccionar primera imagen" : "",
      action: activeImages().length ? "select-first-image" : "",
    }),
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

  return inspectorReviewViewHelpers.reviewPanelHtml({
    lotSummaryHtml: lotInspectorSummaryHtml(),
    image,
    reviewState,
    issues,
    outputName,
    outputDetail,
    hasLocal,
    selectedIndexLabel: selectedIndex >= 0 ? `${selectedIndex + 1} de ${images.length}` : "Sin selección",
    canNavigate,
  });
}

function lotInspectorSummaryHtml() {
  const counts = batchCounts();
  const stateLabel = counts.blockingErrors
    ? `${counts.blockingErrors} bloqueo${counts.blockingErrors === 1 ? "" : "s"}`
    : counts.reviewIssues
      ? `${counts.reviewIssues} aviso${counts.reviewIssues === 1 ? "" : "s"}`
      : "Listo";
  return inspectorReviewViewHelpers.lotInspectorSummaryHtml({ counts, stateLabel });
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
  return outputProfileViewHelpers.outputNameForImage({
    folders: activeFolders(),
    format: state.format,
    image,
    index,
    naming: state.naming,
    suffix: state.suffix,
  });
}

function advancedDirtyCount() {
  const presetSettings = normalizeSettings(activePresetItem()?.settings || defaultSettings);
  return settingsViewHelpers.advancedDirtyCount({
    currentSettings: state.settings,
    keys: advancedSettingKeys,
    presetDirty: state.presetDirty,
    presetSettings,
  });
}

function advancedSettingsDirty() {
  return advancedDirtyCount() > 0;
}

function inspectorMode() {
  return inspectorContextViewHelpers.inspectorMode({
    inspectorTab: state.inspectorTab,
    outputEditMode: state.outputEditMode,
  });
}

function renderInspector() {
  const panel = $(".settings-panel");
  const mode = inspectorMode();
  const validTabs = ["review", "output", "warnings", "advanced"];
  if (!validTabs.includes(state.inspectorTab)) {
    state.inspectorTab = "review";
  }
  panel.classList.toggle("is-editing-output", state.outputEditMode);
  panel.classList.toggle("is-editing-preset", state.presetEditorOpen || mode === "advanced");
  panel.classList.toggle("is-inspector-subview", mode !== "summary");
  const start = $("#inspector-start");
  start.classList.remove("is-hidden");
  if (mode === "summary") {
    start.innerHTML = inspectorCardsHtml();
  } else {
    start.innerHTML = inspectorSubviewHeaderHtml(mode);
  }
  $(".inspector-tabs").classList.add("is-hidden");
  $$(".settings-panel [data-inspector-tab]").forEach((button) => {
    const active = button.dataset.inspectorTab === state.inspectorTab;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", active ? "true" : "false");
  });
  $$(".settings-panel [data-inspector-section]").forEach((section) => {
    const sectionName = section.dataset.inspectorSection;
    const visible = (mode === "output" && sectionName === "output")
      || (mode === "advanced" && sectionName === "advanced")
      || (mode === "warnings" && sectionName === "warnings");
    section.classList.toggle(
      "is-hidden",
      !visible
    );
  });
  syncAdvancedInspectorDetails(mode);
}

function syncAdvancedInspectorDetails(mode) {
  $$(".settings-panel details.inspector-disclosure[data-inspector-section='advanced']").forEach((details) => {
    if (mode !== "advanced") {
      details.open = false;
      return;
    }
    if (state.presetEditorOpen) {
      details.open = details.classList.contains("preset-section");
      return;
    }
    if (details.classList.contains("preset-section")) {
      details.open = false;
      return;
    }
    if (
      details.classList.contains("appearance-section")
      || details.classList.contains("local-adjustment")
      || (state.presetEditorOpen && details.classList.contains("preset-section"))
    ) {
      details.open = true;
    }
  });
}

function inspectorCardsHtml() {
  if (state.batch === "scanning") {
    return `
      <section class="inspector-card inspector-card--busy">
        <div class="inspector-card__head">
          <span>Escaneo</span>
          <strong>Escaneando carpeta...</strong>
        </div>
        <small>${escapeHtml(state.scanStatus || "Leyendo imágenes")}</small>
        ${exportPreflightViewHelpers.progressPanelHtml("Escaneando carpeta")}
      </section>
    `;
  }

  if (state.batch === "none") {
    return "";
  }

  return [
    lotInspectorCardHtml(),
    outputInspectorCardHtml(),
    selectedImageInspectorCardHtml(),
    issuesInspectorCardHtml(),
    aspectInspectorCardHtml(),
  ].filter(Boolean).join("");
}

function lotInspectorCardHtml() {
  const counts = batchCounts();
  const visible = getVisibleAppState();
  const ignored = counts.ignoredFiles ? "Ignorados técnicos en detalle" : "";
  const meta = state.batch === "empty"
    ? `${readyImagesText(0)}${ignored ? ` · ${ignored}` : ""}`
    : `${readyImagesText(counts.exportableImages)}${ignored ? ` · ${ignored}` : ""}`;
  const tone = counts.blockingErrors ? "error" : counts.nonBlockingWarnings ? "warning" : "";
  return inspectorReviewViewHelpers.lotInspectorCardHtml({
    meta,
    title: visible.title,
    tone,
  });
}

function outputInspectorCardHtml() {
  const profiles = state.outputProfiles.length ? state.outputProfiles : [currentOutputProfileData()];
  const activeProfiles = exportOutputProfiles();
  const exportable = exportableImages().length;
  const totalFiles = exportable * activeProfiles.length;
  const dirty = !outputMatchesProfile(activeOutputProfile());
  const rows = profiles.map((profile) => {
    const enabled = Boolean(profile.enabled || profile.id === state.activeOutputProfileId);
    return {
      id: profile.id,
      name: profile.name,
      enabled,
      active: profile.id === state.activeOutputProfileId,
      canToggle: enabledOutputProfiles().length > 1 || !enabled,
      summary: outputProfileSummaryLine(profile),
    };
  });
  return inspectorOutputViewHelpers.outputInspectorCardHtml({
    activeCount: activeProfiles.length,
    totalFiles,
    readyLabel: exportable ? readyImagesText(exportable) : "Sin imágenes listas",
    rows,
    dirty,
  });
}

function outputProfileInlineRowHtml(profile) {
  const enabled = Boolean(profile.enabled || profile.id === state.activeOutputProfileId);
  return inspectorOutputViewHelpers.outputProfileInlineRowHtml({
    id: profile.id,
    name: profile.name,
    enabled,
    active: profile.id === state.activeOutputProfileId,
    canToggle: enabledOutputProfiles().length > 1 || !enabled,
    summary: outputProfileSummaryLine(profile),
  });
}

function selectedImageInspectorCardHtml() {
  const image = selectedImage();
  const hasLocal = image ? hasCurrentImageOverride(image) || image.status === "adjusted" : false;
  return inspectorReviewViewHelpers.selectedImageInspectorCardHtml({
    hasReadyBatch: hasBatch() && state.batch === "ready",
    image,
    detail: image ? image.detail || imageFileType(image) : "",
    hasLocal,
  });
}

function issuesInspectorCardHtml() {
  const rows = actionableIssueRows();
  if (!rows.length) {
    return "";
  }
  const errors = rows.filter((row) => row.level === "error").length;
  const blocking = preflightCounts().errors > 0;
  const count = blocking
    ? `${preflightCounts().errors} bloqueo${preflightCounts().errors === 1 ? "" : "s"}`
    : errors
      ? `${errors} error${errors === 1 ? "" : "es"}`
    : `${rows.length} aviso${rows.length === 1 ? "" : "s"}`;
  return inspectorReviewViewHelpers.issuesInspectorCardHtml({
    rows,
    blocking,
    countLabel: count,
  });
}

function aspectInspectorCardHtml() {
  return inspectorReviewViewHelpers.aspectInspectorCardHtml({
    hasReadyBatch: hasBatch() && state.batch === "ready",
    activePreset: state.activePreset,
    statusLabel: state.presetDirty ? "Global · Modificado" : "Global",
  });
}

function actionableIssueRows() {
  const rows = issueRows().filter((row) => !["info", "ignored"].includes(row.level));
  const validationRows = validationIssues()
    .filter((issue) => issue.title !== "Sin lote" && issue.title !== "No hay PNG válidos")
    .map((issue) => ({
      level: issue.level,
      title: issue.title,
      detail: issue.detail,
      path: "",
      actionLabel: "",
    }));
  const seen = new Set();
  return [...validationRows, ...rows].filter((row) => {
    const key = `${row.level}|${row.title}|${row.detail || ""}`;
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
}

function inspectorSubviewHeaderHtml(mode) {
  return inspectorContextViewHelpers.inspectorSubviewHeaderHtml(
    inspectorContextViewHelpers.inspectorSubviewHeaderState({
      activePreset: state.activePreset,
      mode,
      outputEditMode: state.outputEditMode,
      outputLabel: viewerOutputCompactLabel(),
      presetEditorOpen: state.presetEditorOpen,
      presetSourceLabel: presetSourceLabel(),
      warningCount: actionableIssueRows().length,
    })
  );
}

function contextualInspectorHtml() {
  if (state.batch === "scanning") {
    return inspectorContextViewHelpers.contextualInspectorHtml({
      batch: state.batch,
      scanStatus: state.scanStatus,
      progressHtml: exportPreflightViewHelpers.progressPanelHtml("Preparando lote"),
      preflightHtml: exportPreflightViewHelpers.preflightListHtml(inspectorContextViewHelpers.contextualPreflightRows({
        batch: state.batch,
      })),
    });
  }

  if (state.batch === "none") {
    return inspectorContextViewHelpers.contextualInspectorHtml({
      batch: state.batch,
      preflightHtml: exportPreflightViewHelpers.preflightListHtml(inspectorContextViewHelpers.contextualPreflightRows({
        batch: state.batch,
      })),
      outputSummary: `${state.format} · ${state.size} · ${backgroundLabel(state.background)}`,
      activePreset: state.activePreset,
    });
  }

  if (state.batch === "empty") {
    return inspectorContextViewHelpers.contextualInspectorHtml({
      batch: state.batch,
      scanStatus: state.scanStatus,
      preflightHtml: exportPreflightViewHelpers.preflightListHtml(inspectorContextViewHelpers.contextualPreflightRows({
        batch: state.batch,
        ignoredSummary: ignoredSummaryText(),
        totalFiles: state.scanDiagnostics.totalFiles,
      })),
    });
  }

  return inspectorContextViewHelpers.contextualInspectorHtml({
    batch: state.batch,
    compactStatus: compactHeaderStatusText(),
  });
}

function presetSourceLabel() {
  return settingsViewHelpers.presetSourceLabel({
    bridgePresetWarning: state.bridgePresetWarning,
    presetDirty: state.presetDirty,
  });
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
  const activeOutputs = exportOutputCount();
  const outputCount = exportable * activeOutputs;
  const ready = isExportReady();
  const destinationText = destinationCompactLabel();
  const warningCount = visibleWarningCount();
  $("#export-readiness").textContent = state.outputEditMode ? "Editar salida" : outputProfileDisplayName();
  $("#export-count").textContent = outputCount ? `${outputCount} archivos` : "Pendiente";
  $("#export-count").classList.toggle("dirty", !ready);
  const warningsReadiness = $("#warnings-readiness");
  if (warningsReadiness) {
    warningsReadiness.textContent = warningCount ? `${warningCount} aviso${warningCount === 1 ? "" : "s"}` : "Sin avisos";
  }
  const warningsTab = $("[data-inspector-tab='warnings']");
  if (warningsTab) {
    warningsTab.textContent = warningCount ? `Avisos ${warningCount}` : "Avisos";
  }

  const warningSummary = outputWarningSummary(issues);
  const editDirty = !outputMatchesProfile(activeOutputProfile());
  const activeOutputProfiles = exportOutputProfiles();
  const hasMultipleOutputs = activeOutputProfiles.length > 1;
  $("#export-summary").innerHTML = exportSummaryViewHelpers.exportSummaryHtml({
    editing: state.outputEditMode,
    displayName: outputProfileDisplayName(),
    presetSummary: presetSummaryLine(),
    editDirty,
    activeOutputCount: activeOutputProfiles.length,
    outputCount,
    profileRows: activeOutputProfiles.map((profile) => ({
      format: profile.format,
      name: profile.name,
      size: outputProfileSize(profile),
      destinationLabel: profileDestinationLabel(profile),
    })),
    formatLabel: hasMultipleOutputs ? batchViewHelpers.outputCountLabel(activeOutputProfiles.length) : state.format,
    sizeLabel: hasMultipleOutputs ? "Por salida" : state.size.replace("x", " × "),
    backgroundLabel: hasMultipleOutputs ? "Por salida" : backgroundLabel(state.background),
    destinationText,
    namingLabel: hasMultipleOutputs ? "Por salida" : namingHumanLabel(),
    example: hasMultipleOutputs ? outputNameForProfile(activeOutputProfiles[0]) : namingExample(),
    warningSummaryHtml: warningSummary,
    temporaryNoticeHtml: !outputMatchesProfile(activeOutputProfile()) ? inspectorOutputViewHelpers.outputTemporaryNoticeHtml() : "",
  });

  renderExportResult();

  $("#issue-list").innerHTML = issueListHtml();
}

function renderOutputProfileSelect() {
  const select = $("#output-profile-select");
  if (!select) {
    return;
  }
  select.innerHTML = exportSummaryViewHelpers.outputProfileSelectOptionsHtml(
    state.outputProfiles,
    { includeCustom: !outputMatchesProfile() }
  );
  select.value = outputMatchesProfile() ? state.activeOutputProfileId : "__custom";
}

function outputProfileDisplayName() {
  const profiles = exportOutputProfiles();
  if (profiles.length > 1) {
    return batchViewHelpers.outputCountLabel(profiles.length);
  }
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
  return outputProfileViewHelpers.profileDestinationLabel(profile);
}

function profileDestinationPreviewLabel(profile) {
  return outputProfileViewHelpers.profileDestinationPreviewLabel(profile);
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

function outputProfileRawFromProfile(profile) {
  return {
    id: profile.id,
    name: profile.name,
    format: profile.format,
    background: profile.background,
    width: String(profile.width),
    height: String(profile.height),
    destinationMode: profile.destinationMode,
    destinationValue: profile.destinationValue,
    naming: profile.naming,
    suffix: profile.suffix,
  };
}

function outputProfileDraftFromForm() {
  const current = ensureOutputProfileDraft();
  const raw = outputProfileFormRawData();
  return normalizeOutputProfile({
    id: current.id,
    name: raw.name,
    enabled: current.enabled,
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
    enabled: true,
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
    enabled: true,
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
  state.outputProfiles = normalizeOutputProfileList(state.outputProfiles, saved.id);
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
    next.enabled = true;
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
  rememberModalFocusReturn();
  state.batchDetailOpen = false;
  state.exportConfirmOpen = false;
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
  queueModalFocus("#app-settings-modal", "[data-action='apply-output-profile']");
}

function closeAppSettings() {
  if (state.appSettingsOpen && outputProfileHasUnsavedChanges() && !confirmDiscardOutputDraft("cerrar sin guardar")) {
    return;
  }
  releaseModalFocusBeforeHide();
  state.appSettingsOpen = false;
  state.outputProfileDraft = null;
  state.statusText = "Configuración cerrada";
  render();
}

function openBatchDetail() {
  rememberModalFocusReturn();
  state.exportConfirmOpen = false;
  state.batchDetailOpen = true;
  state.statusText = "Detalle del lote";
  render();
  queueModalFocus("#batch-detail-modal", "[data-action='close-batch-detail']");
}

function closeBatchDetail() {
  releaseModalFocusBeforeHide();
  state.batchDetailOpen = false;
  state.statusText = hasBatch() ? "Lote cargado" : "Sin lote";
  render();
}

function openExportConfirm(risks, options = {}) {
  rememberModalFocusReturn();
  state.appSettingsOpen = false;
  state.outputProfileDraft = null;
  state.batchDetailOpen = false;
  state.exportConfirmOpen = true;
  state.exportConfirmRisks = dedupeExportRisks(risks);
  state.exportConfirmOptions = { ...options };
  state.statusText = state.exportConfirmRisks.some((risk) => risk.blocking)
    ? "Resuelve problemas antes de exportar"
    : "Confirmar exportación";
  render();
  queueModalFocus("#export-confirm-modal", "#export-confirm-action");
}

function closeExportConfirm({ renderAfter = true } = {}) {
  releaseModalFocusBeforeHide();
  state.exportConfirmOpen = false;
  state.exportConfirmRisks = [];
  state.exportConfirmOptions = null;
  if (renderAfter) {
    render();
  }
}

function confirmExportFromModal() {
  const risks = state.exportConfirmRisks || [];
  if (risks.some((risk) => risk.blocking)) {
    closeExportConfirm({ renderAfter: false });
    reviewWarnings();
    return;
  }
  const options = { ...(state.exportConfirmOptions || {}), confirmed: true };
  closeExportConfirm({ renderAfter: false });
  startExport(options);
}

function rememberModalFocusReturn() {
  const active = document.activeElement;
  if (
    active instanceof HTMLElement
    && active !== document.body
    && !active.closest(".app-settings-backdrop")
  ) {
    modalFocusReturnTarget = active;
  }
}

function restoreModalFocusReturn() {
  const target = modalFocusReturnTarget;
  modalFocusReturnTarget = null;
  if (target instanceof HTMLElement && document.contains(target)) {
    target.focus({ preventScroll: true });
  }
}

function releaseModalFocusBeforeHide() {
  const active = document.activeElement;
  if (active instanceof HTMLElement && active.closest(".app-settings-backdrop")) {
    active.blur();
  }
  restoreModalFocusReturn();
}

function queueModalFocus(modalSelector, preferredSelector = "") {
  window.requestAnimationFrame(() => {
    const modal = $(modalSelector);
    if (!modal || modal.classList.contains("is-hidden")) {
      return;
    }
    const preferred = preferredSelector ? modal.querySelector(preferredSelector) : null;
    const fallback = firstFocusableElement(modal);
    (preferred || fallback)?.focus({ preventScroll: true });
  });
}

function firstFocusableElement(container) {
  return Array.from(container.querySelectorAll(
    "button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), summary, [tabindex]:not([tabindex='-1'])"
  )).find((element) => element.offsetParent !== null);
}

function currentOpenModal() {
  if (state.exportConfirmOpen) {
    return $("#export-confirm-modal");
  }
  if (state.appSettingsOpen) {
    return $("#app-settings-modal");
  }
  if (state.batchDetailOpen) {
    return $("#batch-detail-modal");
  }
  return null;
}

function trapOpenModalFocus(event) {
  const modal = currentOpenModal();
  if (!modal || modal.classList.contains("is-hidden")) {
    return false;
  }
  const focusable = Array.from(modal.querySelectorAll(
    "button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), summary, [tabindex]:not([tabindex='-1'])"
  )).filter((element) => element.offsetParent !== null);
  if (!focusable.length) {
    event.preventDefault();
    return true;
  }
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  const active = document.activeElement;
  if (event.shiftKey && active === first) {
    event.preventDefault();
    last.focus({ preventScroll: true });
    return true;
  }
  if (!event.shiftKey && active === last) {
    event.preventDefault();
    first.focus({ preventScroll: true });
    return true;
  }
  if (!modal.contains(active)) {
    event.preventDefault();
    first.focus({ preventScroll: true });
    return true;
  }
  return false;
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
  return outputProfileHelpers.outputProfileValidation(raw);
}

function outputProfileEditorHeadingHtml(profile, validation, dirty) {
  return outputProfileViewHelpers.outputProfileEditorHeadingHtml({
    profile,
    validation,
    dirty,
    active: profile.id === state.activeOutputProfileId,
    summary: outputProfileSummaryLine(profile),
  });
}

function outputProfilePreviewHtml(profile) {
  const image = selectedImage();
  const originalName = image?.name || "imagen_original.png";
  const resultName = outputNameForProfile(profile, image);
  const destination = profileDestinationPreviewLabel(profile);
  const resultPath = destination && destination !== "junto al origen"
    ? `${destination.replace(/[\\/]$/, "")}/${resultName}`
    : resultName;
  return outputProfileViewHelpers.outputProfilePreviewHtml({
    originalName,
    resultName,
    destination,
    resultPath,
    summary: outputProfileSummaryLine(profile),
  });
}

function outputNameForProfile(profile, image = selectedImage(), index = 1) {
  return outputProfileViewHelpers.outputNameForProfile(profile, {
    folders: activeFolders(),
    image,
    index,
  });
}

function outputProfileValidationHtml(validation) {
  return outputProfileViewHelpers.outputProfileValidationHtml(validation);
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
  const footerState = outputProfileViewHelpers.outputProfileFooterState({
    draft,
    dirty,
    isPersisted,
    profileCount: state.outputProfiles.length,
    validation,
  });
  const deleteButton = $("[data-action='delete-output-profile']");
  if (deleteButton) {
    deleteButton.disabled = footerState.deleteDisabled;
    deleteButton.title = footerState.deleteTitle;
  }
  const resetButton = $("[data-action='reset-output-profile-draft']");
  if (resetButton) {
    resetButton.disabled = footerState.resetDisabled;
  }
  const saveButton = $("[data-action='save-output-profile']");
  if (saveButton) {
    saveButton.disabled = footerState.saveDisabled;
  }
  const applyButton = $("[data-action='apply-output-profile']");
  if (applyButton) {
    applyButton.disabled = footerState.applyDisabled;
    applyButton.textContent = footerState.applyLabel;
  }
  const footerNote = $("#output-profile-unsaved");
  if (footerNote) {
    footerNote.textContent = footerState.noteText;
    footerNote.className = footerState.noteClass;
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
    const enabled = profile.enabled;
    const unsaved = !state.outputProfiles.some((item) => item.id === profile.id);
    const canToggle = !unsaved && (enabledOutputProfiles().length > 1 || !enabled);
    return outputProfileViewHelpers.outputProfileManagerRowHtml({
      profile,
      selected,
      active,
      enabled,
      unsaved,
      canToggle,
      summary: outputProfileSummaryLine(profile),
      destination: profileDestinationLabel(profile),
    });
  }).join("");
  setOutputProfileFormValues(draft);
  renderOutputProfileModalState();
}

function presetSummaryLine() {
  return settingsViewHelpers.presetSummaryLine({
    background: state.background,
    format: state.format,
    size: state.size,
  });
}

function destinationCompactLabel() {
  return outputProfileViewHelpers.destinationCompactLabel({
    destinationMode: state.destinationMode,
    destinationValue: state.destinationValue,
  });
}

function namingHumanLabel() {
  return outputProfileViewHelpers.namingHumanLabel({
    naming: state.naming,
    suffix: state.suffix,
  });
}

function outputWarningSummary(issues) {
  return exportPreflightViewHelpers.outputWarningSummaryHtml({
    issues,
    firstIssue: firstActionableIssue(),
    visibleWarningCount: visibleWarningCount(),
  });
}

function issueListHtml() {
  return exportPreflightViewHelpers.issueListHtml({
    hasActiveBatch: hasBatch(),
    batch: state.batch,
    rows: issueRows(),
    counts: preflightCounts(),
    warningCount: visibleWarningCount(),
  });
}

function issueRows() {
  return exportPreflightViewHelpers.issueRows({
    scanOmissions: scanOmissions().map((item) => ({
      ...item,
      reasonLabel: omissionReasonLabel(item.reason),
      severity: omissionSeverity(item),
    })),
    images: activeImages().map((image) => ({
      ...image,
      exportStatus: exportItemState(image)?.status,
    })),
    errors: state.errors,
    statusLabels,
  });
}

function exportStatusClass(ready, issues = preflightIssues()) {
  return exportPreflightViewHelpers.exportStatusClass({
    hasActiveBatch: hasBatch(),
    issues,
    ready,
    status: state.exportStatus,
  });
}

function exportPreflightRows(issues, exportable, ready) {
  return exportPreflightViewHelpers.exportPreflightRows({
    batch: state.batch,
    destinationFallback: destinationFallbackLabel(),
    destinationMissing: state.destinationMode === "custom" && !state.destinationValue.trim(),
    exportable,
    ignoredCount: ignoredOmissions().length,
    ignoredSummary: ignoredSummaryText(),
    issues,
    naming: state.naming,
    namingExample: namingExample(),
    ready,
    warningCount: visibleWarningCount(),
  });
}

function exportPanelStatusLabel(ready, issues = preflightIssues()) {
  return exportPreflightViewHelpers.exportPanelStatusLabel({
    status: state.exportStatus,
    paused: state.paused,
    batch: state.batch,
    hasActiveBatch: hasBatch(),
    ready,
    issues,
  });
}

function exportPreflightSummary(issues, exportable, ready) {
  return exportPreflightViewHelpers.exportPreflightSummary({ issues, exportable, ready });
}

function namingExample() {
  const image = exportableImages()[0] || selectedImage();
  const originalName = image?.name || "imagen_001.png";
  return outputProfileViewHelpers.namingExample({
    folder: activeFolders()[0]?.name || "lote",
    format: state.format,
    naming: state.naming,
    original: originalName.replace(/\.[^.]+$/, ""),
    suffix: state.suffix,
  });
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
  const meta = exportResultMeta(processed, total, errors);
  const actionsHtml = exportResultActionsHtml(issues, destinations);

  target.innerHTML = exportResultViewHelpers.exportResultHtml({
    status: state.exportStatus,
    title,
    meta,
    processed,
    total,
    errors,
    destinations,
    destinationFallback: destinationFallbackLabel(),
    currentFileLabel: currentExportFileLabel(),
    issues,
    issueSummary: exportIssueActionText(issues[0]),
    items,
    actionsHtml,
  });
}

function exportResultTitle() {
  return exportResultViewHelpers.exportResultTitle(state.exportStatus, state.paused);
}

function exportResultMeta(processed, total, errors) {
  return exportResultViewHelpers.exportResultMeta({
    status: state.exportStatus,
    processed,
    total,
    errors,
  });
}

function currentExportFileLabel() {
  return exportResultViewHelpers.currentExportFileLabel({
    images: exportableImages(),
    processed: state.processed,
    statusText: state.statusText,
  });
}

function exportIssueActionText(issue) {
  return exportResultViewHelpers.exportIssueActionText(issue, {
    existingOutput: issueMentionsExistingOutput(issue),
  });
}

function exportResultActionsHtml(issues, destinations) {
  return exportResultViewHelpers.exportResultActionsHtml({
    status: state.exportStatus,
    issues,
    destinations,
    canOpenOutput: Boolean(outputDestinationToOpen()),
    canRetry: isExportReady(),
  });
}

function destinationFallbackLabel() {
  const profiles = exportOutputProfiles();
  return outputProfileViewHelpers.destinationFallbackLabel({
    destinationMode: state.destinationMode,
    destinationValue: state.destinationValue,
    destinations: profiles.length > 1 ? profiles.map(profileDestinationPreviewLabel) : [],
  });
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

function saveCurrentOutputProfile() {
  const current = currentOutputProfileData();
  const index = state.outputProfiles.findIndex((profile) => profile.id === state.activeOutputProfileId);
  if (index < 0) {
    state.outputProfiles.push({ ...current, enabled: true });
  } else {
    state.outputProfiles[index] = {
      ...state.outputProfiles[index],
      ...current,
      id: state.activeOutputProfileId,
      name: state.outputProfiles[index].name || current.name,
      enabled: true,
    };
  }
  state.outputProfiles = normalizeOutputProfileList(state.outputProfiles, state.activeOutputProfileId);
  state.outputDraft = null;
  state.outputEditMode = false;
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = "Preset de salida guardado";
  persistOutputProfiles();
  render();
}

function saveCurrentOutputAsNewProfile() {
  const sourceName = activeOutputProfile()?.name || "Salida";
  const name = window.prompt("Nombre del nuevo preset de salida", `${sourceName} copia`);
  if (name === null) {
    return;
  }
  const profile = normalizeOutputProfile({
    ...currentOutputProfileData(),
    id: uniqueOutputProfileId(name || "salida", Date.now()),
    name: name.trim() || "Nueva salida",
    enabled: true,
  });
  state.outputProfiles = normalizeOutputProfileList([...state.outputProfiles, profile], profile.id);
  state.activeOutputProfileId = profile.id;
  state.outputProfileEditorId = profile.id;
  state.outputProfileDraft = { ...profile };
  state.outputDraft = null;
  state.outputEditMode = false;
  persistOutputProfiles();
  state.statusText = `Nuevo preset: ${profile.name}`;
  render();
}

function discardOutputOverrides() {
  const profile = activeOutputProfile();
  if (!profile) {
    return;
  }
  state.outputDraft = null;
  state.outputEditMode = false;
  applyOutputProfile(profile.id, { statusText: "Cambios temporales descartados" });
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
  state.statusText = "Gestionar ajustes";
  render();
}

function closePresetEditor() {
  state.presetEditorOpen = false;
  state.inspectorTab = "advanced";
  state.statusText = "Editar ajuste";
  render();
}

function exportStatusLabel(ready) {
  return settingsViewHelpers.exportStatusLabel({
    exportStatus: state.exportStatus,
    paused: state.paused,
    ready,
  });
}

function backgroundLabel(value) {
  return settingsViewHelpers.backgroundLabel(value);
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
    || counts.reviewIssues > 0
    || activeImages().some((image) => image.status === "error" || image.status === "warning" || exportItemState(image)?.status === "error")
  );
  $("#review-errors").classList.toggle("is-hidden", !hasReviewIssues);
  $("#review-errors").disabled = !hasReviewIssues;
  $("#review-errors").textContent = "Revisar avisos";
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

function renderAccessibilityHints() {
  const visible = getVisibleAppState();
  const counts = batchCounts();
  setControlHint($("#top-primary-action"), topPrimaryHint(visible));
  setControlHint($("#top-secondary-action"), visible.secondaryAction ? `${visible.secondaryAction.label}. Atajo: Ctrl+E si exporta.` : "");
  setControlHint($("[data-action='open-batch-detail']"), "Abrir detalle del lote");
  setControlHint($("[data-action='open-app-settings']"), "Abrir formatos y salida");
  setControlHint($("[data-action='toggle-inspector']"), "Mostrar u ocultar detalle técnico");
  setControlHint($("#image-search"), "Buscar por nombre, referencia o ruta");
  setControlHint($("#image-search-clear"), "Limpiar búsqueda");

  const galleryViewHints = {
    thumbs: "Ver galería como miniaturas",
    list: "Ver galería como lista compacta",
  };
  $$("[data-gallery-view]").forEach((button) => {
    setControlHint(button, galleryViewHints[button.dataset.galleryView] || button.textContent.trim());
  });

  const filterCounts = {
    all: activeImages().length,
    valid: counts.readyImages,
    warnings: counts.warningImages,
    excluded: counts.nonExportableImages,
  };
  const filterHints = {
    all: "Mostrar todas las imágenes",
    valid: "Mostrar imágenes listas",
    warnings: "Mostrar imágenes con aviso",
    excluded: "Mostrar imágenes ignoradas o no exportables",
  };
  $$("[data-filter]").forEach((button) => {
    const filter = button.dataset.filter;
    setControlHint(button, `${filterHints[filter] || button.textContent.trim()} · ${filterCounts[filter] || 0}`);
  });

  const previewModeHints = {
    processed: "Ver previsualización con el formato activo",
    original: "Ver imagen original",
    compare: "Comparar original y previsualización",
  };
  $$("[data-preview-mode]").forEach((button) => {
    setControlHint(button, previewModeHints[button.dataset.previewMode] || button.textContent.trim());
    button.setAttribute("aria-pressed", button.classList.contains("active") ? "true" : "false");
  });

  const backgroundHints = {
    rgb230: "Fondo gris claro RGB 230",
    white: "Fondo blanco",
    transparent: "Fondo transparente",
  };
  $$("[data-preview-bg]").forEach((button) => {
    setControlHint(button, backgroundHints[button.dataset.previewBg] || button.textContent.trim());
    button.setAttribute("aria-pressed", button.classList.contains("active") ? "true" : "false");
  });

  const zoomHints = {
    "previous-image": "Imagen anterior. Atajo: flecha izquierda",
    "next-image": "Imagen siguiente. Atajo: flecha derecha",
    "zoom-fit": "Encajar imagen en el visor. Atajo: F",
    "zoom-height": "Ajustar a la altura del visor",
    "zoom-width": "Ajustar a la anchura del visor",
    "zoom-100": "Ver al 100 %. Atajo: 1",
    "zoom-out": "Reducir zoom",
    "zoom-in": "Aumentar zoom",
  };
  Object.entries(zoomHints).forEach(([action, hint]) => {
    setControlHint($(`[data-action='${action}']`), hint);
  });

  $$(".settings-panel [data-inspector-tab]").forEach((button) => {
    const active = button.dataset.inspectorTab === state.inspectorTab;
    button.setAttribute("aria-pressed", active ? "true" : "false");
    setControlHint(button, `${button.textContent.trim()} del inspector`);
  });
}

function topPrimaryHint(visible) {
  return topStatusViewHelpers.topPrimaryHint(visible);
}

function setControlHint(target, hint) {
  if (!target || !hint) {
    return;
  }
  target.title = hint;
  if (!target.getAttribute("aria-label") && target.textContent.trim().length <= 2) {
    target.setAttribute("aria-label", hint.replace(/\s*\. Atajo:.*$/, ""));
  }
}

function renderDesignSystemComponents() {
  $$("button").forEach((button) => {
    button.classList.add("ui-button");
    const isIcon = button.classList.contains("icon-button")
      || (button.textContent.trim().length <= 2 && Boolean(button.getAttribute("aria-label")));
    const isPrimary = button.classList.contains("primary");
    const isDanger = button.classList.contains("danger-subtle") || button.classList.contains("danger");
    const isGhost = button.classList.contains("btn-linklike");
    button.classList.toggle("ui-button--icon", isIcon);
    button.classList.toggle("ui-button--primary", isPrimary);
    button.classList.toggle("ui-button--danger", isDanger);
    button.classList.toggle("ui-button--ghost", isGhost);
    button.classList.toggle("ui-button--secondary", !isPrimary && !isDanger && !isGhost && !isIcon);
  });

  addComponentClass(".top-bar", "ui-top-bar");
  addComponentClass(".workspace", "ui-app-workspace");
  addComponentClass(".gallery-column", "ui-gallery-panel");
  addComponentClass(".preview-panel", "ui-viewer-panel");
  addComponentClass(".settings-panel", "ui-inspector-panel");
  addComponentClass(".bottom-bar", "ui-status-bar");
  addComponentClass(".preview-toolbar, .gallery-toolbar, .settings-toolbar, .top-actions, .inspector-actionbar, .warning-actions, .result-actions", "ui-toolbar");
  addComponentClass(".segmented", "ui-segmented-control");
  addComponentClass(".inspector-tabs", "ui-tabs");
  addComponentClass(".state-chip, .status-badge, .preflight-chip, .batch-rail__badge, .asset-state", "ui-status-badge");
  addComponentClass(".batch-summary-card, .preset-summary-card, .compact-panel, .review-card, .format-preview-card, .format-validation-card, .export-confirm-summary, .inspector-output-card, .inspector-summary, .inspector-compact-row, .active-output-row, .output-profile-option", "ui-summary-card");
  addComponentClass(".image-item", "ui-thumbnail-card");
  addComponentClass(".settings-section, .batch-detail-section, .export-confirm-section, .context-panel", "ui-inspector-section");
  addComponentClass(".app-settings-dialog", "ui-modal-shell");
  addComponentClass(".app-settings-backdrop", "ui-modal-backdrop");
  addComponentClass(".empty-state", "ui-empty-state");
  addComponentClass(".progress-track, .context-progress", "ui-progress-state");
  addComponentClass(".issue-item, .export-confirm-risk, .batch-detail-problem", "ui-problem-card");
}

function addComponentClass(selector, className) {
  $$(selector).forEach((element) => element.classList.add(className));
}

function statusBarText() {
  const images = activeImages();
  const counts = batchCounts();
  const selectedIndex = images.findIndex((image) => image.id === state.selectedImageId);
  return topStatusViewHelpers.statusBarText({
    batch: state.batch,
    counts,
    destinationMode: state.destinationMode,
    destinationValue: state.destinationValue,
    exportResultProcessed: state.exportResult?.processed,
    exportResultTotal: state.exportResult?.total,
    exportStatus: state.exportStatus,
    exportableImageCount: exportableImages().length,
    firstErrorDetail: state.errors[0]?.detail,
    imageCount: images.length,
    outputCount: exportOutputCount(),
    paused: state.paused,
    plannedTotal: plannedExportTotal(),
    processed: state.processed,
    scanStatus: state.scanStatus,
    selectedIndex,
    statusText: state.statusText,
  });
}

function previewFooterLabel() {
  return previewStateHelpers.previewFooterLabel({
    previewStatus: state.previewStatus,
    selectedImageSource: selectedImage()?.source,
  });
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
    if (ensureGallerySelectionForFilter()) {
      return;
    }
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
    state.statusText = "Ajustes";
    render();
  } else if (action === "close-inspector-subview") {
    state.inspectorTab = "review";
    state.statusText = getVisibleAppState().nextStep || state.statusText;
    render();
  } else if (action === "edit-output") {
    beginOutputEdit();
  } else if (action === "select-output-profile") {
    const profileId = target?.dataset?.outputProfileId;
    if (profileId) {
      applyOutputProfile(profileId);
    }
  } else if (action === "apply-output-edit") {
    applyOutputEdit();
  } else if (action === "cancel-output-edit") {
    cancelOutputEdit();
  } else if (action === "save-output-current-profile") {
    saveCurrentOutputProfile();
  } else if (action === "save-output-as-new") {
    saveCurrentOutputAsNewProfile();
  } else if (action === "discard-output-overrides") {
    discardOutputOverrides();
  } else if (action === "open-app-settings") {
    openAppSettings();
  } else if (action === "close-app-settings") {
    closeAppSettings();
  } else if (action === "open-batch-detail") {
    openBatchDetail();
  } else if (action === "close-batch-detail") {
    closeBatchDetail();
  } else if (action === "cancel-export-confirm") {
    closeExportConfirm();
  } else if (action === "confirm-export") {
    confirmExportFromModal();
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
  } else if (action === "review-errors" || action === "review-warnings") {
    reviewWarnings();
  } else if (action === "review-output") {
    beginOutputEdit();
  } else if (action === "open-output") {
    openOutputFolder();
  } else if (action === "primary") {
    primaryAction();
  } else if (action === "secondary-primary") {
    runVisibleAction(getVisibleAppState().secondaryAction?.action);
  }
}

function closeTransientDetails(event) {
  const target = event.target;
  document.querySelectorAll("details.format-more-menu[open], details.debug-panel[open]").forEach((details) => {
    if (!details.contains(target)) {
      details.open = false;
    }
  });
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
  closeTransientDetails(event);

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

  if (event.target.id === "export-confirm-modal") {
    closeExportConfirm();
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
    applyGalleryFilter(filterTarget.dataset.filter);
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
  if (event.target?.dataset?.settingNumber) {
    updateSettingFromNumberInput(event.target);
  }
  if (event.target?.dataset?.localSettingNumber) {
    updateLocalOverrideFromNumberInput(event.target);
  }
  if (event.target.closest?.("#output-profile-form")) {
    updateOutputProfileDraftFromForm();
    renderOutputProfileModalState();
  }
});

document.addEventListener("change", (event) => {
  if (event.target?.dataset?.settingNumber) {
    updateSettingFromNumberInput(event.target, { commit: true });
    return;
  }
  if (event.target?.dataset?.localSettingNumber) {
    updateLocalOverrideFromNumberInput(event.target, { commit: true });
    return;
  }
  if (event.target.matches?.("[data-output-profile-enabled-id]")) {
    setOutputProfileEnabled(event.target.dataset.outputProfileEnabledId, event.target.checked);
    return;
  }
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
  if (ensureGallerySelectionForFilter()) {
    return;
  }
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

function numericInputValue(input, fallback = 0) {
  const raw = String(input.value ?? "").trim();
  if (!raw || raw === "-" || raw === "+") {
    return { valid: false, value: fallback };
  }
  const parsed = Number(raw);
  if (!Number.isFinite(parsed)) {
    return { valid: false, value: fallback };
  }
  const min = input.min === "" ? -Infinity : Number(input.min);
  const max = input.max === "" ? Infinity : Number(input.max);
  const rounded = Math.round(parsed);
  return {
    valid: true,
    value: Math.max(min, Math.min(max, rounded)),
  };
}

function updateSettingFromNumberInput(input, options = {}) {
  const key = input?.dataset?.settingNumber;
  if (!key || !(key in state.settings)) {
    return;
  }
  const parsed = numericInputValue(input, state.settings[key]);
  if (!parsed.valid) {
    return;
  }
  if (options.commit) {
    input.value = parsed.value;
  }
  if (state.settings[key] === parsed.value) {
    return;
  }
  state.settings[key] = parsed.value;
  const range = $(`[data-setting="${key}"]`);
  if (range && range.type === "range") {
    range.value = parsed.value;
  }
  markPresetDirty();
}

function updateLocalOverrideFromNumberInput(input, options = {}) {
  const key = input?.dataset?.localSettingNumber;
  if (!key || !localOverrideKeys.includes(key)) {
    return;
  }
  const parsed = numericInputValue(input, currentImageOverride()[key] || 0);
  if (!parsed.valid) {
    return;
  }
  const value = clampLocalOverrideValue(key, parsed.value);
  if (options.commit) {
    input.value = value;
  }
  const range = $(`[data-local-setting="${key}"]`);
  if (range) {
    range.value = value;
  }
  setCurrentImageOverrideValue(key, value);
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

  if (event.key === "Tab" && trapOpenModalFocus(event)) {
    return;
  }

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
    if (state.exportConfirmOpen) {
      closeExportConfirm();
      event.preventDefault();
      return;
    }
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

  if (event.key === "Enter" && state.exportConfirmOpen && !isTyping) {
    event.preventDefault();
    confirmExportFromModal();
    return;
  }

  if (isTyping) {
    return;
  }

  const key = event.key.toLowerCase();
  if (event.key === "ArrowLeft") {
    event.preventDefault();
    selectAdjacentImage(-1, { focus: true });
  } else if (event.key === "ArrowRight") {
    event.preventDefault();
    selectAdjacentImage(1, { focus: true });
  } else if (event.key === "Home") {
    event.preventDefault();
    selectEdgeImage("first", { focus: true });
  } else if (event.key === "End") {
    event.preventDefault();
    selectEdgeImage("last", { focus: true });
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
    || isAutoViewerMode()
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
  clampViewerPan();
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
const restoredSessionSnapshot = restoreSessionSnapshot();
sessionSnapshotPersistenceEnabled = true;
if (restoredSessionSnapshot) {
  render();
} else {
  setScenario("initial");
  restorePersistentBridgeSession();
}
window.addEventListener("flatshot:before-live-reload", writeSessionSnapshot);
window.addEventListener("beforeunload", writeSessionSnapshot);
