import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "settings-view.js"
INDEX_PATH = FRONTEND_DIR / "index.html"
APP_PATH = FRONTEND_DIR / "app.js"
ADVANCED_CSS_PATH = FRONTEND_DIR / "css" / "06-inspector-export" / "advanced-local-overrides.css"
INSPECTOR_NAV_CSS_PATH = FRONTEND_DIR / "css" / "06-inspector-export" / "inspector-navigation.css"
BUTTONS_CSS_PATH = FRONTEND_DIR / "css" / "03-components" / "buttons.css"


def test_settings_view_helper_loads_before_app_script():
    html = INDEX_PATH.read_text(encoding="utf-8")

    helper_index = html.index("settings-view.js")
    app_index = html.index("app.js")

    assert helper_index < app_index


def test_adjustment_editor_actions_use_explicit_scope_labels():
    html = INDEX_PATH.read_text(encoding="utf-8")

    assert 'data-action="cancel-adjustment-edit"' in html
    assert 'data-action="apply-global-adjustment"' in html
    assert "Aplicar al lote sin guardar" in html
    assert 'data-action="save-preset"' in html
    assert "Guardar ajuste" in html
    assert 'data-action="save-preset-as-new"' in html
    assert "Guardar como nuevo" in html
    assert 'data-action="apply-local-adjustment"' in html
    assert "Aplicar a esta imagen" in html
    assert 'data-action="save-local-adjustment-as-new"' in html
    assert "Guardar nuevo" in html
    assert "Restablecer lote" in html


def test_studio_lighting_panel_is_available_in_advanced_settings():
    html = INDEX_PATH.read_text(encoding="utf-8")

    assert '<option value="studio_2_5d">Estudio 2.5D</option>' in html
    assert 'id="studio-lighting-panel"' in html
    assert 'data-lighting-stage' in html
    assert 'data-lighting-preset="overhead_soft"' in html
    assert 'data-lighting-field="main.type"' in html
    assert 'data-lighting-number-field="main.height"' in html
    assert '<output id="lighting-height-output"' not in html
    assert 'data-engine-row="direction"' in html
    assert 'class="lighting-editor-grid"' in html
    assert 'class="lighting-slider-stack"' in html
    assert 'class="advanced-technical-panel"' in html
    assert "Altura luz" in html
    assert "Tamaño luz" in html
    assert "Potencia" in html
    assert "Escala imagen" in html
    assert html.index('id="lighting-stage"') < html.index('data-lighting-field="main.type"')
    assert html.index('class="lighting-slider-stack"') < html.index('data-lighting-field="main.height"')
    assert html.index('data-setting="shadow_engine"') < html.index('data-setting="spread"')
    assert html.index('id="studio-lighting-panel"') < html.index('data-setting="spread"')


def test_studio_lighting_panel_css_keeps_active_preset_filled_and_unclipped():
    css = ADVANCED_CSS_PATH.read_text(encoding="utf-8")
    buttons_css = BUTTONS_CSS_PATH.read_text(encoding="utf-8")

    assert ".lighting-scene-toolbar button.active::after" not in css
    assert ".lighting-scene-toolbar button.active {" in css
    active_rule = css.split(".lighting-scene-toolbar button.active {", 1)[1].split("}", 1)[0]
    assert "background: var(--color-accent)" in active_rule
    assert "color: #fff" in active_rule
    assert "button:not(.primary):not(.active)" in buttons_css
    assert ".settings-panel details.advanced-block[open] { overflow: visible; }" in css
    assert (
        ".settings-panel details.advanced-block[open] .inspector-disclosure__body "
        "{ max-height: none; overflow: visible; }"
    ) in css
    assert (
        '.settings-panel details.inspector-disclosure[data-inspector-section="advanced"]:not([open]) '
        "{ min-height: 54px; overflow: hidden; }"
    ) in css
    assert (
        '.settings-panel[data-shadow-engine="studio_2_5d"] '
        '[data-engine-row="direction"] { display: none; }'
    ) in css


def test_inspector_navigation_does_not_grid_advanced_disclosures():
    css = INSPECTOR_NAV_CSS_PATH.read_text(encoding="utf-8")

    assert '[data-inspector-section="advanced"]:not(.is-hidden)' not in css


def test_studio_lighting_preset_selection_state_is_explicit():
    js = APP_PATH.read_text(encoding="utf-8")

    assert 'lightingPresetId: ""' in js
    assert "const rememberedPresetId =" in js
    assert 'button.classList.toggle("active", selected);' in js
    assert 'button.classList.toggle("is-modified", selected && !exact);' in js
    assert 'button.setAttribute("aria-pressed", String(selected));' in js
    assert "state.lightingPresetId = presetId;" in js
    assert 'const selectedPresetId = enabled ? exactPresetId || rememberedPresetId || "overhead_soft" : "";' in js
    assert "settingsPanel.dataset.shadowEngine = state.settings.shadow_engine" in js
    assert "visibleAdvancedSettingKeys(state.settings)" in js
    assert 'advancedSettingKeys.filter((key) => key !== "angle")' in js
    assert 'data-lighting-number-field' in js


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_settings_view_renders_preset_and_state_contracts():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

assert.equal(helpers.escapeHtml('<a&b"c>'), '&lt;a&amp;b&quot;c&gt;');

const activeChip = helpers.presetChipHtml({{ name: 'Luz "cenital"', category: "Base" }}, 'Luz "cenital"');
assert.equal(activeChip.includes("preset-chip active"), true);
assert.equal(activeChip.includes('aria-pressed="true"'), true);
assert.equal(activeChip.includes('data-preset="Luz &quot;cenital&quot;"'), true);
assert.equal(activeChip.includes("Activo"), true);

const inactiveChip = helpers.presetChipHtml({{ name: "Sombra <suave>", category: "Producto" }}, "Luz");
assert.equal(inactiveChip.includes("preset-chip active"), false);
assert.equal(inactiveChip.includes('aria-pressed="false"'), true);
assert.equal(inactiveChip.includes("Cambiar a Sombra &lt;suave&gt;"), true);
assert.equal(inactiveChip.includes("Producto"), true);

const list = helpers.presetListHtml([
  {{ name: "Luz", category: "Base" }},
  {{ name: "Sombra", category: "" }},
], "Luz");
assert.equal(list.includes("preset-chip active"), true);
assert.equal(list.includes("Ajuste"), true);
assert.equal(helpers.presetListHtml([], "Luz"), '<span class="preset-empty">No hay ajustes guardados</span>');

assert.equal(helpers.presetDirtyLabel(true), "Sin guardar");
assert.equal(helpers.presetDirtyLabel(false), "Sin cambios");
assert.equal(helpers.presetSourceLabel({{ bridgePresetWarning: "", presetDirty: false }}), "Global");
assert.equal(helpers.presetSourceLabel({{ bridgePresetWarning: "", presetDirty: true }}), "Global · Modificado");
assert.equal(helpers.presetSourceLabel({{ bridgePresetWarning: "Aviso", presetDirty: false }}), "Global · aviso");
assert.equal(helpers.presetSourceLabel({{ bridgePresetWarning: "Aviso", presetDirty: true }}), "Global · Modificado · aviso");
assert.equal(helpers.localAdjustmentText(true), "Personalizado");
assert.equal(helpers.localAdjustmentText(false), "Igual que el lote");
assert.equal(helpers.localSettingOutputText(3), "+3");
assert.equal(helpers.localSettingOutputText(0), "0");
assert.equal(helpers.localSettingOutputText(-2), "-2");

assert.deepEqual(helpers.savePresetButtonState(true), {{
  disabled: false,
  primary: true,
  text: "Guardar ajuste",
  title: "Guardar el ajuste activo",
}});
assert.deepEqual(helpers.savePresetButtonState(false), {{
  disabled: true,
  primary: false,
  text: "Guardar ajuste",
  title: "Sin cambios pendientes",
}});
assert.deepEqual(helpers.deletePresetButtonState(1), {{
  disabled: true,
  title: "Debe quedar al menos un ajuste",
}});
assert.deepEqual(helpers.deletePresetButtonState(2), {{
  disabled: false,
  title: "Eliminar el ajuste activo",
}});
assert.equal(helpers.advancedSummaryTitle(0), "Avanzado");
assert.equal(helpers.advancedSummaryTitle(1), "Avanzado · 1 cambio");
assert.equal(helpers.advancedSummaryTitle(3), "Avanzado · 3 cambios");
assert.equal(helpers.advancedDirtyCount({{
  presetDirty: false,
  keys: ["spread"],
  currentSettings: {{ spread: 3 }},
  presetSettings: {{ spread: 0 }},
}}), 0);
assert.equal(helpers.advancedDirtyCount({{
  presetDirty: true,
  keys: ["spread", "noise", "adaptive_zoom"],
  currentSettings: {{ spread: 3, noise: 2, adaptive_zoom: false }},
  presetSettings: {{ spread: 0, noise: 2, adaptive_zoom: true }},
}}), 2);
assert.equal(helpers.advancedDirtyCount({{
  presetDirty: true,
  keys: ["spread", "missing"],
  currentSettings: {{ spread: 0 }},
  presetSettings: {{ spread: 0 }},
}}), 0);
assert.equal(helpers.advancedDirtyCount({{
  presetDirty: true,
  keys: ["lighting_scene"],
  currentSettings: {{ lighting_scene: {{ main: {{ type: "softbox", x: -0.25 }}, ambient_intensity: 0.25 }} }},
  presetSettings: {{ lighting_scene: {{ main: {{ type: "softbox", x: -0.25 }}, ambient_intensity: 0.25 }} }},
}}), 0);
assert.equal(helpers.advancedDirtyCount({{
  presetDirty: true,
  keys: ["lighting_scene"],
  currentSettings: {{ lighting_scene: {{ main: {{ type: "softbox", x: -0.25 }}, ambient_intensity: 0.25 }} }},
  presetSettings: {{ lighting_scene: {{ main: {{ type: "spot", x: -0.25 }}, ambient_intensity: 0.25 }} }},
}}), 1);

assert.equal(helpers.backgroundLabel("transparent"), "transparente");
assert.equal(helpers.backgroundLabel("white"), "blanco");
assert.equal(helpers.backgroundLabel("rgb230"), "gris claro");
assert.equal(helpers.backgroundLabel("rgb:245,246,247"), "RGB 245, 246, 247");
assert.equal(helpers.backgroundLabel("unknown"), "gris claro");

assert.equal(helpers.presetSummaryLine({{
  format: "PNG",
  size: "1200x1600",
  background: "transparent",
}}), "PNG · 1200x1600 · transparente");
assert.equal(helpers.presetSummaryLine({{
  format: "JPG",
  size: "1800x2400",
  background: "white",
}}), "JPG · 1800x2400 · blanco");

assert.equal(helpers.exportStatusLabel({{ exportStatus: "running", paused: true, ready: true }}), "Pausada");
assert.equal(helpers.exportStatusLabel({{ exportStatus: "running", paused: false, ready: true }}), "Procesando");
assert.equal(helpers.exportStatusLabel({{ exportStatus: "completed", ready: true }}), "Completada");
assert.equal(helpers.exportStatusLabel({{ exportStatus: "partial", ready: true }}), "Con errores");
assert.equal(helpers.exportStatusLabel({{ exportStatus: "failed", ready: true }}), "Fallida");
assert.equal(helpers.exportStatusLabel({{ exportStatus: "idle", ready: true }}), "Lista");
assert.equal(helpers.exportStatusLabel({{ exportStatus: "idle", ready: false }}), "Configura exportación");
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
