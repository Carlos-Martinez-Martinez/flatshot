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

function toggleOnboardingBackground() {
  const current = interfacePreferenceHelpers.normalizeInterfacePreferences(state.interfacePreferences);
  updateInterfacePreference(
    { onboardingBackground: !current.onboardingBackground },
    current.onboardingBackground ? "Fondos de inicio ocultos" : "Fondos de inicio activos"
  );
}

function startupAdjustmentLabel(preferences = state.interfacePreferences) {
  const startupAdjustment = interfacePreferenceHelpers.startupAdjustmentPreference(preferences);
  if (!startupAdjustment) {
    return "Sin ajuste inicial guardado; se usará el último ajuste/preset activo.";
  }
  const engine = shadowEngineLabels[startupAdjustment.settings?.shadow_engine] || "Motor guardado";
  return `${startupAdjustment.name} · ${engine}`;
}

function setStartupAdjustmentFromCurrent() {
  const settings = normalizeSettings(state.settings);
  updateInterfacePreference(
    {
      startupAdjustment: {
        name: state.activePreset || "Ajuste inicial",
        settings,
        updatedAt: new Date().toISOString(),
      },
    },
    "Ajuste inicial guardado"
  );
}

function clearStartupAdjustmentPreference() {
  updateInterfacePreference(
    { startupAdjustment: null },
    "Ajuste inicial borrado"
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

async function openOnboardingAssetsFolder() {
  try {
    const response = await bridgeRequest("/assets/onboarding/open", {
      method: "POST",
      body: JSON.stringify({}),
      timeoutMs: 5000,
      retries: 1,
    });
    state.statusText = response?.path ? "Carpeta de fondos abierta" : "Carpeta de fondos solicitada";
  } catch (error) {
    const opened = window.open("./assets/onboarding/", "_blank", "noopener");
    state.statusText = opened ? "Fondos abiertos en navegador" : "No se pudo abrir la carpeta de fondos";
  }
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
