# FlatShot Desktop

Active desktop interface for FlatShot. It combines a static HTML/CSS/JS
frontend with a local Python HTTP bridge that calls the existing application
services and image engine.

## Requirements

- Python with the project dependencies installed.
- A local browser.

No Node, Electron, Tauri, Rust, PyQt or qtawesome runtime is required.

## Run

From the repository root:

```bash
python apps/flatshot-desktop/run_dev.py --open
```

This starts:

- bridge: `http://127.0.0.1:8765` when available;
- frontend: `http://127.0.0.1:4173` when available.

If a default port is busy, the runner chooses the next available port and
prints the final frontend URL. When the bridge port changes, the runner passes
that URL to the frontend automatically.

Windows helper:

```bat
apps\flatshot-desktop\run_dev.bat
```

Stop the environment with `Ctrl+C`.

## Portable Run

From the repository root, build or refresh the portable:

```powershell
python scripts\build_portable.py
```

Open:

```text
release\FlatShotPortable\Abrir FlatShot.vbs
```

The portable keeps its settings, logs and render cache in
`release\FlatShotPortable\data`. It opens in a native desktop window through
WebView2/pywebview, with browser fallback only when that native window cannot
start. On launch it auto-syncs backend and frontend code changes from the source
repo recorded in `source_path.txt`. Rebuild it with `python scripts\build_portable.py`
when Python dependencies change.

## Options

```bash
python apps/flatshot-desktop/run_dev.py
python apps/flatshot-desktop/run_dev.py --open
python apps/flatshot-desktop/run_dev.py --bridge-port 8765 --frontend-port 4173
python apps/flatshot-desktop/run_dev.py --no-bridge
```

Explicit `--bridge-port` and `--frontend-port` values are exact. If either is
busy, the runner stops instead of silently choosing another port.

## Manual Run

Bridge only:

```bash
python apps/flatshot-desktop/bridge/run_bridge.py --host 127.0.0.1 --port 8765
```

Frontend only:

```bash
python -m http.server 4173 --bind 127.0.0.1 --directory apps/flatshot-desktop/frontend
```

Open:

```text
http://127.0.0.1:4173
```

If the bridge runs on a non-default port, pass it in the URL:

```text
http://127.0.0.1:4173?bridge=http://127.0.0.1:8766
```

## Normal Workflow

1. Start the app with the bridge enabled.
2. Use `Seleccionar carpeta`, or paste one or more real folder paths separated by `;`.
3. Review the batch list, omitted files and preview.
4. Choose a preset and adjust the visible settings.
5. Open `Salida`, verify format, size, destination and naming.
6. Use `Exportar N`.

The frontend calls:

- `GET /health`;
- `GET /capabilities`;
- `GET /presets`;
- `POST /folders/pick`;
- `POST /folders/scan`;
- `POST /preview/render`;
- `GET /images/thumbnail`;
- `POST /exports/prepare`;
- `POST /exports/run`;
- `GET /exports/jobs/{jobId}`;
- `POST /exports/jobs/{jobId}/pause`;
- `POST /exports/jobs/{jobId}/resume`;
- `POST /exports/jobs/{jobId}/cancel`.

## Development Mock

The normal route uses the local bridge. Visual mock states are only available
with:

```text
http://127.0.0.1:4173?dev=1
```

Open `Debug` and switch mode or scenario there.

## Verification Checklist

For UI/bridge changes, manually check the affected subset:

- app launches;
- empty folder;
- folder with PNG files;
- multi-folder manual path when relevant;
- batch count and omitted-file diagnostics;
- image selection and preview rendering;
- preset selection and main sliders;
- `Salida` validation;
- export progress;
- pause/resume/cancel when affected;
- output destination and filenames;
- structured errors without tracebacks in the UI.

The frontend does not process images. Export, preview and presets remain in
Python services behind the bridge.
