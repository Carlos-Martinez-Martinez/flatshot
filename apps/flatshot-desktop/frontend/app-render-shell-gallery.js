function render() {
  renderShell();
  renderTop();
  renderDevelopmentStatus();
  renderBridge();
  renderBatch();
  renderPreview();
  renderSettings();
  renderExport();
  renderBatchDetail();
  renderExportConfirm();
  renderQaLab();
  renderAppSettings();
  renderInspector();
  renderFooter();
  renderAccessibilityHints();
  syncRangeFillStyles();
  syncOpenInspectorDisclosureHeights();
  keepActiveThumbnailVisible();
  if (sessionSnapshotPersistenceEnabled) {
    writeSessionSnapshot();
  }
}

function renderAdjustmentResponse() {
  renderPreview();
  renderSettings();
  renderBatch();
  renderExport();
  renderInspector();
  renderTop();
  syncRangeFillStyles();
  syncOpenInspectorDisclosureHeights();
  keepActiveThumbnailVisible();
}
