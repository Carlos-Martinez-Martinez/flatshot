(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotPreflight = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  function countText(count, singular, plural = `${singular}s`) {
    const value = Number(count) || 0;
    return `${value} ${value === 1 ? singular : plural}`;
  }

  function readyImagesText(count) {
    const value = Number(count) || 0;
    return `${value} ${value === 1 ? "imagen lista" : "imágenes listas"}`;
  }

  function ignoredNeutralText(count = 0) {
    const value = Number(count) || 0;
    if (!value) {
      return "";
    }
    return `${value} ignorado${value === 1 ? "" : "s"} · no afectan`;
  }

  function ignoredImagesText(count = 0) {
    const value = Number(count) || 0;
    return `${value} ignorada${value === 1 ? "" : "s"}`;
  }

  function omissionSeverity(item, options = {}) {
    const ignoredReasons = options.ignoredReasons || new Set();
    const actionableReasons = options.actionableReasons || new Set();
    const severity = String(item?.severity || "").toLowerCase();
    if (["ignored", "warning", "error"].includes(severity)) {
      return severity;
    }
    const category = String(item?.category || "").toLowerCase();
    if (["ignored", "warning", "error"].includes(category)) {
      return category;
    }
    const reason = String(item?.reason || "");
    if (actionableReasons.has(reason)) {
      return "warning";
    }
    if (ignoredReasons.has(reason)) {
      return "ignored";
    }
    return "ignored";
  }

  function splitOmissions(omissions, options = {}) {
    const items = Array.isArray(omissions) ? omissions : [];
    return {
      ignored: items.filter((item) => omissionSeverity(item, options) === "ignored"),
      actionable: items.filter((item) => omissionSeverity(item, options) !== "ignored"),
    };
  }

  function imageWarningCount(images = []) {
    return images.filter((image) => image.status === "warning").length;
  }

  function excludedImageCount(images = [], exportItemStatuses = new Map()) {
    return images.filter((image) =>
      !image.exportable || image.status === "error" || exportItemStatuses.get(image.id)?.status === "error"
    ).length;
  }

  function calculateBatchCounts(input = {}) {
    const images = Array.isArray(input.images) ? input.images : [];
    const exportables = Array.isArray(input.exportables) ? input.exportables : [];
    const diagnostics = input.diagnostics || {};
    const omissions = Array.isArray(input.omissions) ? input.omissions : [];
    const exportItemStatuses = input.exportItemStatuses || new Map();
    const stateErrors = Array.isArray(input.stateErrors) ? input.stateErrors : [];
    const options = {
      ignoredReasons: input.ignoredReasons || new Set(),
      actionableReasons: input.actionableReasons || new Set(),
    };
    const omittedFiles = Number(diagnostics.totalOmitted || 0);
    const split = splitOmissions(omissions, options);
    const warningFiles = split.actionable.filter((item) => omissionSeverity(item, options) === "warning").length;
    const errorFiles = split.actionable.filter((item) => omissionSeverity(item, options) === "error").length;
    const filesFound = input.batch === "scanning"
      ? null
      : Math.max(
        Number(diagnostics.totalFiles || 0),
        Number(diagnostics.totalImages || 0) + omittedFiles,
        images.length + omittedFiles
      );
    const validImages = input.batch === "scanning"
      ? null
      : Math.max(Number(diagnostics.totalImages || 0), images.length);
    const exportedErrors = new Set(
      images
        .filter((image) => exportItemStatuses.get(image.id)?.status === "error")
        .map((image) => image.id)
    );
    const exportableWarningImages = imageWarningCount(exportables);
    const nonExportableImages = images.filter((image) =>
      !image.exportable || image.status === "error" || exportedErrors.has(image.id)
    ).length;
    const warningImages = exportableWarningImages;
    const readyImages = exportables.filter((image) =>
      !["warning", "error"].includes(image.status) && !exportedErrors.has(image.id)
    ).length;
    const stateErrorCount = stateErrors.filter((issue) => issue.level === "error").length;
    const stateWarnings = stateErrors.length - stateErrorCount;
    const blockingErrors = Number(input.blockingValidationIssueCount || 0)
      + stateErrorCount
      + errorFiles
      + (input.exportStatus === "failed" ? 1 : 0);
    const reviewIssues = warningImages + nonExportableImages + warningFiles + stateWarnings;

    return {
      filesFound,
      validImages,
      exportableImages: exportables.length,
      readyImages,
      warningImages,
      omittedFiles,
      ignoredFiles: split.ignored.length,
      warningFiles,
      errorFiles,
      nonExportableImages,
      blockingErrors,
      nonBlockingWarnings: reviewIssues,
      reviewIssues,
    };
  }

  function buildPreflightIssues(input = {}) {
    const issues = [
      ...(Array.isArray(input.validationIssues) ? input.validationIssues : []),
      ...(Array.isArray(input.stateErrors) ? input.stateErrors : []),
    ];
    const actionableOmitted = Array.isArray(input.actionableOmissions) ? input.actionableOmissions : [];
    const counts = input.counts || {};
    const warningImages = Number(input.warningImages || 0);
    const errorImages = Number(input.errorImages || 0);
    const exportableCount = Number(input.exportableCount || 0);
    const actionableOmissionSummary = String(input.actionableOmissionSummary || "");

    if (actionableOmitted.length > 0 && input.hasBatch) {
      issues.push({
        level: "warning",
        title: `${actionableOmitted.length} archivo${actionableOmitted.length === 1 ? "" : "s"} a revisar`,
        detail: actionableOmissionSummary,
      });
    }
    if (warningImages > 0) {
      issues.push({
        level: "warning",
        title: "Imágenes con aviso",
        detail: `${warningImages} imagen${warningImages === 1 ? "" : "es"} requiere${warningImages === 1 ? "" : "n"} revisión.`,
      });
    }
    if (errorImages > 0 && exportableCount > 0) {
      issues.push({
        level: "warning",
        title: "Imágenes excluidas",
        detail: `${errorImages} imagen${errorImages === 1 ? "" : "es"} quedará${errorImages === 1 ? "" : "n"} fuera de la salida.`,
      });
    }
    if (Number(counts.errorFiles || 0) > 0) {
      issues.push({
        level: "error",
        title: "Errores de lectura",
        detail: actionableOmissionSummary,
      });
    }

    return issues;
  }

  function preflightCounts(issues = []) {
    return {
      errors: issues.filter((issue) => issue.level === "error").length,
      warnings: issues.filter((issue) => issue.level !== "error").length,
    };
  }

  function isExportReady(input = {}) {
    const issues = Array.isArray(input.validationIssues) ? input.validationIssues : [];
    return issues.filter((issue) => issue.level === "error" || issue.title !== "Sin lote").length === 0
      && Boolean(input.hasBatch)
      && Number(input.exportableCount || 0) > 0;
  }

  function dedupeExportRisks(risks) {
    const seen = new Set();
    return risks.filter((risk) => {
      const key = risk.id || `${risk.title}-${risk.detail}`;
      if (seen.has(key)) {
        return false;
      }
      seen.add(key);
      return true;
    });
  }

  function issueMentionsExistingOutput(issue) {
    const text = `${issue?.title || ""} ${issue?.detail || ""}`.toLowerCase();
    return /ya existe|existente|existentes|sobrescri|overwrite|already exists|collision|colisi/.test(text);
  }

  return {
    buildPreflightIssues,
    calculateBatchCounts,
    countText,
    dedupeExportRisks,
    excludedImageCount,
    ignoredImagesText,
    ignoredNeutralText,
    imageWarningCount,
    isExportReady,
    issueMentionsExistingOutput,
    omissionSeverity,
    preflightCounts,
    readyImagesText,
    splitOmissions,
  };
});
