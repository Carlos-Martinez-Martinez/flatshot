# FlatShot Portrait Viewer Clarity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminar el espacio interno improductivo del visor vertical, aclarar el contexto superior, exponer las herramientas de vista en escritorio y hacer seguro y comprensible el cierre de Salidas.

**Architecture:** Mantener la separación actual entre helpers puros, controladores DOM y CSS modular. La política de cierre se expresa como estado explícito y acciones existentes; la proporción del visor se publica como una variable CSS desde datos de preview; el layout redistribuye el ancho sobrante hacia la galería sin tocar el pipeline.

**Tech Stack:** JavaScript clásico y CommonJS para helpers probables, HTML, CSS por capas, pytest con ejecución de Node para contratos frontend.

## Global Constraints

- No modificar el motor de imagen, el contenido exportado, naming, destinos ni archivos fuente.
- No añadir dependencias.
- Mantener `css/99-legacy-compat.css` vacío y no duplicar selectores ni tokens.
- Validar a 2048×1152 maximizado y 1280×720.
- Ejecutar `python scripts/audit_css.py --check`, `pytest tests/test_frontend_css_contract.py` y `pytest` antes del cierre.

---

### Task 1: Cierre seguro y coherente de Salidas

**Files:**
- Modify: `apps/flatshot-desktop/frontend/app-state.js`
- Modify: `apps/flatshot-desktop/frontend/app-modal-controller.js`
- Modify: `apps/flatshot-desktop/frontend/app-action-dispatcher.js`
- Modify: `apps/flatshot-desktop/frontend/app-output-profile-modal-renderer.js`
- Modify: `apps/flatshot-desktop/frontend/index.html`
- Modify: `apps/flatshot-desktop/frontend/css/07-modals/app-settings.css`
- Test: `tests/test_frontend_output_profile_actions.py`
- Test: `tests/test_frontend_output_profile_view.py`

**Interfaces:**
- Consumes: `outputProfileHasUnsavedChanges(): boolean`, `cancelOutputProfileDraft(): void`, `render(): void`.
- Produces: `state.outputProfileCloseConfirmOpen: boolean`, `keepEditingOutputProfile(): void`, `discardOutputProfileAndClose(): void`.

- [ ] **Step 1: Write failing close-policy tests**

Add behavioral Node tests that open a clean draft and a dirty draft, invoke `closeAppSettings()`, and assert respectively that the modal closes or `outputProfileCloseConfirmOpen` becomes `true`. Add dispatcher assertions for `keep-editing-output-profile` and `discard-output-profile-and-close`.

- [ ] **Step 2: Run tests and verify the intended failures**

Run: `python -m pytest tests/test_frontend_output_profile_actions.py tests/test_frontend_output_profile_view.py -q`

Expected: failures because the close-confirmation state and actions do not exist.

- [ ] **Step 3: Implement one close path**

Implement the controller contract:

```js
function closeAppSettings() {
  if (state.appSettingsOpen && outputProfileHasUnsavedChanges()) {
    state.outputProfileCloseConfirmOpen = true;
    render();
    return;
  }
  closeAppSettingsImmediately();
}

function keepEditingOutputProfile() {
  state.outputProfileCloseConfirmOpen = false;
  render();
}

function discardOutputProfileAndClose() {
  state.outputProfileCloseConfirmOpen = false;
  cancelOutputProfileDraft();
}
```

Render an inline confirmation in the existing footer with `Seguir editando` and `Descartar y cerrar`. Ensure open, save, reset, cancel and successful close reset the flag.

- [ ] **Step 4: Verify Task 1**

Run: `python -m pytest tests/test_frontend_output_profile_actions.py tests/test_frontend_output_profile_view.py tests/test_frontend_hardening_ui.py -q`

Expected: all selected tests pass.

- [ ] **Step 5: Commit Task 1**

```bash
git add apps/flatshot-desktop/frontend tests/test_frontend_output_profile_actions.py tests/test_frontend_output_profile_view.py
git commit -m "fix: make output settings safely closable"
```

### Task 2: Contexto superior legible

**Files:**
- Modify: `apps/flatshot-desktop/frontend/css/02-layout/topbar.css`
- Modify: `apps/flatshot-desktop/frontend/css/08-states-responsive/responsive.css`
- Test: `tests/test_frontend_topbar.py`

**Interfaces:**
- Consumes: el HTML ya generado con `.top-context-item__label`, `.top-active-preset__label` y sus valores.
- Produces: etiquetas visibles en escritorio y ocultación responsive solo donde el ancho lo exige.

- [ ] **Step 1: Write a failing visibility contract**

Add a test that extracts the owning desktop rules and requires visible labels for `Carpeta`, `Preset` and `Salida`, while the compact breakpoint may hide the labels.

- [ ] **Step 2: Run the new contract and verify it fails**

Run: `python -m pytest tests/test_frontend_topbar.py -q`

Expected: failure because the common label rule currently contains `display: none`.

- [ ] **Step 3: Make labels visible without enlarging the shell unpredictably**

Use the existing two-line grid, remove desktop `display: none`, and restore compact one-line values only inside the narrow breakpoint. Preserve ellipsis and full-value titles.

- [ ] **Step 4: Verify and commit Task 2**

Run: `python -m pytest tests/test_frontend_topbar.py tests/test_frontend_workbench_view.py -q`

```bash
git add apps/flatshot-desktop/frontend/css/02-layout/topbar.css apps/flatshot-desktop/frontend/css/08-states-responsive/responsive.css tests/test_frontend_topbar.py
git commit -m "fix: label the active work context"
```

### Task 3: Geometría real del puesto vertical

**Files:**
- Modify: `apps/flatshot-desktop/frontend/preview-state.js`
- Modify: `apps/flatshot-desktop/frontend/app-preview-controller.js`
- Modify: `apps/flatshot-desktop/frontend/css/02-layout/shell-workspace.css`
- Modify: `apps/flatshot-desktop/frontend/css/04-batch-gallery/image-grid.css`
- Modify: `apps/flatshot-desktop/frontend/css/05-viewer/canvas.css`
- Modify: `apps/flatshot-desktop/frontend/css/08-states-responsive/responsive.css`
- Test: `tests/test_frontend_preview_state.py`
- Test: `tests/test_frontend_preview_view.py`
- Test: `tests/test_frontend_css_contract.py`

**Interfaces:**
- Produces: `previewStateHelpers.previewAspectRatio(preview, fallback): number` limitado a proporciones válidas y `--preview-aspect-ratio` en `#preview-canvas`.
- Consumes: `state.previewData.width`, `state.previewData.height` y dimensiones de la imagen seleccionada cuando estén disponibles.

- [ ] **Step 1: Write failing ratio and geometry tests**

Test literal results `1800/2400 = 0.75`, malformed dimensions returning `0.75`, CSS using `--preview-aspect-ratio`, a bounded central column and a gallery column that absorbs remaining desktop width.

- [ ] **Step 2: Verify the tests fail for missing ratio behavior**

Run: `python -m pytest tests/test_frontend_preview_state.py tests/test_frontend_preview_view.py tests/test_frontend_css_contract.py -q`

- [ ] **Step 3: Implement ratio-driven canvas and width redistribution**

Add the pure helper:

```js
function previewAspectRatio(preview = {}, fallback = 0.75) {
  const width = Number(preview.width);
  const height = Number(preview.height);
  const ratio = width > 0 && height > 0 ? width / height : Number(fallback);
  return Number.isFinite(ratio) && ratio > 0 ? Math.min(2, Math.max(0.25, ratio)) : 0.75;
}
```

Publish the value from `renderPreview()`. Size `.preview-canvas` from its available height and ratio, cap the center column for the production monitor, and let the gallery receive the released width with additional thumbnail columns. Preserve current tablet and compact layouts.

- [ ] **Step 4: Verify and commit Task 3**

Run: `python -m pytest tests/test_frontend_preview_state.py tests/test_frontend_preview_view.py tests/test_frontend_css_contract.py tests/test_frontend_gallery.py -q`

```bash
git add apps/flatshot-desktop/frontend tests/test_frontend_preview_state.py tests/test_frontend_preview_view.py tests/test_frontend_css_contract.py tests/test_frontend_gallery.py
git commit -m "fix: size the viewer from the output aspect"
```

### Task 4: Herramientas directas y validación del flujo

**Files:**
- Modify: `apps/flatshot-desktop/frontend/css/05-viewer/viewer-toolbar.css`
- Modify: `apps/flatshot-desktop/frontend/css/08-states-responsive/responsive.css`
- Test: `tests/test_frontend_topbar.py`
- Test: `tests/test_frontend_preview_view.py`
- Update: `.impeccable/qa/README.md`
- Create: `.impeccable/qa/flatshot-viewer-clarity-2048x1152.png`

**Interfaces:**
- Consumes: el único DOM existente bajo `#viewer-options-menu`.
- Produces: popover convertido en grupo inline en escritorio y summary `Vista` restaurado en breakpoints intermedios.

- [ ] **Step 1: Write a failing responsive disclosure test**

Require desktop CSS to hide the `Vista` summary and render `.viewer-options-popover` as an inline static group; require the intermediate breakpoint to restore summary and popover behavior.

- [ ] **Step 2: Run and verify the failure**

Run: `python -m pytest tests/test_frontend_preview_view.py tests/test_frontend_topbar.py -q`

- [ ] **Step 3: Implement the responsive presentation**

Keep one DOM instance and override presentation only:

```css
.viewer-options-menu > summary { display: none; }
.viewer-options-menu > .viewer-options-popover { position: static; display: flex; padding: 0; border: 0; box-shadow: none; }
```

At the intermediate breakpoint, restore the summary button and absolute popover. Do not duplicate IDs or controls.

- [ ] **Step 4: Run mandatory automated verification**

Run:

```bash
python scripts/audit_css.py --check
python -m pytest tests/test_frontend_css_contract.py -q
python -m pytest -q
git diff --check
```

- [ ] **Step 5: Perform bounded visual QA**

At 2048×1152 maximized, verify all gallery cards remain reachable, the output canvas has the real vertical ratio, labels are explicit, Fondo and Guías are direct, and every Salidas close route works. Repeat layout and toolbar checks at 1280×720, capture the primary viewport, inspect console errors, and document that mock QA does not exercise exports.

- [ ] **Step 6: Commit Task 4**

```bash
git add apps/flatshot-desktop/frontend tests .impeccable/qa
git commit -m "fix: expose desktop viewer tools"
```
