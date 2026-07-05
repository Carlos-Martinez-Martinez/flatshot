(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotInterfacePreferences = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const DEFAULTS = Object.freeze({
    density: "compact",
    complexityMode: "simple",
    reduceMotion: false,
    showRecentFolders: true,
    onboardingBackground: true,
    startupAdjustment: null,
    thumbnailSize: "medium",
    fileNameDisplay: "always",
  });
  const densityValues = new Set(["compact", "comfortable"]);
  const complexityModeValues = new Set(["simple", "advanced"]);
  const thumbnailSizeValues = new Set(["small", "medium", "large"]);
  const fileNameDisplayValues = new Set(["always", "hover", "none"]);

  function defaultInterfacePreferences() {
    return { ...DEFAULTS };
  }

  function normalizeChoice(value, allowed, fallback) {
    return allowed.has(value) ? value : fallback;
  }

  function cloneSerializable(value) {
    if (Array.isArray(value)) {
      return value.map(cloneSerializable);
    }
    if (value && typeof value === "object") {
      return Object.fromEntries(
        Object.entries(value).map(([key, item]) => [key, cloneSerializable(item)])
      );
    }
    return value;
  }

  function startupAdjustmentPreference(value = {}) {
    const source = value && typeof value === "object" && !Array.isArray(value)
      ? value.startupAdjustment
      : null;
    if (!source || typeof source !== "object" || Array.isArray(source)) {
      return null;
    }
    if (!source.settings || typeof source.settings !== "object" || Array.isArray(source.settings)) {
      return null;
    }
    const name = String(source.name || "Ajuste inicial").trim() || "Ajuste inicial";
    return {
      name,
      settings: cloneSerializable(source.settings),
      updatedAt: typeof source.updatedAt === "string" ? source.updatedAt : "",
    };
  }

  function normalizeInterfacePreferences(value = {}) {
    const source = value && typeof value === "object" && !Array.isArray(value) ? value : {};
    return {
      density: normalizeChoice(source.density, densityValues, DEFAULTS.density),
      complexityMode: normalizeChoice(source.complexityMode, complexityModeValues, DEFAULTS.complexityMode),
      reduceMotion: source.reduceMotion === true,
      showRecentFolders: source.showRecentFolders === false ? false : DEFAULTS.showRecentFolders,
      onboardingBackground: source.onboardingBackground === false ? false : DEFAULTS.onboardingBackground,
      startupAdjustment: startupAdjustmentPreference(source),
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
      root.dataset.complexityMode = normalized.complexityMode;
      root.dataset.motion = normalized.reduceMotion ? "reduced" : "auto";
      root.dataset.onboardingBackground = normalized.onboardingBackground ? "enabled" : "disabled";
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
    startupAdjustmentPreference,
    writeInterfacePreferences,
  };
});
