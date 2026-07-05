(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotBatchDetailView = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const formatterHelpers = globalThis.FlatShotFormatters
    || (typeof require === "function" ? require("./formatters.js") : null);
  const escapeHtml = (value) => formatterHelpers.escapeHtml(value);

  function batchDetailRowHtml(label, value, title = "") {
    const text = value === null || value === undefined || value === "" ? "Pendiente" : String(value);
    return `
    <div class="batch-detail-row">
      <span>${escapeHtml(label)}</span>
      <strong title="${escapeHtml(title || text)}">${escapeHtml(text)}</strong>
    </div>
  `;
  }

  function batchDetailProblemHtml(options = {}) {
    const tone = options.tone ? ` ${options.tone}` : "";
    const title = options.title || "";
    const detail = options.detail || "";
    return `
    <div class="batch-detail-problem${tone}">
      <strong title="${escapeHtml(options.titleAttr || title)}">${escapeHtml(title)}</strong>
      <span>${escapeHtml(detail)}</span>
    </div>
  `;
  }

  function batchDetailMetricHtml(label, value, title = "") {
    const text = value === null || value === undefined || value === "" ? "Pendiente" : String(value);
    return `
    <div class="batch-detail-metric">
      <span>${escapeHtml(label)}</span>
      <strong title="${escapeHtml(title || text)}">${escapeHtml(text)}</strong>
    </div>
  `;
  }

  function batchDetailOutputHtml(options = {}) {
    const indexLabel = `${Number(options.index) + 1 || 1}.`;
    return `
    <div class="batch-detail-output">
      <div class="batch-detail-output__main">
        <div class="batch-detail-output__title">
          <span>${escapeHtml(indexLabel)}</span>
          <strong title="${escapeHtml(options.name || "")}">${escapeHtml(options.name || "")}</strong>
        </div>
        <div class="batch-detail-output__meta">${escapeHtml(options.summary || "")}</div>
      </div>
      <div class="batch-detail-output__details">
        ${batchDetailRowHtml("Destino", options.destination || "", options.destination || "")}
        ${batchDetailRowHtml("Ejemplo", options.example || "", options.example || "")}
      </div>
    </div>
  `;
  }

  function batchDetailIgnoredSectionHtml(options = {}) {
    if (!options.rowsHtml) {
      return "";
    }
    const count = Number(options.count) || 0;
    const countLabel = `${count} archivo${count === 1 ? "" : "s"}`;
    return `
    <details class="batch-detail-section batch-detail-section--collapsed">
      <summary>
        <h3>Ignorados técnicos</h3>
        <span>${escapeHtml(countLabel)}</span>
      </summary>
      <div class="batch-detail-reasons">
        ${options.rowsHtml}
      </div>
    </details>
  `;
  }

  function batchDetailGridHtml(options = {}) {
    const counts = options.counts || {};
    const secondaryClass = options.ignoredSectionHtml ? "" : " batch-detail-secondary--single";
    return `
    <div class="batch-detail-grid batch-detail-grid--compact">
      <section class="batch-detail-overview" aria-label="Resumen del lote">
        ${batchDetailMetricHtml("Encontrados", options.files)}
        ${batchDetailMetricHtml("Exportables", counts.exportableImages)}
        ${batchDetailMetricHtml("Imágenes", options.valid)}
        ${batchDetailMetricHtml("Ignorados", counts.ignoredFiles)}
        ${batchDetailMetricHtml("Incidencias", options.issueCount)}
      </section>

      <section class="batch-detail-section batch-detail-section--input">
        <h3>Entrada</h3>
        ${batchDetailRowHtml("Carpeta", options.sourceFolderName, options.sourcePath)}
        ${batchDetailRowHtml("Ruta", options.sourcePath || "Pendiente", options.sourcePath)}
        ${batchDetailRowHtml("Imágenes", options.valid)}
        ${batchDetailRowHtml("Estado", options.stateTitle)}
      </section>

      <section class="batch-detail-section batch-detail-section--outputs">
        <h3>Salidas activas</h3>
        ${options.outputRowsHtml || '<span class="batch-detail-muted">Sin salidas activas.</span>'}
      </section>

      <div class="batch-detail-secondary${secondaryClass}">
        ${options.ignoredSectionHtml || ""}
        <section class="batch-detail-section batch-detail-section--issues">
          <h3>Incidencias</h3>
          ${options.issueRowsHtml || '<span class="batch-detail-muted">Sin incidencias.</span>'}
        </section>
      </div>
    </div>
  `;
  }

  function folderItemHtml(folder) {
    const className = folder.status === "warning" ? "empty" : folder.status === "error" ? "error" : folder.status || "";
    return `
    <div class="folder-item ${className}" title="${escapeHtml(folder.path || folder.detail)}">
      <div>
        <strong>${escapeHtml(folder.name)}</strong>
        <small>${escapeHtml(folder.detail)}</small>
      </div>
      <span class="state-chip ${folder.status === "warning" ? "warning" : folder.status === "error" ? "error" : ""}">
        ${escapeHtml(folder.count)}
      </span>
    </div>
  `;
  }

  return {
    batchDetailGridHtml,
    batchDetailIgnoredSectionHtml,
    batchDetailOutputHtml,
    batchDetailProblemHtml,
    batchDetailRowHtml,
    escapeHtml,
    folderItemHtml,
  };
});
