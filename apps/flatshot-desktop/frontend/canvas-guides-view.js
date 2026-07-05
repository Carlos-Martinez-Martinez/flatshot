(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotCanvasGuideView = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const formatterHelpers = globalThis.FlatShotFormatters
    || (typeof require === "function" ? require("./formatters.js") : null);
  const escapeHtml = (value) => formatterHelpers.escapeHtml(value);

  const formatPercent = globalThis.FlatShotCanvasGuides?.formatPercent || function fallbackFormatPercent(value) {
    return `${Number((Number(value || 0) * 100).toFixed(2))}%`;
  };
  const expandRule = globalThis.FlatShotCanvasGuides?.expandRule || function fallbackExpandRule(rule) {
    if (rule?.type === "center") {
      return [{ axis: rule.axis, position: 0.5 }];
    }
    if (rule?.type === "line") {
      return [{ axis: rule.axis, position: Number(rule.position) || 0 }];
    }
    return [];
  };
  const backgroundPresetHelpers = globalThis.FlatShotBackgroundPresets || {};

  function iconSvg(name) {
    const icons = {
      check: '<path d="M5 12l4 4L19 6"></path>',
      copy: '<rect x="8" y="8" width="12" height="12" rx="2"></rect><path d="M4 16V6a2 2 0 0 1 2-2h10"></path>',
      down: '<path d="M12 5v14"></path><path d="M5 12l7 7 7-7"></path>',
      edit: '<path d="M12 20h9"></path><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"></path>',
      plus: '<path d="M12 5v14"></path><path d="M5 12h14"></path>',
      trash: '<path d="M3 6h18"></path><path d="M8 6V4h8v2"></path><path d="M6 6l1 14h10l1-14"></path><path d="M10 11v5"></path><path d="M14 11v5"></path>',
      up: '<path d="M12 19V5"></path><path d="M5 12l7-7 7 7"></path>',
    };
    return `<span class="button-icon" aria-hidden="true"><svg viewBox="0 0 24 24" focusable="false">${icons[name] || ""}</svg></span>`;
  }

  function guideIconButtonHtml(options = {}) {
    const disabled = options.disabled ? "disabled" : "";
    const tone = options.tone ? ` ${escapeHtml(options.tone)}` : "";
    return `<button type="button" class="guide-icon-button${tone}" data-action="${escapeHtml(options.action)}" data-guide-system-id="${escapeHtml(options.systemId)}" aria-label="${escapeHtml(options.label)}" title="${escapeHtml(options.label)}" ${disabled}>${iconSvg(options.icon)}</button>`;
  }

  function guideToolbarListHtml(options = {}) {
    const systems = Array.isArray(options.systems) ? options.systems : [];
    const activeIds = Array.isArray(options.activeIds) ? options.activeIds : [];
    if (!systems.length) {
      return `<div class="viewer-guides-empty">No hay sistemas en el selector</div>`;
    }
    return systems.map((system) => `
      <label class="viewer-guide-system-option">
        <input type="checkbox" data-guide-system-toggle="${escapeHtml(system.id)}" ${activeIds.includes(system.id) ? "checked" : ""} />
        <span class="viewer-guide-system-swatch" style="--guide-system-color: ${escapeHtml(system.color)}"></span>
        <span>${escapeHtml(system.name)}</span>
      </label>
    `).join("");
  }

  function guideManagerHtml(options = {}) {
    const systems = Array.isArray(options.systems) ? options.systems : [];
    const panelHtml = options.draft
      ? guideDraftFormHtml(options.draft)
      : guideReadonlySystemHtml(options.selectedSystem);
    return `
    <div class="app-settings-dialog guide-manager-panel" role="dialog" aria-modal="true" aria-labelledby="guide-manager-title">
      <header class="app-settings-header">
        <div>
          <span class="eyebrow">Visor</span>
          <h2 id="guide-manager-title">Guías del lienzo</h2>
          <small>Sistemas superpuestos para revisar encaje y proporciones.</small>
        </div>
        <button type="button" data-action="close-guide-manager" class="icon-button" aria-label="Cerrar guías" title="Cerrar">×</button>
      </header>
      <div class="guide-manager-body">
        <section class="guide-system-list" aria-label="Sistemas de guías">
          <div class="guide-system-list-heading">
            <strong>Sistemas</strong>
            <button type="button" class="guide-icon-button" data-action="new-guide-system" aria-label="Nuevo sistema" title="Nuevo sistema">${iconSvg("plus")}</button>
          </div>
          <div class="guide-system-list-scroll">
            ${systems.map((system, index) => guideSystemManagerRowHtml(system, index, systems.length, options)).join("")}
          </div>
        </section>
        <section class="guide-draft-panel" aria-label="Editor de guías">
          ${panelHtml}
        </section>
      </div>
    </div>
  `;
  }

  function guideSystemManagerRowHtml(system, index, total, options = {}) {
    const hiddenIds = Array.isArray(options.hiddenIds) ? options.hiddenIds : [];
    const inSelector = !hiddenIds.includes(system.id);
    const selected = options.selectedId === system.id;
    const customActions = system.system ? "" : `
          ${guideIconButtonHtml({ action: "edit-guide-system", systemId: system.id, icon: "edit", label: `Editar ${system.name}` })}
          ${guideIconButtonHtml({ action: "delete-guide-system", systemId: system.id, icon: "trash", label: `Eliminar ${system.name}`, tone: "danger-subtle" })}
        `;
    return `
    <article class="guide-system-row ${selected ? "is-selected" : ""} ${inSelector ? "" : "is-inactive"}">
      <button type="button" class="guide-system-main" data-action="select-guide-system" data-guide-system-id="${escapeHtml(system.id)}" aria-pressed="${selected ? "true" : "false"}">
        <span class="viewer-guide-system-swatch" style="--guide-system-color: ${escapeHtml(system.color)}"></span>
        <div class="guide-system-copy">
          <strong>${escapeHtml(system.name)}</strong>
          <span>${system.rules.length} reglas${system.system ? " · sistema base" : " · personalizado"}${inSelector ? "" : " · fuera del selector"}</span>
        </div>
      </button>
      <div class="guide-system-controls">
        <label class="guide-system-picker ${inSelector ? "is-selected" : ""}" title="${inSelector ? "Ocultar del selector" : "Mostrar en selector"}">
          <input type="checkbox" data-guide-system-picker-toggle="${escapeHtml(system.id)}" aria-label="${inSelector ? "Ocultar del selector" : "Mostrar en selector"}: ${escapeHtml(system.name)}" ${inSelector ? "checked" : ""} />
          ${iconSvg("check")}
        </label>
        <div class="guide-system-actions">
          ${guideIconButtonHtml({ action: "move-guide-system-up", systemId: system.id, icon: "up", label: `Subir ${system.name}`, disabled: index <= 0 })}
          ${guideIconButtonHtml({ action: "move-guide-system-down", systemId: system.id, icon: "down", label: `Bajar ${system.name}`, disabled: index >= total - 1 })}
          ${customActions}
          ${guideIconButtonHtml({ action: "duplicate-guide-system", systemId: system.id, icon: "copy", label: `Duplicar ${system.name}` })}
        </div>
      </div>
    </article>
  `;
  }

  function guideEmptyStateHtml() {
    return `<div class="guide-empty-state"><strong>Selecciona o crea un sistema</strong><span>Elige un preset para revisar sus guías o crea uno nuevo.</span><button type="button" data-action="new-guide-system">${iconSvg("plus")}Nuevo sistema</button></div>`;
  }

  function guideReadonlySystemHtml(system) {
    if (!system) {
      return guideEmptyStateHtml();
    }
    const lines = system.rules.flatMap((rule) => expandRule(rule));
    return `
    <div class="guide-readonly-panel">
      <div class="guide-draft-heading">
        <strong>${escapeHtml(system.name)}</strong>
        <span>${system.system ? "Sistema base" : "Sistema personalizado"} · ${system.rules.length} reglas · ${lines.length} guías</span>
      </div>
      <div class="guide-draft-fields">
        <label>Color <span class="guide-readonly-swatch" style="--guide-system-color: ${escapeHtml(system.color)}"></span></label>
        <label>Opacidad <output>${Math.round((Number(system.opacity) || 0) * 100)}%</output></label>
        <label>Grosor <output>${escapeHtml(system.thickness || 1)} px</output></label>
      </div>
      <div class="guide-list-heading"><strong>Guías del sistema</strong><span>${lines.length} ${lines.length === 1 ? "guía" : "guías"}</span></div>
      <div class="guide-rule-list" aria-label="Guías del sistema">
        ${lines.map((line, index) => guideReadonlyLineHtml(line, index)).join("")}
      </div>
      <footer class="guide-manager-actions">
        <button type="button" data-action="duplicate-guide-system" data-guide-system-id="${escapeHtml(system.id)}">${iconSvg("copy")}Duplicar para editar</button>
      </footer>
    </div>
  `;
  }

  function guideReadonlyLineHtml(line, index) {
    const orientation = line.axis === "y" ? "Horizontal" : "Vertical";
    return `
    <article class="guide-rule-row guide-line-row guide-line-row--readonly">
      <div class="guide-rule-title"><strong>Guía ${index + 1}</strong><span>${orientation} · ${formatPercent(line.position ?? 0.5)}</span></div>
      <output>${formatPercent(line.position ?? 0.5)}</output>
    </article>
  `;
  }

  function guideDraftFormHtml(draft) {
    const count = draft.rules.length;
    return `
    <form id="guide-draft-form" class="guide-draft-form">
      <div class="guide-draft-heading"><strong>${escapeHtml(draft.id ? "Editar sistema" : "Nuevo sistema")}</strong><span>Define reglas en porcentaje del lienzo.</span></div>
      <div class="guide-draft-fields">
        <label>Nombre <input type="text" data-guide-draft-field="name" value="${escapeHtml(draft.name)}" /></label>
        ${guideColorControlHtml(draft.color)}
        <label>Opacidad <input type="number" min="10" max="100" step="5" data-guide-draft-field="opacity" value="${Math.round(draft.opacity * 100)}" /></label>
        <label>Grosor <input type="number" min="1" max="4" step="1" data-guide-draft-field="thickness" value="${draft.thickness}" /></label>
      </div>
      <div class="guide-add-row" aria-label="Añadir guía">
        <div class="guide-add-title"><strong>Añadir guía</strong><span>Posición exacta en porcentaje.</span></div>
        <label>Orientación ${guideAxisSelectHtml("x", "data-guide-new-field")}</label>
        <label><span>Posición</span><span class="guide-percent-input"><input type="number" min="0" max="100" step="0.1" data-guide-new-field="position" value="50" /><span>%</span></span></label>
        <label class="guide-mirror-option"><input type="checkbox" data-guide-new-field="mirror" /> Reflejar</label>
        <button type="button" data-action="add-guide-line" class="primary">${iconSvg("plus")}Añadir</button>
      </div>
      <div class="guide-list-heading"><strong>Guías del sistema</strong><span>${count} ${count === 1 ? "guía" : "guías"}</span></div>
      <div class="guide-rule-list" aria-label="Reglas del sistema">
        ${draft.rules.map((rule, index) => guideRuleEditorHtml(rule, index)).join("")}
      </div>
      <footer class="guide-manager-actions">
        <button type="button" data-action="save-guide-draft" class="primary">Guardar sistema</button>
      </footer>
    </form>
  `;
  }

  function guideColorControlHtml(color) {
    const channels = backgroundPresetHelpers.rgbChannelsFromHex
      ? backgroundPresetHelpers.rgbChannelsFromHex(color, [15, 118, 110])
      : [15, 118, 110];
    const hex = backgroundPresetHelpers.rgbHexValue
      ? backgroundPresetHelpers.rgbHexValue(channels, "#0f766e")
      : "#0f766e";
    return `
        <label>Color <input type="hidden" data-guide-draft-field="color" value="${escapeHtml(hex)}" /><span class="rgb-visual-control rgb-visual-control--swatch-only guide-color-control" data-rgb-visual-control="guide-color" data-rgb-visual-format="hex" style="--rgb-visual-color: rgb(${channels.join(", ")})"><button type="button" class="rgb-visual-control__swatch" data-rgb-visual-picker-trigger data-rgb-visual-swatch aria-label="Elegir color de guía"></button><input type="color" class="rgb-visual-control__picker" value="${escapeHtml(hex)}" data-rgb-visual-picker tabindex="-1" aria-label="Selector de color de guía" /></span></label>
    `;
  }

  function guideRuleEditorHtml(rule, index) {
    const orientation = rule.axis === "y" ? "Horizontal" : "Vertical";
    return `
    <article class="guide-rule-row guide-line-row" data-guide-rule data-guide-rule-type="line" data-guide-rule-id="${escapeHtml(rule.id || "")}">
      <div class="guide-rule-title"><strong>Guía ${index + 1}</strong><span>${orientation} · ${formatPercent(rule.position ?? 0.5)}</span></div>
      <div class="guide-rule-fields">
        <label>Orientación ${guideAxisSelectHtml(rule.axis)}</label>
        <label><span>Posición</span><span class="guide-percent-input"><input type="number" min="0" max="100" step="0.1" data-guide-rule-field="position" value="${guidePercentNumber(rule.position ?? 0.5)}" /><span>%</span></span></label>
      </div>
      <button type="button" class="guide-icon-button danger-subtle" data-action="remove-guide-rule" data-guide-rule-index="${index}" aria-label="Eliminar regla" title="Eliminar regla">${iconSvg("trash")}</button>
    </article>
  `;
  }

  function guideAxisSelectHtml(axis, fieldAttribute = "data-guide-rule-field") {
    return `
    <select ${fieldAttribute}="axis">
      <option value="x" ${axis === "x" ? "selected" : ""}>Vertical</option>
      <option value="y" ${axis === "y" ? "selected" : ""}>Horizontal</option>
    </select>
  `;
  }

  function guidePercentNumber(value) {
    return Number((Number(value || 0) * 100).toFixed(2));
  }

  return {
    guideManagerHtml,
    guideToolbarListHtml,
  };
});
