import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "inspector-review-view.js"
INDEX_PATH = FRONTEND_DIR / "index.html"


def test_inspector_review_view_helper_loads_before_app_script():
    html = INDEX_PATH.read_text(encoding="utf-8")

    helper_index = html.index("inspector-review-view.js")
    app_index = html.index("app.js")

    assert helper_index < app_index


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_inspector_review_view_renders_review_contracts():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

assert.equal(helpers.escapeHtml('<a&b"c>'), '&lt;a&amp;b&quot;c&gt;');

const lot = helpers.lotInspectorSummaryHtml({{
  stateLabel: "2 avisos",
  counts: {{
    readyImages: 3,
    exportableImages: 2,
    nonExportableImages: 1,
    ignoredFiles: 4,
  }},
}});
assert.equal(lot.includes("lot-summary-card"), true);
assert.equal(lot.includes("2 avisos"), true);
assert.equal(lot.includes("<em>Ignorados</em><strong>4</strong>"), true);

const lotCard = helpers.lotInspectorCardHtml({{
  title: "Lote <actual>",
  meta: '3 imágenes listas · Ignorados "técnicos"',
  tone: "warning",
}});
assert.equal(lotCard.includes('class="inspector-summary warning"'), true);
assert.equal(lotCard.includes("<span>Lote</span>"), true);
assert.equal(lotCard.includes("Lote &lt;actual&gt;"), true);
assert.equal(lotCard.includes("Ignorados &quot;técnicos&quot;"), true);
assert.equal(lotCard.includes('data-action="open-batch-detail"'), true);
assert.equal(lotCard.includes("Ver detalle"), true);

const noImage = helpers.reviewPanelHtml({{
  lotSummaryHtml: lot,
  image: null,
  emptyStateHtml: '<div class="empty-state">Selecciona</div>',
}});
assert.equal(noImage.includes("lot-summary-card"), true);
assert.equal(noImage.includes("Selecciona"), true);

const issueList = helpers.reviewIssueListHtml([
  {{ level: "warning", title: "Alpha <bajo>", detail: 'Ruta "x"' }},
  {{ level: "error", title: "Export", detail: "fallo" }},
]);
assert.equal(issueList.includes('class="review-issue warning"'), true);
assert.equal(issueList.includes('class="review-issue error"'), true);
assert.equal(issueList.includes("Alpha &lt;bajo&gt;"), true);
assert.equal(issueList.includes("Ruta &quot;x&quot;"), true);

const html = helpers.reviewPanelHtml({{
  lotSummaryHtml: lot,
  image: {{ name: "camisa <azul>.png", path: "C:/camisa.png" }},
  reviewState: {{ tone: "warning", label: "Aviso" }},
  issues: [
    {{ level: "warning", title: "Vista", detail: "Revisar" }},
  ],
  outputName: "camisa_PRO.jpg",
  outputDetail: "JPG · 1800x2400",
  hasLocal: false,
  selectedIndexLabel: "2 de 3",
  canNavigate: true,
}});
assert.equal(html.includes('class="review-card review-card--compact warning"'), true);
assert.equal(html.includes("camisa &lt;azul&gt;.png"), true);
assert.equal(html.includes("2 de 3"), true);
assert.equal(html.includes("camisa_PRO.jpg"), true);
assert.equal(html.includes('data-action="review-errors"'), true);
assert.equal(html.includes('data-action="open-advanced"'), true);
assert.equal(html.includes('data-action="reset-local-adjustment"'), false);
assert.equal(html.includes('data-action="previous-image" disabled'), false);

const localHtml = helpers.reviewPanelHtml({{
  lotSummaryHtml: lot,
  image: {{ name: "camisa.png" }},
  reviewState: {{ tone: "active", label: "Ajustada" }},
  issues: [],
  outputName: "camisa_PRO.jpg",
  outputDetail: "JPG",
  hasLocal: true,
  selectedIndexLabel: "1 de 1",
  canNavigate: false,
}});
assert.equal(localHtml.includes('data-action="reset-local-adjustment"'), true);
assert.equal(localHtml.includes('data-action="previous-image" disabled'), true);
assert.equal(localHtml.includes('data-action="review-errors"'), false);

assert.equal(helpers.selectedImageInspectorCardHtml({{ hasReadyBatch: false }}), "");
const emptySelected = helpers.selectedImageInspectorCardHtml({{
  hasReadyBatch: true,
  image: null,
}});
assert.equal(emptySelected.includes("Sin selección"), true);
assert.equal(emptySelected.includes('data-action="select-first-image"'), true);

const selectedCard = helpers.selectedImageInspectorCardHtml({{
  hasReadyBatch: true,
  image: {{ name: "camisa <azul>.png", path: "C:/camisa.png" }},
  detail: 'Detalle "x"',
  hasLocal: true,
}});
assert.equal(selectedCard.includes("Imagen seleccionada"), true);
assert.equal(selectedCard.includes("camisa &lt;azul&gt;.png"), true);
assert.equal(selectedCard.includes("Detalle &quot;x&quot;"), true);
assert.equal(selectedCard.includes("Ajuste de esta imagen"), true);
assert.equal(selectedCard.includes("Personalizado"), true);
assert.equal(selectedCard.includes('data-action="open-image-adjustment"'), true);
assert.equal(selectedCard.includes('data-action="reset-local-adjustment"'), true);
assert.equal(selectedCard.includes("Restablecer al lote"), true);

const alertHtml = helpers.issuesInspectorCardHtml({{
  rows: [
    {{ level: "error", title: "Destino <ocupado>", detail: "Ya existe", path: "C:/out" }},
    {{ level: "warning", title: "Alpha", detail: "Bajo" }},
  ],
  blocking: true,
  countLabel: "1 bloqueo",
}});
assert.equal(alertHtml.includes('class="inspector-alert error"'), true);
assert.equal(alertHtml.includes("Exportación bloqueada"), true);
assert.equal(alertHtml.includes("Destino &lt;ocupado&gt;"), true);
assert.equal(alertHtml.includes('data-action="review-errors"'), true);
assert.equal(helpers.issuesInspectorCardHtml({{ rows: [] }}), "");

const aspect = helpers.aspectInspectorCardHtml({{
  hasReadyBatch: true,
  activePreset: "Luz <cenital>",
  statusLabel: "Global · Modificado",
  adjustments: [
    {{ name: "Luz <cenital>" }},
    {{ name: "Sin sombra" }},
  ],
  appliedCount: 2,
  customizedCount: 1,
}});
assert.equal(aspect.includes("Luz &lt;cenital&gt;"), true);
assert.equal(aspect.includes("Procesado"), true);
assert.equal(aspect.includes("Ajuste de imagen"), true);
assert.equal(aspect.includes("Aplicado a 2 imágenes"), true);
assert.equal(aspect.includes('data-action="open-advanced"'), true);
assert.equal(aspect.includes('data-action="open-preset-editor"'), true);
assert.equal(aspect.includes('data-action="apply-global-adjustment-to-overrides"'), true);
assert.equal(aspect.includes("1 imagen mantiene su ajuste personalizado."), true);
assert.equal(helpers.aspectInspectorCardHtml({{ hasReadyBatch: false }}), "");
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
