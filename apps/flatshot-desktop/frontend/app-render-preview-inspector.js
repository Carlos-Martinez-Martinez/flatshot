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
    outputContext.innerHTML = "";
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
  const customPreviewRgb = backgroundPresetHelpers.previewCustomRgbChannels(state.previewBg, backgroundHelperOptions());
  ["r", "g", "b"].forEach((channel, index) => {
    const input = $(`[data-preview-bg-channel="${channel}"]`);
    if (input) {
      input.value = String(customPreviewRgb[index]);
      input.disabled = previewControlsDisabled;
    }
  });
  const customSwatch = $("#preview-bg-custom-swatch");
  if (customSwatch) {
    customSwatch.style.setProperty("--custom-preview-bg-control", `rgb(${customPreviewRgb.join(", ")})`);
  }
  const customFields = $(".viewer-bg-custom-fields");
  if (customFields) {
    customFields.classList.toggle("active", Boolean(outputProfileHelpers.parseRgbBackground(state.previewBg)));
  }
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
  canvas.className = `preview-canvas ${state.previewMode} bg-${previewBackgroundMode} ${previewStateHelpers.viewerModeClass()}`;
  canvas.style.setProperty("--preview-scale", previewStateHelpers.isAutoViewerMode() ? "1" : String(state.zoom / 100));
  applyViewerPanDom();

  if (state.batch === "none") {
    canvas.innerHTML = initialStateHtml();
    queueFitZoomRefresh();
    return;
  }

  if (state.batch === "scanning") {
    canvas.innerHTML = scanningStateHtml();
    queueFitZoomRefresh();
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
    queueFitZoomRefresh();
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
    queueFitZoomRefresh();
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
    queueFitZoomRefresh();
    return;
  }

  if (isBridgeImage) {
    canvas.innerHTML = realPreviewHtml(image);
    queueFitZoomRefresh();
    return;
  }

  if (state.previewStatus === "loading") {
    canvas.innerHTML = previewViewHelpers.previewLoadingHtml(image.name);
    queueFitZoomRefresh();
    return;
  }

  if (state.previewStatus === "error") {
    canvas.innerHTML = previewStateHtml("Vista no disponible", "Revisa alpha o archivo fuente.");
    queueFitZoomRefresh();
    return;
  }

  canvas.innerHTML = previewViewHelpers.mockPreviewHtml({
    warning: state.previewStatus === "warning" ? "Render con fallback. Revisa antes de exportar." : "",
  });
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
  if (!previewStateHelpers.isAutoViewerMode()) {
    label.textContent = `${state.zoom}%`;
    return;
  }

  const zoom = calculateFitZoom();
  state.fitZoom = zoom;
  label.textContent = `${zoom}%`;
  if (!viewerPanState.active) {
    clampViewerPan();
    applyViewerPanDom();
  }
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
      inlineSize: !previewStateHelpers.isAutoViewerMode(),
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

function renderSettings() {
  renderReviewPanel();
  const settingsPanel = $(".settings-panel");
  if (settingsPanel) {
    settingsPanel.dataset.shadowEngine = state.settings.shadow_engine || "";
  }
  const activePreset = $("#active-preset");
  if (activePreset) {
    activePreset.textContent = state.activePreset;
  }
  $("#preset-source").textContent = `${state.activePreset} · ${presetSourceLabel()}`;
  $("#preset-dirty").textContent = settingsViewHelpers.presetDirtyLabel(state.presetDirty);
  $("#preset-dirty").classList.toggle("dirty", state.presetDirty);
  const presetItems = activePresetItems();
  const presetCount = $("#preset-count");
  if (presetCount) {
    presetCount.textContent = `${presetItems.length}`;
  }
  $("#preset-list").innerHTML = settingsViewHelpers.presetListHtml(presetItems, state.activePreset);

  Object.entries(state.settings).forEach(([key, value]) => {
    const input = $(`[data-setting="${key}"]`);
    const output = $(`#${key}-output`);
    const numberInput = $(`[data-setting-number="${key}"]`);
    if (input) {
      if (input.type === "checkbox") {
        input.checked = Boolean(value);
      } else {
        input.value = value;
        syncRangeFill(input);
      }
    }
    if (output) {
      output.textContent = value;
    }
    if (numberInput && document.activeElement !== numberInput) {
      numberInput.value = value;
    }
  });

  const image = selectedImage();
  const localOverride = currentImageOverride(image);
  const localActive = hasImageAdjustmentOverride(image);
  $("#local-adjustment").classList.toggle("active", localActive);
  $("#local-adjustment-text").textContent = settingsViewHelpers.localAdjustmentText(localActive);
  localOverrideKeys.forEach((key) => {
    const value = Number(localOverride[key] || 0);
    const input = $(`[data-local-setting="${key}"]`);
    const output = $(`#local-${key}-output`);
    const numberInput = $(`[data-local-setting-number="${key}"]`);
    if (input) {
      input.value = value;
      syncRangeFill(input);
    }
    if (output) {
      output.textContent = settingsViewHelpers.localSettingOutputText(value);
    }
    if (numberInput && document.activeElement !== numberInput) {
      numberInput.value = value;
    }
  });
  const savePresetButton = $("#save-preset");
  const savePresetState = settingsViewHelpers.savePresetButtonState(state.presetDirty);
  savePresetButton.disabled = savePresetState.disabled;
  savePresetButton.title = savePresetState.title;
  savePresetButton.textContent = savePresetState.text;
  savePresetButton.classList.toggle("primary", savePresetState.primary);
  const deletePresetButton = $("#delete-preset");
  if (deletePresetButton) {
    const deletePresetState = settingsViewHelpers.deletePresetButtonState(presetItems.length);
    deletePresetButton.disabled = deletePresetState.disabled;
    deletePresetButton.title = deletePresetState.title;
  }
  const advanced = $("#advanced-settings");
  const advancedSummaryTitle = advanced?.querySelector("summary strong");
  if (advancedSummaryTitle) {
    advancedSummaryTitle.textContent = settingsViewHelpers.advancedSummaryTitle(advancedDirtyCount());
  }
  renderLightingSceneControls();
}

function lightingSceneFieldValue(scene, field) {
  if (field === "ambient_intensity") {
    return scene.ambient_intensity;
  }
  if (field.startsWith("main.")) {
    return scene.main[field.slice(5)];
  }
  return undefined;
}

function lightingOutputId(field) {
  const names = {
    "main.height": "lighting-height-output",
    "main.size": "lighting-size-output",
    "main.intensity": "lighting-intensity-output",
    ambient_intensity: "lighting-ambient-output",
  };
  return names[field] || "";
}

function lightingSliderValue(field, value) {
  if (field === "main.intensity") {
    return Math.round(numberHelpers.clampNumber(value, 0, 1.5, defaultLightingScene.main.intensity) * 100);
  }
  return Math.round(numberHelpers.clampNumber(value, 0, 1, 0) * 100);
}

function renderLightingSceneControls() {
  const panel = $("#studio-lighting-panel");
  if (!panel) {
    return;
  }
  const enabled = state.settings.shadow_engine === "studio_2_5d";
  panel.hidden = !enabled;
  const scene = normalizeLightingScene(state.settings.lighting_scene);
  state.settings.lighting_scene = scene;
  const exactPresetId = lightingScenePresetId(scene);
  const rememberedPresetId = lightingScenePresets[state.lightingPresetId] ? state.lightingPresetId : "";
  const selectedPresetId = enabled ? exactPresetId || rememberedPresetId || "overhead_soft" : "";

  $$("[data-lighting-field]").forEach((input) => {
    const field = input.dataset.lightingField;
    const value = lightingSceneFieldValue(scene, field);
    if (input.tagName === "SELECT") {
      input.value = value;
    } else {
      const sliderValue = lightingSliderValue(field, value);
      input.value = sliderValue;
      syncRangeFill(input);
      const output = $(`#${lightingOutputId(field)}`);
      if (output) {
        if ("value" in output && document.activeElement !== output) {
          output.value = String(sliderValue);
        } else {
          output.textContent = String(sliderValue);
        }
      }
    }
    input.disabled = !enabled;
  });

  $$("[data-lighting-number-field]").forEach((input) => {
    const field = input.dataset.lightingNumberField;
    const value = lightingSliderValue(field, lightingSceneFieldValue(scene, field));
    if (document.activeElement !== input) {
      input.value = String(value);
    }
    input.disabled = !enabled;
  });

  $$("[data-lighting-preset]").forEach((button) => {
    const presetId = button.dataset.lightingPreset;
    const preset = lightingScenePresets[presetId];
    const selected = enabled && presetId === selectedPresetId;
    const exact = selected && lightingScenesEqual(scene, preset);
    button.disabled = !enabled;
    button.classList.toggle("active", selected);
    button.classList.toggle("is-modified", selected && !exact);
    button.setAttribute("aria-pressed", String(selected));
    button.title = selected && !exact ? "Preset modificado" : "";
  });

  const stage = $("#lighting-stage");
  const handle = $("#lighting-handle");
  if (stage) {
    stage.disabled = !enabled;
  }
  if (handle) {
    const left = ((scene.main.x + 1) / 2) * 100;
    const top = ((scene.main.y + 1) / 2) * 100;
    handle.style.left = `${left}%`;
    handle.style.top = `${top}%`;
  }
}

function lightingScenesEqual(first, second) {
  if (!second) {
    return false;
  }
  return JSON.stringify(normalizeLightingScene(first)) === JSON.stringify(normalizeLightingScene(second));
}

function lightingScenePresetId(scene) {
  return Object.entries(lightingScenePresets)
    .find(([, preset]) => lightingScenesEqual(scene, preset))?.[0] || "";
}

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

function advancedDirtyCount() {
  const presetSettings = normalizeSettings(activePresetItem()?.settings || defaultSettings);
  return settingsViewHelpers.advancedDirtyCount({
    currentSettings: state.settings,
    keys: visibleAdvancedSettingKeys(state.settings),
    presetDirty: state.presetDirty,
    presetSettings,
  });
}

function visibleAdvancedSettingKeys(settings = state.settings) {
  if (settings.shadow_engine === "studio_2_5d") {
    return advancedSettingKeys.filter((key) => key !== "angle");
  }
  return advancedSettingKeys;
}

function advancedSettingsDirty() {
  return advancedDirtyCount() > 0;
}

function inspectorMode() {
  return inspectorContextViewHelpers.inspectorMode({
    inspectorTab: state.inspectorTab,
    outputEditMode: state.outputEditMode,
  });
}

function renderInspector() {
  const panel = $(".settings-panel");
  const mode = inspectorMode();
  const validTabs = ["review", "output", "warnings", "advanced"];
  if (!validTabs.includes(state.inspectorTab)) {
    state.inspectorTab = "review";
  }
  panel.classList.toggle("is-editing-output", state.outputEditMode);
  panel.classList.toggle("is-editing-preset", state.presetEditorOpen || mode === "advanced");
  panel.classList.toggle("is-inspector-subview", mode !== "summary");
  panel.classList.toggle("is-advanced-subview", mode === "advanced");
  const start = $("#inspector-start");
  start.classList.remove("is-hidden");
  if (mode === "summary") {
    start.innerHTML = inspectorCardsHtml();
  } else {
    start.innerHTML = inspectorSubviewHeaderHtml(mode);
  }
  $(".inspector-tabs").classList.add("is-hidden");
  $$(".settings-panel [data-inspector-tab]").forEach((button) => {
    const active = button.dataset.inspectorTab === state.inspectorTab;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", active ? "true" : "false");
  });
  $$(".settings-panel [data-inspector-section]").forEach((section) => {
    const sectionName = section.dataset.inspectorSection;
    const visible = (mode === "output" && sectionName === "output")
      || (mode === "advanced" && sectionName === "advanced")
      || (mode === "warnings" && sectionName === "warnings");
    section.classList.toggle(
      "is-hidden",
      !visible
    );
  });
  syncAdvancedInspectorDetails(mode);
}

function syncAdvancedInspectorDetails(mode) {
  const detailsItems = $$(".settings-panel details.inspector-disclosure[data-inspector-section='advanced']");
  detailsItems.forEach((details) => {
    if (mode !== "advanced") {
      setInspectorDisclosureOpenState(details, false);
    }
  });
  if (mode !== "advanced") {
    pendingAdvancedDisclosure = "";
    return;
  }

  if (state.presetEditorOpen) {
    detailsItems.forEach((details) => {
      setInspectorDisclosureOpenState(details, details.classList.contains("preset-section"));
    });
    pendingAdvancedDisclosure = "";
    return;
  }

  const editableDetails = detailsItems.filter((details) => !details.classList.contains("preset-section"));
  detailsItems
    .filter((details) => details.classList.contains("preset-section"))
    .forEach((details) => setInspectorDisclosureOpenState(details, false));

  if (pendingAdvancedDisclosure) {
    const preferred = editableDetails.find((details) => details.classList.contains(pendingAdvancedDisclosure));
    if (preferred) {
      editableDetails.forEach((details) => setInspectorDisclosureOpenState(details, details === preferred));
    }
    pendingAdvancedDisclosure = "";
    return;
  }

  if (editableDetails.some((details) => details.open)) {
    return;
  }

  editableDetails.forEach((details) => {
    setInspectorDisclosureOpenState(details, details.classList.contains("appearance-section"));
  });
}

function inspectorCardsHtml() {
  if (state.batch === "scanning") {
    return `
      <section class="inspector-card inspector-card--busy">
        <div class="inspector-card__head">
          <span>Escaneo</span>
          <strong>Escaneando carpeta...</strong>
        </div>
        <small>${escapeHtml(state.scanStatus || "Leyendo imágenes")}</small>
        ${exportPreflightViewHelpers.progressPanelHtml("Escaneando carpeta")}
      </section>
    `;
  }

  if (state.batch === "none") {
    return "";
  }

  return [
    lotInspectorCardHtml(),
    aspectInspectorCardHtml(),
    outputInspectorCardHtml(),
    selectedImageInspectorCardHtml(),
    issuesInspectorCardHtml(),
  ].filter(Boolean).join("");
}

function rangeFillPercent(input) {
  if (!input || input.type !== "range") {
    return 0;
  }
  const min = Number(input.min || 0);
  const max = Number(input.max || 100);
  const value = Number(input.value || min);
  if (!Number.isFinite(min) || !Number.isFinite(max) || max <= min) {
    return 0;
  }
  return Math.max(0, Math.min(100, ((value - min) / (max - min)) * 100));
}

function syncRangeFill(input) {
  if (input?.type !== "range") {
    return;
  }
  input.style.setProperty("--range-fill", `${rangeFillPercent(input)}%`);
}

function syncRangeFillStyles() {
  $$(".settings-panel input[type='range']").forEach(syncRangeFill);
}

function lotInspectorCardHtml() {
  const counts = batchCounts();
  const visible = getVisibleAppState();
  const ignored = counts.ignoredFiles ? `${counts.ignoredFiles} ignorado${counts.ignoredFiles === 1 ? "" : "s"}` : "";
  const customCount = imageAdjustmentOverrideCount();
  const custom = customCount ? `${customCount} personalizada${customCount === 1 ? "" : "s"}` : "";
  const meta = state.batch === "empty"
    ? `${preflightHelpers.readyImagesText(0)}${ignored ? ` · ${ignored}` : ""}`
    : `${preflightHelpers.readyImagesText(counts.exportableImages)}${custom ? ` · ${custom}` : ""}${ignored ? ` · ${ignored}` : ""}`;
  const tone = counts.blockingErrors ? "error" : counts.nonBlockingWarnings ? "warning" : "";
  return inspectorReviewViewHelpers.lotInspectorCardHtml({
    meta,
    title: visible.title,
    tone,
  });
}

function outputInspectorCardHtml() {
  const profiles = state.outputProfiles.length ? state.outputProfiles : [currentOutputProfileData()];
  const activeProfiles = exportOutputProfiles();
  const exportable = exportableImages().length;
  const totalFiles = exportable * activeProfiles.length;
  const dirty = !outputMatchesProfile(activeOutputProfile());
  const rows = profiles.map((profile) => {
    const enabled = Boolean(profile.enabled);
    return {
      id: profile.id,
      name: profile.name,
      enabled,
      active: profile.id === state.activeOutputProfileId,
      canToggle: true,
      summary: outputProfileSummaryLine(profile),
    };
  });
  return inspectorOutputViewHelpers.outputInspectorCardHtml({
    activeCount: activeProfiles.length,
    totalFiles,
    rows,
    dirty,
  });
}

function outputProfileInlineRowHtml(profile) {
  const enabled = Boolean(profile.enabled);
  return inspectorOutputViewHelpers.outputProfileInlineRowHtml({
    id: profile.id,
    name: profile.name,
    enabled,
    active: profile.id === state.activeOutputProfileId,
    canToggle: true,
    summary: outputProfileSummaryLine(profile),
  });
}

function selectedImageInspectorCardHtml() {
  const image = selectedImage();
  const hasLocal = image ? hasImageAdjustmentOverride(image) : false;
  return inspectorReviewViewHelpers.selectedImageInspectorCardHtml({
    hasReadyBatch: hasBatch() && state.batch === "ready",
    image,
    detail: image ? image.detail || imageFileType(image) : "",
    hasLocal,
  });
}

function issuesInspectorCardHtml() {
  const rows = actionableIssueRows();
  if (!rows.length) {
    return "";
  }
  const errors = rows.filter((row) => row.level === "error").length;
  const blocking = preflightCounts().errors > 0;
  const count = blocking
    ? `${preflightCounts().errors} bloqueo${preflightCounts().errors === 1 ? "" : "s"}`
    : errors
      ? `${errors} error${errors === 1 ? "" : "es"}`
    : `${rows.length} aviso${rows.length === 1 ? "" : "s"}`;
  return inspectorReviewViewHelpers.issuesInspectorCardHtml({
    rows,
    blocking,
    countLabel: count,
  });
}

function aspectInspectorCardHtml() {
  const images = activeImages();
  const customizedCount = imageAdjustmentOverrideCount(images);
  return inspectorReviewViewHelpers.aspectInspectorCardHtml({
    hasReadyBatch: hasBatch() && state.batch === "ready",
    activePreset: state.activePreset,
    adjustments: activePresetItems(),
    customizedCount,
  });
}

function actionableIssueRows() {
  const rows = issueRows().filter((row) => !["info", "ignored"].includes(row.level));
  const validationRows = validationIssues()
    .filter((issue) => issue.title !== "Sin lote" && issue.title !== "No hay PNG válidos")
    .map((issue) => ({
      level: issue.level,
      title: issue.title,
      detail: issue.detail,
      path: "",
      actionLabel: "",
    }));
  const seen = new Set();
  return [...validationRows, ...rows].filter((row) => {
    const key = `${row.level}|${row.title}|${row.detail || ""}`;
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
}

function inspectorSubviewHeaderHtml(mode) {
  return inspectorContextViewHelpers.inspectorSubviewHeaderHtml(
    inspectorContextViewHelpers.inspectorSubviewHeaderState({
      activePreset: state.activePreset,
      mode,
      outputEditMode: state.outputEditMode,
      outputLabel: viewerOutputCompactLabel(),
      presetEditorOpen: state.presetEditorOpen,
      presetSourceLabel: presetSourceLabel(),
      warningCount: actionableIssueRows().length,
    })
  );
}

function contextualInspectorHtml() {
  if (state.batch === "scanning") {
    return inspectorContextViewHelpers.contextualInspectorHtml({
      batch: state.batch,
      scanStatus: state.scanStatus,
      progressHtml: exportPreflightViewHelpers.progressPanelHtml("Preparando lote"),
      preflightHtml: exportPreflightViewHelpers.preflightListHtml(inspectorContextViewHelpers.contextualPreflightRows({
        batch: state.batch,
      })),
    });
  }

  if (state.batch === "none") {
    return inspectorContextViewHelpers.contextualInspectorHtml({
      batch: state.batch,
      preflightHtml: exportPreflightViewHelpers.preflightListHtml(inspectorContextViewHelpers.contextualPreflightRows({
        batch: state.batch,
      })),
      outputSummary: `${state.format} · ${state.size} · ${settingsViewHelpers.backgroundLabel(state.background)}`,
      activePreset: state.activePreset,
    });
  }

  if (state.batch === "empty") {
    return inspectorContextViewHelpers.contextualInspectorHtml({
      batch: state.batch,
      scanStatus: state.scanStatus,
      preflightHtml: exportPreflightViewHelpers.preflightListHtml(inspectorContextViewHelpers.contextualPreflightRows({
        batch: state.batch,
        ignoredSummary: ignoredSummaryText(),
        totalFiles: state.scanDiagnostics.totalFiles,
      })),
    });
  }

  return inspectorContextViewHelpers.contextualInspectorHtml({
    batch: state.batch,
    compactStatus: compactHeaderStatusText(),
  });
}

function presetSourceLabel() {
  return settingsViewHelpers.presetSourceLabel({
    bridgePresetWarning: state.bridgePresetWarning,
    presetDirty: state.presetDirty,
  });
}
