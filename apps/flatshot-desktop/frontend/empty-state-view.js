(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotEmptyStateView = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const escapeHtml = globalThis.FlatShotFormatters?.escapeHtml || function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  };

  function emptyStateHtml({ variant = "inline", title, detail, actionLabel = "", action = "", meta = "" }) {
    const actionHtml = actionLabel && action
      ? `<button type="button" class="primary" data-action="${escapeHtml(action)}">${escapeHtml(actionLabel)}</button>`
      : "";
    const metaHtml = meta ? `<small>${escapeHtml(meta)}</small>` : "";
    return `
    <div class="empty-state ${escapeHtml(variant)}">
      <span class="empty-icon" aria-hidden="true"></span>
      <strong>${escapeHtml(title)}</strong>
      <span>${escapeHtml(detail)}</span>
      ${actionHtml}
      ${metaHtml}
    </div>
  `;
  }

  function initialStateHtml(options = {}) {
    const qaLabActionHtml = options.devMode
      ? `<button type="button" class="ghost-action dev-only" data-action="open-qa-lab">QA Lab</button>`
      : "";
    const folderEntryHtml = `
      <div class="folder-entry-inline" aria-label="Carpeta de entrada">
        <label class="text-field">
          <span>Carpeta de entrada</span>
          <input id="onboarding-scan-path" type="text" value="${escapeHtml(options.bridgeScanPath || "")}" placeholder="C:/ruta/lote" autocomplete="off" spellcheck="false" />
        </label>
        <button type="button" class="folder-entry-inline__scan primary" data-action="scan-bridge-folder">Escanear</button>
      </div>
  `;
    return `
    <div class="empty-state onboarding initial-onboarding">
      <span class="empty-icon" aria-hidden="true">
        <svg viewBox="0 0 24 24" focusable="false">
          <path d="M3 6.75A2.75 2.75 0 0 1 5.75 4h4.08c.73 0 1.42.34 1.86.92l.82 1.08h5.74A2.75 2.75 0 0 1 21 8.75v.75H7.18a2.75 2.75 0 0 0-2.63 1.96L3 16.65Z"></path>
          <path d="M4.1 18.9A2.75 2.75 0 0 0 6.72 21h10.74a2.75 2.75 0 0 0 2.66-2.05l1.63-6.15A1.75 1.75 0 0 0 20.06 10H7.18c-.79 0-1.48.52-1.69 1.28Z"></path>
        </svg>
      </span>
      <strong>Selecciona una carpeta</strong>
      <span>Carga un lote de imágenes PNG o JPG para revisar y exportar.</span>
      <div class="empty-state__actions">
        <button type="button" class="ghost-action" data-action="pick-bridge-folder">Seleccionar carpeta</button>
        <button type="button" class="ghost-action" data-action="open-app-settings">Gestionar formatos</button>
        ${qaLabActionHtml}
      </div>
      ${folderEntryHtml}
    </div>
  `;
  }

  return {
    emptyStateHtml,
    escapeHtml,
    initialStateHtml,
  };
});
