# Informe de estado de Flatshot

Fecha de auditoría: 2026-05-25  
Repositorio auditado: `C:\Users\cenfot01\Desktop\Proyectos\Herramientas_INSIDE\scripts_2025\flatshot`

## 1. Resumen ejecutivo

Flatshot no está en un único estado de producto: conviven una app PyQt6 real y bastante funcional, un prototipo web local con bridge HTTP parcialmente conectado, una CLI útil pero con fallos de salida en Windows, y documentación de varias fases que no siempre describe el estado actual.

Lo que funciona de verdad:

- El core de procesamiento/exportación existe y está probado: `src/flatshot/application/export_runner.py`, `src/flatshot/core/engine.py`, `src/flatshot/core/models.py`.
- La app PyQt6 arranca en smoke test headless y conserva el flujo real de lote, preview, presets, exportación, cola y workers: `src/flatshot/ui/main_window.py`.
- El bridge local HTTP arranca en `127.0.0.1`, escanea carpetas reales, renderiza preview y ejecuta exportación real: `src/flatshot/bridge/http_server.py`, `src/flatshot/bridge/service.py`, `src/flatshot/bridge/export_jobs.py`.
- Los tests automatizados actuales pasan: `python -m pytest -q` -> `283 passed in 13.98s`.
- La compilación sintáctica pasa: `python -m compileall -q src apps\flatshot-desktop` -> sin errores.

Lo incompleto o engañoso:

- Hay dos interfaces en paralelo. La PyQt parece la ruta productiva más completa. La web/bridge es prometedora, pero aún mezcla modo real, modo mock, estados de revisión y controles pendientes.
- La web se titula todavía `FlatShot Desktop Mock` en `apps/flatshot-desktop/frontend/index.html`, mientras el selector inicial observado en Playwright aparece en `Bridge local` con chip `Bridge pendiente`. Esto confunde el estado real del producto.
- En la web hay controles visuales que no ejecutan una lógica real completa: guardar preset en bridge, ajuste local real, abrir carpeta de salida, comparación/original para imágenes reales de bridge.
- La exportación real puede sobrescribir silenciosamente resultados cuando se exportan imágenes de varias carpetas con el mismo nombre a un destino común. Verificado con bridge real: dos entradas `same.png` en dos carpetas, destino custom único, resultado final `completed`, `errors: 0`, pero sólo quedó `same_PRO.png`.
- La CLI falla al imprimir caracteres Unicode en una consola Windows CP1252, incluso después de haber generado archivos correctamente.

Bloqueos del MVP:

- Decidir explícitamente qué interfaz es el MVP inmediato. Si el objetivo es entregar cuanto antes, la ruta más corta es estabilizar PyQt y congelar la web como prototipo. Si el objetivo es entregar la nueva interfaz web, hay P0 pendientes de producto, claridad y seguridad de exportación.
- Corregir protección de colisiones/sobrescritura en exportación multi-carpeta o limitar el MVP a una carpeta por ejecución.
- Eliminar o aislar los estados mock de la ruta principal para que el usuario no crea que algo visual es funcional.
- Aclarar el arranque y ejecución: PyQt, CLI, bridge y web tienen comandos distintos y documentación parcialmente contradictoria.

Sensación general del proyecto:

- El core ha avanzado más que la claridad de producto. Hay buenas separaciones recientes en `application`/`core`, tests sólidos y bridge real, pero el proyecto transmite lentitud porque se siguen acumulando capas de interfaz, revisión visual, modo mock y documentación histórica sin cerrar una experiencia principal.

Decisión estratégica recomendada:

- Para llegar antes a una versión funcional: declarar PyQt como MVP operativo, congelar rediseños y prototipo web salvo bugs P0, cerrar seguridad de exportación, revisar flujo principal y empaquetar/documentar una ruta de uso clara.
- Si se decide que el MVP debe ser la web, entonces no seguir puliendo visualmente: primero convertirla en una app real sin mock visible, con picker/bridge fiable, exportación segura, persistencia mínima y estados claros.

## 2. Estado actual verificable

### Mapa útil de estructura

```txt
.
├─ main.py
│  └─ Entrada ligera. Añade src al path y delega en flatshot.__main__.
├─ pyproject.toml
│  └─ Paquete Python flatshot 1.0.0. Define script flatshot=flatshot.__main__:main.
├─ requirements.txt
│  └─ Dependencias runtime principales: PyQt6, Pillow, numpy, pydantic, qtawesome.
├─ README.md
│  └─ Documentación de uso PyQt/CLI. Parcialmente desactualizada frente al estado web/bridge.
├─ src/flatshot
│  ├─ __main__.py
│  │  └─ Decide GUI vs CLI. GUI instala crash hook y lanza MainWindow.
│  ├─ cli.py
│  │  └─ CLI real, pero duplica parte del flujo y falla con Unicode en consola Windows CP1252.
│  ├─ core/
│  │  └─ Modelos, motor de sombra, escalado, presets base. Sin PyQt según tests de arquitectura.
│  ├─ application/
│  │  └─ Servicios Qt-free: scanner, preview, export config/planner/runner, cola, estado, presenters.
│  ├─ bridge/
│  │  └─ HTTP local 127.0.0.1 para web: scan, preview, presets, prepare/export/jobs.
│  ├─ ui/
│  │  └─ PyQt6 real. MainWindow concentra demasiadas responsabilidades.
│  ├─ workers/
│  │  └─ Adaptadores QThread/QObject para ExportRunner/QueueRunner.
│  └─ utils/
│     └─ Wrappers de configuración, logs e historial. Parte todavía Qt-dependent.
├─ apps/flatshot-desktop
│  ├─ frontend/
│  │  └─ Prototipo HTML/CSS/JS. Tiene UI real parcial, modo mock y bridge.
│  └─ bridge/
│     └─ Runner/dev docs para arrancar el bridge desde checkout.
├─ docs/
│  └─ Planes, revisiones y checklists. Útiles como contexto, no todos son fuente de verdad.
├─ tests/
│  └─ Suite amplia de arquitectura, servicios, bridge, exportación, UI helpers y workers.
├─ scripts/
│  └─ Herramientas auxiliares. No parecen ruta principal de usuario.
├─ assets/
│  └─ Recursos visuales.
└─ logs/, htmlcov/, .pytest_cache/, __pycache__/
   └─ Artefactos locales/generados. No deben ser fuente de producto.
```

### Tabla general

| Área | Estado | Evidencia | Riesgo | Prioridad |
|---|---|---|---|---|
| Stack principal | Real | `pyproject.toml`: Python >=3.10, PyQt6, Pillow, numpy, pydantic, qtawesome. | Bajo. Stack coherente para app local. | P2 |
| App PyQt6 | Real | `src/flatshot/__main__.py` lanza `MainWindow`; smoke headless creó ventana `FlatShot`. | La UI está concentrada en `main_window.py` de 3584 líneas. | P1 |
| Core procesamiento | Real | `src/flatshot/core/engine.py`, `src/flatshot/application/export_runner.py`; tests pasan. | Cambiarlo sin necesidad puede alterar output. | P0 mantener |
| Servicios Qt-free | Real | `src/flatshot/application/*`; `tests/test_architecture_boundaries.py` prohíbe PyQt en `application`/`core`. | Aún hay duplicación de reglas PNG/naming en varias capas. | P1 |
| Bridge HTTP local | Real parcial | `src/flatshot/bridge/http_server.py` expone `/health`, `/folders/scan`, `/preview/render`, `/exports/run`; export real verificada. | Prototipo dev; no empaquetado ni picker nativo Tauri. | P0 si MVP web |
| Frontend web | Parcial/mock | `apps/flatshot-desktop/frontend/app.js` mezcla estado real bridge y escenarios mock; `index.html` titula `FlatShot Desktop Mock`. | Confunde qué es producto y qué es demo. | P0 si MVP web |
| CLI | Parcial | `python -m flatshot --help` OK; `list-presets` falla con Unicode en CP1252; export real genera archivo pero termina con exit 1. | Automatizaciones reciben fallo aunque el archivo exista. | P1 |
| Tests | Real | `python -m pytest -q` -> `283 passed in 13.98s`. | No sustituyen prueba manual completa de UI. | P0 mantener |
| Build | No verificado / no disponible | `python -m build --sdist --wheel` -> `No module named build`. | No hay validación de paquete reproducible en entorno actual. | P1 |
| Lint/tipado | No disponible | Ruff/mypy no instalados/configurados. | Menor si tests cubren; mayor en JS web grande. | P2 |
| Documentación | Parcial/desactualizada | `docs/ESTADO_ACTUAL_FLATSHOT.md` habla de 196 tests; ahora hay 283. Web README contradice estado inicial observado. | Puede guiar mal a futuros agentes. | P1 |
| Seguridad de fuentes | Parcial | ExportRunner usa copias temporales y no muta inputs; scanner sólo lee. | Salidas sí pueden sobrescribirse sin aviso en ciertos casos. | P0 |

### Comandos de ejecución identificados

| Comando | Resultado verificado | Estado |
|---|---|---|
| `python main.py` | No ejecutado con UI visible; equivalente a `flatshot.__main__`. Smoke PyQt offscreen sí verificado. | No verificado visual |
| `python -m flatshot` | Código lanza GUI salvo CLI args. Smoke PyQt offscreen verificado mediante import/ventana. | Parcial |
| `flatshot` | Definido en `pyproject.toml`; no instalado como comando global en esta auditoría. | No verificado |
| `python -m flatshot --help` | Sale 0 y muestra comandos `list-presets` y `process`. | Real |
| `python -m flatshot list-presets` | Falla en CP1252 por emoji; funciona con `PYTHONUTF8=1`. | Roto parcial |
| `python -m flatshot process ...` | Dry-run OK; export real crea JPG pero puede terminar exit 1 por Unicode. | Parcial |
| `python apps/flatshot-desktop/bridge/run_bridge.py --port N` | Bridge real verificado. | Real |
| `python apps/flatshot-desktop/run_dev.py --bridge-port N --frontend-port M` | Arranca bridge y frontend; terminación no interactiva dejó hijos vivos. | Parcial |
| `python -m http.server` en frontend | Usado por `run_dev.py`. | Real dev |

### Comandos de test/validación identificados

| Comando | Resultado | Estado |
|---|---|---|
| `python -m pytest -q` | `283 passed in 13.98s`. | Real |
| `python -m compileall -q src apps\flatshot-desktop` | Sin errores. | Real |
| `python -m build --sdist --wheel` | Error: módulo `build` no instalado. | No disponible |
| Ruff/mypy | No instalados/configurados. | No disponible |
| Playwright UI web | Snapshot inicial obtenido; interacción por `run-code` falló por API CLI. | Parcial |

## 3. Qué está realmente implementado

### Funcionalidad real

| Funcionalidad | Estado | Evidencia | Problemas | Prioridad |
|---|---|---|---|---|
| Arranque PyQt | Real parcial | Smoke offscreen: ventana `FlatShot`, presets cargados, botón procesar deshabilitado en sesión limpia. Código: `src/flatshot/__main__.py`, `src/flatshot/ui/main_window.py`. | No se verificó interacción visible con file dialog real. | P1 |
| Core de sombra/procesamiento | Real | `src/flatshot/core/engine.py`; `ExportRunner.process_single_image()` abre RGBA, procesa, guarda JPG/PNG. Tests pasan. | No tocar sin golden/output checks. | P0 mantener |
| Escaneo de carpetas PNG | Real | `src/flatshot/application/folder_scanner.py`; bridge test: carpeta válida 3 imágenes, vacía 0, inválida error, mixta con omitted reasons. | Sólo PNG por diseño actual. Escaneo PyQt es síncrono. | P0 |
| Lectura/validación de PNG | Real | `FolderScanner._is_readable_png()` usa `Image.verify()`. Corrupta reportada como `read_error`. | Coste elevado en carpetas grandes. | P1 |
| Preview service | Real | `src/flatshot/application/preview_service.py`; bridge `/preview/render` devolvió 300x400 OK. | Preview web real no permite compare/original. | P1 |
| Exportación PyQt | Real por código/tests | `MainWindow._start_export()` usa `ExportWorker`/`QueueWorker`; `workers` delegan en `ExportRunner`/`QueueRunner`. | Smoke no ejecutó export visible. Pausa sólo está cableada para cola multi-carpeta. | P1 |
| Exportación bridge | Real | Proceso real `run_bridge.py`: `/exports/run` completó 2/2 y creó `producto_1_PRO.jpg`, `producto_2_PRO.jpg`. | Colisiones entre carpetas a destino común no se detectan. | P0 |
| Jobs/progreso bridge | Real | `src/flatshot/bridge/export_jobs.py`; polling devolvió `completed`, `errors: 0`, destinations. | Campos `processed/total` no son consistentes en todos los snapshots observados. | P1 |
| Configuración export | Real | `src/flatshot/application/export_config_service.py` valida formato, dimensiones, destino, naming. | No valida colisiones globales de múltiples carpetas en un destino compartido. | P0 |
| Presets base | Real | `PresetService`, `SettingsService`; `PYTHONUTF8=1 python -m flatshot list-presets` lista 2 presets. | CLI normal falla por Unicode. Web no guarda presets reales en bridge. | P1 |
| Persistencia PyQt | Real parcial | `SettingsService`, `SessionManager`; smoke con usuario normal restauró 1 carpeta y 52 imágenes. | Puede confundir pruebas si no se separa sesión limpia; no se verificó migración manual. | P2 |
| Pausa/cancelación export | Real parcial | `ExportRunner` y `QueueRunner` tienen tokens; bridge expone pause/resume/cancel; PyQt stop cableado. | PyQt pausa single-folder no está cableada en `_toggle_pause()`. | P1 |
| Tests arquitectura | Real | `tests/test_architecture_boundaries.py`, `tests/test_headless_imports.py`. | No cubren frontend JS/CSS. | P1 |

### Funcionalidad parcial

| Funcionalidad | Estado | Evidencia | Problemas | Prioridad |
|---|---|---|---|---|
| Web app con bridge | Parcial | `apps/flatshot-desktop/frontend/app.js` llama a `/folders/scan`, `/preview/render`, `/exports/run`. Bridge real verificado por HTTP. | Interacción UI web con carpeta no verificada por Playwright; picker es dev/tkinter; no Tauri. | P0 si MVP web |
| `run_dev.py` | Parcial | Test: health bridge y frontend OK; proceso no terminó limpiamente con `terminate()` y dejó hijos hasta `Stop-Process -Force`. | Ctrl+C interactivo no verificado. Riesgo en dev, no en usuario final si no se entrega así. | P2 |
| CLI export | Parcial | Dry-run OK; export crea archivo; exit 1 por Unicode en impresión final. | Devuelve fallo falso a scripts/usuarios. | P1 |
| Estados vacíos web | Parcial | Snapshot inicial muestra `0 imágenes`, `Sin carpeta`, `Selecciona una carpeta para empezar`. | Demasiados paneles visibles para un estado inicial; Debug/Revisión existen en flujo principal. | P1 |
| Estados error web | Parcial | Código `applyBridgeScanResult()`, `setBridgeErrorState()`, `renderErrors()`. | No se verificó visualmente con Playwright por fallo de automatización de run-code. | P1 |
| Galería/grid | Parcial | PyQt `GridPreviewWidget`; web `renderBatch()` y `.image-list`. | Sin virtualización; PyQt crea un tile por imagen; web renderiza todos los items filtrados. | P1 |
| Multi-carpeta | Parcial | PyQt `QueueRunner`; bridge agrupa por parent en `_export_requests()`. | Destino común con nombres iguales sobrescribe salida sin error. | P0 |
| Documentación de estado | Parcial | Varios MD; `docs/ESTADO_ACTUAL_FLATSHOT.md` obsoleto en número de tests. | No hay una fuente única actual. | P1 |

### Funcionalidad mock

| Funcionalidad | Estado | Evidencia | Problemas | Prioridad |
|---|---|---|---|---|
| Lotes mock web | Mock | `apps/flatshot-desktop/frontend/app.js` define `mockFolders`, `mockImages`, escenarios `export-completed`, `export-partial`, etc. | Puede ocultar que una ruta real no está conectada. | P0 si MVP web |
| Exportación mock web | Mock | `startExport()` usa `scheduleExportStep()` si no es bridge batch. | El usuario puede ver progreso/completado que no escribe archivos. | P0 si MVP web |
| Panel Revisión web | Mock/parcial | `index.html` contiene `details` Revisión y selector de escenarios; JS cambia estados visuales. | Útil para QA visual, ruido en MVP usuario. | P1 |
| Estados de demo | Mock | `scenarioLabels`, `setScenario()` en `app.js`. | Debe salir de la ruta principal o quedar sólo en modo dev. | P0 si MVP web |

### Funcionalidad visual sin lógica real completa

| Funcionalidad | Estado | Evidencia | Problemas | Prioridad |
|---|---|---|---|---|
| Guardar preset en web bridge | Visual/parcial | `renderSettings()` deshabilita o marca `Guardar pendiente`; `handleAction('save-preset')` en bridge sólo cambia estado. | Promete administración no implementada. | P1 |
| Ajuste local web | Visual/parcial | `handleAction('toggle-local-adjustment')` cambia `localOverride`; no hay persistencia ni aplicación clara en bridge export. | Puede hacer creer que una imagen tiene override real. | P1 |
| Abrir carpeta de salida web | Visual/parcial | `renderFooter()` oculta/deshabilita `open-output`; handler sólo dice `Destino visible en Salida`. | Acción esperada tras exportar no existe. | P2 |
| Comparar/original en preview web real | Visual/parcial | `renderPreview()` deshabilita controles cuando `isBridgeImage`. | Para imágenes reales sólo se ve preview procesada. | P1 |
| Título web | Visual engañoso | `index.html`: `<title>FlatShot Desktop Mock</title>`. | Comunica que la app no es real aunque el bridge sí lo sea. | P1 |

### Funcionalidad no verificada

| Funcionalidad | Estado | Evidencia | Problemas | Prioridad |
|---|---|---|---|---|
| Uso PyQt visible con diálogos reales | No verificado | Sólo smoke offscreen. | No se comprobó add-folder con ratón/teclado en ventana real. | P1 |
| Export PyQt visible de punta a punta | No verificado | Código y tests sí; ejecución manual UI no. | No se observó progress/reset visual final. | P1 |
| Permisos denegados reales | No verificado | Scanner captura `OSError`, pero no se creó carpeta sin permisos. | Caso importante en Windows/red. | P2 |
| Miles de imágenes | No verificado | Código muestra riesgos; no se probó dataset grande. | Puede bloquear UI/memoria. | P1 |
| Imágenes muy pesadas | No verificado | Export usa procesos; preview limita tamaño en bridge. | Riesgo de memoria. | P2 |
| Cancelación bajo carga real | No verificado | Tokens existen; no se probó lote largo. | Puede afectar confianza del usuario. | P1 |
| Empaquetado instalable | No verificado/no existente | No se encontró Tauri/package; `python -m build` no disponible. | Bloquea distribución si se requiere app final instalable. | P1 |

## 4. Flujo principal actual

### Trabajo real que Flatshot intenta resolver

Flatshot procesa lotes de imágenes de producto, actualmente centrado en PNG, para aplicar preset/ajustes de sombra/fondo/tamaño y exportar archivos finales sin modificar las fuentes.

### Flujo actual PyQt

```txt
1. Abrir app con python main.py o python -m flatshot.
2. La app restaura sesión anterior si existe.
3. Usuario añade una carpeta desde el panel inferior/controles.
4. MainWindow escanea carpetas con FolderScanner.
5. Se actualiza resumen de lote y grid.
6. Se selecciona una imagen y se genera preview en background.
7. Usuario elige preset y ajusta controles.
8. Usuario configura exportación en diálogo.
9. Usuario pulsa procesar.
10. ExportWorker o QueueWorker ejecuta ExportRunner fuera del UI thread.
11. La UI muestra progreso, logs, pausa/stop según modo.
12. Finaliza y resetea estado/progreso.
```

Dónde falla o se debilita:

- `src/flatshot/ui/main_window.py` concentra flujo, estado, layout, wiring y reglas. Esto ralentiza cambios.
- El escaneo de carpetas se ejecuta de forma síncrona en `_update_folder_ui()` con `FolderScanner.scan_folders(...)`; en carpetas grandes puede congelar la UI.
- La pausa de exportación en PyQt sólo actúa sobre `queue_worker`; para un `ExportWorker` single-folder hay método de pausa pero no está cableado en `_toggle_pause()`.
- Hay controles de mockup visibles en preview (`_create_preview_panel()` con botones Clara/Media/Oscura), útiles para pruebas pero ruidosos si el foco es producción.
- No se verificó manualmente el flujo visible completo en esta auditoría.

### Flujo actual web/bridge

```txt
1. Abrir frontend estático con run_dev.py o servidor HTTP.
2. La pantalla inicial muestra header, panel fuente, preview, ajustes, salida, barra inferior, Debug y Revisión.
3. El usuario puede estar en modo Mock o Bridge local.
4. En Bridge, comprueba health/capabilities/presets.
5. Selecciona carpeta vía picker dev o introduce ruta manual.
6. El frontend llama a /folders/scan.
7. Renderiza lista, resumen y selecciona primera imagen.
8. Llama a /preview/render para preview.
9. Exporta con /exports/run y hace polling de /exports/jobs/{id}.
10. Pausa/cancela mediante endpoints de job.
```

Dónde falla o se debilita:

- La app se titula `FlatShot Desktop Mock` y conserva paneles Debug/Revisión y escenarios mock.
- El estado inicial observado en Playwright muestra `Bridge local` seleccionado y chip `Bridge pendiente`, mientras la documentación del prototipo dice que el modo por defecto es Mock. Hay contradicción.
- Varias acciones visuales no tienen implementación real completa: guardar preset, ajuste local, abrir salida, compare/original en bridge.
- La interacción completa UI web no se pudo verificar por Playwright `run-code`; sí se verificó el bridge por HTTP.
- No hay empaquetado Tauri/Electron ni picker nativo. `nativeFolderPicker` aparece como `false` en `/capabilities`.

### Flujo CLI

```txt
1. python -m flatshot --help.
2. python -m flatshot list-presets.
3. python -m flatshot process --input CARPETA --output DESTINO --size 1800x2400 --format JPG.
```

Dónde falla:

- En consola Windows CP1252, `list-presets` falla al imprimir emoji.
- La exportación real puede crear el archivo y aun así terminar con exit 1 por imprimir `✓`.
- CLI no es la experiencia principal, pero sí afecta a automatización y confianza técnica.

## 5. Flujo mínimo recomendado para MVP

Para cerrar cuanto antes, el MVP debe eliminar ambigüedad. El flujo mínimo recomendado es:

```txt
1. Abrir Flatshot.
2. Seleccionar una carpeta local.
3. Ver claramente cuántos PNG válidos hay y qué se omitió.
4. Ver una galería navegable y una preview suficientemente grande de la imagen seleccionada.
5. Elegir preset y ajustar sólo controles esenciales.
6. Configurar salida mínima: destino, formato, tamaño, sufijo/nombre.
7. Validar que la exportación no sobrescribirá resultados sin aviso.
8. Procesar.
9. Ver progreso real con estado textual.
10. Finalizar con resumen: procesadas, errores, destino.
11. Poder corregir carpeta/destino y repetir.
```

Acciones siempre visibles:

- Seleccionar carpeta.
- Preset.
- Preview/imagen seleccionada.
- Resumen del lote.
- Destino/exportación.
- Procesar N imágenes.
- Estado/progreso sólo cuando haya trabajo real.

Acciones a ocultar o mover a modo dev/secundario:

- Selector Mock/Bridge.
- Carga de lote mock.
- Panel Revisión/escenarios.
- Debug/capabilities.
- Administración avanzada de presets.
- Parámetros avanzados de sombra.
- Comparación avanzada si no funciona con datos reales.
- Abrir salida si no está implementado.

Decisión práctica:

- MVP más rápido: PyQt como app funcional, con ajustes P0/P1 de seguridad y claridad.
- MVP web: requiere primero retirar mock de la ruta principal, cerrar bridge/picker/export seguro y documentar que PyQt queda legacy.

## 6. Bloqueos actuales

### Bloqueos técnicos

| Bloqueo | Evidencia | Por qué importa | Prioridad |
|---|---|---|---|
| Colisión silenciosa de salidas multi-carpeta en destino común | Bridge real: dos carpetas con `same.png`, destino custom único, job `completed`, `errors: 0`, sólo quedó `same_PRO.png`. Código: `BridgeService._export_requests()` crea requests por parent; `ExportRunner.validate_output_path_collisions()` valida por request. | Se pierden resultados exportados sin aviso. No muta fuentes, pero rompe confianza y conteo de salida. | P0 |
| Escaneo PyQt síncrono | `MainWindow._update_folder_ui()` llama `FolderScanner.scan_folders(...)` directamente. | Carpetas grandes pueden congelar la UI antes de llegar a exportar. | P1 |
| Web sin empaquetado/picker nativo | `apps/flatshot-desktop/README.md` indica no Tauri; `/capabilities` devuelve `nativeFolderPicker: false`. | Si se pretende entregar web como desktop, falta pieza de producto. | P0 si MVP web |
| CLI falla por Unicode | `python -m flatshot list-presets` -> `UnicodeEncodeError`; export real crea archivo pero exit 1 al imprimir check. | Daña automatización y percepción de robustez. | P1 |
| Build no disponible | `python -m build --sdist --wheel` -> `No module named build`. | No hay validación de distribución reproducible. | P1 |

### Bloqueos UX/UI

| Bloqueo | Evidencia | Por qué importa | Prioridad |
|---|---|---|---|
| Ambigüedad mock/real en web | `index.html` title `FlatShot Desktop Mock`; snapshot muestra `Bridge local` y `Bridge pendiente`; JS contiene escenarios mock. | El usuario no sabe si trabaja con archivos reales. | P0 si MVP web |
| Sobrecarga inicial web | Snapshot inicial muestra header, panel fuente, preview, ajustes, salida, bottom bar, Debug y Revisión. | Provoca la sensación de demasiada información antes de importar nada. | P1 |
| Acciones visuales no funcionales | Guardar preset pendiente, ajuste local no aplicado, abrir salida oculto/deshabilitado. | Rompe confianza y genera flujos muertos. | P1 |
| PyQt mantiene herramientas de mockup visibles | `MainWindow._create_preview_panel()` crea botones mockup Clara/Media/Oscura. | Distrae del flujo producción si no son parte del trabajo real. | P2 |

### Bloqueos de arquitectura

| Bloqueo | Evidencia | Por qué importa | Prioridad |
|---|---|---|---|
| `MainWindow` demasiado grande | `src/flatshot/ui/main_window.py`: 3584 líneas. | Cada cierre de flujo exige tocar un archivo de alto riesgo. | P1 |
| Frontend JS monolítico | `apps/flatshot-desktop/frontend/app.js`: 2473 líneas. | Mezcla estado, render, mock, bridge, export y handlers. | P1 si MVP web |
| CSS acumulado por capas | `apps/flatshot-desktop/frontend/styles.css`: 1915 líneas, con secciones de override/polish posteriores. | Aumenta coste de corregir layout sin regresiones. | P2 |
| Reglas PNG/listado duplicadas | `FolderScanner`, `GridPreviewWidget._load_images`, `ExportRunPlanner`, `QueueRunner` usan patrones `*.png` o sufijos propios. | Cambiar formatos o reglas de lote exige tocar varios puntos. | P2 |

### Bloqueos de producto

| Bloqueo | Evidencia | Por qué importa | Prioridad |
|---|---|---|---|
| No hay interfaz MVP declarada | Conviven PyQt, web prototype, CLI y docs de nueva app. | El equipo puede seguir puliendo pantallas parciales sin cerrar entrega. | P0 |
| Soporte de formatos no alineado con expectativas | Scanner sólo admite `.png`; user-facing puede esperar JPG/WEBP/TIFF. | Si el producto real requiere sólo PNG, debe comunicarse; si no, falta alcance. | P1 |
| Export final post-proceso incompleta en web | Abrir destino no implementado; resultado visible parcial. | El usuario necesita saber dónde quedó el trabajo. | P2 |

### Bloqueos de documentación

| Bloqueo | Evidencia | Por qué importa | Prioridad |
|---|---|---|---|
| Estado documentado obsoleto | `docs/ESTADO_ACTUAL_FLATSHOT.md` dice 196 tests; auditoría actual: 283. | Futuros agentes pueden trabajar con mapa incorrecto. | P1 |
| Web README contradice estado observado | README del prototipo habla de default mock; snapshot mostró Bridge local seleccionado. | Confunde validación y decisiones de producto. | P1 |
| Falta una fuente de verdad | Hay planes, checklists y revisiones con distinto propósito. | Se pierde tiempo reinterpretando prioridades. | P1 |

## 7. Auditoría UX/UI orientada a cierre

Esta auditoría no prioriza estética. Sólo se señalan problemas que impiden claridad, velocidad o uso real.

| Problema | Dónde ocurre | Qué ocurre | Consecuencia | Prioridad |
|---|---|---|---|---|
| El usuario no sabe si está en producto real o demo | Web: `index.html`, `app.js`, header Debug | Título `Mock`, selector Mock/Bridge, escenarios y bridge pendiente conviven. | Riesgo de procesar mentalmente estados simulados como reales. | P0 si MVP web |
| Demasiados paneles antes de importar | Web snapshot 1440x900 | Header, fuente, preview, ajustes, salida, barra inferior, Debug y Revisión aparecen desde estado vacío. | Sensación de exceso de información y falta de siguiente acción clara. | P1 |
| Estado vacío con controles activos de más | Web inicial | Se ven filtros, métricas, revisión y exportación aunque no hay carpeta. | El usuario debe distinguir qué sirve ahora y qué no. | P1 |
| Acciones primarias duplicadas o dispersas | Web header, panel fuente, footer | `Seleccionar carpeta` aparece como acción superior y en panel; footer oculta otra primary. | Jerarquía inconsistente. | P2 |
| Panel Debug demasiado cerca del flujo | Web header `details Debug` | Aunque sea colapsable, forma parte de la pantalla principal. | Parece herramienta interna, no producto final. | P1 |
| Panel Revisión/mock dentro del lote | Web `details Revisión` | Estados de QA visual se mezclan con lote real. | Mantiene la app en modo prototipo. | P1 |
| Preview real web pierde comparación | `renderPreview()` deshabilita compare si `isBridgeImage`. | Para datos reales no se puede comparar original/procesado desde la UI web. | Revisión visual menos confiable. | P1 |
| Galería puede no escalar | Web `renderBatch()` renderiza todos; PyQt crea todos los tiles. | Con muchos archivos, scroll y memoria pueden degradarse. | P1 |
| PyQt muestra herramientas de mockup | `MainWindow._create_preview_panel()` | Botones Clara/Media/Oscura compiten con flujo de lote/preset/export. | Ruido moderado si se entrega PyQt a usuarios finales. | P2 |
| Mensajes de estado sí existen, pero dispersos | PyQt presenters y web status/footer | Hay estados como `No hay PNG válidos`, `Procesando`, `Pausado`. | Base positiva; falta simplificar jerarquía. | P2 |

Correcciones UX que sí desbloquean MVP:

- Dejar una sola ruta principal visible: importar carpeta -> revisar -> exportar.
- Ocultar mock/debug/revisión fuera de modo desarrollo.
- Mostrar claramente `Modo real` o eliminar el selector si no es una opción de usuario.
- Bloquear exportación cuando exista riesgo de sobrescritura no confirmada.
- Convertir estados vacíos en una sola invitación clara, no en una pantalla llena de paneles inactivos.

Correcciones UX que pueden esperar:

- Sombras, bordes, microinteracciones, animaciones.
- Reordenaciones finas de espaciado.
- Iconografía secundaria.
- Personalización visual.

## 8. Auditoría técnica

### Arquitectura actual

La dirección arquitectónica reciente es correcta:

```txt
UI PyQt / frontend web
→ application/services
→ core processing/models
→ persistence/filesystem
```

Evidencia:

- `tests/test_architecture_boundaries.py` impide imports PyQt en `src/flatshot/application` y `src/flatshot/core`.
- `tests/test_headless_imports.py` valida que imports de application/core/bridge/CLI no carguen PyQt en casos clave.
- `PreviewService`, `FolderScanner`, `ExportConfigService`, `ExportRunPlanner`, `ExportRunner`, `QueueRunner` son servicios reutilizables o casi reutilizables.

La deuda no está tanto en el core como en las capas de interfaz y cierre de flujo.

### Archivos grandes o de alto riesgo

| Archivo | Tamaño observado | Riesgo | Prioridad |
|---|---:|---|---|
| `src/flatshot/ui/main_window.py` | 3584 líneas | God object de PyQt: layout, estado, scanning, preview, export, sesión, controles. | P1 |
| `apps/flatshot-desktop/frontend/app.js` | 2473 líneas | Mezcla estado, mock, bridge, render, export, handlers y QA visual. | P1 si MVP web |
| `apps/flatshot-desktop/frontend/styles.css` | 1915 líneas | CSS acumulado con overrides; difícil tocar sin regresión. | P2 |
| `src/flatshot/ui/dialogs.py` | 1107 líneas | Diálogos UI grandes; riesgo menor que MainWindow. | P2 |
| `src/flatshot/ui/widgets.py` | 1038 líneas | Widgets compartidos; revisar sólo si bloquean flujo. | P2 |
| `src/flatshot/application/export_runner.py` | 485 líneas | Core de exportación; funcional, tocar con tests. | P0 mantener |

### Deuda que bloquea el MVP

| Deuda | Evidencia | Impacto |
|---|---|---|
| Falta decisión de interfaz MVP | PyQt y web compiten por atención; docs hablan de nueva app en paralelo. | Sin decisión, se seguirá puliendo sin cerrar. |
| Colisiones de salida multi-carpeta | Test bridge real con dos `same.png` -> un único `same_PRO.png`, job completed. | Riesgo de pérdida silenciosa de resultados. |
| Mock mezclado con real en web | `app.js` escenarios mock + endpoints reales; `index.html` title Mock. | El usuario no distingue demo de operación real. |

### Deuda que puede causar bugs graves

| Deuda | Evidencia | Impacto |
|---|---|---|
| Sobrescritura de outputs existentes | `process_single_image()` guarda directamente en `output_path`; no hay confirmación global. | Puede reemplazar salidas previas. |
| Validación de colisiones por request, no por job global | `ExportRunner` valida dentro de una ejecución; bridge/queue ejecutan por carpeta. | Multi-carpeta a destino común no está protegido. |
| Carpetas grandes en UI | Escaneo PyQt síncrono; grids sin virtualización. | Congelación, memoria alta, mala UX. |
| CLI exit falso | UnicodeEncodeError tras exportar. | Scripts pueden reintentar o reportar error aunque haya archivos generados. |

### Deuda que dificulta iterar

| Deuda | Evidencia | Impacto |
|---|---|---|
| UI PyQt monolítica | `main_window.py` 3584 líneas. | Cada cambio P1/P2 cuesta más. |
| Frontend web monolítico | `app.js` 2473 líneas. | Separar mock/bridge será manual y arriesgado. |
| Documentos de fases mezclados | `docs/PLAN_*`, `ESTADO_*`, `CHECKLIST_*`, `REVISION_*`. | Futuros agentes repiten análisis. |
| Reglas de lote duplicadas | `*.png` repetido en scanner/grid/planner/queue/CLI. | Cambios de formatos o escaneo se dispersan. |

### Deuda aceptable temporalmente

- `MainWindow` grande si se congela PyQt y sólo se hacen fixes P0/P1 localizados.
- CSS web acumulado si la web queda fuera del MVP inmediato.
- Ausencia de lint si no se aumenta superficie de código y se mantiene pytest.
- Falta de soporte formatos no PNG si el MVP se declara explícitamente PNG-only.

### Deuda estética o menor

- Sombras, bordes, iconografía secundaria.
- Microcopy no crítica.
- Animaciones/transiciones.
- Ajustes de densidad visual que no afecten a flujo principal.

## 9. Robustez y casos límite

| Caso real | Estado | Evidencia | Imprescindible | Prioridad |
|---|---|---|---|---|
| Carpeta vacía | Implementado | Bridge `/folders/scan`: 0 imágenes, 0 errores. PyQt presenters tienen `No hay PNG válidos`. | Sí | P0 |
| Ruta inválida | Implementado | Bridge scan devolvió error `La carpeta no existe...`; `FolderScanner` maneja missing. CLI inválida exit 1 controlado. | Sí | P0 |
| Ruta no directorio | Implementado por código | `FolderScanner._scan_folder()` añade error `not_a_directory`. | Sí | P1 |
| Ruta sin permisos | No verificado | Código captura `OSError`, pero no se probó permiso denegado real. | Sí para robustez | P2 |
| Carpeta con cientos/miles | No verificado | PyQt/web crean listas completas; scanner verifica imágenes. | Sí para producción | P1 |
| Imágenes corruptas | Implementado | Bridge carpeta mixta: `read_error=1`; preview unsupported/corrupt se maneja por errores. | Sí | P1 |
| Formatos no soportados | Implementado como omitido | Bridge mixta: JPG/TXT `unsupported_extension`; scanner sólo `.png`. | Sí si PNG-only | P1 |
| Mezcla PNG/JPG/WEBP/TIFF | Parcial | Sólo PNG real; otros omitidos. No WEBP/TIFF probados, pero sufijo no `.png` cae como unsupported. | Depende alcance | P1 |
| Nombres raros | Parcial/no verificado | `ExportVariant` valida sufijo; naming no sanea `{original}` de forma global. | Sí | P2 |
| Duplicados mismo nombre en carpetas distintas | Roto para destino común | Test bridge real dejó un solo `same_PRO.png` sin error. | Sí | P0 |
| Imágenes muy pesadas | No verificado | Preview bridge limita `MAX_PREVIEW_SIDE=1200`; export usa procesos. | Sí | P2 |
| Fallo bridge | Parcial | Web tiene `setBridgeErrorState()` y status; no verificado visualmente. | Sí si MVP web | P1 |
| Bridge no iniciado | Parcial | Snapshot inicial: `Bridge pendiente`; código maneja health fail. | Sí si MVP web | P1 |
| Cambio mock/real | Parcial/riesgoso | `app.js` permite selector; no se verificó transición. | No debería ser usuario final | P0 si MVP web |
| Recarga app | Parcial | PyQt sesión real; web no tiene persistencia completa según docs. | Deseable | P2 |
| Cancelación proceso | Parcial | Tokens y endpoints existen; no se probó lote largo. | Sí | P1 |
| Reintento tras error | Parcial | Estados permiten volver a ready/blocked; no se verificó flujo completo. | Sí | P1 |
| Usuario se equivoca de carpeta | Parcial | Clear/add folder existen en PyQt/web; no se probó UI visible. | Sí | P1 |
| Volver atrás | Parcial | PyQt clear folders; web limpiar lote. | Sí | P1 |
| Ver todas las imágenes | Parcial | Grids muestran listas, pero sin virtualización; en web puede no escalar. | Sí | P1 |
| Entender qué se encontró y omitió | Implementado parcial | Bridge serializa `omittedByReason`; web summary muestra métricas. | Sí | P1 |

## 10. Rendimiento

### Riesgos actuales

| Riesgo | Evidencia | Clasificación | Recomendación mínima |
|---|---|---|---|
| Escaneo puede bloquear PyQt | `MainWindow._update_folder_ui()` llama scanner síncrono; scanner abre/verifica PNGs con Pillow. | Riesgo alto | Mover scan a worker o limitar/avisar en MVP si carpetas grandes no son alcance. |
| Grid PyQt crea demasiados widgets | `GridPreviewWidget._create_tiles_for_images()` crea tile por imagen; `_load_images()` lista todos los PNG. | Riesgo alto | Para MVP, fijar límite práctico/feedback; luego virtualizar o paginar. |
| Web renderiza todos los items | `renderBatch()` mapea todas las imágenes filtradas a HTML. | Riesgo alto si MVP web | Paginación/virtualización antes de prometer miles. |
| Preview thumbnails parciales | PyQt usa QThreadPool y chunks; mejor que carga directa. | Aceptable por ahora | Mantener; no rediseñar salvo bloqueo. |
| Export usa muchos procesos | `ExportRunner.run()` usa `max_workers=os.cpu_count()-1`; prueba mostró 23 núcleos. | Riesgo medio | Limitar configurable si hay memoria alta; no P0 salvo fallos reales. |
| Bridge preview limita tamaño | `MAX_PREVIEW_SIDE=1200`, default target 900. | Aceptable | Mantener. |
| Cancelación bajo carga | Tokens existen; no verificado. | Riesgo medio | Probar con lote largo antes de release. |
| `run_dev.py` deja hijos con terminate | Test no interactivo dejó bridge/http.server vivos. | Riesgo bajo para usuario final, medio para dev | Validar Ctrl+C o mejorar cleanup si se usa a diario. |

Conclusión rendimiento:

- El rendimiento de exportación parece diseñado para trabajo real.
- El mayor riesgo para MVP no es el motor, sino el escaneo/listado/render de muchas imágenes antes de exportar.
- No se debe invertir ahora en animaciones ni microinteracciones; primero límite, progreso o worker para operaciones largas.

## 11. Seguridad de archivos locales

### Protecciones existentes

- El scanner sólo lee archivos y no recorre subcarpetas por defecto: `FolderScanner._scan_folder()`.
- El bridge sólo permite host `127.0.0.1` o `localhost`: `src/flatshot/bridge/http_server.py`.
- El bridge rechaza formatos no PNG para preview/export: `BridgeService._preview_path()` y `_export_image_paths()`.
- `ExportRunner` puede copiar inputs a snapshot temporal antes de procesar; `BridgeService` y PyQt planifican `input_files`.
- `process_single_image()` abre la fuente y guarda en output path, no muta source.
- `copy_stable()` elimina el destino parcial si una copia temporal falla.

### Riesgos actuales

| Riesgo | Evidencia | Impacto | Prioridad |
|---|---|---|---|
| Sobrescritura silenciosa de outputs entre carpetas | Test bridge real con destino custom único y dos `same.png`: resultado `completed`, un archivo final. | Pérdida de resultados exportados. | P0 |
| Sobrescritura de outputs previos | `process_single_image()` guarda directamente si el path existe. | Puede reemplazar exportaciones anteriores. | P1 |
| Naming template puede generar paths problemáticos | `apply_naming_template()` sanitiza variante/bg, pero `{original}` y `{folder}` dependen de nombre fuente/carpeta; no se observó sanitización global final. | Riesgo con caracteres raros o separadores. | P2 |
| Destino custom multi-carpeta | `ExportConfigService.destinations_for_folders()` devuelve mismo custom para varias carpetas; validación global no detectada. | Colisiones entre carpetas. | P0 |
| Logs con rutas locales | Logs y bridge serializan rutas POSIX/locales. | Puede exponer rutas sensibles en logs/debug. | P2 |
| Operaciones destructivas | No se encontró borrado/movimiento de fuentes en rutas principales. | Bien; mantener. | P0 mantener |

Separación preview/ejecución:

- Existe separación técnica: preview usa `PreviewService`; export usa `ExportRunner`.
- En web, la separación visual se debilita por estados mock y controles pendientes. El usuario puede no saber cuándo se escribió algo real.

Protección mínima antes de MVP:

- Validar colisiones de salida para todo el job antes de escribir, incluyendo múltiples carpetas y destino custom.
- Avisar o bloquear si el destino ya contiene archivos que serán reemplazados.
- Mantener prohibición de mutar fuentes.

## 12. Documentación y contexto

### Documentos revisados

| Documento | Estado | Evidencia | Acción recomendada |
|---|---|---|---|
| `README.md` | Parcialmente útil | Describe PyQt/CLI y dependencias; no refleja bien web/bridge actual ni 283 tests. | Mantener como entrada de usuario, actualizar comandos reales y alcance. |
| `AGENTS.md` | Útil | Define invariantes, arquitectura, UX y reporting. | Mantener como normas de trabajo. |
| `docs/ESTADO_ACTUAL_FLATSHOT.md` | Obsoleto parcial | Dice 196 tests; auditoría actual 283. | Sustituir por este informe o marcar histórico. |
| `docs/PLAN_NUEVA_APP_FLATSHOT.md` | Útil como plan estratégico | Explica nueva app paralela y qué no hacer. | Mantener, pero añadir estado real y decisión MVP. |
| `docs/UX_NUEVA_APP_FLATSHOT.md` | Útil como objetivo UX | Define flujo y evita debug en principal. | Usar como guía si MVP web continúa. |
| `docs/CHECKLIST_REVISION_VISUAL_NUEVA_APP.md` | Checklist, no estado | Muchos ítems no marcados. | Mantener como QA, no como verdad de avance. |
| `docs/REVISION_PLAN_DESACOPLAMIENTO_FLATSHOT.md` | Auditoría histórica | Contiene observaciones ya parcialmente superadas. | Marcar histórica; no usar como estado actual sin contrastar. |
| `docs/decoupling_notes.md` | Histórico | Registra fases y tests antiguos. | Mantener como changelog técnico, no como roadmap. |
| `apps/flatshot-desktop/README.md` | Parcial/desactualizado | Dice prototipo y default mock; UI observada inicia en bridge local pendiente. | Actualizar si web sigue. |
| `apps/flatshot-desktop/bridge/README.md` | Bastante útil | Endpoints y limitaciones bridge. | Mantener, actualizar estado de export/queue si cambia. |

### Contradicciones relevantes

- `docs/ESTADO_ACTUAL_FLATSHOT.md`: `196 tests passed`; auditoría actual: `283 passed`.
- `apps/flatshot-desktop/README.md`: describe modo mock por defecto; snapshot Playwright mostró `Bridge local` seleccionado.
- `index.html`: título `FlatShot Desktop Mock`, pero bridge y exportación real ya existen.
- Algunos documentos empujan nueva app; PyQt sigue siendo la ruta más completa y funcional.

### Fuente de verdad recomendada

Crear o consolidar un documento único:

```txt
docs/ESTADO_PRODUCTO_FLATSHOT.md
```

Contenido mínimo:

- Interfaz MVP decidida: PyQt o web.
- Flujo principal soportado.
- Alcance explícito: PNG-only o formatos futuros.
- Comandos oficiales: ejecutar, testear, bridge/dev, empaquetar si existe.
- Matriz real/mock/parcial.
- P0/P1 abiertos.
- Qué no tocar hasta cerrar MVP.

Este informe puede ser la base inicial de esa fuente de verdad.

## 13. Priorización

| Prioridad | Tarea | Motivo | Impacto | Esfuerzo | Riesgo | Dependencias |
|---|---|---|---|---|---|---|
| P0 | Decidir interfaz MVP inmediata: PyQt funcional o web/bridge | Sin decisión se duplican esfuerzos y se siguen puliendo prototipos. | Cierra foco de producto. | Bajo | Alto si se evita | Dirección producto |
| P0 | Bloquear o resolver colisiones de salida multi-carpeta/destino común | Verificado: dos `same.png` en carpetas distintas dejaron un único output sin error. | Evita pérdida silenciosa de resultados. | Medio | Medio por output behavior | Tests de export/naming |
| P0 | Si MVP web: retirar mock/debug/revisión de la ruta principal | El usuario no sabe qué es real. | Convierte prototipo en app operable. | Medio | Medio | Decisión MVP web |
| P0 | Si MVP web: cerrar picker/bridge real y estado inicial | `nativeFolderPicker=false`; title Mock; bridge pendiente. | Permite importar carpeta real sin herramientas dev visibles. | Medio/alto | Medio | Shell desktop o decisión dev-only |
| P0 | Mantener invariantes de output al tocar export | AGENTS: no cambiar apariencia ni comportamiento de salida sin pedirlo. | Evita regresión crítica. | Continuo | Alto | Tests/goldens |
| P1 | Probar manualmente flujo PyQt visible completo | Sólo smoke offscreen verificado. | Confirma app usable de punta a punta. | Bajo/medio | Bajo | Entorno con GUI |
| P1 | Arreglar CLI Unicode en Windows | CLI falla incluso tras exportar. | Evita falsos negativos en scripts. | Bajo | Bajo | Ninguna |
| P1 | Añadir validación de sobrescritura de outputs existentes | No hay confirmación de reemplazo de salidas previas. | Protege trabajo generado. | Medio | Medio | Política producto |
| P1 | Reducir sobrecarga inicial web si sigue | Demasiados paneles y estados. | Mejora claridad inmediata. | Medio | Bajo | Decisión MVP web |
| P1 | Sacar escaneo PyQt pesado del hilo UI o limitar alcance | Escaneo con `Image.verify()` puede bloquear. | Evita congelación con carpetas grandes. | Medio | Medio | Tests UI/worker |
| P1 | Documentar comandos oficiales y estado real | Docs contradictorias. | Reduce pérdida de tiempo. | Bajo | Bajo | Decisión MVP |
| P1 | Validar cancel/pause con lote real | Tokens existen, no verificado bajo carga. | Confianza en operaciones largas. | Bajo/medio | Bajo | Dataset prueba |
| P2 | Centralizar reglas de formatos soportados | `*.png` repetido en varias capas. | Reduce errores futuros. | Medio | Bajo | No antes de P0 |
| P2 | Virtualizar/paginar grids si se prometen miles | PyQt/web crean todos los items. | Escala mejor. | Medio/alto | Medio | Métrica objetivo |
| P2 | Limpiar CSS/JS web por módulos | Web monolítica. | Iteración más segura. | Medio | Medio | Sólo si MVP web |
| P2 | Actualizar docs históricas o archivarlas | Hay planes/checklists obsoletos. | Menos confusión. | Bajo | Bajo | Fuente de verdad |
| P3 | Ajustes de espaciado, sombras, iconos | No bloquean uso real. | Pulido. | Variable | Bajo | Después MVP |
| P3 | Animaciones/transiciones | Estético. | Sensación producto. | Bajo/medio | Bajo | Después MVP |
| No hacer ahora | Rediseño visual total | Dispersa y no arregla output/flujo. | Retrasa entrega. | Alto | Alto | Ninguna |
| No hacer ahora | Reescritura completa de PyQt o web | El core ya funciona; falta cierre. | Riesgo masivo. | Alto | Alto | Ninguna |
| No hacer ahora | Añadir formatos nuevos antes de cerrar PNG MVP | Puede tocar procesamiento/output. | Amplía alcance. | Medio/alto | Alto | Decisión producto |
| No hacer ahora | Preferencias avanzadas/personalización visual | No desbloquea flujo. | Ruido. | Medio | Bajo | Después MVP |
| No hacer ahora | Nuevos paneles de métricas o automatización | Añade superficie sin cerrar operación básica. | Dispersión. | Medio | Medio | Después MVP |

## 14. Plan de ejecución recomendado

### Fase 1 — Estabilizar MVP funcional

Objetivo: que la app sirva para completar el flujo principal de principio a fin.

Tareas:

- Declarar MVP inmediato: PyQt o web/bridge.
- Corregir o bloquear colisiones de salida para multi-carpeta/destino común.
- Validar que no se sobrescriben outputs existentes sin decisión explícita.
- Ejecutar prueba manual del flujo elegido: abrir, seleccionar carpeta, ver lote, preview, preset, configurar destino, procesar, ver resultado.
- Si se elige web: ocultar mock/debug/revisión del flujo principal y asegurar que el estado inicial no diga `Mock`.
- Si se elige PyQt: no tocar el layout salvo elementos que bloqueen claridad; confirmar pausa/stop/progreso.
- Arreglar CLI Unicode si la CLI se mantiene documentada.

Criterios de finalización:

- Un usuario puede procesar una carpeta real sin entender conceptos internos.
- Los archivos fuente no se modifican.
- La app bloquea o avisa ante colisiones/sobrescrituras de salida.
- El progreso corresponde a trabajo real.
- Tests pasan.
- Manual check documentado.

Qué NO tocar en esta fase:

- Rediseño visual completo.
- Nuevos formatos de entrada.
- Nueva arquitectura de frontend.
- Preferencias avanzadas.
- Pulido de sombras/bordes.

### Fase 2 — Reducir fricción UX/UI

Objetivo: que la app sea clara, directa y no abrume.

Tareas:

- Simplificar pantalla inicial: una acción primaria clara para importar carpeta.
- De-emphasize u ocultar paneles avanzados hasta que haya lote.
- Mantener visibles preset, preview, lote, exportación y procesar.
- Revisar textos de error para carpeta vacía, ruta inválida, corruptas y unsupported.
- En web, mover Debug/Revisión a modo dev real o quitarlos de usuario.
- En PyQt, reducir prominencia de mockups si no son parte de producción.

Criterios de finalización:

- En estado vacío se entiende el siguiente paso en menos de 5 segundos.
- Con lote cargado se ve qué se procesará, dónde se guardará y si está listo.
- No hay botones visibles que no hagan nada útil.

Qué NO tocar:

- Motor de imagen.
- Naming/output salvo validaciones ya definidas.
- Animaciones y microinteracciones.

### Fase 3 — Robustez y casos reales

Objetivo: que soporte errores, carpetas grandes y uso no ideal.

Tareas:

- Probar carpeta sin permisos, corruptas múltiples, nombres raros y carpetas grandes.
- Medir escaneo y grid con 500/1000 imágenes.
- Mover escaneo pesado a worker si se confirma bloqueo.
- Probar cancelación y pausa con export larga.
- Añadir límites/feedback si se mantiene sin virtualización.
- Consolidar reglas de formatos soportados.

Criterios de finalización:

- La app no se congela de forma inaceptable en el tamaño objetivo.
- Los errores se muestran con acción recuperable.
- Cancelar no deja fuentes tocadas ni outputs corruptos.
- Las reglas PNG-only están claras o ampliadas con tests.

Qué NO tocar:

- Reescritura total de UI.
- Añadir shell nuevo.
- Personalización avanzada.

### Fase 4 — Pulido visual y refinamiento

Objetivo: mejorar la sensación de producto sin retrasar la funcionalidad.

Tareas:

- Ajustar densidad visual y jerarquía.
- Unificar microcopy.
- Revisar iconografía accesible.
- Afinar estados de progreso y resultados.
- Limpiar CSS/JS o extraer módulos si web sigue siendo producto.
- Extraer partes de `MainWindow` sólo donde reduzca riesgo real.

Criterios de finalización:

- La app se siente compacta, profesional y estable.
- Los cambios no alteran output.
- No hay estados visuales muertos.

Qué NO tocar:

- Cambios de motor.
- Nuevos conceptos de producto.
- Automatizaciones futuras.

## 15. Definición de MVP

### Imprescindible

- Una única interfaz declarada como MVP.
- La app abre de forma fiable en el entorno objetivo.
- El usuario puede seleccionar una carpeta local.
- Se detectan PNG válidos.
- Carpeta vacía y ruta inválida tienen mensajes claros.
- Se ve una lista/galería suficiente de imágenes.
- Se ve preview de la imagen seleccionada.
- Se puede elegir preset y usar controles esenciales.
- Se puede configurar destino/formato/tamaño/naming mínimo.
- La app valida colisiones y sobrescrituras de salida antes de escribir.
- Se puede procesar el lote completo.
- Hay progreso real con etiqueta textual.
- Hay resumen final con destino, procesadas y errores.
- No se modifican, borran ni mueven imágenes fuente.
- Tests automatizados pasan.
- Hay al menos una prueba manual documentada de flujo completo.

### Deseable

- Pausa/resume verificados con lote real.
- Cancelación verificada con lote largo.
- Abrir carpeta de salida tras exportar.
- Persistencia de última sesión/destino controlada.
- Mejor feedback para omitted files.
- Soporte aceptable para cientos de imágenes.
- CLI sin errores Unicode.

### Fuera de alcance por ahora

- Rediseño visual total.
- Nuevos formatos de entrada más allá de PNG.
- Edición avanzada de presets.
- Personalización visual.
- Métricas avanzadas.
- Automatizaciones futuras.
- Migrar de PyQt a web si no se elige como MVP.
- Reescritura del motor o del pipeline de imagen.

## 16. Riesgos de seguir como hasta ahora

Si se siguen acumulando rediseños, paneles, microcambios y refactors sin cerrar flujo funcional:

- La app seguirá pareciendo más avanzada de lo que está, porque algunos estados visuales son mock o parciales.
- El equipo seguirá gastando tiempo en discutir apariencia mientras persisten riesgos P0 como sobrescritura silenciosa de salidas.
- La documentación se volverá menos fiable y cada agente necesitará re-auditar.
- PyQt y web competirán por recursos sin que ninguna quede claramente entregable.
- Los usuarios encontrarán botones que no hacen nada útil o estados que no corresponden a archivos reales.
- Los cambios visuales aumentarán el riesgo de regresiones en una UI ya grande sin solucionar seguridad de archivos.
- Se retrasará la decisión más importante: cerrar un flujo real, simple y verificable.

## 17. Recomendación final

Primero:

- Declarar el MVP inmediato. Recomendación pragmática: PyQt como MVP funcional más rápido, web/bridge congelado como prototipo salvo correcciones P0 si se decide lo contrario.
- Corregir o bloquear la colisión de salidas multi-carpeta/destino común.
- Verificar manualmente el flujo completo elegido con una carpeta real.
- Documentar el comando oficial de ejecución y el alcance PNG-only.

Después:

- Reducir fricción visible: ocultar mock/debug/revisión de la ruta principal, simplificar estado vacío y eliminar botones sin acción real.
- Probar carpetas grandes, cancelación y errores reales.
- Actualizar documentación para que este informe o `docs/ESTADO_PRODUCTO_FLATSHOT.md` sea la fuente de verdad.

Congelar:

- Cambios estéticos no críticos.
- Nuevos formatos.
- Administración avanzada de presets.
- Reescrituras amplias.
- Nuevos paneles o preferencias.

Evitar:

- Tocar el motor de imagen sin tests de output.
- Seguir desarrollando PyQt y web con la misma prioridad.
- Mantener modo mock visible en una build que se quiera llamar funcional.
- Aceptar exportaciones que puedan sobrescribir resultados sin aviso.

Conclusión directa: Flatshot tiene base técnica suficiente para cerrar una versión funcional, pero no necesita más capas visuales ahora. Necesita decisión de producto, protección de salida, verificación manual del flujo elegido y limpieza de mock/acciones parciales en la interfaz que se vaya a entregar.
