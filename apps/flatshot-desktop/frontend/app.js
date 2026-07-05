const initialImageAdjustmentPreset = storageHelpers.readValue(window.localStorage, STORAGE_KEYS.imageAdjustmentPreset) || "Luz cenital";
const initialOutputProfileId = storageHelpers.readValue(window.localStorage, STORAGE_KEYS.activeOutputProfile);
const initialExportPreferences = storageHelpers.readJson(window.localStorage, STORAGE_KEYS.exportPreferences, {});
const initialBackgroundPresets = backgroundPresetHelpers.readBackgroundPresets(window.localStorage, STORAGE_KEYS.backgroundPresets, {
  defaultPresets: defaultBackgroundPresets,
  outputProfileHelpers,
  storageHelpers,
});
const initialGuideSystems = guideHelpers.readGuideSystems(window.localStorage, STORAGE_KEYS.guideSystems, {
  storageHelpers,
});
const initialActiveGuideSystemIds = guideHelpers.normalizeActiveGuideSystemIds(
  storageHelpers.readJson(window.localStorage, STORAGE_KEYS.activeGuideSystems, ["center"]),
  initialGuideSystems
);
const initialGuideSystemOrderIds = guideHelpers.normalizeGuideSystemOrderIds(
  storageHelpers.readJson(window.localStorage, STORAGE_KEYS.guideSystemOrder, []),
  initialGuideSystems
);
const initialHiddenGuideSystemIds = guideHelpers.normalizeHiddenGuideSystemIds(
  storageHelpers.readJson(window.localStorage, STORAGE_KEYS.hiddenGuideSystems, []),
  initialGuideSystems
);
const initialGuidesVisible = storageHelpers.readValue(window.localStorage, STORAGE_KEYS.guidesVisible) !== "0";
const initialThemePreference = themeHelpers.readThemePreference(window.localStorage, STORAGE_KEYS.theme);
const initialTheme = themeHelpers.resolveThemePreference(initialThemePreference, window);
const initialBrandTone = themeHelpers.readBrandTonePreference(window.localStorage, STORAGE_KEYS.brandTone);
const initialInterfacePreferences = interfacePreferenceHelpers.readInterfacePreferences(window.localStorage, STORAGE_KEYS.interfacePreferences);
const initialStartupAdjustment = interfacePreferenceHelpers.startupAdjustmentPreference(initialInterfacePreferences);
themeHelpers.applyTheme(document, initialTheme);
themeHelpers.applyBrandTone(document, initialBrandTone);
interfacePreferenceHelpers.applyInterfacePreferences(document, initialInterfacePreferences);
const initialRecentFolders = recentFolderHelpers.readRecentFolders(window.localStorage, STORAGE_KEYS.recentFolders);
const initialExportHistory = exportHistoryHelpers.readExportHistory(window.localStorage, STORAGE_KEYS.exportHistory);
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
  themePreference: initialThemePreference,
  theme: initialTheme,
  brandTone: initialBrandTone,
  interfacePreferences: initialInterfacePreferences,
  batch: "none",
  batchSource: "none",
  selectedImageId: null,
  selectedImageIds: [],
  selectionAnchorImageId: null,
  previewStatus: "empty",
  previewRequestId: 0,
  previewData: null,
  previewError: "",
  thumbnailStatus: {},
  thumbnailErrors: [],
  previewMode: "processed",
  compareSplit: 50,
  previewBg: initialBackground,
  guidesVisible: initialGuidesVisible,
  activeGuideSystemIds: initialActiveGuideSystemIds,
  guideSystemOrderIds: initialGuideSystemOrderIds,
  hiddenGuideSystemIds: initialHiddenGuideSystemIds,
  guideSystems: initialGuideSystems,
  guideManagerOpen: false,
  selectedGuideSystemId: null,
  guideDraft: null,
  zoom: 100,
  fitZoom: 100,
  fitMode: DEFAULT_VIEW_MODE,
  panX: 0,
  panY: 0,
  filter: "all",
  search: "",
  galleryView: "thumbs",
  galleryScrollTop: 0,
  inspectorTab: "review",
  inspectorCollapsed: false,
  responsiveInspectorOpen: false,
  advancedDisclosureKey: "",
  outputEditMode: false,
  presetEditorOpen: false,
  activePreset: initialStartupAdjustment?.name || initialImageAdjustmentPreset,
  presetOutputSettings: {},
  settings: normalizeSettings(initialStartupAdjustment?.settings || defaultSettings),
  lightingPresetId: "",
  presetDirty: Boolean(initialStartupAdjustment),
  presetSource: initialStartupAdjustment ? "Preferencias" : "Global",
  localOverride: false,
  exportStatus: "blocked",
  exportJobId: null,
  exportDestinations: [],
  exportMessages: [],
  exportCompletedItems: [],
  exportFailedItems: [],
  exportIssues: [],
  exportResult: null,
  exportHistory: initialExportHistory,
  exportHistoryRecordedJobId: "",
  exportPollTimer: null,
  outputDraft: null,
  appSettingsOpen: false,
  preferencesOpen: false,
  batchDetailOpen: false,
  exportConfirmOpen: false,
  qaLabOpen: false,
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
  bridgeToken: initialBridgeToken,
  bridgeStatus: "idle",
  bridgeMessage: "Sin lote",
  bridgeLastResponse: "Bridge pendiente",
  bridgeCapabilitiesSummary: "Sin comprobar",
  bridgeCapabilities: null,
  bridgePresets: [],
  bridgePresetSource: "unavailable",
  bridgePresetWarning: "",
  bridgeScanPath: storageHelpers.readValue(window.localStorage, STORAGE_KEYS.bridgeScanPath),
  scanJobId: null,
  scanRecursive: false,
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
  recentFolders: initialRecentFolders,
  folderDropActive: false,
  folderDropMessage: "",
  adjustmentHistory: adjustmentHistoryHelpers.createAdjustmentHistory({ limit: 50 }),
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
let galleryScrollFrame = 0;
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
const compareDividerDrag = {
  active: false,
  pointerId: null,
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));
