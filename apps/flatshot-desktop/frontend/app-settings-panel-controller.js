function renderSettings() {
  renderReviewPanel();
  const settingsPanel = $(".settings-panel");
  if (settingsPanel) {
    settingsPanel.dataset.shadowEngine = state.settings.shadow_engine || "";
  }
  const activePreset = $("#active-preset");
  if (activePreset) {
    activePreset.textContent = state.activePreset;
  }
  $("#preset-source").textContent = `${state.activePreset} · ${presetSourceLabel()}`;
  $("#preset-dirty").textContent = settingsViewHelpers.presetDirtyLabel(state.presetDirty);
  $("#preset-dirty").classList.toggle("dirty", state.presetDirty);
  const presetItems = activePresetItems();
  const presetCount = $("#preset-count");
  if (presetCount) {
    presetCount.textContent = `${presetItems.length}`;
  }
  $("#preset-list").innerHTML = settingsViewHelpers.presetListHtml(presetItems, state.activePreset);

  Object.entries(state.settings).forEach(([key, value]) => {
    const input = $(`[data-setting="${key}"]`);
    const output = $(`#${key}-output`);
    const numberInput = $(`[data-setting-number="${key}"]`);
    if (input) {
      if (input.type === "checkbox") {
        input.checked = Boolean(value);
      } else {
        input.value = value;
        syncRangeFill(input);
      }
    }
    if (output) {
      output.textContent = value;
    }
    if (numberInput && document.activeElement !== numberInput) {
      numberInput.value = value;
    }
  });

  const image = selectedImage();
  const localOverride = currentImageOverride(image);
  const localActive = hasImageAdjustmentOverride(image);
  $("#local-adjustment").classList.toggle("active", localActive);
  $("#local-adjustment-text").textContent = settingsViewHelpers.localAdjustmentText(localActive);
  localOverrideKeys.forEach((key) => {
    const value = Number(localOverride[key] || 0);
    const input = $(`[data-local-setting="${key}"]`);
    const output = $(`#local-${key}-output`);
    const numberInput = $(`[data-local-setting-number="${key}"]`);
    if (input) {
      input.value = value;
      syncRangeFill(input);
    }
    if (output) {
      output.textContent = settingsViewHelpers.localSettingOutputText(value);
    }
    if (numberInput && document.activeElement !== numberInput) {
      numberInput.value = value;
    }
  });
  const savePresetButton = $("#save-preset");
  const savePresetState = settingsViewHelpers.savePresetButtonState(state.presetDirty);
  savePresetButton.disabled = savePresetState.disabled;
  savePresetButton.title = savePresetState.title;
  savePresetButton.textContent = savePresetState.text;
  savePresetButton.classList.toggle("primary", savePresetState.primary);
  const deletePresetButton = $("#delete-preset");
  if (deletePresetButton) {
    const deletePresetState = settingsViewHelpers.deletePresetButtonState(presetItems.length);
    deletePresetButton.disabled = deletePresetState.disabled;
    deletePresetButton.title = deletePresetState.title;
  }
  const advanced = $("#advanced-settings");
  const advancedSummaryTitle = advanced?.querySelector("summary strong");
  if (advancedSummaryTitle) {
    advancedSummaryTitle.textContent = settingsViewHelpers.advancedSummaryTitle(advancedDirtyCount());
  }
  renderLightingSceneControls();
}

function lightingSceneFieldValue(scene, field) {
  if (field === "ambient_intensity") {
    return scene.ambient_intensity;
  }
  if (field.startsWith("main.")) {
    return scene.main[field.slice(5)];
  }
  return undefined;
}

function lightingOutputId(field) {
  const names = {
    "main.height": "lighting-height-output",
    "main.size": "lighting-size-output",
    "main.intensity": "lighting-intensity-output",
    ambient_intensity: "lighting-ambient-output",
  };
  return names[field] || "";
}

function lightingSliderValue(field, value) {
  if (field === "main.intensity") {
    return Math.round(numberHelpers.clampNumber(value, 0, 1.5, defaultLightingScene.main.intensity) * 100);
  }
  return Math.round(numberHelpers.clampNumber(value, 0, 1, 0) * 100);
}

function renderLightingSceneControls() {
  const panel = $("#studio-lighting-panel");
  if (!panel) {
    return;
  }
  const enabled = state.settings.shadow_engine === "studio_2_5d";
  panel.hidden = !enabled;
  const scene = normalizeLightingScene(state.settings.lighting_scene);
  state.settings.lighting_scene = scene;
  const exactPresetId = lightingScenePresetId(scene);
  const rememberedPresetId = lightingScenePresets[state.lightingPresetId] ? state.lightingPresetId : "";
  const selectedPresetId = enabled ? exactPresetId || rememberedPresetId || "overhead_soft" : "";

  $$("[data-lighting-field]").forEach((input) => {
    const field = input.dataset.lightingField;
    const value = lightingSceneFieldValue(scene, field);
    if (input.tagName === "SELECT") {
      input.value = value;
    } else {
      const sliderValue = lightingSliderValue(field, value);
      input.value = sliderValue;
      syncRangeFill(input);
      const output = $(`#${lightingOutputId(field)}`);
      if (output) {
        if ("value" in output && document.activeElement !== output) {
          output.value = String(sliderValue);
        } else {
          output.textContent = String(sliderValue);
        }
      }
    }
    input.disabled = !enabled;
  });

  $$("[data-lighting-number-field]").forEach((input) => {
    const field = input.dataset.lightingNumberField;
    const value = lightingSliderValue(field, lightingSceneFieldValue(scene, field));
    if (document.activeElement !== input) {
      input.value = String(value);
    }
    input.disabled = !enabled;
  });

  $$("[data-lighting-preset]").forEach((button) => {
    const presetId = button.dataset.lightingPreset;
    const preset = lightingScenePresets[presetId];
    const selected = enabled && presetId === selectedPresetId;
    const exact = selected && lightingScenesEqual(scene, preset);
    button.disabled = !enabled;
    button.classList.toggle("active", selected);
    button.classList.toggle("is-modified", selected && !exact);
    button.setAttribute("aria-pressed", String(selected));
    button.title = selected && !exact ? "Preset modificado" : "";
  });

  const stage = $("#lighting-stage");
  const handle = $("#lighting-handle");
  if (stage) {
    stage.disabled = !enabled;
  }
  if (handle) {
    const left = ((scene.main.x + 1) / 2) * 100;
    const top = ((scene.main.y + 1) / 2) * 100;
    handle.style.left = `${left}%`;
    handle.style.top = `${top}%`;
  }
}

function lightingScenesEqual(first, second) {
  if (!second) {
    return false;
  }
  return JSON.stringify(normalizeLightingScene(first)) === JSON.stringify(normalizeLightingScene(second));
}

function lightingScenePresetId(scene) {
  return Object.entries(lightingScenePresets)
    .find(([, preset]) => lightingScenesEqual(scene, preset))?.[0] || "";
}
