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

const currentRow = helpers.outputProfileInlineRowHtml({{
  id: "web_rgb230",
  name: "Web <gris>",
  enabled: true,
  active: true,
  canToggle: false,
  summary: 'JPG · 1800x2400 · "RGB230"',
}});
assert.equal(currentRow.includes("active-output-row is-current is-enabled"), true);
assert.equal(currentRow.includes("Web &lt;gris&gt;"), true);
assert.equal(currentRow.includes("&quot;RGB230&quot;"), true);
assert.equal(currentRow.includes("active-output-row__edit"), true);
assert.equal(currentRow.includes('data-action="edit-output-profile"'), true);
assert.equal(currentRow.includes('data-action="select-output-profile"'), false);
assert.equal(currentRow.includes(">Editar</button>"), true);
assert.equal(currentRow.includes("Principal"), false);
assert.equal(currentRow.includes("disabled"), true);

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

const selectableRow = helpers.outputProfileInlineRowHtml({{
  id: "zalando",
  name: "Zalando",
  enabled: true,
  active: false,
  canToggle: true,
  summary: "PNG · 1800x2400 · blanco",
}});
assert.equal(selectableRow.includes('class="active-output-row__main"'), true);
assert.equal(selectableRow.includes('data-action="select-output-profile"'), true);
assert.equal(selectableRow.includes('data-output-profile-id="zalando"'), true);
assert.equal(selectableRow.includes('aria-pressed="false"'), true);
assert.equal(selectableRow.includes('title="Seleccionar Zalando para previsualizar"'), true);
assert.equal(selectableRow.includes('class="active-output-row__edit" data-action="edit-output-profile"'), true);

const notice = helpers.outputTemporaryNoticeHtml();
assert.equal(notice.includes("Cambios sin guardar en este formato"), true);
assert.equal(notice.includes('data-action="save-output-current-profile"'), true);
assert.equal(notice.includes('data-action="discard-output-overrides"'), true);

const card = helpers.outputInspectorCardHtml({{
  activeCount: 2,
  totalFiles: 8,
  formulaLabel: "4 imágenes x 2 formatos = 8 archivos",
  readyLabel: "4 imágenes listas",
  dirty: true,
  rows: [
    {{ id: "web_rgb230", name: "Web", enabled: true, active: true, canToggle: true, summary: "JPG" }},
    {{ id: "white", name: "Blanco", enabled: true, active: false, canToggle: true, summary: "PNG" }},
  ],
}});
assert.equal(card.includes("2 formatos activos"), true);
assert.equal(card.includes("4 imágenes listas"), false);
assert.equal(card.includes("4 imágenes x 2 formatos = 8 archivos"), false);
assert.equal(card.includes("active-output-list"), true);
assert.equal(card.includes("Cambios sin guardar"), true);
assert.equal(card.includes('data-action="new-output-profile"'), true);
assert.equal(card.includes('data-action="open-app-settings"'), true);
assert.equal(card.includes(">Gestionar formatos</button>"), true);
assert.equal(card.includes(">Nuevo formato</button>"), true);

const pendingCard = helpers.outputInspectorCardHtml({{
  activeCount: 1,
  totalFiles: 0,
  readyLabel: "Sin imágenes listas",
  dirty: false,
  rows: [],
}});
assert.equal(pendingCard.includes("Pendiente de lote"), true);
assert.equal(pendingCard.includes("Sin imágenes listas"), false);
assert.equal(pendingCard.includes("Cambios sin guardar"), false);

const blockedCard = helpers.outputInspectorCardHtml({{
  activeCount: 0,
  totalFiles: 0,
  readyLabel: "4 imágenes listas",
  dirty: false,
  rows: [],
}});
assert.equal(blockedCard.includes("0 formatos activos"), true);
assert.equal(blockedCard.includes("4 imágenes listas"), false);
assert.equal(blockedCard.includes("Selecciona al menos un formato"), true);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
