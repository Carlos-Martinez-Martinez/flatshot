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
      <label class="output-toggle" title="${escapeHtml(canToggle ? "Activar o desactivar salida" : "Debe quedar al menos una salida activa")}">
        <input type="checkbox" data-output-profile-enabled-id="${escapeHtml(row.id)}" ${enabled ? "checked" : ""} ${canToggle ? "" : "disabled"} />
        <span></span>
      </label>
      <button type="button" class="active-output-row__main" data-action="select-output-profile" data-output-profile-id="${escapeHtml(row.id)}" title="${escapeHtml(`${row.name} · ${summary}`)}">
        <strong>${escapeHtml(row.name)}</strong>
        <small>${escapeHtml(summary)}</small>
      </button>
      <span class="active-output-row__tag">${escapeHtml(active ? "Principal" : "")}</span>
    </div>
  `;
  }

  function outputTemporaryNoticeHtml() {
    return `
    <div class="temporary-output-notice">
      <strong>Cambios temporales en esta salida</strong>
      <div>
        <button type="button" data-action="save-output-current-profile">Guardar en preset</button>
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
    const readyLabel = options.readyLabel || "Sin imágenes listas";
    return `
    <section class="inspector-output-card">
      <div class="inspector-output-card__head">
        <span>${escapeHtml(`Salidas activas · ${activeCount}`)}</span>
        <strong>${escapeHtml(totalFiles ? `${totalFiles} archivos previstos` : "Pendiente de lote")}</strong>
        <small>${escapeHtml(readyLabel)}</small>
      </div>
      <div class="active-output-list" aria-label="Salidas del lote">
        ${rows.map(outputProfileInlineRowHtml).join("")}
      </div>
      ${options.dirty ? outputTemporaryNoticeHtml() : ""}
      <div class="inspector-output-card__actions">
        <button type="button" class="primary" data-action="edit-output">Editar salidas</button>
        <button type="button" data-action="open-app-settings">Gestionar presets</button>
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
