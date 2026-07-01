from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend" / "app.js"
INDEX_PATH = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend" / "index.html"
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"


def app_domain_source():
    parts = [APP_PATH.read_text(encoding="utf-8")]
    parts.extend(
        path.read_text(encoding="utf-8")
        for path in sorted(FRONTEND_DIR.glob("app-*.js"))
        if path.name != "app-state.js"
    )
    return "\n".join(parts)


def test_app_js_is_bootstrap_sized_after_full_split():
    lines = APP_PATH.read_text(encoding="utf-8").splitlines()

    assert len(lines) <= 250


def test_app_domain_scripts_stay_bounded():
    oversized = {
        path.name: len(path.read_text(encoding="utf-8").splitlines())
        for path in FRONTEND_DIR.glob("app-*.js")
        if path.name != "app-state.js"
        and len(path.read_text(encoding="utf-8").splitlines()) > 1800
    }

    assert oversized == {}


def test_app_js_no_longer_contains_domain_sections():
    source = APP_PATH.read_text(encoding="utf-8")

    moved_domain_functions = [
        "function setScenario(",
        "function startExport(",
        "function checkBridge(",
        "function render(",
        "function renderPreview(",
        "function renderOutputProfileModalState(",
        "const actionDispatcher =",
        "function handleDocumentClick(",
        "function startFlatShotApp(",
    ]

    for function_signature in moved_domain_functions:
        assert function_signature not in source


def test_app_domain_scripts_are_loaded_in_order():
    html = INDEX_PATH.read_text(encoding="utf-8")

    expected_order = [
        "mock-data.js",
        "app-core.js",
        "app-workflow.js",
        "app-bridge-export.js",
        "app-render-shell-gallery.js",
        "app-render-preview-inspector.js",
        "app-render-export-settings.js",
        "app-actions.js",
        "app.js",
        "app-startup.js",
    ]

    positions = [html.index(script) for script in expected_order]

    assert positions == sorted(positions)


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
    app_source = APP_PATH.read_text(encoding="utf-8")
    source = app_domain_source()

    removed_helpers = [
        "function readPersistentValue(",
        "function readPersistentJson(",
        "function writePersistentValue(",
        "function writePersistentJson(",
        "function clampNumber(",
    ]

    for helper in removed_helpers:
        assert helper not in source

    assert "storageHelpers.readValue(" in app_source
    assert "storageHelpers.readJson(" in app_source
    assert "storageHelpers.writeValue(" in source
    assert "storageHelpers.writeJson(" in source
    assert "numberHelpers.clampNumber(" in source


def test_app_js_does_not_keep_output_profile_passthrough_wrappers():
    source = app_domain_source()

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
    source = app_domain_source()

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
    source = app_domain_source()

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
    source = app_domain_source()

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
    source = app_domain_source()

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
    source = app_domain_source()

    assert "let restoredSessionSnapshot = false;" in source
    assert "const restoredSessionSnapshot = restoreSessionSnapshot();" not in source


def test_app_js_delegates_browser_interaction_wiring():
    source = app_domain_source()

    forbidden_wiring = [
        r"\bdocument\.addEventListener\(",
        r"\bwindow\.addEventListener\(",
        r"\$\([^)]*\)\.addEventListener\(",
    ]

    for pattern in forbidden_wiring:
        assert not re.search(pattern, source)

    assert "interactionBindingHelpers.wireFlatShotInteractions(" in source
