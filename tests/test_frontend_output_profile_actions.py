from pathlib import Path
import subprocess


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
ACTION_DISPATCHER_PATH = FRONTEND_DIR / "app-action-dispatcher.js"
MANAGER_PATH = FRONTEND_DIR / "app-output-profile-manager.js"
MODAL_CONTROLLER_PATH = FRONTEND_DIR / "app-modal-controller.js"
INDEX_PATH = FRONTEND_DIR / "index.html"


def test_export_card_edit_action_opens_profile_editor():
    dispatcher = ACTION_DISPATCHER_PATH.read_text(encoding="utf-8")
    manager = MANAGER_PATH.read_text(encoding="utf-8")

    assert '"edit-output-profile": (target) =>' in dispatcher
    assert "editOutputProfileFromInspector(profileId)" in dispatcher

    assert "function editOutputProfileFromInspector(profileId)" in manager
    assert "state.appSettingsOpen = true;" in manager
    assert "state.outputProfileEditorId = profile.id;" in manager
    assert "queueModalFocus(\"#app-settings-modal\"" in manager


def test_output_settings_close_requests_confirmation_only_for_dirty_drafts():
    script = f"""
const fs = require("fs");
const vm = require("vm");
global.state = {{ appSettingsOpen: true, outputProfileCloseConfirmOpen: false, outputProfileDraft: {{}}, outputProfileNotice: "", outputDeleteConfirmId: "draft" }};
global.HTMLElement = class HTMLElement {{}};
global.document = {{ activeElement: {{}}, body: {{}}, contains: () => false }};
let dirty = true;
let renders = 0;
global.outputProfileHasUnsavedChanges = () => dirty;
global.showOutputProfileUnsavedNotice = () => {{ renders += 1; }};
global.releaseModalFocusBeforeHide = () => {{}};
global.render = () => {{ renders += 1; }};
vm.runInThisContext(fs.readFileSync({str(MODAL_CONTROLLER_PATH)!r}, "utf8"));

closeAppSettings();
if (!state.appSettingsOpen || !state.outputProfileCloseConfirmOpen || renders !== 1) process.exit(1);

dirty = false;
closeAppSettings();
if (state.appSettingsOpen || state.outputProfileCloseConfirmOpen || state.outputProfileDraft !== null) process.exit(2);
"""
    result = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=20)

    assert result.returncode == 0, result.stderr or result.stdout


def test_output_settings_exposes_safe_discard_confirmation_actions():
    dispatcher = ACTION_DISPATCHER_PATH.read_text(encoding="utf-8")
    html = INDEX_PATH.read_text(encoding="utf-8")

    assert '"keep-editing-output-profile": () => keepEditingOutputProfile()' in dispatcher
    assert '"discard-output-profile-and-close": () => discardOutputProfileAndClose()' in dispatcher
    assert 'id="output-close-confirm"' in html
    assert 'data-action="keep-editing-output-profile"' in html
    assert 'data-action="discard-output-profile-and-close"' in html
