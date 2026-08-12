import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "workbench-view.js"


def test_workbench_view_loads_before_shell_controllers():
    html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")

    assert html.index("workbench-view.js") < html.index("app-loader.js")


def test_workbench_shell_prioritizes_portrait_preview_vertical_gallery_and_contextual_inspector():
    html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
    shell_css = (FRONTEND_DIR / "css" / "02-layout" / "shell-workspace.css").read_text(encoding="utf-8")
    gallery_css = (FRONTEND_DIR / "css" / "04-batch-gallery" / "image-grid.css").read_text(encoding="utf-8")
    inspector_css = (FRONTEND_DIR / "css" / "06-inspector-export" / "inspector-navigation.css").read_text(encoding="utf-8")
    responsive_css = (FRONTEND_DIR / "css" / "08-states-responsive" / "responsive.css").read_text(encoding="utf-8")
    app = (FRONTEND_DIR / "app.js").read_text(encoding="utf-8")

    assert "grid-template-columns: clamp(300px, 17vw, 360px) minmax(560px, 1fr) clamp(320px, 19vw, 390px);" in shell_css
    assert "grid-template-rows: minmax(0, 1fr);" in shell_css
    assert "grid-auto-flow: row;" in gallery_css
    assert 'data-inspector-tab="review">Imagen</button>' in html
    assert 'data-inspector-tab="advanced">Aspecto</button>' in html
    assert "grid-template-columns: repeat(4, minmax(0, 1fr));" in inspector_css
    assert 'inspectorTab: "advanced"' in app
    assert '@media (max-width: 1119px)' in responsive_css
    assert '.settings-panel.is-editing-preset' in responsive_css


def test_running_job_keeps_progress_actions_out_of_header():
    source = (FRONTEND_DIR / "app-topbar-bridge.js").read_text(encoding="utf-8")

    assert 'topPrimary.hidden = state.exportStatus === "running";' in source
    assert 'workbenchContext.hidden = state.batch === "none" || state.batch === "scanning" || state.exportStatus === "running";' in source
    assert 'preflight.hidden = state.batch === "none" || state.batch === "scanning" || !headerStatus.showPreflight;' in source


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required")
def test_workbench_view_builds_semantic_batch_and_header_contexts():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

assert.deepEqual(helpers.semanticBatchItems({{
  ready: 12,
  warnings: 2,
  excluded: 1,
  customized: 3,
}}), [
  {{ key: "ready", label: "12 listas", tone: "ready" }},
  {{ key: "warnings", label: "2 con aviso", tone: "warning" }},
  {{ key: "excluded", label: "1 excluida", tone: "error" }},
  {{ key: "customized", label: "3 personalizadas", tone: "info" }},
]);

assert.equal(helpers.semanticBatchText({{ ready: 1, warnings: 1, excluded: 2, customized: 1 }}),
  "1 lista · 1 con aviso · 2 excluidas · 1 personalizada");

assert.deepEqual(helpers.headerContexts({{
  folderPath: "C:/produccion/bolsos agosto",
  presetName: "Luz cenital",
  outputName: "Web JPG",
}}), {{
  folder: {{ label: "Carpeta", value: "bolsos agosto", title: "C:/produccion/bolsos agosto" }},
  preset: {{ label: "Preset", value: "Luz cenital", title: "Luz cenital" }},
  output: {{ label: "Salida", value: "Web JPG", title: "Web JPG" }},
}});

assert.deepEqual(helpers.headerContexts({{}}), {{
  folder: {{ label: "Carpeta", value: "Sin lote", title: "Sin lote" }},
  preset: {{ label: "Preset", value: "Sin preset", title: "Sin preset" }},
  output: {{ label: "Salida", value: "Sin configurar", title: "Sin configurar" }},
}});

assert.deepEqual(helpers.headerStatusVisibility({{
  ready: true,
  issueCount: 0,
  processing: false,
}}), {{ showSummary: false, showPreflight: false }});
assert.deepEqual(helpers.headerStatusVisibility({{
  ready: false,
  issueCount: 2,
  processing: false,
}}), {{ showSummary: true, showPreflight: true }});
assert.deepEqual(helpers.headerStatusVisibility({{
  ready: true,
  issueCount: 2,
  processing: false,
}}), {{ showSummary: true, showPreflight: false }});
assert.deepEqual(helpers.headerStatusVisibility({{
  ready: false,
  issueCount: 0,
  processing: true,
}}), {{ showSummary: false, showPreflight: false }});
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
