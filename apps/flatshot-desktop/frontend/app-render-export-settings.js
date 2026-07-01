function renderExport() {
  renderOutputProfileSelect();
  $("#format-select").value = state.format;
  $("#size-select").value = state.size;
  syncBackgroundSelectValue($("#background-select"), state.background);
  $("#destination-mode").value = state.destinationMode;
  $("#destination-input").value = state.destinationValue;
  $("#naming-input").value = state.naming;

  const issues = preflightIssues();
  const exportable = exportableImages().length;
  const activeOutputs = exportOutputCount();
  const outputCount = exportable * activeOutputs;
  const ready = isExportReady();
  const destinationText = destinationCompactLabel();
  const warningCount = visibleWarningCount();
  $("#export-readiness").textContent = state.outputEditMode ? "Editar formato" : outputProfileDisplayName();
  $("#export-count").textContent = outputCount ? `${outputCount} archivos` : "Pendiente";
  $("#export-count").classList.toggle("dirty", !ready);
  const warningsReadiness = $("#warnings-readiness");
  if (warningsReadiness) {
    warningsReadiness.textContent = warningCount ? `${warningCount} aviso${warningCount === 1 ? "" : "s"}` : "Sin avisos";
  }
  const warningsTab = $("[data-inspector-tab='warnings']");
  if (warningsTab) {
    warningsTab.textContent = warningCount ? `Avisos ${warningCount}` : "Avisos";
  }

  const warningSummary = outputWarningSummary(issues);
  const editDirty = !outputMatchesProfile(activeOutputProfile());
  const activeOutputProfiles = exportOutputProfiles();
  const hasMultipleOutputs = activeOutputProfiles.length > 1;
  $("#export-summary").innerHTML = exportSummaryViewHelpers.exportSummaryHtml({
    editing: state.outputEditMode,
    displayName: outputProfileDisplayName(),
    presetSummary: presetSummaryLine(),
    editDirty,
    activeOutputCount: activeOutputProfiles.length,
    outputCount,
    profileRows: activeOutputProfiles.map((profile) => ({
      format: profile.format,
      name: profile.name,
      size: outputProfileHelpers.outputProfileSize(profile),
      destinationLabel: outputProfileViewHelpers.profileDestinationLabel(profile),
    })),
    formatLabel: activeOutputProfiles.length
      ? hasMultipleOutputs ? batchViewHelpers.outputCountLabel(activeOutputProfiles.length) : state.format
      : "Sin formato activo",
    sizeLabel: activeOutputProfiles.length ? hasMultipleOutputs ? "Por formato" : state.size.replace("x", " × ") : "-",
    backgroundLabel: activeOutputProfiles.length ? hasMultipleOutputs ? "Por formato" : settingsViewHelpers.backgroundLabel(state.background) : "-",
    destinationText,
    namingLabel: activeOutputProfiles.length ? hasMultipleOutputs ? "Por formato" : namingHumanLabel() : "-",
    example: activeOutputProfiles.length ? hasMultipleOutputs ? outputNameForProfile(activeOutputProfiles[0]) : namingExample() : "-",
    warningSummaryHtml: warningSummary,
    temporaryNoticeHtml: !outputMatchesProfile(activeOutputProfile()) ? inspectorOutputViewHelpers.outputTemporaryNoticeHtml() : "",
  });

  renderExportResult();

  $("#issue-list").innerHTML = issueListHtml();
}

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
    return "Sin formatos activos";
  }
  if (profiles.length > 1) {
    return batchViewHelpers.outputCountLabel(profiles.length);
  }
  const profile = activeOutputProfile();
  if (!profile || !outputMatchesProfile(profile)) {
    return "Formato personalizado";
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
    return "Formato sin configurar";
  }
  return `${profile.format} · ${outputProfileHelpers.outputProfileSize(profile).replace("x", " × ")} · ${settingsViewHelpers.backgroundLabel(profile.background)}`;
}

function syncBackgroundSelectValue(select, background) {
  if (!select) {
    return;
  }
  const normalized = outputProfileHelpers.normalizeBackgroundValue(background);
  select.innerHTML = backgroundSelectOptionsHtml(normalized);
  select.value = normalized;
}

function selectedBackgroundPresetFromForm(raw = outputProfileFormRawData()) {
  return backgroundPresetByValue(raw.background);
}

function backgroundRgbFromValue(value) {
  return outputProfileHelpers.parseRgbBackground(outputProfileHelpers.normalizeBackgroundValue(value)) || outputProfileHelpers.backgroundColorTuple(value);
}

function positionBackgroundPresetEditor() {
  const editor = $("#background-preset-editor");
  if (!editor || editor.hidden) {
    return;
  }
  const anchor = $("#profile-background-input");
  const dialog = $("#app-settings-modal .app-settings-dialog");
  const footer = $("#app-settings-modal .app-settings-footer");
  if (!anchor || !dialog) {
    return;
  }
  const margin = 16;
  const anchorRect = anchor.getBoundingClientRect();
  const dialogRect = dialog.getBoundingClientRect();
  const footerRect = footer?.getBoundingClientRect();
  const maxWidth = Math.max(280, Math.min(486, window.innerWidth - margin * 2, dialogRect.width - margin * 2));
  editor.style.width = `${maxWidth}px`;
  const editorHeight = editor.offsetHeight || 0;
  const left = numberHelpers.clampNumber(anchorRect.left, dialogRect.left + margin, dialogRect.right - maxWidth - margin);
  const footerTop = footerRect?.top || dialogRect.bottom;
  const preferredTop = anchorRect.bottom + 8;
  const maxTop = Math.max(dialogRect.top + margin, footerTop - editorHeight - 8);
  const top = numberHelpers.clampNumber(preferredTop, dialogRect.top + margin, maxTop);
  editor.style.left = `${left}px`;
  editor.style.top = `${top}px`;
}

function renderBackgroundPresetControls(raw = outputProfileFormRawData()) {
  const selectedPreset = selectedBackgroundPresetFromForm(raw);
  const editor = $("#background-preset-editor");
  const actions = $(".background-preset-actions");
  const deleteButton = $("[data-action='delete-background-preset']");
  if (deleteButton) {
    deleteButton.disabled = !selectedPreset || state.backgroundPresets.length <= 1;
    deleteButton.title = !selectedPreset
      ? "Este fondo no está guardado como preset"
      : state.backgroundPresets.length <= 1
        ? "Debe quedar al menos un fondo"
        : "Eliminar fondo";
  }
  if (!editor) {
    return;
  }
  const editorState = state.backgroundPresetEditor;
  if (actions) {
    actions.hidden = Boolean(editorState);
  }
  editor.hidden = !editorState;
  if (!editorState) {
    return;
  }
  const nameInput = $("#background-preset-name-input");
  const kindInput = $("#background-preset-kind-input");
  const rgbInput = $("#background-preset-rgb-input");
  const rgbField = $(".background-preset-rgb-field");
  if (nameInput && nameInput.value !== editorState.name) {
    nameInput.value = editorState.name;
  }
  if (kindInput && kindInput.value !== editorState.kind) {
    kindInput.value = editorState.kind;
  }
  if (rgbInput && rgbInput.value !== editorState.rgbText) {
    rgbInput.value = editorState.rgbText;
  }
  if (rgbField) {
    rgbField.hidden = editorState.kind === "transparent";
  }
  editor.classList.toggle("is-transparent", editorState.kind === "transparent");
  const swatch = $("#background-preset-swatch");
  if (swatch) {
    const rgb = editorState.kind === "transparent" ? null : outputProfileHelpers.parseRgbBackground(outputProfileHelpers.customRgbBackgroundValue(editorState.rgbText));
    const isInvalidRgb = editorState.kind !== "transparent" && !rgb;
    swatch.classList.toggle("is-transparent", editorState.kind === "transparent");
    swatch.classList.toggle("is-invalid", isInvalidRgb);
    swatch.style.backgroundColor = rgb ? `rgb(${rgb.join(", ")})` : "";
    swatch.setAttribute(
      "aria-label",
      editorState.kind === "transparent"
        ? "Muestra del fondo transparente"
        : rgb
          ? `Muestra del fondo RGB ${rgb.join(", ")}`
          : "Muestra del fondo sin RGB válido"
    );
  }
  const message = $("#background-preset-editor-message");
  if (message) {
    message.textContent = editorState.error || "";
    message.hidden = !editorState.error;
    message.classList.toggle("error", Boolean(editorState.error));
  }
  positionBackgroundPresetEditor();
}

function updateBackgroundPresetEditorFromFields() {
  const editor = state.backgroundPresetEditor;
  if (!editor) {
    return;
  }
  state.backgroundPresetEditor = {
    ...editor,
    error: "",
    kind: $("#background-preset-kind-input")?.value === "transparent" ? "transparent" : "rgb",
    name: $("#background-preset-name-input")?.value || "",
    rgbText: $("#background-preset-rgb-input")?.value || "",
  };
}

function beginBackgroundPresetEdit(mode = "edit") {
  const raw = outputProfileFormRawData();
  const preset = mode === "edit" ? selectedBackgroundPresetFromForm(raw) : null;
  const source = preset || {
    id: outputProfileHelpers.uniqueOutputProfileId("fondo", Date.now()),
    kind: raw.background === "transparent" ? "transparent" : "rgb",
    name: preset ? preset.name : "Nuevo fondo",
    rgb: backgroundRgbFromValue(raw.background),
  };
  state.backgroundPresetEditor = {
    id: mode === "edit" && preset ? preset.id : outputProfileHelpers.uniqueOutputProfileId(source.name || "fondo", Date.now()),
    mode: mode === "edit" && preset ? "edit" : "new",
    sourceValue: preset ? backgroundPresetHelpers.backgroundPresetValue(preset, backgroundHelperOptions()) : "",
    kind: source.kind === "transparent" ? "transparent" : "rgb",
    name: source.name,
    rgbText: (source.rgb || [230, 230, 230]).join(", "),
    error: "",
  };
  renderOutputProfileModalState();
}

function saveBackgroundPreset() {
  updateBackgroundPresetEditorFromFields();
  const editor = state.backgroundPresetEditor;
  if (!editor) {
    return;
  }
  const name = editor.name.trim();
  const rgb = outputProfileHelpers.customRgbBackgroundValue(editor.rgbText);
  if (!name) {
    state.backgroundPresetEditor = { ...editor, error: "Pon un nombre al fondo." };
    renderBackgroundPresetControls();
    return;
  }
  if (editor.kind !== "transparent" && !rgb) {
    state.backgroundPresetEditor = { ...editor, error: "Indica un RGB válido entre 0 y 255." };
    renderBackgroundPresetControls();
    return;
  }
  const savedPreset = backgroundPresetHelpers.normalizeBackgroundPreset({
    id: editor.id,
    kind: editor.kind,
    name,
    rgb: editor.kind === "transparent" ? [230, 230, 230] : outputProfileHelpers.parseRgbBackground(rgb),
  }, 0, backgroundPresetOptions());
  const previousValue = editor.mode === "edit" ? editor.sourceValue : "";
  const index = state.backgroundPresets.findIndex((preset) => preset.id === editor.id);
  if (index >= 0) {
    state.backgroundPresets[index] = savedPreset;
  } else {
    state.backgroundPresets.push(savedPreset);
  }
  state.backgroundPresets = backgroundPresetHelpers.normalizeBackgroundPresetList(state.backgroundPresets, backgroundPresetOptions());
  const nextValue = backgroundPresetHelpers.backgroundPresetValue(savedPreset, backgroundHelperOptions());
  if (previousValue) {
    replaceBackgroundValue(previousValue, nextValue);
  } else {
    const draft = ensureOutputProfileDraft();
    state.outputProfileDraft = { ...draft, background: nextValue };
  }
  state.backgroundPresetEditor = null;
  state.statusText = `Fondo guardado: ${savedPreset.name}`;
  persistBackgroundPresets();
  render();
}

function replaceBackgroundValue(previousValue, nextValue) {
  const previous = outputProfileHelpers.normalizeBackgroundValue(previousValue);
  const next = outputProfileHelpers.normalizeBackgroundValue(nextValue);
  state.outputProfiles = state.outputProfiles.map((profile) => (
    outputProfileHelpers.normalizeBackgroundValue(profile.background) === previous ? { ...profile, background: next } : profile
  ));
  if (state.outputProfileDraft && outputProfileHelpers.normalizeBackgroundValue(state.outputProfileDraft.background) === previous) {
    state.outputProfileDraft = { ...state.outputProfileDraft, background: next };
  }
  if (outputProfileHelpers.normalizeBackgroundValue(state.background) === previous) {
    state.background = next;
  }
  if (outputProfileHelpers.normalizeBackgroundValue(state.previewBg) === previous) {
    state.previewBg = next;
  }
  persistOutputProfiles();
}

function deleteBackgroundPreset() {
  const preset = selectedBackgroundPresetFromForm();
  if (!preset || state.backgroundPresets.length <= 1) {
    return;
  }
  const confirmed = window.confirm(`Eliminar fondo "${preset.name}"?\n\nLos formatos que ya usen ese RGB conservarán el valor actual.`);
  if (!confirmed) {
    return;
  }
  state.backgroundPresets = state.backgroundPresets.filter((item) => item.id !== preset.id);
  state.backgroundPresetEditor = null;
  state.statusText = `Fondo eliminado: ${preset.name}`;
  persistBackgroundPresets();
  render();
}

function outputProfileCompactLabel(profile) {
  if (!profile) {
    return "Sin salida";
  }
  return `${profile.format} · ${settingsViewHelpers.backgroundLabel(profile.background)}`;
}

function ensureOutputProfileDraft() {
  const current = state.outputProfiles.find((profile) => profile.id === state.outputProfileEditorId)
    || state.outputProfileDraft
    || activeOutputProfile()
    || outputProfileHelpers.normalizeOutputProfile(defaultOutputProfiles[0]);
  if (!state.outputProfileEditorId) {
    state.outputProfileEditorId = current.id;
  }
  if (!state.outputProfileDraft || state.outputProfileDraft.id !== state.outputProfileEditorId) {
    state.outputProfileDraft = { ...current };
  }
  return state.outputProfileDraft;
}

function setOutputProfileFormValues(profile) {
  syncBackgroundSelectValue($("#profile-background-input"), profile.background);
  const pairs = [
    ["profile-name-input", profile.name],
    ["profile-format-input", profile.format],
    ["profile-width-input", profile.width],
    ["profile-height-input", profile.height],
    ["profile-destination-mode-input", profile.destinationMode],
    ["profile-suffix-input", profile.suffix],
    ["profile-destination-input", profile.destinationValue],
    ["profile-naming-input", profile.naming],
  ];
  pairs.forEach(([id, value]) => {
    const input = $(`#${id}`);
    if (input && input.value !== String(value ?? "")) {
      input.value = value ?? "";
    }
  });
}

function outputProfileFormRawData() {
  const current = ensureOutputProfileDraft();
  const value = (id, fallback = "") => {
    const input = $(`#${id}`);
    return input ? String(input.value ?? "") : String(fallback ?? "");
  };
  const backgroundMode = value("profile-background-input", backgroundPresetHelpers.backgroundSelectMode(current.background, backgroundHelperOptions()));
  return {
    id: current.id,
    name: value("profile-name-input", current.name),
    format: value("profile-format-input", current.format),
    background: outputProfileHelpers.normalizeBackgroundValue(backgroundMode, current.background),
    width: value("profile-width-input", current.width),
    height: value("profile-height-input", current.height),
    destinationMode: value("profile-destination-mode-input", current.destinationMode),
    destinationValue: value("profile-destination-input", current.destinationValue),
    naming: value("profile-naming-input", current.naming),
    suffix: value("profile-suffix-input", current.suffix),
    enabled: Boolean(current.enabled),
  };
}

function outputProfileRawFromProfile(profile) {
  return {
    id: profile.id,
    name: profile.name,
    format: profile.format,
    background: profile.background,
    backgroundCustom: outputProfileHelpers.backgroundCustomText(profile.background),
    backgroundMode: backgroundPresetHelpers.backgroundSelectMode(profile.background, backgroundHelperOptions()),
    width: String(profile.width),
    height: String(profile.height),
    destinationMode: profile.destinationMode,
    destinationValue: profile.destinationValue,
    naming: profile.naming,
    suffix: profile.suffix,
  };
}

function outputProfileDraftFromForm() {
  const current = ensureOutputProfileDraft();
  const raw = outputProfileFormRawData();
  return outputProfileHelpers.normalizeOutputProfile({
    id: current.id,
    name: raw.name,
    enabled: Boolean(raw.enabled),
    format: raw.format,
    background: raw.background,
    width: raw.width,
    height: raw.height,
    destinationMode: raw.destinationMode,
    destinationValue: raw.destinationValue,
    naming: raw.naming,
    suffix: raw.suffix,
  });
}

function updateOutputProfileDraftFromForm() {
  if (!state.appSettingsOpen) {
    return;
  }
  state.outputProfileNotice = "";
  syncTransparentBackgroundFormat();
  syncOutputProfileDestinationMode();
  state.outputDeleteConfirmId = "";
  state.outputProfileDraft = outputProfileDraftFromForm();
}

function syncTransparentBackgroundFormat() {
  const backgroundInput = $("#profile-background-input");
  const formatInput = $("#profile-format-input");
  if (!backgroundInput || !formatInput) {
    return;
  }
  if (outputProfileHelpers.normalizeBackgroundValue(backgroundInput.value) === "transparent" && outputProfileHelpers.normalizeExportFormat(formatInput.value) !== "PNG") {
    formatInput.value = "PNG";
  }
}

function looksLikeAbsoluteOutputPath(value) {
  const text = String(value || "").trim();
  return /^[A-Za-z]:[\\/]/.test(text) || /^[/\\]{2}/.test(text) || text.startsWith("/");
}

function syncOutputProfileDestinationMode() {
  const modeInput = $("#profile-destination-mode-input");
  const destinationInput = $("#profile-destination-input");
  if (!modeInput || !destinationInput) {
    return;
  }
  const mode = modeInput.value === "custom" ? "custom" : "source";
  const value = String(destinationInput.value || "").trim();
  if (mode === "source" && (!value || looksLikeAbsoluteOutputPath(value))) {
    destinationInput.value = "Salida";
    return;
  }
  if (mode === "custom" && (!value || value === "Salida")) {
    destinationInput.value = storageHelpers.readValue(window.localStorage, STORAGE_KEYS.lastOutputFolder) || "";
  }
}

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
    showOutputProfileUnsavedNotice("Guarda o descarta los cambios antes de cambiar de formato.");
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
  state.statusText = `Editando formato: ${profile.name}`;
  render();
}

function newOutputProfile() {
  if (state.appSettingsOpen && outputProfileHasUnsavedChanges()) {
    showOutputProfileUnsavedNotice("Guarda o descarta los cambios antes de crear otro formato.");
    return;
  }
  const source = currentOutputProfileData();
  const id = outputProfileHelpers.uniqueOutputProfileId("formato", Date.now());
  state.outputProfileEditorId = id;
  state.outputProfileDraft = {
    ...source,
    id,
    name: "Nuevo formato",
    enabled: false,
  };
  state.outputProfileNotice = "";
  state.outputDeleteConfirmId = "";
  state.appSettingsOpen = true;
  state.statusText = "Nuevo formato de salida";
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
    name: `${source.name || "Formato"} copia`,
    enabled: false,
  };
  state.outputProfileNotice = "";
  state.outputDeleteConfirmId = "";
  state.appSettingsOpen = true;
  state.statusText = "Formato duplicado";
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
    name: draft.name.trim() || "Formato sin nombre",
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
  } else if (saved.id === state.activeOutputProfileId && !saved.enabled) {
    reassignActiveOutputProfileReference({ render: false });
  }
  persistOutputProfiles();
  return state.outputProfiles.find((profile) => profile.id === saved.id) || saved;
}

function saveOutputProfile(options = {}) {
  const saved = commitOutputProfileDraft();
  if (!saved) {
    return null;
  }
  state.statusText = `Formato guardado: ${saved.name}`;
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
    state.statusText = "Formato descartado";
    render();
    return;
  }
  if (state.outputProfiles.length <= 1) {
    state.outputDeleteConfirmId = "";
    state.statusText = "Debe quedar al menos un formato";
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
    state.statusText = "Debe quedar al menos un formato";
    render();
    return;
  }

  const deletedName = profile.name;
  state.outputProfiles = state.outputProfiles.filter((item) => item.id !== profileId);
  if (state.activeOutputProfileId === profileId) {
    reassignActiveOutputProfileReference({ render: false, statusText: `Formato eliminado: ${deletedName}` });
  }
  const nextDraft = state.outputProfiles.find((profile) => profile.id === state.outputProfileEditorId)
    || state.outputProfiles.find((profile) => profile.id === state.activeOutputProfileId)
    || state.outputProfiles[0];
  state.outputProfileEditorId = nextDraft?.id || "";
  state.outputProfileDraft = nextDraft ? { ...nextDraft } : null;
  state.outputDeleteConfirmId = "";
  persistOutputProfiles();
  state.statusText = `Formato eliminado: ${deletedName}`;
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
  state.statusText = "Cambios del formato descartados";
  render();
}

function openAppSettings() {
  rememberModalFocusReturn();
  state.batchDetailOpen = false;
  state.exportConfirmOpen = false;
  const activeProfile = activeOutputProfile();
  const profile = outputMatchesProfile(activeProfile)
    ? activeProfile
    : {
      ...currentOutputProfileData(),
      id: outputProfileHelpers.uniqueOutputProfileId("formato-personalizado", Date.now()),
      name: "Formato personalizado",
    };
  state.appSettingsOpen = true;
  state.outputProfileEditorId = profile.id;
  state.outputProfileDraft = { ...profile };
  state.outputDeleteConfirmId = "";
  state.statusText = "Formatos de salida";
  render();
  queueModalFocus("#app-settings-modal", "[data-action='close-app-settings']");
}

function closeAppSettings() {
  if (state.appSettingsOpen && outputProfileHasUnsavedChanges()) {
    showOutputProfileUnsavedNotice("Guarda o descarta los cambios antes de cerrar.");
    return;
  }
  releaseModalFocusBeforeHide();
  state.appSettingsOpen = false;
  state.outputProfileDraft = null;
  state.outputProfileNotice = "";
  state.outputDeleteConfirmId = "";
  state.statusText = "Configuración cerrada";
  render();
}

function cancelOutputProfileDraft() {
  releaseModalFocusBeforeHide();
  const fallback = enabledActiveOutputProfile()
    || state.outputProfiles.find((profile) => profile.id === state.activeOutputProfileId)
    || state.outputProfiles[0]
    || null;
  state.appSettingsOpen = false;
  state.outputProfileEditorId = fallback?.id || "";
  state.outputProfileDraft = null;
  state.outputDeleteConfirmId = "";
  state.statusText = "Formato descartado";
  render();
}

function openBatchDetail() {
  rememberModalFocusReturn();
  state.exportConfirmOpen = false;
  state.batchDetailOpen = true;
  state.statusText = "Detalle del lote";
  render();
  queueModalFocus("#batch-detail-modal", "[data-action='close-batch-detail']");
}

function closeBatchDetail() {
  releaseModalFocusBeforeHide();
  state.batchDetailOpen = false;
  state.statusText = hasBatch() ? "Lote cargado" : "Sin lote";
  render();
}

function openExportConfirm(risks, options = {}) {
  rememberModalFocusReturn();
  state.appSettingsOpen = false;
  state.outputProfileDraft = null;
  state.outputDeleteConfirmId = "";
  state.batchDetailOpen = false;
  state.exportConfirmOpen = true;
  state.exportConfirmRisks = preflightHelpers.dedupeExportRisks(risks);
  state.exportConfirmOptions = { ...options };
  state.statusText = state.exportConfirmRisks.some((risk) => risk.blocking)
    ? "Resuelve problemas antes de exportar"
    : "Confirmar exportación";
  render();
  queueModalFocus("#export-confirm-modal", "#export-confirm-action");
}

function closeExportConfirm({ renderAfter = true } = {}) {
  releaseModalFocusBeforeHide();
  state.exportConfirmOpen = false;
  state.exportConfirmRisks = [];
  state.exportConfirmOptions = null;
  if (renderAfter) {
    render();
  }
}

function confirmExportFromModal() {
  const risks = state.exportConfirmRisks || [];
  if (risks.some((risk) => risk.blocking)) {
    closeExportConfirm({ renderAfter: false });
    reviewWarnings();
    return;
  }
  const options = { ...(state.exportConfirmOptions || {}), confirmed: true };
  closeExportConfirm({ renderAfter: false });
  startExport(options);
}

function rememberModalFocusReturn() {
  const active = document.activeElement;
  if (
    active instanceof HTMLElement
    && active !== document.body
    && !active.closest(".app-settings-backdrop")
  ) {
    modalFocusReturnTarget = active;
  }
}

function restoreModalFocusReturn() {
  const target = modalFocusReturnTarget;
  modalFocusReturnTarget = null;
  if (target instanceof HTMLElement && document.contains(target)) {
    target.focus({ preventScroll: true });
  }
}

function releaseModalFocusBeforeHide() {
  const active = document.activeElement;
  if (active instanceof HTMLElement && active.closest(".app-settings-backdrop")) {
    active.blur();
  }
  restoreModalFocusReturn();
}

function queueModalFocus(modalSelector, preferredSelector = "") {
  window.requestAnimationFrame(() => {
    const modal = $(modalSelector);
    if (!modal || modal.classList.contains("is-hidden")) {
      return;
    }
    const preferred = preferredSelector ? modal.querySelector(preferredSelector) : null;
    const fallback = firstFocusableElement(modal);
    (preferred || fallback)?.focus({ preventScroll: true });
  });
}

function firstFocusableElement(container) {
  return Array.from(container.querySelectorAll(
    "button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), summary, [tabindex]:not([tabindex='-1'])"
  )).find((element) => element.offsetParent !== null);
}

function currentOpenModal() {
  if (state.exportConfirmOpen) {
    return $("#export-confirm-modal");
  }
  if (state.appSettingsOpen) {
    return $("#app-settings-modal");
  }
  if (state.batchDetailOpen) {
    return $("#batch-detail-modal");
  }
  return null;
}

function trapOpenModalFocus(event) {
  const modal = currentOpenModal();
  if (!modal || modal.classList.contains("is-hidden")) {
    return false;
  }
  const focusable = Array.from(modal.querySelectorAll(
    "button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), summary, [tabindex]:not([tabindex='-1'])"
  )).filter((element) => element.offsetParent !== null);
  if (!focusable.length) {
    event.preventDefault();
    return true;
  }
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  const active = document.activeElement;
  if (event.shiftKey && active === first) {
    event.preventDefault();
    last.focus({ preventScroll: true });
    return true;
  }
  if (!event.shiftKey && active === last) {
    event.preventDefault();
    first.focus({ preventScroll: true });
    return true;
  }
  if (!modal.contains(active)) {
    event.preventDefault();
    first.focus({ preventScroll: true });
    return true;
  }
  return false;
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
    Boolean(saved.enabled) !== Boolean(raw.enabled),
  ];
  return checks.filter(Boolean).length;
}

function outputProfileEditorHeadingHtml(profile, validation, dirty) {
  const saved = state.outputProfiles.find((item) => item.id === profile.id);
  return outputProfileViewHelpers.outputProfileEditorHeadingHtml({
    profile,
    validation,
    dirty,
    enabled: Boolean(profile.enabled),
    isPersisted: Boolean(saved),
    new: !saved,
  });
}

function outputProfilePreviewHtml(profile, validation = {}) {
  const image = selectedImage();
  const originalName = image?.name || "imagen_original.png";
  const resultName = outputNameForProfile(profile, image);
  const destination = outputProfileViewHelpers.profileDestinationPreviewLabel(profile);
  const resultPath = destination && destination !== "junto al origen"
    ? `${destination.replace(/[\\/]$/, "")}/${resultName}`
    : resultName;
  return outputProfileViewHelpers.outputProfilePreviewHtml({
    originalName,
    resultName,
    destination,
    resultPath,
    summary: outputProfileSummaryLine(profile),
    validation,
  });
}

function outputNameForProfile(profile, image = selectedImage(), index = 1) {
  return outputProfileViewHelpers.outputNameForProfile(profile, {
    folders: activeFolders(),
    image,
    index,
  });
}

function renderOutputProfileModalState() {
  const raw = outputProfileFormRawData();
  const profile = outputProfileDraftFromForm();
  state.outputProfileDraft = profile;
  if (state.outputDeleteConfirmId && state.outputDeleteConfirmId !== profile.id) {
    state.outputDeleteConfirmId = "";
  }
  const validation = outputProfileHelpers.outputProfileValidation(raw);
  const dirty = outputProfileHasUnsavedChanges();
  const heading = $("#output-profile-editor-heading");
  if (heading) {
    heading.innerHTML = outputProfileEditorHeadingHtml(profile, validation, dirty);
  }
  const preview = $("#output-profile-preview");
  if (preview) {
    preview.innerHTML = outputProfilePreviewHtml(profile, validation);
  }
  const validationTarget = $("#output-profile-validation");
  if (validationTarget) {
    validationTarget.innerHTML = "";
    validationTarget.hidden = true;
  }
  updateOutputProfileFieldStates(validation, raw);
  renderBackgroundPresetControls(raw);
  updateOutputProfileFooterState(validation, dirty);
  renderOutputProfileDeleteConfirm(profile);
}

function updateOutputProfileFieldStates(validation, raw) {
  const fieldIds = {
    name: "profile-name-input",
    format: "profile-format-input",
    background: "profile-background-input",
    backgroundCustom: "profile-background-custom-input",
    width: "profile-width-input",
    height: "profile-height-input",
    destinationMode: "profile-destination-mode-input",
    destinationValue: "profile-destination-input",
    naming: "profile-naming-input",
    suffix: "profile-suffix-input",
  };
  Object.entries(fieldIds).forEach(([field, id]) => {
    const input = $(`#${id}`);
    if (!input) {
      return;
    }
    const tone = validation.fields[field];
    const fieldMessages = validation.fieldMessages?.[field] || [];
    input.classList.toggle("is-invalid", tone === "error");
    input.classList.toggle("has-warning", tone === "warning");
    input.setAttribute("aria-invalid", tone === "error" ? "true" : "false");
    input.title = fieldMessages[0] || "";
  });

  $$("[data-profile-field-message]").forEach((message) => {
    const field = message.dataset.profileFieldMessage;
    const fieldMessages = validation.fieldMessages?.[field] || [];
    message.textContent = fieldMessages[0] || "";
    message.hidden = !fieldMessages.length;
    message.classList.toggle("error", validation.fields?.[field] === "error");
    message.classList.toggle("warning", validation.fields?.[field] === "warning");
  });

  const destinationInput = $("#profile-destination-input");
  if (destinationInput) {
    destinationInput.placeholder = raw.destinationMode === "custom"
      ? "Ej. C:\\Exports\\FlatShot"
      : "Salida";
  }
  const destinationLabel = $("#profile-destination-value-label");
  if (destinationLabel) {
    destinationLabel.textContent = raw.destinationMode === "custom" ? "Carpeta" : "Subcarpeta";
  }
  const destinationPickButton = $("[data-action='pick-output-profile-destination']");
  if (destinationPickButton) {
    destinationPickButton.hidden = raw.destinationMode !== "custom";
    destinationPickButton.disabled = state.bridgeStatus === "checking";
    destinationPickButton.title = raw.destinationMode === "custom"
      ? "Elegir carpeta de salida"
      : "Disponible con carpeta personalizada";
  }
}

function updateOutputProfileFooterState(validation, dirty) {
  const draft = ensureOutputProfileDraft();
  const isPersisted = state.outputProfiles.some((profile) => profile.id === draft.id);
  const footerState = outputProfileViewHelpers.outputProfileFooterState({
    draft,
    dirty,
    isPersisted,
    changeCount: outputProfileChangeCount(),
    noticeText: state.outputProfileNotice,
    profileCount: state.outputProfiles.length,
    validation,
  });
  const deleteButton = $("[data-action='delete-output-profile']");
  if (deleteButton) {
    const deleteConfirmOpen = state.outputDeleteConfirmId === draft.id;
    deleteButton.disabled = footerState.deleteDisabled || deleteConfirmOpen;
    deleteButton.title = deleteConfirmOpen ? "Confirma o cancela la eliminación" : footerState.deleteTitle;
    deleteButton.setAttribute("aria-expanded", deleteConfirmOpen ? "true" : "false");
  }
  $$("[data-output-profile-reset]").forEach((resetButton) => {
    resetButton.disabled = footerState.resetDisabled;
    resetButton.textContent = footerState.resetLabel;
    if (resetButton.closest(".app-settings-footer")) {
      resetButton.dataset.action = "reset-output-profile-draft";
      resetButton.hidden = footerState.resetHidden;
    }
  });
  const saveButton = $("[data-output-profile-save]");
  if (saveButton) {
    saveButton.disabled = footerState.saveDisabled;
    saveButton.hidden = footerState.saveHidden;
    saveButton.textContent = footerState.saveLabel;
    saveButton.dataset.action = "save-output-profile";
  }
  const closeButton = $("[data-output-profile-close]");
  if (closeButton) {
    closeButton.textContent = footerState.closeLabel;
    closeButton.dataset.action = footerState.closeAction;
    closeButton.hidden = footerState.closeHidden;
  }
  const footerNote = $("#output-profile-unsaved");
  if (footerNote) {
    footerNote.textContent = footerState.noteText;
    footerNote.className = footerState.noteClass;
  }
}

function renderOutputProfileDeleteConfirm(profile) {
  const panel = $("#output-delete-confirm");
  if (!panel) {
    return;
  }
  const isOpen = Boolean(profile?.id && state.outputDeleteConfirmId === profile.id);
  panel.hidden = !isOpen;
  panel.setAttribute("aria-hidden", isOpen ? "false" : "true");
  const footer = panel.closest(".app-settings-footer");
  if (footer) {
    footer.classList.toggle("is-confirming-delete", isOpen);
  }

  const detail = $("#output-delete-confirm-detail");
  if (detail) {
    detail.textContent = isOpen
      ? `Se eliminará "${profile.name}" de los formatos guardados. No se tocarán imágenes ni exportaciones anteriores.`
      : "";
  }

  const confirmButton = panel.querySelector("[data-action='confirm-output-delete']");
  if (confirmButton) {
    confirmButton.disabled = !isOpen;
  }
}

function renderAppSettings() {
  const modal = $("#app-settings-modal");
  if (!modal) {
    return;
  }
  modal.classList.toggle("is-hidden", !state.appSettingsOpen);
  modal.setAttribute("aria-hidden", state.appSettingsOpen ? "false" : "true");
  if (!state.appSettingsOpen) {
    return;
  }

  const draft = ensureOutputProfileDraft();
  const rows = outputProfileManagerRows();
  const profileCount = $("#output-profile-count");
  if (profileCount) {
    profileCount.textContent = `${enabledOutputProfiles().length} activos`;
  }
  const draftDirty = outputProfileHasUnsavedChanges();
  $("#output-profile-list").innerHTML = rows.map((profile) => {
    const selected = profile.id === draft?.id;
    const enabled = profile.enabled;
    const unsaved = !state.outputProfiles.some((item) => item.id === profile.id);
    const dirty = selected && draftDirty;
    const canToggle = !unsaved;
    return outputProfileViewHelpers.outputProfileManagerRowHtml({
      profile,
      selected,
      enabled,
      dirty,
      new: unsaved,
      unsaved,
    });
  }).join("");
  setOutputProfileFormValues(draft);
  renderOutputProfileModalState();
}

function presetSummaryLine() {
  return settingsViewHelpers.presetSummaryLine({
    background: state.background,
    format: state.format,
    size: state.size,
  });
}

function destinationCompactLabel() {
  return outputProfileViewHelpers.destinationCompactLabel({
    destinationMode: state.destinationMode,
    destinationValue: state.destinationValue,
  });
}

function namingHumanLabel() {
  return outputProfileViewHelpers.namingHumanLabel({
    naming: state.naming,
    suffix: state.suffix,
  });
}

function outputWarningSummary(issues) {
  return exportPreflightViewHelpers.outputWarningSummaryHtml({
    issues,
    firstIssue: firstActionableIssue(),
    visibleWarningCount: visibleWarningCount(),
  });
}

function issueListHtml() {
  return exportPreflightViewHelpers.issueListHtml({
    hasActiveBatch: hasBatch(),
    batch: state.batch,
    rows: issueRows(),
    counts: preflightCounts(),
    warningCount: visibleWarningCount(),
  });
}

function issueRows() {
  return exportPreflightViewHelpers.issueRows({
    scanOmissions: scanOmissions().map((item) => ({
      ...item,
      reasonLabel: batchViewHelpers.omissionReasonLabel(item.reason),
      severity: omissionSeverity(item),
    })),
    images: activeImages().map((image) => ({
      ...image,
      exportStatus: exportItemState(image)?.status,
    })),
    errors: state.errors,
    statusLabels,
  });
}

function exportStatusClass(ready, issues = preflightIssues()) {
  return exportPreflightViewHelpers.exportStatusClass({
    hasActiveBatch: hasBatch(),
    issues,
    ready,
    status: state.exportStatus,
  });
}

function exportPreflightRows(issues, exportable, ready) {
  return exportPreflightViewHelpers.exportPreflightRows({
    batch: state.batch,
    destinationFallback: destinationFallbackLabel(),
    destinationMissing: state.destinationMode === "custom" && !state.destinationValue.trim(),
    exportable,
    ignoredCount: ignoredOmissions().length,
    ignoredSummary: ignoredSummaryText(),
    issues,
    naming: state.naming,
    namingExample: namingExample(),
    ready,
    warningCount: visibleWarningCount(),
  });
}

function exportPanelStatusLabel(ready, issues = preflightIssues()) {
  return exportPreflightViewHelpers.exportPanelStatusLabel({
    status: state.exportStatus,
    paused: state.paused,
    batch: state.batch,
    hasActiveBatch: hasBatch(),
    ready,
    issues,
  });
}

function exportPreflightSummary(issues, exportable, ready) {
  return exportPreflightViewHelpers.exportPreflightSummary({ issues, exportable, ready });
}

function namingExample() {
  const image = exportableImages()[0] || selectedImage();
  const originalName = image?.name || "imagen_001.png";
  return outputProfileViewHelpers.namingExample({
    folder: activeFolders()[0]?.name || "lote",
    format: state.format,
    naming: state.naming,
    original: originalName.replace(/\.[^.]+$/, ""),
    suffix: state.suffix,
  });
}

function renderExportResult() {
  const target = $("#export-result");
  const resultStatuses = ["running", "completed", "partial", "failed"];
  const shouldShow = resultStatuses.includes(state.exportStatus) || state.exportJobId || state.exportResult;
  if (!shouldShow) {
    target.innerHTML = "";
    return;
  }

  const total = Number(state.exportResult?.total ?? exportableImages().length ?? 0);
  const processed = Number(state.exportResult?.processed ?? state.processed ?? 0);
  const errors = Number(state.exportResult?.errors ?? state.exportIssues.filter((issue) => issue.level === "error").length ?? 0);
  const destinations = state.exportDestinations.length
    ? state.exportDestinations
    : Array.isArray(state.exportResult?.destinations)
      ? state.exportResult.destinations
      : [];
  const issues = state.exportIssues.length ? state.exportIssues : state.errors;
  const items = Array.isArray(state.exportCompletedItems) ? state.exportCompletedItems.slice(-8) : [];
  const title = exportResultTitle();
  const meta = exportResultMeta(processed, total, errors);
  const actionsHtml = exportResultActionsHtml(issues, destinations);

  target.innerHTML = exportResultViewHelpers.exportResultHtml({
    status: state.exportStatus,
    title,
    meta,
    processed,
    total,
    errors,
    destinations,
    destinationFallback: destinationFallbackLabel(),
    currentFileLabel: currentExportFileLabel(),
    issues,
    issueSummary: exportIssueActionText(issues[0]),
    items,
    actionsHtml,
  });
}

function exportResultTitle() {
  return exportResultViewHelpers.exportResultTitle(state.exportStatus, state.paused);
}

function exportResultMeta(processed, total, errors) {
  return exportResultViewHelpers.exportResultMeta({
    status: state.exportStatus,
    processed,
    total,
    errors,
  });
}

function currentExportFileLabel() {
  return exportResultViewHelpers.currentExportFileLabel({
    images: exportableImages(),
    processed: state.processed,
    statusText: state.statusText,
  });
}

function exportIssueActionText(issue) {
  return exportResultViewHelpers.exportIssueActionText(issue, {
    existingOutput: preflightHelpers.issueMentionsExistingOutput(issue),
  });
}

function exportResultActionsHtml(issues, destinations) {
  return exportResultViewHelpers.exportResultActionsHtml({
    status: state.exportStatus,
    issues,
    destinations,
    canOpenOutput: Boolean(outputDestinationToOpen()),
    canRetry: isExportReady(),
  });
}

function destinationFallbackLabel() {
  const profiles = exportOutputProfiles();
  if (!profiles.length) {
    return "Sin formato activo";
  }
  return outputProfileViewHelpers.destinationFallbackLabel({
    destinationMode: state.destinationMode,
    destinationValue: state.destinationValue,
    destinations: profiles.length > 1 ? profiles.map(profileDestinationPreviewLabel) : [],
  });
}

function beginOutputEdit() {
  state.outputDraft = {
    format: state.format,
    size: state.size,
    background: state.background,
    destinationMode: state.destinationMode,
    destinationValue: state.destinationValue,
    naming: state.naming,
    suffix: state.suffix,
  };
  state.outputEditMode = true;
  state.presetEditorOpen = false;
  state.inspectorTab = "output";
  state.statusText = "Editando formato";
  render();
}

function applyOutputEdit() {
  state.outputDraft = null;
  state.outputEditMode = false;
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = "Formato aplicado al lote";
  persistExportPreferences();
  render();
}

function cancelOutputEdit() {
  if (state.outputDraft) {
    Object.assign(state, state.outputDraft);
  }
  state.outputDraft = null;
  state.outputEditMode = false;
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = "Edición cancelada";
  persistExportPreferences();
  render();
}

function saveCurrentOutputProfile() {
  const current = currentOutputProfileData();
  const index = state.outputProfiles.findIndex((profile) => profile.id === state.activeOutputProfileId);
  if (index < 0) {
    state.outputProfiles.push({ ...current, enabled: true });
  } else {
    state.outputProfiles[index] = {
      ...state.outputProfiles[index],
      ...current,
      id: state.activeOutputProfileId,
      name: state.outputProfiles[index].name || current.name,
      enabled: Boolean(state.outputProfiles[index].enabled),
    };
  }
  state.outputProfiles = outputProfileHelpers.normalizeOutputProfileList(state.outputProfiles, state.activeOutputProfileId);
  state.outputDraft = null;
  state.outputEditMode = false;
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = "Formato de salida guardado";
  persistOutputProfiles();
  render();
}

function saveCurrentOutputAsNewProfile() {
  const sourceName = activeOutputProfile()?.name || "Formato";
  const name = window.prompt("Nombre del nuevo formato de salida", `${sourceName} copia`);
  if (name === null) {
    return;
  }
  const profile = outputProfileHelpers.normalizeOutputProfile({
    ...currentOutputProfileData(),
    id: outputProfileHelpers.uniqueOutputProfileId(name || "formato", Date.now()),
    name: name.trim() || "Nuevo formato",
    enabled: true,
  });
  state.outputProfiles = outputProfileHelpers.normalizeOutputProfileList([...state.outputProfiles, profile], profile.id);
  state.activeOutputProfileId = profile.id;
  state.outputProfileEditorId = profile.id;
  state.outputProfileDraft = { ...profile };
  state.outputDraft = null;
  state.outputEditMode = false;
  persistOutputProfiles();
  state.statusText = `Nuevo formato: ${profile.name}`;
  render();
}

function discardOutputOverrides() {
  const profile = activeOutputProfile();
  if (!profile) {
    return;
  }
  state.outputDraft = null;
  state.outputEditMode = false;
  applyOutputProfile(profile.id, { statusText: "Cambios sin guardar descartados" });
}

async function saveCurrentPreset() {
  const presetName = state.activePreset;
  const presetSettings = normalizeSettings(state.settings);

  if (state.bridgeMode === "bridge") {
    state.statusText = "Guardando ajuste";
    render();
    try {
      const payload = await bridgeRequest("/presets/save", {
        method: "POST",
        body: JSON.stringify({
          name: presetName,
          settings: presetSettings,
        }),
        timeoutMs: 8000,
      });
      applyBridgePresets(payload);
    } catch (error) {
      state.presetDirty = true;
      state.statusText = `No se pudo guardar el ajuste: ${bridgeErrorMessage(error)}`;
      render();
      return;
    }
  }

  updatePresetCache(presetName, presetSettings);

  state.presetDirty = false;
  state.presetSource = "Global";
  persistImageAdjustmentSelection();
  state.outputDraft = null;
  state.outputEditMode = false;
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = "Ajuste guardado";
  render();
}

async function saveAdjustmentAsNew(settings, options = {}) {
  const fallbackName = options.defaultName || `${state.activePreset || "Ajuste"} copia`;
  const name = window.prompt("Nombre del nuevo ajuste de imagen", fallbackName);
  if (name === null) {
    return;
  }
  const presetName = name.trim() || "Nuevo ajuste";
  const presetSettings = normalizeSettings(settings);

  if (state.bridgeMode === "bridge") {
    state.statusText = "Guardando nuevo ajuste";
    render();
    try {
      const payload = await bridgeRequest("/presets/save", {
        method: "POST",
        body: JSON.stringify({
          name: presetName,
          settings: presetSettings,
        }),
        timeoutMs: 8000,
      });
      applyBridgePresets(payload);
    } catch (error) {
      state.statusText = `No se pudo guardar el ajuste: ${bridgeErrorMessage(error)}`;
      render();
      return;
    }
  }

  updatePresetCache(presetName, presetSettings);
  state.activePreset = presetName;
  state.settings = presetSettings;
  state.presetDirty = false;
  state.presetSource = "Global";
  state.presetEditorOpen = false;
  persistImageAdjustmentSelection();
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = options.statusText || `Nuevo ajuste: ${presetName}`;
  render();
}

function saveCurrentPresetAsNew() {
  void saveAdjustmentAsNew(state.settings, {
    defaultName: `${state.activePreset || "Ajuste"} copia`,
    statusText: "Ajuste guardado como nuevo",
  });
}

function saveCurrentLocalAdjustmentAsNew() {
  const image = selectedImage();
  if (!image) {
    return;
  }
  void saveAdjustmentAsNew(settingsWithLocalOverride(state.settings, currentImageOverride(image)), {
    defaultName: `${state.activePreset || "Ajuste"} personalizado`,
    statusText: "Ajuste de imagen guardado como nuevo",
  });
}

function presetsExportPayload() {
  const categories = {};
  const uncategorized = {};
  activePresetItems().forEach((preset) => {
    const settings = normalizeSettings(preset.settings);
    const categoryId = preset.categoryId && preset.categoryId !== "uncategorized"
      ? preset.categoryId
      : "";
    if (!categoryId) {
      uncategorized[preset.name] = settings;
      return;
    }
    if (!categories[categoryId]) {
      categories[categoryId] = {
        name: preset.category || categoryId,
        presets: {},
      };
    }
    categories[categoryId].presets[preset.name] = settings;
  });
  return {
    flatshot_export: {
      type: "presets",
      version: 1,
      exported_at: new Date().toISOString(),
      preset_count: activePresetItems().length,
    },
    presets: {
      categories,
      uncategorized,
    },
  };
}

function exportPresetCollection() {
  const payload = presetsExportPayload();
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  const stamp = new Date().toISOString().slice(0, 10).replaceAll("-", "");
  link.href = url;
  link.download = `flatshot-ajustes-${stamp}.json`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
  state.statusText = `${payload.flatshot_export.preset_count} ajustes exportados`;
  render();
}

async function deleteActivePreset() {
  const presets = activePresetItems();
  if (presets.length <= 1) {
    state.statusText = "Debe quedar al menos un ajuste";
    render();
    return;
  }
  const presetName = state.activePreset;
  const nextPreset = presets.find((preset) => preset.name !== presetName)?.name || presets[0]?.name;
  if (!window.confirm(`Eliminar el ajuste "${presetName}"?`)) {
    return;
  }

  if (state.bridgeMode === "bridge") {
    state.statusText = "Eliminando ajuste";
    render();
    try {
      const payload = await bridgeRequest("/presets/delete", {
        method: "POST",
        body: JSON.stringify({ name: presetName }),
        timeoutMs: 8000,
      });
      applyBridgePresets(payload);
      const preferred = payload.activePreset || nextPreset;
      if (preferred) {
        applyPresetSettings(preferred, { refresh: false, statusText: `Ajuste eliminado: ${presetName}` });
      }
    } catch (error) {
      state.statusText = `No se pudo eliminar el ajuste: ${bridgeErrorMessage(error)}`;
      render();
      return;
    }
  } else {
    removePresetFromCache(presetName);
    if (nextPreset) {
      applyPresetSettings(nextPreset, { refresh: false, statusText: `Ajuste eliminado: ${presetName}` });
    }
  }

  state.presetDirty = false;
  state.outputDraft = null;
  state.outputEditMode = false;
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  render();
}

function openPresetEditor() {
  state.presetEditorOpen = true;
  state.outputEditMode = false;
  state.inspectorTab = "advanced";
  state.statusText = "Gestionar ajustes";
  render();
}

function closePresetEditor() {
  state.presetEditorOpen = false;
  state.inspectorTab = "advanced";
  pendingAdvancedDisclosure = "appearance-section";
  state.statusText = "Editar ajuste";
  render();
}

function exportStatusLabel(ready) {
  return settingsViewHelpers.exportStatusLabel({
    exportStatus: state.exportStatus,
    paused: state.paused,
    ready,
  });
}
