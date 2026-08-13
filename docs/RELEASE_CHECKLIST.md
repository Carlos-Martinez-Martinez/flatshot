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
python scripts/build_portable.py --skip-venv --release
python -m build
python scripts/check_release_version.py v1.0.0
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

- `python scripts/build_portable.py --skip-venv --release` completes without
  embedding `source_path.txt`; `.autosync.json` must report release mode with
  `source_root: null` and contain no development checkout path.
- Portable runtime includes frontend, bridge and launcher files.
- If dependencies changed, run the full portable build without `--skip-venv`.
- Launch diagnostics remain available through `Diagnostico FlatShot.bat`.

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
- Download the published artifact, verify its checksum, launch it on Windows,
  and complete one representative export before announcing the release.
