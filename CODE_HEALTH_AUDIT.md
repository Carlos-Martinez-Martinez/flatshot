# Auditoría de higiene de código - FlatShot

## Resumen ejecutivo

FlatShot esta en un estado tecnicamente mejor que el de una aplicacion heredada tipica: el motor de imagen, los servicios de aplicacion, el bridge HTTP y la interfaz web estan separados en carpetas claras, hay pruebas de arquitectura que impiden recuperar paquetes Qt retirados, y la suite actual cubre dominios importantes como escaneo de carpetas, presets, configuracion de exportacion, runner de exportacion, cache, bridge, CLI y modelos.

La mayor deuda de mantenibilidad no esta hoy en el pipeline de imagen, sino en la interfaz web activa. `apps/flatshot-desktop/frontend/app.js` concentra estado global, datos mock, normalizacion, derivaciones, reglas de exportacion, llamadas HTTP, renderizado HTML, handlers y bootstrap en un unico archivo de 8.734 lineas. Esto hace que cambios pequenos de UI o exportacion puedan tocar muchas responsabilidades a la vez. La capa CSS tambien acumula deuda: `styles.css`, `ux-foundation.css` y `ux-refactor.css` suman unas 13.847 lineas, duplican tokens y selectores, y dependen mucho de sobrescrituras con `!important`.

El backend mantiene limites de capa razonables: `core` y `application` no importan UI ni bridge, y `bridge` actua como adaptador local. Aun asi, hay puntos sensibles que conviene tocar con mucha cautela: `src/flatshot/application/export_runner.py`, `src/flatshot/core/engine.py`, `src/flatshot/core/scaling.py` y `src/flatshot/bridge/service.py`. Estos modulos son largos o concentran reglas de salida, procesamiento, validacion o coordinacion. Cualquier refactor ahi debe proteger primero la apariencia de imagen exportada, nombres de archivo, destinos, formatos y cancelacion.

La recomendacion principal es no reescribir FlatShot ni migrarlo a otro stack. Lo correcto es una limpieza por fases: primero documentar contratos y tests de seguridad, despues extraer helpers puros del frontend, luego normalizar contratos de perfiles/salidas, despues dividir renderizado por dominios, y solo mas tarde consolidar CSS y tocar hotspots Python con pruebas de salida.

## Diagnóstico por áreas

### Estructura general del proyecto

La estructura principal es coherente:

- `src/flatshot/core/`: modelos, motor de sombra, escalado, overrides y helpers de exportacion.
- `src/flatshot/application/`: servicios reutilizables sin UI para escaneo, preview, presets, settings, export config y export runner.
- `src/flatshot/bridge/`: adaptador HTTP local, serializacion y jobs de exportacion.
- `apps/flatshot-desktop/frontend/`: UI activa en HTML/CSS/JS estatico.
- `apps/flatshot-desktop/bridge/` y `apps/flatshot-desktop/run_dev.py`: runners locales.
- `scripts/build_portable.py` y `scripts/portable/FlatShot.pyw`: portable Windows y ventana WebView/browser fallback.
- `tests/`: cobertura amplia de core, application, bridge, CLI, arquitectura y portable.

Esta organizacion soporta bien la regla de futuro: la logica no UI puede ser reutilizada por CLI, bridge, portable u otra interfaz. Los tests `test_architecture_boundaries.py` y `test_headless_imports.py` refuerzan que `core` y `application` no dependan de Qt ni de paquetes retirados.

El problema estructural principal es que la UI no tiene una estructura equivalente: el frontend esta en un unico modulo JS y tres capas CSS historicas. A nivel Python la arquitectura ya esta razonablemente preparada; a nivel frontend falta una separacion minima entre estado, derivaciones, acciones, API, renderizado y componentes visuales.

### UI frontend

`apps/flatshot-desktop/frontend/app.js` es el centro real de la deuda. Contiene unas 420 funciones, de las cuales mas de 200 estan relacionadas con renderizado. El bloque de estado global empieza alrededor de la linea 268 y mezcla conceptos de lote, seleccion, preview, zoom, filtros, inspector, presets, exportacion, bridge, escaneo, mocks y overrides.

Ejemplos de responsabilidades mezcladas en el mismo archivo:

- estado global y persistencia en `localStorage`;
- normalizacion de perfiles de salida;
- reglas de preflight y exportacion;
- construccion del payload del bridge;
- gestion de polling de jobs;
- renderizado de galeria, visor, inspector, modales y footer;
- handlers globales de `input`, `change`, `click`, `submit`, `keydown`;
- mocks/dev scenarios y estados reales de bridge.

La UI actual funciona, pero su mantenibilidad es fragil: cualquier cambio puede afectar render, estado y reglas de negocio a la vez. La prioridad no debe ser cambiar visualmente la app, sino extraer funciones puras y presentadores para reducir el tamano de las zonas que hay que entender antes de modificar.

### Estado y flujo de datos

El estado vive en un objeto global `state`. Hay muchas asignaciones directas a `state.*` repartidas por el archivo, aproximadamente 639 ocurrencias de mutacion directa. No todas son malas por si mismas, pero el volumen dificulta responder preguntas como:

- que campos son fuente de verdad y cuales son derivables;
- que campos representan UI temporal frente a configuracion persistente;
- que campos son del bridge y cuales son del lote;
- cuando un cambio de salida debe resetear preview, readiness o export status;
- que estados exactos son validos para `batch`, `previewStatus`, `exportStatus`, `bridgeStatus` o `scanStatus`.

Hay funciones derivadas utiles (`uiState`, `preflightIssues`, `exportOutputProfiles`, `currentOutputProfileData`, etc.), pero conviven con mutaciones directas y renderizado. El siguiente paso sano es agrupar el estado por dominios y extraer helpers puros sin cambiar su comportamiento.

### Tipos, modelos y contratos de datos

En Python hay modelos Pydantic y dataclasses razonables: `ShadowSettings`, `ExportConfig`, `ExportVariant`, `CurveData`, contratos de escaneo, preview y export job. La compatibilidad de presets antiguos esta cuidada con `normalize_shadow_settings` y `SHADOW_ENGINE_COMPAT`.

El punto debil esta en el contrato frontend/bridge para exportacion. El frontend maneja perfiles con campos como `destinationMode: "source" | "custom"`, `background: "rgb230" | "white" | "transparent"` y `size: "1800x2400"`. El bridge traduce parte de esto a `output_destination: "subfolder" | "custom"`, `transparent_bg`, `bg_color`, `output_width`, `output_height` y `variants`. Esa traduccion esta repartida entre `app.js`, `bridge/service.py`, `ExportConfigService` y `ExportRunner`.

Tambien hay modelos que conviene auditar antes de tocar. `JobItem` en `src/flatshot/core/models.py` aparece principalmente en tests de modelos, no en flujos principales inspeccionados. No deberia borrarse sin una busqueda completa y una decision explicita, pero si deberia marcarse como posible concepto heredado o de bajo uso.

### Logica de negocio

La logica de negocio Python esta mejor separada que la UI. `FolderScanner`, `PreviewService`, `ExportConfigService`, `PresetService`, `SettingsService`, `ExportRunner` y `BridgeExportJob` son unidades reconocibles y testeables.

Los hotspots principales son:

- `src/flatshot/application/export_runner.py`: 679 lineas. Incluye planificacion de rutas, colisiones, cache, snapshots, multiprocessing, pausa/cancelacion y escritura final.
- `src/flatshot/bridge/service.py`: 591 lineas. Valida payloads, traduce contratos frontend, coordina servicios, presets, previews y export jobs.
- `src/flatshot/core/engine.py`: contiene `_aplicar_efectos_with_diagnostics`, funcion larga y muy sensible porque define apariencia final.
- `src/flatshot/core/scaling.py`: contiene logica compleja de perfil optico, presencia y escala.

La recomendacion no es dividir estos modulos por estilo, sino extraer solo cuando haya pruebas de equivalencia. Especialmente `engine.py`, `scaling.py` y `export_runner.py` deben tocarse despues de crear pruebas golden o de paridad que bloqueen cambios visuales y de salida.

### Estilos y sistema visual

La documentacion `docs/FLATSHOT_DESIGN_SYSTEM.md` define una intencion clara de tokens y primitivas `ui-*`, pero la implementacion real conserva capas acumuladas:

- `styles.css`: 9.029 lineas, 1.256 selectores aproximados, muchos tokens y reglas base.
- `ux-foundation.css`: 3.495 lineas, capa de consolidacion adicional.
- `ux-refactor.css`: 1.323 lineas, capa final de ajustes.

Hay duplicacion de variables como `--text-muted`, `--surface-muted`, `--radius-sm`, `--space-*`, `--color-*`, `--column-gallery` y `--column-inspector` entre capas. Tambien hay un uso elevado de `!important`, lo que indica que el orden de cascada ya se esta usando como mecanismo de control. Eso funciona para estabilizar una UI tras refactors rapidos, pero complica cambios futuros y aumenta riesgo de regresiones visuales.

La consolidacion CSS debe hacerse al final de una fase, no al principio. Primero conviene aislar componentes y estados; despues se puede reducir la cascada con menos riesgo.

### Tests y validacion

La suite es una fortaleza del proyecto. Existen 24 archivos de test y la ejecucion con el venv local paso con `237 passed`. Hay tests para:

- boundaries de arquitectura;
- imports headless sin Qt;
- bridge service y HTTP server;
- export runner, variantes y cache;
- configuracion de exportacion;
- presets y settings;
- folder scanner;
- preview service;
- CLI y paridad basica;
- portable y run dev.

La brecha principal es que no hay validacion frontend automatizada equivalente a la cobertura Python. El frontend se valida con `node --check` y revisiones Playwright/manuales, pero no hay tests unitarios para helpers JS ni snapshots DOM de los flujos criticos. Como no hay Node build/test stack instalado, conviene empezar extrayendo helpers puros que puedan validarse con pruebas ligeras o con checks controlados, sin introducir dependencias salvo que se justifique.

## Problemas detectados

### 1. Frontend monolitico con responsabilidades mezcladas

- Descripcion: `app.js` concentra estado, mocks, derivaciones, API bridge, export payloads, renderizado HTML, modales, handlers y bootstrap.
- Archivos/carpetas afectados: `apps/flatshot-desktop/frontend/app.js`.
- Gravedad: alta.
- Riesgo de tocarlo: medio-alto; un cambio local puede romper flujos de lote, seleccion, preview, exportacion o modales.
- Impacto en mantenibilidad: alto; aumenta el coste de entender y modificar cualquier feature UI.
- Recomendacion concreta: extraer primero helpers puros sin dependencias DOM: `output profile`, `preflight`, `batch view model`, `preview state`, `formatters`. Mantener el runtime actual y llamar a esos helpers desde `app.js`.

### 2. Estado global demasiado amplio y mutado desde muchas funciones

- Descripcion: el objeto `state` mezcla dominios y se modifica directamente en muchas zonas. No hay transiciones centralizadas para lote, preview, exportacion o bridge.
- Archivos/carpetas afectados: `apps/flatshot-desktop/frontend/app.js`.
- Gravedad: alta.
- Riesgo de tocarlo: medio; centralizar todo de golpe seria peligroso.
- Impacto en mantenibilidad: alto; dificulta saber que cambios deben resetear progreso, polling, seleccion, preview o readiness.
- Recomendacion concreta: definir helpers de transicion pequenos por dominio, por ejemplo `setBatchScanning`, `applyScanResultState`, `resetExportState`, `applyOutputProfileState`. No introducir un framework de estado.

### 3. Reglas de salida duplicadas entre frontend y backend

- Descripcion: normalizacion y validacion de formato, fondo, destino, tamano, naming y variantes existen en `app.js`, `bridge/service.py`, `export_config_service.py` y `export_runner.py`.
- Archivos/carpetas afectados: `apps/flatshot-desktop/frontend/app.js`, `src/flatshot/bridge/service.py`, `src/flatshot/application/export_config_service.py`, `src/flatshot/application/export_runner.py`, `src/flatshot/core/models.py`.
- Gravedad: alta.
- Riesgo de tocarlo: alto; afecta nombres, destinos, colisiones y comportamiento de salida.
- Impacto en mantenibilidad: alto; una regla puede cambiar en un lado y no en otro.
- Recomendacion concreta: documentar el contrato frontend -> bridge y extraer una capa JS de mapping/validation que refleje el contrato Python. No cambiar nombres ni payloads hasta tener tests de prepare/export.

### 4. CSS acumulado en tres capas con tokens duplicados

- Descripcion: `styles.css`, `ux-foundation.css` y `ux-refactor.css` suman unas 13.847 lineas, con variables repetidas, selectores repetidos y muchos `!important`.
- Archivos/carpetas afectados: `apps/flatshot-desktop/frontend/styles.css`, `apps/flatshot-desktop/frontend/ux-foundation.css`, `apps/flatshot-desktop/frontend/ux-refactor.css`, `docs/FLATSHOT_DESIGN_SYSTEM.md`.
- Gravedad: alta.
- Riesgo de tocarlo: medio-alto; la cascada actual probablemente estabiliza detalles visuales recientes.
- Impacto en mantenibilidad: alto; dificulta saber que regla domina y aumenta regresiones responsive.
- Recomendacion concreta: no borrar capas aun. Primero inventariar tokens vivos y componentes `ui-*`; despues consolidar por bloques visuales con screenshots antes/despues.

### 5. Renderizado HTML generado como strings extensos

- Descripcion: muchas funciones construyen HTML con template strings largos para galeria, preview, inspector, exportacion, modales y resultados.
- Archivos/carpetas afectados: `apps/flatshot-desktop/frontend/app.js`.
- Gravedad: media.
- Riesgo de tocarlo: medio.
- Impacto en mantenibilidad: medio-alto; los cambios de microcopy, accesibilidad o layout obligan a editar bloques grandes.
- Recomendacion concreta: extraer renderizadores por dominio a modulos o secciones: `batch`, `preview`, `inspector`, `output`, `modals`. Mantener funciones puras que reciben view models y devuelven HTML.

### 6. Contrato de estados no formalizado en frontend

- Descripcion: estados como `idle`, `ready`, `preparing`, `processing`, `paused`, `stopping`, `completed`, `error` estan definidos como regla de producto, pero el frontend usa combinaciones propias: `batch`, `previewStatus`, `exportStatus`, `bridgeStatus`, `scanStatus`, `paused`.
- Archivos/carpetas afectados: `apps/flatshot-desktop/frontend/app.js`, `src/flatshot/bridge/export_jobs.py`.
- Gravedad: media.
- Riesgo de tocarlo: medio.
- Impacto en mantenibilidad: medio-alto; aumenta riesgo de botones inconsistentes o progreso que no se resetee.
- Recomendacion concreta: crear un mapa documentado de estados frontend y bridge, sin cambiar comportamiento. Despues extraer selectores tipo `isExporting`, `canPause`, `canResume`, `primaryActionForState`.

### 7. Hotspot de exportacion con muchas responsabilidades

- Descripcion: `ExportRunner.run` combina snapshot de fuentes, calculo de variantes, cache, validacion de colisiones, creacion de destinos, procesamiento paralelo, progreso y limpieza.
- Archivos/carpetas afectados: `src/flatshot/application/export_runner.py`.
- Gravedad: alta.
- Riesgo de tocarlo: alto; toca salida final, cache, DPI, JPG/PNG, cancelacion y destinos.
- Impacto en mantenibilidad: medio-alto; nuevas variantes o politicas de salida costaran mas.
- Recomendacion concreta: antes de refactorizar, crear pruebas golden de planificacion y salida. Luego extraer planificacion/cache/procesamiento en pasos pequenos, preservando bytes o metadatos esperados donde sea viable.

### 8. Motor de imagen y escalado con funciones largas pero sensibles

- Descripcion: `_aplicar_efectos_with_diagnostics`, `_measure_presence_profile`, `calculate_subject_scale` y `render_realistic_v2` son funciones largas. Parte de su complejidad es propia del dominio.
- Archivos/carpetas afectados: `src/flatshot/core/engine.py`, `src/flatshot/core/scaling.py`, `src/flatshot/core/shadow/realistic_v2.py`.
- Gravedad: media.
- Riesgo de tocarlo: alto; puede cambiar apariencia exportada.
- Impacto en mantenibilidad: medio; dificil de entender, pero con tests existentes.
- Recomendacion concreta: no refactorizar durante trabajos UI. Si se toca, hacerlo solo con tests de salida visual/paridad y con comentarios de intencion, no con cambios de formula.

### 9. Servicio bridge grande como fachada y traductor

- Descripcion: `FlatShotBridgeService` agrupa health, presets, carpeta, preview, thumbnail, prepare/export, job control y validacion de payloads.
- Archivos/carpetas afectados: `src/flatshot/bridge/service.py`.
- Gravedad: media.
- Riesgo de tocarlo: medio-alto; es frontera entre UI y servicios.
- Impacto en mantenibilidad: medio-alto; nuevos endpoints pueden aumentar el acoplamiento.
- Recomendacion concreta: extraer parsers/normalizadores de payload de preview/export a helpers testeables dentro de `bridge` o `application`, manteniendo los endpoints iguales.

### 10. Modelos posiblemente heredados o de bajo uso

- Descripcion: `JobItem` aparece en `core/models.py` y tests, pero no se observo uso en flujos principales actuales. Puede ser resto de cola antigua o contrato reservado.
- Archivos/carpetas afectados: `src/flatshot/core/models.py`, `tests/test_models.py`.
- Gravedad: baja.
- Riesgo de tocarlo: bajo-medio; borrarlo sin revisar podria romper API o tests.
- Impacto en mantenibilidad: bajo; ruido conceptual.
- Recomendacion concreta: marcar para investigacion. Si no hay uso real, documentar deprecacion o mover a un modulo de contratos legacy antes de eliminar.

### 11. Validacion frontend sin tests unitarios propios

- Descripcion: el frontend se valida con `node --check` y revisiones visuales/manuales, pero helpers como `outputProfileValidation`, `preflightIssues`, `exportOutputProfiles` no tienen tests unitarios aislados.
- Archivos/carpetas afectados: `apps/flatshot-desktop/frontend/app.js`, `tests/`.
- Gravedad: media.
- Riesgo de tocarlo: bajo si se agregan tests sin cambiar runtime.
- Impacto en mantenibilidad: alto para futuros cambios UI/export.
- Recomendacion concreta: tras extraer helpers puros, crear pruebas sin navegador o con una herramienta minima ya disponible. Evitar anadir dependencias hasta justificarlo.

### 12. Documentacion tecnica buena pero repartida

- Descripcion: existen `README.md`, `AGENTS.md`, `docs/ARCHITECTURE_GUARDS.md`, `docs/FLATSHOT_DESIGN_SYSTEM.md` y `UX_UI_REFACTOR_PROGRESS.md`, pero no hay un mapa unico de deuda y prioridades.
- Archivos/carpetas afectados: `docs/`, `README.md`, `AGENTS.md`, `UX_UI_REFACTOR_PROGRESS.md`.
- Gravedad: baja.
- Riesgo de tocarlo: bajo.
- Impacto en mantenibilidad: medio; nuevos cambios pueden repetir decisiones ya tomadas.
- Recomendacion concreta: usar este informe como backlog tecnico. Cuando se implemente una fase, actualizar `UX_UI_REFACTOR_PROGRESS.md` o una nota interna con resultados y validaciones.

## Refactors recomendados

### Bajo riesgo

- Crear helpers puros de formato y conteo en frontend: pluralizacion, labels de lote, labels de salida, resumen de preflight.
- Extraer normalizacion de perfiles de salida desde `app.js` a un modulo JS local sin build step.
- Separar funciones de payload bridge/export sin cambiar el JSON enviado.
- Documentar estados frontend/bridge/export en `docs/ARCHITECTURE_GUARDS.md` o en un documento nuevo.
- Revisar simbolos de bajo uso como `JobItem` y decidir si se conservan, documentan o deprecian.

### Riesgo medio

- Dividir renderizado frontend por dominios: lote/galeria, visor, inspector, exportacion, modales.
- Reemplazar mutaciones directas repetidas por transiciones de estado pequenas.
- Extraer parsers de payload en `bridge/service.py` para preview/export.
- Consolidar validacion de salida manteniendo mensajes y comportamiento.
- Agregar tests de helpers frontend o checks DOM para flujos criticos.

### Alto impacto

- Consolidar CSS en una capa base real de tokens y componentes comunes.
- Reducir el uso de `!important` por bloques visuales, con screenshots antes/despues.
- Extraer planificacion de exportacion desde `ExportRunner.run` a helpers mas pequenos.
- Unificar conceptos de output profile frontend y `ExportVariant` backend en una documentacion de contrato.

### Preparar antes de tocar

- Motor de imagen y escalado: crear pruebas de salida/paridad antes de mover codigo.
- Export runner: crear pruebas de DPI, JPG quality/subsampling, PNG, transparencia, nombres, destinos, colisiones, cancelacion y cache.
- Portable: validar live reload, autosync y fallback browser antes de cambiar launchers.
- CSS global: capturar estados visuales clave con Playwright o revision manual antes de consolidar.

## Plan de implementación por fases

### Fase 0: seguridad, backups, tests y validacion

- Confirmar git limpio o aislar cambios en una rama.
- Ejecutar `venv\Scripts\python.exe -m pytest -q`.
- Ejecutar `node --check apps/flatshot-desktop/frontend/app.js`.
- Registrar flujos manuales necesarios antes de cada cambio UI.
- Definir explicitamente que no se cambia apariencia exportada ni comportamiento de archivos.

### Fase 1: limpieza sin cambio funcional

- Extraer helpers frontend puros de labels, conteos, filtros y presentacion.
- Mantener llamadas desde `app.js` y no cambiar HTML generado salvo equivalencia.
- Investigar simbolos de bajo uso como `JobItem` sin eliminarlos todavia.
- Actualizar documentacion de contratos si se confirma una deuda o decision.

### Fase 2: extraccion de componentes/utilidades

- Extraer modulo de perfiles de salida: normalizacion, deduplicacion, tamano, comparacion y validacion.
- Extraer modulo de preflight/export readiness.
- Extraer modulo de mapping frontend -> bridge payload.
- Agregar tests alrededor de esas funciones antes de tocar UI visible.

### Fase 3: separacion de logica y UI

- Dividir renderizado por dominios manteniendo la app estatica sin build.
- Hacer que renderizadores reciban view models en vez de leer todo el estado global.
- Introducir transiciones de estado pequenas para scan/export/preview.
- Mantener los handlers actuales hasta que cada dominio este cubierto.

### Fase 4: normalizacion de estado/modelos

- Definir fuente de verdad para lote, seleccion, salida activa, perfiles habilitados y estado de exportacion.
- Eliminar estado derivable solo cuando haya tests y equivalencia visual.
- Alinear nombres frontend con contratos backend sin romper payloads existentes.
- Documentar estados validos y transiciones permitidas.

### Fase 5: sistema de estilos/componentes comunes

- Inventariar tokens vivos y duplicados entre `styles.css`, `ux-foundation.css` y `ux-refactor.css`.
- Consolidar por componentes, no por busqueda global.
- Reducir `!important` solo cuando se pueda verificar el mismo estado visual.
- Actualizar `docs/FLATSHOT_DESIGN_SYSTEM.md` con la capa final real.

### Fase 6: tests y documentacion

- Ampliar tests de contratos de salida, preflight y estado.
- Agregar checks frontend ligeros si no requieren dependencias grandes.
- Documentar comandos reales de validacion en README o docs.
- Registrar en `UX_UI_REFACTOR_PROGRESS.md` que fases quedaron completadas y que no se toco output.

## Criterios de aceptación

- `app.js` queda dividido o reducido por dominios sin cambiar flujo visible.
- Las reglas de perfiles de salida tienen tests y un contrato claro frontend/bridge.
- La validacion de exportacion produce los mismos bloqueos, avisos y payloads que antes.
- La salida exportada conserva apariencia, dimensiones, formato, DPI, nombres, sufijos, destinos, transparencia y comportamiento de colisiones.
- La suite `pytest` pasa en el venv local.
- `node --check apps/flatshot-desktop/frontend/app.js` pasa mientras exista ese archivo.
- Los flujos UI afectados se revisan manualmente: importar carpeta, carpeta vacia, lote con PNGs, seleccion, preview, ajustes, export config, procesar, pausa/reanudar/detener si se toca exportacion.
- La CSS consolidada no introduce overflow, solapamientos, perdida de foco visible ni cambios de layout no buscados.
- No se introducen dependencias nuevas sin justificacion escrita.

## Comandos de validación

Comandos encontrados y resultado en esta auditoria:

```powershell
venv\Scripts\python.exe -m pytest -q
```

Resultado: `237 passed`.

```powershell
node --check apps/flatshot-desktop/frontend/app.js
```

Resultado: correcto, sin errores de sintaxis.

```powershell
python -m pytest -q
```

Resultado con el Python del sistema: fallo porque `pytest` no esta instalado en ese entorno (`No module named pytest`). No es un fallo de la suite del proyecto si se usa el venv local.

Comandos utiles documentados por el proyecto:

```powershell
python apps\flatshot-desktop\run_dev.py --open
```

Arranca bridge y frontend local.

```powershell
python apps\flatshot-desktop\bridge\run_bridge.py --host 127.0.0.1 --port 8765
```

Arranca solo el bridge.

```powershell
python scripts\build_portable.py
```

Construye o actualiza el portable Windows.

```powershell
flatshot list-presets
flatshot process --input RUTA\DE\ENTRADA --preset "Luz cenital" --dry-run
```

Valida CLI y plan de procesamiento sin crear salidas en el modo dry run.

## Riesgos y límites

- No conviene reescribir la app desde cero. La arquitectura Python ya tiene valor y tests.
- No conviene migrar a Electron, Tauri, React u otro stack solo por modernizacion. Primero hay que reducir deuda dentro de la app actual.
- No conviene tocar `core/engine.py`, `core/scaling.py` o `core/shadow/*` durante refactors UI.
- No conviene modificar `ExportRunner` junto con cambios visuales; mezcla dos riesgos distintos.
- No conviene borrar modelos de bajo uso sin confirmar API, tests y compatibilidad.
- No conviene consolidar CSS globalmente sin capturas o revision visual de estados clave.
- No conviene anadir dependencias para resolver problemas que pueden cubrirse con helpers locales.
- No conviene cambiar config/presets sin migracion y tolerancia a archivos malformados.
- No conviene confiar en el Python del sistema para validacion; el venv local es el entorno que actualmente tiene `pytest`.

## Recomendación final

El orden exacto recomendado es:

1. Proteger el estado actual con `pytest`, `node --check` y una lista corta de checks manuales para el flujo que se vaya a tocar.
2. Extraer helpers puros del frontend que no cambien DOM ni payloads.
3. Extraer y probar perfiles de salida: normalizacion, validacion, perfiles activos, mapping a variantes.
4. Extraer preflight/readiness y transiciones de exportacion/lote.
5. Dividir renderizado por dominios manteniendo la UI estatica actual.
6. Consolidar CSS solo despues de que los dominios UI esten aislados.
7. Tocar `ExportRunner` o motor de imagen solo con pruebas golden/paridad y una tarea dedicada.

La prioridad tecnica es clara: mantener intacta la salida de imagen, reducir primero la complejidad del frontend, y despues normalizar contratos de exportacion. La modernizacion visual o de stack deberia quedar fuera hasta que esas bases esten estabilizadas.

Alcance de esta auditoría:

- Archivos cambiados: solo `CODE_HEALTH_AUDIT.md`.
- Cambios funcionales: ninguno.
- Comportamiento preservado: motor de imagen, preview, exportacion, presets, settings, bridge, CLI y frontend.
- Checks manuales UI: no aplican en esta fase porque solo se creo documentacion.
- Salida exportada: sin cambios esperados; no se modifico codigo de procesamiento ni comportamiento de archivos.
