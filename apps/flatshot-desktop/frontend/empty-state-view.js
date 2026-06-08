(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotEmptyStateView = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

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

  return {
    emptyStateHtml,
    escapeHtml,
  };
});
