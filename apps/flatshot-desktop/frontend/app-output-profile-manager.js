function setOutputProfileDraftEnabled(enabled) {
  const draft = ensureOutputProfileDraft();
  state.outputProfileDraft = {
    ...draft,
    enabled: Boolean(enabled),
  };
  state.outputProfileNotice = "";
  state.outputDeleteConfirmId = "";
  renderAppSettings();
}

function selectOutputProfileDraft(profileId) {
  if (state.appSettingsOpen && outputProfileHasUnsavedChanges()) {
    showOutputProfileUnsavedNotice("Guarda o descarta los cambios antes de cambiar de salida.");
    return;
  }
  const profile = outputProfileManagerRows().find((item) => item.id === profileId);
  if (!profile) {
    return;
  }
  state.outputProfileEditorId = profile.id;
  state.outputProfileDraft = { ...profile };
  state.outputProfileNotice = "";
  state.outputDeleteConfirmId = "";
  state.statusText = `Editando salida: ${profile.name}`;
  render();
}

function editOutputProfileFromInspector(profileId) {
  if (state.appSettingsOpen && outputProfileHasUnsavedChanges()) {
    showOutputProfileUnsavedNotice("Guarda o descarta los cambios antes de cambiar de salida.");
    return;
  }
  const profile = outputProfileManagerRows().find((item) => item.id === profileId);
  if (!profile) {
    return;
  }
  rememberModalFocusReturn();
  state.batchDetailOpen = false;
  state.exportConfirmOpen = false;
  state.preferencesOpen = false;
  state.appSettingsOpen = true;
  state.outputProfileEditorId = profile.id;
  state.outputProfileDraft = { ...profile };
  state.outputProfileNotice = "";
  state.outputDeleteConfirmId = "";
  state.statusText = `Editando salida: ${profile.name}`;
  render();
  queueModalFocus("#app-settings-modal", "[data-action='close-app-settings']");
}

function newOutputProfile() {
  if (state.appSettingsOpen && outputProfileHasUnsavedChanges()) {
    showOutputProfileUnsavedNotice("Guarda o descarta los cambios antes de crear otra salida.");
    return;
  }
  const source = currentOutputProfileData();
  const id = outputProfileHelpers.uniqueOutputProfileId("formato", Date.now());
  state.outputProfileEditorId = id;
  state.outputProfileDraft = {
    ...source,
    id,
    name: "Nueva salida",
    enabled: false,
  };
  state.outputProfileNotice = "";
  state.outputDeleteConfirmId = "";
  state.preferencesOpen = false;
  state.appSettingsOpen = true;
  state.statusText = "Nueva salida";
  render();
}

function duplicateOutputProfile() {
  if (state.appSettingsOpen && outputProfileHasUnsavedChanges()) {
    showOutputProfileUnsavedNotice("Guarda o descarta los cambios antes de duplicar.");
    return;
  }
  const source = state.outputProfileDraft || activeOutputProfile() || currentOutputProfileData();
  const id = outputProfileHelpers.uniqueOutputProfileId(source.name || "formato", Date.now());
  state.outputProfileEditorId = id;
  state.outputProfileDraft = {
    ...source,
    id,
    name: `${source.name || "Salida"} copia`,
    enabled: false,
  };
  state.outputProfileNotice = "";
  state.outputDeleteConfirmId = "";
  state.preferencesOpen = false;
  state.appSettingsOpen = true;
  state.statusText = "Salida duplicada";
  render();
}

function commitOutputProfileDraft() {
  const validation = outputProfileHelpers.outputProfileValidation(outputProfileFormRawData());
  if (validation.errors.length) {
    state.statusText = validation.errors[0];
    renderOutputProfileModalState();
    return null;
  }
  const draft = outputProfileDraftFromForm();
  const saved = outputProfileHelpers.normalizeOutputProfile({
    ...draft,
    name: draft.name.trim() || "Salida sin nombre",
  });
  const index = state.outputProfiles.findIndex((profile) => profile.id === saved.id);
  if (index >= 0) {
    state.outputProfiles[index] = saved;
  } else {
    state.outputProfiles.push(saved);
  }
  state.outputProfiles = outputProfileHelpers.normalizeOutputProfileList(state.outputProfiles, saved.id);
  state.outputProfileEditorId = saved.id;
  state.outputProfileDraft = { ...saved };
  state.outputProfileNotice = "";
  state.outputDeleteConfirmId = "";
  if (saved.id === state.activeOutputProfileId && saved.enabled) {
    syncOutputProfileState(saved);
    globalThis.clearOutputConfigurationFailures?.();
  } else if (saved.id === state.activeOutputProfileId && !saved.enabled) {
    reassignActiveOutputProfileReference({ render: false });
    globalThis.clearOutputConfigurationFailures?.();
  }
  persistOutputProfiles();
  return state.outputProfiles.find((profile) => profile.id === saved.id) || saved;
}

function saveOutputProfile(options = {}) {
  const saved = commitOutputProfileDraft();
  if (!saved) {
    return null;
  }
  state.statusText = `Salida guardada: ${saved.name}`;
  if (options.render !== false) {
    render();
  }
  return saved;
}

function deleteManagedOutputProfile() {
  const draft = ensureOutputProfileDraft();
  const exists = state.outputProfiles.some((profile) => profile.id === draft.id);
  if (!exists) {
    const fallback = activeOutputProfile() || state.outputProfiles[0];
    state.outputProfileEditorId = fallback?.id || "";
    state.outputProfileDraft = fallback ? { ...fallback } : null;
    state.outputDeleteConfirmId = "";
    state.statusText = "Salida descartada";
    render();
    return;
  }
  if (state.outputProfiles.length <= 1) {
    state.outputDeleteConfirmId = "";
    state.statusText = "Debe quedar al menos una salida";
    render();
    return;
  }
  state.outputDeleteConfirmId = draft.id;
  state.outputProfileNotice = "";
  state.statusText = `Confirmar eliminación: ${draft.name}`;
  render();
  queueModalFocus("#app-settings-modal", "[data-action='confirm-output-delete']");
}

function cancelDeleteManagedOutputProfile() {
  state.outputDeleteConfirmId = "";
  state.statusText = "Eliminación cancelada";
  render();
}

function confirmDeleteManagedOutputProfile() {
  const profileId = state.outputDeleteConfirmId;
  const profile = state.outputProfiles.find((item) => item.id === profileId);
  if (!profile) {
    state.outputDeleteConfirmId = "";
    render();
    return;
  }
  if (state.outputProfiles.length <= 1) {
    state.outputDeleteConfirmId = "";
    state.statusText = "Debe quedar al menos una salida";
    render();
    return;
  }

  const deletedName = profile.name;
  state.outputProfiles = state.outputProfiles.filter((item) => item.id !== profileId);
  if (state.activeOutputProfileId === profileId) {
    reassignActiveOutputProfileReference({ render: false, statusText: `Salida eliminada: ${deletedName}` });
  }
  const nextDraft = state.outputProfiles.find((profile) => profile.id === state.outputProfileEditorId)
    || state.outputProfiles.find((profile) => profile.id === state.activeOutputProfileId)
    || state.outputProfiles[0];
  state.outputProfileEditorId = nextDraft?.id || "";
  state.outputProfileDraft = nextDraft ? { ...nextDraft } : null;
  state.outputDeleteConfirmId = "";
  persistOutputProfiles();
  state.statusText = `Salida eliminada: ${deletedName}`;
  render();
}

function resetOutputProfileDraft() {
  const original = state.outputProfiles.find((profile) => profile.id === state.outputProfileEditorId)
    || activeOutputProfile()
    || outputProfileHelpers.normalizeOutputProfile(defaultOutputProfiles[0]);
  state.outputProfileDraft = { ...original };
  state.outputProfileEditorId = original.id;
  state.outputProfileNotice = "";
  state.outputDeleteConfirmId = "";
  state.statusText = "Cambios de la salida descartados";
  render();
}

function outputProfileHasUnsavedChanges() {
  if (!state.appSettingsOpen) {
    return false;
  }
  const raw = outputProfileFormRawData();
  const saved = state.outputProfiles.find((profile) => profile.id === raw.id);
  if (!saved) {
    return true;
  }
  return !sameOutputProfileRaw(saved, raw);
}

function showOutputProfileUnsavedNotice(message) {
  state.outputProfileNotice = message;
  state.statusText = "Cambios sin guardar";
  renderOutputProfileModalState();
}

function sameOutputProfileRaw(profile, raw) {
  if (!profile || !raw) {
    return false;
  }
  const destinationMode = raw.destinationMode === "custom" ? "custom" : "source";
  return String(profile.name || "").trim() === String(raw.name || "").trim()
    && profile.format === outputProfileHelpers.normalizeExportFormat(raw.format)
    && profile.background === raw.background
    && String(profile.width) === String(raw.width || "").trim()
    && String(profile.height) === String(raw.height || "").trim()
    && profile.destinationMode === destinationMode
    && String(profile.destinationValue || "") === String(raw.destinationValue || "")
    && String(profile.naming || "") === String(raw.naming || "")
    && String(profile.suffix || "") === String(raw.suffix || "")
    && String(profile.maxFileSizeKb || "") === String(outputProfileHelpers.normalizeMaxFileSizeKb(raw.maxFileSizeKb) || "")
    && Boolean(profile.enabled) === Boolean(raw.enabled);
}

function outputProfileChangeCount() {
  const raw = outputProfileFormRawData();
  const saved = state.outputProfiles.find((profile) => profile.id === raw.id);
  if (!saved) {
    return 1;
  }
  const destinationMode = raw.destinationMode === "custom" ? "custom" : "source";
  const checks = [
    String(saved.name || "").trim() !== String(raw.name || "").trim(),
    saved.format !== outputProfileHelpers.normalizeExportFormat(raw.format),
    saved.background !== raw.background,
    String(saved.width) !== String(raw.width || "").trim(),
    String(saved.height) !== String(raw.height || "").trim(),
    saved.destinationMode !== destinationMode,
    String(saved.destinationValue || "") !== String(raw.destinationValue || ""),
    String(saved.naming || "") !== String(raw.naming || ""),
    String(saved.suffix || "") !== String(raw.suffix || ""),
    String(saved.maxFileSizeKb || "") !== String(outputProfileHelpers.normalizeMaxFileSizeKb(raw.maxFileSizeKb) || ""),
    Boolean(saved.enabled) !== Boolean(raw.enabled),
  ];
  return checks.filter(Boolean).length;
}
