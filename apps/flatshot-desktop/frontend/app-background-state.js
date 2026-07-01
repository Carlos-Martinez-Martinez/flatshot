function backgroundHelperOptions(extra = {}) {
  return {
    outputProfileHelpers,
    softBlackPreviewBg: SOFT_BLACK_PREVIEW_BG,
    ...extra,
  };
}

function backgroundPresetOptions(extra = {}) {
  return backgroundHelperOptions({
    defaultPresets: defaultBackgroundPresets,
    ...extra,
  });
}

function previewCustomBackgroundValue() {
  const fallback = backgroundPresetHelpers.previewCustomRgbChannels(state.previewBg, backgroundHelperOptions());
  const channels = ["r", "g", "b"].map((channel, index) => {
    const input = $(`[data-preview-bg-channel="${channel}"]`);
    return input?.value ?? fallback[index];
  });
  return backgroundPresetHelpers.previewCustomBackgroundValue(channels, {
    clampNumber: numberHelpers.clampNumber,
    fallback,
  });
}

function persistBackgroundPresets() {
  storageHelpers.writeJson(window.localStorage, STORAGE_KEYS.backgroundPresets, state.backgroundPresets);
  scheduleBridgeUiPreferencesSave();
}

function backgroundPresetById(presetId) {
  return state.backgroundPresets.find((preset) => preset.id === presetId) || null;
}

function backgroundPresetByValue(value) {
  return backgroundPresetHelpers.backgroundPresetByValue(value, state.backgroundPresets, { outputProfileHelpers });
}

function backgroundSelectOptionsHtml(selectedValue) {
  return backgroundPresetHelpers.backgroundSelectOptionsHtml(selectedValue, {
    backgroundLabel: settingsViewHelpers.backgroundLabel,
    escapeHtml,
    outputProfileHelpers,
    presets: state.backgroundPresets,
  });
}
