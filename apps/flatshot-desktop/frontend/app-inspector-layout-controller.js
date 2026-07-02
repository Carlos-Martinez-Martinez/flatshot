function advancedDirtyCount() {
  const presetSettings = normalizeSettings(activePresetItem()?.settings || defaultSettings);
  return settingsViewHelpers.advancedDirtyCount({
    currentSettings: state.settings,
    keys: visibleAdvancedSettingKeys(state.settings),
    presetDirty: state.presetDirty,
    presetSettings,
  });
}

function visibleAdvancedSettingKeys(settings = state.settings) {
  if (settings.shadow_engine === "studio_2_5d") {
    return advancedSettingKeys.filter((key) => key !== "angle");
  }
  return advancedSettingKeys;
}

function advancedSettingsDirty() {
  return advancedDirtyCount() > 0;
}

function inspectorMode() {
  return inspectorContextViewHelpers.inspectorMode({
    inspectorTab: state.inspectorTab,
    outputEditMode: state.outputEditMode,
  });
}

function renderInspector() {
  const panel = $(".settings-panel");
  const mode = inspectorMode();
  const validTabs = ["review", "output", "warnings", "advanced"];
  if (!validTabs.includes(state.inspectorTab)) {
    state.inspectorTab = "review";
  }
  panel.classList.toggle("is-editing-output", state.outputEditMode);
  panel.classList.toggle("is-editing-preset", state.presetEditorOpen || mode === "advanced");
  panel.classList.toggle("is-inspector-subview", mode !== "summary");
  panel.classList.toggle("is-advanced-subview", mode === "advanced");
  const start = $("#inspector-start");
  start.classList.remove("is-hidden");
  if (mode === "summary") {
    start.innerHTML = inspectorCardsHtml();
  } else {
    start.innerHTML = inspectorSubviewHeaderHtml(mode);
  }
  $(".inspector-tabs").classList.add("is-hidden");
  $$(".settings-panel [data-inspector-tab]").forEach((button) => {
    const active = button.dataset.inspectorTab === state.inspectorTab;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", active ? "true" : "false");
  });
  $$(".settings-panel [data-inspector-section]").forEach((section) => {
    const sectionName = section.dataset.inspectorSection;
    const visible = (mode === "output" && sectionName === "output")
      || (mode === "advanced" && sectionName === "advanced")
      || (mode === "warnings" && sectionName === "warnings");
    section.classList.toggle(
      "is-hidden",
      !visible
    );
  });
  syncAdvancedInspectorDetails(mode);
}

function syncAdvancedInspectorDetails(mode) {
  const detailsItems = $$(".settings-panel details.inspector-disclosure[data-inspector-section='advanced']");
  detailsItems.forEach((details) => {
    if (mode !== "advanced") {
      setInspectorDisclosureOpenState(details, false);
    }
  });
  if (mode !== "advanced") {
    pendingAdvancedDisclosure = "";
    return;
  }

  if (state.presetEditorOpen) {
    state.advancedDisclosureKey = "preset-section";
    detailsItems.forEach((details) => {
      setInspectorDisclosureOpenState(details, details.classList.contains("preset-section"));
    });
    pendingAdvancedDisclosure = "";
    return;
  }

  const editableDetails = detailsItems.filter((details) => !details.classList.contains("preset-section"));
  detailsItems
    .filter((details) => details.classList.contains("preset-section"))
    .forEach((details) => setInspectorDisclosureOpenState(details, false));

  if (pendingAdvancedDisclosure) {
    const preferred = editableDetails.find((details) => details.classList.contains(pendingAdvancedDisclosure));
    if (preferred) {
      state.advancedDisclosureKey = pendingAdvancedDisclosure;
      editableDetails.forEach((details) => setInspectorDisclosureOpenState(details, details === preferred));
    }
    pendingAdvancedDisclosure = "";
    return;
  }

  const remembered = editableDetails.find((details) => details.classList.contains(state.advancedDisclosureKey));
  if (remembered) {
    editableDetails.forEach((details) => setInspectorDisclosureOpenState(details, details === remembered));
    return;
  }

  const openDetails = editableDetails.find((details) => details.open);
  if (openDetails) {
    state.advancedDisclosureKey = inspectorDisclosurePreferenceKey(openDetails);
    return;
  }

  state.advancedDisclosureKey = "appearance-section";
  editableDetails.forEach((details) => {
    setInspectorDisclosureOpenState(details, details.classList.contains("appearance-section"));
  });
}

function inspectorCardsHtml() {
  if (state.batch === "scanning") {
    return `
      <section class="inspector-card inspector-card--busy">
        <div class="inspector-card__head">
          <span>Escaneo</span>
          <strong>Escaneando carpeta...</strong>
        </div>
        <small>${escapeHtml(state.scanStatus || "Leyendo imágenes")}</small>
        ${exportPreflightViewHelpers.progressPanelHtml("Escaneando carpeta")}
      </section>
    `;
  }

  if (state.batch === "none") {
    return "";
  }

  return [
    lotInspectorCardHtml(),
    aspectInspectorCardHtml(),
    outputInspectorCardHtml(),
    selectedImageInspectorCardHtml(),
    issuesInspectorCardHtml(),
  ].filter(Boolean).join("");
}
