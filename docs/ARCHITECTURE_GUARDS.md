# Architecture Guards

FlatShot now has one active interface: the local web/bridge desktop app in
`apps/flatshot-desktop`.

## Active Layers

```text
apps/flatshot-desktop/frontend
-> src/flatshot/bridge
-> src/flatshot/application
-> src/flatshot/core
-> persistence/filesystem
```

## Package Boundaries

- `src/flatshot/core/` contains image processing, models, scaling, shadow engines and path-safe export helpers.
- `src/flatshot/application/` contains reusable workflows and services.
- `src/flatshot/bridge/` exposes those services through the local HTTP bridge used by the desktop frontend.
- `apps/flatshot-desktop/frontend/` is the only product UI.
- `src/flatshot/utils/render_cache.py` remains as a shared cache utility for export and pre-render services.
- `scripts/build_portable.py` and `scripts/portable/` build the Windows portable launcher around the same bridge/frontend runtime; they must not become a separate product surface.
- The portable launcher may use `pywebview` to host the frontend in a native window; core, application and bridge layers must stay free of that dependency.
- `release/` is generated output and must stay out of version control.

## Removed Legacy Surface

The previous Qt desktop surface has been retired:

- no `main.py` launcher;
- no `src/flatshot/ui/` package;
- no `src/flatshot/workers/` Qt adapter package;
- no `PyQt6` or `qtawesome` runtime dependency;
- no `ConfigManager`, `LogManager`, `SessionManager` or `HistoryManager` compatibility wrappers.
- no presentation/view-state services from the retired UI in `application/`.

## Invariants

- Do not add UI toolkit imports to `core` or `application`.
- Do not put image/export business logic in the frontend.
- Do not route new code through removed compatibility packages.
- Keep export output behavior stable unless the task explicitly changes it.
- Keep compatibility for existing presets and the `shadow_engine="legacy"` renderer because those affect user data and output parity.
- Keep the frontend -> bridge export JSON aligned with `docs/FRONTEND_BRIDGE_EXPORT_CONTRACT.md`.
- Keep frontend state values aligned with `docs/FRONTEND_STATE_CONTRACT.md`; new states need tests and documentation.
- Keep low-use model decisions aligned with `docs/LOW_USE_MODELS_AUDIT.md`; do not remove legacy-looking models without a compatibility review.
- Keep CSS consolidation aligned with `docs/CSS_CASCADE_INVENTORY.md`; do not remove cascade layers or broad `!important` overrides without visual parity checks.

## Tests

- `tests/test_architecture_boundaries.py` checks that removed legacy packages do not return.
- `tests/test_headless_imports.py` checks core/application/bridge/CLI imports without loading Qt modules.
- Export behavior is covered through `application.export_runner` and bridge tests, not UI adapters.
