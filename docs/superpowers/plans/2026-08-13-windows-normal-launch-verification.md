# Windows Normal Launch Verification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove that the exact downloaded FlatShot release-candidate ZIP starts through the normal Windows desktop path on a fresh runner, then use that gate before merging PR #9 and again on a new candidate built from `main`.

**Architecture:** A PowerShell verifier launches the extracted `FlatShot.exe` with `Start-Process -PassThru`, discovers its listeners and native window through Windows APIs, records WebView2 and screenshot evidence, and cleans up the session. A small Python contract validator consumes the JSON evidence and makes every required condition an explicit failing gate shared by both release workflows.

**Tech Stack:** PowerShell 7, Win32 user32/gdi32 APIs, System.Drawing, Python 3.10+, pytest, GitHub Actions on `windows-latest`.

## Global Constraints

- Run the executable extracted from the downloaded candidate ZIP, never from the checkout.
- Keep `PYTHONHOME`, `PYTHONPATH`, and `VIRTUAL_ENV` unset and reduce `PATH` for the child process.
- Do not add a product-only test flag or change image processing, export behavior, UX, or runtime architecture.
- Require the native EdgeChromium window; browser fallback is evidence but not a passing result.
- Upload the screenshot, JSON result, and runtime log even when verification fails.
- Do not publish or tag `v1.0.1`.

---

### Task 1: Evidence contract

**Files:**
- Create: `scripts/verify_normal_launch_result.py`
- Create: `tests/test_verify_normal_launch_result.py`

**Interfaces:**
- Consumes: JSON emitted by the Windows normal-launch collector.
- Produces: `validate_result(payload: dict[str, object]) -> None` and a CLI returning nonzero when a required gate is missing.

- [ ] Write tests for a complete native result and for each release-blocking observation.
- [ ] Run the focused tests and confirm they fail because the module is absent.
- [ ] Implement the minimal validator and CLI.
- [ ] Run the focused tests and confirm they pass.

### Task 2: Windows normal-launch collector

**Files:**
- Create: `scripts/verify_portable_normal_launch.ps1`

**Interfaces:**
- Consumes: `-PortableRoot`, `-ScreenshotPath`, and `-ResultPath`.
- Produces: a JSON observation containing process, listener, HTTP, window, WebView2, log, screenshot, environment, and cleanup evidence.

- [ ] Launch `FlatShot.exe` normally from the extracted root with a sanitized child environment.
- [ ] Poll the actual process-owned listeners and classify frontend `/` and bridge `/health` by HTTP response.
- [ ] Enumerate visible top-level windows, capture the selected HWND with Win32 APIs, and reject an empty image.
- [ ] Record newly started WebView2 processes and distinguish native EdgeChromium from a logged fallback.
- [ ] Post `WM_CLOSE`, wait, force-kill only as final cleanup, and verify listeners and FlatShot processes disappear.

### Task 3: Workflow gates and artifacts

**Files:**
- Modify: `.github/workflows/release-candidate.yml`
- Modify: `.github/workflows/release.yml`
- Modify: `tests/test_ci_config.py`

**Interfaces:**
- Consumes: exact candidate ZIP already downloaded and extracted by `verify_portable_candidate.py`.
- Produces: mandatory normal-launch job step plus an always-uploaded evidence artifact.

- [ ] Add failing workflow contract tests.
- [ ] Confirm the focused tests fail against the old workflows.
- [ ] Invoke the collector and Python evidence validator in both fresh-runner jobs.
- [ ] Upload screenshot, JSON, and runtime log with `if: always()`.
- [ ] Run focused tests, YAML validation, Ruff, and `git diff --check`.

### Task 4: PR and definitive main candidate

**Files:**
- Modify: PR #9 description only after evidence exists.

**Interfaces:**
- Consumes: GitHub Actions checks and uploaded artifacts.
- Produces: merged PR only if every requested gate passes, followed by a separately built candidate from the merge SHA.

- [ ] Commit and push the focused changes.
- [ ] Wait for CI 3.10-3.13, CodeQL Python/JS, frozen smoke, normal launch, native window, screenshot, relocation, and structural gates.
- [ ] Inspect the JSON result, screenshot, and logs from the PR candidate.
- [ ] Update PR #9, mark ready, and merge using a merge commit only if all gates pass.
- [ ] Wait for the six required checks on the merge SHA.
- [ ] Dispatch Release Candidate from `main`, download its new artifacts, and verify the full evidence again.
- [ ] Audit alerts, tags, and releases without creating `v1.0.1`.
