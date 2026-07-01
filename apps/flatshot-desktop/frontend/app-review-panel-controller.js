function renderReviewPanel() {
  const target = $("#review-summary");
  if (!target) {
    return;
  }
  target.innerHTML = reviewPanelHtml();
}

function reviewPanelHtml() {
  const image = selectedImage();
  if (!image) {
    return inspectorReviewViewHelpers.reviewPanelHtml({
      lotSummaryHtml: lotInspectorSummaryHtml(),
      emptyStateHtml: emptyStateViewHelpers.emptyStateHtml({
      variant: "inline",
      title: "Selecciona una imagen",
      detail: "Elige una miniatura para revisar la imagen.",
      actionLabel: activeImages().length ? "Seleccionar primera imagen" : "",
      action: activeImages().length ? "select-first-image" : "",
    }),
    });
  }

  const reviewState = imageReviewState(image);
  const issues = imageReviewIssues(image);
  const outputName = outputNameForImage(image);
  const hasLocal = hasImageAdjustmentOverride(image);
  const images = activeImages();
  const selectedIndex = images.findIndex((item) => item.id === image.id);
  const canNavigate = images.length > 1;
  const outputDetail = viewerOutputCompactLabel();

  return inspectorReviewViewHelpers.reviewPanelHtml({
    lotSummaryHtml: lotInspectorSummaryHtml(),
    image,
    reviewState,
    issues,
    outputName,
    outputDetail,
    hasLocal,
    selectedIndexLabel: selectedIndex >= 0 ? `${selectedIndex + 1} de ${images.length}` : "Sin selección",
    canNavigate,
  });
}

function lotInspectorSummaryHtml() {
  const counts = batchCounts();
  const stateLabel = counts.blockingErrors
    ? `${counts.blockingErrors} bloqueo${counts.blockingErrors === 1 ? "" : "s"}`
    : counts.reviewIssues
      ? `${counts.reviewIssues} aviso${counts.reviewIssues === 1 ? "" : "s"}`
      : "Listo";
  return inspectorReviewViewHelpers.lotInspectorSummaryHtml({ counts, stateLabel });
}

function imageReviewState(image) {
  const exportState = exportItemState(image);
  const status = exportState?.status || (hasImageAdjustmentOverride(image) ? "adjusted" : image.status);
  if (status === "error") {
    return {
      tone: "error",
      label: exportState?.label || "Error",
      detail: image.exportable === false ? "No exportable" : image.detail || "Revisar antes de exportar",
    };
  }
  if (status === "warning") {
    return {
      tone: "warning",
      label: "Aviso",
      detail: image.detail || "Revisar antes de exportar",
    };
  }
  if (status === "exported") {
    return { tone: "ready", label: "Exportada", detail: "Exportación completada" };
  }
  if (status === "adjusted") {
    return { tone: "active", label: "Ajustada", detail: "Ajuste por imagen activo" };
  }
  return { tone: "ready", label: "Lista", detail: "Lista para exportar" };
}

function imageReviewIssues(image) {
  const issues = [];
  const exportState = exportItemState(image);
  if (image.status === "warning") {
    issues.push({
      level: "warning",
      title: "Aviso de imagen",
      detail: image.detail || "Conviene revisar esta imagen antes de exportar.",
    });
  }
  if (image.status === "error" || image.exportable === false) {
    issues.push({
      level: "error",
      title: "Imagen no exportable",
      detail: image.detail || "Esta imagen quedará fuera de la exportación.",
    });
  }
  if (exportState?.status === "error") {
    issues.push({
      level: "error",
      title: "Error de exportación",
      detail: exportState.label || "No se pudo exportar esta imagen.",
    });
  }
  if (image.id === state.selectedImageId && state.previewStatus === "warning" && state.previewData?.warning) {
    issues.push({
      level: "warning",
      title: "Vista con aviso",
      detail: state.previewData.warning,
    });
  }
  if (image.id === state.selectedImageId && state.previewStatus === "error") {
    issues.push({
      level: "error",
      title: "Vista no disponible",
      detail: state.previewError || "No se pudo generar la vista previa.",
    });
  }
  return issues;
}

function outputNameForImage(image, index = 1) {
  return outputProfileViewHelpers.outputNameForImage({
    folders: activeFolders(),
    format: state.format,
    image,
    index,
    naming: state.naming,
    suffix: state.suffix,
  });
}
