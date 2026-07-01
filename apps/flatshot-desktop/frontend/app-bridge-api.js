function normalizedBridgeUrl() {
  return bridgeClientHelpers.normalizedBridgeUrl(state.bridgeUrl, defaultBridgeUrl);
}

function bridgeThumbnailUrl(path, size = 128) {
  return bridgeClientHelpers.thumbnailUrl(normalizedBridgeUrl(), path, size);
}

async function bridgeRequest(path, options = {}) {
  return bridgeClientHelpers.request(normalizedBridgeUrl(), path, options);
}

function bridgeErrorMessage(error) {
  return bridgeClientHelpers.errorMessage(error);
}
