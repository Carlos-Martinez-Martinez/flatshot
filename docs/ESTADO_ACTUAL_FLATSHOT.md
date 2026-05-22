# ESTADO ACTUAL FLATSHOT

Fecha de auditoría: 2026-05-22.

## Alcance y método

Hechos confirmados:

- Se leyó el plan base `PLAN_DESACOPLAMIENTO_FLATSHOT_CODEX.md`.
- Se leyó `README.md`, `AGENTS.md` y `docs/decoupling_notes.md`.
- Se inventarió la estructura con `rg --files`.
- Se inspeccionaron `src/flatshot/ui/main_window.py`, `src/flatshot/ui/`, `src/flatshot/core/`, `src/flatshot/application/`, `src/flatshot/workers/`, `src/flatshot/utils/` y `tests/`.
- No existen actualmente `src/flatshot/adapters/` ni `src/flatshot/api/`.
- Se ejecutó `pytest`: 196 tests pasaron.
- Se ejecutó `python -m compileall src`: finalizó correctamente.
- No se ejecutaron `ruff`, `mypy` ni `pyright` porque no hay configuración de esas herramientas en `pyproject.toml`.

Inferencias:

- El desacoplamiento se implementó de forma incremental hasta cerrar buena parte de las fases 1-8 del plan original.
- El mayor trabajo pendiente ya no es crear servicios desde cero, sino cerrar duplicidades, endurecer contratos y reducir la coordinación que queda dentro de `MainWindow`.

Pendiente de verificar manualmente:

- Arranque visual interactivo de la app en esta auditoría.
- Flujo manual completo de añadir carpetas, preview, exportación simple, exportación múltiple, pausa/reanudación/detención.
- Paridad visual/exportada con muestras reales de producción.

## Estructura real

Hechos confirmados:

```text
src/flatshot/
  application/
    app_state.py
    contracts.py
    events.py
    execution_control.py
    export_config_service.py
    export_runner.py
    folder_scanner.py
    presenters.py
    preset_service.py
    preview_service.py
    queue_runner.py
    session_service.py
    settings_service.py
  core/
    engine.py
    models.py
    overrides.py
    scaling.py
    shadow/
  ui/
    main_window.py
    dialogs.py
    grid_preview.py
    queue_widget.py
    shell.py
    styles.py
    widgets.py
  utils/
    config.py
    history_manager.py
    log_manager.py
    render_cache.py
    session_manager.py
  workers/
    export_worker.py
    queue_worker.py
    pre_render_process.py
    pre_render_scheduler.py
```

Tamaños aproximados confirmados:

- `src/flatshot/ui/main_window.py`: 4037 líneas.
- `src/flatshot/ui/dialogs.py`: 1204 líneas.
- `src/flatshot/ui/grid_preview.py`: 655 líneas.
- `src/flatshot/ui/widgets.py`: 1109 líneas.
- `src/flatshot/application/export_runner.py`: 559 líneas.
- `src/flatshot/application/queue_runner.py`: 222 líneas.
- `src/flatshot/application/app_state.py`: 420 líneas.
- `src/flatshot/workers/export_worker.py`: 136 líneas.
- `src/flatshot/workers/queue_worker.py`: 162 líneas.
- `src/flatshot/workers/pre_render_scheduler.py`: 380 líneas.

## Mapa actual de arquitectura

```text
ui/main_window.py
  ├── usa presenters: sí
  ├── usa FolderScanner: sí
  ├── usa ExportConfigService: sí
  ├── usa PreviewService: sí, a través de PreviewWorker/QRunnable local
  ├── usa PresetService: sí
  ├── usa SettingsService: sí
  ├── usa SessionService: parcial; construye payload, pero restaura sesión en UI
  ├── usa FlatshotAppState/ProcessingState/PreviewState/ExportState: sí
  ├── lanza ExportWorker directamente: sí
  ├── lanza QueueWorker directamente: sí
  ├── contiene lógica de preview: parcial; scheduling, QImage/QPixmap y canvas siguen en UI
  ├── contiene lógica de presets: parcial; operación en servicio, diálogos y decisión UI en MainWindow
  ├── contiene lógica de sesión/configuración: parcial; IO normalizado en servicios, aplicación/restauración en UI
  └── contiene lógica de exportación: parcial; runner puro existe, pero MainWindow prepara snapshots, estado, workers y señales
```

```text
core
  ├── depende de pydantic/PIL/numpy y módulos core.shadow
  └── no importa PyQt6

application
  ├── depende de core
  ├── export_runner depende de utils.render_cache
  ├── preview_service/contracts dependen de PIL
  ├── queue_runner depende de export_runner y contratos/eventos
  └── no importa PyQt6

workers
  ├── export_worker importa PyQt6.QtCore.QThread/pyqtSignal
  ├── export_worker delega en application.export_runner.ExportRunner
  ├── queue_worker importa PyQt6.QtCore.QThread/pyqtSignal
  ├── queue_worker delega en application.queue_runner.QueueRunner
  ├── pre_render_scheduler importa QObject/QTimer/pyqtSignal
  └── pre_render_process es proceso puro sin Qt

utils
  ├── config.py importa QStandardPaths y delega presets a PresetService
  ├── log_manager.py importa QStandardPaths
  ├── session_manager.py delega a SessionService y no importa Qt
  └── render_cache.py no importa Qt

ui
  ├── depende de PyQt6
  ├── consume application/core/workers/utils
  └── sigue siendo la capa de coordinación visual y de workers

adapters
  └── no existe como paquete separado

api
  └── no existe
```

Riesgo marcado:

- No hay imports PyQt en `application` ni `core`, confirmado con `rg`.
- Sí hay dependencia Qt indirecta en CLI/persistencia por `ConfigManager` y `LogManager`, ambos bajo `utils`.
- Los adaptadores Qt existen de facto en `workers/`, pero no en un paquete `adapters/qt`.

## Independencia de Qt

| Elemento | Resultado | Evidencia |
|---|---|---|
| `application.presenters` | Sin dependencia Qt | No hay imports PyQt; usado por `MainWindow` para textos. |
| `application.folder_scanner.FolderScanner` | Sin dependencia Qt | Usa `Path`, contratos y overrides. |
| `application.export_config_service.ExportConfigService` | Sin dependencia Qt | Construye/valida `ExportConfig`. |
| `application.export_runner.ExportRunner` | Sin dependencia Qt | Usa `ProcessPoolExecutor`, `PIL`, `ShadowEngine`, `RenderCache`; no Qt. |
| `application.queue_runner.QueueRunner` | Sin dependencia Qt | Usa eventos/tokens y `ExportRunner`; no Qt. |
| `application.preview_service.PreviewService` | Sin dependencia Qt | Devuelve `PreviewResult` RGB neutro; depende de PIL/Core. |
| `application.preset_service.PresetService` | Sin dependencia Qt | IO JSON y modelos core. |
| `application.settings_service.SettingsService` | Sin dependencia Qt | IO JSON y defaults. |
| `application.session_service.SessionService` | Sin dependencia Qt | IO JSON y payload. |
| `application.app_state` | Sin dependencia Qt | Dataclasses y helpers de estado. |
| `workers.export_worker.ExportWorker` | Dependencia Qt directa | Hereda `QThread`, emite `pyqtSignal`; delega en `ExportRunner`. |
| `workers.queue_worker.QueueWorker` | Dependencia Qt directa | Hereda `QThread`, emite señales; delega en `QueueRunner`. |
| `workers.pre_render_scheduler.PreRenderScheduler` | Dependencia Qt directa | Hereda `QObject`, usa `QTimer` y señales. |
| `workers.pre_render_process` | Sin dependencia Qt | Multiprocessing entry point para cache. |
| `utils.config.ConfigManager` | Dependencia Qt directa | Usa `QStandardPaths`. |
| `utils.log_manager.LogManager` | Dependencia Qt directa | Usa `QStandardPaths`. |
| `cli.py` | Dependencia Qt indirecta | Importa `ConfigManager` y `LogManager`; exporta con `ShadowEngine` propio. |

## MainWindow

Hechos confirmados:

- `MainWindow` mide 4037 líneas.
- Instancia `FolderScanner`, `ExportConfigService`, `PresetService`, `SettingsService`, `SessionManager`, `PreRenderScheduler`, `QThreadPool`, `QFileSystemWatcher`, `ExportWorker` y `QueueWorker`.
- La función `_start_export()` sigue preparando la exportación: valida config, actualiza carpetas, crea snapshot de PNG, construye `ExportState`, decide entre `ExportWorker` y `QueueWorker`, conecta señales y arranca threads.
- La preview central sigue coordinada por `PreviewWorker(QRunnable)` definido dentro de `main_window.py`; el cálculo llama a `PreviewService`, pero la conversión `QImage`/`QPixmap` y el canvas siguen en UI.
- La restauración de sesión sigue en `_restore_session()` porque aplica geometría Qt, widgets, carpetas y controles.
- La gestión visual de presets, diálogos, feedback y QFileDialog/QMessageBox sigue en UI.

Responsabilidades que conserva:

- Construcción de toda la interfaz principal.
- Estado de carpetas seleccionadas.
- Watcher de carpetas.
- Coordinación de grid/canvas/preview.
- Coordinación de exportación simple y múltiple.
- Wiring de workers Qt.
- Diálogos de presets, exportación, detalles, logs y resultados.
- Estado local de overrides por imagen.
- Persistencia diferida de settings.
- Restauración/aplicación de sesión.
- Estado visual de barra inferior.

Lógica ya movida a servicios:

- Textos/estado visual: `application.presenters`, `application.app_state`.
- Escaneo de carpeta: `FolderScanner`.
- Construcción/validación/destinos de export config: `ExportConfigService`.
- Render preview/tile: `PreviewService`.
- Presets: `PresetService`.
- Settings: `SettingsService`.
- Payload de sesión: `SessionService.build_session_data()`.
- Exportación real: `ExportRunner`.
- Cola real: `QueueRunner`.

Inferencia:

- `MainWindow` sigue actuando como God Object de coordinación aunque mucha lógica funcional ya no vive allí. El riesgo actual está en el tamaño, los callbacks y la mezcla de aplicación de estado Qt con preparación de operaciones.

## Workers

### ExportWorker

Hechos confirmados:

- `ExportWorker` hereda de `QThread` y emite `progress_updated`, `log_updated`, `image_completed`, `finished_process`.
- Construye un `ExportJobRequest` y delega en `ExportRunner`.
- Usa `CancellationToken` y `PauseToken`.
- Reexporta helpers desde `application.export_runner` para compatibilidad: `apply_naming_template`, `process_single_image`, `get_enabled_export_variants`, `variant_export_format`, etc.

Resultado:

- Es un adaptador Qt bastante fino.
- Conserva compatibilidad pública, pero sigue siendo importado por UI, CLI y tests para helpers.

### QueueWorker

Hechos confirmados:

- `QueueWorker` hereda de `QThread` y emite señales de cola.
- Construye `QueueRunRequest` y delega en `QueueRunner`.
- `current_worker` referencia el `ExportRunner` activo, no un `ExportWorker`.
- Usa `LogManager`, que depende de `QStandardPaths`.

Resultado:

- Es un adaptador Qt funcional.
- Queda deuda por dependencia indirecta en logging y por estar en paquete `workers` en vez de `adapters/qt`.

### PreRenderScheduler

Hechos confirmados:

- `PreRenderScheduler` hereda de `QObject`.
- Usa `QTimer`, señales Qt y `multiprocessing`.
- Contiene planificación de candidatos, jobs y estado de cache.
- `pre_render_process.py` contiene el trabajo puro de render/cache.

Resultado:

- Es el worker más acoplado a Qt que queda.
- No estaba cubierto de forma explícita en las fases 0-10 originales.

## Preview

Hechos confirmados:

- `PreviewService.render_preview()` y `render_tile_preview()` son Qt-free y devuelven `PreviewResult`/`TilePreviewResult` con bytes RGB.
- `main_window.PreviewWorker` convierte bytes RGB a `QImage`.
- `GridPreviewWidget` usa `PreviewService` para render de tiles, pero conserva `QRunnable`, `QThreadPool`, `QImage`, `QPixmap`, carga de imágenes de carpeta y lógica de chunking.
- `ComparisonCanvas` en `ui/widgets.py` sigue pintando `QPixmap`.

Inferencia:

- El render funcional está desacoplado. La lifecycle/UI de preview sigue fuertemente Qt, lo cual es esperable para la UI actual.

## Exportación

Hechos confirmados:

- `ExportRunner` no requiere `MainWindow` ni `QThread`.
- `ExportRunner` hace snapshot estable, planificación de outputs, validación de colisiones, cache, `ProcessPoolExecutor`, pausa/cancelación y eventos neutros.
- `ExportWorker` es wrapper Qt.
- `MainWindow` todavía decide y lanza `ExportWorker` o `QueueWorker`.
- `cli.py` no usa `ExportRunner`: usa directamente `ShadowEngine._aplicar_efectos_with_diagnostics()` y `apply_naming_template` importado desde `workers.export_worker`.

Inferencia:

- La UI PyQt y el motor runner comparten exportación para GUI, pero CLI sigue teniendo una segunda ruta funcional de exportación.

## Presets, configuración y sesión

Hechos confirmados:

- `PresetService`, `SettingsService` y `SessionService` existen y no importan Qt.
- `ConfigManager` sigue existiendo como wrapper de compatibilidad y usa `QStandardPaths`.
- `LogManager` usa `QStandardPaths`.
- `MainWindow` usa `PresetService` directamente para cargar, guardar, crear, renombrar, borrar, importar y exportar presets.
- `MainWindow` usa `SettingsService` para leer/escribir `settings.json`.
- `SessionManager` delega IO a `SessionService`; `MainWindow` usa `SessionService.build_session_data()` al cerrar.
- La restauración de sesión sigue en `MainWindow`.

Problemas detectados:

- Hay dos capas de acceso a presets: `PresetService` y `ConfigManager` wrapper.
- CLI aún entra por `ConfigManager`, por tanto depende indirectamente de Qt para rutas de config.
- `LogManager` todavía no tiene servicio/adaptador Qt-free.
- `MainWindow._get_default_presets()` conserva defaults propios como fallback, duplicando parcialmente `PresetService.get_default_categorized_presets()`.

## Tests existentes

Hechos confirmados:

- Suite total: 196 tests.
- Tests de presenters: `tests/test_presenters.py`.
- Tests de folder scanner: `tests/test_folder_scanner.py`.
- Tests de export config service: `tests/test_export_config_service.py`.
- Tests de export runner: `tests/test_export_runner.py`.
- Tests de queue runner: `tests/test_queue_runner.py`.
- Tests de preview service: `tests/test_preview_service.py`.
- Tests de preset service: `tests/test_preset_service.py`.
- Tests de settings service: `tests/test_settings_service.py`.
- Tests de session service: `tests/test_session_service.py`.
- Tests de app state: `tests/test_app_state.py`.
- Tests de naming: `tests/test_cli.py` y export runner/variants.
- Tests de destination planning: `tests/test_export_config_service.py`.
- Tests de state transitions: `tests/test_app_state.py` y `tests/test_queue_runner.py`.
- Tests de pre-render: `tests/test_pre_render_process.py`, `tests/test_pre_render_scheduler.py`.

Tests faltantes o insuficientes:

- No hay test de integración que demuestre que la CLI usa el mismo motor que GUI; de hecho no lo usa.
- No hay guard global dedicado que falle si `application` o `core` empiezan a importar PyQt, aunque varios tests por módulo revisan ese punto.
- No hay test de paridad de resultado entre `cli.py` y `ExportRunner`.
- No hay test de `MainWindow` como integración estable en la suite normal; las notas históricas mencionan smokes offscreen, pero no son tests permanentes.
- No hay test de API local porque no existe API.
- La carrera de pausa al inicio de cola documentada en `docs/decoupling_notes.md` no parece tener test específico.

## Checklist original

| Checklist | Estado | Evidencia | Siguiente acción |
|---|---|---|---|
| Exportar no requiere MainWindow. | Cumplido para GUI runner; parcial global. | `ExportRunner.run(ExportJobRequest)` existe y no usa UI. CLI no usa runner. | Añadir plan/servicio común para CLI y futuras interfaces. |
| Exportar no requiere QThread directamente. | Cumplido en core de exportación; parcial en UI. | `ExportRunner` puro; `ExportWorker` es QThread adaptador. | Mantener worker como adapter o mover a `adapters/qt` más adelante. |
| Cola no requiere QueueWorker directamente. | Cumplido en core; parcial en UI. | `QueueRunner` puro; `MainWindow` lanza `QueueWorker`. | Crear capa de lanzamiento más explícita para UI. |
| Preview no requiere QImage/QPixmap. | Cumplido para render; parcial para UI lifecycle. | `PreviewService` devuelve bytes RGB; UI convierte. | Extraer adaptador Qt/helper de conversión si se quiere limpiar. |
| Escanear carpeta no requiere widgets. | Cumplido. | `FolderScanner.scan_folders()`. | Reducir duplicación de glob en grid/export/queue si aporta claridad. |
| Presets pueden gestionarse desde servicio. | Cumplido con deuda. | `PresetService` existe y `MainWindow` lo usa. | Resolver convivencia con `ConfigManager` para CLI/rutas. |
| Configuración puede gestionarse desde servicio. | Cumplido con deuda. | `SettingsService` existe y `MainWindow` lo usa. | Separar resolver de ruta Qt de servicios/config CLI. |
| Estado de progreso se emite como eventos neutros. | Parcialmente cumplido. | `ExportRunner` y `QueueRunner` emiten eventos; workers convierten a señales. `PreRenderScheduler` emite señales Qt. | Unificar pre-render o documentar como adapter Qt. |
| La CLI sigue funcionando. | Cumplido por tests, no por motor común. | `tests/test_cli.py` pasa. | Añadir paridad CLI/runner antes de migrar CLI. |
| La UI PyQt sigue funcionando. | No verificable manualmente en esta auditoría; tests pasan. | No se ejecutó smoke UI interactivo actual. | Ejecutar smoke offscreen/manual antes de cambios de fase 9. |
| Hay tests de servicios. | Cumplido. | Tests específicos para servicios principales. | Añadir guardas globales y paridad CLI/runner. |
| Hay una forma clara de lanzar operaciones desde una API local. | Parcial. | Runners/servicios existen; no hay API ni servicio de orquestación único. | No crear API aún; primero limpiar launch/config/logging. |

## Validación ejecutada

```text
pytest
Resultado: 196 passed in 3.13s

python -m compileall src
Resultado: correcto

rg -n "PyQt6|QThread|pyqtSignal|QRunnable|QThreadPool|QImage|QPixmap|QFileDialog|QMessageBox|QStandardPaths|QWidget|QApplication" src/flatshot/application src/flatshot/core
Resultado: sin coincidencias
```

Manual checks:

- No se ejecutaron checks manuales de UI en esta auditoría porque el encargo era análisis/planificación sin cambios funcionales.

Exported image output changed:

- No. Esta auditoría sólo crea documentación Markdown.
