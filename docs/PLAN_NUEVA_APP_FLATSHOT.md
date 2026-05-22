# PLAN NUEVA APP FLATSHOT

## 1. Objetivo

Levantar una nueva app moderna desde cero aprovechando el motor actual de FlatShot.

No se elimina la app PyQt actual. No se cambia el output de imagen. La nueva app se desarrolla en paralelo hasta tener paridad funcional suficiente.

## 2. Estrategia

Trabajar en paralelo:

```text
app actual legacy estable
        +
nueva app moderna progresiva
```

La app actual sigue siendo la herramienta de produccion mientras la nueva app madura. Cada tanda debe ser pequena, verificable y reversible.

## 3. Estructura propuesta del repositorio

Estructura inicial:

```text
apps/
  flatshot-desktop/
    README.md
    frontend/
      index.html
      styles.css
      app.js
    bridge/
      README.md

src/
  flatshot/
    core/
    application/
    ui/                  # legacy, no tocar para la nueva UX salvo necesidad
    workers/             # adaptadores Qt legacy
```

Estructura futura probable:

```text
apps/
  flatshot-desktop/
    frontend/
    bridge/
    src-tauri/
      tauri.conf.json
      src/

src/
  flatshot/
    core/
    application/
    desktop_bridge/      # futuro, si se crea bridge Python sin activar API local
```

Reglas:

- `core` y `application` siguen siendo la fuente funcional.
- El frontend nuevo vive fuera de `src/flatshot/ui`.
- La UI PyQt no se mueve ni se borra en esta etapa.
- No crear una API local activa hasta tener contratos y seguridad claros.

## 4. Contratos minimos entre UI y motor

Listar presets:

- Entrada: ninguna o ruta de config opcional.
- Salida: categorias, nombres, settings serializables, preset activo si existe.
- Motor: `PresetService`.

Leer configuracion:

- Entrada: ninguna o perfil/config dir.
- Salida: settings normalizados.
- Motor: `SettingsService`, `ConfigPathResolver`.

Escanear carpeta:

- Entrada: lista de rutas seleccionadas.
- Salida: carpetas, imagenes, errores, conteos.
- Motor: `FolderScanner`.

Listar imagenes:

- Entrada: lote escaneado o carpeta.
- Salida: items con nombre, path, tamano, override local.
- Motor: `FolderScanner` y contratos existentes.

Renderizar preview:

- Entrada: path de imagen, settings, curve data, target size, variante opcional.
- Salida: imagen codificada o bytes con dimensiones y warning.
- Motor: `PreviewService`.

Aplicar ajustes:

- Entrada: settings base, cambios globales, override local opcional.
- Salida: settings efectivos serializables.
- Motor: `ShadowSettings`, `normalize_shadow_settings`, `apply_image_override`.

Preparar exportacion:

- Entrada: carpetas, export config, variantes.
- Salida: plan de destinos, cantidad de fuentes, cantidad de archivos.
- Motor: `ExportRunPlanner`, `ExportConfigService`.

Lanzar exportacion:

- Entrada: `ExportJobRequest` o `QueueRunRequest` serializado.
- Salida: job id y eventos.
- Motor: `ExportRunner`, `QueueRunner`.

Recibir progreso:

- Eventos: started, log, progress, image_completed, job_started, job_completed, finished, paused, resumed, cancelled.
- Motor: `application/events.py`.

Pausar, reanudar, cancelar:

- Entrada: job id.
- Salida: confirmacion y eventos.
- Motor: `PauseToken`, `CancellationToken`.

Obtener resultado:

- Entrada: job id.
- Salida: estado final, procesadas, total, errores, duracion, destinos.
- Motor: `ExportJobResult`, `QueueRunResult`.

Abrir carpeta de salida:

- Entrada: destino devuelto por un job o seleccionado por usuario.
- Salida: accion nativa Tauri.
- Motor: no procesa; Tauri abre ruta validada.

## 5. Secuencia de tandas

No crear mas fases salvo necesidad justificada.

### APP.0 - Auditoria de reutilizacion y decision tecnica

Objetivo: inventariar repo, servicios, motor, UI legacy y tests.

Archivos probables: docs de decision.

Se puede tocar: documentacion.

No se puede tocar: motor, UI legacy, exportacion.

Tests: `pytest`, `python -m compileall src`, `git diff --check`.

Validacion manual: no aplica salvo inspeccion.

Riesgos: clasificar mal deuda Qt como reutilizable.

### APP.1 - Scaffold de nueva app moderna

Objetivo: crear estructura minima y pantalla mock sin motor real.

Archivos probables: `apps/flatshot-desktop/frontend/*`, `apps/flatshot-desktop/README.md`.

Se puede tocar: nueva carpeta `apps/flatshot-desktop`.

No se puede tocar: `src/flatshot/core`, `src/flatshot/application`, `src/flatshot/ui`.

Tests: suite Python completa y checks de diff. Si se agregan scripts frontend, ejecutarlos.

Validacion manual: abrir HTML o servidor estatico y comprobar layout base.

Riesgos: convertir el mock en producto, introducir dependencias antes de necesitarlas.

### APP.2 - UI mock navegable sin motor real

Objetivo: hacer navegable el flujo visual completo con datos simulados.

Archivos probables: frontend.

Se puede tocar: estado frontend mock, componentes, navegacion, estados vacios.

No se puede tocar: motor ni PyQt legacy.

Tests: checks estaticos si se configura toolchain; Python suite debe seguir verde.

Validacion manual: flujo sin carpeta, carpeta con datos mock, seleccion, ajustes, exportacion simulada.

Riesgos: crear microcopy o layout demasiado cercano a legacy.

### APP.3 - Bridge/backend minimo

Objetivo: definir proceso Python o contrato IPC minimo sin exportacion real.

Archivos probables: `apps/flatshot-desktop/bridge`, posible `src/flatshot/desktop_bridge`.

Se puede tocar: capa nueva de bridge y tests.

No se puede tocar: output de imagen, runners salvo wrappers seguros.

Tests: unitarios de serializacion y comandos health/config.

Validacion manual: frontend obtiene health/version desde backend.

Riesgos: crear API local insegura o acoplar frontend a modelos Python internos sin versionar.

### APP.4 - Escaneo real de carpetas

Objetivo: seleccionar carpeta y listar PNG reales.

Archivos probables: bridge, frontend, tests de contrato.

Se puede tocar: bridge, conversion de `BatchScanResult` a JSON.

No se puede tocar: `FolderScanner` salvo bug probado.

Tests: `test_folder_scanner.py` existente y nuevos tests del bridge.

Validacion manual: carpeta vacia, carpeta con PNG, carpeta inaccesible si es posible.

Riesgos: rutas Windows, permisos, rutas largas.

### APP.5 - Preview real

Objetivo: mostrar preview real conectada a `PreviewService`.

Archivos probables: bridge preview, frontend canvas.

Se puede tocar: codificacion de preview y cancelacion de solicitudes.

No se puede tocar: `ShadowEngine` salvo bug documentado.

Tests: `test_preview_service.py` y contrato de preview.

Validacion manual: preview carga, loading, warning, error.

Riesgos: previews pesadas, base64 grande, cancelacion obsoleta.

### APP.6 - Presets y ajustes

Objetivo: listar presets reales y modificar settings principales.

Archivos probables: bridge presets/settings, frontend panel de ajustes.

Se puede tocar: contratos de settings serializables.

No se puede tocar: formato de presets sin migracion.

Tests: `test_preset_service.py`, `test_settings_service.py`, contrato bridge.

Validacion manual: preset cambia preview, reset funciona.

Riesgos: defaults nuevos que cambien visual output.

### APP.7 - Exportacion real y progreso

Objetivo: lanzar exportacion real usando runners existentes.

Archivos probables: bridge jobs, frontend barra inferior.

Se puede tocar: orquestador de jobs nuevo.

No se puede tocar: `process_single_image`, naming, calidad JPG/PNG, cache key.

Tests: `test_export_runner.py`, `test_queue_runner.py`, tests de bridge.

Validacion manual: exportar carpeta pequena, ver progreso real, comprobar destino.

Riesgos: multiprocessing empaquetado, cancelacion, errores parciales.

### APP.8 - Gestion de errores y resultados

Objetivo: mostrar errores por imagen/carpeta y resumen final profesional.

Archivos probables: frontend resultado, bridge almacenamiento de eventos.

Se puede tocar: presentacion de eventos y errores.

No se puede tocar: comportamiento de runner salvo bugs.

Tests: eventos de error, estados finales.

Validacion manual: imagen corrupta, destino invalido, stop/cancel.

Riesgos: ocultar errores reales o mostrar detalle tecnico excesivo.

### APP.9 - Paridad funcional basica con app legacy

Objetivo: cubrir flujo principal real.

Archivos probables: frontend, bridge, tests de integracion.

Se puede tocar: capas nuevas.

No se puede tocar: app legacy salvo adaptaciones de servicios justificadas.

Tests: suite completa y smoke de nueva app.

Validacion manual: flujo completo con carpeta real.

Riesgos: paridad incompleta en overrides, variantes, sesion o destino custom.

### APP.10 - Empaquetado experimental

Objetivo: empaquetar Tauri + sidecar Python en Windows.

Archivos probables: `src-tauri`, scripts de build, docs.

Se puede tocar: configuracion de empaquetado.

No se puede tocar: output de exportacion.

Tests: smoke empaquetado y suite Python.

Validacion manual: instalar/ejecutar build, seleccionar carpeta, preview, exportar.

Riesgos: sidecar Python, antivirus, rutas de recursos, multiprocessing.

### APP.11 - Pulido UX/UI

Objetivo: mejorar ergonomia, accesibilidad, estados y rendimiento visual.

Archivos probables: frontend.

Se puede tocar: UI nueva.

No se puede tocar: motor.

Tests: visual/manual, accesibilidad basica, suite Python.

Validacion manual: resoluciones distintas, DPI, teclado, foco, errores.

Riesgos: pulido que cambie flujo funcional o esconda controles necesarios.

### APP.12 - Plan de retirada de interfaz legacy

Objetivo: decidir cuando PyQt deja de ser interfaz principal.

Archivos probables: documentacion, scripts de entrada.

Se puede tocar: docs y estrategia de distribucion.

No se puede tocar: borrar PyQt sin paridad aprobada.

Tests: suite completa y pruebas manuales comparativas.

Validacion manual: checklists de paridad.

Riesgos: retirar antes de cubrir casos de produccion.

## 6. Criterios de aceptacion por fase

Una fase esta aceptada si:

- cumple su objetivo concreto;
- no rompe tests existentes;
- documenta cualquier check no ejecutado;
- no cambia output de imagen salvo que la fase lo pida y lo documente;
- no deja botones o estados sin comportamiento dentro del alcance de la fase;
- no introduce dependencias sin justificacion;
- mantiene la app PyQt actual disponible.

Para fases con UI nueva, se requiere al menos una validacion manual del layout o flujo afectado.

Para fases con bridge, se requieren tests de contrato y serializacion.

Para fases con exportacion o preview real, se requieren tests del servicio existente y checks manuales con imagenes reales o fixtures pequenas.

## 7. Que no hacer todavia

- No eliminar la app actual.
- No reimplementar el motor en frontend.
- No copiar PyQt.
- No construir toda la app de golpe.
- No hacer packaging antes de tener flujo funcional.
- No cambiar output de imagenes.
- No migrar configuracion sin compatibilidad.
- No romper tests.
- No crear servidor local abierto a red.
- No usar rutas absolutas de usuario en codigo versionado.
- No crear dependencia de Windows-only salvo adapter nativo aislado.
- No mover business logic a JS/TS.
- No convertir `MainWindow` en base conceptual de la nueva app.

