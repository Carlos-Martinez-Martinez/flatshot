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
    const background = ["rgb230", "white", "transparent"].includes(source.background)
      ? source.background
      : "rgb230";
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
      destinationValue: String(source.destinationValue || (destinationMode === "custom" ? "" : "_SALIDA_PRO")),
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
      output_folder_name: profile.destinationMode === "source" ? profile.destinationValue || "_SALIDA_PRO" : null,
      custom_output_path: profile.destinationMode === "custom" ? profile.destinationValue : null,
      output_width: size.width,
      output_height: size.height,
    };
  }

  function outputProfileValidation(raw) {
    const errors = [];
    const warnings = [];
    const fields = {};
    const width = Number.parseInt(raw.width, 10);
    const height = Number.parseInt(raw.height, 10);
    const invalidFilenameChars = /[<>:"/\\|?*]/;
    const addError = (field, message) => {
      errors.push(message);
      if (field) {
        fields[field] = "error";
      }
    };
    const addWarning = (field, message) => {
      warnings.push(message);
      if (field && fields[field] !== "error") {
        fields[field] = "warning";
      }
    };

    if (!String(raw.name || "").trim()) {
      addError("name", "Pon un nombre al formato.");
    }
    if (!["JPG", "PNG"].includes(normalizeExportFormat(raw.format))) {
      addError("format", "Elige JPG o PNG como tipo de archivo.");
    }
    if (!["rgb230", "white", "transparent"].includes(raw.background)) {
      addError("background", "Elige un fondo de salida válido.");
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
      addWarning("naming", "Incluye {original} para mantener la referencia del archivo.");
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
    return { errors: Array.from(new Set(errors)), warnings: Array.from(new Set(warnings)), fields };
  }

  return {
    backgroundColorTuple,
    dedupeOutputProfileIds,
    exportVariantId,
    exportVariantPayloadFromProfile,
    normalizeExportFormat,
    normalizeOutputProfile,
    normalizeOutputProfileList,
    outputProfileNameForDisplay,
    outputProfileSize,
    outputProfileValidation,
    parseOutputSize,
    uniqueOutputProfileId,
  };
});
