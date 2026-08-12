# FlatShot workflow-state polish

## Objective

Refine the empty, scanning, and ready-batch states shown in the supplied 2048×1152 captures. Preserve FlatShot's compact production identity and all existing workflow behavior.

## Scope

### Empty state

- Remove the portrait output-canvas silhouette when no folder is selected.
- Use one continuous neutral workspace surface behind the onboarding card.
- Keep the onboarding card compact, centered, and clearly separate from the application chrome.
- Preserve folder selection, drag-and-drop, manual path entry, keyboard focus, and accessible labels.

### Scanning state

- Reuse the same continuous neutral workspace surface as the empty state.
- Present the spinner, `Escaneando carpeta…` label, count, and stop action as one legible status group.
- Ensure text and progress affordances meet the existing dark-theme contrast conventions.
- Preserve cancellation behavior and scanning state transitions.

### Ready-batch state

- Keep the current three-column workstation and portrait output preview.
- Give each viewer-toolbar group stable spacing so `Fondo`, `Guías`, `Imagen`, `Encajar`, and `Zoom` do not visually collide.
- Improve spacing and minimum sizing for the top `Carpeta`, `Preset`, and `Salida` context items while retaining truncation for long values.
- Preserve the current direct wide-screen controls and responsive `Vista` disclosure at smaller widths.

## Implementation boundaries

- Prefer existing semantic tokens and the owning CSS modules.
- Add no dependencies and no new product concepts.
- Do not change image processing, preview pixels, export settings, naming, destination, or output files.
- Do not duplicate selectors or introduce `!important` to override ownership.
- Add or update frontend contract tests before production changes.

## Verification

- Run focused frontend contract tests through a red-green cycle.
- Run `python scripts/audit_css.py --check` and `pytest tests/test_frontend_css_contract.py`.
- Exercise empty, scanning, and ready-batch scenarios in the browser at 2048×1152.
- Confirm no horizontal overflow, clipped content, low-contrast scanning copy, or console errors.
- Run the Impeccable detector once after final UI changes.
- Run the full `pytest` suite.

## Acceptance criteria

1. Empty and scanning states no longer resemble an unused portrait image canvas.
2. Scanning status and progress text remain clearly readable in the active theme.
3. The ready-state viewer toolbar has distinct, stable control groups at 2048×1152.
4. Top context labels and values are visually separated and truncate safely.
5. Existing responsive access, interactions, and exported image behavior remain unchanged.
