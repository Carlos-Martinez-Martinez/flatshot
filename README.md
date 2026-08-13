# FlatShot

FlatShot is a local-first desktop tool for preparing batches of product images for e-commerce. It scans folders of PNG files, previews configurable product presentation and shadows, and exports production-ready copies without modifying source images.

> Status: `v1.0.0` is the first public release, but its Windows portable ZIP is
> non-relocatable and must not be used. Version `1.0.1` is the corrective
> release candidate; it changes packaging only, not image output.

## Highlights

- Batch folder import with verified PNG scanning.
- Presets, per-image adjustments, previews, and exception review.
- PNG and JPG export profiles with explicit destination and naming controls.
- Pause, resume, stop, progress, and export manifests for long-running jobs.
- A local web frontend and loopback-only Python bridge.
- A portable Windows build plus source-based development on Python 3.10+.
- Source images are never overwritten, moved, or deleted.

## Quick start

Clone the repository, create a virtual environment, and install the runtime and development dependencies:

```bash
python -m venv venv
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.lock -r requirements-dev.txt
python apps/flatshot-desktop/run_dev.py --open
```

macOS or Linux:

```bash
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.lock -r requirements-dev.txt
python apps/flatshot-desktop/run_dev.py --open
```

The bridge and frontend bind to loopback. The development launcher generates a per-run token and passes it to the page in a URL fragment that is removed after startup.

## Production workflow

1. Import a folder containing PNG images.
2. Choose a preset and adjust the look.
3. Review the selected image and batch exceptions.
4. Configure format, naming, and output destination.
5. Process the batch and inspect the export summary.

Local configuration is stored outside the repository:

- Windows: `%LOCALAPPDATA%\FlatShot`
- macOS: `~/Library/Preferences/FlatShot`
- Linux: `$XDG_CONFIG_HOME/flatshot` or `~/.config/flatshot`

## Architecture

```text
Desktop frontend
  -> localhost HTTP bridge
    -> application services and job runners
      -> image-processing core and models
        -> local configuration, cache, and export filesystem
```

Business and image-processing rules stay outside the UI. Long-running scan, preview, and export work is coordinated by application runners rather than the browser event loop. See [Architecture](docs/ARCHITECTURE.md) and [Product](PRODUCT.md).

## Validation

Run the complete local quality suite:

```bash
python scripts/check_all.py
python scripts/benchmark_shadow_v2.py --smoke --runs 1
python scripts/build_portable.py --skip-venv
```

The checks cover pytest, Ruff, the CSS contract audit, a frontend E2E asset smoke test, visual landmark regression checks, and a small render benchmark. For CSS changes, both commands below must stay clean:

```bash
python scripts/audit_css.py --check
python -m pytest tests/test_frontend_css_contract.py
```

The automated visual smoke test validates frontend structure and assets; it is not a substitute for manually reviewing representative product images and exported pixels.

## Portable Windows builds

The development portable keeps a local venv, copied sources, autosync, and live
reload. It belongs only to the machine where it was created and is not a
redistributable artifact:

```powershell
python scripts/build_portable.py --skip-venv
```

The release portable is a PyInstaller one-folder bundle with its own CPython
runtime and dependencies. Build the exact pre-tag candidate with:

```powershell
python scripts/package_release_candidate.py --version 1.0.1
```

This creates `release/FlatShotPortable-v1.0.1.zip` and
`release/SHA256SUMS.txt`. Extract the ZIP to a new path and verify the actual
frozen executable, not a repository Python launcher:

```powershell
python scripts/verify_portable_candidate.py `
  release/FlatShotPortable-v1.0.1.zip `
  release/SHA256SUMS.txt `
  --extract-to "$env:TEMP\FlatShot candidate á"
```

`FlatShot.exe --smoke` starts and checks both loopback servers, then shuts them
down without opening a window or processing images. `Abrir FlatShot.vbs` runs
`FlatShot.exe`; it never invokes `pythonw.exe`. On a fresh Windows runner, both
release workflows also launch the extracted executable without arguments and
require the frontend, bridge health endpoint, visible native EdgeChromium
window, WebView2 process, a window screenshot artifact, and clean shutdown
evidence. GitHub's hosted runner does not expose WebView2's DirectComposition
surface to classic Win32 capture and may expose only the top-level window to UI
Automation. The workflow records that limitation explicitly and relies on the
normal process, HTTP, HWND, WebView2, log, and cleanup gates in that environment.

## Safety and compatibility

- FlatShot creates new output files and refuses collisions; source files are not mutated.
- The bridge binds to `127.0.0.1` and portable/development launchers use a per-run authorization token.
- User-selected and configured paths are validated before filesystem operations.
- Configuration changes must remain backward-compatible and tolerate missing or malformed optional values.
- Output-sensitive changes require focused regression tests and a representative manual export check.

Please report vulnerabilities privately as described in [Security](SECURITY.md).

## Contributing

Read [Contributing](CONTRIBUTING.md), the [Code of Conduct](CODE_OF_CONDUCT.md), and [Governance](GOVERNANCE.md) before opening a pull request. Good first contributions include focused tests, documentation improvements, and small maintainability fixes that preserve output.

Project direction is tracked in the [Roadmap](ROADMAP.md), and notable public changes are recorded in the [Changelog](CHANGELOG.md).

## License

FlatShot is released under the [MIT License](LICENSE). Runtime dependencies remain under their respective licenses; see [Third-party notices](THIRD_PARTY_NOTICES.md).
