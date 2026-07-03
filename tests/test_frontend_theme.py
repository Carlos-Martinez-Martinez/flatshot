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
    assert html.index("theme.js") < html.index("app.js")
    assert "color-scheme: dark;" in dark_block
    assert css_tokens(dark_block) <= css_tokens(root_block)


def test_dark_theme_core_contrast_stays_accessible():
    dark_block = css_block(TOKENS_CSS_PATH.read_text(encoding="utf-8"), ':root[data-theme="dark"]')

    surface = css_token_value(dark_block, "--color-surface")
    text = css_token_value(dark_block, "--color-text")
    muted = css_token_value(dark_block, "--color-muted")
    primary = css_token_value(dark_block, "--color-primary")
    inverse = css_token_value(dark_block, "--color-text-inverse")

    assert contrast_ratio(text, surface) >= 4.5
    assert contrast_ratio(muted, surface) >= 4.5
    assert contrast_ratio(inverse, primary) >= 4.5


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
    assert 'theme: "flatshot.theme"' in mock
    assert "global.themeHelpers = window.FlatShotTheme;" in globals_source
    assert "const initialTheme = themeHelpers.readThemePreference" in app
    assert "theme: initialTheme" in app
    assert "themeHelpers.applyTheme(document, state.theme);" in shell
    assert 'shell.dataset.theme = state.theme;' in shell
    assert '"toggle-theme": () => toggleTheme()' in actions
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
assert.equal(helpers.readThemePreference(fakeStorage({{ theme: "dark" }}), "theme"), "dark");
assert.equal(helpers.readThemePreference(fakeStorage({{ theme: "bad" }}), "theme"), "light");
assert.equal(helpers.readThemePreference(fakeStorage({{}}, true), "theme"), "light");

const documentRef = fakeDocument();
assert.equal(helpers.applyTheme(documentRef, "dark"), "dark");
assert.equal(documentRef.documentElement.dataset.theme, "dark");

const storage = fakeStorage();
assert.equal(helpers.toggleTheme({{
  document: documentRef,
  storage,
  storageKey: "theme",
  currentTheme: "dark",
}}), "light");
assert.deepEqual(storage.dump(), {{ theme: "light" }});
assert.equal(documentRef.documentElement.dataset.theme, "light");

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
