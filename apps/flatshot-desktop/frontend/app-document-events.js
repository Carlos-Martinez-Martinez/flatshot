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
