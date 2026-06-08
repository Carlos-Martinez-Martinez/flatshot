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
    ]

    for wrapper in obsolete_wrappers:
        assert wrapper not in source
