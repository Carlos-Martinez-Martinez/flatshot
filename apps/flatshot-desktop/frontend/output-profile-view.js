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
    const enabled = Boolean(options.enabled);

    return `
    <div class="format-editor-title">
      <div>
        <span class="eyebrow">Formato seleccionado</span>
        <strong>${escapeHtml(profile.name || "Formato sin nombre")}</strong>
      </div>
      <div class="format-editor-controls">
        ${errors.length ? `<span class="status-badge error">${escapeHtml("Revisar campos")}</span>` : ""}
        <label class="output-profile-toggle format-editor-toggle" title="${escapeHtml("Usar este formato en el lote")}">
          <span class="switch-label">Usar en este lote</span>
          <input type="checkbox" data-output-profile-draft-enabled ${enabled ? "checked" : ""} />
          <span class="switch-track" aria-hidden="true"></span>
        </label>
      </div>
    </div>
  `;
  }

  function outputProfilePreviewHtml(options = {}) {
    const resultName = options.resultName || "imagen_original.jpg";
    const originalName = options.originalName || "imagen_original.png";
    const resultPath = options.resultPath || resultName;

    return `
    <div class="format-preview-heading">
      <span class="eyebrow">Ejemplo de salida</span>
    </div>
    <div class="format-preview-flow">
      <strong title="${escapeHtml(originalName)}" aria-label="Original: ${escapeHtml(originalName)}">${escapeHtml(originalName)}</strong>
      <span class="format-preview-arrow" aria-hidden="true">→</span>
      <code title="${escapeHtml(resultPath)}" aria-label="Resultado: ${escapeHtml(resultPath)}">${escapeHtml(resultPath)}</code>
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
    const enabled = Boolean(options.enabled);
    const dirty = Boolean(options.dirty);
    const title = dirty ? `${profile.name || "Formato"} · Cambios sin guardar` : profile.name || "Formato";

    return `
      <article class="output-profile-option${selected ? " selected" : ""}${enabled ? " enabled" : ""}${dirty ? " is-unsaved" : ""}">
        <button type="button" class="output-profile-edit" data-output-profile-id="${escapeHtml(profile.id)}" title="${escapeHtml(title)}">
          <span class="output-profile-text">
            <span class="output-profile-mainline">
              <strong>${escapeHtml(profile.name)}</strong>
            </span>
            ${dirty ? '<span class="visually-hidden">Cambios sin guardar</span>' : ""}
          </span>
        </button>
      </article>
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

  function basename(path) {
    return String(path || "").split(/[\\/]/).filter(Boolean).pop() || "";
  }

  function imageFileStem(name) {
    return basename(name).replace(/\.[^.\\/]+$/, "") || basename(name) || "Imagen";
  }

  function folderNameForImage(image = {}, folders = []) {
    const folderItems = Array.isArray(folders) ? folders : [];
    return folderItems.find((item) => item.id === image?.folderId)?.name
      || folderItems[0]?.name
      || "lote";
  }

  function outputNameForImage(options = {}) {
    if (!String(options.naming || "").trim()) {
      return "Nombre de archivo pendiente";
    }
    const image = options.image || {};
    return outputNameFromTemplate({
      naming: options.naming,
      suffix: options.suffix || "_PRO",
      format: options.format || "JPG",
    }, {
      original: imageFileStem(image?.name || "imagen_001.png"),
      folder: folderNameForImage(image, options.folders),
      index: options.index || 1,
    });
  }

  function outputNameForProfile(profile = {}, options = {}) {
    const image = options.image || {};
    return outputNameFromTemplate(profile, {
      original: imageFileStem(image?.name || options.fallbackImageName || "imagen_original.png"),
      folder: folderNameForImage(image, options.folders),
      index: options.index || 1,
    });
  }

  function profileDestinationLabel(profile) {
    if (!profile) {
      return "Sin destino";
    }
    if (profile.destinationMode === "custom") {
      return profile.destinationValue || "Carpeta personalizada";
    }
    return profile.destinationValue || "Salida";
  }

  function profileDestinationPreviewLabel(profile) {
    const destination = profileDestinationLabel(profile);
    if (profile?.destinationMode === "custom") {
      return destination;
    }
    return destination ? destination : "junto al origen";
  }

  function destinationCompactLabel(options = {}) {
    if (options.destinationMode === "custom") {
      return options.destinationValue || "Sin destino";
    }
    return options.destinationValue || "Salida";
  }

  function namingHumanLabel(options = {}) {
    if (options.naming === "{original}{suffix}") {
      return options.suffix ? `original + ${options.suffix}` : "original";
    }
    return options.naming || "Sin plantilla";
  }

  function namingExample(options = {}) {
    if (!String(options.naming || "").trim()) {
      return "Sin ejemplo";
    }
    return outputNameFromTemplate({
      naming: options.naming,
      suffix: options.suffix || "_PRO",
      format: options.format || "JPG",
    }, {
      original: options.original || "imagen_001",
      folder: options.folder || "lote",
      index: options.index || 1,
    });
  }

  function destinationFallbackLabel(options = {}) {
    const destinations = Array.isArray(options.destinations) ? options.destinations : [];
    if (destinations.length > 1) {
      const uniqueDestinations = Array.from(new Set(destinations));
      return uniqueDestinations.length === 1 ? uniqueDestinations[0] : `${uniqueDestinations.length} destinos`;
    }
    if (options.destinationMode === "custom") {
      return options.destinationValue || "Carpeta de salida sin configurar";
    }
    return options.destinationValue || "Salida";
  }

  function outputProfileFooterState(options = {}) {
    const validation = options.validation || { errors: [] };
    const errors = Array.isArray(validation.errors) ? validation.errors : [];
    const dirty = Boolean(options.dirty);
    const changeCount = Math.max(1, Number(options.changeCount) || 1);
    const profileCount = Number(options.profileCount) || 0;
    const isPersisted = Boolean(options.isPersisted);
    const isNew = !isPersisted;
    const noticeText = options.noticeText || "";
    const deleteDisabled = isPersisted && profileCount <= 1;
    const canSave = (dirty || isNew) && errors.length === 0;
    return {
      closeAction: isNew ? "cancel-output-profile-draft" : "close-app-settings",
      closeLabel: isNew ? "Cancelar" : "Cerrar",
      closeHidden: !isNew,
      deleteDisabled,
      deleteTitle: deleteDisabled ? "Debe quedar al menos un formato" : isPersisted ? "Eliminar formato seleccionado" : "Descartar formato nuevo",
      resetDisabled: !dirty || isNew,
      resetHidden: !dirty || isNew,
      resetLabel: "Descartar",
      saveDisabled: !canSave,
      saveHidden: !dirty && !isNew,
      saveLabel: "Guardar cambios",
      noteClass: `settings-footer-note ${errors.length ? "error" : dirty || isNew ? "warning" : ""}`,
      noteText: errors.length
        ? errors[0]
        : noticeText
          ? noticeText
          : isNew
          ? "Formato nuevo sin guardar"
          : dirty
            ? `${changeCount} ${changeCount === 1 ? "cambio sin guardar" : "cambios sin guardar"}`
            : "Cambios guardados",
    };
  }

  return {
    destinationCompactLabel,
    destinationFallbackLabel,
    escapeHtml,
    namingExample,
    namingHumanLabel,
    outputNameForImage,
    outputNameForProfile,
    outputNameFromTemplate,
    outputProfileEditorHeadingHtml,
    outputProfileFooterState,
    outputProfileManagerRowHtml,
    outputProfilePreviewHtml,
    outputProfileValidationHtml,
    profileDestinationLabel,
    profileDestinationPreviewLabel,
  };
});
