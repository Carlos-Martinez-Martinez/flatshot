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

## Batch 3 implementation

- Scope: Phase 3, export configuration service.
- Added `ExportConfigService` to build `ExportConfig` from stored app settings plus current UI destination overrides.
- Added Qt-free validation for:
  - custom destination without path;
  - non-positive output size;
  - unsupported export format;
  - invalid destination mode;
  - empty subfolder name for subfolder destination;
  - empty naming template.
- Added destination planning for selected folders and enabled output variants, including variant subfolders.
- Adapted `MainWindow._build_export_config_from_settings()` to delegate construction to the service while keeping its public wrapper intact.
- Adapted `_start_export()` to use service validation and destination planning.
- Preserved the existing custom-destination warning text and did not touch workers, preview, presets, settings persistence or `ShadowEngine`.

## Batch 3 validation

- Added `tests/test_export_config_service.py` with coverage for:
  - defaults and format normalization;
  - UI destination overrides;
  - valid subfolder configuration;
  - missing custom destination;
  - invalid dimensions, format, destination and naming template;
  - destination planning for subfolder/custom modes and enabled variants.
- `pytest tests/test_export_config_service.py tests/test_folder_scanner.py tests/test_presenters.py` -> 23 passed.
- `python -m compileall -q src/flatshot/application src/flatshot/ui/main_window.py` -> passed.
- `pytest` -> 133 passed.
- PyQt offscreen smoke:
  - instantiated `MainWindow`;
  - added two temporary folders and verified PNG count;
  - selected a preset;
  - touched an essential slider;
  - selected an image through the grid selection handler;
  - rendered a preview;
  - instantiated `ExportConfigDialog` from the current config;
  - processed one folder to a custom destination;
  - processed two folders through the existing subfolder queue path;
  - verified output files exist and progress/button reset.
- Pause/resume/stop were not exercised because queue controls were not changed in this phase.

## Batch 4 implementation

- Scope: Phase 4, export execution runner.
- Added Qt-free export contracts to `flatshot.application.contracts`:
  - `ExportJobRequest`;
  - `ExportJobResult`.
- Added Qt-free export events in `flatshot.application.events`.
- Added Qt-free cancellation and pause primitives in `flatshot.application.execution_control`.
- Added `ExportRunner` in `flatshot.application.export_runner`.
- Moved the reusable export planning/execution helpers out of `ExportWorker`:
  - naming template formatting;
  - enabled variant filtering;
  - variant output path planning;
  - output path collision validation;
  - stable snapshot copying;
  - single-image processing.
- Adapted `ExportWorker(QThread)` into a PyQt adapter that:
  - builds an `ExportJobRequest`;
  - delegates execution to `ExportRunner`;
  - translates runner events back to the existing Qt signals;
  - keeps the existing public imports used by UI, CLI and tests.
- Preserved the existing cache, naming, output format, destination, process-pool and snapshot behavior.
- Did not touch `ShadowEngine`, presets, preview logic, queue orchestration, settings persistence or image output parameters.

## Batch 4 validation

- Added `tests/test_export_runner.py` with coverage for:
  - `ExportRunner` staying free of PyQt imports;
  - empty folder result;
  - subfolder export;
  - custom destination export;
  - cancellation before rendering;
  - pause token blocking/resume behavior.
- `pytest tests/test_export_runner.py tests/test_export_cache.py tests/test_export_variants.py tests/test_overrides.py -q` -> 16 passed.
- `pytest` -> 139 passed.
- PyQt offscreen smoke:
  - instantiated `MainWindow`;
  - added a temporary folder through `_add_folder_to_list`;
  - verified PNG count and batch summary;
  - selected a preset;
  - adjusted an essential slider;
  - selected an image through the grid handler;
  - rendered a preview;
  - configured subfolder export settings in memory;
  - processed one folder through `ExportWorker`;
  - processed two folders through the existing `QueueWorker`;
  - exercised pause/resume on the active queue worker;
  - exercised stop on a running queue;
  - verified exported files exist and progress/button state resets.
- Smoke used an inline executor to avoid Windows multiprocessing-from-stdin issues while preserving `process_single_image` and the export runner path.
- Observed risk: in offscreen smoke, the visual `export_bar_mode == "paused"` can race with a queued `job_started` signal if pause is toggled immediately as the first job starts. The underlying queue pause flag and resume path worked; this should be revisited when extracting `QueueRunner`.

## Batch 5 implementation

- Scope: Phase 5, queue execution runner.
- Added queue contracts to `flatshot.application.contracts`:
  - `QueueRunRequest`;
  - `QueueRunResult`.
- Added neutral queue events to `flatshot.application.events`:
  - `QueueStartedEvent`;
  - `QueueJobStartedEvent`;
  - `QueueJobProgressEvent`;
  - `QueueJobCompletedEvent`;
  - `QueueFinishedEvent`;
  - `QueuePausedEvent`;
  - `QueueResumedEvent`;
  - `QueueCancelledEvent`.
- Added `QueueRunner` in `flatshot.application.queue_runner`.
- Moved the reusable queue orchestration out of `QueueWorker`:
  - sequential folder processing;
  - per-job PNG counting;
  - `JobItem` status/progress updates;
  - per-job success/error/cancel decisions;
  - queue counters;
  - pause/resume/stop tokens;
  - queue logging hooks.
- Adapted `QueueWorker(QThread)` into a PyQt adapter that:
  - builds `QueueRunRequest`;
  - creates `QueueRunner`;
  - translates queue/export events back to existing Qt signals;
  - preserves public `pause()`, `resume()`, `stop()` and `count_images_in_folder()`;
  - keeps the export runner factory wired through the existing export worker module for current monkeypatch/test compatibility.
- Preserved the existing multi-folder sequence, `JobItem` statuses, progress semantics, log messages and processed-image totals.
- Did not touch `ShadowEngine`, preview rendering, presets, settings persistence, export naming, cache or image output parameters.

## Batch 5 validation

- Added `tests/test_queue_runner.py` with coverage for:
  - `QueueRunner` staying free of PyQt imports;
  - empty queue;
  - one folder;
  - multiple folders in order;
  - empty folder inside a queue;
  - folder with failed image;
  - cancellation before run;
  - pause/resume events.
- `pytest tests/test_queue_runner.py tests/test_export_runner.py tests/test_export_cache.py tests/test_export_variants.py -q` -> 20 passed.
- `pytest` -> 147 passed.
- `python -m compileall -q src/flatshot/application src/flatshot/workers/queue_worker.py` -> passed.
- `git diff --check` -> passed, with only expected line-ending warnings from Git.
- `rg -n "PyQt6|QThread|pyqtSignal" src/flatshot/application/queue_runner.py` -> no matches.
- PyQt offscreen smoke:
  - instantiated `MainWindow`;
  - added a temporary folder through `_add_folder_to_list`;
  - verified PNG count and batch summary;
  - selected a preset;
  - adjusted an essential slider;
  - selected an image through the grid handler;
  - rendered a preview;
  - processed one folder through `ExportWorker`;
  - processed two folders through the new `QueueRunner` via `QueueWorker`;
  - exercised pause/resume on the active queue;
  - exercised stop on a running queue;
  - verified exported files exist and progress/button state resets.
- Smoke used an inline executor to avoid Windows multiprocessing-from-stdin issues while preserving `process_single_image` and the production queue/export runner path.
- Remaining risk: `QueueWorker.current_worker` now references the active `ExportRunner` instead of the old nested `ExportWorker`; no app code depends on `ExportWorker`-specific methods there, but external callers should use `QueueWorker.pause()/resume()/stop()` rather than reaching into that attribute.

## Batch 6 implementation

- Scope: Phase 6, Qt-free preview rendering service.
- Added preview contracts to `flatshot.application.contracts`:
  - `PreviewRequest`;
  - `PreviewResult`;
  - `TilePreviewRequest`;
  - `TilePreviewResult`.
- Added `PreviewService` in `flatshot.application.preview_service`.
- Moved central preview rendering out of `ui.main_window._render_preview_task()`:
  - settings normalization;
  - curve reconstruction;
  - `ShadowEngine._aplicar_efectos_with_diagnostics()` call;
  - RGBA-to-RGB background composition;
  - fallback warning extraction;
  - raw RGB payload generation.
- Moved grid tile preview rendering out of `ui.grid_preview._render_tile_preview()`:
  - image loading;
  - tile render call;
  - original thumbnail payload generation;
  - RGB composition.
- Kept `QRunnable`, `QThreadPool`, `QImage` and `QPixmap` in the PyQt UI layer.
- Preserved preview target sizes, scale factors, `is_preview=True`, local overrides, warning behavior and RGB payload layout.
- Did not touch `ShadowEngine`, export, queue, presets, settings persistence or UI styling.

## Batch 6 validation

- Added `tests/test_preview_service.py` with coverage for:
  - `PreviewService` staying free of Qt imports;
  - central preview RGB payload matching the previous direct `ShadowEngine` path byte-for-byte;
  - rendering from `image_path`;
  - tile preview processed/original payloads.
- `pytest tests/test_preview_service.py tests/test_engine.py tests/test_scaling.py -q` -> 43 passed.
- `python -m compileall -q src/flatshot/application src/flatshot/ui/main_window.py src/flatshot/ui/grid_preview.py` -> passed.
- `pytest` -> 151 passed.
- `rg -n "PyQt6|QImage|QPixmap|QThread|QRunnable" src/flatshot/application/preview_service.py` -> no matches.
- PyQt offscreen smoke:
  - instantiated `MainWindow`;
  - added a temporary folder through `_add_folder_to_list`;
  - verified PNG count and batch summary;
  - waited for grid tile previews to render through `PreviewService`;
  - selected a preset;
  - adjusted an essential slider;
  - selected an image through the grid handler;
  - rendered the central preview through `PreviewService`;
  - processed one folder through `ExportWorker`;
  - processed two folders through `QueueRunner` via `QueueWorker`;
  - exercised pause/resume and stop on the queue;
  - verified exported files exist and progress/button state resets.
- Smoke used an inline executor for export only to avoid Windows multiprocessing-from-stdin issues; preview workers used the normal Qt thread pool.
- Remaining risk: `PreviewService` now imports `PIL.Image` in application contracts through type annotations for in-memory preview requests. This keeps the service Qt-free and matches current domain dependencies, but future web/API work may prefer path/bytes-only requests for cleaner transport boundaries.

## Batch 7 implementation

- Scope: Phase 7 partial, application settings service only.
- Added `SettingsService` in `flatshot.application.settings_service`.
- Added `DEFAULT_APP_SETTINGS` as the Qt-free source of app settings defaults.
- Moved the reusable settings logic out of `MainWindow`:
  - default settings construction;
  - `settings.json` loading;
  - invalid/missing settings fallback;
  - `bg_color` list-to-tuple normalization;
  - legacy missing `shadow_engine` compatibility;
  - raw JSON persistence.
- Adapted `MainWindow._load_app_settings()` to delegate to `SettingsService.load()`.
- Adapted `MainWindow._flush_app_settings()` to delegate to `SettingsService.save()`.
- Kept the existing coalesced save timer in the UI layer.
- Kept config directory selection in the current `ConfigManager` path for now; only file IO and normalization moved.
- Did not change presets, session persistence, settings file format, export, queue, preview rendering or `ShadowEngine`.

## Batch 7 validation

- Added `tests/test_settings_service.py` with coverage for:
  - `SettingsService` staying free of Qt imports;
  - missing settings returning independent defaults;
  - loaded settings normalization;
  - invalid JSON fallback;
  - non-object JSON fallback;
  - saving JSON to nested paths.
- `pytest tests/test_settings_service.py tests/test_config_manager.py tests/test_export_config_service.py -q` -> 20 passed.
- `python -m compileall -q src/flatshot/application src/flatshot/ui/main_window.py` -> passed.
- `pytest` -> 157 passed.
- `rg -n "PyQt6|QStandardPaths|QMessageBox|QWidget|QApplication" src/flatshot/application/settings_service.py` -> no matches.
- PyQt offscreen smoke with a temporary config directory:
  - instantiated `MainWindow` from a temporary `settings.json`;
  - verified loaded `format` and `bg_color` normalization;
  - saved a setting through `_flush_app_settings()` and verified the JSON file;
  - added a folder and verified PNG count;
  - waited for grid previews;
  - selected a preset;
  - adjusted an essential slider;
  - selected an image through the grid handler;
  - rendered central preview;
  - processed one folder;
  - processed two folders through the queue;
  - exercised pause/resume and stop;
  - verified exported files exist and progress/button state resets.
- Remaining risk: Phase 7 is only partially complete. Preset operations still route through `ConfigManager`, which imports Qt for `QStandardPaths`; session state still uses `SessionManager` directly.

## Batch 8 implementation

- Scope: Phase 7 partial, preset service.
- Added `PresetService` in `flatshot.application.preset_service`.
- Moved reusable preset persistence/import/export logic out of `ConfigManager`:
  - legacy `presets.json` load/save;
  - categorized `presets_v2.json` load/save;
  - legacy-to-categorized migration;
  - categorized normalization with explicit `shadow_engine`;
  - default categorized presets;
  - flat preset listing;
  - preserving categories when saving the current flat preset map;
  - import/export bundle parsing and writing;
  - pure create/rename/delete/update operations for flat presets.
- Adapted `ConfigManager` into a compatibility wrapper:
  - it still resolves the current Qt config directory;
  - it delegates preset operations to `PresetService`.
- Adapted `MainWindow` to instantiate `PresetService` with the current config directory and use it for:
  - initial preset loading;
  - saving current preset state;
  - create/rename/delete operations;
  - import/export;
  - opening the preset folder via the cached config directory.
- Preserved `presets.json`, `presets_v2.json`, import/export payload format, legacy migration behavior and UI messages/dialog ownership.
- Did not change settings, session persistence, preview, export, queue, cache or `ShadowEngine`.

## Batch 8 validation

- Added `tests/test_preset_service.py` with coverage for:
  - `PresetService` staying free of Qt imports;
  - default presets using the current default shadow engine;
  - legacy flat preset normalization;
  - legacy-to-categorized migration;
  - saving flat presets while preserving categories;
  - export bundle format;
  - import bundle merge plus legacy file sync;
  - legacy flat import;
  - pure save/create/rename/delete operations and invalid-name cases.
- `pytest tests/test_preset_service.py tests/test_config_manager.py -q` -> 15 passed.
- `python -m compileall -q src/flatshot/application src/flatshot/utils/config.py src/flatshot/ui/main_window.py` -> passed.
- `pytest` -> 167 passed.
- `rg -n "PyQt6|QStandardPaths|QMessageBox|QWidget|QApplication" src/flatshot/application/preset_service.py` -> no matches.
- PyQt offscreen smoke with a temporary config directory:
  - created categorized presets through `PresetService`;
  - instantiated `MainWindow` and verified the preset was loaded;
  - selected and saved the preset through existing UI methods;
  - verified the legacy preset file was updated;
  - added a folder and verified PNG count;
  - waited for grid previews;
  - adjusted an essential slider;
  - selected an image through the grid handler;
  - rendered central preview;
  - processed one folder;
  - processed two folders through the queue;
  - exercised pause/resume and stop;
  - verified exported files exist and progress/button state resets.
- Remaining risk: `ConfigManager` still owns the Qt-specific config directory resolver for compatibility. Session state still uses `SessionManager` directly, so Phase 7 is still partial.

## Batch 9 implementation

- Scope: Phase 7 partial, session service.
- Added `SessionService` in `flatshot.application.session_service`.
- Moved reusable session persistence and payload construction out of UI/utility code:
  - default session file resolution;
  - JSON load/save/clear;
  - invalid or non-object session fallback;
  - session payload shape for geometry, window state, selected folders, active preset, mockup, splitter sizes, export config and shadow settings.
- Adapted `SessionManager` into a compatibility wrapper:
  - it preserves `session_dir`, `session_file`, `save_session()`, `load_session()` and `clear_session()`;
  - it delegates file IO to `SessionService`.
- Adapted `MainWindow.closeEvent()` to build session data through `SessionService.build_session_data()` instead of assembling the dictionary inline.
- Kept session restore logic in `MainWindow` because it still applies Qt geometry, widgets, folders and controls.
- Preserved the existing `session.json` key shape and did not change preview, export, queue, cache, presets, settings format or `ShadowEngine`.

## Batch 9 validation

- Added `tests/test_session_service.py` with coverage for:
  - `SessionService` staying free of Qt imports;
  - default `~/.flatshot/session.json` path construction;
  - save/load roundtrip including Unicode;
  - missing, invalid and non-object JSON fallback;
  - session clear behavior;
  - session payload shape and path conversion;
  - `SessionManager` delegation to `SessionService`.
- `pytest tests/test_session_service.py -q` -> 7 passed.
- `pytest tests/test_session_service.py tests/test_settings_service.py tests/test_preset_service.py tests/test_config_manager.py -q` -> 28 passed.
- `python -m compileall -q src/flatshot/application src/flatshot/utils/session_manager.py src/flatshot/ui/main_window.py` -> passed.
- `pytest` -> 174 passed.
- `rg -n "PyQt6|QStandardPaths|QMessageBox|QWidget|QApplication" src/flatshot/application/session_service.py` -> no matches.
- PyQt offscreen smoke with temporary config and temporary session file:
  - pre-created a session through `SessionService`;
  - instantiated `MainWindow` and verified selected folder and preset restoration;
  - added a second folder and verified PNG count;
  - selected a preset;
  - adjusted an essential slider;
  - selected an image through the grid handler;
  - rendered central preview;
  - validated export configuration;
  - processed one folder;
  - processed two folders through the queue;
  - exercised pause/resume and stop;
  - closed the window and verified saved session keys and export/session values.
- Smoke used a thread-backed executor for export to avoid Windows multiprocessing-from-stdin issues while exercising the production worker/runner path.
- Remaining risk: session restoration still lives in `MainWindow` because it applies Qt-specific state. Existing behavior only restores destination mode/custom path from `export_config`; it does not restore every saved export field. This was observed during smoke and left unchanged to avoid altering behavior in this refactor batch.
