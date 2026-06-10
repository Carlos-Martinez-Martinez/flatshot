import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "inspector-output-view.js"
INDEX_PATH = FRONTEND_DIR / "index.html"


def test_inspector_output_view_helper_loads_before_app_script():
    html = INDEX_PATH.read_text(encoding="utf-8")

    helper_index = html.index("inspector-output-view.js")
    app_index = html.index("app.js")

    assert helper_index < app_index


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_inspector_output_view_renders_output_contracts():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

assert.equal(helpers.escapeHtml('<a&b"c>'), '&lt;a&amp;b&quot;c&gt;');

const primaryRow = helpers.outputProfileInlineRowHtml({{
  id: "web_rgb230",
  name: "Web <gris>",
  enabled: true,
  active: true,
  canToggle: false,
  summary: 'JPG · 1800x2400 · "RGB230"',
}});
assert.equal(primaryRow.includes("active-output-row is-primary is-enabled"), true);
assert.equal(primaryRow.includes("Web &lt;gris&gt;"), true);
assert.equal(primaryRow.includes("&quot;RGB230&quot;"), true);
assert.equal(primaryRow.includes("Principal"), true);
assert.equal(primaryRow.includes("disabled"), true);

const disabledRow = helpers.outputProfileInlineRowHtml({{
  id: "archive_png",
  name: "Archivo PNG",
  enabled: false,
  active: false,
  canToggle: true,
  summary: "PNG · transparente",
}});
assert.equal(disabledRow.includes("active-output-row is-disabled"), true);
assert.equal(disabledRow.includes("checked"), false);
assert.equal(disabledRow.includes(' disabled />'), false);

const notice = helpers.outputTemporaryNoticeHtml();
assert.equal(notice.includes("Cambios temporales en esta salida"), true);
assert.equal(notice.includes('data-action="save-output-current-profile"'), true);
assert.equal(notice.includes('data-action="discard-output-overrides"'), true);

const card = helpers.outputInspectorCardHtml({{
  activeCount: 2,
  totalFiles: 8,
  readyLabel: "4 imágenes listas",
  dirty: true,
  rows: [
    {{ id: "web_rgb230", name: "Web", enabled: true, active: true, canToggle: true, summary: "JPG" }},
    {{ id: "white", name: "Blanco", enabled: true, active: false, canToggle: true, summary: "PNG" }},
  ],
}});
assert.equal(card.includes("Salidas activas · 2"), true);
assert.equal(card.includes("8 archivos previstos"), true);
assert.equal(card.includes("4 imágenes listas"), true);
assert.equal(card.includes("active-output-list"), true);
assert.equal(card.includes("Cambios temporales"), true);
assert.equal(card.includes('data-action="edit-output"'), true);
assert.equal(card.includes('data-action="open-app-settings"'), true);

const pendingCard = helpers.outputInspectorCardHtml({{
  activeCount: 1,
  totalFiles: 0,
  readyLabel: "Sin imágenes listas",
  dirty: false,
  rows: [],
}});
assert.equal(pendingCard.includes("Pendiente de lote"), true);
assert.equal(pendingCard.includes("Cambios temporales"), false);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
