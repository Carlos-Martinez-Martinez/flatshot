(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotOutputProfiles = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  function outputProfileNameForDisplay(name) {
    return String(name || "")
      .replace(/\bRGB\s*230\b/gi, "gris claro")
      .replace(/\bRGB230\b/gi, "gris claro");
  }

  function normalizeExportFormat(value) {
    const text = String(value || "JPG").trim().toUpperCase().replace(/^\./, "");
    if (text === "JPEG") {
      return "JPG";
    }
    return text === "PNG" ? "PNG" : "JPG";
  }

  function clampRgbChannel(value) {
    const channel = Number.parseInt(String(value).trim(), 10);
    if (!Number.isInteger(channel) || channel < 0 || channel > 255) {
      return null;
    }
    return channel;
  }

  function rgbBackgroundValue(red, green, blue) {
    const channels = [red, green, blue].map(clampRgbChannel);
    return channels.every((channel) => channel !== null)
      ? `rgb:${channels.join(",")}`
      : "";
  }

  function parseRgbBackground(value) {
    const match = /^rgb\s*:\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})$/i.exec(String(value || "").trim());
    if (!match) {
      return null;
    }
    const channels = match.slice(1).map(clampRgbChannel);
    return channels.every((channel) => channel !== null) ? channels : null;
  }

  function customRgbBackgroundValue(value) {
    const text = String(value || "").trim();
    const prefixed = parseRgbBackground(text);
    if (prefixed) {
      return `rgb:${prefixed.join(",")}`;
    }
    const channels = text.split(/[,\s]+/).filter(Boolean);
    return channels.length === 3 ? rgbBackgroundValue(channels[0], channels[1], channels[2]) : "";
  }

  function isValidBackgroundValue(value) {
    return ["rgb230", "white", "transparent"].includes(value) || Boolean(parseRgbBackground(value));
  }

  function normalizeBackgroundValue(value, fallback = "rgb230") {
    if (["rgb230", "white", "transparent"].includes(value)) {
      return value;
    }
    const custom = parseRgbBackground(value);
    if (custom) {
      return `rgb:${custom.join(",")}`;
    }
    return isValidBackgroundValue(fallback) ? normalizeBackgroundValue(fallback, "rgb230") : "rgb230";
  }

  function backgroundCustomText(value) {
    const custom = parseRgbBackground(value);
    return custom ? custom.join(", ") : "";
  }

  function uniqueOutputProfileId(name = "formato", seed = Date.now()) {
    const base = String(name)
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")
      || "formato";
    return `${base}-${String(seed).replace(/\D/g, "").slice(-6) || Date.now()}`;
  }

  function normalizeOutputProfile(profile, index = 0) {
    const source = profile && typeof profile === "object" ? profile : {};
    const width = Math.max(1, Number.parseInt(source.width, 10) || 1800);
    const height = Math.max(1, Number.parseInt(source.height, 10) || 2400);
    const format = normalizeExportFormat(source.format);
    const background = normalizeBackgroundValue(source.background);
    const destinationMode = source.destinationMode === "custom" ? "custom" : "source";
    return {
      id: String(source.id || uniqueOutputProfileId("formato", index)).trim(),
      name: outputProfileNameForDisplay(String(source.name || `Formato ${index + 1}`).trim()),
      enabled: typeof source.enabled === "boolean" ? source.enabled : false,
      format,
      width,
      height,
      background,
      destinationMode,
      destinationValue: String(source.destinationValue || (destinationMode === "custom" ? "" : "Salida")),
      naming: String(source.naming || "{original}{suffix}"),
      suffix: source.suffix === undefined || source.suffix === null ? "_PRO" : String(source.suffix),
    };
  }

  function dedupeOutputProfileIds(profiles) {
    const seen = new Set();
    return profiles.map((profile, index) => {
      let id = profile.id || uniqueOutputProfileId(profile.name, index);
      while (seen.has(id)) {
        id = uniqueOutputProfileId(profile.name, index + seen.size);
      }
      seen.add(id);
      return { ...profile, id };
    });
  }

  function normalizeOutputProfileList(profiles, activeProfileId = "") {
    const normalized = Array.isArray(profiles)
      ? profiles.map(normalizeOutputProfile).filter((profile) => profile.name)
      : [];
    const deduped = dedupeOutputProfileIds(normalized);
    return deduped;
  }

  function outputProfileSize(profile) {
    return `${Math.max(1, Number(profile?.width) || 1800)}x${Math.max(1, Number(profile?.height) || 2400)}`;
  }

  function parseOutputSize(value) {
    const match = /^(\d+)\s*[x×]\s*(\d+)$/i.exec(String(value || "").trim());
    if (!match) {
      return { width: 1800, height: 2400, normalized: "1800x2400" };
    }
    const width = Math.max(1, Number.parseInt(match[1], 10) || 1800);
    const height = Math.max(1, Number.parseInt(match[2], 10) || 2400);
    return { width, height, normalized: `${width}x${height}` };
  }

  function backgroundColorTuple(value) {
    const custom = parseRgbBackground(value);
    if (custom) {
      return custom;
    }
    if (value === "white") {
      return [255, 255, 255];
    }
    return [230, 230, 230];
  }

  function exportVariantId(profile, index, seenVariantIds = new Set()) {
    const base = String(profile.id || profile.name || `salida-${index + 1}`)
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^A-Za-z0-9_-]+/g, "_")
      .replace(/^_+|_+$/g, "")
      || `salida_${index + 1}`;
    const safeBase = /^[A-Za-z0-9_-]+$/.test(base) ? base : `salida_${index + 1}`;
    let candidate = safeBase;
    let suffix = 2;
    while (seenVariantIds.has(candidate)) {
      candidate = `${safeBase}_${suffix}`;
      suffix += 1;
    }
    seenVariantIds.add(candidate);
    return candidate;
  }

  function exportVariantPayloadFromProfile(profile, index, seenVariantIds = new Set()) {
    const size = parseOutputSize(outputProfileSize(profile));
    const variantId = exportVariantId(profile, index, seenVariantIds);
    return {
      id: variantId,
      label: profile.name,
      enabled: true,
      format: profile.format,
      transparent_bg: profile.background === "transparent",
      bg_color: backgroundColorTuple(profile.background),
      suffix: profile.suffix,
      naming_template: profile.naming,
      output_destination: profile.destinationMode === "custom" ? "custom" : "subfolder",
      output_folder_name: profile.destinationMode === "source" ? profile.destinationValue || "Salida" : null,
      custom_output_path: profile.destinationMode === "custom" ? profile.destinationValue : null,
      output_width: size.width,
      output_height: size.height,
    };
  }

  function outputProfileValidation(raw) {
    const errors = [];
    const warnings = [];
    const fields = {};
    const fieldMessages = {};
    const width = Number.parseInt(raw.width, 10);
    const height = Number.parseInt(raw.height, 10);
    const invalidFilenameChars = /[<>:"/\\|?*]/;
    const rememberFieldMessage = (field, message) => {
      if (!field) {
        return;
      }
      fieldMessages[field] = fieldMessages[field] || [];
      fieldMessages[field].push(message);
    };
    const addError = (field, message) => {
      errors.push(message);
      if (field) {
        fields[field] = "error";
        rememberFieldMessage(field, message);
      }
    };
    const addWarning = (field, message) => {
      warnings.push(message);
      if (field && fields[field] !== "error") {
        fields[field] = "warning";
      }
      rememberFieldMessage(field, message);
    };

    if (!String(raw.name || "").trim()) {
      addError("name", "Pon un nombre al formato.");
    }
    if (!["JPG", "PNG"].includes(normalizeExportFormat(raw.format))) {
      addError("format", "Elige JPG o PNG como tipo de archivo.");
    }
    if (!isValidBackgroundValue(raw.background)) {
      addError(raw.backgroundMode === "custom" ? "backgroundCustom" : "background", "Indica un RGB válido entre 0 y 255.");
    }
    if (normalizeExportFormat(raw.format) === "JPG" && raw.background === "transparent") {
      addError("background", "JPG no admite transparencia. Selecciona fondo blanco, gris claro o cambia el tipo a PNG.");
    }
    if (!String(raw.width || "").trim() || !Number.isInteger(width) || width <= 0) {
      addError("width", "La anchura debe ser un número mayor que 0.");
    }
    if (!String(raw.height || "").trim() || !Number.isInteger(height) || height <= 0) {
      addError("height", "La altura debe ser un número mayor que 0.");
    }
    if (invalidFilenameChars.test(String(raw.suffix || ""))) {
      addError("suffix", "El sufijo contiene caracteres no válidos.");
    }
    if (!String(raw.naming || "").trim()) {
      addError("naming", "Define el nombre de archivo.");
    } else if (invalidFilenameChars.test(String(raw.naming || "").replaceAll("{original}", "").replaceAll("{suffix}", "").replaceAll("{folder}", "").replace(/\{index(?::0?\d+d)?\}/g, ""))) {
      addError("naming", "El nombre de archivo contiene caracteres no válidos.");
    } else if (!String(raw.naming || "").includes("{original}")) {
      addWarning("naming", "La plantilla debería incluir {original} para mantener la referencia del archivo.");
    }
    if (raw.destinationMode === "custom") {
      if (!String(raw.destinationValue || "").trim()) {
        addError("destinationValue", "Indica una carpeta de salida personalizada.");
      }
    } else if (raw.destinationMode !== "source") {
      addError("destinationMode", "Elige una ubicación de salida válida.");
    } else {
      const destination = String(raw.destinationValue || "").trim();
      if (!destination) {
        addError("destinationValue", "Indica una subcarpeta de salida.");
      } else if (destination.includes("..") || /[<>:"|?*]/.test(destination)) {
        addError("destinationValue", "La subcarpeta de salida contiene caracteres no válidos.");
      }
    }
    Object.keys(fieldMessages).forEach((field) => {
      fieldMessages[field] = Array.from(new Set(fieldMessages[field]));
    });
    return { errors: Array.from(new Set(errors)), warnings: Array.from(new Set(warnings)), fields, fieldMessages };
  }

  return {
    backgroundCustomText,
    backgroundColorTuple,
    customRgbBackgroundValue,
    dedupeOutputProfileIds,
    exportVariantId,
    exportVariantPayloadFromProfile,
    isValidBackgroundValue,
    normalizeBackgroundValue,
    normalizeExportFormat,
    normalizeOutputProfile,
    normalizeOutputProfileList,
    outputProfileNameForDisplay,
    outputProfileSize,
    outputProfileValidation,
    parseOutputSize,
    parseRgbBackground,
    rgbBackgroundValue,
    uniqueOutputProfileId,
  };
});
