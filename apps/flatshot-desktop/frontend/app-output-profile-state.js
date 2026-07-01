function activeOutputProfile() {
  return state.outputProfiles.find((profile) => profile.id === state.activeOutputProfileId)
    || state.outputProfiles[0]
    || defaultOutputProfiles[0];
}

function galleryOutputProfiles() {
  return state.outputProfiles.length ? state.outputProfiles : [currentOutputProfileData()];
}

function galleryActiveOutputContext() {
  const savedProfile = activeOutputProfile();
  const matchesSavedProfile = outputMatchesProfile(savedProfile);
  const profile = matchesSavedProfile ? savedProfile : currentOutputProfileData();
  return {
    background: profile?.background || state.background || "rgb230",
    id: matchesSavedProfile ? profile.id : "__custom",
    label: outputProfileCompactLabel(profile),
    name: matchesSavedProfile ? profile.name : "Formato personalizado",
    profile,
    summary: outputProfileSummaryLine(profile),
  };
}

function enabledOutputProfiles() {
  return state.outputProfiles.filter((profile) => profile.enabled);
}

function enabledActiveOutputProfile() {
  return state.outputProfiles.find((profile) => profile.id === state.activeOutputProfileId && profile.enabled) || null;
}

function isActiveOutputProfile(profile) {
  return Boolean(profile && profile.enabled && profile.id === state.activeOutputProfileId);
}

function syncOutputProfileState(profile) {
  if (!profile) {
    return;
  }
  state.format = profile.format;
  state.size = outputProfileHelpers.outputProfileSize(profile);
  state.background = profile.background;
  state.previewBg = profile.background;
  state.destinationMode = profile.destinationMode;
  state.destinationValue = profile.destinationValue;
  state.naming = profile.naming;
  state.suffix = profile.suffix;
  state.exportStatus = isExportReady() ? "ready" : "blocked";
}

function setActiveOutputProfileReference(profileId, options = {}) {
  const profile = state.outputProfiles.find((item) => item.id === profileId);
  if (!profile || !profile.enabled) {
    return false;
  }
  state.activeOutputProfileId = profile.id;
  syncOutputProfileState(profile);
  state.statusText = options.statusText || `Formato activo: ${profile.name}`;
  persistOutputProfiles();
  if (options.render !== false) {
    render();
  }
  return true;
}

function reassignActiveOutputProfileReference(options = {}) {
  const next = enabledOutputProfiles()[0] || null;
  if (!next) {
    state.activeOutputProfileId = "";
    state.exportStatus = isExportReady() ? "ready" : "blocked";
    state.statusText = options.statusText || "Sin formatos activos";
    persistOutputProfiles();
    if (options.render !== false) {
      render();
    }
    return null;
  }
  setActiveOutputProfileReference(next.id, {
    render: options.render,
    statusText: options.statusText || `Formato activo: ${next.name}`,
  });
  return next;
}

function exportOutputProfiles() {
  const current = { ...currentOutputProfileData(), enabled: true };
  const activeId = state.activeOutputProfileId;
  const profiles = [];
  const seen = new Set();
  const pushProfile = (profile) => {
    if (!profile || seen.has(profile.id)) {
      return;
    }
    seen.add(profile.id);
    profiles.push(profile);
  };

  state.outputProfiles.forEach((profile) => {
    if (!profile.enabled) {
      return;
    }
    if (profile.id === activeId && !outputMatchesProfile(profile)) {
      pushProfile(current);
      return;
    }
    if (profile.enabled) {
      pushProfile(profile);
    }
  });
  return profiles;
}

function exportOutputCount() {
  return exportOutputProfiles().length;
}

function currentOutputProfileData() {
  const size = outputProfileHelpers.parseOutputSize(state.size);
  return outputProfileHelpers.normalizeOutputProfile({
    id: state.activeOutputProfileId || outputProfileHelpers.uniqueOutputProfileId("actual"),
    name: activeOutputProfile()?.name || "Formato actual",
    enabled: Boolean(activeOutputProfile()?.enabled),
    format: state.format,
    width: size.width,
    height: size.height,
    background: state.background,
    destinationMode: state.destinationMode,
    destinationValue: state.destinationValue,
    naming: state.naming,
    suffix: state.suffix,
  });
}

function outputMatchesProfile(profile = activeOutputProfile()) {
  if (!profile) {
    return false;
  }
  const current = currentOutputProfileData();
  return current.format === profile.format
    && current.width === profile.width
    && current.height === profile.height
    && current.background === profile.background
    && current.destinationMode === profile.destinationMode
    && current.destinationValue === profile.destinationValue
    && current.naming === profile.naming
    && current.suffix === profile.suffix;
}

function persistOutputProfiles() {
  storageHelpers.writeJson(window.localStorage, STORAGE_KEYS.outputProfiles, state.outputProfiles);
  storageHelpers.writeValue(window.localStorage, STORAGE_KEYS.activeOutputProfile, state.activeOutputProfileId);
  storageHelpers.writeJson(window.localStorage, STORAGE_KEYS.activeOutputFormats, enabledOutputProfiles().map((profile) => profile.id));
  persistExportPreferences({ saveBridge: false });
  scheduleBridgeUiPreferencesSave(0);
}
