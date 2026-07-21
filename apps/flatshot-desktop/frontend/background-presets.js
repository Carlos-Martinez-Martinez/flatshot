(function (root, factory) {
  const api = factory(root);
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotBackgroundPresets = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function (root) {
  const SOFT_BLACK = "soft-black";
  const DEFAULT_RGB = [230, 230, 230];
  const DEFAULT_PRESETS = [
    { id: "rgb230", name: "Gris claro", kind: "rgb", rgb: [230, 230, 230] },
    { id: "white", name: "Blanco", kind: "rgb", rgb: [255, 255, 255] },
    { id: "transparent", name: "Transparente", kind: "transparent", rgb: [230, 230, 230] },
  ];

  function outputHelpers(options = {}) {
    return options.outputProfileHelpers || root.FlatShotOutputProfiles || {};
  }

  function clampRgbChannel(value) {
    const channel = Number.parseInt(String(value).trim(), 10);
    if (!Number.isInteger(channel)) {
      return null;
    }
    return Math.max(0, Math.min(255, channel));
  }

  function parseRgbBackgroundFallback(value) {
    const match = /^rgb\s*:\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})$/i.exec(String(value || "").trim());
    if (!match) {
      return null;
    }
    const channels = match.slice(1).map(clampRgbChannel);
    return channels.every((channel) => channel !== null) ? channels : null;
  }

  function parseRgbBackground(value, options = {}) {
    const helpers = outputHelpers(options);
    return helpers.parseRgbBackground
      ? helpers.parseRgbBackground(value)
      : parseRgbBackgroundFallback(value);
  }

  function rgbBackgroundValue(red, green, blue, options = {}) {
    const helpers = outputHelpers(options);
    if (helpers.rgbBackgroundValue) {
      return helpers.rgbBackgroundValue(red, green, blue);
    }
    const channels = [red, green, blue].map(clampRgbChannel);
    return channels.every((channel) => channel !== null) ? `rgb:${channels.join(",")}` : "";
  }

  function normalizeBackgroundValue(value, fallback = "rgb230", options = {}) {
    const helpers = outputHelpers(options);
    return helpers.normalizeBackgroundValue
      ? helpers.normalizeBackgroundValue(value, fallback)
      : normalizeBackgroundValueFallback(value, fallback, options);
  }

  function normalizeBackgroundValueFallback(value, fallback = "rgb230", options = {}) {
    if (["rgb230", "white", "transparent"].includes(value)) {
      return value;
    }
    const custom = parseRgbBackground(value, options);
    if (custom) {
      return `rgb:${custom.join(",")}`;
    }
    return ["rgb230", "white", "transparent"].includes(fallback) || parseRgbBackground(fallback, options)
      ? normalizeBackgroundValueFallback(fallback, "rgb230", options)
      : "rgb230";
  }

  function backgroundColorTuple(value, options = {}) {
    const helpers = outputHelpers(options);
    if (helpers.backgroundColorTuple) {
      return helpers.backgroundColorTuple(value);
    }
    const custom = parseRgbBackground(value, options);
    if (custom) {
      return custom;
    }
    if (value === "white") {
      return [255, 255, 255];
    }
    return DEFAULT_RGB;
  }

  function uniquePresetId(name = "fondo", seed = Date.now(), options = {}) {
    const helpers = outputHelpers(options);
    if (helpers.uniqueOutputProfileId) {
      return helpers.uniqueOutputProfileId(name, seed);
    }
    const base = String(name)
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")
      || "fondo";
    return `${base}-${String(seed).replace(/\D/g, "").slice(-6) || Date.now()}`;
  }

  function softBlackValue(options = {}) {
    return options.softBlackPreviewBg || root.SOFT_BLACK_PREVIEW_BG || SOFT_BLACK;
  }

  function normalizePreviewBackgroundValue(value, options = {}) {
    if (value === softBlackValue(options)) {
      return softBlackValue(options);
    }
    if (value === "white" || value === "transparent" || value === "rgb230") {
      return value;
    }
    const custom = parseRgbBackground(value, options);
    return custom ? `rgb:${custom.join(",")}` : "rgb230";
  }

  function backgroundSelectMode(value, options = {}) {
    return parseRgbBackground(value, options) ? "custom" : normalizeBackgroundValue(value, "rgb230", options);
  }

  function backgroundCssColor(value, options = {}) {
    const custom = parseRgbBackground(value, options);
    if (custom) {
      return `rgb(${custom.join(", ")})`;
    }
    if (value === softBlackValue(options)) {
      return "rgb(32, 34, 37)";
    }
    if (value === "white") {
      return "rgb(255, 255, 255)";
    }
    if (value === "transparent") {
      return "";
    }
    return "rgb(230, 230, 230)";
  }

  function backgroundVisualMode(value, options = {}) {
    if (value === softBlackValue(options)) {
      return "custom";
    }
    if (value === "white" || value === "transparent") {
      return value;
    }
    return parseRgbBackground(value, options) ? "custom" : "rgb230";
  }

  function previewCustomRgbChannels(value, options = {}) {
    const custom = parseRgbBackground(value, options);
    if (custom) {
      return custom;
    }
    if (value === softBlackValue(options)) {
      return [32, 34, 37];
    }
    return backgroundColorTuple(value || "rgb230", options);
  }

  function rgbChannelsFromHex(value, fallback = DEFAULT_RGB) {
    const match = /^#?([0-9a-fA-F]{6})$/.exec(String(value || "").trim());
    if (!match) {
      return Array.isArray(fallback) ? fallback.slice(0, 3) : DEFAULT_RGB;
    }
    return [0, 2, 4].map((offset) => Number.parseInt(match[1].slice(offset, offset + 2), 16));
  }

  function rgbHexValue(channels = [], fallback = "#e6e6e6") {
    const rgb = Array.isArray(channels) ? channels : DEFAULT_RGB;
    const parsed = rgb.slice(0, 3).map(clampRgbChannel);
    if (!parsed.every((channel) => channel !== null)) {
      return fallback;
    }
    return `#${parsed.map((channel) => channel.toString(16).padStart(2, "0")).join("")}`;
  }

  function previewCustomBackgroundValue(channels = [], options = {}) {
    const fallback = Array.isArray(options.fallback) ? options.fallback : DEFAULT_RGB;
    const clampNumber = options.clampNumber || ((value, min, max, fallbackValue) => {
      const numeric = Number(value);
      return Number.isFinite(numeric) ? Math.max(min, Math.min(max, numeric)) : fallbackValue;
    });
    const rgb = ["r", "g", "b"].map((channel, index) => {
      const value = Array.isArray(channels) ? channels[index] : channels[channel];
      return Math.round(clampNumber(value, 0, 255, fallback[index]));
    });
    return `rgb:${rgb.join(",")}`;
  }

  function previewBackgroundLabel(value, options = {}) {
    const custom = parseRgbBackground(value, options);
    if (custom) {
      return `RGB ${custom.join(", ")}`;
    }
    if (value === softBlackValue(options)) {
      return "negro suave";
    }
    const backgroundLabel = options.backgroundLabel || root.FlatShotSettingsView?.backgroundLabel || ((background) => String(background || "Fondo"));
    return backgroundLabel(value);
  }

  function defaultPresets(options = {}) {
    return Array.isArray(options.defaultPresets) && options.defaultPresets.length
      ? options.defaultPresets
      : DEFAULT_PRESETS;
  }

  function defaultPresetIds(options = {}) {
    return new Set(defaultPresets(options).map((preset) => String(preset?.id || "").trim()).filter(Boolean));
  }

  function isSystemBackgroundPreset(preset, options = {}) {
    if (!preset || typeof preset !== "object") {
      return false;
    }
    return preset.system === true || defaultPresetIds(options).has(String(preset.id || "").trim());
  }

  function uniqueBackgroundPresetListId(baseId, seen) {
    const base = String(baseId || "fondo").trim() || "fondo";
    let id = base;
    let suffix = 2;
    while (seen.has(id)) {
      id = `${base}-${suffix}`;
      suffix += 1;
    }
    seen.add(id);
    return id;
  }

  function normalizeBackgroundPreset(preset, index = 0, options = {}) {
    const presets = defaultPresets(options);
    const source = preset && typeof preset === "object" ? preset : {};
    const kind = source.kind === "transparent" || source.value === "transparent" ? "transparent" : "rgb";
    const parsed = Array.isArray(source.rgb)
      ? source.rgb
      : parseRgbBackground(source.value || source.background, options);
    const fallbackRgb = presets[index % presets.length]?.rgb || DEFAULT_RGB;
    const rgb = kind === "transparent"
      ? fallbackRgb
      : (parsed || fallbackRgb).map((channel) => clampRgbChannel(channel) ?? 0);
    const id = String(source.id || uniquePresetId(source.name || "fondo", index, options)).trim();
    return {
      id,
      kind,
      name: String(source.name || (kind === "transparent" ? "Transparente" : `RGB ${rgb.join(", ")}`)).trim(),
      rgb,
    };
  }

  function normalizeBackgroundPresetList(presets, options = {}) {
    const systemIds = defaultPresetIds(options);
    const seen = new Set();
    const systemPresets = defaultPresets(options)
      .map((preset, index) => ({ ...normalizeBackgroundPreset(preset, index, options), system: true }))
      .filter((preset) => preset.id && preset.name)
      .map((preset) => ({ ...preset, id: uniqueBackgroundPresetListId(preset.id, seen) }));
    const source = Array.isArray(presets) ? presets : [];
    const customPresets = source
      .filter((preset) => {
        const id = String(preset?.id || "").trim();
        return (!id || !systemIds.has(id)) && preset?.system !== true;
      })
      .map((preset, index) => normalizeBackgroundPreset(preset, index, options))
      .filter((preset) => preset.id && preset.name)
      .map((preset) => ({ ...preset, id: uniqueBackgroundPresetListId(preset.id, seen) }));
    return [...systemPresets, ...customPresets];
  }

  function backgroundPresetsForStorage(presets, options = {}) {
    return normalizeBackgroundPresetList(presets, options)
      .filter((preset) => !isSystemBackgroundPreset(preset, options))
      .map((preset) => {
        const storagePreset = { ...preset };
        delete storagePreset.system;
        return storagePreset;
      });
  }

  function readBackgroundPresets(storage, key, options = {}) {
    const storageHelpers = options.storageHelpers || root.FlatShotStorage;
    const saved = storageHelpers?.readJson ? storageHelpers.readJson(storage, key, null) : null;
    return normalizeBackgroundPresetList(saved, options);
  }

  function backgroundPresetValue(preset, options = {}) {
    if (!preset || preset.kind === "transparent") {
      return "transparent";
    }
    const rgb = preset.rgb || DEFAULT_RGB;
    if (preset.id === "rgb230" && rgb[0] === 230 && rgb[1] === 230 && rgb[2] === 230) {
      return "rgb230";
    }
    if (preset.id === "white" && rgb[0] === 255 && rgb[1] === 255 && rgb[2] === 255) {
      return "white";
    }
    return rgbBackgroundValue(rgb[0], rgb[1], rgb[2], options) || "rgb230";
  }

  function backgroundPresetLabel(preset) {
    if (!preset) {
      return "Fondo";
    }
    return preset.name;
  }

  function backgroundPresetByValue(value, presets = [], options = {}) {
    const normalized = normalizeBackgroundValue(value, "rgb230", options);
    return presets.find((preset) => normalizeBackgroundValue(backgroundPresetValue(preset, options), "rgb230", options) === normalized) || null;
  }

  function backgroundSelectOptionsHtml(selectedValue, options = {}) {
    const presets = Array.isArray(options.presets) ? options.presets : [];
    const escapeHtml = options.escapeHtml || ((value) => String(value));
    const selected = normalizeBackgroundValue(selectedValue, "rgb230", options);
    const presetOptions = presets.map((preset) => {
      const value = backgroundPresetValue(preset, options);
      return `<option value="${escapeHtml(value)}">${escapeHtml(backgroundPresetLabel(preset))}</option>`;
    }).join("");
    if (presets.some((preset) => normalizeBackgroundValue(backgroundPresetValue(preset, options), "rgb230", options) === selected)) {
      return presetOptions;
    }
    const backgroundLabel = options.backgroundLabel || root.FlatShotSettingsView?.backgroundLabel || ((background) => String(background || "Fondo"));
    return `${presetOptions}<option value="${escapeHtml(selected)}">${escapeHtml(`Actual · ${backgroundLabel(selected)}`)}</option>`;
  }

  return {
    backgroundCssColor,
    backgroundPresetByValue,
    backgroundPresetLabel,
    backgroundPresetValue,
    backgroundPresetsForStorage,
    backgroundSelectMode,
    backgroundSelectOptionsHtml,
    backgroundVisualMode,
    isSystemBackgroundPreset,
    normalizeBackgroundPreset,
    normalizeBackgroundPresetList,
    normalizePreviewBackgroundValue,
    previewBackgroundLabel,
    previewCustomBackgroundValue,
    previewCustomRgbChannels,
    readBackgroundPresets,
    rgbChannelsFromHex,
    rgbHexValue,
  };
});
