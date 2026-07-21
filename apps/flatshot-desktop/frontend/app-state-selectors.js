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
