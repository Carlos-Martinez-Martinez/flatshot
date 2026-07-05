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
  } else if (action === "edit-output") {
    beginOutputEdit();
  } else if (action === "start-export") {
    startExport();
  } else if (action === "quick-export") {
    quickExport();
  } else if (action === "browse-outputs") {
    browseOutputs();
  } else if (action === "open-output") {
    void openOutputFolder();
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

function pathFromActionTarget(target, key) {
  if (typeof target === "string") {
    return target.trim();
  }
  return String(target?.dataset?.[key] || "").trim();
}

function browseOutputs() {
  state.outputBrowserOpen = !state.outputBrowserOpen;
  if (state.outputBrowserOpen) {
    state.inspectorTab = "output";
  } else if (state.inspectorTab === "output" && !state.outputEditMode) {
    state.inspectorTab = "review";
  }
  state.statusText = state.outputBrowserOpen ? "Salidas exportadas" : "Resultado de exportación";
  render();
  if (state.outputBrowserOpen && typeof document !== "undefined") {
    document.querySelector("#export-result")?.scrollIntoView({ block: "start", behavior: "smooth" });
  }
}

async function openOutputFolder(target = null) {
  const destination = pathFromActionTarget(target, "outputFolder") || outputDestinationToOpen();
  if (!destination) {
    state.statusText = "No hay carpeta de salida registrada";
    render();
    return;
  }
  if (isBridgeBatch()) {
    try {
      await bridgeRequest("/folders/open", {
        method: "POST",
        body: JSON.stringify({ path: destination }),
        timeoutMs: 5000,
      });
      state.statusText = "Carpeta de salida abierta";
    } catch (error) {
      state.statusText = `No se pudo abrir la carpeta de salida: ${bridgeErrorMessage(error)}`;
    }
    render();
    return;
  }
  openOutputFolderInBrowser(destination);
  render();
}

function openOutputFolderInBrowser(destination) {
  const opened = window.open(formatterHelpers.pathToFileUrl(destination), "_blank", "noopener");
  state.statusText = opened ? "Carpeta de salida abierta" : "No se pudo abrir la carpeta de salida";
  return Boolean(opened);
}

async function copyOutputPath(target = null) {
  const destination = pathFromActionTarget(target, "outputPath")
    || pathFromActionTarget(target, "outputFolder")
    || outputDestinationToOpen();
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

async function revealOutputFile(target = null) {
  const outputPath = pathFromActionTarget(target, "outputPath");
  if (!outputPath) {
    state.statusText = "No hay archivo de salida registrado";
    render();
    return;
  }
  if (isBridgeBatch()) {
    try {
      await bridgeRequest("/files/reveal", {
        method: "POST",
        body: JSON.stringify({ path: outputPath }),
        timeoutMs: 5000,
      });
      state.statusText = "Archivo de salida localizado";
    } catch (error) {
      state.statusText = `No se pudo localizar la salida: ${bridgeErrorMessage(error)}`;
    }
    render();
    return;
  }
  const folder = exportResultViewHelpers.outputFolderForPath(outputPath);
  if (folder) {
    openOutputFolderInBrowser(folder);
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
