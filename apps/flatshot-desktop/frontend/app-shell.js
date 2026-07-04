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
  shell.classList.toggle("is-preferences-open", state.preferencesOpen);
  shell.classList.toggle("export-completed", ["completed", "partial", "failed"].includes(state.exportStatus));
  shell.classList.toggle("inspector-collapsed", state.inspectorCollapsed);
  shell.classList.toggle("is-folder-drop-active", state.folderDropActive);
  shell.dataset.uiState = visible.id;
  shell.dataset.batchContext = derived.hasBatchContext ? "true" : "false";
  shell.dataset.statusFooter = hasStatusFooter ? "true" : "false";
  shell.dataset.outputEditing = state.outputEditMode ? "true" : "false";
  shell.dataset.responsiveInspector = state.responsiveInspectorOpen ? "true" : "false";
  themeHelpers.applyTheme(document, state.theme);
  themeHelpers.applyBrandTone(document, state.brandTone);
  state.interfacePreferences = interfacePreferenceHelpers.applyInterfacePreferences(document, state.interfacePreferences);
  shell.dataset.theme = state.theme;
  shell.dataset.brandTone = state.brandTone;
  document.documentElement.dataset.themePreference = state.themePreference;
  shell.dataset.uiDensity = state.interfacePreferences.density;
  shell.dataset.reduceMotion = state.interfacePreferences.reduceMotion ? "true" : "false";
  shell.dataset.thumbnailSize = state.interfacePreferences.thumbnailSize;
  shell.dataset.fileNameDisplay = state.interfacePreferences.fileNameDisplay;
  shell.dataset.onboardingBackground = state.interfacePreferences.onboardingBackground ? "enabled" : "disabled";
  renderBrandToneControls();
  renderPreferenceControls();
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

function toggleTheme() {
  state.theme = themeHelpers.toggleTheme({
    document,
    storage: window.localStorage,
    storageKey: STORAGE_KEYS.theme,
    currentTheme: state.theme,
  });
  state.themePreference = state.theme;
  state.statusText = state.theme === "dark" ? "Tema oscuro" : "Tema claro";
  scheduleBridgeUiPreferencesSave();
  render();
}

function setBrandTone(tone) {
  const nextTone = themeHelpers.normalizeBrandTone(tone);
  const label = themeHelpers.brandToneOptions().find((option) => option.id === nextTone)?.label || "Verde";
  state.brandTone = nextTone;
  themeHelpers.writeBrandTonePreference(window.localStorage, STORAGE_KEYS.brandTone, nextTone);
  themeHelpers.applyBrandTone(document, nextTone);
  state.statusText = `Tono: ${label}`;
  scheduleBridgeUiPreferencesSave();
  render();
}

function renderBrandToneControls() {
  const currentTone = themeHelpers.normalizeBrandTone(state.brandTone);
  $$("[data-brand-tone-value]").forEach((button) => {
    const selected = themeHelpers.normalizeBrandTone(button.dataset.brandToneValue) === currentTone;
    button.classList.toggle("active", selected);
    button.setAttribute("aria-pressed", selected ? "true" : "false");
  });
}

function renderPreferenceControls() {
  const themePreference = themeHelpers.normalizeThemePreference(state.themePreference);
  const preferences = interfacePreferenceHelpers.normalizeInterfacePreferences(state.interfacePreferences);
  const values = {
    brandTone: themeHelpers.normalizeBrandTone(state.brandTone),
    density: preferences.density,
    fileNameDisplay: preferences.fileNameDisplay,
    theme: themePreference,
    thumbnailSize: preferences.thumbnailSize,
  };
  $$("[data-preference-select]").forEach((select) => {
    const value = values[select.dataset.preferenceSelect];
    if (value && select.value !== value) {
      select.value = value;
    }
  });
  const reducedMotion = $("[data-action='toggle-reduced-motion']");
  if (reducedMotion) {
    const reducedMotionLabel = reducedMotion.querySelector("em");
    reducedMotion.setAttribute("aria-pressed", preferences.reduceMotion ? "true" : "false");
    if (reducedMotionLabel) {
      reducedMotionLabel.textContent = preferences.reduceMotion ? "Reducidas" : "Automáticas";
    }
  }
  const recentFolders = $("[data-action='toggle-show-recent-folders']");
  if (recentFolders) {
    const recentFoldersLabel = recentFolders.querySelector("em");
    recentFolders.setAttribute("aria-pressed", preferences.showRecentFolders ? "true" : "false");
    if (recentFoldersLabel) {
      recentFoldersLabel.textContent = preferences.showRecentFolders ? "Visibles" : "Ocultas";
    }
  }
  const onboardingBackground = $("[data-action='toggle-onboarding-background']");
  if (onboardingBackground) {
    const onboardingBackgroundLabel = onboardingBackground.querySelector("em");
    onboardingBackground.setAttribute("aria-pressed", preferences.onboardingBackground ? "true" : "false");
    if (onboardingBackgroundLabel) {
      onboardingBackgroundLabel.textContent = preferences.onboardingBackground ? "Activas" : "Ocultas";
    }
  }
  const startupAdjustment = interfacePreferenceHelpers.startupAdjustmentPreference(preferences);
  const startupAdjustmentSummary = $("[data-preference-startup-adjustment-summary]");
  if (startupAdjustmentSummary) {
    startupAdjustmentSummary.textContent = startupAdjustmentLabel(preferences);
  }
  const clearStartupAdjustment = $("[data-action='clear-startup-adjustment']");
  if (clearStartupAdjustment) {
    clearStartupAdjustment.disabled = !startupAdjustment;
  }
  const clearRecent = $("[data-action='clear-recent-folders']");
  if (clearRecent) {
    clearRecent.disabled = !state.recentFolders.length;
  }
}
