# Architecture Guards

Guía operativa corta para las guardas introducidas en TANDA V2.1.

## Límites protegidos

- `src/flatshot/core/` no debe importar PyQt, `flatshot.ui`, `flatshot.workers`, `flatshot.utils.config` ni `flatshot.utils.log_manager`.
- `src/flatshot/application/` no debe importar PyQt, `flatshot.ui`, `flatshot.workers`, `flatshot.utils.config` ni `flatshot.utils.log_manager`.
- Los servicios/runners principales de `core` y `application` deben poder importarse sin inicializar `QApplication` y sin cargar módulos PyQt.

Estas reglas están protegidas por:

- `tests/test_architecture_boundaries.py`
- `tests/test_headless_imports.py`

## Adaptadores Qt legítimos

Estos módulos pueden seguir importando PyQt porque pertenecen a la capa UI/adaptador actual:

- `src/flatshot/ui/*`
- `src/flatshot/workers/export_worker.py`
- `src/flatshot/workers/queue_worker.py`
- `src/flatshot/workers/pre_render_scheduler.py`
- `src/flatshot/__main__.py` en modo GUI

`ExportWorker` y `QueueWorker` son adaptadores Qt de facto: conservan señales y `QThread`, pero delegan en `ExportRunner` y `QueueRunner`.

## Compatibilidad temporal / deuda aceptada

- `ConfigManager` depende de `QStandardPaths` y convive con `PresetService`.
- `LogManager` depende de `QStandardPaths`.
- `PreRenderScheduler` sigue siendo Qt (`QObject`, `QTimer`, señales).
- La CLI mantiene una ruta de exportación paralela a `ExportRunner`.
- `MainWindow` sigue coordinando demasiado estado y el lanzamiento de workers.
- `PresetService` convive con mecanismos legacy de `ConfigManager`.
- `SettingsService` no sustituye todavía toda la resolución real de configuración porque la ruta sigue pasando por Qt en UI/CLI.
- No existe API local activa y no debe crearse antes de reconciliar estas deudas.

## Qué no eliminar aún

- No eliminar `ConfigManager`, `LogManager`, `ExportWorker`, `QueueWorker` ni `PreRenderScheduler`.
- No mover helpers legacy importados desde `flatshot.workers.export_worker` sin revisar UI, CLI y tests.
- No migrar CLI a `ExportRunner` sin pruebas de paridad de output.
- No cambiar rutas de configuración, formato de presets ni ubicación de logs sin migración y tests.

## Cobertura de paridad mínima

- `tests/test_presenters.py` cubre resumen de lote, exportación, destino, botón de procesado y estado de progreso.
- `tests/test_folder_scanner.py` cubre `FolderScanner`.
- `tests/test_export_config_service.py` cubre `ExportConfigService`.
- `tests/test_export_runner.py` cubre `ExportRunner`.
- `tests/test_queue_runner.py` cubre `QueueRunner`.
- `tests/test_preview_service.py` cubre `PreviewService`.
- `tests/test_architecture_boundaries.py` confirma que los helpers legacy reexportados desde `workers.export_worker` apuntan a la implementación de `application.export_runner`.
