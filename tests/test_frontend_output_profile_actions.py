from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
ACTION_DISPATCHER_PATH = FRONTEND_DIR / "app-action-dispatcher.js"
MANAGER_PATH = FRONTEND_DIR / "app-output-profile-manager.js"


def test_export_card_edit_action_opens_profile_editor():
    dispatcher = ACTION_DISPATCHER_PATH.read_text(encoding="utf-8")
    manager = MANAGER_PATH.read_text(encoding="utf-8")

    assert '"edit-output-profile": (target) =>' in dispatcher
    assert "editOutputProfileFromInspector(profileId)" in dispatcher

    assert "function editOutputProfileFromInspector(profileId)" in manager
    assert "state.appSettingsOpen = true;" in manager
    assert "state.outputProfileEditorId = profile.id;" in manager
    assert "queueModalFocus(\"#app-settings-modal\"" in manager
