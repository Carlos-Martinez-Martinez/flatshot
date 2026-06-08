(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotBatchDetailView = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

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

  function batchDetailOutputHtml(options = {}) {
    const indexLabel = `${Number(options.index) + 1 || 1}.`;
    const activeMarker = options.active ? "<em>Principal</em>" : "";
    return `
    <div class="batch-detail-output">
      <div class="batch-detail-output__title">
        <span>${escapeHtml(indexLabel)}</span>
        <strong title="${escapeHtml(options.name || "")}">${escapeHtml(options.name || "")}</strong>
        ${activeMarker}
      </div>
      <div class="batch-detail-output__meta">${escapeHtml(options.summary || "")}</div>
      ${batchDetailRowHtml("Destino", options.destination || "", options.destination || "")}
      ${batchDetailRowHtml("Ejemplo", options.example || "", options.example || "")}
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
    batchDetailOutputHtml,
    batchDetailProblemHtml,
    batchDetailRowHtml,
    escapeHtml,
    folderItemHtml,
  };
});
