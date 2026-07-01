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
