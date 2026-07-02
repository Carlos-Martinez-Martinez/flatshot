import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend" / "app.js"
INDEX_PATH = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend" / "index.html"
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
APP_DOMAIN_SCRIPT_LIMIT = 400
APP_RENDER_SCRIPT_LIMIT = 400


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
        and len(path.read_text(encoding="utf-8").splitlines()) > APP_DOMAIN_SCRIPT_LIMIT
    }

    assert oversized == {}


def test_app_render_scripts_are_focused_controllers():
    oversized = {
        path.name: len(path.read_text(encoding="utf-8").splitlines())
        for path in FRONTEND_DIR.glob("app-render-*.js")
        if len(path.read_text(encoding="utf-8").splitlines()) > APP_RENDER_SCRIPT_LIMIT
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
    loader_source = (FRONTEND_DIR / "app-loader.js").read_text(encoding="utf-8")

    expected_order = [
        "app-globals.js",
        "mock-data.js",
        "app-state-selectors.js",
        "app-preflight-state.js",
        "app-export-readiness-state.js",
        "app-visible-state.js",
        "app-session-snapshot-controller.js",
        "app-timer-controller.js",
        "app-output-profile-storage.js",
        "app-background-state.js",
        "app-output-profile-state.js",
        "app-export-preferences.js",
        "app-bridge-ui-preferences.js",
        "app-output-profile-apply.js",
        "app-settings-preset-workflow.js",
        "app-viewer-state.js",
        "app-local-adjustment-workflow.js",
        "app-gallery-selection-workflow.js",
        "app-batch-workflow.js",
        "app-bridge-api.js",
        "app-bridge-preview-controller.js",
        "app-export-controller.js",
        "app-bridge-connection-controller.js",
        "app-bridge-scan-controller.js",
        "app-review-actions.js",
        "app-inspector-disclosure-controller.js",
        "app-shell.js",
        "app-topbar-bridge.js",
        "app-gallery-controller.js",
        "app-thumbnail-controller.js",
        "app-modal-render-controller.js",
        "app-canvas-guides-controller.js",
        "app-preview-controller.js",
        "app-range-fill-controller.js",
        "app-review-panel-controller.js",
        "app-inspector-cards.js",
        "app-contextual-inspector-controller.js",
        "app-settings-panel-controller.js",
        "app-inspector-layout-controller.js",
        "app-background-preset-controller.js",
        "app-output-profile-summary.js",
        "app-output-profile-draft.js",
        "app-output-profile-manager.js",
        "app-output-profile-modal-renderer.js",
        "app-modal-controller.js",
        "app-export-view.js",
        "app-preset-controller.js",
        "app-footer-status-controller.js",
        "app-render-shell-gallery.js",
        "app-action-dispatcher.js",
        "app-document-events.js",
        "app-form-events.js",
        "app-viewer-events.js",
        "app.js",
        "app-startup.js",
    ]

    positions = [loader_source.index(script) for script in expected_order]

    assert positions == sorted(positions)


def test_app_domain_scripts_are_loaded_through_loader_only():
    html = INDEX_PATH.read_text(encoding="utf-8")
    manual_app_scripts = [
        match
        for match in re.findall(r'<script src="\./(app-[^"?]+\.js)', html)
        if match not in {"app-state.js", "app-loader.js"}
    ]

    assert manual_app_scripts == []


def test_mock_data_does_not_own_helper_alias_globals():
    source = (FRONTEND_DIR / "mock-data.js").read_text(encoding="utf-8")

    forbidden_aliases = [
        "global.storageHelpers =",
        "global.numberHelpers =",
        "global.bridgeUrlHelpers =",
        "global.bridgeClientHelpers =",
        "global.actionHandlerHelpers =",
        "global.interactionBindingHelpers =",
        "global.sessionSnapshotHelpers =",
        "global.backgroundPresetHelpers =",
        "global.appStateHelpers =",
        "global.formatterHelpers =",
        "global.outputProfileHelpers =",
        "global.outputProfileViewHelpers =",
        "global.exportPayloadHelpers =",
        "global.exportStateHelpers =",
        "global.exportSummaryViewHelpers =",
        "global.exportResultViewHelpers =",
        "global.exportPreflightViewHelpers =",
        "global.topStatusViewHelpers =",
        "global.preflightHelpers =",
        "global.batchViewHelpers =",
        "global.scanStateHelpers =",
        "global.exportConfirmViewHelpers =",
        "global.emptyStateViewHelpers =",
        "global.batchDetailViewHelpers =",
        "global.galleryHelpers =",
        "global.previewViewHelpers =",
        "global.previewStateHelpers =",
        "global.settingsViewHelpers =",
        "global.inspectorOutputViewHelpers =",
        "global.inspectorReviewViewHelpers =",
        "global.inspectorContextViewHelpers =",
    ]

    for alias in forbidden_aliases:
        assert alias not in source


def test_frontend_audit_check_mode_passes_current_contract():
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "audit_frontend.py"), "--check"],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr


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
