(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotBatchView = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const escapeHtml = globalThis.FlatShotFormatters?.escapeHtml || function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  };

  function warningCountLabel(count) {
    return `${count} aviso${count === 1 ? "" : "s"}`;
  }

  function imageCountLabel(count) {
    return `${count} ${count === 1 ? "imagen" : "imágenes"}`;
  }

  function exportActionLabel(imageCount, outputCount = 1) {
    if (outputCount > 1) {
      return `Procesar ${imageCount * outputCount} archivos`;
    }
    return `Procesar ${imageCount} imágenes`;
  }

  function outputCountLabel(count) {
    return `${count} formato${count === 1 ? "" : "s"}`;
  }

  function adjustedCountLabel(count) {
    const value = Number(count) || 0;
    return `${value} ajustada${value === 1 ? "" : "s"}`;
  }

  function batchPillState(options = {}) {
    const issueCount = Number(options.issueCount) || 0;
    const adjustedCount = Number(options.adjustedCount) || 0;
    if (issueCount) {
      return { label: warningCountLabel(issueCount), tone: "warning" };
    }
    if (adjustedCount) {
      return { label: adjustedCountLabel(adjustedCount), tone: "active" };
    }
    return { label: "Listo", tone: "ready" };
  }

  function sidebarLotSummaryText(options = {}) {
    if (options.batch === "scanning") {
      return options.scanStatus || "Leyendo imágenes";
    }
    if (options.batch === "empty") {
      return "No hay PNG válidos";
    }
    if (!options.hasBatch) {
      return "Sin carpeta";
    }
    const parts = [options.readyLabel || ""].filter(Boolean);
    const warnings = Number(options.nonBlockingWarnings) || 0;
    if (warnings) {
      parts.push(warningCountLabel(warnings));
    }
    return parts.join(" · ");
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
    const custom = /^rgb\s*:\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})$/i.exec(String(value || "").trim());
    if (custom) {
      return `RGB ${custom.slice(1).join(", ")}`;
    }
    if (value === "transparent") {
      return "transparente";
    }
    if (value === "white") {
      return "blanco";
    }
    return "gris claro";
  }

  function batchDestinationLine(options = {}) {
    const profileDestinations = Array.isArray(options.profileDestinations) ? options.profileDestinations : [];
    if (profileDestinations.length > 1) {
      const destinations = Array.from(new Set(profileDestinations));
      return destinations.length === 1 ? destinations[0] : `${destinations.length} destinos`;
    }
    if (options.destinationMode === "custom") {
      return options.destinationValue || "Sin destino";
    }
    return options.destinationValue ? `Junto al origen · ${options.destinationValue}` : "Junto al origen";
  }

  function batchOutputLine(options = {}) {
    const profileLines = Array.isArray(options.profileLines) ? options.profileLines : [];
    if (profileLines.length > 1) {
      return profileLines.join(" · ");
    }
    const size = String(options.size || "1800x2400").replace("x", " × ");
    return `${options.format || "JPG"} · ${size} · ${batchBackgroundLabel(options.background)}`;
  }

  function outputProfilesSummaryLabel(options = {}) {
    const profileLabels = Array.isArray(options.profileLabels) ? options.profileLabels : [];
    if (profileLabels.length > 1) {
      return profileLabels.join(" · ");
    }
    const size = options.sizeLabel || String(options.size || "1800x2400").replace("x", "×");
    const background = options.backgroundLabel || batchBackgroundLabel(options.background);
    return `${options.format || "JPG"} · ${size} · ${background}`;
  }

  function sourceInputDetail(batch, filesLabel, validLabel) {
    if (batch === "none") {
      return "Pendiente";
    }
    if (batch === "scanning") {
      return "Leyendo imágenes";
    }
    return `${filesLabel} archivos encontrados · ${validLabel} imágenes listas`;
  }

  function batchSummaryToneClass(tone) {
    if (tone === "error") {
      return "is-error";
    }
    if (tone === "warning") {
      return "is-warning";
    }
    if (tone === "busy") {
      return "is-busy";
    }
    if (tone === "ready") {
      return "is-ready";
    }
    return "is-idle";
  }

  function batchMetricHtml(label, value) {
    return `
    <div class="batch-metric">
      <span>${escapeHtml(label)}</span>
      <strong title="${escapeHtml(value)}">${escapeHtml(value)}</strong>
    </div>
  `;
  }

  function diagnosticsHtml(options = {}) {
    const diagnostics = options.diagnostics || {};
    const open = options.hasScanError ? " open" : "";
    const reasonRows = Object.entries(diagnostics.omittedByReason || {}).map(([reason, count]) => `
    <div class="diagnostic-row">
      <span>${escapeHtml(omissionReasonLabel(reason))}</span>
      <strong>${escapeHtml(count)}</strong>
    </div>
  `).join("");
    const sampleRows = (diagnostics.omitted || []).slice(0, 5).map((item) => `
    <li title="${escapeHtml(item.path || item.name)}">
      <span>${escapeHtml(item.name)}</span>
      <small>${escapeHtml(item.detail || omissionReasonLabel(item.reason))}</small>
    </li>
  `).join("");
    return `
    <details class="batch-diagnostics"${open}>
      <summary>${escapeHtml(diagnostics.totalOmitted ? "Ver diagnóstico" : "Diagnóstico")}</summary>
      <div class="diagnostic-reasons">${reasonRows}</div>
      ${sampleRows ? `<ul>${sampleRows}</ul>` : ""}
    </details>
  `;
  }

  function batchSummaryHtml(options = {}) {
    const counts = options.counts || {};
    const visible = options.visible || {};
    const diagnostics = options.diagnostics || {};
    const filesLabel = counts.filesFound === null ? "Leyendo" : counts.filesFound;
    const validLabel = counts.validImages === null ? "Leyendo" : counts.validImages;
    const outputLine = options.outputLine || "";
    const destinationLine = options.destinationLine || "";
    const sourceTitle = options.sourcePath || visible.subtitle || "";
    const outputDetail = `${outputLine} · ${destinationLine}`;
    const diagnosticBlock = diagnostics.totalOmitted || counts.blockingErrors
      ? diagnosticsHtml({ diagnostics, hasScanError: options.hasScanError })
      : `<div class="diagnostic-ok">${counts.nonBlockingWarnings ? "Avisos en la galería" : "Sin avisos"}</div>`;

    return `
    <div class="batch-summary-card ${batchSummaryToneClass(visible.tone)}">
      <div class="batch-summary-section">
        <span class="batch-rail__section-title">Entrada</span>
        <strong title="${escapeHtml(sourceTitle)}">${escapeHtml(options.sourceFolderName || "")}</strong>
        <small title="${escapeHtml(sourceTitle)}">${escapeHtml(sourceInputDetail(options.batch, filesLabel, validLabel))}</small>
      </div>

      <div class="batch-metric-grid" aria-label="Datos del lote">
        ${batchMetricHtml("Archivos encontrados", filesLabel)}
        ${batchMetricHtml("Imágenes listas", counts.readyImages)}
        ${batchMetricHtml("Excluidas", counts.nonExportableImages)}
        ${batchMetricHtml("Ignorados", counts.ignoredFiles)}
      </div>

      <div class="batch-summary-section">
        <span class="batch-rail__section-title">Estado del lote</span>
        <strong>${escapeHtml(visible.title || "")}</strong>
        <small title="${escapeHtml(visible.subtitle || "")}">${escapeHtml(visible.subtitle || "")}</small>
      </div>

      <div class="batch-summary-lines batch-summary-lines--compact">
        <div class="batch-summary__line">
          <span>Listas</span>
          <strong>${escapeHtml(counts.readyImages)}</strong>
        </div>
        <div class="batch-summary__line">
          <span>Avisos</span>
          <strong>${escapeHtml(counts.reviewIssues)}</strong>
        </div>
        <div class="batch-summary__line">
          <span>Bloqueos</span>
          <strong>${escapeHtml(counts.blockingErrors)}</strong>
        </div>
      </div>

      <div class="batch-summary-section">
        <span class="batch-rail__section-title">Salida</span>
        <strong title="${escapeHtml(outputLine)}">${escapeHtml(options.outputProfileName || "")}</strong>
        <small title="${escapeHtml(outputDetail)}">${escapeHtml(outputDetail)}</small>
      </div>

      <div class="batch-summary-lines">
        <div class="batch-summary__line">
          <span>Nombre de archivo</span>
          <strong title="${escapeHtml(options.namingExample || "")}">${escapeHtml(options.namingLabel || "")}</strong>
        </div>
        <div class="batch-summary__line">
          <span>Avisos</span>
          <strong>${escapeHtml(options.warningsLabel || "Sin avisos")}</strong>
        </div>
        <div class="batch-summary__line">
          <span>Ignorados</span>
          <strong>${escapeHtml(options.ignoredLabel || "Sin ignorados")}</strong>
        </div>
      </div>

      <div class="batch-next">
        <span>Siguiente</span>
        <strong>${escapeHtml(visible.nextStep || "")}</strong>
      </div>
      ${diagnosticBlock}
    </div>
  `;
  }

  return {
    adjustedCountLabel,
    batchBackgroundLabel,
    batchDestinationLine,
    batchMetricHtml,
    batchOutputLine,
    batchPillState,
    batchSummaryHtml,
    batchSummaryLabel,
    batchSummaryToneClass,
    bridgeScanMessage,
    detectedFormatLabel,
    diagnosticsHtml,
    escapeHtml,
    exportActionLabel,
    imageCountLabel,
    omittedSummaryText,
    omissionReasonLabel,
    omissionSummaryText,
    outputProfilesSummaryLabel,
    outputCountLabel,
    readyBatchSummaryText,
    sidebarLotSummaryText,
    sourceInputDetail,
    warningCountLabel,
  };
});
