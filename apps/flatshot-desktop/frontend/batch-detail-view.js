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
    batchDetailRowHtml,
    escapeHtml,
    folderItemHtml,
  };
});
