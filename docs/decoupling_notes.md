# FlatShot decoupling notes

## Baseline

- Branch: `codex/decouple-flatshot-presenters`.
- Initial test run: `pytest` -> 110 passed.
- Scope for this batch: Phase 0 inventory plus Phase 1 presenters/helpers.
- Explicitly out of scope: shadow engine, export runner extraction, queue runner extraction, preview service extraction, API/web/Electron/Tauri work, visual redesign.

## Phase map from the plan

- Phase 0: establish baseline, inventory coupling, keep behavior unchanged.
- Phase 1: extract pure presentation helpers for batch/export/destination/process state.
- Phase 2: move folder scanning out of `MainWindow`.
- Phase 3: move export config building/validation into a service.
- Phase 4: move export execution out of `ExportWorker(QThread)`.
- Phase 5: move queue execution out of `QueueWorker(QThread)`.
- Phase 6: move preview rendering to a Qt-free service.
- Phase 7+: presets/settings/session services, app state, progressive UI adaptation.
- Phase 10 is future-only and should not start before services are stable.

## Audit summary

### `src/flatshot/ui/main_window.py`

- Heavily coupled to PyQt and application orchestration.
- Builds widgets, stores selected folders, counts PNG files, counts local overrides, formats labels, manages export config, starts workers, coordinates preview, stores settings, restores sessions, and shows dialogs.
- Safe first extraction points: label text, process button text, destination summaries, export summaries, basic process readiness, processing status text.
- Leave for later: folder scanning service, export config service, preview service, session service, worker adapters.
- Critical areas not touched in this batch: image rendering, export output planning, cache behavior, preview rendering, queue/export worker internals.

### `src/flatshot/ui/shell.py`

- Contains small UI dataclasses plus Qt frame containers.
- `BatchSummary` is UI-facing state and currently belongs to the PyQt layer.
- Later phase can move neutral state models to `application`, but this batch avoids moving existing UI containers.

### `src/flatshot/ui/widgets.py`

- Contains widget behavior for sliders, collapsible sections, canvas, toolbar, splash and curve graph.
- Canvas mixes presentation, interaction, drag/drop and QPixmap painting.
- Keep in UI for now. Preview rendering service can later reduce the amount of image-specific logic here.

### `src/flatshot/ui/grid_preview.py`

- Mixes folder scanning, tile state, Qt thread pool, PIL rendering, `ShadowEngine`, overrides, and QImage/QPixmap conversion.
- Good future Phase 6 target: `_render_tile_preview` can become part of a pure preview service, while tile widgets keep only Qt painting/interaction.
- Not touched in this batch to avoid changing preview output or responsiveness.

### `src/flatshot/ui/dialogs.py`

- Export config dialog mixes UI controls, naming preview, destination summary text, color formatting and variant editing.
- Some summary formatting can reuse presenters later, but this batch limits changes to `MainWindow` to reduce behavioral risk.
- `apply_naming_template` remains imported from the worker module; that is a future extraction candidate.

### `src/flatshot/ui/styles.py`

- Pure stylesheet constants and scaling helper.
- No functional coupling to extract in this batch.

### `src/flatshot/core/models.py`

- Core Pydantic models are already Qt-free.
- `ExportConfig`, `ExportVariant`, `ShadowSettings`, `CurveData`, `JobItem` should remain stable.
- No changes needed for Phase 1.

### `src/flatshot/workers/export_worker.py`

- Mixes pure export planning/execution with `QThread` and Qt signals.
- Already contains several reusable pure helpers: naming template, variant output path, variant format, collision validation and image processing.
- Phase 4 should split an `ExportRunner` without changing output images, naming, cache keys or quality settings.
- Not touched in this batch.

### `src/flatshot/workers/queue_worker.py`

- `QThread` wrapper also owns queue iteration, pause/resume/stop and worker orchestration.
- Phase 5 should extract a `QueueRunner` and keep this as a Qt adapter.
- Not touched in this batch.

### `src/flatshot/utils/config.py`

- Preset persistence depends on `QStandardPaths`, so it is not currently reusable outside Qt.
- Preset normalization is mostly pure and can be moved behind a `PresetService`/repository later.
- Not touched in this batch.

### `src/flatshot/utils/session_manager.py`

- Qt-free JSON persistence, but path is hardcoded to `~/.flatshot`.
- Future session service can add validation/defaults without tying to widgets.
- Not touched in this batch.

## Decisions in this batch

- Add `flatshot.application.presenters` as a Qt-free module.
- Keep existing `MainWindow` method names as wrappers where possible to reduce diff and preserve behavior.
- Preserve current visible strings even when the plan examples suggest slightly different copy.
- Do not disable processing for missing custom destination in the button state; preserve the existing warning-on-start behavior.

## Batch 1 implementation

- Added pure presentation helpers for:
  - batch summary text;
  - export summary text and tooltip;
  - destination summary and internal batch destination label;
  - process button text;
  - basic destination readiness validation;
  - process button availability;
  - bottom-bar processing status and progress visibility.
- Adapted `MainWindow` to delegate the existing formatting methods to the new helpers.
- Reused `_build_export_config_from_settings()` in `_start_export()` instead of duplicating `ExportConfig` construction.
- Kept folder scanning in `MainWindow` for now, as planned for Phase 2.
- Kept preview, workers, queue and shadow engine unchanged.

## Batch 1 validation

- `pytest tests/test_presenters.py` -> 8 passed.
- `python -m compileall -q src/flatshot/application src/flatshot/ui/main_window.py` -> passed.
- `pytest` -> 118 passed.
- PyQt offscreen smoke:
  - instantiated `MainWindow`;
  - loaded a temporary folder with one PNG and one ignored non-image file;
  - refreshed folder UI;
  - verified `BatchSummary` folder/image counts;
  - verified `Procesar 1 imagen` button text and enabled state.

## Pending manual checks

- Interactive preview behavior was not visually inspected in this batch because preview code was not changed.
- Full interactive single-folder/multi-folder export, pause/resume/stop and grid selection should be checked when touching scanner, preview, export or queue phases.

## Batch 2 implementation

- Scope: Phase 2, folder scanning service.
- Added `flatshot.application.contracts` with Qt-free scan result dataclasses.
- Added `FolderScanner` to count selected source folders, PNG files and local per-image overrides outside `MainWindow`.
- Adapted `MainWindow._update_folder_ui()`, local override refresh and the batch details dialog to consume `FolderScanner` results while keeping UI rendering, grid sync, watcher sync and background pre-render scheduling in the UI layer.
- Kept the existing lower-case `*.png` scan behavior for compatibility.
- Did not touch preview rendering, export execution, queue execution, presets, settings format or `ShadowEngine`.

## Batch 2 validation

- Added `tests/test_folder_scanner.py` with coverage for:
  - empty folder list;
  - missing folder;
  - folder with PNG and non-PNG files;
  - multiple folders;
  - local override detection;
  - path that exists but is not a directory.
- `pytest tests/test_folder_scanner.py tests/test_presenters.py` -> 14 passed.
- `python -m compileall -q src/flatshot/application src/flatshot/ui/main_window.py` -> passed.
- `pytest` -> 124 passed.
- PyQt offscreen smoke:
  - instantiated `MainWindow`;
  - added two temporary folders;
  - verified PNG count and batch summary;
  - selected a preset;
  - touched an essential slider;
  - selected an image through the grid selection handler;
  - rendered a preview;
  - verified export summary;
  - processed one folder to `_SALIDA_PRO`;
  - verified output file exists and progress/button reset.
- PyQt offscreen multi-folder smoke:
  - processed two folders through the existing queue path;
  - verified both output files exist and progress/button reset.
- Pause/resume/stop were not exercised because queue controls were not changed in this phase.
