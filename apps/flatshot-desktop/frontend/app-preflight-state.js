function batchCounts() {
  const images = activeImages();
  const diagnostics = state.scanDiagnostics || emptyScanDiagnostics();
  const exportables = exportableImages();
  return preflightHelpers.calculateBatchCounts({
    batch: state.batch,
    images,
    exportables,
    diagnostics,
    omissions: scanOmissions(),
    exportItemStatuses: exportItemStatusMap(images),
    stateErrors: state.errors,
    exportStatus: state.exportStatus,
    blockingValidationIssueCount: blockingValidationIssues().length,
    ...omissionReasonOptions(),
  });
}

function exportItemState(image) {
  return appStateHelpers.exportItemState(image, state.exportCompletedItems);
}

function filteredImages() {
  const images = activeImages();
  return galleryHelpers.filteredImages(images, {
    exportItemStatuses: exportItemStatusMap(images),
    filter: state.filter,
    filters: BATCH_FILTERS,
    search: state.search,
  });
}

function validationIssues() {
  return appStateHelpers.validationIssues({
    state,
    exportableImages: exportableImages(),
    exportOutputProfiles: exportOutputProfiles(),
    outputProfileRawFromProfile,
    outputProfileValidation: outputProfileHelpers.outputProfileValidation,
  });
}

function preflightIssues() {
  const counts = batchCounts();
  return preflightHelpers.buildPreflightIssues({
    validationIssues: validationIssues(),
    stateErrors: state.errors,
    counts,
    actionableOmissions: actionableOmissions(),
    hasBatch: hasBatch(),
    warningImages: imageWarningCount(),
    errorImages: excludedImageCount(),
    exportableCount: exportableImages().length,
    actionableOmissionSummary: actionableOmissionSummaryText(),
  });
}

function preflightCounts() {
  return preflightHelpers.preflightCounts(preflightIssues());
}

function exportConfirmationRisks() {
  const counts = batchCounts();
  const risks = [];
  const exportableWarningImages = exportableImages().filter((image) => image.status === "warning").length;
  const actionableOmitted = actionableOmissions();

  validationIssues()
    .filter((issue) => issue.level === "error" && issue.title !== "Sin lote")
    .forEach((issue) => {
      risks.push({
        id: `blocker-${issue.title}`,
        level: "error",
        blocking: true,
        title: issue.title,
        detail: issue.detail || "Resuelve este punto antes de exportar.",
      });
    });

  if (actionableOmitted.length > 0) {
    risks.push({
      id: "omitted-file-incidents",
      level: "warning",
      title: `${actionableOmitted.length} archivo${actionableOmitted.length === 1 ? "" : "s"} a revisar`,
      detail: actionableOmissionSummaryText(),
    });
  }

  if (exportableWarningImages > 0) {
    risks.push({
      id: "image-warnings",
      level: "warning",
      title: `${preflightHelpers.countText(exportableWarningImages, "imagen", "imágenes")} con aviso`,
      detail: "Se exportarán, pero conviene revisarlas si el lote es de producción.",
    });
  }

  if (counts.nonExportableImages > 0) {
    risks.push({
      id: "non-exportable-images",
      level: "warning",
      title: `${preflightHelpers.countText(counts.nonExportableImages, "imagen", "imágenes")} excluida${counts.nonExportableImages === 1 ? "" : "s"}`,
      detail: "No se incluirán en la exportación.",
    });
  }

  const existingOutputIssue = [...state.errors, ...state.exportIssues].find(preflightHelpers.issueMentionsExistingOutput);
  if (existingOutputIssue) {
    risks.push({
      id: "existing-output-blocker",
      level: "error",
      blocking: true,
      title: "Archivos ya existentes",
      detail: "Cambia el destino o el nombre de archivo antes de exportar de nuevo.",
    });
  } else if (hasPreviousExportDestination()) {
    risks.push({
      id: "previous-export-destination",
      level: "warning",
      title: "Destino usado en la exportación anterior",
      detail: "Si ya existen archivos con el mismo nombre, el motor local no debe sobrescribirlos sin validación.",
    });
  }

  const lowResolutionCount = lowResolutionImageCount();
  if (lowResolutionCount > 0) {
    risks.push({
      id: "low-resolution",
      level: "warning",
      title: `${preflightHelpers.countText(lowResolutionCount, "imagen", "imágenes")} por debajo del tamaño de salida`,
      detail: "La imagen puede ampliarse para llegar al tamaño configurado.",
    });
  }

  if (advancedSettingsDirty()) {
    risks.push({
      id: "advanced-settings",
      level: "warning",
      title: "Ajustes avanzados modificados",
      detail: "La exportación usará esos valores.",
    });
  }

  if (state.exportStatus === "failed" && state.errors.some((issue) => issue.level === "error" && !preflightHelpers.issueMentionsExistingOutput(issue))) {
    risks.push({
      id: "previous-export-errors",
      level: "warning",
      title: "Errores en la última exportación",
      detail: "Puedes reintentar, pero revisa el resultado si vuelve a fallar.",
    });
  }

  state.errors
    .filter((issue) => issue.level !== "error" && !preflightHelpers.issueMentionsExistingOutput(issue))
    .slice(0, 2)
    .forEach((issue, index) => {
      risks.push({
        id: `state-warning-${index}-${issue.title}`,
        level: "warning",
        title: issue.title || "Aviso",
        detail: issue.detail || "Revisa este punto antes de exportar.",
      });
    });

  return preflightHelpers.dedupeExportRisks(risks);
}

function hasPreviousExportDestination() {
  return ["completed", "partial"].includes(state.exportStatus) && Boolean(outputDestinationToOpen());
}
