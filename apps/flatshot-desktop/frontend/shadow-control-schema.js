(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotShadowControls = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const commonLabels = {
    opacity: "Densidad de sombra",
    blur: "Suavidad",
    distance: "Distancia",
    padding: "Margen",
    noise: "Grano de sombra",
    contact_blur: "Suavidad de contacto",
    scale_adjustment: "Escala del producto",
    angle: "Dirección de la sombra",
    contraction: "Reducir halo del borde",
    adaptive_zoom: "Ajuste automático del producto",
    shadow_engine: "Motor de sombra",
    fusion: "Protección interior",
    lighting_scene: "Escena de luz",
    spread: "Difusión",
  };

  const advancedKeys = [
    "spread",
    "noise",
    "contact_blur",
    "scale_adjustment",
    "fusion",
    "angle",
    "contraction",
    "adaptive_zoom",
    "shadow_engine",
    "lighting_scene",
  ];

  const universalKeys = new Set([
    "opacity",
    "blur",
    "distance",
    "padding",
    "shadow_engine",
    "noise",
    "contact_blur",
    "scale_adjustment",
    "contraction",
    "adaptive_zoom",
  ]);

  const profiles = {
    realistic_v2: {
      label: "Realista",
      supported: new Set([...universalKeys, "spread", "angle"]),
      labels: { spread: "Difusión" },
    },
    studio_2_5d: {
      label: "Estudio con luz",
      supported: new Set([...universalKeys, "spread", "lighting_scene"]),
      labels: { spread: "Expansión" },
    },
    legacy: {
      label: "Clásico · compatibilidad",
      supported: new Set([...universalKeys, "fusion", "angle"]),
      labels: {},
    },
  };

  function normalizeEngine(engine) {
    return profiles[engine] ? engine : "realistic_v2";
  }

  function engineProfile(engine) {
    const engineId = normalizeEngine(engine);
    const profile = profiles[engineId];
    return {
      id: engineId,
      label: profile.label,
      supports: (key) => profile.supported.has(key),
      labelFor: (key) => profile.labels[key] || commonLabels[key] || key,
    };
  }

  function visibleKeysForEngine(engine) {
    const profile = engineProfile(engine);
    return advancedKeys.filter((key) => profile.supports(key));
  }

  function applyControlVisibility(documentRef, engine) {
    if (!documentRef?.querySelectorAll) {
      return;
    }
    const profile = engineProfile(engine);
    documentRef.querySelectorAll("[data-control-key]").forEach((control) => {
      const key = control.dataset.controlKey;
      const visible = profile.supports(key);
      control.hidden = !visible;
      control.classList.toggle("is-hidden", !visible);
      control.setAttribute("aria-hidden", String(!visible));
    });
    documentRef.querySelectorAll("[data-control-label-key]").forEach((label) => {
      const key = label.dataset.controlLabelKey;
      const text = profile.labelFor(key);
      if (!label.id) {
        label.id = `${key}-label`;
      }
      label.textContent = text;
      label.title = text;
    });
    documentRef.querySelectorAll("[data-control-group]").forEach((group) => {
      const keys = String(group.dataset.controlGroup || "")
        .split(",")
        .map((key) => key.trim())
        .filter(Boolean);
      const visible = keys.length === 0 || keys.some((key) => profile.supports(key));
      group.hidden = !visible;
      group.classList.toggle("is-hidden", !visible);
    });
  }

  return {
    advancedKeys: [...advancedKeys],
    commonLabels: { ...commonLabels },
    applyControlVisibility,
    engineProfile,
    normalizeEngine,
    visibleKeysForEngine,
  };
});
