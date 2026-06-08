import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "preview-state.js"
INDEX_PATH = FRONTEND_DIR / "index.html"


def test_preview_state_helper_loads_before_app_script():
    html = INDEX_PATH.read_text(encoding="utf-8")

    preview_state_index = html.index("preview-state.js")
    app_index = html.index("app.js")

    assert preview_state_index < app_index


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_preview_state_helpers_keep_viewer_and_preview_contracts():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

assert.equal(helpers.isAutoViewerMode("fit"), true);
assert.equal(helpers.isAutoViewerMode("height"), true);
assert.equal(helpers.isAutoViewerMode("width"), true);
assert.equal(helpers.isAutoViewerMode("manual"), false);

const labels = {{ fit: "Encajar", height: "Alto", width: "Ancho", manual: "Manual" }};
assert.equal(helpers.viewerModeLabel("height", labels), "Alto");
assert.equal(helpers.viewerModeLabel("unknown", labels), "Manual");
assert.equal(helpers.viewerModeClass("fit"), "fit-mode");
assert.equal(helpers.viewerModeClass("height"), "fit-height-mode");
assert.equal(helpers.viewerModeClass("width"), "fit-width-mode");
assert.equal(helpers.viewerModeClass("manual"), "zoom-mode");

assert.equal(helpers.clampViewerZoom(12), 25);
assert.equal(helpers.clampViewerZoom(101.6), 102);
assert.equal(helpers.clampViewerZoom(500), 320);

assert.deepEqual(helpers.previewLoadingState(), {{
  previewStatus: "loading",
  statusText: "Generando vista",
  previewData: null,
  previewError: "",
}});
assert.deepEqual(helpers.previewLoadingState({{ statusText: "Restaurando vista", clearData: false }}), {{
  previewStatus: "loading",
  statusText: "Restaurando vista",
}});
assert.deepEqual(helpers.previewEmptyState(), {{
  previewStatus: "empty",
  previewData: null,
  previewError: "",
}});
assert.deepEqual(helpers.previewImageStatusState("error"), {{
  previewStatus: "error",
  statusText: "Vista no disponible",
}});
assert.deepEqual(helpers.previewImageStatusState("error", {{ errorAsReady: true }}), {{
  previewStatus: "ready",
  statusText: "Vista lista",
}});
assert.deepEqual(helpers.previewImageStatusState("warning"), {{
  previewStatus: "warning",
  statusText: "Vista lista",
}});
assert.deepEqual(helpers.previewBridgeResultState({{ src: "data" }}, ""), {{
  previewData: {{ src: "data" }},
  previewStatus: "ready",
  statusText: "Vista lista",
}});
assert.deepEqual(helpers.previewBridgeResultState({{ src: "data" }}, "fallback"), {{
  previewData: {{ src: "data" }},
  previewStatus: "warning",
  statusText: "Vista con aviso",
}});
assert.deepEqual(helpers.previewErrorState("timeout"), {{
  previewStatus: "error",
  previewData: null,
  previewError: "timeout",
  statusText: "Vista no disponible",
}});

assert.equal(helpers.bridgePreviewMeta({{ previewStatus: "loading" }}), "Generando vista");
assert.equal(helpers.bridgePreviewMeta({{ previewStatus: "error", previewError: "" }}), "Vista no disponible");
assert.equal(helpers.bridgePreviewMeta({{ previewStatus: "ready", previewData: {{ warning: "fallback" }}, activePreset: "Luz" }}), "Vista con aviso");
assert.equal(helpers.bridgePreviewMeta({{ previewStatus: "ready", previewData: {{}}, activePreset: "Luz" }}), "Luz");
assert.equal(helpers.bridgePreviewMeta({{ previewStatus: "empty" }}), "Vista pendiente");

assert.equal(helpers.previewSettingsLabel({{ bridgeMode: "bridge", activePresetSource: "bridge", presetDirty: false }}), "Salida");
assert.equal(helpers.previewSettingsLabel({{ bridgeMode: "bridge", activePresetSource: "bridge", presetDirty: true }}), "Aspecto modificado");
assert.equal(helpers.previewSettingsLabel({{ bridgeMode: "mock", activePresetSource: "mock", presetDirty: false }}), "Aspecto");

assert.equal(helpers.previewModeLabel("original"), "Original");
assert.equal(helpers.previewModeLabel("compare"), "Comparación");
assert.equal(helpers.previewModeLabel("processed"), "Vista");

assert.equal(helpers.previewOrientation(null), "portrait");
assert.equal(helpers.previewOrientation({{ width: 1000, height: 1400 }}), "portrait");
assert.equal(helpers.previewOrientation({{ width: 1400, height: 1000 }}), "landscape");
assert.equal(helpers.previewOrientation({{ width: 1000, height: 1000 }}), "square");

assert.equal(helpers.previewFooterLabel({{ selectedImageSource: "bridge", previewStatus: "ready" }}), "Real");
assert.equal(helpers.previewFooterLabel({{ selectedImageSource: "bridge", previewStatus: "empty" }}), "Pendiente");
assert.equal(helpers.previewFooterLabel({{ selectedImageSource: "mock", previewStatus: "ready" }}), "Lista");
assert.equal(helpers.previewFooterLabel({{ selectedImageSource: "mock", previewStatus: "empty" }}), "Sin imagen");
assert.equal(helpers.previewFooterLabel({{ selectedImageSource: "mock", previewStatus: "warning" }}), "Con aviso");
assert.equal(helpers.previewFooterLabel({{ selectedImageSource: "mock", previewStatus: "error" }}), "Error");

assert.equal(helpers.previewSubtitle({{
  hasImage: false,
  filterIsEmpty: true,
  filterEmptyDetail: "Filtro sin resultados",
}}), "Filtro sin resultados");
assert.equal(helpers.previewSubtitle({{ hasImage: false, batch: "none" }}), "Sin lote");
assert.equal(helpers.previewSubtitle({{ hasImage: false, batch: "empty", scanStatus: "" }}), "No hay PNG válidos");
assert.equal(helpers.previewSubtitle({{ hasImage: false, batch: "empty", scanStatus: "Sin compatibles" }}), "Sin compatibles");
assert.equal(helpers.previewSubtitle({{ hasImage: false, batch: "scanning", scanStatus: "" }}), "Escaneando");
assert.equal(helpers.previewSubtitle({{ hasImage: false, batch: "ready" }}), "Sin selección");

assert.equal(helpers.previewSubtitle({{
  hasImage: true,
  imageSource: "bridge",
  previewStatus: "loading",
}}), "Generando vista");
assert.equal(helpers.previewSubtitle({{
  hasImage: true,
  imageSource: "bridge",
  previewStatus: "warning",
}}), "Vista con aviso");
assert.equal(helpers.previewSubtitle({{
  hasImage: true,
  imageSource: "bridge",
  previewStatus: "error",
}}), "Vista no disponible");
assert.equal(helpers.previewSubtitle({{
  hasImage: true,
  imageSource: "bridge",
  previewStatus: "ready",
}}), "Vista generada");
assert.equal(helpers.previewSubtitle({{
  hasImage: true,
  imageSource: "bridge",
  previewStatus: "empty",
}}), "Vista pendiente");

assert.equal(helpers.previewSubtitle({{
  hasImage: true,
  imageSource: "mock",
  previewStatus: "loading",
  imageDetail: "Detalle",
}}), "Generando vista");
assert.equal(helpers.previewSubtitle({{
  hasImage: true,
  imageSource: "mock",
  previewStatus: "warning",
  imageDetail: "Detalle",
}}), "Vista con aviso");
assert.equal(helpers.previewSubtitle({{
  hasImage: true,
  imageSource: "mock",
  previewStatus: "error",
  imageDetail: "Detalle",
}}), "Vista no disponible");
assert.equal(helpers.previewSubtitle({{
  hasImage: true,
  imageSource: "mock",
  previewStatus: "ready",
  imageDetail: "Detalle",
}}), "Vista generada");
assert.equal(helpers.previewSubtitle({{
  hasImage: true,
  imageSource: "mock",
  previewStatus: "empty",
  imageDetail: "1800x2400",
}}), "1800x2400");
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
