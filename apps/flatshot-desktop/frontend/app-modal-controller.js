function openAppSettings() {
  rememberModalFocusReturn();
  state.batchDetailOpen = false;
  state.exportConfirmOpen = false;
  state.qaLabOpen = false;
  state.preferencesOpen = false;
  const activeProfile = activeOutputProfile();
  const profile = outputMatchesProfile(activeProfile)
    ? activeProfile
    : {
      ...currentOutputProfileData(),
      id: outputProfileHelpers.uniqueOutputProfileId("formato-personalizado", Date.now()),
      name: "Salida personalizada",
    };
  state.appSettingsOpen = true;
  state.outputProfileEditorId = profile.id;
  state.outputProfileDraft = { ...profile };
  state.outputDeleteConfirmId = "";
  state.outputProfileCloseConfirmOpen = false;
  state.statusText = "Salidas";
  render();
  queueModalFocus("#app-settings-modal", "[data-action='close-app-settings']");
}

function closeAppSettings() {
  if (state.appSettingsOpen && outputProfileHasUnsavedChanges()) {
    state.outputProfileCloseConfirmOpen = true;
    state.outputProfileNotice = "Confirma si quieres descartar los cambios.";
    render();
    return;
  }
  closeAppSettingsImmediately();
}

function closeAppSettingsImmediately() {
  releaseModalFocusBeforeHide();
  state.appSettingsOpen = false;
  state.outputProfileDraft = null;
  state.outputProfileNotice = "";
  state.outputDeleteConfirmId = "";
  state.outputProfileCloseConfirmOpen = false;
  state.statusText = "Configuración cerrada";
  render();
}

function keepEditingOutputProfile() {
  state.outputProfileCloseConfirmOpen = false;
  state.outputProfileNotice = "";
  render();
}

function discardOutputProfileAndClose() {
  state.outputProfileCloseConfirmOpen = false;
  cancelOutputProfileDraft();
}

function cancelOutputProfileDraft() {
  releaseModalFocusBeforeHide();
  const fallback = enabledActiveOutputProfile()
    || state.outputProfiles.find((profile) => profile.id === state.activeOutputProfileId)
    || state.outputProfiles[0]
    || null;
  state.appSettingsOpen = false;
  state.outputProfileEditorId = fallback?.id || "";
  state.outputProfileDraft = null;
  state.outputDeleteConfirmId = "";
  state.outputProfileCloseConfirmOpen = false;
  state.statusText = "Salida descartada";
  render();
}

function openBatchDetail() {
  rememberModalFocusReturn();
  state.exportConfirmOpen = false;
  state.qaLabOpen = false;
  state.preferencesOpen = false;
  state.batchDetailOpen = true;
  state.statusText = "Detalle del lote";
  render();
  queueModalFocus("#batch-detail-modal", "[data-action='close-batch-detail']");
}

function closeBatchDetail() {
  releaseModalFocusBeforeHide();
  state.batchDetailOpen = false;
  state.statusText = hasBatch() ? "Lote cargado" : "Sin lote";
  render();
}

function openExportConfirm(risks, options = {}) {
  rememberModalFocusReturn();
  state.appSettingsOpen = false;
  state.qaLabOpen = false;
  state.preferencesOpen = false;
  state.outputProfileDraft = null;
  state.outputDeleteConfirmId = "";
  state.batchDetailOpen = false;
  state.exportConfirmOpen = true;
  state.exportConfirmRisks = preflightHelpers.dedupeExportRisks(risks);
  state.exportConfirmOptions = { ...options };
  state.statusText = state.exportConfirmRisks.some((risk) => risk.blocking)
    ? "Resuelve problemas antes de exportar"
    : "Confirmar exportación";
  render();
  queueModalFocus("#export-confirm-modal", "#export-confirm-action");
}

function closeExportConfirm({ renderAfter = true } = {}) {
  releaseModalFocusBeforeHide();
  state.exportConfirmOpen = false;
  state.exportConfirmRisks = [];
  state.exportConfirmOptions = null;
  if (renderAfter) {
    render();
  }
}

function confirmExportFromModal() {
  const risks = state.exportConfirmRisks || [];
  if (risks.some((risk) => risk.blocking)) {
    closeExportConfirm({ renderAfter: false });
    reviewWarnings();
    return;
  }
  const options = { ...(state.exportConfirmOptions || {}), confirmed: true };
  closeExportConfirm({ renderAfter: false });
  startExport(options);
}

function openQaLab() {
  if (typeof devMode !== "undefined" && !devMode) {
    return;
  }
  rememberModalFocusReturn();
  state.appSettingsOpen = false;
  state.batchDetailOpen = false;
  state.exportConfirmOpen = false;
  state.preferencesOpen = false;
  state.qaLabOpen = true;
  state.statusText = "QA Lab";
  render();
  queueModalFocus("#qa-lab-modal", "[data-action='close-qa-lab']");
}

function closeQaLab() {
  releaseModalFocusBeforeHide();
  state.qaLabOpen = false;
  state.statusText = "QA Lab cerrado";
  render();
}

function rememberModalFocusReturn() {
  const active = document.activeElement;
  if (
    active instanceof HTMLElement
    && active !== document.body
    && !active.closest(".app-settings-backdrop")
  ) {
    modalFocusReturnTarget = active;
  }
}

function restoreModalFocusReturn() {
  if (typeof modalFocusReturnTarget === "undefined") {
    return;
  }
  const target = modalFocusReturnTarget;
  modalFocusReturnTarget = null;
  if (target instanceof HTMLElement && document.contains(target)) {
    target.focus({ preventScroll: true });
  }
}

function releaseModalFocusBeforeHide() {
  const active = document.activeElement;
  if (active instanceof HTMLElement && active.closest(".app-settings-backdrop")) {
    active.blur();
  }
  restoreModalFocusReturn();
}

function queueModalFocus(modalSelector, preferredSelector = "") {
  const requestFrame = typeof window !== "undefined" && typeof window.requestAnimationFrame === "function"
    ? window.requestAnimationFrame.bind(window)
    : (callback) => callback();
  requestFrame(() => {
    const modal = $(modalSelector);
    if (!modal || modal.classList.contains("is-hidden")) {
      return;
    }
    const preferred = preferredSelector ? modal.querySelector(preferredSelector) : null;
    const fallback = firstFocusableElement(modal);
    (preferred || fallback)?.focus({ preventScroll: true });
  });
}

function firstFocusableElement(container) {
  return Array.from(container.querySelectorAll(
    "button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), summary, [tabindex]:not([tabindex='-1'])"
  )).find((element) => element.offsetParent !== null);
}

function currentOpenModal() {
  if (state.qaLabOpen) {
    return $("#qa-lab-modal");
  }
  if (state.preferencesOpen) {
    return $("#preferences-modal");
  }
  if (state.exportConfirmOpen) {
    return $("#export-confirm-modal");
  }
  if (state.appSettingsOpen) {
    return $("#app-settings-modal");
  }
  if (state.batchDetailOpen) {
    return $("#batch-detail-modal");
  }
  return null;
}

function trapOpenModalFocus(event) {
  const modal = currentOpenModal();
  if (!modal || modal.classList.contains("is-hidden")) {
    return false;
  }
  const focusable = Array.from(modal.querySelectorAll(
    "button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), summary, [tabindex]:not([tabindex='-1'])"
  )).filter((element) => element.offsetParent !== null);
  if (!focusable.length) {
    event.preventDefault();
    return true;
  }
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  const active = document.activeElement;
  if (event.shiftKey && active === first) {
    event.preventDefault();
    last.focus({ preventScroll: true });
    return true;
  }
  if (!event.shiftKey && active === last) {
    event.preventDefault();
    first.focus({ preventScroll: true });
    return true;
  }
  if (!modal.contains(active)) {
    event.preventDefault();
    first.focus({ preventScroll: true });
    return true;
  }
  return false;
}
