function applyOutputProfile(profileId, options = {}) {
  const profile = state.outputProfiles.find((item) => item.id === profileId);
  if (!profile) {
    return false;
  }
  profile.enabled = true;
  if (state.outputProfileDraft?.id === profile.id) {
    state.outputProfileDraft = { ...state.outputProfileDraft, enabled: true };
  }
  const applied = setActiveOutputProfileReference(profile.id, options);
  globalThis.clearOutputConfigurationFailures?.();
  refreshBridgePreviewForAppliedOutputProfile(options);
  return applied;
}

function refreshBridgePreviewForAppliedOutputProfile(options = {}) {
  if (options.refreshPreview === false || typeof selectedImage !== "function" || typeof requestBridgePreview !== "function") {
    return;
  }
  const image = selectedImage();
  if (image?.source === "bridge") {
    void requestBridgePreview(image);
  }
}

function setOutputProfileEnabled(profileId, enabled) {
  const profile = state.outputProfiles.find((item) => item.id === profileId);
  if (!profile) {
    return;
  }
  const wasActiveReference = profile.id === state.activeOutputProfileId;
  profile.enabled = Boolean(enabled);
  if (state.outputProfileDraft?.id === profile.id) {
    state.outputProfileDraft = { ...state.outputProfileDraft, enabled: profile.enabled };
  }

  if (profile.enabled && !enabledActiveOutputProfile()) {
    setActiveOutputProfileReference(profile.id, { render: false, statusText: `Salida activa: ${profile.name}` });
  } else if (!profile.enabled && wasActiveReference) {
    reassignActiveOutputProfileReference({ render: false, statusText: `Salida desactivada: ${profile.name}` });
  }

  state.exportStatus = isExportReady() ? "ready" : "blocked";
  globalThis.clearOutputConfigurationFailures?.();
  state.statusText = profile.enabled ? `Salida activa: ${profile.name}` : `Salida desactivada: ${profile.name}`;
  persistOutputProfiles();
  render();
}
