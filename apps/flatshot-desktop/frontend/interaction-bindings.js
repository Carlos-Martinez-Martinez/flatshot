(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotInteractionBindings = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  function optionalElement($, selector) {
    return typeof $ === "function" ? $(selector) : null;
  }

  function createFlatShotInteractionHandlers(handlers = {}) {
    return { ...handlers };
  }

  function wireFlatShotInteractions(deps = {}) {
    const documentRef = deps.document || (typeof document !== "undefined" ? document : null);
    const windowRef = deps.window || (typeof window !== "undefined" ? window : null);
    const $ = deps.$ || (() => null);
    const $$ = deps.$$ || (() => []);
    const handlers = createFlatShotInteractionHandlers(deps.handlers || {});
    const onboardingBackgroundHelpers = deps.onboardingBackgroundHelpers || null;

    if (!documentRef || !windowRef) {
      return;
    }

    documentRef.addEventListener("load", handlers.documentLoad, true);
    documentRef.addEventListener("error", handlers.documentError, true);
    documentRef.addEventListener("pointerdown", handlers.documentPointerDown, true);
    documentRef.addEventListener("click", handlers.inspectorDisclosureClick, true);
    documentRef.addEventListener("click", handlers.documentClick);
    documentRef.addEventListener("toggle", handlers.documentToggle, true);
    documentRef.addEventListener("input", handlers.documentInput);
    documentRef.addEventListener("change", handlers.documentChange);
    documentRef.addEventListener("focusout", handlers.documentFocusOut);
    documentRef.addEventListener("submit", handlers.documentSubmit);
    documentRef.addEventListener("keydown", handlers.documentKeydown);
    documentRef.addEventListener("dragenter", handlers.documentDragEnter);
    documentRef.addEventListener("dragover", handlers.documentDragOver);
    documentRef.addEventListener("dragleave", handlers.documentDragLeave);
    documentRef.addEventListener("drop", handlers.documentDrop);
    documentRef.addEventListener("scroll", handlers.positionBackgroundPresetEditor, true);

    optionalElement($, "#bridge-url")?.addEventListener("input", handlers.bridgeUrlInput);
    optionalElement($, "#bridge-scan-path")?.addEventListener("input", handlers.bridgeScanPathInput);
    optionalElement($, "#image-search")?.addEventListener("input", handlers.imageSearchInput);
    optionalElement($, "#image-list")?.addEventListener("scroll", handlers.galleryScroll);
    optionalElement($, "#format-select")?.addEventListener("change", handlers.formatSelectChange);
    optionalElement($, "#output-profile-select")?.addEventListener("change", handlers.outputProfileSelectChange);
    optionalElement($, "#size-select")?.addEventListener("input", handlers.sizeSelectInput);
    optionalElement($, "#size-select")?.addEventListener("change", handlers.sizeSelectChange);
    optionalElement($, "#background-select")?.addEventListener("change", handlers.backgroundSelectChange);
    optionalElement($, "#destination-mode")?.addEventListener("change", handlers.destinationModeChange);
    optionalElement($, "#destination-input")?.addEventListener("input", handlers.destinationInput);
    optionalElement($, "#naming-input")?.addEventListener("input", handlers.namingInput);

    $$("[data-setting]").forEach((input) => {
      input.addEventListener("input", handlers.settingInput);
      input.addEventListener("change", handlers.settingInput);
    });
    $$("[data-lighting-field]").forEach((input) => {
      input.addEventListener("input", handlers.lightingFieldInput);
      input.addEventListener("change", handlers.lightingFieldInput);
    });
    $$("[data-lighting-number-field]").forEach((input) => {
      input.addEventListener("input", handlers.lightingNumberFieldInput);
      input.addEventListener("change", handlers.lightingNumberFieldInput);
    });
    $$("[data-lighting-preset]").forEach((button) => {
      button.addEventListener("click", () => handlers.lightingPresetClick?.(button));
    });

    wireLightingStage(optionalElement($, "#lighting-stage"), handlers);
    wireViewerCanvas(optionalElement($, "#preview-canvas"), documentRef, handlers);

    windowRef.addEventListener("flatshot:before-live-reload", handlers.writeSessionSnapshot);
    windowRef.addEventListener("beforeunload", handlers.writeSessionSnapshot);
    windowRef.addEventListener("resize", handlers.positionBackgroundPresetEditor);

    void onboardingBackgroundHelpers?.initialize?.({ document: documentRef });
    handlers.initViewerResizeObserver?.();
    handlers.startup?.();
  }

  function wireLightingStage(lightingStage, handlers) {
    if (!lightingStage) {
      return;
    }
    let lightingDragActive = false;
    let lightingDragChanged = false;
    let lightingPointerId = null;
    const finishLightingDrag = (event) => {
      if (!lightingDragActive || (lightingPointerId !== null && event.pointerId !== lightingPointerId)) {
        return;
      }
      lightingDragActive = false;
      lightingPointerId = null;
      lightingStage.releasePointerCapture?.(event.pointerId);
      if (lightingDragChanged) {
        lightingDragChanged = false;
        handlers.refreshPreviewAfterSettingChange?.();
      }
    };
    lightingStage.addEventListener("pointerdown", (event) => {
      event.preventDefault();
      lightingDragActive = true;
      lightingDragChanged = false;
      lightingPointerId = event.pointerId;
      lightingStage.setPointerCapture?.(event.pointerId);
      lightingDragChanged = Boolean(handlers.updateLightingScenePosition?.(event.clientX, event.clientY, { deferRender: true }));
    });
    lightingStage.addEventListener("pointermove", (event) => {
      if (lightingDragActive && event.pointerId === lightingPointerId) {
        event.preventDefault();
        lightingDragChanged = Boolean(handlers.updateLightingScenePosition?.(event.clientX, event.clientY, { deferRender: true }))
          || lightingDragChanged;
      }
    });
    lightingStage.addEventListener("pointerup", (event) => {
      event.preventDefault();
      finishLightingDrag(event);
    });
    lightingStage.addEventListener("pointercancel", finishLightingDrag);
  }

  function wireViewerCanvas(canvas, documentRef, handlers) {
    if (!canvas) {
      return;
    }
    canvas.addEventListener("wheel", handlers.viewerWheel, { passive: false });
    canvas.addEventListener("dblclick", handlers.viewerDoubleClick);
    canvas.addEventListener("pointerdown", handlers.viewerPointerDown);
    documentRef.addEventListener("pointermove", handlers.viewerPointerMove);
    documentRef.addEventListener("pointerup", handlers.viewerPointerEnd);
    documentRef.addEventListener("pointercancel", handlers.viewerPointerEnd);
  }

  return {
    createFlatShotInteractionHandlers,
    wireFlatShotInteractions,
  };
});
