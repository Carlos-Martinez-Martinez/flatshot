import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "empty-state-view.js"
ONBOARDING_BACKGROUND_PATH = FRONTEND_DIR / "onboarding-background.js"
INDEX_PATH = FRONTEND_DIR / "index.html"
EMPTY_CSS_PATH = FRONTEND_DIR / "css" / "03-components" / "empty-states.css"
WORKFLOW_CSS_PATH = FRONTEND_DIR / "css" / "03-components" / "workflow-panels.css"


def test_empty_state_view_helper_loads_before_app_script():
    html = INDEX_PATH.read_text(encoding="utf-8")

    helper_index = html.index("empty-state-view.js")
    app_index = html.index("app.js")

    assert helper_index < app_index


def test_onboarding_background_module_loads_before_app_loader():
    html = INDEX_PATH.read_text(encoding="utf-8")

    background_index = html.index("onboarding-background.js")
    loader_index = html.index("app-loader.js")

    assert background_index < loader_index


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_onboarding_background_uses_optional_local_assets():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(ONBOARDING_BACKGROUND_PATH))});

assert.equal(Array.isArray(helpers.ONBOARDING_BACKGROUND_ASSETS), true);
assert.equal(helpers.ONBOARDING_BACKGROUND_ASSETS.length, 5);
assert.equal(helpers.ONBOARDING_BACKGROUND_ASSET_DIR, "./assets/onboarding/");
assert.deepEqual(helpers.ONBOARDING_BACKGROUND_ASSETS, [
  "./assets/onboarding/flatshot-abstract-01.png",
  "./assets/onboarding/flatshot-abstract-02.png",
  "./assets/onboarding/flatshot-abstract-03.png",
  "./assets/onboarding/flatshot-abstract-04.png",
  "./assets/onboarding/flatshot-abstract-05.png",
]);

assert.deepEqual(helpers.uniqueLoadedAssets([
  "./assets/onboarding/mesh-01.png",
  "",
  "./assets/onboarding/mesh-01.png",
  "./assets/onboarding/mesh-02.png",
]), [
  "./assets/onboarding/mesh-01.png",
  "./assets/onboarding/mesh-02.png",
]);
assert.deepEqual(helpers.uniqueLoadedAssets([]), []);
assert.deepEqual(helpers.normalizeAssetList([
  "flatshot-extra-06.png",
  "assets/onboarding/flatshot-extra-07.jpg",
  "./assets/onboarding/flatshot-extra-08.webp",
  "./assets/onboarding/flatshot-extra-08.webp",
  "../escape.png",
  "https://example.com/remote.png",
  "notes.txt",
]), [
  "./assets/onboarding/flatshot-extra-06.png",
  "./assets/onboarding/flatshot-extra-07.jpg",
  "./assets/onboarding/flatshot-extra-08.webp",
]);
assert.deepEqual(helpers.assetsFromDirectoryListing(`
  <a href="flatshot-abstract-01.png">flatshot-abstract-01.png</a>
  <a href="custom-extra.webp">custom-extra.webp</a>
  <a href="nested/">nested/</a>
  <a href="../">../</a>
  <a href="notes.txt">notes.txt</a>
`), [
  "./assets/onboarding/custom-extra.webp",
  "./assets/onboarding/flatshot-abstract-01.png",
]);

(async () => {{
  const configured = await helpers.configuredAssetCandidates({{
    fetch: async (url) => {{
      assert.equal(url, "./assets/onboarding/");
      return {{
        ok: true,
        async text() {{
          return `
            <a href="flatshot-extra-06.png">flatshot-extra-06.png</a>
            <a href="flatshot-extra-07.jpg">flatshot-extra-07.jpg</a>
          `;
        }},
      }};
    }},
  }});
  assert.deepEqual(configured, [
    "./assets/onboarding/flatshot-extra-06.png",
    "./assets/onboarding/flatshot-extra-07.jpg",
  ]);

  const fallback = await helpers.configuredAssetCandidates({{
    fetch: async () => {{ throw new Error("manifest unavailable"); }},
  }});
  assert.deepEqual(fallback, helpers.ONBOARDING_BACKGROUND_ASSETS);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
}});

(async () => {{
  Object.defineProperty(global, "Image", {{
    configurable: true,
    value: class MissingImage {{
      set src(value) {{
        this.onerror();
      }}
    }},
  }});
  function fakeClassList(initial = "") {{
    const names = new Set(initial ? initial.split(" ") : []);
    return {{
      contains(name) {{ return names.has(name); }},
      toggle(name, enabled) {{ enabled ? names.add(name) : names.delete(name); }},
      toString() {{ return Array.from(names).join(" "); }},
    }};
  }}
  function fakeElement(tag) {{
    const element = {{
      tag,
      children: [],
      className: "",
      id: "",
      style: {{}},
      classList: fakeClassList(),
      appendChild(child) {{ this.children.push(child); }},
      prepend(child) {{ this.children.unshift(child); }},
      querySelectorAll(selector) {{
        return selector === ".onboarding-background__slide"
          ? this.children.filter((child) => child.className === "onboarding-background__slide")
          : [];
      }},
      remove() {{ this.removed = true; }},
      setAttribute(name, value) {{ this[name] = value; }},
    }};
    return element;
  }}
  const shell = {{ dataset: {{ uiState: "no_folder" }} }};
  const previewCanvas = fakeElement("div");
  const fakeDocument = {{
    querySelector(selector) {{
      if (selector === ".app-shell") {{
        return shell;
      }}
      if (selector === "#preview-canvas") {{
        return previewCanvas;
      }}
      return null;
    }},
    createElement: fakeElement,
    getElementById() {{
      return null;
    }},
  }};
  const controller = await helpers.initialize({{ document: fakeDocument, assets: ["./assets/onboarding/missing.png"] }});
  assert.notEqual(controller, null);
  assert.equal(previewCanvas.children.length, 1);
  assert.equal(controller.layer.classList.contains("is-visible"), true);
  assert.equal(controller.layer.classList.contains("is-fallback"), true);
  assert.equal(controller.layer.querySelectorAll(".onboarding-background__slide").length, 0);
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
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


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_onboarding_background_randomizes_initial_and_rotation_without_repeating():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(ONBOARDING_BACKGROUND_PATH))});

assert.equal(helpers.pickInitialAssetIndex(5, () => 0), 0);
assert.equal(helpers.pickInitialAssetIndex(5, () => 0.62), 3);
assert.equal(helpers.pickInitialAssetIndex(5, () => 0.999), 4);
assert.equal(helpers.pickInitialAssetIndex(0, () => 0.5), 0);
assert.equal(helpers.nextRandomSlideIndex(0, 1, () => 0.9), 0);
assert.equal(helpers.nextRandomSlideIndex(1, 3, () => 0), 2);
assert.equal(helpers.nextRandomSlideIndex(1, 3, () => 0.99), 0);

(async () => {{
  Object.defineProperty(global, "Image", {{
    configurable: true,
    value: class LoadedImage {{
      set src(_value) {{
        this.onload();
      }}
    }},
  }});

  let intervalCallback = null;
  const originalSetInterval = global.setInterval;
  const originalClearInterval = global.clearInterval;
  const originalMatchMedia = global.matchMedia;
  global.setInterval = (callback) => {{
    intervalCallback = callback;
    return 99;
  }};
  global.clearInterval = () => {{}};
  global.matchMedia = () => ({{ matches: false }});

  function fakeClassList(element, initial = "") {{
    const names = new Set(initial ? initial.split(" ") : []);
    return {{
      contains(name) {{ return names.has(name); }},
      toggle(name, enabled) {{ enabled ? names.add(name) : names.delete(name); }},
      add(name) {{ names.add(name); }},
      remove(name) {{ names.delete(name); }},
      toString() {{ return Array.from(names).join(" "); }},
    }};
  }}
  function fakeElement(tag) {{
    const element = {{
      tag,
      children: [],
      className: "",
      id: "",
      style: {{}},
      appendChild(child) {{ this.children.push(child); }},
      prepend(child) {{ this.children.unshift(child); }},
      querySelectorAll(selector) {{
        return selector === ".onboarding-background__slide"
          ? this.children.filter((child) => child.className === "onboarding-background__slide")
          : [];
      }},
      remove() {{ this.removed = true; }},
      setAttribute(name, value) {{ this[name] = value; }},
    }};
    element.classList = fakeClassList(element);
    return element;
  }}
  const shell = {{ dataset: {{ uiState: "no_folder" }} }};
  const previewCanvas = fakeElement("div");
  const fakeDocument = {{
    querySelector(selector) {{
      if (selector === ".app-shell") {{
        return shell;
      }}
      if (selector === "#preview-canvas") {{
        return previewCanvas;
      }}
      return null;
    }},
    createElement: fakeElement,
    getElementById() {{
      return null;
    }},
  }};

  const randomValues = [0.6, 0, 0];
  const controller = await helpers.initialize({{
    document: fakeDocument,
    assets: [
      "./assets/onboarding/a.png",
      "./assets/onboarding/b.png",
      "./assets/onboarding/c.png",
    ],
    random() {{
      return randomValues.shift() ?? 0;
    }},
  }});
  const slides = controller.layer.querySelectorAll(".onboarding-background__slide");
  assert.equal(slides[1].classList.contains("is-active"), true);
  assert.equal(slides[0].classList.contains("is-active"), false);

  intervalCallback();
  assert.equal(slides[2].classList.contains("is-active"), true);
  assert.equal(slides[1].classList.contains("is-active"), false);

  intervalCallback();
  assert.equal(slides[0].classList.contains("is-active"), true);
  assert.equal(slides[2].classList.contains("is-active"), false);

  controller.stop();
  global.setInterval = originalSetInterval;
  global.clearInterval = originalClearInterval;
  global.matchMedia = originalMatchMedia;
}})().catch((error) => {{
  console.error(error);
  process.exit(1);
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


def test_onboarding_background_assets_exist():
    source = ONBOARDING_BACKGROUND_PATH.read_text(encoding="utf-8")

    for index in range(1, 6):
        relative = f"./assets/onboarding/flatshot-abstract-{index:02}.png"
        assert relative in source
        assert (FRONTEND_DIR / relative.removeprefix("./")).is_file()


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_empty_state_view_keeps_existing_html_contract():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

assert.equal(helpers.escapeHtml("<a&b\\"c>"), "&lt;a&amp;b&quot;c&gt;");

const plain = helpers.emptyStateHtml({{
  title: "Sin lote",
  detail: "Elige <carpeta>",
}});
assert.equal(plain.includes('class="empty-state inline"'), true);
assert.equal(plain.includes('<strong>Sin lote</strong>'), true);
assert.equal(plain.includes('<span>Elige &lt;carpeta&gt;</span>'), true);
assert.equal(plain.includes('<button'), false);
assert.equal(plain.includes('<small>'), false);

const withAction = helpers.emptyStateHtml({{
  variant: 'onboarding "x"',
  title: "Selecciona",
  detail: "Carga",
  actionLabel: "Elegir & abrir",
  action: 'pick-"folder"',
  meta: "PNG & JPG",
}});
assert.equal(withAction.includes('class="empty-state onboarding &quot;x&quot;"'), true);
assert.equal(withAction.includes('data-action="pick-&quot;folder&quot;"'), true);
assert.equal(withAction.includes('>Elegir &amp; abrir</button>'), true);
assert.equal(withAction.includes('<small>PNG &amp; JPG</small>'), true);

const batchEmpty = helpers.emptyStateHtml({{
  variant: "batch-empty",
  title: "No se encontraron imágenes compatibles",
  detail: "Esta carpeta no contiene imágenes compatibles.",
  actionLabel: "Elegir otra carpeta",
  action: "pick-bridge-folder",
}});
assert.equal(batchEmpty.includes('class="empty-state batch-empty"'), true);
assert.equal(batchEmpty.includes('<svg viewBox="0 0 24 24"'), true);
assert.equal(batchEmpty.includes('M3 6.75A2.75 2.75'), true);
assert.equal(batchEmpty.includes('class="primary" data-action="pick-bridge-folder"'), true);
assert.equal(batchEmpty.includes('>Elegir otra carpeta</button>'), true);

const initial = helpers.initialStateHtml({{ devMode: false }});
assert.equal(initial.includes('class="empty-state onboarding initial-onboarding"'), true);
assert.equal(initial.includes("<strong>Selecciona una carpeta</strong>"), true);
assert.equal(initial.includes("Carga un lote de imágenes PNG o JPG"), true);
assert.equal(initial.includes('data-action="pick-bridge-folder"'), true);
assert.equal(initial.includes('class="primary" data-action="pick-bridge-folder"'), true);
assert.equal(initial.includes(">Seleccionar carpeta</button>"), true);
assert.equal(initial.includes('data-action="open-app-settings"'), false);
assert.equal(initial.includes("Gestionar salidas"), false);
assert.equal(initial.includes('data-action="open-qa-lab"'), false);
assert.equal(initial.includes('class="folder-entry-inline"'), true);
assert.equal(initial.includes('class="manual-path-inline"'), true);
assert.equal(initial.includes("Introducir ruta"), true);
assert.equal(initial.includes("Carpeta de entrada"), true);
assert.equal(initial.includes('id="onboarding-scan-path"'), true);
assert.equal(initial.includes('class="folder-entry-inline__scan primary"'), true);
assert.equal(initial.includes('data-action="scan-bridge-folder"'), true);
assert.equal(initial.includes('title="Escanear carpeta"'), true);
assert.ok(initial.indexOf('class="empty-state__actions"') < initial.indexOf('class="folder-entry-inline"'));
assert.equal(initial.includes("<svg"), true);

const devInitial = helpers.initialStateHtml({{
  devMode: true,
  bridgeScanPath: 'C:/Entrada/"uno"&<dos>',
}});
assert.equal(devInitial.includes('class="folder-entry-inline"'), true);
assert.equal(devInitial.includes('class="manual-path-inline"'), true);
assert.equal(devInitial.includes("Introducir ruta"), true);
assert.equal(devInitial.includes('id="onboarding-scan-path"'), true);
assert.equal(devInitial.includes('value="C:/Entrada/&quot;uno&quot;&amp;&lt;dos&gt;"'), true);
assert.equal(devInitial.includes('data-action="scan-bridge-folder"'), true);
assert.equal(devInitial.includes('data-action="open-qa-lab"'), true);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout


def test_initial_folder_entry_keeps_stable_layout_styles():
    css = WORKFLOW_CSS_PATH.read_text(encoding="utf-8")

    entry_rule = css.split(".folder-entry-inline {", 1)[1].split("}", 1)[0]
    input_rule = css.split(".folder-entry-inline input {", 1)[1].split("}", 1)[0]

    assert "width: var(--workflow-inline-width);" in entry_rule
    assert "display: grid;" in entry_rule
    assert "grid-template-columns: minmax(0, 1fr) auto;" in entry_rule
    assert "align-items: end;" in entry_rule
    assert "min-width: 0;" in input_rule
    assert "width: 100%;" in input_rule


def test_initial_onboarding_card_uses_deliberate_stable_layout_styles():
    css = EMPTY_CSS_PATH.read_text(encoding="utf-8")

    card_rule = css.split(".empty-state.onboarding.initial-onboarding {", 1)[1].split("}", 1)[0]
    actions_rule = css.split(".empty-state.onboarding.initial-onboarding .empty-state__actions {", 1)[1].split("}", 1)[0]
    action_button_rule = css.split(".empty-state.onboarding.initial-onboarding .empty-state__actions button {", 1)[1].split("}", 1)[0]

    assert "width: min(680px, calc(100% - var(--modal-viewport-gutter)));" in card_rule
    assert "z-index: 3;" in card_rule
    assert "gap: var(--space-4);" in card_rule
    assert "width: auto;" in actions_rule
    assert "display: inline-flex;" in actions_rule
    assert "min-width: 170px;" in action_button_rule
    assert "width: auto;" in action_button_rule
    assert "box-shadow: none;" in card_rule


def test_batch_empty_state_is_centered_without_a_floating_card():
    css = EMPTY_CSS_PATH.read_text(encoding="utf-8")

    state_rule = css.split(".empty-state.batch-empty {", 1)[1].split("}", 1)[0]
    icon_rule = css.split(".empty-state.batch-empty .empty-icon {", 1)[1].split("}", 1)[0]

    assert "align-content: center;" in state_rule
    assert "background:" not in state_rule
    assert "box-shadow:" not in state_rule
    assert "background: var(--color-warning-soft);" in icon_rule
    assert ".empty-state:is(.onboarding, .batch-empty) .empty-icon::before" in css
    assert ".empty-state:is(.onboarding, .batch-empty) .empty-icon svg" in css


def test_onboarding_background_styles_are_perceptible_without_blocking_controls():
    css = EMPTY_CSS_PATH.read_text(encoding="utf-8")

    layer_rule = css.split(".onboarding-background {", 1)[1].split("}", 1)[0]
    base_rule = css.split(".onboarding-background::before {", 1)[1].split("}", 1)[0]
    overlay_rule = css.split(".onboarding-background::after {", 1)[1].split("}", 1)[0]
    active_slide_rule = css.split(".onboarding-background__slide.is-active {", 1)[1].split("}", 1)[0]
    fallback_rule = css.split(".onboarding-background.is-fallback::before {", 1)[1].split("}", 1)[0]
    slide_rule = css.split(".onboarding-background__slide {", 1)[1].split("}", 1)[0]

    assert "pointer-events: none;" in layer_rule
    assert "z-index: 0;" in layer_rule
    assert "opacity: 0.9;" in base_rule
    assert "repeating-linear-gradient" in base_rule
    assert "repeating-linear-gradient" in overlay_rule
    assert "opacity: 0.92;" in active_slide_rule
    assert "radial-gradient" in fallback_rule
    assert "background-position: center;" in slide_rule
    assert "background-size: cover;" in slide_rule
    assert "background-repeat: no-repeat;" in slide_rule
    assert "background-color: color-mix(in srgb, var(--color-accent)" in slide_rule
    assert "background-blend-mode: luminosity;" in slide_rule
    assert "grayscale(" not in slide_rule
    assert "hue-rotate" not in slide_rule
    assert "background-color var(--duration-onboarding-fade)" in slide_rule

    enabled_selector = '.app-shell[data-ui-state="no_folder"] .onboarding-background.is-visible {'
    enabled_rule = css.split(enabled_selector, 1)[1].split("}", 1)[0]
    assert "display: none;" in enabled_rule

    disabled_selector = ':root[data-onboarding-background="disabled"] .app-shell[data-ui-state="no_folder"] .onboarding-background.is-visible {'
    assert disabled_selector in css
    disabled_rule = css.split(disabled_selector, 1)[1].split("}", 1)[0]
    assert "display: none;" in disabled_rule

    dark_slide_selector = ':root[data-theme="dark"] .onboarding-background__slide {'
    dark_active_selector = ':root[data-theme="dark"] .onboarding-background__slide.is-active {'
    assert dark_slide_selector in css
    assert dark_active_selector in css
    dark_slide_rule = css.split(dark_slide_selector, 1)[1].split("}", 1)[0]
    dark_active_slide_rule = css.split(dark_active_selector, 1)[1].split("}", 1)[0]
    assert "background-color: color-mix(in srgb, var(--color-accent)" in dark_slide_rule
    assert "grayscale(" not in dark_slide_rule
    assert "brightness(0." in dark_slide_rule
    assert "opacity: 0." in dark_active_slide_rule
