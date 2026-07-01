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
