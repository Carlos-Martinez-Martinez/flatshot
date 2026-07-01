function imageDimensions(image) {
  return appStateHelpers.imageDimensions(image);
}

function lowResolutionImageCount() {
  const targets = exportOutputProfiles().map((profile) => outputProfileHelpers.parseOutputSize(outputProfileHelpers.outputProfileSize(profile)));
  return appStateHelpers.lowResolutionImageCount({
    images: exportableImages(),
    targets,
  });
}

function isExportReady() {
  return preflightHelpers.isExportReady({
    activeOutputCount: exportOutputCount(),
    hasImageAdjustment: Boolean(String(state.activePreset || "").trim()),
    validationIssues: validationIssues(),
    hasBatch: hasBatch(),
    exportableCount: exportableImages().length,
  });
}

function uiState() {
  const counts = preflightCounts();
  const lotCounts = batchCounts();
  const image = selectedImage();
  return appStateHelpers.uiState({
    state,
    counts,
    lotCounts,
    selectedImage: image,
    hasBatch: hasBatch(),
    canExport: isExportReady(),
  });
}

function visibleWarningCount() {
  return batchCounts().nonBlockingWarnings;
}

function exportActionLabel(imageCount = batchCounts().exportableImages) {
  return batchViewHelpers.exportActionLabel(imageCount, exportOutputCount());
}

function plannedExportTotal() {
  return exportableImages().length * exportOutputCount();
}

function firstOmittedItem() {
  const omitted = actionableOmissions();
  return omitted.length ? omitted[0] : null;
}

function firstActionableIssue() {
  const omitted = firstOmittedItem();
  if (omitted) {
    return {
      level: "warning",
      title: "Archivo a revisar",
      file: omitted.name || "Archivo",
      detail: batchViewHelpers.omissionReasonLabel(omitted.reason),
      path: omitted.path || omitted.folder || "",
    };
  }

  const imageIssue = activeImages().find((image) => image.status === "error")
    || activeImages().find((image) => image.status === "warning")
    || activeImages().find((image) => exportItemState(image)?.status === "error");
  if (imageIssue) {
    return {
      level: imageIssue.status === "error" || exportItemState(imageIssue)?.status === "error" ? "error" : "warning",
      title: imageIssue.status === "error" ? "Imagen no exportable" : "Imagen con aviso",
      file: imageIssue.name,
      detail: imageIssue.detail || statusLabels[imageIssue.status] || "Revisar imagen",
      path: imageIssue.path || "",
    };
  }

  const issue = state.errors[0] || preflightIssues().find((item) => item.title !== "Sin lote") || null;
  return issue
    ? {
        level: issue.level,
        title: issue.title,
        file: "",
        detail: issue.detail,
        path: "",
      }
    : null;
}
