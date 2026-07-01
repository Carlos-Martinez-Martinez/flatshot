async function pickBridgeFolder() {
  Object.assign(state, scanStateHelpers.folderPickStartState());
  render();

  try {
    const selected = await bridgeRequest("/folders/pick", {
      method: "POST",
      body: JSON.stringify({ initialPath: parseFolderInput(state.bridgeScanPath)[0] || "" }),
      timeoutMs: 300000,
    });
    if (!selected.selected || !selected.path) {
      Object.assign(state, scanStateHelpers.folderPickCancelledState());
      render();
      return;
    }

    Object.assign(state, scanStateHelpers.folderPickSelectedState(selected.path));
    persistBridgeScanPath();
    render();
    await scanBridgeFolder();
  } catch (error) {
    const message = bridgeErrorMessage(error);
    Object.assign(state, scanStateHelpers.folderPickErrorState(message));
    render();
  }
}

async function pickOutputProfileDestination() {
  if (!state.appSettingsOpen) {
    return;
  }
  updateOutputProfileDraftFromForm();
  renderOutputProfileModalState();
  const raw = outputProfileFormRawData();
  const initialPath = raw.destinationMode === "custom" && raw.destinationValue
    ? raw.destinationValue
    : storageHelpers.readValue(window.localStorage, STORAGE_KEYS.lastOutputFolder);
  state.statusText = "Eligiendo carpeta de salida";
  try {
    const selected = await bridgeRequest("/folders/pick", {
      method: "POST",
      body: JSON.stringify({ initialPath: initialPath || "" }),
      timeoutMs: 300000,
    });
    if (!selected.selected || !selected.path) {
      state.statusText = "Selección de carpeta cancelada";
      renderOutputProfileModalState();
      return;
    }
    const modeInput = $("#profile-destination-mode-input");
    const destinationInput = $("#profile-destination-input");
    if (modeInput) {
      modeInput.value = "custom";
    }
    if (destinationInput) {
      destinationInput.value = selected.path;
    }
    storageHelpers.writeValue(window.localStorage, STORAGE_KEYS.lastOutputFolder, selected.path);
    updateOutputProfileDraftFromForm();
    state.statusText = "Carpeta de salida configurada";
    renderOutputProfileModalState();
  } catch (error) {
    state.statusText = bridgeErrorMessage(error);
    renderOutputProfileModalState();
  }
}

function applyBridgePresets(payload) {
  const items = Array.isArray(payload.items)
    ? payload.items.map(normalizePresetItem).filter(Boolean)
    : [];
  state.bridgePresets = items;
  state.bridgePresetSource = payload.source || "unavailable";
  state.bridgePresetWarning = payload.warning || "";
  if (!items.length) {
    state.presetSource = "Sin ajustes";
    return;
  }

  const names = items.map((item) => item.name);
  if (state.bridgeMode === "bridge") {
    if (!names.includes(state.activePreset)) {
      state.activePreset = names[0];
    }
    applyPresetSettings(state.activePreset, { refresh: false, statusText: state.statusText });
  }
}

function normalizePresetItem(item) {
  if (!item || typeof item !== "object" || !item.name) {
    return null;
  }
  return {
    name: String(item.name),
    categoryId: String(item.categoryId || "uncategorized"),
    category: String(item.category || "Sin categoría"),
    settings: normalizeSettings(item.settings),
    source: "bridge",
  };
}

async function scanBridgeFolder() {
  state.bridgeMode = "bridge";
  const folders = parseFolderInput(state.bridgeScanPath);
  if (!folders.length) {
    Object.assign(state, scanStateHelpers.emptyScanPathState(state.bridgeStatus === "connected"));
    render();
    return;
  }
  persistBridgeScanPath(folders[0]);

  clearTimers();
  thumbnailPreloads.clear();
  thumbnailFallbackQueue.length = 0;
  thumbnailFallbackInFlight.clear();
  clearBridgeExportPoll();
  Object.assign(state, scanStateHelpers.scanStartState(folders, emptyScanDiagnostics(), DEFAULT_VIEW_MODE));
  render();

  try {
    if (!state.bridgePresets.length) {
      const presetPayload = await bridgeRequest("/presets");
      applyBridgePresets(presetPayload);
    }
    const response = await bridgeRequest("/folders/scan", {
      method: "POST",
      body: JSON.stringify({ folders, imageOverrides: state.imageOverrides }),
    });
    applyBridgeScanResult(response);
  } catch (error) {
    const message = bridgeErrorMessage(error);
    Object.assign(state, scanStateHelpers.scanFailureState(message, emptyScanDiagnostics()));
  }

  render();
}

function persistBridgeScanPath(path = parseFolderInput(state.bridgeScanPath)[0] || "") {
  storageHelpers.writeValue(window.localStorage, STORAGE_KEYS.bridgeScanPath, path);
  scheduleBridgeUiPreferencesSave();
}

function applyBridgeScanResult(response) {
  state.scanDiagnostics = scanDiagnosticsFromResponse(response);
  state.realFolders = (response.folders || []).map(bridgeFolderToItem);
  state.realImages = (response.folders || []).flatMap((folder, folderIndex) =>
    (folder.images || []).map((image, imageIndex) => bridgeImageToItem(image, folderIndex, imageIndex))
  );
  const folderWarnings = state.realFolders.filter((folder) => folder.status === "warning" || folder.status === "error").length;
  const responseErrors = Array.isArray(response.errors) ? response.errors : [];
  state.bridgeStatus = "connected";
  state.batchSource = "bridge";
  state.bridgeMessage = batchViewHelpers.bridgeScanMessage(response.totalImages || 0, folderWarnings + responseErrors.length);
  state.bridgeLastResponse = `scan OK · ${response.totalImages || 0} imágenes`;
  state.scanIssues = [
    ...state.realFolders
      .filter((folder) => folder.status === "warning" || folder.status === "error")
      .map((folder) => ({
        level: folder.status === "error" ? "error" : "warning",
        title: folder.name,
        detail: folder.detail,
      })),
    ...responseErrors.map((detail) => ({ level: "error", title: "Escaneo", detail })),
  ];
  if (actionableOmissions().length > 0) {
    state.scanIssues.push({
      level: "warning",
      title: "Archivos a revisar",
      detail: actionableOmissionSummaryText(),
    });
  }

  if (state.realImages.length) {
    const rememberedPath = storageHelpers.readValue(window.localStorage, STORAGE_KEYS.selectedImagePath);
    const rememberedImage = rememberedPath
      ? state.realImages.find((image) => image.path === rememberedPath)
      : null;
    const selectedImage = rememberedImage || state.realImages[0];
    Object.assign(state, scanStateHelpers.scanReadyState({
      defaultViewMode: DEFAULT_VIEW_MODE,
      imageCount: state.realImages.length,
      localOverride: hasImageAdjustmentOverride(selectedImage),
      scanIssueCount: state.scanIssues.length,
      selectedImageId: selectedImage.id,
    }));
    rememberSelectedImage(selectedImage);
    void requestBridgePreview(selectedImage);
    return;
  }

  Object.assign(state, scanStateHelpers.scanEmptyState(state.scanIssues));
}

function parseFolderInput(value) {
  return String(value || "")
    .split(/[;\n\r]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function actionableOmissionSummaryText() {
  return batchViewHelpers.omissionSummaryText(actionableOmissions(), "Sin avisos de archivos");
}

function ignoredSummaryText() {
  return batchViewHelpers.omissionSummaryText(ignoredOmissions(), "Sin archivos ignorados");
}

function folderActionableOmissionCount(folder) {
  return (folder.omitted || []).filter((item) => omissionSeverity(item) !== "ignored").length;
}

function bridgeFolderToItem(folder, index) {
  const hasErrors = Array.isArray(folder.errors) && folder.errors.length > 0;
  const count = Array.isArray(folder.images) ? folder.images.length : 0;
  const omittedCount = Number(folder.omittedCount) || 0;
  const actionableOmitted = folderActionableOmissionCount(folder);
  const exists = folder.exists !== false;
  const isDir = folder.isDir !== false;
  const status = hasErrors
    ? count ? "warning" : "error"
    : actionableOmitted ? "warning" : count ? "ready" : exists && isDir ? "empty" : "error";
  return {
    id: `bridge-folder-${index}`,
    name: formatterHelpers.basename(folder.path) || `Carpeta ${index + 1}`,
    path: folder.path,
    count,
    source: "bridge",
    exists,
    isDir,
    status,
    detail: hasErrors
      ? folder.errors[0]
      : actionableOmitted
        ? `${count} imágenes · ${actionableOmitted} avisos`
        : omittedCount
          ? `${count} imágenes · ${omittedCount} ignorados`
        : count ? `${count} imágenes` : "No se encontraron imágenes",
    filesFound: Number(folder.filesFound) || count,
    omittedCount,
  };
}

function bridgeImageToItem(image, folderIndex, imageIndex) {
  const suffix = String(image.suffix || "").replace(".", "").toUpperCase() || "PNG";
  const detail = `${suffix} · ${formatterHelpers.formatBytes(image.sizeBytes)}`;
  return {
    id: `bridge-${folderIndex}-${imageIndex}`,
    folderId: `bridge-folder-${folderIndex}`,
    name: image.name,
    detail,
    status: image.hasLocalOverride ? "adjusted" : "ready",
    exportable: true,
    source: "bridge",
    path: image.path,
    thumbnailUrl: bridgeThumbnailUrl(image.path),
    originalUrl: "",
  };
}

function imageFileType(image) {
  return formatterHelpers.imageFileType(image, state.format || "Imagen");
}

function capabilitiesSummary(capabilities) {
  return formatterHelpers.capabilitiesSummary(capabilities);
}
