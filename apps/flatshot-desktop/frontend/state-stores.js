(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotAppStateStores = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const STORE_FIELDS = {
    batch: [
      "batch",
      "batchSource",
      "realFolders",
      "realImages",
      "scanDiagnostics",
      "scanIssues",
      "scanStatus",
      "scanJobId",
      "scanRecursive",
    ],
    selection: [
      "selectedImageId",
      "selectedImageIds",
      "selectionAnchorImageId",
      "filter",
      "search",
      "galleryView",
      "galleryScrollTop",
    ],
    preview: [
      "previewStatus",
      "previewRequestId",
      "previewData",
      "previewError",
      "previewMode",
      "previewBg",
      "thumbnailStatus",
      "thumbnailErrors",
      "compareSplit",
      "zoom",
      "fitZoom",
      "fitMode",
      "panX",
      "panY",
    ],
    export: [
      "exportStatus",
      "exportJobId",
      "exportDestinations",
      "exportMessages",
      "exportCompletedItems",
      "exportFailedItems",
      "exportIssues",
      "exportResult",
      "exportHistory",
      "exportPollTimer",
      "progress",
      "processed",
      "paused",
    ],
    settings: [
      "activePreset",
      "settings",
      "presetDirty",
      "presetSource",
      "localOverride",
      "imageOverrides",
      "outputProfiles",
      "activeOutputProfileId",
      "destinationMode",
      "destinationValue",
      "format",
      "size",
      "background",
      "naming",
      "suffix",
      "maxFileSizeKb",
    ],
    ui: [
      "theme",
      "themePreference",
      "brandTone",
      "interfacePreferences",
      "inspectorTab",
      "inspectorCollapsed",
      "responsiveInspectorOpen",
      "advancedDisclosureKey",
      "appSettingsOpen",
      "preferencesOpen",
      "batchDetailOpen",
      "exportConfirmOpen",
      "qaLabOpen",
      "statusText",
      "errors",
    ],
    bridge: [
      "bridgeMode",
      "bridgeUrl",
      "bridgeToken",
      "bridgeStatus",
      "bridgeMessage",
      "bridgeLastResponse",
      "bridgeCapabilitiesSummary",
      "bridgeCapabilities",
      "bridgePresets",
      "bridgePresetSource",
      "bridgePresetWarning",
      "bridgeScanPath",
    ],
  };

  function storeNames() {
    return Object.keys(STORE_FIELDS);
  }

  function stateStoreFields(name) {
    return [...(STORE_FIELDS[name] || [])];
  }

  function stateStoreSnapshot(state = {}) {
    return storeNames().reduce((snapshot, name) => {
      snapshot[name] = pickFields(state, STORE_FIELDS[name]);
      return snapshot;
    }, {});
  }

  function pickFields(state, fields) {
    return fields.reduce((store, field) => {
      if (Object.prototype.hasOwnProperty.call(state, field)) {
        store[field] = state[field];
      }
      return store;
    }, {});
  }

  return {
    stateStoreFields,
    stateStoreSnapshot,
    storeNames,
  };
});
