# Architecture Guards

Guía operativa corta para las guardas introducidas en TANDA V2.1 y ampliadas en TANDAS V2.3-V2.6.

## Límites protegidos

- `src/flatshot/core/` no debe importar PyQt, `flatshot.ui`, `flatshot.workers`, `flatshot.utils.config` ni `flatshot.utils.log_manager`.
- `src/flatshot/application/` no debe importar PyQt, `flatshot.ui`, `flatshot.workers`, `flatshot.utils.config` ni `flatshot.utils.log_manager`.
- Los servicios/runners principales de `core` y `application` deben poder importarse sin inicializar `QApplication` y sin cargar módulos PyQt.

Estas reglas están protegidas por:

- `tests/test_architecture_boundaries.py`
- `tests/test_headless_imports.py`
- `tests/test_cli_export_runner_parity.py`
- `tests/test_config_paths.py`
- `tests/test_log_service.py`
- `tests/test_pre_render_planner.py`

## Adaptadores Qt legítimos

Estos módulos pueden seguir importando PyQt porque pertenecen a la capa UI/adaptador actual:

- `src/flatshot/ui/*`
- `src/flatshot/ui/export_result_dialog.py` como adaptador UI para el diálogo de resultado de exportación
- `src/flatshot/workers/export_worker.py`
- `src/flatshot/workers/queue_worker.py`
- `src/flatshot/workers/pre_render_scheduler.py`
- `src/flatshot/__main__.py` en modo GUI

`ExportWorker` y `QueueWorker` son adaptadores Qt de facto: conservan señales y `QThread`, pero delegan en `ExportRunner` y `QueueRunner`.

`ConfigManager` y `LogManager` siguen siendo wrappers de compatibilidad Qt para la UI actual. Las operaciones reutilizables viven en servicios Qt-free:

- `src/flatshot/application/config_paths.py`
- `src/flatshot/application/log_service.py`
- `src/flatshot/application/preset_service.py`
- `src/flatshot/application/pre_render_planner.py`
- `src/flatshot/application/settings_service.py`

## Compatibilidad temporal / deuda aceptada

- `ConfigManager` depende de `QStandardPaths` y convive con `PresetService` como wrapper de UI/compatibilidad.
- `LogManager` depende de `QStandardPaths` sólo para resolver la ruta UI; delega operaciones de log en `ActivityLogService`.
- `PreRenderScheduler` sigue siendo Qt (`QObject`, `QTimer`, señales), pero delega la planificación de candidatos/jobs en `pre_render_planner`.
- La CLI usa servicios Qt-free para presets/settings/logging, pero mantiene una ruta de exportación paralela a `ExportRunner`; hay paridad básica protegida para metadatos JPG, pero la CLI aún no está migrada.
- `MainWindow` sigue coordinando demasiado estado y el lanzamiento de workers. TANDA V2.6 sólo extrajo el diálogo de resultado de exportación a un adaptador UI, sin cambiar exportación ni workers.
- `PresetService` convive con mecanismos legacy de `ConfigManager`.
- `SettingsService` no sustituye todavía toda la resolución real de configuración porque la ruta sigue pasando por Qt en UI/CLI.
- No existe API local activa y no debe crearse antes de reconciliar estas deudas.

## Qué no eliminar aún

- No eliminar `ConfigManager`, `LogManager`, `ExportWorker`, `QueueWorker` ni `PreRenderScheduler`.
- No mover helpers legacy importados desde `flatshot.workers.export_worker` sin revisar UI, CLI y tests.
- No migrar CLI a `ExportRunner` sin preservar las pruebas de paridad de output y ampliar cobertura si se tocan presets, configuración global o variantes.
- No cambiar rutas de configuración, formato de presets ni ubicación de logs sin migración y tests.

## Cobertura de paridad mínima

- `tests/test_presenters.py` cubre resumen de lote, exportación, destino, botón de procesado y estado de progreso.
- `tests/test_folder_scanner.py` cubre `FolderScanner`.
- `tests/test_export_config_service.py` cubre `ExportConfigService`.
- `tests/test_export_runner.py` cubre `ExportRunner`.
- `tests/test_cli_export_runner_parity.py` compara ruta CLI actual y `ExportRunner` para nombre, extensión, dimensiones, modo de color y DPI en una exportación JPG mínima; también protege que `--dry-run` no cree salida.
- `tests/test_config_paths.py` cubre el resolver Qt-free de rutas de configuración y el override `FLATSHOT_CONFIG_DIR`.
- `tests/test_log_service.py` cubre logging Qt-free y limpieza de logs antiguos.
- `tests/test_headless_imports.py` confirma que `flatshot.cli` puede importarse sin cargar PyQt.
- `tests/test_pre_render_planner.py` cubre firma de contexto, orden de candidatos y construcción de jobs/cache sin Qt.
- `tests/test_export_result_dialog.py` cubre los adaptadores UI que construyen el resumen de resultado de exportación desde `ExportState` sin instanciar el diálogo real.
- `tests/test_queue_runner.py` cubre `QueueRunner`.
- `tests/test_preview_service.py` cubre `PreviewService`.
- `tests/test_architecture_boundaries.py` confirma que los helpers legacy reexportados desde `workers.export_worker` apuntan a la implementación de `application.export_runner`.
