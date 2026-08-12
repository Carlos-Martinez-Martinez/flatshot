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
  if (!dirty) {
    state.outputProfileCloseConfirmOpen = false;
  }
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
  renderOutputProfileCloseConfirm(dirty);
}

function renderOutputProfileCloseConfirm(dirty) {
  const panel = $("#output-close-confirm");
  if (!panel) {
    return;
  }
  const isOpen = Boolean(dirty && state.outputProfileCloseConfirmOpen);
  panel.hidden = !isOpen;
  panel.setAttribute("aria-hidden", isOpen ? "false" : "true");
  panel.closest(".app-settings-footer")?.classList.toggle("is-confirming-close", isOpen);
}

function updateOutputProfileFieldStates(validation, raw) {
  const fieldIds = {
    name: "profile-name-input",
    format: "profile-format-input",
    background: "profile-background-input",
    backgroundCustom: "profile-background-custom-input",
    width: "profile-width-input",
    height: "profile-height-input",
    maxFileSizeKb: "profile-max-file-size-input",
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
      ? `Se eliminará "${profile.name}" de las salidas guardadas. No se tocarán imágenes ni exportaciones anteriores.`
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
  syncModalVisibility(modal, state.appSettingsOpen);
  if (!state.appSettingsOpen) {
    return;
  }

  const draft = ensureOutputProfileDraft();
  const rows = outputProfileManagerRows();
  const profileCount = $("#output-profile-count");
  if (profileCount) {
    profileCount.textContent = `${enabledOutputProfiles().length} activos`;
  }
  setOutputProfileFormValues(draft);
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
  renderOutputProfileModalState();
}
