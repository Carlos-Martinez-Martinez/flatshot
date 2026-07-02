function initViewerResizeObserver() {
  const canvas = $("#preview-canvas");
  if (!canvas || !("ResizeObserver" in window)) {
    return;
  }
  viewerResizeObserver = new ResizeObserver(() => updateFitZoomReadout());
  viewerResizeObserver.observe(canvas);
}

function restorePersistentBridgeSession() {
  const path = parseFolderInput(state.bridgeScanPath)[0];
  if (!path || state.bridgeMode !== "bridge") {
    return;
  }
  state.bridgeScanPath = path;
  state.scanStatus = `Última carpeta: ${formatterHelpers.basename(path)}`;
  state.statusText = "Restaurando último lote";
  render();
  void scanBridgeFolder();
}

function startFlatShotApp() {
  restoredSessionSnapshot = restoreSessionSnapshot();
  sessionSnapshotPersistenceEnabled = true;
  if (restoredSessionSnapshot) {
    render();
    return;
  }
  setScenario("initial");
  void restoreBridgeUiPreferences({ skipSessionSnapshot: true });
  restorePersistentBridgeSession();
}

interactionBindingHelpers.wireFlatShotInteractions({
  document,
  window,
  $,
  $$,
  handlers: {
    backgroundSelectChange: handleBackgroundSelectChange,
    bridgeScanPathInput: handleBridgeScanPathInput,
    bridgeUrlInput: handleBridgeUrlInput,
    destinationInput: handleDestinationInput,
    destinationModeChange: handleDestinationModeChange,
    documentChange: handleDocumentChange,
    documentClick: handleDocumentClick,
    documentError: handleDocumentImageError,
    documentFocusOut: handleDocumentFocusOut,
    documentInput: handleDocumentInput,
    documentKeydown: handleDocumentKeydown,
    documentLoad: handleDocumentImageLoad,
    documentPointerDown: handleDocumentPointerDown,
    documentSubmit: handleDocumentSubmit,
    documentToggle: handleDocumentToggle,
    formatSelectChange: handleFormatSelectChange,
    imageSearchInput: handleImageSearchInput,
    initViewerResizeObserver,
    inspectorDisclosureClick: handleInspectorDisclosureClick,
    lightingFieldInput: handleLightingFieldInput,
    lightingNumberFieldInput: handleLightingNumberFieldInput,
    lightingPresetClick: handleLightingPresetClick,
    namingInput: handleNamingInput,
    outputProfileSelectChange: handleOutputProfileSelectChange,
    positionBackgroundPresetEditor,
    refreshPreviewAfterSettingChange,
    settingInput: handleSettingInput,
    sizeSelectChange: handleSizeSelectChange,
    sizeSelectInput: handleSizeSelectInput,
    startup: startFlatShotApp,
    updateLightingScenePosition,
    viewerDoubleClick: handleViewerDoubleClick,
    viewerPointerDown: handleViewerPointerDown,
    viewerPointerEnd: handleViewerPointerEnd,
    viewerPointerMove: handleViewerPointerMove,
    viewerWheel: handleViewerWheel,
    writeSessionSnapshot,
  },
});
