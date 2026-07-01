from pathlib import Path


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
