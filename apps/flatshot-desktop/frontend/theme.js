(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotTheme = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  function normalizeTheme(value) {
    return value === "dark" ? "dark" : "light";
  }

  function readThemePreference(storage, key) {
    try {
      return normalizeTheme(storage.getItem(key));
    } catch (error) {
      return "light";
    }
  }

  function writeThemePreference(storage, key, theme) {
    try {
      storage.setItem(key, normalizeTheme(theme));
    } catch (error) {
      // Theme persistence is optional; the current session still updates.
    }
  }

  function applyTheme(documentRef, theme) {
    const normalized = normalizeTheme(theme);
    const root = documentRef?.documentElement;
    if (root?.dataset) {
      root.dataset.theme = normalized;
    }
    return normalized;
  }

  function toggleTheme(options = {}) {
    const nextTheme = normalizeTheme(options.currentTheme) === "dark" ? "light" : "dark";
    writeThemePreference(options.storage, options.storageKey, nextTheme);
    applyTheme(options.document, nextTheme);
    return nextTheme;
  }

  return {
    applyTheme,
    normalizeTheme,
    readThemePreference,
    toggleTheme,
    writeThemePreference,
  };
});
