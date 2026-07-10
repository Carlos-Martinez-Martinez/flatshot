from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"


def test_local_adjustment_cancel_restores_the_pre_edit_override():
    workflow = (FRONTEND_DIR / "app-local-adjustment-workflow.js").read_text(encoding="utf-8")
    html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
    dispatcher = (FRONTEND_DIR / "app-action-dispatcher.js").read_text(encoding="utf-8")

    assert "localAdjustmentDraft" in workflow
    assert "function beginLocalAdjustmentDraft" in workflow
    assert "function cancelLocalAdjustment" in workflow
    assert "state.imageOverrides[draft.imageKey] = restored" in workflow
    assert "delete state.imageOverrides[draft.imageKey]" in workflow
    assert 'data-action="cancel-local-adjustment"' in html
    assert '"cancel-local-adjustment": () => cancelLocalAdjustment()' in dispatcher


def test_local_adjustment_draft_is_discarded_when_image_selection_changes():
    app = (FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
    selection = (FRONTEND_DIR / "app-gallery-selection-workflow.js").read_text(encoding="utf-8")

    assert "localAdjustmentDraft: null" in app
    assert "state.localAdjustmentDraft = null;" in selection


def test_output_profile_dirty_state_is_computed_after_form_sync():
    renderer = (FRONTEND_DIR / "app-output-profile-modal-renderer.js").read_text(encoding="utf-8")

    sync_index = renderer.index("setOutputProfileFormValues(draft);")
    dirty_index = renderer.index("const draftDirty = outputProfileHasUnsavedChanges();")
    assert sync_index < dirty_index


def test_output_settings_close_button_names_the_salidas_modal():
    html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")

    assert 'id="app-settings-title">Salidas</h2>' in html
    assert 'data-action="close-app-settings" aria-label="Cerrar Salidas"' in html


def test_result_actions_have_a_narrow_viewport_layout():
    css = (FRONTEND_DIR / "css" / "03-components" / "review-status-panels.css").read_text(encoding="utf-8")

    assert ".result-actions > button" in css
    assert "min-width: 0" in css
    assert "flex: 1 1 100%" in css
