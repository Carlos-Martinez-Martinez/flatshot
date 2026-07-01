(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotBridgeClient = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const DEFAULT_MAX_RETRIES = 3;
  const RETRY_DELAY_MS = 500;

  function normalizedBridgeUrl(currentBridgeUrl, defaultBridgeUrl) {
    return String(currentBridgeUrl || defaultBridgeUrl || "").trim().replace(/\/+$/, "");
  }

  function thumbnailUrl(baseUrl, path, size = 128) {
    if (!path) {
      return "";
    }
    return `${normalizedBridgeUrl(baseUrl)}/images/thumbnail?path=${encodeURIComponent(path)}&size=${encodeURIComponent(size)}`;
  }

  function errorMessage(error) {
    if (error && error.name === "AbortError") {
      return "La conexión local tardó demasiado. Verifica que FlatShot esté funcionando.";
    }
    const message = (error && error.message) ? String(error.message) : "";
    if (message.startsWith("HTTP ")) {
      return `Error del servidor local: ${message}`;
    }
    if (message) {
      return `Conexión local no disponible: ${message}`;
    }
    return "Conexión local no disponible. Reinicia la aplicación.";
  }

  function abortableDelay(delayMs, signal) {
    return new Promise((resolve) => {
      const id = setTimeout(resolve, delayMs);
      if (signal) {
        signal.addEventListener("abort", () => {
          clearTimeout(id);
          resolve();
        }, { once: true });
      }
    });
  }

  async function request(baseUrl, path, options = {}) {
    const controller = new AbortController();
    const timeoutMs = options.timeoutMs || 3500;
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    const headers = options.body
      ? { "Content-Type": "application/json", ...(options.headers || {}) }
      : { ...(options.headers || {}) };
    const { timeoutMs: _timeoutMs, retries: _retries, ...fetchOptions } = options;
    const maxRetries = options.retries ?? DEFAULT_MAX_RETRIES;
    let lastError = null;

    try {
      for (let attempt = 0; attempt <= maxRetries; attempt += 1) {
        if (controller.signal.aborted) {
          break;
        }

        try {
          const response = await fetch(`${normalizedBridgeUrl(baseUrl)}${path}`, {
            ...fetchOptions,
            headers,
            signal: controller.signal,
          });
          const payload = await response.json().catch(() => ({}));
          if (!response.ok) {
            throw new Error(payload.error?.message || `HTTP ${response.status}`);
          }
          return payload;
        } catch (err) {
          lastError = err;
          if (controller.signal.aborted) {
            break;
          }
          if (attempt < maxRetries) {
            await abortableDelay(RETRY_DELAY_MS * Math.pow(2, attempt), controller.signal);
          }
        }
      }
    } finally {
      clearTimeout(timer);
    }

    throw lastError || new Error("Bridge request failed");
  }

  async function requestPreviewImage(baseUrl, options = {}) {
    const payload = {
      imagePath: options.imagePath,
      ...(options.targetSize || {}),
      settings: options.settings || {},
      localOverride: options.localOverride || {},
    };
    const response = await fetch(`${normalizedBridgeUrl(baseUrl)}/preview/render-image`, {
      method: "POST",
      body: JSON.stringify(payload),
      headers: { "Content-Type": "application/json" },
      signal: options.signal,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.error?.message || `HTTP ${response.status}`);
    }

    return {
      blob: await response.blob(),
      width: Number(response.headers.get("X-FlatShot-Width")) || 0,
      height: Number(response.headers.get("X-FlatShot-Height")) || 0,
      warning: response.headers.get("X-FlatShot-Warning") || "",
    };
  }

  return {
    errorMessage,
    normalizedBridgeUrl,
    request,
    requestPreviewImage,
    thumbnailUrl,
  };
});
