function closeTransientDetails(event) {
  const target = event.target;
  document.querySelectorAll("details.format-more-menu[open], details.debug-panel[open], details.viewer-guides-menu[open], details.top-preferences-menu[open]").forEach((details) => {
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

function eventElementTarget(event) {
  const target = event.target;
  if (target?.closest) {
    return target;
  }
  return target?.parentElement || null;
}

function handleDocumentPointerDown(event) {
  if (event.target.closest?.(".settings-panel details > summary")) {
    inspectorScrollTopBeforeToggle = $(".settings-panel")?.scrollTop || 0;
  }
}

function closeBackgroundPresetEditorOnOutsideClick(event) {
  if (!state.backgroundPresetEditor) {
    return false;
  }
  const target = event.target;
  if (
    target.closest?.("#background-preset-editor")
    || target.closest?.(".background-preset-actions")
  ) {
    return false;
  }
  state.backgroundPresetEditor = null;
  return true;
}

function handleGuideSystemToggle(target) {
  const systemId = target.dataset.guideSystemToggle;
  if (!systemId) {
    return false;
  }
  setGuideSystemActive(systemId, target.checked);
  return true;
}

function handleGuideSystemPickerToggle(target) {
  const systemId = target.dataset.guideSystemPickerToggle;
  if (!systemId) {
    return false;
  }
  setGuideSystemInPicker(systemId, target.checked);
  return true;
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
  const target = eventElementTarget(event);
  if (!target) {
    return;
  }

  closeTransientDetails({ target });

  const disclosureSummary = target.closest(".settings-panel details > summary");
  if (disclosureSummary) {
    const details = disclosureSummary.closest("details");
    if (details?.classList.contains("inspector-disclosure")) {
      event.preventDefault();
      toggleInspectorDisclosure(details);
      return;
    }
  }

  const modalCloseHandler = {
    "app-settings-modal": closeAppSettings,
    "batch-detail-modal": closeBatchDetail,
    "export-confirm-modal": closeExportConfirm,
    "qa-lab-modal": closeQaLab,
    "preferences-modal": closePreferences,
    "guide-manager-modal": closeGuideManager,
  }[target.id];
  if (modalCloseHandler) {
    modalCloseHandler();
    return;
  }

  const closedBackgroundPresetEditor = closeBackgroundPresetEditorOnOutsideClick(event);

  const actionTarget = target.closest("[data-action]");
  if (actionTarget) {
    handleAction(actionTarget.dataset.action, actionTarget);
    return;
  }

  const outputProfileTarget = target.closest("[data-output-profile-id]");
  if (outputProfileTarget) {
    selectOutputProfileDraft(outputProfileTarget.dataset.outputProfileId);
    return;
  }

  const imageTarget = target.closest("[data-image-id]");
  if (imageTarget) {
    selectGalleryImage(imageTarget.dataset.imageId, {
      additive: event.ctrlKey || event.metaKey,
      range: event.shiftKey,
    });
    return;
  }

  const reviewTarget = target.closest("[data-review-scenario]");
  if (reviewTarget) {
    showReviewScenario(reviewTarget.dataset.reviewScenario);
    return;
  }

  const filterTarget = target.closest("[data-filter]");
  if (filterTarget) {
    applyGalleryFilter(filterTarget.dataset.filter);
    return;
  }

  const galleryViewTarget = target.closest("[data-gallery-view]");
  if (galleryViewTarget) {
    state.galleryView = galleryViewTarget.dataset.galleryView === "list" ? "list" : "thumbs";
    state.statusText = state.galleryView === "list" ? "Galería en lista" : "Galería en miniaturas";
    render();
    return;
  }

  const modeTarget = target.closest("[data-preview-mode]");
  if (modeTarget) {
    state.previewMode = modeTarget.dataset.previewMode;
    state.statusText = modeTarget.textContent.trim();
    render();
    return;
  }

  const rgbPickerTrigger = target.closest("[data-rgb-visual-picker-trigger]");
  if (rgbPickerTrigger) { openRgbVisualPicker(rgbPickerTrigger.closest(".rgb-visual-control")); return; }

  const bgTarget = target.closest("[data-preview-bg]");
  if (bgTarget) {
    applyPreviewBackgroundValue(bgTarget.dataset.previewBg === "custom" ? previewCustomBackgroundValue() : bgTarget.dataset.previewBg);
    render();
    return;
  }

  const presetTarget = target.closest("[data-preset]");
  if (presetTarget) {
    applyPresetSettings(presetTarget.dataset.preset, { recordHistory: true });
  }

  const inspectorTarget = target.closest("[data-inspector-tab]");
  if (inspectorTarget) {
    state.inspectorTab = inspectorTarget.dataset.inspectorTab;
    if (state.inspectorTab === "output") {
      state.presetEditorOpen = false;
    }
    render();
  }

  if (closedBackgroundPresetEditor) {
    renderOutputProfileModalState();
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

function handleDocumentInput(event) {
  if (event.target?.matches?.("input[type='range']")) {
    syncRangeFill(event.target);
  }
  if (typeof setNumericControlPending === "function") setNumericControlPending(event.target);
  if (event.target.id === "onboarding-scan-path") {
    state.bridgeScanPath = event.target.value;
    const sidebarInput = $("#bridge-scan-path");
    if (sidebarInput) {
      sidebarInput.value = state.bridgeScanPath;
    }
  }
  const localKey = event.target?.dataset?.localSetting;
  if (localKey) {
    beginAdjustmentChange(adjustmentHistoryToken("local", localKey));
    setCurrentImageOverrideValue(localKey, event.target.value);
  }
  if (event.target?.matches?.("[data-preview-bg-picker]")) {
    applyPreviewBackgroundPickerChange(event.target);
    renderPreview();
    return;
  }
  if (event.target?.matches?.("[data-rgb-visual-channel], [data-rgb-visual-picker]")) { syncRgbVisualControlToTarget(event.target.closest(".rgb-visual-control"), event.target); }
  if (event.target.closest?.("#background-preset-editor")) {
    updateBackgroundPresetEditorFromFields();
    return;
  }
  if (event.target.closest?.("#guide-draft-form") && !event.target?.dataset?.guideNewField) {
    updateGuideDraftFromFields();
    return;
  }
  if (event.target.closest?.("#output-profile-form")) {
    updateOutputProfileDraftFromForm();
    renderOutputProfileModalState();
  }
}

function handleDocumentChange(event) {
  if (event.target?.matches?.("[data-preference-select]")) {
    handlePreferenceSelectChange(event.target);
    return;
  }
  if (event.target?.matches?.("[data-guide-system-toggle]")) {
    handleGuideSystemToggle(event.target);
    return;
  }
  if (event.target?.matches?.("[data-guide-system-picker-toggle]")) {
    handleGuideSystemPickerToggle(event.target);
    return;
  }
  if (event.target.matches?.("[data-preview-bg-channel], [data-preview-bg-picker]")) {
    applyPreviewBackgroundPickerChange(event.target);
    render();
    return;
  }
  if (event.target?.matches?.("[data-rgb-visual-channel], [data-rgb-visual-picker]")) { syncRgbVisualControlToTarget(event.target.closest(".rgb-visual-control"), event.target); }
  if (event.target?.dataset?.localSetting) {
    commitAdjustmentChange(adjustmentHistoryToken("local", event.target.dataset.localSetting), "Ajustar imagen");
    return;
  }
  if (event.target?.id === "gallery-output-select") {
    if (event.target.value !== "__custom") {
      applyOutputProfile(event.target.value);
    }
    return;
  }
  if (isNumericControlInput(event.target)) {
    commitNumericControlInput(event.target);
    clearNumericControlPending(event.target);
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
  if (event.target.closest?.("#guide-draft-form") && !event.target?.dataset?.guideNewField) {
    updateGuideDraftFromFields();
    renderGuideManager();
    return;
  }
  if (event.target.matches?.("[data-image-adjustment-select]")) {
    applyPresetSettings(event.target.value, { recordHistory: true });
    return;
  }
  if (event.target.closest?.("#output-profile-form")) {
    updateOutputProfileDraftFromForm();
    renderOutputProfileModalState();
  }
}

function handleDocumentFocusOut(event) {
  const target = event.target;
  if (target?.id === "onboarding-scan-path" || target?.id === "bridge-scan-path") {
    state.bridgeScanPath = target.value || "";
    const otherInput = target.id === "onboarding-scan-path" ? $("#bridge-scan-path") : $("#onboarding-scan-path");
    if (otherInput) {
      otherInput.value = state.bridgeScanPath;
    }
  }
  if (isNumericControlInput(target)) {
    commitNumericControlInput(target);
    clearNumericControlPending(target);
    return;
  }
}

function handleDocumentSubmit(event) {
  if (event.target.id === "output-profile-form") {
    event.preventDefault();
    saveOutputProfile();
  }
}

function handleGalleryScroll(event) {
  if (event.target?.id !== "image-list") {
    return;
  }
  state.galleryScrollTop = event.target.scrollLeft;
  if (galleryScrollFrame) {
    return;
  }
  galleryScrollFrame = window.requestAnimationFrame(() => {
    galleryScrollFrame = 0;
    renderBatch();
  });
}
