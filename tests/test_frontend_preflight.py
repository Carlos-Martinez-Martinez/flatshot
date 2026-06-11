import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "preflight.js"
INDEX_PATH = FRONTEND_DIR / "index.html"


def test_preflight_helper_loads_before_app_script():
    html = INDEX_PATH.read_text(encoding="utf-8")

    output_index = html.index("output-profiles.js")
    preflight_index = html.index("preflight.js")
    app_index = html.index("app.js")

    assert output_index < app_index
    assert preflight_index < app_index


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_preflight_helpers_keep_batch_and_readiness_contracts():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

const ignoredReasons = new Set(["system_file", "unsupported_extension"]);
const actionableReasons = new Set(["read_error"]);
const omissions = [
  {{ reason: "system_file", name: "desktop.ini" }},
  {{ reason: "read_error", name: "bad.png" }},
  {{ severity: "error", reason: "read_error", name: "locked.png" }},
];

assert.equal(helpers.countText(2, "imagen", "imágenes"), "2 imágenes");
assert.equal(helpers.readyImagesText(1), "1 imagen lista");
assert.equal(helpers.ignoredNeutralText(0), "");
assert.equal(helpers.ignoredImagesText(2), "2 ignoradas");
assert.equal(helpers.omissionSeverity(omissions[0], {{ ignoredReasons, actionableReasons }}), "ignored");
assert.equal(helpers.omissionSeverity(omissions[1], {{ ignoredReasons, actionableReasons }}), "warning");
assert.equal(helpers.omissionSeverity(omissions[2], {{ ignoredReasons, actionableReasons }}), "error");

const split = helpers.splitOmissions(omissions, {{ ignoredReasons, actionableReasons }});
assert.equal(split.ignored.length, 1);
assert.equal(split.actionable.length, 2);

const images = [
  {{ id: "a", status: "ready", exportable: true }},
  {{ id: "b", status: "warning", exportable: true }},
  {{ id: "c", status: "ready", exportable: false }},
  {{ id: "d", status: "error", exportable: false }},
];
const exportables = images.filter((image) => image.exportable);
const exportItemStatuses = new Map([["a", null], ["b", {{ status: "error" }}]]);
const counts = helpers.calculateBatchCounts({{
  batch: "ready",
  images,
  exportables,
  diagnostics: {{ totalFiles: 7, totalImages: 4, totalOmitted: 3 }},
  omissions,
  exportItemStatuses,
  stateErrors: [{{ level: "warning" }}],
  exportStatus: "failed",
  blockingValidationIssueCount: 1,
  ignoredReasons,
  actionableReasons,
}});
assert.deepEqual(counts, {{
  filesFound: 7,
  validImages: 4,
  exportableImages: 2,
  readyImages: 1,
  warningImages: 1,
  omittedFiles: 3,
  ignoredFiles: 1,
  warningFiles: 1,
  errorFiles: 1,
  nonExportableImages: 3,
  blockingErrors: 3,
  nonBlockingWarnings: 6,
  reviewIssues: 6,
}});

const issues = helpers.buildPreflightIssues({{
  validationIssues: [{{ level: "error", title: "Nombre de archivo vacío", detail: "Define una plantilla." }}],
  stateErrors: [{{ level: "warning", title: "Aviso previo", detail: "Revisar." }}],
  counts,
  actionableOmissions: split.actionable,
  hasBatch: true,
  warningImages: 1,
  errorImages: 2,
  exportableCount: 2,
  actionableOmissionSummary: "bad.png y locked.png",
}});
assert.equal(issues.length, 6);
assert.deepEqual(helpers.preflightCounts(issues), {{ errors: 2, warnings: 4 }});

assert.equal(helpers.isExportReady({{
  validationIssues: [],
  hasBatch: true,
  exportableCount: 1,
  activeOutputCount: 1,
  hasImageAdjustment: true,
}}), true);
assert.equal(helpers.isExportReady({{
  validationIssues: [{{ level: "warning", title: "No hay PNG válidos" }}],
  hasBatch: true,
  exportableCount: 1,
  activeOutputCount: 1,
  hasImageAdjustment: true,
}}), false);
assert.equal(helpers.isExportReady({{
  validationIssues: [],
  hasBatch: true,
  exportableCount: 1,
  activeOutputCount: 0,
  hasImageAdjustment: true,
}}), false);
assert.equal(helpers.isExportReady({{
  validationIssues: [],
  hasBatch: true,
  exportableCount: 1,
  activeOutputCount: 1,
  hasImageAdjustment: false,
}}), false);

assert.equal(helpers.issueMentionsExistingOutput({{ title: "Archivos ya existentes", detail: "" }}), true);
assert.deepEqual(helpers.dedupeExportRisks([
  {{ id: "same", title: "A", detail: "1" }},
  {{ id: "same", title: "B", detail: "2" }},
  {{ title: "C", detail: "3" }},
  {{ title: "C", detail: "3" }},
]), [
  {{ id: "same", title: "A", detail: "1" }},
  {{ title: "C", detail: "3" }},
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
