# DECISIÓN NUEVA APP FLATSHOT

Fecha: 2026-05-22.

## 1. Objetivo

Levantar una nueva aplicacion moderna de escritorio para FlatShot desde cero, aprovechando el motor funcional existente cuando ya esta desacoplado de PyQt.

El proyecto actual se considera una base tecnica y una referencia de comportamiento. No se considera una referencia visual. La nueva app debe tener frontend, flujo, layout y experiencia propios, sin portar pantallas ni decisiones de `MainWindow`.

Invariante: no cambiar el aspecto de las imagenes exportadas ni el comportamiento de salida salvo decision explicita, documentada y testeada.

## 2. Que se aprovecha del proyecto actual

[REUTILIZAR] Puede usarse como motor/backend:

- `src/flatshot/core/engine.py`: `ShadowEngine` y entrada principal de render de sombras.
- `src/flatshot/core/shadow/`: renderers `legacy` y `realistic_v2`, geometria, composicion y tipos de diagnostico.
- `src/flatshot/core/models.py`: `ShadowSettings`, `ExportConfig`, `ExportVariant`, `CurveData`, `JobItem` y normalizadores.
- `src/flatshot/core/scaling.py`: calculo de escala, mascara de sujeto y curva adaptativa.
- `src/flatshot/core/overrides.py`: overrides locales por imagen.
- `src/flatshot/application/contracts.py`: contratos Qt-free para escaneo, preview, exportacion y cola.
- `src/flatshot/application/events.py`: eventos neutrales de exportacion y cola.
- `src/flatshot/application/execution_control.py`: tokens de pausa y cancelacion sin Qt.
- `src/flatshot/application/folder_scanner.py`: escaneo de carpetas y PNG.
- `src/flatshot/application/preview_service.py`: preview Qt-free basada en el motor.
- `src/flatshot/application/export_config_service.py`: construccion, validacion y destinos de exportacion.
- `src/flatshot/application/export_run_planner.py`: planificacion previa de exportacion.
- `src/flatshot/application/export_runner.py`: exportacion real, cache, naming, variantes, progreso y cancelacion.
- `src/flatshot/application/queue_runner.py`: cola secuencial de carpetas con eventos neutrales.
- `src/flatshot/application/preset_service.py`: carga, migracion, importacion y exportacion de presets.
- `src/flatshot/application/settings_service.py`: defaults y persistencia de settings.
- `src/flatshot/application/session_service.py`: persistencia de sesion Qt-free.
- `src/flatshot/application/log_service.py`: logging reutilizable sin widgets.
- `src/flatshot/application/pre_render_planner.py`: planificacion de cache sin Qt.
- `src/flatshot/utils/render_cache.py`: cache de renders reutilizable por exportacion y pre-render.
- `src/flatshot/workers/pre_render_process.py`: job puro de pre-render en proceso aislado.
- `tests/`: suite existente como red de seguridad, especialmente tests de motor, exportacion, previews, presets, cola, CLI y fronteras arquitectonicas.

[ADAPTAR] Es util, pero necesita envoltorio, bridge o contrato:

- `src/flatshot/cli.py`: comportamiento util para automatizacion y dry-run, pero aun mantiene una ruta propia de procesamiento. Conviene adaptarlo gradualmente a runners comunes si se toca.
- `src/flatshot/application/app_state.py`: contiene estados y textos utiles; para la nueva app se puede reutilizar parcialmente, evitando arrastrar microcopy o estructura mental de la UI legacy.
- `src/flatshot/application/presenters.py`: helpers de texto reutilizables como punto de partida, pero la nueva UX puede necesitar presenters nuevos.
- `src/flatshot/workers/export_worker.py`: adaptador Qt de `ExportRunner`; no usar directamente en la nueva app, pero sirve como ejemplo de traduccion de eventos.
- `src/flatshot/workers/queue_worker.py`: adaptador Qt de `QueueRunner`; no usar directamente, pero referencia la integracion de progreso.
- `src/flatshot/workers/pre_render_scheduler.py`: scheduler acoplado a `QObject/QTimer`; reutilizar ideas y `pre_render_planner`, no el scheduler Qt.
- `src/flatshot/utils/config.py` y `src/flatshot/utils/log_manager.py`: wrappers de compatibilidad con dependencias Qt; preferir `ConfigPathResolver`, `SettingsService` y `ActivityLogService`.

[REFERENCIA] Solo sirve para entender comportamiento esperado:

- `README.md`: flujo funcional, CLI, configuracion y comportamiento documentado.
- `docs/ARCHITECTURE_GUARDS.md`: fronteras actuales y deuda aceptada.
- `docs/ESTADO_ACTUAL_FLATSHOT.md`: auditoria previa de desacoplamiento.
- `src/flatshot/ui/main_window.py`: flujo funcional, restauracion de sesion, lanzamiento de workers, decisiones de negocio aun conectadas a UI.
- `src/flatshot/ui/dialogs.py`: opciones de exportacion, presets y calibracion como referencia funcional.
- `src/flatshot/ui/grid_preview.py`: comportamiento esperado de miniaturas, seleccion y estados.
- `src/flatshot/ui/widgets.py`: comportamiento de canvas, comparacion, zoom, fondo y guias.
- Tests de adaptadores UI, cuando existan, para entender resultados esperados.

[DESCARTAR] No debe condicionar la nueva app:

- Layout PyQt actual.
- Navegacion actual.
- Dialogos visuales actuales.
- Estructura de `MainWindow`.
- Widgets PyQt, `QSplitter`, `QDialog`, `QMessageBox`, `QFileDialog`, `QPixmap`, `QImage`.
- Tema visual, estilos y composicion de `src/flatshot/ui/styles.py`.
- `qtawesome` como decision visual para la nueva interfaz.
- Splash actual y cualquier patron ornamental heredado.

## 3. Que no debe arrastrarse

La nueva app no debe heredar:

- interfaz PyQt actual;
- layout de paneles actual;
- dialogos actuales;
- patrones de interaccion antiguos;
- estructura mental de `MainWindow`;
- acoplamiento entre seleccion visual y preparacion de exportacion;
- dependencia de widgets para validar configuracion;
- conversiones Qt como contrato de preview;
- estilos, iconografia o microcopy tecnico heredado;
- administracion de presets como experiencia principal visible;
- controles tecnicos avanzados expuestos al mismo nivel que el flujo de produccion.

## 4. Opciones de stack

### Tauri + frontend web moderno + sidecar Python

Encaje con FlatShot:

- Integracion con Python: buena si se usa un sidecar Python empaquetado y un bridge estable. Requiere disenar IPC.
- Acceso a filesystem: fuerte mediante APIs Tauri para dialogos, abrir carpetas y permisos locales.
- Seleccion de carpetas: nativa con dialogo del sistema desde Tauri.
- Previews: el motor Python genera imagen o bytes; frontend solo muestra resultado.
- Exportacion larga con progreso: viable con proceso Python persistente y eventos hacia frontend.
- Comunicacion: Tauri commands + sidecar por stdio/NDJSON o servidor local con token.
- Empaquetado Windows: mejor peso que Electron, pero requiere resolver empaquetado del sidecar Python.
- Peso: menor que Electron.
- Desarrollo: mas complejo al inicio por Rust/Tauri y Python sidecar.
- Mantenimiento: bueno si el bridge queda pequeño y los contratos viven en Python.
- Riesgo tecnico: sidecar y packaging.
- Velocidad hasta version usable: media. El mock puede arrancar rapido, el empaquetado llegara mas tarde.

### Electron + frontend web moderno + sidecar Python

Encaje con FlatShot:

- Integracion con Python: buena via `child_process` y mensajes por stdio.
- Acceso a filesystem: fuerte desde main process.
- Seleccion de carpetas: nativa y sencilla.
- Previews: igual que Tauri, generadas por Python.
- Exportacion larga con progreso: viable.
- Comunicacion: IPC Electron + proceso Python.
- Empaquetado Windows: maduro, pero incluir Python sidecar sigue siendo trabajo.
- Peso: alto por Chromium + Node.
- Desarrollo: rapido si se prioriza velocidad sobre peso.
- Mantenimiento: mas superficie JS/Node y actualizaciones de Electron.
- Riesgo tecnico: menor en IPC, mayor en peso y mantenimiento.
- Velocidad hasta version usable: alta.

### App web local servida por Python

Encaje con FlatShot:

- Integracion con Python: excelente.
- Acceso a filesystem: fuerte en backend, limitado en navegador.
- Seleccion de carpetas: problematica si se quiere UX desktop nativa; el browser limita rutas y destino.
- Previews: facil por endpoints locales.
- Exportacion larga con progreso: viable con SSE/WebSocket.
- Comunicacion: HTTP local.
- Empaquetado Windows: menos claro para app de escritorio; necesita wrapper o instalador propio.
- Peso: bajo.
- Desarrollo: muy rapido.
- Mantenimiento: simple si se acepta experiencia de navegador.
- Riesgo tecnico: seguridad local, permisos, puertos, CORS/token, experiencia no tan desktop.
- Velocidad hasta version usable: muy alta para prototipo, media para producto final.

### Mantener interfaz actual redisenada

Encaje con FlatShot:

- Integracion con Python: excelente.
- Acceso a filesystem: ya resuelto.
- Previews/exportacion/progreso: ya resueltos.
- Empaquetado Windows: similar al estado actual.
- Peso: bajo-medio.
- Desarrollo: rapido para cambios superficiales.
- Mantenimiento: seguiria atrapado por `MainWindow` y widgets heredados.
- Riesgo tecnico: bajo a corto plazo, alto para el objetivo real.
- Velocidad hasta version usable: alta, pero incumple el enfoque pedido.

No se recomienda porque el objetivo explicito es una app nueva, no modernizar o redisenar la UI actual.

## 5. Decision recomendada

Recomendacion: Tauri + frontend web moderno + backend Python sidecar.

Justificacion para este proyecto:

- FlatShot ya tiene motor Python reutilizable y tests. No conviene reimplementar imagen, sombras, presets ni exportacion en frontend.
- La nueva app debe ser de escritorio, no solo una pagina local. Tauri da dialogos nativos, apertura de carpetas y empaquetado desktop con menor peso que Electron.
- El coste principal de Tauri es el sidecar Python. Ese coste existe tambien en Electron si se quiere preservar el motor.
- La app actual no se elimina. Podemos avanzar en paralelo: primero frontend mock, luego bridge Python, luego shell Tauri real.
- El repo ya tiene contratos Qt-free (`application/contracts.py`, `events.py`, runners y services), lo que reduce mucho el riesgo de crear un bridge.
- Para tener algo usable rapido, el primer scaffold no necesita introducir Tauri, Rust, Node ni dependencias nuevas. Se crea el frontend estatico y se retrasa el shell Tauri hasta que los contratos del bridge esten claros.

Decision provisional de APP.1:

- Crear `apps/flatshot-desktop/` como nueva app.
- Crear `frontend/` estatico sin dependencias para validar direccion UX.
- Crear `bridge/` solo como placeholder documental.
- No crear aun `src-tauri/`, servidor local ni API activa.

## 6. Arquitectura objetivo

```text
frontend moderno
    ↓
bridge/API/IPC local
    ↓
servicios Python reutilizados
    ↓
motor FlatShot
```

Arquitectura propuesta:

```text
apps/flatshot-desktop/
  frontend/
    index.html
    styles.css
    app.js
  bridge/
    README.md
  src-tauri/              # futuro, no en APP.1

src/flatshot/
  application/
  core/
  utils/
```

Donde vive el frontend:

- En `apps/flatshot-desktop/frontend`.
- En APP.1 es HTML/CSS/JS estatico.
- En fases posteriores puede pasar a Vite/React/Svelte si se justifica, sin cambiar el motor.

Donde vive Python:

- El motor y servicios siguen en `src/flatshot/core` y `src/flatshot/application`.
- El bridge Python deberia ser una capa fina nueva, fuera de `ui/` y sin PyQt.
- No crear `src/flatshot/api` todavia porque hay un test que confirma que no existe API activa.

Como se comunican:

- Frontend llama a comandos Tauri.
- Tauri mantiene un sidecar Python vivo.
- Sidecar recibe mensajes JSON con contratos estables y responde con resultados serializables.
- Eventos de progreso se emiten como NDJSON o canal equivalente y Tauri los reemite al frontend.

Seleccion de carpetas:

- La seleccion la hace Tauri con dialogo nativo.
- El frontend recibe rutas seleccionadas.
- El bridge valida y escanea usando `FolderScanner`.

Previews:

- El frontend solicita preview para una imagen, preset, ajustes y tamano.
- El bridge llama `PreviewService`.
- El bridge devuelve una imagen codificada para visualizacion o una referencia temporal segura.
- El frontend no implementa sombras ni escala.

Exportacion:

- El frontend prepara una solicitud serializable.
- El bridge construye `ExportJobRequest` o `QueueRunRequest`.
- `ExportRunner` o `QueueRunner` ejecutan el trabajo.
- El sidecar emite eventos de progreso y finalizacion.

Errores:

- El motor produce excepciones o eventos neutrales.
- El bridge normaliza a payloads `{type, message, path?, code?}`.
- El frontend muestra resumen breve y detalle expandible.

Abrir carpeta de salida:

- El backend devuelve destinos reales.
- Tauri abre carpetas con API nativa despues de validar que corresponden a resultados de exportacion o rutas seleccionadas.

Como se evita duplicar logica:

- JavaScript no procesa imagenes.
- JavaScript no genera nombres finales.
- JavaScript no decide cache, variantes, DPI, calidad JPG/PNG ni transparencia.
- JavaScript solo representa estado, recoge intenciones y muestra resultados.

## 7. Riesgos

- Filesystem: rutas largas, permisos, carpetas movidas durante el trabajo, rutas con caracteres no ASCII.
- Empaquetado: incluir Python, dependencias Pillow/numpy/pydantic y multiprocessing en Windows.
- Progreso de exportacion: mantener eventos reales, no barras decorativas.
- Previews pesadas: evitar bloquear frontend o sidecar principal; cachear y cancelar previews obsoletas.
- Rutas Windows: espacios, `LOCALAPPDATA`, rutas UNC, separadores y apertura de explorador.
- Permisos: Tauri debe limitar operaciones a rutas seleccionadas por el usuario.
- Comunicacion entre procesos: caidas del sidecar, reinicio, timeouts, versionado de contratos.
- Rendimiento: conversion de preview a base64 puede ser costosa para imagenes grandes.
- Dos interfaces durante transicion: PyQt legacy y nueva app deben coexistir sin tocar output.
- Tests insuficientes: falta una prueba end-to-end del futuro bridge y no hay pruebas visuales del nuevo frontend.
- CLI: sigue siendo util, pero no debe convertirse en la unica capa de bridge si duplica exportacion.

## 8. Criterios para considerar viable la nueva app

Primer prototipo real viable:

- Cargar una carpeta desde selector nativo.
- Listar imagenes PNG encontradas con conteo fiable.
- Mostrar preview real de una imagen o placeholder conectado al bridge.
- Listar presets reales desde `PresetService`.
- Aplicar preset o, como minimo, enviar sus settings al preview.
- Preparar exportacion con formato, tamano, destino y naming.
- Lanzar exportacion real o simulada solo en una fase temprana marcada como simulada.
- Mostrar progreso real desde eventos cuando la exportacion sea real.
- Mostrar errores por carpeta/imagen.
- Mostrar resultado final con destinos.
- Abrir carpeta de salida.
- Volver a estado listo para otro lote.
