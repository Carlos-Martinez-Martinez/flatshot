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
