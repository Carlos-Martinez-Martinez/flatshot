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
    modal.className = "modal-backdrop guide-manager-modal";
    document.body.appendChild(modal);
  }
  modal.innerHTML = `
    <div class="modal-panel guide-manager-panel" role="dialog" aria-modal="true" aria-labelledby="guide-manager-title">
      <header class="modal-header">
        <div>
          <span class="eyebrow">Visor</span>
          <h2 id="guide-manager-title">Guías del lienzo</h2>
        </div>
        <button type="button" data-action="close-guide-manager" class="icon-button" aria-label="Cerrar guías" title="Cerrar">×</button>
      </header>
      <div class="guide-manager-body">
        <section class="guide-system-list" aria-label="Sistemas de guías">
          ${state.guideSystems.map((system) => guideSystemManagerRow(system)).join("")}
          <button type="button" data-action="new-guide-system">Nuevo sistema</button>
        </section>
        <section class="guide-draft-panel" aria-label="Editor de guías">
          ${state.guideDraft ? guideDraftFormHtml(state.guideDraft) : "<p>Selecciona o duplica un sistema para editarlo.</p>"}
        </section>
      </div>
    </div>
  `;
}
function guideSystemManagerRow(system) {
  const locked = system.system ? "disabled" : "";
  return `
    <article class="guide-system-row">
      <div>
        <strong>${previewViewHelpers.escapeHtml(system.name)}</strong>
        <span>${system.rules.length} reglas${system.system ? " · sistema" : ""}</span>
      </div>
      <button type="button" data-action="edit-guide-system" data-guide-system-id="${previewViewHelpers.escapeHtml(system.id)}" ${locked}>Editar</button>
      <button type="button" data-action="duplicate-guide-system" data-guide-system-id="${previewViewHelpers.escapeHtml(system.id)}">Duplicar</button>
      <button type="button" data-action="delete-guide-system" data-guide-system-id="${previewViewHelpers.escapeHtml(system.id)}" ${locked}>Eliminar</button>
    </article>
  `;
}
function guideDraftFormHtml(draft) {
  return `
    <form id="guide-draft-form">
      <div class="guide-draft-fields">
        <label>Nombre <input type="text" data-guide-draft-field="name" value="${previewViewHelpers.escapeHtml(draft.name)}" /></label>
        <label>Color <input type="color" data-guide-draft-field="color" value="${previewViewHelpers.escapeHtml(draft.color)}" /></label>
        <label>Opacidad <input type="number" min="10" max="100" step="5" data-guide-draft-field="opacity" value="${Math.round(draft.opacity * 100)}" /></label>
        <label>Grosor <input type="number" min="1" max="4" step="1" data-guide-draft-field="thickness" value="${draft.thickness}" /></label>
      </div>
      <div class="guide-rule-actions">
        <button type="button" data-action="add-guide-pair">Añadir par</button>
        <button type="button" data-action="add-guide-division">Dividir lienzo</button>
        <button type="button" data-action="add-guide-center">Añadir centro</button>
        <button type="button" data-action="add-guide-line">Añadir línea libre</button>
      </div>
      <div class="guide-rule-list">
        ${draft.rules.map((rule, index) => guideRuleEditorHtml(rule, index)).join("")}
      </div>
      <footer class="guide-manager-actions">
        <button type="button" data-action="save-guide-draft" class="primary">Guardar sistema</button>
      </footer>
    </form>
  `;
}
function guideRuleEditorHtml(rule, index) {
  const typeLabels = {
    center: "Centro",
    "mirror-pair": "Par simétrico",
    division: "División",
    line: "Línea libre",
  };
  return `
    <article class="guide-rule-row" data-guide-rule data-guide-rule-type="${previewViewHelpers.escapeHtml(rule.type)}" data-guide-rule-id="${previewViewHelpers.escapeHtml(rule.id || "")}">
      <strong>${typeLabels[rule.type] || "Regla"}</strong>
      <label>Eje ${guideAxisSelectHtml(rule.axis)}</label>
      ${guideRuleValueFieldsHtml(rule)}
      <button type="button" data-action="remove-guide-rule" data-guide-rule-index="${index}" aria-label="Eliminar regla" title="Eliminar regla">Eliminar</button>
    </article>
  `;
}
function guideAxisSelectHtml(axis) {
  return `
    <select data-guide-rule-field="axis">
      <option value="x" ${axis === "x" ? "selected" : ""}>Vertical</option>
      <option value="y" ${axis === "y" ? "selected" : ""}>Horizontal</option>
    </select>
  `;
}
function guideRuleValueFieldsHtml(rule) {
  if (rule.type === "center") {
    return "";
  }
  if (rule.type === "mirror-pair") {
    return `<label>Desde borde <input type="number" min="0.1" max="49.9" step="0.1" data-guide-rule-field="inset" value="${guidePercentNumber(rule.inset || 0.1)}" />%</label>`;
  }
  if (rule.type === "line") {
    return `<label>Posición <input type="number" min="0" max="100" step="0.1" data-guide-rule-field="position" value="${guidePercentNumber(rule.position ?? 0.5)}" />%</label>`;
  }
  const positions = rule.mode === "custom"
    ? (rule.positions || []).map(guideHelpers.formatPercent).join(", ")
    : equalDivisionPositions(rule.parts || 3).map(guideHelpers.formatPercent).join(", ");
  return `
    <label>Modo
      <select data-guide-rule-field="mode">
        <option value="equal" ${rule.mode !== "custom" ? "selected" : ""}>Iguales</option>
        <option value="custom" ${rule.mode === "custom" ? "selected" : ""}>Personalizadas</option>
      </select>
    </label>
    <label>Partes <input type="number" min="2" max="24" step="1" data-guide-rule-field="parts" value="${Math.max(2, Math.round(Number(rule.parts) || 3))}" /></label>
    <label>Porcentajes <input type="text" data-guide-rule-field="positions" value="${previewViewHelpers.escapeHtml(positions)}" /></label>
  `;
}
function guidePercentNumber(value) {
  return Number((Number(value || 0) * 100).toFixed(2));
}
function equalDivisionPositions(parts) {
  const safeParts = Math.max(2, Math.min(24, Math.round(Number(parts) || 2)));
  return Array.from({ length: safeParts - 1 }, (_, index) => Math.round(((index + 1) / safeParts) * 10000) / 10000);
}
function guideDraftCopy(system) {
  return JSON.parse(JSON.stringify(system));
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
  state.guideDraft = guideDraftCopy(system);
  renderGuideManager();
}
function duplicateGuideSystem(target) {
  const system = state.guideSystems.find((item) => item.id === target?.dataset?.guideSystemId);
  if (!system) {
    return;
  }
  state.guideDraft = {
    ...guideDraftCopy(system),
    id: "",
    system: false,
    name: `${system.name} copia`,
  };
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
function addGuideCenterRule() {
  const draft = editableGuideDraft();
  draft.rules.push({ id: guideRuleId("center-x"), type: "center", axis: "x" });
  draft.rules.push({ id: guideRuleId("center-y"), type: "center", axis: "y" });
  renderGuideManager();
}
function addGuideMirrorPairRule() {
  editableGuideDraft().rules.push({ id: guideRuleId("pair"), type: "mirror-pair", axis: "y", inset: 0.1 });
  renderGuideManager();
}
function addGuideDivisionRule() {
  editableGuideDraft().rules.push({ id: guideRuleId("division"), type: "division", axis: "x", mode: "equal", parts: 3 });
  renderGuideManager();
}
function addGuideLineRule() {
  editableGuideDraft().rules.push({ id: guideRuleId("line"), type: "line", axis: "x", position: 0.5 });
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
  const type = row.dataset.guideRuleType;
  const axis = row.querySelector('[data-guide-rule-field="axis"]')?.value === "y" ? "y" : "x";
  const id = row.dataset.guideRuleId || guideRuleId(type || "rule");
  if (type === "center") {
    return { id, type, axis };
  }
  if (type === "mirror-pair") {
    return { id, type, axis, inset: guideHelpers.parsePercent(row.querySelector('[data-guide-rule-field="inset"]')?.value, 0.1) };
  }
  if (type === "line") {
    return { id, type, axis, position: guideHelpers.parsePercent(row.querySelector('[data-guide-rule-field="position"]')?.value, 0.5) };
  }
  if (type === "division") {
    const mode = row.querySelector('[data-guide-rule-field="mode"]')?.value === "custom" ? "custom" : "equal";
    const parts = Math.max(2, Math.min(24, Math.round(Number(row.querySelector('[data-guide-rule-field="parts"]')?.value || 3))));
    if (mode === "custom") {
      const rawPositions = row.querySelector('[data-guide-rule-field="positions"]')?.value || "";
      const positions = rawPositions.split(/[,\s]+/).map((value) => guideHelpers.parsePercent(value, NaN)).filter(Number.isFinite);
      return { id, type, axis, mode, parts, positions: positions.length ? positions : equalDivisionPositions(parts) };
    }
    return { id, type, axis, mode, parts };
  }
  return null;
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
