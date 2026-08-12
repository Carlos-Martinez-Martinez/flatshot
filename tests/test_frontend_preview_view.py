import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "preview-view.js"
INDEX_PATH = FRONTEND_DIR / "index.html"
APP_PATH = FRONTEND_DIR / "app.js"
VIEWER_TOOLBAR_CSS_PATH = FRONTEND_DIR / "css" / "05-viewer" / "viewer-toolbar.css"
CANVAS_CSS_PATH = FRONTEND_DIR / "css" / "05-viewer" / "canvas.css"
VIEWER_SHELL_CSS_PATH = FRONTEND_DIR / "css" / "05-viewer" / "viewer-shell.css"
INSPECTOR_WORKFLOW_CSS_PATH = FRONTEND_DIR / "css" / "06-inspector-export" / "inspector-workflow.css"


def app_domain_source():
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in [APP_PATH, *sorted(FRONTEND_DIR.glob("app-*.js"))]
        if path.name != "app-state.js"
    )


def test_preview_view_helper_loads_before_app_script():
    html = INDEX_PATH.read_text(encoding="utf-8")

    helper_index = html.index("preview-view.js")
    app_index = html.index("app.js")

    assert helper_index < app_index


def test_preview_toolbar_keeps_compact_context_labels():
    html = INDEX_PATH.read_text(encoding="utf-8")
    app_js = app_domain_source()

    for label in ("Fondo", "Guías", "Imagen", "Encajar", "Zoom"):
        assert f'class="viewer-control-label">{label}</span>' in html
    assert 'data-preview-bg="soft-black"' in html
    assert 'data-preview-bg="custom"' in html
    custom_control = html[html.index('data-rgb-visual-control="preview-background"'):html.index('id="preview-output-context"')]
    assert 'data-rgb-visual-format="rgb-background"' in custom_control
    assert 'id="preview-bg-custom-value" type="hidden"' in custom_control
    assert 'id="preview-bg-color-input" type="color"' in html
    assert 'data-preview-bg-picker' in html
    assert 'data-rgb-visual-picker-trigger' in html
    assert 'data-rgb-visual-picker' in html
    assert 'data-preview-bg-channel=' not in custom_control
    assert 'data-rgb-visual-channel=' not in custom_control
    assert "openRgbVisualPicker" in app_js
    assert "applyPreviewBackgroundPickerChange" in app_js
    assert "renderPreview();" in app_js
    assert "customFields.classList.toggle(\"active\"" in app_js
    assert ">Gris</button>" not in html
    assert ">Blanco</button>" not in html
    assert ">Transparente</button>" not in html
    assert html.index("background-presets.js") < html.index("app.js")
    assert "backgroundPresetHelpers.normalizePreviewBackgroundValue" in app_js
    assert "function previewCustomBackgroundValue" in app_js
    assert 'bgTarget.dataset.previewBg === "custom" ? previewCustomBackgroundValue()' in app_js
    assert 'data-action="zoom-fit"' not in html
    assert 'data-action="zoom-fit" title="Encajar' not in html
    assert 'data-action="zoom-100"' not in html
    assert ">1:1</button>" not in html


def test_preview_rgb230_swatch_uses_real_light_background_color():
    css = VIEWER_TOOLBAR_CSS_PATH.read_text(encoding="utf-8")

    assert '.viewer-background-switch [data-preview-bg="rgb230"]::before' in css
    rgb230_rule = css.split('.viewer-background-switch [data-preview-bg="rgb230"]::before {', 1)[1].split("}", 1)[0]
    assert "background: var(--rgb-neutral-fallback);" in rgb230_rule


def test_preview_rgb230_canvas_uses_real_light_background_color():
    css = CANVAS_CSS_PATH.read_text(encoding="utf-8")

    assert ".canvas-area.bg-rgb230 .preview-canvas" in css
    rgb230_rule = css.split(".canvas-area.bg-rgb230 .preview-canvas {", 1)[1].split("}", 1)[0]
    assert "background: var(--rgb-neutral-fallback);" in rgb230_rule
    assert "background: var(--color-bg-stage);" not in rgb230_rule


def test_preview_background_and_guides_are_bounded_to_portrait_workspace():
    css = CANVAS_CSS_PATH.read_text(encoding="utf-8")

    canvas_rule = re.search(r"(?m)^\.preview-canvas\s*\{([^}]*)\}", css).group(1)
    guide_rule = css.split(".guide-overlay {", 1)[1].split("}", 1)[0]

    assert "width: min(100%, 920px);" in canvas_rule
    assert "width: min(100%, 920px);" in guide_rule
    assert "left: 50%;" in guide_rule
    assert "transform: translateX(-50%);" in guide_rule


def test_initial_canvas_uses_app_background_instead_of_preview_background():
    css = CANVAS_CSS_PATH.read_text(encoding="utf-8")

    assert '.app-shell[data-ui-state="no_folder"] .canvas-area' in css
    initial_rule = css.split('.app-shell[data-ui-state="no_folder"] .canvas-area {', 1)[1].split("}", 1)[0]
    assert "background: var(--color-bg);" in initial_rule
    assert "--rgb-neutral-fallback" not in initial_rule


def test_empty_batch_places_viewer_in_primary_column_with_a_neutral_canvas():
    viewer_css = VIEWER_SHELL_CSS_PATH.read_text(encoding="utf-8")
    canvas_css = CANVAS_CSS_PATH.read_text(encoding="utf-8")
    inspector_css = INSPECTOR_WORKFLOW_CSS_PATH.read_text(encoding="utf-8")
    empty_selector = '.app-shell:is([data-ui-state="batch_empty"], [data-ui-state="scan_empty"])'

    panel_selector = f"{empty_selector} .preview-panel {{"
    assert panel_selector in viewer_css
    panel_rule = viewer_css.split(panel_selector, 1)[1].split("}", 1)[0]
    assert "grid-column: 1;" in panel_rule

    toolbar_selector = f"{empty_selector} .preview-toolbar {{"
    assert toolbar_selector in viewer_css
    toolbar_rule = viewer_css.split(toolbar_selector, 1)[1].split("}", 1)[0]
    assert "display: none;" in toolbar_rule

    canvas_selector = f"{empty_selector} .canvas-area {{"
    assert canvas_selector in canvas_css
    canvas_rule = canvas_css.split(canvas_selector, 1)[1].split("}", 1)[0]
    assert "background: var(--color-bg-stage);" in canvas_rule

    inspector_selector = f"{empty_selector} .settings-panel {{"
    assert inspector_selector in inspector_css
    inspector_rule = inspector_css.split(inspector_selector, 1)[1].split("}", 1)[0]
    assert "grid-column: 2;" in inspector_rule


def test_preview_render_preserves_onboarding_background_layer():
    source = (FRONTEND_DIR / "app-preview-controller.js").read_text(encoding="utf-8")

    assert "function setPreviewCanvasHtml(" in source
    assert 'canvas.querySelector("#onboarding-background")' in source
    assert "canvas.prepend(onboardingLayer);" in source


def test_empty_batch_preview_offers_folder_recovery_action():
    source = (FRONTEND_DIR / "app-preview-controller.js").read_text(encoding="utf-8")
    empty_branch = source.split('if (state.batch === "empty") {', 1)[1].split("finishPreviewRender();", 1)[0]

    assert 'variant: "batch-empty"' in empty_branch
    assert 'actionLabel: "Elegir otra carpeta"' in empty_branch
    assert 'action: "pick-bridge-folder"' in empty_branch


def test_compare_mode_has_draggable_divider_wiring():
    app_js = app_domain_source()
    canvas_css = (FRONTEND_DIR / "css" / "05-viewer" / "canvas.css").read_text(encoding="utf-8")

    assert "compareSplit: 50" in app_js
    assert "compareDividerDrag" in app_js
    assert "previewViewHelpers.compareDividerHtml" in app_js
    assert "handleCompareDividerPointerDown(event)" in app_js
    assert "updateCompareDividerFromPointer(event)" in app_js
    assert "data-compare-divider" in app_js
    assert "--compare-split" in canvas_css
    assert ".compare-divider" in canvas_css


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_preview_view_renders_canvas_state_contracts():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

assert.equal(helpers.escapeHtml('<a&b"c>'), '&lt;a&amp;b&quot;c&gt;');

const loading = helpers.previewLoadingHtml('camisa <azul>.png');
assert.equal(loading.includes('class="preview-state"'), true);
assert.equal(loading.includes('Generando vista'), true);
assert.equal(loading.includes('camisa &lt;azul&gt;.png'), true);

const scanning = helpers.scanningStateHtml('Leyendo "PNG"');
assert.equal(scanning.includes('scanning-state'), true);
assert.equal(scanning.includes('Escaneando carpeta...'), true);
assert.equal(scanning.includes('Leyendo &quot;PNG&quot;'), true);

const image = helpers.realPreviewImageHtml({{
  src: 'http://127.0.0.1/preview?name=<uno>',
  imageName: 'foto "uno".png',
  width: 1200,
  height: 800,
  zoom: 50,
  warning: 'Render <fallback>',
}});
assert.equal(image.includes('class="preview-image"'), true);
assert.equal(image.includes('src="http://127.0.0.1/preview?name=&lt;uno&gt;"'), true);
assert.equal(image.includes('alt="Vista previa de foto &quot;uno&quot;.png"'), true);
assert.equal(image.includes('style="width: 600px; height: 400px;" width="1200" height="800"'), true);
assert.equal(image.includes('Render &lt;fallback&gt;'), true);

const imageWithoutSize = helpers.realPreviewImageHtml({{
  src: 'data:image/png;base64,abc',
  imageName: 'sin-medidas.png',
  width: 0,
  height: 0,
  zoom: 200,
}});
assert.equal(imageWithoutSize.includes('style="width:'), false);
assert.equal(imageWithoutSize.includes('preview-warning-card'), false);

const imageAutoSize = helpers.realPreviewImageHtml({{
  src: 'data:image/png;base64,abc',
  imageName: 'auto.png',
  width: 1200,
  height: 800,
  zoom: 80,
  inlineSize: false,
}});
assert.equal(imageAutoSize.includes('style="width:'), false);
assert.equal(imageAutoSize.includes('width="1200" height="800"'), true);

const placeholder = helpers.realPreviewPlaceholderHtml({{
  imageName: 'pendiente <uno>.png',
  imagePath: 'C:/Entrada/"uno".png',
}});
assert.equal(placeholder.includes('real-preview-placeholder'), true);
assert.equal(placeholder.includes('pendiente &lt;uno&gt;.png'), true);
assert.equal(placeholder.includes('C:/Entrada/&quot;uno&quot;.png'), true);

const mock = helpers.mockPreviewHtml({{ warning: 'Render con "fallback"' }});
assert.equal(mock.includes('class="mock-product"'), true);
assert.equal(mock.includes('class="mock-shadow"'), true);
assert.equal(mock.includes('Render con &quot;fallback&quot;'), true);

const mockWithoutWarning = helpers.mockPreviewHtml();
assert.equal(mockWithoutWarning.includes('preview-warning-card'), false);

assert.equal(helpers.viewerOutputCompactLabel({{
  format: "PNG",
  sizeLabel: "1200×1600",
  backgroundLabel: "transparente",
}}), "PNG · 1200×1600 · transparente");
assert.equal(helpers.viewerOutputCompactLabel({{}}), "JPG · 1800×2400 · gris claro");

const outputContext = helpers.viewerOutputContextHtml({{
  name: 'Web <gris>',
  summary: 'JPG · 1800×2400 · "RGB230"',
}});
assert.equal(outputContext.includes("<span>Previsualizando</span>"), true);
assert.equal(outputContext.includes("<strong>Web &lt;gris&gt;</strong>"), true);
assert.equal(outputContext.includes("JPG · 1800×2400 · &quot;RGB230&quot;"), true);
assert.equal(helpers.viewerOutputContextHtml({{ name: "", summary: "" }}), "");
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
