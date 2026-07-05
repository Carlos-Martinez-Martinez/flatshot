function isGuideOverlayAvailable() {
  return Boolean(selectedImage()) && !["empty", "error", "loading"].includes(state.previewStatus);
}
function activeGuideSystems() {
  return guideHelpers.activeGuideSystems(state.guideSystems, state.activeGuideSystemIds);
}
function orderedGuideSystems() {
  return guideHelpers.orderGuideSystems(state.guideSystems, state.guideSystemOrderIds);
}
function pickerGuideSystems() {
  return guideHelpers.pickerGuideSystems(state.guideSystems, state.guideSystemOrderIds, state.hiddenGuideSystemIds);
}
function normalizeGuideSelectorPreferences() {
  state.guideSystemOrderIds = guideHelpers.normalizeGuideSystemOrderIds(state.guideSystemOrderIds, state.guideSystems);
  state.hiddenGuideSystemIds = guideHelpers.normalizeHiddenGuideSystemIds(state.hiddenGuideSystemIds, state.guideSystems);
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
    list.innerHTML = guideViewHelpers.guideToolbarListHtml({
      systems: pickerGuideSystems(),
      activeIds: state.activeGuideSystemIds,
    });
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
  normalizeGuideSelectorPreferences();
  storageHelpers.writeJson(window.localStorage, STORAGE_KEYS.guideSystems, guideHelpers.guideSystemsForStorage(state.guideSystems));
  storageHelpers.writeJson(window.localStorage, STORAGE_KEYS.activeGuideSystems, state.activeGuideSystemIds);
  storageHelpers.writeJson(window.localStorage, STORAGE_KEYS.guideSystemOrder, state.guideSystemOrderIds);
  storageHelpers.writeJson(window.localStorage, STORAGE_KEYS.hiddenGuideSystems, state.hiddenGuideSystemIds);
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
  if (!state.selectedGuideSystemId || !state.guideSystems.some((system) => system.id === state.selectedGuideSystemId)) {
    state.selectedGuideSystemId = orderedGuideSystems()[0]?.id || null;
  }
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
  state.selectedGuideSystemId = null;
  render();
}
function renderGuideManager() {
  let modal = $("#guide-manager-modal");
  if (!state.guideManagerOpen) {
    if (modal) {
      syncModalVisibility(modal, false, { exitMs: 0 });
      modal.remove();
    }
    return;
  }
  const shouldOpenModal = !modal;
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "guide-manager-modal";
    modal.className = "app-settings-backdrop guide-manager-modal is-hidden";
    document.body.appendChild(modal);
  }
  modal.innerHTML = guideViewHelpers.guideManagerHtml({
    systems: orderedGuideSystems(),
    selectedId: state.selectedGuideSystemId,
    selectedSystem: selectedGuideSystem(),
    draft: state.guideDraft,
    hiddenIds: state.hiddenGuideSystemIds,
  });
  if (shouldOpenModal) {
    syncModalVisibility(modal, true);
  }
}
function selectedGuideSystem() {
  return state.guideSystems.find((system) => system.id === state.selectedGuideSystemId) || null;
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
  state.selectedGuideSystemId = null;
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
function selectGuideSystem(target) {
  const systemId = target?.dataset?.guideSystemId;
  const system = state.guideSystems.find((item) => item.id === systemId);
  if (!system) {
    return;
  }
  state.selectedGuideSystemId = system.id;
  state.guideDraft = system.system ? null : guideDraftFromSystem(system);
  renderGuideManager();
}
function editGuideSystem(target) {
  const system = state.guideSystems.find((item) => item.id === target?.dataset?.guideSystemId);
  if (!system || system.system) {
    return;
  }
  state.selectedGuideSystemId = system.id;
  state.guideDraft = guideDraftFromSystem(system);
  renderGuideManager();
}
function duplicateGuideSystem(target) {
  const system = state.guideSystems.find((item) => item.id === target?.dataset?.guideSystemId);
  if (!system) {
    return;
  }
  state.selectedGuideSystemId = null;
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
  state.guideSystemOrderIds = state.guideSystemOrderIds.filter((id) => id !== systemId);
  state.hiddenGuideSystemIds = state.hiddenGuideSystemIds.filter((id) => id !== systemId);
  if (state.selectedGuideSystemId === systemId) {
    state.selectedGuideSystemId = orderedGuideSystems().find((item) => item.id !== systemId)?.id || null;
  }
  if (state.guideDraft?.id === systemId) {
    state.guideDraft = null;
  }
  persistGuidePreferences();
  render();
}
function setGuideSystemInPicker(systemId, visible) {
  if (!state.guideSystems.some((system) => system.id === systemId)) {
    return;
  }
  const hidden = new Set(state.hiddenGuideSystemIds);
  if (visible) {
    hidden.delete(systemId);
  } else {
    hidden.add(systemId);
  }
  state.hiddenGuideSystemIds = guideHelpers.normalizeHiddenGuideSystemIds([...hidden], state.guideSystems);
  state.statusText = visible ? "Sistema añadido al selector" : "Sistema oculto del selector";
  persistGuidePreferences();
  render();
}
function moveGuideSystem(target, direction) {
  const systemId = target?.dataset?.guideSystemId;
  const ordered = guideHelpers.normalizeGuideSystemOrderIds(state.guideSystemOrderIds, state.guideSystems);
  const index = ordered.indexOf(systemId);
  const nextIndex = index + direction;
  if (index < 0 || nextIndex < 0 || nextIndex >= ordered.length) {
    return;
  }
  [ordered[index], ordered[nextIndex]] = [ordered[nextIndex], ordered[index]];
  state.guideSystemOrderIds = ordered;
  state.statusText = "Orden de guías actualizado";
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
    state.hiddenGuideSystemIds = state.hiddenGuideSystemIds.filter((id) => id !== normalized.id);
  }
  state.guideSystemOrderIds = guideHelpers.normalizeGuideSystemOrderIds([...state.guideSystemOrderIds, normalized.id], state.guideSystems);
  state.activeGuideSystemIds = guideHelpers.normalizeActiveGuideSystemIds([...state.activeGuideSystemIds, normalized.id], state.guideSystems);
  state.selectedGuideSystemId = normalized.id;
  state.guideDraft = guideDraftCopy(normalized);
  state.statusText = "Sistema de guías guardado";
  persistGuidePreferences();
  render();
}
