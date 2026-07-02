function clearFilter() {
  state.filter = BATCH_FILTERS.all;
  state.search = "";
  state.statusText = "Mostrando todo";
  if (ensureGallerySelectionForFilter()) {
    return;
  }
  render();
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
  } else if (action === "copy-output-path") {
    void copyOutputPath();
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

async function copyOutputPath() {
  const destination = outputDestinationToOpen();
  if (!destination) {
    state.statusText = "No hay carpeta de salida registrada";
    render();
    return;
  }
  const clipboard = typeof navigator !== "undefined" ? navigator.clipboard : null;
  if (!clipboard?.writeText) {
    state.statusText = `Ruta de salida: ${destination}`;
    render();
    return;
  }
  try {
    await clipboard.writeText(destination);
    state.statusText = "Ruta de salida copiada";
  } catch (error) {
    state.statusText = "No se pudo copiar la ruta de salida";
  }
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
