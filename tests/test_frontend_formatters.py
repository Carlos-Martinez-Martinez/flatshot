import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "formatters.js"
INDEX_PATH = FRONTEND_DIR / "index.html"


def test_formatters_helper_loads_before_app_script():
    html = INDEX_PATH.read_text(encoding="utf-8")

    formatters_index = html.index("formatters.js")
    output_index = html.index("output-profiles.js")
    preflight_index = html.index("preflight.js")
    gallery_index = html.index("gallery.js")
    app_index = html.index("app.js")

    assert formatters_index < app_index
    assert output_index < app_index
    assert preflight_index < app_index
    assert gallery_index < app_index


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_formatters_keep_existing_text_and_path_contracts():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

assert.equal(helpers.basename("C:/lote/Camisa blanca.png"), "Camisa blanca.png");
assert.equal(helpers.basename("C:\\\\lote\\\\sub\\\\"), "sub");
assert.equal(helpers.basename(""), "");
assert.equal(helpers.displayPath("C:/lote/Export"), "Export");
assert.equal(helpers.displayPath(""), "");

assert.equal(helpers.imageFileStem("C:/lote/Camisa blanca.png"), "Camisa blanca");
assert.equal(helpers.imageFileStem("sin-extension"), "sin-extension");
assert.equal(helpers.imageFileStem(""), "Imagen");

assert.equal(helpers.imageFileType({{ name: "camisa.png" }}, "JPG"), "PNG");
assert.equal(helpers.imageFileType({{ name: "camisa", detail: "WEBP · 14 KB" }}, "JPG"), "WEBP");
assert.equal(helpers.imageFileType({{ name: "" }}, "JPG"), "JPG");

assert.equal(helpers.formatBytes(0), "0 B");
assert.equal(helpers.formatBytes(1536), "2 KB");
assert.equal(helpers.formatBytes(1572864), "1.5 MB");

assert.equal(helpers.pathToFileUrl("C:\\\\Salida Pro\\\\foto 1.jpg"), "file:///C:/Salida%20Pro/foto%201.jpg");
assert.equal(helpers.pathToFileUrl("/tmp/foto 1.png"), "file:///tmp/foto%201.png");
assert.equal(helpers.pathToFileUrl("relative/foto 1.png"), "relative/foto%201.png");

assert.equal(helpers.capabilitiesSummary(null), "Sin comprobar");
assert.equal(helpers.capabilitiesSummary({{ folderScan: true, presetsRead: true, previewRender: true, exportRun: true }}), "scan · presets · preview · export");
assert.equal(helpers.capabilitiesSummary({{}}), "Sin capacidades activas");

assert.equal(helpers.escapeHtml('<a&b"c>'), '&lt;a&amp;b&quot;c&gt;');

const dataLabel = helpers.debugUrlLabel("data:image/png;base64,abc123");
assert.equal(dataLabel, "data:image/png;base64...");
assert.equal(helpers.debugUrlLabel("x".repeat(121)), "x".repeat(117) + "...");
assert.equal(helpers.debugUrlLabel("https://local/preview.png"), "https://local/preview.png");
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
