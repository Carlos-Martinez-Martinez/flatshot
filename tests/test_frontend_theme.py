import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "theme.js"
INDEX_PATH = FRONTEND_DIR / "index.html"
TOKENS_CSS_PATH = FRONTEND_DIR / "css" / "00-settings" / "tokens.css"


def css_block(source: str, selector: str) -> str:
    match = re.search(rf"{re.escape(selector)}\s*\{{(?P<body>.*?)\n\}}", source, re.S)
    assert match, f"{selector} block not found"
    return match.group("body")


def css_tokens(block: str) -> set[str]:
    return set(re.findall(r"(--[a-z0-9-]+)\s*:", block))


def css_token_value(block: str, token: str) -> str:
    match = re.search(rf"{re.escape(token)}:\s*([^;]+);", block)
    assert match, f"{token} not found"
    return match.group(1).strip()


def css_rule(source: str, selector: str) -> str:
    match = re.search(rf"(?m)^{re.escape(selector)}\s*\{{(?P<body>[^}}]*)\}}", source)
    assert match, f"{selector} rule not found"
    return match.group("body")


def relative_luminance(hex_color: str) -> float:
    assert re.fullmatch(r"#[0-9a-fA-F]{6}", hex_color), hex_color
    channels = [int(hex_color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [
        channel / 12.92 if channel <= 0.03928 else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(first: str, second: str) -> float:
    first_luminance = relative_luminance(first)
    second_luminance = relative_luminance(second)
    lighter, darker = sorted([first_luminance, second_luminance], reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def test_dark_theme_loads_early_and_uses_existing_token_names():
    html = INDEX_PATH.read_text(encoding="utf-8")
    tokens = TOKENS_CSS_PATH.read_text(encoding="utf-8")
    root_block = css_block(tokens, ":root")
    dark_block = css_block(tokens, ':root[data-theme="dark"]')

    assert 'localStorage.getItem("flatshot.theme")' in html
    assert html.index('localStorage.getItem("flatshot.theme")') < html.index("css/00-settings/tokens.css")
    assert 'prefers-color-scheme: dark' in html
    assert "dataset.themePreference" in html
    assert html.index("theme.js") < html.index("app.js")
    assert "color-scheme: dark;" in dark_block
    assert css_tokens(dark_block) <= css_tokens(root_block)


def test_dark_theme_core_contrast_stays_accessible():
    dark_block = css_block(TOKENS_CSS_PATH.read_text(encoding="utf-8"), ':root[data-theme="dark"]')

    surface = css_token_value(dark_block, "--color-surface")
    background = css_token_value(dark_block, "--color-bg")
    text = css_token_value(dark_block, "--color-text")
    muted = css_token_value(dark_block, "--color-muted")
    primary = css_token_value(dark_block, "--color-primary")
    primary_hover = css_token_value(dark_block, "--color-primary-hover")
    inverse = css_token_value(dark_block, "--color-text-inverse")

    assert background == "#18181b"
    assert surface == "#27272a"
    assert contrast_ratio(text, surface) >= 4.5
    assert contrast_ratio(muted, surface) >= 4.5
    assert contrast_ratio(inverse, primary) >= 4.5
    assert contrast_ratio(primary_hover, surface) >= 4.5


def test_dark_brand_tones_keep_text_accent_legible():
    tokens = TOKENS_CSS_PATH.read_text(encoding="utf-8")
    dark_block = css_block(tokens, ':root[data-theme="dark"]')
    root_block = css_block(tokens, ":root")
    surface = css_token_value(dark_block, "--color-surface")
    inverse = css_token_value(dark_block, "--color-text-inverse")

    expected_hover = {
        "blue": "#60a5fa",
        "indigo": "#818cf8",
        "violet": "#a78bfa",
        "coral": "#fb923c",
        "amber": "#f97316",
    }
    for tone, hover in expected_hover.items():
        block = css_block(tokens, f':root[data-theme="dark"][data-brand-tone="{tone}"]')
        assert css_tokens(block) <= css_tokens(root_block)
        assert css_token_value(block, "--color-primary-hover") == hover
        assert contrast_ratio(css_token_value(block, "--color-primary"), inverse) >= 4.5
        assert contrast_ratio(hover, surface) >= 4.5


def test_active_accent_text_uses_accessible_selection_token():
    tokens = TOKENS_CSS_PATH.read_text(encoding="utf-8")
    root_block = css_block(tokens, ":root")
    dark_block = css_block(tokens, ':root[data-theme="dark"]')
    navigation_css = (FRONTEND_DIR / "css" / "03-components" / "navigation-controls.css").read_text(encoding="utf-8")
    states_css = (FRONTEND_DIR / "css" / "08-states-responsive" / "states.css").read_text(encoding="utf-8")
    gallery_css = (FRONTEND_DIR / "css" / "04-batch-gallery" / "gallery-shell.css").read_text(encoding="utf-8")
    all_css = "\n".join(path.read_text(encoding="utf-8") for path in (FRONTEND_DIR / "css").rglob("*.css"))

    assert css_token_value(root_block, "--semantic-selection") == "var(--color-primary-hover)"
    assert css_token_value(dark_block, "--semantic-selection") == "var(--color-primary-hover)"
    assert css_token_value(root_block, "--rail-accent") == "var(--semantic-selection)"
    assert ".segmented.compact" in navigation_css
    assert "grid-auto-columns: minmax(0, 1fr);" in navigation_css
    assert ".segmented button.active, .inspector-tabs button.active" in states_css
    assert "color: var(--semantic-selection);" in states_css
    assert ".segmented button.active {\n  border-color: var(--color-accent-border);" not in states_css
    assert ".gallery-filter button.active" in gallery_css
    assert ".gallery-view-switch" in gallery_css
    assert "min-width: 168px;" in gallery_css
    assert not re.search(r"(?<!-)color:\s*var\(--color-accent-hover\);", all_css)
    assert "color: var(--color-primary);" not in gallery_css
    assert not re.search(r"(?<!-)color:\s*var\(--color-primary-hover\);", all_css)


def test_gallery_rail_uses_brand_tint_in_light_and_dark():
    tokens = TOKENS_CSS_PATH.read_text(encoding="utf-8")
    root_block = css_block(tokens, ":root")
    dark_block = css_block(tokens, ':root[data-theme="dark"]')
    gallery_css = (FRONTEND_DIR / "css" / "04-batch-gallery" / "gallery-shell.css").read_text(encoding="utf-8")
    batch_rail_css = (FRONTEND_DIR / "css" / "04-batch-gallery" / "batch-rail.css").read_text(encoding="utf-8")
    source_import_css = (FRONTEND_DIR / "css" / "04-batch-gallery" / "source-import.css").read_text(encoding="utf-8")
    viewer_css = (FRONTEND_DIR / "css" / "05-viewer" / "viewer-shell.css").read_text(encoding="utf-8")
    adjustments_css = (FRONTEND_DIR / "css" / "06-inspector-export" / "adjustments-presets.css").read_text(encoding="utf-8")

    assert "--gallery-rail" not in tokens
    assert "--batch-rail-accent" not in tokens
    assert css_token_value(root_block, "--rail-bg") == "color-mix(in srgb, var(--color-surface) 88%, var(--color-primary) 12%)"
    assert css_token_value(dark_block, "--rail-bg") == "color-mix(in srgb, var(--color-surface) 84%, var(--color-primary) 16%)"
    assert css_token_value(root_block, "--rail-border") == "color-mix(in srgb, var(--color-border) 78%, var(--color-primary) 22%)"
    assert css_token_value(dark_block, "--rail-border") == "color-mix(in srgb, var(--color-border) 68%, var(--color-primary) 32%)"
    for css, selector in (
        (gallery_css, ".gallery-column"),
        (batch_rail_css, ".batch-rail"),
    ):
        rule = css_rule(css, selector)
        assert "background: var(--rail-bg);" in rule
        expected_border = "border-top" if selector == ".gallery-column" else "border-right"
        assert f"{expected_border}: var(--border-width) solid var(--rail-border);" in rule
    for selector in (
        ".gallery-view-switch",
        ".gallery-output-control select",
        ".batch-search__box",
    ):
        rule = css_rule(gallery_css, selector)
        assert "border-color: var(--rail-border);" in rule
        assert "background: color-mix(in srgb, var(--rail-bg) 82%, var(--color-primary) 18%);" in rule
    search_input_rule = css_rule(gallery_css, ".batch-search__box input")
    assert "appearance: none;" in search_input_rule
    assert "-webkit-appearance: none;" in search_input_rule
    assert "background: transparent;" in search_input_rule
    assert "border-radius: 0;" in search_input_rule
    search_focus_rule = css_rule(gallery_css, ".batch-search__box input:focus-visible")
    assert "box-shadow: none;" in search_focus_rule
    assert "outline: 0;" in search_focus_rule
    assert "box-shadow: var(--shadow-focus);" in css_rule(gallery_css, ".batch-search__box:focus-within")
    assert "font-weight: var(--font-weight-bold);" in css_rule(gallery_css, ".gallery-search > span")
    assert ".settings-panel .search-field input" in adjustments_css
    assert not re.search(r"(?m)^\.search-field input\b", adjustments_css)
    assert ".gallery-view-switch.segmented button:hover:not(:disabled)" in gallery_css
    assert "background: color-mix(in srgb, var(--rail-bg) 76%, var(--color-primary) 24%);" in gallery_css
    assert ".gallery-header.gallery-toolbar" in gallery_css
    assert "background: transparent;" in gallery_css
    assert "border-bottom: var(--border-width) solid var(--rail-border);" in gallery_css
    assert ".source-panel.batch-rail__source" in source_import_css
    assert "background: transparent;" in source_import_css
    assert "border-bottom: var(--border-width) solid var(--rail-border);" in source_import_css
    assert not re.search(r"\.batch-panel[^{}]*\{[^{}]*background:", viewer_css)
    assert not re.search(r"\.gallery-column[^{}]*\{[^{}]*background:", viewer_css)


def test_brand_tone_loads_early_and_reuses_theme_tokens():
    html = INDEX_PATH.read_text(encoding="utf-8")
    tokens = TOKENS_CSS_PATH.read_text(encoding="utf-8")
    root_block = css_block(tokens, ":root")
    blue_block = css_block(tokens, ':root[data-brand-tone="blue"]')

    assert 'localStorage.getItem("flatshot.brandTone")' in html
    assert html.index('localStorage.getItem("flatshot.brandTone")') < html.index("css/00-settings/tokens.css")
    assert "data-brand-tone-value" in html
    assert css_tokens(blue_block) <= css_tokens(root_block)
    assert css_token_value(blue_block, "--color-primary") == "#2563eb"


def test_boot_theme_script_accepts_server_injected_preferences_before_css():
    html = INDEX_PATH.read_text(encoding="utf-8")
    shell_css = (FRONTEND_DIR / "css" / "02-layout" / "shell-workspace.css").read_text(encoding="utf-8")
    startup = (FRONTEND_DIR / "app-startup.js").read_text(encoding="utf-8")
    bridge_preferences = (FRONTEND_DIR / "app-bridge-ui-preferences.js").read_text(encoding="utf-8")

    assert 'document.getElementById("flatshot-boot-preferences")' in html
    assert html.index('document.getElementById("flatshot-boot-preferences")') < html.index("css/00-settings/tokens.css")
    assert "bootPreferences.themePreference" in html
    assert "bootPreferences.brandTone" in html
    assert "bootPreferences.interfacePreferences" in html
    assert 'root.dataset.boot = "pending";' in html
    assert ':root[data-boot="pending"] .app-shell {' in shell_css
    assert "visibility: hidden;" in shell_css
    assert "function markFlatShotBootReady()" in startup
    assert 'document.documentElement.dataset.boot = "ready";' in startup
    assert 'await restoreBridgeUiPreferences({ skipSessionSnapshot: true, renderOnRestore: false, timeoutMs: 900 });' in startup
    assert "restorePersistentBridgeSession();" not in startup
    assert "void scanBridgeFolder();" not in startup
    assert "if (restored && options.renderOnRestore !== false)" in bridge_preferences
    assert 'localStorage.setItem("flatshot.theme", themePreference)' in html
    assert 'localStorage.setItem("flatshot.brandTone", brandTone)' in html
    assert 'localStorage.setItem("flatshot.interfacePreferences", JSON.stringify(preferences))' in html


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend bootstrap checks")
def test_boot_theme_script_applies_injected_preferences_before_app_helpers():
    html = INDEX_PATH.read_text(encoding="utf-8")
    boot_script = re.search(r"<script>\s*(?P<script>\(\(\) => \{.*?\}\)\(\);)\s*</script>", html, re.S)
    assert boot_script, "theme bootstrap script not found"
    script = f"""
const assert = require("node:assert/strict");
const vm = require("node:vm");
const storage = new Map();
global.window = {{ matchMedia: () => ({{ matches: false }}) }};
global.localStorage = {{
  getItem(key) {{ return storage.has(key) ? storage.get(key) : null; }},
  setItem(key, value) {{ storage.set(key, String(value)); }},
}};
global.document = {{
  documentElement: {{ dataset: {{}} }},
  getElementById(id) {{
    if (id !== "flatshot-boot-preferences") return null;
    return {{
      textContent: JSON.stringify({{
        themePreference: "dark",
        brandTone: "blue",
        interfacePreferences: {{
          density: "comfortable",
          reduceMotion: true,
          thumbnailSize: "large",
          fileNameDisplay: "none",
        }},
      }}),
    }};
  }},
}};

vm.runInThisContext({json.dumps(boot_script.group("script"))});

assert.equal(document.documentElement.dataset.theme, "dark");
assert.equal(document.documentElement.dataset.themePreference, "dark");
assert.equal(document.documentElement.dataset.brandTone, "blue");
assert.equal(document.documentElement.dataset.boot, "pending");
assert.equal(document.documentElement.dataset.uiDensity, "comfortable");
assert.equal(document.documentElement.dataset.motion, "reduced");
assert.equal(document.documentElement.dataset.thumbnailSize, "large");
assert.equal(document.documentElement.dataset.fileNameDisplay, "none");
assert.equal(storage.get("flatshot.theme"), "dark");
assert.equal(storage.get("flatshot.brandTone"), "blue");
assert.equal(JSON.parse(storage.get("flatshot.interfacePreferences")).thumbnailSize, "large");
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout


def test_dark_theme_is_wired_to_topbar_state_and_persistence():
    html = INDEX_PATH.read_text(encoding="utf-8")
    mock = (FRONTEND_DIR / "mock-data.js").read_text(encoding="utf-8")
    globals_source = (FRONTEND_DIR / "app-globals.js").read_text(encoding="utf-8")
    app = (FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
    shell = (FRONTEND_DIR / "app-shell.js").read_text(encoding="utf-8")
    topbar = (FRONTEND_DIR / "app-topbar-bridge.js").read_text(encoding="utf-8")
    actions = (FRONTEND_DIR / "app-action-dispatcher.js").read_text(encoding="utf-8")
    topbar_css = (FRONTEND_DIR / "css" / "02-layout" / "topbar.css").read_text(encoding="utf-8")

    assert 'class="top-theme-action"' in html
    assert 'data-action="toggle-theme"' in html
    assert 'data-action="set-brand-tone"' in html
    assert 'theme: "flatshot.theme"' in mock
    assert 'brandTone: "flatshot.brandTone"' in mock
    assert "global.themeHelpers = window.FlatShotTheme;" in globals_source
    assert "const initialThemePreference = themeHelpers.readThemePreference" in app
    assert "const initialTheme = themeHelpers.resolveThemePreference(initialThemePreference" in app
    assert "const initialBrandTone = themeHelpers.readBrandTonePreference" in app
    assert "themePreference: initialThemePreference" in app
    assert "theme: initialTheme" in app
    assert "brandTone: initialBrandTone" in app
    assert "themeHelpers.applyTheme(document, state.theme);" in shell
    assert "themeHelpers.applyBrandTone(document, state.brandTone);" in shell
    assert "document.documentElement.dataset.themePreference = state.themePreference;" in shell
    assert 'shell.dataset.theme = state.theme;' in shell
    assert 'shell.dataset.brandTone = state.brandTone;' in shell
    assert '"toggle-theme": () => toggleTheme()' in actions
    assert '"set-brand-tone": (target) => setBrandTone(target?.dataset?.brandToneValue)' in actions
    assert 'themeButton.setAttribute("aria-pressed", state.theme === "dark" ? "true" : "false");' in topbar
    assert ".top-theme-action" in topbar_css


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_theme_helper_normalizes_applies_and_persists_theme():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

function fakeStorage(initial = {{}}, failing = false) {{
  const data = new Map(Object.entries(initial));
  return {{
    getItem(key) {{
      if (failing) throw new Error("blocked");
      return data.has(key) ? data.get(key) : null;
    }},
    setItem(key, value) {{
      if (failing) throw new Error("blocked");
      data.set(key, String(value));
    }},
    dump() {{
      return Object.fromEntries(data.entries());
    }},
  }};
}}

function fakeDocument() {{
  return {{ documentElement: {{ dataset: {{}} }} }};
}}

assert.equal(helpers.normalizeTheme("dark"), "dark");
assert.equal(helpers.normalizeTheme("light"), "light");
assert.equal(helpers.normalizeTheme("system"), "light");
assert.equal(helpers.normalizeThemePreference("system"), "system");
assert.equal(helpers.normalizeThemePreference("bad"), "light");
assert.equal(helpers.readThemePreference(fakeStorage({{ theme: "dark" }}), "theme"), "dark");
assert.equal(helpers.readThemePreference(fakeStorage({{ theme: "system" }}), "theme"), "system");
assert.equal(helpers.readThemePreference(fakeStorage({{ theme: "bad" }}), "theme"), "light");
assert.equal(helpers.readThemePreference(fakeStorage({{}}, true), "theme"), "light");
assert.equal(helpers.resolveThemePreference("system", {{ matchMedia: () => ({{ matches: true }}) }}), "dark");
assert.equal(helpers.resolveThemePreference("system", {{ matchMedia: () => ({{ matches: false }}) }}), "light");
assert.deepEqual(helpers.brandToneOptions().map((tone) => tone.id), ["green", "blue", "indigo", "violet", "coral", "amber"]);
assert.equal(helpers.normalizeBrandTone("blue"), "blue");
assert.equal(helpers.normalizeBrandTone("bad"), "green");
assert.equal(helpers.readBrandTonePreference(fakeStorage({{ tone: "violet" }}), "tone"), "violet");
assert.equal(helpers.readBrandTonePreference(fakeStorage({{}}, true), "tone"), "green");

const documentRef = fakeDocument();
assert.equal(helpers.applyTheme(documentRef, "dark"), "dark");
assert.equal(documentRef.documentElement.dataset.theme, "dark");
assert.equal(helpers.applyBrandTone(documentRef, "coral"), "coral");
assert.equal(documentRef.documentElement.dataset.brandTone, "coral");

const storage = fakeStorage();
assert.equal(helpers.toggleTheme({{
  document: documentRef,
  storage,
  storageKey: "theme",
  currentTheme: "dark",
}}), "light");
assert.deepEqual(storage.dump(), {{ theme: "light" }});
assert.equal(documentRef.documentElement.dataset.theme, "light");
helpers.writeThemePreference(storage, "theme", "system");
assert.equal(storage.dump().theme, "system");

helpers.writeBrandTonePreference(storage, "tone", "amber");
assert.equal(storage.dump().tone, "amber");
assert.doesNotThrow(() => helpers.writeBrandTonePreference(fakeStorage({{}}, true), "tone", "blue"));
assert.doesNotThrow(() => helpers.writeThemePreference(fakeStorage({{}}, true), "theme", "dark"));
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
