(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotPreviewState = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const DEFAULT_VIEW_MODE_LABELS = {
    fit: "Encajar",
    height: "Alto",
    width: "Ancho",
    manual: "Manual",
  };

  function isAutoViewerMode(mode) {
    return ["fit", "height", "width"].includes(mode);
  }

  function viewerModeLabel(mode, labels = DEFAULT_VIEW_MODE_LABELS) {
    return labels[mode] || labels.manual;
  }

  function viewerModeClass(mode) {
    if (mode === "height") {
      return "fit-height-mode";
    }
    if (mode === "width") {
      return "fit-width-mode";
    }
    return mode === "fit" ? "fit-mode" : "zoom-mode";
  }

  function clampViewerZoom(value) {
    return Math.max(25, Math.min(320, Math.round(value)));
  }

  function previewLoadingState(options = {}) {
    const patch = {
      previewStatus: "loading",
      statusText: options.statusText || "Generando vista",
    };
    if (options.clearData !== false) {
      patch.previewData = null;
      patch.previewError = "";
    }
    return patch;
  }

  function previewEmptyState() {
    return {
      previewStatus: "empty",
      previewData: null,
      previewError: "",
    };
  }

  function previewImageStatusState(imageStatus, options = {}) {
    const previewStatus = imageStatus === "error" && !options.errorAsReady
      ? "error"
      : imageStatus === "warning" ? "warning" : "ready";
    return {
      previewStatus,
      statusText: previewStatus === "error" ? "Vista no disponible" : "Vista lista",
    };
  }

  function previewBridgeResultState(previewData, warning = "") {
    return {
      previewData,
      previewStatus: warning ? "warning" : "ready",
      statusText: warning ? "Vista con aviso" : "Vista lista",
    };
  }

  function previewErrorState(message) {
    return {
      previewStatus: "error",
      previewData: null,
      previewError: message,
      statusText: "Vista no disponible",
    };
  }

  function bridgePreviewMeta(options = {}) {
    const previewStatus = options.previewStatus;
    if (previewStatus === "loading") {
      return "Generando vista";
    }
    if (previewStatus === "error") {
      return options.previewError || "Vista no disponible";
    }
    if (options.previewData) {
      return options.previewData.warning ? "Vista con aviso" : options.activePreset;
    }
    return "Vista pendiente";
  }

  function previewSettingsLabel(options = {}) {
    const dirtyLabel = "Aspecto modificado";
    if (options.bridgeMode === "bridge" && options.activePresetSource === "bridge") {
      return options.presetDirty ? dirtyLabel : "Salida";
    }
    return options.presetDirty ? dirtyLabel : "Aspecto";
  }

  function previewModeLabel(previewMode) {
    if (previewMode === "original") {
      return "Original";
    }
    if (previewMode === "compare") {
      return "Comparación";
    }
    return "Vista";
  }

  function previewOrientation(previewData) {
    const width = Number(previewData?.width || 0);
    const height = Number(previewData?.height || 0);
    if (!width || !height) {
      return "portrait";
    }
    if (height > width * 1.08) {
      return "portrait";
    }
    if (width > height * 1.08) {
      return "landscape";
    }
    return "square";
  }

  function previewFooterLabel(options = {}) {
    const previewStatus = options.previewStatus;
    if (previewStatus === "loading") {
      return "Generando";
    }
    if (previewStatus === "warning") {
      return "Con aviso";
    }
    if (previewStatus === "error") {
      return "Error";
    }
    if (previewStatus === "ready") {
      return options.selectedImageSource === "bridge" ? "Real" : "Lista";
    }
    return options.selectedImageSource === "bridge" ? "Pendiente" : "Sin imagen";
  }

  function previewSubtitle(options = {}) {
    const previewStatus = options.previewStatus;
    if (!options.hasImage) {
      if (options.filterIsEmpty) {
        return options.filterEmptyDetail || "";
      }
      if (options.batch === "none") {
        return "Sin lote";
      }
      if (options.batch === "empty") {
        return options.scanStatus || "No hay PNG válidos";
      }
      if (options.batch === "scanning") {
        return options.scanStatus || "Escaneando";
      }
      return "Sin selección";
    }
    if (options.imageSource === "bridge") {
      if (previewStatus === "loading") {
        return "Generando vista";
      }
      if (previewStatus === "warning") {
        return "Vista con aviso";
      }
      if (previewStatus === "error") {
        return "Vista no disponible";
      }
      if (previewStatus === "ready") {
        return "Vista generada";
      }
      return "Vista pendiente";
    }
    if (previewStatus === "loading") {
      return "Generando vista";
    }
    if (previewStatus === "warning") {
      return "Vista con aviso";
    }
    if (previewStatus === "error") {
      return "Vista no disponible";
    }
    return previewStatus === "ready" ? "Vista generada" : options.imageDetail;
  }

  return {
    bridgePreviewMeta,
    clampViewerZoom,
    isAutoViewerMode,
    previewBridgeResultState,
    previewEmptyState,
    previewErrorState,
    previewFooterLabel,
    previewImageStatusState,
    previewLoadingState,
    previewModeLabel,
    previewOrientation,
    previewSettingsLabel,
    previewSubtitle,
    viewerModeClass,
    viewerModeLabel,
  };
});
