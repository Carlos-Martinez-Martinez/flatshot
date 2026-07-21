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

function openPresetEditor() {
  enableAdvancedInspectorMode();
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
