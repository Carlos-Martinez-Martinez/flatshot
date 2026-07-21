# Canvas Guides Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build global, percentage-based canvas guide systems for the FlatShot viewer, with symmetric pairs, uniform/custom divisions, toolbar activation, a basic manager, persistence, and no export-output changes.

**Architecture:** Keep guide data and rule expansion in a pure frontend helper (`canvas-guides.js`). Keep DOM state, toolbar wiring, overlay layout, and manager actions in one focused app controller (`app-canvas-guides-controller.js`). Render guide lines as a viewer-only DOM overlay inside `canvas-area`, synchronized with the preview target rectangle, zoom, fit, and pan.

**Tech Stack:** Plain browser JavaScript modules loaded through the existing `app-loader.js`, localStorage/bridge UI preferences, modular CSS under `css/05-viewer`, Python pytest invoking Node for frontend helper checks.

---

## File Structure

- Create `apps/flatshot-desktop/frontend/canvas-guides.js`
  - Owns default guide systems, normalization, storage filtering, rule expansion, percent formatting/parsing, and derived active-line data.
- Create `apps/flatshot-desktop/frontend/app-canvas-guides-controller.js`
  - Owns guide toolbar state, popover actions, manager draft state, overlay HTML/layout updates, and persistence triggers.
- Create `tests/test_frontend_canvas_guides.py`
  - Node-backed helper tests plus static load-order/contract tests.
- Modify `apps/flatshot-desktop/frontend/index.html`
  - Load `canvas-guides.js` before `mock-data.js` and `app.js`.
  - Add the `Guías` toolbar control.
  - Add the persistent `guide-overlay` element inside `canvas-area`.
  - Add `app-canvas-guides-controller.js` to the loader manifest.
- Modify `apps/flatshot-desktop/frontend/app-loader.js`
  - Load `app-canvas-guides-controller.js` before `app-preview-controller.js`.
- Modify `apps/flatshot-desktop/frontend/app-globals.js`
  - Expose `guideHelpers = window.FlatShotCanvasGuides`.
- Modify `apps/flatshot-desktop/frontend/mock-data.js`
  - Add guide storage keys.
- Modify `apps/flatshot-desktop/frontend/app.js`
  - Initialize guide state from localStorage.
- Modify `apps/flatshot-desktop/frontend/session-snapshot.js`
  - Include guide state in live reload snapshots and restore it safely.
- Modify `apps/flatshot-desktop/frontend/app-bridge-ui-preferences.js`
  - Persist guide preferences through bridge UI preferences without adding them to export preferences.
- Modify `apps/flatshot-desktop/frontend/app-document-events.js`
  - Close the guide popover on outside click.
  - Route guide input/change events to the guide controller.
- Modify `apps/flatshot-desktop/frontend/app-action-dispatcher.js`
  - Add guide actions.
- Modify `apps/flatshot-desktop/frontend/app-render-shell-gallery.js`
  - Render the guide manager modal from the central render pass.
- Modify `apps/flatshot-desktop/frontend/app-viewer-events.js`
  - Close the guide manager on Escape before generic details handling.
- Modify `apps/flatshot-desktop/frontend/app-preview-controller.js`
  - Update toolbar and overlay after preview render and fit-layout recalculation.
- Modify `apps/flatshot-desktop/frontend/app-viewer-state.js`
  - Update the overlay after pan changes.
- Modify `apps/flatshot-desktop/frontend/css/05-viewer/viewer-toolbar.css`
  - Style the compact `Guías` toolbar control and popover.
- Modify `apps/flatshot-desktop/frontend/css/05-viewer/canvas.css`
  - Style the overlay, line rendering, labels, and hidden states.
- Modify `tests/test_frontend_preview_view.py`
  - Extend toolbar contract tests to include `Guías`.
- Modify `tests/test_frontend_session_snapshot.py`
  - Extend snapshot contract for guide state.
- Modify `tests/test_frontend_app_cleanup.py`
  - Extend load-order expectations for `app-canvas-guides-controller.js`.

Do not touch Python image processing, export runners, preview service, naming helpers, or filesystem write behavior for this feature.

---

### Task 1: Pure Guide Helper

**Files:**
- Create: `apps/flatshot-desktop/frontend/canvas-guides.js`
- Create: `tests/test_frontend_canvas_guides.py`
- Modify: `apps/flatshot-desktop/frontend/index.html`
- Modify: `apps/flatshot-desktop/frontend/app-globals.js`

- [ ] **Step 1: Write the failing load-order/global tests**

Add `tests/test_frontend_canvas_guides.py` with these initial tests:

```python
import json
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "apps" / "flatshot-desktop" / "frontend"
HELPER_PATH = FRONTEND_DIR / "canvas-guides.js"
INDEX_PATH = FRONTEND_DIR / "index.html"
APP_GLOBALS_PATH = FRONTEND_DIR / "app-globals.js"


def test_canvas_guides_helper_loads_before_mock_data_and_app():
    html = INDEX_PATH.read_text(encoding="utf-8")

    helper_index = html.index("canvas-guides.js")
    mock_data_index = html.index("mock-data.js")
    app_index = html.index("app.js")

    assert helper_index < mock_data_index < app_index


def test_app_globals_exposes_canvas_guide_helpers():
    source = APP_GLOBALS_PATH.read_text(encoding="utf-8")

    assert "global.guideHelpers = window.FlatShotCanvasGuides;" in source
```

- [ ] **Step 2: Run the load-order/global tests and verify they fail**

Run:

```bash
pytest tests/test_frontend_canvas_guides.py -q
```

Expected: failure because `canvas-guides.js` is not referenced in `index.html` and `guideHelpers` is not exposed in `app-globals.js`.

- [ ] **Step 3: Add the helper script to the static loader section**

In `apps/flatshot-desktop/frontend/index.html`, add the helper before `mock-data.js`:

```html
    <script src="./canvas-guides.js?v=20260616-inspector-fit-height"></script>
    <script src="./mock-data.js?v=20260616-inspector-fit-height"></script>
```

Keep `canvas-guides.js` after `background-presets.js` and before `mock-data.js`.

- [ ] **Step 4: Expose the helper globally**

In `apps/flatshot-desktop/frontend/app-globals.js`, add this line near the other helper aliases:

```js
  global.guideHelpers = window.FlatShotCanvasGuides;
```

- [ ] **Step 5: Create the pure helper with default systems and rule expansion**

Create `apps/flatshot-desktop/frontend/canvas-guides.js`:

```js
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotCanvasGuides = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const DEFAULT_GUIDE_SYSTEMS = [
    {
      id: "center",
      name: "Centro",
      color: "#0f766e",
      opacity: 0.85,
      thickness: 1,
      system: true,
      rules: [
        { id: "center-x", type: "center", axis: "x" },
        { id: "center-y", type: "center", axis: "y" },
      ],
    },
    {
      id: "thirds",
      name: "Tercios",
      color: "#2563eb",
      opacity: 0.7,
      thickness: 1,
      system: true,
      rules: [
        { id: "thirds-x", type: "division", axis: "x", mode: "equal", parts: 3 },
        { id: "thirds-y", type: "division", axis: "y", mode: "equal", parts: 3 },
      ],
    },
    {
      id: "safe-10",
      name: "Márgenes 10%",
      color: "#b45309",
      opacity: 0.78,
      thickness: 1,
      system: true,
      rules: [
        { id: "safe-x", type: "mirror-pair", axis: "x", inset: 0.1 },
        { id: "safe-y", type: "mirror-pair", axis: "y", inset: 0.1 },
      ],
    },
  ];

  function clamp01(value, fallback = 0) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) {
      return fallback;
    }
    return Math.max(0, Math.min(1, numeric));
  }

  function roundPosition(value) {
    return Math.round(clamp01(value) * 10000) / 10000;
  }

  function normalizeAxis(axis) {
    return axis === "y" ? "y" : "x";
  }

  function normalizeColor(value, fallback = "#0f766e") {
    const text = String(value || "").trim();
    return /^#[0-9a-fA-F]{6}$/.test(text) ? text.toLowerCase() : fallback;
  }

  function slugify(value, fallback = "guide") {
    const base = String(value || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
    return base || fallback;
  }

  function uniqueId(base, usedIds) {
    const normalized = slugify(base);
    let candidate = normalized;
    let index = 2;
    while (usedIds.has(candidate)) {
      candidate = `${normalized}-${index}`;
      index += 1;
    }
    usedIds.add(candidate);
    return candidate;
  }

  function normalizeRule(ruleInput, usedRuleIds = new Set()) {
    const rule = ruleInput && typeof ruleInput === "object" ? ruleInput : {};
    const type = ["center", "mirror-pair", "division", "line"].includes(rule.type) ? rule.type : "";
    if (!type) {
      return null;
    }
    const axis = normalizeAxis(rule.axis);
    const id = uniqueId(rule.id || `${type}-${axis}`, usedRuleIds);
    if (type === "center") {
      return { id, type, axis };
    }
    if (type === "mirror-pair") {
      const inset = roundPosition(rule.inset);
      if (inset <= 0 || inset >= 0.5) {
        return null;
      }
      return { id, type, axis, inset };
    }
    if (type === "line") {
      const position = roundPosition(rule.position);
      return { id, type, axis, position };
    }
    if (type === "division") {
      const mode = rule.mode === "custom" ? "custom" : "equal";
      if (mode === "custom") {
        const positions = Array.isArray(rule.positions)
          ? dedupePositions(rule.positions.map(roundPosition).filter((value) => value > 0 && value < 1))
          : [];
        return positions.length ? { id, type, axis, mode, positions } : null;
      }
      const parts = Math.max(2, Math.min(24, Math.round(Number(rule.parts) || 2)));
      return { id, type, axis, mode: "equal", parts };
    }
    return null;
  }

  function dedupePositions(positions, tolerance = 0.0001) {
    const sorted = positions.map(roundPosition).sort((a, b) => a - b);
    return sorted.filter((position, index) => index === 0 || Math.abs(position - sorted[index - 1]) > tolerance);
  }

  function normalizeGuideSystemList(items = [], options = {}) {
    const defaultSystems = (options.defaultSystems || DEFAULT_GUIDE_SYSTEMS).map((system) => ({
      ...system,
      system: true,
      rules: system.rules.map((rule) => ({ ...rule })),
    }));
    const usedIds = new Set(defaultSystems.map((system) => system.id));
    const custom = Array.isArray(items) ? items : [];
    const normalizedCustom = custom
      .filter((item) => item && typeof item === "object" && !defaultSystems.some((system) => system.id === item.id))
      .map((item) => normalizeGuideSystem(item, usedIds))
      .filter(Boolean);
    return [...defaultSystems, ...normalizedCustom];
  }

  function normalizeGuideSystem(input, usedIds = new Set()) {
    const name = String(input?.name || "").trim();
    if (!name) {
      return null;
    }
    const ruleIds = new Set();
    const rules = Array.isArray(input.rules)
      ? input.rules.map((rule) => normalizeRule(rule, ruleIds)).filter(Boolean)
      : [];
    return {
      id: uniqueId(input.id || name, usedIds),
      name,
      color: normalizeColor(input.color),
      opacity: Math.max(0.1, Math.min(1, Number(input.opacity) || 0.85)),
      thickness: Math.max(1, Math.min(4, Math.round(Number(input.thickness) || 1))),
      rules,
    };
  }

  function guideSystemsForStorage(systems = [], options = {}) {
    const defaultIds = new Set((options.defaultSystems || DEFAULT_GUIDE_SYSTEMS).map((system) => system.id));
    return normalizeGuideSystemList(systems, options)
      .filter((system) => !defaultIds.has(system.id))
      .map(({ system, ...item }) => item);
  }

  function readGuideSystems(storage, key, options = {}) {
    const storageHelpers = options.storageHelpers;
    const stored = storageHelpers?.readJson ? storageHelpers.readJson(storage, key, []) : [];
    return normalizeGuideSystemList(stored, options);
  }

  function expandRule(rule) {
    if (rule.type === "center") {
      return [{ axis: rule.axis, position: 0.5, sourceRuleId: rule.id }];
    }
    if (rule.type === "line") {
      return [{ axis: rule.axis, position: roundPosition(rule.position), sourceRuleId: rule.id }];
    }
    if (rule.type === "mirror-pair") {
      return [
        { axis: rule.axis, position: roundPosition(rule.inset), sourceRuleId: rule.id },
        { axis: rule.axis, position: roundPosition(1 - rule.inset), sourceRuleId: rule.id },
      ];
    }
    if (rule.type === "division" && rule.mode === "equal") {
      const positions = [];
      for (let index = 1; index < rule.parts; index += 1) {
        positions.push(roundPosition(index / rule.parts));
      }
      return positions.map((position) => ({ axis: rule.axis, position, sourceRuleId: rule.id }));
    }
    if (rule.type === "division" && rule.mode === "custom") {
      return rule.positions.map((position) => ({ axis: rule.axis, position, sourceRuleId: rule.id }));
    }
    return [];
  }

  function activeGuideSystems(systems = [], activeIds = []) {
    const ids = new Set(Array.isArray(activeIds) ? activeIds.map(String) : []);
    return systems.filter((system) => ids.has(system.id));
  }

  function guideLinesForSystems(systems = [], activeIds = []) {
    return activeGuideSystems(systems, activeIds).flatMap((system) => (
      system.rules.flatMap((rule) => expandRule(rule)).map((line) => ({
        ...line,
        systemId: system.id,
        systemName: system.name,
        color: system.color,
        opacity: system.opacity,
        thickness: system.thickness,
      }))
    ));
  }

  function normalizeActiveGuideSystemIds(ids = [], systems = []) {
    const available = new Set(systems.map((system) => system.id));
    return Array.isArray(ids) ? ids.map(String).filter((id, index, list) => available.has(id) && list.indexOf(id) === index) : [];
  }

  function formatPercent(value) {
    const percent = roundPosition(value) * 100;
    return `${Number(percent.toFixed(2))}%`;
  }

  function parsePercent(value, fallback = 0) {
    const text = String(value ?? "").replace("%", "").trim();
    const numeric = Number(text);
    return Number.isFinite(numeric) ? roundPosition(numeric / 100) : fallback;
  }

  return {
    DEFAULT_GUIDE_SYSTEMS,
    activeGuideSystems,
    expandRule,
    formatPercent,
    guideLinesForSystems,
    guideSystemsForStorage,
    normalizeActiveGuideSystemIds,
    normalizeGuideSystemList,
    parsePercent,
    readGuideSystems,
  };
});
```

- [ ] **Step 6: Add the pure helper contract test**

Append this test to `tests/test_frontend_canvas_guides.py`:

```python
@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_canvas_guide_helpers_normalize_and_expand_rules():
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(HELPER_PATH))});

const systems = helpers.normalizeGuideSystemList([
  {{
    id: "center",
    name: "Centro roto",
    color: "#ffffff",
    rules: [{{ type: "line", axis: "x", position: 0.2 }}],
  }},
  {{
    id: "market",
    name: "Marketplace",
    color: "#ABCDEF",
    opacity: 2,
    thickness: 9,
    rules: [
      {{ id: "top", type: "mirror-pair", axis: "y", inset: 0.12 }},
      {{ id: "thirds", type: "division", axis: "x", mode: "equal", parts: 3 }},
      {{ id: "custom", type: "division", axis: "y", mode: "custom", positions: [0.78, 0.22, 0.22] }},
      {{ id: "bad", type: "mirror-pair", axis: "x", inset: 0.6 }},
    ],
  }},
]);

assert.equal(systems[0].id, "center");
assert.equal(systems[0].system, true);
assert.equal(systems[0].name, "Centro");
assert.equal(systems.at(-1).id, "market");
assert.equal(systems.at(-1).color, "#abcdef");
assert.equal(systems.at(-1).opacity, 1);
assert.equal(systems.at(-1).thickness, 4);
assert.equal(systems.at(-1).rules.length, 3);

const activeIds = helpers.normalizeActiveGuideSystemIds(["market", "missing", "market"], systems);
assert.deepEqual(activeIds, ["market"]);

const lines = helpers.guideLinesForSystems(systems, activeIds).map((line) => `${line.axis}:${line.position}`);
assert.deepEqual(lines, ["y:0.12", "y:0.88", "x:0.3333", "x:0.6667", "y:0.22", "y:0.78"]);
assert.equal(helpers.formatPercent(0.33333), "33.33%");
assert.equal(helpers.parsePercent("12.5%"), 0.125);

const storage = helpers.guideSystemsForStorage(systems);
assert.deepEqual(storage.map((system) => system.id), ["market"]);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
```

- [ ] **Step 7: Run the helper tests and verify they pass**

Run:

```bash
pytest tests/test_frontend_canvas_guides.py -q
```

Expected: all tests in `test_frontend_canvas_guides.py` pass.

- [ ] **Step 8: Commit Task 1**

```bash
git add apps/flatshot-desktop/frontend/canvas-guides.js apps/flatshot-desktop/frontend/index.html apps/flatshot-desktop/frontend/app-globals.js tests/test_frontend_canvas_guides.py
git commit -m "Add canvas guide helper contracts"
```

---

### Task 2: State, Storage, Session Snapshot, And Bridge Preferences

**Files:**
- Modify: `apps/flatshot-desktop/frontend/mock-data.js`
- Modify: `apps/flatshot-desktop/frontend/app.js`
- Modify: `apps/flatshot-desktop/frontend/session-snapshot.js`
- Modify: `apps/flatshot-desktop/frontend/app-bridge-ui-preferences.js`
- Modify: `tests/test_frontend_session_snapshot.py`
- Modify: `tests/test_frontend_canvas_guides.py`

- [ ] **Step 1: Write failing static tests for storage keys and bridge preference separation**

Append these tests to `tests/test_frontend_canvas_guides.py`:

```python
def test_canvas_guides_storage_keys_are_defined():
    source = (FRONTEND_DIR / "mock-data.js").read_text(encoding="utf-8")

    assert 'guideSystems: "flatshot.guideSystems"' in source
    assert 'activeGuideSystems: "flatshot.activeGuideSystemIds"' in source
    assert 'guidesVisible: "flatshot.guidesVisible"' in source


def test_guide_preferences_are_ui_preferences_not_export_preferences():
    source = (FRONTEND_DIR / "app-bridge-ui-preferences.js").read_text(encoding="utf-8")

    payload_start = source.index("function uiPreferencesPayload()")
    payload_end = source.index("function cacheUiPreferences", payload_start)
    payload_block = source[payload_start:payload_end]
    export_start = payload_block.index("exportPreferences:")
    export_block = payload_block[export_start:]

    assert "guideSystems:" in payload_block
    assert "activeGuideSystemIds:" in payload_block
    assert "guidesVisible:" in payload_block
    assert "guideSystems:" not in export_block
    assert "activeGuideSystemIds:" not in export_block
    assert "guidesVisible:" not in export_block
```

- [ ] **Step 2: Extend the session snapshot test before implementation**

In `tests/test_frontend_session_snapshot.py`, add guide state to the existing `state` object:

```js
  guidesVisible: true,
  activeGuideSystemIds: ["center"],
  guideSystems: [{{ id: "center", name: "Centro" }}],
```

Add these assertions after the existing snapshot assertions:

```js
assert.equal(snapshot.state.guidesVisible, true);
assert.deepEqual(snapshot.state.activeGuideSystemIds, ["center"]);
assert.deepEqual(snapshot.state.guideSystems, [{{ id: "center", name: "Centro" }}]);
```

Pass guide normalizers into `restoreSessionState`:

```js
  normalizeGuideSystemList: (items) => items,
  normalizeActiveGuideSystemIds: (ids) => ids,
```

Add these restored-state assertions:

```js
assert.equal(restored.patch.guidesVisible, true);
assert.deepEqual(restored.patch.activeGuideSystemIds, ["center"]);
assert.deepEqual(restored.patch.guideSystems, [{{ id: "center", name: "Centro" }}]);
```

- [ ] **Step 3: Run the targeted tests and verify they fail**

Run:

```bash
pytest tests/test_frontend_canvas_guides.py tests/test_frontend_session_snapshot.py -q
```

Expected: failures because guide storage keys, UI preference payload fields, and snapshot fields are not wired yet.

- [ ] **Step 4: Add guide storage keys**

In `apps/flatshot-desktop/frontend/mock-data.js`, add the keys inside `global.STORAGE_KEYS`:

```js
  guideSystems: "flatshot.guideSystems",
  activeGuideSystems: "flatshot.activeGuideSystemIds",
  guidesVisible: "flatshot.guidesVisible",
```

- [ ] **Step 5: Initialize guide state in app bootstrap state**

In `apps/flatshot-desktop/frontend/app.js`, add initial constants after `initialBackgroundPresets`:

```js
const initialGuideSystems = guideHelpers.readGuideSystems(window.localStorage, STORAGE_KEYS.guideSystems, {
  storageHelpers,
});
const initialActiveGuideSystemIds = guideHelpers.normalizeActiveGuideSystemIds(
  storageHelpers.readJson(window.localStorage, STORAGE_KEYS.activeGuideSystems, ["center"]),
  initialGuideSystems
);
const initialGuidesVisible = storageHelpers.readValue(window.localStorage, STORAGE_KEYS.guidesVisible) !== "0";
```

Add these properties to `state` near other viewer state:

```js
  guidesVisible: initialGuidesVisible,
  activeGuideSystemIds: initialActiveGuideSystemIds,
  guideSystems: initialGuideSystems,
  guideManagerOpen: false,
  guideDraft: null,
```

- [ ] **Step 6: Include guide state in session snapshots**

In `apps/flatshot-desktop/frontend/session-snapshot.js`, add these keys to `SESSION_STATE_KEYS` after `previewBg`:

```js
    "guidesVisible",
    "activeGuideSystemIds",
    "guideSystems",
```

Inside `restoreSessionState`, add option defaults near the other normalizers:

```js
    const normalizeGuideSystemList = options.normalizeGuideSystemList || ((value) => Array.isArray(value) ? value : []);
    const normalizeActiveGuideSystemIds = options.normalizeActiveGuideSystemIds || ((ids) => Array.isArray(ids) ? ids : []);
```

Before the return object, add:

```js
    const restoredGuideSystems = normalizeGuideSystemList(restored.guideSystems || currentState.guideSystems || []);
    const restoredActiveGuideSystemIds = normalizeActiveGuideSystemIds(
      restored.activeGuideSystemIds || currentState.activeGuideSystemIds || [],
      restoredGuideSystems
    );
```

Add to the `patch` object after `previewBg`:

```js
        guidesVisible: restored.guidesVisible === undefined ? currentState.guidesVisible !== false : Boolean(restored.guidesVisible),
        activeGuideSystemIds: restoredActiveGuideSystemIds,
        guideSystems: restoredGuideSystems,
        guideManagerOpen: false,
        guideDraft: null,
```

- [ ] **Step 7: Add guide preferences to bridge UI preferences**

In `apps/flatshot-desktop/frontend/app-bridge-ui-preferences.js`, add these fields to `uiPreferencesPayload()` above `exportPreferences`:

```js
    guideSystems: guideHelpers.guideSystemsForStorage(state.guideSystems),
    activeGuideSystemIds: state.activeGuideSystemIds,
    guidesVisible: state.guidesVisible,
```

In `cacheUiPreferences`, add:

```js
  if (Array.isArray(source.guideSystems)) {
    storageHelpers.writeJson(window.localStorage, STORAGE_KEYS.guideSystems, guideHelpers.guideSystemsForStorage(source.guideSystems));
  }
  if (Array.isArray(source.activeGuideSystemIds)) {
    storageHelpers.writeJson(window.localStorage, STORAGE_KEYS.activeGuideSystems, source.activeGuideSystemIds);
  }
  if (source.guidesVisible !== undefined) {
    storageHelpers.writeValue(window.localStorage, STORAGE_KEYS.guidesVisible, source.guidesVisible === false ? "0" : "1");
  }
```

In `applyBridgeUiPreferences`, after background preset restore, add:

```js
  if (Array.isArray(source.guideSystems)) {
    state.guideSystems = guideHelpers.normalizeGuideSystemList(source.guideSystems);
  }
  if (Array.isArray(source.activeGuideSystemIds)) {
    state.activeGuideSystemIds = guideHelpers.normalizeActiveGuideSystemIds(source.activeGuideSystemIds, state.guideSystems);
  }
  if (source.guidesVisible !== undefined) {
    state.guidesVisible = Boolean(source.guidesVisible);
  }
```

- [ ] **Step 8: Run targeted persistence tests**

Run:

```bash
pytest tests/test_frontend_canvas_guides.py tests/test_frontend_session_snapshot.py -q
```

Expected: all targeted tests pass.

- [ ] **Step 9: Commit Task 2**

```bash
git add apps/flatshot-desktop/frontend/mock-data.js apps/flatshot-desktop/frontend/app.js apps/flatshot-desktop/frontend/session-snapshot.js apps/flatshot-desktop/frontend/app-bridge-ui-preferences.js tests/test_frontend_canvas_guides.py tests/test_frontend_session_snapshot.py
git commit -m "Persist canvas guide preferences"
```

---

### Task 3: Toolbar Control And DOM Overlay

**Files:**
- Modify: `apps/flatshot-desktop/frontend/index.html`
- Modify: `apps/flatshot-desktop/frontend/app-loader.js`
- Create: `apps/flatshot-desktop/frontend/app-canvas-guides-controller.js`
- Modify: `apps/flatshot-desktop/frontend/app-preview-controller.js`
- Modify: `apps/flatshot-desktop/frontend/app-viewer-state.js`
- Modify: `tests/test_frontend_canvas_guides.py`
- Modify: `tests/test_frontend_preview_view.py`
- Modify: `tests/test_frontend_app_cleanup.py`

- [ ] **Step 1: Write failing toolbar, overlay, and loader tests**

Append this test to `tests/test_frontend_canvas_guides.py`:

```python
def test_canvas_guides_toolbar_overlay_and_controller_are_wired():
    html = INDEX_PATH.read_text(encoding="utf-8")
    loader = (FRONTEND_DIR / "app-loader.js").read_text(encoding="utf-8")

    assert 'class="viewer-control-group viewer-guides"' in html
    assert 'id="guide-overlay"' in html
    assert 'data-action="toggle-guides"' in html
    assert 'data-guide-system-list' in html
    assert loader.index("app-canvas-guides-controller.js") < loader.index("app-preview-controller.js")
```

In `tests/test_frontend_preview_view.py`, update `test_preview_toolbar_keeps_compact_context_labels`:

```python
    for label in ("Fondo", "Guías", "Imagen", "Encajar", "Zoom"):
        assert f'class="viewer-control-label">{label}</span>' in html
```

In `tests/test_frontend_app_cleanup.py`, add `"app-canvas-guides-controller.js"` to `expected_order` between `"app-modal-render-controller.js"` and `"app-preview-controller.js"`.

- [ ] **Step 2: Run the targeted tests and verify they fail**

Run:

```bash
pytest tests/test_frontend_canvas_guides.py tests/test_frontend_preview_view.py tests/test_frontend_app_cleanup.py -q
```

Expected: failures because toolbar, overlay, controller, and loader ordering are not wired.

- [ ] **Step 3: Add the toolbar control and overlay element**

In `apps/flatshot-desktop/frontend/index.html`, add this control immediately after the background switch and before `zoom-controls`:

```html
              <details class="viewer-control-group viewer-guides" id="viewer-guides-menu">
                <summary aria-label="Guías del lienzo">
                  <span class="viewer-control-label">Guías</span>
                  <button type="button" data-action="toggle-guides" id="guides-toggle" aria-pressed="true" title="Mostrar u ocultar guías">On</button>
                  <span id="guides-active-count" class="viewer-guides-count">0</span>
                </summary>
                <div class="viewer-guides-popover" role="menu" aria-label="Sistemas de guías">
                  <div data-guide-system-list></div>
                  <button type="button" data-action="open-guide-manager">Gestionar guías</button>
                </div>
              </details>
```

Inside `canvas-area`, add the overlay before `preview-canvas`:

```html
            <div class="guide-overlay" id="guide-overlay" aria-hidden="true"></div>
```

- [ ] **Step 4: Add the app controller to loader order and manifest**

In `apps/flatshot-desktop/frontend/app-loader.js`, insert:

```js
    "app-canvas-guides-controller.js",
```

between `"app-modal-render-controller.js"` and `"app-preview-controller.js"`.

Make the same insertion in the JSON manifest inside `apps/flatshot-desktop/frontend/index.html`.

- [ ] **Step 5: Create the guide controller with toolbar and overlay rendering**

Create `apps/flatshot-desktop/frontend/app-canvas-guides-controller.js`:

```js
function isGuideOverlayAvailable() {
  return Boolean(selectedImage()) && !["empty", "error", "loading"].includes(state.previewStatus);
}

function activeGuideSystems() {
  return guideHelpers.activeGuideSystems(state.guideSystems, state.activeGuideSystemIds);
}

function renderGuideToolbarState() {
  const menu = $("#viewer-guides-menu");
  const toggle = $("#guides-toggle");
  const count = $("#guides-active-count");
  const list = $("[data-guide-system-list]");
  const disabled = !isGuideOverlayAvailable();
  if (menu) {
    menu.classList.toggle("is-disabled", disabled);
  }
  if (toggle) {
    toggle.textContent = state.guidesVisible ? "On" : "Off";
    toggle.disabled = disabled;
    toggle.classList.toggle("active", state.guidesVisible);
    toggle.setAttribute("aria-pressed", state.guidesVisible ? "true" : "false");
  }
  if (count) {
    count.textContent = String(activeGuideSystems().length);
  }
  if (list) {
    list.innerHTML = state.guideSystems.map((system) => `
      <label class="viewer-guide-system-option">
        <input type="checkbox" data-guide-system-toggle="${previewViewHelpers.escapeHtml(system.id)}" ${state.activeGuideSystemIds.includes(system.id) ? "checked" : ""} />
        <span class="viewer-guide-system-swatch" style="--guide-system-color: ${previewViewHelpers.escapeHtml(system.color)}"></span>
        <span>${previewViewHelpers.escapeHtml(system.name)}</span>
      </label>
    `).join("");
  }
}

function renderGuideOverlay() {
  const overlay = $("#guide-overlay");
  const canvas = $("#preview-canvas");
  const target = canvas?.querySelector(".preview-image, .mock-product");
  if (!overlay || !canvas || !target || !state.guidesVisible || !isGuideOverlayAvailable()) {
    if (overlay) {
      overlay.hidden = true;
      overlay.innerHTML = "";
    }
    return;
  }
  const lines = guideHelpers.guideLinesForSystems(state.guideSystems, state.activeGuideSystemIds);
  overlay.hidden = !lines.length;
  overlay.innerHTML = lines.map((line) => `
    <div class="guide-line guide-line--${line.axis}" style="
      --guide-position: ${line.position};
      --guide-color: ${previewViewHelpers.escapeHtml(line.color)};
      --guide-opacity: ${line.opacity};
      --guide-thickness: ${line.thickness}px;
    "></div>
  `).join("");
  updateGuideOverlayLayout();
}

function updateGuideOverlayLayout() {
  const overlay = $("#guide-overlay");
  const canvas = $("#preview-canvas");
  const target = canvas?.querySelector(".preview-image, .mock-product");
  if (!overlay || !canvas || !target || overlay.hidden) {
    return;
  }
  const canvasRect = canvas.getBoundingClientRect();
  const targetRect = target.getBoundingClientRect();
  if (!canvasRect.width || !canvasRect.height || !targetRect.width || !targetRect.height) {
    overlay.hidden = true;
    return;
  }
  overlay.style.left = `${Math.round(targetRect.left - canvasRect.left)}px`;
  overlay.style.top = `${Math.round(targetRect.top - canvasRect.top)}px`;
  overlay.style.width = `${Math.round(targetRect.width)}px`;
  overlay.style.height = `${Math.round(targetRect.height)}px`;
}
```

- [ ] **Step 6: Call guide rendering from preview and pan updates**

In `apps/flatshot-desktop/frontend/app-preview-controller.js`, after preview toolbar background state updates, call:

```js
  renderGuideToolbarState();
```

After each `canvas.innerHTML = ...` branch currently followed by `queueFitZoomRefresh(); return;`, call `renderGuideOverlay();` before `queueFitZoomRefresh();`.

In `updateFitZoomReadout()`, after `applyViewerPanDom();`, add:

```js
    updateGuideOverlayLayout();
```

At the end of `updateFitZoomReadout()`, after the auto-mode branch updates `fitZoom`, add:

```js
  renderGuideOverlay();
```

In `apps/flatshot-desktop/frontend/app-viewer-state.js`, at the end of `applyViewerPanDom()`, add:

```js
  if (typeof updateGuideOverlayLayout === "function") {
    updateGuideOverlayLayout();
  }
```

- [ ] **Step 7: Run targeted tests**

Run:

```bash
pytest tests/test_frontend_canvas_guides.py tests/test_frontend_preview_view.py tests/test_frontend_app_cleanup.py -q
```

Expected: targeted tests pass.

- [ ] **Step 8: Commit Task 3**

```bash
git add apps/flatshot-desktop/frontend/index.html apps/flatshot-desktop/frontend/app-loader.js apps/flatshot-desktop/frontend/app-canvas-guides-controller.js apps/flatshot-desktop/frontend/app-preview-controller.js apps/flatshot-desktop/frontend/app-viewer-state.js tests/test_frontend_canvas_guides.py tests/test_frontend_preview_view.py tests/test_frontend_app_cleanup.py
git commit -m "Render canvas guide overlay controls"
```

---

### Task 4: Guide Activation Actions And Popover Robustness

**Files:**
- Modify: `apps/flatshot-desktop/frontend/app-canvas-guides-controller.js`
- Modify: `apps/flatshot-desktop/frontend/app-action-dispatcher.js`
- Modify: `apps/flatshot-desktop/frontend/app-document-events.js`
- Modify: `apps/flatshot-desktop/frontend/app-render-shell-gallery.js`
- Modify: `apps/flatshot-desktop/frontend/app-viewer-events.js`
- Modify: `tests/test_frontend_canvas_guides.py`

- [ ] **Step 1: Write failing interaction contract tests**

Append these tests to `tests/test_frontend_canvas_guides.py`:

```python
def test_canvas_guide_actions_are_registered_and_popover_closes_transiently():
    dispatcher = (FRONTEND_DIR / "app-action-dispatcher.js").read_text(encoding="utf-8")
    document_events = (FRONTEND_DIR / "app-document-events.js").read_text(encoding="utf-8")

    assert '"toggle-guides": () => toggleGuidesVisible()' in dispatcher
    assert '"open-guide-manager": () => openGuideManager()' in dispatcher
    assert 'details.viewer-guides[open]' in document_events
    assert "handleGuideSystemToggle" in document_events


def test_canvas_guide_controller_persists_after_mutations():
    source = (FRONTEND_DIR / "app-canvas-guides-controller.js").read_text(encoding="utf-8")

    assert "function persistGuidePreferences()" in source
    assert "storageHelpers.writeJson(window.localStorage, STORAGE_KEYS.activeGuideSystems" in source
    assert "scheduleBridgeUiPreferencesSave();" in source
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```bash
pytest tests/test_frontend_canvas_guides.py -q
```

Expected: failures because actions and persistence helpers are not implemented.

- [ ] **Step 3: Add persistence and activation functions**

Append to `apps/flatshot-desktop/frontend/app-canvas-guides-controller.js`:

```js
function persistGuidePreferences() {
  storageHelpers.writeJson(window.localStorage, STORAGE_KEYS.guideSystems, guideHelpers.guideSystemsForStorage(state.guideSystems));
  storageHelpers.writeJson(window.localStorage, STORAGE_KEYS.activeGuideSystems, state.activeGuideSystemIds);
  storageHelpers.writeValue(window.localStorage, STORAGE_KEYS.guidesVisible, state.guidesVisible ? "1" : "0");
  scheduleBridgeUiPreferencesSave();
}

function toggleGuidesVisible() {
  state.guidesVisible = !state.guidesVisible;
  state.statusText = state.guidesVisible ? "Guías visibles" : "Guías ocultas";
  persistGuidePreferences();
  render();
}

function setGuideSystemActive(systemId, active) {
  const ids = new Set(state.activeGuideSystemIds);
  if (active) {
    ids.add(systemId);
  } else {
    ids.delete(systemId);
  }
  state.activeGuideSystemIds = guideHelpers.normalizeActiveGuideSystemIds([...ids], state.guideSystems);
  state.statusText = `${activeGuideSystems().length} sistemas de guías activos`;
  persistGuidePreferences();
  render();
}

function openGuideManager() {
  state.guideManagerOpen = true;
  state.guideDraft = null;
  state.statusText = "Gestionar guías";
  const menu = $("#viewer-guides-menu");
  if (menu) {
    menu.open = false;
  }
  render();
}

function closeGuideManager() {
  state.guideManagerOpen = false;
  state.guideDraft = null;
  render();
}
```

- [ ] **Step 4: Register guide actions**

In `apps/flatshot-desktop/frontend/app-action-dispatcher.js`, add entries near viewer actions:

```js
  "toggle-guides": () => toggleGuidesVisible(),
  "open-guide-manager": () => openGuideManager(),
  "close-guide-manager": () => closeGuideManager(),
```

- [ ] **Step 5: Close guide popover on outside click**

In `apps/flatshot-desktop/frontend/app-document-events.js`, update `closeTransientDetails` selector:

```js
  document.querySelectorAll("details.format-more-menu[open], details.debug-panel[open], details.viewer-guides[open]").forEach((details) => {
```

- [ ] **Step 6: Route guide checkbox changes**

In `apps/flatshot-desktop/frontend/app-document-events.js`, add:

```js
function handleGuideSystemToggle(target) {
  const systemId = target.dataset.guideSystemToggle;
  if (!systemId) {
    return false;
  }
  setGuideSystemActive(systemId, target.checked);
  return true;
}
```

In `handleDocumentChange`, before output profile change handling, add:

```js
  if (event.target?.matches?.("[data-guide-system-toggle]")) {
    handleGuideSystemToggle(event.target);
    return;
  }
```

- [ ] **Step 7: Run targeted interaction tests**

Run:

```bash
pytest tests/test_frontend_canvas_guides.py -q
```

Expected: all guide tests pass.

- [ ] **Step 8: Commit Task 4**

```bash
git add apps/flatshot-desktop/frontend/app-canvas-guides-controller.js apps/flatshot-desktop/frontend/app-action-dispatcher.js apps/flatshot-desktop/frontend/app-document-events.js tests/test_frontend_canvas_guides.py
git commit -m "Wire canvas guide activation actions"
```

---

### Task 5: Guide Manager Drafts And Rule Editing

**Files:**
- Modify: `apps/flatshot-desktop/frontend/app-canvas-guides-controller.js`
- Modify: `apps/flatshot-desktop/frontend/app-action-dispatcher.js`
- Modify: `apps/flatshot-desktop/frontend/app-document-events.js`
- Modify: `tests/test_frontend_canvas_guides.py`

- [ ] **Step 1: Write failing manager contract tests**

Append this test to `tests/test_frontend_canvas_guides.py`:

```python
def test_canvas_guide_manager_supports_system_and_rule_actions():
    controller = (FRONTEND_DIR / "app-canvas-guides-controller.js").read_text(encoding="utf-8")
    dispatcher = (FRONTEND_DIR / "app-action-dispatcher.js").read_text(encoding="utf-8")
    document_events = (FRONTEND_DIR / "app-document-events.js").read_text(encoding="utf-8")
    render_source = (FRONTEND_DIR / "app-render-shell-gallery.js").read_text(encoding="utf-8")
    keydown_source = (FRONTEND_DIR / "app-viewer-events.js").read_text(encoding="utf-8")

    for function_name in [
        "renderGuideManager",
        "newGuideSystem",
        "editGuideSystem",
        "duplicateGuideSystem",
        "deleteGuideSystem",
        "saveGuideDraft",
        "addGuideCenterRule",
        "addGuideMirrorPairRule",
        "addGuideDivisionRule",
        "addGuideLineRule",
    ]:
        assert f"function {function_name}" in controller

    for action in [
        "new-guide-system",
        "duplicate-guide-system",
        "delete-guide-system",
        "save-guide-draft",
        "add-guide-center",
        "add-guide-pair",
        "add-guide-division",
        "add-guide-line",
    ]:
        assert f'"{action}"' in dispatcher

    assert "updateGuideDraftFromFields" in document_events
    assert "renderGuideManager();" in render_source
    assert "closeGuideManager();" in keydown_source
```

- [ ] **Step 2: Run manager tests and verify they fail**

Run:

```bash
pytest tests/test_frontend_canvas_guides.py -q
```

Expected: failure because the manager functions and actions are not implemented.

- [ ] **Step 3: Add manager rendering**

Append to `apps/flatshot-desktop/frontend/app-canvas-guides-controller.js`:

```js
function renderGuideManager() {
  let modal = $("#guide-manager-modal");
  if (!state.guideManagerOpen) {
    if (modal) {
      modal.remove();
    }
    return;
  }
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "guide-manager-modal";
    modal.className = "modal-backdrop guide-manager-modal";
    document.body.appendChild(modal);
  }
  const draft = state.guideDraft;
  modal.innerHTML = `
    <div class="modal-panel guide-manager-panel" role="dialog" aria-modal="true" aria-labelledby="guide-manager-title">
      <header class="modal-header">
        <div>
          <span class="eyebrow">Visor</span>
          <h2 id="guide-manager-title">Guías del lienzo</h2>
        </div>
        <button type="button" data-action="close-guide-manager" class="icon-button" aria-label="Cerrar guías" title="Cerrar">×</button>
      </header>
      <div class="guide-manager-body">
        <section class="guide-system-list" aria-label="Sistemas de guías">
          ${state.guideSystems.map((system) => guideSystemManagerRow(system)).join("")}
          <button type="button" data-action="new-guide-system">Nuevo sistema</button>
        </section>
        <section class="guide-draft-panel" aria-label="Editor de guías">
          ${draft ? guideDraftFormHtml(draft) : "<p>Selecciona o crea un sistema para editarlo.</p>"}
        </section>
      </div>
    </div>
  `;
}

function guideSystemManagerRow(system) {
  const systemLocked = system.system ? "disabled" : "";
  return `
    <article class="guide-system-row">
      <div>
        <strong>${previewViewHelpers.escapeHtml(system.name)}</strong>
        <span>${system.rules.length} reglas</span>
      </div>
      <button type="button" data-action="edit-guide-system" data-guide-system-id="${previewViewHelpers.escapeHtml(system.id)}">Editar</button>
      <button type="button" data-action="duplicate-guide-system" data-guide-system-id="${previewViewHelpers.escapeHtml(system.id)}">Duplicar</button>
      <button type="button" data-action="delete-guide-system" data-guide-system-id="${previewViewHelpers.escapeHtml(system.id)}" ${systemLocked}>Eliminar</button>
    </article>
  `;
}

function guideDraftFormHtml(draft) {
  return `
    <form id="guide-draft-form">
      <label>Nombre <input type="text" data-guide-draft-field="name" value="${previewViewHelpers.escapeHtml(draft.name)}" /></label>
      <label>Color <input type="color" data-guide-draft-field="color" value="${previewViewHelpers.escapeHtml(draft.color)}" /></label>
      <label>Opacidad <input type="number" min="10" max="100" step="5" data-guide-draft-field="opacity" value="${Math.round(draft.opacity * 100)}" /></label>
      <label>Grosor <input type="number" min="1" max="4" step="1" data-guide-draft-field="thickness" value="${draft.thickness}" /></label>
      <div class="guide-rule-actions">
        <button type="button" data-action="add-guide-pair">Añadir par</button>
        <button type="button" data-action="add-guide-division">Dividir lienzo</button>
        <button type="button" data-action="add-guide-center">Añadir centro</button>
        <button type="button" data-action="add-guide-line">Añadir línea libre</button>
      </div>
      <div class="guide-rule-list">
        ${draft.rules.map((rule) => guideRuleEditorHtml(rule)).join("")}
      </div>
      <footer class="guide-manager-actions">
        <button type="button" data-action="save-guide-draft" class="primary">Guardar sistema</button>
      </footer>
    </form>
  `;
}
```

- [ ] **Step 4: Add draft mutation functions**

Append:

```js
function draftFromSystem(system) {
  return JSON.parse(JSON.stringify(system));
}

function editableGuideDraft() {
  if (!state.guideDraft) {
    newGuideSystem();
  }
  return state.guideDraft;
}

function newGuideSystem() {
  state.guideDraft = {
    id: "",
    name: "Nuevo sistema",
    color: "#0f766e",
    opacity: 0.85,
    thickness: 1,
    rules: [],
  };
  renderGuideManager();
}

function editGuideSystem(target) {
  const system = state.guideSystems.find((item) => item.id === target?.dataset?.guideSystemId);
  if (!system) {
    return;
  }
  state.guideDraft = draftFromSystem(system);
  renderGuideManager();
}

function duplicateGuideSystem(target) {
  const system = state.guideSystems.find((item) => item.id === target?.dataset?.guideSystemId);
  if (!system) {
    return;
  }
  state.guideDraft = {
    ...draftFromSystem(system),
    id: "",
    system: false,
    name: `${system.name} copia`,
  };
  renderGuideManager();
}

function deleteGuideSystem(target) {
  const systemId = target?.dataset?.guideSystemId;
  const system = state.guideSystems.find((item) => item.id === systemId);
  if (!system || system.system) {
    return;
  }
  state.guideSystems = state.guideSystems.filter((item) => item.id !== systemId);
  state.activeGuideSystemIds = state.activeGuideSystemIds.filter((id) => id !== systemId);
  persistGuidePreferences();
  render();
}
```

- [ ] **Step 5: Add rule editor helpers and save**

Append:

```js
function addGuideCenterRule() {
  editableGuideDraft().rules.push({ id: `center-${Date.now()}`, type: "center", axis: "x" });
  editableGuideDraft().rules.push({ id: `center-y-${Date.now()}`, type: "center", axis: "y" });
  renderGuideManager();
}

function addGuideMirrorPairRule() {
  editableGuideDraft().rules.push({ id: `pair-${Date.now()}`, type: "mirror-pair", axis: "y", inset: 0.1 });
  renderGuideManager();
}

function addGuideDivisionRule() {
  editableGuideDraft().rules.push({ id: `division-${Date.now()}`, type: "division", axis: "x", mode: "equal", parts: 3 });
  renderGuideManager();
}

function addGuideLineRule() {
  editableGuideDraft().rules.push({ id: `line-${Date.now()}`, type: "line", axis: "x", position: 0.5 });
  renderGuideManager();
}

function guideRuleEditorHtml(rule) {
  const label = rule.type === "mirror-pair"
    ? `Par ${rule.axis.toUpperCase()} ${guideHelpers.formatPercent(rule.inset)}`
    : rule.type === "division"
      ? `División ${rule.axis.toUpperCase()}`
      : rule.type === "center"
        ? `Centro ${rule.axis.toUpperCase()}`
        : `Línea ${rule.axis.toUpperCase()} ${guideHelpers.formatPercent(rule.position)}`;
  return `<div class="guide-rule-row">${previewViewHelpers.escapeHtml(label)}</div>`;
}

function updateGuideDraftFromFields() {
  const draft = state.guideDraft;
  if (!draft) {
    return;
  }
  const form = $("#guide-draft-form");
  if (!form) {
    return;
  }
  const name = form.querySelector('[data-guide-draft-field="name"]')?.value || "";
  const color = form.querySelector('[data-guide-draft-field="color"]')?.value || "#0f766e";
  const opacity = Number(form.querySelector('[data-guide-draft-field="opacity"]')?.value || 85) / 100;
  const thickness = Number(form.querySelector('[data-guide-draft-field="thickness"]')?.value || 1);
  state.guideDraft = { ...draft, name, color, opacity, thickness };
}

function saveGuideDraft() {
  updateGuideDraftFromFields();
  const normalized = guideHelpers.normalizeGuideSystemList([state.guideDraft], { defaultSystems: [] })[0];
  if (!normalized) {
    state.statusText = "Revisa el sistema de guías";
    renderGuideManager();
    return;
  }
  const existingIndex = state.guideSystems.findIndex((system) => system.id === state.guideDraft.id && !system.system);
  if (existingIndex >= 0) {
    state.guideSystems = state.guideSystems.map((system, index) => index === existingIndex ? normalized : system);
  } else {
    state.guideSystems = guideHelpers.normalizeGuideSystemList([...state.guideSystems, normalized]);
  }
  state.activeGuideSystemIds = guideHelpers.normalizeActiveGuideSystemIds(
    [...state.activeGuideSystemIds, normalized.id],
    state.guideSystems
  );
  state.guideDraft = draftFromSystem(normalized);
  state.statusText = "Sistema de guías guardado";
  persistGuidePreferences();
  render();
}
```

- [ ] **Step 6: Register manager actions and input updates**

In `apps/flatshot-desktop/frontend/app-action-dispatcher.js`, add:

```js
  "new-guide-system": () => newGuideSystem(),
  "edit-guide-system": (target) => editGuideSystem(target),
  "duplicate-guide-system": (target) => duplicateGuideSystem(target),
  "delete-guide-system": (target) => deleteGuideSystem(target),
  "save-guide-draft": () => saveGuideDraft(),
  "add-guide-center": () => addGuideCenterRule(),
  "add-guide-pair": () => addGuideMirrorPairRule(),
  "add-guide-division": () => addGuideDivisionRule(),
  "add-guide-line": () => addGuideLineRule(),
```

In `apps/flatshot-desktop/frontend/app-document-events.js`, add to `handleDocumentInput`:

```js
  if (event.target.closest?.("#guide-draft-form")) {
    updateGuideDraftFromFields();
    return;
  }
```

In `handleDocumentClick`, add after modal backdrop checks:

```js
  if (target.id === "guide-manager-modal") {
    closeGuideManager();
    return;
  }
```

In `apps/flatshot-desktop/frontend/app-render-shell-gallery.js`, call the manager renderer from the central `render()` function after the other modal renderers:

```js
  renderQaLab();
  renderGuideManager();
  renderAppSettings();
```

In `apps/flatshot-desktop/frontend/app-viewer-events.js`, add this branch to the Escape handling block before `state.appSettingsOpen`:

```js
    if (state.guideManagerOpen) {
      closeGuideManager();
      event.preventDefault();
      return;
    }
```

- [ ] **Step 7: Run manager contract tests**

Run:

```bash
pytest tests/test_frontend_canvas_guides.py -q
```

Expected: guide manager contract tests pass.

- [ ] **Step 8: Commit Task 5**

```bash
git add apps/flatshot-desktop/frontend/app-canvas-guides-controller.js apps/flatshot-desktop/frontend/app-action-dispatcher.js apps/flatshot-desktop/frontend/app-document-events.js apps/flatshot-desktop/frontend/app-render-shell-gallery.js apps/flatshot-desktop/frontend/app-viewer-events.js tests/test_frontend_canvas_guides.py
git commit -m "Add canvas guide manager workflow"
```

---

### Task 6: Viewer Guide Styling

**Files:**
- Modify: `apps/flatshot-desktop/frontend/css/05-viewer/viewer-toolbar.css`
- Modify: `apps/flatshot-desktop/frontend/css/05-viewer/canvas.css`
- Modify: `tests/test_frontend_canvas_guides.py`

- [ ] **Step 1: Write failing CSS ownership tests**

Append this test to `tests/test_frontend_canvas_guides.py`:

```python
def test_canvas_guides_css_lives_in_viewer_modules():
    toolbar_css = (FRONTEND_DIR / "css" / "05-viewer" / "viewer-toolbar.css").read_text(encoding="utf-8")
    canvas_css = (FRONTEND_DIR / "css" / "05-viewer" / "canvas.css").read_text(encoding="utf-8")

    assert ".viewer-guides" in toolbar_css
    assert ".viewer-guides-popover" in toolbar_css
    assert ".guide-overlay" in canvas_css
    assert ".guide-line--x" in canvas_css
    assert ".guide-line--y" in canvas_css
```

- [ ] **Step 2: Run CSS ownership test and verify it fails**

Run:

```bash
pytest tests/test_frontend_canvas_guides.py::test_canvas_guides_css_lives_in_viewer_modules -q
```

Expected: failure because CSS rules are not present.

- [ ] **Step 3: Add toolbar CSS to the existing viewer toolbar module**

Append inside the existing `@layer flatshot` block in `apps/flatshot-desktop/frontend/css/05-viewer/viewer-toolbar.css`:

```css
.viewer-guides {
  position: relative;
}

.viewer-guides > summary {
  display: inline-flex;
  align-items: center;
  min-height: 32px;
  gap: var(--space-2);
  list-style: none;
  cursor: pointer;
}

.viewer-guides > summary::-webkit-details-marker {
  display: none;
}

.viewer-guides.is-disabled > summary {
  opacity: 0.55;
  cursor: default;
}

.viewer-guides-count {
  min-width: 20px;
  padding: 0 var(--space-1);
  border-radius: var(--radius-sm);
  background: var(--surface-muted);
  color: var(--text-secondary);
  font-size: var(--font-size-xs);
  line-height: 20px;
  text-align: center;
}

.viewer-guides-popover {
  position: absolute;
  top: calc(100% + var(--space-2));
  left: 0;
  z-index: 10;
  min-width: 220px;
  padding: var(--space-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  background: var(--surface-panel);
  box-shadow: var(--shadow-md);
}

.viewer-guide-system-option {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-1) 0;
  color: var(--text-primary);
  cursor: pointer;
}

.viewer-guide-system-swatch {
  width: 12px;
  height: 12px;
  border-radius: var(--radius-xs);
  background: var(--guide-system-color);
  border: 1px solid var(--border-subtle);
}
```

- [ ] **Step 4: Add overlay CSS to the canvas module**

Append inside the existing `@layer flatshot` block in `apps/flatshot-desktop/frontend/css/05-viewer/canvas.css`:

```css
.guide-overlay {
  position: absolute;
  z-index: 2;
  pointer-events: none;
  overflow: hidden;
}

.guide-overlay[hidden] {
  display: none;
}

.guide-line {
  position: absolute;
  background: var(--guide-color);
  opacity: var(--guide-opacity);
}

.guide-line--x {
  top: 0;
  bottom: 0;
  left: calc(var(--guide-position) * 100%);
  width: var(--guide-thickness);
  transform: translateX(-50%);
}

.guide-line--y {
  left: 0;
  right: 0;
  top: calc(var(--guide-position) * 100%);
  height: var(--guide-thickness);
  transform: translateY(-50%);
}
```

- [ ] **Step 5: Run CSS checks**

Run:

```bash
pytest tests/test_frontend_canvas_guides.py::test_canvas_guides_css_lives_in_viewer_modules -q
python scripts/audit_css.py --check
pytest tests/test_frontend_css_contract.py -q
```

Expected: all commands pass.

- [ ] **Step 6: Commit Task 6**

```bash
git add apps/flatshot-desktop/frontend/css/05-viewer/viewer-toolbar.css apps/flatshot-desktop/frontend/css/05-viewer/canvas.css tests/test_frontend_canvas_guides.py
git commit -m "Style canvas guide controls and overlay"
```

---

### Task 7: Full Validation And Manual Checks

**Files:**
- No planned source changes unless validation finds a bug.

- [ ] **Step 1: Run frontend-focused tests**

Run:

```bash
pytest tests/test_frontend_canvas_guides.py tests/test_frontend_preview_view.py tests/test_frontend_session_snapshot.py tests/test_frontend_app_cleanup.py tests/test_frontend_css_contract.py -q
```

Expected: all selected tests pass.

- [ ] **Step 2: Run CSS and frontend audits**

Run:

```bash
python scripts/audit_css.py --check
python scripts/audit_frontend.py --check
```

Expected: both audits return exit code `0`.

- [ ] **Step 3: Run the full test suite**

Run:

```bash
pytest
```

Expected: full suite passes. If unrelated pre-existing failures appear, capture the exact failing tests and do not mark this feature complete until the guide-specific tests and affected frontend contracts are green.

- [ ] **Step 4: Launch the app for manual verification**

Run:

```bash
python apps/flatshot-desktop/run_dev.py --open
```

Expected: the launcher prints local frontend and bridge URLs, opens the browser, and keeps running until interrupted.

Manual checks:

- App launches.
- Empty state still shows the folder selection flow.
- Selecting/scanning a folder still works.
- Selecting a thumbnail updates the preview.
- `Fondo` still changes only the viewer background.
- `Guías` appears next to `Fondo` without wrapping awkwardly.
- Turning guides off hides the overlay.
- Activating multiple systems overlays multiple colors.
- Guides remain aligned when switching `Alto`, `Ancho`, zooming, panning, resizing the window, and changing preview mode.
- `Gestionar guías` opens and closes on backdrop, close button, and Escape.
- Creating a custom symmetric pair at `12%` renders lines at `12%` and `88%`.
- Creating a 3-part division renders `33.33%` and `66.67%`.
- Reloading the app preserves guide visibility, active systems, and custom systems.
- Processing/exporting images produces normal output without guide lines.

- [ ] **Step 5: Inspect git status and commit any validation fixes**

Run:

```bash
git status --short
```

Expected: clean tree if no fixes were needed. If fixes were needed, commit them:

```bash
git add <changed-files>
git commit -m "Fix canvas guide validation issues"
```

---

## Self-Review Notes

- Spec coverage: global guides, percentage storage, symmetric pairs, divisions, multiple active systems, immutable defaults, toolbar integration, overlay-only rendering, persistence, malformed-data tolerance, accessibility affordances, and test requirements are covered.
- Non-goals preserved: no export rendering, no source mutation, no Python processing changes, no per-format guide binding, no canvas drag handles, no snapping, no new dependency.
- Key risk called out for implementers: `renderGuideOverlay()` must be called after the preview target exists and after fit dimensions/pan update. Alignment is not complete until manual zoom/fit/pan checks pass.
