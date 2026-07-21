import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "export-summary-view.js"
INDEX_PATH = FRONTEND_DIR / "index.html"


def test_export_summary_view_helper_loads_before_app_script():
    html = INDEX_PATH.read_text(encoding="utf-8")

    helper_index = html.index("export-summary-view.js")
    app_index = html.index("app.js")

    assert helper_index < app_index


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_export_summary_view_renders_edit_and_preset_contracts():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

assert.equal(helpers.escapeHtml('<a&b"c>'), '&lt;a&amp;b&quot;c&gt;');

const editActions = helpers.exportEditActionsHtml();
assert.equal(editActions.includes('data-action="cancel-output-edit"'), true);
assert.equal(editActions.includes('data-action="apply-output-edit"'), true);
assert.equal(editActions.includes('data-action="save-output-current-profile"'), true);
assert.equal(editActions.includes("Aplicar al lote sin guardar"), true);
assert.equal(editActions.includes("Guardar salida"), true);

const presetActions = helpers.exportPresetActionsHtml();
assert.equal(presetActions.includes('data-action="open-app-settings"'), true);
assert.equal(presetActions.includes('data-action="new-output-profile"'), true);
assert.equal(presetActions.includes("Gestionar salidas"), true);

const selectOptions = helpers.outputProfileSelectOptionsHtml(
  [
    {{ id: "main", name: "Principal" }},
    {{ id: 'custom-"id"', name: "Salida <especial>" }},
  ],
  {{ includeCustom: true }}
);
assert.equal(selectOptions.includes('value="main"'), true);
assert.equal(selectOptions.includes("Principal"), true);
assert.equal(selectOptions.includes('value="custom-&quot;id&quot;"'), true);
assert.equal(selectOptions.includes("Salida &lt;especial&gt;"), true);
assert.equal(selectOptions.includes('value="__custom"'), true);
assert.equal(selectOptions.includes("Personalizado sin guardar"), true);

const compactNotice = helpers.outputTemporaryNoticeHtml({{ compact: true }});
assert.equal(compactNotice.includes('temporary-output-notice--compact'), true);
assert.equal(compactNotice.includes('Aplica al lote o guarda la salida.'), true);

const editHtml = helpers.exportSummaryHtml({{
  editing: true,
  displayName: 'Salida <temporal>',
  presetSummary: 'JPG · "1800x2400"',
  editDirty: true,
}});
assert.equal(editHtml.includes('Salida &lt;temporal&gt;'), true);
assert.equal(editHtml.includes('JPG · &quot;1800x2400&quot;'), true);
assert.equal(editHtml.includes('temporary-output-notice--compact'), true);
assert.equal(editHtml.includes('data-action="apply-output-edit"'), true);

const profileRows = [
  {{ format: "JPG", name: "Principal", size: "1800x2400", backgroundLabel: "gris claro", destinationLabel: "Salida" }},
  {{ format: "PNG", name: "Transparente", size: "1200x1200", backgroundLabel: "transparente", destinationLabel: "C:/Export" }},
  {{ format: "JPG", name: "Marketplace", size: "1600x1600", destinationLabel: "market" }},
  {{ format: "PNG", name: "Thumb", size: "800x800", destinationLabel: "thumb" }},
  {{ format: "JPG", name: "Extra", size: "600x600", destinationLabel: "extra" }},
];
const rowsHtml = helpers.profileSummaryRowsHtml(profileRows, profileRows.length);
assert.equal(rowsHtml.includes("Principal"), true);
assert.equal(rowsHtml.includes('class="preset-summary-output-badge">JPG</span>'), true);
assert.equal(rowsHtml.includes('class="preset-summary-output-meta"'), true);
assert.equal(rowsHtml.includes(">1800 × 2400</span>"), true);
assert.equal(rowsHtml.includes(">gris claro</span>"), true);
assert.equal(rowsHtml.includes(">Salida</span>"), true);
assert.equal(rowsHtml.includes('title="Principal · 1800x2400 · Salida"'), true);
assert.equal(rowsHtml.includes("1 salida más"), true);

const presetHtml = helpers.exportSummaryHtml({{
  editing: false,
  displayName: "5 salidas",
  activeOutputCount: 5,
  outputCount: 25,
  profileRows,
  formatLabel: "5 salidas",
  sizeLabel: "Por salida",
  backgroundLabel: "Por salida",
  destinationText: 'C:/Export/"uno"',
  namingLabel: "Por salida",
  example: 'camisa <azul>.jpg',
  warningSummaryHtml: '<div class="warning-summary">Aviso</div>',
  temporaryNoticeHtml: '<div class="temporary-output-notice">Temporal</div>',
}});
assert.equal(presetHtml.includes("<span>Salidas</span>"), true);
assert.equal(presetHtml.includes("5 activas"), true);
assert.equal(presetHtml.includes("25 archivos previstos"), true);
assert.equal(presetHtml.includes("Formato"), false);
assert.equal(presetHtml.includes("Nombre final"), false);
assert.equal(presetHtml.includes("camisa &lt;azul&gt;.jpg"), false);
assert.equal(presetHtml.includes('warning-summary'), true);
assert.equal(presetHtml.includes('temporary-output-notice'), true);
assert.equal(presetHtml.includes('data-action="new-output-profile"'), true);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
