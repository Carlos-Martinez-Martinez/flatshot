(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotStorage = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  function readValue(storage, key) {
    try {
      return storage.getItem(key) || "";
    } catch (error) {
      return "";
    }
  }

  function readJson(storage, key, fallback) {
    const raw = readValue(storage, key);
    if (!raw) {
      return fallback;
    }
    try {
      return JSON.parse(raw);
    } catch (error) {
      return fallback;
    }
  }

  function writeValue(storage, key, value) {
    const normalized = String(value || "").trim();
    try {
      if (normalized) {
        storage.setItem(key, normalized);
      } else {
        storage.removeItem(key);
      }
    } catch (error) {
      // Persistence is a convenience; the app must still work if storage is blocked.
    }
  }

  function writeJson(storage, key, value) {
    try {
      storage.setItem(key, JSON.stringify(value));
    } catch (error) {
      // Settings persistence is local convenience; runtime state remains usable.
    }
  }

  return {
    readJson,
    readValue,
    writeJson,
    writeValue,
  };
});
