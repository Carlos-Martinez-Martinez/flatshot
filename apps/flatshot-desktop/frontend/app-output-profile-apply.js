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
    setActiveOutputProfileReference(profile.id, { render: false, statusText: `Formato activo: ${profile.name}` });
  } else if (!profile.enabled && wasActiveReference) {
    reassignActiveOutputProfileReference({ render: false, statusText: `Formato desactivado: ${profile.name}` });
  }

  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = profile.enabled ? `Formato activo: ${profile.name}` : `Formato desactivado: ${profile.name}`;
  persistOutputProfiles();
  render();
}
