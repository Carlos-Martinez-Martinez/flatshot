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

assert.equal(helpers.outputNameForImage({{
  naming: "",
  suffix: "_PRO",
  format: "JPG",
  image: {{ name: "camisa.png" }},
  folders: [{{ id: "folder-a", name: "Lote A" }}],
  index: 4,
}}), "Nombre de archivo pendiente");
assert.equal(helpers.outputNameForImage({{
  naming: "{{folder}}_{{index:02d}}_{{original}}{{suffix}}",
  suffix: "_WEB",
  format: "PNG",
  image: {{ name: "C:/Fotos/camisa.azul.png", folderId: "folder-b" }},
  folders: [
    {{ id: "folder-a", name: "Lote A" }},
    {{ id: "folder-b", name: "Lote B" }},
  ],
  index: 4,
}}), "Lote B_04_camisa.azul_WEB.png");
assert.equal(helpers.outputNameForImage({{
  naming: "{{folder}}_{{original}}{{suffix}}",
  suffix: "",
  format: "JPG",
  image: {{ name: "camisa.png", folderId: "missing" }},
  folders: [{{ id: "folder-a", name: "Lote A" }}],
}}), "Lote A_camisa_PRO.jpg");
assert.equal(helpers.outputNameForImage({{
  naming: "{{folder}}_{{original}}{{suffix}}",
  suffix: "",
  format: "JPG",
  image: {{}},
  folders: [],
}}), "lote_imagen_001_PRO.jpg");
assert.equal(helpers.outputNameForImage({{
  naming: "{{original}}.webp",
  suffix: "_PRO",
  format: "JPG",
  image: {{ name: "camisa.png" }},
  folders: [],
}}), "camisa.webp");

assert.equal(helpers.outputNameForProfile(profile, {{
  image: {{ name: "C:/Fotos/camisa.azul.png", folderId: "folder-b" }},
  folders: [
    {{ id: "folder-a", name: "Lote A" }},
    {{ id: "folder-b", name: "Lote B" }},
  ],
  index: 8,
}}), "Lote B_008_camisa.azul_PRO.jpg");
assert.equal(helpers.outputNameForProfile({{
  naming: "{{folder}}_{{original}}{{suffix}}",
  suffix: "",
  format: "PNG",
}}, {{
  folders: [],
}}), "lote_imagen_original.png");

assert.equal(helpers.destinationCompactLabel({{
  destinationMode: "custom",
  destinationValue: "",
}}), "Sin destino");
assert.equal(helpers.destinationCompactLabel({{
  destinationMode: "custom",
  destinationValue: "C:/Export",
}}), "C:/Export");
assert.equal(helpers.destinationCompactLabel({{
  destinationMode: "source",
  destinationValue: "",
}}), "_SALIDA_PRO");
assert.equal(helpers.destinationCompactLabel({{
  destinationMode: "source",
  destinationValue: "SALIDA",
}}), "SALIDA");

assert.equal(helpers.profileDestinationLabel(null), "Sin destino");
assert.equal(helpers.profileDestinationLabel({{
  destinationMode: "custom",
  destinationValue: "",
}}), "Carpeta personalizada");
assert.equal(helpers.profileDestinationLabel({{
  destinationMode: "custom",
  destinationValue: "C:/Export",
}}), "C:/Export");
assert.equal(helpers.profileDestinationLabel({{
  destinationMode: "source",
  destinationValue: "",
}}), "_SALIDA_PRO");
assert.equal(helpers.profileDestinationPreviewLabel({{
  destinationMode: "custom",
  destinationValue: "",
}}), "Carpeta personalizada");
assert.equal(helpers.profileDestinationPreviewLabel({{
  destinationMode: "source",
  destinationValue: "WEB",
}}), "WEB");

assert.equal(helpers.namingHumanLabel({{
  naming: "{{original}}{{suffix}}",
  suffix: "_PRO",
}}), "original + _PRO");
assert.equal(helpers.namingHumanLabel({{
  naming: "{{original}}{{suffix}}",
  suffix: "",
}}), "original");
assert.equal(helpers.namingHumanLabel({{
  naming: "{{folder}}_{{index:02d}}",
  suffix: "_PRO",
}}), "{{folder}}_{{index:02d}}");
assert.equal(helpers.namingHumanLabel({{
  naming: "",
  suffix: "_PRO",
}}), "Sin plantilla");

assert.equal(helpers.namingExample({{
  naming: "",
  suffix: "_PRO",
  format: "JPG",
  original: "camisa",
  folder: "Lote",
}}), "Sin ejemplo");
assert.equal(helpers.namingExample({{
  naming: "{{folder}}_{{index:02d}}_{{original}}{{suffix}}",
  suffix: "_PRO",
  format: "PNG",
  original: "camisa",
  folder: "Lote",
  index: 3,
}}), "Lote_03_camisa_PRO.png");
assert.equal(helpers.namingExample({{
  naming: "{{original}}.webp",
  suffix: "_PRO",
  format: "JPG",
  original: "camisa",
  folder: "Lote",
}}), "camisa.webp");

assert.equal(helpers.destinationFallbackLabel({{
  destinationMode: "custom",
  destinationValue: "",
  destinations: [],
}}), "Carpeta de salida sin configurar");
assert.equal(helpers.destinationFallbackLabel({{
  destinationMode: "custom",
  destinationValue: "C:/Export",
  destinations: [],
}}), "C:/Export");
assert.equal(helpers.destinationFallbackLabel({{
  destinationMode: "source",
  destinationValue: "",
  destinations: [],
}}), "_SALIDA_PRO");
assert.equal(helpers.destinationFallbackLabel({{
  destinationMode: "source",
  destinationValue: "",
  destinations: ["_SALIDA_PRO", "_SALIDA_PRO"],
}}), "_SALIDA_PRO");
assert.equal(helpers.destinationFallbackLabel({{
  destinationMode: "source",
  destinationValue: "",
  destinations: ["A", "B", "A"],
}}), "2 destinos");

assert.deepEqual(helpers.outputProfileFooterState({{
  draft: {{ enabled: true }},
  dirty: false,
  isPersisted: true,
  profileCount: 1,
  validation: {{ errors: [] }},
}}), {{
  deleteDisabled: true,
  deleteTitle: "Debe quedar al menos un formato",
  resetDisabled: true,
  saveDisabled: true,
  applyDisabled: false,
  applyLabel: "Aplicar cambios al lote",
  noteClass: "settings-footer-note ",
  noteText: "Sin cambios pendientes",
}});

assert.deepEqual(helpers.outputProfileFooterState({{
  draft: {{ enabled: false }},
  dirty: false,
  isPersisted: true,
  profileCount: 2,
  validation: {{ errors: [] }},
}}), {{
  deleteDisabled: false,
  deleteTitle: "Eliminar formato seleccionado",
  resetDisabled: true,
  saveDisabled: true,
  applyDisabled: false,
  applyLabel: "Activar en este lote",
  noteClass: "settings-footer-note ",
  noteText: "Sin cambios pendientes",
}});

assert.deepEqual(helpers.outputProfileFooterState({{
  draft: {{ enabled: true }},
  dirty: true,
  isPersisted: false,
  profileCount: 2,
  validation: {{ errors: [] }},
}}), {{
  deleteDisabled: false,
  deleteTitle: "Eliminar formato seleccionado",
  resetDisabled: false,
  saveDisabled: false,
  applyDisabled: false,
  applyLabel: "Guardar y aplicar",
  noteClass: "settings-footer-note warning",
  noteText: "Cambios sin guardar",
}});

assert.deepEqual(helpers.outputProfileFooterState({{
  draft: {{ enabled: true }},
  dirty: true,
  isPersisted: true,
  profileCount: 2,
  validation: {{ errors: ["Nombre requerido"] }},
}}), {{
  deleteDisabled: false,
  deleteTitle: "Eliminar formato seleccionado",
  resetDisabled: false,
  saveDisabled: true,
  applyDisabled: true,
  applyLabel: "Guardar y aplicar",
  noteClass: "settings-footer-note error",
  noteText: "Nombre requerido",
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
