import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "settings-view.js"
INDEX_PATH = FRONTEND_DIR / "index.html"


def test_settings_view_helper_loads_before_app_script():
    html = INDEX_PATH.read_text(encoding="utf-8")

    helper_index = html.index("settings-view.js")
    app_index = html.index("app.js")

    assert helper_index < app_index


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
assert.equal(helpers.localAdjustmentText(true), "Ajuste local activo");
assert.equal(helpers.localAdjustmentText(false), "Sin ajuste local");
assert.equal(helpers.localSettingOutputText(3), "+3");
assert.equal(helpers.localSettingOutputText(0), "0");
assert.equal(helpers.localSettingOutputText(-2), "-2");

assert.deepEqual(helpers.savePresetButtonState(true), {{
  disabled: false,
  primary: true,
  text: "Guardar cambios",
  title: "Guardar el ajuste activo",
}});
assert.deepEqual(helpers.savePresetButtonState(false), {{
  disabled: true,
  primary: false,
  text: "Guardar cambios",
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
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
