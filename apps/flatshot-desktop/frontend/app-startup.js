function initViewerResizeObserver() {
  const canvas = $("#preview-canvas");
  if (!canvas || !("ResizeObserver" in window)) {
    return;
  }
  viewerResizeObserver = new ResizeObserver(() => updateFitZoomReadout());
  viewerResizeObserver.observe(canvas);
}

function markFlatShotBootReady() {
  if (document?.documentElement?.dataset) {
    document.documentElement.dataset.boot = "ready";
  }
}

async function startFlatShotApp() {
  try {
    restoredSessionSnapshot = restoreSessionSnapshot();
    sessionSnapshotPersistenceEnabled = true;
    if (restoredSessionSnapshot) {
      render();
      return;
    }
    await restoreBridgeUiPreferences({ skipSessionSnapshot: true, renderOnRestore: false, timeoutMs: 900 });
    setScenario("initial");
  } catch (error) {
    window.FlatShotErrorBoundary?.renderGlobalError?.(error, { document, source: "app-startup" });
  } finally {
    markFlatShotBootReady();
  }
}

try {
  interactionBindingHelpers.wireFlatShotInteractions({
    document,
    window,
    $,
    $$,
    onboardingBackgroundHelpers,
    handlers: {
      backgroundSelectChange: handleBackgroundSelectChange,
      bridgeScanPathInput: handleBridgeScanPathInput,
      bridgeUrlInput: handleBridgeUrlInput,
      destinationInput: handleDestinationInput,
      destinationModeChange: handleDestinationModeChange,
      documentChange: handleDocumentChange,
      documentClick: handleDocumentClick,
      documentDragEnter: handleDocumentDragEnter,
      documentDragLeave: handleDocumentDragLeave,
      documentDragOver: handleDocumentDragOver,
      documentDrop: handleDocumentDrop,
      documentError: handleDocumentImageError,
      documentFocusOut: handleDocumentFocusOut,
      documentInput: handleDocumentInput,
      documentKeydown: handleDocumentKeydown,
      documentLoad: handleDocumentImageLoad,
      documentPointerDown: handleDocumentPointerDown,
      documentSubmit: handleDocumentSubmit,
      documentToggle: handleDocumentToggle,
      formatSelectChange: handleFormatSelectChange,
      galleryScroll: handleGalleryScroll,
      imageSearchInput: handleImageSearchInput,
      initViewerResizeObserver,
      inspectorDisclosureClick: handleInspectorDisclosureClick,
      lightingFieldInput: handleLightingFieldInput,
      lightingNumberFieldInput: handleLightingNumberFieldInput,
      lightingPresetClick: handleLightingPresetClick,
      namingInput: handleNamingInput,
      nudgeLightingScenePosition,
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
} catch (error) {
  window.FlatShotErrorBoundary?.renderGlobalError?.(error, { document, source: "app-startup" });
}
