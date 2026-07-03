const MODAL_EXIT_MS = 160;
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

function syncModalVisibility(modal, open, options = {}) {
  if (!modal) {
    return;
  }
  const rootRef = options.root || (typeof window !== "undefined" ? window : null);
  clearModalVisibilityTimer(modal, rootRef);
  modal.setAttribute("aria-hidden", open ? "false" : "true");
  if (open) {
    modal.classList.remove("is-hidden", "is-closing");
    return;
  }
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
