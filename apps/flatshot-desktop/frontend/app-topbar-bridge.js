function renderDevelopmentStatus() {
  $("#dev-mode-label").textContent = state.bridgeMode === "bridge" ? "Bridge local" : "Mock";
  $("#dev-bridge-label").textContent = bridgeStatusLabel();
  $("#dev-bridge-url-label").textContent = state.bridgeUrl || defaultBridgeUrl;
  $("#dev-last-response").textContent = state.bridgeLastResponse;
  updatePreviewDebugPanel();
}

function updatePreviewDebugPanel() {
  const image = selectedImage();
  const previewImage = $("#preview-canvas .preview-image");
  const thumbSrc = image ? imageThumbnailSrc(image) : "";
  const rendered = previewImage?.getBoundingClientRect();
  const naturalWidth = Number(previewImage?.naturalWidth || state.previewData?.width || 0);
  const naturalHeight = Number(previewImage?.naturalHeight || state.previewData?.height || 0);
  const stats = thumbnailStats();

  setDebugText("debug-original-url", image?.originalUrl || image?.path || "-");
  setDebugText("debug-preview-url", state.previewData?.src ? formatterHelpers.debugUrlLabel(state.previewData.src) : "-");
  setDebugText("debug-thumbnail-url", thumbSrc || "-");
  setDebugText("debug-natural-size", naturalWidth && naturalHeight ? `${naturalWidth} x ${naturalHeight}` : "-");
  setDebugText("debug-rendered-size", rendered ? `${Math.round(rendered.width)} x ${Math.round(rendered.height)}` : "-");
  setDebugText("debug-load-status", state.previewStatus || "-");
  setDebugText("debug-preview-error", state.previewError || "-");
  setDebugText("debug-thumbnail-stats", `${stats.loaded}/${stats.total} cargadas · ${stats.failed} fallidas · ${stats.pending} pendientes`);
}

function setDebugText(id, value) {
  const target = $(`#${id}`);
  if (target) {
    target.textContent = value;
    target.title = value;
  }
}

function thumbnailStats() {
  const images = activeImages();
  const total = images.length;
  let loaded = 0;
  let failed = 0;
  images.forEach((image) => {
    const src = imageThumbnailSrc(image);
    const status = state.thumbnailStatus[image.id];
    if (status?.src === src && status.status === "loaded") {
      loaded += 1;
    } else if (status?.src === src && status.status === "error") {
      failed += 1;
    }
  });
  return {
    total,
    loaded,
    failed,
    pending: Math.max(0, total - loaded - failed),
  };
}

function renderTop() {
  const visible = getVisibleAppState();
  const counts = batchCounts();
  $("#bridge-url").value = state.bridgeUrl;
  $("#active-batch-label").textContent = "";
  const topStatus = $("#top-status-text");
  const topbarText = conciseTopbarStatusText();
  const topSummary = $(".top-summary");
  if (topSummary) {
    topSummary.hidden = !topbarText;
  }
  topStatus.textContent = topbarText;
  topStatus.title = topbarText ? visible.subtitle || topbarText : "";
  $("#status-dot").className = `status-dot ${statusMode()}`;
  const hasBatchDetail = hasBatch() || state.batch === "empty"
    || counts.reviewIssues > 0
    || counts.ignoredFiles > 0
    || counts.blockingErrors > 0
    || ["partial", "failed"].includes(state.exportStatus);
  const detailButton = $("[data-action='open-batch-detail']");
  if (detailButton) {
    detailButton.hidden = !hasBatchDetail;
    detailButton.title = state.batch === "none" ? "Ver configuración inicial" : "Ver detalle del lote";
  }
  const preflight = $("#top-preflight-status");
  if (preflight) {
    preflight.textContent = preflightStatusLabel();
    preflight.className = `preflight-chip ${preflightStatusClass()}`;
  }
  const secondary = $("#top-secondary-action");
  if (secondary) {
    const action = visible.secondaryAction;
    secondary.hidden = !action;
    secondary.disabled = !action?.enabled;
    secondary.textContent = action?.label || "";
    secondary.dataset.stateAction = action?.action || "";
    secondary.title = action?.label || "";
  }
  const canChangeBatch = state.batch !== "none" && state.batch !== "scanning" && state.exportStatus !== "running";
  const folderButton = $(".top-folder-action");
  if (folderButton) {
    folderButton.hidden = !canChangeBatch;
    folderButton.disabled = !canChangeBatch;
    folderButton.title = "Seleccionar otra carpeta";
  }
  const formatButton = $(".top-format-action");
  if (formatButton) {
    const showFormat = state.batch !== "none" && state.batch !== "scanning";
    formatButton.hidden = !showFormat;
    formatButton.disabled = !showFormat || state.exportStatus === "running";
    formatButton.title = "Formatos de salida";
  }
  const resetButton = $(".top-reset-action");
  if (resetButton) {
    resetButton.hidden = state.batch === "none" || state.batch === "scanning";
    resetButton.disabled = state.exportStatus === "running";
    resetButton.title = "Volver al estado inicial";
  }
  const moreMenu = $(".top-more-menu");
  if (moreMenu) {
    moreMenu.hidden = true;
  }
}

function conciseTopbarStatusText() {
  if (["running", "completed", "partial", "failed"].includes(state.exportStatus)) {
    return compactHeaderStatusText();
  }
  if (state.batch === "scanning") {
    return "Escaneando";
  }
  if (state.bridgeMode === "bridge" && state.bridgeStatus === "disconnected") {
    return "Bridge no disponible";
  }
  return "";
}

function compactHeaderStatusText() {
  const counts = batchCounts();
  const images = activeImages();
  return topStatusViewHelpers.compactHeaderStatusText({
    batch: state.batch,
    exportResultProcessed: state.exportResult?.processed,
    exportResultTotal: state.exportResult?.total,
    exportStatus: state.exportStatus,
    exportableImages: counts.exportableImages,
    filesFound: counts.filesFound,
    formatLabel: batchViewHelpers.detectedFormatLabel(images),
    ignoredFiles: counts.ignoredFiles,
    imageCount: images.length,
    nonBlockingWarnings: counts.nonBlockingWarnings,
    paused: state.paused,
    plannedTotal: plannedExportTotal(),
    processed: state.processed,
    readyLabel: preflightHelpers.readyImagesText(counts.exportableImages),
  });
}

function topStatusText() {
  return topStatusViewHelpers.topStatusText({
    batch: state.batch,
    bridgeMode: state.bridgeMode,
    bridgeStatus: state.bridgeStatus,
    compactHeaderStatus: compactHeaderStatusText(),
    exportStatus: state.exportStatus,
    exportableImages: exportableImages().length,
    paused: state.paused,
    plannedTotal: plannedExportTotal(),
    processed: state.processed,
    statusText: state.statusText,
  });
}

function preflightStatusLabel() {
  const ready = isExportReady();
  const counts = preflightCounts();
  return topStatusViewHelpers.preflightStatusLabel({
    errors: counts.errors,
    exportStatus: state.exportStatus,
    paused: state.paused,
    ready,
    warnings: counts.warnings,
  });
}

function preflightStatusClass() {
  const ready = isExportReady();
  const counts = preflightCounts();
  return topStatusViewHelpers.preflightStatusClass({
    errors: counts.errors,
    exportStatus: state.exportStatus,
    ready,
    warnings: counts.warnings,
  });
}

function renderBridge() {
  const chip = $("#bridge-status");
  const sourcePanel = $("#source-panel");
  const sourceBadge = $("#scan-source-badge");
  const message = $("#bridge-message");
  const counts = batchCounts();
  const viewState = scanStateHelpers.sourcePanelViewState({
    batch: state.batch,
    bridgeMode: state.bridgeMode,
    bridgeStatus: state.bridgeStatus,
    devMode,
    exportableImages: counts.exportableImages,
    folders: sourceFoldersForDisplay(),
    hasBatch: hasBatch(),
    hasScanError: state.scanIssues.some((issue) => issue.level === "error"),
    ignoredFiles: counts.ignoredFiles,
    isBridgeBatch: isBridgeBatch(),
    isMockBatch: isMockBatch(),
    persistedFolderName: persistedScanFolderName(),
    scanStatus: state.scanStatus,
    scanningFolderName: scanningScanFolderName(),
  });

  chip.className = `bridge-chip ${bridgeStatusClass()}`;
  chip.textContent = bridgeStatusLabel();
  sourcePanel.className = `source-panel batch-rail__source ${viewState.panelClass}`;
  sourceBadge.className = `state-chip ${viewState.badgeClass}`;
  sourceBadge.textContent = viewState.badgeLabel;
  $("#source-title").textContent = viewState.title;
  const sourceName = $("#source-folder-name");
  if (sourceName) {
    sourceName.textContent = viewState.folderName;
    sourceName.title = viewState.folderName;
  }
  $("#scan-status").textContent = viewState.scanStatus;
  $("#bridge-scan-path").value = state.bridgeScanPath;
  $("#bridge-pick-folder").textContent = viewState.pickButtonLabel;
  $("#bridge-scan-folder").textContent = viewState.scanButtonLabel;
  $("#bridge-scan-folder").title = viewState.scanButtonTitle;
  $("#bridge-scan-folder").setAttribute("aria-label", $("#bridge-scan-folder").title);
  $("#bridge-pick-folder").disabled = viewState.controlsDisabled;
  $("#bridge-scan-folder").disabled = viewState.controlsDisabled;
  $("#bridge-last-response").textContent = state.bridgeLastResponse;
  $("#bridge-capabilities").textContent = state.bridgeCapabilitiesSummary;
  message.textContent = viewState.message;
  message.className = viewState.messageClass;
  renderBatchSummary();
}

function sourceFoldersForDisplay() {
  if (state.batch === "ready") {
    return activeFolders();
  }
  if (state.batch === "empty" && isBridgeBatch()) {
    return state.realFolders;
  }
  return [];
}

function persistedScanFolderName() {
  const persistedPath = parseFolderInput(state.bridgeScanPath)[0];
  return persistedPath ? formatterHelpers.basename(persistedPath) || "Carpeta actual" : "";
}

function scanningScanFolderName() {
  return formatterHelpers.basename(parseFolderInput(state.bridgeScanPath)[0]);
}

function sourceFolderName() {
  if (state.batch === "scanning") {
    return scanStateHelpers.sourceFolderName({
      batch: state.batch,
      scanningFolderName: scanningScanFolderName(),
    });
  }
  return scanStateHelpers.sourceFolderName({
    batch: state.batch,
    folders: sourceFoldersForDisplay(),
    hasBatch: hasBatch(),
    persistedFolderName: persistedScanFolderName(),
  });
}

function emptyScanDiagnostics() {
  return {
    totalFiles: 0,
    totalImages: 0,
    totalOmitted: 0,
    omittedByReason: {},
    omittedByCategory: {},
    omitted: [],
  };
}

function mockScanDiagnostics() {
  return {
    totalFiles: mockImages.length,
    totalImages: mockImages.length,
    totalOmitted: 0,
    omittedByReason: {},
    omittedByCategory: {},
    omitted: [],
  };
}

function scanDiagnosticsFromResponse(response) {
  const omitted = (response.folders || []).flatMap((folder) =>
    (folder.omitted || []).map((item) => ({
      ...item,
      folder: folder.path,
    }))
  );
  return {
    totalFiles: Number(response.totalFiles) || Number(response.totalImages) || 0,
    totalImages: Number(response.totalImages) || 0,
    totalOmitted: Number(response.totalOmitted) || omitted.length,
    omittedByReason: response.omittedByReason || {},
    omittedByCategory: response.omittedByCategory || {},
    omitted,
  };
}

function bridgeStatusClass() {
  return scanStateHelpers.bridgeStatusClass({
    bridgeMode: state.bridgeMode,
    bridgeStatus: state.bridgeStatus,
    devMode,
  });
}

function bridgeStatusLabel() {
  return scanStateHelpers.bridgeStatusLabel({
    bridgeMode: state.bridgeMode,
    bridgeStatus: state.bridgeStatus,
    devMode,
  });
}
