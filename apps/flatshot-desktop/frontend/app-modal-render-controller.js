function renderBatchDetail() {
  const modal = $("#batch-detail-modal");
  if (!modal) {
    return;
  }
  syncModalVisibility(modal, state.batchDetailOpen);
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
  syncModalVisibility(modal, state.exportConfirmOpen);
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

function renderQaLab() {
  const modal = $("#qa-lab-modal");
  if (!modal) {
    return;
  }
  syncModalVisibility(modal, state.qaLabOpen);
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
