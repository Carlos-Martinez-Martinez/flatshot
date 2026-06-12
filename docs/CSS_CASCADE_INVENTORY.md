# Inventario de cascada CSS - FlatShot

Este documento registra la cascada CSS activa tras la consolidacion modular de
junio de 2026. La limpieza no cambia procesamiento, preview/export, naming,
destinos ni escritura de archivos.

## Carga activa

`apps/flatshot-desktop/frontend/index.html` carga las hojas en este orden:

1. `css/00-settings/tokens.css`
2. `css/01-base/base.css`
3. `css/02-layout/shell-workspace.css`
4. `css/02-layout/topbar.css`
5. `css/02-layout/footer.css`
6. `css/03-components/primitives.css`
7. `css/03-components/workflow-panels.css`
8. `css/03-components/review-status-panels.css`
9. `css/03-components/buttons.css`
10. `css/03-components/forms.css`
11. `css/03-components/navigation-controls.css`
12. `css/03-components/status-badges.css`
13. `css/03-components/cards.css`
14. `css/03-components/empty-states.css`
15. `css/03-components/progress-loaders.css`
16. `css/03-components/dev-debug.css`
17. `css/04-batch-gallery/batch-rail.css`
18. `css/04-batch-gallery/source-import.css`
19. `css/04-batch-gallery/batch-summary.css`
20. `css/04-batch-gallery/gallery-shell.css`
21. `css/04-batch-gallery/image-grid.css`
22. `css/04-batch-gallery/thumbnails.css`
23. `css/04-batch-gallery/review-devtools.css`
24. `css/05-viewer/viewer-shell.css`
25. `css/05-viewer/viewer-toolbar.css`
26. `css/05-viewer/canvas.css`
27. `css/05-viewer/viewer-states.css`
28. `css/06-inspector-export/inspector-shell.css`
29. `css/06-inspector-export/inspector-navigation.css`
30. `css/06-inspector-export/inspector-workflow.css`
31. `css/06-inspector-export/inspector-cards.css`
32. `css/06-inspector-export/adjustments-presets.css`
33. `css/06-inspector-export/adjustment-controls.css`
34. `css/06-inspector-export/advanced-local-overrides.css`
35. `css/06-inspector-export/export-panel.css`
36. `css/06-inspector-export/output-profiles.css`
37. `css/06-inspector-export/review-warnings.css`
38. `css/07-modals/app-settings.css`
39. `css/07-modals/batch-detail.css`
40. `css/07-modals/export-confirm.css`
41. `css/08-states-responsive/states.css`
42. `css/08-states-responsive/responsive.css`
43. `css/99-legacy-compat.css`

No hay build step. El orden de enlaces es el contrato de cascada. Todos los
modulos activos, salvo `css/99-legacy-compat.css`, estan envueltos en una
unica capa `@layer flatshot` para dejar un limite explicito de cascada sin
cambiar la prioridad relativa entre modulos.

## Metricas actuales

Medicion ejecutada con:

```powershell
python scripts\audit_css.py --check
```

| Archivo | Lineas | `!important` | `:root` | Tokens |
| --- | ---: | ---: | ---: | ---: |
| `css/00-settings/tokens.css` | 293 | 0 | 7 | 255 |
| `css/01-base/base.css` | 61 | 7 | 0 | 0 |
| `css/02-layout/shell-workspace.css` | 127 | 0 | 0 | 0 |
| `css/02-layout/topbar.css` | 361 | 1 | 0 | 0 |
| `css/02-layout/footer.css` | 87 | 0 | 0 | 0 |
| `css/03-components/primitives.css` | 233 | 0 | 0 | 0 |
| `css/03-components/workflow-panels.css` | 238 | 0 | 0 | 0 |
| `css/03-components/review-status-panels.css` | 162 | 0 | 0 | 0 |
| `css/03-components/buttons.css` | 118 | 0 | 0 | 0 |
| `css/03-components/forms.css` | 149 | 0 | 0 | 0 |
| `css/03-components/navigation-controls.css` | 13 | 0 | 0 | 0 |
| `css/03-components/status-badges.css` | 59 | 0 | 0 | 0 |
| `css/03-components/cards.css` | 13 | 0 | 0 | 0 |
| `css/03-components/empty-states.css` | 140 | 0 | 0 | 0 |
| `css/03-components/progress-loaders.css` | 63 | 0 | 0 | 0 |
| `css/03-components/dev-debug.css` | 34 | 1 | 0 | 0 |
| `css/04-batch-gallery/batch-rail.css` | 293 | 0 | 0 | 0 |
| `css/04-batch-gallery/source-import.css` | 254 | 0 | 0 | 0 |
| `css/04-batch-gallery/batch-summary.css` | 255 | 1 | 0 | 0 |
| `css/04-batch-gallery/gallery-shell.css` | 484 | 2 | 0 | 0 |
| `css/04-batch-gallery/image-grid.css` | 468 | 1 | 0 | 0 |
| `css/04-batch-gallery/thumbnails.css` | 291 | 0 | 0 | 0 |
| `css/04-batch-gallery/review-devtools.css` | 60 | 0 | 0 | 0 |
| `css/05-viewer/viewer-shell.css` | 75 | 0 | 0 | 0 |
| `css/05-viewer/viewer-toolbar.css` | 335 | 0 | 0 | 0 |
| `css/05-viewer/canvas.css` | 333 | 0 | 0 | 0 |
| `css/05-viewer/viewer-states.css` | 134 | 0 | 0 | 0 |
| `css/06-inspector-export/inspector-shell.css` | 271 | 2 | 0 | 0 |
| `css/06-inspector-export/inspector-navigation.css` | 180 | 0 | 0 | 0 |
| `css/06-inspector-export/inspector-workflow.css` | 187 | 0 | 0 | 0 |
| `css/06-inspector-export/inspector-cards.css` | 361 | 0 | 0 | 0 |
| `css/06-inspector-export/adjustments-presets.css` | 228 | 0 | 0 | 0 |
| `css/06-inspector-export/adjustment-controls.css` | 219 | 0 | 0 | 0 |
| `css/06-inspector-export/advanced-local-overrides.css` | 151 | 0 | 0 | 0 |
| `css/06-inspector-export/export-panel.css` | 288 | 0 | 0 | 0 |
| `css/06-inspector-export/output-profiles.css` | 482 | 0 | 0 | 0 |
| `css/06-inspector-export/review-warnings.css` | 197 | 0 | 0 | 0 |
| `css/07-modals/app-settings.css` | 161 | 0 | 0 | 0 |
| `css/07-modals/batch-detail.css` | 214 | 0 | 0 | 0 |
| `css/07-modals/export-confirm.css` | 137 | 0 | 0 | 0 |
| `css/08-states-responsive/states.css` | 316 | 3 | 0 | 0 |
| `css/08-states-responsive/responsive.css` | 471 | 0 | 0 | 0 |
| `css/99-legacy-compat.css` | 2 | 0 | 0 | 0 |
| **Total** | **8.998** | **18** | **7** | **255** |

Resumen:

- Tokens unicos activos: 223.
- Tokens duplicados entre archivos activos: 0.
- `!important` activos: 18, limitados a ocultacion/accesibilidad y guards de estado existentes.
- Selectores duplicados dentro del mismo contexto de cascada: 0.
- Listas de selectores duplicadas dentro del mismo contexto, normalizadas por orden: 0.
- Selectores con clases legacy de estado detectados: 0. Los estados visuales usan `data-ui-state`, `data-batch-context`, `data-status-footer` y `data-output-editing`.
- Mayor modulo activo: `css/04-batch-gallery/gallery-shell.css`, 484 lineas. El contrato evita pasar de 500 lineas por archivo.
- Todos los modulos enlazados tienen reglas activas; solo `css/99-legacy-compat.css` puede quedar vacio.
- `css/99-legacy-compat.css` esta intencionadamente vacio salvo comentario.

## Propiedad por modulo

- `00-settings/`: tokens canonicos, aliases legacy y overrides responsive de tokens. Es el unico propietario de `:root`.
- `01-base/`: reset, documento, tipografia base, foco y comportamiento primitivo de controles.
- `02-layout/`: shell, topbar, workspace y footer.
- `03-components/`: primitivas reutilizables, patrones de flujo, resultados/revision, botones, controles, chips, badges, cards, progress, estados vacios y dev/debug.
- `04-batch-gallery/`: importacion, lote, fuente, resumen, filtros, galeria, grid y miniaturas.
- `05-viewer/`: cabecera de preview, toolbar, canvas, zoom, fondos y estados de imagen.
- `06-inspector-export/`: panel derecho, navegacion, tarjetas, workflows de edicion, presets, ajustes, exportacion, warnings y formatos activos.
- `07-modals/`: ajustes de formatos, detalle de lote y confirmacion de exportacion.
- `08-states-responsive/`: `data-ui-state`, clases `is-*`, responsive y guards finales.
- `99-legacy-compat.css`: no debe recibir reglas nuevas salvo excepcion temporal documentada y con test.

## Contratos

- `index.html` debe enlazar solo los modulos anteriores y en ese orden.
- Los antiguos `styles.css`, `ux-foundation.css` y `ux-refactor.css` no forman parte del runtime y no deben existir en la raiz del frontend.
- No se declaran tokens fuera de `css/00-settings/tokens.css`; los cambios de estado deben expresarse como reglas, no como nuevos duenios de tokens.
- Mantener una unica capa `@layer flatshot` en todos los modulos activos salvo `99-legacy-compat.css`. No dividir en multiples capas sin una fase especifica de QA, porque cambiaria la semantica de cascada.
- Mantener `!important` por debajo de 25. Cualquier nuevo uso requiere razon local.
- Mantener cada modulo CSS por debajo de 500 lineas. Si un archivo crece, dividir por subdominio antes de ampliar excepciones.
- Mantener cero selectores duplicados y cero listas de selectores duplicadas dentro del mismo contexto de cascada; responsive y `@supports` son contextos distintos y se auditan por separado.
- Mantener cero selectores con clases legacy de estado; nuevas pantallas y transiciones deben usar `data-ui-state` o atributos `data-*` derivados.
- No reintroducir decoracion visual por runtime como `renderDesignSystemComponents()`; las reglas deben apuntar a clases reales del markup o templates.
- No meter logica de negocio ni procesamiento en CSS/JS visual.

## Validacion ejecutada en esta consolidacion

- `python scripts\audit_css.py --check`: 43 CSS activos, capa `flatshot`, 8.998 lineas, 18 `!important`, 0 tokens duplicados entre archivos, 0 selectores duplicados y 0 listas de selectores duplicadas dentro del mismo contexto, maximo 484 lineas por modulo, 0 selectores legacy de estado.
- `pytest tests\test_frontend_css_contract.py`: 8 passed.
- `pytest`: 294 passed.
- Smoke Playwright adicional en `1440x900` con `batch-ready` y salida `PNG transparente 1800x2400`: topbar sin resumen de lote ni punto suelto, selector de salida visible en galeria, miniaturas con etiqueta `PNG · transparente`, fondo transparente sincronizado con el viewer y sin overflow horizontal.
- Smoke Playwright en `?dev=1`: matriz de escritorio `1920x1080`, `1440x900`, `1366x768` y `1080x844` en estados `batch-ready`, `output-edit`, `export-running`, `formats-modal`, `batch-detail-modal` y `export-confirm-modal`; sin overflow horizontal, sin solape topbar/workspace, sin toolbar fuera del header de preview y sin errores JS de consola.
- Smoke Playwright responsive minimo `390x844`: `export-running` sin recorte de footer ni overflow horizontal.

## Salida exportada

Sin cambios esperados. La migracion solo toca CSS, `index.html`, documentacion,
tests de contrato y auditoria; no modifica core, bridge, preview service,
export runner, naming ni configuracion de salida.
