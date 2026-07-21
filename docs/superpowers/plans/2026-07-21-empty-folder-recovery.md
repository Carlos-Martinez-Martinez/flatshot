# Empty Folder Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Recuperar correctamente el flujo tras escanear una carpeta sin imágenes y mostrar un estado vacío visualmente coherente.

**Architecture:** El controlador del bridge seguirá siendo responsable de encadenar selección y escaneo. El render del visor añadirá una clase de estado serializable al DOM; el módulo CSS propietario del lienzo usará esa clase para neutralizar el fondo de salida, mientras el helper de estado vacío proporciona la acción de recuperación.

**Tech Stack:** JavaScript sin framework, CSS por capas, pytest con comprobaciones Node.js.

## Global Constraints

- No cambiar la apariencia ni el comportamiento de los archivos exportados.
- No mover lógica de negocio a la UI.
- No añadir dependencias.
- Mantener foco visible, nombres accesibles y contraste suficiente.
- Ejecutar `python scripts/audit_css.py --check` y `pytest tests/test_frontend_css_contract.py`.

---

### Task 1: Reescanear tras elegir carpeta

**Files:**
- Modify: `apps/flatshot-desktop/frontend/app-bridge-scan-controller.js`
- Test: `tests/test_frontend_folder_pick_flow.py`

**Interfaces:**
- Consumes: `pickBridgeFolder()`, `scanBridgeFolder()` y el estado `bridgeScanPath`.
- Produces: selección confirmada que persiste la ruta y espera exactamente un escaneo.

- [x] **Step 1: Escribir la prueba fallida**

Cambiar la prueba para sustituir `scanBridgeFolder` después de cargar el controlador y comprobar `scanCalls === 1` tras `await pickBridgeFolder()`.

- [x] **Step 2: Verificar el fallo**

Run: `.\venv\Scripts\python.exe -m pytest tests/test_frontend_folder_pick_flow.py -q`
Expected: FAIL con `0 !== 1`.

- [x] **Step 3: Implementar el encadenado mínimo**

Añadir después de persistir y renderizar la ruta:

```js
await scanBridgeFolder();
```

- [x] **Step 4: Verificar el paso**

Run: `.\venv\Scripts\python.exe -m pytest tests/test_frontend_folder_pick_flow.py -q`
Expected: PASS.

### Task 2: Unificar el estado visual vacío

**Files:**
- Modify: `apps/flatshot-desktop/frontend/app-preview-controller.js`
- Modify: `apps/flatshot-desktop/frontend/css/05-viewer/canvas.css`
- Modify: `apps/flatshot-desktop/frontend/css/05-viewer/viewer-shell.css`
- Modify: `apps/flatshot-desktop/frontend/css/06-inspector-export/inspector-workflow.css`
- Test: `tests/test_frontend_preview_view.py`
- Test: `tests/test_frontend_empty_state_view.py`

**Interfaces:**
- Consumes: `state.batch === "empty"` y `emptyStateViewHelpers.emptyStateHtml(...)`.
- Produces: visor en la primera columna, inspector en la segunda, fondo neutro y acción `pick-bridge-folder` dentro del mensaje.

- [x] **Step 1: Escribir pruebas fallidas de contrato**

Comprobar que el controlador pasa `actionLabel: "Elegir otra carpeta"` y `action: "pick-bridge-folder"`; comprobar que los estados `batch_empty` y `scan_empty` colocan el visor y el inspector en las dos columnas declaradas y neutralizan el fondo del área.

- [x] **Step 2: Verificar los fallos**

Run: `.\venv\Scripts\python.exe -m pytest tests/test_frontend_preview_view.py tests/test_frontend_empty_state_view.py -q`
Expected: FAIL porque no existen la acción ni la clase.

- [x] **Step 3: Implementar presentación mínima**

El controlador debe usar la variante `batch-empty` y proporcionar al helper la acción de recuperación. Los módulos propietarios deben colocar el visor en la columna 1, el inspector en la columna 2, ocultar la barra de herramientas de imagen y usar `var(--color-bg-stage)` como fondo del lienzo.

- [x] **Step 4: Ejecutar validación focalizada y global**

Run: `.\venv\Scripts\python.exe scripts/audit_css.py --check`
Expected: auditoría limpia.

Run: `.\venv\Scripts\python.exe -m pytest tests/test_frontend_css_contract.py tests/test_frontend_folder_pick_flow.py tests/test_frontend_preview_view.py tests/test_frontend_empty_state_view.py -q`
Expected: PASS.

Run: `.\venv\Scripts\python.exe -m pytest -q`
Expected: PASS.
