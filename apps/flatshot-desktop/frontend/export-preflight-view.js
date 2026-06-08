(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotExportPreflightView = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function issueItemHtml(row = {}) {
    const action = row.imageId
      ? `<button type="button" data-action="select-image-id" data-image-id="${escapeHtml(row.imageId)}">${escapeHtml(row.actionLabel || "Ir a imagen")}</button>`
      : "";
    return `
    <div class="issue-item ${row.level === "error" ? "error" : row.level === "info" || row.level === "ignored" ? "clear" : "warning"}" title="${escapeHtml(row.path || row.detail || row.title)}">
      <div>
        <strong>${escapeHtml(row.title)}</strong>
        <span>${escapeHtml(row.detail || "Revisar")}</span>
      </div>
      ${action}
    </div>
  `;
  }

  function progressPanelHtml(label, value = null) {
    const valueHtml = value === null ? "" : `<strong>${escapeHtml(Math.round(value))}%</strong>`;
    return `
    <div class="context-progress${value === null ? " is-indeterminate" : ""}">
      <span>${escapeHtml(label)}</span>
      ${valueHtml}
    </div>
  `;
  }

  function outputWarningSummaryHtml(options = {}) {
    const issues = Array.isArray(options.issues) ? options.issues : [];
    const warnings = issues.filter((issue) => issue.title !== "Sin lote");
    if (!warnings.length) {
      return "";
    }
    const hasBlocking = warnings.some((issue) => issue.level === "error");
    if (!hasBlocking) {
      return "";
    }
    const first = options.firstIssue || warnings[0];
    const count = Math.max(warnings.length, Number(options.visibleWarningCount) || 0);
    const fileLine = first.file ? `<span title="${escapeHtml(first.path || first.file)}">${escapeHtml(first.file)}</span>` : "";
    const detail = first.file ? `Motivo: ${first.detail}` : `${first.title}${first.detail ? `: ${first.detail}` : ""}`;
    return `
    <div class="warning-summary ${warnings.some((issue) => issue.level === "error") ? "error" : ""}">
      <strong>${count} aviso${count === 1 ? "" : "s"}</strong>
      ${fileLine}
      <span>${escapeHtml(detail)}</span>
      <button type="button" data-action="review-errors">Revisar aviso</button>
    </div>
  `;
  }

  function issueListHtml(options = {}) {
    const hasActiveBatch = Boolean(options.hasActiveBatch);
    const batch = options.batch || "none";
    if (!hasActiveBatch && batch !== "empty") {
      return "";
    }

    const rows = Array.isArray(options.rows) ? options.rows : [];
    const counts = options.counts || { errors: 0 };
    const warningCount = Number(options.warningCount) || 0;
    const onlyIgnored = rows.length > 0 && warningCount === 0 && Number(counts.errors) === 0;
    const footerAction = counts.errors
      ? '<button type="button" class="primary" data-action="edit-output">Revisar salida</button>'
      : "";

    if (!rows.length) {
      return `
      <div class="issue-list-summary ready issue-list-summary--compact">
        <strong>Sin avisos</strong>
      </div>
    `;
    }

    const summaryText = counts.errors
      ? `${counts.errors} bloqueo${counts.errors === 1 ? "" : "s"}`
      : onlyIgnored
        ? `${rows.length} ignorado${rows.length === 1 ? "" : "s"}`
        : `${warningCount || rows.length} aviso${(warningCount || rows.length) === 1 ? "" : "s"}`;
    const detailText = counts.errors
      ? "Resuelve los bloqueos antes de exportar."
      : onlyIgnored
        ? "No afectan a la exportación."
        : "Puedes revisar sin bloquear la exportación.";

    return `
    <div class="issue-list-summary ${counts.errors ? "error" : onlyIgnored ? "clear" : "warning"}">
      <strong>${escapeHtml(summaryText)}</strong>
      <span>${escapeHtml(detailText)}</span>
    </div>
    ${rows.slice(0, 8).map(issueItemHtml).join("")}
    ${footerAction ? `<div class="inspector-actionbar warning-actions">${footerAction}</div>` : ""}
  `;
  }

  function preflightListHtml(rows = []) {
    return `
    <div class="preflight-list">
      ${rows.map((row) => `
        <div class="preflight-item ${escapeHtml(row.state)}">
          <span aria-hidden="true"></span>
          <div>
            <strong>${escapeHtml(row.title)}</strong>
            <small title="${escapeHtml(row.detail)}">${escapeHtml(row.detail)}</small>
          </div>
        </div>
      `).join("")}
    </div>
  `;
  }

  function exportPanelStatusLabel(options = {}) {
    const status = options.status || "idle";
    const issues = Array.isArray(options.issues) ? options.issues : [];
    const ready = Boolean(options.ready);
    if (status === "running") {
      return options.paused ? "Pausado" : "Exportando";
    }
    if (status === "completed") {
      return "Exportado";
    }
    if (status === "partial") {
      return "Exportado con avisos";
    }
    if (status === "failed") {
      return "Revisar antes de exportar";
    }
    if (issues.some((issue) => issue.level === "error")) {
      return "Revisar antes de exportar";
    }
    if (options.batch === "empty" || (options.hasActiveBatch && !ready)) {
      return "Pendiente";
    }
    if (ready && issues.length) {
      return `${issues.length} aviso${issues.length === 1 ? "" : "s"} antes de exportar`;
    }
    return ready ? "Listo para exportar" : "Configura salida";
  }

  function exportPreflightSummary(options = {}) {
    const issues = Array.isArray(options.issues) ? options.issues : [];
    const exportable = Number(options.exportable) || 0;
    const ready = Boolean(options.ready);
    const errors = issues.filter((issue) => issue.level === "error").length;
    const warnings = issues.length - errors;
    if (errors) {
      return `${errors} bloqueo${errors === 1 ? "" : "s"} · ${exportable} exportables`;
    }
    if (warnings) {
      return `${warnings} aviso${warnings === 1 ? "" : "s"} · ${exportable} exportables`;
    }
    return ready ? `${exportable} imágenes listas` : "Pendiente";
  }

  return {
    escapeHtml,
    exportPanelStatusLabel,
    exportPreflightSummary,
    issueItemHtml,
    issueListHtml,
    outputWarningSummaryHtml,
    preflightListHtml,
    progressPanelHtml,
  };
});
