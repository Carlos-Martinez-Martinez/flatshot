(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotTopStatusView = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function countLabel(value, singular, plural) {
    const count = Number(value) || 0;
    return `${count} ${count === 1 ? singular : plural}`;
  }

  function topStatusSummaryHtml(options = {}) {
    const exportStatus = options.exportStatus || "idle";
    if (!options.hasBatch || exportStatus === "running" || ["completed", "partial", "failed"].includes(exportStatus)) {
      return "";
    }
    const files = Number(options.filesFound ?? options.imageCount ?? 0) || 0;
    const chips = [
      options.formatLabel || "",
      `${files} archivos`,
      options.readyLabel || "",
    ].filter(Boolean);
    if (options.ignoredFiles) {
      chips.push(countLabel(options.ignoredFiles, "ignorado", "ignorados"));
    }
    if (options.nonBlockingWarnings) {
      chips.push(countLabel(options.nonBlockingWarnings, "aviso", "avisos"));
    }
    return `<span class="top-status-chips">${chips.map((chip) => `<span>${escapeHtml(chip)}</span>`).join("")}</span>`;
  }

  function compactHeaderStatusText(options = {}) {
    const exportStatus = options.exportStatus || "idle";
    const batch = options.batch || "none";
    const exportableImages = Number(options.exportableImages) || 0;
    if (exportStatus === "running") {
      const total = Number(options.plannedTotal) || exportableImages;
      return options.paused ? `Pausado · ${Number(options.processed) || 0}/${total}` : `Exportando ${Number(options.processed) || 0}/${total}`;
    }
    if (exportStatus === "completed" || exportStatus === "partial") {
      const processed = Number(options.exportResultProcessed ?? options.processed ?? exportableImages);
      const total = Number(options.exportResultTotal ?? exportableImages);
      return exportStatus === "partial" ? `Exportado con avisos · ${processed}/${total}` : `Exportado · ${processed}/${total}`;
    }
    if (exportStatus === "failed") {
      return "Exportación fallida";
    }
    if (batch === "scanning") {
      return "Escaneando...";
    }
    if (batch === "none") {
      return "Sin lote";
    }
    if (batch === "empty") {
      const files = Number(options.filesFound) || 0;
      const ignored = Number(options.ignoredFiles) || 0;
      return ignored ? `${files} archivos · no hay PNG válidos · ${ignored} ignorados` : "No hay PNG válidos";
    }
    const files = Number(options.filesFound) || Number(options.imageCount) || 0;
    const parts = [
      options.formatLabel || "",
      `${files} archivos`,
      options.readyLabel || "",
    ].filter(Boolean);
    if (options.nonBlockingWarnings) {
      parts.push(countLabel(options.nonBlockingWarnings, "aviso", "avisos"));
    }
    if (options.ignoredFiles) {
      parts.push(countLabel(options.ignoredFiles, "ignorado", "ignorados"));
    }
    return parts.join(" · ");
  }

  function topStatusText(options = {}) {
    if (options.batch === "scanning") {
      return "Escaneando carpeta";
    }
    if (options.batch === "none") {
      return "Sin lote";
    }
    if (options.batch === "empty") {
      return "No hay PNG válidos";
    }
    if (options.exportStatus === "running") {
      const total = Number(options.plannedTotal) || Number(options.exportableImages) || 0;
      return options.paused ? `Pausado · ${Number(options.processed) || 0}/${total}` : `Exportando ${Number(options.processed) || 0}/${total}`;
    }
    if (options.batch === "ready") {
      return options.compactHeaderStatus || compactHeaderStatusText(options);
    }
    if (options.bridgeMode === "bridge" && options.bridgeStatus === "disconnected") {
      return "Conexión local no disponible";
    }
    return options.statusText || "";
  }

  function preflightStatusLabel(options = {}) {
    const exportStatus = options.exportStatus || "idle";
    if (exportStatus === "running") {
      return options.paused ? "Salida pausada" : "Exportando";
    }
    if (exportStatus === "completed") {
      return "Salida completada";
    }
    if (exportStatus === "partial") {
      return "Avisos";
    }
    if (exportStatus === "failed") {
      return "Revisar";
    }
    if (!options.ready && Number(options.errors) > 0) {
      return "Revisar";
    }
    if (!options.ready) {
      return "Pendiente";
    }
    const warnings = Number(options.warnings) || 0;
    if (warnings > 0) {
      return countLabel(warnings, "aviso", "avisos");
    }
    return "Listo";
  }

  function preflightStatusClass(options = {}) {
    const exportStatus = options.exportStatus || "idle";
    if (exportStatus === "failed") {
      return "error";
    }
    if (exportStatus === "running" || exportStatus === "partial") {
      return "warning";
    }
    if (!options.ready || Number(options.errors) > 0) {
      return "error";
    }
    if (Number(options.warnings) > 0) {
      return "warning";
    }
    return "ready";
  }

  return {
    compactHeaderStatusText,
    escapeHtml,
    preflightStatusClass,
    preflightStatusLabel,
    topStatusSummaryHtml,
    topStatusText,
  };
});
