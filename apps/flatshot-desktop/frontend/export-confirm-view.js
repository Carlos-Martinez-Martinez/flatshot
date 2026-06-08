(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotExportConfirmView = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function exportConfirmRiskHtml(risk) {
    const icon = risk.blocking ? "!" : "⚠";
    return `
    <div class="export-confirm-risk ${risk.blocking ? "error" : "warning"}">
      <span aria-hidden="true">${escapeHtml(icon)}</span>
      <div>
        <strong>${escapeHtml(risk.title)}</strong>
        <small>${escapeHtml(risk.detail || "Revisar antes de exportar.")}</small>
      </div>
    </div>
  `;
  }

  function exportConfirmHtml(options = {}) {
    const risks = Array.isArray(options.risks) ? options.risks : [];
    const summaryRows = Array.isArray(options.summaryRows) ? options.summaryRows : [];
    const blocking = risks.some((risk) => risk.blocking);
    const riskTitle = blocking ? "Bloqueos" : "Avisos";
    const riskRows = risks.length
      ? risks.map(exportConfirmRiskHtml).join("")
      : `
      <div class="export-confirm-risk ready">
        <span aria-hidden="true">✓</span>
        <div>
          <strong>Sin avisos</strong>
          <small>El lote se exportará con el formato activo.</small>
        </div>
      </div>
    `;
    const overwriteNote = risks.some((risk) => risk.id === "previous-export-destination" || risk.id === "existing-output-blocker")
      ? `
      <div class="export-confirm-note">
        <strong>Archivos existentes</strong>
        <span>FlatShot mantiene la validación segura: no sobrescribe archivos existentes sin soporte explícito del motor local.</span>
      </div>
    `
      : "";

    return `
    <div class="export-confirm-summary">
      ${summaryRows.map(([label, value]) => `
        <div>
          <span>${escapeHtml(label)}</span>
          <strong title="${escapeHtml(value)}">${escapeHtml(value)}</strong>
        </div>
      `).join("")}
    </div>
    <section class="export-confirm-section">
      <h3>${escapeHtml(riskTitle)}</h3>
      <div class="export-confirm-risks">${riskRows}</div>
    </section>
    ${overwriteNote}
  `;
  }

  function exportConfirmModalState(options = {}) {
    const risks = Array.isArray(options.risks) ? options.risks : [];
    const blocking = risks.some((risk) => risk.blocking);
    return {
      actionDanger: blocking,
      actionText: blocking ? "Revisar problemas" : String(options.actionText || ""),
      blocking,
      subtitle: blocking
        ? "Hay puntos que impiden exportar."
        : "Confirma solo los puntos que requieren atención.",
    };
  }

  return {
    escapeHtml,
    exportConfirmHtml,
    exportConfirmModalState,
    exportConfirmRiskHtml,
  };
});
