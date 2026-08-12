import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "gallery.js"
INDEX_PATH = FRONTEND_DIR / "index.html"
APP_GALLERY_CONTROLLER_PATH = FRONTEND_DIR / "app-gallery-controller.js"
APP_GALLERY_SELECTION_PATH = FRONTEND_DIR / "app-gallery-selection-workflow.js"
APP_RENDER_SHELL_GALLERY_PATH = FRONTEND_DIR / "app-render-shell-gallery.js"
APP_DOCUMENT_EVENTS_PATH = FRONTEND_DIR / "app-document-events.js"
APP_THUMBNAIL_CONTROLLER_PATH = FRONTEND_DIR / "app-thumbnail-controller.js"
APP_JS_PATH = FRONTEND_DIR / "app.js"
APP_EXPORT_VIEW_PATH = FRONTEND_DIR / "app-export-view.js"
GALLERY_CSS_PATH = FRONTEND_DIR / "css" / "04-batch-gallery" / "image-grid.css"
THUMBNAILS_CSS_PATH = FRONTEND_DIR / "css" / "04-batch-gallery" / "thumbnails.css"


def test_gallery_helper_loads_before_app_script():
    html = INDEX_PATH.read_text(encoding="utf-8")

    output_index = html.index("output-profiles.js")
    preflight_index = html.index("preflight.js")
    gallery_index = html.index("gallery.js")
    app_index = html.index("app.js")

    assert output_index < app_index
    assert preflight_index < app_index
    assert gallery_index < app_index


def test_gallery_and_export_views_use_output_profile_destination_helper():
    gallery_controller = APP_GALLERY_CONTROLLER_PATH.read_text(encoding="utf-8")
    export_view = APP_EXPORT_VIEW_PATH.read_text(encoding="utf-8")

    assert "profiles.map(outputProfileViewHelpers.profileDestinationPreviewLabel)" in gallery_controller
    assert "profiles.map(outputProfileViewHelpers.profileDestinationPreviewLabel)" in export_view
    assert "profiles.map(profileDestinationPreviewLabel)" not in gallery_controller
    assert "profiles.map(profileDestinationPreviewLabel)" not in export_view


def test_gallery_thumbnail_view_keeps_file_metadata_visible():
    css = GALLERY_CSS_PATH.read_text(encoding="utf-8")

    assert '.gallery-column[data-gallery-view="thumbs"] .image-copy small' in css
    assert '.gallery-column[data-gallery-view="thumbs"] .image-copy small {\n  display: none;' not in css
    assert '.gallery-column[data-gallery-view="thumbs"] .image-copy small, .gallery-filter[hidden]' not in css


def test_gallery_rgb230_thumbnail_background_uses_resolved_output_color():
    css = THUMBNAILS_CSS_PATH.read_text(encoding="utf-8")

    assert '.gallery-column[data-output-bg="rgb230"] .thumb' in css
    assert '.gallery-column[data-output-bg="rgb230"] .thumb, .gallery-column[data-output-bg="custom"] .thumb' in css


def test_gallery_multiselect_and_virtual_window_are_wired():
    app = APP_JS_PATH.read_text(encoding="utf-8")
    selection = APP_GALLERY_SELECTION_PATH.read_text(encoding="utf-8")
    controller = APP_GALLERY_CONTROLLER_PATH.read_text(encoding="utf-8")
    events = APP_DOCUMENT_EVENTS_PATH.read_text(encoding="utf-8")
    thumbnails = APP_THUMBNAIL_CONTROLLER_PATH.read_text(encoding="utf-8")
    css = GALLERY_CSS_PATH.read_text(encoding="utf-8")

    assert "selectedImageIds: []" in app
    assert "selectionAnchorImageId: null" in app
    assert "galleryScrollTop: 0" in app
    assert "function selectGalleryImage(imageId, options = {})" in selection
    assert "galleryHelpers.resolveGallerySelection" in selection
    assert "selectGalleryImage(imageTarget.dataset.imageId" in events
    assert "additive: event.ctrlKey || event.metaKey" in events
    assert "range: event.shiftKey" in events
    assert "galleryHelpers.virtualGalleryWindow" in controller
    assert "galleryVirtualSpacerHtml" in controller
    assert "queueThumbnailPreload(renderedImages)" in controller
    assert "function queueThumbnailPreload(images = null)" in thumbnails
    assert "preloadBatchThumbnails(images)" in thumbnails
    assert "gallery-virtual-spacer" in css


def test_gallery_auto_scroll_runs_only_when_selection_changes():
    selection = APP_GALLERY_SELECTION_PATH.read_text(encoding="utf-8")
    rendering = APP_RENDER_SHELL_GALLERY_PATH.read_text(encoding="utf-8")

    assert "keepActiveThumbnailVisible();" in selection
    assert "keepActiveThumbnailVisible();" not in rendering


def test_virtual_gallery_render_restores_vertical_scroll_position_after_replacing_items():
    controller = APP_GALLERY_CONTROLLER_PATH.read_text(encoding="utf-8")

    capture = "const preservedScrollTop = imageList.scrollTop;"
    replace = "imageList.innerHTML = ["
    restore = "imageList.scrollTop = preservedScrollTop;"
    assert capture in controller
    assert restore in controller
    assert controller.index(capture) < controller.index(replace) < controller.index(restore)


def test_gallery_virtual_window_reads_vertical_viewport_geometry():
    controller = APP_GALLERY_CONTROLLER_PATH.read_text(encoding="utf-8")
    events = APP_DOCUMENT_EVENTS_PATH.read_text(encoding="utf-8")

    assert "imageList?.scrollTop || 0" in controller
    assert "viewportHeight: imageList?.clientHeight || 0" in controller
    assert "state.galleryScrollTop = event.target.scrollTop;" in events
    assert 'style="height:${normalized}px"' in controller


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

assert.deepEqual(helpers.resolveGallerySelection({{
  images,
  selectedIds: ["a"],
  primaryId: "a",
  anchorId: "a",
  targetId: "c",
  additive: false,
  range: false,
}}), {{
  selectedImageId: "c",
  selectedIds: ["c"],
  anchorId: "c",
}});
assert.deepEqual(helpers.resolveGallerySelection({{
  images,
  selectedIds: ["a"],
  primaryId: "a",
  anchorId: "a",
  targetId: "c",
  additive: true,
  range: false,
}}), {{
  selectedImageId: "c",
  selectedIds: ["a", "c"],
  anchorId: "c",
}});
assert.deepEqual(helpers.resolveGallerySelection({{
  images,
  selectedIds: ["a"],
  primaryId: "a",
  anchorId: "a",
  targetId: "d",
  additive: false,
  range: true,
}}), {{
  selectedImageId: "d",
  selectedIds: ["a", "b", "c", "d"],
  anchorId: "a",
}});

assert.deepEqual(helpers.virtualGalleryWindow({{
  total: 20,
  scrollTop: 180,
  viewportHeight: 240,
  rowHeight: 60,
  columns: 2,
  overscanRows: 1,
}}), {{
  virtualized: false,
  start: 0,
  end: 20,
  paddingTop: 0,
  paddingBottom: 0,
}});
assert.deepEqual(helpers.virtualGalleryWindow({{
  total: 240,
  scrollTop: 360,
  viewportHeight: 300,
  rowHeight: 60,
  columns: 2,
  overscanRows: 2,
  threshold: 80,
}}), {{
  virtualized: true,
  start: 8,
  end: 24,
  paddingTop: 240,
  paddingBottom: 6480,
}});

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
const subfolderEmpty = helpers.emptyBatchNoteHtml({{
  ignored: 2,
  ignoredSummary: "2 subcarpetas no escaneadas",
  subfoldersOmitted: 2,
}});
assert.equal(subfolderEmpty.includes('data-action="include-subfolders"'), true);
assert.equal(subfolderEmpty.includes("Incluir subcarpetas"), true);
assert.equal(subfolderEmpty.includes('data-action="open-batch-detail"'), true);
assert.equal(subfolderEmpty.includes("Ver ignorados"), true);
assert.equal(
  helpers.emptyBatchNoteHtml({{ ignored: 0, scanStatus: "Sin compatibles" }}).includes("Sin compatibles"),
  true,
);
assert.equal(helpers.compactImageDetail("PNG · 14 KB"), "14 KB");
assert.equal(helpers.compactImageDetail("Lista"), "");
assert.equal(helpers.assetStatusLabel("ready", {{ warning: "Aviso" }}), "Lista");
assert.equal(helpers.assetStatusLabel("adjusted", {{ warning: "Aviso" }}), "Personalizado");
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
assert.deepEqual(helpers.thumbnailState({{
  src: "rendered:thumb",
  displaySrc: "",
  renderedOnly: true,
}}), {{
  status: "loading",
  src: "rendered:thumb",
  error: "",
  displaySrc: "",
  renderedOnly: true,
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
const renderedOnlyThumb = helpers.thumbnailHtml(
  {{ id: "img-2", name: "Vestido.png" }},
  {{ status: "loading", src: "rendered:thumb", renderedOnly: true }},
  "rendered:thumb",
);
assert.equal(renderedOnlyThumb.includes('class="thumb-image"'), false);
assert.equal(renderedOnlyThumb.includes('class="thumb is-loading"'), true);

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

const itemWithOutput = helpers.imageItemHtml({{
  image: {{
    id: "img-2",
    name: "Camisa.png",
    path: "C:/lote/Camisa.png",
    detail: "PNG · 14 KB",
    status: "ready",
  }},
  outputLabel: "PNG · transparente",
  statusLabels: {{}},
}});
assert.equal(itemWithOutput.includes('aria-label="Camisa.png · Lista · PNG · transparente"'), true);
assert.equal(itemWithOutput.includes('class="image-output-label">PNG · transparente</span>'), true);

const multiSelectedItem = helpers.imageItemHtml({{
  image: {{
    id: "img-3",
    name: "Bolso.png",
    path: "C:/lote/Bolso.png",
    detail: "PNG · 14 KB",
    status: "ready",
  }},
  selected: true,
  primarySelected: false,
  statusLabels: {{}},
}});
assert.equal(multiSelectedItem.includes('class="image-item asset-row selected ready"'), true);
assert.equal(multiSelectedItem.includes('aria-selected="true"'), true);
assert.equal(multiSelectedItem.includes('aria-current="false"'), true);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
