(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotExportSummaryView = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const formatterHelpers = globalThis.FlatShotFormatters
    || (typeof require === "function" ? require("./formatters.js") : null);
  const escapeHtml = (value) => formatterHelpers.escapeHtml(value);

  function exportEditActionsHtml() {
    return `
    <div class="inspector-actionbar output-edit-actions">
      <button type="button" data-action="cancel-output-edit">Cancelar</button>
      <button type="button" class="primary" data-action="apply-output-edit">Aplicar al lote sin guardar</button>
      <button type="button" data-action="save-output-current-profile">Guardar salida</button>
      <button type="button" data-action="save-output-as-new">Guardar como nuevo</button>
      <button type="button" class="btn-linklike" data-action="open-app-settings">Gestionar salidas</button>
    </div>
  `;
  }

  function exportPresetActionsHtml() {
    return `
    <div class="inspector-actionbar">
      <button type="button" class="primary" data-action="open-app-settings">Gestionar salidas</button>
      <button type="button" data-action="new-output-profile">Nueva salida</button>
    </div>
  `;
  }

  function outputTemporaryNoticeHtml({ compact = false } = {}) {
    return `
    <div class="temporary-output-notice${compact ? " temporary-output-notice--compact" : ""}">
      <strong>Cambios sin guardar</strong>
      <span>${compact ? "Aplica al lote o guarda la salida." : "La salida actual no coincide con una salida guardada."}</span>
    </div>
  `;
  }

  function profileSummaryRowsHtml(rows = [], totalProfiles = rows.length) {
    const visibleRows = rows.slice(0, 4).map((profile) => {
      const size = profile.size || "";
      const title = `${profile.name || ""} · ${size} · ${profile.destinationLabel || ""}`;
      return `
      <div class="preset-summary-row">
        <span>${escapeHtml(profile.format || "")}</span>
        <strong title="${escapeHtml(title)}">${escapeHtml(`${profile.name || ""} · ${size.replace("x", " × ")}`)}</strong>
      </div>
    `;
    }).join("");
    const extraCount = totalProfiles - 4;
    const extraRows = extraCount > 0
      ? `<div class="preset-summary-row"><span>Más</span><strong>${escapeHtml(`${extraCount} salida${extraCount === 1 ? "" : "s"} más`)}</strong></div>`
      : "";
    return `${visibleRows}${extraRows}`;
  }

  function outputProfileSelectOptionsHtml(profiles = [], options = {}) {
    const customOption = options.includeCustom
      ? '<option value="__custom">Personalizado sin guardar</option>'
      : "";
    return `
    ${profiles.map((profile) => `
      <option value="${escapeHtml(profile.id)}">${escapeHtml(profile.name)}</option>
    `).join("")}
    ${customOption}
  `;
  }

  function exportEditSummaryHtml(options = {}) {
    return `
    <div class="compact-panel">
      <div>
        <span>Salida</span>
        <strong>${escapeHtml(options.displayName || "")}</strong>
      </div>
      <small>${escapeHtml(options.presetSummary || "")}</small>
    </div>
    ${options.editDirty ? outputTemporaryNoticeHtml({ compact: true }) : ""}
    ${exportEditActionsHtml()}
  `;
  }

  function exportPresetSummaryHtml(options = {}) {
    const activeOutputCount = Number(options.activeOutputCount) || 0;
    const hasMultipleOutputs = activeOutputCount > 1;
    const profileRows = Array.isArray(options.profileRows) ? options.profileRows : [];
    const outputCount = Number(options.outputCount) || 0;
    const temporaryNoticeHtml = options.temporaryNoticeHtml || "";
    const warningSummaryHtml = options.warningSummaryHtml || "";
    return `
    <div class="preset-summary-card">
      <div class="preset-summary-main">
        <span>${escapeHtml(hasMultipleOutputs ? "Salidas activas" : "Salida activa")}</span>
        <strong>${escapeHtml(options.displayName || "")}</strong>
        ${hasMultipleOutputs ? `<small>${escapeHtml(`${outputCount} archivos previstos`)}</small>` : ""}
      </div>
      ${hasMultipleOutputs ? profileSummaryRowsHtml(profileRows, activeOutputCount) : ""}
      <div class="preset-summary-row">
        <span>Formato</span>
        <strong>${escapeHtml(options.formatLabel || "")}</strong>
      </div>
      <div class="preset-summary-row">
        <span>Tamaño</span>
        <strong>${escapeHtml(options.sizeLabel || "")}</strong>
      </div>
      <div class="preset-summary-row">
        <span>Fondo</span>
        <strong>${escapeHtml(options.backgroundLabel || "")}</strong>
      </div>
      <div class="preset-summary-row">
        <span>Destino</span>
        <strong title="${escapeHtml(options.destinationText || "")}">${escapeHtml(formatterHelpers.displayPath(options.destinationText))}</strong>
      </div>
      <div class="preset-summary-row">
        <span>Nombre final</span>
        <strong>${escapeHtml(options.namingLabel || "")}</strong>
      </div>
      <div class="preset-summary-row">
        <span>Ejemplo</span>
        <strong title="${escapeHtml(options.example || "")}">${escapeHtml(options.example || "")}</strong>
      </div>
    </div>
    ${warningSummaryHtml}
    ${temporaryNoticeHtml}
    ${exportPresetActionsHtml()}
  `;
  }

  function exportSummaryHtml(options = {}) {
    if (options.editing) {
      return exportEditSummaryHtml(options);
    }
    return exportPresetSummaryHtml(options);
  }

  return {
    escapeHtml,
    exportEditActionsHtml,
    exportPresetActionsHtml,
    exportSummaryHtml,
    outputTemporaryNoticeHtml,
    outputProfileSelectOptionsHtml,
    profileSummaryRowsHtml,
  };
});
