import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
INDEX_PATH = FRONTEND_DIR / "index.html"
PREFERENCES_HELPER_PATH = FRONTEND_DIR / "interface-preferences.js"


def preferences_modal_html() -> str:
    html = INDEX_PATH.read_text(encoding="utf-8")
    return html.split('id="preferences-modal"', 1)[1].split('id="app-settings-modal"', 1)[0]


def test_preferences_modal_is_dedicated_to_interface_preferences():
    html = INDEX_PATH.read_text(encoding="utf-8")
    modal = preferences_modal_html()

    assert 'data-action="open-preferences"' in html
    assert 'id="preferences-modal"' in html
    assert 'aria-labelledby="preferences-title"' in modal
    assert 'id="preferences-title">Preferencias' in modal

    for section in ("Apariencia", "Inicio", "Procesado", "Vista", "Datos locales"):
        assert section in modal

    assert 'class="preferences-row"' in modal
    assert 'data-preference-select="theme"' in modal
    assert '<option value="system">Sistema</option>' in modal
    assert 'data-preference-select="brandTone"' in modal
    assert 'data-preference-select="density"' in modal
    assert 'class="preference-toggle" data-action="toggle-reduced-motion"' in modal
    assert 'class="preference-toggle" data-action="toggle-show-recent-folders"' in modal
    assert 'class="preference-toggle" data-action="toggle-onboarding-background"' in modal
    assert 'data-action="open-onboarding-assets-folder"' in modal
    assert 'data-preference-startup-adjustment-summary' in modal
    assert 'data-action="set-startup-adjustment"' in modal
    assert 'data-action="clear-startup-adjustment"' in modal
    assert 'data-preference-select="thumbnailSize"' in modal
    assert 'data-preference-select="fileNameDisplay"' in modal
    assert 'data-action="clear-recent-folders"' in modal
    assert 'data-action="reset-interface-preferences"' in modal
    assert 'class="preference-segmented"' not in modal

    assert 'id="output-profile-list"' not in modal
    assert 'id="profile-format-input"' not in modal
    assert 'data-action="save-output-profile"' not in modal


def test_topbar_preferences_menu_stays_compact_and_opens_full_preferences():
    html = INDEX_PATH.read_text(encoding="utf-8")
    preferences_menu = html.split('<details class="top-preferences-menu" id="top-preferences-menu">', 1)[1].split("</details>", 1)[0]

    assert 'data-action="toggle-theme"' in preferences_menu
    assert 'data-action="set-brand-tone"' in preferences_menu
    assert 'data-action="open-preferences"' in preferences_menu
    assert "Preferencias..." in preferences_menu
    assert 'data-action="set-ui-density"' not in preferences_menu
    assert 'data-action="clear-recent-folders"' not in preferences_menu


def test_preferences_actions_state_and_modal_visibility_are_wired():
    mock = (FRONTEND_DIR / "mock-data.js").read_text(encoding="utf-8")
    app = (FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
    shell = (FRONTEND_DIR / "app-shell.js").read_text(encoding="utf-8")
    actions = (FRONTEND_DIR / "app-action-dispatcher.js").read_text(encoding="utf-8")
    preferences = (FRONTEND_DIR / "app-preferences-controller.js").read_text(encoding="utf-8")
    preset_workflow = (FRONTEND_DIR / "app-settings-preset-workflow.js").read_text(encoding="utf-8")
    scan_controller = (FRONTEND_DIR / "app-bridge-scan-controller.js").read_text(encoding="utf-8")
    renderer = (FRONTEND_DIR / "app-modal-render-controller.js").read_text(encoding="utf-8")
    modals = (FRONTEND_DIR / "app-modal-controller.js").read_text(encoding="utf-8")
    bridge_preferences = (FRONTEND_DIR / "app-bridge-ui-preferences.js").read_text(encoding="utf-8")
    globals_source = (FRONTEND_DIR / "app-globals.js").read_text(encoding="utf-8")

    assert 'interfacePreferences: "flatshot.interfacePreferences"' in mock
    assert "global.interfacePreferenceHelpers = window.FlatShotInterfacePreferences;" in globals_source
    assert "const initialInterfacePreferences = interfacePreferenceHelpers.readInterfacePreferences" in app
    assert "const initialStartupAdjustment = interfacePreferenceHelpers.startupAdjustmentPreference(initialInterfacePreferences);" in app
    assert "settings: normalizeSettings(initialStartupAdjustment?.settings || defaultSettings)" in app
    assert 'presetSource: initialStartupAdjustment ? "Preferencias" : "Global"' in app
    assert 'root.dataset.onboardingBackground = preferences.onboardingBackground === false ? "disabled" : "enabled";' in (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
    assert "themePreference: initialThemePreference" in app
    assert "interfacePreferences: initialInterfacePreferences" in app
    assert "preferencesOpen: false" in app
    assert "interfacePreferenceHelpers.applyInterfacePreferences(document, state.interfacePreferences);" in shell
    assert 'shell.dataset.uiDensity = state.interfacePreferences.density;' in shell
    assert 'shell.dataset.thumbnailSize = state.interfacePreferences.thumbnailSize;' in shell
    assert 'shell.dataset.fileNameDisplay = state.interfacePreferences.fileNameDisplay;' in shell
    assert 'shell.dataset.onboardingBackground = state.interfacePreferences.onboardingBackground ? "enabled" : "disabled";' in shell
    assert "function handlePreferenceSelectChange(" in (FRONTEND_DIR / "app-preferences-controller.js").read_text(encoding="utf-8")
    assert "function setStartupAdjustmentFromCurrent()" in preferences
    assert "function clearStartupAdjustmentPreference()" in preferences
    assert "function applyStartupAdjustmentPreference(" in preset_workflow
    assert "if (applyStartupAdjustmentPreference({ refresh: false, statusText: state.statusText }))" in scan_controller
    assert '[data-preference-select]' in (FRONTEND_DIR / "app-document-events.js").read_text(encoding="utf-8")

    for action in (
        "open-preferences",
        "close-preferences",
        "set-theme-preference",
        "set-ui-density",
        "toggle-reduced-motion",
        "toggle-show-recent-folders",
        "toggle-onboarding-background",
        "open-onboarding-assets-folder",
        "set-startup-adjustment",
        "clear-startup-adjustment",
        "set-thumbnail-size",
        "set-file-name-display",
        "clear-recent-folders",
        "reset-interface-preferences",
    ):
        assert f'"{action}"' in actions

    assert "syncModalVisibility(modal, state.preferencesOpen)" in renderer
    assert 'return $("#preferences-modal");' in modals
    assert "interfacePreferences: state.interfacePreferences" in bridge_preferences
    assert "themePreference: state.themePreference" in bridge_preferences
    assert "brandTone: state.brandTone" in bridge_preferences


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_interface_preferences_helper_normalizes_and_persists_values():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(PREFERENCES_HELPER_PATH))});

function fakeStorage(initial = {{}}, failing = false) {{
  const data = new Map(Object.entries(initial));
  return {{
    getItem(key) {{
      if (failing) throw new Error("blocked");
      return data.has(key) ? data.get(key) : null;
    }},
    setItem(key, value) {{
      if (failing) throw new Error("blocked");
      data.set(key, String(value));
    }},
    removeItem(key) {{
      if (failing) throw new Error("blocked");
      data.delete(key);
    }},
    dump() {{
      return Object.fromEntries(data.entries());
    }},
  }};
}}

function fakeDocument() {{
  return {{ documentElement: {{ dataset: {{}} }} }};
}}

assert.deepEqual(helpers.defaultInterfacePreferences(), {{
  density: "compact",
  reduceMotion: false,
  showRecentFolders: true,
  onboardingBackground: true,
  startupAdjustment: null,
  thumbnailSize: "medium",
  fileNameDisplay: "always",
}});

assert.deepEqual(helpers.normalizeInterfacePreferences({{
  density: "comfortable",
  reduceMotion: true,
  showRecentFolders: false,
  onboardingBackground: false,
  startupAdjustment: {{
    name: "Estudio propio",
    settings: {{ shadow_engine: "studio_2_5d", opacity: 42 }},
    updatedAt: "2026-07-04T10:00:00.000Z",
  }},
  thumbnailSize: "large",
  fileNameDisplay: "hover",
}}), {{
  density: "comfortable",
  reduceMotion: true,
  showRecentFolders: false,
  onboardingBackground: false,
  startupAdjustment: {{
    name: "Estudio propio",
    settings: {{ shadow_engine: "studio_2_5d", opacity: 42 }},
    updatedAt: "2026-07-04T10:00:00.000Z",
  }},
  thumbnailSize: "large",
  fileNameDisplay: "hover",
}});

assert.deepEqual(helpers.normalizeInterfacePreferences({{
  density: "wide",
  reduceMotion: "yes",
  showRecentFolders: "no",
  onboardingBackground: "no",
  startupAdjustment: {{ name: "", settings: null }},
  thumbnailSize: "huge",
  fileNameDisplay: "bad",
}}), helpers.defaultInterfacePreferences());

assert.deepEqual(helpers.startupAdjustmentPreference({{
  startupAdjustment: {{
    name: "Studio",
    settings: {{ shadow_engine: "studio_2_5d", lighting_scene: {{ main: {{ x: 0.2 }} }} }},
  }},
}}), {{
  name: "Studio",
  settings: {{ shadow_engine: "studio_2_5d", lighting_scene: {{ main: {{ x: 0.2 }} }} }},
  updatedAt: "",
}});

assert.equal(helpers.startupAdjustmentPreference({{ startupAdjustment: {{ name: "Bad" }} }}), null);

const storage = fakeStorage();
helpers.writeInterfacePreferences(storage, "prefs", {{ density: "comfortable", thumbnailSize: "small" }});
assert.equal(JSON.parse(storage.dump().prefs).density, "comfortable");
assert.equal(helpers.readInterfacePreferences(storage, "prefs").thumbnailSize, "small");
helpers.writeInterfacePreferences(storage, "startup", {{
  startupAdjustment: {{ name: "Inicio", settings: {{ shadow_engine: "studio_2_5d" }} }},
}});
assert.equal(JSON.parse(storage.dump().startup).startupAdjustment.settings.shadow_engine, "studio_2_5d");
assert.deepEqual(helpers.readInterfacePreferences(fakeStorage({{ prefs: "{{" }}), "prefs"), helpers.defaultInterfacePreferences());
assert.deepEqual(helpers.readInterfacePreferences(fakeStorage({{}}, true), "prefs"), helpers.defaultInterfacePreferences());

const documentRef = fakeDocument();
helpers.applyInterfacePreferences(documentRef, {{ density: "comfortable", reduceMotion: true, onboardingBackground: false, thumbnailSize: "large", fileNameDisplay: "none" }});
assert.deepEqual(documentRef.documentElement.dataset, {{
  uiDensity: "comfortable",
  motion: "reduced",
  onboardingBackground: "disabled",
  thumbnailSize: "large",
  fileNameDisplay: "none",
}});
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
