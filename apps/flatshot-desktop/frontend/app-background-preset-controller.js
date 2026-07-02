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
  const editButton = $("[data-action='edit-background-preset']");
  const deleteButton = $("[data-action='delete-background-preset']");
  const selectedIsSystemPreset = backgroundPresetHelpers.isSystemBackgroundPreset(selectedPreset, backgroundPresetOptions());
  if (editButton) {
    editButton.disabled = !selectedPreset || selectedIsSystemPreset;
    editButton.title = !selectedPreset
      ? "Este fondo no está guardado como preset"
      : selectedIsSystemPreset
        ? "Los fondos del sistema no se editan. Usa Nuevo para crear una variante."
        : "Editar fondo";
  }
  if (deleteButton) {
    deleteButton.disabled = !selectedPreset || selectedIsSystemPreset;
    deleteButton.title = !selectedPreset
      ? "Este fondo no está guardado como preset"
      : selectedIsSystemPreset
        ? "Los fondos del sistema no se eliminan."
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
  if (preset && backgroundPresetHelpers.isSystemBackgroundPreset(preset, backgroundPresetOptions())) {
    state.backgroundPresetEditor = null;
    state.statusText = "Los fondos del sistema no se editan. Usa Nuevo para crear una variante.";
    renderOutputProfileModalState();
    return;
  }
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
  const editingSystemPreset = backgroundPresetHelpers.isSystemBackgroundPreset({ id: editor.id }, backgroundPresetOptions());
  const savedPresetId = editingSystemPreset ? outputProfileHelpers.uniqueOutputProfileId(name || "fondo", Date.now()) : editor.id;
  const savedPreset = backgroundPresetHelpers.normalizeBackgroundPreset({
    id: savedPresetId,
    kind: editor.kind,
    name,
    rgb: editor.kind === "transparent" ? [230, 230, 230] : outputProfileHelpers.parseRgbBackground(rgb),
  }, 0, backgroundPresetOptions());
  const previousValue = editor.mode === "edit" && !editingSystemPreset ? editor.sourceValue : "";
  const index = editingSystemPreset ? -1 : state.backgroundPresets.findIndex((preset) => preset.id === editor.id);
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
  if (!preset) {
    return;
  }
  if (backgroundPresetHelpers.isSystemBackgroundPreset(preset, backgroundPresetOptions())) {
    state.statusText = "Los fondos del sistema no se eliminan.";
    renderOutputProfileModalState();
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
