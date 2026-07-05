(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotFormatters = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  function basename(path) {
    return String(path || "").split(/[\\/]/).filter(Boolean).pop() || "";
  }

  function displayPath(path) {
    const name = basename(path);
    return name || String(path || "");
  }

  function imageFileStem(name) {
    return basename(name).replace(/\.[^.\\/]+$/, "") || basename(name) || "Imagen";
  }

  function imageFileType(image, fallback = "Imagen") {
    const fromName = String(image?.name || "").split(".").pop();
    if (fromName && fromName !== image?.name) {
      return fromName.toUpperCase();
    }
    const fromDetail = String(image?.detail || "").split("·")[0]?.trim();
    return fromDetail || fallback || "Imagen";
  }

  function formatBytes(bytes) {
    const value = Number(bytes) || 0;
    if (value >= 1024 * 1024) {
      return `${(value / (1024 * 1024)).toFixed(1)} MB`;
    }
    if (value >= 1024) {
      return `${Math.round(value / 1024)} KB`;
    }
    return `${value} B`;
  }

  function pathToFileUrl(path) {
    const normalized = String(path || "").replaceAll("\\", "/");
    if (/^[a-z]:\//i.test(normalized)) {
      return `file:///${encodeURI(normalized)}`;
    }
    if (normalized.startsWith("/")) {
      return `file://${encodeURI(normalized)}`;
    }
    return encodeURI(normalized);
  }

  function capabilitiesSummary(capabilities) {
    if (!capabilities) {
      return "Sin comprobar";
    }
    const available = [];
    if (capabilities.folderScan) {
      available.push("scan");
    }
    if (capabilities.presetsRead) {
      available.push("presets");
    }
    if (capabilities.previewRender) {
      available.push("preview");
    }
    if (capabilities.exportRun) {
      available.push("export");
    }
    return available.length ? available.join(" · ") : "Sin capacidades activas";
  }

  function debugUrlLabel(value) {
    const text = String(value || "");
    if (text.startsWith("data:")) {
      const comma = text.indexOf(",");
      return comma > 0 ? `${text.slice(0, comma)}...` : "data URL";
    }
    return text.length > 120 ? `${text.slice(0, 117)}...` : text;
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  if (typeof window !== "undefined") {
    window.escapeHtml = escapeHtml;
  }

  return {
    basename,
    capabilitiesSummary,
    debugUrlLabel,
    displayPath,
    escapeHtml,
    formatBytes,
    imageFileStem,
    imageFileType,
    pathToFileUrl,
  };
});
