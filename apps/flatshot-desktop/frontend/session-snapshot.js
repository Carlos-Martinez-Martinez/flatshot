(function (root, factory) {
  const api = factory(root);
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotSessionSnapshot = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const SESSION_STATE_KEYS = [
    "batch",
    "batchSource",
    "selectedImageId",
    "previewMode",
    "previewBg",
    "guidesVisible",
    "activeGuideSystemIds",
    "guideSystems",
    "zoom",
    "fitZoom",
    "fitMode",
    "panX",
    "panY",
    "filter",
    "search",
    "galleryView",
    "inspectorTab",
    "inspectorCollapsed",
    "activePreset",
    "presetOutputSettings",
    "settings",
    "presetDirty",
    "presetSource",
    "localOverride",
    "outputProfiles",
    "backgroundPresets",
    "activeOutputProfileId",
    "outputProfileEditorId",
    "outputProfileDraft",
    "destinationMode",
    "destinationValue",
    "format",
    "size",
    "background",
    "naming",
    "suffix",
    "maxFileSizeKb",
    "appSettingsOpen",
    "batchDetailOpen",
    "bridgeMode",
    "bridgeUrl",
    "bridgeStatus",
    "bridgeMessage",
    "bridgeLastResponse",
    "bridgeCapabilitiesSummary",
    "bridgeCapabilities",
    "bridgePresets",
    "bridgePresetSource",
    "bridgePresetWarning",
    "bridgeScanPath",
    "scanStatus",
    "scanIssues",
    "scanDiagnostics",
    "realFolders",
    "realImages",
    "imageOverrides",
  ];

  function safeObject(value) {
    return value && typeof value === "object" && !Array.isArray(value) ? value : {};
  }

  function isSessionSnapshot(snapshot) {
    return snapshot?.version === 1 && snapshot.state && typeof snapshot.state === "object";
  }

  function readSessionSnapshot(storage, key, storageHelpers) {
    const snapshot = storageHelpers.readJson(storage, key, null);
    return isSessionSnapshot(snapshot) ? snapshot : null;
  }

  function writeSessionSnapshot(storage, key, snapshot, storageHelpers) {
    storageHelpers.writeJson(storage, key, snapshot);
  }

  function buildSessionSnapshot(options = {}) {
    const state = safeObject(options.state);
    const snapshotState = {};
    SESSION_STATE_KEYS.forEach((key) => {
      snapshotState[key] = state[key];
    });
    snapshotState.selectedImagePath = options.selectedImagePath || options.fallbackSelectedImagePath || "";
    return {
      version: 1,
      savedAt: options.savedAt || Date.now(),
      state: snapshotState,
    };
  }

  function restoreSessionState(restoredInput = {}, options = {}) {
    const restored = safeObject(restoredInput);
    const currentState = safeObject(options.currentState);
    const normalizeBackgroundPresetList = options.normalizeBackgroundPresetList || ((value) => value);
    const normalizeGuideSystemList = options.normalizeGuideSystemList || ((value) => Array.isArray(value) ? value : []);
    const normalizeActiveGuideSystemIds = options.normalizeActiveGuideSystemIds || ((ids) => Array.isArray(ids) ? ids : []);
    const normalizeOutputProfileList = options.normalizeOutputProfileList || ((value) => value);
    const normalizePreviewBackgroundValue = options.normalizePreviewBackgroundValue || ((value) => value || "rgb230");
    const normalizeSettings = options.normalizeSettings || ((value) => value);
    const normalizePresetItem = options.normalizePresetItem || ((item) => item);
    const normalizeBridgeIssue = options.normalizeBridgeIssue || ((issue) => issue);
    const normalizeExportFormat = options.normalizeExportFormat || ((value) => value || "JPG");
    const parseOutputSize = options.parseOutputSize || ((value) => ({ normalized: value || "1800x2400" }));
    const normalizeBackgroundValue = options.normalizeBackgroundValue || ((value) => value || "rgb230");
    const clampNumber = options.clampNumber || ((value, min, max, fallback) => {
      const numeric = Number(value);
      return Number.isFinite(numeric) ? Math.max(min, Math.min(max, numeric)) : fallback;
    });
    const resolveRuntimeBridgeUrl = options.resolveRuntimeBridgeUrl || ((input) => input.restoredBridgeUrl || input.currentBridgeUrl || input.defaultBridgeUrl);
    const emptyScanDiagnostics = options.emptyScanDiagnostics || (() => ({
      totalFiles: 0,
      totalImages: 0,
      totalOmitted: 0,
      omittedByReason: {},
      omitted: [],
    }));

    const restoredBackgroundPresets = normalizeBackgroundPresetList(restored.backgroundPresets || currentState.backgroundPresets);
    const restoredGuideSystems = normalizeGuideSystemList(restored.guideSystems || currentState.guideSystems || []);
    const restoredActiveGuideSystemIds = normalizeActiveGuideSystemIds(
      restored.activeGuideSystemIds || currentState.activeGuideSystemIds || [],
      restoredGuideSystems
    );
    const outputProfiles = Array.isArray(restored.outputProfiles)
      ? normalizeOutputProfileList(restored.outputProfiles, restored.activeOutputProfileId)
      : currentState.outputProfiles;
    const fallbackProfiles = Array.isArray(outputProfiles) ? outputProfiles : options.defaultOutputProfiles || [];
    const restoredActiveOutputProfile = fallbackProfiles.find((profile) => profile.id === restored.activeOutputProfileId && profile.enabled)
      || fallbackProfiles.find((profile) => profile.enabled)
      || null;
    const selectedPath = String(restored.selectedImagePath || "");
    const realFolders = Array.isArray(restored.realFolders) ? restored.realFolders : [];
    const realImages = Array.isArray(restored.realImages) ? restored.realImages : [];
    const batchFilters = options.batchFilters || { all: "all" };
    const viewModeLabels = options.viewModeLabels || {};
    const defaultViewMode = options.defaultViewMode || "height";

    return {
      selectedPath,
      patch: {
        batch: restored.batch === "empty" ? "empty" : realImages.length ? "ready" : "none",
        batchSource: realImages.length || restored.batch === "empty" ? "bridge" : "none",
        scenario: "initial",
        selectedImageId: null,
        previewStatus: "empty",
        previewData: null,
        previewError: "",
        previewMode: ["processed", "original", "compare"].includes(restored.previewMode) ? restored.previewMode : "processed",
        previewBg: normalizePreviewBackgroundValue(restored.previewBg || currentState.previewBg),
        guidesVisible: restored.guidesVisible === undefined ? currentState.guidesVisible !== false : Boolean(restored.guidesVisible),
        activeGuideSystemIds: restoredActiveGuideSystemIds,
        guideSystems: restoredGuideSystems,
        guideManagerOpen: false,
        guideDraft: null,
        zoom: clampNumber(restored.zoom, 25, 400, 100),
        fitZoom: clampNumber(restored.fitZoom, 25, 400, 100),
        fitMode: viewModeLabels[restored.fitMode] ? restored.fitMode : defaultViewMode,
        panX: clampNumber(restored.panX, -10000, 10000, 0),
        panY: clampNumber(restored.panY, -10000, 10000, 0),
        filter: Object.values(batchFilters).includes(restored.filter) ? restored.filter : batchFilters.all,
        search: String(restored.search || ""),
        galleryView: restored.galleryView === "list" ? "list" : "thumbs",
        inspectorTab: ["review", "output", "warnings", "advanced"].includes(restored.inspectorTab) ? restored.inspectorTab : "review",
        inspectorCollapsed: Boolean(restored.inspectorCollapsed),
        activePreset: String(restored.activePreset || currentState.activePreset),
        presetOutputSettings: safeObject(restored.presetOutputSettings),
        settings: normalizeSettings(restored.settings),
        presetDirty: Boolean(restored.presetDirty),
        presetSource: String(restored.presetSource || "Global"),
        localOverride: Boolean(restored.localOverride),
        outputProfiles: fallbackProfiles,
        backgroundPresets: restoredBackgroundPresets,
        backgroundPresetEditor: null,
        activeOutputProfileId: restoredActiveOutputProfile?.id || "",
        outputProfileEditorId: fallbackProfiles.some((profile) => profile.id === restored.outputProfileEditorId)
          ? restored.outputProfileEditorId
          : restoredActiveOutputProfile?.id || fallbackProfiles[0]?.id || "",
        outputProfileDraft: restored.outputProfileDraft && typeof restored.outputProfileDraft === "object"
          ? restored.outputProfileDraft
          : null,
        destinationMode: restored.destinationMode === "custom" ? "custom" : "source",
        destinationValue: String(restored.destinationValue || "Salida"),
        format: normalizeExportFormat(restored.format),
        size: parseOutputSize(restored.size).normalized,
        background: normalizeBackgroundValue(restored.background),
        naming: String(restored.naming || "{original}{suffix}"),
        suffix: restored.suffix === undefined || restored.suffix === null ? "_PRO" : String(restored.suffix),
        maxFileSizeKb: normalizeExportFormat(restored.format) === "JPG"
          ? (options.normalizeMaxFileSizeKb || (() => null))(restored.maxFileSizeKb)
          : null,
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
        bridgeUrl: resolveRuntimeBridgeUrl({
          currentBridgeUrl: options.initialBridgeUrl,
          restoredBridgeUrl: restored.bridgeUrl,
          defaultBridgeUrl: options.defaultBridgeUrl,
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
      },
    };
  }

  return {
    buildSessionSnapshot,
    isSessionSnapshot,
    readSessionSnapshot,
    restoreSessionState,
    safeObject,
    writeSessionSnapshot,
  };
});
