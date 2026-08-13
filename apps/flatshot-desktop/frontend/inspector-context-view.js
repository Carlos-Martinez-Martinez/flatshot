(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotInspectorContextView = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const formatterHelpers = globalThis.FlatShotFormatters
    || (typeof require === "function" ? require("./formatters.js") : null);
  const escapeHtml = (value) => formatterHelpers.escapeHtml(value);

  function inspectorSubviewHeaderHtml(options = {}) {
    const detail = options.detail || "";
    const manageAction = options.showManageAction
      ? '<button type="button" data-action="open-preset-editor">Gestionar ajustes</button>'
      : "";
    const backAction = options.showBackAction
      ? `<button type="button" data-action="${escapeHtml(options.backAction || "close-inspector-subview")}">${escapeHtml(options.backLabel || "Volver")}</button>`
      : "";
    return `
    <section class="inspector-pane-head">
      <div class="inspector-pane-head__copy">
        <h2>${escapeHtml(options.title || "Detalle")}</h2>
        <strong>${escapeHtml(options.subtitle || "")}</strong>
        ${detail ? `<small>${escapeHtml(detail)}</small>` : ""}
      </div>
      ${manageAction || backAction ? `<div class="inspector-pane-head__actions">${manageAction}${backAction}</div>` : ""}
    </section>
  `;
  }

  function inspectorMode(options = {}) {
    if (options.outputEditMode || options.inspectorTab === "output") {
      return "output";
    }
    if (options.inspectorTab === "advanced") {
      return "advanced";
    }
    if (options.inspectorTab === "warnings") {
      return "warnings";
    }
    return "summary";
  }

  function inspectorSummaryCardKeys(options = {}) {
    return ["selectedImage"];
  }

  function inspectorSubviewHeaderState(options = {}) {
    const mode = options.mode || "summary";
    const isPresetManager = mode === "advanced" && Boolean(options.presetEditorOpen);
    const warningCount = Number(options.warningCount) || 0;
    const ignoredCount = Number(options.ignoredCount) || 0;
    const labels = {
      output: options.outputEditMode
        ? ["Editar salida", options.outputLabel, "Los cambios afectan solo a esta salida."]
        : ["Exportación", options.outputLabel, "Salidas y destino del lote"],
      advanced: [
        isPresetManager ? "Gestionar ajustes" : "Aspecto",
        options.activePreset,
        options.presetSourceLabel,
      ],
      warnings: [
        "Avisos",
        warningCount ? `${warningCount} por revisar` : "Todo listo",
        warningCount
          ? "No bloquean la exportación"
          : ignoredCount
            ? `${ignoredCount} archivo${ignoredCount === 1 ? "" : "s"} ignorado${ignoredCount === 1 ? "" : "s"}`
            : "Sin incidencias",
      ],
    };
    const [title, subtitle, detail = ""] = labels[mode] || ["Detalle", ""];
    return {
      title,
      subtitle,
      detail,
      backAction: options.outputEditMode
        ? "cancel-output-edit"
        : isPresetManager
          ? "close-preset-editor"
          : "close-inspector-subview",
      backLabel: options.outputEditMode ? "Cancelar" : "Volver",
      showManageAction: mode === "advanced" && !isPresetManager,
      showBackAction: Boolean(options.outputEditMode || isPresetManager),
    };
  }

  function contextualPreflightRows(options = {}) {
    if (options.batch === "scanning") {
      return [
        { state: "pending", title: "Carpeta seleccionada", detail: "Leyendo origen" },
        { state: "pending", title: "Imágenes listas", detail: "Contando archivos" },
        { state: "pending", title: "Destino", detail: "Se configurará después" },
      ];
    }
    if (options.batch === "none") {
      return [
        { state: "pending", title: "Carpeta seleccionada", detail: "Pendiente" },
        { state: "pending", title: "Imágenes listas", detail: "Pendiente" },
        { state: "pending", title: "Destino de salida", detail: "Origen / Salida" },
      ];
    }
    if (options.batch === "empty") {
      const totalFiles = Number(options.totalFiles) || 0;
      return [
        {
          state: "warning",
          title: "Carpeta revisada",
          detail: totalFiles ? `${totalFiles} archivos encontrados` : "Sin archivos compatibles",
        },
        { state: "error", title: "Imágenes exportables", detail: "0 imágenes" },
        { state: "pending", title: "Ignorados", detail: options.ignoredSummary || "Sin archivos ignorados" },
        { state: "pending", title: "Destino", detail: "Pendiente hasta cargar un lote" },
      ];
    }
    return [];
  }

  function contextualInspectorHtml(options = {}) {
    const state = options.batch || "ready";
    const preflightHtml = options.preflightHtml || "";
    if (state === "scanning") {
      return `
      <div class="context-panel">
        <div class="context-header">
          <span class="eyebrow">Preparación</span>
          <strong>Escaneando carpeta</strong>
          <small>${escapeHtml(options.scanStatus || "Leyendo imágenes")}</small>
        </div>
        ${options.progressHtml || ""}
        ${preflightHtml}
      </div>
    `;
    }

    if (state === "none") {
      return `
      <div class="context-panel">
        <div class="context-header">
          <span class="eyebrow">Preparación</span>
          <strong>Seleccionar carpeta</strong>
          <small>El ajuste de imagen y las salidas se preparan automáticamente.</small>
        </div>
        ${preflightHtml}
        <div class="default-stack">
          <span>Exportación</span>
          <strong>${escapeHtml(options.outputSummary || "")}</strong>
          <small>Ajuste ${escapeHtml(options.activePreset || "")}</small>
        </div>
        <button type="button" class="primary" data-action="pick-bridge-folder">Seleccionar carpeta</button>
      </div>
    `;
    }

    if (state === "empty") {
      return `
      <div class="context-panel warning">
        <div class="context-header">
          <span class="eyebrow">Salida</span>
          <strong>Exportación bloqueada</strong>
          <small>${escapeHtml(options.scanStatus || "La carpeta no contiene imágenes procesables.")}</small>
        </div>
        ${preflightHtml}
        <button type="button" class="primary" data-action="pick-bridge-folder">Elegir otra carpeta</button>
      </div>
    `;
    }

    return `
    <div class="context-panel">
      <div class="context-header">
        <strong>Selecciona una imagen</strong>
        <small>${escapeHtml(options.compactStatus || "")}</small>
      </div>
      <button type="button" class="primary" data-action="select-first-image">Seleccionar primera imagen</button>
    </div>
  `;
  }

  return {
    contextualInspectorHtml,
    contextualPreflightRows,
    escapeHtml,
    inspectorMode,
    inspectorSummaryCardKeys,
    inspectorSubviewHeaderState,
    inspectorSubviewHeaderHtml,
  };
});
