function syncOpenInspectorDisclosureHeights() {
  window.requestAnimationFrame(() => {
    $$(".settings-panel details.inspector-disclosure[open]").forEach((details) => {
      if (!details.classList.contains("is-closing")) {
        setInspectorDisclosureHeight(details);
      }
    });
  });
}

function inspectorDisclosureBody(details) {
  return details?.querySelector?.(".inspector-disclosure__body") || null;
}

function inspectorDisclosurePreferenceKey(details) {
  const knownKeys = ["preset-section", "appearance-section", "composition-section", "advanced-block", "local-adjustment"];
  return knownKeys.find((key) => details?.classList?.contains(key)) || "";
}

function rememberAdvancedDisclosure(details) {
  const key = inspectorDisclosurePreferenceKey(details);
  if (key && state) {
    state.advancedDisclosureKey = key;
  }
}

function forgetAdvancedDisclosure(details) {
  const key = inspectorDisclosurePreferenceKey(details);
  if (key && state?.advancedDisclosureKey === key) {
    state.advancedDisclosureKey = "";
  }
}

function setInspectorDisclosureHeight(details, height = null) {
  const body = inspectorDisclosureBody(details);
  if (!body) {
    return;
  }
  let nextHeight = height;
  if (nextHeight === null) {
    const wasOpening = details.classList.contains("is-opening");
    const wasClosing = details.classList.contains("is-closing");
    if (wasOpening || wasClosing) {
      details.classList.remove("is-opening", "is-closing");
    }
    const previousHeight = body.style.getPropertyValue("--inspector-disclosure-height");
    body.style.setProperty("--inspector-disclosure-height", "none");
    const bodyRect = body.getBoundingClientRect();
    const bodyStyle = getComputedStyle(body);
    const paddingBottom = Number.parseFloat(bodyStyle.paddingBottom) || 0;
    const childBottom = Array.from(body.children).reduce((max, child) => {
      const rect = child.getBoundingClientRect();
      return Math.max(max, rect.bottom - bodyRect.top);
    }, 0);
    nextHeight = Math.max(body.scrollHeight, Math.ceil(childBottom + paddingBottom));
    if (previousHeight) {
      body.style.setProperty("--inspector-disclosure-height", previousHeight);
    } else {
      body.style.removeProperty("--inspector-disclosure-height");
    }
    if (wasOpening) {
      details.classList.add("is-opening");
    }
    if (wasClosing) {
      details.classList.add("is-closing");
    }
  }
  body.style.setProperty("--inspector-disclosure-height", `${Math.max(0, Math.round(nextHeight))}px`);
}

function setInspectorDisclosureOpenState(details, open) {
  if (!details) {
    return;
  }
  const previousTimer = inspectorDisclosureTimers.get(details);
  if (previousTimer) {
    window.clearTimeout(previousTimer);
    inspectorDisclosureTimers.delete(details);
  }
  details.open = open;
  if (open) {
    rememberAdvancedDisclosure(details);
  } else {
    forgetAdvancedDisclosure(details);
  }
  details.classList.remove("is-opening", "is-closing", "is-open");
  inspectorDisclosureBody(details)?.style.removeProperty("--inspector-disclosure-height");
}

function restoreInspectorScroll(panel, scrollTop = inspectorScrollTopBeforeToggle) {
  if (!panel) {
    return;
  }
  const restore = () => {
    panel.scrollTop = scrollTop;
  };
  restore();
  window.requestAnimationFrame(() => {
    restore();
    window.requestAnimationFrame(restore);
    window.setTimeout(restore, 0);
    window.setTimeout(restore, INSPECTOR_DISCLOSURE_MS);
  });
}

function closeInspectorDisclosure(details, panel = $(".settings-panel"), scrollTop = inspectorScrollTopBeforeToggle) {
  if (!details?.open || details.classList.contains("is-closing")) {
    return;
  }
  forgetAdvancedDisclosure(details);
  const previousTimer = inspectorDisclosureTimers.get(details);
  if (previousTimer) {
    window.clearTimeout(previousTimer);
  }

  setInspectorDisclosureHeight(details);
  details.classList.remove("is-opening", "is-open");
  details.classList.add("is-closing");
  window.requestAnimationFrame(() => {
    setInspectorDisclosureHeight(details, 0);
    restoreInspectorScroll(panel, scrollTop);
  });

  const timer = window.setTimeout(() => {
    details.open = false;
    details.classList.remove("is-closing");
    const body = inspectorDisclosureBody(details);
    body?.style.removeProperty("--inspector-disclosure-height");
    inspectorDisclosureTimers.delete(details);
    restoreInspectorScroll(panel, scrollTop);
  }, INSPECTOR_DISCLOSURE_MS);
  inspectorDisclosureTimers.set(details, timer);
}

function openInspectorDisclosure(details, panel = $(".settings-panel"), scrollTop = inspectorScrollTopBeforeToggle) {
  if (!details) {
    return;
  }
  $$(".settings-panel details.inspector-disclosure").forEach((other) => {
    if (other !== details && other.open) {
      closeInspectorDisclosure(other, panel, scrollTop);
    }
  });

  const previousTimer = inspectorDisclosureTimers.get(details);
  if (previousTimer) {
    window.clearTimeout(previousTimer);
    inspectorDisclosureTimers.delete(details);
  }
  details.open = true;
  rememberAdvancedDisclosure(details);
  details.classList.remove("is-closing", "is-open");
  details.classList.add("is-opening");
  setInspectorDisclosureHeight(details, 0);
  restoreInspectorScroll(panel, scrollTop);
  window.requestAnimationFrame(() => {
    setInspectorDisclosureHeight(details);
    restoreInspectorScroll(panel, scrollTop);
  });
  const timer = window.setTimeout(() => {
    details.classList.remove("is-opening");
    details.classList.add("is-open");
    const body = inspectorDisclosureBody(details);
    body?.style.setProperty("--inspector-disclosure-height", "none");
    inspectorDisclosureTimers.delete(details);
    restoreInspectorScroll(panel, scrollTop);
  }, INSPECTOR_DISCLOSURE_MS);
  inspectorDisclosureTimers.set(details, timer);
}

function toggleInspectorDisclosure(details) {
  const panel = $(".settings-panel");
  inspectorScrollTopBeforeToggle = panel?.scrollTop || 0;
  const shouldOpen = !details.open || details.classList.contains("is-closing");
  if (shouldOpen) {
    openInspectorDisclosure(details, panel, inspectorScrollTopBeforeToggle);
  } else {
    closeInspectorDisclosure(details, panel, inspectorScrollTopBeforeToggle);
  }
}
