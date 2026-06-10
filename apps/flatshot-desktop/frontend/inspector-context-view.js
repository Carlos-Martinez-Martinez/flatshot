(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotInspectorContextView = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function inspectorSubviewHeaderHtml(options = {}) {
    const detail = options.detail || "";
    const manageAction = options.showManageAction
      ? '<button type="button" data-action="open-preset-editor">Gestionar ajustes</button>'
      : "";
    return `
    <section class="inspector-subview-head">
      <div>
        <span>${escapeHtml(options.title || "Detalle")}</span>
        <strong>${escapeHtml(options.subtitle || "")}</strong>
        ${detail ? `<small>${escapeHtml(detail)}</small>` : ""}
      </div>
      ${manageAction}
      <button type="button" data-action="${escapeHtml(options.backAction || "close-inspector-subview")}">${escapeHtml(options.backLabel || "Volver")}</button>
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

  function inspectorSubviewHeaderState(options = {}) {
    const mode = options.mode || "summary";
    const isPresetManager = mode === "advanced" && Boolean(options.presetEditorOpen);
    const warningCount = Number(options.warningCount) || 0;
    const labels = {
      output: ["Salida", options.outputEditMode ? "Editar salida" : options.outputLabel],
      advanced: [
        isPresetManager ? "Gestionar ajustes" : "Editar ajuste",
        options.activePreset,
        options.presetSourceLabel,
      ],
      warnings: [
        "Revisar",
        warningCount ? `${warningCount} punto${warningCount === 1 ? "" : "s"}` : "Sin avisos",
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
        { state: "pending", title: "Destino de salida", detail: "Origen / _SALIDA_PRO" },
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
          <small>El ajuste activo y la salida se preparan automáticamente.</small>
        </div>
        ${preflightHtml}
        <div class="default-stack">
          <span>Salida</span>
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
    inspectorSubviewHeaderState,
    inspectorSubviewHeaderHtml,
  };
});
