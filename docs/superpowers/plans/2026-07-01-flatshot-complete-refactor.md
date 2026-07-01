# FlatShot Complete Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the remaining maintenance refactor so FlatShot has no known follow-up cleanup batch for the current architecture.

**Architecture:** Keep `apps/flatshot-desktop/frontend/app.js` as the composition root for app state and workflow decisions. Move reusable/pure behavior and browser wiring into focused helpers, and enforce the boundary with tests so future work does not drift back into a monolith.

**Tech Stack:** Python 3.14, pytest, ruff, vanilla browser JavaScript, Node-based frontend helper tests, PowerShell on Windows.

---

## Ideal State Contract

- `app.js` owns state, workflow orchestration, rendering calls, and domain decisions that genuinely need the live state object.
- Reusable frontend helpers live in separate files loaded before `app.js`, expose browser globals, and are importable from Node tests.
- Browser event/listener wiring lives outside `app.js` in `interaction-bindings.js`; `app.js` calls a single wiring function and passes explicit dependencies.
- Trivial helper passthrough wrappers in `app.js` are eliminated unless they bind several pieces of live state into a clearer domain concept.
- Portable builder and launcher share common sync/manifest modules.
- Export planning uses typed dataclasses instead of anonymous dict task objects.
- Tests enforce the architecture boundary, not only individual behavior.
- Completion requires: full pytest suite, ruff, CSS audit, portable build without venv, diff whitespace check, clean local tree, and `origin/main` matching `HEAD`.

## Phase 1: Frontend Browser Wiring Extraction

**Files:**
- Create: `apps/flatshot-desktop/frontend/interaction-bindings.js`
- Modify: `apps/flatshot-desktop/frontend/index.html`
- Modify: `apps/flatshot-desktop/frontend/mock-data.js`
- Modify: `apps/flatshot-desktop/frontend/app.js`
- Test: `tests/test_frontend_interaction_bindings.py`
- Test: `tests/test_frontend_app_cleanup.py`

- [ ] **Step 1: Write failing tests**

Add tests requiring `interaction-bindings.js` to load before `app.js`, expose `wireFlatShotInteractions`, and ensure `app.js` no longer registers top-level document/window/element listeners directly.

- [ ] **Step 2: Verify red**

Run:

```powershell
python -m pytest tests/test_frontend_interaction_bindings.py tests/test_frontend_app_cleanup.py -q
```

Expected: failure because `interaction-bindings.js` does not exist and listener wiring is still in `app.js`.

- [ ] **Step 3: Implement extraction**

Move browser event registration, lighting-stage wiring, viewer canvas navigation initialization, resize observer setup, and startup session restore into `interaction-bindings.js`. Keep state mutation behavior the same by passing explicit dependencies from `app.js`.

- [ ] **Step 4: Verify green**

Run:

```powershell
python -m pytest tests/test_frontend_interaction_bindings.py tests/test_frontend_app_cleanup.py tests/test_frontend_number_utils.py tests/test_frontend_storage_helpers.py -q
```

Expected: all selected tests pass.

## Phase 2: Remaining Passthrough Wrapper Cleanup

**Files:**
- Modify: `apps/flatshot-desktop/frontend/app.js`
- Test: `tests/test_frontend_app_cleanup.py`

- [ ] **Step 1: Write or extend failing cleanup tests**

Require that `app.js` has no simple helper passthrough wrappers of the form `return *Helpers.*` unless the wrapper binds live app state into a named domain state.

- [ ] **Step 2: Verify red**

Run:

```powershell
python -m pytest tests/test_frontend_app_cleanup.py -q
```

Expected: failure listing remaining pure passthrough wrappers.

- [ ] **Step 3: Replace pure passthrough calls**

Replace direct wrappers such as formatter/preflight/output label passthroughs with direct helper calls where the wrapper does not add app-specific context.

- [ ] **Step 4: Verify green**

Run:

```powershell
python -m pytest tests/test_frontend_app_cleanup.py tests/test_frontend_output_profile_view.py tests/test_frontend_export_payload.py -q
```

Expected: all selected tests pass.

## Phase 3: Final Architecture Audit and Verification

**Files:**
- Modify only if the audit exposes a real gap.

- [ ] **Step 1: Run architecture searches**

Run:

```powershell
rg -n "function readPersistentValue|function writePersistentValue|function clampNumber|task\\[|cached\\[|outputProfileHelpers\\.outputProfileHelpers" apps src scripts tests
rg -n "document\\.addEventListener|window\\.addEventListener|\\$\\([^\\n]+\\)\\.addEventListener" apps/flatshot-desktop/frontend/app.js
```

Expected: no obsolete helper duplication and no top-level browser wiring left in `app.js` except the single call into `interaction-bindings.js`.

- [ ] **Step 2: Run complete verification**

Run:

```powershell
python -m pytest
python -m ruff check .
python scripts\audit_css.py --check
python scripts\build_portable.py --skip-venv
git diff --check
```

Expected: every command exits 0.

- [ ] **Step 3: Commit and push**

Run:

```powershell
git add -A
git commit -m "Finish frontend refactor boundaries"
git push origin main
git status --short --branch
git rev-parse HEAD origin/main
```

Expected: clean tree and identical local/remote commit hashes.

## Self-Review

- Spec coverage: the plan defines a measurable ideal state, handles the remaining `app.js` monolith boundary, keeps backend/portable refactors intact, and requires full verification.
- Placeholder scan: no TODO/TBD placeholders are present.
- Type consistency: new frontend module name is consistently `interaction-bindings.js`; global helper is `FlatShotInteractionBindings`; app-level handle is `interactionBindingHelpers`.
