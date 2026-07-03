let _previewBlobUrl = null;

async function requestBridgePreview(image) {
  const requestId = state.previewRequestId + 1;
  state.previewRequestId = requestId;
  Object.assign(state, previewStateHelpers.previewLoadingState({ clearData: false }));
  render();

  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), 20000);

  try {
    const previewImage = await bridgeClientHelpers.requestPreviewImage(normalizedBridgeUrl(), {
      signal: controller.signal,
      imagePath: image.path,
      targetSize: previewTargetSize(),
      settings: bridgePreviewSettings(),
      localOverride: currentImageOverride(image),
    });
    window.clearTimeout(timer);

    if (isStalePreviewResponse(requestId, image)) {
      return;
    }

    if (_previewBlobUrl) {
      URL.revokeObjectURL(_previewBlobUrl);
    }
    _previewBlobUrl = URL.createObjectURL(previewImage.blob);

    const previewData = {
      src: _previewBlobUrl,
      width: previewImage.width,
      height: previewImage.height,
      sourceName: image.name,
      sourcePath: image.path,
      warning: previewImage.warning,
      renderTimeMs: 0,
    };

    Object.assign(state, previewStateHelpers.previewBridgeResultState(previewData, previewData.warning));
  } catch (error) {
    window.clearTimeout(timer);
    if (isStalePreviewResponse(requestId, image)) {
      return;
    }
    const message = error.name === "AbortError"
      ? "La vista tardó demasiado. Intenta de nuevo."
      : bridgeErrorMessage(error);
    Object.assign(state, previewStateHelpers.previewErrorState(message));
  }

  render();
}

function isStalePreviewResponse(requestId, image) {
  return requestId !== state.previewRequestId || state.selectedImageId !== image.id;
}

function previewResponseToData(response) {
  return {
    src: `data:${response.image.mimeType};base64,${response.image.dataBase64}`,
    width: response.image.width,
    height: response.image.height,
    sourceName: response.source?.name || selectedImage()?.name || "imagen.png",
    sourcePath: response.source?.path || selectedImage()?.path || "",
    warning: response.warning || "",
    renderTimeMs: Number(response.renderTimeMs) || 0,
  };
}

function bridgePreviewSettings() {
  return {
    ...normalizeSettings(state.settings),
    presetName: state.activePreset,
    transparentBg: state.background === "transparent",
    bgColor: outputProfileHelpers.backgroundColorTuple(state.background),
  };
}

function previewTargetSize() {
  const match = /^(\d+)x(\d+)$/.exec(state.size);
  if (!match) {
    return { targetWidth: 900, targetHeight: 900 };
  }
  const width = Number(match[1]);
  const height = Number(match[2]);
  const scale = Math.min(900 / Math.max(width, height), 1);
  return {
    targetWidth: Math.max(1, Math.round(width * scale)),
    targetHeight: Math.max(1, Math.round(height * scale)),
  };
}
