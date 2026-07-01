function lotInspectorCardHtml() {
  const counts = batchCounts();
  const visible = getVisibleAppState();
  const ignored = counts.ignoredFiles ? `${counts.ignoredFiles} ignorado${counts.ignoredFiles === 1 ? "" : "s"}` : "";
  const customCount = imageAdjustmentOverrideCount();
  const custom = customCount ? `${customCount} personalizada${customCount === 1 ? "" : "s"}` : "";
  const meta = state.batch === "empty"
    ? `${preflightHelpers.readyImagesText(0)}${ignored ? ` · ${ignored}` : ""}`
    : `${preflightHelpers.readyImagesText(counts.exportableImages)}${custom ? ` · ${custom}` : ""}${ignored ? ` · ${ignored}` : ""}`;
  const tone = counts.blockingErrors ? "error" : counts.nonBlockingWarnings ? "warning" : "";
  return inspectorReviewViewHelpers.lotInspectorCardHtml({
    meta,
    title: visible.title,
    tone,
  });
}

function outputInspectorCardHtml() {
  const profiles = state.outputProfiles.length ? state.outputProfiles : [currentOutputProfileData()];
  const activeProfiles = exportOutputProfiles();
  const exportable = exportableImages().length;
  const totalFiles = exportable * activeProfiles.length;
  const dirty = !outputMatchesProfile(activeOutputProfile());
  const rows = profiles.map((profile) => {
    const enabled = Boolean(profile.enabled);
    return {
      id: profile.id,
      name: profile.name,
      enabled,
      active: profile.id === state.activeOutputProfileId,
      canToggle: true,
      summary: outputProfileSummaryLine(profile),
    };
  });
  return inspectorOutputViewHelpers.outputInspectorCardHtml({
    activeCount: activeProfiles.length,
    totalFiles,
    rows,
    dirty,
  });
}

function outputProfileInlineRowHtml(profile) {
  const enabled = Boolean(profile.enabled);
  return inspectorOutputViewHelpers.outputProfileInlineRowHtml({
    id: profile.id,
    name: profile.name,
    enabled,
    active: profile.id === state.activeOutputProfileId,
    canToggle: true,
    summary: outputProfileSummaryLine(profile),
  });
}

function selectedImageInspectorCardHtml() {
  const image = selectedImage();
  const hasLocal = image ? hasImageAdjustmentOverride(image) : false;
  return inspectorReviewViewHelpers.selectedImageInspectorCardHtml({
    hasReadyBatch: hasBatch() && state.batch === "ready",
    image,
    detail: image ? image.detail || imageFileType(image) : "",
    hasLocal,
  });
}

function issuesInspectorCardHtml() {
  const rows = actionableIssueRows();
  if (!rows.length) {
    return "";
  }
  const errors = rows.filter((row) => row.level === "error").length;
  const blocking = preflightCounts().errors > 0;
  const count = blocking
    ? `${preflightCounts().errors} bloqueo${preflightCounts().errors === 1 ? "" : "s"}`
    : errors
      ? `${errors} error${errors === 1 ? "" : "es"}`
    : `${rows.length} aviso${rows.length === 1 ? "" : "s"}`;
  return inspectorReviewViewHelpers.issuesInspectorCardHtml({
    rows,
    blocking,
    countLabel: count,
  });
}

function aspectInspectorCardHtml() {
  const images = activeImages();
  const customizedCount = imageAdjustmentOverrideCount(images);
  return inspectorReviewViewHelpers.aspectInspectorCardHtml({
    hasReadyBatch: hasBatch() && state.batch === "ready",
    activePreset: state.activePreset,
    adjustments: activePresetItems(),
    customizedCount,
  });
}

function actionableIssueRows() {
  const rows = issueRows().filter((row) => !["info", "ignored"].includes(row.level));
  const validationRows = validationIssues()
    .filter((issue) => issue.title !== "Sin lote" && issue.title !== "No hay PNG válidos")
    .map((issue) => ({
      level: issue.level,
      title: issue.title,
      detail: issue.detail,
      path: "",
      actionLabel: "",
    }));
  const seen = new Set();
  return [...validationRows, ...rows].filter((row) => {
    const key = `${row.level}|${row.title}|${row.detail || ""}`;
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
}

function inspectorSubviewHeaderHtml(mode) {
  return inspectorContextViewHelpers.inspectorSubviewHeaderHtml(
    inspectorContextViewHelpers.inspectorSubviewHeaderState({
      activePreset: state.activePreset,
      mode,
      outputEditMode: state.outputEditMode,
      outputLabel: viewerOutputCompactLabel(),
      presetEditorOpen: state.presetEditorOpen,
      presetSourceLabel: presetSourceLabel(),
      warningCount: actionableIssueRows().length,
    })
  );
}
