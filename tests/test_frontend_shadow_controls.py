import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
INDEX_PATH = FRONTEND_DIR / "index.html"
SCHEMA_PATH = FRONTEND_DIR / "shadow-control-schema.js"
INTERACTION_PATH = FRONTEND_DIR / "interaction-bindings.js"


def test_shadow_control_schema_is_loaded_before_app_domain_scripts():
    html = INDEX_PATH.read_text(encoding="utf-8")

    schema_index = html.index("shadow-control-schema.js")
    mock_data_index = html.index("mock-data.js")
    app_index = html.index("app.js")

    assert mock_data_index < schema_index < app_index


def test_settings_markup_uses_plain_language_and_one_preset_management_entry():
    html = INDEX_PATH.read_text(encoding="utf-8")

    for label in (
        "Densidad de sombra",
        "Suavidad",
        "Distancia",
        "Margen",
        "Calibración del motor",
        "Difusión",
        "Grano de sombra",
        "Suavidad de contacto",
        "Escala del producto",
        "Dirección de la sombra",
        "Reducir halo del borde",
        "Ajuste automático del producto",
        "Escala respecto al lote",
        "Densidad respecto al lote",
        "Suavidad respecto al lote",
        "Aplicar a esta imagen",
        "Restablecer al lote",
    ):
        assert label in html

    review_source = (FRONTEND_DIR / "inspector-review-view.js").read_text(encoding="utf-8")
    context_source = (FRONTEND_DIR / "inspector-context-view.js").read_text(encoding="utf-8")
    assert review_source.count('data-action="open-preset-editor"') == 0
    assert 'showManageAction: mode === "advanced" && !isPresetManager' in context_source
    assert "Padding" not in html
    assert ">Spread<" not in html


def test_render_settings_applies_engine_control_schema():
    source = (FRONTEND_DIR / "app-settings-panel-controller.js").read_text(encoding="utf-8")

    assert "FlatShotShadowControls" in source
    assert "applyControlVisibility" in source
    layout_source = (FRONTEND_DIR / "app-inspector-layout-controller.js").read_text(encoding="utf-8")
    assert "visibleKeysForEngine" in layout_source


def test_lighting_stage_supports_keyboard_nudging():
    source = (FRONTEND_DIR / "interaction-bindings.js").read_text(encoding="utf-8")

    assert 'addEventListener("keydown"' in source
    assert "ArrowLeft" in source
    assert "ArrowRight" in source
    assert "ArrowUp" in source
    assert "ArrowDown" in source
    assert "nudgeLightingScenePosition" in source


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_value_controls_use_one_commit_event_and_continuous_range_events():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(INTERACTION_PATH))});

function input(type, tagName) {{
  const events = [];
  return {{
    type,
    tagName,
    addEventListener: (eventName) => events.push(eventName),
    events,
  }};
}}

const select = input("select-one", "SELECT");
helpers.bindValueControl(select, () => {{}});
assert.deepEqual(select.events, ["change"]);

const checkbox = input("checkbox", "INPUT");
helpers.bindValueControl(checkbox, () => {{}});
assert.deepEqual(checkbox.events, ["change"]);

const range = input("range", "INPUT");
helpers.bindValueControl(range, () => {{}});
assert.deepEqual(range.events, ["input", "change"]);
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
def test_shadow_control_schema_exposes_engine_capabilities_and_labels():
    script = f"""
const assert = require("node:assert/strict");
const controls = require({json.dumps(str(SCHEMA_PATH))});

const realistic = controls.engineProfile("realistic_v2");
assert.equal(realistic.label, "Realista");
assert.equal(realistic.labelFor("spread"), "Difusión");
assert.equal(realistic.supports("angle"), true);
assert.equal(realistic.supports("fusion"), false);
assert.equal(realistic.supports("lighting_scene"), false);

const studio = controls.engineProfile("studio_2_5d");
assert.equal(studio.labelFor("spread"), "Expansión");
assert.equal(studio.supports("angle"), false);
assert.equal(studio.supports("lighting_scene"), true);

const legacy = controls.engineProfile("legacy");
assert.equal(legacy.labelFor("fusion"), "Protección interior");
assert.equal(legacy.supports("spread"), false);
assert.equal(legacy.supports("fusion"), true);

assert.deepEqual(controls.visibleKeysForEngine("studio_2_5d"), [
      "spread", "noise", "contact_blur", "scale_adjustment", "contraction", "adaptive_zoom", "shadow_engine", "lighting_scene",
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
