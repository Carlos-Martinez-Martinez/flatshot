function contextualInspectorHtml() {
  if (state.batch === "scanning") {
    return inspectorContextViewHelpers.contextualInspectorHtml({
      batch: state.batch,
      scanStatus: state.scanStatus,
      progressHtml: exportPreflightViewHelpers.progressPanelHtml("Preparando lote"),
      preflightHtml: exportPreflightViewHelpers.preflightListHtml(inspectorContextViewHelpers.contextualPreflightRows({
        batch: state.batch,
      })),
    });
  }

  if (state.batch === "none") {
    return inspectorContextViewHelpers.contextualInspectorHtml({
      batch: state.batch,
      preflightHtml: exportPreflightViewHelpers.preflightListHtml(inspectorContextViewHelpers.contextualPreflightRows({
        batch: state.batch,
      })),
      outputSummary: `${state.format} · ${state.size} · ${settingsViewHelpers.backgroundLabel(state.background)}`,
      activePreset: state.activePreset,
    });
  }

  if (state.batch === "empty") {
    return inspectorContextViewHelpers.contextualInspectorHtml({
      batch: state.batch,
      scanStatus: state.scanStatus,
      preflightHtml: exportPreflightViewHelpers.preflightListHtml(inspectorContextViewHelpers.contextualPreflightRows({
        batch: state.batch,
        ignoredSummary: ignoredSummaryText(),
        totalFiles: state.scanDiagnostics.totalFiles,
      })),
    });
  }

  return inspectorContextViewHelpers.contextualInspectorHtml({
    batch: state.batch,
    compactStatus: compactHeaderStatusText(),
  });
}

function presetSourceLabel() {
  return settingsViewHelpers.presetSourceLabel({
    bridgePresetWarning: state.bridgePresetWarning,
    presetDirty: state.presetDirty,
  });
}
