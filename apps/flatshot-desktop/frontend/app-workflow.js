function setScenario(scenario) {
  clearTimers();
  thumbnailPreloads.clear();
  thumbnailFallbackQueue.length = 0;
  thumbnailFallbackInFlight.clear();
  clearBridgeExportPoll();
  Object.assign(state, {
    scenario,
    batch: "ready",
    batchSource: "mock",
    selectedImageId: "img-001",
    previewStatus: "ready",
    previewData: null,
    previewError: "",
    thumbnailStatus: {},
    thumbnailErrors: [],
    exportStatus: "ready",
    exportJobId: null,
    exportDestinations: [],
    exportMessages: [],
    exportCompletedItems: [],
    exportIssues: [],
    exportResult: null,
    destinationMode: "source",
    destinationValue: "Salida",
    progress: 0,
    processed: 0,
    errors: [],
    filter: "all",
    search: "",
    fitMode: DEFAULT_VIEW_MODE,
    fitZoom: 100,
    zoom: 100,
    panX: 0,
    panY: 0,
    inspectorTab: "review",
    outputEditMode: false,
    presetEditorOpen: false,
    exportConfirmOpen: false,
    exportConfirmRisks: [],
    exportConfirmOptions: null,
    scanIssues: [],
    scanDiagnostics: mockScanDiagnostics(),
    paused: false,
    statusText: "Listo para exportar",
    scanStatus: "Escenario mock activo",
  });

  if (scenario === "initial") {
    Object.assign(state, {
      batch: "none",
      batchSource: "none",
      selectedImageId: null,
      previewStatus: "empty",
      exportStatus: "blocked",
      statusText: "Sin lote",
      scanStatus: "Sin lote",
      scanDiagnostics: emptyScanDiagnostics(),
    });
  } else if (scenario === "empty-folder") {
    Object.assign(state, {
      batch: "empty",
      batchSource: "mock",
      selectedImageId: null,
      previewStatus: "empty",
      exportStatus: "blocked",
      statusText: "No hay PNG válidos",
      scanStatus: "Carpeta mock vacía",
      scanDiagnostics: emptyScanDiagnostics(),
    });
  } else if (scenario === "preview-loading") {
    Object.assign(state, {
      previewStatus: "loading",
      exportStatus: "ready",
      statusText: "Generando vista",
    });
  } else if (scenario === "preview-warning") {
    Object.assign(state, {
      selectedImageId: "img-003",
      previewStatus: "warning",
      exportStatus: "ready",
      statusText: "Vista con aviso",
    });
  } else if (scenario === "preview-error") {
    Object.assign(state, {
      selectedImageId: "img-004",
      previewStatus: "error",
      exportStatus: "blocked",
      statusText: "Vista no disponible",
    });
  } else if (scenario === "export-blocked") {
    Object.assign(state, {
      destinationMode: "custom",
      destinationValue: "",
      exportStatus: "blocked",
      statusText: "Carpeta de salida sin configurar",
    });
  } else if (scenario === "export-running") {
    Object.assign(state, {
      exportStatus: "running",
      progress: 42,
      processed: 2,
      statusText: `Procesando 2/${exportableImages().length}`,
    });
    render();
    return;
  } else if (scenario === "export-completed") {
    Object.assign(state, {
      exportStatus: "completed",
      progress: 100,
      processed: exportableImages().length,
      exportCompletedItems: exportableImages().map((image) => ({ name: image.name, success: true })),
      exportDestinations: ["Mock / Salida"],
      exportResult: {
        success: true,
        processed: exportableImages().length,
        total: exportableImages().length,
        errors: 0,
        destinations: ["Mock / Salida"],
      },
      statusText: "Exportación completada",
    });
  } else if (scenario === "export-partial") {
    Object.assign(state, {
      exportStatus: "partial",
      progress: 100,
      processed: exportableImages().length,
      exportCompletedItems: [
        { name: "camiseta_001.png", success: true },
        { name: "chaqueta_004.png", success: false },
      ],
      exportDestinations: ["Mock / Salida"],
      exportIssues: [
        { level: "error", title: "chaqueta_004.png", detail: "No se pudo leer alpha." },
        { level: "warning", title: "chaqueta_003.png", detail: "Vista renderizada con fallback." },
      ],
      exportResult: {
        success: false,
        processed: exportableImages().length,
        total: exportableImages().length,
        errors: 1,
        destinations: ["Mock / Salida"],
      },
      errors: [
        { level: "error", title: "chaqueta_004.png", detail: "No se pudo leer alpha." },
        { level: "warning", title: "chaqueta_003.png", detail: "Vista renderizada con fallback." },
      ],
      statusText: "Exportación con errores",
    });
  } else if (scenario === "export-failed") {
    Object.assign(state, {
      exportStatus: "failed",
      progress: 38,
      processed: 2,
      exportIssues: [
        { level: "error", title: "Destino no disponible", detail: "La carpeta ya no existe." },
      ],
      exportResult: {
        success: false,
        processed: 2,
        total: exportableImages().length,
        errors: 1,
        destinations: [],
      },
      errors: [
        { level: "error", title: "Destino no disponible", detail: "La carpeta ya no existe." },
      ],
      statusText: "Exportación fallida",
    });
  }

  render();
}

function loadBatch() {
  if (state.bridgeMode === "bridge") {
    void scanBridgeFolder();
    return;
  }

  clearTimers();
  thumbnailPreloads.clear();
  thumbnailFallbackQueue.length = 0;
  thumbnailFallbackInFlight.clear();
  clearBridgeExportPoll();
  Object.assign(state, {
    scenario: "batch-ready",
    batch: "scanning",
    batchSource: "mock",
    selectedImageId: null,
    previewStatus: "empty",
    previewData: null,
    previewError: "",
    thumbnailStatus: {},
    thumbnailErrors: [],
    exportStatus: "blocked",
    exportJobId: null,
    exportDestinations: [],
    exportMessages: [],
    exportCompletedItems: [],
    exportIssues: [],
    exportResult: null,
    progress: 0,
    processed: 0,
    errors: [],
    scanIssues: [],
    scanDiagnostics: emptyScanDiagnostics(),
    scanStatus: "Escaneando lote mock",
    statusText: "Escaneando carpeta",
  });
  render();
  setTimer(() => {
    Object.assign(state, {
      batch: "ready",
      selectedImageId: "img-001",
      previewStatus: "loading",
      exportStatus: "ready",
      scanDiagnostics: mockScanDiagnostics(),
      statusText: "Generando vista",
    });
    render();
    setTimer(() => {
      Object.assign(state, {
        previewStatus: "ready",
        statusText: "Listo para exportar",
      });
      render();
    }, 550);
  }, 450);
}

function loadMockBatch() {
  if (!devMode) {
    return;
  }
  state.bridgeMode = "mock";
  state.bridgeLastResponse = "Estado mock: lote listo";
  loadBatch();
}

function clearBatch() {
  clearBridgeExportPoll();
  state.outputEditMode = false;
  state.presetEditorOpen = false;
  setScenario("initial");
}

function showEmptyFolder() {
  if (!devMode) {
    return;
  }
  state.bridgeMode = "mock";
  state.bridgeLastResponse = "Estado mock: carpeta vacía";
  setScenario("empty-folder");
}

function selectImage(imageId) {
  const image = activeImages().find((item) => item.id === imageId);
  if (!image) {
    return;
  }
  rememberSelectedImage(image);
  clearTimers();
  state.selectedImageId = image.id;
  state.localOverride = hasImageAdjustmentOverride(image);
  state.fitZoom = 100;
  resetViewerPan();
  if (image.source === "bridge") {
    void requestBridgePreview(image);
    return;
  }
  Object.assign(state, previewStateHelpers.previewLoadingState());
  render();
  setTimer(() => {
    Object.assign(state, previewStateHelpers.previewImageStatusState(image.status));
    render();
  }, 380);
}

function rememberSelectedImage(image) {
  if (image?.source === "bridge" && image.path) {
    storageHelpers.writeValue(window.localStorage, STORAGE_KEYS.selectedImagePath, image.path);
  }
}

function selectAdjacentImage(delta, options = {}) {
  const images = filteredImages();
  if (!images.length) {
    return;
  }
  const currentIndex = images.findIndex((image) => image.id === state.selectedImageId);
  const startIndex = currentIndex >= 0 ? currentIndex : 0;
  const nextIndex = Math.max(0, Math.min(images.length - 1, startIndex + delta));
  selectImage(images[nextIndex].id);
  if (options.focus) {
    queueImageFocus(images[nextIndex].id);
  }
}

function selectEdgeImage(edge, options = {}) {
  const images = filteredImages();
  if (!images.length) {
    return;
  }
  const image = edge === "last" ? images[images.length - 1] : images[0];
  selectImage(image.id);
  if (options.focus) {
    queueImageFocus(image.id);
  }
}

function clearPreviewSelection() {
  state.previewRequestId += 1;
  clearTimers();
  state.selectedImageId = null;
  state.localOverride = false;
  Object.assign(state, previewStateHelpers.previewEmptyState());
  state.fitZoom = 100;
  resetViewerPan();
}

function ensureGallerySelectionForFilter() {
  const visible = filteredImages();
  if (visible.some((image) => image.id === state.selectedImageId)) {
    return false;
  }
  if (visible.length) {
    selectImage(visible[0].id);
    return true;
  }
  if (state.filter !== BATCH_FILTERS.all || state.search.trim()) {
    clearPreviewSelection();
  }
  return false;
}

function applyGalleryFilter(filter) {
  state.filter = filter || BATCH_FILTERS.all;
  state.statusText = galleryHelpers.filterStatusText(state.filter);
  if (ensureGallerySelectionForFilter()) {
    return;
  }
  render();
}

function queueImageFocus(imageId = state.selectedImageId) {
  if (!imageId) {
    return;
  }
  window.requestAnimationFrame(() => {
    const button = $$("#image-list [data-image-id]").find((item) => item.dataset.imageId === imageId);
    button?.focus({ preventScroll: true });
  });
}

function imageOverrideKey(image = selectedImage()) {
  return image?.path || image?.id || "";
}

function clampLocalOverrideValue(key, value) {
  const [minimum, maximum] = localOverrideLimits[key] || [-100, 100];
  const parsed = Number(value);
  const numeric = Number.isFinite(parsed) ? Math.round(parsed) : 0;
  return Math.max(minimum, Math.min(maximum, numeric));
}

function normalizeLocalOverride(override = {}) {
  const normalized = {};
  localOverrideKeys.forEach((key) => {
    const value = clampLocalOverrideValue(key, override?.[key]);
    if (value) {
      normalized[key] = value;
    }
  });
  return normalized;
}

function currentImageOverride(image = selectedImage()) {
  const key = imageOverrideKey(image);
  return key ? normalizeLocalOverride(state.imageOverrides[key]) : {};
}

function hasCurrentImageOverride(image = selectedImage()) {
  return Object.keys(currentImageOverride(image)).length > 0;
}

function hasImageAdjustmentOverride(image) {
  return hasCurrentImageOverride(image) || image?.status === "adjusted";
}

function imageAdjustmentOverrideCount(images = activeImages()) {
  return images.filter(hasImageAdjustmentOverride).length;
}

function resetAllImageOverrides() {
  state.imageOverrides = {};
  state.realImages = state.realImages.map((image) =>
    image.status === "adjusted" ? { ...image, status: "ready" } : image
  );
  state.localOverride = false;
  state.statusText = "Ajuste del lote aplicado a todas las imágenes";
  refreshPreviewAfterSettingChange();
}

function setCurrentImageOverrideValue(key, value) {
  const image = selectedImage();
  const overrideKey = imageOverrideKey(image);
  if (!image || !overrideKey || !localOverrideKeys.includes(key)) {
    return;
  }
  const next = {
    ...currentImageOverride(image),
    [key]: clampLocalOverrideValue(key, value),
  };
  const normalized = normalizeLocalOverride(next);
  if (Object.keys(normalized).length) {
    state.imageOverrides[overrideKey] = normalized;
  } else {
    delete state.imageOverrides[overrideKey];
  }
  state.localOverride = Object.keys(normalized).length > 0;
  state.statusText = state.localOverride ? "Ajuste personalizado" : "Ajuste de imagen restablecido";
  refreshPreviewAfterSettingChange();
}

function resetCurrentImageOverride() {
  const key = imageOverrideKey();
  if (!key) {
    return;
  }
  delete state.imageOverrides[key];
  state.localOverride = false;
  state.statusText = "Ajuste de imagen restablecido";
  refreshPreviewAfterSettingChange();
}

function settingsWithLocalOverride(settings = state.settings, override = currentImageOverride()) {
  const normalizedSettings = normalizeSettings(settings);
  const local = normalizeLocalOverride(override);
  const next = { ...normalizedSettings };
  if (Object.prototype.hasOwnProperty.call(local, "size_delta")) {
    next.scale_adjustment = Math.max(-30, Math.min(30, Number(next.scale_adjustment || 0) + local.size_delta));
  }
  if (Object.prototype.hasOwnProperty.call(local, "shadow_delta")) {
    next.opacity = Math.max(0, Math.min(100, Number(next.opacity || 0) + local.shadow_delta));
  }
  if (Object.prototype.hasOwnProperty.call(local, "blur_delta")) {
    next.blur = Math.max(0, Math.min(100, Number(next.blur || 0) + local.blur_delta));
  }
  return normalizeSettings(next);
}

function applyLocalAdjustmentOnly() {
  const image = selectedImage();
  if (!image) {
    return;
  }
  state.presetEditorOpen = false;
  state.localOverride = hasImageAdjustmentOverride(image);
  state.statusText = state.localOverride ? "Ajuste aplicado sólo a esta imagen" : "La imagen usa el ajuste del lote";
  render();
}

function isViewerNavigationAvailable() {
  return Boolean(selectedImage()) && !["empty", "error", "loading"].includes(state.previewStatus);
}

function applyViewerPanDom() {
  const canvas = $("#preview-canvas");
  if (!canvas) {
    return;
  }
  if (!viewerPanState.active) {
    clampViewerPan();
  }
  canvas.style.setProperty("--canvas-pan-x", `${Math.round(state.panX)}px`);
  canvas.style.setProperty("--canvas-pan-y", `${Math.round(state.panY)}px`);
}

function resetViewerPan() {
  state.panX = 0;
  state.panY = 0;
  applyViewerPanDom();
}

function viewerPanBounds() {
  const canvas = $("#preview-canvas");
  const target = canvas?.querySelector(".preview-image, .mock-product");
  if (!canvas || !target || state.fitMode === "fit") {
    return { minX: 0, maxX: 0, minY: 0, maxY: 0 };
  }
  const canvasRect = canvas.getBoundingClientRect();
  const targetRect = target.getBoundingClientRect();
  if (!canvasRect.width || !canvasRect.height || !targetRect.width || !targetRect.height) {
    return { minX: 0, maxX: 0, minY: 0, maxY: 0 };
  }
  const minVisibleX = Math.min(96, Math.max(32, Math.min(canvasRect.width, targetRect.width) * 0.25));
  const minVisibleY = Math.min(96, Math.max(32, Math.min(canvasRect.height, targetRect.height) * 0.25));
  const maxX = targetRect.width > canvasRect.width
    ? Math.max(0, Math.round((canvasRect.width + targetRect.width) / 2 - minVisibleX))
    : 0;
  const maxY = targetRect.height > canvasRect.height
    ? Math.max(0, Math.round((canvasRect.height + targetRect.height) / 2 - minVisibleY))
    : 0;
  return { minX: -maxX, maxX, minY: -maxY, maxY };
}

function clampViewerPan() {
  const bounds = viewerPanBounds();
  state.panX = Math.max(bounds.minX, Math.min(bounds.maxX, state.panX));
  state.panY = Math.max(bounds.minY, Math.min(bounds.maxY, state.panY));
}

function canViewerPan() {
  const bounds = viewerPanBounds();
  return bounds.minX !== 0 || bounds.maxX !== 0 || bounds.minY !== 0 || bounds.maxY !== 0;
}

function viewerModeLabel(mode = state.fitMode) {
  return previewStateHelpers.viewerModeLabel(mode, VIEW_MODE_LABELS);
}

function currentViewerZoom() {
  return previewStateHelpers.isAutoViewerMode() ? state.fitZoom : state.zoom;
}

function setViewerZoom(nextZoom, anchorEvent = null) {
  const zoom = previewStateHelpers.clampViewerZoom(nextZoom);
  const previousZoom = Math.max(1, currentViewerZoom());
  if (anchorEvent) {
    const canvas = $("#preview-canvas");
    const rect = canvas?.getBoundingClientRect();
    if (rect?.width && rect?.height) {
      const originX = anchorEvent.clientX - (rect.left + rect.width / 2);
      const originY = anchorEvent.clientY - (rect.top + rect.height / 2);
      const ratio = zoom / previousZoom;
      state.panX = originX - (originX - state.panX) * ratio;
      state.panY = originY - (originY - state.panY) * ratio;
    }
  }
  state.fitMode = "manual";
  state.zoom = zoom;
  state.statusText = zoom === 100 ? "Zoom 100%" : `Zoom ${zoom}%`;
  render();
  window.requestAnimationFrame(() => {
    clampViewerPan();
    applyViewerPanDom();
  });
}

function setViewerMode(mode) {
  if (!["height", "width"].includes(mode)) {
    return;
  }
  state.fitMode = mode;
  resetViewerPan();
  state.statusText = `Vista: ${viewerModeLabel(mode)}`;
  render();
}

function toggleViewerZoomMode() {
  if (!isViewerNavigationAvailable()) {
    return;
  }
  setViewerMode(DEFAULT_VIEW_MODE);
}

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
