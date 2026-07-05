function renderFooter() {
  const issues = [...validationIssues(), ...state.errors];
  const visible = getVisibleAppState();
  const counts = batchCounts();
  $("#footer-statusline").textContent = statusBarText();
  $("#bottom-status").textContent = state.statusText;
  $("#progress-fill").style.width = `${state.progress}%`;
  $("#progress-fill").className = state.exportStatus === "failed" ? "error" : state.exportStatus === "partial" ? "warning" : "";
  $(".progress-track").classList.toggle("is-idle", state.exportStatus !== "running");

  const hasReviewIssues = (hasBatch() || state.batch === "empty") && (
    issues.some((issue) => issue.title !== "Sin lote")
    || counts.reviewIssues > 0
    || activeImages().some((image) => image.status === "error" || image.status === "warning" || exportItemState(image)?.status === "error")
  );
  $("#review-errors").classList.toggle("is-hidden", !hasReviewIssues);
  $("#review-errors").disabled = !hasReviewIssues;
  $("#review-errors").textContent = "Revisar avisos";
  $("#pause-export").classList.toggle("is-hidden", state.exportStatus !== "running");
  $("#pause-export").textContent = state.paused ? "Reanudar" : "Pausar";
  $("#stop-export").classList.toggle("is-hidden", state.exportStatus !== "running");
  $("#open-output").classList.add("is-hidden");
  $("#open-output").disabled = true;
  $("#primary-action").classList.add("is-hidden");

  const primaryButtons = [$("#primary-action"), $("#top-primary-action")].filter(Boolean);
  const primaryActionState = visible.primaryAction || {};
  primaryButtons.forEach((button) => {
    button.disabled = primaryActionState.enabled === false;
    button.textContent = primaryActionState.label || "Seleccionar carpeta";
    button.title = visible.subtitle || primaryActionState.label || "";
  });
}

function renderAccessibilityHints() {
  const visible = getVisibleAppState();
  const counts = batchCounts();
  setControlHint($("#top-primary-action"), topPrimaryHint(visible));
  setControlHint($("#top-secondary-action"), visible.secondaryAction ? `${visible.secondaryAction.label}. Atajo: Ctrl+E si exporta.` : "");
  setControlHint($("[data-action='open-batch-detail']"), "Abrir detalle del lote");
  setControlHint($("[data-action='open-app-settings']"), "Abrir salidas");
  setControlHint($("[data-action='toggle-inspector']"), "Mostrar u ocultar detalle técnico");
  setControlHint($("#image-search"), "Buscar por nombre, referencia o ruta");
  setControlHint($("#image-search-clear"), "Limpiar búsqueda");

  const galleryViewHints = {
    thumbs: "Ver galería como miniaturas",
    list: "Ver galería como lista compacta",
  };
  $$("[data-gallery-view]").forEach((button) => {
    setControlHint(button, galleryViewHints[button.dataset.galleryView] || button.textContent.trim());
  });

  const filterCounts = {
    all: activeImages().length,
    valid: counts.readyImages,
    warnings: counts.warningImages,
    excluded: counts.nonExportableImages,
  };
  const filterHints = {
    all: "Mostrar todas las imágenes",
    valid: "Mostrar imágenes listas",
    warnings: "Mostrar imágenes con aviso",
    excluded: "Mostrar imágenes ignoradas o no exportables",
  };
  $$("[data-filter]").forEach((button) => {
    const filter = button.dataset.filter;
    setControlHint(button, `${filterHints[filter] || button.textContent.trim()} · ${filterCounts[filter] || 0}`);
  });

  const previewModeHints = {
    processed: "Ver previsualización con la salida activa",
    original: "Ver imagen original",
    compare: "Comparar original y previsualización",
  };
  $$("[data-preview-mode]").forEach((button) => {
    setControlHint(button, previewModeHints[button.dataset.previewMode] || button.textContent.trim());
    button.setAttribute("aria-pressed", button.classList.contains("active") ? "true" : "false");
  });

  const backgroundHints = {
    rgb230: "Fondo gris claro RGB 230",
    white: "Fondo blanco",
    [SOFT_BLACK_PREVIEW_BG]: "Fondo negro suave RGB 32, 34, 37",
    transparent: "Fondo transparente",
    custom: "Fondo personalizado con los campos RGB",
  };
  $$("[data-preview-bg]").forEach((button) => {
    setControlHint(button, backgroundHints[button.dataset.previewBg] || button.textContent.trim());
    button.setAttribute("aria-pressed", button.classList.contains("active") ? "true" : "false");
  });

  const zoomHints = {
    "previous-image": "Imagen anterior. Atajo: flecha izquierda",
    "next-image": "Imagen siguiente. Atajo: flecha derecha",
    "zoom-height": "Ajustar a la altura del visor",
    "zoom-width": "Ajustar a la anchura del visor",
    "zoom-out": "Reducir zoom",
    "zoom-in": "Aumentar zoom",
  };
  Object.entries(zoomHints).forEach(([action, hint]) => {
    setControlHint($(`[data-action='${action}']`), hint);
  });

  $$(".settings-panel [data-inspector-tab]").forEach((button) => {
    const active = button.dataset.inspectorTab === state.inspectorTab;
    button.setAttribute("aria-pressed", active ? "true" : "false");
    setControlHint(button, `${button.textContent.trim()} del inspector`);
  });
}

function topPrimaryHint(visible) {
  return topStatusViewHelpers.topPrimaryHint(visible);
}

function setControlHint(target, hint) {
  if (!target || !hint) {
    return;
  }
  target.title = hint;
  if (!target.getAttribute("aria-label") && target.textContent.trim().length <= 2) {
    target.setAttribute("aria-label", hint.replace(/\s*\. Atajo:.*$/, ""));
  }
}

function statusBarText() {
  const images = activeImages();
  const counts = batchCounts();
  const selectedIndex = images.findIndex((image) => image.id === state.selectedImageId);
  return topStatusViewHelpers.statusBarText({
    batch: state.batch,
    counts,
    destinationMode: state.destinationMode,
    destinationValue: state.destinationValue,
    exportResultProcessed: state.exportResult?.processed,
    exportResultTotal: state.exportResult?.total,
    exportStatus: state.exportStatus,
    exportableImageCount: exportableImages().length,
    firstErrorDetail: state.errors[0]?.detail,
    hasOutputBlocker: hasOutputConfigurationIssue(),
    imageCount: images.length,
    outputCount: exportOutputCount(),
    paused: state.paused,
    plannedTotal: plannedExportTotal(),
    processed: state.processed,
    scanStatus: state.scanStatus,
    selectedIndex,
    statusText: state.statusText,
  });
}

function previewFooterLabel() {
  return previewStateHelpers.previewFooterLabel({
    previewStatus: state.previewStatus,
    selectedImageSource: selectedImage()?.source,
  });
}
