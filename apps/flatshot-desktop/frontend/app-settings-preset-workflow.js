function normalizeLightingScene(scene = {}) {
  const source = scene && typeof scene === "object" ? scene : {};
  const sourceMain = source.main && typeof source.main === "object" ? source.main : {};
  const defaultMain = defaultLightingScene.main;
  const type = ["softbox", "spot", "strip"].includes(sourceMain.type) ? sourceMain.type : defaultMain.type;
  return {
    main: {
      type,
      x: numberHelpers.roundedSceneValue(sourceMain.x, -1, 1, defaultMain.x),
      y: numberHelpers.roundedSceneValue(sourceMain.y, -1, 1, defaultMain.y),
      height: numberHelpers.roundedSceneValue(sourceMain.height, 0, 1, defaultMain.height),
      size: numberHelpers.roundedSceneValue(sourceMain.size, 0, 1, defaultMain.size),
      intensity: numberHelpers.roundedSceneValue(sourceMain.intensity, 0, 1.5, defaultMain.intensity),
    },
    ambient_intensity: numberHelpers.roundedSceneValue(source.ambient_intensity, 0, 1, defaultLightingScene.ambient_intensity),
  };
}

function cloneLightingScene(scene = defaultLightingScene) {
  return normalizeLightingScene(scene);
}

function normalizeSettings(settings = {}) {
  const source = settings && typeof settings === "object" ? settings : {};
  const normalized = { ...defaultSettings };
  shadowSettingKeys.forEach((key) => {
    if (source[key] === undefined || source[key] === null) {
      return;
    }
    if (key === "adaptive_zoom" || key === "transparent_bg") {
      normalized[key] = Boolean(source[key]);
      return;
    }
    if (key === "shadow_engine") {
      normalized[key] = ["legacy", "realistic_v2", "studio_2_5d"].includes(source[key]) ? source[key] : "realistic_v2";
      return;
    }
    if (key === "lighting_scene") {
      normalized[key] = normalizeLightingScene(source[key]);
      return;
    }
    if (key === "bg_color") {
      normalized[key] = Array.isArray(source[key]) && source[key].length === 3
        ? source[key].map((channel) => Number(channel))
        : defaultSettings.bg_color;
      return;
    }
    normalized[key] = Number(source[key]);
  });
  normalized.lighting_scene = cloneLightingScene(normalized.lighting_scene);
  return normalized;
}

function presetItemByName(name) {
  return activePresetItems().find((preset) => preset.name === name) || null;
}

function updatePresetCache(name, settings) {
  const normalized = normalizeSettings(settings);
  const bridgeIndex = state.bridgePresets.findIndex((preset) => preset.name === name);
  if (bridgeIndex >= 0) {
    state.bridgePresets[bridgeIndex] = {
      ...state.bridgePresets[bridgeIndex],
      settings: normalized,
    };
  }
  const preset = presetItemByName(name);
  if (preset) {
    preset.settings = normalized;
  }
  if (!mockPresets.includes(name) && state.bridgeMode !== "bridge") {
    mockPresets.push(name);
  }
  mockPresetSettings[name] = normalized;
}

function removePresetFromCache(name) {
  state.bridgePresets = state.bridgePresets.filter((preset) => preset.name !== name);
  const mockIndex = mockPresets.indexOf(name);
  if (mockIndex >= 0) {
    mockPresets.splice(mockIndex, 1);
  }
  delete mockPresetSettings[name];
  delete state.presetOutputSettings[name];
}

function applyPresetSettings(name, options = {}) {
  const preset = presetItemByName(name);
  if (!preset) {
    return false;
  }
  state.activePreset = preset.name;
  state.settings = normalizeSettings(preset.settings);
  state.presetDirty = false;
  state.presetSource = preset.category || "Global";
  persistImageAdjustmentSelection();
  const advanced = $("#advanced-settings");
  if (advanced) {
    advanced.open = false;
  }
  state.statusText = options.statusText || `Ajuste: ${preset.name}`;
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  if (options.refresh !== false) {
    refreshPreviewAfterSettingChange();
  }
  return true;
}

function resetActivePresetSettings() {
  if (applyPresetSettings(state.activePreset, { statusText: "Ajuste restaurado" })) {
    return;
  }
  state.settings = { ...defaultSettings };
  state.presetDirty = false;
  state.presetSource = "Global";
  state.statusText = "Ajuste restaurado";
  refreshPreviewAfterSettingChange();
}

function cancelAdjustmentEdit() {
  const preset = activePresetItem();
  state.settings = normalizeSettings(preset?.settings || defaultSettings);
  state.presetDirty = false;
  state.presetSource = preset?.category || "Global";
  state.presetEditorOpen = false;
  state.statusText = "Cambios de ajuste descartados";
  refreshPreviewAfterSettingChange();
}

function applyGlobalAdjustmentWithoutSaving() {
  state.presetEditorOpen = false;
  state.presetDirty = true;
  state.presetSource = "Modificado";
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = "Ajuste aplicado al lote sin guardar";
  refreshPreviewAfterSettingChange();
}

function markPresetDirty(options = {}) {
  state.presetDirty = true;
  state.presetSource = "Modificado";
  if (options.deferRender) {
    return;
  }
  refreshPreviewAfterSettingChange();
}

function refreshPreviewAfterSettingChange() {
  if (selectedImage()?.source === "bridge") {
    Object.assign(state, previewStateHelpers.previewLoadingState());
    renderAdjustmentResponse();
    clearTimers();
    setTimer(() => {
      const image = selectedImage();
      if (image?.source === "bridge") {
        void requestBridgePreview(image);
      }
    }, 360);
    return;
  }
  if (hasBatch() && state.previewStatus !== "error") {
    Object.assign(state, previewStateHelpers.previewLoadingState({ clearData: false }));
    renderAdjustmentResponse();
    clearTimers();
    setTimer(() => {
      Object.assign(state, previewStateHelpers.previewImageStatusState(selectedImage()?.status, { errorAsReady: true }));
      renderAdjustmentResponse();
    }, 420);
  } else {
    renderAdjustmentResponse();
  }
}
