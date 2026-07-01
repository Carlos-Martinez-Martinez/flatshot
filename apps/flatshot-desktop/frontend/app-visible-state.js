function batchSummaryLabel() {
  return batchViewHelpers.batchSummaryLabel({
    batch: state.batch,
    count: activeImages().length,
    warnings: visibleWarningCount(),
  });
}

function firstBlockingIssue() {
  return preflightIssues().find((issue) => issue.level === "error")
    || preflightIssues()[0]
    || null;
}

function getVisibleAppState() {
  const counts = batchCounts();
  const blockers = blockingValidationIssues();
  const hasWarnings = counts.nonBlockingWarnings > 0;
  const output = batchOutputLine();
  const destination = batchDestinationLine();
  const summary = readyBatchSummaryText(counts);

  if (state.exportStatus === "running") {
    const total = plannedExportTotal() || counts.exportableImages;
    return {
      id: "exporting",
      tone: "busy",
      title: state.paused ? "Exportación pausada" : "Exportando lote",
      subtitle: state.paused ? `Pausado · ${state.processed}/${total}` : `Procesando ${state.processed}/${total}`,
      topSummary: compactHeaderStatusText(),
      primaryAction: { label: state.paused ? "Exportación pausada" : "Exportando...", action: "", enabled: false },
      secondaryAction: { label: "Detener", action: "stop-export", enabled: true },
      nextStep: state.paused ? "Reanudar o detener" : "Esperar a que termine la exportación",
      counts,
    };
  }

  if (state.exportStatus === "completed" || state.exportStatus === "partial") {
    const processed = Number(state.exportResult?.processed ?? state.processed ?? counts.exportableImages);
    const total = Number(state.exportResult?.total ?? counts.exportableImages);
    return {
      id: "export_done",
      tone: state.exportStatus === "partial" ? "warning" : "ready",
      title: state.exportStatus === "partial" ? "Exportación finalizada con avisos" : "Exportación finalizada",
      subtitle: `${processed}/${total} imágenes exportadas · ${destination}`,
      topSummary: compactHeaderStatusText(),
      primaryAction: { label: "Abrir destino", action: "open-output", enabled: Boolean(outputDestinationToOpen()) },
      secondaryAction: { label: "Exportar de nuevo", action: "start-export", enabled: isExportReady() },
      nextStep: outputDestinationToOpen() ? "Abrir carpeta de salida" : "Revisar resultado de exportación",
      counts,
    };
  }

  if (state.exportStatus === "failed") {
    const issue = firstBlockingIssue();
    return {
      id: "ready_with_blockers",
      tone: "error",
      title: "Exportación con errores",
      subtitle: issue?.detail || "Revisa el detalle antes de continuar.",
      topSummary: compactHeaderStatusText(),
      primaryAction: { label: "Ver error", action: "review-warnings", enabled: true },
      secondaryAction: isExportReady() ? { label: "Exportar de nuevo", action: "start-export", enabled: true } : null,
      nextStep: "Revisar error",
      counts,
    };
  }

  if (state.batch === "scanning") {
    return {
      id: "scanning",
      tone: "busy",
      title: "Escaneando carpeta...",
      subtitle: state.scanStatus || "Leyendo imágenes",
      topSummary: compactHeaderStatusText(),
      primaryAction: { label: "Escaneando", action: "", enabled: false },
      secondaryAction: null,
      nextStep: "Escaneando carpeta",
      counts,
    };
  }

  if (state.batch === "none") {
    return {
      id: "no_folder",
      tone: "idle",
      title: "Sin lote",
      subtitle: "Selecciona una carpeta para empezar",
      topSummary: compactHeaderStatusText(),
      primaryAction: { label: "Seleccionar carpeta", action: "pick-bridge-folder", enabled: state.bridgeStatus !== "checking" },
      secondaryAction: null,
      nextStep: "Seleccionar carpeta",
      counts,
    };
  }

  if (state.batch === "empty") {
    const hasFoundFiles = counts.filesFound > 0 || counts.omittedFiles > 0;
    return {
      id: hasFoundFiles ? "scan_empty" : "batch_empty",
      tone: "warning",
      title: "No hay PNG válidos",
      subtitle: hasFoundFiles
        ? `${preflightHelpers.countText(counts.filesFound, "archivo encontrado", "archivos encontrados")}${counts.ignoredFiles ? ` · ${ignoredNeutralText(counts.ignoredFiles)}` : ""}`
        : "No hay archivos compatibles en esta carpeta.",
      topSummary: compactHeaderStatusText(),
      primaryAction: { label: "Elegir otra carpeta", action: "pick-bridge-folder", enabled: state.bridgeStatus !== "checking" },
      secondaryAction: counts.reviewIssues ? { label: "Revisar avisos", action: "review-warnings", enabled: true } : null,
      nextStep: "Elegir otra carpeta",
      counts,
    };
  }

  if (blockers.length) {
    const issue = blockers[0];
    return {
      id: "ready_with_blockers",
      tone: "error",
      title: "Exportación bloqueada",
      subtitle: issue.detail || "Hay un problema que impide exportar.",
      topSummary: compactHeaderStatusText(),
      primaryAction: { label: "Revisar errores", action: "review-output", enabled: true },
      secondaryAction: null,
      nextStep: "Resolver problemas",
      counts,
    };
  }

  if (hasWarnings) {
    return {
      id: "ready_with_warnings",
      tone: "warning",
      title: "Lote listo",
      subtitle: `${summary} · ${preflightHelpers.countText(counts.nonBlockingWarnings, "aviso", "avisos")}`,
      topSummary: compactHeaderStatusText(),
      primaryAction: { label: exportActionLabel(counts.exportableImages), action: "start-export", enabled: isExportReady() },
      secondaryAction: { label: "Revisar avisos", action: "review-warnings", enabled: true },
      nextStep: exportActionLabel(counts.exportableImages),
      counts,
    };
  }

  return {
    id: counts.ignoredFiles ? "ready_with_omitted" : "ready",
    tone: "ready",
    title: "Lote listo",
    subtitle: `${summary}${counts.ignoredFiles ? ` · ${ignoredNeutralText(counts.ignoredFiles)}` : ""} · ${output} · ${destination}`,
    topSummary: compactHeaderStatusText(),
    primaryAction: { label: exportActionLabel(counts.exportableImages), action: "start-export", enabled: isExportReady() },
    secondaryAction: null,
    nextStep: exportActionLabel(counts.exportableImages),
    counts,
  };
}

function readyBatchSummaryText(counts = batchCounts()) {
  const readyText = preflightHelpers.readyImagesText(counts.filesFound > 0 || counts.exportableImages > 0 ? counts.exportableImages : 0);
  return batchViewHelpers.readyBatchSummaryText(counts, batchViewHelpers.detectedFormatLabel(activeImages()), readyText);
}
