from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
INDEX_PATH = FRONTEND_DIR / "index.html"
APP_JS_LIMIT = 250
APP_DOMAIN_LIMIT = 400
APP_RENDER_LIMIT = 400
EXPECTED_APP_SCRIPT_ORDER = [
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
    "app-folder-drop-controller.js",
    "app-review-actions.js",
    "app-inspector-disclosure-controller.js",
    "app-shell.js",
    "app-topbar-bridge.js",
    "app-gallery-controller.js",
    "app-thumbnail-controller.js",
    "app-modal-visibility.js",
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
APP_LOADER_SCRIPT = "app-loader.js"
MANUAL_APP_SCRIPT_ALLOWLIST = {"app-state.js", APP_LOADER_SCRIPT}
FORBIDDEN_MOCK_ALIASES = [
    "storageHelpers",
    "numberHelpers",
    "bridgeUrlHelpers",
    "bridgeClientHelpers",
    "actionHandlerHelpers",
    "interactionBindingHelpers",
    "sessionSnapshotHelpers",
    "backgroundPresetHelpers",
    "appStateHelpers",
    "formatterHelpers",
    "outputProfileHelpers",
    "outputProfileViewHelpers",
    "exportPayloadHelpers",
    "exportStateHelpers",
    "exportSummaryViewHelpers",
    "exportResultViewHelpers",
    "exportPreflightViewHelpers",
    "topStatusViewHelpers",
    "preflightHelpers",
    "batchViewHelpers",
    "scanStateHelpers",
    "exportConfirmViewHelpers",
    "emptyStateViewHelpers",
    "batchDetailViewHelpers",
    "galleryHelpers",
    "previewViewHelpers",
    "previewStateHelpers",
    "settingsViewHelpers",
    "inspectorOutputViewHelpers",
    "inspectorReviewViewHelpers",
    "inspectorContextViewHelpers",
]
EVENT_WIRING_ALLOWLIST = {
    "interaction-bindings.js",
    "bridge-client.js",
}


def script_names(index_path: Path = INDEX_PATH) -> list[str]:
    html = index_path.read_text(encoding="utf-8")
    return [
        Path(match.group("src").split("?", 1)[0]).name
        for match in re.finditer(r'<script\s+src="\./(?P<src>[^"]+)"', html)
    ]


def app_loader_script_order(path: Path = FRONTEND_DIR / APP_LOADER_SCRIPT) -> list[str]:
    source = path.read_text(encoding="utf-8")
    match = re.search(r"APP_SCRIPT_ORDER\s*=\s*\[(?P<body>.*?)\];", source, re.DOTALL)
    if not match:
        return []
    return re.findall(r'"([^"]+\.js)"', match.group("body"))


def line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def file_has_payload(path: Path) -> bool:
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("//") and not stripped.startswith("/*") and not stripped.startswith("*"):
            return True
    return False


def audit() -> dict[str, object]:
    scripts = script_names()
    loader_scripts = app_loader_script_order()
    app_order_ok = loader_scripts == EXPECTED_APP_SCRIPT_ORDER
    missing_app_scripts = [name for name in EXPECTED_APP_SCRIPT_ORDER if name not in loader_scripts]
    manual_app_scripts = [
        name for name in scripts if name.startswith("app-") and name not in MANUAL_APP_SCRIPT_ALLOWLIST
    ]

    referenced_scripts = [*scripts, *loader_scripts]
    missing_files = [name for name in referenced_scripts if not (FRONTEND_DIR / name).exists()]
    empty_linked_scripts = [
        name for name in referenced_scripts if (FRONTEND_DIR / name).exists() and not file_has_payload(FRONTEND_DIR / name)
    ]

    oversized_app_scripts: dict[str, dict[str, int]] = {}
    for path in sorted(FRONTEND_DIR.glob("app-*.js")):
        if path.name == "app-state.js":
            continue
        limit = APP_RENDER_LIMIT if path.name.startswith("app-render-") else APP_DOMAIN_LIMIT
        if path.name == "app.js":
            limit = APP_JS_LIMIT
        lines = line_count(path)
        if lines > limit:
            oversized_app_scripts[path.name] = {"lines": lines, "limit": limit}

    mock_source = (FRONTEND_DIR / "mock-data.js").read_text(encoding="utf-8")
    mock_aliases = [
        alias for alias in FORBIDDEN_MOCK_ALIASES if f"global.{alias} =" in mock_source
    ]

    event_wiring_violations = []
    for path in sorted(FRONTEND_DIR.glob("*.js")):
        if path.name in EVENT_WIRING_ALLOWLIST:
            continue
        source = path.read_text(encoding="utf-8")
        if re.search(r"\.addEventListener\(", source):
            event_wiring_violations.append(path.name)

    return {
        "index_script_count": len(scripts),
        "app_script_count": len(loader_scripts),
        "app_order_ok": app_order_ok,
        "missing_app_scripts": missing_app_scripts,
        "manual_app_scripts": manual_app_scripts,
        "missing_files": missing_files,
        "empty_linked_scripts": empty_linked_scripts,
        "oversized_app_scripts": oversized_app_scripts,
        "mock_aliases": mock_aliases,
        "event_wiring_violations": event_wiring_violations,
    }


def failures(report: dict[str, object]) -> list[str]:
    messages: list[str] = []
    if not report["app_order_ok"]:
        messages.append("App-domain scripts are missing or out of order.")
    if report["missing_files"]:
        messages.append("Linked frontend scripts are missing.")
    if report["manual_app_scripts"]:
        messages.append("App-domain scripts must be loaded through app-loader.js.")
    if report["empty_linked_scripts"]:
        messages.append("Linked frontend scripts must not be empty.")
    if report["oversized_app_scripts"]:
        messages.append("App-domain scripts exceed size limits.")
    if report["mock_aliases"]:
        messages.append("mock-data.js must not own helper alias globals.")
    if report["event_wiring_violations"]:
        messages.append("DOM event wiring must stay in interaction-bindings.js.")
    return messages


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    report = audit()
    print(json.dumps(report, indent=2, sort_keys=True))

    if args.check:
        problems = failures(report)
        if problems:
            for problem in problems:
                print(f"ERROR: {problem}")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
