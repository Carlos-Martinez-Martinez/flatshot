# FlatShot release checklist

Use this checklist before creating a release tag. Pushing a matching `vX.Y.Z`
tag publishes artifacts, so do not create or push the tag until every required
gate and manual check is signed off.

## Required Gates

Run from the repository root:

```bash
python -m pytest
python -m ruff check .
python scripts/audit_css.py --check
python scripts/e2e_smoke.py
python scripts/visual_regression_smoke.py
python scripts/benchmark_shadow_v2.py --smoke --runs 1
python scripts/package_release_candidate.py --version 1.0.1
python scripts/verify_portable_candidate.py release/FlatShotPortable-v1.0.1.zip release/SHA256SUMS.txt --extract-to "C:\Temp\FlatShot candidate á"
python -m build
python scripts/check_release_version.py v1.0.1
```

## Manual Workflow Checks

- App launches with the bridge enabled.
- Empty folder reports `No hay PNG validos`.
- Folder with PNG files shows the correct batch count.
- Preset selection and essential sliders update preview state.
- Export readiness explains blocking issues before processing.
- Single-folder export writes to the configured destination.
- Pause, resume and stop leave controls consistent when export flow changed.
- Errors are brief in the UI and detailed enough in logs.

## Data Safety

- Source images are never overwritten or moved.
- Custom output paths cannot escape the selected destination.
- Export manifests are written only under the configured app data location.
- Bridge write endpoints require the local bridge token.

## Image Output

Record this explicitly in the release notes:

```text
Exported image output changed: yes/no
```

If the answer is `yes`, include the reason, affected formats and the visual
or golden comparison that approved the change.

## Portable

- The candidate ZIP contains `FlatShot.exe`, `_internal`, frontend, bridge,
  launchers, notices, and writable `data`, but no venv, `pyvenv.cfg`, source
  pointer, development flag, repository path, or CI-builder path.
- Verify the SHA-256 checksum before extraction.
- Extract to a different path containing spaces and non-ASCII characters.
- Clear `PYTHONHOME`, `PYTHONPATH`, and `VIRTUAL_ENV`, reduce `PATH` to Windows
  system directories, and require `FlatShot.exe --smoke` to return zero.
- On a fresh runner, launch the extracted `FlatShot.exe` without arguments and
  require a live process, frontend and bridge HTTP 200 responses, a visible
  FlatShot window with a nonzero handle, native EdgeChromium/WebView2, a
  screenshot artifact, no new startup errors, and clean process/listener
  cleanup. The hosted runner cannot expose WebView2's DirectComposition surface
  through classic Win32 capture, so the PNG may have a white client area. Record
  that limitation explicitly and require UI Automation to expose the real
  `FlatShot Desktop - Web content` control alongside the documented
  process/HTTP/HWND/WebView2/log gate. Browser fallback is diagnostic evidence,
  not a passing release gate.
- Launch diagnostics remain available through `Diagnostico FlatShot.bat` and
  `data\logs\runtime.log`.
- Download and manually check the Release Candidate workflow artifact before
  creating the tag. Do not tag if its fresh-runner verification is not green.

## Tag and GitHub release

- Update `CHANGELOG.md` with the release date and move relevant entries from
  `Unreleased`.
- Confirm the version in `pyproject.toml` and `src/flatshot/__init__.py`.
- Run `python scripts/check_release_version.py vX.Y.Z` with the intended tag.
- Merge the reviewed release pull request into `main`.
- Create the tag from the exact reviewed `main` commit only after approval.
- Confirm the GitHub `release` environment and release-tag protections are active.
- The workflow independently verifies that the tagged commit is reachable from
  `origin/main`; do not bypass this provenance gate.
- Let `.github/workflows/release.yml` build and publish the portable ZIP,
  Python distributions, and SHA-256 checksum.
- Confirm `publish` depends on fresh-runner `portable-verification`.
- Download the published artifact, verify its checksum, launch it on Windows,
  and complete one representative export before announcing the release.
