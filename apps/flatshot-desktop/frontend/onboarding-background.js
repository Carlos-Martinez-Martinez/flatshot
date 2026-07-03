(function (root, factory) {
  const api = factory(root);
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotOnboardingBackground = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function (root) {
  const ONBOARDING_BACKGROUND_ASSETS = [];

  const BACKGROUND_ID = "onboarding-background";
  const SLIDE_INTERVAL_MS = 9000;

  function uniqueLoadedAssets(assets) {
    const seen = new Set();
    return assets.filter((asset) => {
      if (!asset || seen.has(asset)) {
        return false;
      }
      seen.add(asset);
      return true;
    });
  }

  function preloadAsset(src) {
    return new Promise((resolve) => {
      const ImageConstructor = root.Image;
      if (!ImageConstructor) {
        resolve("");
        return;
      }
      const image = new ImageConstructor();
      image.onload = () => resolve(src);
      image.onerror = () => resolve("");
      image.src = src;
    });
  }

  async function preloadAssets(assets = ONBOARDING_BACKGROUND_ASSETS) {
    const loaded = await Promise.all(assets.map(preloadAsset));
    return uniqueLoadedAssets(loaded);
  }

  function createLayer(documentRef, assets, options = {}) {
    const layer = documentRef.createElement("div");
    layer.id = BACKGROUND_ID;
    layer.className = "onboarding-background";
    layer.classList.toggle("is-fallback", Boolean(options.fallback));
    layer.setAttribute("aria-hidden", "true");

    assets.forEach((asset, index) => {
      const slide = documentRef.createElement("span");
      slide.className = "onboarding-background__slide";
      slide.style.backgroundImage = `url("${asset}")`;
      slide.classList.toggle("is-active", index === 0);
      layer.appendChild(slide);
    });

    return layer;
  }

  function syncLayerState(shell, layer) {
    const active = shell?.dataset?.uiState === "no_folder";
    layer.classList.toggle("is-visible", active);
  }

  function startCarousel(layer, reducedMotion) {
    const slides = Array.from(layer.querySelectorAll(".onboarding-background__slide"));
    if (reducedMotion || slides.length < 2) {
      return 0;
    }

    let activeIndex = 0;
    return root.setInterval(() => {
      slides[activeIndex]?.classList.remove("is-active");
      activeIndex = (activeIndex + 1) % slides.length;
      slides[activeIndex]?.classList.add("is-active");
    }, SLIDE_INTERVAL_MS);
  }

  async function initialize(options = {}) {
    const documentRef = options.document || root.document;
    if (!documentRef) {
      return null;
    }

    const shell = documentRef.querySelector(".app-shell");
    const previewCanvas = documentRef.querySelector("#preview-canvas");
    if (!shell || !previewCanvas || documentRef.getElementById(BACKGROUND_ID)) {
      return null;
    }

    const assets = await preloadAssets(options.assets || ONBOARDING_BACKGROUND_ASSETS);
    const layer = createLayer(documentRef, assets, { fallback: !assets.length });
    previewCanvas.prepend(layer);
    syncLayerState(shell, layer);

    const reducedMotion = Boolean(root.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches);
    const intervalId = startCarousel(layer, reducedMotion);
    const MutationObserverConstructor = root.MutationObserver;
    const observer = MutationObserverConstructor
      ? new MutationObserverConstructor(() => syncLayerState(shell, layer))
      : null;
    observer?.observe(shell, { attributes: true, attributeFilter: ["data-ui-state"] });

    return {
      layer,
      stop() {
        if (intervalId) {
          root.clearInterval(intervalId);
        }
        observer?.disconnect();
        layer.remove();
      },
    };
  }

  return {
    ONBOARDING_BACKGROUND_ASSETS,
    initialize,
    preloadAssets,
    uniqueLoadedAssets,
  };
});
