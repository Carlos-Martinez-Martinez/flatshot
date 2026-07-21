function renderOutputProfileSelect() {
  const select = $("#output-profile-select");
  if (!select) {
    return;
  }
  select.innerHTML = exportSummaryViewHelpers.outputProfileSelectOptionsHtml(
    state.outputProfiles,
    { includeCustom: !outputMatchesProfile() }
  );
  select.value = outputMatchesProfile() ? state.activeOutputProfileId : "__custom";
}

function outputProfileDisplayName() {
  const profiles = exportOutputProfiles();
  if (!profiles.length) {
    return "Sin salidas activas";
  }
  if (profiles.length > 1) {
    return batchViewHelpers.outputCountLabel(profiles.length);
  }
  const profile = activeOutputProfile();
  if (!profile || !outputMatchesProfile(profile)) {
    return "Salida personalizada";
  }
  return profile.name;
}

function outputProfileManagerRows() {
  const draft = state.outputProfileDraft;
  if (!draft || state.outputProfiles.some((profile) => profile.id === draft.id)) {
    return state.outputProfiles;
  }
  return [...state.outputProfiles, draft];
}

function outputProfileSummaryLine(profile) {
  if (!profile) {
    return "Salida sin configurar";
  }
  return `${profile.format} · ${outputProfileHelpers.outputProfileSize(profile).replace("x", " × ")} · ${settingsViewHelpers.backgroundLabel(profile.background)}`;
}

function outputProfileCompactLabel(profile) {
  if (!profile) {
    return "Sin salida";
  }
  return `${profile.format} · ${settingsViewHelpers.backgroundLabel(profile.background)}`;
}
