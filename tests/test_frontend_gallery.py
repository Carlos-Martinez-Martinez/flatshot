import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "gallery.js"
INDEX_PATH = FRONTEND_DIR / "index.html"


def test_gallery_helper_loads_before_app_script():
    html = INDEX_PATH.read_text(encoding="utf-8")

    output_index = html.index("output-profiles.js")
    preflight_index = html.index("preflight.js")
    gallery_index = html.index("gallery.js")
    app_index = html.index("app.js")

    assert output_index < app_index
    assert preflight_index < app_index
    assert gallery_index < app_index


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_gallery_helpers_keep_filter_and_search_contracts():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

const images = [
  {{ id: "a", name: "Zapato-Verde 01.png", path: "C:/lote/Zapato-Verde 01.png", status: "ready", exportable: true }},
  {{ id: "b", name: "Bolso_rojo.png", path: "C:/lote/Bolso_rojo.png", status: "warning", exportable: true }},
  {{ id: "c", name: "Camisa.png", path: "C:/lote/Camisa.png", status: "adjusted", exportable: true }},
  {{ id: "d", name: "Error.png", path: "C:/lote/Error.png", status: "error", exportable: false }},
  {{ id: "e", name: "ExportFail.png", path: "C:/lote/ExportFail.png", status: "ready", exportable: true }},
];
const exportItemStatuses = new Map([
  ["e", {{ status: "error", label: "Error" }}],
]);

assert.equal(helpers.imageFileStem("C:/lote/Zapato-Verde 01.png"), "Zapato-Verde 01");
assert.equal(helpers.imageFileStem(""), "Imagen");

const searchText = helpers.imageSearchText(images[0]);
assert.equal(searchText.includes("zapato-verde 01.png"), true);
assert.equal(searchText.includes("zapato-verde 01"), true);
assert.equal(searchText.includes("zapato"), true);
assert.equal(searchText.includes("verde"), true);
assert.equal(searchText.includes("c:/lote/zapato-verde 01.png"), true);

assert.deepEqual(
  helpers.filteredImages(images, {{ search: "verde", filter: "all", exportItemStatuses }}).map((image) => image.id),
  ["a"],
);
assert.deepEqual(
  helpers.filteredImages(images, {{ search: "", filter: "valid", exportItemStatuses }}).map((image) => image.id),
  ["a", "c", "e"],
);
assert.deepEqual(
  helpers.filteredImages(images, {{ search: "", filter: "warnings", exportItemStatuses }}).map((image) => image.id),
  ["b"],
);
assert.deepEqual(
  helpers.filteredImages(images, {{ search: "", filter: "excluded", exportItemStatuses }}).map((image) => image.id),
  ["d", "e"],
);

const counts = helpers.galleryFilterCounts(images, exportItemStatuses);
assert.deepEqual(counts, {{
  all: 5,
  valid: 3,
  warnings: 1,
  excluded: 2,
}});

assert.equal(helpers.galleryFilterVisible("all", counts), true);
assert.equal(helpers.galleryFilterVisible("valid", counts), true);
assert.equal(helpers.galleryFilterVisible("warnings", counts), true);
assert.equal(helpers.galleryFilterVisible("excluded", counts), true);
assert.equal(helpers.galleryFilterVisible("valid", {{ all: 2, valid: 2, warnings: 0, excluded: 0 }}), false);
assert.equal(helpers.galleryFilterVisible("warnings", {{ all: 2, valid: 2, warnings: 0, excluded: 0 }}), false);

assert.equal(helpers.resolveAvailableFilter("warnings", [images[0]], new Map()), "all");
assert.equal(helpers.resolveAvailableFilter("valid", images, exportItemStatuses), "valid");
assert.equal(helpers.filterDisplayName("warnings"), "con aviso");
assert.equal(helpers.filterStatusText("all"), "Mostrando todo");
assert.equal(helpers.filterStatusText("warnings"), "Mostrando con aviso");

assert.deepEqual(helpers.galleryFilterButtonStates({{
  activeFilter: "warnings",
  counts,
}}), [
  {{ filter: "all", label: "Todas", count: 5, title: "Todas 5", order: 1, active: false, empty: false, hidden: false }},
  {{ filter: "valid", label: "Listas", count: 3, title: "Listas 3", order: 2, active: false, empty: false, hidden: false }},
  {{ filter: "warnings", label: "Avisos", count: 1, title: "Avisos 1", order: 3, active: true, empty: false, hidden: false }},
  {{ filter: "excluded", label: "Excluidas", count: 2, title: "Excluidas 2", order: 4, active: false, empty: false, hidden: false }},
]);
assert.deepEqual(helpers.galleryFilterButtonStates({{
  activeFilter: "all",
  counts: {{ all: 2, valid: 2, warnings: 0, excluded: 0 }},
}}), [
  {{ filter: "all", label: "Todas", count: 2, title: "Todas 2", order: 1, active: true, empty: false, hidden: true }},
  {{ filter: "valid", label: "Listas", count: 2, title: "Listas 2", order: 2, active: false, empty: false, hidden: true }},
  {{ filter: "warnings", label: "Avisos", count: 0, title: "Avisos 0", order: 3, active: false, empty: true, hidden: true }},
  {{ filter: "excluded", label: "Excluidas", count: 0, title: "Excluidas 0", order: 4, active: false, empty: true, hidden: true }},
]);

assert.equal(helpers.escapeHtml('<a&b"c>'), "&lt;a&amp;b&quot;c&gt;");
assert.equal(helpers.filteredEmptyHtml({{ total: 0 }}), "No hay imágenes en este lote.");
assert.equal(
  helpers.filteredEmptyHtml({{ total: 5, valid: 2, warnings: 1, errors: 2, filter: "warnings" }}).includes("1 en este filtro"),
  true,
);
assert.equal(
  helpers.filteredEmptyHtml({{ total: 5, search: "zapato", filter: "all" }}).includes('No hay imágenes que coincidan con &quot;zapato&quot;.'),
  true,
);
assert.equal(
  helpers.filteredEmptyHtml({{ total: 5, search: "zapato", filter: "warnings" }}).includes("en el filtro actual"),
  true,
);
assert.equal(helpers.filterEmptyDetail({{ search: "rojo" }}), 'No hay coincidencias para "rojo".');
assert.equal(helpers.filterEmptyDetail({{ filter: "warnings" }}), "El lote no contiene imágenes con avisos.");
assert.equal(helpers.filterEmptyDetail({{ filter: "excluded" }}), "No hay imágenes excluidas de la exportación.");
assert.equal(helpers.filterEmptyDetail({{ filter: "valid" }}), "No hay imágenes listas en este filtro.");

assert.equal(
  helpers.emptyBatchNoteHtml({{ ignored: 1, ignoredSummary: "1 archivo temporal" }}).includes("Esta carpeta no contiene PNG válidos. 1 archivo temporal."),
  true,
);
assert.equal(
  helpers.emptyBatchNoteHtml({{ ignored: 0, scanStatus: "Sin compatibles" }}).includes("Sin compatibles"),
  true,
);
assert.equal(helpers.compactImageDetail("PNG · 14 KB"), "14 KB");
assert.equal(helpers.compactImageDetail("Lista"), "");
assert.equal(helpers.assetStatusLabel("ready", {{ warning: "Aviso" }}), "Lista");
assert.equal(helpers.assetStatusLabel("adjusted", {{ warning: "Aviso" }}), "Ajustada");
assert.equal(helpers.assetStatusLabel("warning", {{ warning: "Aviso" }}), "Aviso");
assert.equal(helpers.assetStatusIcon("warning"), "!");
assert.equal(helpers.assetStatusIcon("error"), "×");
assert.equal(helpers.assetStatusIcon("exported"), "✓");
assert.equal(helpers.assetStatusIcon("adjusted"), "*");

assert.deepEqual(helpers.thumbnailState({{
  src: "",
  stored: null,
}}), {{
  status: "error",
  error: "Sin preview",
}});
const storedBySrc = {{ status: "loaded", src: "thumb-a", resolvedSrc: "thumb-a" }};
assert.equal(helpers.thumbnailState({{
  src: "thumb-a",
  stored: storedBySrc,
}}), storedBySrc);
const storedBySourceSrc = {{ status: "loaded", sourceSrc: "thumb-b", resolvedSrc: "thumb-rendered" }};
assert.equal(helpers.thumbnailState({{
  src: "thumb-b",
  stored: storedBySourceSrc,
}}), storedBySourceSrc);
assert.deepEqual(helpers.thumbnailState({{
  src: "thumb-new",
  stored: {{ status: "loaded", src: "thumb-old" }},
}}), {{
  status: "loading",
  src: "thumb-new",
  error: "",
}});

const mockThumb = helpers.mockThumbnailDataUrl({{ tone: "tone-b" }});
assert.equal(mockThumb.startsWith("data:image/svg+xml;charset=utf-8,"), true);
const mockSvg = decodeURIComponent(mockThumb.split(",", 2)[1]);
assert.equal(mockSvg.includes('viewBox="0 0 96 96"'), true);
assert.equal(mockSvg.includes('stop-color="#f8e1dc"'), true);
assert.equal(mockSvg.includes('stop-color="#dfe9ec"'), true);
assert.equal(mockSvg.includes('stroke="#723d45"'), true);

const fallbackSvg = decodeURIComponent(helpers.mockThumbnailDataUrl({{ tone: "missing" }}).split(",", 2)[1]);
assert.equal(fallbackSvg.includes('stop-color="#f8f1e8"'), true);
assert.equal(fallbackSvg.includes('stroke="#34534a"'), true);

const thumb = helpers.thumbnailHtml(
  {{ id: "img-1", name: "Camisa <azul>.png" }},
  {{ status: "error", resolvedSrc: "data:image/png,<x>", error: "Sin <preview>" }},
  "",
);
assert.equal(thumb.includes('class="thumb is-error"'), true);
assert.equal(thumb.includes('data-thumb-id="img-1"'), true);
assert.equal(thumb.includes('src="data:image/png,&lt;x&gt;"'), true);
assert.equal(thumb.includes('alt="Miniatura de Camisa &lt;azul&gt;.png"'), true);
assert.equal(thumb.includes('Sin &lt;preview&gt;'), true);

const item = helpers.imageItemHtml({{
  image: {{
    id: "img-1",
    name: "Camisa <azul>.png",
    path: "C:/lote/Camisa <azul>.png",
    detail: "PNG · 14 KB",
    status: "ready",
  }},
  selected: true,
  imageStatus: "adjusted",
  exportState: {{ status: "error", label: "Error" }},
  fileType: "PNG",
  thumbState: {{ status: "error", error: "Sin preview" }},
  thumbnailSrc: "",
  statusLabels: {{ error: "Error" }},
}});
assert.equal(item.includes('class="image-item asset-row active error"'), true);
assert.equal(item.includes('data-image-id="img-1"'), true);
assert.equal(item.includes('title="C:/lote/Camisa &lt;azul&gt;.png"'), true);
assert.equal(item.includes('aria-pressed="true"'), true);
assert.equal(item.includes('aria-label="Camisa &lt;azul&gt;.png · Error"'), true);
assert.equal(item.includes('<strong>Camisa &lt;azul&gt;</strong>'), true);
assert.equal(item.includes('<small>PNG · 14 KB · sin preview</small>'), true);
assert.equal(item.includes('class="asset-state error"'), true);
assert.equal(item.includes('<span aria-hidden="true">×</span>'), true);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
