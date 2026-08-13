# FlatShot Workflow State Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make FlatShot's empty, scanning, and ready-batch states visually coherent and legible at the primary 2048×1152 desktop resolution.

**Architecture:** Keep behavior and markup contracts intact. Refine the state-specific surface ownership in the existing CSS modules, then verify the rendered scenarios through the built-in QA Lab. Tests protect observable layout and contrast contracts before CSS changes.

**Tech Stack:** HTML, layered CSS, vanilla JavaScript, pytest contract tests, Browser plugin QA.

## Global Constraints

- Preserve folder selection, drag-and-drop, manual path entry, keyboard focus, and accessible labels.
- Preserve cancellation behavior and scanning state transitions.
- Preserve image processing, preview pixels, export settings, naming, destination, and output files.
- Add no dependencies and no new product concepts.
- Add no duplicate selectors or `!important` overrides.

---

### Task 1: Neutral empty and scanning workspace

**Files:**
- Modify: `tests/test_frontend_empty_state_view.py`
- Modify: `tests/test_frontend_preview_view.py`
- Modify: `apps/flatshot-desktop/frontend/css/05-viewer/canvas.css`
- Modify: `apps/flatshot-desktop/frontend/css/03-components/empty-states.css`
- Modify: `apps/flatshot-desktop/frontend/css/05-viewer/viewer-states.css`

**Interfaces:**
- Consumes: `.app-shell[data-ui-state]`, `.canvas-area`, `.preview-canvas`, `.initial-onboarding`, `.scanning-state`.
- Produces: a continuous state surface and readable empty/scanning status group without changing DOM behavior.

- [ ] **Step 1: Write failing state-layout tests**

Add contract assertions that empty/scanning states make the canvas and preview canvas inherit the application surface, constrain the onboarding card, and give scanning copy semantic foreground colors.

- [ ] **Step 2: Verify the tests fail for the missing contracts**

Run: `venv\Scripts\python.exe -m pytest -q tests/test_frontend_empty_state_view.py tests/test_frontend_preview_view.py`

- [ ] **Step 3: Implement the minimal state-specific CSS**

Extend the owning selectors so empty/scanning states use one neutral workspace, the onboarding card is compact, and the scanning group has an explicit panel surface and semantic text colors.

- [ ] **Step 4: Verify focused tests and CSS ownership**

Run: `venv\Scripts\python.exe -m pytest -q tests/test_frontend_empty_state_view.py tests/test_frontend_preview_view.py`

Run: `venv\Scripts\python.exe scripts/audit_css.py --check`

### Task 2: Ready-state toolbar and top context rhythm

**Files:**
- Modify: `tests/test_frontend_preview_view.py`
- Modify: `tests/test_frontend_workbench_view.py`
- Modify: `apps/flatshot-desktop/frontend/css/05-viewer/viewer-toolbar.css`
- Modify: `apps/flatshot-desktop/frontend/css/02-layout/topbar.css`

**Interfaces:**
- Consumes: `.preview-toolbar`, `.viewer-options-popover`, `.zoom-controls`, `.viewer-control-group`, `.top-workbench-context`, `.top-context-item`.
- Produces: stable grouping and safe truncation at wide desktop while preserving responsive disclosure.

- [ ] **Step 1: Write failing spacing-contract tests**

Assert that wide toolbar groups use explicit separation and that header context columns have useful minimum widths with bounded values.

- [ ] **Step 2: Verify the tests fail**

Run: `venv\Scripts\python.exe -m pytest -q tests/test_frontend_preview_view.py tests/test_frontend_workbench_view.py`

- [ ] **Step 3: Implement the minimal wide-layout rules**

Use the existing 1600px breakpoint and token spacing. Do not alter compact breakpoint behavior or duplicate selector ownership.

- [ ] **Step 4: Verify focused tests and CSS audit**

Run: `venv\Scripts\python.exe -m pytest -q tests/test_frontend_preview_view.py tests/test_frontend_workbench_view.py`

Run: `venv\Scripts\python.exe scripts/audit_css.py --check`

### Task 3: Rendered QA and completion

**Files:**
- Modify only if a verified functional defect requires it: files owned by Tasks 1–2.

**Interfaces:**
- Consumes: built-in QA Lab scenarios `Sin lote`, `Vista cargando`/scanning, and `Lote listo`.
- Produces: visual and interaction evidence at 2048×1152 plus a clean regression suite.

- [ ] **Step 1: Start the static frontend and open it with the Browser plugin**

Use a free localhost port and the existing `?dev=1` QA route.

- [ ] **Step 2: Inspect all three scenarios in one batched pass**

Check page identity, DOM content, error overlays, console warnings/errors, contrast, clipping, overflow, and the folder/stop/thumbnail interactions.

- [ ] **Step 3: Fix any verified defects in one batch and confirm once**

Repeat the same scenario checks and capture the final 2048×1152 states outside the repository.

- [ ] **Step 4: Run final automated verification**

Run: `venv\Scripts\python.exe scripts/audit_css.py --check`

Run: `venv\Scripts\python.exe -m pytest -q tests/test_frontend_css_contract.py`

Run the Impeccable detector once over changed frontend targets.

Run: `venv\Scripts\python.exe -m pytest -q`

- [ ] **Step 5: Commit the implementation**

Commit only source, tests, and the implementation plan; leave temporary browser evidence outside the repository.
