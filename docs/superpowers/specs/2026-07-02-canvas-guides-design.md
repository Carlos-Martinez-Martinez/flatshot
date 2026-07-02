# FlatShot Canvas Guides Design

## Goal

Add configurable visual guides to the viewer canvas so product images can be reviewed against consistent layout references while adjusting garment size and position.

Guides are a viewer-only aid. They must never alter source images, generated previews, export settings, output files, processing behavior, naming, destinations, or batch state.

## Current Context

The active viewer lives in `apps/flatshot-desktop/frontend/index.html` with:

- `preview-toolbar` for view controls such as preview mode, background, image navigation, fit mode, and zoom.
- `canvas-area` containing `preview-output-context` and `preview-canvas`.
- viewer pan and zoom state in `app-viewer-state.js`.
- fit layout helpers in `preview-state.js`.
- modular viewer CSS under `apps/flatshot-desktop/frontend/css/05-viewer/`.

The guide feature should follow the existing compact toolbar pattern and must not crowd the viewer header with inline editing controls.

## Product Decisions

- Guides are global app preferences, not properties of an output format.
- Positions are edited as percentages of the output canvas.
- Internally, percentages are stored as normalized values from `0` to `1`.
- Multiple guide systems can be active at the same time.
- Each guide system can have its own name, color, opacity, and line thickness.
- Symmetric guides are the default for edge-based guides.
- Uniform canvas divisions are a first-class creation mode.
- Manual adjustment of division percentages is supported without requiring canvas dragging in the first implementation.
- Direct drag editing on the canvas is deferred.
- Rectangular safe areas are deferred beyond the first implementation.

## UX Model

The viewer toolbar gets a single compact `Guías` control placed near `Fondo`, before image navigation and zoom controls.

The control should expose:

- A visible on/off state for all guides.
- A compact indication of how many guide systems are active.
- A popover with active system checkboxes.
- A `Gestionar guías` action for creating and editing systems.

The guide manager should use task-oriented actions:

- `Añadir par`
- `Dividir lienzo`
- `Añadir centro`
- `Añadir línea libre` as a secondary action

For symmetric pairs, the user enters one percentage from an edge. FlatShot renders the matching opposite guide automatically.

Examples:

- Horizontal pair with `12%` renders lines at `12%` and `88%` on the Y axis.
- Vertical pair with `8%` renders lines at `8%` and `92%` on the X axis.

For canvas divisions, the user chooses:

- Axis: horizontal, vertical, or both.
- Number of parts.
- Mode: equal or custom.

Equal divisions generate positions automatically. A `Convertir en personalizada` action lets the user edit the generated percentages.

## Data Model

The persistent guide preference payload should remain serializable and UI-framework independent.

```js
{
  guidesVisible: true,
  activeGuideSystemIds: ["center-safe"],
  guideSystems: [
    {
      id: "center-safe",
      name: "Centro y márgenes",
      color: "#009988",
      opacity: 0.85,
      thickness: 1,
      rules: [
        { id: "center-x", type: "center", axis: "x" },
        { id: "center-y", type: "center", axis: "y" },
        { id: "vertical-margin", type: "mirror-pair", axis: "x", inset: 0.08 },
        { id: "horizontal-margin", type: "mirror-pair", axis: "y", inset: 0.12 },
        { id: "thirds-x", type: "division", axis: "x", mode: "equal", parts: 3 },
        { id: "custom-y", type: "division", axis: "y", mode: "custom", positions: [0.22, 0.5, 0.78] }
      ]
    }
  ]
}
```

Rules are the source of truth. Rendered guide lines are derived from rules at display time.

Supported first-version rule types:

- `center`: renders one line at `50%`.
- `mirror-pair`: renders two lines from one inset percentage.
- `division` with `mode: "equal"`: renders internal division boundaries.
- `division` with `mode: "custom"`: renders explicitly stored percentage positions.
- `line`: renders one free single guide and supports the secondary `Añadir línea libre` action.

Normalization rules:

- Clamp positions to `0..1`.
- Store percentages as decimals with stable rounding.
- Deduplicate generated positions within a small tolerance.
- Ignore malformed rules without discarding the stored system.
- Preserve custom systems even when one rule is invalid.

## Rendering Architecture

Guides should render as a DOM overlay in the viewer, not as pixels in the preview image.

Recommended structure:

- Add a persistent guide overlay element inside `canvas-area`, as a sibling of `preview-canvas`.
- Keep it `aria-hidden="true"` and `pointer-events: none`.
- Position it over the rendered preview target, not over the full viewport.
- Update overlay layout when preview data, fit mode, zoom, pan, preview mode, selected image, or window size changes.

The overlay should derive its rectangle from the same rendered target used for panning:

- `.preview-image` for real previews.
- `.mock-product` only if mock/no-bridge previews remain relevant.

Guide z-index must keep guides above the image but below higher-priority viewer affordances such as comparison dividers or context labels.

## State And Persistence

Guide settings belong to UI preferences, parallel to existing viewer/background preferences.

They should be loaded with safe defaults and persisted with the rest of the local app UI state. They must not be included in export payloads or processing requests.

Suggested state additions:

```js
state.guidesVisible = true;
state.activeGuideSystemIds = [];
state.guideSystems = [];
```

The bridge UI preference payload should persist guide preferences for parity between dev and portable production runs, but guide data must remain separate from export settings.

## Error Handling

Malformed persisted guide data should not break app startup.

Fallback behavior:

- If `guideSystems` is missing, use default guide systems.
- If active ids reference missing systems, skip those ids.
- If a rule is invalid, skip that rule and keep the rest of the system.
- If all rules in an active system are invalid, show no lines for that system without throwing.

User-facing validation should prevent:

- Empty guide system names.
- Duplicate system ids.
- Division parts below `2`.
- Positions outside `0%..100%`.
- Mirror insets at or beyond `50%`, because they collapse or invert the pair.

## Accessibility

- The toolbar control needs a visible label or accessible name.
- Icon-only affordances need `title` and `aria-label`.
- The popover should close on outside click and Escape.
- Focus should remain visible and return predictably to the toolbar trigger when the popover closes.
- Guide lines are decorative and should not enter the tab order.

## Testing And Validation

Pure logic tests should cover:

- Guide preference normalization.
- Rule-to-line expansion for center, mirror pairs, equal divisions, and custom divisions.
- Malformed persisted data.
- Active system filtering.
- Percentage rounding and duplicate generated positions.

Frontend/manual checks should cover:

- App launches with no guide preferences.
- Toolbar remains compact at desktop and narrow widths.
- Guides show, hide, and persist across reloads.
- Multiple systems can be active at once.
- Guides stay aligned in height fit, width fit, zoom mode, pan, and window resize.
- Guides do not affect preview generation or export output.

Required existing checks for future implementation:

```bash
python scripts/audit_css.py --check
pytest tests/test_frontend_css_contract.py
pytest
```

For the first implementation, add focused tests for the pure guide helpers before wiring the UI.

## Non-Goals

- No export watermarking or guide rendering into output files.
- No source image mutation.
- No per-format guide binding in the first version.
- No canvas drag handles in the first version.
- No snapping or automatic garment alignment in the first version.
- No new dependency for the guide UI.

## Implementation Phases

### Phase 1: Global Guide Core And Overlay

- Add guide model helpers and tests.
- Add default global guide systems.
- Add viewer overlay rendering.
- Add compact toolbar control and popover.
- Persist visibility and active system ids.

### Phase 2: Guide Manager

- Add create, duplicate, rename, delete, and edit flows for custom systems.
- Add task-oriented rule creation for symmetric pairs, centers, and divisions.
- Add percentage inputs for custom division positions.
- Persist custom systems safely.

### Phase 3: Canvas Editing

- Add optional drag editing for line positions.
- Add live percentage readouts.
- Consider snapping and rectangular safe-area tools if the workflow proves useful.

## Default Systems Decision

Default guide systems should ship as immutable system presets. Users can duplicate them to create editable custom systems. This matches the background preset direction and avoids accidental corruption of defaults.
