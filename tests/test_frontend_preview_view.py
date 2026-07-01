import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "preview-view.js"
INDEX_PATH = FRONTEND_DIR / "index.html"
APP_PATH = FRONTEND_DIR / "app.js"


def test_preview_view_helper_loads_before_app_script():
    html = INDEX_PATH.read_text(encoding="utf-8")

    helper_index = html.index("preview-view.js")
    app_index = html.index("app.js")

    assert helper_index < app_index


def test_preview_toolbar_keeps_compact_context_labels():
    html = INDEX_PATH.read_text(encoding="utf-8")
    app_js = APP_PATH.read_text(encoding="utf-8")

    for label in ("Fondo", "Imagen", "Encajar", "Zoom"):
        assert f'class="viewer-control-label">{label}</span>' in html
    assert 'data-preview-bg="soft-black"' in html
    assert 'data-preview-bg="custom"' in html
    assert 'data-preview-bg-channel="r"' in html
    assert 'data-preview-bg-channel="g"' in html
    assert 'data-preview-bg-channel="b"' in html
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
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
