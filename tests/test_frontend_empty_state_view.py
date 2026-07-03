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
assert.equal(helpers.ONBOARDING_BACKGROUND_ASSETS.every((asset) => asset.startsWith("./assets/onboarding/")), true);
assert.equal(helpers.ONBOARDING_BACKGROUND_ASSETS.every((asset) => asset.endsWith(".png")), true);

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

const initial = helpers.initialStateHtml({{ devMode: false }});
assert.equal(initial.includes('class="empty-state onboarding initial-onboarding"'), true);
assert.equal(initial.includes("<strong>Selecciona una carpeta</strong>"), true);
assert.equal(initial.includes("Carga un lote de imágenes PNG o JPG"), true);
assert.equal(initial.includes('data-action="pick-bridge-folder"'), true);
assert.equal(initial.includes('class="primary" data-action="pick-bridge-folder"'), false);
assert.equal(initial.includes('class="ghost-action" data-action="pick-bridge-folder"'), true);
assert.equal(initial.includes(">Buscar carpeta</button>"), true);
assert.equal(initial.includes(">Seleccionar carpeta</button>"), false);
assert.equal(initial.includes('data-action="open-app-settings"'), true);
assert.equal(initial.includes("Gestionar formatos"), true);
assert.equal(initial.includes('data-action="open-qa-lab"'), false);
assert.equal(initial.includes('class="folder-entry-inline"'), true);
assert.equal(initial.includes('class="manual-path-inline"'), false);
assert.equal(initial.includes("Ruta manual"), false);
assert.equal(initial.includes("Carpeta de entrada"), true);
assert.equal(initial.includes('id="onboarding-scan-path"'), true);
assert.equal(initial.includes('class="folder-entry-inline__scan primary"'), true);
assert.equal(initial.includes('data-action="scan-bridge-folder"'), true);
assert.equal(initial.includes('title="Escanear carpeta"'), true);
assert.ok(initial.indexOf('class="folder-entry-inline"') < initial.indexOf('class="empty-state__actions"'));
assert.equal(initial.includes("<svg"), true);

const devInitial = helpers.initialStateHtml({{
  devMode: true,
  bridgeScanPath: 'C:/Entrada/"uno"&<dos>',
}});
assert.equal(devInitial.includes('class="folder-entry-inline"'), true);
assert.equal(devInitial.includes('class="manual-path-inline"'), false);
assert.equal(devInitial.includes("Ruta manual"), false);
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

    assert "width: min(640px, 100%);" in entry_rule
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

    assert "width: min(680px, calc(100% - 48px));" in card_rule
    assert "z-index: 3;" in card_rule
    assert "gap: var(--space-4);" in card_rule
    assert "width: auto;" in actions_rule
    assert "display: inline-flex;" in actions_rule
    assert "min-width: 170px;" in action_button_rule
    assert "width: auto;" in action_button_rule


def test_onboarding_background_styles_are_perceptible_without_blocking_controls():
    css = EMPTY_CSS_PATH.read_text(encoding="utf-8")

    layer_rule = css.split(".onboarding-background {", 1)[1].split("}", 1)[0]
    base_rule = css.split(".onboarding-background::before {", 1)[1].split("}", 1)[0]
    overlay_rule = css.split(".onboarding-background::after {", 1)[1].split("}", 1)[0]
    active_slide_rule = css.split(".onboarding-background__slide.is-active {", 1)[1].split("}", 1)[0]
    fallback_rule = css.split(".onboarding-background.is-fallback::before {", 1)[1].split("}", 1)[0]

    assert "pointer-events: none;" in layer_rule
    assert "z-index: 0;" in layer_rule
    assert "opacity: 0.9;" in base_rule
    assert "repeating-linear-gradient" in base_rule
    assert "repeating-linear-gradient" in overlay_rule
    assert "opacity: 0.92;" in active_slide_rule
    assert "radial-gradient" in fallback_rule
