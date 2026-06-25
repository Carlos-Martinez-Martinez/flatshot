(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotBridgeUrl = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  function normalizeBridgeUrl(value, fallback = "") {
    const candidate = String(value || "").trim().replace(/\/+$/, "");
    if (candidate) {
      return candidate;
    }
    return String(fallback || "").trim().replace(/\/+$/, "");
  }

  function initialBridgeUrlFromSearch(search, defaultBridgeUrl) {
    let bridgeParam = "";
    try {
      bridgeParam = new URLSearchParams(search || "").get("bridge") || "";
    } catch (error) {
      bridgeParam = "";
    }
    return normalizeBridgeUrl(bridgeParam, defaultBridgeUrl);
  }

  function resolveRuntimeBridgeUrl(options = {}) {
    return normalizeBridgeUrl(
      options.currentBridgeUrl,
      normalizeBridgeUrl(options.restoredBridgeUrl, options.defaultBridgeUrl)
    );
  }

  return {
    initialBridgeUrlFromSearch,
    normalizeBridgeUrl,
    resolveRuntimeBridgeUrl,
  };
});
