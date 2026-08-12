(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotWorkbenchView = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  function countLabel(value, singular, plural) {
    const count = Math.max(0, Number(value) || 0);
    return `${count} ${count === 1 ? singular : plural}`;
  }

  function semanticBatchItems(options = {}) {
    const rows = [
      ["ready", options.ready, "lista", "listas", "ready"],
      ["warnings", options.warnings, "con aviso", "con aviso", "warning"],
      ["excluded", options.excluded, "excluida", "excluidas", "error"],
      ["customized", options.customized, "personalizada", "personalizadas", "info"],
    ];
    return rows
      .filter(([, value]) => Number(value) > 0)
      .map(([key, value, singular, plural, tone]) => ({
        key,
        label: countLabel(value, singular, plural),
        tone,
      }));
  }

  function semanticBatchText(options = {}) {
    return semanticBatchItems(options).map((item) => item.label).join(" · ");
  }

  function basename(path) {
    const parts = String(path || "").split(/[\\/]+/).filter(Boolean);
    return parts.at(-1) || "";
  }

  function context(label, value, fallback) {
    const normalized = String(value || "").trim() || fallback;
    return { label, value: normalized, title: normalized };
  }

  function headerContexts(options = {}) {
    const folderPath = String(options.folderPath || "").trim();
    return {
      folder: {
        label: "Carpeta",
        value: basename(folderPath) || "Sin lote",
        title: folderPath || "Sin lote",
      },
      preset: context("Preset", options.presetName, "Sin preset"),
      output: context("Salida", options.outputName, "Sin configurar"),
    };
  }

  return {
    headerContexts,
    semanticBatchItems,
    semanticBatchText,
  };
});
