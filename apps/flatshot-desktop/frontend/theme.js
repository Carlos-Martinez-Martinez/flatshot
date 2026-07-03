(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotTheme = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const brandTones = Object.freeze([
    { id: "green", label: "Verde", color: "#0e8469" },
    { id: "blue", label: "Azul", color: "#2563eb" },
    { id: "indigo", label: "Índigo", color: "#4f46e5" },
    { id: "violet", label: "Violeta", color: "#7c3aed" },
    { id: "coral", label: "Coral", color: "#c2410c" },
    { id: "amber", label: "Ámbar", color: "#b45309" },
  ]);
  const brandToneIds = new Set(brandTones.map((tone) => tone.id));

  function normalizeTheme(value) {
    return value === "dark" ? "dark" : "light";
  }

  function normalizeThemePreference(value) {
    return ["light", "dark", "system"].includes(value) ? value : "light";
  }

  function resolveThemePreference(preference, rootRef = typeof window !== "undefined" ? window : null) {
    const normalized = normalizeThemePreference(preference);
    if (normalized !== "system") {
      return normalized;
    }
    try {
      return rootRef?.matchMedia?.("(prefers-color-scheme: dark)")?.matches ? "dark" : "light";
    } catch (error) {
      return "light";
    }
  }

  function normalizeBrandTone(value) {
    return brandToneIds.has(value) ? value : "green";
  }

  function brandToneOptions() {
    return brandTones.map((tone) => ({ ...tone }));
  }

  function readThemePreference(storage, key) {
    try {
      return normalizeThemePreference(storage.getItem(key));
    } catch (error) {
      return "light";
    }
  }

  function readBrandTonePreference(storage, key) {
    try {
      return normalizeBrandTone(storage.getItem(key));
    } catch (error) {
      return "green";
    }
  }

  function writeThemePreference(storage, key, theme) {
    try {
      storage.setItem(key, normalizeThemePreference(theme));
    } catch (error) {
      // Theme persistence is optional; the current session still updates.
    }
  }

  function writeBrandTonePreference(storage, key, tone) {
    try {
      storage.setItem(key, normalizeBrandTone(tone));
    } catch (error) {
      // Brand persistence is optional; the current session still updates.
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

  function applyBrandTone(documentRef, tone) {
    const normalized = normalizeBrandTone(tone);
    const root = documentRef?.documentElement;
    if (root?.dataset) {
      root.dataset.brandTone = normalized;
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
    applyBrandTone,
    applyTheme,
    brandToneOptions,
    normalizeBrandTone,
    normalizeTheme,
    normalizeThemePreference,
    readBrandTonePreference,
    readThemePreference,
    resolveThemePreference,
    toggleTheme,
    writeBrandTonePreference,
    writeThemePreference,
  };
});
