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

  function thumbnailUrl(baseUrl, path, size = 128, authToken = "", imageId = "") {
    if (!path && !imageId) {
      return "";
    }
    const imageParam = imageId
      ? `imageId=${encodeURIComponent(imageId)}`
      : `path=${encodeURIComponent(path)}`;
    const tokenParam = authToken ? `&token=${encodeURIComponent(authToken)}` : "";
    return `${normalizedBridgeUrl(baseUrl)}/images/thumbnail?${imageParam}&size=${encodeURIComponent(size)}${tokenParam}`;
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

  function bridgeHttpError(response, payload = {}) {
    const errorPayload = payload.error && typeof payload.error === "object" ? payload.error : {};
    const error = new Error(errorPayload.message || `HTTP ${response.status}`);
    error.status = response.status;
    error.bridgeCode = errorPayload.code || "";
    return error;
  }

  async function request(baseUrl, path, options = {}) {
    const controller = new AbortController();
    const timeoutMs = options.timeoutMs || 3500;
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    const authHeaders = options.authToken ? { "X-FlatShot-Token": options.authToken } : {};
    const headers = options.body
      ? { "Content-Type": "application/json", ...(options.headers || {}) }
      : { ...(options.headers || {}) };
    Object.assign(headers, authHeaders);
    const { timeoutMs: _timeoutMs, retries: _retries, authToken: _authToken, ...fetchOptions } = options;
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
            throw bridgeHttpError(response, payload);
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
    const controller = new AbortController();
    const timeoutMs = options.timeoutMs || 3500;
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    if (options.signal) {
      if (options.signal.aborted) {
        controller.abort();
      } else {
        options.signal.addEventListener("abort", () => controller.abort(), { once: true });
      }
    }
    const imageId = String(options.imageId || "").trim();
    const imagePath = String(options.imagePath || "").trim();
    const payload = {
      ...(imageId ? { imageId } : {}),
      ...(!imageId && imagePath ? { imagePath } : {}),
      ...(options.targetSize || {}),
      settings: options.settings || {},
      localOverride: options.localOverride || {},
      curveData: options.curveData || options.scaleCurve || null,
    };
    try {
      const response = await fetch(`${normalizedBridgeUrl(baseUrl)}/preview/render-image`, {
        method: "POST",
        body: JSON.stringify(payload),
        headers: {
          "Content-Type": "application/json",
          ...(options.authToken ? { "X-FlatShot-Token": options.authToken } : {}),
        },
        signal: controller.signal,
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw bridgeHttpError(response, error);
      }

      return {
        blob: await response.blob(),
        width: Number(response.headers.get("X-FlatShot-Width")) || 0,
        height: Number(response.headers.get("X-FlatShot-Height")) || 0,
        warning: response.headers.get("X-FlatShot-Warning") || "",
      };
    } finally {
      clearTimeout(timer);
    }
  }

  return {
    errorMessage,
    normalizedBridgeUrl,
    request,
    requestPreviewImage,
    thumbnailUrl,
  };
});
