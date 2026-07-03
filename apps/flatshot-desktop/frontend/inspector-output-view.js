(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotInspectorOutputView = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const escapeHtml = globalThis.FlatShotFormatters?.escapeHtml || function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  };

  function outputProfileInlineRowHtml(row = {}) {
    const active = Boolean(row.active);
    const enabled = Boolean(row.enabled);
    const canToggle = Boolean(row.canToggle);
    const selectable = enabled && canToggle;
    const summary = row.summary || "";
    const destinationLabel = String(row.destinationLabel || "").trim();
    const destinationText = destinationLabel ? `Destino · ${destinationLabel}` : "";
    const editLabel = `Editar formato ${row.name || ""}`.trim();
    const mainContent = `
        <span class="active-output-row__title">
          <strong>${escapeHtml(row.name)}</strong>
        </span>
        <small>${escapeHtml(summary)}</small>
        ${destinationText ? `<small>${escapeHtml(destinationText)}</small>` : ""}
    `;
    const title = [row.name, summary, destinationText].filter(Boolean).join(" · ");
    const mainHtml = selectable
      ? `<button type="button" class="active-output-row__main" data-action="select-output-profile" data-output-profile-id="${escapeHtml(row.id)}" aria-pressed="${active ? "true" : "false"}" title="${escapeHtml(`Seleccionar ${row.name} para previsualizar`)}">${mainContent}</button>`
      : `<div class="active-output-row__main" title="${escapeHtml(title)}">${mainContent}</div>`;
    return `
    <div class="active-output-row${active ? " is-current" : ""}${enabled ? " is-enabled" : " is-disabled"}">
      <label class="output-toggle" title="${escapeHtml(canToggle ? "Activar o desactivar formato" : "Guarda el formato para activarlo")}">
        <input type="checkbox" data-output-profile-enabled-id="${escapeHtml(row.id)}" ${enabled ? "checked" : ""} ${canToggle ? "" : "disabled"} />
        <span></span>
      </label>
      ${mainHtml}
      <button type="button" class="active-output-row__edit" data-action="edit-output-profile" data-output-profile-id="${escapeHtml(row.id)}" aria-label="${escapeHtml(editLabel)}" title="${escapeHtml(editLabel)}">
        <span class="button-icon" aria-hidden="true"><svg viewBox="0 0 24 24" focusable="false"><path d="M12 20h9"></path><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"></path></svg></span>
        <span class="visually-hidden">Editar formato</span>
      </button>
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
    const noteLabel = totalFiles
      ? ""
      : activeCount
        ? "Pendiente de lote"
        : "Selecciona al menos un formato";
    return `
    <section class="inspector-output-card panel-summary-card">
      <header class="inspector-output-card__head">
        <div>
          <span>${escapeHtml("Exportación")}</span>
          <strong>${escapeHtml(countLabel)}</strong>
        </div>
        ${noteLabel ? `<em class="inspector-output-card__note">${escapeHtml(noteLabel)}</em>` : ""}
      </header>
      <div class="active-output-list" aria-label="Formatos activos del lote">
        ${rows.map(outputProfileInlineRowHtml).join("")}
      </div>
      ${options.dirty ? outputTemporaryNoticeHtml() : ""}
      <div class="inspector-output-card__actions">
        <button type="button" data-action="open-app-settings">Gestionar formatos</button>
        <button type="button" data-action="new-output-profile">Nuevo formato</button>
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
