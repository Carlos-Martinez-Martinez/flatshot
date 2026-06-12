# AGENTS.md

## Mission

FlatShot is a local desktop tool for batch product-image processing. Preserve the working image pipeline while improving maintainability, UI clarity, and future interface flexibility.

Primary invariant: **do not change exported image appearance or file-output behavior unless explicitly requested.**

---

## Stable project context

- Language: Python 3.10+.
- Current UI: local web/bridge desktop app in `apps/flatshot-desktop`.
- Core dependencies: Pillow, numpy, pydantic.
- Main domains:
  - image/shadow processing;
  - presets and settings;
  - local folder scanning;
  - preview generation;
  - batch export;
  - queue/progress/cancel/pause;
  - desktop UI.

Keep the app usable as a reliable local production tool.

---

## Hard rules

1. Do not touch image-processing output casually.
2. Do not move business logic into UI widgets.
3. Do not block the UI thread with heavy work.
4. Do not delete, move, overwrite, or mutate source images.
5. Do not invent product concepts not present in the current code.
6. Do not add dependencies without a clear reason.
7. Do not make broad rewrites when a small extraction is enough.
8. Do not leave disconnected buttons, dead states, or half-implemented flows.
9. Do not assume Windows-only paths, one monitor size, one DPI scale, or one locale.
10. Do not claim success unless tests or manual checks were run.

---

## Preferred architecture

Keep responsibilities separated:

```text
UI layer
→ application/services layer
→ core processing layer
→ persistence/filesystem
```

### Core layer

Allowed:
- pure processing logic;
- models;
- validation;
- naming/export helpers;
- path-safe utilities;
- reusable algorithms.

Forbidden:
- UI toolkit imports;
- widget references;
- dialogs;
- UI state;
- direct user interaction.

### Services layer

Use for reusable workflows:
- scan folders;
- build batch summaries;
- validate export configuration;
- prepare export jobs;
- generate previews;
- coordinate job status;
- format UI/view data from core state.

Services must not depend on widgets.

### UI layer

Allowed:
- HTML/CSS/JS frontend code;
- bridge request wiring;
- displaying state;
- calling services.

Avoid:
- duplicated business rules;
- direct export logic;
- heavy processing;
- repeated formatting scattered across callbacks.

---

## UI/UX rules

FlatShot should feel compact, professional, and production-oriented.

Primary workflow:

```text
Import batch → choose preset → adjust look → review exceptions → configure export → process
```

Visible UI must support this workflow.

### Show by default

- current preset;
- essential adjustment controls;
- preview/canvas;
- batch grid;
- export readiness;
- primary process action.

### Hide or de-emphasize

- preset administration;
- advanced shadow parameters;
- debug/status details;
- full paths;
- destructive actions;
- rarely used configuration.

Use progressive disclosure: basic first, advanced second.

### Microcopy

Use short labels:

- `Preset`
- `Aspecto`
- `Imagen seleccionada`
- `Lote`
- `Exportación`
- `Destino`
- `Procesar X imágenes`
- `Listo para procesar`
- `No hay PNG válidos`

Avoid vague labels:

- `Editar...`
- `Opciones`
- `Más`
- long explanatory UI text.

Put detail in tooltips, dialogs, or logs.

### Layout stability

- Avoid layout jumps.
- Reserve space for state changes where needed.
- Truncate long paths/names.
- Use tooltips for full paths.
- Do not let a filename, route, or status message resize panels unexpectedly.

### Status

Do not show progress bars as decoration.

Every progress bar needs a short status label:

- `Generando previews 17/23`
- `Procesando 8/23`
- `Preparando exportación`
- `Pausado`
- `Deteniendo...`

### Selection/cursor

- Buttons and operational labels must not be accidentally text-selectable.
- Only selectable text where copying is useful: paths, logs, error details.
- Use pointer cursor only for interactive controls.
- Use text cursor only for editable/selectable text.

### Accessibility

Maintain:
- visible focus;
- logical tab order;
- accessible names for icon-only controls;
- contrast;
- non-color-only status signals;
- tooltips for truncated content.

### CSS architecture guard

When editing `apps/flatshot-desktop/frontend/css/`, do not add a new rule by copying an existing selector block. Search first and extend the owning module.

Required before reporting any CSS/frontend change as complete:

```bash
python scripts/audit_css.py --check
pytest tests/test_frontend_css_contract.py
```

The CSS audit must remain clean:
- zero duplicate selectors in the same cascade context;
- zero duplicate selector groups in the same cascade context, even if selector order differs;
- zero duplicated token declarations outside `css/00-settings/tokens.css`;
- zero legacy shell state classes;
- `css/99-legacy-compat.css` empty.

If the audit fails, fix the cascade ownership instead of weakening the test or adding `!important`.

---

## Processing/output rules

When touching image or export code, verify:

- RGBA/RGB conversion;
- alpha handling;
- transparent background;
- background color;
- output dimensions;
- DPI preservation;
- JPG quality/subsampling;
- PNG behavior;
- naming template;
- suffix;
- output folder;
- custom destination;
- cache validity;
- local per-image overrides;
- cancellation safety.

Never overwrite source images.

When changing export behavior, document whether output files may differ from previous versions.

---

## Workers/background work

Long tasks must run outside the UI thread.

Processing states should be explicit:

```text
idle | ready | preparing | processing | paused | stopping | completed | error
```

Rules:
- progress must reset after completion/cancel/error;
- pause/resume/stop must leave controls consistent;
- cancellation must not corrupt output or source files;
- worker errors must be logged and surfaced briefly;
- UI must not freeze while previews or exports run.

Keep long-running work in application/bridge runners, not in frontend code.

---

## Configuration/persistence

Config changes must be backward-compatible.

When adding/changing settings:
- provide defaults;
- tolerate missing keys;
- tolerate malformed user config;
- migrate safely;
- never discard presets silently;
- avoid user-specific absolute paths in committed code.

Do not commit:
- logs;
- caches;
- local sessions;
- generated exports;
- user config;
- temporary files.

---

## Refactoring rules

Good refactors:
- extract pure helpers;
- extract presenters/view models;
- isolate services from UI;
- remove duplicated formatting;
- split huge UI construction methods by responsibility;
- add tests around extracted logic.

Risky refactors:
- changing processing output while doing UI work;
- changing export runners and UI layout in the same pass;
- replacing the GUI toolkit directly;
- changing config schema without migration;
- adding dependencies for visual polish;
- broad rename-only changes without value.

Prefer small, reviewable commits.

---

## Future-interface rule

Design new non-UI logic so it can be reused by:
- current local web/bridge UI;
- CLI;
- future Electron/Tauri shell;
- automation scripts.

Therefore:
- no UI toolkit imports in core/services;
- no widget objects in service APIs;
- prefer serializable inputs/outputs;
- keep paths explicit;
- keep progress/events adapter-friendly.

---

## Tests and validation

Run:

```bash
pytest
```

If tests cannot run, state why.

For UI/workflow changes, manually check at least the affected subset:

- app launches;
- add folder;
- empty folder;
- folder with PNGs;
- batch count;
- preset selection;
- essential sliders;
- preview update;
- select image from grid;
- local image adjustment if affected;
- export config dialog if affected;
- single-folder export;
- multi-folder export if affected;
- pause/resume/stop if affected;
- progress reset;
- output destination;
- output filenames;
- logs/errors.

For pure logic changes, add or update tests when reasonable.

Best test targets:
- naming template;
- batch summary;
- export config validation;
- folder scanning;
- path formatting;
- state/presenter helpers;
- settings migration.

---

## Dependency policy

Before adding a dependency, justify:

- why stdlib/existing deps are insufficient;
- packaging impact;
- cross-platform impact;
- license/security risk;
- runtime cost.

Do not add dependencies for minor UI convenience.

---

## Security/data safety

FlatShot works with local files.

Do not:
- execute shell commands from untrusted paths;
- expose local files over network APIs by default;
- process recursive trees unless explicitly designed;
- write outside configured destinations;
- trust config blindly.

For any future local API:
- bind to localhost by default;
- validate paths;
- restrict operations to user-selected locations;
- shut down cleanly.

---

## Reporting format

After each task, report:

1. Files changed.
2. Functional changes.
3. What was preserved.
4. Tests run.
5. Manual checks.
6. Known limitations.
7. Whether exported image output changed.

Be precise. Do not overstate verification.

---

## Working method

For every task:

1. Inspect relevant code first.
2. Identify the smallest safe boundary.
3. Make one coherent change.
4. Avoid unrelated edits.
5. Run tests/checks.
6. Summarize exactly.

Final priority: **reliable processing first, maintainable architecture second, modern UI third**.
