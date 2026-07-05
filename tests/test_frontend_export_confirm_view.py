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


def test_export_confirm_controller_lists_output_names_per_profile():
    source = (FRONTEND_DIR / "app-modal-render-controller.js").read_text(encoding="utf-8")
    confirm_block = source.split("function exportConfirmHtml(risks) {", 1)[1].split("function batchDetailHtml()", 1)[0]

    assert "exportConfirmSummaryRows" in confirm_block
    assert "exportConfirmOutputNameRows" in source
    assert "outputNameForProfile(profile)" in source
    assert 'label: "Nombres de salida"' in source
    assert '["Nombre", namingExample()]' not in confirm_block


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
    ["Destino", "Salida"],
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

const multiOutputHtml = helpers.exportConfirmHtml({{
  risks: [],
  summaryRows: [
    {{ label: "Salidas", value: "3 salidas", items: ["Percha web (JPG)", "Zalando (JPG)", "JPG Baja (JPG)"] }},
    {{ label: "Nombres de salida", items: [
      {{ label: "Percha web (JPG)", value: "Capa 1.jpg" }},
      {{ label: "Zalando (JPG)", value: "Capa 1.jpg" }},
      {{ label: "JPG Baja (JPG)", value: "Capa 1.jpg" }},
    ] }},
  ],
}});
assert.equal(multiOutputHtml.includes('class="export-confirm-summary__item has-list"'), true);
assert.equal(multiOutputHtml.includes("<span>Nombres de salida</span>"), true);
assert.equal(multiOutputHtml.includes("Percha web (JPG)"), true);
assert.equal(multiOutputHtml.includes('title="Capa 1.jpg"'), true);
assert.equal(multiOutputHtml.includes("Capa 1_PRO.jpg"), false);

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

assert.deepEqual(helpers.exportConfirmModalState({{
  risks: [],
  actionText: "Exportar 4 imágenes",
}}), {{
  actionDanger: false,
  actionText: "Exportar 4 imágenes",
  blocking: false,
  subtitle: "Confirma solo los puntos que requieren atención.",
}});

assert.deepEqual(helpers.exportConfirmModalState({{
  risks: [{{ blocking: true, title: "Destino" }}],
  actionText: "Exportar 4 imágenes",
}}), {{
  actionDanger: true,
  actionText: "Revisar problemas",
  blocking: true,
  subtitle: "Hay puntos que impiden exportar.",
}});
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
