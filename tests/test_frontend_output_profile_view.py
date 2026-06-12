import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "output-profile-view.js"
INDEX_PATH = FRONTEND_DIR / "index.html"
APP_PATH = FRONTEND_DIR / "app.js"


def test_output_profile_view_helper_loads_before_app_script():
    html = INDEX_PATH.read_text(encoding="utf-8")

    helper_index = html.index("output-profile-view.js")
    app_index = html.index("app.js")

    assert helper_index < app_index


def test_output_profile_delete_uses_in_app_confirmation():
    html = INDEX_PATH.read_text(encoding="utf-8")
    app_js = APP_PATH.read_text(encoding="utf-8")

    delete_start = app_js.index("function deleteManagedOutputProfile()")
    delete_end = app_js.index("function resetOutputProfileDraft()", delete_start)
    delete_block = app_js[delete_start:delete_end]

    assert 'id="output-delete-confirm"' in html
    assert 'data-action="confirm-output-delete"' in html
    assert 'data-action="cancel-output-delete"' in html
    assert "is-confirming-delete" in app_js
    assert "function confirmDeleteManagedOutputProfile()" in delete_block
    assert "window.confirm" not in delete_block


def test_background_preset_editor_stays_with_background_controls():
    html = INDEX_PATH.read_text(encoding="utf-8")
    app_js = APP_PATH.read_text(encoding="utf-8")

    image_section_index = html.index('class="format-form-section format-section-image"')
    editor_index = html.index('id="background-preset-editor"')
    preview_index = html.index('id="output-profile-preview"')
    footer_index = html.index('<footer class="app-settings-footer">', preview_index)
    form_end_index = html.index("</form>")

    assert image_section_index < preview_index < form_end_index < footer_index < editor_index
    assert "format-footer-workbench" not in html
    assert "<span>Nombre</span>" in html
    assert "Nombre del fondo" not in html
    assert 'id="background-preset-swatch"' in html
    assert 'class="background-preset-editor-fields"' in html
    assert "summary.hidden = Boolean(editorState)" not in app_js
    assert "preview.hidden = Boolean(editorState)" not in app_js
    assert "workbench.classList.toggle(\"is-editing-background\"" not in app_js
    assert "function positionBackgroundPresetEditor()" in app_js
    assert "editor.style.left" in app_js
    assert "editor.classList.toggle(\"is-transparent\"" in app_js
    assert "editorFields" not in app_js
    assert "swatch.classList.toggle(\"is-transparent\"" in app_js
    assert "Muestra del fondo RGB" in app_js


def test_transparent_background_switches_output_type_before_validation():
    app_js = APP_PATH.read_text(encoding="utf-8")

    update_start = app_js.index("function updateOutputProfileDraftFromForm()")
    update_end = app_js.index("function setOutputProfileDraftEnabled", update_start)
    update_block = app_js[update_start:update_end]

    assert "function syncTransparentBackgroundFormat()" in update_block
    assert update_block.index("syncTransparentBackgroundFormat();") < update_block.index("outputProfileDraftFromForm();")
    assert 'formatInput.value = "PNG";' in update_block


def test_destination_mode_clears_custom_path_before_validation():
    app_js = APP_PATH.read_text(encoding="utf-8")

    update_start = app_js.index("function updateOutputProfileDraftFromForm()")
    update_end = app_js.index("function setOutputProfileDraftEnabled", update_start)
    update_block = app_js[update_start:update_end]

    assert "function syncOutputProfileDestinationMode()" in update_block
    assert update_block.index("syncOutputProfileDestinationMode();") < update_block.index("outputProfileDraftFromForm();")
    assert "function looksLikeAbsoluteOutputPath" in update_block
    assert 'destinationInput.value = "Salida";' in update_block
    assert "readPersistentValue(STORAGE_KEYS.lastOutputFolder)" in update_block


def test_custom_destination_can_pick_folder_from_bridge():
    html = INDEX_PATH.read_text(encoding="utf-8")
    app_js = APP_PATH.read_text(encoding="utf-8")

    assert 'id="profile-destination-value-label"' in html
    assert 'data-action="pick-output-profile-destination"' in html
    assert "function pickOutputProfileDestination()" in app_js
    assert 'bridgeRequest("/folders/pick"' in app_js
    assert 'modeInput.value = "custom";' in app_js
    assert 'destinationLabel.textContent = raw.destinationMode === "custom" ? "Carpeta" : "Subcarpeta";' in app_js


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
  enabled: true,
  isPersisted: true,
  summary: "JPG · 1800x2400",
}});
assert.equal(heading.includes("Formato seleccionado"), true);
assert.equal(heading.includes("Web &lt;gris&gt;"), true);
assert.equal(heading.includes("Usar en este lote"), true);
assert.equal(heading.includes("data-output-profile-draft-enabled"), true);
assert.equal(heading.includes("En lote"), false);
assert.equal(heading.includes("Principal"), false);
assert.equal(heading.includes("Editado"), false);
assert.equal(heading.includes("Activo en este lote"), false);
assert.equal(heading.includes('status-badge ready'), false);
assert.equal(helpers.outputProfileEditorHeadingHtml({{
  profile: {{ name: "Nuevo formato" }},
  validation: {{ errors: [] }},
  enabled: false,
  isPersisted: false,
  new: true,
}}).includes("Formato nuevo"), false);

const invalidHeading = helpers.outputProfileEditorHeadingHtml({{
  profile,
  validation: {{ errors: ["Destino requerido"] }},
  dirty: true,
  enabled: false,
  isPersisted: true,
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
assert.equal(preview.includes("Resultado"), true);
assert.equal(preview.includes("<code"), true);

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
  enabled: true,
  dirty: false,
  new: false,
  unsaved: false,
  canToggle: false,
  summary: "JPG · 1800x2400",
  destination: "Salida",
}});
assert.equal(row.includes("output-profile-option selected enabled"), true);
assert.equal(row.includes("output-profile-status-badge"), false);
assert.equal(row.includes("data-output-profile-enabled-id"), false);
assert.equal(row.includes("disabled"), false);
assert.equal(row.includes("Usar"), false);
assert.equal(row.includes("Usar en este lote"), false);
assert.equal(row.includes("En lote"), false);
assert.equal(row.includes("Principal"), false);
assert.equal(row.includes("Activo"), false);
assert.equal(row.includes("Editado"), false);
assert.equal(row.includes("Nuevo"), false);
assert.equal(row.includes("Web &lt;gris&gt;"), true);

const dirtyRow = helpers.outputProfileManagerRowHtml({{
  profile,
  selected: true,
  enabled: true,
  dirty: true,
}});
assert.equal(dirtyRow.includes("output-profile-option selected enabled is-unsaved"), true);
assert.equal(dirtyRow.includes("output-profile-unsaved-dot"), false);
assert.equal(dirtyRow.includes("Cambios sin guardar"), true);
assert.equal(dirtyRow.includes("Editado"), false);

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
}}), "Salida");
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
}}), "Salida");
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
}}), "Salida");
assert.equal(helpers.destinationFallbackLabel({{
  destinationMode: "source",
  destinationValue: "",
  destinations: ["Salida", "Salida"],
}}), "Salida");
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
  closeAction: "close-app-settings",
  closeLabel: "Cerrar",
  closeHidden: true,
  deleteDisabled: true,
  deleteTitle: "Debe quedar al menos un formato",
  resetDisabled: true,
  resetHidden: true,
  resetLabel: "Descartar",
  saveDisabled: true,
  saveHidden: true,
  saveLabel: "Guardar cambios",
  noteClass: "settings-footer-note ",
  noteText: "Cambios guardados",
}});

assert.deepEqual(helpers.outputProfileFooterState({{
  draft: {{ enabled: false }},
  dirty: false,
  isPersisted: true,
  profileCount: 2,
  validation: {{ errors: [] }},
}}), {{
  closeAction: "close-app-settings",
  closeLabel: "Cerrar",
  closeHidden: true,
  deleteDisabled: false,
  deleteTitle: "Eliminar formato seleccionado",
  resetDisabled: true,
  resetHidden: true,
  resetLabel: "Descartar",
  saveDisabled: true,
  saveHidden: true,
  saveLabel: "Guardar cambios",
  noteClass: "settings-footer-note ",
  noteText: "Cambios guardados",
}});

assert.deepEqual(helpers.outputProfileFooterState({{
  draft: {{ enabled: true }},
  dirty: true,
  isPersisted: false,
  profileCount: 2,
  validation: {{ errors: [] }},
}}), {{
  closeAction: "cancel-output-profile-draft",
  closeLabel: "Cancelar",
  closeHidden: false,
  deleteDisabled: false,
  deleteTitle: "Descartar formato nuevo",
  resetDisabled: true,
  resetHidden: true,
  resetLabel: "Descartar",
  saveDisabled: false,
  saveHidden: false,
  saveLabel: "Guardar cambios",
  noteClass: "settings-footer-note warning",
  noteText: "Formato nuevo sin guardar",
}});

assert.deepEqual(helpers.outputProfileFooterState({{
  draft: {{ enabled: true }},
  dirty: true,
  isPersisted: true,
  noticeText: "Guarda o descarta los cambios antes de cambiar de formato.",
  profileCount: 2,
  validation: {{ errors: [] }},
}}), {{
  closeAction: "close-app-settings",
  closeLabel: "Cerrar",
  closeHidden: true,
  deleteDisabled: false,
  deleteTitle: "Eliminar formato seleccionado",
  resetDisabled: false,
  resetHidden: false,
  resetLabel: "Descartar",
  saveDisabled: false,
  saveHidden: false,
  saveLabel: "Guardar cambios",
  noteClass: "settings-footer-note warning",
  noteText: "Guarda o descarta los cambios antes de cambiar de formato.",
}});

assert.deepEqual(helpers.outputProfileFooterState({{
  draft: {{ enabled: true }},
  dirty: true,
  isPersisted: true,
  profileCount: 2,
  validation: {{ errors: ["Nombre requerido"] }},
}}), {{
  closeAction: "close-app-settings",
  closeLabel: "Cerrar",
  closeHidden: true,
  deleteDisabled: false,
  deleteTitle: "Eliminar formato seleccionado",
  resetDisabled: false,
  resetHidden: false,
  resetLabel: "Descartar",
  saveDisabled: true,
  saveHidden: false,
  saveLabel: "Guardar cambios",
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
