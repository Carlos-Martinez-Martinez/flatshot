function readSessionSnapshot() {
  return sessionSnapshotHelpers.readSessionSnapshot(window.sessionStorage, STORAGE_KEYS.sessionSnapshot, storageHelpers);
}

function writeSessionSnapshot() {
  const selected = selectedImage();
  sessionSnapshotHelpers.writeSessionSnapshot(
    window.sessionStorage,
    STORAGE_KEYS.sessionSnapshot,
    sessionSnapshotHelpers.buildSessionSnapshot({
      state,
      selectedImagePath: selected?.path,
      fallbackSelectedImagePath: storageHelpers.readValue(window.localStorage, STORAGE_KEYS.selectedImagePath),
    }),
    storageHelpers
  );
}

function restoreSessionSnapshot() {
  const snapshot = readSessionSnapshot();
  if (!snapshot) {
    return false;
  }

  const restored = sessionSnapshotHelpers.restoreSessionState(snapshot.state, {
    currentState: state,
    initialBridgeUrl,
    defaultBridgeUrl,
    defaultViewMode: DEFAULT_VIEW_MODE,
    batchFilters: BATCH_FILTERS,
    viewModeLabels: VIEW_MODE_LABELS,
    defaultOutputProfiles,
    normalizeBackgroundPresetList: (presets) => backgroundPresetHelpers.normalizeBackgroundPresetList(presets, backgroundPresetOptions()),
    normalizeOutputProfileList: outputProfileHelpers.normalizeOutputProfileList,
    normalizePreviewBackgroundValue: (value) => backgroundPresetHelpers.normalizePreviewBackgroundValue(value, backgroundHelperOptions()),
    normalizeSettings,
    normalizePresetItem,
    normalizeBridgeIssue: exportStateHelpers.normalizeBridgeIssue,
    normalizeExportFormat: outputProfileHelpers.normalizeExportFormat,
    parseOutputSize: outputProfileHelpers.parseOutputSize,
    normalizeBackgroundValue: outputProfileHelpers.normalizeBackgroundValue,
    clampNumber: numberHelpers.clampNumber,
    resolveRuntimeBridgeUrl: bridgeUrlHelpers.resolveRuntimeBridgeUrl,
    emptyScanDiagnostics,
  });
  Object.assign(state, restored.patch);

  if (state.batch === "ready") {
    const selected = restored.selectedPath
      ? state.realImages.find((image) => image.path === restored.selectedPath)
      : state.realImages.find((image) => image.id === snapshot.state.selectedImageId);
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

function backgroundHelperOptions(extra = {}) {
  return {
    outputProfileHelpers,
    softBlackPreviewBg: SOFT_BLACK_PREVIEW_BG,
    ...extra,
  };
}

function backgroundPresetOptions(extra = {}) {
  return backgroundHelperOptions({
    defaultPresets: defaultBackgroundPresets,
    ...extra,
  });
}

function previewCustomBackgroundValue() {
  const fallback = backgroundPresetHelpers.previewCustomRgbChannels(state.previewBg, backgroundHelperOptions());
  const channels = ["r", "g", "b"].map((channel, index) => {
    const input = $(`[data-preview-bg-channel="${channel}"]`);
    return input?.value ?? fallback[index];
  });
  return backgroundPresetHelpers.previewCustomBackgroundValue(channels, {
    clampNumber: numberHelpers.clampNumber,
    fallback,
  });
}

function persistBackgroundPresets() {
  storageHelpers.writeJson(window.localStorage, STORAGE_KEYS.backgroundPresets, state.backgroundPresets);
  scheduleBridgeUiPreferencesSave();
}

function backgroundPresetById(presetId) {
  return state.backgroundPresets.find((preset) => preset.id === presetId) || null;
}

function backgroundPresetByValue(value) {
  return backgroundPresetHelpers.backgroundPresetByValue(value, state.backgroundPresets, { outputProfileHelpers });
}

function backgroundSelectOptionsHtml(selectedValue) {
  return backgroundPresetHelpers.backgroundSelectOptionsHtml(selectedValue, {
    backgroundLabel: settingsViewHelpers.backgroundLabel,
    escapeHtml,
    outputProfileHelpers,
    presets: state.backgroundPresets,
  });
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
  const source = sessionSnapshotHelpers.safeObject(preferences);
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
  return appStateHelpers.selectedImage(state, { mockImages });
}

function hasBatch() {
  return appStateHelpers.hasBatch(state);
}

function isBridgeBatch() {
  return appStateHelpers.isBridgeBatch(state);
}

function isMockBatch() {
  return appStateHelpers.isMockBatch(state);
}

function activeImages() {
  return appStateHelpers.activeImages(state, { mockImages });
}

function activeFolders() {
  return appStateHelpers.activeFolders(state, { mockFolders });
}

function activePresetItems() {
  return appStateHelpers.activePresetItems(state, {
    devMode,
    mockPresets,
    mockPresetSettings,
    normalizeSettings,
  });
}

function activePresetItem() {
  return appStateHelpers.activePresetItem(state, {
    devMode,
    mockPresets,
    mockPresetSettings,
    normalizeSettings,
  });
}

function exportableImages() {
  return appStateHelpers.exportableImages(activeImages());
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
  return appStateHelpers.exportItemStatusMap(images, state.exportCompletedItems);
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
  return appStateHelpers.exportItemState(image, state.exportCompletedItems);
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
  return appStateHelpers.validationIssues({
    state,
    exportableImages: exportableImages(),
    exportOutputProfiles: exportOutputProfiles(),
    outputProfileRawFromProfile,
    outputProfileValidation: outputProfileHelpers.outputProfileValidation,
  });
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

  const existingOutputIssue = [...state.errors, ...state.exportIssues].find(preflightHelpers.issueMentionsExistingOutput);
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
  return appStateHelpers.imageDimensions(image);
}

function lowResolutionImageCount() {
  const targets = exportOutputProfiles().map((profile) => outputProfileHelpers.parseOutputSize(outputProfileHelpers.outputProfileSize(profile)));
  return appStateHelpers.lowResolutionImageCount({
    images: exportableImages(),
    targets,
  });
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
  return appStateHelpers.uiState({
    state,
    counts,
    lotCounts,
    selectedImage: image,
    hasBatch: hasBatch(),
    canExport: isExportReady(),
  });
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
