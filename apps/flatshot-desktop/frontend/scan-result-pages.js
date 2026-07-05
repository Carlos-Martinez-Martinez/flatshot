(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotScanResultPages = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const DEFAULT_SCAN_RESULT_PAGE_SIZE = 500;

  function scanJobStatusUrl(jobId, offset = 0, pageSize = DEFAULT_SCAN_RESULT_PAGE_SIZE) {
    return `/folders/scan/jobs/${encodeURIComponent(jobId)}?imageOffset=${offset}&imageLimit=${pageSize}`;
  }

  function scanJobCancelUrl(jobId) {
    return `/folders/scan/jobs/${encodeURIComponent(jobId)}/cancel`;
  }

  function scanJobPayload(folders, state = {}) {
    return {
      folders,
      imageOverrides: state.imageOverrides,
      recursive: Boolean(state.scanRecursive),
      scanMode: "verified",
    };
  }

  function scanJobDelay(delayMs, setTimeoutFn = globalThis.setTimeout) {
    return new Promise((resolve) => setTimeoutFn(resolve, delayMs));
  }

  function nextScanResultOffset(page = {}) {
    return Number(page.imageOffset || 0) + Number(page.imageCount || 0);
  }

  function isScanCancelledError(error) {
    return String(error?.message || "").toLowerCase().includes("escaneo cancelado");
  }

  function isScanJobUnsupportedError(error) {
    const message = String(error?.message || "").toLowerCase();
    return message.includes("not found")
      || message.includes("no encontrado")
      || message.includes("use post")
      || message.includes("method")
      || message.includes("http 404")
      || message.includes("http 405");
  }

  function mergeBridgeScanResultPages(baseResult = {}, nextResult = {}) {
    const mergedFolders = (baseResult.folders || []).map((folder) => {
      const nextFolder = (nextResult.folders || []).find((candidate) => candidate.path === folder.path);
      return {
        ...folder,
        images: [
          ...(Array.isArray(folder.images) ? folder.images : []),
          ...(Array.isArray(nextFolder?.images) ? nextFolder.images : []),
        ],
      };
    });
    (nextResult.folders || []).forEach((folder) => {
      if (!mergedFolders.some((candidate) => candidate.path === folder.path)) {
        mergedFolders.push(folder);
      }
    });
    return {
      ...baseResult,
      ...nextResult,
      folders: mergedFolders,
    };
  }

  return {
    DEFAULT_SCAN_RESULT_PAGE_SIZE,
    isScanCancelledError,
    isScanJobUnsupportedError,
    mergeBridgeScanResultPages,
    nextScanResultOffset,
    scanJobCancelUrl,
    scanJobDelay,
    scanJobPayload,
    scanJobStatusUrl,
  };
});
