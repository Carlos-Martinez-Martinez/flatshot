(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotInspectorReviewView = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function lotInspectorSummaryHtml(options = {}) {
    const counts = options.counts || {};
    const stateLabel = options.stateLabel || "Listo";
    return `
    <div class="lot-summary-card">
      <div class="lot-summary-card__head">
        <span>Lote</span>
        <strong>${escapeHtml(stateLabel)}</strong>
      </div>
      <div class="lot-summary-card__grid">
        <span><em>Listas</em><strong>${escapeHtml(counts.readyImages || 0)}</strong></span>
        <span><em>Exportables</em><strong>${escapeHtml(counts.exportableImages || 0)}</strong></span>
        <span><em>Excluidas</em><strong>${escapeHtml(counts.nonExportableImages || 0)}</strong></span>
        <span><em>Ignorados</em><strong>${escapeHtml(counts.ignoredFiles || 0)}</strong></span>
      </div>
    </div>
  `;
  }

  function reviewIssueListHtml(issues = []) {
    if (!issues.length) {
      return "";
    }
    return `
    <div class="review-issue-list">
      ${issues.map((issue) => `
        <div class="review-issue ${issue.level === "error" ? "error" : "warning"}">
          <strong>${escapeHtml(issue.title)}</strong>
          <span>${escapeHtml(issue.detail)}</span>
        </div>
      `).join("")}
    </div>
  `;
  }

  function reviewPanelHtml(options = {}) {
    const lotSummaryHtml = options.lotSummaryHtml || "";
    const image = options.image || null;
    if (!image) {
      return `
      ${lotSummaryHtml}
      ${options.emptyStateHtml || ""}
    `;
    }

    const reviewState = options.reviewState || { tone: "ready", label: "Lista" };
    const issues = Array.isArray(options.issues) ? options.issues : [];
    const issueList = reviewIssueListHtml(issues);
    const selectedIndexLabel = options.selectedIndexLabel || "Sin selección";
    const canNavigate = Boolean(options.canNavigate);
    const hasLocal = Boolean(options.hasLocal);

    return `
    ${lotSummaryHtml}

    <div class="review-card review-card--compact ${escapeHtml(reviewState.tone)}">
      <div class="review-card__header">
        <div>
          <strong title="${escapeHtml(image.path || image.name)}">${escapeHtml(image.name)}</strong>
          <small>${escapeHtml(selectedIndexLabel)}</small>
        </div>
        <span class="status-badge ${escapeHtml(reviewState.tone)}">${escapeHtml(reviewState.label)}</span>
      </div>
    </div>

    <div class="review-output-card review-output-card--compact">
      <strong title="${escapeHtml(options.outputName || "")}">${escapeHtml(options.outputName || "")}</strong>
      <small>${escapeHtml(options.outputDetail || "")}</small>
    </div>

    ${issueList}

    <div class="inspector-actionbar review-actions">
      <button type="button" data-action="previous-image"${canNavigate ? "" : " disabled"}>Anterior</button>
      <button type="button" data-action="next-image"${canNavigate ? "" : " disabled"}>Siguiente</button>
      ${issues.length ? '<button type="button" data-action="review-errors">Revisar avisos</button>' : ""}
      <button type="button" data-action="open-app-settings">Cambiar formato</button>
      ${hasLocal ? '<button type="button" data-action="reset-local-adjustment">Quitar ajuste local</button>' : '<button type="button" data-action="open-advanced">Editar ajuste</button>'}
    </div>
  `;
  }

  function selectedImageInspectorCardHtml(options = {}) {
    if (!options.hasReadyBatch) {
      return "";
    }
    const image = options.image || null;
    if (!image) {
      return `
      <section class="inspector-compact-row">
        <div>
          <span>Imagen</span>
          <strong>Sin selección</strong>
        </div>
        <button type="button" data-action="select-first-image">Seleccionar primera</button>
      </section>
    `;
    }
    return `
      <section class="inspector-compact-row">
        <div>
          <span>Imagen seleccionada</span>
          <strong title="${escapeHtml(image.path || image.name)}">${escapeHtml(image.name)}</strong>
          <small>${escapeHtml(options.detail || "")}</small>
        </div>
      ${options.hasLocal ? '<button type="button" data-action="reset-local-adjustment">Quitar ajuste</button>' : ""}
    </section>
  `;
  }

  function issuesInspectorCardHtml(options = {}) {
    const rows = Array.isArray(options.rows) ? options.rows : [];
    if (!rows.length) {
      return "";
    }
    const tone = options.blocking ? "error" : "warning";
    const title = options.blocking ? "Exportación bloqueada" : "Revisar";
    return `
    <section class="inspector-alert ${tone}">
      <div class="inspector-alert__head">
        <span>${escapeHtml(title)}</span>
        <strong>${escapeHtml(options.countLabel || "")}</strong>
      </div>
      <div class="inspector-alert__list">
        ${rows.slice(0, 3).map((row) => `
          <span title="${escapeHtml(row.path || row.detail || row.title)}">${escapeHtml(row.title)}</span>
        `).join("")}
      </div>
      <div class="inspector-alert__actions">
        <button type="button" data-action="review-errors">Revisar avisos</button>
      </div>
    </section>
  `;
  }

  function aspectInspectorCardHtml(options = {}) {
    if (!options.hasReadyBatch) {
      return "";
    }
    return `
    <section class="inspector-compact-row inspector-compact-row--quiet">
      <div>
        <span>Ajuste</span>
        <strong>${escapeHtml(options.activePreset || "")}</strong>
        <small>${escapeHtml(options.statusLabel || "Global")}</small>
      </div>
      <button type="button" data-action="open-advanced">Editar ajuste</button>
    </section>
  `;
  }

  return {
    aspectInspectorCardHtml,
    escapeHtml,
    issuesInspectorCardHtml,
    lotInspectorSummaryHtml,
    reviewIssueListHtml,
    reviewPanelHtml,
    selectedImageInspectorCardHtml,
  };
});
