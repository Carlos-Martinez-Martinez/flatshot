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
    void startBridgeExport(options);
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

  state.exportHistoryRecordedJobId = "";
  Object.assign(state, exportStateHelpers.exportStartState({
    scenario: options.keepScenario ? "export-running" : state.scenario,
    resetConfirm: true,
  }));
  render();
  scheduleExportStep();
}

async function startBridgeExport(options = {}) {
  const retryImages = options.retryFailedOnly ? retryableFailedExportImages() : exportableImages();
  if (options.retryFailedOnly && !retryImages.length) {
    state.errors = [{
      level: "warning",
      title: "Sin fallidas reintentables",
      detail: "La última exportación no conserva rutas fallidas para reintentar.",
    }];
    state.statusText = "Sin fallidas reintentables";
    render();
    return;
  }
  clearBridgeExportPoll();
  cancelThumbnailWork();
  state.exportHistoryRecordedJobId = "";
  Object.assign(state, exportStateHelpers.exportStartState());
  render();

  try {
    const response = await bridgeRequest("/exports/run", {
      method: "POST",
      body: JSON.stringify(bridgeExportPayload({ images: retryImages })),
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

function bridgeExportPayload(options = {}) {
  const images = Array.isArray(options.images) ? options.images : exportableImages();
  return exportPayloadHelpers.buildBridgeExportPayload({
    activeOutputProfileId: state.activeOutputProfileId,
    fallbackProfile: currentOutputProfileData(),
    imageOverrides: state.imageOverrides,
    images,
    presetName: state.activePreset,
    profiles: exportOutputProfiles(),
    settings: bridgePreviewSettings(),
    curveData: state.curveData || state.scaleCurve || null,
  });
}

function retryableFailedExportImages() {
  return exportPayloadHelpers.failedBridgeExportImages(exportableImages(), retryableFailedExportItems());
}

function retryableFailedExportItems() {
  return state.exportFailedItems.length ? state.exportFailedItems : state.exportCompletedItems;
}

function retryFailedExport() {
  startExport({ retryFailedOnly: true, confirmed: true });
}

function quickExport() {
  startExport({ confirmed: true, quick: true });
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
  state.errors = exportStateHelpers.bridgeStatusErrors(payload, retryableFailedExportItems(), state.exportIssues);
  if (["completed", "partial", "failed"].includes(state.exportStatus)) {
    rememberCurrentExportHistory();
  }
}

function rememberCurrentExportHistory() {
  if (!["completed", "partial", "failed"].includes(state.exportStatus) || !state.exportResult) {
    return;
  }
  const recordId = state.exportJobId
    || `local-${state.exportStatus}-${state.exportResult.processed}-${state.exportResult.total}-${state.exportHistory.length}`;
  if (state.exportHistoryRecordedJobId === recordId) {
    return;
  }
  const destinations = state.exportDestinations.length
    ? state.exportDestinations
    : Array.isArray(state.exportResult.destinations)
      ? state.exportResult.destinations
      : [];
  state.exportHistory = exportHistoryHelpers.rememberExportHistory(window.localStorage, STORAGE_KEYS.exportHistory, {
    id: recordId,
    status: state.exportStatus,
    processed: state.exportResult.processed,
    total: state.exportResult.total,
    errors: state.exportResult.errors,
    destinations,
    presetName: state.activePreset,
    outputProfileName: outputProfileDisplayName(),
  });
  state.exportHistoryRecordedJobId = recordId;
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
      rememberCurrentExportHistory();
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
