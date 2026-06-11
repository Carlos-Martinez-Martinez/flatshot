(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotInspectorOutputView = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function outputProfileInlineRowHtml(row = {}) {
    const active = Boolean(row.active);
    const enabled = Boolean(row.enabled);
    const canToggle = Boolean(row.canToggle);
    const summary = row.summary || "";
    return `
    <div class="active-output-row${active ? " is-primary" : ""}${enabled ? " is-enabled" : " is-disabled"}">
      <label class="output-toggle" title="${escapeHtml(canToggle ? "Activar o desactivar formato" : "Guarda el formato para activarlo")}">
        <input type="checkbox" data-output-profile-enabled-id="${escapeHtml(row.id)}" ${enabled ? "checked" : ""} ${canToggle ? "" : "disabled"} />
        <span></span>
      </label>
      <button type="button" class="active-output-row__main" data-action="select-output-profile" data-output-profile-id="${escapeHtml(row.id)}" title="${escapeHtml(`${row.name} · ${summary}`)}">
        <strong>${escapeHtml(row.name)}</strong>
        <small>${escapeHtml(summary)}</small>
      </button>
      ${active ? '<span class="active-output-row__tag">Principal</span>' : ""}
    </div>
  `;
  }

  function outputTemporaryNoticeHtml() {
    return `
    <div class="temporary-output-notice">
      <strong>Cambios sin guardar en este formato</strong>
      <div>
        <button type="button" data-action="save-output-current-profile">Guardar formato</button>
        <button type="button" data-action="save-output-as-new">Guardar como nuevo</button>
        <button type="button" data-action="discard-output-overrides">Descartar</button>
      </div>
    </div>
  `;
  }

  function outputInspectorCardHtml(options = {}) {
    const rows = Array.isArray(options.rows) ? options.rows : [];
    const activeCount = Number(options.activeCount) || 0;
    const totalFiles = Number(options.totalFiles) || 0;
    const countLabel = activeCount === 1 ? "1 formato activo" : `${activeCount} formatos activos`;
    const totalLabel = totalFiles
      ? `${escapeHtml(options.formulaLabel || `${totalFiles} archivos previstos`)}`
      : activeCount
        ? "Pendiente de lote"
        : "Selecciona al menos un formato";
    return `
    <section class="inspector-output-card panel-summary-card">
      <div class="inspector-output-card__head">
        <div>
          <span>${escapeHtml("Exportación")}</span>
          <strong>${escapeHtml(countLabel)}</strong>
        </div>
        <small>${totalLabel}</small>
      </div>
      <div class="active-output-list" aria-label="Formatos activos del lote">
        ${rows.map(outputProfileInlineRowHtml).join("")}
      </div>
      ${options.dirty ? outputTemporaryNoticeHtml() : ""}
      <div class="inspector-output-card__actions">
        <button type="button" data-action="open-app-settings">Formatos</button>
        <button type="button" data-action="new-output-profile">Nuevo</button>
      </div>
    </section>
  `;
  }

  return {
    escapeHtml,
    outputInspectorCardHtml,
    outputProfileInlineRowHtml,
    outputTemporaryNoticeHtml,
  };
});
