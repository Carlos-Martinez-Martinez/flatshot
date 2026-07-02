const initialImageAdjustmentPreset = storageHelpers.readValue(window.localStorage, STORAGE_KEYS.imageAdjustmentPreset) || "Luz cenital";
const initialOutputProfileId = storageHelpers.readValue(window.localStorage, STORAGE_KEYS.activeOutputProfile);
const initialExportPreferences = storageHelpers.readJson(window.localStorage, STORAGE_KEYS.exportPreferences, {});
const initialBackgroundPresets = backgroundPresetHelpers.readBackgroundPresets(window.localStorage, STORAGE_KEYS.backgroundPresets, {
  defaultPresets: defaultBackgroundPresets,
  outputProfileHelpers,
  storageHelpers,
});
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
const initialMaxFileSizeKb = initialFormat === "JPG"
  ? outputProfileHelpers.normalizeMaxFileSizeKb(initialExportPreferences.maxFileSizeKb ?? initialOutputProfile.maxFileSizeKb)
  : null;

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
  advancedDisclosureKey: "",
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
  maxFileSizeKb: initialMaxFileSizeKb,
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
let restoredSessionSnapshot = false;
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
