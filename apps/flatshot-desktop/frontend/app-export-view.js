function renderExport() {
  renderOutputProfileSelect();
  $("#format-select").value = state.format;
  $("#size-select").value = state.size;
  syncBackgroundSelectValue($("#background-select"), state.background);
  $("#destination-mode").value = state.destinationMode;
  $("#destination-input").value = state.destinationValue;
  $("#naming-input").value = state.naming;

  const issues = preflightIssues();
  const exportable = exportableImages().length;
  const activeOutputs = exportOutputCount();
  const outputCount = exportable * activeOutputs;
  const ready = isExportReady();
  const destinationText = destinationCompactLabel();
  const warningCount = visibleWarningCount();
  $("#export-readiness").textContent = state.outputEditMode ? "Editar salida" : outputProfileDisplayName();
  $("#export-count").textContent = outputCount ? `${outputCount} archivos` : "Pendiente";
  $("#export-count").classList.toggle("dirty", !ready);
  const warningsReadiness = $("#warnings-readiness");
  if (warningsReadiness) {
    warningsReadiness.textContent = warningCount ? `${warningCount} aviso${warningCount === 1 ? "" : "s"}` : "Sin avisos";
  }
  const warningsTab = $("[data-inspector-tab='warnings']");
  if (warningsTab) {
    warningsTab.textContent = warningCount ? `Avisos ${warningCount}` : "Avisos";
  }

  const warningSummary = outputWarningSummary(issues);
  const editDirty = !outputMatchesProfile(activeOutputProfile());
  const activeOutputProfiles = exportOutputProfiles();
  const hasMultipleOutputs = activeOutputProfiles.length > 1;
  $("#export-summary").innerHTML = exportSummaryViewHelpers.exportSummaryHtml({
    editing: state.outputEditMode,
    displayName: outputProfileDisplayName(),
    presetSummary: presetSummaryLine(),
    editDirty,
    activeOutputCount: activeOutputProfiles.length,
    outputCount,
    profileRows: activeOutputProfiles.map((profile) => ({
      backgroundLabel: settingsViewHelpers.backgroundLabel(profile.background),
      format: profile.format,
      name: profile.name,
      size: outputProfileHelpers.outputProfileSize(profile),
      destinationLabel: outputProfileViewHelpers.profileDestinationLabel(profile),
    })),
    formatLabel: activeOutputProfiles.length
      ? hasMultipleOutputs ? batchViewHelpers.outputCountLabel(activeOutputProfiles.length) : state.format
      : "Sin salida activa",
    sizeLabel: activeOutputProfiles.length ? hasMultipleOutputs ? "Por salida" : state.size.replace("x", " × ") : "-",
    backgroundLabel: activeOutputProfiles.length ? hasMultipleOutputs ? "Por salida" : settingsViewHelpers.backgroundLabel(state.background) : "-",
    destinationText,
    namingLabel: activeOutputProfiles.length ? hasMultipleOutputs ? "Por salida" : namingHumanLabel() : "-",
    example: activeOutputProfiles.length ? hasMultipleOutputs ? outputNameForProfile(activeOutputProfiles[0]) : namingExample() : "-",
    warningSummaryHtml: warningSummary,
    temporaryNoticeHtml: !outputMatchesProfile(activeOutputProfile()) ? inspectorOutputViewHelpers.outputTemporaryNoticeHtml() : "",
  });

  renderExportResult();

  $("#issue-list").innerHTML = issueListHtml();
}

function presetSummaryLine() {
  return settingsViewHelpers.presetSummaryLine({
    background: state.background,
    format: state.format,
    size: state.size,
  });
}

function destinationCompactLabel() {
  return outputProfileViewHelpers.destinationCompactLabel({
    destinationMode: state.destinationMode,
    destinationValue: state.destinationValue,
  });
}

function namingHumanLabel() {
  return outputProfileViewHelpers.namingHumanLabel({
    naming: state.naming,
    suffix: state.suffix,
  });
}

function outputWarningSummary(issues) {
  return exportPreflightViewHelpers.outputWarningSummaryHtml({
    issues,
    firstIssue: firstActionableIssue(),
    visibleWarningCount: visibleWarningCount(),
  });
}

function issueListHtml() {
  return exportPreflightViewHelpers.issueListHtml({
    hasActiveBatch: hasBatch(),
    batch: state.batch,
    rows: issueRows(),
    counts: preflightCounts(),
    warningCount: visibleWarningCount(),
  });
}

function issueRows() {
  return exportPreflightViewHelpers.issueRows({
    scanOmissions: scanOmissions().map((item) => ({
      ...item,
      reasonLabel: batchViewHelpers.omissionReasonLabel(item.reason),
      severity: omissionSeverity(item),
    })),
    images: activeImages().map((image) => ({
      ...image,
      exportStatus: exportItemState(image)?.status,
    })),
    errors: state.errors,
    statusLabels,
  });
}

function exportStatusClass(ready, issues = preflightIssues()) {
  return exportPreflightViewHelpers.exportStatusClass({
    hasActiveBatch: hasBatch(),
    issues,
    ready,
    status: state.exportStatus,
  });
}

function exportPreflightRows(issues, exportable, ready) {
  return exportPreflightViewHelpers.exportPreflightRows({
    batch: state.batch,
    destinationFallback: destinationFallbackLabel(),
    destinationMissing: state.destinationMode === "custom" && !state.destinationValue.trim(),
    exportable,
    ignoredCount: ignoredOmissions().length,
    ignoredSummary: ignoredSummaryText(),
    issues,
    naming: state.naming,
    namingExample: namingExample(),
    ready,
    warningCount: visibleWarningCount(),
  });
}

function exportPanelStatusLabel(ready, issues = preflightIssues()) {
  return exportPreflightViewHelpers.exportPanelStatusLabel({
    status: state.exportStatus,
    paused: state.paused,
    batch: state.batch,
    hasActiveBatch: hasBatch(),
    ready,
    issues,
  });
}

function exportPreflightSummary(issues, exportable, ready) {
  return exportPreflightViewHelpers.exportPreflightSummary({ issues, exportable, ready });
}

function namingExample() {
  const image = exportableImages()[0] || selectedImage();
  const originalName = image?.name || "imagen_001.png";
  return outputProfileViewHelpers.namingExample({
    folder: activeFolders()[0]?.name || "lote",
    format: state.format,
    naming: state.naming,
    original: originalName.replace(/\.[^.]+$/, ""),
    suffix: state.suffix,
  });
}

function renderExportResult() {
  const target = $("#export-result");
  const resultStatuses = ["running", "completed", "partial", "failed"];
  const shouldShow = resultStatuses.includes(state.exportStatus) || state.exportJobId || state.exportResult;
  const historyHtml = state.outputBrowserOpen ? "" : exportHistoryHelpers.exportHistoryHtml(state.exportHistory);
  if (!shouldShow) {
    target.innerHTML = historyHtml;
    return;
  }

  const total = Number(state.exportResult?.total ?? exportableImages().length ?? 0);
  const processed = Number(state.exportResult?.processed ?? state.processed ?? 0);
  const errors = Number(state.exportResult?.errors ?? state.exportIssues.filter((issue) => issue.level === "error").length ?? 0);
  const destinations = state.exportDestinations.length
    ? state.exportDestinations
    : Array.isArray(state.exportResult?.destinations)
      ? state.exportResult.destinations
      : [];
  const issues = state.exportIssues.length ? state.exportIssues : state.errors;
  const items = Array.isArray(state.exportCompletedItems) ? state.exportCompletedItems.slice(-8) : [];
  const outputGroups = exportResultViewHelpers.outputBrowserGroups({
    items: state.exportCompletedItems,
    destinations,
  });
  const outputBrowserHtml = state.outputBrowserOpen
    ? exportResultViewHelpers.exportOutputBrowserHtml({
      groups: outputGroups,
      total: Math.max(0, processed - errors) || items.filter((item) => item.success !== false).length,
    })
    : "";
  const title = exportResultTitle();
  const meta = exportResultMeta(processed, total, errors);
  const actionsHtml = exportResultActionsHtml(issues, destinations, outputGroups);

  target.innerHTML = exportResultViewHelpers.exportResultHtml({
    status: state.exportStatus,
    title,
    meta,
    processed,
    total,
    errors,
    destinations,
    destinationFallback: destinationFallbackLabel(),
    currentFileLabel: currentExportFileLabel(),
    issues,
    issueSummary: exportIssueActionText(issues[0]),
    outputBrowserHtml,
    items,
    actionsHtml,
  }) + historyHtml;
}

function exportResultTitle() {
  return exportResultViewHelpers.exportResultTitle(state.exportStatus, state.paused);
}

function exportResultMeta(processed, total, errors) {
  return exportResultViewHelpers.exportResultMeta({
    status: state.exportStatus,
    processed,
    total,
    errors,
  });
}

function currentExportFileLabel() {
  return exportResultViewHelpers.currentExportFileLabel({
    images: exportableImages(),
    processed: state.processed,
    statusText: state.statusText,
  });
}

function exportIssueActionText(issue) {
  return exportResultViewHelpers.exportIssueActionText(issue, {
    existingOutput: preflightHelpers.issueMentionsExistingOutput(issue),
  });
}

function exportResultActionsHtml(issues, destinations, outputGroups = []) {
  const hasOutputBlocker = issues.some(exportStateHelpers.isOutputConfigurationIssue);
  return exportResultViewHelpers.exportResultActionsHtml({
    status: state.exportStatus,
    issues,
    destinations,
    canEditOutput: hasOutputBlocker,
    canBrowseOutputs: outputGroups.length > 1,
    canOpenOutput: Boolean(outputDestinationToOpen()),
    canRetry: isExportReady(),
    canRetryFailed: retryableFailedExportImages().length > 0,
    hasOutputBlocker,
    outputBrowserOpen: state.outputBrowserOpen,
  });
}

function destinationFallbackLabel() {
  const profiles = exportOutputProfiles();
  if (!profiles.length) {
    return "Sin salida activa";
  }
  return outputProfileViewHelpers.destinationFallbackLabel({
    destinationMode: state.destinationMode,
    destinationValue: state.destinationValue,
    destinations: profiles.length > 1 ? profiles.map(outputProfileViewHelpers.profileDestinationPreviewLabel) : [],
  });
}

function beginOutputEdit() {
  state.outputDraft = {
    format: state.format,
    size: state.size,
    background: state.background,
    destinationMode: state.destinationMode,
    destinationValue: state.destinationValue,
    naming: state.naming,
    suffix: state.suffix,
    maxFileSizeKb: state.maxFileSizeKb,
  };
  state.outputEditMode = true;
  state.presetEditorOpen = false;
  state.inspectorTab = "output";
  state.statusText = "Editando salida";
  render();
}

function applyOutputEdit() {
  state.outputDraft = null;
  state.outputEditMode = false;
  clearOutputConfigurationFailures();
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = "Salida aplicada al lote";
  persistExportPreferences();
  render();
}

function cancelOutputEdit() {
  if (state.outputDraft) {
    Object.assign(state, state.outputDraft);
  }
  state.outputDraft = null;
  state.outputEditMode = false;
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = "Edición cancelada";
  persistExportPreferences();
  render();
}

function saveCurrentOutputProfile() {
  const current = currentOutputProfileData();
  const index = state.outputProfiles.findIndex((profile) => profile.id === state.activeOutputProfileId);
  if (index < 0) {
    state.outputProfiles.push({ ...current, enabled: true });
  } else {
    state.outputProfiles[index] = {
      ...state.outputProfiles[index],
      ...current,
      id: state.activeOutputProfileId,
      name: state.outputProfiles[index].name || current.name,
      enabled: Boolean(state.outputProfiles[index].enabled),
    };
  }
  state.outputProfiles = outputProfileHelpers.normalizeOutputProfileList(state.outputProfiles, state.activeOutputProfileId);
  state.outputDraft = null;
  state.outputEditMode = false;
  clearOutputConfigurationFailures();
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = "Salida guardada";
  persistOutputProfiles();
  render();
}

function saveCurrentOutputAsNewProfile() {
  const sourceName = activeOutputProfile()?.name || "Salida";
  const name = window.prompt("Nombre de la nueva salida", `${sourceName} copia`);
  if (name === null) {
    return;
  }
  const profile = outputProfileHelpers.normalizeOutputProfile({
    ...currentOutputProfileData(),
    id: outputProfileHelpers.uniqueOutputProfileId(name || "formato", Date.now()),
    name: name.trim() || "Nueva salida",
    enabled: true,
  });
  state.outputProfiles = outputProfileHelpers.normalizeOutputProfileList([...state.outputProfiles, profile], profile.id);
  state.activeOutputProfileId = profile.id;
  state.outputProfileEditorId = profile.id;
  state.outputProfileDraft = { ...profile };
  state.outputDraft = null;
  state.outputEditMode = false;
  clearOutputConfigurationFailures();
  persistOutputProfiles();
  state.statusText = `Nueva salida: ${profile.name}`;
  render();
}

function discardOutputOverrides() {
  const profile = activeOutputProfile();
  if (!profile) {
    return;
  }
  state.outputDraft = null;
  state.outputEditMode = false;
  applyOutputProfile(profile.id, { statusText: "Cambios sin guardar descartados" });
}

function clearOutputConfigurationFailures() {
  const nextErrors = exportStateHelpers.clearOutputConfigurationIssues(state.errors);
  const nextExportIssues = exportStateHelpers.clearOutputConfigurationIssues(state.exportIssues);
  const changed = nextErrors.length !== state.errors.length || nextExportIssues.length !== state.exportIssues.length;
  if (!changed) {
    return false;
  }
  state.errors = nextErrors;
  state.exportIssues = nextExportIssues;
  if (state.exportStatus === "failed") {
    state.exportStatus = isExportReady() ? "ready" : "blocked";
  }
  return true;
}

function exportStatusLabel(ready) {
  return settingsViewHelpers.exportStatusLabel({
    exportStatus: state.exportStatus,
    paused: state.paused,
    ready,
  });
}
