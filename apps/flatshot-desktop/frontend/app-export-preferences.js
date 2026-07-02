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
    maxFileSizeKb: state.format === "JPG" ? state.maxFileSizeKb : null,
  };
  storageHelpers.writeJson(window.localStorage, STORAGE_KEYS.exportPreferences, preferences);
  if (String(state.destinationValue || "").trim()) {
    storageHelpers.writeValue(window.localStorage, STORAGE_KEYS.lastOutputFolder, state.destinationValue);
  }
  if (options.saveBridge !== false) {
    scheduleBridgeUiPreferencesSave();
  }
}
