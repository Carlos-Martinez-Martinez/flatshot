import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
INDEX_PATH = FRONTEND_DIR / "index.html"
SCHEMA_PATH = FRONTEND_DIR / "shadow-control-schema.js"
ADVANCED_CSS_PATH = FRONTEND_DIR / "css" / "06-inspector-export" / "advanced-local-overrides.css"
RESPONSIVE_CSS_PATH = FRONTEND_DIR / "css" / "08-states-responsive" / "responsive.css"
DOCUMENT_EVENTS_PATH = FRONTEND_DIR / "app-document-events.js"
SETTINGS_CONTROLLER_PATH = FRONTEND_DIR / "app-settings-panel-controller.js"


def test_editor_uses_plain_labels_and_keeps_secondary_actions_collapsed():
    html = INDEX_PATH.read_text(encoding="utf-8")

    for label in (
        "Densidad de sombra",
        "Suavidad",
        "Distancia",
        "Escala del producto",
        "Margen",
        "Realista",
        "Estudio con luz",
        "Clásico · compatibilidad",
        "Aplicar al lote",
        "Aplicar a esta imagen",
        "Restablecer al lote",
        "Más acciones",
    ):
        assert label in html

    assert "Aplicar al lote sin guardar" not in html
    assert "Guardar excepción" not in html
    assert 'class="secondary-actions"' in html


def test_advanced_engine_controls_are_split_by_intent_and_explain_modes():
    html = INDEX_PATH.read_text(encoding="utf-8")

    assert 'data-advanced-group="lighting"' in html
    assert 'data-advanced-group="quality"' in html
    assert 'id="shadow-engine-description"' in html
    assert 'id="engine-state-help"' in html
    assert 'aria-describedby="shadow-engine-description engine-state-help"' in html


def test_numeric_inputs_expose_a_pending_commit_state():
    html = INDEX_PATH.read_text(encoding="utf-8")
    source = DOCUMENT_EVENTS_PATH.read_text(encoding="utf-8")
    controller = SETTINGS_CONTROLLER_PATH.read_text(encoding="utf-8")

    assert 'id="numeric-pending-status"' in html
    assert "dataset.pending" in controller
    assert "setNumericControlPending" in source
    assert "clearNumericControlPending" in source


def test_preset_management_has_one_entry_point():
    review_source = (FRONTEND_DIR / "inspector-review-view.js").read_text(encoding="utf-8")
    context_source = (FRONTEND_DIR / "inspector-context-view.js").read_text(encoding="utf-8")

    assert review_source.count('data-action="open-preset-editor"') == 0
    assert "showManageAction: mode === \"advanced\" && !isPresetManager" in context_source


def test_dynamic_control_names_share_the_visible_label_for_accessibility():
    html = INDEX_PATH.read_text(encoding="utf-8")

    for key in ("opacity", "distance", "spread"):
        assert f'id="{key}-label"' in html
        assert f'aria-labelledby="{key}-label"' in html


def test_editing_inspector_gets_a_wider_responsive_column_without_changing_the_shell():
    css = RESPONSIVE_CSS_PATH.read_text(encoding="utf-8")

    assert '.app-shell[data-inspector-editing="true"] .workspace' in css
    assert "minmax(380px, 440px)" in css


def test_edit_mode_rows_do_not_allow_labels_to_overlap_controls():
    css = ADVANCED_CSS_PATH.read_text(encoding="utf-8")

    assert ".settings-panel.is-editing-preset .control-row > span" in css
    assert "overflow: hidden" in css
    assert "text-overflow: ellipsis" in css


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_engine_labels_keep_internal_ids_and_use_plain_display_names():
    script = f"""
const assert = require("node:assert/strict");
const controls = require({json.dumps(str(SCHEMA_PATH))});

assert.equal(controls.engineProfile("realistic_v2").label, "Realista");
assert.equal(controls.engineProfile("studio_2_5d").label, "Estudio con luz");
assert.equal(controls.engineProfile("legacy").label, "Clásico · compatibilidad");
assert.equal(controls.engineProfile("studio_2_5d").labelFor("shadow_engine"), "Motor de sombra");
assert.equal(controls.engineProfile("studio_2_5d").labelFor("spread"), "Expansión");
assert.equal(controls.engineProfile("realistic_v2").description, "Sombra natural con contacto suave");
assert.equal(controls.engineProfile("studio_2_5d").description, "Control manual de luz y escena");
assert.equal(controls.engineProfile("legacy").description, "Motor anterior para compatibilidad");
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
