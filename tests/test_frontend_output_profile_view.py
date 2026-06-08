import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "output-profile-view.js"
INDEX_PATH = FRONTEND_DIR / "index.html"


def test_output_profile_view_helper_loads_before_app_script():
    html = INDEX_PATH.read_text(encoding="utf-8")

    helper_index = html.index("output-profile-view.js")
    app_index = html.index("app.js")

    assert helper_index < app_index


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_output_profile_view_renders_manager_and_editor_contracts():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

assert.equal(helpers.escapeHtml('<a&b"c>'), '&lt;a&amp;b&quot;c&gt;');

const profile = {{
  id: "web_rgb230",
  name: "Web <gris>",
  enabled: true,
  format: "JPG",
  naming: "{{folder}}_{{index:03d}}_{{original}}{{suffix}}",
  suffix: "_PRO",
}};

const heading = helpers.outputProfileEditorHeadingHtml({{
  profile,
  validation: {{ errors: [] }},
  dirty: false,
  active: true,
  summary: "JPG · 1800x2400",
}});
assert.equal(heading.includes("Formato editado"), true);
assert.equal(heading.includes("Web &lt;gris&gt;"), true);
assert.equal(heading.includes("Activo en este lote · Principal"), true);
assert.equal(heading.includes('status-badge ready'), true);

const invalidHeading = helpers.outputProfileEditorHeadingHtml({{
  profile,
  validation: {{ errors: ["Destino requerido"] }},
  dirty: true,
  active: false,
  summary: "PNG",
}});
assert.equal(invalidHeading.includes("Revisar campos"), true);
assert.equal(invalidHeading.includes('status-badge error'), true);

const preview = helpers.outputProfilePreviewHtml({{
  originalName: 'camisa "azul".png',
  resultName: "Lote_007_camisa_PRO.jpg",
  resultPath: "C:/Export/Lote_007_camisa_PRO.jpg",
  destination: "C:/Export",
  summary: "JPG · RGB230",
}});
assert.equal(preview.includes("camisa &quot;azul&quot;.png"), true);
assert.equal(preview.includes("C:/Export/Lote_007_camisa_PRO.jpg"), true);

const validationHtml = helpers.outputProfileValidationHtml({{
  errors: ["Formato invalido"],
  warnings: ["Falta {{original}}"],
}});
assert.equal(validationHtml.includes("Revisa el formato"), true);
assert.equal(validationHtml.includes('class="error"'), true);
assert.equal(validationHtml.includes('class="warning"'), true);

const emptyValidation = helpers.outputProfileValidationHtml({{ errors: [], warnings: [] }});
assert.equal(emptyValidation, "");

const row = helpers.outputProfileManagerRowHtml({{
  profile,
  selected: true,
  active: true,
  enabled: true,
  unsaved: false,
  canToggle: false,
  summary: "JPG · 1800x2400",
  destination: "_SALIDA_PRO",
}});
assert.equal(row.includes("output-profile-option selected active enabled"), true);
assert.equal(row.includes("disabled"), true);
assert.equal(row.includes("Principal"), true);
assert.equal(row.includes("Web &lt;gris&gt;"), true);

const name = helpers.outputNameFromTemplate(profile, {{
  original: "camisa",
  folder: "Lote Junio",
  index: 7,
}});
assert.equal(name, "Lote Junio_007_camisa_PRO.jpg");
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
