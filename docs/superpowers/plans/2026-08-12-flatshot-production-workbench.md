# FlatShot Production Workbench Implementation Plan

> **Goal:** Recompose the existing desktop UI into a compact production workbench while preserving every image-processing and file-output contract.

## Guardrails

- Keep the current bridge, services, processing pipeline, preset schema, and export behavior unchanged.
- Implement view decisions in serializable presenters/controllers, not in processing code.
- Add no runtime dependencies.
- Build every behavior change test-first and keep the CSS ownership audit clean.
- Validate the maximized app at the primary 2048 x 1152 monitor resolution, then at the existing compact breakpoints.

## Task 1: Establish workbench view contracts

**Files:**
- Add `apps/flatshot-desktop/frontend/js/workbench-view.js`
- Modify `apps/flatshot-desktop/frontend/index.html`
- Add `tests/test_workbench_view_contract.py`

Define pure presentation helpers for semantic batch counts, output context, and stable compact labels. Load the presenter before the shell controllers and cover ready, warning, excluded, customized, empty, and processing cases.

## Task 2: Recompose the desktop shell

**Files:**
- Modify `apps/flatshot-desktop/frontend/index.html`
- Modify `apps/flatshot-desktop/frontend/css/02-layout/shell-workspace.css`
- Modify `apps/flatshot-desktop/frontend/css/02-layout/topbar.css`
- Modify `apps/flatshot-desktop/frontend/css/03-preview/*` only where ownership already exists
- Modify `apps/flatshot-desktop/frontend/css/04-batch-gallery/*` only where ownership already exists
- Modify `apps/flatshot-desktop/frontend/css/05-inspector/*` only where ownership already exists
- Add or update frontend contract tests

Replace the permanent left rail with a dominant central preview, a horizontal bottom filmstrip, and a single right contextual inspector. Keep the folder, preset, output, readiness, review, and process contexts visible in the compact header. Preserve all existing element IDs and bridge actions where possible.

## Task 3: Clarify empty, review, and export states

**Files:**
- Modify the existing empty-state, summary, review, and export-confirm presenters/controllers
- Modify their owning CSS modules
- Add or update focused presenter tests

Give the empty state one primary native folder action and a secondary manual-path path. Separate warnings from exclusions in counts and confirmation copy. Keep full paths available through tooltips without allowing them to resize the layout.

## Task 4: Consolidate processing feedback

**Files:**
- Modify `apps/flatshot-desktop/frontend/js/app-topbar-bridge.js`
- Modify `apps/flatshot-desktop/frontend/js/app-footer-status-controller.js`
- Modify `apps/flatshot-desktop/frontend/css/02-layout/footer.css`
- Add or update controller/view tests

Make the bottom process bar the sole owner of progress, filename, pause/resume, and stop while a job is active. Remove duplicate operational feedback from the header and reset the bar after completion, cancellation, or error using the existing state machine.

## Task 5: Responsive and accessibility completion

**Files:**
- Modify existing responsive CSS owners
- Update accessibility/frontend contract tests

Support full workbench layout at 1600 px and above, a narrower inspector at 1120-1599 px, a drawer/stacked inspector at 760-1119 px, and a single-column arrangement below 760 px. Verify focus visibility, accessible names, logical DOM order, truncation tooltips, non-color-only status, and non-selectable operational controls.

## Task 6: Verification and visual QA

Run, in order:

```powershell
python scripts/audit_css.py --check
pytest tests/test_frontend_css_contract.py
pytest
```

Launch the desktop app and manually check the affected workflow: no folder, empty folder, PNG batch, preset, essential controls, preview selection, export configuration, review states, processing controls, reset, destination, and filenames. Capture the maximized 2048 x 1152 interface and representative compact breakpoints. Compare exported-image behavior against the unchanged pipeline boundary and document any untestable manual dependency.
