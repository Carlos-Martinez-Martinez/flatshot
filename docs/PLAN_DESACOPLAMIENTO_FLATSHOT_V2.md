# PLAN DESACOPLAMIENTO FLATSHOT V2

Fecha de auditoría base: 2026-05-22.

Este plan sustituye como guía operativa a `PLAN_DESACOPLAMIENTO_FLATSHOT_CODEX.md`. El plan original queda como contexto histórico.

## 1. Estado de partida confirmado

Hechos confirmados:

- `application` y `core` no importan PyQt.
- Ya existen servicios Qt-free para presenters, escaneo, export config, export runner, queue runner, preview, presets, settings, sesión y estado de aplicación.
- `ExportWorker` y `QueueWorker` siguen heredando de `QThread`, pero delegan en `ExportRunner` y `QueueRunner`.
- `PreviewService` devuelve datos neutros RGB; la conversión a `QImage/QPixmap` sigue en UI.
- `MainWindow` consume servicios, pero conserva mucha coordinación y mide 4037 líneas.
- No existen `src/flatshot/adapters/` ni `src/flatshot/api/`.
- `ConfigManager` y `LogManager` siguen usando `QStandardPaths`.
- `cli.py` no usa `ExportRunner`; mantiene una ruta de exportación directa.
- `PreRenderScheduler` es un subsistema Qt no contemplado en el plan original.
- Suite actual: `pytest` pasa con 196 tests.

Inferencia:

- FlatShot está bastante desacoplado en servicios, pero todavía no tiene una frontera limpia de aplicación/adaptadores para lanzar operaciones desde PyQt, CLI o una futura API.

## 2. Qué queda vigente del plan original

- Estabilidad antes que rediseño.
- No romper exportación.
- No tocar `ShadowEngine` sin bug confirmado.
- No cambiar apariencia/exported image output sin petición explícita.
- Mantener PyQt mientras se desacopla.
- No crear API antes de tener servicios limpios.
- No mover lógica de negocio a widgets.
- No añadir dependencias sin razón fuerte.
- Mantener output, naming, destino, DPI, calidad JPG/PNG, transparencia, cache y overrides.
- Ejecutar tests tras cada tanda.
- Preferir tandas pequeñas y reversibles.

## 3. Qué queda obsoleto o debe corregirse

- No continuar por “FASE 9” de forma genérica; hay que redefinirla en tandas V2 concretas.
- No asumir que `adapters/qt` existe: hoy los adapters de facto están en `workers/`.
- No tratar `ExportRunner`, `QueueRunner` o `PreviewService` como pendientes de creación.
- No ignorar `PreRenderScheduler`: es Qt y afecta cache/export readiness.
- No tratar CLI como plenamente desacoplada: usa `ShadowEngine` directo y `ConfigManager`/`LogManager`.
- No crear API local todavía.
- No borrar wrappers de compatibilidad (`ConfigManager`, `ExportWorker`, `QueueWorker`) sin pruebas de paridad.
- No mover archivos sólo por arquitectura si el cambio no reduce un riesgo real.

## 4. Riesgos actuales prioritarios

1. Riesgo de rotura funcional: unificar CLI/export runner o tocar snapshots/cache puede cambiar archivos exportados.
2. Riesgo de datos/configuración: `ConfigManager`, `PresetService`, `SettingsService` y sesión conviven; una limpieza mal hecha puede perder presets o settings.
3. Riesgo de duplicidad arquitectónica: CLI, grid, scanner, queue y export launch siguen listando PNG por rutas distintas.
4. Riesgo de acoplamiento Qt residual: `MainWindow`, workers, pre-render scheduler, config path y logging siguen atados a Qt.
5. Riesgo de tests insuficientes: hay buenos tests de servicios, pero faltan guardas globales, paridad CLI/runner y smoke UI permanente.
6. Riesgo de documentación obsoleta: README y plan original no reflejan el estado real.
7. Riesgo de seguir añadiendo UI sobre base inestable: `MainWindow` aún concentra demasiada coordinación.

# TANDA V2.1 - Guardas de arquitectura y paridad antes de seguir

## Objetivo

Asegurar que el estado desacoplado actual queda protegido por tests antes de reducir `MainWindow` o tocar CLI/export.

## Estado previo que debe comprobarse

- `pytest` pasa.
- `application` y `core` no importan PyQt.
- `MainWindow` sigue instanciando servicios principales.
- No se han creado `api/` ni nuevas dependencias.

## Cambios permitidos

- Añadir tests de arquitectura/imports.
- Añadir tests de paridad de helpers entre imports legacy y ubicación real.
- Añadir tests pequeños de CLI dry-run/listado si no mutan config real.
- Añadir documentación mínima de decisiones si el test revela deuda.

## Cambios prohibidos

- Cambiar lógica de producción.
- Migrar CLI a `ExportRunner`.
- Mover workers.
- Cambiar outputs.
- Rediseñar UI.

## Archivos probables

- `tests/test_architecture_boundaries.py`
- `tests/test_cli.py`
- `tests/test_export_runner.py`
- `docs/decoupling_notes.md` o documento de seguimiento V2 si se decide continuar notas.

## Pasos

1. Añadir test que inspeccione `src/flatshot/application` y `src/flatshot/core` para bloquear imports PyQt.
2. Añadir test que documente que helpers importados desde `workers.export_worker` son los mismos de `application.export_runner`.
3. Añadir test que confirme que no existe `src/flatshot/api` o que la API está explícitamente fuera de alcance.
4. Revisar si `cli.py --dry-run` puede testearse sin tocar config real; si no, dejarlo como pendiente documentado.
5. Ejecutar tests focales y suite completa.

## Tests obligatorios

```bash
pytest tests/test_architecture_boundaries.py
pytest
python -m compileall src
```

## Validación manual

- No requerida si sólo se añaden tests y documentación.

## Criterios de aceptación

- La suite sigue en verde.
- Los límites `application/core` sin PyQt quedan protegidos por test.
- La deuda CLI/runner queda documentada como deuda real, no suposición.

## Riesgos

- Tests demasiado rígidos pueden bloquear imports legítimos de PIL/pydantic.
- No convertir guardas en snapshots frágiles de estructura.

## Resultado esperado

- Base de seguridad para empezar tandas V2 funcionales sin degradar el desacoplamiento logrado.

# TANDA V2.2 - Preparación neutra de export run

## Objetivo

Reducir `MainWindow._start_export()` extrayendo la preparación de exportación a un servicio Qt-free sin cambiar cómo se exporta.

## Estado previo que debe comprobarse

- TANDA V2.1 completada.
- `ExportConfigService` y `FolderScanner` siguen pasando tests.
- `ExportRunner` y `QueueRunner` siguen pasando tests.

## Cambios permitidos

- Crear un servicio pequeño tipo `ExportRunPlanner` o `ExportPreparationService`.
- El servicio puede recibir carpetas, `ExportConfig`, variantes activas y overrides.
- El servicio puede devolver un plan serializable con:
  - carpetas;
  - input files por carpeta;
  - destinos;
  - labels de variantes;
  - source count;
  - file total.
- Adaptar `MainWindow._start_export()` para consumir ese plan.

## Cambios prohibidos

- Cambiar `ExportRunner.process_single_image`.
- Cambiar naming, destinos, cache, calidad o formato.
- Cambiar `ExportWorker`/`QueueWorker`.
- Cambiar UI visual.
- Cambiar comportamiento de PNG lower-case sin test explícito.

## Archivos probables

- `src/flatshot/application/export_run_planner.py`
- `src/flatshot/application/contracts.py`
- `src/flatshot/ui/main_window.py`
- `tests/test_export_run_planner.py`

## Pasos

1. Inspeccionar `_start_export()` y aislar sólo la preparación previa a workers.
2. Crear contrato de plan con dataclass.
3. Mover snapshot/listado y cálculo de destinos/labels/source count al servicio.
4. Mantener en UI los `QMessageBox`, señales, botones y arranque de workers.
5. Añadir tests con `tmp_path` para una carpeta, varias carpetas, carpeta vacía, variantes activas y custom destination.

## Tests obligatorios

```bash
pytest tests/test_export_run_planner.py tests/test_export_config_service.py tests/test_export_runner.py tests/test_queue_runner.py
pytest
python -m compileall src
```

## Validación manual

- Smoke PyQt offscreen o manual:
  - añadir carpeta con PNG;
  - procesar una carpeta;
  - procesar dos carpetas;
  - verificar output existe y progress reset.

## Criterios de aceptación

- `MainWindow._start_export()` queda más corto y sólo coordina UI/workers.
- El plan producido por el servicio coincide con el snapshot anterior.
- Exported image output no cambia.

## Riesgos

- Cambiar el momento del snapshot puede cambiar qué archivos entran si la carpeta cambia durante exportación.
- La ruta custom con variantes puede duplicarse mal si no se conserva la lógica actual.

## Resultado esperado

- Exportar queda más cerca de poder lanzarse desde CLI/API sin `MainWindow`.

# TANDA V2.3 - CLI y export runner: pruebas de paridad antes de migrar

## Objetivo

Preparar la futura migración de CLI a `ExportRunner` sin cambiar todavía el comportamiento externo.

## Estado previo que debe comprobarse

- TANDA V2.2 completada.
- Hay tests de output básico de `ExportRunner`.
- `tests/test_cli.py` sigue pasando.

## Cambios permitidos

- Añadir tests que comparen nombres, extensión, dimensiones, modo de color y DPI entre la ruta CLI actual y el runner cuando sea posible.
- Extraer helpers compartidos de construcción de `ExportConfig` CLI si no altera ejecución.
- Documentar diferencias encontradas.

## Cambios prohibidos

- Sustituir todavía el loop de CLI por `ExportRunner`.
- Cambiar defaults CLI.
- Cambiar mensajes CLI salvo que el test lo exija y se apruebe.

## Archivos probables

- `tests/test_cli.py`
- `tests/test_export_runner.py`
- `docs/REVISION_PLAN_DESACOPLAMIENTO_FLATSHOT.md`

## Pasos

1. Identificar salida actual de CLI en dry-run y en procesamiento con imagen mínima.
2. Crear fixture temporal sin usar config real.
3. Comparar campos funcionales, no bytes completos si las rutas no son idénticas.
4. Documentar brechas.

## Tests obligatorios

```bash
pytest tests/test_cli.py tests/test_export_runner.py
pytest
```

## Validación manual

- No obligatoria si se limita a tests.

## Criterios de aceptación

- Hay evidencia de qué debe preservarse antes de migrar CLI.
- No cambia la producción.

## Riesgos

- Tests de imagen pueden ser lentos o frágiles si comparan bytes completos.

## Resultado esperado

- Migración CLI futura con menor riesgo de cambiar output.

# TANDA V2.4 - Resolver rutas de configuración/logging sin Qt en servicios/CLI

## Objetivo

Reducir la dependencia Qt indirecta de CLI y persistencia separando resolución de rutas de las operaciones de presets/settings/logs.

## Estado previo que debe comprobarse

- Tests de presets/settings/session/logging actuales pasan.
- No hay API local.

## Cambios permitidos

- Crear un resolver Qt-free configurable para CLI/tests si preserva ruta por defecto.
- Mantener `ConfigManager` como wrapper Qt para UI.
- Añadir un servicio/log repository Qt-free si se toca logging.
- Adaptar CLI sólo si hay tests de compatibilidad.

## Cambios prohibidos

- Cambiar ubicación real de presets/settings/logs para usuarios existentes sin migración.
- Borrar `ConfigManager`.
- Cambiar formato de presets.
- Cambiar sesión.

## Archivos probables

- `src/flatshot/application/settings_service.py`
- `src/flatshot/application/preset_service.py`
- `src/flatshot/utils/config.py`
- `src/flatshot/utils/log_manager.py`
- `src/flatshot/cli.py`
- `tests/test_config_manager.py`
- `tests/test_cli.py`

## Pasos

1. Diseñar sin implementar migración de rutas.
2. Añadir tests que fijen comportamiento actual.
3. Introducir resolver sólo si no cambia path UI.
4. Mantener compatibilidad con `QStandardPaths` para GUI.

## Tests obligatorios

```bash
pytest tests/test_config_manager.py tests/test_preset_service.py tests/test_settings_service.py tests/test_cli.py
pytest
```

## Validación manual

- Abrir app con config existente y confirmar presets visibles.
- Ejecutar `flatshot list-presets` en entorno controlado.

## Criterios de aceptación

- CLI puede operar con servicios sin requerir widgets.
- UI conserva rutas actuales.

## Riesgos

- Alto riesgo de mover archivos de usuario o crear config paralela.

## Resultado esperado

- Persistencia más reusable para CLI/API sin romper usuarios actuales.

# TANDA V2.5 - Pre-render como subsistema reconciliado

## Objetivo

Separar la planificación pura de pre-render/cache del scheduler Qt, manteniendo el proceso aislado actual.

## Estado previo que debe comprobarse

- `tests/test_pre_render_process.py` y `tests/test_pre_render_scheduler.py` pasan.
- No se toca export output.

## Cambios permitidos

- Extraer helpers puros de ordenación de candidatos, firma de contexto y construcción de jobs.
- Mantener `PreRenderScheduler(QObject)` como adapter Qt.
- Añadir tests a los helpers.

## Cambios prohibidos

- Cambiar política de cache.
- Cambiar prioridad del proceso.
- Cambiar formato de cache.
- Cambiar cuándo se lanza desde UI sin validación manual.

## Archivos probables

- `src/flatshot/application/pre_render_planner.py`
- `src/flatshot/workers/pre_render_scheduler.py`
- `tests/test_pre_render_planner.py`
- `tests/test_pre_render_scheduler.py`

## Pasos

1. Identificar en `PreRenderScheduler` qué cálculo no necesita Qt.
2. Extraer funciones puras sin cambiar nombres de estado emitidos.
3. Mantener timers, procesos y señales en scheduler.
4. Añadir tests.

## Tests obligatorios

```bash
pytest tests/test_pre_render_process.py tests/test_pre_render_scheduler.py tests/test_pre_render_planner.py
pytest
```

## Validación manual

- Con background pre-render activado, confirmar status de cache y que exportación sigue funcionando.

## Criterios de aceptación

- Scheduler Qt queda más fino.
- La planificación de cache puede probarse sin Qt.

## Riesgos

- Cambiar orden de candidatos puede afectar rendimiento percibido.

## Resultado esperado

- Pre-render deja de ser una excepción arquitectónica grande.

# TANDA V2.6 - Reducir MainWindow por boundaries UI, no por rediseño

## Objetivo

Dividir responsabilidades internas de `MainWindow` sin cambiar look & feel ni comportamiento.

## Estado previo que debe comprobarse

- TANDAS V2.1-V2.5 completadas o justificadamente pospuestas.
- Hay smoke manual/offscreen disponible.

## Cambios permitidos

- Extraer módulos UI-only pequeños para wiring de export bar, result dialogs o preview adapter.
- Mantener clases Qt en `ui/`.
- Mantener nombres públicos de callbacks si ayuda a reducir riesgo.

## Cambios prohibidos

- Rediseñar layout.
- Cambiar copy visible salvo bug.
- Mover lógica funcional de vuelta a UI.
- Crear framework interno de estado.

## Archivos probables

- `src/flatshot/ui/main_window.py`
- `src/flatshot/ui/export_view_adapter.py`
- `src/flatshot/ui/preview_adapter.py`
- `tests/test_app_state.py`

## Pasos

1. Escoger un único bloque: export result dialogs, preview adapter o export bar.
2. Extraer sólo código UI/coordinación.
3. Ejecutar tests.
4. Hacer smoke manual del bloque afectado.

## Tests obligatorios

```bash
pytest tests/test_app_state.py tests/test_presenters.py
pytest
python -m compileall src
```

## Validación manual

- App lanza.
- Preview actualiza.
- Export bar no salta.
- Result dialog aparece tras exportación.

## Criterios de aceptación

- `MainWindow` reduce tamaño o complejidad sin mover negocio a widgets.
- No cambia output.

## Riesgos

- Romper señales/callbacks por extracción mecánica.

## Resultado esperado

- `MainWindow` deja de ser el único punto de coordinación UI.

# TANDA V2.7 - Valorar API local experimental

## Objetivo

Decidir, no implementar de golpe, si ya existe una frontera limpia para API local.

## Estado previo que debe comprobarse

- CLI y export runner están reconciliados o la deuda está aceptada.
- Config/logging no fuerzan Qt para rutas no UI.
- Pre-render está documentado o extraído.
- Hay smoke UI reciente.

## Cambios permitidos

- Crear un documento de diseño API local.
- Añadir un healthcheck mínimo sólo si no introduce dependencias o si la dependencia está aprobada.

## Cambios prohibidos

- Añadir FastAPI sin justificación.
- Abrir puertos por defecto.
- Exponer rutas arbitrarias.
- Crear frontend web.

## Archivos probables

- `docs/API_LOCAL_EXPERIMENTAL.md`
- `src/flatshot/api/` sólo si se aprueba explícitamente.

## Pasos

1. Re-evaluar checklist de preparación web.
2. Definir operaciones mínimas.
3. Definir estrategia de seguridad local.
4. Pedir decisión antes de implementar servidor.

## Tests obligatorios

- Ninguno si sólo es documento.
- Si se implementa healthcheck, añadir test específico.

## Validación manual

- No aplica si sólo diseño.

## Criterios de aceptación

- Hay decisión técnica clara y riesgos conocidos.

## Riesgos

- Crear API demasiado pronto puede fijar contratos malos.

## Resultado esperado

- API local sólo empieza cuando aporta valor y no deuda.

## 6. Orden recomendado

1. TANDA V2.1 - Guardas de arquitectura y paridad antes de seguir.
2. TANDA V2.2 - Preparación neutra de export run.
3. TANDA V2.3 - CLI y export runner: pruebas de paridad antes de migrar.
4. TANDA V2.4 - Resolver rutas de configuración/logging sin Qt en servicios/CLI.
5. TANDA V2.5 - Pre-render como subsistema reconciliado.
6. TANDA V2.6 - Reducir MainWindow por boundaries UI, no por rediseño.
7. Actualizar README y documentación de arquitectura.
8. TANDA V2.7 - Valorar API local experimental.

Este orden prioriza cerrar duplicidades, asegurar tests, preservar PyQt, reducir `MainWindow`, completar adapters/runners y dejar API para el final.

## 7. Qué NO hacer todavía

- No rediseñar la UI visual.
- No migrar a React, Electron, Tauri o web.
- No crear API local mientras CLI/config/logging/pre-render sigan parcialmente acoplados.
- No eliminar PyQt.
- No tocar `ShadowEngine` salvo bug confirmado.
- No introducir base de datos.
- No cambiar formato de presets sin migración.
- No cambiar rutas de usuario sin migración y tests.
- No eliminar `ConfigManager`, `ExportWorker` ni `QueueWorker` de golpe.
- No mover helpers de compatibilidad sin revisar imports de CLI/tests/UI.
- No hacer refactors masivos sin tests.
- No cambiar output JPG/PNG, DPI, nombres, carpetas, cache ni overrides.

## 8. Prompt recomendado para la siguiente tanda

```md
Vamos a continuar el desacoplamiento de FlatShot usando `docs/PLAN_DESACOPLAMIENTO_FLATSHOT_V2.md`, no el plan antiguo.

Objetivo de esta tanda: TANDA V2.1 - Guardas de arquitectura y paridad antes de seguir.

Condiciones:
- No cambiar lógica de producción.
- No rediseñar UI.
- No mover workers.
- No migrar CLI.
- No crear API.
- No cambiar dependencias.
- No tocar `ShadowEngine`.
- No cambiar output de imágenes.

Primero revisa:
- `docs/ESTADO_ACTUAL_FLATSHOT.md`
- `docs/REVISION_PLAN_DESACOPLAMIENTO_FLATSHOT.md`
- `docs/PLAN_DESACOPLAMIENTO_FLATSHOT_V2.md`
- `src/flatshot/application/`
- `src/flatshot/core/`
- `src/flatshot/workers/export_worker.py`
- `src/flatshot/cli.py`
- `tests/`

Implementa sólo tests/guardas:
1. Añade un test que falle si `src/flatshot/application` o `src/flatshot/core` importan PyQt o tipos Qt.
2. Añade un test que documente que los helpers legacy importados desde `flatshot.workers.export_worker` apuntan a la implementación real de `flatshot.application.export_runner`.
3. Añade, si es seguro, una comprobación de que no existe API local activa todavía.
4. No cambies código de producción salvo que un test revele una inconsistencia trivial y lo justifiques antes.

Ejecuta:
- `pytest tests/test_architecture_boundaries.py` si creas ese archivo.
- `pytest`
- `python -m compileall src`

Entrega:
- Archivos modificados.
- Tests añadidos.
- Resultado de comandos.
- Qué riesgo queda antes de TANDA V2.2.
- Confirmación explícita de que exported image output no cambió.
```
