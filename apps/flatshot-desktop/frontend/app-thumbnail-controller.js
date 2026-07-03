function imageThumbnailSrc(image) {
  if (!image) {
    return "";
  }
  if (image.source === "bridge") {
    return image.thumbnailUrl || (image.path ? bridgeThumbnailUrl(image.path) : "");
  }
  return galleryHelpers.mockThumbnailDataUrl(image);
}

function thumbnailState(image, src) {
  return galleryHelpers.thumbnailState({
    displaySrc: src,
    renderedOnly: false,
    src,
    stored: state.thumbnailStatus[image.id],
  });
}

function renderedThumbnailKey(image) {
  const signature = {
    background: state.background,
    format: state.format,
    imagePath: image.path,
    localOverride: currentImageOverride(image),
    preset: state.activePreset,
    settings: bridgePreviewSettings(),
    size: state.size,
  };
  return `rendered:${JSON.stringify(signature)}`;
}

function thumbnailTargetSize(maxSide = 180) {
  const match = /^(\d+)x(\d+)$/.exec(state.size);
  if (!match) {
    return { targetWidth: maxSide, targetHeight: maxSide };
  }
  const width = Number(match[1]) || maxSide;
  const height = Number(match[2]) || maxSide;
  const scale = Math.min(maxSide / Math.max(width, height), 1);
  return {
    targetWidth: Math.max(1, Math.round(width * scale)),
    targetHeight: Math.max(1, Math.round(height * scale)),
  };
}

function queueThumbnailPreload(images = null) {
  if (!hasBatch() || state.exportStatus === "running") {
    return;
  }
  window.requestAnimationFrame(() => preloadBatchThumbnails(images));
}

function preloadBatchThumbnails(images = null) {
  if (state.exportStatus === "running") {
    return;
  }
  (Array.isArray(images) ? images : activeImages()).forEach((image) => {
    const src = imageThumbnailSrc(image);
    const current = state.thumbnailStatus[image.id];
    const key = `${image.id}|${src}`;
    if (!src || (current?.src === src && ["loaded", "error"].includes(current.status)) || thumbnailPreloads.has(key)) {
      return;
    }
    const preloader = new Image();
    thumbnailPreloads.set(key, preloader);
    preloader.onload = () => {
      markThumbnailLoaded(image.id, src, preloader.naturalWidth, preloader.naturalHeight);
      thumbnailPreloads.delete(key);
    };
    preloader.onerror = () => {
      markThumbnailError(image.id, src);
      thumbnailPreloads.delete(key);
    };
    preloader.src = src;
  });
}

function cancelThumbnailWork() {
  thumbnailPreloads.forEach((preloader) => {
    preloader.onload = null;
    preloader.onerror = null;
    preloader.src = "";
  });
  thumbnailPreloads.clear();
  thumbnailFallbackQueue.length = 0;
}

function markThumbnailLoaded(imageId, sourceSrc, naturalWidth, naturalHeight, resolvedSrc = sourceSrc) {
  if (!activeImages().some((image) => image.id === imageId)) {
    return;
  }
  state.thumbnailStatus[imageId] = {
    status: "loaded",
    src: sourceSrc,
    sourceSrc,
    resolvedSrc,
    naturalWidth,
    naturalHeight,
    error: "",
  };
  applyThumbnailDomStatus(imageId, "loaded", resolvedSrc);
  updatePreviewDebugPanel();
}

function markThumbnailError(imageId, src) {
  const current = state.thumbnailStatus[imageId];
  if ((current?.sourceSrc === src || current?.src === src) && current.status === "loaded") {
    return;
  }
  if (requestThumbnailFallback(imageId, src)) {
    return;
  }
  commitThumbnailError(imageId, src);
}

function commitThumbnailError(imageId, src, detail = "") {
  const current = state.thumbnailStatus[imageId];
  if ((current?.sourceSrc === src || current?.src === src) && current.status === "loaded") {
    return;
  }
  if (!activeImages().some((image) => image.id === imageId)) {
    return;
  }
  const error = detail ? `Preview no disponible: ${detail}` : `Preview no disponible: ${src}`;
  state.thumbnailStatus[imageId] = {
    status: "error",
    src,
    sourceSrc: src,
    error,
  };
  state.thumbnailErrors = [
    { imageId, src, error },
    ...state.thumbnailErrors.filter((item) => item.imageId !== imageId),
  ].slice(0, 20);
  applyThumbnailDomStatus(imageId, "error");
  state.bridgeLastResponse = `thumbnail error: ${formatterHelpers.basename(src) || imageId}`;
  updatePreviewDebugPanel();
}

function requestThumbnailFallback(imageId, sourceSrc) {
  if (state.exportStatus === "running") {
    return false;
  }
  const image = activeImages().find((item) => item.id === imageId);
  if (!image || image.source !== "bridge" || !image.path) {
    return false;
  }

  const current = state.thumbnailStatus[imageId];
  if (current?.sourceSrc === sourceSrc && current.status === "loaded") {
    return false;
  }
  if (current?.sourceSrc === sourceSrc && current.fallbackAttempted && current.status === "loading") {
    return true;
  }
  if (thumbnailFallbackInFlight.has(imageId) || thumbnailFallbackQueue.some((item) => item.imageId === imageId)) {
    return true;
  }

  state.thumbnailStatus[imageId] = {
    renderedOnly: true,
    status: "loading",
    src: sourceSrc,
    sourceSrc,
    fallbackAttempted: true,
    error: "",
  };
  applyThumbnailDomStatus(imageId, "loading");
  thumbnailFallbackQueue.push({ imageId, sourceSrc });
  processThumbnailFallbackQueue();
  return true;
}

function processThumbnailFallbackQueue() {
  while (thumbnailFallbackInFlight.size < MAX_THUMBNAIL_FALLBACKS && thumbnailFallbackQueue.length) {
    const item = thumbnailFallbackQueue.shift();
    thumbnailFallbackInFlight.add(item.imageId);
    void renderFallbackThumbnail(item)
      .catch((error) => {
        commitThumbnailError(item.imageId, item.sourceSrc, bridgeErrorMessage(error));
      })
      .finally(() => {
        thumbnailFallbackInFlight.delete(item.imageId);
        processThumbnailFallbackQueue();
      });
  }
}

function applyThumbnailDomStatus(imageId, status, resolvedSrc = "") {
  const wrapper = Array.from(document.querySelectorAll(".thumb[data-thumb-id]"))
    .find((item) => item.dataset.thumbId === imageId);
  if (!wrapper) {
    return;
  }
  if (resolvedSrc) {
    let image = wrapper.querySelector(".thumb-image");
    if (!image) {
      const item = activeImages().find((activeImage) => activeImage.id === imageId);
      image = document.createElement("img");
      image.className = "thumb-image";
      image.loading = "eager";
      image.dataset.imageId = imageId;
      image.alt = `Miniatura de ${item?.name || "imagen"}`;
      wrapper.prepend(image);
    }
    if (image && image.getAttribute("src") !== resolvedSrc) {
      image.src = resolvedSrc;
    }
  }
  wrapper.classList.remove("is-loading", "is-loaded", "is-error");
  wrapper.classList.add(`is-${status}`);
  if (status === "error") {
    const label = wrapper.querySelector(".thumb-error");
    if (label) {
      label.textContent = "Sin preview";
    }
  }
}

async function renderFallbackThumbnail({ imageId, sourceSrc }) {
  const image = activeImages().find((item) => item.id === imageId);
  if (!image) {
    return;
  }

  const response = await bridgeRequest("/preview/render", {
    method: "POST",
    body: JSON.stringify({
      imagePath: image.path,
      ...thumbnailTargetSize(),
      settings: bridgePreviewSettings(),
      localOverride: currentImageOverride(image),
    }),
    timeoutMs: 20000,
  });
  if (imageThumbnailSrc(image) !== sourceSrc) {
    return;
  }
  const data = previewResponseToData(response);
  markThumbnailLoaded(imageId, sourceSrc, data.width, data.height, data.src);
}
