function imageOverrideKey(image = selectedImage()) {
  return image?.path || image?.id || "";
}

function clampLocalOverrideValue(key, value) {
  const [minimum, maximum] = localOverrideLimits[key] || [-100, 100];
  const parsed = Number(value);
  const numeric = Number.isFinite(parsed) ? Math.round(parsed) : 0;
  return Math.max(minimum, Math.min(maximum, numeric));
}

function normalizeLocalOverride(override = {}) {
  const normalized = {};
  localOverrideKeys.forEach((key) => {
    const value = clampLocalOverrideValue(key, override?.[key]);
    if (value) {
      normalized[key] = value;
    }
  });
  return normalized;
}

function currentImageOverride(image = selectedImage()) {
  const key = imageOverrideKey(image);
  return key ? normalizeLocalOverride(state.imageOverrides[key]) : {};
}

function hasCurrentImageOverride(image = selectedImage()) {
  return Object.keys(currentImageOverride(image)).length > 0;
}

function hasImageAdjustmentOverride(image) {
  return hasCurrentImageOverride(image) || image?.status === "adjusted";
}

function imageAdjustmentOverrideCount(images = activeImages()) {
  return images.filter(hasImageAdjustmentOverride).length;
}

function resetAllImageOverrides() {
  const before = adjustmentSnapshot();
  state.imageOverrides = {};
  state.realImages = state.realImages.map((image) =>
    image.status === "adjusted" ? { ...image, status: "ready" } : image
  );
  state.localOverride = false;
  state.statusText = "Ajuste del lote aplicado a todas las imágenes";
  refreshPreviewAfterSettingChange();
  recordAdjustmentChange(before, "Aplicar ajuste global");
}

function setCurrentImageOverrideValue(key, value) {
  const image = selectedImage();
  const overrideKey = imageOverrideKey(image);
  if (!image || !overrideKey || !localOverrideKeys.includes(key)) {
    return;
  }
  const next = {
    ...currentImageOverride(image),
    [key]: clampLocalOverrideValue(key, value),
  };
  const normalized = normalizeLocalOverride(next);
  if (Object.keys(normalized).length) {
    state.imageOverrides[overrideKey] = normalized;
  } else {
    delete state.imageOverrides[overrideKey];
  }
  state.localOverride = Object.keys(normalized).length > 0;
  state.statusText = state.localOverride ? "Ajuste personalizado" : "Ajuste de imagen restablecido";
  refreshPreviewAfterSettingChange();
}

function resetCurrentImageOverride() {
  const key = imageOverrideKey();
  if (!key) {
    return;
  }
  const before = adjustmentSnapshot();
  delete state.imageOverrides[key];
  state.localOverride = false;
  state.statusText = "Ajuste de imagen restablecido";
  refreshPreviewAfterSettingChange();
  recordAdjustmentChange(before, "Restablecer imagen");
}

function settingsWithLocalOverride(settings = state.settings, override = currentImageOverride()) {
  const normalizedSettings = normalizeSettings(settings);
  const local = normalizeLocalOverride(override);
  const next = { ...normalizedSettings };
  if (Object.prototype.hasOwnProperty.call(local, "size_delta")) {
    next.scale_adjustment = Math.max(-30, Math.min(30, Number(next.scale_adjustment || 0) + local.size_delta));
  }
  if (Object.prototype.hasOwnProperty.call(local, "shadow_delta")) {
    next.opacity = Math.max(0, Math.min(100, Number(next.opacity || 0) + local.shadow_delta));
  }
  if (Object.prototype.hasOwnProperty.call(local, "blur_delta")) {
    next.blur = Math.max(0, Math.min(100, Number(next.blur || 0) + local.blur_delta));
  }
  return normalizeSettings(next);
}

function applyLocalAdjustmentOnly() {
  const image = selectedImage();
  if (!image) {
    return;
  }
  state.presetEditorOpen = false;
  state.localOverride = hasImageAdjustmentOverride(image);
  state.statusText = state.localOverride ? "Ajuste aplicado sólo a esta imagen" : "La imagen usa el ajuste del lote";
  render();
}
