# FlatShot Reliability and UX Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the approved FlatShot reliability, correctness, persistence, bridge, packaging, accessibility, responsive, and test hardening without changing valid image-processing output.

**Architecture:** Preserve the existing UI → bridge → application → core → filesystem boundaries. Add shared result/commit helpers at the application boundary, enforce validation before job admission, and keep UI changes in existing controllers/renderers. Every behavior change is introduced by a failing regression test and verified at the smallest affected layer before the full suite.

**Tech Stack:** Python 3.10+, Pillow, numpy, pydantic, pytest, Ruff, vanilla HTML/CSS/JS frontend, local HTTP bridge, existing portable build scripts.

## Global Constraints

- Do not change exported image appearance or file-output behavior except to prevent corruption, stale-cache output, or false success reporting.
- Do not mutate or overwrite source images.
- Core and application modules remain free of UI toolkit imports and widget references.
- Long-running work remains outside the UI thread.
- Do not add dependencies for minor UI convenience.
- Preserve Windows compatibility and test platform-aware behavior where applicable.
- CSS edits must pass `python scripts/audit_css.py --check` and `pytest tests/test_frontend_css_contract.py`.
- Every task must add a focused regression test before production code.

---

### Task 1: Make export results truthful and pause-safe

**Files:**
- Modify: `src/flatshot/application/export_runner.py`, `src/flatshot/application/execution_control.py`, `src/flatshot/bridge/export_jobs.py`, `src/flatshot/cli.py`
- Test: `tests/test_export_runner.py`, `tests/test_cli.py`, `tests/test_bridge_service.py`

**Interfaces:**
- `ExportRunner.run()` continues returning `ExportJobResult`.
- `ExportJobResult.success` is derived from `processed == total`, zero errors, no fatal error, and not cancelled.
- `ExecutionControl.wait_if_paused()` blocks until resume or cancellation and returns a boolean cancellation signal.

- [ ] Write a test where executor construction raises and assert `success is False`, `fatal_error` is present, and `processed == 0`.
- [ ] Write a test with pending work and a paused token whose wait expires; assert the runner does not return success until resumed or cancelled.
- [ ] Write a test for a `0/3` bridge result and assert the payload reports `processed=0`, not `3`.
- [ ] Write a CLI test for a collision/failure and assert a non-zero exit code with no success marker.
- [ ] Run the focused tests and observe the failures against the current implementation.
- [ ] Implement the smallest result invariant and condition-based pause changes.
- [ ] Run the focused tests and then `pytest tests/test_export_runner.py tests/test_cli.py tests/test_bridge_service.py`.

### Task 2: Unify atomic commits and harden cache identity

**Files:**
- Modify: `src/flatshot/utils/render_cache.py`, `src/flatshot/application/export_runner.py`, `src/flatshot/application/export_workers.py`
- Test: `tests/test_export_cache.py`, `tests/test_render_cache.py`, add focused cache-integrity tests in those files

**Interfaces:**
- Cache key generation accepts the stable source fingerprint and output metadata.
- Cache-hit output uses the same exclusive commit helper as normal rendering.

- [ ] Add a red test replacing file contents while preserving size and mtime; assert the cache key changes or the old entry is rejected.
- [ ] Add a red test where cache copy writes partially and raises; assert the final destination is absent or unchanged and only the temporary is removed.
- [ ] Add a red test creating a destination after preflight; assert the cache path refuses to overwrite it.
- [ ] Run the focused cache tests and confirm each fails for the current reason.
- [ ] Implement content fingerprinting with compatibility misses for old entries.
- [ ] Extract/reuse one temporary-to-exclusive-commit helper for render and cache paths.
- [ ] Run all cache and export tests and inspect output bytes for existing golden cases.

### Task 3: Coordinate cancellation, admission limits, and shutdown

**Files:**
- Modify: `src/flatshot/application/export_runner.py`, `src/flatshot/bridge/export_endpoints.py`, `src/flatshot/bridge/service.py`, `src/flatshot/bridge/export_jobs.py`, `src/flatshot/application/folder_scan_jobs.py`, `scripts/portable/FlatShot.pyw`
- Test: `tests/test_export_runner.py`, `tests/test_bridge_http_server.py`, `tests/test_folder_scan_jobs.py`, add focused concurrency tests

**Interfaces:**
- Job admission reserves a slot and inserts the job under one lock or semaphore.
- `FlatShotBridgeService.shutdown()` cancels active jobs and joins worker threads within a bounded shutdown interval.

- [ ] Add a barrier-based red test proving two simultaneous export requests cannot exceed `max_concurrent_exports`.
- [ ] Add a red test for active work during cancellation; assert final output accounting and job state agree.
- [ ] Add a red test for scan admission and bounded active scan count.
- [ ] Add a red shutdown test with an active job and assert the worker is joined or reported as still stopping.
- [ ] Run focused concurrency tests and confirm failures.
- [ ] Implement reservation/rollback, explicit in-flight accounting, bounded shutdown, and incremental cancellation checks.
- [ ] Run bridge, runner, folder-scan, and portable launcher tests.

### Task 4: Make persistence migrations and concurrent saves safe

**Files:**
- Modify: `src/flatshot/application/config_paths.py`, `src/flatshot/application/preset_service.py`, `src/flatshot/application/settings_service.py`, `src/flatshot/bridge/service.py`, `src/flatshot/bridge/preset_endpoints.py`
- Test: `tests/test_config_paths.py`, `tests/test_preset_service.py`, `tests/test_settings_service.py`, `tests/test_bridge_service.py`

**Interfaces:**
- Startup migration is idempotent when the destination directory already exists.
- Per-file persistence uses a shared lock and unique temporary file.

- [ ] Add a red bridge-startup migration test with an existing new directory and a legacy preset.
- [ ] Add a red concurrent-save test for two distinct preset names and assert both survive.
- [ ] Add a red settings-save test that uses distinct temporary paths under concurrent writes.
- [ ] Run focused persistence tests and observe expected failures.
- [ ] Implement idempotent migration and shared file-level locking without discarding malformed or unknown keys.
- [ ] Run all configuration, preset, settings, and bridge tests.

### Task 5: Bound export dimensions, workers, and destination preflight

**Files:**
- Modify: `src/flatshot/core/models.py`, `src/flatshot/bridge/payload_helpers.py`, `src/flatshot/application/export_config_service.py`, `src/flatshot/application/export_preflight.py`, `src/flatshot/application/export_runner.py`, `apps/flatshot-desktop/frontend/index.html`, `apps/flatshot-desktop/frontend/output-profiles.js`
- Test: `tests/test_models.py`, `tests/test_export_config_service.py`, `tests/test_bridge_service.py`, `tests/test_frontend_output_profiles.py`, `tests/test_frontend_preflight.py`

**Interfaces:**
- Export configuration rejects dimensions above explicit side and total-pixel limits with a user-safe validation error.
- Worker count is clamped to a CPU-aware hard maximum.
- Preflight checks every destination volume and accounts for variants and conservative pixel-based output size.

- [ ] Add red model/service tests for oversized side and total-pixel requests.
- [ ] Add a red test for worker values above the hard maximum.
- [ ] Add a red preflight test with destination on a separate volume abstraction and multiple variants.
- [ ] Add frontend tests asserting the controls expose the same limits and error copy.
- [ ] Run focused tests and observe failures.
- [ ] Implement shared constants, validation, conservative estimates, and UI `min`/`max`/`step` attributes.
- [ ] Run model, bridge, preflight, and frontend tests.

### Task 6: Make bridge requests idempotent and retry-safe

**Files:**
- Modify: `apps/flatshot-desktop/frontend/bridge-client.js`, `apps/flatshot-desktop/frontend/app-export-controller.js`, `apps/flatshot-desktop/frontend/app-bridge-scan-controller.js`, `src/flatshot/bridge/export_endpoints.py`, `src/flatshot/bridge/service.py`
- Test: `tests/test_frontend_bridge_client.py`, `tests/test_frontend_export_payload.py`, `tests/test_bridge_http_server.py`

**Interfaces:**
- GET/HEAD may retry transient failures; mutating methods default to zero retries unless explicitly idempotent.
- Export creation accepts an idempotency key and returns the existing job for the same key.

- [ ] Add red client tests proving POST is not retried by default and GET still retries transient errors.
- [ ] Add a red HTTP test repeating an export request with the same idempotency key and assert one job.
- [ ] Add a red test for a failed idempotent request that permits a new key to create a new job.
- [ ] Run focused client and bridge tests and observe failures.
- [ ] Implement method-aware retry policy, key propagation, bounded key retention, and sanitized responses.
- [ ] Run all bridge and frontend bridge tests.

### Task 7: Restore local-adjustment cancel semantics and fix responsive/a11y state

**Files:**
- Modify: `apps/flatshot-desktop/frontend/app-local-adjustment-workflow.js`, `apps/flatshot-desktop/frontend/app-preset-controller.js`, `apps/flatshot-desktop/frontend/app-document-events.js`, `apps/flatshot-desktop/frontend/output-profile-view.js`, `apps/flatshot-desktop/frontend/app-output-profile-modal-renderer.js`, `apps/flatshot-desktop/frontend/index.html`, `apps/flatshot-desktop/frontend/css/08-states-responsive/responsive.css`, `apps/flatshot-desktop/frontend/css/06-inspector-export/output-profiles.css`
- Test: `tests/test_frontend_action_handlers.py`, `tests/test_frontend_output_profile_view.py`, `tests/test_frontend_css_contract.py`, add browser assertions through the existing frontend smoke harness

**Interfaces:**
- Opening an image editor creates a draft override snapshot; apply commits, cancel restores.
- Output modal dirty state is computed after form synchronization and its close control is labelled for `Salidas`.

- [ ] Add a red frontend test that changes a local override, cancels, and asserts the previous override remains.
- [ ] Add a red view test preventing stale `Cambios sin guardar` when the footer says saved.
- [ ] Add a red DOM/CSS smoke assertion for the recovery CTA at 480/560 px widths.
- [ ] Run focused frontend tests and confirm failures.
- [ ] Implement draft lifecycle, accessible naming, consistent dirty-state calculation, and a responsive single-column recovery action below the minimum desktop width.
- [ ] Run CSS audit, frontend contract tests, and rendered browser checks.

### Task 8: Seal portable releases and dependency reproducibility

**Files:**
- Modify: `scripts/build_portable.py`, `scripts/portable/FlatShot.pyw`, `scripts/portable/runtime_sync.py`, `.github/workflows/ci.yml`, `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`, `.gitignore`
- Test: `tests/test_build_portable.py`, `tests/test_portable_launcher.py`, `tests/test_portable_runtime_sync.py`, `tests/test_ci_config.py`

**Interfaces:**
- A release build stages only allowlisted runtime files and user-safe defaults.
- Development autosync/live reload requires an explicit development flag.
- Dependencies are reproducibly constrained and CI tests supported Python versions.

- [ ] Add red build tests that fail if release staging includes `data`, source paths, autosync metadata, or absolute checkout paths.
- [ ] Add a red launcher test requiring an explicit dev flag for live reload/autosync.
- [ ] Add a red CI/config test for supported Python matrix and pinned action/dependency policy.
- [ ] Run focused build and CI tests and observe failures.
- [ ] Implement clean staging, allowlist copying, redaction/default config, explicit dev mode, constraints/hashes policy, and matrix coverage.
- [ ] Run portable build smoke and inspect the staged artifact for personal paths.

### Task 9: Add real browser workflow coverage and operational retention

**Files:**
- Modify: `scripts/e2e_smoke.py`, `scripts/visual_regression_smoke.py`, `src/flatshot/bridge/export_job_repository.py`, `src/flatshot/application/export_preflight.py`, `src/flatshot/bridge/service.py`, documentation under `docs/`
- Test: `tests/test_frontend_e2e_smoke.py`, `tests/test_frontend_visual_regression_smoke.py`, `tests/test_bridge_service.py`

**Interfaces:**
- Browser smoke checks real DOM geometry and interaction states at 480, 560, 800, and desktop widths.
- Manifest retention has a bounded policy and redacts or avoids unnecessary absolute paths in user-facing history.

- [ ] Add red geometry checks for the collision recovery controls and keyboard focus/escape behavior.
- [ ] Add a red retention test that keeps the configured number of manifests and removes older entries safely.
- [ ] Add a red preflight test for destination-volume free space.
- [ ] Run focused smoke and repository tests to confirm failures.
- [ ] Implement browser checks, retention, and destination-aware preflight reporting.
- [ ] Run the complete verification stack and manual workflow.

### Final verification and review

- [ ] Run `python scripts/check_all.py` and capture the full result.
- [ ] Run `python scripts/audit_frontend.py --check`.
- [ ] Run `python scripts/benchmark_shadow_v2.py --smoke --runs 1`.
- [ ] Start the local app and manually verify import, empty folder, PNG batch, preset, adjustment apply/cancel, output profiles, collision recovery, export state transitions, and responsive widths.
- [ ] Inspect `git diff --check`, `git status --short --branch`, and output fixtures.
- [ ] Dispatch a whole-branch code review and resolve all critical/important findings before claiming completion.

