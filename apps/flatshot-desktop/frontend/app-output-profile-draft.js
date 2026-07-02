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
    ["profile-max-file-size-input", profile.maxFileSizeKb || ""],
  ];
  pairs.forEach(([id, value]) => {
    const input = $(`#${id}`);
    if (input && input.value !== String(value ?? "")) {
      input.value = value ?? "";
    }
  });
  syncJpgSizeLimitVisibility();
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
    maxFileSizeKb: value("profile-max-file-size-input", current.maxFileSizeKb || ""),
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
    maxFileSizeKb: profile.maxFileSizeKb || "",
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
    maxFileSizeKb: raw.maxFileSizeKb,
  });
}

function updateOutputProfileDraftFromForm() {
  if (!state.appSettingsOpen) {
    return;
  }
  state.outputProfileNotice = "";
  syncTransparentBackgroundFormat();
  syncOutputProfileDestinationMode();
  syncJpgSizeLimitVisibility();
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

function syncJpgSizeLimitVisibility() {
  const sizeLimitField = $("#profile-max-file-size-field");
  const sizeLimitInput = $("#profile-max-file-size-input");
  const formatInput = $("#profile-format-input");
  if (!sizeLimitField || !sizeLimitInput || !formatInput) {
    return;
  }
  sizeLimitField.hidden = outputProfileHelpers.normalizeExportFormat(formatInput.value) !== "JPG";
  if (sizeLimitField.hidden) {
    sizeLimitInput.value = "";
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
