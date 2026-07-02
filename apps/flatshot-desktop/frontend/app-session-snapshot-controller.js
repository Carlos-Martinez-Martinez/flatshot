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
    normalizeGuideSystemList: (systems) => guideHelpers.normalizeGuideSystemList(systems),
    normalizeActiveGuideSystemIds: guideHelpers.normalizeActiveGuideSystemIds,
    normalizeOutputProfileList: outputProfileHelpers.normalizeOutputProfileList,
    normalizePreviewBackgroundValue: (value) => backgroundPresetHelpers.normalizePreviewBackgroundValue(value, backgroundHelperOptions()),
    normalizeSettings,
    normalizePresetItem,
    normalizeBridgeIssue: exportStateHelpers.normalizeBridgeIssue,
    normalizeExportFormat: outputProfileHelpers.normalizeExportFormat,
    normalizeMaxFileSizeKb: outputProfileHelpers.normalizeMaxFileSizeKb,
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
