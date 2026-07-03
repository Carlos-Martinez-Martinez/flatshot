function renderShell() {
  const shell = $(".app-shell");
  const gallery = $(".gallery-column");
  const derived = uiState();
  const visible = getVisibleAppState();
  const hasStatusFooter = state.exportStatus === "running"
    || state.exportStatus === "completed"
    || state.exportStatus === "partial"
    || state.exportStatus === "failed";
  shell.classList.toggle("dev-mode", devMode);
  shell.classList.toggle("has-selected-image", derived.hasSelectedImage);
  shell.classList.toggle("no-selected-image", !derived.hasSelectedImage);
  shell.classList.toggle("can-export", derived.canExport);
  shell.classList.toggle("is-settings-open", state.appSettingsOpen);
  shell.classList.toggle("export-completed", ["completed", "partial", "failed"].includes(state.exportStatus));
  shell.classList.toggle("inspector-collapsed", state.inspectorCollapsed);
  shell.classList.toggle("is-folder-drop-active", state.folderDropActive);
  shell.dataset.uiState = visible.id;
  shell.dataset.batchContext = derived.hasBatchContext ? "true" : "false";
  shell.dataset.statusFooter = hasStatusFooter ? "true" : "false";
  shell.dataset.outputEditing = state.outputEditMode ? "true" : "false";
  shell.dataset.responsiveInspector = state.responsiveInspectorOpen ? "true" : "false";
  if (gallery) {
    gallery.dataset.galleryView = state.galleryView;
    const galleryBackground = galleryActiveOutputContext().background;
    gallery.dataset.outputBg = backgroundPresetHelpers.backgroundVisualMode(galleryBackground, backgroundHelperOptions());
    const galleryBackgroundColor = backgroundPresetHelpers.backgroundCssColor(galleryBackground, backgroundHelperOptions());
    if (galleryBackgroundColor) {
      gallery.style.setProperty("--custom-output-bg", galleryBackgroundColor);
    } else {
      gallery.style.removeProperty("--custom-output-bg");
    }
  }
}

function keepActiveThumbnailVisible() {
  window.requestAnimationFrame(() => {
    const active = $("#image-list .image-item.active");
    if (!active) {
      return;
    }
    active.scrollIntoView({ block: "nearest", inline: "center" });
  });
}
