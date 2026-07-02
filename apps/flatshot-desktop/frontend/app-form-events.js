function handleImageSearchInput(event) {
  state.search = event.target.value;
  if (ensureGallerySelectionForFilter()) {
    return;
  }
  render();
}

function handleSettingInput(event) {
  const key = event.target.dataset.setting;
  const nextValue = settingInputValue(event.target);
  if (state.settings[key] === nextValue) {
    return;
  }
  state.settings[key] = nextValue;
  markPresetDirty();
}

function handleLightingFieldInput(event) {
  updateLightingSceneField(event.target.dataset.lightingField, event.target.value);
}

function handleLightingNumberFieldInput(event) {
  if (event.type !== "change") {
    return;
  }
  updateLightingNumberFieldFromInput(event.target, { commit: true });
}

function handleLightingPresetClick(button) {
  const presetId = button.dataset.lightingPreset;
  const preset = lightingScenePresets[presetId];
  if (!preset) {
    return;
  }
  state.settings.shadow_engine = "studio_2_5d";
  state.settings.lighting_scene = cloneLightingScene(preset);
  state.lightingPresetId = presetId;
  markPresetDirty();
}

function settingInputValue(input) {
  if (input.type === "checkbox") {
    return input.checked;
  }
  if (input.tagName === "SELECT") {
    return input.value;
  }
  return Number(input.value);
}

function updateLightingSceneField(field, rawValue) {
  const scene = cloneLightingScene(state.settings.lighting_scene);
  if (field === "main.type") {
    scene.main.type = ["softbox", "spot", "strip"].includes(rawValue) ? rawValue : scene.main.type;
  } else if (field === "main.height") {
    scene.main.height = numberHelpers.roundedSceneValue(Number(rawValue) / 100, 0, 1, scene.main.height);
  } else if (field === "main.size") {
    scene.main.size = numberHelpers.roundedSceneValue(Number(rawValue) / 100, 0, 1, scene.main.size);
  } else if (field === "main.intensity") {
    scene.main.intensity = numberHelpers.roundedSceneValue(Number(rawValue) / 100, 0, 1.5, scene.main.intensity);
  } else if (field === "ambient_intensity") {
    scene.ambient_intensity = numberHelpers.roundedSceneValue(Number(rawValue) / 100, 0, 1, scene.ambient_intensity);
  } else {
    return false;
  }
  if (lightingScenesEqual(scene, state.settings.lighting_scene)) {
    return false;
  }
  state.settings.lighting_scene = scene;
  markPresetDirty();
  return true;
}

function updateLightingScenePosition(clientX, clientY, options = {}) {
  const stage = $("#lighting-stage");
  if (!stage || state.settings.shadow_engine !== "studio_2_5d") {
    return false;
  }
  const rect = stage.getBoundingClientRect();
  if (!rect.width || !rect.height) {
    return false;
  }
  const x = numberHelpers.roundedSceneValue(((clientX - rect.left) / rect.width) * 2 - 1, -1, 1, defaultLightingScene.main.x);
  const y = numberHelpers.roundedSceneValue(((clientY - rect.top) / rect.height) * 2 - 1, -1, 1, defaultLightingScene.main.y);
  const scene = cloneLightingScene(state.settings.lighting_scene);
  if (scene.main.x === x && scene.main.y === y) {
    return false;
  }
  scene.main.x = x;
  scene.main.y = y;
  state.settings.lighting_scene = scene;
  markPresetDirty({ deferRender: options.deferRender });
  if (options.deferRender) {
    renderLightingSceneControls();
  }
  return true;
}

function numberInputBound(input, name, fallback) {
  const raw = input?.[name];
  if (raw === "" || raw === null || raw === undefined) {
    return fallback;
  }
  const numeric = Number(raw);
  return Number.isFinite(numeric) ? numeric : fallback;
}

function numericInputValue(input, fallback = 0) {
  return numberHelpers.parseIntegerInput(input?.value, {
    fallback,
    min: numberInputBound(input, "min", -Infinity),
    max: numberInputBound(input, "max", Infinity),
  });
}

function currentSettingNumberValue(key) {
  return Number(state.settings?.[key] ?? 0);
}

function currentLocalNumberValue(key) {
  return clampLocalOverrideValue(key, currentImageOverride()[key] ?? 0);
}

function currentLightingNumberValue(field) {
  if (typeof lightingSliderValue === "function" && typeof lightingSceneFieldValue === "function") {
    return lightingSliderValue(field, lightingSceneFieldValue(state.settings.lighting_scene, field));
  }
  const scene = state.settings?.lighting_scene || {};
  const sceneValue = field === "ambient_intensity"
    ? scene.ambient_intensity
    : field?.startsWith?.("main.")
      ? scene.main?.[field.slice(5)]
      : 0;
  const max = field === "main.intensity" ? 1.5 : 1;
  return Math.round(numberHelpers.clampNumber(sceneValue, 0, max, 0) * 100);
}

function committedNumericControlValue(input) {
  if (input?.dataset?.settingNumber) {
    return currentSettingNumberValue(input.dataset.settingNumber);
  }
  if (input?.dataset?.localSettingNumber) {
    return currentLocalNumberValue(input.dataset.localSettingNumber);
  }
  if (input?.dataset?.lightingNumberField) {
    return currentLightingNumberValue(input.dataset.lightingNumberField);
  }
  return undefined;
}

function isNumericControlInput(input) {
  return Boolean(
    input?.dataset?.settingNumber
    || input?.dataset?.localSettingNumber
    || input?.dataset?.lightingNumberField
  );
}

function cancelNumericControlInput(input) {
  if (!isNumericControlInput(input)) {
    return false;
  }
  const value = committedNumericControlValue(input);
  if (value === undefined) {
    return false;
  }
  input.value = String(value);
  return true;
}

function commitNumericControlInput(input, options = {}) {
  if (!isNumericControlInput(input) || input.disabled) {
    return false;
  }
  const commitOptions = { ...options, commit: true };
  if (input.dataset.settingNumber) {
    return updateSettingFromNumberInput(input, commitOptions);
  }
  if (input.dataset.localSettingNumber) {
    return updateLocalOverrideFromNumberInput(input, commitOptions);
  }
  if (input.dataset.lightingNumberField) {
    return updateLightingNumberFieldFromInput(input, commitOptions);
  }
  return false;
}

function updateSettingFromNumberInput(input, options = {}) {
  const key = input?.dataset?.settingNumber;
  if (!key || !(key in state.settings)) {
    return false;
  }
  const fallback = currentSettingNumberValue(key);
  const parsed = numericInputValue(input, fallback);
  if (!parsed.valid) {
    if (options.commit) {
      input.value = String(fallback);
    }
    return false;
  }
  if (options.commit) {
    input.value = String(parsed.value);
  }
  if (state.settings[key] === parsed.value) {
    return true;
  }
  state.settings[key] = parsed.value;
  const range = $(`[data-setting="${key}"]`);
  if (range && range.type === "range") {
    range.value = parsed.value;
    syncRangeFill(range);
  }
  markPresetDirty();
  return true;
}

function updateLocalOverrideFromNumberInput(input, options = {}) {
  const key = input?.dataset?.localSettingNumber;
  if (!key || !localOverrideKeys.includes(key)) {
    return false;
  }
  const fallback = currentLocalNumberValue(key);
  const parsed = numericInputValue(input, fallback);
  if (!parsed.valid) {
    if (options.commit) {
      input.value = String(fallback);
    }
    return false;
  }
  const value = clampLocalOverrideValue(key, parsed.value);
  if (options.commit) {
    input.value = String(value);
  }
  const range = $(`[data-local-setting="${key}"]`);
  if (range) {
    range.value = value;
    syncRangeFill(range);
  }
  if (fallback === value) {
    return true;
  }
  setCurrentImageOverrideValue(key, value);
  return true;
}

function updateLightingNumberFieldFromInput(input, options = {}) {
  const field = input?.dataset?.lightingNumberField;
  if (!field || input.disabled) {
    return false;
  }
  const fallback = currentLightingNumberValue(field);
  const parsed = numericInputValue(input, fallback);
  if (!parsed.valid) {
    if (options.commit) {
      input.value = String(fallback);
    }
    return false;
  }
  if (options.commit) {
    input.value = String(parsed.value);
  }
  return updateLightingSceneField(field, parsed.value);
}

function handleFormatSelectChange(event) {
  state.format = outputProfileHelpers.normalizeExportFormat(event.target.value);
  if (state.format !== "JPG") {
    state.maxFileSizeKb = null;
  }
  state.statusText = `Formato: ${state.format}`;
  persistExportPreferences();
  render();
}

function handleOutputProfileSelectChange(event) {
  if (event.target.value === "__custom") {
    return;
  }
  applyOutputProfile(event.target.value);
}

function handleSizeSelectInput(event) {
  state.size = event.target.value;
}

function handleSizeSelectChange(event) {
  state.size = outputProfileHelpers.parseOutputSize(event.target.value).normalized;
  state.statusText = `Tamaño: ${state.size}`;
  persistExportPreferences();
  const image = selectedImage();
  if (image?.source === "bridge") {
    void requestBridgePreview(image);
    return;
  }
  render();
}

function handleBackgroundSelectChange(event) {
  state.background = outputProfileHelpers.normalizeBackgroundValue(event.target.value, state.background);
  state.statusText = `Fondo: ${settingsViewHelpers.backgroundLabel(state.background)}`;
  persistExportPreferences();
  const image = selectedImage();
  if (image?.source === "bridge") {
    void requestBridgePreview(image);
    return;
  }
  render();
}

function handleDestinationModeChange(event) {
  state.destinationMode = event.target.value;
  state.destinationValue = state.destinationMode === "custom" ? "" : "Salida";
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = state.destinationMode === "custom" ? "Carpeta de salida sin configurar" : "Destino junto al origen";
  persistExportPreferences();
  render();
}

function handleDestinationInput(event) {
  state.destinationValue = event.target.value;
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = state.destinationValue.trim() ? "Carpeta de salida configurada" : "Carpeta de salida sin configurar";
  persistExportPreferences();
  render();
}

function handleNamingInput(event) {
  state.naming = event.target.value;
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = state.naming.trim() ? "Nombre de archivo actualizado" : "Nombre de archivo vacío";
  persistExportPreferences();
  render();
}
