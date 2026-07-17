(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotSettingsView = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const formatterHelpers = globalThis.FlatShotFormatters
    || (typeof require === "function" ? require("./formatters.js") : null);
  const escapeHtml = (value) => formatterHelpers.escapeHtml(value);

  function presetChipHtml(preset = {}, activePreset = "") {
    const active = preset.name === activePreset;
    const title = active ? `${preset.name} activo` : `Cambiar a ${preset.name}`;
    return `
      <button type="button" class="preset-chip${active ? " active" : ""}" data-preset="${escapeHtml(preset.name || "")}" aria-pressed="${active ? "true" : "false"}" title="${escapeHtml(title)}">
        <span class="preset-chip__name">${escapeHtml(preset.name || "")}</span>
        <span class="preset-chip__meta">${escapeHtml(active ? "Activo" : preset.category || "Ajuste")}</span>
      </button>
    `;
  }

  function presetListHtml(presets = [], activePreset = "") {
    if (!presets.length) {
      return '<span class="preset-empty">No hay ajustes guardados</span>';
    }
    return presets.map((preset) => presetChipHtml(preset, activePreset)).join("");
  }

  function presetDirtyLabel(presetDirty) {
    return presetDirty ? "Sin guardar" : "Sin cambios";
  }

  function presetSourceLabel(options = {}) {
    if (options.bridgePresetWarning) {
      return options.presetDirty ? "Global · Modificado · aviso" : "Global · aviso";
    }
    return options.presetDirty ? "Global · Modificado" : "Global";
  }

  function localAdjustmentText(localActive) {
    return localActive ? "Con excepción" : "Usa el ajuste del lote";
  }

  function localSettingOutputText(value) {
    const numeric = Number(value) || 0;
    return numeric > 0 ? `+${numeric}` : String(numeric);
  }

  function savePresetButtonState(presetDirty) {
    return {
      disabled: !presetDirty,
      primary: Boolean(presetDirty),
      text: "Guardar ajuste",
      title: presetDirty ? "Guardar el ajuste activo" : "Sin cambios pendientes",
    };
  }

  function resetPresetButtonState(presetDirty) {
    return {
      disabled: !presetDirty,
      label: "Restaurar recomendado",
      title: presetDirty ? "Restaurar recomendado" : "Sin cambios que restaurar",
    };
  }

  function deletePresetButtonState(presetCount) {
    const canDelete = Number(presetCount) > 1;
    return {
      disabled: !canDelete,
      title: canDelete ? "Eliminar el ajuste activo" : "Debe quedar al menos un ajuste",
    };
  }

  function advancedSummaryTitle(dirtyCount) {
    const count = Number(dirtyCount) || 0;
    return count
      ? `Calibración del motor · ${count} cambio${count === 1 ? "" : "s"}`
      : "Calibración del motor";
  }

  function advancedDirtyCount(options = {}) {
    if (!options.presetDirty) {
      return 0;
    }
    const keys = Array.isArray(options.keys) ? options.keys : [];
    const currentSettings = options.currentSettings || {};
    const presetSettings = options.presetSettings || {};
    return keys.filter((key) => !settingValuesEqual(currentSettings[key], presetSettings[key])).length;
  }

  function settingValuesEqual(first, second) {
    if (first === second) {
      return true;
    }
    if (!first || !second || typeof first !== "object" || typeof second !== "object") {
      return false;
    }
    return JSON.stringify(first) === JSON.stringify(second);
  }

  function backgroundLabel(value) {
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

  function presetSummaryLine(options = {}) {
    return `${options.format || "JPG"} · ${options.size || "1800x2400"} · ${backgroundLabel(options.background)}`;
  }

  function exportStatusLabel(options = {}) {
    const exportStatus = options.exportStatus || "idle";
    if (exportStatus === "running") {
      return options.paused ? "Pausada" : "Procesando";
    }
    if (exportStatus === "completed") {
      return "Completada";
    }
    if (exportStatus === "partial") {
      return "Con errores";
    }
    if (exportStatus === "failed") {
      return "Fallida";
    }
    return options.ready ? "Lista" : "Configura exportación";
  }

  return {
    advancedDirtyCount,
    advancedSummaryTitle,
    backgroundLabel,
    deletePresetButtonState,
    escapeHtml,
    exportStatusLabel,
    localAdjustmentText,
    localSettingOutputText,
    presetSummaryLine,
    presetChipHtml,
    presetDirtyLabel,
    presetListHtml,
    presetSourceLabel,
    resetPresetButtonState,
    savePresetButtonState,
  };
});
