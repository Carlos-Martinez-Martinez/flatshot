(function () {
  const APP_SCRIPT_ORDER = [
    "app-globals.js",
    "mock-data.js",
    "app-state-selectors.js",
    "app-preflight-state.js",
    "app-export-readiness-state.js",
    "app-visible-state.js",
    "app-session-snapshot-controller.js",
    "app-timer-controller.js",
    "app-output-profile-storage.js",
    "app-background-state.js",
    "app-output-profile-state.js",
    "app-export-preferences.js",
    "app-bridge-ui-preferences.js",
    "app-output-profile-apply.js",
    "app-settings-preset-workflow.js",
    "app-viewer-state.js",
    "app-local-adjustment-workflow.js",
    "app-gallery-selection-workflow.js",
    "app-batch-workflow.js",
    "app-bridge-api.js",
    "app-bridge-preview-controller.js",
    "app-export-controller.js",
    "app-bridge-connection-controller.js",
    "app-bridge-scan-controller.js",
    "app-review-actions.js",
    "app-inspector-disclosure-controller.js",
    "app-shell.js",
    "app-topbar-bridge.js",
    "app-gallery-controller.js",
    "app-thumbnail-controller.js",
    "app-modal-render-controller.js",
    "app-canvas-guides-controller.js",
    "app-preview-controller.js",
    "app-range-fill-controller.js",
    "app-review-panel-controller.js",
    "app-inspector-cards.js",
    "app-contextual-inspector-controller.js",
    "app-settings-panel-controller.js",
    "app-inspector-layout-controller.js",
    "app-background-preset-controller.js",
    "app-output-profile-summary.js",
    "app-output-profile-draft.js",
    "app-output-profile-manager.js",
    "app-output-profile-modal-renderer.js",
    "app-modal-controller.js",
    "app-export-view.js",
    "app-preset-controller.js",
    "app-footer-status-controller.js",
    "app-render-shell-gallery.js",
    "app-action-dispatcher.js",
    "app-document-events.js",
    "app-form-events.js",
    "app-viewer-events.js",
    "app.js",
    "app-startup.js",
  ];

  const currentScript = document.currentScript;
  const currentSrc = currentScript?.src || "";
  const query = currentSrc.includes("?") ? currentSrc.slice(currentSrc.indexOf("?")) : "";
  const baseUrl = currentSrc
    ? currentSrc.slice(0, currentSrc.lastIndexOf("/") + 1)
    : "./";

  function loadScript(name) {
    return new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.async = false;
      script.src = `${baseUrl}${name}${query}`;
      script.onload = resolve;
      script.onerror = () => reject(new Error(`No se pudo cargar ${name}`));
      document.head.appendChild(script);
    });
  }

  async function loadFlatShotApp() {
    for (const scriptName of APP_SCRIPT_ORDER) {
      await loadScript(scriptName);
    }
  }

  window.FlatShotAppScriptOrder = APP_SCRIPT_ORDER;
  void loadFlatShotApp().catch((error) => {
    console.error(error);
    const shell = document.querySelector(".app-shell");
    if (shell) {
      shell.dataset.uiState = "error";
    }
  });
})();
