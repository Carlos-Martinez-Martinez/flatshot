function uiPreferencesPayload() {
  return {
    outputProfiles: state.outputProfiles,
    backgroundPresets: backgroundPresetHelpers.backgroundPresetsForStorage(state.backgroundPresets, backgroundPresetOptions()),
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
      maxFileSizeKb: state.format === "JPG" ? state.maxFileSizeKb : null,
    },
  };
}

function cacheUiPreferences(preferences = uiPreferencesPayload()) {
  const source = sessionSnapshotHelpers.safeObject(preferences);
  if (Array.isArray(source.outputProfiles)) {
    storageHelpers.writeJson(window.localStorage, STORAGE_KEYS.outputProfiles, source.outputProfiles);
  }
  if (Array.isArray(source.backgroundPresets)) {
    storageHelpers.writeJson(
      window.localStorage,
      STORAGE_KEYS.backgroundPresets,
      backgroundPresetHelpers.backgroundPresetsForStorage(source.backgroundPresets, backgroundPresetOptions())
    );
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
  const source = sessionSnapshotHelpers.safeObject(preferences);
  if (!Object.keys(source).length) {
    return false;
  }

  const exportPreferences = sessionSnapshotHelpers.safeObject(source.exportPreferences);
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
    state.backgroundPresets = backgroundPresetHelpers.normalizeBackgroundPresetList(source.backgroundPresets, backgroundPresetOptions());
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
  state.naming = String(exportPreferences.naming || profileForDefaults.naming || "{original}{suffix}");
  state.suffix = exportPreferences.suffix === undefined || exportPreferences.suffix === null
    ? profileForDefaults.suffix
    : String(exportPreferences.suffix);
  state.maxFileSizeKb = state.format === "JPG"
    ? outputProfileHelpers.normalizeMaxFileSizeKb(exportPreferences.maxFileSizeKb ?? profileForDefaults.maxFileSizeKb)
    : null;

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
