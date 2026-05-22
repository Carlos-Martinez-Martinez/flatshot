# REVISION DEL PLAN DE DESACOPLAMIENTO FLATSHOT

Fecha de auditoría: 2026-05-22.

Documento base: `PLAN_DESACOPLAMIENTO_FLATSHOT_CODEX.md`.

## Resumen

Hechos confirmados:

- El repositorio ya contiene servicios y runners para presenters, escaneo, configuración de exportación, exportación, cola, preview, presets, settings, sesión y estado de aplicación.
- `application` y `core` no importan PyQt.
- `workers.export_worker` y `workers.queue_worker` son adaptadores Qt que delegan en runners puros.
- `MainWindow` consume muchos servicios, pero sigue siendo el coordinador principal y mide 4037 líneas.
- No existen paquetes `adapters/` ni `api/`.
- La suite actual pasa: 196 tests.

Inferencia:

- El plan original ya no debe ejecutarse de forma lineal. Las fases 1-8 están implementadas en distinto grado; la fase útil ahora es reconciliar deuda de integración, duplicidades y puntos no contemplados.

## Estado por fases

### FASE 0 - Línea base y seguridad

Estado: completada con deuda de verificación manual actual.

Evidencias:

- `docs/decoupling_notes.md` registra baseline inicial y tandas de validación.
- `pytest` actual: 196 passed.
- `python -m compileall src` actual: correcto.
- `AGENTS.md` conserva reglas de seguridad de output.

Problemas:

- La auditoría actual no ejecutó smoke UI interactivo ni exportación manual con muestras reales.
- Las validaciones manuales históricas están en notas, no como tests permanentes.

Siguiente acción:

- Antes de tocar fase 9, añadir o repetir un smoke controlado de UI/exportación o documentar explícitamente que la tanda no toca UI runtime.

### FASE 1 - Presenters/helpers visuales

Estado: completada e integrada.

Evidencias:

- `src/flatshot/application/presenters.py` contiene `format_batch_summary`, `format_destination_summary`, `format_export_config_summary`, `format_outputs_summary`, `format_process_button_text`, `format_processing_status`.
- `src/flatshot/ui/main_window.py` usa `presenters` en `_format_batch_summary_text()`, `_format_destination_summary()`, `_format_export_config_summary()`, `_process_button_text()` y `_update_export_bar_state()`.
- `tests/test_presenters.py` cubre textos, destino, botón y estado de progreso.

Problemas:

- Algunos textos/formatos visuales siguen en `app_state.py` y `MainWindow`, lo cual es aceptable si son estado UI, pero conviene evitar nuevas duplicaciones.

Siguiente acción:

- No reabrir salvo para mover textos duplicados cuando se toque el flujo correspondiente.

### FASE 2 - FolderScanner

Estado: completada e integrada con deuda menor de duplicación.

Evidencias:

- `src/flatshot/application/folder_scanner.py` implementa `FolderScanner.scan_folders()`.
- `src/flatshot/application/contracts.py` define `ImageFileInfo`, `FolderScanResult`, `BatchScanResult`.
- `MainWindow._update_folder_ui()` usa `self.folder_scanner.scan_folders(...)`.
- `MainWindow._refresh_image_overrides()` usa scanner para recalcular ajustadas.
- `tests/test_folder_scanner.py` cubre vacíos, inexistentes, PNG, múltiples carpetas, overrides y ruta no directorio.

Problemas:

- `GridPreviewWidget._load_images()` sigue haciendo `folder.glob("*.png")`.
- `MainWindow._start_export()` vuelve a crear snapshots con `folder.glob("*.png")`.
- `QueueRunner._job_images()` también lista PNG si no recibe `input_files`.

Siguiente acción:

- No cambiar todavía el comportamiento. Si se toca export launch, centralizar snapshot/listado sin alterar el criterio de PNG.

### FASE 3 - ExportConfigService

Estado: integrada pero con deuda.

Evidencias:

- `src/flatshot/application/export_config_service.py` implementa `build_from_settings()`, `validate()` y `destinations_for_folders()`.
- `MainWindow._build_export_config_from_settings()` delega en el servicio.
- `MainWindow._start_export()` usa `validate()` y `destinations_for_folders()`.
- `tests/test_export_config_service.py` cubre defaults, overrides, validación y destinos con variantes.

Problemas:

- `ExportConfigDialog` sigue teniendo lógica visual propia de resumen y naming preview.
- `MainWindow._apply_export_preferences()` todavía sincroniza radio buttons, path, variants y settings.
- El servicio no representa todo el flujo de preparación de exportación; sólo configuración/destinos.

Siguiente acción:

- Crear una tanda de preparación de export run si se quiere reducir `_start_export()`.

### FASE 4 - ExportRunner

Estado: completada e integrada con deuda de compatibilidad.

Evidencias:

- `src/flatshot/application/export_runner.py` contiene `ExportRunner`, `process_single_image`, `apply_naming_template`, planificación de variantes, cache y snapshots.
- `src/flatshot/application/events.py` define eventos neutros de exportación.
- `src/flatshot/application/execution_control.py` define `CancellationToken` y `PauseToken`.
- `src/flatshot/workers/export_worker.py` hereda `QThread`, construye `ExportJobRequest` y delega en `ExportRunner`.
- `tests/test_export_runner.py`, `tests/test_export_cache.py`, `tests/test_export_variants.py` y `tests/test_overrides.py` cubren runner, cache, variantes y overrides.

Problemas:

- `workers.export_worker` reexporta helpers de `export_runner` por compatibilidad; UI, CLI y tests siguen importando helpers desde `workers`.
- `cli.py` no usa `ExportRunner`; mantiene una ruta de exportación paralela con `ShadowEngine`.
- `MainWindow._start_export()` sigue preparando snapshots y lanzando `ExportWorker`.

Siguiente acción:

- Añadir guardas/paridad antes de migrar CLI o imports de helpers.

### FASE 5 - QueueRunner

Estado: completada e integrada con deuda.

Evidencias:

- `src/flatshot/application/queue_runner.py` contiene `QueueRunner`.
- `src/flatshot/application/contracts.py` define `QueueRunRequest` y `QueueRunResult`.
- `src/flatshot/application/events.py` define eventos neutros de cola.
- `src/flatshot/workers/queue_worker.py` hereda `QThread`, construye `QueueRunRequest` y delega en `QueueRunner`.
- `MainWindow._start_export()` usa `QueueWorker` para múltiples carpetas.
- `tests/test_queue_runner.py` cubre cola vacía, una/múltiples carpetas, carpeta vacía, error, cancelación y pausa/reanudación.

Problemas:

- `QueueWorker` depende de `LogManager`, que usa `QStandardPaths`.
- `QueueWorker._create_export_runner()` importa `workers.export_worker` para conservar compatibilidad con monkeypatch/tests.
- `docs/decoupling_notes.md` registra una posible carrera visual si se pausa justo al inicio del primer job.

Siguiente acción:

- No mover módulos todavía. Primero consolidar tests de lifecycle y logging/adaptadores.

### FASE 6 - PreviewService

Estado: completada e integrada con deuda UI.

Evidencias:

- `src/flatshot/application/preview_service.py` contiene `PreviewService`.
- `src/flatshot/application/contracts.py` define `PreviewRequest`, `PreviewResult`, `TilePreviewRequest`, `TilePreviewResult`.
- `MainWindow._render_preview_task()` llama a `PreviewService.render_preview()`.
- `GridPreviewWidget._render_tile_preview()` llama a `PreviewService.render_tile_preview()`.
- `tests/test_preview_service.py` cubre ausencia de Qt, payload RGB y tiles.

Problemas:

- La conversión a `QImage/QPixmap` sigue repartida entre `main_window.py` y `grid_preview.py`.
- El scheduling con `QRunnable/QThreadPool` sigue dentro de UI.
- `contracts.py` importa `PIL.Image` para permitir preview en memoria; no es Qt, pero no es ideal para una API local serializable.

Siguiente acción:

- Si se prepara API/web, añadir contrato path/bytes codificado sin romper el actual.

### FASE 7 - Preset/Settings/Session services

Estado: parcialmente completada e integrada con deuda.

Evidencias:

- `src/flatshot/application/preset_service.py` implementa persistencia, migración, import/export y operaciones de nombres.
- `src/flatshot/application/settings_service.py` implementa defaults, load/save y normalización.
- `src/flatshot/application/session_service.py` implementa load/save/clear y build payload.
- `MainWindow` usa `PresetService`, `SettingsService` y `SessionService.build_session_data()`.
- `utils.config.ConfigManager` delega a `PresetService`.
- `utils.session_manager.SessionManager` delega a `SessionService`.
- Tests: `test_preset_service.py`, `test_settings_service.py`, `test_session_service.py`, `test_config_manager.py`.

Problemas:

- `ConfigManager` sigue resolviendo ruta con `QStandardPaths`.
- `LogManager` sigue resolviendo ruta con `QStandardPaths`.
- CLI usa `ConfigManager` y `LogManager`, por tanto conserva dependencia Qt indirecta.
- Restauración de sesión sigue en `MainWindow`.
- `MainWindow._get_default_presets()` duplica defaults parciales.

Siguiente acción:

- Separar resolución de rutas Qt de servicios y CLI en una tanda posterior, con tests de compatibilidad.

### FASE 8 - Estado unificado de aplicación

Estado: integrada pero con deuda.

Evidencias:

- `src/flatshot/application/app_state.py` define `UiViewState`, `BatchSummary`, `ProcessingState`, `ExportState`, `PreviewState`, `FlatshotAppState` y helpers.
- `MainWindow` mantiene `self.batch_summary`, `self.export_state`, `self.preview_state`, `self.processing_state`, `self.ui_view_state` y reconstruye `self.app_state` con `build_flatshot_app_state()`.
- `MainWindow._update_export_bar_state()`, `_apply_preview_state()`, `_apply_processing_state()`, `_on_queue_job_started()`, `_reset_export_ui()` usan helpers de estado.
- `tests/test_app_state.py` cubre estados, textos, progreso, export summaries y preview state.

Problemas:

- El estado no es todavía una fuente única completa: `MainWindow` conserva listas, paths, mockups, workers, timers, overrides y widgets.
- El estado ayuda a pintar UI, pero no coordina por sí solo operaciones.

Siguiente acción:

- Mantenerlo como helper de coordinación. No crear framework de estado más grande salvo necesidad concreta.

### FASE 9 - Adaptación progresiva de PyQt a servicios

Estado: iniciada/parcialmente implementada.

Evidencias:

- `MainWindow` instancia servicios y consume runners a través de workers.
- `ui.shell` reexporta dataclasses de `app_state` y conserva componentes UI.
- `grid_preview.py` consume `PreviewService`.
- `workers/export_worker.py` y `workers/queue_worker.py` ya son adapters de facto.

Problemas:

- No existe paquete `adapters/qt`.
- `MainWindow` sigue lanzando `ExportWorker` y `QueueWorker` directamente.
- `MainWindow._start_export()` concentra validación, snapshot, estado, decisión de worker, wiring de señales y arranque.
- `MainWindow` sigue siendo grande y sensible a callbacks.
- Pre-render no fue tratado por la arquitectura de adapters.

Siguiente acción:

- Reescribir fase 9 como tandas pequeñas: guardas de arquitectura, preparación de export run, adapters explícitos/logging/config y reducción progresiva de MainWindow.

### FASE 10 - API local experimental

Estado: no iniciada y debe seguir bloqueada.

Evidencias:

- No existe `src/flatshot/api/`.
- No hay dependencias FastAPI/servidor.
- La checklist de API local sólo está parcialmente cumplida.

Problemas:

- CLI no comparte motor de exportación con GUI.
- Persistencia/logging aún tienen rutas Qt vía `utils`.
- Pre-render scheduler sigue Qt.
- No hay servicio único de lanzamiento de operaciones.

Siguiente acción:

- No crear API local todavía.

## Desviaciones detectadas

Fases implementadas fuera de la forma original:

- `workers/` se convirtió en adaptador Qt, pero no se creó `adapters/qt`.
- `app_state.py` creció más allá de un estado mínimo y cubre batch, export, preview y processing.
- `PreRenderScheduler` y `pre_render_process` existen como subsistema nuevo que el plan original no contemplaba de forma explícita.
- Las variantes de exportación multi-salida ya existen y están integradas; el plan original advertía no inventarlas, pero en el código actual son una realidad que debe preservarse.

Duplicidades actuales:

- Ruta CLI exporta directamente con `ShadowEngine`; GUI usa `ExportRunner`.
- Helpers de exportación se consumen desde `workers.export_worker` aunque viven en `application.export_runner`.
- Escaneo/listado de PNG aparece en scanner, grid, snapshot de export y queue fallback.
- Presets pasan por `PresetService` y por wrapper `ConfigManager`.
- Defaults de presets existen en `PresetService` y fallback de `MainWindow`.

Servicios creados pero no completamente integrados:

- `SessionService`: usado para IO/payload, pero restore sigue en `MainWindow`.
- `SettingsService`: usado para IO, pero path de config sigue en `ConfigManager` Qt.
- `ExportRunner`: integrado en GUI vía worker, no en CLI.
- `QueueRunner`: integrado en GUI vía worker; logging sigue con `LogManager` Qt.
- `PreviewService`: integrado para render, pero adapters/conversión Qt siguen repartidos.

Documentación desactualizada:

- `README.md` describe tests como motor/CLI/historial/modelos, pero la suite ya cubre servicios/runners/estado/pre-render.
- `PLAN_DESACOPLAMIENTO_FLATSHOT_CODEX.md` conserva fases como pendientes aunque muchas están implementadas.
- `docs/decoupling_notes.md` es histórico y útil, pero ya no debe ser el plan operativo principal.

Riesgos si se continúa sin reconciliar:

- Duplicar más lógica de exportación en CLI/API.
- Crear API sobre rutas Qt o workers Qt.
- Refactorizar `MainWindow` sin guardas suficientes de paridad.
- Cambiar accidentalmente outputs al unificar CLI y runner.
- Olvidar pre-render/cache en el diseño de futuros adapters.

## Recomendación

El plan original debe quedar como histórico. A partir de ahora debe usarse `docs/PLAN_DESACOPLAMIENTO_FLATSHOT_V2.md`.
