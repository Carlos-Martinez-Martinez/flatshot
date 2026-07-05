(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotTopStatusView = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const formatterHelpers = globalThis.FlatShotFormatters
    || (typeof require === "function" ? require("./formatters.js") : null);
  const escapeHtml = (value) => formatterHelpers.escapeHtml(value);

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
      return options.hasOutputBlocker ? "Revisar salida" : "Exportación fallida";
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
      return options.paused ? "Exportación pausada" : "Exportando";
    }
    if (exportStatus === "completed") {
      return "Exportación completada";
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

  function topPrimaryHint(options = {}) {
    const primaryAction = options.primaryAction || {};
    const action = primaryAction.action || "";
    if (action === "start-export") {
      return `${primaryAction.label}. Atajo: Ctrl+E`;
    }
    if (action === "quick-export") {
      return `${primaryAction.label} con la salida activa. Atajo: Ctrl+Shift+E`;
    }
    if (action === "pick-bridge-folder") {
      return "Seleccionar carpeta de entrada";
    }
    if (action === "review-warnings") {
      return "Revisar avisos del lote";
    }
    if (action === "edit-output") {
      return "Corregir destino, sufijo o nombre de salida";
    }
    if (action === "browse-outputs") {
      return "Ver salidas exportadas";
    }
    if (action === "open-output") {
      return "Abrir carpeta de salida";
    }
    return primaryAction.label || options.title;
  }

  function statusMode(options = {}) {
    if (options.batch === "none" && options.bridgeStatus === "idle") {
      return "";
    }
    if (options.exportStatus === "failed" || options.previewStatus === "error" || options.hasScanError) {
      return "error";
    }
    if (options.exportStatus === "running" || options.previewStatus === "loading" || options.batch === "scanning") {
      return "busy";
    }
    if (options.bridgeMode === "bridge" && options.bridgeStatus !== "connected") {
      return "busy";
    }
    if (options.exportStatus === "partial" || options.previewStatus === "warning" || options.hasValidationIssues) {
      return "busy";
    }
    return "ready";
  }

  function statusBarText(options = {}) {
    const exportStatus = options.exportStatus || "idle";
    const batch = options.batch || "none";
    const counts = options.counts || {};
    const imageCount = Number(options.imageCount) || 0;
    const selectedIndex = Number(options.selectedIndex);
    const selectedText = selectedIndex >= 0 ? `Imagen ${selectedIndex + 1}/${imageCount}` : "Sin selección";
    const destination = Number(options.outputCount) > 1
      ? countLabel(options.outputCount, "salida", "salidas")
      : options.destinationMode === "custom"
        ? (options.destinationValue ? formatterHelpers.displayPath(options.destinationValue) : "sin destino")
        : `origen / ${options.destinationValue}`;

    if (exportStatus === "running") {
      const total = Number(options.plannedTotal) || Number(options.exportableImageCount) || 0;
      return `${options.paused ? "Pausado" : "Exportando"} ${Number(options.processed) || 0}/${total} · ${options.statusText || ""}`;
    }
    if (exportStatus === "completed") {
      const total = Number(options.exportResultTotal ?? options.exportableImageCount ?? 0);
      const processed = Number(options.exportResultProcessed ?? total);
      return `Última exportación completada · ${processed}/${total} archivos`;
    }
    if (exportStatus === "partial") {
      const total = Number(options.exportResultTotal ?? options.exportableImageCount ?? 0);
      const processed = Number(options.exportResultProcessed ?? options.processed ?? 0);
      return `Última exportación con avisos · ${processed}/${total} archivos`;
    }
    if (exportStatus === "failed") {
      return `${options.hasOutputBlocker ? "Revisa salida" : "Exportación fallida"} · ${options.firstErrorDetail || "Revisa avisos"}`;
    }
    if (batch === "none") {
      return "Sin lote · Elige una carpeta para empezar";
    }
    if (batch === "scanning") {
      return `Escaneando · ${options.scanStatus || ""}`;
    }
    if (batch === "empty") {
      return `0 imágenes · ${options.scanStatus || "Cambia de carpeta"}`;
    }

    const warnings = Number(counts.nonBlockingWarnings) || 0;
    const warningText = warnings ? ` · ${countLabel(warnings, "aviso", "avisos")}` : "";
    return `${Number(counts.exportableImages) || 0} exportables · ${selectedText}${warningText} · Salida: ${destination}`;
  }

  return {
    compactHeaderStatusText,
    escapeHtml,
    preflightStatusClass,
    preflightStatusLabel,
    statusMode,
    statusBarText,
    topPrimaryHint,
    topStatusSummaryHtml,
    topStatusText,
  };
});
