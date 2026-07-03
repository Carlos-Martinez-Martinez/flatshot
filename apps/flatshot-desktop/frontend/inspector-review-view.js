(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotInspectorReviewView = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const escapeHtml = globalThis.FlatShotFormatters?.escapeHtml || function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  };

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

  function lotInspectorCardHtml(options = {}) {
    const tone = options.tone || "";
    return `
    <section class="inspector-summary panel-summary-card ${escapeHtml(tone)}">
      <header class="panel-summary-card__head">
        <div>
          <span>Lote</span>
          <strong>${escapeHtml(options.title || "")}</strong>
        </div>
        <button type="button" class="panel-link-button" data-action="open-batch-detail">Ver lote</button>
      </header>
      ${options.meta ? `<small class="panel-summary-card__meta">${escapeHtml(options.meta)}</small>` : ""}
    </section>
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
      <button type="button" data-action="open-app-settings">Formatos</button>
      ${hasLocal ? '<button type="button" data-action="reset-local-adjustment">Restablecer al lote</button>' : '<button type="button" data-action="open-advanced">Editar ajuste</button>'}
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
    const hasLocal = Boolean(options.hasLocal);
    return `
      <section class="inspector-compact-row selected-image-card panel-summary-card">
        <header class="panel-summary-card__head selected-image-card__head">
          <div>
            <span>Imagen seleccionada</span>
            <strong title="${escapeHtml(image.path || image.name)}">${escapeHtml(image.name)}</strong>
            <small>${escapeHtml(options.detail || "")}</small>
          </div>
          <small class="selected-image-card__state">${escapeHtml(hasLocal ? "Ajuste personalizado" : "Ajuste del lote")}</small>
        </header>
        <div class="selected-image-card__actions">
          <button type="button" data-action="open-image-adjustment">${escapeHtml(hasLocal ? "Editar ajuste" : "Personalizar imagen")}</button>
          ${hasLocal ? '<button type="button" data-action="reset-local-adjustment">Restablecer</button>' : ""}
        </div>
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
    const adjustments = Array.isArray(options.adjustments) && options.adjustments.length
      ? options.adjustments
      : options.activePreset ? [{ name: options.activePreset }] : [];
    const optionsHtml = adjustments.map((adjustment) => `
      <option value="${escapeHtml(adjustment.name || "")}"${adjustment.name === options.activePreset ? " selected" : ""}>
        ${escapeHtml(adjustment.name || "")}
      </option>
    `).join("");
    const customizedCount = Number(options.customizedCount) || 0;
    const customizedLabel = customizedCount
      ? `${customizedCount} imagen${customizedCount === 1 ? "" : "es"} mantiene${customizedCount === 1 ? "" : "n"} su ajuste personalizado.`
      : "";
    return `
    <section class="inspector-compact-row inspector-processing-card panel-summary-card">
      <header class="panel-summary-card__head">
        <div>
          <span>Procesado</span>
          <strong>Ajuste del lote</strong>
        </div>
      </header>
      <div class="processing-card__controls">
        <label class="processing-card__select">
          <span class="visually-hidden">Ajuste de imagen</span>
          <select data-image-adjustment-select aria-label="Ajuste de imagen del lote">
            ${optionsHtml}
          </select>
        </label>
        <div class="processing-card__actions">
          <button type="button" data-action="open-advanced" aria-label="Editar ajuste del lote" title="Editar ajuste del lote">
            <span class="button-icon" aria-hidden="true"><svg viewBox="0 0 24 24" focusable="false"><path d="M12 20h9"></path><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"></path></svg></span>
            <span class="visually-hidden">Editar ajuste</span>
          </button>
          <button type="button" data-action="open-preset-editor" aria-label="Gestionar ajustes" title="Gestionar ajustes">
            <span class="button-icon" aria-hidden="true"><svg viewBox="0 0 24 24" focusable="false"><path d="M4 7h8"></path><path d="M16 7h4"></path><path d="M4 17h4"></path><path d="M12 17h8"></path><path d="M12 5v4"></path><path d="M8 15v4"></path></svg></span>
            <span class="visually-hidden">Ajustes</span>
          </button>
        </div>
      </div>
      ${customizedLabel ? `
        <div class="processing-card__notice">
          <span>${escapeHtml(customizedLabel)}</span>
          <button type="button" data-action="apply-global-adjustment-to-overrides">Aplicar también a imágenes personalizadas</button>
        </div>
      ` : ""}
    </section>
  `;
  }

  return {
    aspectInspectorCardHtml,
    escapeHtml,
    issuesInspectorCardHtml,
    lotInspectorCardHtml,
    lotInspectorSummaryHtml,
    reviewIssueListHtml,
    reviewPanelHtml,
    selectedImageInspectorCardHtml,
  };
});
