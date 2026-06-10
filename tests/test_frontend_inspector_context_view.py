import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "inspector-context-view.js"
INDEX_PATH = FRONTEND_DIR / "index.html"


def test_inspector_context_view_helper_loads_before_app_script():
    html = INDEX_PATH.read_text(encoding="utf-8")

    helper_index = html.index("inspector-context-view.js")
    app_index = html.index("app.js")

    assert helper_index < app_index


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_inspector_context_view_renders_context_contracts():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

assert.equal(helpers.escapeHtml('<a&b"c>'), '&lt;a&amp;b&quot;c&gt;');
assert.equal(helpers.inspectorMode({{ outputEditMode: true, inspectorTab: "review" }}), "output");
assert.equal(helpers.inspectorMode({{ outputEditMode: false, inspectorTab: "output" }}), "output");
assert.equal(helpers.inspectorMode({{ outputEditMode: false, inspectorTab: "advanced" }}), "advanced");
assert.equal(helpers.inspectorMode({{ outputEditMode: false, inspectorTab: "warnings" }}), "warnings");
assert.equal(helpers.inspectorMode({{ outputEditMode: false, inspectorTab: "review" }}), "summary");
assert.equal(helpers.inspectorMode({{ outputEditMode: false, inspectorTab: "unknown" }}), "summary");

assert.deepEqual(helpers.inspectorSubviewHeaderState({{
  mode: "output",
  outputEditMode: true,
  outputLabel: "JPG · 1800×2400",
}}), {{
  title: "Salida",
  subtitle: "Editar salida",
  detail: "",
  backAction: "cancel-output-edit",
  backLabel: "Cancelar",
  showManageAction: false,
}});
assert.deepEqual(helpers.inspectorSubviewHeaderState({{
  mode: "advanced",
  activePreset: "Luz cenital",
  presetSourceLabel: "Global · Modificado",
}}), {{
  title: "Editar ajuste",
  subtitle: "Luz cenital",
  detail: "Global · Modificado",
  backAction: "close-inspector-subview",
  backLabel: "Volver",
  showManageAction: true,
}});
assert.deepEqual(helpers.inspectorSubviewHeaderState({{
  mode: "advanced",
  activePreset: "Luz cenital",
  presetEditorOpen: true,
  presetSourceLabel: "Global",
}}), {{
  title: "Gestionar ajustes",
  subtitle: "Luz cenital",
  detail: "Global",
  backAction: "close-preset-editor",
  backLabel: "Volver",
  showManageAction: false,
}});
assert.deepEqual(helpers.inspectorSubviewHeaderState({{
  mode: "warnings",
  warningCount: 2,
}}), {{
  title: "Revisar",
  subtitle: "2 puntos",
  detail: "",
  backAction: "close-inspector-subview",
  backLabel: "Volver",
  showManageAction: false,
}});
assert.deepEqual(helpers.inspectorSubviewHeaderState({{
  mode: "unknown",
}}), {{
  title: "Detalle",
  subtitle: "",
  detail: "",
  backAction: "close-inspector-subview",
  backLabel: "Volver",
  showManageAction: false,
}});

assert.deepEqual(helpers.contextualPreflightRows({{ batch: "scanning" }}), [
  {{ state: "pending", title: "Carpeta seleccionada", detail: "Leyendo origen" }},
  {{ state: "pending", title: "Imágenes listas", detail: "Contando archivos" }},
  {{ state: "pending", title: "Destino", detail: "Se configurará después" }},
]);
assert.deepEqual(helpers.contextualPreflightRows({{ batch: "none" }}), [
  {{ state: "pending", title: "Carpeta seleccionada", detail: "Pendiente" }},
  {{ state: "pending", title: "Imágenes listas", detail: "Pendiente" }},
  {{ state: "pending", title: "Destino de salida", detail: "Origen / _SALIDA_PRO" }},
]);
assert.deepEqual(helpers.contextualPreflightRows({{
  batch: "empty",
  totalFiles: 7,
  ignoredSummary: "2 archivos ignorados",
}}), [
  {{ state: "warning", title: "Carpeta revisada", detail: "7 archivos encontrados" }},
  {{ state: "error", title: "Imágenes exportables", detail: "0 imágenes" }},
  {{ state: "pending", title: "Ignorados", detail: "2 archivos ignorados" }},
  {{ state: "pending", title: "Destino", detail: "Pendiente hasta cargar un lote" }},
]);
assert.equal(helpers.contextualPreflightRows({{ batch: "ready" }}).length, 0);

const header = helpers.inspectorSubviewHeaderHtml({{
  title: "Editar <ajuste>",
  subtitle: 'Luz "cenital"',
  detail: "Global",
  backAction: "close-inspector-subview",
  backLabel: "Volver",
  showManageAction: true,
}});
assert.equal(header.includes("Editar &lt;ajuste&gt;"), true);
assert.equal(header.includes("Luz &quot;cenital&quot;"), true);
assert.equal(header.includes('data-action="open-preset-editor"'), true);
assert.equal(header.includes('data-action="close-inspector-subview"'), true);

const scanning = helpers.contextualInspectorHtml({{
  batch: "scanning",
  scanStatus: "Leyendo <PNG>",
  progressHtml: '<div class="context-progress">P</div>',
  preflightHtml: '<div class="preflight-list">F</div>',
}});
assert.equal(scanning.includes("Escaneando carpeta"), true);
assert.equal(scanning.includes("Leyendo &lt;PNG&gt;"), true);
assert.equal(scanning.includes("context-progress"), true);

const none = helpers.contextualInspectorHtml({{
  batch: "none",
  preflightHtml: '<div class="preflight-list">F</div>',
  outputSummary: 'JPG · "1800x2400"',
  activePreset: "Luz <cenital>",
}});
assert.equal(none.includes("Seleccionar carpeta"), true);
assert.equal(none.includes("JPG · &quot;1800x2400&quot;"), true);
assert.equal(none.includes("Ajuste Luz &lt;cenital&gt;"), true);
assert.equal(none.includes('data-action="pick-bridge-folder"'), true);

const empty = helpers.contextualInspectorHtml({{
  batch: "empty",
  scanStatus: "Sin PNG",
  preflightHtml: '<div class="preflight-list">F</div>',
}});
assert.equal(empty.includes("context-panel warning"), true);
assert.equal(empty.includes("Exportación bloqueada"), true);
assert.equal(empty.includes("Elegir otra carpeta"), true);

const fallback = helpers.contextualInspectorHtml({{
  batch: "ready",
  compactStatus: '4 imágenes "listas"',
}});
assert.equal(fallback.includes("Selecciona una imagen"), true);
assert.equal(fallback.includes("4 imágenes &quot;listas&quot;"), true);
assert.equal(fallback.includes('data-action="select-first-image"'), true);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
