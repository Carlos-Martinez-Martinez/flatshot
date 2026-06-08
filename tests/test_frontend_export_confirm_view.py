import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "export-confirm-view.js"
INDEX_PATH = FRONTEND_DIR / "index.html"


def test_export_confirm_view_helper_loads_before_app_script():
    html = INDEX_PATH.read_text(encoding="utf-8")

    helper_index = html.index("export-confirm-view.js")
    app_index = html.index("app.js")

    assert helper_index < app_index


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_export_confirm_view_renders_existing_modal_contract():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

assert.equal(helpers.escapeHtml("<a&b\\"c>"), "&lt;a&amp;b&quot;c&gt;");

const readyHtml = helpers.exportConfirmHtml({{
  risks: [],
  summaryRows: [
    ["Imágenes", "2 exportables"],
    ["Salidas", "Web <gris>"],
    ["Destino", "_SALIDA_PRO"],
    ["Nombre", "foto_PRO.jpg"],
  ],
}});
assert.equal(readyHtml.includes('<div class="export-confirm-summary">'), true);
assert.equal(readyHtml.includes('<span>Imágenes</span>'), true);
assert.equal(readyHtml.includes('<strong title="Web &lt;gris&gt;">Web &lt;gris&gt;</strong>'), true);
assert.equal(readyHtml.includes('<h3>Avisos</h3>'), true);
assert.equal(readyHtml.includes('<div class="export-confirm-risk ready">'), true);
assert.equal(readyHtml.includes('Sin avisos'), true);
assert.equal(readyHtml.includes('Archivos existentes'), false);

const riskHtml = helpers.exportConfirmRiskHtml({{
  blocking: true,
  title: "Destino <bloqueado>",
  detail: 'Ruta "ocupada"',
}});
assert.equal(riskHtml.includes('class="export-confirm-risk error"'), true);
assert.equal(riskHtml.includes('<span aria-hidden="true">!</span>'), true);
assert.equal(riskHtml.includes('Destino &lt;bloqueado&gt;'), true);
assert.equal(riskHtml.includes('Ruta &quot;ocupada&quot;'), true);

const blockingHtml = helpers.exportConfirmHtml({{
  risks: [
    {{
      id: "existing-output-blocker",
      blocking: true,
      title: "Archivos existentes",
      detail: "Ya hay salidas.",
    }},
  ],
  summaryRows: [["Imágenes", "1 exportable"]],
}});
assert.equal(blockingHtml.includes('<h3>Bloqueos</h3>'), true);
assert.equal(blockingHtml.includes('FlatShot mantiene la validación segura'), true);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
