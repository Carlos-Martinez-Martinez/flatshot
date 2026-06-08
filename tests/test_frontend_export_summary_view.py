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

const presetActions = helpers.exportPresetActionsHtml();
assert.equal(presetActions.includes('data-action="edit-output"'), true);
assert.equal(presetActions.includes('data-action="open-app-settings"'), true);

const compactNotice = helpers.outputTemporaryNoticeHtml({{ compact: true }});
assert.equal(compactNotice.includes('temporary-output-notice--compact'), true);
assert.equal(compactNotice.includes('Aplica al lote o guarda el preset.'), true);

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
  {{ format: "JPG", name: "Principal", size: "1800x2400", destinationLabel: "_SALIDA_PRO" }},
  {{ format: "PNG", name: "Transparente", size: "1200x1200", destinationLabel: "C:/Export" }},
  {{ format: "JPG", name: "Marketplace", size: "1600x1600", destinationLabel: "market" }},
  {{ format: "PNG", name: "Thumb", size: "800x800", destinationLabel: "thumb" }},
  {{ format: "JPG", name: "Extra", size: "600x600", destinationLabel: "extra" }},
];
const rowsHtml = helpers.profileSummaryRowsHtml(profileRows, profileRows.length);
assert.equal(rowsHtml.includes("Principal · 1800 × 2400"), true);
assert.equal(rowsHtml.includes('title="Principal · 1800x2400 · _SALIDA_PRO"'), true);
assert.equal(rowsHtml.includes("1 salidas más"), true);

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
assert.equal(presetHtml.includes("25 archivos previstos"), true);
assert.equal(presetHtml.includes('C:/Export/&quot;uno&quot;'), true);
assert.equal(presetHtml.includes('camisa &lt;azul&gt;.jpg'), true);
assert.equal(presetHtml.includes('warning-summary'), true);
assert.equal(presetHtml.includes('temporary-output-notice'), true);
assert.equal(presetHtml.includes('data-action="edit-output"'), true);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
