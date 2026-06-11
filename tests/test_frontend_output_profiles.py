import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend" / "output-profiles.js"
INDEX_PATH = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend" / "index.html"


def test_output_profile_helper_loads_before_app_script():
    html = INDEX_PATH.read_text(encoding="utf-8")

    helper_index = html.index("output-profiles.js")
    app_index = html.index("app.js")

    assert helper_index < app_index


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_output_profile_helpers_keep_export_contracts():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

assert.equal(helpers.normalizeExportFormat("jpeg"), "JPG");
assert.equal(helpers.normalizeExportFormat(".png"), "PNG");
assert.equal(helpers.normalizeExportFormat("gif"), "JPG");

assert.deepEqual(helpers.parseOutputSize("1200 x 1600"), {{
  width: 1200,
  height: 1600,
  normalized: "1200x1600",
}});
assert.deepEqual(helpers.parseOutputSize("bad"), {{
  width: 1800,
  height: 2400,
  normalized: "1800x2400",
}});

const normalized = helpers.normalizeOutputProfile({{
  id: "main",
  name: "Web RGB230",
  enabled: true,
  format: "jpeg",
  width: "0",
  height: "2500",
  background: "unknown",
  destinationMode: "source",
  destinationValue: "",
  naming: "",
  suffix: null,
}});
assert.deepEqual(normalized, {{
  id: "main",
  name: "Web gris claro",
  enabled: true,
  format: "JPG",
  width: 1800,
  height: 2500,
  background: "rgb230",
  destinationMode: "source",
  destinationValue: "_SALIDA_PRO",
  naming: "{{original}}{{suffix}}",
  suffix: "_PRO",
}});

const list = helpers.normalizeOutputProfileList([
  {{ id: "dup", name: "Uno", enabled: false }},
  {{ id: "dup", name: "Dos", enabled: false }},
], "dup");
assert.equal(list.length, 2);
assert.equal(list[0].id, "dup");
assert.notEqual(list[1].id, "dup");
assert.equal(list[0].enabled, false);

const validation = helpers.outputProfileValidation({{
  name: "Canal",
  format: "JPG",
  background: "rgb230",
  width: "1800",
  height: "2400",
  suffix: "_WEB",
  naming: "{{folder}}_{{index:03d}}",
  destinationMode: "source",
  destinationValue: "_WEB",
}});
assert.deepEqual(validation.errors, []);
assert.deepEqual(validation.warnings, ["Incluye {{original}} para mantener la referencia del archivo."]);
assert.equal(validation.fields.naming, "warning");

const seen = new Set();
const primary = helpers.exportVariantPayloadFromProfile({{
  id: "web_rgb230",
  name: "Web RGB230",
  format: "JPG",
  background: "rgb230",
  destinationMode: "source",
  destinationValue: "_SALIDA_PRO",
  naming: "{{original}}{{suffix}}",
  suffix: "_PRO",
  width: 1800,
  height: 2400,
}}, 0, seen);
const duplicate = helpers.exportVariantPayloadFromProfile({{
  id: "web_rgb230",
  name: "Web RGB230 copia",
  format: "PNG",
  background: "transparent",
  destinationMode: "custom",
  destinationValue: "C:/salida",
  naming: "{{original}}{{suffix}}",
  suffix: "_PNG",
  width: 1000,
  height: 1200,
}}, 1, seen);

assert.deepEqual(primary, {{
  id: "web_rgb230",
  label: "Web RGB230",
  enabled: true,
  format: "JPG",
  transparent_bg: false,
  bg_color: [230, 230, 230],
  suffix: "_PRO",
  naming_template: "{{original}}{{suffix}}",
  output_destination: "subfolder",
  output_folder_name: "_SALIDA_PRO",
  custom_output_path: null,
  output_width: 1800,
  output_height: 2400,
}});
assert.equal(duplicate.id, "web_rgb230_2");
assert.equal(duplicate.output_destination, "custom");
assert.equal(duplicate.custom_output_path, "C:/salida");
assert.equal(duplicate.transparent_bg, true);
assert.deepEqual(duplicate.bg_color, [230, 230, 230]);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
