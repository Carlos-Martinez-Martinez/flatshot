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
  setControlHint($("[data-action='open-app-settings']"), "Abrir formatos de salida");
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
    processed: "Ver previsualización con el formato activo",
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

const actionDispatcher = actionHandlerHelpers.createActionDispatcher({
  "load-batch": () => loadBatch(),
  "load-mock-batch": () => loadMockBatch(),
  "check-bridge": () => { void checkBridge(); },
  "toggle-inspector": () => {
    state.inspectorCollapsed = !state.inspectorCollapsed;
    state.statusText = state.inspectorCollapsed ? "Inspector oculto" : "Inspector visible";
    render();
  },
  "pick-bridge-folder": () => { void pickBridgeFolder(); },
  "pick-output-profile-destination": () => { void pickOutputProfileDestination(); },
  "scan-bridge-folder": () => { void scanBridgeFolder(); },
  "clear-batch": () => clearBatch(),
  "show-empty-folder": () => showEmptyFolder(),
  "force-preview-error": () => {
    if (hasBatch()) {
      state.previewStatus = "error";
      state.statusText = "Vista no disponible";
      render();
    }
  },
  "previous-image": () => selectAdjacentImage(-1),
  "next-image": () => selectAdjacentImage(1),
  "clear-filter": () => clearFilter(),
  "clear-search": () => {
    state.search = "";
    state.statusText = galleryHelpers.filterStatusText(state.filter);
    if (!ensureGallerySelectionForFilter()) {
      render();
    }
  },
  "select-first-image": () => {
    const image = filteredImages()[0] || activeImages()[0];
    if (image) {
      selectImage(image.id);
    }
  },
  "select-image-id": (target) => {
    const imageId = target?.dataset?.imageId;
    if (imageId) {
      state.inspectorTab = "review";
      selectImage(imageId);
    }
  },
  "open-advanced": () => {
    state.inspectorTab = "advanced";
    pendingAdvancedDisclosure = "appearance-section";
    state.statusText = "Ajustes";
    render();
  },
  "open-image-adjustment": () => {
    state.inspectorTab = "advanced";
    state.presetEditorOpen = false;
    pendingAdvancedDisclosure = "local-adjustment";
    state.statusText = "Ajuste de esta imagen";
    render();
  },
  "apply-global-adjustment-to-overrides": () => resetAllImageOverrides(),
  "close-inspector-subview": () => {
    state.inspectorTab = "review";
    state.statusText = getVisibleAppState().nextStep || state.statusText;
    render();
  },
  "edit-output": () => beginOutputEdit(),
  "select-output-profile": (target) => {
    const profileId = target?.dataset?.outputProfileId;
    if (profileId) {
      applyOutputProfile(profileId);
    }
  },
  "apply-output-edit": () => applyOutputEdit(),
  "cancel-output-edit": () => cancelOutputEdit(),
  "save-output-current-profile": () => saveCurrentOutputProfile(),
  "save-output-as-new": () => saveCurrentOutputAsNewProfile(),
  "discard-output-overrides": () => discardOutputOverrides(),
  "open-app-settings": () => openAppSettings(),
  "close-app-settings": () => closeAppSettings(),
  "cancel-output-profile-draft": () => cancelOutputProfileDraft(),
  "open-batch-detail": () => openBatchDetail(),
  "close-batch-detail": () => closeBatchDetail(),
  "cancel-export-confirm": () => closeExportConfirm(),
  "confirm-export": () => confirmExportFromModal(),
  "new-output-profile": () => newOutputProfile(),
  "duplicate-output-profile": () => duplicateOutputProfile(),
  "reset-output-profile-draft": () => resetOutputProfileDraft(),
  "delete-output-profile": () => deleteManagedOutputProfile(),
  "cancel-output-delete": () => cancelDeleteManagedOutputProfile(),
  "confirm-output-delete": () => confirmDeleteManagedOutputProfile(),
  "save-output-profile": () => saveOutputProfile(),
  "edit-background-preset": () => beginBackgroundPresetEdit("edit"),
  "new-background-preset": () => beginBackgroundPresetEdit("new"),
  "delete-background-preset": () => deleteBackgroundPreset(),
  "save-background-preset": () => saveBackgroundPreset(),
  "cancel-background-preset-edit": () => {
    state.backgroundPresetEditor = null;
    renderOutputProfileModalState();
  },
  "open-preset-editor": () => openPresetEditor(),
  "close-preset-editor": () => closePresetEditor(),
  "zoom-height": () => setViewerMode("height"),
  "zoom-width": () => setViewerMode("width"),
  "zoom-in": () => setViewerZoom(Math.round(currentViewerZoom() / 10) * 10 + 10),
  "zoom-out": () => setViewerZoom(Math.round(currentViewerZoom() / 10) * 10 - 10),
  "reset-settings": () => resetActivePresetSettings(),
  "cancel-adjustment-edit": () => cancelAdjustmentEdit(),
  "apply-global-adjustment": () => applyGlobalAdjustmentWithoutSaving(),
  "save-preset": () => { void saveCurrentPreset(); },
  "save-preset-as-new": () => saveCurrentPresetAsNew(),
  "apply-local-adjustment": () => applyLocalAdjustmentOnly(),
  "save-local-adjustment-as-new": () => saveCurrentLocalAdjustmentAsNew(),
  "export-presets": () => exportPresetCollection(),
  "delete-preset": () => { void deleteActivePreset(); },
  "toggle-local-adjustment": () => {
    state.localOverride = !state.localOverride;
    state.statusText = state.localOverride ? "Ajuste personalizado" : "Igual que el lote";
    render();
  },
  "reset-local-adjustment": () => resetCurrentImageOverride(),
  "pause-export": () => pauseExport(),
  "stop-export": () => stopExport(),
  "start-export": () => startExport(),
  "review-errors": () => reviewWarnings(),
  "review-warnings": () => reviewWarnings(),
  "review-output": () => beginOutputEdit(),
  "open-output": () => openOutputFolder(),
  "primary": () => primaryAction(),
  "secondary-primary": () => runVisibleAction(getVisibleAppState().secondaryAction?.action),
});

function handleAction(action, target = null) {
  actionDispatcher(action, target);
}

function closeTransientDetails(event) {
  const target = event.target;
  document.querySelectorAll("details.format-more-menu[open], details.debug-panel[open]").forEach((details) => {
    if (!details.contains(target)) {
      details.open = false;
    }
  });
}

function handleDocumentImageLoad(event) {
  const target = event.target;
  if (target instanceof HTMLImageElement && target.classList.contains("thumb-image")) {
    recordThumbnailLoad(target);
  }
  if (target instanceof HTMLImageElement && target.classList.contains("preview-image")) {
    updatePreviewDebugPanel();
  }
}

function handleDocumentImageError(event) {
  const target = event.target;
  if (target instanceof HTMLImageElement && target.classList.contains("thumb-image")) {
    recordThumbnailError(target);
  }
  if (target instanceof HTMLImageElement && target.classList.contains("preview-image")) {
    state.previewStatus = "error";
    state.previewError = "No se pudo cargar la preview renderizada";
    state.statusText = "Vista no disponible";
    render();
  }
}

function recordThumbnailLoad(imageElement) {
  const imageId = imageElement.dataset.imageId;
  if (!imageId) {
    return;
  }
  const loadedSrc = imageElement.currentSrc || imageElement.src;
  const current = state.thumbnailStatus[imageId];
  markThumbnailLoaded(
    imageId,
    current?.sourceSrc || loadedSrc,
    imageElement.naturalWidth,
    imageElement.naturalHeight,
    loadedSrc
  );
}

function recordThumbnailError(imageElement) {
  const imageId = imageElement.dataset.imageId;
  const src = imageElement.currentSrc || imageElement.src;
  if (!imageId) {
    return;
  }
  markThumbnailError(imageId, src);
}

function handleDocumentPointerDown(event) {
  if (event.target.closest?.(".settings-panel details > summary")) {
    inspectorScrollTopBeforeToggle = $(".settings-panel")?.scrollTop || 0;
  }
}

function handleInspectorDisclosureClick(event) {
  const disclosureSummary = event.target.closest?.(".settings-panel details.inspector-disclosure > summary");
  if (!disclosureSummary) {
    return;
  }
  const panel = $(".settings-panel");
  const details = disclosureSummary.closest("details");
  inspectorScrollTopBeforeToggle = panel?.scrollTop || 0;
  event.preventDefault();
  event.stopImmediatePropagation();
  toggleInspectorDisclosure(details);
  disclosureSummary.blur();
}

function handleDocumentClick(event) {
  closeTransientDetails(event);

  const disclosureSummary = event.target.closest(".settings-panel details > summary");
  if (disclosureSummary) {
    const details = disclosureSummary.closest("details");
    if (details?.classList.contains("inspector-disclosure")) {
      event.preventDefault();
      toggleInspectorDisclosure(details);
      return;
    }
  }

  if (event.target.id === "app-settings-modal") {
    closeAppSettings();
    return;
  }

  if (event.target.id === "batch-detail-modal") {
    closeBatchDetail();
    return;
  }

  if (event.target.id === "export-confirm-modal") {
    closeExportConfirm();
    return;
  }

  const actionTarget = event.target.closest("[data-action]");
  if (actionTarget) {
    handleAction(actionTarget.dataset.action, actionTarget);
    return;
  }

  const outputProfileTarget = event.target.closest("[data-output-profile-id]");
  if (outputProfileTarget) {
    selectOutputProfileDraft(outputProfileTarget.dataset.outputProfileId);
    return;
  }

  const imageTarget = event.target.closest("[data-image-id]");
  if (imageTarget) {
    selectImage(imageTarget.dataset.imageId);
    return;
  }

  const reviewTarget = event.target.closest("[data-review-scenario]");
  if (reviewTarget) {
    showReviewScenario(reviewTarget.dataset.reviewScenario);
    return;
  }

  const filterTarget = event.target.closest("[data-filter]");
  if (filterTarget) {
    applyGalleryFilter(filterTarget.dataset.filter);
    return;
  }

  const galleryViewTarget = event.target.closest("[data-gallery-view]");
  if (galleryViewTarget) {
    state.galleryView = galleryViewTarget.dataset.galleryView === "list" ? "list" : "thumbs";
    state.statusText = state.galleryView === "list" ? "Galería en lista" : "Galería en miniaturas";
    render();
    return;
  }

  const modeTarget = event.target.closest("[data-preview-mode]");
  if (modeTarget) {
    state.previewMode = modeTarget.dataset.previewMode;
    state.statusText = modeTarget.textContent.trim();
    render();
    return;
  }

  const bgTarget = event.target.closest("[data-preview-bg]");
  if (bgTarget) {
    state.previewBg = backgroundPresetHelpers.normalizePreviewBackgroundValue(
      bgTarget.dataset.previewBg === "custom" ? previewCustomBackgroundValue() : bgTarget.dataset.previewBg,
      backgroundHelperOptions()
    );
    state.statusText = `Fondo: ${backgroundPresetHelpers.previewBackgroundLabel(state.previewBg, {
      ...backgroundHelperOptions(),
      backgroundLabel: settingsViewHelpers.backgroundLabel,
    })}`;
    render();
    return;
  }

  const presetTarget = event.target.closest("[data-preset]");
  if (presetTarget) {
    applyPresetSettings(presetTarget.dataset.preset);
  }

  const inspectorTarget = event.target.closest("[data-inspector-tab]");
  if (inspectorTarget) {
    state.inspectorTab = inspectorTarget.dataset.inspectorTab;
    if (state.inspectorTab === "output") {
      state.presetEditorOpen = false;
    }
    render();
  }
}

function handleDocumentToggle(event) {
  if (!event.target.matches?.(".settings-panel details.inspector-disclosure")) {
    return;
  }
  const panel = $(".settings-panel");
  if (!panel) {
    return;
  }
  const restoreScroll = () => {
    panel.scrollTop = inspectorScrollTopBeforeToggle;
  };
  window.requestAnimationFrame(() => {
    restoreScroll();
    window.requestAnimationFrame(restoreScroll);
    window.setTimeout(restoreScroll, 0);
    window.setTimeout(restoreScroll, 80);
    window.setTimeout(restoreScroll, 180);
  });
}

function handleDemoScenarioChange(event) {
  if (!devMode) {
    return;
  }
  state.bridgeMode = "mock";
  state.bridgeLastResponse = `Estado mock: ${scenarioLabels[event.target.value] || event.target.value}`;
  setScenario(event.target.value);
}

function handleAppModeChange(event) {
  if (!devMode && event.target.value !== "bridge") {
    event.target.value = "bridge";
    state.bridgeMode = "bridge";
    render();
    return;
  }
  state.bridgeMode = event.target.value;
  state.statusText = state.bridgeMode === "bridge" ? "Conexión local" : "Modo demo";
  state.bridgeLastResponse = state.bridgeMode === "bridge" ? "Conexión pendiente" : "Demo activo";
  state.scanStatus = state.bridgeMode === "bridge" ? "Sin lote" : "Escenarios mock activos.";
  render();
}

function handleBridgeUrlInput(event) {
  state.bridgeUrl = event.target.value || defaultBridgeUrl;
  state.bridgeStatus = "idle";
  state.bridgeMessage = "Comprueba conexión";
  state.bridgeLastResponse = "URL pendiente";
  state.scanStatus = "Comprueba bridge";
  render();
}

function handleBridgeScanPathInput(event) {
  state.bridgeScanPath = event.target.value;
}

function handleDocumentInput(event) {
  if (event.target?.matches?.("input[type='range']")) {
    syncRangeFill(event.target);
  }
  if (event.target.id === "onboarding-scan-path") {
    state.bridgeScanPath = event.target.value;
    const sidebarInput = $("#bridge-scan-path");
    if (sidebarInput) {
      sidebarInput.value = state.bridgeScanPath;
    }
  }
  const localKey = event.target?.dataset?.localSetting;
  if (localKey) {
    setCurrentImageOverrideValue(localKey, event.target.value);
  }
  if (event.target?.dataset?.settingNumber) {
    updateSettingFromNumberInput(event.target);
  }
  if (event.target?.dataset?.localSettingNumber) {
    updateLocalOverrideFromNumberInput(event.target);
  }
  if (event.target.closest?.("#background-preset-editor")) {
    updateBackgroundPresetEditorFromFields();
    return;
  }
  if (event.target.closest?.("#output-profile-form")) {
    updateOutputProfileDraftFromForm();
    renderOutputProfileModalState();
  }
}

function handleDocumentChange(event) {
  if (event.target.matches?.("[data-preview-bg-channel]")) {
    state.previewBg = backgroundPresetHelpers.normalizePreviewBackgroundValue(previewCustomBackgroundValue(), backgroundHelperOptions());
    state.statusText = `Fondo: ${backgroundPresetHelpers.previewBackgroundLabel(state.previewBg, {
      ...backgroundHelperOptions(),
      backgroundLabel: settingsViewHelpers.backgroundLabel,
    })}`;
    render();
    return;
  }
  if (event.target?.id === "gallery-output-select") {
    if (event.target.value !== "__custom") {
      applyOutputProfile(event.target.value);
    }
    return;
  }
  if (event.target?.dataset?.settingNumber) {
    updateSettingFromNumberInput(event.target, { commit: true });
    return;
  }
  if (event.target?.dataset?.localSettingNumber) {
    updateLocalOverrideFromNumberInput(event.target, { commit: true });
    return;
  }
  if (event.target.matches?.("[data-output-profile-enabled-id]")) {
    setOutputProfileEnabled(event.target.dataset.outputProfileEnabledId, event.target.checked);
    return;
  }
  if (event.target.matches?.("[data-output-profile-draft-enabled]")) {
    setOutputProfileDraftEnabled(event.target.checked);
    return;
  }
  if (event.target.closest?.("#background-preset-editor")) {
    updateBackgroundPresetEditorFromFields();
    renderBackgroundPresetControls();
    return;
  }
  if (event.target.matches?.("[data-image-adjustment-select]")) {
    applyPresetSettings(event.target.value);
    return;
  }
  if (event.target.closest?.("#output-profile-form")) {
    updateOutputProfileDraftFromForm();
    renderOutputProfileModalState();
  }
}

function handleDocumentSubmit(event) {
  if (event.target.id === "output-profile-form") {
    event.preventDefault();
    saveOutputProfile();
  }
}

function handleImageSearchInput(event) {
  state.search = event.target.value;
  if (ensureGallerySelectionForFilter()) {
    return;
  }
  render();
}

function handleSettingInput(event) {
  const key = event.target.dataset.setting;
  const nextValue = settingInputValue(event.target);
  if (state.settings[key] === nextValue) {
    return;
  }
  state.settings[key] = nextValue;
  markPresetDirty();
}

function handleLightingFieldInput(event) {
  updateLightingSceneField(event.target.dataset.lightingField, event.target.value);
}

function handleLightingNumberFieldInput(event) {
  updateLightingSceneField(event.target.dataset.lightingNumberField, event.target.value);
}

function handleLightingPresetClick(button) {
  const presetId = button.dataset.lightingPreset;
  const preset = lightingScenePresets[presetId];
  if (!preset) {
    return;
  }
  state.settings.shadow_engine = "studio_2_5d";
  state.settings.lighting_scene = cloneLightingScene(preset);
  state.lightingPresetId = presetId;
  markPresetDirty();
}

function settingInputValue(input) {
  if (input.type === "checkbox") {
    return input.checked;
  }
  if (input.tagName === "SELECT") {
    return input.value;
  }
  return Number(input.value);
}

function updateLightingSceneField(field, rawValue) {
  const scene = cloneLightingScene(state.settings.lighting_scene);
  if (field === "main.type") {
    scene.main.type = ["softbox", "spot", "strip"].includes(rawValue) ? rawValue : scene.main.type;
  } else if (field === "main.height") {
    scene.main.height = numberHelpers.roundedSceneValue(Number(rawValue) / 100, 0, 1, scene.main.height);
  } else if (field === "main.size") {
    scene.main.size = numberHelpers.roundedSceneValue(Number(rawValue) / 100, 0, 1, scene.main.size);
  } else if (field === "main.intensity") {
    scene.main.intensity = numberHelpers.roundedSceneValue(Number(rawValue) / 100, 0, 1.5, scene.main.intensity);
  } else if (field === "ambient_intensity") {
    scene.ambient_intensity = numberHelpers.roundedSceneValue(Number(rawValue) / 100, 0, 1, scene.ambient_intensity);
  } else {
    return;
  }
  if (lightingScenesEqual(scene, state.settings.lighting_scene)) {
    return;
  }
  state.settings.lighting_scene = scene;
  markPresetDirty();
}

function updateLightingScenePosition(clientX, clientY, options = {}) {
  const stage = $("#lighting-stage");
  if (!stage || state.settings.shadow_engine !== "studio_2_5d") {
    return false;
  }
  const rect = stage.getBoundingClientRect();
  if (!rect.width || !rect.height) {
    return false;
  }
  const x = numberHelpers.roundedSceneValue(((clientX - rect.left) / rect.width) * 2 - 1, -1, 1, defaultLightingScene.main.x);
  const y = numberHelpers.roundedSceneValue(((clientY - rect.top) / rect.height) * 2 - 1, -1, 1, defaultLightingScene.main.y);
  const scene = cloneLightingScene(state.settings.lighting_scene);
  if (scene.main.x === x && scene.main.y === y) {
    return false;
  }
  scene.main.x = x;
  scene.main.y = y;
  state.settings.lighting_scene = scene;
  markPresetDirty({ deferRender: options.deferRender });
  if (options.deferRender) {
    renderLightingSceneControls();
  }
  return true;
}

function numericInputValue(input, fallback = 0) {
  const raw = String(input.value ?? "").trim();
  if (!raw || raw === "-" || raw === "+") {
    return { valid: false, value: fallback };
  }
  const parsed = Number(raw);
  if (!Number.isFinite(parsed)) {
    return { valid: false, value: fallback };
  }
  const min = input.min === "" ? -Infinity : Number(input.min);
  const max = input.max === "" ? Infinity : Number(input.max);
  const rounded = Math.round(parsed);
  return {
    valid: true,
    value: Math.max(min, Math.min(max, rounded)),
  };
}

function updateSettingFromNumberInput(input, options = {}) {
  const key = input?.dataset?.settingNumber;
  if (!key || !(key in state.settings)) {
    return;
  }
  const parsed = numericInputValue(input, state.settings[key]);
  if (!parsed.valid) {
    return;
  }
  if (options.commit) {
    input.value = parsed.value;
  }
  if (state.settings[key] === parsed.value) {
    return;
  }
  state.settings[key] = parsed.value;
  const range = $(`[data-setting="${key}"]`);
  if (range && range.type === "range") {
    range.value = parsed.value;
    syncRangeFill(range);
  }
  markPresetDirty();
}

function updateLocalOverrideFromNumberInput(input, options = {}) {
  const key = input?.dataset?.localSettingNumber;
  if (!key || !localOverrideKeys.includes(key)) {
    return;
  }
  const parsed = numericInputValue(input, currentImageOverride()[key] || 0);
  if (!parsed.valid) {
    return;
  }
  const value = clampLocalOverrideValue(key, parsed.value);
  if (options.commit) {
    input.value = value;
  }
  const range = $(`[data-local-setting="${key}"]`);
  if (range) {
    range.value = value;
    syncRangeFill(range);
  }
  setCurrentImageOverrideValue(key, value);
}

function handleFormatSelectChange(event) {
  state.format = outputProfileHelpers.normalizeExportFormat(event.target.value);
  state.statusText = `Formato: ${state.format}`;
  persistExportPreferences();
  render();
}

function handleOutputProfileSelectChange(event) {
  if (event.target.value === "__custom") {
    return;
  }
  applyOutputProfile(event.target.value);
}

function handleSizeSelectInput(event) {
  state.size = event.target.value;
}

function handleSizeSelectChange(event) {
  state.size = outputProfileHelpers.parseOutputSize(event.target.value).normalized;
  state.statusText = `Tamaño: ${state.size}`;
  persistExportPreferences();
  const image = selectedImage();
  if (image?.source === "bridge") {
    void requestBridgePreview(image);
    return;
  }
  render();
}

function handleBackgroundSelectChange(event) {
  state.background = outputProfileHelpers.normalizeBackgroundValue(event.target.value, state.background);
  state.previewBg = state.background;
  state.statusText = `Fondo: ${settingsViewHelpers.backgroundLabel(state.background)}`;
  persistExportPreferences();
  const image = selectedImage();
  if (image?.source === "bridge") {
    void requestBridgePreview(image);
    return;
  }
  render();
}

function handleDestinationModeChange(event) {
  state.destinationMode = event.target.value;
  state.destinationValue = state.destinationMode === "custom" ? "" : "Salida";
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = state.destinationMode === "custom" ? "Carpeta de salida sin configurar" : "Destino junto al origen";
  persistExportPreferences();
  render();
}

function handleDestinationInput(event) {
  state.destinationValue = event.target.value;
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = state.destinationValue.trim() ? "Carpeta de salida configurada" : "Carpeta de salida sin configurar";
  persistExportPreferences();
  render();
}

function handleNamingInput(event) {
  state.naming = event.target.value;
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = state.naming.trim() ? "Nombre de archivo actualizado" : "Nombre de archivo vacío";
  persistExportPreferences();
  render();
}

function handleDocumentKeydown(event) {
  const target = event.target;
  const isTyping = target instanceof HTMLInputElement
    || target instanceof HTMLTextAreaElement
    || target instanceof HTMLSelectElement
    || target?.isContentEditable;
  const command = event.ctrlKey || event.metaKey;

  if (event.key === "Tab" && trapOpenModalFocus(event)) {
    return;
  }

  if (command && event.key.toLowerCase() === "f") {
    event.preventDefault();
    const search = $("#image-search");
    if (search && hasBatch()) {
      search.focus();
      search.select();
    }
    return;
  }

  if (command && event.key.toLowerCase() === "e") {
    event.preventDefault();
    if (isExportReady() && state.exportStatus !== "running") {
      startExport();
    }
    return;
  }

  if (event.key === "Escape") {
    if (state.exportConfirmOpen) {
      closeExportConfirm();
      event.preventDefault();
      return;
    }
    if (state.batchDetailOpen) {
      closeBatchDetail();
      event.preventDefault();
      return;
    }
    if (state.appSettingsOpen) {
      closeAppSettings();
      event.preventDefault();
      return;
    }
    const openDetails = Array.from(document.querySelectorAll("details[open]")).reverse()[0];
    if (openDetails) {
      openDetails.open = false;
      event.preventDefault();
    }
    return;
  }

  if (event.key === "Enter" && state.exportConfirmOpen && !isTyping) {
    event.preventDefault();
    confirmExportFromModal();
    return;
  }

  if (isTyping) {
    return;
  }

  const key = event.key.toLowerCase();
  if (event.key === "ArrowLeft") {
    event.preventDefault();
    selectAdjacentImage(-1, { focus: true });
  } else if (event.key === "ArrowRight") {
    event.preventDefault();
    selectAdjacentImage(1, { focus: true });
  } else if (event.key === "Home") {
    event.preventDefault();
    selectEdgeImage("first", { focus: true });
  } else if (event.key === "End") {
    event.preventDefault();
    selectEdgeImage("last", { focus: true });
  }
}

function handleViewerWheel(event) {
  if (!isViewerNavigationAvailable()) {
    return;
  }
  event.preventDefault();
  const baseZoom = currentViewerZoom();
  const direction = event.deltaY < 0 ? 1 : -1;
  const step = event.shiftKey ? 5 : 10;
  setViewerZoom(baseZoom + direction * step, event);
}

function handleViewerPointerDown(event) {
  if (
    event.button !== 0
    || !isViewerNavigationAvailable()
    || event.target.closest("button, input, textarea, select, summary, a")
  ) {
    return;
  }
  if (!canViewerPan()) {
    return;
  }
  const canvas = $("#preview-canvas");
  viewerPanState.active = true;
  viewerPanState.pointerId = event.pointerId;
  viewerPanState.startX = event.clientX;
  viewerPanState.startY = event.clientY;
  viewerPanState.originX = state.panX;
  viewerPanState.originY = state.panY;
  canvas?.classList.add("is-panning");
  try {
    canvas?.setPointerCapture(event.pointerId);
  } catch (error) {
    // Pointer capture is optional; document-level listeners continue the drag.
  }
}

function handleViewerPointerMove(event) {
  if (!viewerPanState.active || event.pointerId !== viewerPanState.pointerId) {
    return;
  }
  state.panX = viewerPanState.originX + event.clientX - viewerPanState.startX;
  state.panY = viewerPanState.originY + event.clientY - viewerPanState.startY;
  clampViewerPan();
  applyViewerPanDom();
}

function handleViewerPointerEnd(event) {
  if (!viewerPanState.active || event.pointerId !== viewerPanState.pointerId) {
    return;
  }
  const canvas = $("#preview-canvas");
  viewerPanState.active = false;
  canvas?.classList.remove("is-panning");
  try {
    if (viewerPanState.pointerId !== null) {
      canvas?.releasePointerCapture(viewerPanState.pointerId);
    }
  } catch (error) {
    // Release can fail if the pointer was already released by the browser.
  }
  viewerPanState.pointerId = null;
}

function handleViewerDoubleClick(event) {
  if (event.target.closest("button, input, textarea, select, summary, a")) {
    return;
  }
  event.preventDefault();
  toggleViewerZoomMode();
}
