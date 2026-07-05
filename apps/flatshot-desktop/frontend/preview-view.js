(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotPreviewView = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const formatterHelpers = globalThis.FlatShotFormatters
    || (typeof require === "function" ? require("./formatters.js") : null);
  const escapeHtml = (value) => formatterHelpers.escapeHtml(value);

  function previewLoadingHtml(detail = "") {
    return `
      <div class="preview-state">
        <span class="loader" aria-hidden="true"></span>
        <strong>Generando vista</strong>
        <span>${escapeHtml(detail)}</span>
      </div>
    `;
  }

  function previewLoadingOverlayHtml(detail = "") {
    return `
      <div class="preview-loading-overlay" role="status" aria-live="polite">
        <span class="loader" aria-hidden="true"></span>
        <strong>Generando vista</strong>
        <span>${escapeHtml(detail)}</span>
      </div>
    `;
  }

  function scanningStateHtml(scanStatus = "") {
    return `
    <div class="empty-state inline scanning-state">
      <span class="loader" aria-hidden="true"></span>
      <strong>Escaneando carpeta...</strong>
      <span>${escapeHtml(scanStatus || "Leyendo imágenes")}</span>
    </div>
  `;
  }

  function realPreviewImageHtml(options = {}) {
    const width = Number(options.width) || 0;
    const height = Number(options.height) || 0;
    const zoom = Number(options.zoom) || 100;
    const inlineSize = options.inlineSize !== false;
    const zoomWidth = width ? Math.max(1, Math.round(width * zoom / 100)) : "";
    const zoomHeight = height ? Math.max(1, Math.round(height * zoom / 100)) : "";
    const sizeStyle = inlineSize && zoomWidth && zoomHeight
      ? ` style="width: ${zoomWidth}px; height: ${zoomHeight}px;"`
      : "";
    const dimensionAttrs = width && height
      ? ` width="${width}" height="${height}"`
      : "";
    const warning = options.warning
      ? `<div class="preview-warning-card">${escapeHtml(options.warning)}</div>`
      : "";
    return `
      <img class="preview-image" src="${escapeHtml(options.src || "")}" alt="Vista previa de ${escapeHtml(options.imageName || "")}"${sizeStyle}${dimensionAttrs} />
      ${warning}
    `;
  }

  function realPreviewPlaceholderHtml(options = {}) {
    return `
    <div class="real-preview-placeholder">
      <strong>Vista pendiente</strong>
      <span>Imagen seleccionada: ${escapeHtml(options.imageName || "")}</span>
      <small class="path-line">Ruta: ${escapeHtml(options.imagePath || "Sin ruta")}</small>
      <small>Genera la vista al seleccionar la imagen.</small>
    </div>
  `;
  }

  function mockPreviewHtml(options = {}) {
    const warning = options.warning
      ? `<div class="preview-warning-card">${escapeHtml(options.warning)}</div>`
      : "";
    return `
    <div class="mock-product" aria-hidden="true">
      <div class="mock-shadow"></div>
      <div class="mock-body"></div>
    </div>
    ${warning}
  `;
  }

  function compareDividerHtml(value = 50) {
    const percent = Math.max(5, Math.min(95, Number(value) || 50));
    return `
      <button type="button" class="compare-divider" data-compare-divider aria-label="Mover divisor de comparación" aria-valuemin="5" aria-valuemax="95" aria-valuenow="${percent}" title="Mover comparación"></button>
    `;
  }

  function viewerOutputCompactLabel(options = {}) {
    return `${options.format || "JPG"} · ${options.sizeLabel || "1800×2400"} · ${options.backgroundLabel || "gris claro"}`;
  }

  function viewerOutputContextHtml(options = {}) {
    const name = options.name || "";
    if (!name) {
      return "";
    }
    const summary = options.summary || "";
    const summaryHtml = summary ? `<small title="${escapeHtml(summary)}">${escapeHtml(summary)}</small>` : "";
    return `
      <span>Previsualizando</span>
      <strong>${escapeHtml(name)}</strong>
      ${summaryHtml}
    `;
  }

  return {
    compareDividerHtml,
    escapeHtml,
    mockPreviewHtml,
    previewLoadingOverlayHtml,
    previewLoadingHtml,
    realPreviewImageHtml,
    realPreviewPlaceholderHtml,
    scanningStateHtml,
    viewerOutputContextHtml,
    viewerOutputCompactLabel,
  };
});
