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
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
