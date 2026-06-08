import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "export-state.js"
INDEX_PATH = FRONTEND_DIR / "index.html"


def test_export_state_helper_loads_before_app_script():
    html = INDEX_PATH.read_text(encoding="utf-8")

    helper_index = html.index("export-state.js")
    app_index = html.index("app.js")

    assert helper_index < app_index


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_export_state_helpers_keep_status_transition_contracts():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

assert.deepEqual(helpers.exportStartState({{ scenario: "export-running", resetConfirm: true }}), {{
  exportStatus: "running",
  progress: 0,
  processed: 0,
  exportJobId: null,
  exportDestinations: [],
  exportMessages: [],
  exportCompletedItems: [],
  exportIssues: [],
  exportResult: null,
  errors: [],
  paused: false,
  statusText: "Preparando exportación",
  scenario: "export-running",
  exportConfirmOpen: false,
  exportConfirmRisks: [],
  exportConfirmOptions: null,
}});

assert.deepEqual(helpers.bridgeRunFailureState("timeout"), {{
  exportStatus: "failed",
  progress: 0,
  processed: 0,
  exportIssues: [{{ level: "error", title: "Exportación fallida", detail: "timeout" }}],
  exportResult: null,
  errors: [{{ level: "error", title: "Exportación fallida", detail: "timeout" }}],
  statusText: "Exportación fallida",
}});

assert.deepEqual(helpers.bridgeProgressUnavailableState("offline"), {{
  exportStatus: "failed",
  paused: false,
  errors: [{{ level: "error", title: "Progreso no disponible", detail: "offline" }}],
  statusText: "Progreso no disponible",
}});

assert.deepEqual(helpers.stoppedExportState(), {{
  exportStatus: "failed",
  paused: false,
  errors: [{{ level: "error", title: "Exportación detenida", detail: "No se generaron más archivos." }}],
  statusText: "Exportación fallida",
}});

assert.deepEqual(helpers.normalizeBridgeIssue({{ level: "info", title: "", detail: "" }}), {{
  level: "warning",
  title: "Exportación",
  detail: "Revisa el resultado.",
}});

const previous = {{
  exportJobId: "old",
  exportDestinations: ["C:/old"],
  exportMessages: ["prev"],
  exportCompletedItems: [],
  exportIssues: [],
  exportResult: {{ success: false }},
}};

assert.deepEqual(helpers.bridgeStatusPatch({{
  jobId: "job-1",
  destinations: ["C:/out"],
  messages: ["ok"],
  completedItems: [{{ name: "a", success: true }}],
  issues: [{{ level: "error", title: "A", detail: "B" }}],
  result: {{ success: true }},
  progress: {{ percent: 100, processed: 3, total: 3 }},
  status: "completed",
}}, previous), {{
  exportJobId: "job-1",
  exportDestinations: ["C:/out"],
  exportMessages: ["ok"],
  exportCompletedItems: [{{ name: "a", success: true }}],
  exportIssues: [{{ level: "error", title: "A", detail: "B" }}],
  exportResult: {{ success: true }},
  progress: 0,
  processed: 3,
  paused: false,
  exportStatus: "completed",
  statusText: "Exportación completada · 3/3",
}});

assert.equal(helpers.bridgeStatusPatch({{ status: "partial", progress: {{ percent: 80, processed: 2, total: 3 }} }}, previous).statusText, "Exportación con avisos");
assert.equal(helpers.bridgeStatusPatch({{ status: "failed", progress: {{ processed: 2 }} }}, previous).statusText, "Exportación fallida");
assert.equal(helpers.bridgeStatusPatch({{ status: "cancelled", progress: {{ processed: 2 }} }}, previous).statusText, "Exportación cancelada");
assert.equal(helpers.bridgeStatusPatch({{ status: "paused", progress: {{ processed: 2, total: 3 }} }}, previous).statusText, "Pausado");
assert.equal(helpers.bridgeStatusPatch({{ status: "cancelling", progress: {{ processed: 2, total: 3 }} }}, previous).statusText, "Deteniendo...");
assert.equal(helpers.bridgeStatusPatch({{ status: "running", progress: {{ processed: 2, total: 3 }} }}, previous).statusText, "Procesando 2/3");

assert.deepEqual(helpers.bridgeStatusErrors({{ status: "running", messages: ["x"] }}, [], []), []);
assert.deepEqual(helpers.bridgeStatusErrors({{ status: "partial", messages: ["a", "b"] }}, [], []), [
  {{ level: "warning", title: "Exportación", detail: "a" }},
  {{ level: "warning", title: "Exportación", detail: "b" }},
]);
assert.deepEqual(helpers.bridgeStatusErrors({{ status: "failed", messages: ["m"] }}, [
  {{ name: "bad.png", success: false }},
], []), [
  {{ level: "error", title: "bad.png", detail: "No se pudo exportar." }},
  {{ level: "error", title: "Exportación", detail: "m" }},
]);
assert.deepEqual(helpers.bridgeStatusErrors({{ status: "failed", messages: ["m"] }}, [], [
  {{ level: "error", title: "Bridge", detail: "fallo" }},
]), [
  {{ level: "error", title: "Bridge", detail: "fallo" }},
]);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
