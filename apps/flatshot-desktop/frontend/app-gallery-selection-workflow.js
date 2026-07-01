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
