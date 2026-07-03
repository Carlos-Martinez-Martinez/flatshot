function renderPreview() {
  const image = selectedImage();
  const visibleImages = filteredImages();
  const filterIsEmpty = hasBatch() && activeImages().length > 0 && visibleImages.length === 0;
  const isBridgeImage = image?.source === "bridge";
  const previewControlsDisabled = !image || state.previewStatus === "empty" || state.previewStatus === "error";
  const compareControlsDisabled = !image || isBridgeImage || state.previewStatus === "empty" || state.previewStatus === "error";
  const previewName = image
    ? image.name
    : filterIsEmpty
      ? "Sin imágenes en este filtro"
    : state.batch === "none"
      ? "Selecciona una carpeta"
      : state.batch === "empty"
        ? "No se encontraron imágenes compatibles"
        : state.batch === "scanning"
          ? "Escaneando carpeta..."
          : "Selecciona una imagen";
  $("#preview-name").textContent = previewName;
  $("#preview-name").title = previewName;
  $("#preview-subtitle").textContent = previewSubtitle(image);
  $("#zoom-label").textContent = `${currentViewerZoom()}%`;
  const visibleIndex = visibleImages.findIndex((item) => item.id === state.selectedImageId);
  $("#viewer-position").textContent = visibleIndex >= 0
    ? `${visibleIndex + 1} / ${visibleImages.length}`
    : activeImages().length ? "Sin selección" : "Sin imagen";
  $("#preview-meta").textContent = isBridgeImage
    ? bridgePreviewMeta()
    : image ? state.activePreset : "Sin lote";
  const outputContext = $("#preview-output-context");
  if (outputContext) {
    outputContext.innerHTML = image && hasBatch()
      ? previewViewHelpers.viewerOutputContextHtml(galleryActiveOutputContext())
      : "";
  }
  const previewBackgroundMode = backgroundPresetHelpers.backgroundVisualMode(state.previewBg, backgroundHelperOptions());
  const previewBackgroundColor = backgroundPresetHelpers.backgroundCssColor(state.previewBg, backgroundHelperOptions());
  const canvasArea = $("#canvas-area");
  canvasArea.className = `canvas-area bg-${previewBackgroundMode}`;
  if (previewBackgroundColor) {
    canvasArea.style.setProperty("--custom-preview-bg", previewBackgroundColor);
  } else {
    canvasArea.style.removeProperty("--custom-preview-bg");
  }
  $$(".preview-toolbar [data-preview-mode]").forEach((button) => {
    button.classList.toggle("active", button.dataset.previewMode === state.previewMode);
    button.disabled = button.dataset.previewMode === "processed"
      ? previewControlsDisabled
      : compareControlsDisabled;
  });
  $$(".background-switch [data-preview-bg]").forEach((button) => {
    const previewBg = backgroundPresetHelpers.normalizePreviewBackgroundValue(state.previewBg, backgroundHelperOptions());
    const isCustom = button.dataset.previewBg === "custom";
    const isActive = isCustom ? Boolean(outputProfileHelpers.parseRgbBackground(previewBg)) : button.dataset.previewBg === previewBg;
    button.classList.toggle("active", isActive);
    button.disabled = previewControlsDisabled;
  });
  const customFields = $(".viewer-bg-custom-fields");
  if (customFields) {
    syncRgbVisualControlFromValue(customFields, state.previewBg);
    customFields.classList.toggle("active", Boolean(outputProfileHelpers.parseRgbBackground(state.previewBg)));
    const colorPicker = customFields.querySelector("[data-preview-bg-picker]");
    if (colorPicker) {
      colorPicker.disabled = previewControlsDisabled;
    }
  }
  renderGuideToolbarState();
  $$("[data-action='zoom-height'], [data-action='zoom-width'], [data-action='zoom-out'], [data-action='zoom-in'], [data-action='force-preview-error']").forEach((button) => {
    button.disabled = previewControlsDisabled;
  });
  $$("[data-action='zoom-height'], [data-action='zoom-width']").forEach((button) => {
    const expectedMode = button.dataset.action === "zoom-height"
      ? "height"
      : "width";
    const active = state.fitMode === expectedMode;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", button.classList.contains("active") ? "true" : "false");
  });
  $$("[data-action='previous-image'], [data-action='next-image']").forEach((button) => {
    button.disabled = visibleImages.length < 2;
  });

  const previewPanel = $("#preview-panel");
  if (previewPanel) {
    previewPanel.className = `preview-panel preview-panel--${previewOrientation()}`;
  }
  const canvas = $("#preview-canvas");
  canvas.className = `preview-canvas ${state.previewMode} bg-${previewBackgroundMode} ${previewStateHelpers.viewerModeClass(state.fitMode)}`;
  canvas.style.setProperty("--preview-scale", previewStateHelpers.isAutoViewerMode(state.fitMode) ? "1" : String(state.zoom / 100));
  applyViewerPanDom();

  if (state.batch === "none") {
    canvas.innerHTML = initialStateHtml();
    finishPreviewRender();
    return;
  }

  if (state.batch === "scanning") {
    canvas.innerHTML = scanningStateHtml();
    finishPreviewRender();
    return;
  }

  if (state.batch === "empty") {
    canvas.innerHTML = emptyStateViewHelpers.emptyStateHtml({
      variant: "warning",
      title: "No se encontraron imágenes compatibles",
      detail: state.scanDiagnostics.totalOmitted
        ? ignoredSummaryText()
        : "Esta carpeta no contiene imágenes compatibles.",
      actionLabel: "",
      action: "",
      meta: state.scanStatus || "",
    });
    finishPreviewRender();
    return;
  }

  if (filterIsEmpty) {
    canvas.innerHTML = emptyStateViewHelpers.emptyStateHtml({
      variant: "inline",
      title: "No hay imágenes en este filtro",
      detail: filterEmptyDetail(),
      actionLabel: "Ver todas",
      action: "clear-filter",
      meta: `${activeImages().length} imágenes en el lote`,
    });
    finishPreviewRender();
    return;
  }

  if (!image || state.previewStatus === "empty") {
    canvas.innerHTML = emptyStateViewHelpers.emptyStateHtml({
      variant: "inline",
      title: "Selecciona una imagen",
      detail: "Elige una miniatura para revisar.",
      actionLabel: activeImages().length ? "Seleccionar primera" : "",
      action: activeImages().length ? "select-first-image" : "",
      meta: activeImages().length ? `${activeImages().length} imágenes en el lote` : "",
    });
    finishPreviewRender();
    return;
  }

  if (isBridgeImage) {
    canvas.innerHTML = realPreviewHtml(image);
    finishPreviewRender();
    return;
  }

  if (state.previewStatus === "loading") {
    canvas.innerHTML = previewViewHelpers.previewLoadingHtml(image.name);
    finishPreviewRender();
    return;
  }

  if (state.previewStatus === "error") {
    canvas.innerHTML = previewStateHtml("Vista no disponible", "Revisa alpha o archivo fuente.");
    finishPreviewRender();
    return;
  }

  canvas.innerHTML = previewViewHelpers.mockPreviewHtml({
    warning: state.previewStatus === "warning" ? "Render con fallback. Revisa antes de exportar." : "",
  });
  finishPreviewRender();
}

function finishPreviewRender() {
  renderGuideOverlay();
  queueFitZoomRefresh();
}

function queueFitZoomRefresh() {
  if (fitZoomFrame) {
    window.cancelAnimationFrame(fitZoomFrame);
  }
  fitZoomFrame = window.requestAnimationFrame(() => {
    fitZoomFrame = 0;
    updateFitZoomReadout();
  });
}

function updateFitZoomReadout() {
  const label = $("#zoom-label");
  if (!label) {
    return;
  }
  if (!previewStateHelpers.isAutoViewerMode(state.fitMode)) {
    label.textContent = `${state.zoom}%`;
    renderGuideOverlay();
    return;
  }

  const zoom = calculateFitZoom();
  state.fitZoom = zoom;
  label.textContent = `${zoom}%`;
  if (!viewerPanState.active) {
    clampViewerPan();
    applyViewerPanDom();
  }
  renderGuideOverlay();
}

function calculateFitZoom() {
  const canvas = $("#preview-canvas");
  if (!canvas) {
    return 100;
  }
  const image = canvas.querySelector(".preview-image");
  const naturalWidth = Number(image?.naturalWidth || image?.getAttribute("width") || state.previewData?.width || 0);
  const naturalHeight = Number(image?.naturalHeight || image?.getAttribute("height") || state.previewData?.height || 0);
  if (!naturalWidth || !naturalHeight || !canvas.clientWidth || !canvas.clientHeight) {
    canvas.style.removeProperty("--fit-width");
    canvas.style.removeProperty("--fit-height");
    return 100;
  }
  const layout = previewStateHelpers.viewerFitLayout({
    canvasHeight: canvas.clientHeight,
    canvasWidth: canvas.clientWidth,
    mode: state.fitMode,
    naturalHeight,
    naturalWidth,
  });
  canvas.style.setProperty("--fit-width", `${layout.width}px`);
  canvas.style.setProperty("--fit-height", `${layout.height}px`);
  return layout.zoom;
}

function realPreviewHtml(image) {
  if (state.previewStatus === "loading") {
    return previewViewHelpers.previewLoadingHtml(image.name);
  }

  if (state.previewStatus === "error") {
    return previewStateHtml("Vista no disponible", state.previewError || "Revisa la imagen fuente.");
  }

  if (state.previewData?.src) {
    return previewViewHelpers.realPreviewImageHtml({
      src: state.previewData.src,
      imageName: image.name,
      width: state.previewData.width,
      height: state.previewData.height,
      zoom: state.zoom,
      inlineSize: !previewStateHelpers.isAutoViewerMode(state.fitMode),
      warning: state.previewData.warning,
    });
  }

  return previewViewHelpers.realPreviewPlaceholderHtml({
    imageName: image.name,
    imagePath: image.path,
  });
}

function bridgePreviewMeta() {
  return previewStateHelpers.bridgePreviewMeta({
    activePreset: state.activePreset,
    engineLabel: shadowEngineLabels[state.settings.shadow_engine] || "",
    previewData: state.previewData,
    previewError: state.previewError,
    previewStatus: state.previewStatus,
  });
}

function previewSettingsLabel() {
  return previewStateHelpers.previewSettingsLabel({
    activePresetSource: activePresetItem()?.source,
    bridgeMode: state.bridgeMode,
    presetDirty: state.presetDirty,
  });
}

function outputSizeDisplay() {
  const size = outputProfileHelpers.parseOutputSize(state.size);
  return `${size.width}×${size.height}`;
}

function viewerOutputCompactLabel() {
  return previewViewHelpers.viewerOutputCompactLabel({
    backgroundLabel: settingsViewHelpers.backgroundLabel(state.background),
    format: state.format,
    sizeLabel: outputSizeDisplay(),
  });
}

function previewStateHtml(title, detail) {
  return emptyStateViewHelpers.emptyStateHtml({ variant: "inline", title, detail });
}

function initialStateHtml() {
  return emptyStateViewHelpers.initialStateHtml({
    bridgeScanPath: state.bridgeScanPath,
    devMode,
  });
}

function scanningStateHtml() {
  return previewViewHelpers.scanningStateHtml(state.scanStatus);
}

function previewOrientation() {
  return previewStateHelpers.previewOrientation(state.previewData);
}

function previewSubtitle(image) {
  const filterIsEmpty = !image && hasBatch() && activeImages().length && !filteredImages().length;
  return previewStateHelpers.previewSubtitle({
    batch: state.batch,
    filterEmptyDetail: filterIsEmpty ? filterEmptyDetail() : "",
    filterIsEmpty,
    hasImage: Boolean(image),
    imageDetail: image?.detail,
    imageSource: image?.source,
    previewStatus: state.previewStatus,
    scanStatus: state.scanStatus,
  });
}
