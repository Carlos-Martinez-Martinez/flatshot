function isGuideOverlayAvailable() {
  return Boolean(selectedImage()) && !["empty", "error", "loading"].includes(state.previewStatus);
}
function activeGuideSystems() {
  return guideHelpers.activeGuideSystems(state.guideSystems, state.activeGuideSystemIds);
}
function renderGuideToolbarState() {
  const group = $(".viewer-guides");
  const toggle = $("#guides-toggle");
  const count = $("#guides-active-count");
  const list = $("[data-guide-system-list]");
  const disabled = !isGuideOverlayAvailable();
  const activeSystems = activeGuideSystems();
  if (group) {
    group.classList.toggle("is-disabled", disabled);
  }
  if (toggle) {
    toggle.textContent = state.guidesVisible ? "On" : "Off";
    toggle.disabled = disabled;
    toggle.classList.toggle("active", state.guidesVisible);
    toggle.setAttribute("aria-pressed", state.guidesVisible ? "true" : "false");
  }
  if (count) {
    count.textContent = String(activeSystems.length);
    count.title = `${activeSystems.length} sistemas activos`;
  }
  if (list) {
    list.innerHTML = state.guideSystems.map((system) => `
      <label class="viewer-guide-system-option">
        <input type="checkbox" data-guide-system-toggle="${previewViewHelpers.escapeHtml(system.id)}" ${state.activeGuideSystemIds.includes(system.id) ? "checked" : ""} />
        <span class="viewer-guide-system-swatch" style="--guide-system-color: ${previewViewHelpers.escapeHtml(system.color)}"></span>
        <span>${previewViewHelpers.escapeHtml(system.name)}</span>
      </label>
    `).join("");
  }
}
function renderGuideOverlay() {
  const overlay = $("#guide-overlay");
  const canvas = $("#preview-canvas");
  const target = canvas?.querySelector(".preview-image, .mock-product");
  if (!overlay || !canvas || !target || !state.guidesVisible || !isGuideOverlayAvailable()) {
    if (overlay) {
      overlay.hidden = true;
      overlay.innerHTML = "";
    }
    return;
  }
  const lines = guideHelpers.guideLinesForSystems(state.guideSystems, state.activeGuideSystemIds);
  overlay.hidden = !lines.length;
  overlay.innerHTML = lines.map((line) => `
    <div class="guide-line guide-line--${line.axis}" style="--guide-position: ${line.position}; --guide-color: ${previewViewHelpers.escapeHtml(line.color)}; --guide-opacity: ${line.opacity}; --guide-thickness: ${line.thickness}px"></div>
  `).join("");
  updateGuideOverlayLayout();
}
function updateGuideOverlayLayout() {
  const overlay = $("#guide-overlay");
  const canvasArea = $("#canvas-area");
  const canvas = $("#preview-canvas");
  const target = canvas?.querySelector(".preview-image, .mock-product");
  if (!overlay || !canvasArea || !canvas || !target || overlay.hidden) {
    return;
  }
  const areaRect = canvasArea.getBoundingClientRect();
  const targetRect = target.getBoundingClientRect();
  if (!areaRect.width || !areaRect.height || !targetRect.width || !targetRect.height) {
    overlay.hidden = true;
    return;
  }
  overlay.style.left = `${Math.round(targetRect.left - areaRect.left)}px`;
  overlay.style.top = `${Math.round(targetRect.top - areaRect.top)}px`;
  overlay.style.width = `${Math.round(targetRect.width)}px`;
  overlay.style.height = `${Math.round(targetRect.height)}px`;
}
function persistGuidePreferences() {
  storageHelpers.writeJson(window.localStorage, STORAGE_KEYS.guideSystems, guideHelpers.guideSystemsForStorage(state.guideSystems));
  storageHelpers.writeJson(window.localStorage, STORAGE_KEYS.activeGuideSystems, state.activeGuideSystemIds);
  storageHelpers.writeValue(window.localStorage, STORAGE_KEYS.guidesVisible, state.guidesVisible ? "1" : "0");
  scheduleBridgeUiPreferencesSave();
}
function toggleGuidesVisible() {
  state.guidesVisible = !state.guidesVisible;
  state.statusText = state.guidesVisible ? "Guías visibles" : "Guías ocultas";
  persistGuidePreferences();
  render();
}
function setGuideSystemActive(systemId, active) {
  const ids = new Set(state.activeGuideSystemIds);
  if (active) {
    ids.add(systemId);
  } else {
    ids.delete(systemId);
  }
  state.activeGuideSystemIds = guideHelpers.normalizeActiveGuideSystemIds([...ids], state.guideSystems);
  state.statusText = `${activeGuideSystems().length} sistemas de guías activos`;
  persistGuidePreferences();
  render();
}
function openGuideManager() {
  state.guideManagerOpen = true;
  state.guideDraft = null;
  state.statusText = "Gestionar guías";
  const menu = $("#viewer-guides-menu");
  if (menu) {
    menu.open = false;
  }
  render();
}
function closeGuideManager() {
  state.guideManagerOpen = false;
  state.guideDraft = null;
  render();
}
function renderGuideManager() {
  let modal = $("#guide-manager-modal");
  if (!state.guideManagerOpen) {
    if (modal) {
      modal.remove();
    }
    return;
  }
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "guide-manager-modal";
    modal.className = "app-settings-backdrop guide-manager-modal";
    document.body.appendChild(modal);
  }
  modal.innerHTML = `
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
            <button type="button" data-action="new-guide-system">Nuevo</button>
          </div>
          <div class="guide-system-list-scroll">
            ${state.guideSystems.map((system) => guideSystemManagerRow(system)).join("")}
          </div>
        </section>
        <section class="guide-draft-panel" aria-label="Editor de guías">
          ${state.guideDraft ? guideDraftFormHtml(state.guideDraft) : guideEmptyStateHtml()}
        </section>
      </div>
    </div>
  `;
}
function guideSystemManagerRow(system) {
  const customActions = system.system ? "" : `<button type="button" data-action="edit-guide-system" data-guide-system-id="${previewViewHelpers.escapeHtml(system.id)}">Editar</button><button type="button" data-action="delete-guide-system" data-guide-system-id="${previewViewHelpers.escapeHtml(system.id)}">Eliminar</button>`;
  return `
    <article class="guide-system-row">
      <div class="guide-system-main">
        <span class="viewer-guide-system-swatch" style="--guide-system-color: ${previewViewHelpers.escapeHtml(system.color)}"></span>
        <div>
          <strong>${previewViewHelpers.escapeHtml(system.name)}</strong>
          <span>${system.rules.length} reglas${system.system ? " · sistema base" : " · personalizado"}</span>
        </div>
      </div>
      <div class="guide-system-actions">
        ${customActions}
        <button type="button" data-action="duplicate-guide-system" data-guide-system-id="${previewViewHelpers.escapeHtml(system.id)}">Duplicar</button>
      </div>
    </article>
  `;
}
function guideEmptyStateHtml() {
  return `<div class="guide-empty-state"><strong>Prepara un sistema editable</strong><span>Duplica una base o crea un sistema para colocar guías exactas en porcentaje.</span><button type="button" data-action="new-guide-system">Nuevo sistema</button></div>`;
}
function guideDraftFormHtml(draft) {
  const count = draft.rules.length;
  return `
    <form id="guide-draft-form" class="guide-draft-form">
      <div class="guide-draft-heading"><strong>${previewViewHelpers.escapeHtml(draft.id ? "Editar sistema" : "Nuevo sistema")}</strong><span>Define reglas en porcentaje del lienzo.</span></div>
      <div class="guide-draft-fields">
        <label>Nombre <input type="text" data-guide-draft-field="name" value="${previewViewHelpers.escapeHtml(draft.name)}" /></label>
        <label>Color <input type="color" data-guide-draft-field="color" value="${previewViewHelpers.escapeHtml(draft.color)}" /></label>
        <label>Opacidad <input type="number" min="10" max="100" step="5" data-guide-draft-field="opacity" value="${Math.round(draft.opacity * 100)}" /></label>
        <label>Grosor <input type="number" min="1" max="4" step="1" data-guide-draft-field="thickness" value="${draft.thickness}" /></label>
      </div>
      <div class="guide-add-row" aria-label="Añadir guía">
        <div class="guide-add-title"><strong>Añadir guía</strong><span>Posición exacta en porcentaje.</span></div>
        <label>Orientación ${guideAxisSelectHtml("x", "data-guide-new-field")}</label>
        <label><span>Posición</span><span class="guide-percent-input"><input type="number" min="0" max="100" step="0.1" data-guide-new-field="position" value="50" /><span>%</span></span></label>
        <label class="guide-mirror-option"><input type="checkbox" data-guide-new-field="mirror" /> Reflejar</label>
        <button type="button" data-action="add-guide-line" class="primary">Añadir guía</button>
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
function guideRuleEditorHtml(rule, index) {
  const orientation = rule.axis === "y" ? "Horizontal" : "Vertical";
  return `
    <article class="guide-rule-row guide-line-row" data-guide-rule data-guide-rule-type="line" data-guide-rule-id="${previewViewHelpers.escapeHtml(rule.id || "")}">
      <div class="guide-rule-title"><strong>Guía ${index + 1}</strong><span>${orientation} · ${guideHelpers.formatPercent(rule.position ?? 0.5)}</span></div>
      <div class="guide-rule-fields">
        <label>Orientación ${guideAxisSelectHtml(rule.axis)}</label>
        <label><span>Posición</span><span class="guide-percent-input"><input type="number" min="0" max="100" step="0.1" data-guide-rule-field="position" value="${guidePercentNumber(rule.position ?? 0.5)}" /><span>%</span></span></label>
      </div>
      <button type="button" data-action="remove-guide-rule" data-guide-rule-index="${index}" aria-label="Eliminar regla" title="Eliminar regla">Eliminar</button>
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
function guideDraftCopy(system) {
  return JSON.parse(JSON.stringify(system));
}
function editableGuideRulesFromSystem(system) {
  let index = 0;
  return (system.rules || []).flatMap((rule) => (
    guideHelpers.expandRule(rule).map((line) => {
      index += 1;
      return { id: `${rule.id || rule.type || "guide"}-${index}`, type: "line", axis: line.axis, position: line.position };
    })
  ));
}
function guideDraftFromSystem(system, options = {}) {
  const draft = guideDraftCopy(system);
  return {
    ...draft,
    id: options.clearId ? "" : draft.id,
    system: false,
    name: options.copyName ? `${draft.name} copia` : draft.name,
    rules: editableGuideRulesFromSystem(draft),
  };
}
function editableGuideDraft() {
  if (!state.guideDraft) {
    newGuideSystem();
  }
  return state.guideDraft;
}
function guideRuleId(prefix) {
  return `${prefix}-${Date.now()}-${Math.max(0, state.guideDraft?.rules?.length || 0)}`;
}
function newGuideSystem() {
  state.guideDraft = {
    id: "",
    name: "Nuevo sistema",
    color: "#0f766e",
    opacity: 0.85,
    thickness: 1,
    rules: [],
  };
  renderGuideManager();
}
function editGuideSystem(target) {
  const system = state.guideSystems.find((item) => item.id === target?.dataset?.guideSystemId);
  if (!system || system.system) {
    return;
  }
  state.guideDraft = guideDraftFromSystem(system);
  renderGuideManager();
}
function duplicateGuideSystem(target) {
  const system = state.guideSystems.find((item) => item.id === target?.dataset?.guideSystemId);
  if (!system) {
    return;
  }
  state.guideDraft = guideDraftFromSystem(system, { clearId: true, copyName: true });
  renderGuideManager();
}
function deleteGuideSystem(target) {
  const systemId = target?.dataset?.guideSystemId;
  const system = state.guideSystems.find((item) => item.id === systemId);
  if (!system || system.system) {
    return;
  }
  state.guideSystems = state.guideSystems.filter((item) => item.id !== systemId);
  state.activeGuideSystemIds = state.activeGuideSystemIds.filter((id) => id !== systemId);
  if (state.guideDraft?.id === systemId) {
    state.guideDraft = null;
  }
  persistGuidePreferences();
  render();
}
function addGuideLineRule() {
  const draft = editableGuideDraft();
  const form = $("#guide-draft-form");
  const axis = form?.querySelector('[data-guide-new-field="axis"]')?.value === "y" ? "y" : "x";
  const position = guideHelpers.parsePercent(form?.querySelector('[data-guide-new-field="position"]')?.value, 0.5);
  const mirror = Boolean(form?.querySelector('[data-guide-new-field="mirror"]')?.checked);
  const positions = [position];
  const reflected = 1 - position;
  if (mirror && Math.abs(reflected - position) > 0.0001) {
    positions.push(reflected);
  }
  positions.forEach((guidePosition) => {
    draft.rules.push({ id: guideRuleId("guide"), type: "line", axis, position: guidePosition });
  });
  renderGuideManager();
}
function removeGuideRule(target) {
  const index = Number(target?.dataset?.guideRuleIndex);
  if (!state.guideDraft || !Number.isInteger(index)) {
    return;
  }
  state.guideDraft.rules = state.guideDraft.rules.filter((_, ruleIndex) => ruleIndex !== index);
  renderGuideManager();
}
function updateGuideDraftFromFields() {
  const form = $("#guide-draft-form");
  if (!form || !state.guideDraft) {
    return;
  }
  state.guideDraft = {
    ...state.guideDraft,
    name: form.querySelector('[data-guide-draft-field="name"]')?.value || "",
    color: form.querySelector('[data-guide-draft-field="color"]')?.value || "#0f766e",
    opacity: Number(form.querySelector('[data-guide-draft-field="opacity"]')?.value || 85) / 100,
    thickness: Number(form.querySelector('[data-guide-draft-field="thickness"]')?.value || 1),
    rules: Array.from(form.querySelectorAll("[data-guide-rule]")).map(guideRuleFromRow).filter(Boolean),
  };
}
function guideRuleFromRow(row) {
  const axis = row.querySelector('[data-guide-rule-field="axis"]')?.value === "y" ? "y" : "x";
  const id = row.dataset.guideRuleId || guideRuleId("guide");
  return { id, type: "line", axis, position: guideHelpers.parsePercent(row.querySelector('[data-guide-rule-field="position"]')?.value, 0.5) };
}
function saveGuideDraft() {
  updateGuideDraftFromFields();
  const normalized = guideHelpers.normalizeGuideSystemList([state.guideDraft], { defaultSystems: [] })[0];
  if (!normalized) {
    state.statusText = "Revisa el sistema de guías";
    renderGuideManager();
    return;
  }
  const existingIndex = state.guideSystems.findIndex((system) => system.id === state.guideDraft.id && !system.system);
  if (existingIndex >= 0) {
    state.guideSystems = state.guideSystems.map((system, index) => index === existingIndex ? normalized : system);
  } else {
    state.guideSystems = guideHelpers.normalizeGuideSystemList([...state.guideSystems, normalized]);
  }
  state.activeGuideSystemIds = guideHelpers.normalizeActiveGuideSystemIds([...state.activeGuideSystemIds, normalized.id], state.guideSystems);
  state.guideDraft = guideDraftCopy(normalized);
  state.statusText = "Sistema de guías guardado";
  persistGuidePreferences();
  render();
}
