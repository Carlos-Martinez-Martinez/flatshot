(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotQaLabView = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  function qaLabModalHtml() {
    return `
      <div class="app-settings-backdrop qa-lab-backdrop is-hidden dev-only" id="qa-lab-modal" role="dialog" aria-modal="true" aria-labelledby="qa-lab-title" aria-hidden="true">
        <section class="app-settings-dialog qa-lab-dialog">
          <header class="app-settings-header">
            <div>
              <span class="eyebrow">Diagnostico</span>
              <h2 id="qa-lab-title">QA Lab</h2>
              <small>Estados visuales simulados fuera del flujo principal.</small>
            </div>
            <button type="button" class="icon-button" data-action="close-qa-lab" aria-label="Cerrar QA Lab">&times;</button>
          </header>
          <div class="qa-lab-body" id="qa-lab-body">
            <section class="qa-lab-section">
              <div class="qa-lab-section-heading">
                <h3>Estados visuales</h3>
                <small>Estados simulados para revisar la interfaz sin depender de archivos reales.</small>
              </div>
              <div class="review-grid" aria-label="Estados visuales simulados">
                <button type="button" data-review-scenario="initial">Sin lote</button>
                <button type="button" data-review-scenario="batch-ready">Lote listo</button>
                <button type="button" data-review-scenario="empty-folder">Carpeta vacia</button>
                <button type="button" data-review-scenario="preview-loading">Vista cargando</button>
                <button type="button" data-review-scenario="preview-warning">Vista con aviso</button>
                <button type="button" data-review-scenario="preview-error">Error de vista</button>
                <button type="button" data-review-scenario="export-blocked">Exportacion bloqueada</button>
                <button type="button" data-review-scenario="export-ready">Exportacion lista</button>
                <button type="button" data-review-scenario="export-running">En curso</button>
                <button type="button" data-review-scenario="export-completed">Completada</button>
                <button type="button" data-review-scenario="export-partial">Con errores</button>
                <button type="button" data-review-scenario="export-failed">Fallida</button>
              </div>
            </section>
            <section class="qa-lab-section">
              <div class="qa-lab-section-heading">
                <h3>Bridge real</h3>
                <small>Comprobaciones que usan la misma ruta local que produccion.</small>
              </div>
              <div class="review-actions">
                <button type="button" data-action="check-bridge">Bridge health</button>
                <button type="button" data-action="scan-bridge-folder">Escaneo real</button>
                <button type="button" data-action="force-preview-error">Error de vista</button>
              </div>
            </section>
          </div>
          <footer class="app-settings-footer">
            <button type="button" data-action="close-qa-lab">Cerrar</button>
          </footer>
        </section>
      </div>
    `;
  }

  function ensureQaLabModal(documentRef) {
    if (!documentRef || documentRef.getElementById("qa-lab-modal")) {
      return documentRef ? documentRef.getElementById("qa-lab-modal") : null;
    }
    const wrapper = documentRef.createElement("div");
    wrapper.innerHTML = qaLabModalHtml().trim();
    const modal = wrapper.firstElementChild;
    if (modal) {
      documentRef.body.appendChild(modal);
    }
    return modal || null;
  }

  return {
    ensureQaLabModal,
    qaLabModalHtml,
  };
});
