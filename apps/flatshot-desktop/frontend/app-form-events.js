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
  updateLightingSceneField(event.target.dataset.lightingNumberField, event.target.value);
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
    return;
  }
  if (lightingScenesEqual(scene, state.settings.lighting_scene)) {
    return;
  }
  state.settings.lighting_scene = scene;
  markPresetDirty();
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

function numericInputValue(input, fallback = 0) {
  const raw = String(input.value ?? "").trim();
  if (!raw || raw === "-" || raw === "+") {
    return { valid: false, value: fallback };
  }
  const parsed = Number(raw);
  if (!Number.isFinite(parsed)) {
    return { valid: false, value: fallback };
  }
  const min = input.min === "" ? -Infinity : Number(input.min);
  const max = input.max === "" ? Infinity : Number(input.max);
  const rounded = Math.round(parsed);
  return {
    valid: true,
    value: Math.max(min, Math.min(max, rounded)),
  };
}

function updateSettingFromNumberInput(input, options = {}) {
  const key = input?.dataset?.settingNumber;
  if (!key || !(key in state.settings)) {
    return;
  }
  const parsed = numericInputValue(input, state.settings[key]);
  if (!parsed.valid) {
    return;
  }
  if (options.commit) {
    input.value = parsed.value;
  }
  if (state.settings[key] === parsed.value) {
    return;
  }
  state.settings[key] = parsed.value;
  const range = $(`[data-setting="${key}"]`);
  if (range && range.type === "range") {
    range.value = parsed.value;
    syncRangeFill(range);
  }
  markPresetDirty();
}

function updateLocalOverrideFromNumberInput(input, options = {}) {
  const key = input?.dataset?.localSettingNumber;
  if (!key || !localOverrideKeys.includes(key)) {
    return;
  }
  const parsed = numericInputValue(input, currentImageOverride()[key] || 0);
  if (!parsed.valid) {
    return;
  }
  const value = clampLocalOverrideValue(key, parsed.value);
  if (options.commit) {
    input.value = value;
  }
  const range = $(`[data-local-setting="${key}"]`);
  if (range) {
    range.value = value;
    syncRangeFill(range);
  }
  setCurrentImageOverrideValue(key, value);
}

function handleFormatSelectChange(event) {
  state.format = outputProfileHelpers.normalizeExportFormat(event.target.value);
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
  state.previewBg = state.background;
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
