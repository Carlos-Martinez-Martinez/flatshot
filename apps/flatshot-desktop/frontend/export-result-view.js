(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotExportResultView = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const escapeHtml = globalThis.FlatShotFormatters?.escapeHtml || function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  };

  function exportResultClass(status) {
    if (status === "failed") {
      return "error";
    }
    if (status === "partial") {
      return "warning";
    }
    if (status === "completed") {
      return "ready";
    }
    return "running";
  }

  function exportResultTitle(status, paused = false) {
    if (status === "running") {
      return paused ? "Exportación pausada" : "Exportando";
    }
    if (status === "completed") {
      return "Exportación completada";
    }
    if (status === "partial") {
      return "Completada con avisos";
    }
    if (status === "failed") {
      return "Exportación fallida";
    }
    return "Resultado";
  }

  function exportResultMeta(options = {}) {
    const status = options.status;
    const processed = Number(options.processed) || 0;
    const total = Number(options.total) || 0;
    const errors = Number(options.errors) || 0;
    if (status === "running") {
      return `${processed}/${total} imágenes`;
    }
    if (status === "completed") {
      return `${processed}/${total} exportadas`;
    }
    if (status === "partial") {
      return `${processed}/${total} exportadas · ${errors} error${errors === 1 ? "" : "es"}`;
    }
    if (status === "failed") {
      return errors ? `${errors} error${errors === 1 ? "" : "es"}` : "No completada";
    }
    return `${processed}/${total}`;
  }

  function exportIssueActionText(issue, options = {}) {
    if (!issue) {
      return "Revisa el resultado.";
    }
    if (options.existingOutput) {
      return "Ya hay archivos en destino. Cambia la carpeta o el nombre final.";
    }
    const title = issue.title || "Exportación";
    const detail = issue.detail || "Revisa el resultado.";
    return `${title} · ${detail}`;
  }

  function exportResultActionsHtml(options = {}) {
    const status = options.status;
    const issues = Array.isArray(options.issues) ? options.issues : [];
    const destinations = Array.isArray(options.destinations) ? options.destinations : [];
    const actions = [];
    if ((status === "completed" || status === "partial") && options.canOpenOutput) {
      const openLabel = destinations.length > 1 ? "Abrir carpeta principal" : "Abrir carpeta";
      actions.push(`<button type="button" data-action="open-output">${openLabel}</button>`);
      actions.push('<button type="button" data-action="copy-output-path">Copiar ruta</button>');
    }
    if (issues.length || status === "failed" || status === "partial") {
      actions.push('<button type="button" data-action="review-errors">Revisar avisos</button>');
    }
    if (status === "failed" && options.canRetry) {
      actions.push('<button type="button" class="primary" data-action="start-export">Reintentar</button>');
    }
    if (!actions.length || destinations.length > 3) {
      return destinations.length > 3
        ? `<div class="result-actions"><span>${escapeHtml(destinations.length - 3)} carpetas más</span>${actions.join("")}</div>`
        : "";
    }
    return `<div class="result-actions">${actions.join("")}</div>`;
  }

  function currentExportFileLabel(options = {}) {
    const images = Array.isArray(options.images) ? options.images : [];
    if (!images.length) {
      return options.statusText || "Preparando";
    }
    const index = Math.min(Math.max(Number(options.processed) || 0, 0), images.length - 1);
    return images[index]?.name || options.statusText || "Preparando";
  }

  function outputDestinationToOpen(options = {}) {
    const exportDestinations = Array.isArray(options.exportDestinations) ? options.exportDestinations : [];
    if (exportDestinations.length) {
      return exportDestinations[0];
    }
    const resultDestinations = Array.isArray(options.resultDestinations) ? options.resultDestinations : [];
    if (resultDestinations.length) {
      return resultDestinations[0];
    }
    return "";
  }

  function exportResultHtml(options = {}) {
    const status = options.status || "running";
    const title = options.title || exportResultTitle(status, options.paused);
    const meta = options.meta || exportResultMeta(options);
    const resultClass = options.resultClass || exportResultClass(status);
    const destinations = Array.isArray(options.destinations) ? options.destinations : [];
    const issues = Array.isArray(options.issues) ? options.issues : [];
    const items = Array.isArray(options.items) ? options.items : [];
    const errors = Number(options.errors) || 0;
    const destinationFallback = options.destinationFallback || "Pendiente";
    const actionsHtml = options.actionsHtml || "";

    const destinationHtml = destinations.length
      ? destinations.slice(0, 3).map((path) => `
      <div class="result-path" title="${escapeHtml(path)}">
        <span>Carpeta</span>
        <strong>${escapeHtml(path)}</strong>
      </div>
    `).join("")
      : `<div class="result-path muted"><span>Carpeta</span><strong>${escapeHtml(destinationFallback)}</strong></div>`;

    const currentItemHtml = status === "running" ? `
    <div class="result-path muted">
      <span>Actual</span>
      <strong title="${escapeHtml(options.currentFileLabel || "Preparando")}">${escapeHtml(options.currentFileLabel || "Preparando")}</strong>
    </div>
  ` : "";

    const issueSummary = options.issueSummary || "";
    const issuesHtml = issues.length ? `
    <div class="result-issues">
      <strong>${errors ? `${errors} error${errors === 1 ? "" : "es"}` : `${issues.length} aviso${issues.length === 1 ? "" : "s"}`}</strong>
      <span>${escapeHtml(issueSummary)}</span>
    </div>
  ` : "";

    const itemsHtml = items.length ? `
    <div class="result-items" aria-label="Archivos procesados">
      ${items.map((item) => `
        <span class="result-item ${item.success ? "ready" : "error"}" title="${escapeHtml(item.name || "Archivo")}">
          ${escapeHtml(item.name || "Archivo")}
        </span>
      `).join("")}
    </div>
  ` : "";

    return `
    <div class="result-header ${resultClass}">
      <strong>${escapeHtml(title)}</strong>
      <span>${escapeHtml(meta)}</span>
    </div>
    ${destinationHtml}
    ${currentItemHtml}
    ${issuesHtml}
    ${itemsHtml}
    ${actionsHtml}
  `;
  }

  return {
    escapeHtml,
    currentExportFileLabel,
    exportIssueActionText,
    exportResultActionsHtml,
    exportResultClass,
    exportResultHtml,
    exportResultMeta,
    exportResultTitle,
    outputDestinationToOpen,
  };
});
