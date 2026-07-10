# FlatShot Release Checklist

Use this checklist before publishing a local build or portable package.

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

- `python scripts/build_portable.py --skip-venv --release` completes without embedding `source_path.txt` or development autosync markers.
- Portable runtime includes frontend, bridge and launcher files.
- If dependencies changed, run the full portable build without `--skip-venv`.
- Launch diagnostics remain available through `Diagnostico FlatShot.bat`.
