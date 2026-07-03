function preferenceSaveSync() {
  if (typeof scheduleBridgeUiPreferencesSave === "function") {
    scheduleBridgeUiPreferencesSave();
  }
}

function persistInterfacePreferences() {
  state.interfacePreferences = interfacePreferenceHelpers.normalizeInterfacePreferences(state.interfacePreferences);
  interfacePreferenceHelpers.writeInterfacePreferences(
    window.localStorage,
    STORAGE_KEYS.interfacePreferences,
    state.interfacePreferences
  );
  interfacePreferenceHelpers.applyInterfacePreferences(document, state.interfacePreferences);
  preferenceSaveSync();
}

function closeTopPreferencesMenu() {
  const menu = $("#top-preferences-menu");
  if (menu) {
    menu.open = false;
  }
}

function openPreferences() {
  rememberModalFocusReturn();
  closeTopPreferencesMenu();
  state.appSettingsOpen = false;
  state.batchDetailOpen = false;
  state.exportConfirmOpen = false;
  state.qaLabOpen = false;
  state.preferencesOpen = true;
  state.statusText = "Preferencias";
  render();
  queueModalFocus("#preferences-modal", "[data-action='close-preferences']");
}

function closePreferences() {
  releaseModalFocusBeforeHide();
  state.preferencesOpen = false;
  state.statusText = "Preferencias cerradas";
  render();
}

function themePreferenceLabel(preference) {
  if (preference === "dark") {
    return "Tema oscuro";
  }
  if (preference === "system") {
    return "Tema del sistema";
  }
  return "Tema claro";
}

function setThemePreference(target) {
  const preference = themeHelpers.normalizeThemePreference(target?.dataset?.themePreference || target?.value);
  state.themePreference = preference;
  state.theme = themeHelpers.resolveThemePreference(preference, window);
  themeHelpers.writeThemePreference(window.localStorage, STORAGE_KEYS.theme, preference);
  themeHelpers.applyTheme(document, state.theme);
  state.statusText = themePreferenceLabel(preference);
  preferenceSaveSync();
  render();
}

function updateInterfacePreference(patch, statusText) {
  state.interfacePreferences = interfacePreferenceHelpers.normalizeInterfacePreferences({
    ...state.interfacePreferences,
    ...patch,
  });
  persistInterfacePreferences();
  state.statusText = statusText;
  render();
}

function setUiDensity(target) {
  const rawDensity = target?.dataset?.uiDensity || target?.value;
  const density = rawDensity === "comfortable" ? "comfortable" : "compact";
  updateInterfacePreference(
    { density },
    density === "comfortable" ? "Densidad cómoda" : "Densidad compacta"
  );
}

function toggleReducedMotion() {
  const current = interfacePreferenceHelpers.normalizeInterfacePreferences(state.interfacePreferences);
  updateInterfacePreference(
    { reduceMotion: !current.reduceMotion },
    current.reduceMotion ? "Animaciones automáticas" : "Animaciones reducidas"
  );
}

function toggleShowRecentFolders() {
  const current = interfacePreferenceHelpers.normalizeInterfacePreferences(state.interfacePreferences);
  updateInterfacePreference(
    { showRecentFolders: !current.showRecentFolders },
    current.showRecentFolders ? "Recientes ocultas" : "Recientes visibles"
  );
}

function setThumbnailSize(target) {
  const rawSize = target?.dataset?.thumbnailSize || target?.value;
  const size = ["small", "medium", "large"].includes(rawSize)
    ? rawSize
    : "medium";
  const labels = { small: "Miniaturas pequeñas", medium: "Miniaturas medianas", large: "Miniaturas grandes" };
  updateInterfacePreference({ thumbnailSize: size }, labels[size]);
}

function setFileNameDisplay(target) {
  const rawDisplay = target?.dataset?.fileNameDisplay || target?.value;
  const display = ["always", "hover", "none"].includes(rawDisplay)
    ? rawDisplay
    : "always";
  const labels = { always: "Nombres visibles", hover: "Nombres al pasar", none: "Nombres ocultos" };
  updateInterfacePreference({ fileNameDisplay: display }, labels[display]);
}

function handlePreferenceSelectChange(target) {
  const key = target?.dataset?.preferenceSelect;
  if (key === "theme") {
    setThemePreference(target);
  } else if (key === "brandTone") {
    setBrandTone(target?.value);
  } else if (key === "density") {
    setUiDensity(target);
  } else if (key === "thumbnailSize") {
    setThumbnailSize(target);
  } else if (key === "fileNameDisplay") {
    setFileNameDisplay(target);
  }
}

function clearRecentFolders() {
  recentFolderHelpers.writeRecentFolders(window.localStorage, STORAGE_KEYS.recentFolders, []);
  state.recentFolders = [];
  state.statusText = "Historial de carpetas borrado";
  preferenceSaveSync();
  render();
}

function resetInterfacePreferences() {
  state.themePreference = "light";
  state.theme = "light";
  state.brandTone = "green";
  state.interfacePreferences = interfacePreferenceHelpers.defaultInterfacePreferences();
  themeHelpers.writeThemePreference(window.localStorage, STORAGE_KEYS.theme, state.themePreference);
  themeHelpers.writeBrandTonePreference(window.localStorage, STORAGE_KEYS.brandTone, state.brandTone);
  persistInterfacePreferences();
  themeHelpers.applyTheme(document, state.theme);
  themeHelpers.applyBrandTone(document, state.brandTone);
  state.statusText = "Preferencias restablecidas";
  render();
}
