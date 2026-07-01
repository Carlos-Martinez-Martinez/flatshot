function render() {
  renderShell();
  renderTop();
  renderDevelopmentStatus();
  renderBridge();
  renderBatch();
  renderPreview();
  renderSettings();
  renderExport();
  renderBatchDetail();
  renderExportConfirm();
  renderAppSettings();
  renderInspector();
  renderFooter();
  renderAccessibilityHints();
  syncRangeFillStyles();
  syncOpenInspectorDisclosureHeights();
  keepActiveThumbnailVisible();
  if (sessionSnapshotPersistenceEnabled) {
    writeSessionSnapshot();
  }
}

function renderAdjustmentResponse() {
  renderPreview();
  renderSettings();
  renderBatch();
  renderExport();
  renderInspector();
  renderTop();
  syncRangeFillStyles();
  syncOpenInspectorDisclosureHeights();
  keepActiveThumbnailVisible();
}

function syncOpenInspectorDisclosureHeights() {
  window.requestAnimationFrame(() => {
    $$(".settings-panel details.inspector-disclosure[open]").forEach((details) => {
      if (!details.classList.contains("is-closing")) {
        setInspectorDisclosureHeight(details);
      }
    });
  });
}

function inspectorDisclosureBody(details) {
  return details?.querySelector?.(".inspector-disclosure__body") || null;
}

function setInspectorDisclosureHeight(details, height = null) {
  const body = inspectorDisclosureBody(details);
  if (!body) {
    return;
  }
  let nextHeight = height;
  if (nextHeight === null) {
    const wasOpening = details.classList.contains("is-opening");
    const wasClosing = details.classList.contains("is-closing");
    if (wasOpening || wasClosing) {
      details.classList.remove("is-opening", "is-closing");
    }
    const previousHeight = body.style.getPropertyValue("--inspector-disclosure-height");
    body.style.setProperty("--inspector-disclosure-height", "none");
    const bodyRect = body.getBoundingClientRect();
    const bodyStyle = getComputedStyle(body);
    const paddingBottom = Number.parseFloat(bodyStyle.paddingBottom) || 0;
    const childBottom = Array.from(body.children).reduce((max, child) => {
      const rect = child.getBoundingClientRect();
      return Math.max(max, rect.bottom - bodyRect.top);
    }, 0);
    nextHeight = Math.max(body.scrollHeight, Math.ceil(childBottom + paddingBottom));
    if (previousHeight) {
      body.style.setProperty("--inspector-disclosure-height", previousHeight);
    } else {
      body.style.removeProperty("--inspector-disclosure-height");
    }
    if (wasOpening) {
      details.classList.add("is-opening");
    }
    if (wasClosing) {
      details.classList.add("is-closing");
    }
  }
  body.style.setProperty("--inspector-disclosure-height", `${Math.max(0, Math.round(nextHeight))}px`);
}

function setInspectorDisclosureOpenState(details, open) {
  if (!details) {
    return;
  }
  const previousTimer = inspectorDisclosureTimers.get(details);
  if (previousTimer) {
    window.clearTimeout(previousTimer);
    inspectorDisclosureTimers.delete(details);
  }
  details.open = open;
  details.classList.remove("is-opening", "is-closing", "is-open");
  inspectorDisclosureBody(details)?.style.removeProperty("--inspector-disclosure-height");
}

function restoreInspectorScroll(panel, scrollTop = inspectorScrollTopBeforeToggle) {
  if (!panel) {
    return;
  }
  const restore = () => {
    panel.scrollTop = scrollTop;
  };
  restore();
  window.requestAnimationFrame(() => {
    restore();
    window.requestAnimationFrame(restore);
    window.setTimeout(restore, 0);
    window.setTimeout(restore, INSPECTOR_DISCLOSURE_MS);
  });
}

function closeInspectorDisclosure(details, panel = $(".settings-panel"), scrollTop = inspectorScrollTopBeforeToggle) {
  if (!details?.open || details.classList.contains("is-closing")) {
    return;
  }
  const previousTimer = inspectorDisclosureTimers.get(details);
  if (previousTimer) {
    window.clearTimeout(previousTimer);
  }

  setInspectorDisclosureHeight(details);
  details.classList.remove("is-opening", "is-open");
  details.classList.add("is-closing");
  window.requestAnimationFrame(() => {
    setInspectorDisclosureHeight(details, 0);
    restoreInspectorScroll(panel, scrollTop);
  });

  const timer = window.setTimeout(() => {
    details.open = false;
    details.classList.remove("is-closing");
    const body = inspectorDisclosureBody(details);
    body?.style.removeProperty("--inspector-disclosure-height");
    inspectorDisclosureTimers.delete(details);
    restoreInspectorScroll(panel, scrollTop);
  }, INSPECTOR_DISCLOSURE_MS);
  inspectorDisclosureTimers.set(details, timer);
}

function openInspectorDisclosure(details, panel = $(".settings-panel"), scrollTop = inspectorScrollTopBeforeToggle) {
  if (!details) {
    return;
  }
  $$(".settings-panel details.inspector-disclosure").forEach((other) => {
    if (other !== details && other.open) {
      closeInspectorDisclosure(other, panel, scrollTop);
    }
  });

  const previousTimer = inspectorDisclosureTimers.get(details);
  if (previousTimer) {
    window.clearTimeout(previousTimer);
    inspectorDisclosureTimers.delete(details);
  }
  details.open = true;
  details.classList.remove("is-closing", "is-open");
  details.classList.add("is-opening");
  setInspectorDisclosureHeight(details, 0);
  restoreInspectorScroll(panel, scrollTop);
  window.requestAnimationFrame(() => {
    setInspectorDisclosureHeight(details);
    restoreInspectorScroll(panel, scrollTop);
  });
  const timer = window.setTimeout(() => {
    details.classList.remove("is-opening");
    details.classList.add("is-open");
    const body = inspectorDisclosureBody(details);
    body?.style.setProperty("--inspector-disclosure-height", "none");
    inspectorDisclosureTimers.delete(details);
    restoreInspectorScroll(panel, scrollTop);
  }, INSPECTOR_DISCLOSURE_MS);
  inspectorDisclosureTimers.set(details, timer);
}

function toggleInspectorDisclosure(details) {
  const panel = $(".settings-panel");
  inspectorScrollTopBeforeToggle = panel?.scrollTop || 0;
  const shouldOpen = !details.open || details.classList.contains("is-closing");
  if (shouldOpen) {
    openInspectorDisclosure(details, panel, inspectorScrollTopBeforeToggle);
  } else {
    closeInspectorDisclosure(details, panel, inspectorScrollTopBeforeToggle);
  }
}

function renderShell() {
  const shell = $(".app-shell");
  const gallery = $(".gallery-column");
  const derived = uiState();
  const visible = getVisibleAppState();
  const hasStatusFooter = state.exportStatus === "running"
    || state.exportStatus === "completed"
    || state.exportStatus === "partial"
    || state.exportStatus === "failed";
  shell.classList.toggle("dev-mode", devMode);
  shell.classList.toggle("has-selected-image", derived.hasSelectedImage);
  shell.classList.toggle("no-selected-image", !derived.hasSelectedImage);
  shell.classList.toggle("can-export", derived.canExport);
  shell.classList.toggle("is-settings-open", state.appSettingsOpen);
  shell.classList.toggle("export-completed", ["completed", "partial", "failed"].includes(state.exportStatus));
  shell.classList.toggle("inspector-collapsed", state.inspectorCollapsed);
  shell.dataset.uiState = visible.id;
  shell.dataset.batchContext = derived.hasBatchContext ? "true" : "false";
  shell.dataset.statusFooter = hasStatusFooter ? "true" : "false";
  shell.dataset.outputEditing = state.outputEditMode ? "true" : "false";
  if (gallery) {
    gallery.dataset.galleryView = state.galleryView;
    const galleryBackground = galleryActiveOutputContext().background;
    gallery.dataset.outputBg = backgroundPresetHelpers.backgroundVisualMode(galleryBackground, backgroundHelperOptions());
    const galleryBackgroundColor = backgroundPresetHelpers.backgroundCssColor(galleryBackground, backgroundHelperOptions());
    if (galleryBackgroundColor) {
      gallery.style.setProperty("--custom-output-bg", galleryBackgroundColor);
    } else {
      gallery.style.removeProperty("--custom-output-bg");
    }
  }
}

function keepActiveThumbnailVisible() {
  window.requestAnimationFrame(() => {
    const active = $("#image-list .image-item.active");
    if (!active) {
      return;
    }
    active.scrollIntoView({ block: "nearest", inline: "center" });
  });
}

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
  $("#demo-scenario").value = scenarioLabels[state.scenario] ? state.scenario : "batch-ready";
  $("#app-mode").value = state.bridgeMode;
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

function renderBatchSummary() {
  const summary = $("#batch-summary");
  const visible = getVisibleAppState();
  const counts = visible.counts;
  const diagnostics = state.scanDiagnostics || emptyScanDiagnostics();
  const sourcePath = state.batch === "ready"
    ? activeFolders()[0]?.path || state.bridgeScanPath
    : state.batch === "empty" && state.realFolders.length
      ? state.realFolders[0]?.path || state.bridgeScanPath
      : state.bridgeScanPath;
  const outputLine = batchOutputLine();
  const destinationLine = batchDestinationLine();
  const warningsLabel = counts.nonBlockingWarnings ? preflightHelpers.countText(counts.nonBlockingWarnings, "aviso", "avisos") : "Sin avisos";
  const ignoredLabel = counts.ignoredFiles ? preflightHelpers.countText(counts.ignoredFiles, "ignorado", "ignorados") : "Sin ignorados";

  summary.innerHTML = batchViewHelpers.batchSummaryHtml({
    batch: state.batch,
    counts,
    destinationLine,
    diagnostics,
    hasScanError: state.scanIssues.some((issue) => issue.level === "error"),
    ignoredLabel,
    namingExample: namingExample(),
    namingLabel: namingHumanLabel(),
    outputLine,
    outputProfileName: outputProfileDisplayName(),
    sourceFolderName: sourceFolderName(),
    sourcePath,
    visible,
    warningsLabel,
  });
}

function batchOutputLine() {
  const profiles = exportOutputProfiles();
  if (!profiles.length) {
    return "Sin formatos activos";
  }
  return batchViewHelpers.batchOutputLine({
    background: state.background,
    format: state.format,
    profileLines: profiles.length > 1
      ? profiles.map((profile) => `${profile.format} ${outputProfileHelpers.outputProfileSize(profile).replace("x", "×")}`)
      : [],
    size: state.size,
  });
}

function outputProfilesSummaryLabel(profiles = exportOutputProfiles()) {
  if (!profiles.length) {
    return "Sin formatos activos";
  }
  return batchViewHelpers.outputProfilesSummaryLabel({
    backgroundLabel: settingsViewHelpers.backgroundLabel(state.background),
    format: state.format,
    profileLabels: profiles.length > 1 ? profiles.map((profile) => `${profile.name} (${profile.format})`) : [],
    sizeLabel: outputSizeDisplay(),
  });
}

function batchDestinationLine() {
  const profiles = exportOutputProfiles();
  if (!profiles.length) {
    return "Sin destino activo";
  }
  return batchViewHelpers.batchDestinationLine({
    destinationMode: state.destinationMode,
    destinationValue: state.destinationValue,
    profileDestinations: profiles.length > 1 ? profiles.map(profileDestinationPreviewLabel) : [],
  });
}

function renderBatchDetail() {
  const modal = $("#batch-detail-modal");
  if (!modal) {
    return;
  }
  modal.classList.toggle("is-hidden", !state.batchDetailOpen);
  modal.setAttribute("aria-hidden", state.batchDetailOpen ? "false" : "true");
  if (!state.batchDetailOpen) {
    return;
  }
  const body = $("#batch-detail-body");
  if (body) {
    body.innerHTML = batchDetailHtml();
  }
}

function renderExportConfirm() {
  const modal = $("#export-confirm-modal");
  if (!modal) {
    return;
  }
  modal.classList.toggle("is-hidden", !state.exportConfirmOpen);
  modal.setAttribute("aria-hidden", state.exportConfirmOpen ? "false" : "true");
  if (!state.exportConfirmOpen) {
    return;
  }

  const risks = state.exportConfirmRisks.length ? state.exportConfirmRisks : exportConfirmationRisks();
  const body = $("#export-confirm-body");
  if (body) {
    body.innerHTML = exportConfirmHtml(risks);
  }
  const modalState = exportConfirmViewHelpers.exportConfirmModalState({
    actionText: exportActionLabel(batchCounts().exportableImages),
    risks,
  });
  const action = $("#export-confirm-action");
  if (action) {
    action.textContent = modalState.actionText;
    action.classList.toggle("danger", modalState.actionDanger);
  }
  const subtitle = $("#export-confirm-subtitle");
  if (subtitle) {
    subtitle.textContent = modalState.subtitle;
  }
}

function exportConfirmHtml(risks) {
  const counts = batchCounts();
  const exportable = counts.exportableImages;
  const summaryRows = [
    ["Imágenes", `${exportable} exportable${exportable === 1 ? "" : "s"}`],
    ["Formatos", outputProfilesSummaryLabel()],
    ["Destino", destinationFallbackLabel()],
    ["Nombre", namingExample()],
  ];
  return exportConfirmViewHelpers.exportConfirmHtml({ risks, summaryRows });
}

function batchDetailHtml() {
  const counts = batchCounts();
  const sourcePath = state.batch === "ready"
    ? activeFolders()[0]?.path || state.bridgeScanPath
    : state.batch === "empty" && state.realFolders.length
      ? state.realFolders[0]?.path || state.bridgeScanPath
      : state.bridgeScanPath;
  const files = counts.filesFound === null ? "Leyendo" : counts.filesFound;
  const valid = counts.validImages === null ? "Leyendo" : counts.validImages;
  const ignoredItems = ignoredOmissions();
  const ignoredRowsHtml = ignoredItems.slice(0, 8).map((item) => batchDetailViewHelpers.batchDetailProblemHtml({
    detail: item.detail || batchViewHelpers.omissionReasonLabel(item.reason),
    title: item.name || "Archivo ignorado",
    titleAttr: item.path || item.name,
    tone: "clear",
  })).join("");
  const issueRowsHtml = actionableIssueRows().slice(0, 8).map((row) => batchDetailViewHelpers.batchDetailProblemHtml({
    detail: row.detail || "Revisar",
    title: row.title,
    titleAttr: row.path || row.title,
    tone: row.level === "error" ? "error" : "warning",
  })).join("");
  const outputRowsHtml = exportOutputProfiles().map((profile, index) => batchDetailViewHelpers.batchDetailOutputHtml({
    active: profile.id === state.activeOutputProfileId,
    destination: outputProfileViewHelpers.profileDestinationPreviewLabel(profile),
    example: outputNameForProfile(profile),
    index,
    name: profile.name,
    summary: outputProfileSummaryLine(profile),
  })).join("");
  const ignoredSectionHtml = batchDetailViewHelpers.batchDetailIgnoredSectionHtml({
    count: ignoredItems.length,
    rowsHtml: ignoredRowsHtml,
  });

  return batchDetailViewHelpers.batchDetailGridHtml({
    counts,
    files,
    ignoredSectionHtml,
    issueCount: actionableIssueRows().length,
    issueRowsHtml,
    outputRowsHtml,
    sourceFolderName: sourceFolderName(),
    sourcePath,
    stateTitle: getVisibleAppState().title,
    valid,
  });
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

function renderBatch() {
  const images = activeImages();
  const counts = batchCounts();
  const adjusted = imageAdjustmentOverrideCount(images);
  const valid = images.filter((image) => image.status === "ready" || hasImageAdjustmentOverride(image)).length;
  const warnings = images.filter((image) => image.status === "warning").length;
  const errors = images.filter((image) => image.status === "error" || exportItemState(image)?.status === "error").length;
  const ignored = counts.ignoredFiles;
  const issueCount = counts.reviewIssues;
  const filmstripCount = $("#filmstrip-count");
  $("#image-search").value = state.search;
  updateBatchSearchClear();
  renderGalleryViewButtons();
  renderGalleryOutputControl();

  if (state.batch === "none") {
    $("#batch-count").textContent = "Sin lote";
    setBatchPill("Sin carpeta", "muted");
    setGalleryTitle(0, "Sin lote");
    setGalleryMeta("");
    $("#batch-visible-count").textContent = "";
    $("#folder-list").innerHTML = "";
    $("#image-list").innerHTML = "";
    $("#batch-empty-note").innerHTML = "";
    if (filmstripCount) {
      filmstripCount.textContent = "Sin lote";
    }
    renderFilterButtons();
    return;
  }

  const sidebarSummaryText = batchViewHelpers.sidebarLotSummaryText({
    batch: state.batch,
    hasBatch: hasBatch(),
    nonBlockingWarnings: counts.nonBlockingWarnings,
    readyLabel: preflightHelpers.readyImagesText(counts.exportableImages),
    scanStatus: state.scanStatus,
  });

  if (state.batch === "scanning") {
    $("#batch-count").textContent = "Escaneando";
    setBatchPill("Escaneando", "active");
    setGalleryTitle(0, "Escaneando");
    setGalleryMeta(state.scanStatus || "Leyendo carpeta");
    $("#batch-visible-count").textContent = sidebarSummaryText;
    $("#folder-list").innerHTML = batchDetailViewHelpers.folderItemHtml({
      id: "scan",
      name: isBridgeBatch() || !devMode ? formatterHelpers.basename(parseFolderInput(state.bridgeScanPath)[0]) || "Ruta" : "Camisetas Mayo",
      path: state.bridgeScanPath,
      detail: "Leyendo imágenes",
      count: "...",
      status: "ready",
    });
    $("#image-list").innerHTML = "";
    $("#batch-empty-note").innerHTML = "";
    if (filmstripCount) {
      filmstripCount.textContent = "Escaneando";
    }
    renderFilterButtons();
    return;
  }

  if (state.batch === "empty") {
    const emptyFolders = isBridgeBatch() && state.realFolders.length
      ? state.realFolders
      : [{
          id: "empty",
          name: "Carpeta vacía",
          detail: "No hay PNG válidos",
          count: "0",
          status: "empty",
        }];
    $("#batch-count").textContent = "Sin imágenes";
    setBatchPill("Sin imágenes", "muted");
    setGalleryTitle(0, "No hay PNG válidos");
    setGalleryMeta(sidebarSummaryText);
    $("#batch-visible-count").textContent = sidebarSummaryText;
    $("#folder-list").innerHTML = emptyFolders.map((folder) => batchDetailViewHelpers.folderItemHtml(folder)).join("");
    $("#image-list").innerHTML = "";
    $("#batch-empty-note").innerHTML = emptyBatchNoteHtml();
    if (filmstripCount) {
      filmstripCount.textContent = "Sin imágenes";
    }
    renderFilterButtons();
    return;
  }

  const exportable = exportableImages().length;
  $("#batch-count").textContent = exportable ? preflightHelpers.readyImagesText(exportable) : "Sin exportables";
  const batchPillState = batchViewHelpers.batchPillState({
    adjustedCount: adjusted,
    issueCount,
  });
  setBatchPill(batchPillState.label, batchPillState.tone);
  $("#folder-list").innerHTML = "";
  ensureGalleryFilterAvailable(images);
  renderFilterButtons();

  const visible = filteredImages();
  setGalleryTitle(exportable);
  setGalleryMeta(galleryBatchMetaText(counts, images));
  $("#batch-visible-count").textContent = visible.length === images.length
    ? ""
    : `${visible.length}/${images.length}`;
  $("#image-list").innerHTML = visible.map(imageItemHtml).join("");
  queueThumbnailPreload();
  $("#batch-empty-note").innerHTML = visible.length ? "" : filteredEmptyHtml(images.length, valid, warnings, errors);
  if (filmstripCount) {
    filmstripCount.textContent = visible.length === images.length
      ? `${images.length} imágenes`
      : `${visible.length} de ${images.length}`;
  }
}

function setGalleryTitle(count, label = "") {
  const title = $("#gallery-title");
  if (title) {
    title.textContent = label || preflightHelpers.readyImagesText(Number(count) || 0);
  }
}

function setGalleryMeta(text = "") {
  const meta = $("#gallery-batch-meta");
  if (meta) {
    meta.textContent = text;
    meta.title = text;
  }
}

function galleryBatchMetaText(counts = batchCounts(), images = activeImages()) {
  const filesFound = counts.filesFound === null ? images.length : Number(counts.filesFound) || images.length;
  const parts = [
    batchViewHelpers.detectedFormatLabel(images),
    filesFound ? `${filesFound} archivos` : "",
  ].filter(Boolean);
  if (counts.nonBlockingWarnings) {
    parts.push(`${counts.nonBlockingWarnings} ${counts.nonBlockingWarnings === 1 ? "aviso" : "avisos"}`);
  }
  if (counts.ignoredFiles) {
    parts.push(`${counts.ignoredFiles} ${counts.ignoredFiles === 1 ? "ignorado" : "ignorados"}`);
  }
  return parts.join(" · ");
}

function renderGalleryOutputControl() {
  const control = $("#gallery-output-control");
  const select = $("#gallery-output-select");
  if (!control || !select) {
    return;
  }
  const profiles = galleryOutputProfiles();
  const showControl = state.batch === "ready" && profiles.length > 1;
  control.hidden = !showControl;
  if (!showControl) {
    select.innerHTML = "";
    return;
  }
  const context = galleryActiveOutputContext();
  const customOption = context.id === "__custom"
    ? `<option value="__custom">Formato personalizado · ${escapeHtml(context.label)}</option>`
    : "";
  select.innerHTML = `${customOption}${profiles.map((profile) => {
    return `<option value="${escapeHtml(profile.id)}">${escapeHtml(profile.name)}</option>`;
  }).join("")}`;
  select.value = context.id;
  if (select.value !== context.id) {
    select.value = profiles[0]?.id || "";
  }
  select.title = context.summary;
}

function setBatchPill(label, tone = "muted") {
  const pill = $("#batch-pill");
  pill.textContent = label;
  pill.className = `batch-rail__badge is-${tone}`;
}

function updateBatchSearchClear() {
  const clearButton = $("#image-search-clear");
  if (!clearButton) {
    return;
  }
  const hasSearch = Boolean(state.search.trim());
  clearButton.classList.toggle("is-visible", hasSearch);
  clearButton.disabled = !hasSearch;
}

function filteredEmptyHtml(total, valid, warnings, errors) {
  return galleryHelpers.filteredEmptyHtml({
    errors,
    filter: state.filter,
    search: state.search,
    total,
    valid,
    warnings,
  });
}

function filterEmptyDetail() {
  return galleryHelpers.filterEmptyDetail({
    filter: state.filter,
    search: state.search,
  });
}

function emptyBatchNoteHtml() {
  return galleryHelpers.emptyBatchNoteHtml({
    ignored: ignoredOmissions().length,
    ignoredSummary: ignoredSummaryText(),
    scanStatus: state.scanStatus,
  });
}

function imageThumbnailSrc(image) {
  if (!image) {
    return "";
  }
  if (image.source === "bridge") {
    return image.thumbnailUrl || (image.path ? bridgeThumbnailUrl(image.path) : "");
  }
  return galleryHelpers.mockThumbnailDataUrl(image);
}

function thumbnailState(image, src) {
  return galleryHelpers.thumbnailState({
    displaySrc: src,
    renderedOnly: false,
    src,
    stored: state.thumbnailStatus[image.id],
  });
}

function renderedThumbnailKey(image) {
  const signature = {
    background: state.background,
    format: state.format,
    imagePath: image.path,
    localOverride: currentImageOverride(image),
    preset: state.activePreset,
    settings: bridgePreviewSettings(),
    size: state.size,
  };
  return `rendered:${JSON.stringify(signature)}`;
}

function thumbnailTargetSize(maxSide = 180) {
  const match = /^(\d+)x(\d+)$/.exec(state.size);
  if (!match) {
    return { targetWidth: maxSide, targetHeight: maxSide };
  }
  const width = Number(match[1]) || maxSide;
  const height = Number(match[2]) || maxSide;
  const scale = Math.min(maxSide / Math.max(width, height), 1);
  return {
    targetWidth: Math.max(1, Math.round(width * scale)),
    targetHeight: Math.max(1, Math.round(height * scale)),
  };
}

function queueThumbnailPreload() {
  if (!hasBatch() || state.exportStatus === "running") {
    return;
  }
  window.requestAnimationFrame(() => preloadBatchThumbnails());
}

function preloadBatchThumbnails() {
  if (state.exportStatus === "running") {
    return;
  }
  activeImages().forEach((image) => {
    const src = imageThumbnailSrc(image);
    const current = state.thumbnailStatus[image.id];
    const key = `${image.id}|${src}`;
    if (!src || (current?.src === src && ["loaded", "error"].includes(current.status)) || thumbnailPreloads.has(key)) {
      return;
    }
    const preloader = new Image();
    thumbnailPreloads.set(key, preloader);
    preloader.onload = () => {
      markThumbnailLoaded(image.id, src, preloader.naturalWidth, preloader.naturalHeight);
      thumbnailPreloads.delete(key);
    };
    preloader.onerror = () => {
      markThumbnailError(image.id, src);
      thumbnailPreloads.delete(key);
    };
    preloader.src = src;
  });
}

function cancelThumbnailWork() {
  thumbnailPreloads.forEach((preloader) => {
    preloader.onload = null;
    preloader.onerror = null;
    preloader.src = "";
  });
  thumbnailPreloads.clear();
  thumbnailFallbackQueue.length = 0;
}

function markThumbnailLoaded(imageId, sourceSrc, naturalWidth, naturalHeight, resolvedSrc = sourceSrc) {
  if (!activeImages().some((image) => image.id === imageId)) {
    return;
  }
  state.thumbnailStatus[imageId] = {
    status: "loaded",
    src: sourceSrc,
    sourceSrc,
    resolvedSrc,
    naturalWidth,
    naturalHeight,
    error: "",
  };
  applyThumbnailDomStatus(imageId, "loaded", resolvedSrc);
  updatePreviewDebugPanel();
}

function markThumbnailError(imageId, src) {
  const current = state.thumbnailStatus[imageId];
  if ((current?.sourceSrc === src || current?.src === src) && current.status === "loaded") {
    return;
  }
  if (requestThumbnailFallback(imageId, src)) {
    return;
  }
  commitThumbnailError(imageId, src);
}

function commitThumbnailError(imageId, src, detail = "") {
  const current = state.thumbnailStatus[imageId];
  if ((current?.sourceSrc === src || current?.src === src) && current.status === "loaded") {
    return;
  }
  if (!activeImages().some((image) => image.id === imageId)) {
    return;
  }
  const error = detail ? `Preview no disponible: ${detail}` : `Preview no disponible: ${src}`;
  state.thumbnailStatus[imageId] = {
    status: "error",
    src,
    sourceSrc: src,
    error,
  };
  state.thumbnailErrors = [
    { imageId, src, error },
    ...state.thumbnailErrors.filter((item) => item.imageId !== imageId),
  ].slice(0, 20);
  applyThumbnailDomStatus(imageId, "error");
  state.bridgeLastResponse = `thumbnail error: ${formatterHelpers.basename(src) || imageId}`;
  updatePreviewDebugPanel();
}

function requestThumbnailFallback(imageId, sourceSrc) {
  if (state.exportStatus === "running") {
    return false;
  }
  const image = activeImages().find((item) => item.id === imageId);
  if (!image || image.source !== "bridge" || !image.path) {
    return false;
  }

  const current = state.thumbnailStatus[imageId];
  if (current?.sourceSrc === sourceSrc && current.status === "loaded") {
    return false;
  }
  if (current?.sourceSrc === sourceSrc && current.fallbackAttempted && current.status === "loading") {
    return true;
  }
  if (thumbnailFallbackInFlight.has(imageId) || thumbnailFallbackQueue.some((item) => item.imageId === imageId)) {
    return true;
  }

  state.thumbnailStatus[imageId] = {
    renderedOnly: true,
    status: "loading",
    src: sourceSrc,
    sourceSrc,
    fallbackAttempted: true,
    error: "",
  };
  applyThumbnailDomStatus(imageId, "loading");
  thumbnailFallbackQueue.push({ imageId, sourceSrc });
  processThumbnailFallbackQueue();
  return true;
}

function processThumbnailFallbackQueue() {
  while (thumbnailFallbackInFlight.size < MAX_THUMBNAIL_FALLBACKS && thumbnailFallbackQueue.length) {
    const item = thumbnailFallbackQueue.shift();
    thumbnailFallbackInFlight.add(item.imageId);
    void renderFallbackThumbnail(item)
      .catch((error) => {
        commitThumbnailError(item.imageId, item.sourceSrc, bridgeErrorMessage(error));
      })
      .finally(() => {
        thumbnailFallbackInFlight.delete(item.imageId);
        processThumbnailFallbackQueue();
      });
  }
}

async function renderFallbackThumbnail({ imageId, sourceSrc }) {
  const image = activeImages().find((item) => item.id === imageId);
  if (!image) {
    return;
  }

  const response = await bridgeRequest("/preview/render", {
    method: "POST",
    body: JSON.stringify({
      imagePath: image.path,
      ...thumbnailTargetSize(),
      settings: bridgePreviewSettings(),
      localOverride: currentImageOverride(image),
    }),
    timeoutMs: 20000,
  });
  if (imageThumbnailSrc(image) !== sourceSrc) {
    return;
  }
  const data = previewResponseToData(response);
  markThumbnailLoaded(imageId, sourceSrc, data.width, data.height, data.src);
}

function applyThumbnailDomStatus(imageId, status, resolvedSrc = "") {
  const wrapper = Array.from(document.querySelectorAll(".thumb[data-thumb-id]"))
    .find((item) => item.dataset.thumbId === imageId);
  if (!wrapper) {
    return;
  }
  if (resolvedSrc) {
    let image = wrapper.querySelector(".thumb-image");
    if (!image) {
      const item = activeImages().find((activeImage) => activeImage.id === imageId);
      image = document.createElement("img");
      image.className = "thumb-image";
      image.loading = "eager";
      image.dataset.imageId = imageId;
      image.alt = `Miniatura de ${item?.name || "imagen"}`;
      wrapper.prepend(image);
    }
    if (image && image.getAttribute("src") !== resolvedSrc) {
      image.src = resolvedSrc;
    }
  }
  wrapper.classList.remove("is-loading", "is-loaded", "is-error");
  wrapper.classList.add(`is-${status}`);
  if (status === "error") {
    const label = wrapper.querySelector(".thumb-error");
    if (label) {
      label.textContent = "Sin preview";
    }
  }
}

function imageItemHtml(image) {
  const exportState = exportItemState(image);
  const imageStatus = hasImageAdjustmentOverride(image) ? "adjusted" : image.status;
  const thumbnailSrc = imageThumbnailSrc(image);
  return galleryHelpers.imageItemHtml({
    exportState,
    fileType: imageFileType(image),
    image,
    imageStatus,
    outputLabel: "",
    selected: image.id === state.selectedImageId,
    statusLabels,
    thumbState: thumbnailState(image, thumbnailSrc),
    thumbnailSrc,
  });
}

function galleryFilterCounts(images = activeImages()) {
  return galleryHelpers.galleryFilterCounts(images, exportItemStatusMap(images));
}

function ensureGalleryFilterAvailable(images = activeImages()) {
  const nextFilter = galleryHelpers.resolveAvailableFilter(state.filter, images, exportItemStatusMap(images));
  if (nextFilter !== state.filter) {
    state.filter = nextFilter;
  }
}

function renderFilterButtons() {
  const images = activeImages();
  const counts = galleryFilterCounts(images);
  const buttonStates = galleryHelpers.galleryFilterButtonStates({
    activeFilter: state.filter,
    counts,
  });
  const visibleCount = buttonStates.filter((item) => !item.hidden).length;
  const filterGroup = $(".gallery-filter");
  if (filterGroup) {
    filterGroup.hidden = visibleCount <= 1;
  }
  $$(".batch-filter button").forEach((button) => {
    const filter = button.dataset.filter;
    const buttonState = buttonStates.find((item) => item.filter === filter);
    if (!buttonState) {
      return;
    }
    button.innerHTML = `${escapeHtml(buttonState.label)} <span>${escapeHtml(buttonState.count)}</span>`;
    button.title = buttonState.title;
    button.style.order = String(buttonState.order);
    button.classList.toggle("active", buttonState.active);
    button.classList.toggle("is-empty", buttonState.empty);
    button.hidden = buttonState.hidden;
  });
}

function renderGalleryViewButtons() {
  $$("[data-gallery-view]").forEach((button) => {
    const active = button.dataset.galleryView === state.galleryView;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", active ? "true" : "false");
  });
}
