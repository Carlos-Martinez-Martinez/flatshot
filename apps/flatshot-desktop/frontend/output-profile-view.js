(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotOutputProfileView = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function outputProfileEditorHeadingHtml(options = {}) {
    const profile = options.profile || {};
    const validation = options.validation || { errors: [] };
    const errors = Array.isArray(validation.errors) ? validation.errors : [];
    const dirty = Boolean(options.dirty);
    const active = Boolean(options.active);
    const enabled = Boolean(profile.enabled);
    const summary = options.summary || "";
    const status = dirty
      ? "Cambios sin guardar"
      : active
        ? "Activo en este lote · Principal"
        : enabled
          ? "Salida activa"
          : "Formato guardado";

    return `
    <div class="format-editor-title">
      <div>
        <span class="eyebrow">Formato editado</span>
        <strong>${escapeHtml(profile.name || "Formato sin nombre")}</strong>
        <small>${escapeHtml(summary)}</small>
      </div>
      <span class="status-badge ${errors.length ? "error" : dirty ? "warning" : active ? "ready" : ""}">${escapeHtml(errors.length ? "Revisar campos" : status)}</span>
    </div>
  `;
  }

  function outputProfilePreviewHtml(options = {}) {
    const resultName = options.resultName || "imagen_original.jpg";
    const originalName = options.originalName || "imagen_original.png";
    const destination = options.destination || "junto al origen";
    const summary = options.summary || "";
    const resultPath = options.resultPath || resultName;

    return `
    <div class="format-preview-heading">
      <span class="eyebrow">Ejemplo</span>
      <strong>${escapeHtml(resultName)}</strong>
    </div>
    <div class="format-preview-grid">
      <div>
        <span>Original</span>
        <strong title="${escapeHtml(originalName)}">${escapeHtml(originalName)}</strong>
      </div>
      <div>
        <span>Resultado</span>
        <strong title="${escapeHtml(resultPath)}">${escapeHtml(resultPath)}</strong>
      </div>
      <div>
        <span>Formato</span>
        <strong>${escapeHtml(summary)}</strong>
      </div>
      <div>
        <span>Destino</span>
        <strong title="${escapeHtml(destination)}">${escapeHtml(destination)}</strong>
      </div>
    </div>
  `;
  }

  function outputProfileValidationHtml(validation = {}) {
    const errors = Array.isArray(validation.errors) ? validation.errors : [];
    const warnings = Array.isArray(validation.warnings) ? validation.warnings : [];
    if (!errors.length && !warnings.length) {
      return "";
    }
    const rows = [
      ...errors.map((message) => ({ tone: "error", message })),
      ...warnings.map((message) => ({ tone: "warning", message })),
    ];
    return `
    <strong>${errors.length ? "Revisa el formato" : "Aviso"}</strong>
    ${rows.map((row) => `<span class="${escapeHtml(row.tone)}">${escapeHtml(row.message)}</span>`).join("")}
  `;
  }

  function outputProfileManagerRowHtml(options = {}) {
    const profile = options.profile || {};
    const selected = Boolean(options.selected);
    const active = Boolean(options.active);
    const enabled = Boolean(options.enabled);
    const unsaved = Boolean(options.unsaved);
    const canToggle = Boolean(options.canToggle);
    const summary = options.summary || "";
    const destination = options.destination || "";
    const toggleTitle = canToggle
      ? "Activar esta salida en el lote"
      : unsaved
        ? "Guarda el formato para activarlo"
        : "Debe quedar al menos una salida activa";
    const marker = unsaved ? "Sin guardar" : active ? "Principal" : "";

    return `
      <div class="output-profile-option${selected ? " selected" : ""}${active ? " active" : ""}${enabled ? " enabled" : ""}">
        <label class="output-profile-toggle" title="${escapeHtml(toggleTitle)}">
          <input type="checkbox" data-output-profile-enabled-id="${escapeHtml(profile.id)}" ${enabled ? "checked" : ""} ${canToggle ? "" : "disabled"} />
          <span aria-hidden="true"></span>
        </label>
        <button type="button" class="output-profile-edit" data-output-profile-id="${escapeHtml(profile.id)}" title="${escapeHtml(`${profile.name} · ${summary}`)}">
          <span>
            <strong>${escapeHtml(profile.name)}</strong>
            <small>${escapeHtml(summary)}</small>
            <small>${escapeHtml(destination)}</small>
          </span>
          <em>${escapeHtml(marker)}</em>
        </button>
      </div>
    `;
  }

  function outputNameFromTemplate(profile = {}, options = {}) {
    const original = options.original || "imagen_original";
    const folder = options.folder || "lote";
    const index = Number(options.index) || 1;
    let outputName = String(profile.naming || "{original}{suffix}")
      .replaceAll("{original}", original)
      .replaceAll("{suffix}", profile.suffix || "")
      .replaceAll("{folder}", folder);
    outputName = outputName.replace(/\{index(?::0?(\d+)d)?\}/g, (_match, width) => {
      const digits = Number(width) || 1;
      return String(index).padStart(digits, "0");
    });
    if (!/\.[a-z0-9]+$/i.test(outputName)) {
      outputName = `${outputName}.${String(profile.format || "JPG").toLowerCase()}`;
    }
    return outputName;
  }

  function outputProfileFooterState(options = {}) {
    const validation = options.validation || { errors: [] };
    const errors = Array.isArray(validation.errors) ? validation.errors : [];
    const dirty = Boolean(options.dirty);
    const profileCount = Number(options.profileCount) || 0;
    const draft = options.draft || {};
    const isPersisted = Boolean(options.isPersisted);
    const deleteDisabled = isPersisted && profileCount <= 1;
    return {
      deleteDisabled,
      deleteTitle: deleteDisabled ? "Debe quedar al menos un formato" : "Eliminar formato seleccionado",
      resetDisabled: !dirty,
      saveDisabled: errors.length > 0 || !dirty,
      applyDisabled: errors.length > 0,
      applyLabel: dirty
        ? "Guardar y aplicar"
        : draft.enabled
          ? "Aplicar cambios al lote"
          : "Activar en este lote",
      noteClass: `settings-footer-note ${errors.length ? "error" : dirty ? "warning" : ""}`,
      noteText: errors.length
        ? errors[0]
        : dirty
          ? "Cambios sin guardar"
          : "Sin cambios pendientes",
    };
  }

  return {
    escapeHtml,
    outputNameFromTemplate,
    outputProfileEditorHeadingHtml,
    outputProfileFooterState,
    outputProfileManagerRowHtml,
    outputProfilePreviewHtml,
    outputProfileValidationHtml,
  };
});
