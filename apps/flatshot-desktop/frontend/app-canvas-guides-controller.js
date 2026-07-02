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
