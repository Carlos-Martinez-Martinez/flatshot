from pathlib import Path


FRONTEND_DIR = Path(__file__).resolve().parents[1] / "apps" / "flatshot-desktop" / "frontend"


def test_topbar_groups_mixed_actions_by_task_type():
    html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")

    assert 'top-action-cluster top-action-cluster--batch" aria-label="Importación"' in html
    assert 'top-action-cluster top-action-cluster--config" aria-label="Exportación"' in html
    assert 'top-action-cluster top-action-cluster--run" aria-label="Procesamiento"' in html

    run_group = html.split('top-action-cluster top-action-cluster--run"', 1)[1].split("</div>", 1)[0]
    batch_group = html.split('top-action-cluster top-action-cluster--batch"', 1)[1].split("</div>", 1)[0]
    config_group = html.split('top-action-cluster top-action-cluster--config"', 1)[1].split("</div>", 1)[0]

    assert 'id="top-primary-action"' in run_group
    assert 'data-action="pick-bridge-folder"' in batch_group
    assert 'data-action="clear-batch"' not in batch_group
    assert 'data-action="open-app-settings"' in config_group


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

    assert top_actions.count('data-action="pick-bridge-folder"') == 1
    assert 'top-reset-action' not in top_actions
    assert 'Nuevo lote' not in top_actions


def test_topbar_actions_follow_workflow_order():
    html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")

    batch_index = html.index("top-action-cluster--batch")
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
    assert "grid-template-columns: auto auto auto;" in actions_rule
    assert "minmax(320px, 1fr)" not in actions_rule
    assert "grid-column: 2;" in preset_rule
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


def test_primary_toolbar_controls_use_stable_icon_names():
    html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
    buttons_css = (FRONTEND_DIR / "css" / "03-components" / "buttons.css").read_text(encoding="utf-8")

    expected_icons = {
        "sliders",
        "folder-open",
    }

    for icon in expected_icons:
        assert f'data-icon="{icon}"' in html

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
    assert 'data-action="open-qa-lab"' in html
    assert '<details class="review-panel dev-only">' not in html
    assert "html:not(.dev-mode) .dev-only" in debug_css
