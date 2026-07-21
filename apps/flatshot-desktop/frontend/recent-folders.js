(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotRecentFolders = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const DEFAULT_LIMIT = 8;

  function normalizePath(path) {
    return String(path || "").trim();
  }

  function basename(path) {
    const normalized = normalizePath(path).replace(/[\\/]+$/, "");
    if (!normalized) {
      return "";
    }
    return normalized.split(/[\\/]+/).pop() || normalized;
  }

  function normalizedEntry(entry = {}) {
    const path = normalizePath(entry.path);
    if (!path) {
      return null;
    }
    const imageCount = Number(entry.imageCount);
    return {
      path,
      name: normalizePath(entry.name) || basename(path) || path,
      lastUsedAt: normalizePath(entry.lastUsedAt) || new Date().toISOString(),
      imageCount: Number.isFinite(imageCount) && imageCount >= 0 ? Math.round(imageCount) : null,
    };
  }

  function readRecentFolders(storage, key) {
    try {
      const raw = storage?.getItem?.(key);
      if (!raw) {
        return [];
      }
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed)) {
        return [];
      }
      return parsed.map(normalizedEntry).filter(Boolean);
    } catch (error) {
      return [];
    }
  }

  function writeRecentFolders(storage, key, folders) {
    try {
      const normalized = Array.isArray(folders) ? folders.map(normalizedEntry).filter(Boolean) : [];
      if (normalized.length) {
        storage?.setItem?.(key, JSON.stringify(normalized));
      } else {
        storage?.removeItem?.(key);
      }
    } catch (error) {
      // Recent folders are convenience state; blocked storage must not block scans.
    }
  }

  function rememberRecentFolder(storage, key, options = {}) {
    const entry = normalizedEntry({
      path: options.path,
      name: options.name,
      imageCount: options.imageCount,
      lastUsedAt: options.now || new Date().toISOString(),
    });
    if (!entry) {
      return [];
    }
    const limit = Math.max(1, Math.min(20, Number(options.limit) || DEFAULT_LIMIT));
    const existing = readRecentFolders(storage, key).filter((item) => item.path !== entry.path);
    const next = [entry, ...existing].slice(0, limit);
    writeRecentFolders(storage, key, next);
    return next;
  }

  function forgetRecentFolder(storage, key, path) {
    const normalizedPath = normalizePath(path);
    const next = readRecentFolders(storage, key).filter((item) => item.path !== normalizedPath);
    writeRecentFolders(storage, key, next);
    return next;
  }

  function recentFolderMeta(entry = {}) {
    const date = normalizePath(entry.lastUsedAt).slice(0, 10);
    const count = Number(entry.imageCount);
    const parts = [];
    if (date) {
      parts.push(date);
    }
    if (Number.isFinite(count) && count >= 0) {
      parts.push(`${count} ${count === 1 ? "imagen" : "imágenes"}`);
    }
    return parts.join(" · ");
  }

  return {
    basename,
    forgetRecentFolder,
    normalizePath,
    readRecentFolders,
    recentFolderMeta,
    rememberRecentFolder,
    writeRecentFolders,
  };
});
