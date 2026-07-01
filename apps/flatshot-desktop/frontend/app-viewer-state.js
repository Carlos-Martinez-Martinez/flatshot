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
