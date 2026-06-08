(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotBatchView = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  function warningCountLabel(count) {
    return `${count} aviso${count === 1 ? "" : "s"}`;
  }

  function imageCountLabel(count) {
    return `${count} ${count === 1 ? "imagen" : "imágenes"}`;
  }

  function exportActionLabel(imageCount, outputCount = 1) {
    if (outputCount > 1) {
      return `Exportar ${imageCount * outputCount} archivos`;
    }
    return `Exportar ${imageCount} imágenes`;
  }

  function outputCountLabel(count) {
    return `${count} salida${count === 1 ? "" : "s"}`;
  }

  function detectedFormatLabel(images = []) {
    if (!images.length) {
      return "PNG";
    }
    const suffixes = Array.from(new Set(images.map((image) =>
      String(image.name || image.suffix || "")
        .split(".")
        .pop()
        ?.toUpperCase()
        || "PNG"
    )));
    return suffixes.length === 1 ? suffixes[0] : "PNG/JPG";
  }

  function batchSummaryLabel(options = {}) {
    if (options.batch === "none") {
      return "Sin lote";
    }
    if (options.batch === "scanning") {
      return "Escaneando";
    }
    if (options.batch === "empty") {
      return "Sin imágenes";
    }
    const count = Number(options.count) || 0;
    const warnings = Number(options.warnings) || 0;
    return `${imageCountLabel(count)}${warnings ? ` · ${warningCountLabel(warnings)}` : ""}`;
  }

  function readyBatchSummaryText(counts = {}, format = "PNG", readyImagesText = "") {
    if (counts.filesFound === null) {
      return "Leyendo archivos";
    }
    if (counts.filesFound > 0 || counts.exportableImages > 0) {
      return `${format} · ${counts.filesFound} archivos · ${readyImagesText}`;
    }
    return `${format} · ${readyImagesText}`;
  }

  function bridgeScanMessage(totalImages, warningCount) {
    if (warningCount) {
      return `Escaneo completado con ${warningCount} aviso${warningCount === 1 ? "" : "s"}`;
    }
    if (totalImages === 0) {
      return "No se encontraron PNG válidos";
    }
    return `${totalImages} imágenes encontradas`;
  }

  function omissionReasonLabel(reason) {
    if (reason === "system_file") {
      return "Archivo del sistema";
    }
    if (reason === "temporary_or_config_file") {
      return "Archivo temporal o de configuración";
    }
    if (reason === "unsupported_extension") {
      return "Extensión no admitida";
    }
    if (reason === "read_error") {
      return "Error de lectura";
    }
    if (reason === "subfolder_not_scanned") {
      return "Subcarpeta no escaneada";
    }
    return "Ignorado";
  }

  function omittedSummaryText(diagnostics = {}) {
    if (!diagnostics.totalOmitted) {
      return "Sin ignorados";
    }
    return Object.entries(diagnostics.omittedByReason || {})
      .map(([reason, count]) => `${count} ${omissionReasonLabel(reason).toLowerCase()}`)
      .join(" · ") || `${diagnostics.totalOmitted} ignorados`;
  }

  function omissionSummaryText(items = [], emptyText) {
    if (!items.length) {
      return emptyText;
    }
    const counts = items.reduce((acc, item) => {
      const label = omissionReasonLabel(item.reason).toLowerCase();
      acc[label] = (acc[label] || 0) + 1;
      return acc;
    }, {});
    return Object.entries(counts)
      .map(([label, count]) => `${count} ${label}`)
      .join(" · ");
  }

  function batchBackgroundLabel(value) {
    if (value === "transparent") {
      return "transparente";
    }
    if (value === "white") {
      return "blanco";
    }
    return "gris claro";
  }

  return {
    batchBackgroundLabel,
    batchSummaryLabel,
    bridgeScanMessage,
    detectedFormatLabel,
    exportActionLabel,
    imageCountLabel,
    omittedSummaryText,
    omissionReasonLabel,
    omissionSummaryText,
    outputCountLabel,
    readyBatchSummaryText,
    warningCountLabel,
  };
});
