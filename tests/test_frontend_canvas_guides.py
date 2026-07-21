import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "canvas-guides.js"
VIEW_HELPER_PATH = FRONTEND_DIR / "canvas-guides-view.js"
INDEX_PATH = FRONTEND_DIR / "index.html"
APP_GLOBALS_PATH = FRONTEND_DIR / "app-globals.js"


def test_canvas_guides_helper_loads_before_mock_data_and_app():
    html = INDEX_PATH.read_text(encoding="utf-8")

    helper_index = html.index("canvas-guides.js")
    view_helper_index = html.index("canvas-guides-view.js")
    mock_data_index = html.index("mock-data.js")
    app_index = html.index("app.js")

    assert helper_index < view_helper_index < mock_data_index < app_index


def test_app_globals_exposes_canvas_guide_helpers():
    source = APP_GLOBALS_PATH.read_text(encoding="utf-8")

    assert "global.guideHelpers = window.FlatShotCanvasGuides;" in source
    assert "global.guideViewHelpers = window.FlatShotCanvasGuideView;" in source


def test_canvas_guides_storage_keys_are_defined():
    source = (FRONTEND_DIR / "mock-data.js").read_text(encoding="utf-8")

    assert 'guideSystems: "flatshot.guideSystems"' in source
    assert 'activeGuideSystems: "flatshot.activeGuideSystemIds"' in source
    assert 'guideSystemOrder: "flatshot.guideSystemOrderIds"' in source
    assert 'hiddenGuideSystems: "flatshot.hiddenGuideSystemIds"' in source
    assert 'guidesVisible: "flatshot.guidesVisible"' in source


def test_guide_preferences_are_ui_preferences_not_export_preferences():
    source = (FRONTEND_DIR / "app-bridge-ui-preferences.js").read_text(encoding="utf-8")

    payload_start = source.index("function uiPreferencesPayload()")
    payload_end = source.index("function cacheUiPreferences", payload_start)
    payload_block = source[payload_start:payload_end]
    export_start = payload_block.index("exportPreferences:")
    export_block = payload_block[export_start:]

    assert "guideSystems:" in payload_block
    assert "activeGuideSystemIds:" in payload_block
    assert "guideSystemOrderIds:" in payload_block
    assert "hiddenGuideSystemIds:" in payload_block
    assert "guidesVisible:" in payload_block
    assert "guideSystems:" not in export_block
    assert "activeGuideSystemIds:" not in export_block
    assert "guideSystemOrderIds:" not in export_block
    assert "hiddenGuideSystemIds:" not in export_block
    assert "guidesVisible:" not in export_block


def test_canvas_guides_toolbar_overlay_and_controller_are_wired():
    html = INDEX_PATH.read_text(encoding="utf-8")

    assert 'class="viewer-control-group viewer-guides"' in html
    assert 'id="guide-overlay"' in html
    assert 'data-action="toggle-guides"' in html
    assert 'data-guide-system-list' in html
    assert 'class="viewer-guides-menu"' in html
    assert 'class="viewer-guides-menu-trigger"' in html
    assert 'class="visually-hidden">Sistemas de guías</span>' in html
    guide_block = html[html.index('class="viewer-control-group viewer-guides"'):html.index('class="zoom-controls"', html.index('class="viewer-control-group viewer-guides"'))]
    assert guide_block.index('class="button-icon"') < guide_block.index('id="guides-active-count"')
    assert html.index("app-canvas-guides-controller.js") < html.index("app-preview-controller.js")


def test_canvas_guide_actions_are_registered_and_popover_closes_transiently():
    dispatcher = (FRONTEND_DIR / "app-action-dispatcher.js").read_text(encoding="utf-8")
    document_events = (FRONTEND_DIR / "app-document-events.js").read_text(encoding="utf-8")

    assert '"toggle-guides": () => toggleGuidesVisible()' in dispatcher
    assert '"open-guide-manager": () => openGuideManager()' in dispatcher
    assert 'details.viewer-guides-menu[open]' in document_events
    assert "handleGuideSystemToggle" in document_events
    assert "handleGuideSystemPickerToggle" in document_events


def test_canvas_guide_controller_persists_after_mutations():
    source = (FRONTEND_DIR / "app-canvas-guides-controller.js").read_text(encoding="utf-8")

    assert "function persistGuidePreferences()" in source
    assert "storageHelpers.writeJson(window.localStorage, STORAGE_KEYS.activeGuideSystems" in source
    assert "storageHelpers.writeJson(window.localStorage, STORAGE_KEYS.guideSystemOrder" in source
    assert "storageHelpers.writeJson(window.localStorage, STORAGE_KEYS.hiddenGuideSystems" in source
    assert "scheduleBridgeUiPreferencesSave();" in source


def test_canvas_guide_manager_supports_system_and_rule_actions():
    controller = (FRONTEND_DIR / "app-canvas-guides-controller.js").read_text(encoding="utf-8")
    dispatcher = (FRONTEND_DIR / "app-action-dispatcher.js").read_text(encoding="utf-8")
    document_events = (FRONTEND_DIR / "app-document-events.js").read_text(encoding="utf-8")
    render_source = (FRONTEND_DIR / "app-render-shell-gallery.js").read_text(encoding="utf-8")
    keydown_source = (FRONTEND_DIR / "app-viewer-events.js").read_text(encoding="utf-8")

    for function_name in [
        "renderGuideManager",
        "newGuideSystem",
        "selectGuideSystem",
        "editGuideSystem",
        "duplicateGuideSystem",
        "deleteGuideSystem",
        "setGuideSystemInPicker",
        "moveGuideSystem",
        "saveGuideDraft",
        "guideDraftFromSystem",
        "editableGuideRulesFromSystem",
        "addGuideLineRule",
        "removeGuideRule",
    ]:
        assert f"function {function_name}" in controller

    for action in [
        "new-guide-system",
        "select-guide-system",
        "edit-guide-system",
        "duplicate-guide-system",
        "delete-guide-system",
        "move-guide-system-up",
        "move-guide-system-down",
        "save-guide-draft",
        "add-guide-line",
        "remove-guide-rule",
    ]:
        assert f'"{action}"' in dispatcher

    assert "updateGuideDraftFromFields" in document_events
    assert '!event.target?.dataset?.guideNewField' in document_events
    assert 'event.target?.matches?.("[data-guide-system-picker-toggle]")' in document_events
    assert "renderGuideManager();" in render_source
    assert "closeGuideManager();" in keydown_source


def test_canvas_guide_manager_uses_existing_modal_shell():
    controller = (FRONTEND_DIR / "app-canvas-guides-controller.js").read_text(encoding="utf-8")
    view = VIEW_HELPER_PATH.read_text(encoding="utf-8")
    source = f"{controller}\n{view}"

    assert 'modal.className = "app-settings-backdrop guide-manager-modal is-hidden"' in controller
    assert "syncModalVisibility(modal, true)" in controller
    assert "guideViewHelpers.guideManagerHtml" in controller
    assert 'class="app-settings-dialog guide-manager-panel"' in source
    assert 'class="app-settings-header"' in source
    assert 'class="guide-system-list-heading"' in source
    assert 'class="guide-system-list-scroll"' in source
    assert 'class="guide-empty-state"' in source
    assert 'class="guide-system-controls"' in source
    assert 'class="guide-system-picker ${inSelector ? "is-selected" : ""}"' in source
    assert 'class="guide-icon-button' in source
    assert 'data-guide-system-picker-toggle="' in source
    assert 'aria-label="${inSelector ? "Ocultar del selector" : "Mostrar en selector"}' in source
    assert 'action: "move-guide-system-up"' in source
    assert 'action: "move-guide-system-down"' in source
    assert 'data-action="select-guide-system"' in source
    assert 'aria-pressed="${selected ? "true" : "false"}"' in source
    assert 'class="guide-system-row ${selected ? "is-selected" : ""} ${inSelector ? "" : "is-inactive"}"' in source
    assert 'class="guide-system-actions"' in source
    assert '<svg viewBox="0 0 24 24"' in source
    assert 'class="guide-readonly-panel"' in source
    assert 'class="guide-readonly-swatch"' in source
    assert 'class="guide-rule-row guide-line-row guide-line-row--readonly"' in source
    assert "modal-backdrop" not in source
    assert "modal-panel" not in source
    assert "modal-header" not in source


def test_canvas_guide_manager_uses_bounded_editor_layout():
    controller = (FRONTEND_DIR / "app-canvas-guides-controller.js").read_text(encoding="utf-8")
    view = VIEW_HELPER_PATH.read_text(encoding="utf-8")
    source = f"{controller}\n{view}"
    toolbar_css = (FRONTEND_DIR / "css" / "05-viewer" / "viewer-toolbar.css").read_text(encoding="utf-8")

    assert 'id="guide-draft-form" class="guide-draft-form"' in source
    assert 'class="guide-add-row"' in source
    assert 'data-guide-new-field="position"' in source
    assert 'data-guide-new-field="mirror"' in source
    assert "const reflected = 1 - position" in controller
    assert "Math.abs(reflected - position) > 0.0001" in controller
    assert 'class="guide-list-heading"' in source
    assert 'class="guide-rule-title"' in source
    assert 'class="guide-rule-fields"' in source
    assert 'guide-line-row' in source
    editor_block = view[view.index("function guideDraftFormHtml"):view.index("function guidePercentNumber")]
    assert "Par simétrico" not in editor_block
    assert "División" not in editor_block

    assert ".guide-manager-panel" in toolbar_css and "height: min(" in toolbar_css
    assert "var(--modal-guide-manager-width)" in toolbar_css
    assert "var(--modal-max-height)" in toolbar_css
    assert "var(--modal-padding-wide)" in toolbar_css
    assert "grid-template-columns: 340px minmax(0, 1fr)" in toolbar_css
    assert ".guide-system-row .viewer-guide-system-swatch" in toolbar_css
    assert "grid-template-columns: 24px minmax(0, 1fr)" in toolbar_css
    assert ".guide-system-controls" in toolbar_css
    assert ".guide-system-picker" in toolbar_css
    assert ".guide-icon-button" in toolbar_css
    assert "width: var(--control-size-compact)" in toolbar_css
    assert ".guide-system-row.is-inactive" in toolbar_css
    assert ".guide-system-row.is-selected" in toolbar_css
    assert ".guide-draft-form" in toolbar_css and "grid-template-rows: auto auto auto auto minmax(0, 1fr) auto" in toolbar_css
    assert ".guide-readonly-panel" in toolbar_css and "grid-template-rows: auto auto auto minmax(0, 1fr) auto" in toolbar_css
    assert ".guide-readonly-swatch" in toolbar_css
    assert ".guide-draft-panel" in toolbar_css and "overflow: hidden" in toolbar_css
    assert ".guide-rule-list" in toolbar_css and "overflow-y: auto" in toolbar_css
    assert "grid-template-columns: minmax(240px, 1fr) 54px 92px 78px" in toolbar_css
    assert ".guide-color-control" in toolbar_css
    assert ".guide-color-control input" not in toolbar_css
    assert ".guide-add-row" in toolbar_css
    assert "grid-template-columns: minmax(190px, 1fr) 180px 150px 96px 160px" in toolbar_css
    assert "padding: var(--space-3) var(--space-5)" in toolbar_css
    assert ".guide-rule-fields" in toolbar_css
    assert "display: contents" in toolbar_css
    assert ".guide-line-row" in toolbar_css
    assert "grid-template-columns: minmax(160px, 1fr) minmax(180px, 220px) minmax(150px, 190px) 132px" in toolbar_css
    assert ".guide-line-row--readonly" in toolbar_css
    assert "padding-inline: var(--space-4)" in toolbar_css
    assert ".guide-rule-row--division" not in toolbar_css


def test_canvas_guide_manager_uses_visual_rgb_selector_for_color():
    view = VIEW_HELPER_PATH.read_text(encoding="utf-8")
    document_events = (FRONTEND_DIR / "app-document-events.js").read_text(encoding="utf-8")
    forms_css = (FRONTEND_DIR / "css" / "03-components" / "forms.css").read_text(encoding="utf-8")

    draft_block = view[view.index("function guideDraftFormHtml"):view.index("function guideRuleEditorHtml")]

    assert 'type="hidden" data-guide-draft-field="color"' in draft_block
    assert 'class="rgb-visual-control rgb-visual-control--swatch-only guide-color-control"' in draft_block
    assert 'data-rgb-visual-control="guide-color"' in draft_block
    assert 'data-rgb-visual-format="hex"' in draft_block
    assert 'type="button" class="rgb-visual-control__swatch"' in draft_block
    assert 'data-rgb-visual-picker-trigger' in draft_block
    assert 'type="color" class="rgb-visual-control__picker"' in draft_block
    assert 'data-rgb-visual-picker' in draft_block
    assert 'data-rgb-visual-channel=' not in draft_block
    assert 'data-rgb-visual-swatch' in draft_block
    assert "syncRgbVisualControlToTarget" in document_events
    assert ".rgb-visual-control" in forms_css


def test_canvas_guide_manager_converts_presets_to_editable_exact_guides():
    controller = (FRONTEND_DIR / "app-canvas-guides-controller.js").read_text(encoding="utf-8")

    copy_block = controller[controller.index("function editableGuideRulesFromSystem"):controller.index("function newGuideSystem")]

    assert "guideHelpers.expandRule(rule)" in copy_block
    assert 'type: "line"' in copy_block
    assert "position: line.position" in copy_block
    assert "system: false" in copy_block


def test_canvas_guides_css_lives_in_viewer_modules():
    toolbar_css = (FRONTEND_DIR / "css" / "05-viewer" / "viewer-toolbar.css").read_text(encoding="utf-8")
    canvas_css = (FRONTEND_DIR / "css" / "05-viewer" / "canvas.css").read_text(encoding="utf-8")

    assert ".viewer-guides" in toolbar_css
    assert "#guides-toggle { width:" in toolbar_css
    assert ".viewer-guides-menu-trigger" in toolbar_css
    assert ".viewer-guides-popover" in toolbar_css
    assert ".guide-manager-panel" in toolbar_css
    assert ".guide-system-list-scroll" in toolbar_css
    assert ".guide-system-actions" in toolbar_css
    assert ".guide-empty-state" in toolbar_css
    assert ".viewer-guide-system-option, .viewer-guide-system-option *" in toolbar_css
    assert ".guide-overlay" in canvas_css
    assert ".guide-line--x" in canvas_css
    assert ".guide-line--y" in canvas_css


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_canvas_guide_helpers_normalize_and_expand_rules():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

const systems = helpers.normalizeGuideSystemList([
  {{
    id: "center",
    name: "Centro roto",
    color: "#ffffff",
    rules: [{{ type: "line", axis: "x", position: 0.2 }}],
  }},
  {{
    id: "market",
    name: "Marketplace",
    color: "#ABCDEF",
    opacity: 2,
    thickness: 9,
    rules: [
      {{ id: "top", type: "mirror-pair", axis: "y", inset: 0.12 }},
      {{ id: "thirds", type: "division", axis: "x", mode: "equal", parts: 3 }},
      {{ id: "custom", type: "division", axis: "y", mode: "custom", positions: [0.78, 0.22, 0.22] }},
      {{ id: "bad", type: "mirror-pair", axis: "x", inset: 0.6 }},
    ],
  }},
]);

assert.equal(systems[0].id, "center");
assert.equal(systems[0].system, true);
assert.equal(systems[0].name, "Centro");
assert.equal(systems.at(-1).id, "market");
assert.equal(systems.at(-1).color, "#abcdef");
assert.equal(systems.at(-1).opacity, 1);
assert.equal(systems.at(-1).thickness, 4);
assert.equal(systems.at(-1).rules.length, 3);

const activeIds = helpers.normalizeActiveGuideSystemIds(["market", "missing", "market"], systems);
assert.deepEqual(activeIds, ["market"]);

const orderIds = helpers.normalizeGuideSystemOrderIds(["market", "center"], systems);
assert.deepEqual(orderIds.slice(0, 2), ["market", "center"]);
assert.deepEqual(helpers.orderGuideSystems(systems, orderIds).map((system) => system.id).slice(0, 2), ["market", "center"]);
assert.deepEqual(helpers.normalizeHiddenGuideSystemIds(["center", "missing", "center"], systems), ["center"]);
assert.deepEqual(helpers.pickerGuideSystems(systems, ["market", "center"], ["center"]).map((system) => system.id)[0], "market");

const lines = helpers.guideLinesForSystems(systems, activeIds).map((line) => `${{line.axis}}:${{line.position}}`);
assert.deepEqual(lines, ["y:0.12", "y:0.88", "x:0.3333", "x:0.6667", "y:0.22", "y:0.78"]);
assert.equal(helpers.formatPercent(0.33333), "33.33%");
assert.equal(helpers.parsePercent("12.5%"), 0.125);

const storage = helpers.guideSystemsForStorage(systems);
assert.deepEqual(storage.map((system) => system.id), ["market"]);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
