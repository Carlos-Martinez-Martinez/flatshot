(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotInterfacePreferences = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const DEFAULTS = Object.freeze({
    density: "compact",
    reduceMotion: false,
    showRecentFolders: true,
    thumbnailSize: "medium",
    fileNameDisplay: "always",
  });
  const densityValues = new Set(["compact", "comfortable"]);
  const thumbnailSizeValues = new Set(["small", "medium", "large"]);
  const fileNameDisplayValues = new Set(["always", "hover", "none"]);

  function defaultInterfacePreferences() {
    return { ...DEFAULTS };
  }

  function normalizeChoice(value, allowed, fallback) {
    return allowed.has(value) ? value : fallback;
  }

  function normalizeInterfacePreferences(value = {}) {
    const source = value && typeof value === "object" && !Array.isArray(value) ? value : {};
    return {
      density: normalizeChoice(source.density, densityValues, DEFAULTS.density),
      reduceMotion: source.reduceMotion === true,
      showRecentFolders: source.showRecentFolders === false ? false : DEFAULTS.showRecentFolders,
      thumbnailSize: normalizeChoice(source.thumbnailSize, thumbnailSizeValues, DEFAULTS.thumbnailSize),
      fileNameDisplay: normalizeChoice(source.fileNameDisplay, fileNameDisplayValues, DEFAULTS.fileNameDisplay),
    };
  }

  function readInterfacePreferences(storage, key) {
    try {
      const raw = storage?.getItem?.(key);
      if (!raw) {
        return defaultInterfacePreferences();
      }
      return normalizeInterfacePreferences(JSON.parse(raw));
    } catch (error) {
      return defaultInterfacePreferences();
    }
  }

  function writeInterfacePreferences(storage, key, preferences) {
    try {
      storage?.setItem?.(key, JSON.stringify(normalizeInterfacePreferences(preferences)));
    } catch (error) {
      // Interface preference persistence is optional; the session state remains active.
    }
  }

  function applyInterfacePreferences(documentRef, preferences) {
    const normalized = normalizeInterfacePreferences(preferences);
    const root = documentRef?.documentElement;
    if (root?.dataset) {
      root.dataset.uiDensity = normalized.density;
      root.dataset.motion = normalized.reduceMotion ? "reduced" : "auto";
      root.dataset.thumbnailSize = normalized.thumbnailSize;
      root.dataset.fileNameDisplay = normalized.fileNameDisplay;
    }
    return normalized;
  }

  return {
    applyInterfacePreferences,
    defaultInterfacePreferences,
    normalizeInterfacePreferences,
    readInterfacePreferences,
    writeInterfacePreferences,
  };
});
