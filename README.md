# FlatShot

FlatShot is a local desktop tool for batch product-image processing. The active
interface is the modern web/bridge desktop app in `apps/flatshot-desktop`; the
Python package provides the image engine, application services, bridge and CLI.

## Requirements

- Python 3.10 or newer.
- Dependencies: Pillow, numpy and pydantic.
- A local browser for the desktop frontend.

No Node, Tauri, Rust, Electron, PyQt or qtawesome installation is required for
the current local app.

## Install

From the repository root:

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -e .
```

On macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Installer helpers are available in `scripts/install.bat` and
`scripts/install.sh`.

## Run The Desktop App

From the repository root:

```bash
python apps/flatshot-desktop/run_dev.py --open
```

On Windows you can also use:

```bat
scripts\run.bat
```

On macOS/Linux:

```bash
./scripts/run.sh
```

The runner starts:

- frontend: `http://127.0.0.1:4173` when available;
- bridge: `http://127.0.0.1:8765` when available.

If either default port is busy, the runner automatically chooses the next free
port and prints the final URL to open.

## Portable

Build or refresh the Windows portable folder:

```powershell
python scripts\build_portable.py
```

The generated portable lives in:

```text
release\FlatShotPortable
```

Run it with:

```text
release\FlatShotPortable\Abrir FlatShot.vbs
```

The portable starts the bridge and frontend on `127.0.0.1`, choosing the next
free ports if `8765` or `4173` are already busy. It stores portable data under
`release\FlatShotPortable\data`, including settings, logs and render cache.

When the portable remains inside `release\FlatShotPortable`, every launch checks
the source repo in `source_path.txt` and auto-syncs changes from:

- `src\flatshot`
- `apps\flatshot-desktop\frontend`

If `requirements.txt` or `pyproject.toml` changes, run
`python scripts\build_portable.py` again so the portable virtual environment is
updated.

## Development URLs

Typical full run:

```bash
python apps/flatshot-desktop/run_dev.py --open
```

Explicit ports:

```bash
python apps/flatshot-desktop/run_dev.py --bridge-port 8765 --frontend-port 4173
```

Frontend only:

```bash
python apps/flatshot-desktop/run_dev.py --no-bridge
```

Manual bridge run:

```bash
python apps/flatshot-desktop/bridge/run_bridge.py --host 127.0.0.1 --port 8765
```

## CLI

The installed `flatshot` command remains available for automation:

```bash
flatshot list-presets
flatshot process --input RUTA/DE/ENTRADA --preset "Luz cenital" --dry-run
```

Use `flatshot process --help` for all export options.

## Project Structure

```text
apps/flatshot-desktop/
  frontend/          # active desktop UI, static HTML/CSS/JS
  bridge/            # source-checkout bridge launcher
src/flatshot/
  bridge/            # local HTTP bridge
  application/       # reusable workflows and services
  core/              # image/shadow engine, models, scaling, export helpers
  utils/             # shared non-UI utilities
tests/               # core, application, bridge, CLI and architecture tests
docs/                # current architecture and UX documentation
```

The retired Qt desktop surface has been removed. Keep new code out of deleted
compatibility packages such as `flatshot.ui` and `flatshot.workers`.

## Tests

```bash
pytest
```

For UI or bridge workflow changes, also launch the app and manually verify the
affected flow with an empty folder and a folder containing PNG images.

## Output Invariant

Do not change exported image appearance, naming, destination behavior, format,
quality/subsampling, transparency or DPI handling unless the task explicitly
asks for it.
