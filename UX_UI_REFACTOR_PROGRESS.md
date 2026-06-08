# FlatShot UX/UI Refactor Progress

## Fase 0 - Auditoria inicial y proteccion

Estado: completada.

Cambios realizados:
- Rama de trabajo creada: `codex/ui-system-consolidation`.
- Plan leido completo: `flatshot_plan_fases_ux_ui.md`.
- UI afectada localizada en `apps/flatshot-desktop/frontend/index.html`, `app.js`, `styles.css`, `ux-foundation.css` y `ux-refactor.css`.
- Documento de sistema existente revisado: `docs/FLATSHOT_DESIGN_SYSTEM.md`.

Mapa de componentes:
- Cabecera global y acciones: `index.html` (`.top-bar`, `.top-actions`) y `renderTop()`.
- Empty state y visor central: `initialStateHtml()`, `renderPreview()`, `emptyStateHtml()`.
- Shell/layout: `.workspace`, `.batch-panel`, `.gallery-column`, `.preview-panel`, `.settings-panel`.
- Galeria y miniaturas: `renderBatch()`, `imageItemHtml()`, `renderFilterButtons()`, `renderGalleryViewButtons()`.
- Panel derecho/resumen: `renderInspector()`, `inspectorCardsHtml()`, `lotInspectorCardHtml()`, `outputInspectorCardHtml()`, `selectedImageInspectorCardHtml()`, `aspectInspectorCardHtml()`.
- Edicion de salidas: `renderExport()`, `beginOutputEdit()`, `applyOutputEdit()`.
- Gestor de salidas: modal `#app-settings-modal`, `renderAppSettings()`, `renderOutputProfileModalState()`.
- Detalle de lote: modal `#batch-detail-modal`, `batchDetailHtml()`.
- Ajustes de imagen: `renderSettings()`, detalles `.preset-section`, `.appearance-section`, `.advanced-block`, `.local-adjustment`.

Orden de intervencion:
1. Consolidar tokens/estados y layout desde `ux-refactor.css`.
2. Normalizar microcopy y acciones principales en `index.html`.
3. Ajustar HTML renderizado en `app.js` por bloques: galeria, visor, inspector, salidas, ajustes y detalle.
4. Ejecutar validaciones disponibles y revision visual local.

Validaciones ejecutadas:
- Navegador integrado: intento inicial fallido por crash de la herramienta al cargar localhost.
- Playwright CLI: referencia inicial tomada en `http://127.0.0.1:4174?dev=1`.

Incidencias encontradas:
- La UI ya tenia capas de refactor previas en `styles.css`, `ux-foundation.css` y `ux-refactor.css`; se prioriza una capa final de consolidacion para evitar reescrituras amplias.
- El puerto `4173` servia otra app local; se uso `4174` para FlatShot.

Decisiones tomadas:
- Mantener la logica de preview/export/presets en JavaScript existente y servicios Python.
- No tocar motor de imagen ni runners de exportacion.
- Usar el CSS cargado al final para reducir el alcance del cambio.

## Fase 1 - Sistema visual base

Estado: completada.

Cambios realizados:
- Se consolido una capa final de tokens/layout en `ux-refactor.css`.
- Botones, acciones, tarjetas de resumen, filas de salida, inputs numericos, sliders, gestor y detalle usan radios/alturas/gaps comunes.
- Estados diferenciados: principal como badge, activo como checkbox, seleccionado como borde/fondo suave, modificado/temporal en ambar.

Validaciones ejecutadas:
- `node --check apps/flatshot-desktop/frontend/app.js`.
- Revision visual en Playwright: lote cargado, varias salidas activas, ajustes y gestor.

Decisiones tomadas:
- No se anadio ninguna dependencia.
- Se mantuvieron las primitivas `ui-*` existentes y se ampliaron las clases asignadas por `renderDesignSystemComponents()`.

## Fase 2 - Shell, cabecera y layout

Estado: completada.

Cambios realizados:
- El estado sin lote usa una sola columna centrada.
- El estado con lote usa tres columnas operativas: galeria, visor y panel derecho.
- La cabecera mantiene identidad y acciones globales; los controles debug siguen disponibles solo en modo dev.
- El panel derecho se expande a 460-520 px durante edicion de salidas.

Validaciones ejecutadas:
- Capturas Playwright: `after-initial-fixed.png`, `after-batch-ready-fixed.png`, `after-narrow.png`.

Incidencias encontradas:
- El primer ajuste de grid dejaba un bloque vacio sobre la galeria con lote cargado; corregido ocultando el rail de importacion cuando hay lote y haciendo que la galeria ocupe la columna izquierda completa.

## Fase 3 - Galeria y miniaturas

Estado: completada.

Cambios realizados:
- Contador principal cambiado a `X imagen(es) lista(s)`.
- Buscador mantiene el boton limpiar oculto hasta que hay texto.
- Miniaturas sin metadata repetida en vista de miniaturas.
- Estado seleccionado discreto con borde/fondo suave.
- Fondo de miniatura sigue el fondo de la salida principal activa (`rgb230`, blanco o transparente con damero).

Validaciones ejecutadas:
- Playwright: lote mock cargado, seleccion visible, filtros y varias salidas activas.

## Fase 4 - Visor, canvas y toolbar

Estado: completada.

Cambios realizados:
- Toolbar mantiene nombre de archivo con tooltip, fondo de revision, navegacion y zoom en controles homogeneos.
- Fondo de revision queda limitado al area/canvas.
- Se conservaron limites de pan/zoom existentes.
- Se eliminaron sombras decorativas del contenedor de canvas; la sombra visible en mock corresponde al producto/render de prueba.

Validaciones ejecutadas:
- Playwright: lote cargado, fondo gris, navegacion/zoom visibles y sin solapamiento en 1440 y 1120 px.

## Fase 5 - Panel derecho resumen

Estado: completada.

Cambios realizados:
- `Salidas activas · N` con archivos previstos como dato secundario.
- Filas de salidas con checkbox, metadata y badge `Principal`/`Activa`.
- `Editar salidas` queda como accion primaria; `Gestionar presets` como secundaria.
- Imagen seleccionada y ajuste quedan compactos y sin duplicidad.

Validaciones ejecutadas:
- Playwright: una salida activa y varias salidas activas.

## Fase 6 - Edicion de salidas y gestor de presets

Estado: completada.

Cambios realizados:
- Edicion rapida usa panel derecho expandido, no formulario comprimido.
- CTA cambiado a `Aplicar temporalmente`; acciones de guardar quedan secundarias.
- Gestor de salidas muestra acciones visibles (`Nuevo`, `Duplicar`, `Restaurar`, `Eliminar`) sin menu ambiguo.
- Ejemplo de exportacion queda como bloque compacto.
- Footer del detalle de lote ya no compite con presets.

Validaciones ejecutadas:
- Playwright: `after-output-edit.png`, `after-output-manager.png`.

## Fase 7 - Ajustes de imagen

Estado: completada.

Cambios realizados:
- Microcopy normalizada a `Editar ajuste`, `Ajuste`, `Global`.
- Sliders mantienen input numerico editable y valores sin clipping.
- `Avanzado` queda colapsado salvo cambios/accion del usuario.
- Ajuste local se presenta en bloque separado con inputs numericos.

Validaciones ejecutadas:
- Playwright: `after-adjustments-final.png`.

## Fase 8 - Detalle de lote

Estado: completada.

Cambios realizados:
- Detalle convertido en vista de auditoria con secciones `Resumen`, `Entrada`, `Lote`, `Salidas activas`, `Ignorados tecnicos` e `Incidencias`.
- Varias salidas se muestran una por una con destino y ejemplo.
- Ignorados tecnicos quedan colapsados por defecto cuando existen.
- Footer reducido a `Cerrar` y `Cambiar carpeta`.

Validaciones ejecutadas:
- Playwright: `after-batch-detail.png`.

## Fase 9 - Microinteracciones, responsive, accesibilidad y QA final

Estado: completada.

Cambios realizados:
- Menus/details transitorios se cierran al hacer click fuera.
- Escape mantiene cierre de modales/details existente.
- Correccion de foco al cerrar modales para evitar `aria-hidden` sobre descendiente enfocado.
- Responsive revisado en 1440x900 y 1120x760.

Validaciones ejecutadas:
- `node --check apps/flatshot-desktop/frontend/app.js`.
- `pytest` completo: 237 passed.
- Playwright CLI: inicial, lote cargado, varias salidas, edicion de salidas, gestor, detalle de lote, ajustes y ventana estrecha.
- Consola Playwright tras correccion de foco: 0 errores, 0 warnings.

Limitaciones:
- La validacion visual se hizo con estados mock/dev. No se ejecuto exportacion real de archivos desde una carpeta de produccion en esta pasada.
- No se modifico salida de imagen ni comportamiento de archivos exportados.

## Fase 10 - Consolidacion adicional del informe v2

Estado: completada.

Cambios realizados:
- Estado de escaneo reforzado como estado centrado de una sola columna: sin galeria, panel derecho ni rail lateral visibles durante el escaneo.
- Boton superior de escaneo tratado como estado pasivo deshabilitado (`Escaneando`) y no como CTA primario.
- Selector de fondo del visor ajustado para usar swatches cuadrados, evitando indicadores circulares que podian leerse como radios.
- Panel derecho de salidas ajustado a `Salidas activas · N` + archivos previstos como dato principal.
- Eliminado el badge textual `Activa` en filas de salida; el checkbox comunica activo y `Principal` queda como unico badge.
- Microcopy corregida: `0 imagenes listas`, `Ignorados tecnicos en detalle`, `Ver detalle`.
- Gestor de salidas: CTA del footer aclarado entre `Guardar y aplicar`, `Aplicar cambios al lote` y `Activar en este lote`.
- Editor de ajustes: `Gestionar ajustes` queda como subvista secundaria explicita; la edicion operativa mantiene un unico encabezado, controles principales, avanzado colapsado y ajuste por imagen.
- Guardar ajustes queda deshabilitado cuando no hay cambios pendientes; eliminar mantiene estilo destructivo.

Archivos modificados:
- `apps/flatshot-desktop/frontend/index.html`
- `apps/flatshot-desktop/frontend/app.js`
- `apps/flatshot-desktop/frontend/ux-refactor.css`
- `UX_UI_REFACTOR_PROGRESS.md`

Decisiones tomadas:
- No tocar motor de imagen, preview service, export runner, presets Python ni logica de archivos.
- No anadir dependencias.
- Mantener el refactor en la capa frontend existente para evitar una reescritura amplia.
- Usar estados mock/dev para la revision visual, sin abrir carpetas reales ni ejecutar exportacion real.

Validaciones ejecutadas:
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `git diff --check`: OK; solo avisos Git LF/CRLF en archivos frontend modificados.
- `pytest`: 237 passed.
- Playwright CLI en `http://127.0.0.1:4185/?dev=1`:
  - sin lote: una columna, sin galeria/panel derecho, sin overflow horizontal;
  - escaneo: una columna, paneles laterales ocultos, texto `Escaneando carpeta...`, boton `Escaneando` deshabilitado, sin overflow;
  - lote mock: galeria visible, panel derecho visible, `4 imagenes listas`, selector de fondo con swatch 12x12 y radio 3px;
  - varias salidas activas: `Salidas activas · 2`, 8 archivos previstos, 2 checkboxes activos, solo badge `Principal`;
  - detalle de lote: 2 salidas activas listadas, footer `Cerrar` / `Cambiar carpeta`, Escape cierra;
  - gestor de salidas: 3 presets, 1 seleccionado, 1 principal, 2 activos por checkbox, footer `Aplicar cambios al lote`, Escape cierra;
  - editor de ajustes: encabezado unico, controles principales y ajuste por imagen abiertos, avanzado colapsado;
  - avanzado expandido: sliders e inputs numericos alineados con la misma grilla;
  - gestionar ajustes: subvista separada, controles principales/locales ocultos, guardar deshabilitado sin cambios, eliminar destructivo;
  - viewport 1120x760 y 1000x760: sin overflow horizontal.

Problemas encontrados:
- El navegador integrado de Codex volvio a mostrar una pagina de crash al navegar a localhost, por lo que la revision visual final se hizo con Playwright CLI.
- PowerShell quedo bloqueado durante comandos Playwright paralelos; las validaciones finales se ejecutaron mediante Node `child_process`.
- La captura Playwright intentada en paralelo no se conservo como evidencia; se conservaron los resultados textuales de checks DOM/computed-style.

Deuda tecnica pendiente:
- Seria conveniente convertir los controles de ajuste en un componente JS/HTML unico (`SliderField`) en una pasada posterior, aunque visualmente ya comparten grilla y comportamiento.
- La capa CSS sigue teniendo reglas historicas duplicadas en `styles.css`, `ux-foundation.css` y `ux-refactor.css`; se mantuvo la consolidacion final para minimizar riesgo.

Salida exportada:
- Sin cambios esperados en apariencia de imagen exportada ni comportamiento de archivos. No se ejecuto exportacion real.

## Fase 11 - Implementacion del audit de higiene de codigo

Estado: completada.

Rama de trabajo:
- `codex/code-health-audit-implementation`.

Commits subidos:
- `aac39c3 Add CODE_HEALTH_AUDIT.md (FlatShot)`.
- `166b84e Extract frontend audit helpers`.
- `c3bb087 Document CSS cascade inventory`.
- `26e6bf6 Add export output parity coverage`.

Cambios realizados:
- Se creo `CODE_HEALTH_AUDIT.md` como informe raiz en espanol, especifico al estado inspeccionado del repo.
- Se extrajeron helpers frontend puros desde `app.js` sin introducir build step ni dependencias:
  - perfiles de salida y mapping de exportacion;
  - preflight/readiness;
  - galeria, lote, detalle de lote y empty states;
  - preview, scan y export state;
  - formatters y modal de confirmacion de exportacion.
- `index.html` carga los nuevos modulos JS antes de `app.js`.
- Se documentaron contratos de frontera:
  - `docs/FRONTEND_BRIDGE_EXPORT_CONTRACT.md`;
  - `docs/FRONTEND_STATE_CONTRACT.md`;
  - `docs/LOW_USE_MODELS_AUDIT.md`;
  - `docs/CSS_CASCADE_INVENTORY.md`.
- `docs/ARCHITECTURE_GUARDS.md` referencia los contratos para evitar que futuras fases rompan la frontera frontend/bridge, estados, modelos de bajo uso o cascada CSS.
- Se agregaron tests unitarios ligeros para los helpers frontend.
- Se agrego cobertura de salida/exportacion para DPI, JPG 4:4:4, PNG transparente, variantes y no mutacion de fuente.

Archivos CSS:
- No se modificaron `styles.css`, `ux-foundation.css` ni `ux-refactor.css`.
- La fase CSS fue inventario y estrategia; la reduccion real de tokens/overrides queda pendiente de capturas antes/despues.

Validaciones ejecutadas:
- `venv\Scripts\python.exe -m pytest -q`: 262 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- `git diff --check`: OK; solo avisos Git LF/CRLF en Windows.
- Test aislado nuevo: `tests/test_export_variants.py::test_export_runner_preserves_output_metadata_transparency_and_source_file`: OK.
- Carga estatica previa de frontend por HTTP local: `index.html`, helpers JS y `app.js` respondieron 200.

Checks manuales:
- No se ejecuto un flujo UI manual completo en esta fase porque los cambios son extracciones puras, documentacion y tests.
- No se ejecuto exportacion real sobre carpetas de produccion; la nueva prueba de paridad usa archivos temporales de test.

Decisiones tomadas:
- No tocar `src/flatshot/application/export_runner.py`, `src/flatshot/core/engine.py`, `src/flatshot/core/scaling.py` ni `src/flatshot/bridge/service.py` en esta pasada.
- No borrar `JobItem`; queda marcado para investigacion antes de cualquier eliminacion.
- No hacer reescritura de stack, migracion ni dependencia nueva.
- Mantener payloads y nombres existentes mientras se extraen helpers alrededor.

Salida exportada:
- Sin cambios esperados en apariencia de imagen exportada ni comportamiento de archivos.
- No se modifico el pipeline de imagen ni la logica de escritura de archivos.

## Fase 12 - Limpieza CSS acotada post-inventario

Estado: completada.

Cambios realizados:
- Se redujo el primer bloque `:root` de `ux-foundation.css`.
- Se retiraron 25 aliases tempranos que ya estaban redefinidos por el bloque final de la misma hoja.
- Se conservaron tokens que esa capa sigue definiendo como fuente activa: `--semantic-success-soft`, `--semantic-info-*`, `--z-*` y `--ui-*`.
- Se actualizaron las metricas en `docs/CSS_CASCADE_INVENTORY.md`.

Impacto medido:
- `ux-foundation.css`: 3.494 -> 3.469 lineas.
- Declaraciones de tokens CSS totales: 463 -> 438.
- Nombres de token duplicados: 164 -> 145.
- `!important`: sin cambios, 337 en total.

Validaciones ejecutadas:
- `venv\Scripts\python.exe -m pytest -q`: 262 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- `git diff --check`: OK; solo avisos Git LF/CRLF en Windows.
- HTTP local en `http://127.0.0.1:4192/`: `index.html`, `styles.css`, `ux-foundation.css`, `ux-refactor.css` y `app.js` respondieron 200.

Checks manuales:
- No se ejecuto flujo visual completo; esta fase solo retira aliases CSS redundantes que quedan definidos por el bloque final de la misma hoja.

Salida exportada:
- Sin cambios esperados. No se toco codigo de procesamiento ni exportacion.

## Fase 13 - Extraccion de vistas de formatos de salida

Estado: completada.

Cambios realizados:
- Se agrego `apps/flatshot-desktop/frontend/output-profile-view.js`.
- Se movio HTML puro del editor/gestor de formatos de salida fuera de `app.js`:
  - encabezado del editor;
  - preview de nombre/destino;
  - mensajes de validacion;
  - fila del gestor de formatos;
  - naming por plantilla para preview.
- `index.html` carga el helper antes de `app.js`.
- `app.js` mantiene la logica de estado, formulario, handlers y persistencia; solo delega renderizado puro.
- Se agrego `tests/test_frontend_output_profile_view.py` para contrato de HTML, escaping, naming y orden de carga.

Impacto medido:
- `app.js`: 7.919 -> 7.865 lineas.

Validaciones ejecutadas:
- `venv\Scripts\python.exe -m pytest tests/test_frontend_output_profile_view.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 264 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- `node --check apps/flatshot-desktop/frontend/output-profile-view.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `git diff --check`: OK; solo avisos Git LF/CRLF en Windows.
- HTTP local en `http://127.0.0.1:4193/`: `index.html`, `output-profile-view.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico pipeline de imagen, bridge Python ni escritura de archivos.

## Fase 14 - Extraccion de vista de resultado de exportacion

Estado: completada.

Cambios realizados:
- Se agrego `apps/flatshot-desktop/frontend/export-result-view.js`.
- Se movio HTML puro del bloque de resultado de exportacion fuera de `app.js`:
  - titulo y clase visual del resultado;
  - metadata procesadas/totales/errores;
  - resumen de issue de exportacion;
  - acciones (`Abrir carpeta`, `Revisar avisos`, `Reintentar`);
  - render de destinos, archivo actual e items procesados.
- `index.html` carga el helper antes de `app.js`.
- `app.js` mantiene los datos de estado, readiness, destino abierto y seleccion de issues; solo delega presentacion.
- Se agrego `tests/test_frontend_export_result_view.py` para labels, acciones, escaping, HTML final y orden de carga.

Impacto medido:
- `app.js`: 7.865 -> 7.796 lineas.

Validaciones ejecutadas:
- `venv\Scripts\python.exe -m pytest tests/test_frontend_export_result_view.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 266 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- `node --check apps/flatshot-desktop/frontend/export-result-view.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `git diff --check`: OK; solo avisos Git LF/CRLF en Windows.
- HTTP local en `http://127.0.0.1:4194/`: `index.html`, `export-result-view.js`, `output-profile-view.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 20 - Extraccion de vista contextual del inspector

Estado: completada.

Cambios realizados:
- Se agrego `apps/flatshot-desktop/frontend/inspector-context-view.js`.
- Se movio HTML puro fuera de `app.js` para:
  - encabezado de subvista del inspector;
  - panel contextual de escaneo;
  - panel de seleccion inicial de carpeta;
  - panel de carpeta vacia;
  - fallback de "Selecciona una imagen".
- `index.html` carga el helper antes de `app.js`.
- `app.js` conserva los estados, filas preflight, labels de salida y acciones; solo delega presentacion.
- Se agrego `tests/test_frontend_inspector_context_view.py` para estados contextuales, encabezado, escaping y orden de carga.

Impacto medido:
- `app.js`: 7.620 -> 7.589 lineas.

Validaciones ejecutadas:
- `venv\Scripts\python.exe -m pytest tests/test_frontend_inspector_context_view.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 274 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- `node --check apps/flatshot-desktop/frontend/inspector-context-view.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `git diff --check`: OK; solo avisos Git LF/CRLF en Windows.
- HTTP local en `http://127.0.0.1:4200/`: `index.html`, `inspector-context-view.js`, `inspector-review-view.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 21 - Extraccion de vista resumen de exportacion

Estado: completada.

Cambios realizados:
- Se agrego `apps/flatshot-desktop/frontend/export-summary-view.js`.
- Se movio HTML puro del resumen de exportacion fuera de `app.js`:
  - resumen compacto durante edicion de salida;
  - aviso compacto de cambios temporales;
  - acciones de aplicar/guardar/cancelar edicion;
  - tarjeta de salida o salidas activas;
  - filas resumidas de perfiles activos;
  - acciones de editar salidas y gestionar presets.
- `index.html` carga el helper antes de `app.js`.
- `app.js` conserva calculos de readiness, perfiles activos, labels, destinos, ejemplos, avisos y estado; solo delega presentacion.
- Se agrego `tests/test_frontend_export_summary_view.py` para HTML, escaping, acciones, multiples salidas y orden de carga.

Impacto medido:
- `app.js`: 7.589 -> 7.533 lineas.
- Modulos JS frontend: 19 -> 20.
- Tests frontend `test_frontend_*.py`: 18 -> 19.

Validaciones ejecutadas:
- `venv\Scripts\python.exe -m pytest tests/test_frontend_export_summary_view.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 276 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- `node --check apps/flatshot-desktop/frontend/export-summary-view.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `git diff --check`: OK; solo avisos Git LF/CRLF en Windows.
- HTTP local en `http://127.0.0.1:4201/`: `index.html`, `export-summary-view.js`, `export-result-view.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 22 - Extension del selector de perfiles de salida

Estado: completada.

Cambios realizados:
- `export-summary-view.js` ahora tambien renderiza las opciones del selector de perfil de salida.
- `renderOutputProfileSelect()` conserva el nodo DOM, el valor seleccionado y la decision de mostrar `Personalizado sin guardar`; solo delega el HTML de `<option>`.
- Se amplio `tests/test_frontend_export_summary_view.py` para cubrir escaping de IDs/nombres y opcion personalizada.

Impacto medido:
- `app.js`: 7.533 -> 7.530 lineas.

Validaciones ejecutadas:
- `venv\Scripts\python.exe -m pytest tests/test_frontend_export_summary_view.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 276 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- `node --check apps/flatshot-desktop/frontend/export-summary-view.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `git diff --check`: OK; solo avisos Git LF/CRLF en Windows.
- HTTP local en `http://127.0.0.1:4202/`: `index.html`, `export-summary-view.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 23 - Extraccion de vista del preview

Estado: completada.

Cambios realizados:
- Se agrego `apps/flatshot-desktop/frontend/preview-view.js`.
- Se movio HTML puro del canvas de preview fuera de `app.js`:
  - estado de carga de preview;
  - estado de escaneo;
  - imagen real generada con dimensiones de zoom;
  - placeholder de preview real pendiente;
  - preview mock y aviso de fallback.
- `index.html` carga el helper antes de `app.js`.
- `app.js` conserva seleccion, modo bridge/mock, calculos de zoom, pan, clases del canvas, estado de preview y decisiones de flujo; solo delega presentacion.
- Se agrego `tests/test_frontend_preview_view.py` para HTML, escaping, warning, dimensiones de zoom y orden de carga.

Impacto medido:
- `app.js`: 7.530 -> 7.504 lineas.
- Modulos JS frontend: 20 -> 21.
- Tests frontend `test_frontend_*.py`: 19 -> 20.

Validaciones ejecutadas:
- `venv\Scripts\python.exe -m pytest tests/test_frontend_preview_view.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 278 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- `node --check apps/flatshot-desktop/frontend/preview-view.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `git diff --check`: OK; solo avisos Git LF/CRLF en Windows.
- HTTP local en `http://127.0.0.1:4203/`: `index.html`, `preview-view.js`, `preview-state.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 24 - Extraccion de estado visual de cabecera

Estado: completada.

Cambios realizados:
- Se agrego `apps/flatshot-desktop/frontend/top-status-view.js`.
- Se movio presentacion pura de cabecera fuera de `app.js`:
  - chips compactos de estado superior;
  - texto compacto de lote/exportacion;
  - texto de estado superior;
  - label y clase del chip preflight.
- `index.html` carga el helper antes de `app.js`.
- `app.js` conserva lectura de estado global, conteos, readiness, bridge y totales planificados; solo pasa datos serializables al helper.
- Se agrego `tests/test_frontend_top_status_view.py` para chips, escaping, estados de lote/exportacion, preflight y orden de carga.

Impacto medido:
- `app.js`: 7.504 -> 7.450 lineas.
- Modulos JS frontend: 21 -> 22.
- Tests frontend `test_frontend_*.py`: 20 -> 21.

Validaciones ejecutadas:
- `venv\Scripts\python.exe -m pytest tests/test_frontend_top_status_view.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 280 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- `node --check apps/flatshot-desktop/frontend/top-status-view.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `git diff --check`: OK; solo avisos Git LF/CRLF en Windows.
- HTTP local en `http://127.0.0.1:4204/`: `index.html`, `top-status-view.js`, `export-preflight-view.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 25 - Extraccion de vista de ajustes

Estado: completada.

Cambios realizados:
- Se agrego `apps/flatshot-desktop/frontend/settings-view.js`.
- Se movio presentacion pura de ajustes fuera de `app.js`:
  - chips de presets;
  - estado `Sin guardar` / `Sin cambios`;
  - texto de ajuste local;
  - formato de valores locales con signo;
  - estado de botones de guardar/eliminar preset;
  - titulo compacto de `Avanzado`.
- `index.html` carga el helper antes de `app.js`.
- `app.js` conserva lectura/escritura de inputs, sliders, checkboxes, seleccion actual, overrides locales y handlers; solo delega etiquetas/HTML puro.
- Se agrego `tests/test_frontend_settings_view.py` para chips, escaping, labels, estados de botones y orden de carga.

Impacto medido:
- `app.js`: 7.450 -> 7.441 lineas.
- Modulos JS frontend: 22 -> 23.
- Tests frontend `test_frontend_*.py`: 21 -> 22.

Validaciones ejecutadas:
- `venv\Scripts\python.exe -m pytest tests/test_frontend_settings_view.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 282 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- `node --check apps/flatshot-desktop/frontend/settings-view.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `git diff --check`: OK; solo avisos Git LF/CRLF en Windows.
- HTTP local en `http://127.0.0.1:4205/`: `index.html`, `settings-view.js`, `preview-state.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 26 - Extraccion de subtitulo de preview

Estado: completada.

Cambios realizados:
- `preview-state.js` ahora tambien calcula el subtitulo del visor segun:
  - ausencia de imagen;
  - filtro sin resultados;
  - lote sin cargar, vacio o escaneando;
  - preview bridge;
  - preview mock;
  - estados `loading`, `warning`, `error`, `ready` y pendiente.
- `app.js` conserva seleccion, filtros activos, estado global y detalle de imagen; solo pasa datos serializables al helper.
- Se amplio `tests/test_frontend_preview_state.py` para cubrir subtitulos sin imagen, bridge y mock.

Impacto medido:
- `app.js`: 7.441 -> 7.412 lineas.
- Modulos JS frontend: sin cambios, 23.
- Tests frontend `test_frontend_*.py`: sin cambios, 22.

Validaciones ejecutadas:
- `venv\Scripts\python.exe -m pytest tests/test_frontend_preview_state.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 282 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- `node --check apps/flatshot-desktop/frontend/preview-state.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `git diff --check`: OK; solo avisos Git LF/CRLF en Windows.
- HTTP local en `http://127.0.0.1:4206/`: `index.html`, `preview-state.js`, `preview-view.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 27 - Extraccion de etiquetas de entrada y bridge

Estado: completada.

Cambios realizados:
- `scan-state.js` ahora tambien calcula presentacion pura del panel de entrada:
  - estado compacto de escaneo;
  - nombre visible de carpeta;
  - mensaje normal del bridge;
  - clase del panel de origen;
  - clase y texto del badge de origen;
  - titulo del bloque de entrada;
  - labels/titulos de botones de seleccionar/escanear;
  - clase del mensaje bridge.
- `app.js` conserva parseo de rutas, carpetas activas, deteccion bridge/mock, estado global y escritura de DOM; solo pasa datos serializables al helper.
- Se amplio `tests/test_frontend_scan_state.py` para cubrir labels, clases, pluralizacion, carpetas, mensajes y botones.

Impacto medido:
- `app.js`: 7.412 -> 7.395 lineas.
- Modulos JS frontend: sin cambios, 23.
- Tests frontend `test_frontend_*.py`: sin cambios, 22.

Validaciones ejecutadas:
- `venv\Scripts\python.exe -m pytest tests/test_frontend_scan_state.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 282 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- `node --check apps/flatshot-desktop/frontend/scan-state.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `git diff --check`: OK; solo avisos Git LF/CRLF en Windows.
- HTTP local en `http://127.0.0.1:4207/`: `index.html`, `scan-state.js`, `top-status-view.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 28 - Extraccion de resumen lateral de lote

Estado: completada.

Cambios realizados:
- `batch-view.js` ahora tambien renderiza HTML puro del resumen lateral de lote:
  - tarjeta `batch-summary-card`;
  - metricas compactas;
  - detalle de entrada;
  - estado del lote;
  - salida y naming;
  - siguiente paso;
  - bloque de diagnostico/omisiones.
- `app.js` conserva calculo de rutas, estado visible, perfiles de salida, destino, naming y diagnosticos; solo delega presentacion.
- Se amplio `tests/test_frontend_batch_view.py` para cubrir escaping, tono visual, metricas, diagnostico y resumen completo.

Impacto medido:
- `app.js`: 7.395 -> 7.286 lineas.
- Modulos JS frontend: sin cambios, 23.
- Tests frontend `test_frontend_*.py`: sin cambios, 22.

Validaciones ejecutadas:
- `venv\Scripts\python.exe -m pytest tests/test_frontend_batch_view.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 282 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- `node --check apps/flatshot-desktop/frontend/batch-view.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `git diff --check`: OK; solo avisos Git LF/CRLF en Windows.
- HTTP local en `http://127.0.0.1:4208/`: `index.html`, `batch-view.js`, `batch-detail-view.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 29 - Extraccion de estado de footer de perfiles

Estado: completada.

Cambios realizados:
- `output-profile-view.js` ahora tambien calcula estado puro del footer del gestor de perfiles:
  - disabled/title de eliminar;
  - disabled de reset/guardar/aplicar;
  - label de aplicar;
  - texto y clase de nota inferior.
- `app.js` conserva draft activo, persistencia, conteo de perfiles, validacion y escritura en DOM; solo delega calculos de presentacion.
- Se amplio `tests/test_frontend_output_profile_view.py` para cubrir estados persistido/unico, inactivo, sucio y con error.

Impacto medido:
- `app.js`: 7.286 -> 7.285 lineas.
- Modulos JS frontend: sin cambios, 23.
- Tests frontend `test_frontend_*.py`: sin cambios, 22.

Validaciones ejecutadas:
- `venv\Scripts\python.exe -m pytest tests/test_frontend_output_profile_view.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 282 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- `node --check apps/flatshot-desktop/frontend/output-profile-view.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `git diff --check`: OK; solo avisos Git LF/CRLF en Windows.
- HTTP local en `http://127.0.0.1:4209/`: `index.html`, `output-profile-view.js`, `output-profiles.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 30 - Extraccion de filas preflight de exportacion

Estado: completada.

Cambios realizados:
- `export-preflight-view.js` ahora tambien calcula:
  - clase visual del estado de exportacion;
  - filas preflight para lote ausente;
  - filas preflight para lote vacio;
  - filas preflight para lote listo;
  - inclusion filtrada de issues adicionales;
  - fila final de estado cuando no hay bloqueos ni avisos.
- `app.js` conserva calculo de readiness, issues, destino, naming, avisos e ignorados; solo pasa datos serializables al helper.
- Se amplio `tests/test_frontend_export_preflight_view.py` para cubrir clases de estado y filas de preflight.

Impacto medido:
- `app.js`: 7.285 -> 7.264 lineas.
- Modulos JS frontend: sin cambios, 23.
- Tests frontend `test_frontend_*.py`: sin cambios, 22.

Validaciones ejecutadas:
- `venv\Scripts\python.exe -m pytest tests/test_frontend_export_preflight_view.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 282 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- `node --check apps/flatshot-desktop/frontend/export-preflight-view.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `git diff --check`: OK; solo avisos Git LF/CRLF en Windows.
- HTTP local en `http://127.0.0.1:4210/`: `index.html`, `export-preflight-view.js`, `export-summary-view.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 31 - Extraccion de labels de destino y naming

Estado: completada.

Cambios realizados:
- `output-profile-view.js` ahora tambien calcula:
  - label compacto de destino;
  - label humano de plantilla de nombre;
  - ejemplo de nombre final;
  - fallback de destino para exportacion/resultados.
- `app.js` conserva seleccion de imagen, carpeta activa, formato actual, perfiles activos y datos de estado; solo delega reglas de presentacion/naming.
- Se amplio `tests/test_frontend_output_profile_view.py` para cubrir destino custom/source, multi-salida, plantillas vacias, extension explicita e indices.

Impacto medido:
- `app.js`: 7.264 -> 7.251 lineas.
- Modulos JS frontend: sin cambios, 23.
- Tests frontend `test_frontend_*.py`: sin cambios, 22.

Validaciones ejecutadas:
- `venv\Scripts\python.exe -m pytest tests/test_frontend_output_profile_view.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 282 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- `node --check apps/flatshot-desktop/frontend/output-profile-view.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `git diff --check`: OK; solo avisos Git LF/CRLF en Windows.
- HTTP local en `http://127.0.0.1:4211/`: `index.html`, `output-profile-view.js`, `export-summary-view.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 32 - Extraccion de filas de incidencias

Estado: completada.

Cambios realizados:
- `export-preflight-view.js` ahora tambien construye filas de incidencias a partir de omisiones de escaneo, imagenes con aviso/error de exportacion y errores globales.
- `app.js` conserva las fuentes de verdad (`scanOmissions`, `activeImages`, `state.errors`, `statusLabels`) y solo adapta los datos antes de delegar.
- Se amplio `tests/test_frontend_export_preflight_view.py` para cubrir omisiones ignoradas, omisiones revisables, imagenes con warning, imagenes bloqueadas por exportacion y errores globales.

Impacto medido:
- `app.js`: 7.251 -> 7.231 lineas.
- Modulos JS frontend: sin cambios, 23.
- Tests frontend `test_frontend_*.py`: sin cambios, 22.

Validaciones ejecutadas:
- `node --check apps/flatshot-desktop/frontend/export-preflight-view.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `venv\Scripts\python.exe -m pytest tests/test_frontend_export_preflight_view.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 282 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- HTTP local: `index.html`, `export-preflight-view.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 33 - Extraccion de textos de estado inferior

Estado: completada.

Cambios realizados:
- `top-status-view.js` ahora tambien calcula:
  - tooltip/hint de la accion primaria superior;
  - texto de la barra inferior para estados sin lote, escaneo, lote vacio, listo, exportando, completado, parcial y fallido.
- `app.js` conserva seleccion, conteos, estado de exportacion, destino y errores; solo delega reglas de microcopy/presentacion.
- Se amplio `tests/test_frontend_top_status_view.py` para cubrir las ramas de footer y accion primaria.

Impacto medido:
- `app.js`: 7.231 -> 7.202 lineas.
- Modulos JS frontend: sin cambios, 23.
- Tests frontend `test_frontend_*.py`: sin cambios, 22.

Validaciones ejecutadas:
- `node --check apps/flatshot-desktop/frontend/top-status-view.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `venv\Scripts\python.exe -m pytest tests/test_frontend_top_status_view.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 282 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- HTTP local: `index.html`, `top-status-view.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 34 - Extraccion de labels de ajustes y salida

Estado: completada.

Cambios realizados:
- `settings-view.js` ahora tambien calcula:
  - label humano de fondo (`transparent`, `white`, `rgb230`);
  - linea resumen de preset/formato;
  - label de estado de exportacion para el panel inferior.
- `app.js` conserva estado activo, `paused`, readiness, formato, tamano y fondo; solo delega reglas de microcopy.
- Se amplio `tests/test_frontend_settings_view.py` para cubrir labels de fondo, resumen de preset y estados de exportacion.

Impacto medido:
- `app.js`: 7.202 -> 7.192 lineas.
- Modulos JS frontend: sin cambios, 23.
- Tests frontend `test_frontend_*.py`: sin cambios, 22.

Validaciones ejecutadas:
- `node --check apps/flatshot-desktop/frontend/settings-view.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `venv\Scripts\python.exe -m pytest tests/test_frontend_settings_view.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 282 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- HTTP local: `index.html`, `settings-view.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 35 - Extraccion de view state de origen

Estado: completada.

Cambios realizados:
- `scan-state.js` ahora expone `sourcePanelViewState()` para derivar en un solo objeto:
  - clase del panel de origen;
  - badge y label de fuente;
  - titulo, nombre de carpeta y estado compacto;
  - labels/titles de botones de carpeta/escaneo;
  - estado disabled de controles;
  - mensaje y clase de bridge.
- `renderBridge()` en `app.js` consume ese view state y deja de reconstruir cada label/clase por separado.
- `sourceFolderName()` queda como wrapper porque se reutiliza en resumen y detalle de lote.
- Se amplio `tests/test_frontend_scan_state.py` para cubrir view states de lote listo y escaneo activo.

Impacto medido:
- `app.js`: 7.192 -> 7.183 lineas.
- Modulos JS frontend: sin cambios, 23.
- Tests frontend `test_frontend_*.py`: sin cambios, 22.

Validaciones ejecutadas:
- `node --check apps/flatshot-desktop/frontend/scan-state.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `venv\Scripts\python.exe -m pytest tests/test_frontend_scan_state.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 282 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- HTTP local: `index.html`, `scan-state.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 36 - Extraccion de estado de miniatura

Estado: completada.

Cambios realizados:
- `gallery.js` ahora expone `thumbnailState()` para decidir entre:
  - preview ausente (`Sin preview`);
  - estado almacenado compatible por `src` o `sourceSrc`;
  - estado inicial `loading`.
- `app.js` conserva el acceso al estado real `state.thumbnailStatus` y solo delega la decision pura.
- Se amplio `tests/test_frontend_gallery.py` para cubrir los tres caminos del estado de miniatura.

Impacto medido:
- `app.js`: 7.183 -> 7.179 lineas.
- Modulos JS frontend: sin cambios, 23.
- Tests frontend `test_frontend_*.py`: sin cambios, 22.

Validaciones ejecutadas:
- `node --check apps/flatshot-desktop/frontend/gallery.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `venv\Scripts\python.exe -m pytest tests/test_frontend_gallery.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 282 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- HTTP local: `index.html`, `gallery.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 37 - Extraccion de estado de filtros de galeria

Estado: completada.

Cambios realizados:
- `gallery.js` ahora expone `galleryFilterButtonStates()` para derivar:
  - label y contador de cada filtro;
  - titulo;
  - orden visual;
  - estado activo;
  - estado vacio;
  - visibilidad.
- `renderFilterButtons()` en `app.js` conserva la aplicacion DOM y delega el calculo del estado de botones.
- Se amplio `tests/test_frontend_gallery.py` para cubrir filtros visibles y filtros ocultos cuando solo queda `Todas`.

Impacto medido:
- `app.js`: 7.179 -> 7.178 lineas.
- Modulos JS frontend: sin cambios, 23.
- Tests frontend `test_frontend_*.py`: sin cambios, 22.

Validaciones ejecutadas:
- `node --check apps/flatshot-desktop/frontend/gallery.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `venv\Scripts\python.exe -m pytest tests/test_frontend_gallery.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 282 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- HTTP local: `index.html`, `gallery.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 38 - Extraccion de labels de estado bridge

Estado: completada.

Cambios realizados:
- `scan-state.js` ahora expone:
  - `bridgeStatusClass()`;
  - `bridgeStatusLabel()`.
- `app.js` conserva `bridgeMode`, `bridgeStatus` y `devMode`; solo delega clase y texto del chip de bridge.
- Se amplio `tests/test_frontend_scan_state.py` para cubrir modo demo, conectado, comprobando, desconectado y pendiente.

Impacto medido:
- `app.js`: 7.178 -> 7.171 lineas.
- Modulos JS frontend: sin cambios, 23.
- Tests frontend `test_frontend_*.py`: sin cambios, 22.

Validaciones ejecutadas:
- `node --check apps/flatshot-desktop/frontend/scan-state.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `venv\Scripts\python.exe -m pytest tests/test_frontend_scan_state.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 282 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- HTTP local: `index.html`, `scan-state.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 39 - Extraccion de modo del punto de estado

Estado: completada.

Cambios realizados:
- `top-status-view.js` ahora expone `statusMode()` para decidir la clase visual del punto superior:
  - estado inicial sin lote;
  - error por exportacion, preview o escaneo;
  - ocupado por exportacion, preview, escaneo, bridge o validaciones;
  - listo.
- `app.js` conserva las fuentes de verdad (`batch`, `bridgeStatus`, `exportStatus`, `previewStatus`, errores de escaneo y validaciones) y solo delega la decision.
- Se amplio `tests/test_frontend_top_status_view.py` para cubrir todas las ramas del modo visual.

Impacto medido:
- `app.js`: 7.171 -> 7.164 lineas.
- Modulos JS frontend: sin cambios, 23.
- Tests frontend `test_frontend_*.py`: sin cambios, 22.

Validaciones ejecutadas:
- `node --check apps/flatshot-desktop/frontend/top-status-view.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `venv\Scripts\python.exe -m pytest tests/test_frontend_top_status_view.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 282 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- HTTP local: `index.html`, `top-status-view.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 40 - Extraccion de label de archivo exportado actual

Estado: completada.

Cambios realizados:
- `export-result-view.js` ahora expone `currentExportFileLabel()` para decidir el archivo visible durante exportacion en curso.
- `app.js` conserva las fuentes de verdad (`exportableImages`, `processed`, `statusText`) y solo delega el calculo.
- Se amplio `tests/test_frontend_export_result_view.py` para cubrir:
  - sin imagenes con `statusText`;
  - sin imagenes y fallback `Preparando`;
  - indice negativo;
  - indice valido;
  - indice mayor al total;
  - nombre vacio con fallback.

Impacto medido:
- `app.js`: 7.164 -> 7.163 lineas.
- Modulos JS frontend: sin cambios, 23.
- Tests frontend `test_frontend_*.py`: sin cambios, 22.

Validaciones ejecutadas:
- `node --check apps/flatshot-desktop/frontend/export-result-view.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `venv\Scripts\python.exe -m pytest tests/test_frontend_export_result_view.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 282 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- HTTP local: `index.html`, `export-result-view.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 41 - Extraccion de destino abrible de exportacion

Estado: completada.

Cambios realizados:
- `export-result-view.js` ahora expone `outputDestinationToOpen()` para elegir el primer destino abrible.
- `app.js` conserva las fuentes de verdad (`state.exportDestinations`, `state.exportResult.destinations`) y solo delega la prioridad.
- Se amplio `tests/test_frontend_export_result_view.py` para cubrir:
  - prioridad de destinos en estado;
  - fallback a destinos del resultado;
  - arrays vacios;
  - entradas nulas.

Impacto medido:
- `app.js`: 7.163 -> 7.160 lineas.
- Modulos JS frontend: sin cambios, 23.
- Tests frontend `test_frontend_*.py`: sin cambios, 22.

Validaciones ejecutadas:
- `node --check apps/flatshot-desktop/frontend/export-result-view.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `venv\Scripts\python.exe -m pytest tests/test_frontend_export_result_view.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 282 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- HTTP local: `index.html`, `export-result-view.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 42 - Extraccion de conteo avanzado modificado

Estado: completada.

Cambios realizados:
- `settings-view.js` ahora expone `advancedDirtyCount()` para contar diferencias entre settings actuales y preset base usando las claves avanzadas.
- `app.js` conserva la normalizacion de settings y la lista `advancedSettingKeys`; solo delega el conteo.
- Se amplio `tests/test_frontend_settings_view.py` para cubrir:
  - preset sin cambios pendientes;
  - comparacion estricta de claves avanzadas;
  - claves ausentes en ambos lados.

Impacto medido:
- `app.js`: 7.160 -> 7.162 lineas.
- Modulos JS frontend: sin cambios, 23.
- Tests frontend `test_frontend_*.py`: sin cambios, 22.

Validaciones ejecutadas:
- `node --check apps/flatshot-desktop/frontend/settings-view.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `venv\Scripts\python.exe -m pytest tests/test_frontend_settings_view.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 282 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- HTTP local: `index.html`, `settings-view.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 43 - Extraccion de selector de modo del inspector

Estado: completada.

Cambios realizados:
- `inspector-context-view.js` ahora expone `inspectorMode()` para decidir la subvista activa del inspector.
- `app.js` conserva las fuentes de verdad (`outputEditMode`, `inspectorTab`) y solo delega el selector.
- Se amplio `tests/test_frontend_inspector_context_view.py` para cubrir:
  - edicion de salida;
  - tab de salida;
  - avanzado;
  - avisos;
  - resumen por defecto;
  - tab desconocido.

Impacto medido:
- `app.js`: 7.162 -> 7.156 lineas.
- Modulos JS frontend: sin cambios, 23.
- Tests frontend `test_frontend_*.py`: sin cambios, 22.

Validaciones ejecutadas:
- `node --check apps/flatshot-desktop/frontend/inspector-context-view.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `venv\Scripts\python.exe -m pytest tests/test_frontend_inspector_context_view.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 282 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- HTTP local: `index.html`, `inspector-context-view.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 44 - Extraccion de label de fuente de preset

Estado: completada.

Cambios realizados:
- `settings-view.js` ahora expone `presetSourceLabel()` para calcular la microcopy de fuente del ajuste.
- `app.js` conserva las fuentes de verdad (`bridgePresetWarning`, `presetDirty`) y solo delega el label.
- Se amplio `tests/test_frontend_settings_view.py` para cubrir:
  - global limpio;
  - global modificado;
  - aviso bridge sin cambios;
  - aviso bridge con cambios.

Impacto medido:
- `app.js`: sin cambios netos, 7.156 lineas.
- Modulos JS frontend: sin cambios, 23.
- Tests frontend `test_frontend_*.py`: sin cambios, 22.

Validaciones ejecutadas:
- `node --check apps/flatshot-desktop/frontend/settings-view.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `venv\Scripts\python.exe -m pytest tests/test_frontend_settings_view.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 282 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- HTTP local: `index.html`, `settings-view.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 45 - Extraccion de nombre de salida por imagen

Estado: completada.

Cambios realizados:
- `output-profile-view.js` ahora expone `outputNameForImage()` para calcular el nombre visible de salida por imagen.
- El helper conserva las reglas actuales de plantilla, `suffix`, carpeta por `folderId`, fallback a primera carpeta, fallback a `lote`, extension explicita e indice con padding.
- `app.js` conserva las fuentes de verdad (`state.naming`, `state.suffix`, `state.format`, imagen activa y carpetas activas) y solo delega el calculo.
- Se amplio `tests/test_frontend_output_profile_view.py` para cubrir:
  - plantilla vacia;
  - carpeta coincidente por `folderId`;
  - fallback a primera carpeta;
  - fallback sin carpeta ni imagen;
  - extension explicita.

Impacto medido:
- `app.js`: 6.570 -> 6.559 lineas.
- Modulos JS frontend: sin cambios, 23.
- Tests frontend `test_frontend_*.py`: sin cambios, 22.

Validaciones ejecutadas:
- `node --check apps/flatshot-desktop/frontend/output-profile-view.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `venv\Scripts\python.exe -m pytest tests/test_frontend_output_profile_view.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 282 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- `git diff --check`: OK; solo avisos Git LF/CRLF en Windows.
- HTTP local: `index.html`, `output-profile-view.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 46 - Extraccion de nombre por perfil de salida

Estado: completada.

Cambios realizados:
- `output-profile-view.js` ahora expone `outputNameForProfile()` para calcular el nombre visible desde un perfil de salida concreto.
- El helper reutiliza la resolucion de carpeta/imagen ya cubierta y conserva el fallback `imagen_original` usado por la vista de previsualizacion de perfil.
- `app.js` conserva seleccion de imagen, perfil activo y carpetas activas; solo delega el calculo.
- Se amplio `tests/test_frontend_output_profile_view.py` para cubrir:
  - perfil con carpeta coincidente por `folderId`;
  - fallback sin imagen ni carpeta;
  - sufijo definido por perfil, sin aplicar el fallback `_PRO` del estado global.

Impacto medido:
- `app.js`: sin cambios netos, 6.559 lineas.
- Modulos JS frontend: sin cambios, 23.
- Tests frontend `test_frontend_*.py`: sin cambios, 22.

Validaciones ejecutadas:
- `node --check apps/flatshot-desktop/frontend/output-profile-view.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `venv\Scripts\python.exe -m pytest tests/test_frontend_output_profile_view.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 282 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- `git diff --check`: OK; solo avisos Git LF/CRLF en Windows.
- HTTP local: `index.html`, `output-profile-view.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 47 - Extraccion de labels de destino de perfil

Estado: completada.

Cambios realizados:
- `output-profile-view.js` ahora expone `profileDestinationLabel()` y `profileDestinationPreviewLabel()`.
- Se movio microcopy de destino de perfil fuera de `app.js`:
  - perfil ausente;
  - destino personalizado vacio;
  - destino personalizado configurado;
  - subcarpeta junto al origen.
- `app.js` conserva los puntos de llamada existentes y solo delega los labels.
- Se amplio `tests/test_frontend_output_profile_view.py` para cubrir los estados de destino de perfil.

Impacto medido:
- `app.js`: 6.559 -> 6.549 lineas.
- Modulos JS frontend: sin cambios, 23.
- Tests frontend `test_frontend_*.py`: sin cambios, 22.

Validaciones ejecutadas:
- `node --check apps/flatshot-desktop/frontend/output-profile-view.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `venv\Scripts\python.exe -m pytest tests/test_frontend_output_profile_view.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 282 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- `git diff --check`: OK; solo avisos Git LF/CRLF en Windows.
- HTTP local: `index.html`, `output-profile-view.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 48 - Extraccion de linea de destino del lote

Estado: completada.

Cambios realizados:
- `batch-view.js` ahora expone `batchDestinationLine()` para formatear la linea visible de destino del lote.
- Se movio fuera de `app.js` la microcopy para:
  - destino personalizado vacio;
  - destino personalizado configurado;
  - salida junto al origen;
  - subcarpeta junto al origen;
  - multiples perfiles con uno o varios destinos.
- `app.js` conserva la resolucion de perfiles activos y solo entrega datos ya calculados al helper.
- Se amplio `tests/test_frontend_batch_view.py` para cubrir destinos globales y destinos por perfil.

Impacto medido:
- `app.js`: 6.549 -> 6.546 lineas.
- Modulos JS frontend: sin cambios, 23.
- Tests frontend `test_frontend_*.py`: sin cambios, 22.

Validaciones ejecutadas:
- `node --check apps/flatshot-desktop/frontend/batch-view.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `venv\Scripts\python.exe -m pytest tests/test_frontend_batch_view.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 282 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- `git diff --check`: OK; solo avisos Git LF/CRLF en Windows.
- HTTP local: `index.html`, `batch-view.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 49 - Extraccion de linea de salida del lote

Estado: completada.

Cambios realizados:
- `batch-view.js` ahora expone `batchOutputLine()` para formatear la linea visible de salida del lote.
- Se movio fuera de `app.js` la microcopy para:
  - salida unica con formato, tamano y fondo;
  - multiples perfiles ya resumidos;
  - fallback de tamano/fondo en ausencia de datos.
- `app.js` conserva la resolucion de perfiles activos y el calculo de tamano por perfil; solo pasa `profileLines` al helper.
- Se amplio `tests/test_frontend_batch_view.py` para cubrir salida unica, multiples perfiles y fallback.

Impacto medido:
- `app.js`: 6.546 -> 6.550 lineas; aumento neto por objeto de parametros, con menos reglas embebidas.
- Modulos JS frontend: sin cambios, 23.
- Tests frontend `test_frontend_*.py`: sin cambios, 22.

Validaciones ejecutadas:
- `node --check apps/flatshot-desktop/frontend/batch-view.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `venv\Scripts\python.exe -m pytest tests/test_frontend_batch_view.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 282 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- `git diff --check`: OK; solo avisos Git LF/CRLF en Windows.
- HTTP local: `index.html`, `batch-view.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 50 - Extraccion de resumen de salidas del lote

Estado: completada.

Cambios realizados:
- `batch-view.js` ahora expone `outputProfilesSummaryLabel()` para formatear el resumen visible de salidas.
- Se movio fuera de `app.js` la microcopy para:
  - una salida con formato, tamano y fondo;
  - multiples perfiles con `Nombre (Formato)`;
  - fallback de tamano/fondo en ausencia de datos.
- `app.js` conserva `outputSizeDisplay()`, `backgroundLabel()` y la construccion de labels de perfiles; solo delega el formato final.
- Se amplio `tests/test_frontend_batch_view.py` para cubrir salida unica, multiples perfiles y fallback.

Impacto medido:
- `app.js`: 6.550 -> 6.552 lineas; aumento neto por objeto de parametros, con menos reglas embebidas.
- Modulos JS frontend: sin cambios, 23.
- Tests frontend `test_frontend_*.py`: sin cambios, 22.

Validaciones ejecutadas:
- `node --check apps/flatshot-desktop/frontend/batch-view.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `venv\Scripts\python.exe -m pytest tests/test_frontend_batch_view.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 282 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- `git diff --check`: OK; solo avisos Git LF/CRLF en Windows.
- HTTP local: `index.html`, `batch-view.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 51 - Extraccion de label compacto de salida del visor

Estado: completada.

Cambios realizados:
- `preview-view.js` ahora expone `viewerOutputCompactLabel()` para formatear el texto visible `formato · tamano · fondo`.
- `app.js` conserva el calculo de `outputSizeDisplay()` y `backgroundLabel()`; solo delega la composicion final del label.
- Se amplio `tests/test_frontend_preview_view.py` para cubrir label configurado y fallback.

Impacto medido:
- `app.js`: 6.552 -> 6.556 lineas; aumento neto por objeto de parametros, con menos microcopy embebida.
- Modulos JS frontend: sin cambios, 23.
- Tests frontend `test_frontend_*.py`: sin cambios, 22.

Validaciones ejecutadas:
- `node --check apps/flatshot-desktop/frontend/preview-view.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `venv\Scripts\python.exe -m pytest tests/test_frontend_preview_view.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 282 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- `git diff --check`: OK; solo avisos Git LF/CRLF en Windows.
- HTTP local: `index.html`, `preview-view.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 52 - Extraccion de fila de problema del detalle de lote

Estado: completada.

Cambios realizados:
- `batch-detail-view.js` ahora expone `batchDetailProblemHtml()` para renderizar filas de incidencias e ignorados del detalle de lote.
- `app.js` conserva la seleccion de incidencias, ignorados, limites y labels de motivo; solo delega el HTML de cada fila.
- Se amplio `tests/test_frontend_batch_detail_view.py` para cubrir:
  - clase visual `warning`;
  - clase visual `clear`;
  - escaping de titulo, ruta y detalle;
  - fallback de `title` cuando no se entrega `titleAttr`.

Impacto medido:
- `app.js`: sin cambios netos, 6.556 lineas.
- Modulos JS frontend: sin cambios, 23.
- Tests frontend `test_frontend_*.py`: sin cambios, 22.

Validaciones ejecutadas:
- `node --check apps/flatshot-desktop/frontend/batch-detail-view.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `venv\Scripts\python.exe -m pytest tests/test_frontend_batch_detail_view.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 282 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- `git diff --check`: OK; solo avisos Git LF/CRLF en Windows.
- HTTP local: `index.html`, `batch-detail-view.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 53 - Extraccion de salida activa del detalle de lote

Estado: completada.

Cambios realizados:
- `batch-detail-view.js` ahora expone `batchDetailOutputHtml()` para renderizar cada salida activa del detalle de lote.
- `app.js` conserva la resolucion de perfiles activos, perfil principal, destino, resumen y ejemplo de nombre; solo delega el HTML de cada salida.
- Se amplio `tests/test_frontend_batch_detail_view.py` para cubrir:
  - salida principal con marcador `Principal`;
  - salida secundaria sin marcador;
  - indice visible;
  - escaping de nombre, destino y ejemplo.

Impacto medido:
- `app.js`: 6.556 -> 6.546 lineas.
- Modulos JS frontend: sin cambios, 23.
- Tests frontend `test_frontend_*.py`: sin cambios, 22.

Validaciones ejecutadas:
- `node --check apps/flatshot-desktop/frontend/batch-detail-view.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `venv\Scripts\python.exe -m pytest tests/test_frontend_batch_detail_view.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 282 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- `git diff --check`: OK; solo avisos Git LF/CRLF en Windows.
- HTTP local: `index.html`, `batch-detail-view.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 54 - Extraccion de seccion de ignorados del detalle de lote

Estado: completada.

Cambios realizados:
- `batch-detail-view.js` ahora expone `batchDetailIgnoredSectionHtml()` para renderizar la seccion colapsable de ignorados tecnicos.
- `app.js` conserva la lista de ignorados, el limite de filas visibles y los motivos; solo delega la seccion final.
- Se ajusto `app.js` para reutilizar una lista local `ignoredItems`, evitando recalcular `ignoredOmissions()` para filas y conteo.
- Se amplio `tests/test_frontend_batch_detail_view.py` para cubrir:
  - seccion presente con conteo plural;
  - inclusion de filas ya renderizadas;
  - seccion vacia sin HTML.

Impacto medido:
- `app.js`: 6.546 -> 6.540 lineas.
- Modulos JS frontend: sin cambios, 23.
- Tests frontend `test_frontend_*.py`: sin cambios, 22.

Validaciones ejecutadas:
- `node --check apps/flatshot-desktop/frontend/batch-detail-view.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `venv\Scripts\python.exe -m pytest tests/test_frontend_batch_detail_view.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 282 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- `git diff --check`: OK; solo avisos Git LF/CRLF en Windows.
- HTTP local: `index.html`, `batch-detail-view.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 55 - Extraccion del grid de detalle de lote

Estado: completada.

Cambios realizados:
- `batch-detail-view.js` ahora expone `batchDetailGridHtml()` para renderizar la estructura principal del detalle de lote.
- `app.js` conserva conteos, ruta de entrada, estado visible, incidencias, ignorados y salidas activas; solo delega el HTML de secciones.
- Se amplio `tests/test_frontend_batch_detail_view.py` para cubrir:
  - secciones `Resumen`, `Entrada`, `Lote`, `Salidas activas` e `Incidencias`;
  - escaping de carpeta/ruta;
  - inclusion de filas de salida, ignorados e incidencias;
  - fallback de salidas e incidencias vacias.

Impacto medido:
- `app.js`: 6.540 -> 6.519 lineas.
- Modulos JS frontend: sin cambios, 23.
- Tests frontend `test_frontend_*.py`: sin cambios, 22.

Validaciones ejecutadas:
- `node --check apps/flatshot-desktop/frontend/batch-detail-view.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `venv\Scripts\python.exe -m pytest tests/test_frontend_batch_detail_view.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 282 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- `git diff --check`: OK; solo avisos Git LF/CRLF en Windows.
- HTTP local: `index.html`, `batch-detail-view.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 19 - Extension de vista del inspector para tarjetas compactas

Estado: completada.

Cambios realizados:
- `inspector-review-view.js` ahora tambien renderiza:
  - tarjeta compacta de imagen seleccionada;
  - alerta compacta de issues;
  - tarjeta compacta de ajuste activo.
- `app.js` conserva seleccion, deduplicacion de issues, conteos y estado del preset; solo delega presentacion.
- Se amplio `tests/test_frontend_inspector_review_view.py` para cubrir seleccion vacia, imagen con ajuste local, alertas y tarjeta de ajuste.

Impacto medido:
- `app.js`: 7.659 -> 7.620 lineas.

Validaciones ejecutadas:
- `venv\Scripts\python.exe -m pytest tests/test_frontend_inspector_review_view.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 272 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- `node --check apps/flatshot-desktop/frontend/inspector-review-view.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `git diff --check`: OK; solo avisos Git LF/CRLF en Windows.
- HTTP local en `http://127.0.0.1:4199/`: `index.html`, `inspector-review-view.js`, `inspector-output-view.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 18 - Extraccion de vista de salidas del inspector

Estado: completada.

Cambios realizados:
- Se agrego `apps/flatshot-desktop/frontend/inspector-output-view.js`.
- Se movio HTML puro de la tarjeta de salidas activas fuera de `app.js`:
  - tarjeta `inspector-output-card`;
  - filas `active-output-row`;
  - aviso de cambios temporales.
- `index.html` carga el helper antes de `app.js`.
- `app.js` conserva conteos, perfil activo, toggles permitidos y summaries; solo delega presentacion.
- Se agrego `tests/test_frontend_inspector_output_view.py` para filas, toggles, acciones, aviso temporal, escaping y orden de carga.

Impacto medido:
- `app.js`: 7.674 -> 7.659 lineas.

Validaciones ejecutadas:
- `venv\Scripts\python.exe -m pytest tests/test_frontend_inspector_output_view.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 272 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- `node --check apps/flatshot-desktop/frontend/inspector-output-view.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `git diff --check`: OK; solo avisos Git LF/CRLF en Windows.
- HTTP local en `http://127.0.0.1:4198/`: `index.html`, `inspector-output-view.js`, `inspector-review-view.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 17 - Extraccion de vista de revision del inspector

Estado: completada.

Cambios realizados:
- Se agrego `apps/flatshot-desktop/frontend/inspector-review-view.js`.
- Se movio HTML puro del panel de revision fuera de `app.js`:
  - resumen compacto del lote;
  - estado vacio de seleccion;
  - tarjeta de imagen seleccionada;
  - salida prevista;
  - lista de issues de imagen;
  - acciones de navegacion/formato/ajuste local.
- `index.html` carga el helper antes de `app.js`.
- `app.js` conserva seleccion, calculo de estado, issues y datos derivados; solo delega presentacion.
- Se agrego `tests/test_frontend_inspector_review_view.py` para HTML, escaping, acciones, estado local y orden de carga.

Impacto medido:
- `app.js`: 7.713 -> 7.674 lineas.

Validaciones ejecutadas:
- `venv\Scripts\python.exe -m pytest tests/test_frontend_inspector_review_view.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 270 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- `node --check apps/flatshot-desktop/frontend/inspector-review-view.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `git diff --check`: OK; solo avisos Git LF/CRLF en Windows.
- HTTP local en `http://127.0.0.1:4197/`: `index.html`, `inspector-review-view.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 16 - Extension de helper preflight para progreso y resumen bloqueante

Estado: completada.

Cambios realizados:
- `export-preflight-view.js` ahora tambien renderiza:
  - panel compacto de progreso;
  - resumen bloqueante de avisos de salida.
- `app.js` conserva la seleccion de issue accionable y conteos; delega solo HTML.
- Se amplio `tests/test_frontend_export_preflight_view.py` con contratos para progreso determinado/indeterminado y resumen bloqueante con archivo.

Impacto medido:
- `app.js`: 7.734 -> 7.713 lineas.

Validaciones ejecutadas:
- `venv\Scripts\python.exe -m pytest tests/test_frontend_export_preflight_view.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 268 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- `node --check apps/flatshot-desktop/frontend/export-preflight-view.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `git diff --check`: OK; solo avisos Git LF/CRLF en Windows.
- HTTP local en `http://127.0.0.1:4196/`: `index.html`, `export-preflight-view.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.

## Fase 15 - Extraccion de vista preflight y avisos de exportacion

Estado: completada.

Cambios realizados:
- Se agrego `apps/flatshot-desktop/frontend/export-preflight-view.js`.
- Se movio HTML puro de avisos/preflight fuera de `app.js`:
  - lista de issues;
  - fila de issue;
  - lista de preflight;
  - label del estado del panel de exportacion;
  - resumen de bloqueos/avisos/exportables.
- `index.html` carga el helper antes de `app.js`.
- `app.js` mantiene construccion de filas, calculos de readiness y lectura de estado; solo delega presentacion.
- Se agrego `tests/test_frontend_export_preflight_view.py` para escaping, summaries, acciones, labels y orden de carga.

Impacto medido:
- `app.js`: 7.796 -> 7.734 lineas.

Validaciones ejecutadas:
- `venv\Scripts\python.exe -m pytest tests/test_frontend_export_preflight_view.py -q`: 2 passed.
- `venv\Scripts\python.exe -m pytest -q`: 268 passed.
- `Get-ChildItem apps/flatshot-desktop/frontend -Filter *.js | ForEach-Object { node --check $_.FullName }`: OK.
- `node --check apps/flatshot-desktop/frontend/export-preflight-view.js`: OK.
- `node --check apps/flatshot-desktop/frontend/app.js`: OK.
- `git diff --check`: OK; solo avisos Git LF/CRLF en Windows.
- HTTP local en `http://127.0.0.1:4195/`: `index.html`, `export-preflight-view.js`, `export-result-view.js` y `app.js` respondieron 200.

Salida exportada:
- Sin cambios esperados. No se modifico `ExportRunner`, bridge Python, motor de imagen ni escritura de archivos.
