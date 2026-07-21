(function (root, factory) {
  const api = factory(root);
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotOnboardingBackground = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function (root) {
  const ONBOARDING_BACKGROUND_ASSET_DIR = "./assets/onboarding/";
  const ONBOARDING_BACKGROUND_ASSETS = [
    "./assets/onboarding/flatshot-abstract-01.png",
    "./assets/onboarding/flatshot-abstract-02.png",
    "./assets/onboarding/flatshot-abstract-03.png",
    "./assets/onboarding/flatshot-abstract-04.png",
    "./assets/onboarding/flatshot-abstract-05.png",
  ];

  const BACKGROUND_ID = "onboarding-background";
  const SLIDE_INTERVAL_MS = 9000;
  const IMAGE_ASSET_PATTERN = /\.(?:png|jpe?g|webp|avif)$/i;

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

  function cleanAssetPath(value) {
    let asset = String(value || "").trim().replaceAll("\\", "/");
    if (!asset) {
      return "";
    }
    asset = asset.split("#", 1)[0].split("?", 1)[0];
    try {
      asset = decodeURIComponent(asset);
    } catch {
      return "";
    }
    if (
      !asset
      || asset.endsWith("/")
      || asset.includes("://")
      || asset.startsWith("//")
      || asset.includes("..")
      || /["<>]/.test(asset)
      || !IMAGE_ASSET_PATTERN.test(asset)
    ) {
      return "";
    }
    if (asset.startsWith(ONBOARDING_BACKGROUND_ASSET_DIR)) {
      return asset;
    }
    if (asset.startsWith(ONBOARDING_BACKGROUND_ASSET_DIR.slice(2))) {
      return `./${asset}`;
    }
    if (!asset.includes("/")) {
      return `${ONBOARDING_BACKGROUND_ASSET_DIR}${asset}`;
    }
    return "";
  }

  function normalizeAssetList(assets = []) {
    return uniqueLoadedAssets(
      (Array.isArray(assets) ? assets : [])
        .map(cleanAssetPath)
        .filter(Boolean)
    );
  }

  function assetsFromDirectoryListing(html) {
    const matches = Array.from(String(html || "").matchAll(/\bhref\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))/gi));
    return normalizeAssetList(matches.map((match) => match[1] || match[2] || match[3]))
      .sort((first, second) => first.localeCompare(second));
  }

  async function configuredAssetCandidates(options = {}) {
    if (Array.isArray(options.assets)) {
      return normalizeAssetList(options.assets);
    }
    const fetchImpl = options.fetch || root.fetch?.bind(root);
    if (fetchImpl) {
      try {
        const response = await fetchImpl(ONBOARDING_BACKGROUND_ASSET_DIR);
        if (response?.ok && typeof response.text === "function") {
          const discovered = assetsFromDirectoryListing(await response.text());
          if (discovered.length) {
            return discovered;
          }
        }
      } catch {
        // Static directory listing is a progressive enhancement; fallback below.
      }
    }
    return ONBOARDING_BACKGROUND_ASSETS.slice();
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

  function normalizedPositiveInteger(value) {
    const number = Number(value);
    return Number.isFinite(number) ? Math.max(0, Math.floor(number)) : 0;
  }

  function boundedRandom(random = root.Math?.random?.bind(root.Math)) {
    const value = typeof random === "function" ? Number(random()) : Math.random();
    if (!Number.isFinite(value)) {
      return 0;
    }
    return Math.min(Math.max(value, 0), 0.999999);
  }

  function pickInitialAssetIndex(count, random) {
    const total = normalizedPositiveInteger(count);
    if (total < 2) {
      return 0;
    }
    return Math.floor(boundedRandom(random) * total);
  }

  function nextRandomSlideIndex(currentIndex, count, random) {
    const total = normalizedPositiveInteger(count);
    if (total < 2) {
      return 0;
    }
    const current = Math.min(Math.max(normalizedPositiveInteger(currentIndex), 0), total - 1);
    const offset = 1 + Math.floor(boundedRandom(random) * (total - 1));
    return (current + offset) % total;
  }

  function createLayer(documentRef, assets, options = {}) {
    const layer = documentRef.createElement("div");
    layer.id = BACKGROUND_ID;
    layer.className = "onboarding-background";
    layer.classList.toggle("is-fallback", Boolean(options.fallback));
    layer.setAttribute("aria-hidden", "true");
    const activeIndex = Math.min(
      Math.max(normalizedPositiveInteger(options.activeIndex), 0),
      Math.max(assets.length - 1, 0)
    );

    assets.forEach((asset, index) => {
      const slide = documentRef.createElement("span");
      slide.className = "onboarding-background__slide";
      slide.style.backgroundImage = `url("${asset}")`;
      slide.classList.toggle("is-active", index === activeIndex);
      layer.appendChild(slide);
    });

    return layer;
  }

  function syncLayerState(shell, layer) {
    const active = shell?.dataset?.uiState === "no_folder";
    layer.classList.toggle("is-visible", active);
  }

  function startCarousel(layer, reducedMotion, random) {
    const slides = Array.from(layer.querySelectorAll(".onboarding-background__slide"));
    if (reducedMotion || slides.length < 2) {
      return 0;
    }

    let activeIndex = slides.findIndex((slide) => slide.classList.contains("is-active"));
    if (activeIndex < 0) {
      activeIndex = 0;
      slides[activeIndex]?.classList.add("is-active");
    }
    return root.setInterval(() => {
      slides[activeIndex]?.classList.remove("is-active");
      activeIndex = nextRandomSlideIndex(activeIndex, slides.length, random);
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

    const random = typeof options.random === "function" ? options.random : root.Math?.random?.bind(root.Math);
    const assets = await preloadAssets(await configuredAssetCandidates(options));
    const layer = createLayer(documentRef, assets, {
      activeIndex: pickInitialAssetIndex(assets.length, random),
      fallback: !assets.length,
    });
    previewCanvas.prepend(layer);
    syncLayerState(shell, layer);

    const reducedMotion = Boolean(root.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches);
    const intervalId = startCarousel(layer, reducedMotion, random);
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
    ONBOARDING_BACKGROUND_ASSET_DIR,
    ONBOARDING_BACKGROUND_ASSETS,
    assetsFromDirectoryListing,
    configuredAssetCandidates,
    initialize,
    normalizeAssetList,
    nextRandomSlideIndex,
    pickInitialAssetIndex,
    preloadAssets,
    uniqueLoadedAssets,
  };
});
