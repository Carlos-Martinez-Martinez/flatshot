function normalizedBridgeUrl() {
  return bridgeClientHelpers.normalizedBridgeUrl(state.bridgeUrl, defaultBridgeUrl);
}

function bridgeThumbnailUrl(path, size = 128, imageId = "") {
  return bridgeClientHelpers.thumbnailUrl(normalizedBridgeUrl(), path, size, state.bridgeToken, imageId);
}

async function bridgeRequest(path, options = {}) {
  return bridgeClientHelpers.request(normalizedBridgeUrl(), path, {
    ...options,
    authToken: state.bridgeToken,
  });
}

function bridgeErrorMessage(error) {
  return bridgeClientHelpers.errorMessage(error);
}
