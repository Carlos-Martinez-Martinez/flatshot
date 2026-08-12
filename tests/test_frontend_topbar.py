from pathlib import Path


FRONTEND_DIR = Path(__file__).resolve().parents[1] / "apps" / "flatshot-desktop" / "frontend"


def test_topbar_groups_mixed_actions_by_task_type():
    html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")

    assert 'class="top-workbench-context"' in html
    assert 'class="top-folder-action top-context-item"' in html
    assert 'id="top-active-preset"' in html
    assert 'class="top-format-action top-context-item"' in html
    assert 'top-action-cluster top-action-cluster--config" aria-label="Exportación"' in html
    assert 'top-action-cluster top-action-cluster--run" aria-label="Procesamiento"' in html

    run_group = html.split('top-action-cluster top-action-cluster--run"', 1)[1].split("</div>", 1)[0]

    assert 'id="top-primary-action"' in run_group
    visible_header = html.split('<header class="top-bar">', 1)[1].split('<button type="button" class="dev-only"', 1)[0]
    assert 'data-action="clear-batch"' not in visible_header


def test_topbar_preferences_menu_owns_interface_preferences():
    html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")

    assert '<details class="top-preferences-menu" id="top-preferences-menu">' in html
    preferences_menu = html.split('<details class="top-preferences-menu" id="top-preferences-menu">', 1)[1].split("</details>", 1)[0]
    app_settings = html.split('id="app-settings-modal"', 1)[1].split('id="output-profile-list"', 1)[0]

    assert 'data-action="toggle-theme"' in preferences_menu
    assert 'data-action="set-brand-tone"' in preferences_menu
    assert 'data-brand-tone-value="blue"' in preferences_menu
    assert 'data-action="set-brand-tone"' not in app_settings
    assert "Tono de marca" not in app_settings


def test_topbar_exposes_single_batch_entry_action():
    html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")

    top_actions = html.split('<div class="top-actions">', 1)[1].split('data-action="toggle-inspector"', 1)[0]

    header = html.split('<header class="top-bar">', 1)[1].split("</header>", 1)[0]
    assert header.count('data-action="pick-bridge-folder"') == 1
    assert top_actions.count('data-action="pick-bridge-folder"') == 0
    assert 'top-reset-action' not in top_actions
    assert 'Nuevo lote' not in top_actions


def test_product_html_uses_salidas_and_ajustes_language():
    html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")

    assert ">Salidas<" in html
    assert 'aria-label="Fondos guardados"' in html
    assert "Formatos" not in html
    assert "Presets de fondo" not in html


def test_topbar_actions_follow_workflow_order():
    html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")

    batch_index = html.index("top-workbench-context")
    config_index = html.index("top-action-cluster--config")
    run_index = html.index("top-action-cluster--run")

    assert batch_index < config_index < run_index


def test_topbar_primary_button_has_no_drop_shadow():
    topbar_css = (FRONTEND_DIR / "css" / "02-layout" / "topbar.css").read_text(encoding="utf-8")

    primary_rule = topbar_css.split("#top-primary-action.top-export {", 1)[1].split("}", 1)[0]
    primary_hover_rule = topbar_css.split("#top-primary-action.top-export:hover:not(:disabled) {", 1)[1].split("}", 1)[0]

    assert "box-shadow: none;" in primary_rule
    assert "box-shadow: none;" in primary_hover_rule
    assert "transform: none;" in primary_hover_rule


def test_topbar_active_preset_is_status_text_outside_action_group():
    html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
    topbar_css = (FRONTEND_DIR / "css" / "02-layout" / "topbar.css").read_text(encoding="utf-8")
    topbar_js = (FRONTEND_DIR / "app-topbar-bridge.js").read_text(encoding="utf-8")

    actions_block = html.split('<div class="top-actions">', 1)[1].split('<button type="button" class="dev-only"', 1)[0]
    actions_rule = topbar_css.split("\n.top-actions {", 1)[1].split("}", 1)[0]
    preset_rule = topbar_css.split("\n.top-active-preset {", 1)[1].split("}", 1)[0]

    assert html.index('id="top-active-preset"') < html.index('<div class="top-actions">')
    assert 'id="top-active-preset"' not in actions_block
    assert "grid-template-columns: auto auto;" in actions_rule
    assert "minmax(320px, 1fr)" not in actions_rule
    assert "display: inline-grid;" in preset_rule
    assert "border:" not in preset_rule
    assert "background:" not in preset_rule
    assert "border-radius:" not in preset_rule
    assert "max-width:" not in preset_rule
    assert "overflow: hidden;" not in preset_rule
    assert "text-overflow:" not in preset_rule
    assert ".top-active-preset__label" in topbar_css
    assert ".top-active-preset__value" in topbar_css
    assert "activePreset.replaceChildren" in topbar_js


def test_desktop_work_context_keeps_folder_preset_and_output_labels_visible():
    topbar_css = (FRONTEND_DIR / "css" / "02-layout" / "topbar.css").read_text(encoding="utf-8")
    responsive_css = (FRONTEND_DIR / "css" / "08-states-responsive" / "responsive.css").read_text(encoding="utf-8")

    label_rule = topbar_css.split(".top-context-item__label, .top-active-preset__label {", 1)[1].split("}", 1)[0]
    compact = responsive_css.split("@media (max-width: 1119px) {", 1)[1].split("@media (max-width: 759px) {", 1)[0]

    assert "display: none;" not in label_rule
    assert ".top-context-item__label" in compact
    assert "display: none;" in compact.split(".top-context-item__label", 1)[1].split("}", 1)[0]


def test_topbar_export_status_actions_stay_in_header_row():
    topbar_css = (FRONTEND_DIR / "css" / "02-layout" / "topbar.css").read_text(encoding="utf-8")
    viewer_toolbar_css = (FRONTEND_DIR / "css" / "05-viewer" / "viewer-toolbar.css").read_text(encoding="utf-8")

    actions_rule = topbar_css.split("\n.top-actions {", 1)[1].split("}", 1)[0]
    active_preset_status_rule = topbar_css.split('.app-shell[data-status-footer="true"] .top-active-preset {', 1)[1].split("}", 1)[0]
    viewer_toolbar_setup_rule = viewer_toolbar_css.split("{", 1)[0]

    assert ".top-actions" not in viewer_toolbar_setup_rule
    assert ".top-summary" not in viewer_toolbar_setup_rule
    assert ".brand-block" not in viewer_toolbar_setup_rule
    assert "display: grid;" in actions_rule
    assert "grid-row: 1;" in actions_rule
    assert "display: none;" in active_preset_status_rule


def test_primary_toolbar_controls_use_stable_icon_names():
    html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
    buttons_css = (FRONTEND_DIR / "css" / "03-components" / "buttons.css").read_text(encoding="utf-8")

    expected_icons = {"sliders"}

    for icon in expected_icons:
        assert f'data-icon="{icon}"' in html

    assert 'class="top-folder-action top-context-item"' in html

    assert "button[data-icon]::before" not in buttons_css
    assert ".button-icon svg" in buttons_css
    assert 'class="button-icon' in html


def test_theme_toggle_icon_visibility_beats_generic_button_icon_rule():
    topbar_css = (FRONTEND_DIR / "css" / "02-layout" / "topbar.css").read_text(encoding="utf-8")

    assert ".top-theme-action .theme-icon--light" in topbar_css
    assert ':root[data-theme="dark"] .top-theme-action .theme-icon--dark' in topbar_css
    assert ':root[data-theme="dark"] .top-theme-action .theme-icon--light' in topbar_css


def test_dev_review_controls_are_hidden_outside_dev_mode():
    html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
    debug_css = (FRONTEND_DIR / "css" / "03-components" / "dev-debug.css").read_text(encoding="utf-8")

    assert '<button type="button" class="dev-only" data-action="toggle-inspector">Diagnóstico</button>' in html
    assert '<details class="debug-panel dev-only" id="debug-panel">' in html
    assert 'data-action="open-qa-lab"' not in html
    assert '<details class="review-panel dev-only">' not in html
    assert "html:not(.dev-mode) :is(" in debug_css
    assert ".dev-only" in debug_css
    assert "html.dev-mode body .top-actions > :is(button.dev-only, details.debug-panel)" in debug_css


def test_primary_view_chrome_uses_progressive_disclosure():
    html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")

    assert 'aria-label="Cambiar carpeta"' in html
    assert 'aria-label="Configurar salida"' in html
    assert '<details class="viewer-options-menu" id="viewer-options-menu">' in html
    menu = html.split('<details class="viewer-options-menu" id="viewer-options-menu">', 1)[1].split("</details>", 1)[0]
    assert '<summary aria-label="Opciones de vista">Vista</summary>' in menu
    assert 'class="segmented compact viewer-background-switch background-switch"' in menu
    assert 'class="viewer-control-group viewer-guides"' in menu
