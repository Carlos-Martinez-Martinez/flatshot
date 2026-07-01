(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotNumberUtils = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  function clampNumber(value, min, max, fallback) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) {
      return fallback;
    }
    return Math.min(max, Math.max(min, numeric));
  }

  function roundedSceneValue(value, min, max, fallback) {
    return Math.round(clampNumber(value, min, max, fallback) * 1000) / 1000;
  }

  return {
    clampNumber,
    roundedSceneValue,
  };
});
