(function () {
  const APP_SCRIPT_NAME_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_-]*\.js$/;
  const errorBoundary = window.FlatShotErrorBoundary;
  errorBoundary?.installGlobalErrorBoundary?.(window, { document });

  const currentScript = document.currentScript;
  const currentSrc = currentScript?.src || "";
  const query = currentSrc.includes("?") ? currentSrc.slice(currentSrc.indexOf("?")) : "";
  const baseUrl = currentSrc
    ? currentSrc.slice(0, currentSrc.lastIndexOf("/") + 1)
    : "./";

  function appScriptOrder() {
    const manifest = document.getElementById("flatshot-app-loader-manifest");
    const parsed = JSON.parse(manifest?.textContent || "[]");
    if (
      !Array.isArray(parsed)
      || parsed.some((name) => typeof name !== "string" || !APP_SCRIPT_NAME_PATTERN.test(name))
    ) {
      throw new Error("Manifest de scripts de FlatShot no válido.");
    }
    return parsed;
  }

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
    for (const scriptName of appScripts) {
      await loadScript(scriptName);
    }
  }

  const appScripts = appScriptOrder();
  window.FlatShotAppScriptOrder = appScripts;
  void loadFlatShotApp().catch((error) => {
    errorBoundary?.renderGlobalError?.(error, { document, source: "app-loader" });
  });
})();
