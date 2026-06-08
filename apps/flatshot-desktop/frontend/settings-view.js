(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotSettingsView = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

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

  function localAdjustmentText(localActive) {
    return localActive ? "Ajuste local activo" : "Sin ajuste local";
  }

  function localSettingOutputText(value) {
    const numeric = Number(value) || 0;
    return numeric > 0 ? `+${numeric}` : String(numeric);
  }

  function savePresetButtonState(presetDirty) {
    return {
      disabled: !presetDirty,
      primary: Boolean(presetDirty),
      text: "Guardar cambios",
      title: presetDirty ? "Guardar el ajuste activo" : "Sin cambios pendientes",
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
    return count ? `Avanzado · ${count} cambio${count === 1 ? "" : "s"}` : "Avanzado";
  }

  return {
    advancedSummaryTitle,
    deletePresetButtonState,
    escapeHtml,
    localAdjustmentText,
    localSettingOutputText,
    presetChipHtml,
    presetDirtyLabel,
    presetListHtml,
    savePresetButtonState,
  };
});
