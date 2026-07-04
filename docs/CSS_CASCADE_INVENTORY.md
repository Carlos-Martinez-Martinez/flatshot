# Inventario de cascada CSS - FlatShot

Este documento registra la cascada CSS activa tras la limpieza de julio de
2026. La limpieza no cambia procesamiento, preview/export, naming, destinos ni
escritura de archivos.

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
37. `css/06-inspector-export/background-presets.css`
38. `css/06-inspector-export/review-warnings.css`
39. `css/07-modals/app-settings.css`
40. `css/07-modals/batch-detail.css`
41. `css/07-modals/export-confirm.css`
42. `css/08-states-responsive/states.css`
43. `css/08-states-responsive/responsive.css`
44. `css/99-legacy-compat.css`

No hay build step. El orden de enlaces es el contrato de cascada. Todos los
modulos activos, salvo `css/99-legacy-compat.css`, estan envueltos en una
unica capa `@layer flatshot` para mantener la prioridad relativa entre modulos.

## Metricas actuales

Medicion ejecutada con:

```powershell
python scripts\audit_css.py --check
```

| Archivo | Lineas | `!important` | `:root` | Tokens |
| --- | ---: | ---: | ---: | ---: |
| `css/00-settings/tokens.css` | 563 | 0 | 5 | 498 |
| `css/01-base/base.css` | 61 | 7 | 0 | 0 |
| `css/02-layout/shell-workspace.css` | 127 | 0 | 0 | 0 |
| `css/02-layout/topbar.css` | 433 | 0 | 0 | 0 |
| `css/02-layout/footer.css` | 78 | 0 | 0 | 0 |
| `css/03-components/primitives.css` | 162 | 0 | 0 | 0 |
| `css/03-components/workflow-panels.css` | 201 | 0 | 0 | 0 |
| `css/03-components/review-status-panels.css` | 113 | 0 | 0 | 0 |
| `css/03-components/buttons.css` | 133 | 0 | 0 | 0 |
| `css/03-components/forms.css` | 156 | 0 | 0 | 0 |
| `css/03-components/navigation-controls.css` | 18 | 0 | 0 | 0 |
| `css/03-components/status-badges.css` | 46 | 0 | 0 | 0 |
| `css/03-components/cards.css` | 13 | 0 | 0 | 0 |
| `css/03-components/empty-states.css` | 97 | 0 | 0 | 0 |
| `css/03-components/progress-loaders.css` | 63 | 0 | 0 | 0 |
| `css/03-components/dev-debug.css` | 28 | 1 | 0 | 0 |
| `css/04-batch-gallery/batch-rail.css` | 262 | 0 | 0 | 0 |
| `css/04-batch-gallery/source-import.css` | 255 | 0 | 0 | 0 |
| `css/04-batch-gallery/batch-summary.css` | 208 | 0 | 0 | 0 |
| `css/04-batch-gallery/gallery-shell.css` | 493 | 0 | 0 | 0 |
| `css/04-batch-gallery/image-grid.css` | 470 | 0 | 0 | 0 |
| `css/04-batch-gallery/thumbnails.css` | 306 | 0 | 0 | 0 |
| `css/04-batch-gallery/review-devtools.css` | 58 | 0 | 0 | 0 |
| `css/05-viewer/viewer-shell.css` | 69 | 0 | 0 | 0 |
| `css/05-viewer/viewer-toolbar.css` | 323 | 0 | 0 | 0 |
| `css/05-viewer/canvas.css` | 220 | 0 | 0 | 0 |
| `css/05-viewer/viewer-states.css` | 175 | 0 | 0 | 0 |
| `css/06-inspector-export/inspector-shell.css` | 207 | 0 | 0 | 0 |
| `css/06-inspector-export/inspector-navigation.css` | 131 | 0 | 0 | 0 |
| `css/06-inspector-export/inspector-workflow.css` | 155 | 0 | 0 | 0 |
| `css/06-inspector-export/inspector-cards.css` | 266 | 0 | 0 | 0 |
| `css/06-inspector-export/adjustments-presets.css` | 209 | 0 | 0 | 0 |
| `css/06-inspector-export/adjustment-controls.css` | 183 | 0 | 0 | 0 |
| `css/06-inspector-export/advanced-local-overrides.css` | 259 | 0 | 0 | 0 |
| `css/06-inspector-export/export-panel.css` | 279 | 0 | 0 | 0 |
| `css/06-inspector-export/output-profiles.css` | 441 | 0 | 0 | 0 |
| `css/06-inspector-export/background-presets.css` | 80 | 0 | 0 | 0 |
| `css/06-inspector-export/review-warnings.css` | 197 | 0 | 0 | 0 |
| `css/07-modals/app-settings.css` | 437 | 0 | 0 | 0 |
| `css/07-modals/batch-detail.css` | 135 | 0 | 0 | 0 |
| `css/07-modals/export-confirm.css` | 180 | 0 | 0 | 0 |
| `css/08-states-responsive/states.css` | 358 | 2 | 0 | 0 |
| `css/08-states-responsive/responsive.css` | 368 | 0 | 0 | 0 |
| `css/99-legacy-compat.css` | 2 | 0 | 0 | 0 |
| **Total** | **9018** | **10** | **5** | **311** |

Resumen:

- Hojas activas: 44.
- Tokens unicos activos: 311.
- Tokens duplicados entre archivos activos: 0.
- `!important` activos: 10.
- Selectores duplicados dentro del mismo contexto de cascada: 0.
- Listas de selectores duplicadas dentro del mismo contexto, normalizadas por orden: 0.
- Clases CSS activas sin referencia en HTML/JS runtime: 0.
- IDs CSS activos sin referencia en HTML/JS runtime: 0.
- Selectores con clases legacy de estado detectados: 0.
- Mayor modulo activo: `css/00-settings/tokens.css`, 563 lineas. El contrato permite hasta 650 lineas por modulo.
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
- Mantener `!important` por debajo de 10 o igual a 10. Cualquier nuevo uso requiere razon local y debe pasar `audit_css.py --check`.
- Mantener cada modulo CSS por debajo de 650 lineas.
- Mantener cero selectores duplicados y cero listas de selectores duplicadas dentro del mismo contexto de cascada; responsive y `@supports` son contextos distintos y se auditan por separado.
- Mantener cero clases CSS activas sin referencia en HTML/JS runtime. Las clases construidas dinamicamente deben estar en la allowlist pequena de `scripts/audit_css.py`.
- Mantener cero IDs CSS activos sin referencia en HTML/JS runtime. Los IDs construidos dinamicamente deben estar en la allowlist pequena de `scripts/audit_css.py`.
- Mantener cero selectores con clases legacy de estado; nuevas pantallas y transiciones deben usar `data-ui-state` o atributos `data-*` derivados.
- No reintroducir decoracion visual por runtime como `renderDesignSystemComponents()`; las reglas deben apuntar a clases reales del markup o templates.
- No meter logica de negocio ni procesamiento en CSS/JS visual.

## Validacion requerida

Antes de reportar cambios CSS/frontend como completos:

```powershell
python scripts\audit_css.py --check
pytest tests\test_frontend_css_contract.py
python scripts\audit_frontend.py --check
pytest
```

Para cambios visuales, revisar manualmente al menos:

- Estados `no_folder`, `scanning`, `batch_empty`, `scan_empty`, lote listo y exportacion en curso.
- Galeria en lista y miniaturas, busqueda, filtros y seleccion.
- Viewer con fondos `rgb230`, blanco, transparente y personalizado.
- Inspector de revision, ajustes, avisos y edicion de salida.
- Modales de preferencias, formatos, detalle de lote y confirmacion de exportacion.
- Viewports de escritorio, tablet y movil sin overflow horizontal ni solapes.

## Salida exportada

Sin cambios esperados. Este inventario solo describe CSS, documentacion, tests
de contrato y auditoria; no modifica core, bridge, preview service, export
runner, naming ni configuracion de salida.
