const MODAL_ENTER_MS = 160;
const MODAL_EXIT_MS = 160;
const modalOpeningTimers = new WeakMap();
const modalVisibilityTimers = new WeakMap();

function modalMotionAllowed(rootRef = typeof window !== "undefined" ? window : null) {
  if (!rootRef || typeof rootRef.matchMedia !== "function") {
    return true;
  }
  return !rootRef.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function clearModalVisibilityTimer(modal, rootRef = typeof window !== "undefined" ? window : null) {
  const timer = modalVisibilityTimers.get(modal);
  if (!timer) {
    return;
  }
  const clearTimer = rootRef?.clearTimeout || clearTimeout;
  clearTimer(timer);
  modalVisibilityTimers.delete(modal);
}

function clearModalOpeningTimer(modal, rootRef = typeof window !== "undefined" ? window : null) {
  const timer = modalOpeningTimers.get(modal);
  if (!timer) {
    return;
  }
  const clearTimer = rootRef?.clearTimeout || clearTimeout;
  clearTimer(timer);
  modalOpeningTimers.delete(modal);
}

function settleModalOpening(modal) {
  modal.classList.remove("is-opening");
  modalOpeningTimers.delete(modal);
}

function startModalOpening(modal, rootRef, enterMs) {
  clearModalOpeningTimer(modal, rootRef);
  modal.classList.add("is-opening");
  const setTimer = rootRef?.setTimeout || setTimeout;
  const timer = setTimer(() => settleModalOpening(modal), enterMs);
  modalOpeningTimers.set(modal, timer);
}

function syncModalVisibility(modal, open, options = {}) {
  if (!modal) {
    return;
  }
  const rootRef = options.root || (typeof window !== "undefined" ? window : null);
  const wasHidden = modal.classList.contains("is-hidden");
  const wasClosing = modal.classList.contains("is-closing");
  modal.setAttribute("aria-hidden", open ? "false" : "true");
  if (open) {
    clearModalVisibilityTimer(modal, rootRef);
    modal.classList.remove("is-hidden", "is-closing");
    const enterMs = Number(options.enterMs ?? MODAL_ENTER_MS);
    if ((wasHidden || wasClosing) && enterMs > 0 && modalMotionAllowed(rootRef)) {
      startModalOpening(modal, rootRef, enterMs);
    } else if (!modalOpeningTimers.has(modal)) {
      modal.classList.remove("is-opening");
    }
    return;
  }
  clearModalOpeningTimer(modal, rootRef);
  modal.classList.remove("is-opening");
  clearModalVisibilityTimer(modal, rootRef);
  if (modal.classList.contains("is-hidden")) {
    modal.classList.remove("is-closing");
    return;
  }
  const exitMs = Number(options.exitMs ?? MODAL_EXIT_MS);
  if (exitMs <= 0 || !modalMotionAllowed(rootRef)) {
    modal.classList.add("is-hidden");
    modal.classList.remove("is-closing");
    return;
  }
  modal.classList.add("is-closing");
  const setTimer = rootRef?.setTimeout || setTimeout;
  const timer = setTimer(() => {
    modal.classList.add("is-hidden");
    modal.classList.remove("is-closing");
    modalVisibilityTimers.delete(modal);
  }, exitMs);
  modalVisibilityTimers.set(modal, timer);
}

if (typeof window !== "undefined") {
  window.syncModalVisibility = syncModalVisibility;
}

if (typeof module !== "undefined") {
  module.exports = {
    modalMotionAllowed,
    syncModalVisibility,
  };
}
