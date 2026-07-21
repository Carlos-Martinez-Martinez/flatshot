# FlatShot Maintenance Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Finish the maintenance refactor by removing the remaining large app-domain modules, tightening architecture guards, and splitting oversized backend responsibilities without changing image output behavior.

**Architecture:** Keep the zero-build local frontend model, but split orchestration, controllers, and render helpers by domain. Backend splits must preserve public imports and service behavior through compatibility re-exports where useful.

**Tech Stack:** Plain browser JavaScript, Python 3.10+, pytest, Ruff, existing CSS/JS audit style.

---

### Task 1: Frontend Architecture Guard Tests

**Files:**
- Modify: `tests/test_frontend_app_cleanup.py`
- Modify: `tests/test_architecture_boundaries.py`

- [x] **Step 1: Add failing frontend size and global-surface tests**

Add tests requiring `app-render-*.js` and app-domain files to stay below 400 lines, explicit controller script order, and `mock-data.js` to stop owning helper alias globals.

- [x] **Step 2: Add failing backend size boundary tests**

Add tests requiring `src/flatshot/application/export_runner.py` and `src/flatshot/bridge/service.py` to stay below focused-size thresholds after extraction.

- [x] **Step 3: Run focused tests and confirm RED**

Run:

```powershell
python -m pytest tests\test_frontend_app_cleanup.py tests\test_architecture_boundaries.py -q
```

Expected: failures naming oversized JS/Python files and missing controller scripts.

### Task 2: Frontend Controllers and Render Split

**Files:**
- Create: focused `apps/flatshot-desktop/frontend/app-*.js` controller/state modules loaded by `app-loader.js`
- Modify: `apps/flatshot-desktop/frontend/app-render-shell-gallery.js`
- Modify: `apps/flatshot-desktop/frontend/index.html`

- [x] **Step 1: Move shell/topbar/bridge functions**

Move `renderShell`, `renderTop`, `renderDevelopmentStatus`, `renderBridge`, and related status helpers out of `app-render-shell-gallery.js` into focused files.

- [x] **Step 2: Move gallery and thumbnail functions**

Move batch/gallery functions into `app-gallery-controller.js` and thumbnail queue/state functions into `app-thumbnail-controller.js`.

- [x] **Step 3: Move preview/fit/zoom and inspector functions**

Move preview rendering/fit zoom into `app-preview-controller.js` and inspector/review/settings-card functions into focused inspector modules.

- [x] **Step 4: Move export/profile/modal/preset functions**

Move export panel/result helpers into `app-export-view.js`, output profile/background editor functions into focused output/background modules, modal focus and open/close functions into `app-modal-controller.js`, and preset import/export functions into `app-preset-controller.js`.

- [x] **Step 5: Update script order and keep zero-build startup**

Load app-domain scripts through `app-loader.js` in dependency order and leave `app.js`/`app-startup.js` as bootstrap/startup only.

### Task 3: Reduce Frontend Global Alias Fragility

**Files:**
- Create: `apps/flatshot-desktop/frontend/app-globals.js`
- Modify: `apps/flatshot-desktop/frontend/mock-data.js`
- Modify: `apps/flatshot-desktop/frontend/index.html`

- [x] **Step 1: Move helper aliases to a single app global adapter**

Move `storageHelpers`, `numberHelpers`, `bridgeUrlHelpers`, and related `FlatShot*` aliases out of `mock-data.js`.

- [x] **Step 2: Keep mock data as data only**

Leave `mock-data.js` with mock folders, images, presets, labels, constants, and default settings only.

- [x] **Step 3: Verify helper aliases still exist before app startup**

Add `app-globals.js` before `mock-data.js` in `index.html`.

### Task 4: Backend Responsibility Split

**Files:**
- Create: `src/flatshot/application/export_naming.py`
- Create: `src/flatshot/application/export_planning.py`
- Create: `src/flatshot/bridge/preset_endpoints.py`
- Create: `src/flatshot/bridge/preferences.py`
- Create: `src/flatshot/bridge/preview_endpoints.py`
- Modify: `src/flatshot/application/export_runner.py`
- Modify: `src/flatshot/bridge/service.py`
- Modify: affected tests only if imports move.

- [x] **Step 1: Extract naming and output path helpers**

Move `apply_naming_template`, variant output helpers, and collision validation out of `export_runner.py` while re-exporting names for compatibility.

- [x] **Step 2: Extract export plan builders**

Move export plan dataclasses and planning helpers out of `export_runner.py`, leaving `ExportRunner` focused on execution and events.

- [x] **Step 3: Extract bridge preset/preferences/preview operations**

Move method bodies from `FlatShotBridgeService` into free functions that receive the service instance. Keep method names and response payloads unchanged.

### Task 5: Tooling Hardening

**Files:**
- Create: `scripts/audit_frontend.py`
- Modify: `tests/test_frontend_app_cleanup.py`
- Modify: `pyproject.toml`
- Modify: `docs/ARCHITECTURE_GUARDS.md`

- [x] **Step 1: Add frontend audit script**

The script must check frontend script order, app-domain line limits, allowed helper aliases, and browser event wiring ownership.

- [x] **Step 2: Wire audit into tests**

Call the audit script in check mode from `tests/test_frontend_app_cleanup.py`.

- [x] **Step 3: Tighten Ruff incrementally**

Extend Ruff beyond only `E9/F*` with flake8-bugbear (`B`) so correctness checks improve without forcing broad historical style churn.

- [x] **Step 4: Document the final guardrails**

Update architecture docs with final frontend/backend size and ownership rules.

### Task 6: Verification and Completion Audit

**Files:**
- No production changes expected.

- [x] **Step 1: Run JS syntax check**

```powershell
Get-ChildItem apps\flatshot-desktop\frontend -Filter '*.js' | ForEach-Object { node --check $_.FullName }
```

- [x] **Step 2: Run focused frontend/backend tests**

```powershell
python -m pytest tests\test_frontend_app_cleanup.py tests\test_architecture_boundaries.py -q
```

- [x] **Step 3: Run full tests and audits**

```powershell
python -m pytest
python -m ruff check .
python scripts\audit_css.py --check
python scripts\audit_frontend.py --check
python scripts\build_portable.py --skip-venv
```

- [x] **Step 4: Completion audit**

Confirm no remaining file violates the new size/ownership boundaries, exported image behavior tests still pass, and generated portable app builds.
