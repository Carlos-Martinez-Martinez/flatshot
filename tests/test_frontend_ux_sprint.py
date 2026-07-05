import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
INDEX_PATH = FRONTEND_DIR / "index.html"
TOKENS_CSS_PATH = FRONTEND_DIR / "css" / "00-settings" / "tokens.css"
RESPONSIVE_CSS_PATH = FRONTEND_DIR / "css" / "08-states-responsive" / "responsive.css"
APP_LOADER_PATH = FRONTEND_DIR / "app-loader.js"
APP_STARTUP_PATH = FRONTEND_DIR / "app-startup.js"
APP_SHELL_PATH = FRONTEND_DIR / "app-shell.js"
APP_ACTION_DISPATCHER_PATH = FRONTEND_DIR / "app-action-dispatcher.js"
APP_BRIDGE_SCAN_CONTROLLER_PATH = FRONTEND_DIR / "app-bridge-scan-controller.js"
APP_EXPORT_CONTROLLER_PATH = FRONTEND_DIR / "app-export-controller.js"
APP_EXPORT_VIEW_PATH = FRONTEND_DIR / "app-export-view.js"
APP_VIEWER_EVENTS_PATH = FRONTEND_DIR / "app-viewer-events.js"
INTERACTION_BINDINGS_PATH = FRONTEND_DIR / "interaction-bindings.js"
ONBOARDING_BACKGROUND_PATH = FRONTEND_DIR / "onboarding-background.js"
RECENT_FOLDERS_PATH = FRONTEND_DIR / "recent-folders.js"
FOLDER_DROP_PATH = FRONTEND_DIR / "folder-drop.js"
ERROR_BOUNDARY_PATH = FRONTEND_DIR / "error-boundary.js"
ADJUSTMENT_HISTORY_PATH = FRONTEND_DIR / "adjustment-history.js"
MODAL_VISIBILITY_PATH = FRONTEND_DIR / "app-modal-visibility.js"
MODAL_RENDER_CONTROLLER_PATH = FRONTEND_DIR / "app-modal-render-controller.js"
APP_SETTINGS_MODAL_CSS_PATH = FRONTEND_DIR / "css" / "07-modals" / "app-settings.css"


def test_sprint_tokens_fix_focus_contrast_and_system_font():
    tokens = TOKENS_CSS_PATH.read_text(encoding="utf-8")

    assert "--shadow-focus: 0 0 0 3px color-mix(in srgb, var(--color-primary) 18%, transparent);" in tokens
    assert "--focus-ring: var(--shadow-focus);" in tokens
    assert "--color-muted-2: #6b7b8f;" in tokens
    assert "Inter" not in tokens
    assert "--font-family-sans: ui-sans-serif, system-ui" in tokens

    css_sources = "\n".join(path.read_text(encoding="utf-8") for path in FRONTEND_DIR.glob("css/**/*.css"))
    assert not re.search(r"font-weight:\s*(750|760|780)\b", css_sources)


def test_onboarding_uses_local_assets_without_missing_references():
    source = ONBOARDING_BACKGROUND_PATH.read_text(encoding="utf-8")

    assert "ONBOARDING_BACKGROUND_ASSETS = [" in source
    assert "ONBOARDING_BACKGROUND_ASSET_DIR" in source
    assert "assetsFromDirectoryListing" in source
    assert source.count("./assets/onboarding/flatshot-abstract-") == 5
    for index in range(1, 6):
        relative = f"./assets/onboarding/flatshot-abstract-{index:02}.png"
        assert relative in source
        assert (FRONTEND_DIR / relative.removeprefix("./")).is_file()


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_recent_folders_helper_persists_limits_and_formats_entries():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(RECENT_FOLDERS_PATH))});

function fakeStorage(initial = {{}}) {{
  const data = new Map(Object.entries(initial));
  return {{
    getItem(key) {{ return data.has(key) ? data.get(key) : null; }},
    setItem(key, value) {{ data.set(key, String(value)); }},
    removeItem(key) {{ data.delete(key); }},
    dump() {{ return Object.fromEntries(data.entries()); }},
  }};
}}

const storage = fakeStorage({{ recent: "{{" }});
assert.deepEqual(helpers.readRecentFolders(storage, "recent"), []);

helpers.rememberRecentFolder(storage, "recent", {{
  path: "C:/Batch/A",
  imageCount: 3,
  now: "2026-07-03T10:00:00.000Z",
  limit: 3,
}});
helpers.rememberRecentFolder(storage, "recent", {{
  path: "C:/Batch/B",
  imageCount: 0,
  now: "2026-07-03T11:00:00.000Z",
  limit: 3,
}});
helpers.rememberRecentFolder(storage, "recent", {{
  path: "C:/Batch/A",
  imageCount: 4,
  now: "2026-07-03T12:00:00.000Z",
  limit: 3,
}});
helpers.rememberRecentFolder(storage, "recent", {{
  path: "C:/Batch/C",
  imageCount: 1,
  now: "2026-07-03T13:00:00.000Z",
  limit: 3,
}});
helpers.rememberRecentFolder(storage, "recent", {{
  path: "C:/Batch/D",
  imageCount: 2,
  now: "2026-07-03T14:00:00.000Z",
  limit: 3,
}});

assert.deepEqual(helpers.readRecentFolders(storage, "recent").map((entry) => entry.path), [
  "C:/Batch/D",
  "C:/Batch/C",
  "C:/Batch/A",
]);
assert.equal(helpers.readRecentFolders(storage, "recent")[2].imageCount, 4);
assert.equal(helpers.recentFolderMeta(helpers.readRecentFolders(storage, "recent")[0]), "2026-07-03 · 2 imágenes");

helpers.forgetRecentFolder(storage, "recent", "C:/Batch/C");
assert.deepEqual(helpers.readRecentFolders(storage, "recent").map((entry) => entry.path), [
  "C:/Batch/D",
  "C:/Batch/A",
]);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_folder_drop_helper_resolves_supported_paths_and_rejects_files():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(FOLDER_DROP_PATH))});

assert.equal(helpers.fileUrlToLocalPath("file:///C:/Users/Carlos/Batch"), "C:/Users/Carlos/Batch");
assert.equal(helpers.fileUrlToLocalPath("file://server/share/Batch"), "//server/share/Batch");

const folderDrop = helpers.resolveDroppedFolderPath({{
  getData(type) {{
    return type === "text/uri-list" ? "file:///C:/Batch/Entrada" : "";
  }},
  files: [],
  items: [],
}});
assert.deepEqual(folderDrop, {{ status: "ready", path: "C:/Batch/Entrada", message: "" }});

const fileDrop = helpers.resolveDroppedFolderPath({{
  getData() {{ return ""; }},
  files: [{{ name: "foto.png", type: "image/png", path: "C:/Batch/foto.png" }}],
  items: [],
}});
assert.equal(fileDrop.status, "invalid");
assert.equal(fileDrop.path, "");

const unsupportedDrop = helpers.resolveDroppedFolderPath({{
  getData() {{ return ""; }},
  files: [{{ name: "Entrada", type: "", path: "" }}],
  items: [],
}});
assert.equal(unsupportedDrop.status, "unsupported");
assert.equal(unsupportedDrop.path, "");
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout


def test_drag_and_drop_is_wired_without_replacing_manual_scan_flow():
    bindings = INTERACTION_BINDINGS_PATH.read_text(encoding="utf-8")
    controller = (FRONTEND_DIR / "app-folder-drop-controller.js").read_text(encoding="utf-8")
    actions = APP_ACTION_DISPATCHER_PATH.read_text(encoding="utf-8")

    for event_name in ("dragenter", "dragover", "dragleave", "drop"):
      assert f'documentRef.addEventListener("{event_name}", handlers.document' in bindings
    assert "folderDropHelpers.resolveDroppedFolderPath" in controller
    assert "void scanBridgeFolder();" in controller
    assert '"clear-folder-drop-message"' in actions
    assert '"scan-recent-folder"' in actions
    assert '"remove-recent-folder"' in actions


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_error_boundary_helper_exposes_global_fallback_contract():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(ERROR_BOUNDARY_PATH))});

const normalized = helpers.normalizeError(new Error("Boom"));
assert.equal(normalized.message, "Boom");
assert.equal(normalized.detail.includes("Error: Boom"), true);

const html = helpers.errorBoundaryHtml({{
  message: "No se pudo iniciar",
  detail: "stack <trace>",
}});
assert.equal(html.includes("FlatShot no pudo iniciar"), true);
assert.equal(html.includes("No se pudo iniciar"), true);
assert.equal(html.includes("stack &lt;trace&gt;"), true);
assert.equal(html.includes("<details"), true);

const root = {{}};
helpers.installGlobalErrorBoundary(root, {{ document: null }});
assert.equal(typeof root.onerror, "function");
assert.equal(typeof root.onunhandledrejection, "function");
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout


def test_error_boundary_loads_before_app_and_wraps_loader_and_startup():
    html = INDEX_PATH.read_text(encoding="utf-8")
    loader = APP_LOADER_PATH.read_text(encoding="utf-8")
    startup = APP_STARTUP_PATH.read_text(encoding="utf-8")

    assert html.index("error-boundary.js") < html.index("app-loader.js")
    assert "FlatShotErrorBoundary" in loader
    assert "installGlobalErrorBoundary" in loader
    assert "renderGlobalError" in loader
    assert "error, { document" in loader
    assert "try {" in startup
    assert "renderGlobalError" in startup
    assert 'source: "app-startup"' in startup


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_adjustment_history_helper_groups_undo_and_redo_snapshots():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(ADJUSTMENT_HISTORY_PATH))});

const history = helpers.createAdjustmentHistory({{ limit: 2 }});
const start = {{ settings: {{ opacity: 20 }}, imageOverrides: {{}} }};
const middle = {{ settings: {{ opacity: 30 }}, imageOverrides: {{}} }};
const end = {{ settings: {{ opacity: 40 }}, imageOverrides: {{}} }};

helpers.pushAdjustmentHistory(history, start, middle, "opacity");
helpers.pushAdjustmentHistory(history, middle, end, "opacity");
helpers.pushAdjustmentHistory(history, end, {{ settings: {{ opacity: 50 }}, imageOverrides: {{}} }}, "opacity");

assert.equal(history.undo.length, 2);
assert.equal(history.redo.length, 0);
assert.equal(helpers.undoAdjustmentHistory(history, {{ settings: {{ opacity: 50 }} }}).settings.opacity, 40);
assert.equal(history.undo.length, 1);
assert.equal(history.redo.length, 1);
assert.equal(helpers.redoAdjustmentHistory(history, {{ settings: {{ opacity: 40 }} }}).settings.opacity, 50);

helpers.startAdjustmentHistoryChange(history, "slider:opacity", start);
helpers.commitAdjustmentHistoryChange(history, "slider:opacity", end, "opacity drag");
assert.equal(history.undo.at(-1).label, "opacity drag");
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout


def test_adjustment_history_shortcuts_are_wired_before_typing_bailout():
    source = APP_VIEWER_EVENTS_PATH.read_text(encoding="utf-8")

    shortcut_index = source.index('event.key.toLowerCase() === "z"')
    typing_index = source.index("if (isTyping) {")
    assert shortcut_index < typing_index
    assert "undoAdjustmentChange()" in source
    assert "redoAdjustmentChange()" in source


def test_preview_loading_keeps_previous_render_and_uses_overlay_class():
    preview_state = (FRONTEND_DIR / "preview-state.js").read_text(encoding="utf-8")
    preview_view = (FRONTEND_DIR / "preview-view.js").read_text(encoding="utf-8")
    preview_controller = (FRONTEND_DIR / "app-preview-controller.js").read_text(encoding="utf-8")
    bridge_preview = (FRONTEND_DIR / "app-bridge-preview-controller.js").read_text(encoding="utf-8")

    assert "clearData === true" in preview_state
    assert "preview-loading-overlay" in preview_view
    assert "previewLoadingOverlayHtml" in preview_controller
    assert "previewLoadingState({ clearData: false })" in bridge_preview


def test_failed_export_retry_is_wired_to_failed_bridge_paths_only():
    actions = APP_ACTION_DISPATCHER_PATH.read_text(encoding="utf-8")
    controller = APP_EXPORT_CONTROLLER_PATH.read_text(encoding="utf-8")
    view = APP_EXPORT_VIEW_PATH.read_text(encoding="utf-8")
    visible = (FRONTEND_DIR / "app-visible-state.js").read_text(encoding="utf-8")

    assert '"retry-failed-export"' in actions
    assert "retryFailedExport()" in actions
    assert "function retryFailedExport()" in controller
    assert "failedBridgeExportImages(exportableImages(), retryableFailedExportItems())" in controller
    assert "state.exportFailedItems.length ? state.exportFailedItems : state.exportCompletedItems" in controller
    assert "retryFailedOnly" in controller
    assert "images: retryImages" in controller
    assert "canRetryFailed: retryableFailedExportImages().length > 0" in view
    assert "canRetry: isExportReady()" in view
    assert "canRetry: !hasOutputBlocker && isExportReady()" not in view
    assert 'label: outputBlocker && isExportReady() ? "Exportar de nuevo" : outputBlocker ? "Corregir salida" : "Ver error"' in visible
    assert 'action: outputBlocker && isExportReady() ? "start-export" : outputBlocker ? "edit-output" : "review-warnings"' in visible


def test_quick_export_uses_active_output_profile_without_warning_bypass_as_default():
    actions = APP_ACTION_DISPATCHER_PATH.read_text(encoding="utf-8")
    controller = APP_EXPORT_CONTROLLER_PATH.read_text(encoding="utf-8")
    review_actions = (FRONTEND_DIR / "app-review-actions.js").read_text(encoding="utf-8")
    keydown = APP_VIEWER_EVENTS_PATH.read_text(encoding="utf-8")
    visible = (FRONTEND_DIR / "app-visible-state.js").read_text(encoding="utf-8")

    assert '"quick-export": () => quickExport()' in actions
    assert "function quickExport()" in controller
    assert "startExport({ confirmed: true, quick: true })" in controller
    assert 'action === "quick-export"' in review_actions
    assert "quickExport();" in review_actions
    assert 'event.shiftKey && event.key.toLowerCase() === "e"' in keydown
    assert "quickExport();" in keydown
    assert 'primaryAction: { label: exportActionLabel(counts.exportableImages), action: "start-export", enabled: isExportReady() }' in visible
    assert 'primaryAction: { label: exportActionLabel(counts.exportableImages), action: "quick-export", enabled: isExportReady() }' in visible


def test_completed_export_primary_action_browses_multiple_output_groups():
    visible = (FRONTEND_DIR / "app-visible-state.js").read_text(encoding="utf-8")
    actions = APP_ACTION_DISPATCHER_PATH.read_text(encoding="utf-8")

    assert 'label: outputBrowserGroups().length > 1 ? state.outputBrowserOpen ? "Ocultar salidas" : "Ver salidas" : "Abrir destino"' in visible
    assert 'action: outputBrowserGroups().length > 1 ? "browse-outputs" : "open-output"' in visible
    assert '"browse-outputs": () => browseOutputs()' in actions


def test_scan_uses_async_job_endpoint_with_sync_fallback():
    controller = APP_BRIDGE_SCAN_CONTROLLER_PATH.read_text(encoding="utf-8")
    scan_helpers = (FRONTEND_DIR / "scan-result-pages.js").read_text(encoding="utf-8")
    actions = APP_ACTION_DISPATCHER_PATH.read_text(encoding="utf-8")
    visible = (FRONTEND_DIR / "app-visible-state.js").read_text(encoding="utf-8")

    assert '"/folders/scan/jobs"' in controller
    assert "pollBridgeScanJob(" in controller
    assert "scanResultPageHelpers.scanJobStatusUrl(jobId, 0)" in controller
    assert "scanResultPageHelpers.scanJobCancelUrl(jobId)" in controller
    assert "fallbackBridgeScan(" in controller
    assert '"/folders/scan"' in controller
    assert "function cancelBridgeScan()" in controller
    assert "function includeSubfoldersAndScan()" in controller
    assert "recursive: Boolean(state.scanRecursive)" in scan_helpers
    assert '"cancel-scan": () => { void cancelBridgeScan(); }' in actions
    assert '"include-subfolders": () => { void includeSubfoldersAndScan(); }' in actions
    assert 'primaryAction: { label: "Detener", action: "cancel-scan", enabled: Boolean(state.scanJobId) }' in visible


def test_export_history_is_persisted_and_rendered_from_export_flow():
    app = (FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
    controller = APP_EXPORT_CONTROLLER_PATH.read_text(encoding="utf-8")
    view = APP_EXPORT_VIEW_PATH.read_text(encoding="utf-8")

    assert "initialExportHistory" in app
    assert "exportHistory: initialExportHistory" in app
    assert "rememberCurrentExportHistory" in controller
    assert "exportHistoryHelpers.rememberExportHistory" in controller
    assert "STORAGE_KEYS.exportHistory" in controller
    assert 'state.outputBrowserOpen ? "" : exportHistoryHelpers.exportHistoryHtml(state.exportHistory)' in view


def test_responsive_inspector_has_drawer_toggle_under_1120px():
    html = INDEX_PATH.read_text(encoding="utf-8")
    shell = APP_SHELL_PATH.read_text(encoding="utf-8")
    actions = APP_ACTION_DISPATCHER_PATH.read_text(encoding="utf-8")
    responsive = RESPONSIVE_CSS_PATH.read_text(encoding="utf-8")
    topbar = (FRONTEND_DIR / "css" / "02-layout" / "topbar.css").read_text(encoding="utf-8")
    buttons = (FRONTEND_DIR / "css" / "03-components" / "buttons.css").read_text(encoding="utf-8")

    assert 'class="top-inspector-action"' in html
    assert 'data-action="toggle-responsive-inspector"' in html
    assert 'shell.dataset.responsiveInspector = state.responsiveInspectorOpen ? "true" : "false";' in shell
    assert '"toggle-responsive-inspector"' in actions
    assert '.app-shell[data-responsive-inspector="true"] .settings-panel' in responsive
    assert ".top-inspector-action" in responsive
    assert ".top-inspector-action {\n  display: none;" in topbar
    assert ":is(.top-format-action, .top-folder-action, .top-secondary-action, .top-theme-action, .top-inspector-action), .top-preferences-menu > summary" in topbar
    assert ".top-more-menu" not in topbar
    assert "button:where([data-action]" in buttons
    assert ":not(.top-inspector-action)" not in buttons


def test_modals_use_shared_transition_visibility_controller():
    html = INDEX_PATH.read_text(encoding="utf-8")
    helper = MODAL_VISIBILITY_PATH.read_text(encoding="utf-8") if MODAL_VISIBILITY_PATH.exists() else ""
    renderer = MODAL_RENDER_CONTROLLER_PATH.read_text(encoding="utf-8")

    assert MODAL_VISIBILITY_PATH.exists()
    assert html.index("app-modal-visibility.js") < html.index("app-modal-render-controller.js")
    assert "function syncModalVisibility" in helper
    assert "modalVisibilityTimers" in helper
    assert "is-closing" in helper
    assert "prefers-reduced-motion: reduce" in helper
    assert "syncModalVisibility(modal, state.batchDetailOpen)" in renderer
    assert "syncModalVisibility(modal, state.exportConfirmOpen)" in renderer
    assert "syncModalVisibility(modal, state.qaLabOpen)" in renderer


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_modal_visibility_open_animation_settles_before_visible_rerender():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(MODAL_VISIBILITY_PATH))});

function classListFrom(initial) {{
  const classes = new Set(initial);
  return {{
    add(...names) {{ names.forEach((name) => classes.add(name)); }},
    remove(...names) {{ names.forEach((name) => classes.delete(name)); }},
    contains(name) {{ return classes.has(name); }},
    value() {{ return [...classes].sort().join(" "); }},
  }};
}}

const timers = [];
const root = {{
  matchMedia() {{ return {{ matches: false }}; }},
  setTimeout(callback, delay) {{
    timers.push({{ callback, delay }});
    return timers.length;
  }},
  clearTimeout() {{}},
}};
const modal = {{
  attrs: {{}},
  classList: classListFrom(["is-hidden"]),
  setAttribute(name, value) {{ this.attrs[name] = value; }},
}};

helpers.syncModalVisibility(modal, true, {{ root, enterMs: 160 }});
assert.equal(modal.attrs["aria-hidden"], "false");
assert.equal(modal.classList.contains("is-hidden"), false);
assert.equal(modal.classList.contains("is-opening"), true);
assert.equal(timers.length, 1);

timers[0].callback();
assert.equal(modal.classList.contains("is-opening"), false);

helpers.syncModalVisibility(modal, true, {{ root, enterMs: 160 }});
assert.equal(modal.classList.contains("is-opening"), false);
assert.equal(timers.length, 1);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout


def test_modal_css_animates_open_and_close_with_reduced_motion_escape():
    css = APP_SETTINGS_MODAL_CSS_PATH.read_text(encoding="utf-8")

    assert "@keyframes modal-backdrop-in" in css
    assert "@keyframes modal-backdrop-out" in css
    assert "@keyframes modal-dialog-in" in css
    assert "@keyframes modal-dialog-out" in css
    assert ".app-settings-backdrop.is-opening" in css
    assert ".app-settings-backdrop.is-opening > section, .app-settings-backdrop.is-opening .guide-manager-panel" in css
    assert ".app-settings-backdrop:not(.is-hidden) > section" not in css
    assert ".app-settings-backdrop.is-closing" in css
    assert "pointer-events: none;" in css
    assert "@media (prefers-reduced-motion: reduce)" in css
