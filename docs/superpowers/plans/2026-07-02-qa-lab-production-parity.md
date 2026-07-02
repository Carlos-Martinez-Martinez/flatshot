# QA Lab Production Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Move mock/demo states out of FlatShot's primary workflow into a clearly separated QA Lab while keeping the main app production-like in dev and production.

**Architecture:** The main workflow keeps using `scanBridgeFolder()` and bridge-backed state. QA Lab owns visual scenario controls and may call the existing scenario helpers, but those controls are isolated from primary batch import actions.

**Tech Stack:** Python tests, Node-backed frontend helper tests, HTML/CSS/vanilla JS frontend, local bridge HTTP API.

---

### Task 1: Red Tests For Production-Like Entry

**Files:**
- Modify: `tests/test_frontend_empty_state_view.py`
- Modify: `tests/test_frontend_scan_state.py`
- Modify: `tests/test_frontend_action_handlers.py`

- [x] Add a test that `emptyStateView.initialStateHtml({ devMode: false })` includes `Ruta manual`, `onboarding-scan-path`, and `data-action="scan-bridge-folder"`.
- [x] Add a test that top/debug markup no longer contains `data-action="load-mock-batch"` in `index.html`.
- [x] Add a test that `loadBatch()` only delegates to `scanBridgeFolder()` and does not create mock state.
- [x] Run the focused tests and verify they fail before editing production files.

### Task 2: Implement Production-Like Main Flow

**Files:**
- Modify: `apps/flatshot-desktop/frontend/empty-state-view.js`
- Modify: `apps/flatshot-desktop/frontend/index.html`
- Modify: `apps/flatshot-desktop/frontend/app-batch-workflow.js`
- Modify: `apps/flatshot-desktop/frontend/app-action-dispatcher.js`

- [x] Show manual path entry in initial state regardless of `devMode`.
- [x] Remove `Lote mock` from primary debug actions.
- [x] Make `loadBatch()` delegate to `scanBridgeFolder()` consistently.
- [x] Keep `loadMockBatch()` only if QA Lab still references it; otherwise remove its dispatcher action.
- [x] Run focused tests and verify green.

### Task 3: QA Lab Isolation

**Files:**
- Modify: `apps/flatshot-desktop/frontend/index.html`
- Modify: `apps/flatshot-desktop/frontend/app.js`
- Modify: `apps/flatshot-desktop/frontend/app-action-dispatcher.js`
- Modify: `apps/flatshot-desktop/frontend/app-document-events.js`
- Modify: `apps/flatshot-desktop/frontend/app-modal-render-controller.js`
- Modify: `apps/flatshot-desktop/frontend/css/03-components/dev-debug.css`
- Modify: `apps/flatshot-desktop/frontend/css/04-batch-gallery/review-devtools.css`
- Test: `tests/test_frontend_qa_lab.py`

- [x] Add `qaLabOpen: false` to UI state.
- [x] Add dev-only `QA Lab` button and modal/panel.
- [x] Move visual scenario controls into the QA Lab surface.
- [x] Add open/close actions and outside-click close behavior.
- [x] Keep labels explicit: `QA Lab`, `Estados visuales`, `Simulado`.
- [x] Run focused tests and CSS audit.

### Task 4: Validation And Packaging

**Files:**
- No production source edits expected unless validation finds a bug.

- [x] Run `python scripts/audit_css.py --check`.
- [x] Run `python -m pytest tests/test_frontend_css_contract.py -q`.
- [x] Run `python -m pytest`.
- [x] Start dev app with bridge on free ports.
- [x] Use a temporary PNG folder and verify `/folders/scan` returns one valid image.
- [x] Open the rendered app and verify no console errors, initial route manual is visible, and QA Lab opens.
- [x] Run `python scripts/build_portable.py --skip-venv`.
- [x] Confirm `git status --short` only shows intended tracked changes.

### Task 5: Commit And Push

**Files:**
- All staged implementation, tests, and docs.

- [x] Run `git diff --check`.
- [x] Commit with message `Separate QA Lab from production flow`.
- [x] Push `main` to origin.
