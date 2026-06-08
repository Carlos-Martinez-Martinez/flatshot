(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotPreviewView = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function previewLoadingHtml(detail = "") {
    return `
      <div class="preview-state">
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
    const zoomWidth = width ? Math.max(1, Math.round(width * zoom / 100)) : "";
    const zoomHeight = height ? Math.max(1, Math.round(height * zoom / 100)) : "";
    const sizeStyle = zoomWidth && zoomHeight
      ? ` style="width: ${zoomWidth}px; height: ${zoomHeight}px;" width="${width}" height="${height}"`
      : "";
    const warning = options.warning
      ? `<div class="preview-warning-card">${escapeHtml(options.warning)}</div>`
      : "";
    return `
      <img class="preview-image" src="${escapeHtml(options.src || "")}" alt="Vista previa de ${escapeHtml(options.imageName || "")}"${sizeStyle} />
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

  return {
    escapeHtml,
    mockPreviewHtml,
    previewLoadingHtml,
    realPreviewImageHtml,
    realPreviewPlaceholderHtml,
    scanningStateHtml,
  };
});
