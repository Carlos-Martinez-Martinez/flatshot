(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotAppState = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const stateStoreHelpers = globalThis.FlatShotAppStateStores || {};

  function hasBatch(state = {}) {
    return state.batch === "ready" || state.batch === "scanning";
  }

  function isBridgeBatch(state = {}) {
    return state.batchSource === "bridge";
  }

  function isMockBatch(state = {}) {
    return state.batchSource === "mock";
  }

  function activeImages(state = {}, options = {}) {
    if (state.batch !== "ready") {
      return [];
    }
    if (isBridgeBatch(state)) {
      return Array.isArray(state.realImages) ? state.realImages : [];
    }
    return isMockBatch(state) ? options.mockImages || [] : [];
  }

  function activeFolders(state = {}, options = {}) {
    if (state.batch !== "ready") {
      return [];
    }
    if (isBridgeBatch(state)) {
      return Array.isArray(state.realFolders) ? state.realFolders : [];
    }
    return isMockBatch(state) ? options.mockFolders || [] : [];
  }

  function selectedImage(state = {}, options = {}) {
    return activeImages(state, options).find((image) => image.id === state.selectedImageId)
      || (options.mockImages || []).find((image) => image.id === state.selectedImageId)
      || null;
  }

  function activePresetItems(state = {}, options = {}) {
    if (state.bridgeMode === "bridge" && Array.isArray(state.bridgePresets) && state.bridgePresets.length) {
      return state.bridgePresets;
    }
    const normalizeSettings = options.normalizeSettings || ((settings) => settings);
    const mockPresetSettings = options.mockPresetSettings || {};
    return (options.mockPresets || []).map((name) => ({
      name,
      category: options.devMode ? "Demo" : "Ajuste",
      categoryId: options.devMode ? "mock" : "fallback",
      settings: normalizeSettings(mockPresetSettings[name]),
      source: options.devMode ? "demo" : "fallback",
    }));
  }

  function activePresetItem(state = {}, options = {}) {
    return activePresetItems(state, options).find((preset) => preset.name === state.activePreset) || null;
  }

  function exportableImages(images = []) {
    return images.filter((image) => image.exportable);
  }

  function exportItemState(image, completedItems = []) {
    const items = Array.isArray(completedItems) ? completedItems : [];
    if (!items.length || !image?.name) {
      return null;
    }
    const sourceName = image.name.toLowerCase();
    const sourceStem = sourceName.replace(/\.[^.]+$/, "");
    const matches = items.filter((item) => {
      const itemName = String(item.name || "").toLowerCase();
      return itemName === sourceName
        || itemName === sourceStem
        || itemName.startsWith(`${sourceStem}.`)
        || itemName.startsWith(`${sourceStem}_`);
    });
    if (matches.some((item) => item.success === false)) {
      return { status: "error", label: "Error" };
    }
    if (matches.some((item) => item.success === true)) {
      return { status: "exported", label: "Exportada" };
    }
    return null;
  }

  function exportItemStatusMap(images = [], completedItems = []) {
    return new Map(images.map((image) => [image.id, exportItemState(image, completedItems)]));
  }

  function validationIssues(input = {}) {
    const state = input.state || {};
    const issues = [];
    const exportables = Array.isArray(input.exportableImages) ? input.exportableImages : [];
    const exportProfiles = Array.isArray(input.exportOutputProfiles) ? input.exportOutputProfiles : [];
    const outputProfileValidation = input.outputProfileValidation || (() => ({ errors: [] }));
    const outputProfileRawFromProfile = input.outputProfileRawFromProfile || ((profile) => profile);

    if (state.batch === "none") {
      issues.push({ level: "error", title: "Sin lote", detail: "Selecciona una carpeta." });
    }
    if (state.batch === "empty") {
      issues.push({ level: "warning", title: "No hay PNG válidos", detail: "Elige otra carpeta." });
    }
    if (exportables.length === 0 && state.batch === "ready") {
      issues.push({ level: "error", title: "Sin imágenes exportables", detail: "Revisa los errores." });
    }
    if (!String(state.activePreset || "").trim()) {
      issues.push({ level: "error", title: "Sin ajuste de imagen", detail: "Selecciona un ajuste de imagen." });
    }
    if (exportProfiles.length === 0) {
      issues.push({ level: "error", title: "Sin salidas activas", detail: "Selecciona al menos una salida." });
    }
    if (!String(state.naming || "").trim()) {
      issues.push({ level: "error", title: "Nombre de archivo vacío", detail: "Define una plantilla de nombre." });
    }
    if (state.destinationMode === "custom" && !String(state.destinationValue || "").trim()) {
      issues.push({ level: "error", title: "Carpeta de salida sin configurar", detail: "Elige una carpeta de salida." });
    }
    exportProfiles.forEach((profile) => {
      outputProfileValidation(outputProfileRawFromProfile(profile)).errors.forEach((message) => {
        issues.push({
          level: "error",
          title: "Salida incompleta",
          detail: `${profile.name}: ${message}`,
        });
      });
    });
    return issues;
  }

  function imageDimensions(image) {
    const width = Number(image?.width || image?.naturalWidth || image?.sourceWidth || 0);
    const height = Number(image?.height || image?.naturalHeight || image?.sourceHeight || 0);
    if (width > 0 && height > 0) {
      return { width, height };
    }
    const detail = String(image?.detail || "");
    const match = /(\d{2,5})\s*[x×]\s*(\d{2,5})/i.exec(detail);
    if (!match) {
      return null;
    }
    return {
      width: Number.parseInt(match[1], 10),
      height: Number.parseInt(match[2], 10),
    };
  }

  function lowResolutionImageCount(input = {}) {
    const images = Array.isArray(input.images) ? input.images : [];
    const targets = Array.isArray(input.targets) ? input.targets : [];
    return images.filter((image) => {
      const dimensions = imageDimensions(image);
      return dimensions && targets.some((target) => dimensions.width < target.width || dimensions.height < target.height);
    }).length;
  }

  function uiState(input = {}) {
    const state = input.state || {};
    const counts = input.counts || {};
    const lotCounts = input.lotCounts || {};
    const batchPresent = Boolean(input.hasBatch);
    return {
      hasBatch: batchPresent,
      hasBatchContext: batchPresent || state.batch === "empty" || state.batch === "scanning",
      hasSelectedImage: Boolean(input.selectedImage),
      isBridgeReady: state.bridgeMode === "bridge" && state.bridgeStatus === "connected",
      canExport: Boolean(input.canExport),
      hasWarnings: Number(lotCounts.nonBlockingWarnings || 0) > 0 || Number(counts.warnings || 0) > 0,
      hasBlockingErrors: Number(lotCounts.blockingErrors || 0) > 0,
      isProcessing: state.batch === "scanning" || state.previewStatus === "loading" || state.exportStatus === "running",
      isExporting: state.exportStatus === "running",
    };
  }

  function stateStoreSnapshot(state = {}) {
    if (typeof stateStoreHelpers.stateStoreSnapshot === "function") {
      return stateStoreHelpers.stateStoreSnapshot(state);
    }
    return { app: { ...state } };
  }

  function stateStoreFields(name) {
    return typeof stateStoreHelpers.stateStoreFields === "function"
      ? stateStoreHelpers.stateStoreFields(name)
      : [];
  }

  function storeNames() {
    return typeof stateStoreHelpers.storeNames === "function"
      ? stateStoreHelpers.storeNames()
      : ["app"];
  }

  return {
    activeFolders,
    activeImages,
    activePresetItem,
    activePresetItems,
    exportableImages,
    exportItemState,
    exportItemStatusMap,
    hasBatch,
    imageDimensions,
    isBridgeBatch,
    isMockBatch,
    lowResolutionImageCount,
    selectedImage,
    stateStoreFields,
    stateStoreSnapshot,
    storeNames,
    uiState,
    validationIssues,
  };
});
