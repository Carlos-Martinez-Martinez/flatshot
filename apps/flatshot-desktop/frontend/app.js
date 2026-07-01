const initialImageAdjustmentPreset = storageHelpers.readValue(window.localStorage, STORAGE_KEYS.imageAdjustmentPreset) || "Luz cenital";
const initialOutputProfileId = storageHelpers.readValue(window.localStorage, STORAGE_KEYS.activeOutputProfile);
const initialExportPreferences = storageHelpers.readJson(window.localStorage, STORAGE_KEYS.exportPreferences, {});
const initialBackgroundPresets = readBackgroundPresets();
const initialOutputProfiles = readOutputProfiles(initialOutputProfileId);
const initialEnabledOutputProfiles = initialOutputProfiles.filter((profile) => profile.enabled);
const initialOutputProfile = initialEnabledOutputProfiles.find((profile) => profile.id === initialOutputProfileId)
  || initialEnabledOutputProfiles[0]
  || initialOutputProfiles.find((profile) => profile.id === initialOutputProfileId)
  || initialOutputProfiles[0]
  || defaultOutputProfiles[0];
const initialDestinationMode = initialExportPreferences.destinationMode === "custom"
  ? "custom"
  : initialOutputProfile.destinationMode;
const initialDestinationValue = String(
  initialExportPreferences.destinationValue
  || storageHelpers.readValue(window.localStorage, STORAGE_KEYS.lastOutputFolder)
  || initialOutputProfile.destinationValue
  || (initialDestinationMode === "custom" ? "" : "Salida")
);
const initialFormat = outputProfileHelpers.normalizeExportFormat(initialExportPreferences.format || initialOutputProfile.format);
const initialSize = outputProfileHelpers.parseOutputSize(initialExportPreferences.size || outputProfileHelpers.outputProfileSize(initialOutputProfile)).normalized;
const initialBackground = outputProfileHelpers.normalizeBackgroundValue(initialExportPreferences.background, initialOutputProfile.background);
const initialNaming = String(initialExportPreferences.naming || initialOutputProfile.naming || "{original}{suffix}");
const initialSuffix = initialExportPreferences.suffix === undefined || initialExportPreferences.suffix === null
  ? initialOutputProfile.suffix
  : String(initialExportPreferences.suffix);

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
  previewBg: initialBackground,
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
  activePreset: initialImageAdjustmentPreset,
  presetOutputSettings: {},
  settings: { ...defaultSettings },
  lightingPresetId: "",
  presetDirty: false,
  presetSource: "Global",
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
  backgroundPresets: initialBackgroundPresets,
  backgroundPresetEditor: null,
  outputProfileNotice: "",
  outputDeleteConfirmId: "",
  activeOutputProfileId: initialEnabledOutputProfiles.length ? initialOutputProfile.id : "",
  outputProfileEditorId: initialOutputProfiles.length ? initialOutputProfile.id : "",
  outputProfileDraft: null,
  destinationMode: initialDestinationMode,
  destinationValue: initialDestinationValue,
  format: initialFormat,
  size: initialSize,
  background: initialBackground,
  naming: initialNaming,
  suffix: initialSuffix,
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
  bridgeScanPath: storageHelpers.readValue(window.localStorage, STORAGE_KEYS.bridgeScanPath),
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
let bridgeUiPreferencesSaveTimer = 0;
let bridgeUiPreferencesRestored = false;
let pendingAdvancedDisclosure = "";
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

function readSessionSnapshot() {
  const snapshot = storageHelpers.readJson(window.sessionStorage, STORAGE_KEYS.sessionSnapshot, null);
  return snapshot?.version === 1 && snapshot.state && typeof snapshot.state === "object"
    ? snapshot
    : null;
}

function writeSessionSnapshot() {
  storageHelpers.writeJson(window.sessionStorage, STORAGE_KEYS.sessionSnapshot, buildSessionSnapshot());
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
      selectedImagePath: selected?.path || storageHelpers.readValue(window.localStorage, STORAGE_KEYS.selectedImagePath),
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
      backgroundPresets: state.backgroundPresets,
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
  const restoredBackgroundPresets = normalizeBackgroundPresetList(restored.backgroundPresets || state.backgroundPresets);
  const outputProfiles = Array.isArray(restored.outputProfiles)
    ? outputProfileHelpers.normalizeOutputProfileList(restored.outputProfiles, restored.activeOutputProfileId)
    : state.outputProfiles;
  const restoredActiveOutputProfile = outputProfiles.find((profile) => profile.id === restored.activeOutputProfileId && profile.enabled)
    || outputProfiles.find((profile) => profile.enabled)
    || null;
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
    previewBg: normalizePreviewBackgroundValue(restored.previewBg || state.previewBg),
    zoom: numberHelpers.clampNumber(restored.zoom, 25, 400, 100),
    fitZoom: numberHelpers.clampNumber(restored.fitZoom, 25, 400, 100),
    fitMode: VIEW_MODE_LABELS[restored.fitMode] ? restored.fitMode : DEFAULT_VIEW_MODE,
    panX: numberHelpers.clampNumber(restored.panX, -10000, 10000, 0),
    panY: numberHelpers.clampNumber(restored.panY, -10000, 10000, 0),
    filter: Object.values(BATCH_FILTERS).includes(restored.filter) ? restored.filter : BATCH_FILTERS.all,
    search: String(restored.search || ""),
    galleryView: restored.galleryView === "list" ? "list" : "thumbs",
    inspectorTab: ["review", "output", "warnings", "advanced"].includes(restored.inspectorTab) ? restored.inspectorTab : "review",
    inspectorCollapsed: Boolean(restored.inspectorCollapsed),
    activePreset: String(restored.activePreset || state.activePreset),
    presetOutputSettings: safeObject(restored.presetOutputSettings),
    settings: normalizeSettings(restored.settings),
    presetDirty: Boolean(restored.presetDirty),
    presetSource: String(restored.presetSource || "Global"),
    localOverride: Boolean(restored.localOverride),
    outputProfiles,
    backgroundPresets: restoredBackgroundPresets,
    backgroundPresetEditor: null,
    activeOutputProfileId: restoredActiveOutputProfile?.id || "",
    outputProfileEditorId: outputProfiles.some((profile) => profile.id === restored.outputProfileEditorId)
      ? restored.outputProfileEditorId
      : restoredActiveOutputProfile?.id || outputProfiles[0]?.id || "",
    outputProfileDraft: restored.outputProfileDraft && typeof restored.outputProfileDraft === "object"
      ? restored.outputProfileDraft
      : null,
    destinationMode: restored.destinationMode === "custom" ? "custom" : "source",
    destinationValue: String(restored.destinationValue || "Salida"),
    format: outputProfileHelpers.normalizeExportFormat(restored.format),
    size: outputProfileHelpers.parseOutputSize(restored.size).normalized,
    background: outputProfileHelpers.normalizeBackgroundValue(restored.background),
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
    bridgeUrl: bridgeUrlHelpers.resolveRuntimeBridgeUrl({
      currentBridgeUrl: initialBridgeUrl,
      restoredBridgeUrl: restored.bridgeUrl,
      defaultBridgeUrl,
    }),
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
    state.localOverride = hasImageAdjustmentOverride(nextImage);
    state.exportStatus = isExportReady() ? "ready" : "blocked";
    if (nextImage?.path) {
      storageHelpers.writeValue(window.localStorage, STORAGE_KEYS.selectedImagePath, nextImage.path);
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

function readOutputProfiles(activeProfileId = "") {
  const saved = storageHelpers.readJson(window.localStorage, STORAGE_KEYS.outputProfiles, null);
  const profiles = Array.isArray(saved) ? saved : defaultOutputProfiles;
  const activeFormatIds = storageHelpers.readJson(window.localStorage, STORAGE_KEYS.activeOutputFormats, null);
  const normalized = outputProfileHelpers.normalizeOutputProfileList(profiles, activeProfileId).map((profile) => (
    Array.isArray(activeFormatIds)
      ? { ...profile, enabled: activeFormatIds.includes(profile.id) }
      : profile
  ));
  return normalized.length ? normalized : outputProfileHelpers.normalizeOutputProfileList(defaultOutputProfiles, activeProfileId);
}

function backgroundSelectMode(value) {
  return outputProfileHelpers.parseRgbBackground(value) ? "custom" : outputProfileHelpers.normalizeBackgroundValue(value);
}

function normalizePreviewBackgroundValue(value) {
  if (value === SOFT_BLACK_PREVIEW_BG) {
    return SOFT_BLACK_PREVIEW_BG;
  }
  if (value === "white" || value === "transparent" || value === "rgb230") {
    return value;
  }
  const custom = outputProfileHelpers.parseRgbBackground(value);
  return custom ? `rgb:${custom.join(",")}` : "rgb230";
}

function backgroundCssColor(value) {
  const custom = outputProfileHelpers.parseRgbBackground(value);
  if (custom) {
    return `rgb(${custom.join(", ")})`;
  }
  if (value === SOFT_BLACK_PREVIEW_BG) {
    return "rgb(32, 34, 37)";
  }
  if (value === "white") {
    return "rgb(255, 255, 255)";
  }
  if (value === "transparent") {
    return "";
  }
  return "rgb(230, 230, 230)";
}

function backgroundVisualMode(value) {
  if (value === SOFT_BLACK_PREVIEW_BG) {
    return "custom";
  }
  if (value === "white" || value === "transparent") {
    return value;
  }
  return outputProfileHelpers.parseRgbBackground(value) ? "custom" : "rgb230";
}

function previewCustomRgbChannels(value) {
  const custom = outputProfileHelpers.parseRgbBackground(value);
  if (custom) {
    return custom;
  }
  if (value === SOFT_BLACK_PREVIEW_BG) {
    return [32, 34, 37];
  }
  return outputProfileHelpers.backgroundColorTuple(value || "rgb230");
}

function previewCustomBackgroundValue() {
  const fallback = previewCustomRgbChannels(state.previewBg);
  const channels = ["r", "g", "b"].map((channel, index) => {
    const input = $(`[data-preview-bg-channel="${channel}"]`);
    return Math.round(numberHelpers.clampNumber(input?.value, 0, 255, fallback[index]));
  });
  return `rgb:${channels.join(",")}`;
}

function previewBackgroundLabel(value) {
  const custom = outputProfileHelpers.parseRgbBackground(value);
  if (custom) {
    return `RGB ${custom.join(", ")}`;
  }
  if (value === SOFT_BLACK_PREVIEW_BG) {
    return "negro suave";
  }
  return settingsViewHelpers.backgroundLabel(value);
}

function normalizeBackgroundPreset(preset, index = 0) {
  const source = preset && typeof preset === "object" ? preset : {};
  const kind = source.kind === "transparent" || source.value === "transparent" ? "transparent" : "rgb";
  const parsed = Array.isArray(source.rgb)
    ? source.rgb
    : outputProfileHelpers.parseRgbBackground(source.value || source.background);
  const fallbackRgb = defaultBackgroundPresets[index % defaultBackgroundPresets.length]?.rgb || [230, 230, 230];
  const rgb = kind === "transparent"
    ? fallbackRgb
    : (parsed || fallbackRgb).map((channel) => Math.max(0, Math.min(255, Number.parseInt(channel, 10) || 0)));
  const id = String(source.id || outputProfileHelpers.uniqueOutputProfileId(source.name || "fondo", index)).trim();
  return {
    id,
    kind,
    name: String(source.name || (kind === "transparent" ? "Transparente" : `RGB ${rgb.join(", ")}`)).trim(),
    rgb,
  };
}

function normalizeBackgroundPresetList(presets) {
  const source = Array.isArray(presets) && presets.length ? presets : defaultBackgroundPresets;
  const seen = new Set();
  const normalized = source.map(normalizeBackgroundPreset).filter((preset) => preset.id && preset.name);
  return normalized.map((preset, index) => {
    let id = preset.id;
    while (seen.has(id)) {
      id = `${preset.id}-${index + seen.size}`;
    }
    seen.add(id);
    return { ...preset, id };
  });
}

function readBackgroundPresets() {
  return normalizeBackgroundPresetList(storageHelpers.readJson(window.localStorage, STORAGE_KEYS.backgroundPresets, null));
}

function persistBackgroundPresets() {
  storageHelpers.writeJson(window.localStorage, STORAGE_KEYS.backgroundPresets, state.backgroundPresets);
  scheduleBridgeUiPreferencesSave();
}

function backgroundPresetValue(preset) {
  if (!preset || preset.kind === "transparent") {
    return "transparent";
  }
  const rgb = preset.rgb || [230, 230, 230];
  if (preset.id === "rgb230" && rgb[0] === 230 && rgb[1] === 230 && rgb[2] === 230) {
    return "rgb230";
  }
  if (preset.id === "white" && rgb[0] === 255 && rgb[1] === 255 && rgb[2] === 255) {
    return "white";
  }
  return outputProfileHelpers.rgbBackgroundValue(rgb[0], rgb[1], rgb[2]) || "rgb230";
}

function backgroundPresetLabel(preset) {
  if (!preset) {
    return "Fondo";
  }
  return preset.name;
}

function backgroundPresetById(presetId) {
  return state.backgroundPresets.find((preset) => preset.id === presetId) || null;
}

function backgroundPresetByValue(value) {
  const normalized = outputProfileHelpers.normalizeBackgroundValue(value);
  return state.backgroundPresets.find((preset) => outputProfileHelpers.normalizeBackgroundValue(backgroundPresetValue(preset)) === normalized) || null;
}

function backgroundSelectOptionsHtml(selectedValue) {
  const selected = outputProfileHelpers.normalizeBackgroundValue(selectedValue);
  const presetOptions = state.backgroundPresets.map((preset) => {
    const value = backgroundPresetValue(preset);
    return `<option value="${escapeHtml(value)}">${escapeHtml(backgroundPresetLabel(preset))}</option>`;
  }).join("");
  if (state.backgroundPresets.some((preset) => outputProfileHelpers.normalizeBackgroundValue(backgroundPresetValue(preset)) === selected)) {
    return presetOptions;
  }
  return `${presetOptions}<option value="${escapeHtml(selected)}">${escapeHtml(`Actual · ${settingsViewHelpers.backgroundLabel(selected)}`)}</option>`;
}

function activeOutputProfile() {
  return state.outputProfiles.find((profile) => profile.id === state.activeOutputProfileId)
    || state.outputProfiles[0]
    || defaultOutputProfiles[0];
}

function galleryOutputProfiles() {
  return state.outputProfiles.length ? state.outputProfiles : [currentOutputProfileData()];
}

function galleryActiveOutputContext() {
  const savedProfile = activeOutputProfile();
  const matchesSavedProfile = outputMatchesProfile(savedProfile);
  const profile = matchesSavedProfile ? savedProfile : currentOutputProfileData();
  return {
    background: profile?.background || state.background || "rgb230",
    id: matchesSavedProfile ? profile.id : "__custom",
    label: outputProfileCompactLabel(profile),
    name: matchesSavedProfile ? profile.name : "Formato personalizado",
    profile,
    summary: outputProfileSummaryLine(profile),
  };
}

function enabledOutputProfiles() {
  return state.outputProfiles.filter((profile) => profile.enabled);
}

function enabledActiveOutputProfile() {
  return state.outputProfiles.find((profile) => profile.id === state.activeOutputProfileId && profile.enabled) || null;
}

function isActiveOutputProfile(profile) {
  return Boolean(profile && profile.enabled && profile.id === state.activeOutputProfileId);
}

function syncOutputProfileState(profile) {
  if (!profile) {
    return;
  }
  state.format = profile.format;
  state.size = outputProfileHelpers.outputProfileSize(profile);
  state.background = profile.background;
  state.previewBg = profile.background;
  state.destinationMode = profile.destinationMode;
  state.destinationValue = profile.destinationValue;
  state.naming = profile.naming;
  state.suffix = profile.suffix;
  state.exportStatus = isExportReady() ? "ready" : "blocked";
}

function setActiveOutputProfileReference(profileId, options = {}) {
  const profile = state.outputProfiles.find((item) => item.id === profileId);
  if (!profile || !profile.enabled) {
    return false;
  }
  state.activeOutputProfileId = profile.id;
  syncOutputProfileState(profile);
  state.statusText = options.statusText || `Formato activo: ${profile.name}`;
  persistOutputProfiles();
  if (options.render !== false) {
    render();
  }
  return true;
}

function reassignActiveOutputProfileReference(options = {}) {
  const next = enabledOutputProfiles()[0] || null;
  if (!next) {
    state.activeOutputProfileId = "";
    state.exportStatus = isExportReady() ? "ready" : "blocked";
    state.statusText = options.statusText || "Sin formatos activos";
    persistOutputProfiles();
    if (options.render !== false) {
      render();
    }
    return null;
  }
  setActiveOutputProfileReference(next.id, {
    render: options.render,
    statusText: options.statusText || `Formato activo: ${next.name}`,
  });
  return next;
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
    if (!profile.enabled) {
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
  return profiles;
}

function exportOutputCount() {
  return exportOutputProfiles().length;
}

function currentOutputProfileData() {
  const size = outputProfileHelpers.parseOutputSize(state.size);
  return outputProfileHelpers.normalizeOutputProfile({
    id: state.activeOutputProfileId || outputProfileHelpers.uniqueOutputProfileId("actual"),
    name: activeOutputProfile()?.name || "Formato actual",
    enabled: Boolean(activeOutputProfile()?.enabled),
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
  storageHelpers.writeJson(window.localStorage, STORAGE_KEYS.outputProfiles, state.outputProfiles);
  storageHelpers.writeValue(window.localStorage, STORAGE_KEYS.activeOutputProfile, state.activeOutputProfileId);
  storageHelpers.writeJson(window.localStorage, STORAGE_KEYS.activeOutputFormats, enabledOutputProfiles().map((profile) => profile.id));
  persistExportPreferences({ saveBridge: false });
  scheduleBridgeUiPreferencesSave(0);
}

function persistImageAdjustmentSelection() {
  storageHelpers.writeValue(window.localStorage, STORAGE_KEYS.imageAdjustmentPreset, state.activePreset);
  scheduleBridgeUiPreferencesSave();
}

function persistExportPreferences(options = {}) {
  const preferences = {
    activeOutputProfileId: state.activeOutputProfileId,
    activeOutputFormatIds: enabledOutputProfiles().map((profile) => profile.id),
    destinationMode: state.destinationMode,
    destinationValue: state.destinationValue,
    format: state.format,
    size: state.size,
    background: state.background,
    naming: state.naming,
    suffix: state.suffix,
  };
  storageHelpers.writeJson(window.localStorage, STORAGE_KEYS.exportPreferences, preferences);
  if (String(state.destinationValue || "").trim()) {
    storageHelpers.writeValue(window.localStorage, STORAGE_KEYS.lastOutputFolder, state.destinationValue);
  }
  if (options.saveBridge !== false) {
    scheduleBridgeUiPreferencesSave();
  }
}

function uiPreferencesPayload() {
  return {
    outputProfiles: state.outputProfiles,
    backgroundPresets: state.backgroundPresets,
    activeOutputProfile: state.activeOutputProfileId,
    activeOutputFormats: enabledOutputProfiles().map((profile) => profile.id),
    imageAdjustmentPreset: state.activePreset,
    bridgeScanPath: state.bridgeScanPath,
    lastOutputFolder: storageHelpers.readValue(window.localStorage, STORAGE_KEYS.lastOutputFolder),
    exportPreferences: {
      activeOutputProfileId: state.activeOutputProfileId,
      activeOutputFormatIds: enabledOutputProfiles().map((profile) => profile.id),
      destinationMode: state.destinationMode,
      destinationValue: state.destinationValue,
      format: state.format,
      size: state.size,
      background: state.background,
      naming: state.naming,
      suffix: state.suffix,
    },
  };
}

function cacheUiPreferences(preferences = uiPreferencesPayload()) {
  const source = safeObject(preferences);
  if (Array.isArray(source.outputProfiles)) {
    storageHelpers.writeJson(window.localStorage, STORAGE_KEYS.outputProfiles, source.outputProfiles);
  }
  if (Array.isArray(source.backgroundPresets)) {
    storageHelpers.writeJson(window.localStorage, STORAGE_KEYS.backgroundPresets, source.backgroundPresets);
  }
  if (source.activeOutputProfile !== undefined) {
    storageHelpers.writeValue(window.localStorage, STORAGE_KEYS.activeOutputProfile, source.activeOutputProfile);
  }
  if (Array.isArray(source.activeOutputFormats)) {
    storageHelpers.writeJson(window.localStorage, STORAGE_KEYS.activeOutputFormats, source.activeOutputFormats);
  }
  if (source.imageAdjustmentPreset !== undefined) {
    storageHelpers.writeValue(window.localStorage, STORAGE_KEYS.imageAdjustmentPreset, source.imageAdjustmentPreset);
  }
  if (source.bridgeScanPath !== undefined) {
    storageHelpers.writeValue(window.localStorage, STORAGE_KEYS.bridgeScanPath, source.bridgeScanPath);
  }
  if (source.lastOutputFolder !== undefined) {
    storageHelpers.writeValue(window.localStorage, STORAGE_KEYS.lastOutputFolder, source.lastOutputFolder);
  }
  if (source.exportPreferences && typeof source.exportPreferences === "object") {
    storageHelpers.writeJson(window.localStorage, STORAGE_KEYS.exportPreferences, source.exportPreferences);
  }
}

function applyBridgeUiPreferences(preferences) {
  const source = safeObject(preferences);
  if (!Object.keys(source).length) {
    return false;
  }

  const exportPreferences = safeObject(source.exportPreferences);
  const activeFormatIds = Array.isArray(source.activeOutputFormats)
    ? source.activeOutputFormats.map(String)
    : Array.isArray(exportPreferences.activeOutputFormatIds)
      ? exportPreferences.activeOutputFormatIds.map(String)
      : null;
  const activeProfileId = String(source.activeOutputProfile || exportPreferences.activeOutputProfileId || "");

  if (Array.isArray(source.outputProfiles)) {
    const normalized = outputProfileHelpers.normalizeOutputProfileList(source.outputProfiles, activeProfileId).map((profile) => (
      activeFormatIds ? { ...profile, enabled: activeFormatIds.includes(profile.id) } : profile
    ));
    if (normalized.length) {
      state.outputProfiles = normalized;
    }
  }

  if (Array.isArray(source.backgroundPresets)) {
    state.backgroundPresets = normalizeBackgroundPresetList(source.backgroundPresets);
  }

  const enabledProfiles = enabledOutputProfiles();
  const activeProfile = state.outputProfiles.find((profile) => profile.id === activeProfileId && profile.enabled)
    || enabledProfiles[0]
    || state.outputProfiles.find((profile) => profile.id === activeProfileId)
    || state.outputProfiles[0]
    || defaultOutputProfiles[0];
  state.activeOutputProfileId = activeProfile?.enabled ? activeProfile.id : enabledProfiles[0]?.id || "";
  state.outputProfileEditorId = state.outputProfiles.some((profile) => profile.id === state.outputProfileEditorId)
    ? state.outputProfileEditorId
    : activeProfile?.id || state.outputProfiles[0]?.id || "";

  const profileForDefaults = activeProfile || defaultOutputProfiles[0];
  state.destinationMode = exportPreferences.destinationMode === "custom"
    ? "custom"
    : profileForDefaults.destinationMode;
  state.destinationValue = String(
    exportPreferences.destinationValue
    || source.lastOutputFolder
    || profileForDefaults.destinationValue
    || (state.destinationMode === "custom" ? "" : "Salida")
  );
  state.format = outputProfileHelpers.normalizeExportFormat(exportPreferences.format || profileForDefaults.format);
  state.size = outputProfileHelpers.parseOutputSize(exportPreferences.size || outputProfileHelpers.outputProfileSize(profileForDefaults)).normalized;
  state.background = outputProfileHelpers.normalizeBackgroundValue(exportPreferences.background, profileForDefaults.background);
  state.previewBg = state.background;
  state.naming = String(exportPreferences.naming || profileForDefaults.naming || "{original}{suffix}");
  state.suffix = exportPreferences.suffix === undefined || exportPreferences.suffix === null
    ? profileForDefaults.suffix
    : String(exportPreferences.suffix);

  if (source.imageAdjustmentPreset !== undefined) {
    state.activePreset = String(source.imageAdjustmentPreset || state.activePreset);
  }
  if (source.bridgeScanPath !== undefined) {
    state.bridgeScanPath = String(source.bridgeScanPath || "");
  }

  state.exportStatus = isExportReady() ? "ready" : "blocked";
  cacheUiPreferences(source);
  return true;
}

function scheduleBridgeUiPreferencesSave(delayMs = 250) {
  if (state.bridgeMode !== "bridge" || state.bridgeStatus === "disconnected") {
    return;
  }
  window.clearTimeout(bridgeUiPreferencesSaveTimer);
  bridgeUiPreferencesSaveTimer = window.setTimeout(() => {
    bridgeUiPreferencesSaveTimer = 0;
    void saveBridgeUiPreferences();
  }, delayMs);
}

async function saveBridgeUiPreferences() {
  if (state.bridgeMode !== "bridge" || state.bridgeStatus === "disconnected") {
    return false;
  }
  try {
    await bridgeRequest("/ui/preferences", {
      method: "POST",
      body: JSON.stringify(uiPreferencesPayload()),
      timeoutMs: 5000,
      retries: 1,
    });
    return true;
  } catch (error) {
    return false;
  }
}

async function restoreBridgeUiPreferences(options = {}) {
  if (options.skipSessionSnapshot && restoredSessionSnapshot) {
    return false;
  }
  try {
    const payload = await bridgeRequest("/ui/preferences", { timeoutMs: 5000, retries: 1 });
    const restored = applyBridgeUiPreferences(payload.preferences);
    bridgeUiPreferencesRestored = restored || bridgeUiPreferencesRestored;
    if (restored) {
      state.statusText = state.statusText === "Sin lote" ? "Ajustes restaurados" : state.statusText;
      render();
    }
    return restored;
  } catch (error) {
    return false;
  }
}

function applyOutputProfile(profileId, options = {}) {
  const profile = state.outputProfiles.find((item) => item.id === profileId);
  if (!profile) {
    return false;
  }
  profile.enabled = true;
  if (state.outputProfileDraft?.id === profile.id) {
    state.outputProfileDraft = { ...state.outputProfileDraft, enabled: true };
  }
  return setActiveOutputProfileReference(profile.id, options);
}

function setOutputProfileEnabled(profileId, enabled) {
  const profile = state.outputProfiles.find((item) => item.id === profileId);
  if (!profile) {
    return;
  }
  const wasActiveReference = profile.id === state.activeOutputProfileId;
  profile.enabled = Boolean(enabled);
  if (state.outputProfileDraft?.id === profile.id) {
    state.outputProfileDraft = { ...state.outputProfileDraft, enabled: profile.enabled };
  }

  if (profile.enabled && !enabledActiveOutputProfile()) {
    setActiveOutputProfileReference(profile.id, { render: false, statusText: `Formato activo: ${profile.name}` });
  } else if (!profile.enabled && wasActiveReference) {
    reassignActiveOutputProfileReference({ render: false, statusText: `Formato desactivado: ${profile.name}` });
  }

  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = profile.enabled ? `Formato activo: ${profile.name}` : `Formato desactivado: ${profile.name}`;
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
    category: devMode ? "Demo" : "Ajuste",
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
  if (!String(state.activePreset || "").trim()) {
    issues.push({ level: "error", title: "Sin ajuste de imagen", detail: "Selecciona un ajuste de imagen." });
  }
  if (exportOutputProfiles().length === 0) {
    issues.push({ level: "error", title: "Sin formatos activos", detail: "Selecciona al menos un formato de salida." });
  }
  if (!state.naming.trim()) {
    issues.push({ level: "error", title: "Nombre de archivo vacío", detail: "Define una plantilla de nombre." });
  }
  if (state.destinationMode === "custom" && !state.destinationValue.trim()) {
    issues.push({ level: "error", title: "Carpeta de salida sin configurar", detail: "Elige una carpeta de salida." });
  }
  exportOutputProfiles()
    .forEach((profile) => {
      outputProfileValidation(outputProfileRawFromProfile(profile)).errors.forEach((message) => {
        issues.push({
          level: "error",
          title: "Formato incompleto",
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
      title: `${preflightHelpers.countText(exportableWarningImages, "imagen", "imágenes")} con aviso`,
      detail: "Se exportarán, pero conviene revisarlas si el lote es de producción.",
    });
  }

  if (counts.nonExportableImages > 0) {
    risks.push({
      id: "non-exportable-images",
      level: "warning",
      title: `${preflightHelpers.countText(counts.nonExportableImages, "imagen", "imágenes")} excluida${counts.nonExportableImages === 1 ? "" : "s"}`,
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
      title: `${preflightHelpers.countText(lowResolutionCount, "imagen", "imágenes")} por debajo del tamaño de salida`,
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

  if (state.exportStatus === "failed" && state.errors.some((issue) => issue.level === "error" && !preflightHelpers.issueMentionsExistingOutput(issue))) {
    risks.push({
      id: "previous-export-errors",
      level: "warning",
      title: "Errores en la última exportación",
      detail: "Puedes reintentar, pero revisa el resultado si vuelve a fallar.",
    });
  }

  state.errors
    .filter((issue) => issue.level !== "error" && !preflightHelpers.issueMentionsExistingOutput(issue))
    .slice(0, 2)
    .forEach((issue, index) => {
      risks.push({
        id: `state-warning-${index}-${issue.title}`,
        level: "warning",
        title: issue.title || "Aviso",
        detail: issue.detail || "Revisa este punto antes de exportar.",
      });
    });

  return preflightHelpers.dedupeExportRisks(risks);
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
  const targets = exportOutputProfiles().map((profile) => outputProfileHelpers.parseOutputSize(outputProfileHelpers.outputProfileSize(profile)));
  return exportableImages().filter((image) => {
    const dimensions = imageDimensions(image);
    return dimensions && targets.some((target) => dimensions.width < target.width || dimensions.height < target.height);
  }).length;
}

function isExportReady() {
  return preflightHelpers.isExportReady({
    activeOutputCount: exportOutputCount(),
    hasImageAdjustment: Boolean(String(state.activePreset || "").trim()),
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
      detail: batchViewHelpers.omissionReasonLabel(omitted.reason),
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
        ? `${preflightHelpers.countText(counts.filesFound, "archivo encontrado", "archivos encontrados")}${counts.ignoredFiles ? ` · ${ignoredNeutralText(counts.ignoredFiles)}` : ""}`
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
      subtitle: `${summary} · ${preflightHelpers.countText(counts.nonBlockingWarnings, "aviso", "avisos")}`,
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
  const readyText = preflightHelpers.readyImagesText(counts.filesFound > 0 || counts.exportableImages > 0 ? counts.exportableImages : 0);
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

function selectImage(imageId) {
  const image = activeImages().find((item) => item.id === imageId);
  if (!image) {
    return;
  }
  rememberSelectedImage(image);
  clearTimers();
  state.selectedImageId = image.id;
  state.localOverride = hasImageAdjustmentOverride(image);
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
    storageHelpers.writeValue(window.localStorage, STORAGE_KEYS.selectedImagePath, image.path);
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
  state.statusText = galleryHelpers.filterStatusText(state.filter);
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

function hasImageAdjustmentOverride(image) {
  return hasCurrentImageOverride(image) || image?.status === "adjusted";
}

function imageAdjustmentOverrideCount(images = activeImages()) {
  return images.filter(hasImageAdjustmentOverride).length;
}

function resetAllImageOverrides() {
  state.imageOverrides = {};
  state.realImages = state.realImages.map((image) =>
    image.status === "adjusted" ? { ...image, status: "ready" } : image
  );
  state.localOverride = false;
  state.statusText = "Ajuste del lote aplicado a todas las imágenes";
  refreshPreviewAfterSettingChange();
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
  state.statusText = state.localOverride ? "Ajuste personalizado" : "Ajuste de imagen restablecido";
  refreshPreviewAfterSettingChange();
}

function resetCurrentImageOverride() {
  const key = imageOverrideKey();
  if (!key) {
    return;
  }
  delete state.imageOverrides[key];
  state.localOverride = false;
  state.statusText = "Ajuste de imagen restablecido";
  refreshPreviewAfterSettingChange();
}

function settingsWithLocalOverride(settings = state.settings, override = currentImageOverride()) {
  const normalizedSettings = normalizeSettings(settings);
  const local = normalizeLocalOverride(override);
  const next = { ...normalizedSettings };
  if (Object.prototype.hasOwnProperty.call(local, "size_delta")) {
    next.scale_adjustment = Math.max(-30, Math.min(30, Number(next.scale_adjustment || 0) + local.size_delta));
  }
  if (Object.prototype.hasOwnProperty.call(local, "shadow_delta")) {
    next.opacity = Math.max(0, Math.min(100, Number(next.opacity || 0) + local.shadow_delta));
  }
  if (Object.prototype.hasOwnProperty.call(local, "blur_delta")) {
    next.blur = Math.max(0, Math.min(100, Number(next.blur || 0) + local.blur_delta));
  }
  return normalizeSettings(next);
}

function applyLocalAdjustmentOnly() {
  const image = selectedImage();
  if (!image) {
    return;
  }
  state.presetEditorOpen = false;
  state.localOverride = hasImageAdjustmentOverride(image);
  state.statusText = state.localOverride ? "Ajuste aplicado sólo a esta imagen" : "La imagen usa el ajuste del lote";
  render();
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
  if (!canvas || !target || state.fitMode === "fit") {
    return { minX: 0, maxX: 0, minY: 0, maxY: 0 };
  }
  const canvasRect = canvas.getBoundingClientRect();
  const targetRect = target.getBoundingClientRect();
  if (!canvasRect.width || !canvasRect.height || !targetRect.width || !targetRect.height) {
    return { minX: 0, maxX: 0, minY: 0, maxY: 0 };
  }
  const minVisibleX = Math.min(96, Math.max(32, Math.min(canvasRect.width, targetRect.width) * 0.25));
  const minVisibleY = Math.min(96, Math.max(32, Math.min(canvasRect.height, targetRect.height) * 0.25));
  const maxX = targetRect.width > canvasRect.width
    ? Math.max(0, Math.round((canvasRect.width + targetRect.width) / 2 - minVisibleX))
    : 0;
  const maxY = targetRect.height > canvasRect.height
    ? Math.max(0, Math.round((canvasRect.height + targetRect.height) / 2 - minVisibleY))
    : 0;
  return { minX: -maxX, maxX, minY: -maxY, maxY };
}

function clampViewerPan() {
  const bounds = viewerPanBounds();
  state.panX = Math.max(bounds.minX, Math.min(bounds.maxX, state.panX));
  state.panY = Math.max(bounds.minY, Math.min(bounds.maxY, state.panY));
}

function canViewerPan() {
  const bounds = viewerPanBounds();
  return bounds.minX !== 0 || bounds.maxX !== 0 || bounds.minY !== 0 || bounds.maxY !== 0;
}

function viewerModeLabel(mode = state.fitMode) {
  return previewStateHelpers.viewerModeLabel(mode, VIEW_MODE_LABELS);
}

function currentViewerZoom() {
  return previewStateHelpers.isAutoViewerMode() ? state.fitZoom : state.zoom;
}

function setViewerZoom(nextZoom, anchorEvent = null) {
  const zoom = previewStateHelpers.clampViewerZoom(nextZoom);
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
  if (!["height", "width"].includes(mode)) {
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
  setViewerMode(DEFAULT_VIEW_MODE);
}

function normalizeLightingScene(scene = {}) {
  const source = scene && typeof scene === "object" ? scene : {};
  const sourceMain = source.main && typeof source.main === "object" ? source.main : {};
  const defaultMain = defaultLightingScene.main;
  const type = ["softbox", "spot", "strip"].includes(sourceMain.type) ? sourceMain.type : defaultMain.type;
  return {
    main: {
      type,
      x: numberHelpers.roundedSceneValue(sourceMain.x, -1, 1, defaultMain.x),
      y: numberHelpers.roundedSceneValue(sourceMain.y, -1, 1, defaultMain.y),
      height: numberHelpers.roundedSceneValue(sourceMain.height, 0, 1, defaultMain.height),
      size: numberHelpers.roundedSceneValue(sourceMain.size, 0, 1, defaultMain.size),
      intensity: numberHelpers.roundedSceneValue(sourceMain.intensity, 0, 1.5, defaultMain.intensity),
    },
    ambient_intensity: numberHelpers.roundedSceneValue(source.ambient_intensity, 0, 1, defaultLightingScene.ambient_intensity),
  };
}

function cloneLightingScene(scene = defaultLightingScene) {
  return normalizeLightingScene(scene);
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
      normalized[key] = ["legacy", "realistic_v2", "studio_2_5d"].includes(source[key]) ? source[key] : "realistic_v2";
      return;
    }
    if (key === "lighting_scene") {
      normalized[key] = normalizeLightingScene(source[key]);
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
  normalized.lighting_scene = cloneLightingScene(normalized.lighting_scene);
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
  state.presetDirty = false;
  state.presetSource = preset.category || "Global";
  persistImageAdjustmentSelection();
  const advanced = $("#advanced-settings");
  if (advanced) {
    advanced.open = false;
  }
  state.statusText = options.statusText || `Ajuste: ${preset.name}`;
  state.exportStatus = isExportReady() ? "ready" : "blocked";
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
  state.presetSource = "Global";
  state.statusText = "Ajuste restaurado";
  refreshPreviewAfterSettingChange();
}

function cancelAdjustmentEdit() {
  const preset = activePresetItem();
  state.settings = normalizeSettings(preset?.settings || defaultSettings);
  state.presetDirty = false;
  state.presetSource = preset?.category || "Global";
  state.presetEditorOpen = false;
  state.statusText = "Cambios de ajuste descartados";
  refreshPreviewAfterSettingChange();
}

function applyGlobalAdjustmentWithoutSaving() {
  state.presetEditorOpen = false;
  state.presetDirty = true;
  state.presetSource = "Modificado";
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = "Ajuste aplicado al lote sin guardar";
  refreshPreviewAfterSettingChange();
}

function markPresetDirty(options = {}) {
  state.presetDirty = true;
  state.presetSource = "Modificado";
  if (options.deferRender) {
    return;
  }
  refreshPreviewAfterSettingChange();
}

function refreshPreviewAfterSettingChange() {
  if (selectedImage()?.source === "bridge") {
    Object.assign(state, previewStateHelpers.previewLoadingState());
    renderAdjustmentResponse();
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
    renderAdjustmentResponse();
    clearTimers();
    setTimer(() => {
      Object.assign(state, previewStateHelpers.previewImageStatusState(selectedImage()?.status, { errorAsReady: true }));
      renderAdjustmentResponse();
    }, 420);
  } else {
    renderAdjustmentResponse();
  }
}

function startExport(options = {}) {
  if (!options.skipOutputProfileUnsavedCheck && state.appSettingsOpen && outputProfileHasUnsavedChanges()) {
    showOutputProfileUnsavedNotice("Guarda o descarta los cambios antes de exportar.");
    return;
  }
  clearTimers();
  if (!isExportReady()) {
    state.exportStatus = "blocked";
    state.statusText = validationIssues()[0]?.title || "Configura exportación";
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
      state.exportDestinations = ["Mock / Salida"];
      state.exportIssues = [];
      state.exportResult = {
        success: true,
        processed: total,
        total,
        errors: 0,
        destinations: ["Mock / Salida"],
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
  return bridgeClientHelpers.normalizedBridgeUrl(state.bridgeUrl, defaultBridgeUrl);
}

function bridgeThumbnailUrl(path, size = 128) {
  return bridgeClientHelpers.thumbnailUrl(normalizedBridgeUrl(), path, size);
}

async function bridgeRequest(path, options = {}) {
  return bridgeClientHelpers.request(normalizedBridgeUrl(), path, options);
}

function bridgeErrorMessage(error) {
  return bridgeClientHelpers.errorMessage(error);
}

let _previewBlobUrl = null;

async function requestBridgePreview(image) {
  const requestId = state.previewRequestId + 1;
  state.previewRequestId = requestId;
  Object.assign(state, previewStateHelpers.previewLoadingState());
  render();

  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), 20000);

  try {
    const previewImage = await bridgeClientHelpers.requestPreviewImage(normalizedBridgeUrl(), {
      signal: controller.signal,
      imagePath: image.path,
      targetSize: previewTargetSize(),
      settings: bridgePreviewSettings(),
      localOverride: currentImageOverride(image),
    });
    window.clearTimeout(timer);

    if (isStalePreviewResponse(requestId, image)) {
      return;
    }

    if (_previewBlobUrl) {
      URL.revokeObjectURL(_previewBlobUrl);
    }
    _previewBlobUrl = URL.createObjectURL(previewImage.blob);

    const previewData = {
      src: _previewBlobUrl,
      width: previewImage.width,
      height: previewImage.height,
      sourceName: image.name,
      sourcePath: image.path,
      warning: previewImage.warning,
      renderTimeMs: 0,
    };

    Object.assign(state, previewStateHelpers.previewBridgeResultState(previewData, previewData.warning));
  } catch (error) {
    window.clearTimeout(timer);
    if (isStalePreviewResponse(requestId, image)) {
      return;
    }
    const message = error.name === "AbortError"
      ? "La vista tardó demasiado. Intenta de nuevo."
      : bridgeErrorMessage(error);
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
    bgColor: outputProfileHelpers.backgroundColorTuple(state.background),
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
    const uiPreferences = bridgeUiPreferencesRestored || restoredSessionSnapshot
      ? null
      : await bridgeRequest("/ui/preferences").catch(() => null);
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
    if (uiPreferences) {
      applyBridgeUiPreferences(uiPreferences.preferences);
      bridgeUiPreferencesRestored = true;
    }
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

async function pickOutputProfileDestination() {
  if (!state.appSettingsOpen) {
    return;
  }
  updateOutputProfileDraftFromForm();
  renderOutputProfileModalState();
  const raw = outputProfileFormRawData();
  const initialPath = raw.destinationMode === "custom" && raw.destinationValue
    ? raw.destinationValue
    : storageHelpers.readValue(window.localStorage, STORAGE_KEYS.lastOutputFolder);
  state.statusText = "Eligiendo carpeta de salida";
  try {
    const selected = await bridgeRequest("/folders/pick", {
      method: "POST",
      body: JSON.stringify({ initialPath: initialPath || "" }),
      timeoutMs: 300000,
    });
    if (!selected.selected || !selected.path) {
      state.statusText = "Selección de carpeta cancelada";
      renderOutputProfileModalState();
      return;
    }
    const modeInput = $("#profile-destination-mode-input");
    const destinationInput = $("#profile-destination-input");
    if (modeInput) {
      modeInput.value = "custom";
    }
    if (destinationInput) {
      destinationInput.value = selected.path;
    }
    storageHelpers.writeValue(window.localStorage, STORAGE_KEYS.lastOutputFolder, selected.path);
    updateOutputProfileDraftFromForm();
    state.statusText = "Carpeta de salida configurada";
    renderOutputProfileModalState();
  } catch (error) {
    state.statusText = bridgeErrorMessage(error);
    renderOutputProfileModalState();
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
  storageHelpers.writeValue(window.localStorage, STORAGE_KEYS.bridgeScanPath, path);
  scheduleBridgeUiPreferencesSave();
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
    const rememberedPath = storageHelpers.readValue(window.localStorage, STORAGE_KEYS.selectedImagePath);
    const rememberedImage = rememberedPath
      ? state.realImages.find((image) => image.path === rememberedPath)
      : null;
    const selectedImage = rememberedImage || state.realImages[0];
    Object.assign(state, scanStateHelpers.scanReadyState({
      defaultViewMode: DEFAULT_VIEW_MODE,
      imageCount: state.realImages.length,
      localOverride: hasImageAdjustmentOverride(selectedImage),
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
    name: formatterHelpers.basename(folder.path) || `Carpeta ${index + 1}`,
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
  const detail = `${suffix} · ${formatterHelpers.formatBytes(image.sizeBytes)}`;
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

function imageFileType(image) {
  return formatterHelpers.imageFileType(image, state.format || "Imagen");
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
    ? `${preflightHelpers.countText(issueCount, "aviso", "avisos")} para revisar`
    : "Sin avisos";
  render();
}

function reviewOutput() {
  state.inspectorTab = "output";
  state.statusText = firstBlockingIssue()?.title || "Revisa exportación";
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
  const opened = window.open(formatterHelpers.pathToFileUrl(destination), "_blank", "noopener");
  state.statusText = opened ? "Carpeta de salida abierta" : "No se pudo abrir la carpeta de salida";
  render();
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
  syncRangeFillStyles();
  syncOpenInspectorDisclosureHeights();
  keepActiveThumbnailVisible();
  if (sessionSnapshotPersistenceEnabled) {
    writeSessionSnapshot();
  }
}

function renderAdjustmentResponse() {
  renderPreview();
  renderSettings();
  renderBatch();
  renderExport();
  renderInspector();
  renderTop();
  syncRangeFillStyles();
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

function setInspectorDisclosureOpenState(details, open) {
  if (!details) {
    return;
  }
  const previousTimer = inspectorDisclosureTimers.get(details);
  if (previousTimer) {
    window.clearTimeout(previousTimer);
    inspectorDisclosureTimers.delete(details);
  }
  details.open = open;
  details.classList.remove("is-opening", "is-closing", "is-open");
  inspectorDisclosureBody(details)?.style.removeProperty("--inspector-disclosure-height");
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
  shell.classList.toggle("has-selected-image", derived.hasSelectedImage);
  shell.classList.toggle("no-selected-image", !derived.hasSelectedImage);
  shell.classList.toggle("can-export", derived.canExport);
  shell.classList.toggle("is-settings-open", state.appSettingsOpen);
  shell.classList.toggle("export-completed", ["completed", "partial", "failed"].includes(state.exportStatus));
  shell.classList.toggle("inspector-collapsed", state.inspectorCollapsed);
  shell.dataset.uiState = visible.id;
  shell.dataset.batchContext = derived.hasBatchContext ? "true" : "false";
  shell.dataset.statusFooter = hasStatusFooter ? "true" : "false";
  shell.dataset.outputEditing = state.outputEditMode ? "true" : "false";
  if (gallery) {
    gallery.dataset.galleryView = state.galleryView;
    const galleryBackground = galleryActiveOutputContext().background;
    gallery.dataset.outputBg = backgroundVisualMode(galleryBackground);
    const galleryBackgroundColor = backgroundCssColor(galleryBackground);
    if (galleryBackgroundColor) {
      gallery.style.setProperty("--custom-output-bg", galleryBackgroundColor);
    } else {
      gallery.style.removeProperty("--custom-output-bg");
    }
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
  setDebugText("debug-preview-url", state.previewData?.src ? formatterHelpers.debugUrlLabel(state.previewData.src) : "-");
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
  const topbarText = conciseTopbarStatusText();
  const topSummary = $(".top-summary");
  if (topSummary) {
    topSummary.hidden = !topbarText;
  }
  topStatus.textContent = topbarText;
  topStatus.title = topbarText ? visible.subtitle || topbarText : "";
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
    formatButton.title = "Formatos de salida";
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

function conciseTopbarStatusText() {
  if (["running", "completed", "partial", "failed"].includes(state.exportStatus)) {
    return compactHeaderStatusText();
  }
  if (state.batch === "scanning") {
    return "Escaneando";
  }
  if (state.bridgeMode === "bridge" && state.bridgeStatus === "disconnected") {
    return "Bridge no disponible";
  }
  return "";
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
    readyLabel: preflightHelpers.readyImagesText(counts.exportableImages),
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
  return persistedPath ? formatterHelpers.basename(persistedPath) || "Carpeta actual" : "";
}

function scanningScanFolderName() {
  return formatterHelpers.basename(parseFolderInput(state.bridgeScanPath)[0]);
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
  const warningsLabel = counts.nonBlockingWarnings ? preflightHelpers.countText(counts.nonBlockingWarnings, "aviso", "avisos") : "Sin avisos";
  const ignoredLabel = counts.ignoredFiles ? preflightHelpers.countText(counts.ignoredFiles, "ignorado", "ignorados") : "Sin ignorados";

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
  if (!profiles.length) {
    return "Sin formatos activos";
  }
  return batchViewHelpers.batchOutputLine({
    background: state.background,
    format: state.format,
    profileLines: profiles.length > 1
      ? profiles.map((profile) => `${profile.format} ${outputProfileHelpers.outputProfileSize(profile).replace("x", "×")}`)
      : [],
    size: state.size,
  });
}

function outputProfilesSummaryLabel(profiles = exportOutputProfiles()) {
  if (!profiles.length) {
    return "Sin formatos activos";
  }
  return batchViewHelpers.outputProfilesSummaryLabel({
    backgroundLabel: settingsViewHelpers.backgroundLabel(state.background),
    format: state.format,
    profileLabels: profiles.length > 1 ? profiles.map((profile) => `${profile.name} (${profile.format})`) : [],
    sizeLabel: outputSizeDisplay(),
  });
}

function batchDestinationLine() {
  const profiles = exportOutputProfiles();
  if (!profiles.length) {
    return "Sin destino activo";
  }
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
    ["Formatos", outputProfilesSummaryLabel()],
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
    detail: item.detail || batchViewHelpers.omissionReasonLabel(item.reason),
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
    destination: outputProfileViewHelpers.profileDestinationPreviewLabel(profile),
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
  const adjusted = imageAdjustmentOverrideCount(images);
  const valid = images.filter((image) => image.status === "ready" || hasImageAdjustmentOverride(image)).length;
  const warnings = images.filter((image) => image.status === "warning").length;
  const errors = images.filter((image) => image.status === "error" || exportItemState(image)?.status === "error").length;
  const ignored = counts.ignoredFiles;
  const issueCount = counts.reviewIssues;
  const filmstripCount = $("#filmstrip-count");
  $("#image-search").value = state.search;
  updateBatchSearchClear();
  renderGalleryViewButtons();
  renderGalleryOutputControl();

  if (state.batch === "none") {
    $("#batch-count").textContent = "Sin lote";
    setBatchPill("Sin carpeta", "muted");
    setGalleryTitle(0, "Sin lote");
    setGalleryMeta("");
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
    readyLabel: preflightHelpers.readyImagesText(counts.exportableImages),
    scanStatus: state.scanStatus,
  });

  if (state.batch === "scanning") {
    $("#batch-count").textContent = "Escaneando";
    setBatchPill("Escaneando", "active");
    setGalleryTitle(0, "Escaneando");
    setGalleryMeta(state.scanStatus || "Leyendo carpeta");
    $("#batch-visible-count").textContent = sidebarSummaryText;
    $("#folder-list").innerHTML = batchDetailViewHelpers.folderItemHtml({
      id: "scan",
      name: isBridgeBatch() || !devMode ? formatterHelpers.basename(parseFolderInput(state.bridgeScanPath)[0]) || "Ruta" : "Camisetas Mayo",
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
    setGalleryMeta(sidebarSummaryText);
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
  $("#batch-count").textContent = exportable ? preflightHelpers.readyImagesText(exportable) : "Sin exportables";
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
  setGalleryMeta(galleryBatchMetaText(counts, images));
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
    title.textContent = label || preflightHelpers.readyImagesText(Number(count) || 0);
  }
}

function setGalleryMeta(text = "") {
  const meta = $("#gallery-batch-meta");
  if (meta) {
    meta.textContent = text;
    meta.title = text;
  }
}

function galleryBatchMetaText(counts = batchCounts(), images = activeImages()) {
  const filesFound = counts.filesFound === null ? images.length : Number(counts.filesFound) || images.length;
  const parts = [
    batchViewHelpers.detectedFormatLabel(images),
    filesFound ? `${filesFound} archivos` : "",
  ].filter(Boolean);
  if (counts.nonBlockingWarnings) {
    parts.push(`${counts.nonBlockingWarnings} ${counts.nonBlockingWarnings === 1 ? "aviso" : "avisos"}`);
  }
  if (counts.ignoredFiles) {
    parts.push(`${counts.ignoredFiles} ${counts.ignoredFiles === 1 ? "ignorado" : "ignorados"}`);
  }
  return parts.join(" · ");
}

function renderGalleryOutputControl() {
  const control = $("#gallery-output-control");
  const select = $("#gallery-output-select");
  if (!control || !select) {
    return;
  }
  const profiles = galleryOutputProfiles();
  const showControl = state.batch === "ready" && profiles.length > 1;
  control.hidden = !showControl;
  if (!showControl) {
    select.innerHTML = "";
    return;
  }
  const context = galleryActiveOutputContext();
  const customOption = context.id === "__custom"
    ? `<option value="__custom">Formato personalizado · ${escapeHtml(context.label)}</option>`
    : "";
  select.innerHTML = `${customOption}${profiles.map((profile) => {
    return `<option value="${escapeHtml(profile.id)}">${escapeHtml(profile.name)}</option>`;
  }).join("")}`;
  select.value = context.id;
  if (select.value !== context.id) {
    select.value = profiles[0]?.id || "";
  }
  select.title = context.summary;
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
    return image.thumbnailUrl || (image.path ? bridgeThumbnailUrl(image.path) : "");
  }
  return galleryHelpers.mockThumbnailDataUrl(image);
}

function thumbnailState(image, src) {
  return galleryHelpers.thumbnailState({
    displaySrc: src,
    renderedOnly: false,
    src,
    stored: state.thumbnailStatus[image.id],
  });
}

function renderedThumbnailKey(image) {
  const signature = {
    background: state.background,
    format: state.format,
    imagePath: image.path,
    localOverride: currentImageOverride(image),
    preset: state.activePreset,
    settings: bridgePreviewSettings(),
    size: state.size,
  };
  return `rendered:${JSON.stringify(signature)}`;
}

function thumbnailTargetSize(maxSide = 180) {
  const match = /^(\d+)x(\d+)$/.exec(state.size);
  if (!match) {
    return { targetWidth: maxSide, targetHeight: maxSide };
  }
  const width = Number(match[1]) || maxSide;
  const height = Number(match[2]) || maxSide;
  const scale = Math.min(maxSide / Math.max(width, height), 1);
  return {
    targetWidth: Math.max(1, Math.round(width * scale)),
    targetHeight: Math.max(1, Math.round(height * scale)),
  };
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
  state.bridgeLastResponse = `thumbnail error: ${formatterHelpers.basename(src) || imageId}`;
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
    renderedOnly: true,
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
      ...thumbnailTargetSize(),
      settings: bridgePreviewSettings(),
      localOverride: currentImageOverride(image),
    }),
    timeoutMs: 20000,
  });
  if (imageThumbnailSrc(image) !== sourceSrc) {
    return;
  }
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
    let image = wrapper.querySelector(".thumb-image");
    if (!image) {
      const item = activeImages().find((activeImage) => activeImage.id === imageId);
      image = document.createElement("img");
      image.className = "thumb-image";
      image.loading = "eager";
      image.dataset.imageId = imageId;
      image.alt = `Miniatura de ${item?.name || "imagen"}`;
      wrapper.prepend(image);
    }
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
  const imageStatus = hasImageAdjustmentOverride(image) ? "adjusted" : image.status;
  const thumbnailSrc = imageThumbnailSrc(image);
  return galleryHelpers.imageItemHtml({
    exportState,
    fileType: imageFileType(image),
    image,
    imageStatus,
    outputLabel: "",
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
  const previewBackgroundMode = backgroundVisualMode(state.previewBg);
  const previewBackgroundColor = backgroundCssColor(state.previewBg);
  const canvasArea = $("#canvas-area");
  canvasArea.className = `canvas-area bg-${previewBackgroundMode}`;
  if (previewBackgroundColor) {
    canvasArea.style.setProperty("--custom-preview-bg", previewBackgroundColor);
  } else {
    canvasArea.style.removeProperty("--custom-preview-bg");
  }
  $$(".preview-toolbar [data-preview-mode]").forEach((button) => {
    button.classList.toggle("active", button.dataset.previewMode === state.previewMode);
    button.disabled = button.dataset.previewMode === "processed"
      ? previewControlsDisabled
      : compareControlsDisabled;
  });
  $$(".background-switch [data-preview-bg]").forEach((button) => {
    const previewBg = normalizePreviewBackgroundValue(state.previewBg);
    const isCustom = button.dataset.previewBg === "custom";
    const isActive = isCustom ? Boolean(outputProfileHelpers.parseRgbBackground(previewBg)) : button.dataset.previewBg === previewBg;
    button.classList.toggle("active", isActive);
    button.disabled = previewControlsDisabled;
  });
  const customPreviewRgb = previewCustomRgbChannels(state.previewBg);
  ["r", "g", "b"].forEach((channel, index) => {
    const input = $(`[data-preview-bg-channel="${channel}"]`);
    if (input) {
      input.value = String(customPreviewRgb[index]);
      input.disabled = previewControlsDisabled;
    }
  });
  const customSwatch = $("#preview-bg-custom-swatch");
  if (customSwatch) {
    customSwatch.style.setProperty("--custom-preview-bg-control", `rgb(${customPreviewRgb.join(", ")})`);
  }
  const customFields = $(".viewer-bg-custom-fields");
  if (customFields) {
    customFields.classList.toggle("active", Boolean(outputProfileHelpers.parseRgbBackground(state.previewBg)));
  }
  $$("[data-action='zoom-height'], [data-action='zoom-width'], [data-action='zoom-out'], [data-action='zoom-in'], [data-action='force-preview-error']").forEach((button) => {
    button.disabled = previewControlsDisabled;
  });
  $$("[data-action='zoom-height'], [data-action='zoom-width']").forEach((button) => {
    const expectedMode = button.dataset.action === "zoom-height"
      ? "height"
      : "width";
    const active = state.fitMode === expectedMode;
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
  canvas.className = `preview-canvas ${state.previewMode} bg-${previewBackgroundMode} ${previewStateHelpers.viewerModeClass()}`;
  canvas.style.setProperty("--preview-scale", previewStateHelpers.isAutoViewerMode() ? "1" : String(state.zoom / 100));
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
    canvas.innerHTML = emptyStateViewHelpers.emptyStateHtml({
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
    canvas.innerHTML = emptyStateViewHelpers.emptyStateHtml({
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
    canvas.innerHTML = emptyStateViewHelpers.emptyStateHtml({
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
  if (!previewStateHelpers.isAutoViewerMode()) {
    label.textContent = `${state.zoom}%`;
    return;
  }

  const zoom = calculateFitZoom();
  state.fitZoom = zoom;
  label.textContent = `${zoom}%`;
  if (!viewerPanState.active) {
    clampViewerPan();
    applyViewerPanDom();
  }
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
    canvas.style.removeProperty("--fit-width");
    canvas.style.removeProperty("--fit-height");
    return 100;
  }
  const layout = previewStateHelpers.viewerFitLayout({
    canvasHeight: canvas.clientHeight,
    canvasWidth: canvas.clientWidth,
    mode: state.fitMode,
    naturalHeight,
    naturalWidth,
  });
  canvas.style.setProperty("--fit-width", `${layout.width}px`);
  canvas.style.setProperty("--fit-height", `${layout.height}px`);
  return layout.zoom;
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
      inlineSize: !previewStateHelpers.isAutoViewerMode(),
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
    engineLabel: shadowEngineLabels[state.settings.shadow_engine] || "",
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
  const size = outputProfileHelpers.parseOutputSize(state.size);
  return `${size.width}×${size.height}`;
}

function viewerOutputCompactLabel() {
  return previewViewHelpers.viewerOutputCompactLabel({
    backgroundLabel: settingsViewHelpers.backgroundLabel(state.background),
    format: state.format,
    sizeLabel: outputSizeDisplay(),
  });
}

function previewStateHtml(title, detail) {
  return emptyStateViewHelpers.emptyStateHtml({ variant: "inline", title, detail });
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
  const settingsPanel = $(".settings-panel");
  if (settingsPanel) {
    settingsPanel.dataset.shadowEngine = state.settings.shadow_engine || "";
  }
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
        syncRangeFill(input);
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
  const localActive = hasImageAdjustmentOverride(image);
  $("#local-adjustment").classList.toggle("active", localActive);
  $("#local-adjustment-text").textContent = settingsViewHelpers.localAdjustmentText(localActive);
  localOverrideKeys.forEach((key) => {
    const value = Number(localOverride[key] || 0);
    const input = $(`[data-local-setting="${key}"]`);
    const output = $(`#local-${key}-output`);
    const numberInput = $(`[data-local-setting-number="${key}"]`);
    if (input) {
      input.value = value;
      syncRangeFill(input);
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
  renderLightingSceneControls();
}

function lightingSceneFieldValue(scene, field) {
  if (field === "ambient_intensity") {
    return scene.ambient_intensity;
  }
  if (field.startsWith("main.")) {
    return scene.main[field.slice(5)];
  }
  return undefined;
}

function lightingOutputId(field) {
  const names = {
    "main.height": "lighting-height-output",
    "main.size": "lighting-size-output",
    "main.intensity": "lighting-intensity-output",
    ambient_intensity: "lighting-ambient-output",
  };
  return names[field] || "";
}

function lightingSliderValue(field, value) {
  if (field === "main.intensity") {
    return Math.round(numberHelpers.clampNumber(value, 0, 1.5, defaultLightingScene.main.intensity) * 100);
  }
  return Math.round(numberHelpers.clampNumber(value, 0, 1, 0) * 100);
}

function renderLightingSceneControls() {
  const panel = $("#studio-lighting-panel");
  if (!panel) {
    return;
  }
  const enabled = state.settings.shadow_engine === "studio_2_5d";
  panel.hidden = !enabled;
  const scene = normalizeLightingScene(state.settings.lighting_scene);
  state.settings.lighting_scene = scene;
  const exactPresetId = lightingScenePresetId(scene);
  const rememberedPresetId = lightingScenePresets[state.lightingPresetId] ? state.lightingPresetId : "";
  const selectedPresetId = enabled ? exactPresetId || rememberedPresetId || "overhead_soft" : "";

  $$("[data-lighting-field]").forEach((input) => {
    const field = input.dataset.lightingField;
    const value = lightingSceneFieldValue(scene, field);
    if (input.tagName === "SELECT") {
      input.value = value;
    } else {
      const sliderValue = lightingSliderValue(field, value);
      input.value = sliderValue;
      syncRangeFill(input);
      const output = $(`#${lightingOutputId(field)}`);
      if (output) {
        if ("value" in output && document.activeElement !== output) {
          output.value = String(sliderValue);
        } else {
          output.textContent = String(sliderValue);
        }
      }
    }
    input.disabled = !enabled;
  });

  $$("[data-lighting-number-field]").forEach((input) => {
    const field = input.dataset.lightingNumberField;
    const value = lightingSliderValue(field, lightingSceneFieldValue(scene, field));
    if (document.activeElement !== input) {
      input.value = String(value);
    }
    input.disabled = !enabled;
  });

  $$("[data-lighting-preset]").forEach((button) => {
    const presetId = button.dataset.lightingPreset;
    const preset = lightingScenePresets[presetId];
    const selected = enabled && presetId === selectedPresetId;
    const exact = selected && lightingScenesEqual(scene, preset);
    button.disabled = !enabled;
    button.classList.toggle("active", selected);
    button.classList.toggle("is-modified", selected && !exact);
    button.setAttribute("aria-pressed", String(selected));
    button.title = selected && !exact ? "Preset modificado" : "";
  });

  const stage = $("#lighting-stage");
  const handle = $("#lighting-handle");
  if (stage) {
    stage.disabled = !enabled;
  }
  if (handle) {
    const left = ((scene.main.x + 1) / 2) * 100;
    const top = ((scene.main.y + 1) / 2) * 100;
    handle.style.left = `${left}%`;
    handle.style.top = `${top}%`;
  }
}

function lightingScenesEqual(first, second) {
  if (!second) {
    return false;
  }
  return JSON.stringify(normalizeLightingScene(first)) === JSON.stringify(normalizeLightingScene(second));
}

function lightingScenePresetId(scene) {
  return Object.entries(lightingScenePresets)
    .find(([, preset]) => lightingScenesEqual(scene, preset))?.[0] || "";
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
      emptyStateHtml: emptyStateViewHelpers.emptyStateHtml({
      variant: "inline",
      title: "Selecciona una imagen",
      detail: "Elige una miniatura para revisar la imagen.",
      actionLabel: activeImages().length ? "Seleccionar primera imagen" : "",
      action: activeImages().length ? "select-first-image" : "",
    }),
    });
  }

  const reviewState = imageReviewState(image);
  const issues = imageReviewIssues(image);
  const outputName = outputNameForImage(image);
  const hasLocal = hasImageAdjustmentOverride(image);
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
  const status = exportState?.status || (hasImageAdjustmentOverride(image) ? "adjusted" : image.status);
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
      detail: image.detail || "Esta imagen quedará fuera de la exportación.",
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
    keys: visibleAdvancedSettingKeys(state.settings),
    presetDirty: state.presetDirty,
    presetSettings,
  });
}

function visibleAdvancedSettingKeys(settings = state.settings) {
  if (settings.shadow_engine === "studio_2_5d") {
    return advancedSettingKeys.filter((key) => key !== "angle");
  }
  return advancedSettingKeys;
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
  panel.classList.toggle("is-advanced-subview", mode === "advanced");
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
  const detailsItems = $$(".settings-panel details.inspector-disclosure[data-inspector-section='advanced']");
  detailsItems.forEach((details) => {
    if (mode !== "advanced") {
      setInspectorDisclosureOpenState(details, false);
    }
  });
  if (mode !== "advanced") {
    pendingAdvancedDisclosure = "";
    return;
  }

  if (state.presetEditorOpen) {
    detailsItems.forEach((details) => {
      setInspectorDisclosureOpenState(details, details.classList.contains("preset-section"));
    });
    pendingAdvancedDisclosure = "";
    return;
  }

  const editableDetails = detailsItems.filter((details) => !details.classList.contains("preset-section"));
  detailsItems
    .filter((details) => details.classList.contains("preset-section"))
    .forEach((details) => setInspectorDisclosureOpenState(details, false));

  if (pendingAdvancedDisclosure) {
    const preferred = editableDetails.find((details) => details.classList.contains(pendingAdvancedDisclosure));
    if (preferred) {
      editableDetails.forEach((details) => setInspectorDisclosureOpenState(details, details === preferred));
    }
    pendingAdvancedDisclosure = "";
    return;
  }

  if (editableDetails.some((details) => details.open)) {
    return;
  }

  editableDetails.forEach((details) => {
    setInspectorDisclosureOpenState(details, details.classList.contains("appearance-section"));
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
    aspectInspectorCardHtml(),
    outputInspectorCardHtml(),
    selectedImageInspectorCardHtml(),
    issuesInspectorCardHtml(),
  ].filter(Boolean).join("");
}

function rangeFillPercent(input) {
  if (!input || input.type !== "range") {
    return 0;
  }
  const min = Number(input.min || 0);
  const max = Number(input.max || 100);
  const value = Number(input.value || min);
  if (!Number.isFinite(min) || !Number.isFinite(max) || max <= min) {
    return 0;
  }
  return Math.max(0, Math.min(100, ((value - min) / (max - min)) * 100));
}

function syncRangeFill(input) {
  if (input?.type !== "range") {
    return;
  }
  input.style.setProperty("--range-fill", `${rangeFillPercent(input)}%`);
}

function syncRangeFillStyles() {
  $$(".settings-panel input[type='range']").forEach(syncRangeFill);
}

function lotInspectorCardHtml() {
  const counts = batchCounts();
  const visible = getVisibleAppState();
  const ignored = counts.ignoredFiles ? `${counts.ignoredFiles} ignorado${counts.ignoredFiles === 1 ? "" : "s"}` : "";
  const customCount = imageAdjustmentOverrideCount();
  const custom = customCount ? `${customCount} personalizada${customCount === 1 ? "" : "s"}` : "";
  const meta = state.batch === "empty"
    ? `${preflightHelpers.readyImagesText(0)}${ignored ? ` · ${ignored}` : ""}`
    : `${preflightHelpers.readyImagesText(counts.exportableImages)}${custom ? ` · ${custom}` : ""}${ignored ? ` · ${ignored}` : ""}`;
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
    const enabled = Boolean(profile.enabled);
    return {
      id: profile.id,
      name: profile.name,
      enabled,
      active: profile.id === state.activeOutputProfileId,
      canToggle: true,
      summary: outputProfileSummaryLine(profile),
    };
  });
  return inspectorOutputViewHelpers.outputInspectorCardHtml({
    activeCount: activeProfiles.length,
    totalFiles,
    rows,
    dirty,
  });
}

function outputProfileInlineRowHtml(profile) {
  const enabled = Boolean(profile.enabled);
  return inspectorOutputViewHelpers.outputProfileInlineRowHtml({
    id: profile.id,
    name: profile.name,
    enabled,
    active: profile.id === state.activeOutputProfileId,
    canToggle: true,
    summary: outputProfileSummaryLine(profile),
  });
}

function selectedImageInspectorCardHtml() {
  const image = selectedImage();
  const hasLocal = image ? hasImageAdjustmentOverride(image) : false;
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
  const images = activeImages();
  const customizedCount = imageAdjustmentOverrideCount(images);
  return inspectorReviewViewHelpers.aspectInspectorCardHtml({
    hasReadyBatch: hasBatch() && state.batch === "ready",
    activePreset: state.activePreset,
    adjustments: activePresetItems(),
    customizedCount,
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
      outputSummary: `${state.format} · ${state.size} · ${settingsViewHelpers.backgroundLabel(state.background)}`,
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
  syncBackgroundSelectValue($("#background-select"), state.background);
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
  $("#export-readiness").textContent = state.outputEditMode ? "Editar formato" : outputProfileDisplayName();
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
      size: outputProfileHelpers.outputProfileSize(profile),
      destinationLabel: outputProfileViewHelpers.profileDestinationLabel(profile),
    })),
    formatLabel: activeOutputProfiles.length
      ? hasMultipleOutputs ? batchViewHelpers.outputCountLabel(activeOutputProfiles.length) : state.format
      : "Sin formato activo",
    sizeLabel: activeOutputProfiles.length ? hasMultipleOutputs ? "Por formato" : state.size.replace("x", " × ") : "-",
    backgroundLabel: activeOutputProfiles.length ? hasMultipleOutputs ? "Por formato" : settingsViewHelpers.backgroundLabel(state.background) : "-",
    destinationText,
    namingLabel: activeOutputProfiles.length ? hasMultipleOutputs ? "Por formato" : namingHumanLabel() : "-",
    example: activeOutputProfiles.length ? hasMultipleOutputs ? outputNameForProfile(activeOutputProfiles[0]) : namingExample() : "-",
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
  if (!profiles.length) {
    return "Sin formatos activos";
  }
  if (profiles.length > 1) {
    return batchViewHelpers.outputCountLabel(profiles.length);
  }
  const profile = activeOutputProfile();
  if (!profile || !outputMatchesProfile(profile)) {
    return "Formato personalizado";
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
  return `${profile.format} · ${outputProfileHelpers.outputProfileSize(profile).replace("x", " × ")} · ${settingsViewHelpers.backgroundLabel(profile.background)}`;
}

function syncBackgroundSelectValue(select, background) {
  if (!select) {
    return;
  }
  const normalized = outputProfileHelpers.normalizeBackgroundValue(background);
  select.innerHTML = backgroundSelectOptionsHtml(normalized);
  select.value = normalized;
}

function selectedBackgroundPresetFromForm(raw = outputProfileFormRawData()) {
  return backgroundPresetByValue(raw.background);
}

function backgroundRgbFromValue(value) {
  return outputProfileHelpers.parseRgbBackground(outputProfileHelpers.normalizeBackgroundValue(value)) || outputProfileHelpers.backgroundColorTuple(value);
}

function positionBackgroundPresetEditor() {
  const editor = $("#background-preset-editor");
  if (!editor || editor.hidden) {
    return;
  }
  const anchor = $("#profile-background-input");
  const dialog = $("#app-settings-modal .app-settings-dialog");
  const footer = $("#app-settings-modal .app-settings-footer");
  if (!anchor || !dialog) {
    return;
  }
  const margin = 16;
  const anchorRect = anchor.getBoundingClientRect();
  const dialogRect = dialog.getBoundingClientRect();
  const footerRect = footer?.getBoundingClientRect();
  const maxWidth = Math.max(280, Math.min(486, window.innerWidth - margin * 2, dialogRect.width - margin * 2));
  editor.style.width = `${maxWidth}px`;
  const editorHeight = editor.offsetHeight || 0;
  const left = numberHelpers.clampNumber(anchorRect.left, dialogRect.left + margin, dialogRect.right - maxWidth - margin);
  const footerTop = footerRect?.top || dialogRect.bottom;
  const preferredTop = anchorRect.bottom + 8;
  const maxTop = Math.max(dialogRect.top + margin, footerTop - editorHeight - 8);
  const top = numberHelpers.clampNumber(preferredTop, dialogRect.top + margin, maxTop);
  editor.style.left = `${left}px`;
  editor.style.top = `${top}px`;
}

function renderBackgroundPresetControls(raw = outputProfileFormRawData()) {
  const selectedPreset = selectedBackgroundPresetFromForm(raw);
  const editor = $("#background-preset-editor");
  const actions = $(".background-preset-actions");
  const deleteButton = $("[data-action='delete-background-preset']");
  if (deleteButton) {
    deleteButton.disabled = !selectedPreset || state.backgroundPresets.length <= 1;
    deleteButton.title = !selectedPreset
      ? "Este fondo no está guardado como preset"
      : state.backgroundPresets.length <= 1
        ? "Debe quedar al menos un fondo"
        : "Eliminar fondo";
  }
  if (!editor) {
    return;
  }
  const editorState = state.backgroundPresetEditor;
  if (actions) {
    actions.hidden = Boolean(editorState);
  }
  editor.hidden = !editorState;
  if (!editorState) {
    return;
  }
  const nameInput = $("#background-preset-name-input");
  const kindInput = $("#background-preset-kind-input");
  const rgbInput = $("#background-preset-rgb-input");
  const rgbField = $(".background-preset-rgb-field");
  if (nameInput && nameInput.value !== editorState.name) {
    nameInput.value = editorState.name;
  }
  if (kindInput && kindInput.value !== editorState.kind) {
    kindInput.value = editorState.kind;
  }
  if (rgbInput && rgbInput.value !== editorState.rgbText) {
    rgbInput.value = editorState.rgbText;
  }
  if (rgbField) {
    rgbField.hidden = editorState.kind === "transparent";
  }
  editor.classList.toggle("is-transparent", editorState.kind === "transparent");
  const swatch = $("#background-preset-swatch");
  if (swatch) {
    const rgb = editorState.kind === "transparent" ? null : outputProfileHelpers.parseRgbBackground(outputProfileHelpers.customRgbBackgroundValue(editorState.rgbText));
    const isInvalidRgb = editorState.kind !== "transparent" && !rgb;
    swatch.classList.toggle("is-transparent", editorState.kind === "transparent");
    swatch.classList.toggle("is-invalid", isInvalidRgb);
    swatch.style.backgroundColor = rgb ? `rgb(${rgb.join(", ")})` : "";
    swatch.setAttribute(
      "aria-label",
      editorState.kind === "transparent"
        ? "Muestra del fondo transparente"
        : rgb
          ? `Muestra del fondo RGB ${rgb.join(", ")}`
          : "Muestra del fondo sin RGB válido"
    );
  }
  const message = $("#background-preset-editor-message");
  if (message) {
    message.textContent = editorState.error || "";
    message.hidden = !editorState.error;
    message.classList.toggle("error", Boolean(editorState.error));
  }
  positionBackgroundPresetEditor();
}

function updateBackgroundPresetEditorFromFields() {
  const editor = state.backgroundPresetEditor;
  if (!editor) {
    return;
  }
  state.backgroundPresetEditor = {
    ...editor,
    error: "",
    kind: $("#background-preset-kind-input")?.value === "transparent" ? "transparent" : "rgb",
    name: $("#background-preset-name-input")?.value || "",
    rgbText: $("#background-preset-rgb-input")?.value || "",
  };
}

function beginBackgroundPresetEdit(mode = "edit") {
  const raw = outputProfileFormRawData();
  const preset = mode === "edit" ? selectedBackgroundPresetFromForm(raw) : null;
  const source = preset || {
    id: outputProfileHelpers.uniqueOutputProfileId("fondo", Date.now()),
    kind: raw.background === "transparent" ? "transparent" : "rgb",
    name: preset ? preset.name : "Nuevo fondo",
    rgb: backgroundRgbFromValue(raw.background),
  };
  state.backgroundPresetEditor = {
    id: mode === "edit" && preset ? preset.id : outputProfileHelpers.uniqueOutputProfileId(source.name || "fondo", Date.now()),
    mode: mode === "edit" && preset ? "edit" : "new",
    sourceValue: preset ? backgroundPresetValue(preset) : "",
    kind: source.kind === "transparent" ? "transparent" : "rgb",
    name: source.name,
    rgbText: (source.rgb || [230, 230, 230]).join(", "),
    error: "",
  };
  renderOutputProfileModalState();
}

function saveBackgroundPreset() {
  updateBackgroundPresetEditorFromFields();
  const editor = state.backgroundPresetEditor;
  if (!editor) {
    return;
  }
  const name = editor.name.trim();
  const rgb = outputProfileHelpers.customRgbBackgroundValue(editor.rgbText);
  if (!name) {
    state.backgroundPresetEditor = { ...editor, error: "Pon un nombre al fondo." };
    renderBackgroundPresetControls();
    return;
  }
  if (editor.kind !== "transparent" && !rgb) {
    state.backgroundPresetEditor = { ...editor, error: "Indica un RGB válido entre 0 y 255." };
    renderBackgroundPresetControls();
    return;
  }
  const savedPreset = normalizeBackgroundPreset({
    id: editor.id,
    kind: editor.kind,
    name,
    rgb: editor.kind === "transparent" ? [230, 230, 230] : outputProfileHelpers.parseRgbBackground(rgb),
  });
  const previousValue = editor.mode === "edit" ? editor.sourceValue : "";
  const index = state.backgroundPresets.findIndex((preset) => preset.id === editor.id);
  if (index >= 0) {
    state.backgroundPresets[index] = savedPreset;
  } else {
    state.backgroundPresets.push(savedPreset);
  }
  state.backgroundPresets = normalizeBackgroundPresetList(state.backgroundPresets);
  const nextValue = backgroundPresetValue(savedPreset);
  if (previousValue) {
    replaceBackgroundValue(previousValue, nextValue);
  } else {
    const draft = ensureOutputProfileDraft();
    state.outputProfileDraft = { ...draft, background: nextValue };
  }
  state.backgroundPresetEditor = null;
  state.statusText = `Fondo guardado: ${savedPreset.name}`;
  persistBackgroundPresets();
  render();
}

function replaceBackgroundValue(previousValue, nextValue) {
  const previous = outputProfileHelpers.normalizeBackgroundValue(previousValue);
  const next = outputProfileHelpers.normalizeBackgroundValue(nextValue);
  state.outputProfiles = state.outputProfiles.map((profile) => (
    outputProfileHelpers.normalizeBackgroundValue(profile.background) === previous ? { ...profile, background: next } : profile
  ));
  if (state.outputProfileDraft && outputProfileHelpers.normalizeBackgroundValue(state.outputProfileDraft.background) === previous) {
    state.outputProfileDraft = { ...state.outputProfileDraft, background: next };
  }
  if (outputProfileHelpers.normalizeBackgroundValue(state.background) === previous) {
    state.background = next;
  }
  if (outputProfileHelpers.normalizeBackgroundValue(state.previewBg) === previous) {
    state.previewBg = next;
  }
  persistOutputProfiles();
}

function deleteBackgroundPreset() {
  const preset = selectedBackgroundPresetFromForm();
  if (!preset || state.backgroundPresets.length <= 1) {
    return;
  }
  const confirmed = window.confirm(`Eliminar fondo "${preset.name}"?\n\nLos formatos que ya usen ese RGB conservarán el valor actual.`);
  if (!confirmed) {
    return;
  }
  state.backgroundPresets = state.backgroundPresets.filter((item) => item.id !== preset.id);
  state.backgroundPresetEditor = null;
  state.statusText = `Fondo eliminado: ${preset.name}`;
  persistBackgroundPresets();
  render();
}

function outputProfileCompactLabel(profile) {
  if (!profile) {
    return "Sin salida";
  }
  return `${profile.format} · ${settingsViewHelpers.backgroundLabel(profile.background)}`;
}

function ensureOutputProfileDraft() {
  const current = state.outputProfiles.find((profile) => profile.id === state.outputProfileEditorId)
    || state.outputProfileDraft
    || activeOutputProfile()
    || outputProfileHelpers.normalizeOutputProfile(defaultOutputProfiles[0]);
  if (!state.outputProfileEditorId) {
    state.outputProfileEditorId = current.id;
  }
  if (!state.outputProfileDraft || state.outputProfileDraft.id !== state.outputProfileEditorId) {
    state.outputProfileDraft = { ...current };
  }
  return state.outputProfileDraft;
}

function setOutputProfileFormValues(profile) {
  syncBackgroundSelectValue($("#profile-background-input"), profile.background);
  const pairs = [
    ["profile-name-input", profile.name],
    ["profile-format-input", profile.format],
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
  const backgroundMode = value("profile-background-input", backgroundSelectMode(current.background));
  return {
    id: current.id,
    name: value("profile-name-input", current.name),
    format: value("profile-format-input", current.format),
    background: outputProfileHelpers.normalizeBackgroundValue(backgroundMode, current.background),
    width: value("profile-width-input", current.width),
    height: value("profile-height-input", current.height),
    destinationMode: value("profile-destination-mode-input", current.destinationMode),
    destinationValue: value("profile-destination-input", current.destinationValue),
    naming: value("profile-naming-input", current.naming),
    suffix: value("profile-suffix-input", current.suffix),
    enabled: Boolean(current.enabled),
  };
}

function outputProfileRawFromProfile(profile) {
  return {
    id: profile.id,
    name: profile.name,
    format: profile.format,
    background: profile.background,
    backgroundCustom: outputProfileHelpers.backgroundCustomText(profile.background),
    backgroundMode: backgroundSelectMode(profile.background),
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
  return outputProfileHelpers.normalizeOutputProfile({
    id: current.id,
    name: raw.name,
    enabled: Boolean(raw.enabled),
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
  state.outputProfileNotice = "";
  syncTransparentBackgroundFormat();
  syncOutputProfileDestinationMode();
  state.outputDeleteConfirmId = "";
  state.outputProfileDraft = outputProfileDraftFromForm();
}

function syncTransparentBackgroundFormat() {
  const backgroundInput = $("#profile-background-input");
  const formatInput = $("#profile-format-input");
  if (!backgroundInput || !formatInput) {
    return;
  }
  if (outputProfileHelpers.normalizeBackgroundValue(backgroundInput.value) === "transparent" && outputProfileHelpers.normalizeExportFormat(formatInput.value) !== "PNG") {
    formatInput.value = "PNG";
  }
}

function looksLikeAbsoluteOutputPath(value) {
  const text = String(value || "").trim();
  return /^[A-Za-z]:[\\/]/.test(text) || /^[/\\]{2}/.test(text) || text.startsWith("/");
}

function syncOutputProfileDestinationMode() {
  const modeInput = $("#profile-destination-mode-input");
  const destinationInput = $("#profile-destination-input");
  if (!modeInput || !destinationInput) {
    return;
  }
  const mode = modeInput.value === "custom" ? "custom" : "source";
  const value = String(destinationInput.value || "").trim();
  if (mode === "source" && (!value || looksLikeAbsoluteOutputPath(value))) {
    destinationInput.value = "Salida";
    return;
  }
  if (mode === "custom" && (!value || value === "Salida")) {
    destinationInput.value = storageHelpers.readValue(window.localStorage, STORAGE_KEYS.lastOutputFolder) || "";
  }
}

function setOutputProfileDraftEnabled(enabled) {
  const draft = ensureOutputProfileDraft();
  state.outputProfileDraft = {
    ...draft,
    enabled: Boolean(enabled),
  };
  state.outputProfileNotice = "";
  state.outputDeleteConfirmId = "";
  renderAppSettings();
}

function selectOutputProfileDraft(profileId) {
  if (state.appSettingsOpen && outputProfileHasUnsavedChanges()) {
    showOutputProfileUnsavedNotice("Guarda o descarta los cambios antes de cambiar de formato.");
    return;
  }
  const profile = outputProfileManagerRows().find((item) => item.id === profileId);
  if (!profile) {
    return;
  }
  state.outputProfileEditorId = profile.id;
  state.outputProfileDraft = { ...profile };
  state.outputProfileNotice = "";
  state.outputDeleteConfirmId = "";
  state.statusText = `Editando formato: ${profile.name}`;
  render();
}

function newOutputProfile() {
  if (state.appSettingsOpen && outputProfileHasUnsavedChanges()) {
    showOutputProfileUnsavedNotice("Guarda o descarta los cambios antes de crear otro formato.");
    return;
  }
  const source = currentOutputProfileData();
  const id = outputProfileHelpers.uniqueOutputProfileId("formato", Date.now());
  state.outputProfileEditorId = id;
  state.outputProfileDraft = {
    ...source,
    id,
    name: "Nuevo formato",
    enabled: false,
  };
  state.outputProfileNotice = "";
  state.outputDeleteConfirmId = "";
  state.appSettingsOpen = true;
  state.statusText = "Nuevo formato de salida";
  render();
}

function duplicateOutputProfile() {
  if (state.appSettingsOpen && outputProfileHasUnsavedChanges()) {
    showOutputProfileUnsavedNotice("Guarda o descarta los cambios antes de duplicar.");
    return;
  }
  const source = state.outputProfileDraft || activeOutputProfile() || currentOutputProfileData();
  const id = outputProfileHelpers.uniqueOutputProfileId(source.name || "formato", Date.now());
  state.outputProfileEditorId = id;
  state.outputProfileDraft = {
    ...source,
    id,
    name: `${source.name || "Formato"} copia`,
    enabled: false,
  };
  state.outputProfileNotice = "";
  state.outputDeleteConfirmId = "";
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
  const saved = outputProfileHelpers.normalizeOutputProfile({
    ...draft,
    name: draft.name.trim() || "Formato sin nombre",
  });
  const index = state.outputProfiles.findIndex((profile) => profile.id === saved.id);
  if (index >= 0) {
    state.outputProfiles[index] = saved;
  } else {
    state.outputProfiles.push(saved);
  }
  state.outputProfiles = outputProfileHelpers.normalizeOutputProfileList(state.outputProfiles, saved.id);
  state.outputProfileEditorId = saved.id;
  state.outputProfileDraft = { ...saved };
  state.outputProfileNotice = "";
  state.outputDeleteConfirmId = "";
  if (saved.id === state.activeOutputProfileId && saved.enabled) {
    syncOutputProfileState(saved);
  } else if (saved.id === state.activeOutputProfileId && !saved.enabled) {
    reassignActiveOutputProfileReference({ render: false });
  }
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

function deleteManagedOutputProfile() {
  const draft = ensureOutputProfileDraft();
  const exists = state.outputProfiles.some((profile) => profile.id === draft.id);
  if (!exists) {
    const fallback = activeOutputProfile() || state.outputProfiles[0];
    state.outputProfileEditorId = fallback?.id || "";
    state.outputProfileDraft = fallback ? { ...fallback } : null;
    state.outputDeleteConfirmId = "";
    state.statusText = "Formato descartado";
    render();
    return;
  }
  if (state.outputProfiles.length <= 1) {
    state.outputDeleteConfirmId = "";
    state.statusText = "Debe quedar al menos un formato";
    render();
    return;
  }
  state.outputDeleteConfirmId = draft.id;
  state.outputProfileNotice = "";
  state.statusText = `Confirmar eliminación: ${draft.name}`;
  render();
  queueModalFocus("#app-settings-modal", "[data-action='confirm-output-delete']");
}

function cancelDeleteManagedOutputProfile() {
  state.outputDeleteConfirmId = "";
  state.statusText = "Eliminación cancelada";
  render();
}

function confirmDeleteManagedOutputProfile() {
  const profileId = state.outputDeleteConfirmId;
  const profile = state.outputProfiles.find((item) => item.id === profileId);
  if (!profile) {
    state.outputDeleteConfirmId = "";
    render();
    return;
  }
  if (state.outputProfiles.length <= 1) {
    state.outputDeleteConfirmId = "";
    state.statusText = "Debe quedar al menos un formato";
    render();
    return;
  }

  const deletedName = profile.name;
  state.outputProfiles = state.outputProfiles.filter((item) => item.id !== profileId);
  if (state.activeOutputProfileId === profileId) {
    reassignActiveOutputProfileReference({ render: false, statusText: `Formato eliminado: ${deletedName}` });
  }
  const nextDraft = state.outputProfiles.find((profile) => profile.id === state.outputProfileEditorId)
    || state.outputProfiles.find((profile) => profile.id === state.activeOutputProfileId)
    || state.outputProfiles[0];
  state.outputProfileEditorId = nextDraft?.id || "";
  state.outputProfileDraft = nextDraft ? { ...nextDraft } : null;
  state.outputDeleteConfirmId = "";
  persistOutputProfiles();
  state.statusText = `Formato eliminado: ${deletedName}`;
  render();
}

function resetOutputProfileDraft() {
  const original = state.outputProfiles.find((profile) => profile.id === state.outputProfileEditorId)
    || activeOutputProfile()
    || outputProfileHelpers.normalizeOutputProfile(defaultOutputProfiles[0]);
  state.outputProfileDraft = { ...original };
  state.outputProfileEditorId = original.id;
  state.outputProfileNotice = "";
  state.outputDeleteConfirmId = "";
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
      id: outputProfileHelpers.uniqueOutputProfileId("formato-personalizado", Date.now()),
      name: "Formato personalizado",
    };
  state.appSettingsOpen = true;
  state.outputProfileEditorId = profile.id;
  state.outputProfileDraft = { ...profile };
  state.outputDeleteConfirmId = "";
  state.statusText = "Formatos de salida";
  render();
  queueModalFocus("#app-settings-modal", "[data-action='close-app-settings']");
}

function closeAppSettings() {
  if (state.appSettingsOpen && outputProfileHasUnsavedChanges()) {
    showOutputProfileUnsavedNotice("Guarda o descarta los cambios antes de cerrar.");
    return;
  }
  releaseModalFocusBeforeHide();
  state.appSettingsOpen = false;
  state.outputProfileDraft = null;
  state.outputProfileNotice = "";
  state.outputDeleteConfirmId = "";
  state.statusText = "Configuración cerrada";
  render();
}

function cancelOutputProfileDraft() {
  releaseModalFocusBeforeHide();
  const fallback = enabledActiveOutputProfile()
    || state.outputProfiles.find((profile) => profile.id === state.activeOutputProfileId)
    || state.outputProfiles[0]
    || null;
  state.appSettingsOpen = false;
  state.outputProfileEditorId = fallback?.id || "";
  state.outputProfileDraft = null;
  state.outputDeleteConfirmId = "";
  state.statusText = "Formato descartado";
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
  state.outputDeleteConfirmId = "";
  state.batchDetailOpen = false;
  state.exportConfirmOpen = true;
  state.exportConfirmRisks = preflightHelpers.dedupeExportRisks(risks);
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

function showOutputProfileUnsavedNotice(message) {
  state.outputProfileNotice = message;
  state.statusText = "Cambios sin guardar";
  renderOutputProfileModalState();
}

function sameOutputProfileRaw(profile, raw) {
  if (!profile || !raw) {
    return false;
  }
  const destinationMode = raw.destinationMode === "custom" ? "custom" : "source";
  return String(profile.name || "").trim() === String(raw.name || "").trim()
    && profile.format === outputProfileHelpers.normalizeExportFormat(raw.format)
    && profile.background === raw.background
    && String(profile.width) === String(raw.width || "").trim()
    && String(profile.height) === String(raw.height || "").trim()
    && profile.destinationMode === destinationMode
    && String(profile.destinationValue || "") === String(raw.destinationValue || "")
    && String(profile.naming || "") === String(raw.naming || "")
    && String(profile.suffix || "") === String(raw.suffix || "")
    && Boolean(profile.enabled) === Boolean(raw.enabled);
}

function outputProfileChangeCount() {
  const raw = outputProfileFormRawData();
  const saved = state.outputProfiles.find((profile) => profile.id === raw.id);
  if (!saved) {
    return 1;
  }
  const destinationMode = raw.destinationMode === "custom" ? "custom" : "source";
  const checks = [
    String(saved.name || "").trim() !== String(raw.name || "").trim(),
    saved.format !== outputProfileHelpers.normalizeExportFormat(raw.format),
    saved.background !== raw.background,
    String(saved.width) !== String(raw.width || "").trim(),
    String(saved.height) !== String(raw.height || "").trim(),
    saved.destinationMode !== destinationMode,
    String(saved.destinationValue || "") !== String(raw.destinationValue || ""),
    String(saved.naming || "") !== String(raw.naming || ""),
    String(saved.suffix || "") !== String(raw.suffix || ""),
    Boolean(saved.enabled) !== Boolean(raw.enabled),
  ];
  return checks.filter(Boolean).length;
}

function outputProfileValidation(raw = outputProfileFormRawData()) {
  return outputProfileHelpers.outputProfileValidation(raw);
}

function outputProfileEditorHeadingHtml(profile, validation, dirty) {
  const saved = state.outputProfiles.find((item) => item.id === profile.id);
  return outputProfileViewHelpers.outputProfileEditorHeadingHtml({
    profile,
    validation,
    dirty,
    enabled: Boolean(profile.enabled),
    isPersisted: Boolean(saved),
    new: !saved,
  });
}

function outputProfilePreviewHtml(profile, validation = {}) {
  const image = selectedImage();
  const originalName = image?.name || "imagen_original.png";
  const resultName = outputNameForProfile(profile, image);
  const destination = outputProfileViewHelpers.profileDestinationPreviewLabel(profile);
  const resultPath = destination && destination !== "junto al origen"
    ? `${destination.replace(/[\\/]$/, "")}/${resultName}`
    : resultName;
  return outputProfileViewHelpers.outputProfilePreviewHtml({
    originalName,
    resultName,
    destination,
    resultPath,
    summary: outputProfileSummaryLine(profile),
    validation,
  });
}

function outputNameForProfile(profile, image = selectedImage(), index = 1) {
  return outputProfileViewHelpers.outputNameForProfile(profile, {
    folders: activeFolders(),
    image,
    index,
  });
}

function renderOutputProfileModalState() {
  const raw = outputProfileFormRawData();
  const profile = outputProfileDraftFromForm();
  state.outputProfileDraft = profile;
  if (state.outputDeleteConfirmId && state.outputDeleteConfirmId !== profile.id) {
    state.outputDeleteConfirmId = "";
  }
  const validation = outputProfileValidation(raw);
  const dirty = outputProfileHasUnsavedChanges();
  const heading = $("#output-profile-editor-heading");
  if (heading) {
    heading.innerHTML = outputProfileEditorHeadingHtml(profile, validation, dirty);
  }
  const preview = $("#output-profile-preview");
  if (preview) {
    preview.innerHTML = outputProfilePreviewHtml(profile, validation);
  }
  const validationTarget = $("#output-profile-validation");
  if (validationTarget) {
    validationTarget.innerHTML = "";
    validationTarget.hidden = true;
  }
  updateOutputProfileFieldStates(validation, raw);
  renderBackgroundPresetControls(raw);
  updateOutputProfileFooterState(validation, dirty);
  renderOutputProfileDeleteConfirm(profile);
}

function updateOutputProfileFieldStates(validation, raw) {
  const fieldIds = {
    name: "profile-name-input",
    format: "profile-format-input",
    background: "profile-background-input",
    backgroundCustom: "profile-background-custom-input",
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
    const fieldMessages = validation.fieldMessages?.[field] || [];
    input.classList.toggle("is-invalid", tone === "error");
    input.classList.toggle("has-warning", tone === "warning");
    input.setAttribute("aria-invalid", tone === "error" ? "true" : "false");
    input.title = fieldMessages[0] || "";
  });

  $$("[data-profile-field-message]").forEach((message) => {
    const field = message.dataset.profileFieldMessage;
    const fieldMessages = validation.fieldMessages?.[field] || [];
    message.textContent = fieldMessages[0] || "";
    message.hidden = !fieldMessages.length;
    message.classList.toggle("error", validation.fields?.[field] === "error");
    message.classList.toggle("warning", validation.fields?.[field] === "warning");
  });

  const destinationInput = $("#profile-destination-input");
  if (destinationInput) {
    destinationInput.placeholder = raw.destinationMode === "custom"
      ? "Ej. C:\\Exports\\FlatShot"
      : "Salida";
  }
  const destinationLabel = $("#profile-destination-value-label");
  if (destinationLabel) {
    destinationLabel.textContent = raw.destinationMode === "custom" ? "Carpeta" : "Subcarpeta";
  }
  const destinationPickButton = $("[data-action='pick-output-profile-destination']");
  if (destinationPickButton) {
    destinationPickButton.hidden = raw.destinationMode !== "custom";
    destinationPickButton.disabled = state.bridgeStatus === "checking";
    destinationPickButton.title = raw.destinationMode === "custom"
      ? "Elegir carpeta de salida"
      : "Disponible con carpeta personalizada";
  }
}

function updateOutputProfileFooterState(validation, dirty) {
  const draft = ensureOutputProfileDraft();
  const isPersisted = state.outputProfiles.some((profile) => profile.id === draft.id);
  const footerState = outputProfileViewHelpers.outputProfileFooterState({
    draft,
    dirty,
    isPersisted,
    changeCount: outputProfileChangeCount(),
    noticeText: state.outputProfileNotice,
    profileCount: state.outputProfiles.length,
    validation,
  });
  const deleteButton = $("[data-action='delete-output-profile']");
  if (deleteButton) {
    const deleteConfirmOpen = state.outputDeleteConfirmId === draft.id;
    deleteButton.disabled = footerState.deleteDisabled || deleteConfirmOpen;
    deleteButton.title = deleteConfirmOpen ? "Confirma o cancela la eliminación" : footerState.deleteTitle;
    deleteButton.setAttribute("aria-expanded", deleteConfirmOpen ? "true" : "false");
  }
  $$("[data-output-profile-reset]").forEach((resetButton) => {
    resetButton.disabled = footerState.resetDisabled;
    resetButton.textContent = footerState.resetLabel;
    if (resetButton.closest(".app-settings-footer")) {
      resetButton.dataset.action = "reset-output-profile-draft";
      resetButton.hidden = footerState.resetHidden;
    }
  });
  const saveButton = $("[data-output-profile-save]");
  if (saveButton) {
    saveButton.disabled = footerState.saveDisabled;
    saveButton.hidden = footerState.saveHidden;
    saveButton.textContent = footerState.saveLabel;
    saveButton.dataset.action = "save-output-profile";
  }
  const closeButton = $("[data-output-profile-close]");
  if (closeButton) {
    closeButton.textContent = footerState.closeLabel;
    closeButton.dataset.action = footerState.closeAction;
    closeButton.hidden = footerState.closeHidden;
  }
  const footerNote = $("#output-profile-unsaved");
  if (footerNote) {
    footerNote.textContent = footerState.noteText;
    footerNote.className = footerState.noteClass;
  }
}

function renderOutputProfileDeleteConfirm(profile) {
  const panel = $("#output-delete-confirm");
  if (!panel) {
    return;
  }
  const isOpen = Boolean(profile?.id && state.outputDeleteConfirmId === profile.id);
  panel.hidden = !isOpen;
  panel.setAttribute("aria-hidden", isOpen ? "false" : "true");
  const footer = panel.closest(".app-settings-footer");
  if (footer) {
    footer.classList.toggle("is-confirming-delete", isOpen);
  }

  const detail = $("#output-delete-confirm-detail");
  if (detail) {
    detail.textContent = isOpen
      ? `Se eliminará "${profile.name}" de los formatos guardados. No se tocarán imágenes ni exportaciones anteriores.`
      : "";
  }

  const confirmButton = panel.querySelector("[data-action='confirm-output-delete']");
  if (confirmButton) {
    confirmButton.disabled = !isOpen;
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
  const profileCount = $("#output-profile-count");
  if (profileCount) {
    profileCount.textContent = `${enabledOutputProfiles().length} activos`;
  }
  const draftDirty = outputProfileHasUnsavedChanges();
  $("#output-profile-list").innerHTML = rows.map((profile) => {
    const selected = profile.id === draft?.id;
    const enabled = profile.enabled;
    const unsaved = !state.outputProfiles.some((item) => item.id === profile.id);
    const dirty = selected && draftDirty;
    const canToggle = !unsaved;
    return outputProfileViewHelpers.outputProfileManagerRowHtml({
      profile,
      selected,
      enabled,
      dirty,
      new: unsaved,
      unsaved,
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
      reasonLabel: batchViewHelpers.omissionReasonLabel(item.reason),
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
    existingOutput: preflightHelpers.issueMentionsExistingOutput(issue),
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
  if (!profiles.length) {
    return "Sin formato activo";
  }
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
  state.statusText = "Editando formato";
  render();
}

function applyOutputEdit() {
  state.outputDraft = null;
  state.outputEditMode = false;
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = "Formato aplicado al lote";
  persistExportPreferences();
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
  persistExportPreferences();
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
      enabled: Boolean(state.outputProfiles[index].enabled),
    };
  }
  state.outputProfiles = outputProfileHelpers.normalizeOutputProfileList(state.outputProfiles, state.activeOutputProfileId);
  state.outputDraft = null;
  state.outputEditMode = false;
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = "Formato de salida guardado";
  persistOutputProfiles();
  render();
}

function saveCurrentOutputAsNewProfile() {
  const sourceName = activeOutputProfile()?.name || "Formato";
  const name = window.prompt("Nombre del nuevo formato de salida", `${sourceName} copia`);
  if (name === null) {
    return;
  }
  const profile = outputProfileHelpers.normalizeOutputProfile({
    ...currentOutputProfileData(),
    id: outputProfileHelpers.uniqueOutputProfileId(name || "formato", Date.now()),
    name: name.trim() || "Nuevo formato",
    enabled: true,
  });
  state.outputProfiles = outputProfileHelpers.normalizeOutputProfileList([...state.outputProfiles, profile], profile.id);
  state.activeOutputProfileId = profile.id;
  state.outputProfileEditorId = profile.id;
  state.outputProfileDraft = { ...profile };
  state.outputDraft = null;
  state.outputEditMode = false;
  persistOutputProfiles();
  state.statusText = `Nuevo formato: ${profile.name}`;
  render();
}

function discardOutputOverrides() {
  const profile = activeOutputProfile();
  if (!profile) {
    return;
  }
  state.outputDraft = null;
  state.outputEditMode = false;
  applyOutputProfile(profile.id, { statusText: "Cambios sin guardar descartados" });
}

async function saveCurrentPreset() {
  const presetName = state.activePreset;
  const presetSettings = normalizeSettings(state.settings);

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
  state.presetSource = "Global";
  persistImageAdjustmentSelection();
  state.outputDraft = null;
  state.outputEditMode = false;
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = "Ajuste guardado";
  render();
}

async function saveAdjustmentAsNew(settings, options = {}) {
  const fallbackName = options.defaultName || `${state.activePreset || "Ajuste"} copia`;
  const name = window.prompt("Nombre del nuevo ajuste de imagen", fallbackName);
  if (name === null) {
    return;
  }
  const presetName = name.trim() || "Nuevo ajuste";
  const presetSettings = normalizeSettings(settings);

  if (state.bridgeMode === "bridge") {
    state.statusText = "Guardando nuevo ajuste";
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
      state.statusText = `No se pudo guardar el ajuste: ${bridgeErrorMessage(error)}`;
      render();
      return;
    }
  }

  updatePresetCache(presetName, presetSettings);
  state.activePreset = presetName;
  state.settings = presetSettings;
  state.presetDirty = false;
  state.presetSource = "Global";
  state.presetEditorOpen = false;
  persistImageAdjustmentSelection();
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = options.statusText || `Nuevo ajuste: ${presetName}`;
  render();
}

function saveCurrentPresetAsNew() {
  void saveAdjustmentAsNew(state.settings, {
    defaultName: `${state.activePreset || "Ajuste"} copia`,
    statusText: "Ajuste guardado como nuevo",
  });
}

function saveCurrentLocalAdjustmentAsNew() {
  const image = selectedImage();
  if (!image) {
    return;
  }
  void saveAdjustmentAsNew(settingsWithLocalOverride(state.settings, currentImageOverride(image)), {
    defaultName: `${state.activePreset || "Ajuste"} personalizado`,
    statusText: "Ajuste de imagen guardado como nuevo",
  });
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
  pendingAdvancedDisclosure = "appearance-section";
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
  setControlHint($("[data-action='open-app-settings']"), "Abrir formatos de salida");
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
    [SOFT_BLACK_PREVIEW_BG]: "Fondo negro suave RGB 32, 34, 37",
    transparent: "Fondo transparente",
    custom: "Fondo personalizado con los campos RGB",
  };
  $$("[data-preview-bg]").forEach((button) => {
    setControlHint(button, backgroundHints[button.dataset.previewBg] || button.textContent.trim());
    button.setAttribute("aria-pressed", button.classList.contains("active") ? "true" : "false");
  });

  const zoomHints = {
    "previous-image": "Imagen anterior. Atajo: flecha izquierda",
    "next-image": "Imagen siguiente. Atajo: flecha derecha",
    "zoom-height": "Ajustar a la altura del visor",
    "zoom-width": "Ajustar a la anchura del visor",
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

const actionDispatcher = actionHandlerHelpers.createActionDispatcher({
  "load-batch": () => loadBatch(),
  "load-mock-batch": () => loadMockBatch(),
  "check-bridge": () => { void checkBridge(); },
  "toggle-inspector": () => {
    state.inspectorCollapsed = !state.inspectorCollapsed;
    state.statusText = state.inspectorCollapsed ? "Inspector oculto" : "Inspector visible";
    render();
  },
  "pick-bridge-folder": () => { void pickBridgeFolder(); },
  "pick-output-profile-destination": () => { void pickOutputProfileDestination(); },
  "scan-bridge-folder": () => { void scanBridgeFolder(); },
  "clear-batch": () => clearBatch(),
  "show-empty-folder": () => showEmptyFolder(),
  "force-preview-error": () => {
    if (hasBatch()) {
      state.previewStatus = "error";
      state.statusText = "Vista no disponible";
      render();
    }
  },
  "previous-image": () => selectAdjacentImage(-1),
  "next-image": () => selectAdjacentImage(1),
  "clear-filter": () => clearFilter(),
  "clear-search": () => {
    state.search = "";
    state.statusText = galleryHelpers.filterStatusText(state.filter);
    if (!ensureGallerySelectionForFilter()) {
      render();
    }
  },
  "select-first-image": () => {
    const image = filteredImages()[0] || activeImages()[0];
    if (image) {
      selectImage(image.id);
    }
  },
  "select-image-id": (target) => {
    const imageId = target?.dataset?.imageId;
    if (imageId) {
      state.inspectorTab = "review";
      selectImage(imageId);
    }
  },
  "open-advanced": () => {
    state.inspectorTab = "advanced";
    pendingAdvancedDisclosure = "appearance-section";
    state.statusText = "Ajustes";
    render();
  },
  "open-image-adjustment": () => {
    state.inspectorTab = "advanced";
    state.presetEditorOpen = false;
    pendingAdvancedDisclosure = "local-adjustment";
    state.statusText = "Ajuste de esta imagen";
    render();
  },
  "apply-global-adjustment-to-overrides": () => resetAllImageOverrides(),
  "close-inspector-subview": () => {
    state.inspectorTab = "review";
    state.statusText = getVisibleAppState().nextStep || state.statusText;
    render();
  },
  "edit-output": () => beginOutputEdit(),
  "select-output-profile": (target) => {
    const profileId = target?.dataset?.outputProfileId;
    if (profileId) {
      applyOutputProfile(profileId);
    }
  },
  "apply-output-edit": () => applyOutputEdit(),
  "cancel-output-edit": () => cancelOutputEdit(),
  "save-output-current-profile": () => saveCurrentOutputProfile(),
  "save-output-as-new": () => saveCurrentOutputAsNewProfile(),
  "discard-output-overrides": () => discardOutputOverrides(),
  "open-app-settings": () => openAppSettings(),
  "close-app-settings": () => closeAppSettings(),
  "cancel-output-profile-draft": () => cancelOutputProfileDraft(),
  "open-batch-detail": () => openBatchDetail(),
  "close-batch-detail": () => closeBatchDetail(),
  "cancel-export-confirm": () => closeExportConfirm(),
  "confirm-export": () => confirmExportFromModal(),
  "new-output-profile": () => newOutputProfile(),
  "duplicate-output-profile": () => duplicateOutputProfile(),
  "reset-output-profile-draft": () => resetOutputProfileDraft(),
  "delete-output-profile": () => deleteManagedOutputProfile(),
  "cancel-output-delete": () => cancelDeleteManagedOutputProfile(),
  "confirm-output-delete": () => confirmDeleteManagedOutputProfile(),
  "save-output-profile": () => saveOutputProfile(),
  "edit-background-preset": () => beginBackgroundPresetEdit("edit"),
  "new-background-preset": () => beginBackgroundPresetEdit("new"),
  "delete-background-preset": () => deleteBackgroundPreset(),
  "save-background-preset": () => saveBackgroundPreset(),
  "cancel-background-preset-edit": () => {
    state.backgroundPresetEditor = null;
    renderOutputProfileModalState();
  },
  "open-preset-editor": () => openPresetEditor(),
  "close-preset-editor": () => closePresetEditor(),
  "zoom-height": () => setViewerMode("height"),
  "zoom-width": () => setViewerMode("width"),
  "zoom-in": () => setViewerZoom(Math.round(currentViewerZoom() / 10) * 10 + 10),
  "zoom-out": () => setViewerZoom(Math.round(currentViewerZoom() / 10) * 10 - 10),
  "reset-settings": () => resetActivePresetSettings(),
  "cancel-adjustment-edit": () => cancelAdjustmentEdit(),
  "apply-global-adjustment": () => applyGlobalAdjustmentWithoutSaving(),
  "save-preset": () => { void saveCurrentPreset(); },
  "save-preset-as-new": () => saveCurrentPresetAsNew(),
  "apply-local-adjustment": () => applyLocalAdjustmentOnly(),
  "save-local-adjustment-as-new": () => saveCurrentLocalAdjustmentAsNew(),
  "export-presets": () => exportPresetCollection(),
  "delete-preset": () => { void deleteActivePreset(); },
  "toggle-local-adjustment": () => {
    state.localOverride = !state.localOverride;
    state.statusText = state.localOverride ? "Ajuste personalizado" : "Igual que el lote";
    render();
  },
  "reset-local-adjustment": () => resetCurrentImageOverride(),
  "pause-export": () => pauseExport(),
  "stop-export": () => stopExport(),
  "start-export": () => startExport(),
  "review-errors": () => reviewWarnings(),
  "review-warnings": () => reviewWarnings(),
  "review-output": () => beginOutputEdit(),
  "open-output": () => openOutputFolder(),
  "primary": () => primaryAction(),
  "secondary-primary": () => runVisibleAction(getVisibleAppState().secondaryAction?.action),
});

function handleAction(action, target = null) {
  actionDispatcher(action, target);
}

function closeTransientDetails(event) {
  const target = event.target;
  document.querySelectorAll("details.format-more-menu[open], details.debug-panel[open]").forEach((details) => {
    if (!details.contains(target)) {
      details.open = false;
    }
  });
}

function handleDocumentImageLoad(event) {
  const target = event.target;
  if (target instanceof HTMLImageElement && target.classList.contains("thumb-image")) {
    recordThumbnailLoad(target);
  }
  if (target instanceof HTMLImageElement && target.classList.contains("preview-image")) {
    updatePreviewDebugPanel();
  }
}

function handleDocumentImageError(event) {
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
}

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

function handleDocumentPointerDown(event) {
  if (event.target.closest?.(".settings-panel details > summary")) {
    inspectorScrollTopBeforeToggle = $(".settings-panel")?.scrollTop || 0;
  }
}

function handleInspectorDisclosureClick(event) {
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
}

function handleDocumentClick(event) {
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
    state.previewBg = normalizePreviewBackgroundValue(
      bgTarget.dataset.previewBg === "custom" ? previewCustomBackgroundValue() : bgTarget.dataset.previewBg
    );
    state.statusText = `Fondo: ${previewBackgroundLabel(state.previewBg)}`;
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
}

function handleDocumentToggle(event) {
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
}

function handleDemoScenarioChange(event) {
  if (!devMode) {
    return;
  }
  state.bridgeMode = "mock";
  state.bridgeLastResponse = `Estado mock: ${scenarioLabels[event.target.value] || event.target.value}`;
  setScenario(event.target.value);
}

function handleAppModeChange(event) {
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
}

function handleBridgeUrlInput(event) {
  state.bridgeUrl = event.target.value || defaultBridgeUrl;
  state.bridgeStatus = "idle";
  state.bridgeMessage = "Comprueba conexión";
  state.bridgeLastResponse = "URL pendiente";
  state.scanStatus = "Comprueba bridge";
  render();
}

function handleBridgeScanPathInput(event) {
  state.bridgeScanPath = event.target.value;
}

function handleDocumentInput(event) {
  if (event.target?.matches?.("input[type='range']")) {
    syncRangeFill(event.target);
  }
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
  if (event.target.closest?.("#background-preset-editor")) {
    updateBackgroundPresetEditorFromFields();
    return;
  }
  if (event.target.closest?.("#output-profile-form")) {
    updateOutputProfileDraftFromForm();
    renderOutputProfileModalState();
  }
}

function handleDocumentChange(event) {
  if (event.target.matches?.("[data-preview-bg-channel]")) {
    state.previewBg = normalizePreviewBackgroundValue(previewCustomBackgroundValue());
    state.statusText = `Fondo: ${previewBackgroundLabel(state.previewBg)}`;
    render();
    return;
  }
  if (event.target?.id === "gallery-output-select") {
    if (event.target.value !== "__custom") {
      applyOutputProfile(event.target.value);
    }
    return;
  }
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
  if (event.target.matches?.("[data-output-profile-draft-enabled]")) {
    setOutputProfileDraftEnabled(event.target.checked);
    return;
  }
  if (event.target.closest?.("#background-preset-editor")) {
    updateBackgroundPresetEditorFromFields();
    renderBackgroundPresetControls();
    return;
  }
  if (event.target.matches?.("[data-image-adjustment-select]")) {
    applyPresetSettings(event.target.value);
    return;
  }
  if (event.target.closest?.("#output-profile-form")) {
    updateOutputProfileDraftFromForm();
    renderOutputProfileModalState();
  }
}

function handleDocumentSubmit(event) {
  if (event.target.id === "output-profile-form") {
    event.preventDefault();
    saveOutputProfile();
  }
}

function handleImageSearchInput(event) {
  state.search = event.target.value;
  if (ensureGallerySelectionForFilter()) {
    return;
  }
  render();
}

function handleSettingInput(event) {
  const key = event.target.dataset.setting;
  const nextValue = settingInputValue(event.target);
  if (state.settings[key] === nextValue) {
    return;
  }
  state.settings[key] = nextValue;
  markPresetDirty();
}

function handleLightingFieldInput(event) {
  updateLightingSceneField(event.target.dataset.lightingField, event.target.value);
}

function handleLightingNumberFieldInput(event) {
  updateLightingSceneField(event.target.dataset.lightingNumberField, event.target.value);
}

function handleLightingPresetClick(button) {
  const presetId = button.dataset.lightingPreset;
  const preset = lightingScenePresets[presetId];
  if (!preset) {
    return;
  }
  state.settings.shadow_engine = "studio_2_5d";
  state.settings.lighting_scene = cloneLightingScene(preset);
  state.lightingPresetId = presetId;
  markPresetDirty();
}

function settingInputValue(input) {
  if (input.type === "checkbox") {
    return input.checked;
  }
  if (input.tagName === "SELECT") {
    return input.value;
  }
  return Number(input.value);
}

function updateLightingSceneField(field, rawValue) {
  const scene = cloneLightingScene(state.settings.lighting_scene);
  if (field === "main.type") {
    scene.main.type = ["softbox", "spot", "strip"].includes(rawValue) ? rawValue : scene.main.type;
  } else if (field === "main.height") {
    scene.main.height = numberHelpers.roundedSceneValue(Number(rawValue) / 100, 0, 1, scene.main.height);
  } else if (field === "main.size") {
    scene.main.size = numberHelpers.roundedSceneValue(Number(rawValue) / 100, 0, 1, scene.main.size);
  } else if (field === "main.intensity") {
    scene.main.intensity = numberHelpers.roundedSceneValue(Number(rawValue) / 100, 0, 1.5, scene.main.intensity);
  } else if (field === "ambient_intensity") {
    scene.ambient_intensity = numberHelpers.roundedSceneValue(Number(rawValue) / 100, 0, 1, scene.ambient_intensity);
  } else {
    return;
  }
  if (lightingScenesEqual(scene, state.settings.lighting_scene)) {
    return;
  }
  state.settings.lighting_scene = scene;
  markPresetDirty();
}

function updateLightingScenePosition(clientX, clientY, options = {}) {
  const stage = $("#lighting-stage");
  if (!stage || state.settings.shadow_engine !== "studio_2_5d") {
    return false;
  }
  const rect = stage.getBoundingClientRect();
  if (!rect.width || !rect.height) {
    return false;
  }
  const x = numberHelpers.roundedSceneValue(((clientX - rect.left) / rect.width) * 2 - 1, -1, 1, defaultLightingScene.main.x);
  const y = numberHelpers.roundedSceneValue(((clientY - rect.top) / rect.height) * 2 - 1, -1, 1, defaultLightingScene.main.y);
  const scene = cloneLightingScene(state.settings.lighting_scene);
  if (scene.main.x === x && scene.main.y === y) {
    return false;
  }
  scene.main.x = x;
  scene.main.y = y;
  state.settings.lighting_scene = scene;
  markPresetDirty({ deferRender: options.deferRender });
  if (options.deferRender) {
    renderLightingSceneControls();
  }
  return true;
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
    syncRangeFill(range);
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
    syncRangeFill(range);
  }
  setCurrentImageOverrideValue(key, value);
}

function handleFormatSelectChange(event) {
  state.format = outputProfileHelpers.normalizeExportFormat(event.target.value);
  state.statusText = `Formato: ${state.format}`;
  persistExportPreferences();
  render();
}

function handleOutputProfileSelectChange(event) {
  if (event.target.value === "__custom") {
    return;
  }
  applyOutputProfile(event.target.value);
}

function handleSizeSelectInput(event) {
  state.size = event.target.value;
}

function handleSizeSelectChange(event) {
  state.size = outputProfileHelpers.parseOutputSize(event.target.value).normalized;
  state.statusText = `Tamaño: ${state.size}`;
  persistExportPreferences();
  const image = selectedImage();
  if (image?.source === "bridge") {
    void requestBridgePreview(image);
    return;
  }
  render();
}

function handleBackgroundSelectChange(event) {
  state.background = outputProfileHelpers.normalizeBackgroundValue(event.target.value, state.background);
  state.previewBg = state.background;
  state.statusText = `Fondo: ${settingsViewHelpers.backgroundLabel(state.background)}`;
  persistExportPreferences();
  const image = selectedImage();
  if (image?.source === "bridge") {
    void requestBridgePreview(image);
    return;
  }
  render();
}

function handleDestinationModeChange(event) {
  state.destinationMode = event.target.value;
  state.destinationValue = state.destinationMode === "custom" ? "" : "Salida";
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = state.destinationMode === "custom" ? "Carpeta de salida sin configurar" : "Destino junto al origen";
  persistExportPreferences();
  render();
}

function handleDestinationInput(event) {
  state.destinationValue = event.target.value;
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = state.destinationValue.trim() ? "Carpeta de salida configurada" : "Carpeta de salida sin configurar";
  persistExportPreferences();
  render();
}

function handleNamingInput(event) {
  state.naming = event.target.value;
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = state.naming.trim() ? "Nombre de archivo actualizado" : "Nombre de archivo vacío";
  persistExportPreferences();
  render();
}

function handleDocumentKeydown(event) {
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
  }
}

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
  if (!canViewerPan()) {
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

function handleViewerDoubleClick(event) {
  if (event.target.closest("button, input, textarea, select, summary, a")) {
    return;
  }
  event.preventDefault();
  toggleViewerZoomMode();
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
  state.scanStatus = `Última carpeta: ${formatterHelpers.basename(path)}`;
  state.statusText = "Restaurando último lote";
  render();
  void scanBridgeFolder();
}

function startFlatShotApp() {
  const restoredSessionSnapshot = restoreSessionSnapshot();
  sessionSnapshotPersistenceEnabled = true;
  if (restoredSessionSnapshot) {
    render();
    return;
  }
  setScenario("initial");
  void restoreBridgeUiPreferences({ skipSessionSnapshot: true });
  restorePersistentBridgeSession();
}

interactionBindingHelpers.wireFlatShotInteractions({
  document,
  window,
  $,
  $$,
  handlers: {
    appModeChange: handleAppModeChange,
    backgroundSelectChange: handleBackgroundSelectChange,
    bridgeScanPathInput: handleBridgeScanPathInput,
    bridgeUrlInput: handleBridgeUrlInput,
    demoScenarioChange: handleDemoScenarioChange,
    destinationInput: handleDestinationInput,
    destinationModeChange: handleDestinationModeChange,
    documentChange: handleDocumentChange,
    documentClick: handleDocumentClick,
    documentError: handleDocumentImageError,
    documentInput: handleDocumentInput,
    documentKeydown: handleDocumentKeydown,
    documentLoad: handleDocumentImageLoad,
    documentPointerDown: handleDocumentPointerDown,
    documentSubmit: handleDocumentSubmit,
    documentToggle: handleDocumentToggle,
    formatSelectChange: handleFormatSelectChange,
    imageSearchInput: handleImageSearchInput,
    initViewerResizeObserver,
    inspectorDisclosureClick: handleInspectorDisclosureClick,
    lightingFieldInput: handleLightingFieldInput,
    lightingNumberFieldInput: handleLightingNumberFieldInput,
    lightingPresetClick: handleLightingPresetClick,
    namingInput: handleNamingInput,
    outputProfileSelectChange: handleOutputProfileSelectChange,
    positionBackgroundPresetEditor,
    refreshPreviewAfterSettingChange,
    settingInput: handleSettingInput,
    sizeSelectChange: handleSizeSelectChange,
    sizeSelectInput: handleSizeSelectInput,
    startup: startFlatShotApp,
    updateLightingScenePosition,
    viewerDoubleClick: handleViewerDoubleClick,
    viewerPointerDown: handleViewerPointerDown,
    viewerPointerEnd: handleViewerPointerEnd,
    viewerPointerMove: handleViewerPointerMove,
    viewerWheel: handleViewerWheel,
    writeSessionSnapshot,
  },
});
