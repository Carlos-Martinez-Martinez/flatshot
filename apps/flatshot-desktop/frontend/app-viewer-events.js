function handleDocumentKeydown(event) {
  const target = event.target;
  const isTyping = target instanceof HTMLInputElement
    || target instanceof HTMLTextAreaElement
    || target instanceof HTMLSelectElement
    || target?.isContentEditable;
  const command = event.ctrlKey || event.metaKey;

  if (event.key === "Tab" && trapOpenModalFocus(event)) {
    return;
  }

  if (typeof isNumericControlInput === "function" && isNumericControlInput(target)) {
    if (event.key === "Enter") {
      commitNumericControlInput(target);
      event.preventDefault();
      return;
    }
    if (event.key === "Escape") {
      cancelNumericControlInput(target);
      event.preventDefault();
      return;
    }
  }

  if (command && event.key.toLowerCase() === "f") {
    event.preventDefault();
    const search = $("#image-search");
    if (search && hasBatch()) {
      search.focus();
      search.select();
    }
    return;
  }

  if (command && event.key.toLowerCase() === "e") {
    event.preventDefault();
    if (isExportReady() && state.exportStatus !== "running") {
      startExport();
    }
    return;
  }

  if (event.key === "Escape") {
    if (state.exportConfirmOpen) {
      closeExportConfirm();
      event.preventDefault();
      return;
    }
    if (state.batchDetailOpen) {
      closeBatchDetail();
      event.preventDefault();
      return;
    }
    if (state.appSettingsOpen) {
      closeAppSettings();
      event.preventDefault();
      return;
    }
    const openDetails = Array.from(document.querySelectorAll("details[open]")).reverse()[0];
    if (openDetails) {
      openDetails.open = false;
      event.preventDefault();
    }
    return;
  }

  if (event.key === "Enter" && state.exportConfirmOpen && !isTyping) {
    event.preventDefault();
    confirmExportFromModal();
    return;
  }

  if (isTyping) {
    return;
  }

  const key = event.key.toLowerCase();
  if (event.key === "ArrowLeft") {
    event.preventDefault();
    selectAdjacentImage(-1, { focus: true });
  } else if (event.key === "ArrowRight") {
    event.preventDefault();
    selectAdjacentImage(1, { focus: true });
  } else if (event.key === "Home") {
    event.preventDefault();
    selectEdgeImage("first", { focus: true });
  } else if (event.key === "End") {
    event.preventDefault();
    selectEdgeImage("last", { focus: true });
  }
}

function handleViewerWheel(event) {
  if (!isViewerNavigationAvailable()) {
    return;
  }
  event.preventDefault();
  const baseZoom = currentViewerZoom();
  const direction = event.deltaY < 0 ? 1 : -1;
  const step = event.shiftKey ? 5 : 10;
  setViewerZoom(baseZoom + direction * step, event);
}

function handleViewerPointerDown(event) {
  if (
    event.button !== 0
    || !isViewerNavigationAvailable()
    || event.target.closest("button, input, textarea, select, summary, a")
  ) {
    return;
  }
  if (!canViewerPan()) {
    return;
  }
  const canvas = $("#preview-canvas");
  viewerPanState.active = true;
  viewerPanState.pointerId = event.pointerId;
  viewerPanState.startX = event.clientX;
  viewerPanState.startY = event.clientY;
  viewerPanState.originX = state.panX;
  viewerPanState.originY = state.panY;
  canvas?.classList.add("is-panning");
  try {
    canvas?.setPointerCapture(event.pointerId);
  } catch (error) {
    // Pointer capture is optional; document-level listeners continue the drag.
  }
}

function handleViewerPointerMove(event) {
  if (!viewerPanState.active || event.pointerId !== viewerPanState.pointerId) {
    return;
  }
  state.panX = viewerPanState.originX + event.clientX - viewerPanState.startX;
  state.panY = viewerPanState.originY + event.clientY - viewerPanState.startY;
  clampViewerPan();
  applyViewerPanDom();
}

function handleViewerPointerEnd(event) {
  if (!viewerPanState.active || event.pointerId !== viewerPanState.pointerId) {
    return;
  }
  const canvas = $("#preview-canvas");
  viewerPanState.active = false;
  canvas?.classList.remove("is-panning");
  try {
    if (viewerPanState.pointerId !== null) {
      canvas?.releasePointerCapture(viewerPanState.pointerId);
    }
  } catch (error) {
    // Release can fail if the pointer was already released by the browser.
  }
  viewerPanState.pointerId = null;
}

function handleViewerDoubleClick(event) {
  if (event.target.closest("button, input, textarea, select, summary, a")) {
    return;
  }
  event.preventDefault();
  toggleViewerZoomMode();
}
