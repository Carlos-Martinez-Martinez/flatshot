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
  const storedValue = $("#preview-bg-custom-value")?.value || "";
  if (outputProfileHelpers.parseRgbBackground(storedValue)) {
    return backgroundPresetHelpers.normalizePreviewBackgroundValue(storedValue, backgroundHelperOptions());
  }
  const pickerValue = $("[data-preview-bg-picker]")?.value || "";
  if (pickerValue) {
    const pickerChannels = backgroundPresetHelpers.rgbChannelsFromHex(pickerValue, fallback);
    return backgroundPresetHelpers.previewCustomBackgroundValue(pickerChannels, {
      clampNumber: numberHelpers.clampNumber,
      fallback,
    });
  }
  const channels = ["r", "g", "b"].map((channel, index) => {
    const input = $(`[data-preview-bg-channel="${channel}"]`);
    return input?.value ?? fallback[index];
  });
  return backgroundPresetHelpers.previewCustomBackgroundValue(channels, {
    clampNumber: numberHelpers.clampNumber,
    fallback,
  });
}

function applyPreviewBackgroundValue(value) {
  state.previewBg = backgroundPresetHelpers.normalizePreviewBackgroundValue(value, backgroundHelperOptions());
  state.statusText = `Fondo: ${backgroundPresetHelpers.previewBackgroundLabel(state.previewBg, {
    ...backgroundHelperOptions(),
    backgroundLabel: settingsViewHelpers.backgroundLabel,
  })}`;
}

function applyPreviewBackgroundPickerChange(source = null) {
  const control = source?.closest?.(".rgb-visual-control") || $(".viewer-bg-custom-fields");
  const synced = syncRgbVisualControlToTarget(control, source);
  applyPreviewBackgroundValue(synced || previewCustomBackgroundValue());
}

function persistBackgroundPresets() {
  storageHelpers.writeJson(
    window.localStorage,
    STORAGE_KEYS.backgroundPresets,
    backgroundPresetHelpers.backgroundPresetsForStorage(state.backgroundPresets, backgroundPresetOptions())
  );
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
