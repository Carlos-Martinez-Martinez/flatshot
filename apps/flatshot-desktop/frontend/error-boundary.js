(function (root, factory) {
  const api = factory(root);
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotErrorBoundary = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function (root) {
  function escapeHtml(value) {
    return String(value || "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function normalizeError(error) {
    if (error instanceof Error) {
      return {
        message: error.message || "Error inesperado",
        detail: error.stack || error.message || String(error),
      };
    }
    if (error && typeof error === "object") {
      return {
        message: String(error.message || "Error inesperado"),
        detail: String(error.stack || JSON.stringify(error)),
      };
    }
    return {
      message: String(error || "Error inesperado"),
      detail: String(error || ""),
    };
  }

  function errorBoundaryHtml(error) {
    const normalized = normalizeError(error);
    return `
      <div class="app-error-boundary__card">
        <span class="app-error-boundary__eyebrow">Error</span>
        <strong>FlatShot no pudo iniciar</strong>
        <p>${escapeHtml(normalized.message)}</p>
        <button type="button" data-action="reload-app" onclick="window.location.reload()">Recargar</button>
        <details>
          <summary>Detalle técnico</summary>
          <pre>${escapeHtml(normalized.detail)}</pre>
        </details>
      </div>
    `;
  }

  function renderGlobalError(error, options = {}) {
    const documentRef = options.document || root.document;
    const logger = options.console || root.console;
    const normalized = normalizeError(error);
    logger?.error?.(error);
    if (!documentRef) {
      return false;
    }
    if (documentRef.documentElement?.dataset) {
      documentRef.documentElement.dataset.boot = "ready";
    }
    const shell = documentRef.querySelector?.(".app-shell");
    const host = documentRef.querySelector?.(".workspace") || shell || documentRef.body;
    if (!host) {
      return false;
    }
    if (shell) {
      shell.dataset.uiState = "error";
      shell.dataset.statusFooter = "false";
    }
    let boundary = documentRef.getElementById?.("flatshot-error-boundary");
    if (!boundary) {
      boundary = documentRef.createElement("section");
      boundary.id = "flatshot-error-boundary";
      boundary.className = "app-error-boundary";
      boundary.setAttribute("role", "alert");
      boundary.setAttribute("aria-live", "assertive");
      host.appendChild(boundary);
    }
    boundary.innerHTML = errorBoundaryHtml(normalized);
    return true;
  }

  function installGlobalErrorBoundary(windowRef = root, options = {}) {
    if (!windowRef) {
      return;
    }
    windowRef.onerror = function onFlatShotError(message, source, lineno, colno, error) {
      const fallback = error || new Error(`${message || "Error inesperado"} (${source || "sin origen"}:${lineno || 0}:${colno || 0})`);
      renderGlobalError(fallback, options);
      return false;
    };
    windowRef.onunhandledrejection = function onFlatShotUnhandledRejection(event) {
      renderGlobalError(event?.reason || new Error("Promesa rechazada sin gestionar"), options);
      return false;
    };
  }

  return {
    errorBoundaryHtml,
    escapeHtml,
    installGlobalErrorBoundary,
    normalizeError,
    renderGlobalError,
  };
});
