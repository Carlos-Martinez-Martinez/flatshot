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


def test_dev_review_controls_are_hidden_outside_dev_mode():
    html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
    debug_css = (FRONTEND_DIR / "css" / "03-components" / "dev-debug.css").read_text(encoding="utf-8")

    assert '<button type="button" class="dev-only" data-action="toggle-inspector">Diagnóstico</button>' in html
    assert '<details class="debug-panel dev-only" id="debug-panel">' in html
    assert '<details class="review-panel dev-only">' in html
    assert "html:not(.dev-mode) .dev-only" in debug_css
