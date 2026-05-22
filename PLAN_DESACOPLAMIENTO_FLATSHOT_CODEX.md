# PLAN DE DESACOPLAMIENTO DE FLATSHOT PARA REDISEÑO UI Y FUTURA INTERFAZ WEB

**Proyecto:** FlatShot  
**Objetivo:** desacoplar la lógica funcional de la interfaz PyQt6 para poder modernizar la UI sin romper exportación, sombras, previews, presets, cola, caché ni acceso a carpetas.  
**Destino del documento:** Codex / agente de implementación.  
**Prioridad:** estabilidad funcional antes que rediseño visual.

---

## 0. Resumen ejecutivo

FlatShot ya tiene un núcleo funcional valioso: motor de sombras, presets, exportación configurable, cola de carpetas, previsualización, grid, caché y CLI. El problema no es el motor; el problema es que la interfaz PyQt6 y la lógica de aplicación están demasiado entremezcladas, especialmente en `MainWindow`.

El rediseño visual o una futura UI web no deberían empezar sustituyendo la interfaz directamente. Antes hay que conseguir que FlatShot pueda hacer estas operaciones sin depender de widgets Qt:

```text
escanear carpetas
cargar presets
aplicar ajustes
renderizar preview
crear plan de exportación
ejecutar exportación
emitir progreso
pausar / reanudar / cancelar
registrar errores
guardar configuración
```

La estrategia correcta es:

```text
PyQt actual funcionando
        ↓
extraer servicios Python independientes de UI
        ↓
envolver esos servicios con adaptadores Qt
        ↓
mantener paridad funcional
        ↓
preparar API local / interfaz web si se decide
```

No se debe romper la app actual durante el proceso. Cada fase debe dejar FlatShot ejecutable.

---

## 1. Diagnóstico del estado actual

### 1.1. Lo que debe conservarse

No tocar salvo necesidad justificada:

- `ShadowEngine`
- `ShadowSettings`
- `ExportConfig`
- `CurveData`
- `JobItem`
- lógica de presets
- sistema de exportación
- generación de nombres
- cola de carpetas
- caché de render/exportación
- logs
- CLI
- tests existentes

### 1.2. Lo que debe desacoplarse

Actualmente hay acoplamientos fuertes entre UI y lógica:

- `MainWindow` construye UI y también coordina estado, previews, exportación, workers, sesión, logs y carpetas.
- `ExportWorker` hereda de `QThread` y emite señales Qt.
- `QueueWorker` hereda de `QThread` y emite señales Qt.
- Previews de canvas y grid convierten directamente entre `PIL`, `QImage`, `QPixmap` y widgets.
- El escaneo de carpetas y el estado visual del lote viven dentro de métodos de UI.
- La configuración de exportación se interpreta y pinta desde `MainWindow`.
- El estado de procesamiento está repartido entre varios métodos.
- La app depende de `QFileDialog`, `QMessageBox`, `QTimer`, `QFileSystemWatcher`, `QThreadPool`, `QRunnable`, `QProgressBar`, labels y botones para coordinar operaciones que deberían vivir en servicios.

### 1.3. Riesgo principal

El mayor riesgo no es técnico, sino arquitectónico: hacer cambios visuales sobre una base en la que la UI es la aplicación.

El desacoplamiento debe evitar esto:

```text
rediseñar widgets → romper callbacks → parchear estados → generar más deuda
```

Y perseguir esto:

```text
extraer estado y casos de uso → adaptar PyQt → rediseñar visualmente con menor riesgo
```

---

## 2. Objetivos del desacoplamiento

### 2.1. Objetivo principal

Conseguir que la lógica de FlatShot pueda ejecutarse desde tres posibles interfaces:

```text
1. PyQt actual o rediseñada
2. CLI
3. futura API local / UI web empaquetada
```

### 2.2. Objetivos técnicos

- Separar dominio, aplicación, adaptadores e interfaz.
- Eliminar dependencias Qt de servicios funcionales.
- Reducir responsabilidades de `MainWindow`.
- Centralizar estado de lote, exportación y procesamiento.
- Crear contratos de datos estables.
- Convertir workers Qt en wrappers/adaptadores, no en núcleo lógico.
- Mantener compatibilidad con los modelos actuales.
- Mantener tests verdes en cada fase.
- Permitir que una futura UI web use el mismo motor.

### 2.3. No objetivos

No hacer en esta fase:

- No rediseñar toda la interfaz visual.
- No migrar aún a React/Electron/Tauri.
- No crear un servidor API de producción.
- No reescribir el motor de sombras.
- No cambiar la lógica de exportación si funciona.
- No introducir base de datos.
- No crear sistema de “salidas múltiples” si no existe ya en la rama actual.
- No eliminar PyQt.
- No romper CLI.
- No introducir dependencias nuevas sin justificar.

---

## 3. Arquitectura objetivo

### 3.1. Capas propuestas

```text
flatshot/
├── core/
│   ├── engine.py
│   ├── models.py
│   ├── overrides.py
│   ├── scaling.py
│   └── ...
│
├── application/
│   ├── contracts.py
│   ├── events.py
│   ├── errors.py
│   ├── folder_scanner.py
│   ├── preview_service.py
│   ├── export_runner.py
│   ├── queue_runner.py
│   ├── preset_service.py
│   ├── export_config_service.py
│   ├── session_service.py
│   └── image_override_service.py
│
├── adapters/
│   ├── qt/
│   │   ├── export_worker_qt.py
│   │   ├── queue_worker_qt.py
│   │   ├── preview_adapter_qt.py
│   │   └── file_dialogs_qt.py
│   │
│   └── local_fs/
│       ├── file_repository.py
│       └── config_repository.py
│
├── ui/
│   ├── main_window.py
│   ├── shell.py
│   ├── styles.py
│   ├── widgets.py
│   ├── grid_preview.py
│   └── dialogs.py
│
├── workers/
│   ├── export_worker.py          # mantener temporalmente como wrapper o compatibilidad
│   └── queue_worker.py           # mantener temporalmente como wrapper o compatibilidad
│
└── api/                          # futura fase opcional
    ├── app.py
    ├── routes.py
    └── websocket_events.py
```

No hace falta crear toda la estructura de golpe. La extracción debe ser incremental.

### 3.2. Regla de dependencias

Permitido:

```text
ui → adapters.qt → application → core
cli → application → core
api → application → core
```

Prohibido:

```text
core → PyQt6
application → PyQt6
application → widgets
application → QMessageBox
application → QThread
application → QPixmap
application → QImage
```

### 3.3. Principio de adaptadores

La lógica funcional debe emitir eventos neutrales. Qt debe traducirlos a señales.

Ejemplo conceptual:

```python
# application/events.py

from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class ExportProgressEvent:
    job_id: str
    processed: int
    total: int
    percent: int
    current_file: str | None = None

@dataclass(frozen=True)
class ExportStatusEvent:
    job_id: str
    status: Literal["pending", "running", "paused", "stopping", "completed", "error", "cancelled"]
    message: str = ""

@dataclass(frozen=True)
class ExportErrorEvent:
    job_id: str
    message: str
    file_path: str | None = None
```

Qt puede convertir eso en:

```python
self.progress_updated.emit(event.percent)
self.log_updated.emit(event.message)
self.finished_process.emit(...)
```

Una futura API podría convertirlo en:

```json
{"type": "progress", "processed": 17, "total": 23, "percent": 74}
```

---

## 4. Contratos de datos propuestos

Crear contratos separados de los modelos de dominio si aportan claridad. No sustituir los modelos actuales sin necesidad.

Archivo recomendado:

```text
src/flatshot/application/contracts.py
```

### 4.1. Folder / batch

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class ImageFileInfo:
    path: Path
    name: str
    stem: str
    suffix: str
    size_bytes: int
    has_local_override: bool = False

@dataclass(frozen=True)
class FolderScanResult:
    folder: Path
    exists: bool
    is_dir: bool
    images: list[ImageFileInfo]
    errors: list[str]

@dataclass(frozen=True)
class BatchScanResult:
    folders: list[FolderScanResult]
    total_folders: int
    total_images: int
    adjusted_images: int
    errors: list[str]
```

### 4.2. Preview

```python
@dataclass(frozen=True)
class PreviewRequest:
    image_path: Path
    settings: ShadowSettings
    curve_data: CurveData
    target_size: tuple[int, int]
    scale_factor: float
    is_preview: bool = True

@dataclass(frozen=True)
class PreviewResult:
    width: int
    height: int
    mode: str
    bytes_rgb: bytes
    warning: str | None = None
```

La UI Qt convertiría `bytes_rgb` a `QImage`. Una futura UI web podría convertirlo a PNG/JPEG o endpoint de imagen temporal.

### 4.3. Export

```python
@dataclass(frozen=True)
class ExportJobRequest:
    folders: list[Path]
    settings: ShadowSettings
    export_config: ExportConfig
    curve_data: CurveData
    preset_name: str | None = None
    image_overrides: dict | None = None

@dataclass(frozen=True)
class ExportJobResult:
    success: bool
    processed: int
    total: int
    errors: int
    duration: float
    destinations: list[Path]
```

### 4.4. Control de ejecución

```python
class CancellationToken:
    def cancel(self) -> None: ...
    @property
    def cancelled(self) -> bool: ...

class PauseToken:
    def pause(self) -> None: ...
    def resume(self) -> None: ...
    def wait_if_paused(self) -> None: ...
    @property
    def paused(self) -> bool: ...
```

No deben depender de Qt. Pueden usar `threading.Event`.

---

## 5. Plan por fases

---

# FASE 0 — Línea base y seguridad

## Objetivo

Crear una base estable antes de tocar arquitectura.

## Tareas

1. Crear rama:

```bash
git checkout -b feature/decouple-flatshot-core
```

2. Ejecutar tests:

```bash
pytest
```

3. Registrar estado inicial:
   - resultado de tests;
   - capturas de UI;
   - flujo manual probado.

4. Localizar y documentar:
   - métodos de `MainWindow` que actualizan estado;
   - métodos de preview;
   - métodos de exportación;
   - métodos de carpetas;
   - métodos de sesión;
   - dependencias Qt en workers.

5. Crear un archivo de seguimiento:

```text
docs/decoupling_notes.md
```

Debe incluir:
- inventario de dependencias;
- lista de acoplamientos;
- riesgos;
- decisiones tomadas.

## Criterios de aceptación

- La app arranca.
- `pytest` pasa o se documentan fallos existentes.
- No se ha modificado lógica funcional.
- Existe inventario inicial.

## Prohibido

- Rediseñar UI.
- Extraer grandes módulos.
- Cambiar comportamiento.

---

# FASE 1 — Presenters y helpers de estado visual

## Objetivo

Separar texto/estado visual de la construcción de widgets, sin cambiar la lógica funcional.

## Archivos recomendados

```text
src/flatshot/application/view_models.py
src/flatshot/application/presenters.py
tests/test_presenters.py
```

## Tareas

1. Crear funciones puras para textos de lote:

```python
def format_batch_summary(folders_count: int, images_count: int, adjusted_count: int = 0) -> str:
    ...
```

Ejemplos:
- `0, 0, 0` → `Sin lote cargado`
- `1, 0, 0` → `1 carpeta · 0 imágenes`
- `1, 23, 0` → `1 carpeta · 23 imágenes`
- `2, 50, 4` → `2 carpetas · 50 imágenes · 4 ajustadas`

2. Crear función pura para resumen de exportación:

```python
def format_export_summary(config: ExportConfig) -> str:
    ...
```

Ejemplos:
- JPG con fondo RGB → `JPG · 1800×2400 · fondo #E6E6E6`
- PNG transparente → `PNG · 1800×2400 · transparente`

3. Crear función pura para destino:

```python
def format_destination_summary(config: ExportConfig) -> str:
    ...
```

Ejemplos:
- subfolder → `Destino: origen / _SALIDA_PRO`
- custom con ruta → `Destino: carpeta personalizada`
- custom sin ruta → `Destino personalizado sin elegir`

4. Crear función para texto de botón:

```python
def format_process_button_text(images_count: int) -> str:
    ...
```

Ejemplos:
- `0` → `Procesar lote`
- `1` → `Procesar 1 imagen`
- `23` → `Procesar 23 imágenes`

5. Adaptar `MainWindow` para usar estas funciones en:
   - `_update_folder_ui`
   - `_update_export_destination_label`
   - `_reset_export_ui`

## Criterios de aceptación

- La UI se ve igual o casi igual.
- Los textos vienen de funciones testeables.
- Hay tests unitarios para singular/plural, destino y exportación.
- No se rompe exportación.
- No se ha tocado `ShadowEngine`.

## Riesgo

Bajo. Esta fase sólo extrae presentación.

---

# FASE 2 — Servicio de escaneo de carpetas

## Objetivo

Sacar de `MainWindow` la lógica de contar imágenes y detectar ajustes locales.

Actualmente `_update_folder_ui` cuenta PNG, ajustadas y actualiza estado visual. Hay que separar cálculo de UI.

## Archivos nuevos

```text
src/flatshot/application/folder_scanner.py
tests/test_folder_scanner.py
```

## Servicio propuesto

```python
from pathlib import Path
from flatshot.application.contracts import BatchScanResult, FolderScanResult, ImageFileInfo
from flatshot.core.overrides import has_image_override, override_key

class FolderScanner:
    def scan_folders(self, folders: list[Path], image_overrides: dict | None = None) -> BatchScanResult:
        ...
```

## Reglas

- Sólo contar PNG si ese es el comportamiento actual.
- Mantener orden estable.
- No fallar si una carpeta no existe.
- No bloquear UI más de lo necesario.
- No acceder a widgets.
- No emitir mensajes Qt.
- No modificar `selected_folders`.

## Adaptación de UI

`MainWindow._update_folder_ui` debe pasar a:

```python
scan = self.folder_scanner.scan_folders(self.selected_folders, self.image_overrides)
self.batch_summary = BatchSummary(
    folders_count=scan.total_folders,
    images_count=scan.total_images,
    adjusted_count=scan.adjusted_images,
    destination_label=...
)
self._render_folder_ui(scan)
```

## Tests

Casos mínimos:

- lista vacía;
- carpeta inexistente;
- carpeta sin PNG;
- carpeta con PNG;
- varias carpetas;
- archivos no PNG ignorados;
- overrides locales detectados.

## Criterios de aceptación

- Añadir carpeta sigue funcionando.
- Limpiar carpeta sigue funcionando.
- Grid se sincroniza.
- El contador coincide con antes.
- `pytest` pasa.

---

# FASE 3 — Servicio de configuración de exportación

## Objetivo

Separar construcción, resumen y validación de `ExportConfig` de `MainWindow`.

Actualmente `_build_export_config_from_settings`, `_apply_export_preferences` y `_update_export_destination_label` viven en UI. Mantener la UI como consumidor, no como dueña de la configuración.

## Archivos nuevos

```text
src/flatshot/application/export_config_service.py
tests/test_export_config_service.py
```

## Servicio propuesto

```python
class ExportConfigService:
    def build_from_settings(self, app_settings: dict, destination_override: str | None = None) -> ExportConfig:
        ...

    def validate(self, config: ExportConfig) -> list[str]:
        ...

    def destinations_for_folders(self, folders: list[Path], config: ExportConfig) -> list[Path]:
        ...

    def summarize(self, config: ExportConfig) -> ExportConfigSummary:
        ...
```

## Validaciones mínimas

- Si destino es `custom`, debe haber `custom_output_path`.
- `output_width` y `output_height` deben ser positivos.
- `format` debe normalizarse a JPG/PNG.
- Si `transparent_bg=True`, formato debería ser PNG o al menos advertir.
- `output_folder_name` no debe estar vacío.
- `naming_template` debe ser válida o advertir.

## Adaptación de UI

- `ExportConfigDialog` puede seguir devolviendo `ExportConfig`.
- `MainWindow` usa el servicio para construir y validar.
- `_start_export` no debe contener validación de destino mezclada con manipulación visual.

## Criterios de aceptación

- Configuración de exportación funciona igual.
- Destino personalizado sigue funcionando.
- El resumen inferior se actualiza correctamente.
- Tests unitarios cubren validación.
- No se modifica el motor.

---

# FASE 4 — Desacoplar exportación: `ExportRunner`

## Objetivo

Sacar la lógica principal de exportación de `ExportWorker(QThread)` a una clase Python independiente.

Este es el punto más importante del desacoplamiento.

## Estado actual

`ExportWorker`:
- hereda de `QThread`;
- usa señales Qt;
- escanea o recibe snapshot de archivos;
- crea snapshots temporales;
- crea carpeta de salida;
- usa `ProcessPoolExecutor`;
- usa `RenderCache`;
- aplica `process_single_image`;
- emite progreso;
- controla stop/pause;
- emite resultado final.

La lógica debe moverse a un runner sin Qt.

## Archivos nuevos

```text
src/flatshot/application/export_runner.py
src/flatshot/application/execution_control.py
src/flatshot/application/events.py
tests/test_export_runner.py
```

## Arquitectura propuesta

```python
class ExportEventSink(Protocol):
    def emit(self, event: ExportEvent) -> None:
        ...

class ExportRunner:
    def __init__(
        self,
        event_sink: ExportEventSink | None = None,
        cancellation_token: CancellationToken | None = None,
        pause_token: PauseToken | None = None,
    ):
        ...

    def run(self, request: ExportJobRequest) -> ExportJobResult:
        ...
```

## Eventos

```python
ExportStartedEvent
ExportProgressEvent
ExportImageCompletedEvent
ExportWarningEvent
ExportErrorEvent
ExportFinishedEvent
ExportCancelledEvent
```

## Qué debe moverse desde `ExportWorker`

- Snapshot estable de archivos.
- Filtrado de PNG.
- Construcción de tareas.
- Validación/creación de carpeta destino.
- Uso de caché.
- Dispatch con `ProcessPoolExecutor`.
- Conteo de completadas/errores.
- Pausa/reanudación/cancelación.
- Limpieza de temporales.
- Cálculo de duración.
- Generación de `ExportJobResult`.

## Qué debe quedarse en `ExportWorker`

`ExportWorker` debe convertirse en adaptador Qt:

```python
class ExportWorker(QThread):
    progress_updated = pyqtSignal(int)
    log_updated = pyqtSignal(str)
    image_completed = pyqtSignal(str, bool)
    finished_process = pyqtSignal(bool, int, int, float)

    def run(self):
        runner = ExportRunner(event_sink=self._qt_event_sink, ...)
        result = runner.run(self.request)
        self.finished_process.emit(...)
```

## Reglas

- Mantener firma pública de `ExportWorker` si es posible para no romper `MainWindow`.
- Primero extraer internamente; después limpiar.
- No cambiar `process_single_image` salvo para moverlo si queda más limpio.
- No cambiar salida de archivos.
- No cambiar nombres generados.
- No cambiar calidad JPG/PNG.
- No cambiar cache key salvo que sea inevitable.

## Tests

Usar `tmp_path` con imágenes PNG pequeñas.

Casos:
- carpeta vacía;
- una imagen;
- varias imágenes;
- destino subfolder;
- destino custom;
- cancelación;
- pausa/reanudación si se puede testear sin flakiness;
- error al crear carpeta;
- naming template;
- uso de overrides locales.

## Criterios de aceptación

- La UI actual sigue exportando.
- CLI sigue funcionando.
- Tests pasan.
- `ExportRunner` no importa PyQt6.
- `ExportWorker` es adaptador.
- El comportamiento visual no necesita cambiar todavía.

## Riesgo

Alto. Hacer en commits pequeños.

---

# FASE 5 — Desacoplar cola: `QueueRunner`

## Objetivo

Sacar la lógica de `QueueWorker(QThread)` a una cola independiente de Qt.

## Archivos nuevos

```text
src/flatshot/application/queue_runner.py
tests/test_queue_runner.py
```

## Arquitectura propuesta

```python
class QueueRunner:
    def __init__(
        self,
        export_runner_factory: Callable[..., ExportRunner],
        event_sink: ExportEventSink | None = None,
        cancellation_token: CancellationToken | None = None,
        pause_token: PauseToken | None = None,
    ):
        ...

    def run(self, request: ExportJobRequest) -> QueueJobResult:
        ...
```

## Eventos de cola

```python
QueueStartedEvent
QueueJobStartedEvent
QueueJobProgressEvent
QueueJobCompletedEvent
QueueFinishedEvent
QueuePausedEvent
QueueResumedEvent
QueueCancelledEvent
```

## Qué debe quedarse en `QueueWorker`

`QueueWorker` debe ser adaptador Qt:
- recibe jobs;
- crea `QueueRunner`;
- traduce eventos a señales existentes;
- conserva API pública para `MainWindow`.

## Reglas

- Mantener secuencia de procesamiento por carpetas.
- Mantener pausa/reanudación.
- Mantener stop/cancel.
- Mantener logs equivalentes.
- No cambiar resultado final.

## Tests

- cola vacía;
- una carpeta;
- varias carpetas;
- carpeta vacía dentro de cola;
- error en una carpeta;
- cancelación;
- pausa/reanudación si es estable.

## Criterios de aceptación

- Procesamiento de varias carpetas funciona igual.
- Botones pausar/reanudar/detener siguen funcionando.
- `QueueRunner` no importa PyQt6.
- `QueueWorker` es wrapper.

---

# FASE 6 — Preview independiente de Qt

## Objetivo

Separar renderizado preview de la representación Qt.

Ahora la preview mezcla:
- `PIL`;
- `QImage`;
- `QPixmap`;
- widgets;
- timers;
- thread pool.

La lógica de render debe devolver datos neutros.

## Archivos nuevos

```text
src/flatshot/application/preview_service.py
tests/test_preview_service.py
```

## Servicio propuesto

```python
class PreviewService:
    def render_preview(self, request: PreviewRequest) -> PreviewResult:
        ...

    def render_tile_preview(self, request: PreviewRequest) -> TilePreviewResult:
        ...
```

## Resultado neutro

Opción A, RGB raw:

```python
@dataclass(frozen=True)
class PreviewResult:
    width: int
    height: int
    bytes_rgb: bytes
    warning: str | None
```

Opción B, imagen codificada:

```python
@dataclass(frozen=True)
class EncodedPreviewResult:
    mime_type: str
    data: bytes
    width: int
    height: int
```

Para futura web, la opción B es más directa. Para Qt, la opción A puede ser más eficiente.

Recomendación:
- Internamente usar RGB raw.
- Añadir helper opcional para codificar PNG/JPEG cuando haga falta.

## Adaptador Qt

```text
src/flatshot/adapters/qt/preview_adapter_qt.py
```

```python
def preview_result_to_qimage(result: PreviewResult) -> QImage:
    ...
```

## Reglas

- `PreviewService` no debe importar Qt.
- Mantener la calidad/escala actual de preview.
- Mantener warnings del motor.
- No bloquear la UI: Qt puede seguir usando `QRunnable` temporalmente, pero la tarea ejecutada debe llamar al servicio.

## Criterios de aceptación

- Preview central funciona.
- Grid funciona.
- No cambia el aspecto del render.
- `PreviewService` testeado con imágenes pequeñas.
- Codex documenta diferencias visuales si las hubiera.

---

# FASE 7 — Presets y configuración como servicios

## Objetivo

Separar acceso a presets/configuración de la UI.

## Archivos nuevos

```text
src/flatshot/application/preset_service.py
src/flatshot/application/settings_service.py
src/flatshot/application/session_service.py
tests/test_preset_service.py
tests/test_settings_service.py
```

## PresetService

Debe cubrir:
- cargar presets categorizados;
- migrar si procede;
- listar presets planos;
- guardar preset actual;
- crear;
- renombrar;
- eliminar;
- importar;
- exportar;
- devolver errores como excepciones o resultados, no como QMessageBox.

## SettingsService

Debe cubrir:
- cargar `settings.json`;
- normalizar defaults;
- guardar cambios;
- coalescing de escritura puede quedarse en UI o moverse a servicio con cuidado;
- validar forma de datos.

## SessionService

Debe cubrir:
- estado de ventana;
- carpetas recientes;
- preset activo;
- export config;
- splitter;
- ajustes de sombra;
- sin depender de widgets.

## Reglas

- Servicios no deben abrir diálogos.
- UI decide cómo preguntar al usuario.
- Servicio sólo ejecuta operación y devuelve resultado/error.

---

# FASE 8 — Sistema unificado de estado de aplicación

## Objetivo

Crear un estado legible que la UI pueda pintar sin recalcular todo.

## Archivo propuesto

```text
src/flatshot/application/app_state.py
```

## Estado conceptual

```python
@dataclass
class FlatshotAppState:
    batch: BatchState
    export: ExportState
    preview: PreviewState
    processing: ProcessingState
    selected_image: str | None
    active_preset: str | None
```

## Reglas

- No crear un framework de estado complejo.
- No usar Redux ni similares.
- Debe servir para centralizar lo que ahora está disperso.
- Debe permitir que `MainWindow` pregunte:
  - qué texto pintar;
  - qué botones habilitar;
  - qué progreso mostrar.

## Criterios de aceptación

- Menos lógica condicional dispersa en `MainWindow`.
- Estados vacíos/listo/procesando/pausado/error claros.
- No se rompe nada.

---

# FASE 9 — Adaptar UI PyQt a servicios

## Objetivo

Que PyQt consuma servicios, no lógica interna dispersa.

## Tareas

1. `MainWindow.__init__` debe crear servicios:

```python
self.folder_scanner = FolderScanner()
self.export_config_service = ExportConfigService()
self.preview_service = PreviewService()
self.preset_service = PresetService(...)
```

2. Métodos de UI deben delegar:
   - añadir carpeta → actualizar lista + llamar scanner;
   - configurar exportación → usar service;
   - iniciar exportación → crear request + lanzar adapter Qt;
   - preview → llamar preview service desde worker/thread;
   - grid → usar servicio de preview/tile.

3. Reducir tamaño de `MainWindow`.

4. Mantener callbacks existentes mientras se migra.

## Criterios de aceptación

- La UI actual sigue funcionando.
- La lógica funcional ya es accesible sin widgets.
- Se puede imaginar una API local usando servicios.
- Tests pasan.

---

# FASE 10 — API local experimental opcional

Esta fase no debe hacerse hasta que las anteriores estén estables.

## Objetivo

Demostrar que el núcleo ya no depende de PyQt y puede ser consumido por una futura UI web.

## Tecnología sugerida

FastAPI es razonable porque:
- usa Python;
- se integra bien con Pydantic;
- permite endpoints HTTP;
- permite WebSockets para eventos de progreso.

## Archivos propuestos

```text
src/flatshot/api/app.py
src/flatshot/api/routes_presets.py
src/flatshot/api/routes_batch.py
src/flatshot/api/routes_preview.py
src/flatshot/api/routes_export.py
src/flatshot/api/events.py
```

## Endpoints mínimos

```text
GET  /api/health
GET  /api/presets
POST /api/folders/scan
POST /api/preview/render
GET  /api/export/config
POST /api/export/config
POST /api/export/start
GET  /api/export/{job_id}
POST /api/export/{job_id}/pause
POST /api/export/{job_id}/resume
POST /api/export/{job_id}/cancel
WS   /api/export/{job_id}/events
```

## Reglas

- API sólo local en esta fase.
- No abrir puertos públicos.
- Bind por defecto a `127.0.0.1`.
- No aceptar rutas arbitrarias remotas.
- Validar rutas.
- No crear UI web todavía salvo smoke test mínimo.

## Criterio de aceptación

Desde una petición local se puede:
- listar presets;
- escanear una carpeta;
- generar una preview;
- lanzar exportación;
- recibir progreso.

---

## 6. Plan de tests

### 6.1. Tests unitarios

Añadir tests para:

```text
presenters
folder scanner
export config service
preset service
preview service
export runner
queue runner
naming
destination planning
state transitions
```

### 6.2. Tests de integración

Usar `tmp_path`:

- crear carpeta temporal con PNGs pequeños;
- aplicar exportación;
- comprobar número de salidas;
- comprobar nombres generados;
- comprobar destino subfolder;
- comprobar destino custom;
- comprobar errores controlados.

### 6.3. Tests de regresión visual funcional

No usar screenshots frágiles en esta fase.

Sí comprobar:
- dimensiones de imagen exportada;
- modo de color;
- presencia de fondo/transparencia;
- existencia de archivos;
- no corrupción;
- logs generados.

### 6.4. Tests manuales obligatorios

Al final de cada fase importante:

1. Abrir app.
2. Añadir carpeta.
3. Ver grid.
4. Seleccionar imagen.
5. Cambiar preset.
6. Mover sliders esenciales.
7. Aplicar ajuste local.
8. Abrir avanzado.
9. Cambiar configuración de exportación.
10. Exportar una carpeta.
11. Exportar varias carpetas.
12. Pausar/reanudar/detener.
13. Ver resultado.
14. Cerrar y reabrir.
15. Confirmar sesión restaurada.

---

## 7. Reglas operativas para Codex

### 7.1. Antes de cada tanda

Codex debe:

1. Leer este documento completo.
2. Revisar archivos afectados.
3. Indicar plan breve de cambios.
4. Ejecutar tests si procede.
5. Trabajar en una tanda limitada.
6. No mezclar fases.

### 7.2. Después de cada tanda

Codex debe informar:

```text
TANDA X completada
Archivos modificados
Cambios realizados
Cambios NO realizados
Tests ejecutados
Resultado de tests
Riesgos detectados
Siguiente tanda recomendada
```

### 7.3. Prohibiciones

Codex no debe:

- Reescribir toda la app de golpe.
- Eliminar PyQt.
- Cambiar el motor de sombras.
- Cambiar algoritmos de escala.
- Cambiar exportación sin test.
- Cambiar formato de presets sin migración.
- Introducir dependencias nuevas sin justificar.
- Inventar salida múltiple si no existe.
- Crear servidor API antes de desacoplar servicios.
- Mezclar rediseño visual con extracción de lógica.
- Dejar la app en estado no ejecutable.

### 7.4. Política de commits

Idealmente un commit por fase o subtarea:

```text
refactor: add batch presenters
refactor: extract folder scanner
refactor: extract export config service
refactor: introduce export runner
refactor: wrap export runner in qt worker
refactor: introduce queue runner
refactor: extract preview service
```

---

## 8. Prompt de arranque para Codex

Usar este prompt para iniciar el trabajo.

```md
Vamos a iniciar el desacoplamiento arquitectónico de FlatShot para poder modernizar la UI y, en el futuro, permitir una interfaz web/desktop basada en frontend moderno.

Lee primero `PLAN_DESACOPLAMIENTO_FLATSHOT_CODEX.md` completo.

Objetivo de esta primera tanda:
- No rediseñar la UI.
- No tocar `ShadowEngine`.
- No cambiar la lógica de exportación.
- No romper la app actual.
- Crear la base de presenters/helpers puros para estado visual:
  - resumen de lote;
  - resumen de exportación;
  - resumen de destino;
  - texto del botón de procesar;
  - estado básico de barra inferior.
- Añadir tests unitarios para esos helpers.
- Adaptar `MainWindow` mínimamente para usar esos helpers donde sea seguro.

Antes de modificar:
1. Revisa `src/flatshot/ui/main_window.py`.
2. Revisa `src/flatshot/core/models.py`.
3. Revisa `src/flatshot/ui/shell.py`.
4. Revisa `src/flatshot/ui/styles.py`.
5. Ejecuta `pytest` y anota el estado inicial.

Entrega:
- Archivos modificados.
- Tests añadidos.
- Resultado de `pytest`.
- Explicación de qué queda preparado para la siguiente fase.
```

---

## 9. Prompt para Fase 2

```md
Continúa el desacoplamiento de FlatShot siguiendo `PLAN_DESACOPLAMIENTO_FLATSHOT_CODEX.md`.

Objetivo de esta tanda:
Extraer el escaneo de carpetas desde `MainWindow._update_folder_ui` hacia un servicio puro `FolderScanner`.

Condiciones:
- No cambiar comportamiento visible.
- No tocar exportación.
- No tocar `ShadowEngine`.
- No tocar workers.
- Mantener PyQt funcionando.
- Añadir tests con `tmp_path`.

El servicio debe:
- aceptar lista de `Path`;
- contar PNG;
- ignorar no-PNG;
- detectar carpetas inexistentes;
- contar imágenes con ajuste local usando `override_key` y `has_image_override`;
- devolver un resultado estructurado.

Después adapta `MainWindow._update_folder_ui` para consumir ese resultado, manteniendo la sincronización actual del grid, watcher, batch summary y botón de procesar.

Entrega:
- Archivos modificados.
- Tests.
- Resultado de `pytest`.
- Riesgos o inconsistencias detectadas.
```

---

## 10. Prompt para Fase 4

```md
Continúa el desacoplamiento de FlatShot siguiendo `PLAN_DESACOPLAMIENTO_FLATSHOT_CODEX.md`.

Objetivo:
Extraer la lógica de exportación de `ExportWorker(QThread)` hacia un runner puro independiente de Qt: `ExportRunner`.

Condiciones:
- `ExportRunner` no debe importar PyQt6.
- `ExportWorker` debe seguir existiendo como adaptador Qt para no romper `MainWindow`.
- No cambiar output visual de imágenes.
- No cambiar naming.
- No cambiar caché salvo que sea imprescindible.
- No cambiar calidad de guardado JPG/PNG.
- No cambiar el comportamiento funcional actual.

Pasos:
1. Analiza `src/flatshot/workers/export_worker.py`.
2. Identifica bloques lógicos puros.
3. Crea contratos/eventos en `src/flatshot/application/`.
4. Implementa `ExportRunner`.
5. Modifica `ExportWorker` para delegar en `ExportRunner`.
6. Añade tests con carpetas temporales e imágenes PNG mínimas.
7. Ejecuta `pytest`.

Entrega:
- Archivos modificados.
- Qué lógica se movió.
- Qué quedó como adaptador Qt.
- Tests ejecutados.
- Resultado.
- Cualquier diferencia funcional detectada.
```

---

## 11. Prompt para Fase 6

```md
Continúa el desacoplamiento de FlatShot siguiendo `PLAN_DESACOPLAMIENTO_FLATSHOT_CODEX.md`.

Objetivo:
Extraer la generación de previews hacia un `PreviewService` independiente de Qt.

Condiciones:
- `PreviewService` no debe importar PyQt6.
- Debe usar `PIL`, `ShadowEngine`, `ShadowSettings`, `CurveData`.
- Debe devolver datos neutros: dimensiones, bytes RGB o imagen codificada, warning.
- La UI Qt debe convertir el resultado a `QImage`/`QPixmap` mediante un adaptador.
- No debe cambiar el aspecto de la preview salvo diferencias inevitables documentadas.
- No romper grid ni canvas.

Entrega:
- Servicio creado.
- Adaptador Qt creado.
- MainWindow/grid actualizados mínimamente.
- Tests añadidos.
- Resultado de `pytest`.
```

---

## 12. Checklist de preparación para UI web

FlatShot estará preparado para una UI web cuando se cumpla esto:

```text
[ ] Exportar no requiere MainWindow.
[ ] Exportar no requiere QThread directamente.
[ ] Cola no requiere QueueWorker directamente.
[ ] Preview no requiere QImage/QPixmap.
[ ] Escanear carpeta no requiere widgets.
[ ] Presets pueden gestionarse desde servicio.
[ ] Configuración puede gestionarse desde servicio.
[ ] Estado de progreso se emite como eventos neutros.
[ ] La CLI sigue funcionando.
[ ] La UI PyQt sigue funcionando.
[ ] Hay tests de servicios.
[ ] Hay una forma clara de lanzar operaciones desde una API local.
```

Si alguno de estos puntos falta, todavía no conviene iniciar React/Electron/Tauri.

---

## 13. Decisiones técnicas recomendadas

### 13.1. No eliminar PyQt todavía

PyQt debe seguir siendo la interfaz estable mientras se extraen servicios.

### 13.2. Mantener Pydantic

El proyecto ya usa Pydantic. Aprovechar `ExportConfig`, `ShadowSettings`, `CurveData` y `JobItem`.

### 13.3. Eventos neutrales

No usar señales Qt fuera de adaptadores.

### 13.4. Servicios pequeños

Evitar un `FlatShotService` gigante. Mejor servicios por caso de uso.

### 13.5. Compatibilidad antes que limpieza extrema

Si una extracción perfecta exige reescribir demasiado, hacer una extracción parcial segura.

### 13.6. Tests antes de mover workers

La extracción de exportación y cola necesita tests antes o durante el cambio.

---

## 14. Definición de terminado del desacoplamiento

El desacoplamiento se considera completado cuando:

1. `MainWindow` ya no contiene lógica sustancial de:
   - escaneo;
   - exportación;
   - cola;
   - configuración;
   - previews;
   - presets.

2. Los servicios principales no importan PyQt6.

3. `ExportWorker` y `QueueWorker` son adaptadores.

4. La UI PyQt sigue funcionando.

5. La CLI sigue funcionando.

6. Hay tests de:
   - scanner;
   - export config;
   - export runner;
   - queue runner;
   - preview service;
   - presenters.

7. Existe documentación de arquitectura.

8. Se puede crear una API local mínima sin tocar el motor.

---

## 15. Riesgos y mitigaciones

### Riesgo 1: romper exportación

Mitigación:
- extraer `ExportRunner` en paralelo;
- mantener `ExportWorker` como wrapper;
- tests con imágenes temporales;
- comparar archivos generados.

### Riesgo 2: romper previews

Mitigación:
- separar render de conversión Qt;
- comparar dimensiones y bytes básicos;
- probar canvas y grid manualmente.

### Riesgo 3: introducir duplicación

Mitigación:
- una vez validado servicio nuevo, eliminar duplicación antigua;
- no dejar dos fuentes de verdad.

### Riesgo 4: sobrediseñar arquitectura

Mitigación:
- servicios pequeños;
- no crear framework interno;
- no introducir DI container;
- no crear API hasta fases finales.

### Riesgo 5: Codex cambia demasiado de golpe

Mitigación:
- tandas cerradas;
- commits pequeños;
- tests tras cada tanda;
- rollback fácil.

---

## 16. Orden recomendado de ejecución

Orden estricto:

```text
0. Línea base
1. Presenters/helpers visuales
2. FolderScanner
3. ExportConfigService
4. ExportRunner
5. QueueRunner
6. PreviewService
7. Preset/Settings/Session services
8. Estado unificado
9. Adaptación progresiva de PyQt
10. API local experimental
```

No saltar a la fase 10 sin completar al menos 1-6.

---

## 17. Nota final para Codex

Este plan no busca “hacer la app web” todavía. Busca algo más importante: que FlatShot deje de depender de PyQt para existir como aplicación.

Una vez conseguido, el rediseño visual será mucho más seguro y se podrá decidir con criterio entre:

```text
PyQt modernizado
PySide/PyQt con UI reestructurada
Electron + frontend web
Tauri + frontend web
API local + React/Vue/Svelte
CLI ampliada
```

La prioridad de esta etapa es preservar lo que funciona y preparar el terreno para cambiar lo que no funciona: la arquitectura de interfaz.
