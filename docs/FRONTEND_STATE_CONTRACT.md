# Contrato de estados frontend

Este documento describe los estados actuales de la UI web/bridge de FlatShot. No propone una maquina nueva: fija los valores que ya usa `apps/flatshot-desktop/frontend/app.js` y los helpers extraidos para evitar combinaciones incoherentes en futuros refactors.

## Estado de lote: `state.batch`

Valores actuales:

- `none`: no hay lote cargado.
- `scanning`: el bridge esta leyendo una o mas carpetas.
- `empty`: hubo escaneo, pero no hay imagenes compatibles/exportables.
- `ready`: hay imagenes en el lote.

Transiciones principales:

- `none -> scanning`: `scanState.scanStartState`.
- `scanning -> ready`: `scanState.scanReadyState`.
- `scanning -> empty`: `scanState.scanEmptyState`.
- `scanning -> none`: `scanState.scanFailureState`.
- mock/dev: `setScenario` puede fijar `none`, `empty`, `ready` o `scanning`.

Reglas:

- `ready` debe tener `selectedImageId` si hay imagenes reales.
- `empty` debe bloquear exportacion.
- `scanning` debe limpiar seleccion, preview, progreso y resultados de exportacion anteriores.

## Estado de preview: `state.previewStatus`

Valores actuales:

- `empty`: sin imagen o preview limpia.
- `loading`: generando preview.
- `ready`: preview disponible.
- `warning`: preview disponible con aviso/fallback.
- `error`: preview no disponible.

Helpers de transicion:

- `previewState.previewLoadingState`.
- `previewState.previewEmptyState`.
- `previewState.previewImageStatusState`.
- `previewState.previewBridgeResultState`.
- `previewState.previewErrorState`.

Reglas:

- `loading` normalmente limpia `previewData` y `previewError`; el refresco mock conserva datos previos con `clearData: false`.
- `warning` no bloquea por si sola, pero debe mostrarse como aviso.
- `error` bloquea controles de preview y puede bloquear exportacion si no hay alternativa valida.

## Estado de exportacion: `state.exportStatus`

Valores actuales:

- `blocked`: no se puede exportar por estado/configuracion.
- `ready`: listo para exportar.
- `running`: exportacion activa, pausada o deteniendose en bridge.
- `completed`: exportacion terminada correctamente.
- `partial`: exportacion terminada con avisos.
- `failed`: exportacion fallida, cancelada o detenida.

Helpers de transicion:

- `exportState.exportStartState`.
- `exportState.bridgeStatusPatch`.
- `exportState.bridgeStatusErrors`.
- `exportState.bridgeRunFailureState`.
- `exportState.bridgeProgressUnavailableState`.
- `exportState.stoppedExportState`.

Reglas:

- Al iniciar, limpiar progreso, job id, destinos, mensajes, issues y resultado anterior.
- Al completar, resetear barra de progreso a `0`.
- `paused` es un flag adicional; el bridge puede informar `paused`, pero la UI conserva `exportStatus: "running"`.
- `cancelled` del bridge se representa como `failed` con texto `Exportacion cancelada`.

## Estado bridge: `state.bridgeStatus`

Valores actuales:

- `idle`: bridge pendiente o no comprobado.
- `checking`: health check, selector o accion local en curso.
- `connected`: bridge local disponible.
- `disconnected`: bridge no disponible o fallo de conexion.

Reglas:

- Las acciones de carpeta deben usar `scanState.folderPick*`.
- El escaneo sin ruta conserva `connected` solo si el bridge ya estaba conectado.
- Los errores de conexion deben poblar `bridgeMessage`, `bridgeLastResponse`, `scanStatus` y `statusText`.

## Estado textual de escaneo: `state.scanStatus`

`scanStatus` no es un enum estricto; es texto visible. Debe ser corto y estable porque aparece en cabecera, empty states y debug.

Textos comunes:

- `Sin lote`
- `Elige una carpeta`
- `Escaneando ruta`
- `Escaneando N rutas`
- `Carpeta seleccionada`
- `Seleccion cancelada`
- `Conexion local no disponible`
- `No se encontraron PNG validos`

## Invariantes

- No mezclar cambios de estado UI con cambios de motor de imagen/exportacion.
- No introducir nuevos valores de estado sin actualizar este documento y tests frontend.
- No leer DOM dentro de helpers de estado.
- No mover reglas de salida/exportacion a renderizadores.
- Mantener los helpers de estado testeables con Node sin navegador.

## Tests relacionados

- `tests/test_frontend_scan_state.py`
- `tests/test_frontend_preview_state.py`
- `tests/test_frontend_export_state.py`
- `tests/test_frontend_preflight.py`
