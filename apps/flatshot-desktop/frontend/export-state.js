(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotExportState = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  function exportStartState(options = {}) {
    const patch = {
      exportStatus: "running",
      progress: 0,
      processed: 0,
      exportJobId: null,
      exportDestinations: [],
      exportMessages: [],
      exportCompletedItems: [],
      exportFailedItems: [],
      exportIssues: [],
      exportResult: null,
      errors: [],
      paused: false,
      statusText: "Preparando exportación",
    };
    if (Object.prototype.hasOwnProperty.call(options, "scenario")) {
      patch.scenario = options.scenario;
    }
    if (options.resetConfirm) {
      patch.exportConfirmOpen = false;
      patch.exportConfirmRisks = [];
      patch.exportConfirmOptions = null;
    }
    return patch;
  }

  function bridgeRunFailureState(message) {
    return {
      exportStatus: "failed",
      progress: 0,
      processed: 0,
      exportIssues: [{ level: "error", title: "Exportación fallida", detail: message }],
      exportResult: null,
      errors: [{ level: "error", title: "Exportación fallida", detail: message }],
      statusText: "Exportación fallida",
    };
  }

  function bridgeProgressUnavailableState(message) {
    return {
      exportStatus: "failed",
      paused: false,
      errors: [{ level: "error", title: "Progreso no disponible", detail: message }],
      statusText: "Progreso no disponible",
    };
  }

  function stoppedExportState() {
    return {
      exportStatus: "failed",
      paused: false,
      errors: [{ level: "error", title: "Exportación detenida", detail: "No se generaron más archivos." }],
      statusText: "Exportación fallida",
    };
  }

  function normalizeBridgeIssue(issue) {
    const source = issue && typeof issue === "object" ? issue : {};
    return {
      level: source.level === "error" ? "error" : "warning",
      title: String(source.title || "Exportación"),
      detail: String(source.detail || "Revisa el resultado."),
    };
  }

  function bridgeStatusPatch(payload = {}, previous = {}) {
    const progress = payload.progress || {};
    const processed = Number(progress.processed) || 0;
    const patch = {
      exportJobId: payload.jobId || previous.exportJobId,
      exportDestinations: Array.isArray(payload.destinations) ? payload.destinations : previous.exportDestinations,
      exportMessages: Array.isArray(payload.messages) ? payload.messages : previous.exportMessages,
      exportCompletedItems: Array.isArray(payload.completedItems) ? payload.completedItems : previous.exportCompletedItems,
      exportFailedItems: Array.isArray(payload.failedItems) ? payload.failedItems : previous.exportFailedItems || [],
      exportIssues: Array.isArray(payload.issues) ? payload.issues.map(normalizeBridgeIssue) : previous.exportIssues,
      exportResult: payload.result || previous.exportResult,
      progress: Number(progress.percent) || 0,
      processed,
      paused: payload.status === "paused",
    };

    if (payload.status === "completed") {
      patch.exportStatus = "completed";
      patch.progress = 0;
      patch.statusText = `Exportación completada · ${processed}/${progress.total || processed}`;
    } else if (payload.status === "partial") {
      patch.exportStatus = "partial";
      patch.progress = 0;
      patch.statusText = "Exportación con avisos";
    } else if (payload.status === "failed" || payload.status === "cancelled") {
      patch.exportStatus = "failed";
      patch.progress = 0;
      patch.paused = false;
      patch.statusText = payload.status === "cancelled" ? "Exportación cancelada" : "Exportación fallida";
    } else if (payload.status === "paused") {
      patch.exportStatus = "running";
      patch.statusText = "Pausado";
    } else if (payload.status === "cancelling") {
      patch.exportStatus = "running";
      patch.statusText = "Deteniendo...";
    } else {
      patch.exportStatus = "running";
      patch.statusText = `Procesando ${processed}/${progress.total || "..."}`;
    }

    return patch;
  }

  function bridgeStatusErrors(payload = {}, completedItems = [], exportIssues = []) {
    const failedItems = completedItems.filter((item) => !item.success);
    if (!["partial", "failed", "cancelled"].includes(payload.status) && !failedItems.length && !exportIssues.length) {
      return [];
    }
    const messageItems = (payload.messages || []).slice(-4).map((message) => ({
      level: payload.status === "partial" ? "warning" : "error",
      title: "Exportación",
      detail: message,
    }));
    const itemErrors = failedItems.slice(-4).map((item) => ({
      level: "error",
      title: item.name || "Imagen",
      detail: "No se pudo exportar.",
    }));
    return exportIssues.length ? exportIssues : [...itemErrors, ...messageItems];
  }

  return {
    bridgeProgressUnavailableState,
    bridgeRunFailureState,
    bridgeStatusErrors,
    bridgeStatusPatch,
    exportStartState,
    normalizeBridgeIssue,
    stoppedExportState,
  };
});
