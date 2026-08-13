# FlatShot Portrait Workstation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the oversized horizontal workbench with a compact three-column workstation optimized for vertical product images.

**Architecture:** Keep the current DOM actions, bridge calls, presenters, and processing state. Reassign the existing gallery, preview, and inspector surfaces through their owning CSS modules; change gallery virtualization back to its vertical axis and remove only duplicated presentation from the primary viewport.

**Tech Stack:** Vanilla HTML, CSS layers, JavaScript controllers, pytest contract tests, CSS audit, Browser/IAB visual QA.

## Global Constraints

- Do not change image-processing or file-output behavior.
- Do not add runtime dependencies.
- Preserve existing element IDs, actions, settings, presets, bridge requests, and processing states.
- At 2048 x 1152, no primary content may be clipped or require page-level scrolling.
- The preview surface must be width-bounded for vertical product imagery.
- The gallery owns vertical scrolling and must show complete thumbnail cards.
- Search, filters, output selection, inspector contexts, and process controls remain accessible through progressive disclosure.
- Run `python scripts/audit_css.py --check` and `pytest tests/test_frontend_css_contract.py` before completion.

---

### Task 1: Protect the portrait workstation geometry

**Files:**
- Modify: `tests/test_frontend_css_contract.py`
- Modify: `apps/flatshot-desktop/frontend/css/02-layout/shell-workspace.css`
- Modify: `apps/flatshot-desktop/frontend/css/05-viewer/viewer-shell.css`
- Modify: `apps/flatshot-desktop/frontend/css/04-batch-gallery/gallery-shell.css`

**Interfaces:**
- Consumes: existing `.workspace`, `.gallery-column`, `.preview-panel`, and `.settings-panel` elements.
- Produces: a three-column desktop grid with a vertical gallery and a bounded central viewer.

- [ ] Add a rendered-style contract for gallery column 1, preview column 2, inspector column 3, and no desktop filmstrip row.
- [ ] Run the focused contract and confirm it fails against the horizontal layout.
- [ ] Change only the owning layout selectors to implement the three-column geometry.
- [ ] Run the focused contract and confirm it passes.

### Task 2: Restore complete vertical gallery cards

**Files:**
- Modify: `tests/test_frontend_gallery.py`
- Modify: `apps/flatshot-desktop/frontend/app-gallery-controller.js`
- Modify: `apps/flatshot-desktop/frontend/css/04-batch-gallery/image-grid.css`
- Modify: `apps/flatshot-desktop/frontend/css/04-batch-gallery/thumbnails.css`

**Interfaces:**
- Consumes: current gallery items and virtual spacer.
- Produces: vertical `scrollTop` virtualization and complete list/thumbnail rows.

- [ ] Add a gallery test that exercises vertical viewport calculations and card rendering contracts.
- [ ] Run it and confirm failure caused by horizontal `scrollLeft` behavior.
- [ ] Restore vertical measurement and scrolling without changing selection or filtering.
- [ ] Size thumbnail rows so image and copy fit without overflow clipping.
- [ ] Run the focused gallery tests.

### Task 3: Distill the visible chrome

**Files:**
- Modify: `tests/test_frontend_topbar.py`
- Modify: `apps/flatshot-desktop/frontend/index.html`
- Modify: `apps/flatshot-desktop/frontend/css/02-layout/topbar.css`
- Modify: `apps/flatshot-desktop/frontend/css/05-viewer/viewer-toolbar.css`
- Modify: `apps/flatshot-desktop/frontend/css/06-inspector-export/inspector-navigation.css`

**Interfaces:**
- Consumes: existing context, toolbar, and inspector actions.
- Produces: one primary process action, compact context, and progressively disclosed secondary controls.

- [ ] Add contract coverage for a single visible primary action and non-repeated operational context.
- [ ] Confirm the contract fails against the current dense chrome.
- [ ] Collapse secondary viewer controls without deleting their actions or accessible names.
- [ ] Reduce inspector and header framing while keeping every context reachable.
- [ ] Run topbar, inspector, and accessibility tests.

### Task 4: Adapt responsive layouts

**Files:**
- Modify: `tests/test_frontend_css_contract.py`
- Modify: `apps/flatshot-desktop/frontend/css/08-states-responsive/responsive.css`

**Interfaces:**
- Consumes: portrait workstation desktop geometry.
- Produces: compact rail at 1120-1599, drawer inspector at 760-1119, and stacked contingency below 760.

- [ ] Add breakpoint contracts that prevent hidden columns from reserving space.
- [ ] Confirm the new contract fails where horizontal assumptions remain.
- [ ] Implement the smallest responsive overrides consistent with desktop ownership.
- [ ] Run CSS contracts and audit.

### Task 5: Rendered verification and closure

**Files:**
- Update: `.impeccable/qa/README.md`
- Create: `.impeccable/qa/flatshot-portrait-workstation-2048x1152.png`

**Interfaces:**
- Consumes: the completed frontend.
- Produces: maximized visual evidence and a clean committed branch.

- [ ] Run focused frontend tests.
- [ ] Run `python scripts/audit_css.py --check`.
- [ ] Run `pytest tests/test_frontend_css_contract.py`.
- [ ] Run full `pytest`.
- [ ] Render the ready state at 2048 x 1152, verify no clipping, and inspect the screenshot with `view_image`.
- [ ] Exercise gallery selection and inspector navigation with no console errors.
- [ ] Run the Impeccable detector once over changed UI targets.
- [ ] Commit the coherent correction on `codex/flatshot-production-workbench`.
