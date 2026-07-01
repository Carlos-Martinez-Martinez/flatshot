from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend" / "app.js"


def test_app_js_does_not_reintroduce_extracted_wrapper_helpers():
    source = APP_PATH.read_text(encoding="utf-8")

    obsolete_wrappers = [
        "function topStatusSummaryHtml(",
        "function batchDetailRowHtml(",
        "function compactImageDetail(",
        "function assetStatusLabel(",
        "function assetStatusIcon(",
        "function batchFormatHtml(",
        "function previewOutputContextHtml(",
        "function activePresets(",
        "function outputPresetLabel(",
        "function reviewErrors(",
        "function sameOutputProfile(",
        "function pluralizeCount(",
        "function sidebarLotSummaryText(",
        "function warningCountLabel(",
        "function imageCountLabel(",
        "function omittedSummaryText(",
        "function batchBackgroundLabel(",
        "function outputCountLabel(",
        "function detectedFormatLabel(",
        "function bridgeScanMessage(",
        "function folderItemHtml(",
        "function progressPanelHtml(",
        "function outputTemporaryNoticeHtml(",
        "function issueItemHtml(",
        "function preflightListHtml(",
        "function imageSearchText(",
        "function filterDisplayName(",
        "function thumbnailHtml(",
        "function galleryFilterVisible(",
        "function previewModeLabel(",
    ]

    for wrapper in obsolete_wrappers:
        assert wrapper not in source


def test_app_js_uses_shared_storage_and_number_helpers():
    source = APP_PATH.read_text(encoding="utf-8")

    removed_helpers = [
        "function readPersistentValue(",
        "function readPersistentJson(",
        "function writePersistentValue(",
        "function writePersistentJson(",
        "function clampNumber(",
    ]

    for helper in removed_helpers:
        assert helper not in source

    assert "storageHelpers.readValue(" in source
    assert "storageHelpers.readJson(" in source
    assert "storageHelpers.writeValue(" in source
    assert "storageHelpers.writeJson(" in source
    assert "numberHelpers.clampNumber(" in source


def test_app_js_does_not_keep_output_profile_passthrough_wrappers():
    source = APP_PATH.read_text(encoding="utf-8")

    passthrough_wrappers = [
        "function normalizeOutputProfile(",
        "function outputProfileNameForDisplay(",
        "function normalizeExportFormat(",
        "function normalizeOutputProfileList(",
        "function dedupeOutputProfileIds(",
        "function uniqueOutputProfileId(",
        "function outputProfileSize(",
        "function parseOutputSize(",
        "function normalizeBackgroundValue(",
        "function parseRgbBackground(",
        "function backgroundCustomText(",
        "function customRgbBackgroundValue(",
    ]

    for wrapper in passthrough_wrappers:
        assert wrapper not in source

    assert "outputProfileHelpers.normalizeOutputProfile(" in source
    assert "outputProfileHelpers.parseOutputSize(" in source
    assert "outputProfileHelpers.normalizeBackgroundValue(" in source


def test_app_js_does_not_keep_pure_helper_passthrough_wrappers():
    source = APP_PATH.read_text(encoding="utf-8")

    pure_passthrough_wrappers = [
        "function countText(",
        "function readyImagesText(",
        "function filterStatusText(",
        "function dedupeExportRisks(",
        "function issueMentionsExistingOutput(",
        "function isAutoViewerMode(",
        "function viewerModeClass(",
        "function clampViewerZoom(",
        "function normalizeBridgeIssue(",
        "function backgroundColorTuple(",
        "function omissionReasonLabel(",
        "function basename(",
        "function imageFileStem(",
        "function formatBytes(",
        "function pathToFileUrl(",
        "function debugUrlLabel(",
        "function emptyStateHtml(",
        "function profileDestinationLabel(",
        "function profileDestinationPreviewLabel(",
        "function outputProfileValidationHtml(",
        "function outputProfileValidation(",
        "function backgroundLabel(",
    ]

    for wrapper in pure_passthrough_wrappers:
        assert wrapper not in source


def test_app_js_does_not_keep_extracted_background_or_snapshot_helpers():
    source = APP_PATH.read_text(encoding="utf-8")

    extracted_helpers = [
        "function buildSessionSnapshot(",
        "function safeObject(",
        "function backgroundSelectMode(",
        "function normalizePreviewBackgroundValue(",
        "function backgroundCssColor(",
        "function backgroundVisualMode(",
        "function previewCustomRgbChannels(",
        "function previewBackgroundLabel(",
        "function normalizeBackgroundPreset(",
        "function normalizeBackgroundPresetList(",
        "function backgroundPresetValue(",
        "function backgroundPresetLabel(",
    ]

    for helper in extracted_helpers:
        assert helper not in source

    assert "sessionSnapshotHelpers.buildSessionSnapshot(" in source
    assert "backgroundPresetHelpers.normalizePreviewBackgroundValue(" in source


def test_app_js_uses_explicit_helper_references_after_wrapper_removal():
    source = APP_PATH.read_text(encoding="utf-8")

    forbidden_bare_calls = [
        r"(?<!exportStateHelpers\.)\bnormalizeBridgeIssue\(",
        r"(?<!preflightHelpers\.)\bissueMentionsExistingOutput\(",
        r"(?<!preflightHelpers\.)\bissueMentionsExistingOutput\b",
        r"(?<!preflightHelpers\.)\bdedupeExportRisks\(",
        r"(?<!outputProfileHelpers\.)\boutputProfileValidation\(",
    ]

    for pattern in forbidden_bare_calls:
        assert not re.search(pattern, source)


def test_app_js_delegates_derived_state_algorithms():
    source = APP_PATH.read_text(encoding="utf-8")

    assert "appStateHelpers.exportItemState(" in source
    assert "appStateHelpers.validationIssues(" in source
    assert "appStateHelpers.lowResolutionImageCount(" in source
    assert "appStateHelpers.uiState(" in source

    extracted_snippets = [
        "const sourceStem = sourceName.replace(",
        "outputProfileHelpers.outputProfileValidation(outputProfileRawFromProfile(profile)).errors.forEach",
        "const detail = String(image?.detail || \"\");",
    ]
    for snippet in extracted_snippets:
        assert snippet not in source


def test_app_js_tracks_restored_session_snapshot_as_explicit_state():
    source = APP_PATH.read_text(encoding="utf-8")

    assert "let restoredSessionSnapshot = false;" in source
    assert "const restoredSessionSnapshot = restoreSessionSnapshot();" not in source


def test_app_js_delegates_browser_interaction_wiring():
    source = APP_PATH.read_text(encoding="utf-8")

    forbidden_wiring = [
        r"\bdocument\.addEventListener\(",
        r"\bwindow\.addEventListener\(",
        r"\$\([^)]*\)\.addEventListener\(",
    ]

    for pattern in forbidden_wiring:
        assert not re.search(pattern, source)

    assert "interactionBindingHelpers.wireFlatShotInteractions(" in source
