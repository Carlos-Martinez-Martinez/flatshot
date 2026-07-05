(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotExportHistory = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const DEFAULT_LIMIT = 8;

  const formatterHelpers = globalThis.FlatShotFormatters
    || (typeof require === "function" ? require("./formatters.js") : null);
  const escapeHtml = (value) => formatterHelpers.escapeHtml(value);

  function readExportHistory(storage, key) {
    try {
      const raw = storage.getItem(key);
      const entries = raw ? JSON.parse(raw) : [];
      return Array.isArray(entries)
        ? entries.map(normalizeExportHistoryEntry).filter((entry) => entry.id)
        : [];
    } catch (error) {
      return [];
    }
  }

  function rememberExportHistory(storage, key, options = {}) {
    const limit = Math.max(1, Number(options.limit) || DEFAULT_LIMIT);
    const entry = normalizeExportHistoryEntry(options);
    if (!entry.id) {
      return readExportHistory(storage, key);
    }
    const next = [
      entry,
      ...readExportHistory(storage, key).filter((item) => item.id !== entry.id),
    ].slice(0, limit);
    try {
      storage.setItem(key, JSON.stringify(next));
    } catch (error) {
      // Export history is convenience state; exporting must not depend on storage.
    }
    return next;
  }

  function normalizeExportHistoryEntry(entry = {}) {
    const status = ["completed", "partial", "failed"].includes(entry.status) ? entry.status : "failed";
    const completedAt = String(entry.completedAt || entry.now || new Date().toISOString());
    const processed = Math.max(0, Number(entry.processed) || 0);
    const total = Math.max(processed, Number(entry.total) || 0);
    const errors = Math.max(0, Number(entry.errors) || 0);
    return {
      id: String(entry.id || `${completedAt}-${status}-${processed}-${total}`),
      completedAt,
      status,
      processed,
      total,
      errors,
      destinations: uniqueStrings(entry.destinations).slice(0, 4),
      presetName: String(entry.presetName || ""),
      outputProfileName: String(entry.outputProfileName || ""),
    };
  }

  function uniqueStrings(values) {
    const seen = new Set();
    return (Array.isArray(values) ? values : [])
      .map((value) => String(value || "").trim())
      .filter((value) => {
        if (!value || seen.has(value)) {
          return false;
        }
        seen.add(value);
        return true;
      });
  }

  function exportHistoryStatusLabel(entry = {}) {
    if (entry.status === "completed") {
      return "Completada";
    }
    if (entry.status === "partial") {
      return "Con avisos";
    }
    return "Fallida";
  }

  function exportHistoryMeta(entry = {}) {
    const date = String(entry.completedAt || "").slice(0, 10) || "Sin fecha";
    const processed = Number(entry.processed) || 0;
    const total = Number(entry.total) || 0;
    const errors = Number(entry.errors) || 0;
    const errorText = errors ? ` · ${errors} error${errors === 1 ? "" : "es"}` : "";
    return `${date} · ${processed}/${total}${errorText}`;
  }

  function exportHistoryHtml(entries = []) {
    const items = (Array.isArray(entries) ? entries : []).slice(0, 3);
    if (!items.length) {
      return "";
    }
    return `
      <section class="export-history" aria-label="Historial de exportaciones">
        <div class="export-history__title">Historial</div>
        ${items.map((entry) => exportHistoryItemHtml(entry)).join("")}
      </section>
    `;
  }

  function exportHistoryItemHtml(entry = {}) {
    const label = exportHistoryStatusLabel(entry);
    const destination = entry.destinations?.[0] || "Sin destino registrado";
    const descriptor = [entry.outputProfileName, entry.presetName].filter(Boolean).join(" · ") || label;
    return `
      <article class="export-history__item ${escapeHtml(entry.status || "failed")}">
        <div>
          <strong>${escapeHtml(descriptor)}</strong>
          <span>${escapeHtml(exportHistoryMeta(entry))}</span>
        </div>
        <span class="export-history__status">${escapeHtml(label)}</span>
        <small title="${escapeHtml(destination)}">${escapeHtml(destination)}</small>
      </article>
    `;
  }

  return {
    exportHistoryHtml,
    exportHistoryMeta,
    exportHistoryStatusLabel,
    normalizeExportHistoryEntry,
    readExportHistory,
    rememberExportHistory,
  };
});
