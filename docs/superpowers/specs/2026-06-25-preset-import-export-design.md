# Preset Import And Export Design

## Context

FlatShot already has a Qt-free `PresetService` that can persist categorized presets, keep the legacy flat file in sync, export a portable JSON bundle, and parse portable or legacy preset files. The desktop UI can currently save, save-as-new, delete, and export presets from the preset manager, but import is not exposed and conflict behavior is not user-controlled.

This feature must not change image processing, preview rendering, batch export behavior, naming, output folders, or generated image appearance. It only changes preset persistence workflows and the preset management UI.

## Goals

- Let users export saved image-adjustment presets to a portable JSON file.
- Let users import presets from another FlatShot installation or a compatible legacy flat preset file.
- Avoid interfering with existing presets by default.
- Resolve name conflicts with `Importar como copia` as the recommended action.
- Preserve categories when possible.
- Keep preset import/export rules in application or bridge services, not UI widgets.

## Non-Goals

- No changes to shadow processing defaults or output image rendering.
- No import/export for output profiles, UI preferences, logs, caches, source images, or batch state.
- No broad preset administration redesign.
- No new third-party dependencies.

## Recommended Architecture

Use the existing service boundary:

```text
frontend preset manager
-> bridge endpoints
-> PresetService import/export helpers
-> config files: presets_v2.json and presets.json
```

`PresetService` remains the source of truth for parsing, normalization, category preservation, conflict detection, and final persistence. The bridge exposes small serializable operations for the frontend. The frontend handles file selection/download, displays conflict choices, and refreshes preset state from bridge responses.

## Portable File Format

Keep the current bundle shape:

```json
{
  "flatshot_export": {
    "type": "presets",
    "version": 1,
    "exported_at": "2026-06-25T00:00:00+00:00",
    "preset_count": 3
  },
  "presets": {
    "categories": {},
    "uncategorized": {}
  }
}
```

Import also accepts legacy flat mappings such as:

```json
{
  "Preset legado": {
    "angle": 180,
    "distance": 25
  }
}
```

Missing shadow engine values are normalized with the existing compatibility behavior.

## Conflict Policy

When imported preset names collide with existing preset names:

- Default action: `copy`.
- UI label: `Importar como copia`.
- Copy naming is deterministic:
  - `Luz cenital` -> `Luz cenital copia`
  - if taken, `Luz cenital copia 2`
  - then `Luz cenital copia 3`, and so on.
- Secondary action: `overwrite`.
- Cancel leaves existing presets unchanged.

When there are no conflicts, import proceeds without prompting.

The service should report import results using serializable counts and names:

- imported count;
- copied count;
- overwritten count;
- conflict names;
- final preset list via the existing list-presets shape.

## Bridge Contract

Add bridge operations that keep filesystem decisions local and explicit:

- `POST /presets/import/preview`
  - Input: parsed JSON object from the selected file.
  - Output: validity, preset count, conflicts, and recommended strategy.
  - Does not write config.
- `POST /presets/import`
  - Input: parsed JSON object plus `strategy: "copy" | "overwrite"`.
  - Output: existing `/presets` payload plus `ok`, `imported`, `copied`, `overwritten`, `conflicts`.
  - Writes both categorized and legacy preset files through `PresetService`.
- `GET /presets/export`
  - Returns the official bundle from `PresetService`.
  - The frontend uses this payload for browser download, keeping export shape owned by the service layer.

The import endpoints should reject non-object JSON, non-preset exports, malformed categories, or invalid settings with `InvalidRequestError` and short user-facing messages.

## UI Flow

The preset manager keeps import/export as secondary controls under `Gestionar ajustes`.

Suggested actions:

- `Exportar`
- `Importar`

Import flow:

1. User clicks `Importar`.
2. Browser file picker accepts `.json`.
3. Frontend parses JSON locally.
4. Frontend calls `/presets/import/preview`.
5. If invalid, show a compact status message and keep current presets.
6. If no conflicts, call `/presets/import` with `strategy: "copy"` directly.
7. If conflicts exist, show a confirmation with:
   - primary: `Importar como copia`;
   - secondary: `Sobrescribir existentes`;
   - cancel.
8. Refresh preset list from the bridge response.
9. Keep the active preset unchanged if it still exists.
10. Show status text such as `Importados 5 ajustes · 2 como copia`.

The UI should not expose full local paths unless needed for an error detail. File input controls should not resize layout.

## Error Handling

- Invalid JSON: `Archivo JSON no válido`.
- Valid JSON but not a preset bundle or legacy preset map: `Archivo de ajustes no compatible`.
- Import write failure: `No se pudieron importar los ajustes`.
- Cancelled file picker: no state change and no error.

All failures leave existing presets untouched.

## Tests

Application/service tests:

- preview import detects conflicts without writing files;
- copy strategy renames conflicting presets deterministically;
- overwrite strategy replaces conflicting presets;
- import preserves existing non-conflicting presets;
- legacy flat import still normalizes missing `shadow_engine`;
- invalid payloads raise or return a clean bridge error.

Bridge tests:

- `/presets/import/preview` returns conflicts and counts;
- `/presets/import` returns refreshed presets and result counts;
- existing `/presets/save` and `/presets/delete` behavior remains unchanged.

Frontend tests:

- settings view renders import/export controls;
- conflict summary labels prefer `Importar como copia`;
- app action wiring parses selected file, previews conflicts, and sends selected strategy.

Required checks for frontend/CSS changes:

```bash
python scripts/audit_css.py --check
pytest tests/test_frontend_css_contract.py
```

General checks:

```bash
pytest tests/test_preset_service.py tests/test_bridge_service.py tests/test_bridge_http_server.py tests/test_frontend_settings_view.py
pytest
```

## Manual Checks

- App launches.
- Preset manager opens.
- Export downloads a `.json` bundle.
- Import valid bundle with no conflicts.
- Import valid bundle with conflicts and choose `Importar como copia`.
- Import valid bundle with conflicts and choose overwrite.
- Import invalid JSON.
- Import legacy flat preset file.
- Existing active preset remains selected when possible.
- Preview and batch export still use the selected preset normally.

## Output Impact

Exported image appearance and file-output behavior must remain unchanged. Imported presets can produce different image output only when a user explicitly selects one of those imported presets for preview or processing.
