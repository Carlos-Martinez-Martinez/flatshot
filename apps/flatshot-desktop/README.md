# FlatShot Desktop

Interfaz web/bridge de FlatShot para el MVP actual. La ruta normal de usuario trabaja con carpetas reales mediante el bridge local; el mock queda reservado para desarrollo explícito con `?dev=1`.

Estado actual:

- MVP web/bridge decidido para la fase de cierre P0/P1.
- APP.7 completada como exportación real con progreso por bridge local.
- Validación previa de salidas para bloquear colisiones internas y archivos ya existentes antes de escribir.
- Saneamiento UX/UI de pantalla principal aplicado antes de conectar exportación real.
- Frontend estático en HTML/CSS/JS vanilla.
- Sin `package.json`, Tauri, Rust, Node obligatorio ni dependencias nuevas.
- Bridge HTTP local de desarrollo en Python.
- Escaneo real de carpetas por ruta manual usando servicios existentes.
- Selector local de carpeta para desarrollo usando el bridge Python.
- Diagnóstico de escaneo: archivos encontrados, imágenes válidas y omitidas.
- Preview real de PNG seleccionados usando `PreviewService`.
- Lectura real de presets desde el servicio Python.
- Presets y ajustes principales/avanzados aplicados a la preview real.
- Exportación real usando `ExportRunner`, sin cambiar naming ni output.
- La app PyQt legacy sigue intacta.

## Rediseño UX/UI 2026-05-25

Se consolidó la pantalla principal como shell de producción: topbar de estado/CTA, navegador de lote, visor central dominante, panel contextual `Ajustes`/`Salida` y status bar siempre visible. El cambio es de interfaz; no modifica el bridge, el runner de exportación ni el pipeline de imagen.

Para revisar:

- arrancar con `python apps/flatshot-desktop/run_dev.py --open`;
- probar sin lote, carpeta vacía, carpeta con PNG, búsqueda/filtros, selección de imagen, fondos de preview, sliders básicos, `Avanzado`, `Salida` y exportación temporal;
- comprobar que no hay scroll global, que los paneles laterales usan scroll interno y que el CTA superior refleja `Exportar N`, `Nuevo lote` o bloqueo de preflight.

## Probar visualmente la nueva app

### Requisitos

- Python disponible en consola.
- Dependencias del proyecto instaladas como para ejecutar `pytest`.
- Navegador local.

No hace falta instalar Node, Tauri, Rust ni Electron para revisar este prototipo.

### Arrancar entorno completo

Desde la raiz del repositorio:

```bash
python apps/flatshot-desktop/run_dev.py --open
```

Esto arranca:

- bridge Python: `http://127.0.0.1:8765`;
- frontend estatico: `http://127.0.0.1:4173`;
- navegador, si se usa `--open`.

Para detener todo:

```text
Ctrl+C
```

Opciones utiles:

```bash
python apps/flatshot-desktop/run_dev.py
python apps/flatshot-desktop/run_dev.py --bridge-port 8765 --frontend-port 4173
python apps/flatshot-desktop/run_dev.py --no-bridge
```

En Windows tambien existe:

```bat
apps\flatshot-desktop\run_dev.bat
```

Si un puerto esta ocupado, el script lo indica y no arranca servidores a medias.

### Abrir manualmente

Si prefieres levantar solo el frontend:

Opción directa:

```text
apps/flatshot-desktop/frontend/index.html
```

Opción recomendada para revisar en navegador:

```bash
python -m http.server 4173 --bind 127.0.0.1 --directory apps/flatshot-desktop/frontend
```

Abrir:

```text
http://127.0.0.1:4173
```

### Herramientas de desarrollo mock

El modo mock ya no aparece en la ruta normal. Para revisar estados visuales:

1. Abrir `http://127.0.0.1:4173?dev=1`.
2. Abrir `Debug`.
3. Cambiar `Modo` a `Mock` si hace falta.
4. Usar el selector `Demo` o el panel `Revisión`.

`Debug` muestra:

- modo activo;
- estado del bridge;
- URL configurada;
- ultima respuesta o estado mock.

### Probar bridge local

1. Arrancar con `python apps/flatshot-desktop/run_dev.py --open`.
2. Usar `Seleccionar carpeta`.
3. Como alternativa, abrir `Ruta manual`, escribir una ruta real y pulsar `Escanear`.
4. Revisar lote, preview, ajustes y salida.
5. Pulsar `Exportar N` cuando la salida esté lista.

Esto llama a:

- `GET /health`, si se comprueba desde modo desarrollo;
- `GET /capabilities`;
- `GET /presets`;
- `POST /folders/pick`, si usas `Seleccionar carpeta`;
- `POST /folders/scan`.
- `POST /preview/render`.
- `POST /exports/run` y `GET /exports/jobs/{jobId}` al exportar.

El panel de lote se actualiza con carpetas, imagenes, contadores y errores reales del bridge. La preview real se genera en Python al seleccionar imagen. Los presets reales actualizan la preview. La exportacion se ejecuta con el runner Python existente.

## Probar APP.4 — Escaneo real de carpetas

1. Arrancar la app:

   ```bash
   python apps/flatshot-desktop/run_dev.py --open
   ```

2. Abrir `http://127.0.0.1:4173` si el navegador no se abre solo.
3. Pulsar `Seleccionar carpeta` o pegar en `Ruta manual` una carpeta real con PNG.
4. Si pegaste la ruta manualmente, pulsar `Escanear`.

Debe verse:

- `Origen: Bridge local`;
- contador de carpetas e imagenes reales;
- diagnóstico de archivos válidos y omitidos;
- lista de carpetas con estado;
- lista de imagenes devuelta por `/folders/scan`;
- primera imagen seleccionada automaticamente;
- preview central con imagen real o estado de carga;
- ruta de la imagen seleccionada;
- salida disponible en la pestaña `Salida`.

Para probar carpeta vacia:

1. Pegar una carpeta existente sin PNG.
2. Pulsar `Escanear`.
3. Revisar `No se encontraron PNG` y contador `0 PNG`.

Para probar ruta invalida:

1. Pegar una ruta que no exista, por ejemplo `C:/flatshot/ruta-inexistente`.
2. Pulsar `Escanear`.
3. Revisar `Carpeta no encontrada` o el error controlado del bridge.

Para probar varias carpetas, separarlas con `;` en `Ruta manual`.

Para usar mock de desarrollo:

1. Abrir `http://127.0.0.1:4173?dev=1`.
2. Abrir `Debug` y cambiar `Modo` a `Mock`, o usar el selector `Demo`.
2. Pulsar `Lote mock` o elegir un escenario de `Revisión`.

Sigue sin conectarse:

- selector nativo Tauri de carpetas;
- apertura real de carpeta de salida desde shell nativo.

## Revisión visual APP.4.5

Arrancar:

```bash
python apps/flatshot-desktop/run_dev.py --open
```

Revisar:

- sin scroll horizontal;
- sin scroll vertical global;
- paneles laterales con scroll propio;
- barra inferior siempre visible;
- bridge legible;
- controles de revisión ocultos en modo normal;
- escaneo real visible en el flujo principal;
- preview real clara;
- exportación real disponible desde `Salida`.

## Probar APP.5 — Preview real

1. Arrancar la app:

   ```bash
   python apps/flatshot-desktop/run_dev.py --open
   ```

2. Pulsar `Seleccionar carpeta` o pegar una carpeta real con PNG en `Ruta manual`.
3. Si usaste ruta manual, pulsar `Escanear`.
4. Seleccionar una imagen del lote.
5. Esperar `Generando preview`.

Debe verse:

- imagen real en el panel central;
- metadatos de dimensiones y tiempo de render;
- `Preview real` o `Preview real con aviso`;
- salida marcada como pendiente.

Para reconocer errores:

- un PNG corrupto o ilegible muestra `Preview no disponible`;
- una ruta de preview no soportada devuelve error controlado desde el bridge;
- no aparece traceback en la UI.

Sigue sin conectarse:

- selector nativo Tauri de carpetas;
- comparación/original de preview real;
- apertura real de carpeta de salida desde shell nativo.

## Revisión UX/UI pantalla principal

La pantalla principal queda organizada en:

- header compacto con lote, estado simple y acción principal;
- rail izquierdo de lote con miniaturas y diagnóstico;
- visor central dominante con imagen completa por defecto;
- inspector derecho con pestañas `Ajustes` y `Salida`;
- barra inferior mínima con contexto del lote.

El modo normal oculta:

- URL del bridge;
- capabilities;
- última respuesta técnica;
- selector Mock/Bridge;
- controles de revisión.

Todo eso queda detrás de `Debug`.

El escaneo informa:

- archivos encontrados;
- imágenes PNG válidas;
- archivos omitidos;
- motivo de omisión: extensión no admitida, error de lectura o subcarpeta no escaneada.

La preview usa modo `Ajustar` por defecto para que la imagen completa sea visible sin tocar zoom.

El rediseño profundo de la pantalla principal refuerza estas decisiones:

- el visor ocupa el espacio central y mantiene `contain` por defecto;
- los controles de error simulado y escenarios quedan en `Revisión` o `Debug`;
- el footer se reduce a contexto mínimo y deja la acción principal arriba o en `Salida`;
- los filtros muestran un vacío contextual, por ejemplo `No hay imágenes con errores` y `Ver todas`;
- `Avisos`, `Errores`, `Omitidas` y `Válidas` se comunican por separado;
- la navegación `‹ Imagen n de m ›` permite revisar sin perder foco visual.

## Probar APP.6 — Presets y ajustes reales

1. Arrancar la app:

   ```bash
   python apps/flatshot-desktop/run_dev.py --open
   ```

2. Escanear una carpeta real con PNG.
3. Revisar el panel `Preset`.
4. Seleccionar `Luz cenital` o `Estándar oscuro`.
5. Seleccionar una imagen.
6. Cambiar opacidad, blur, distancia o padding.
7. Abrir `Avanzado` y cambiar ruido, contacto, escala o motor.

Debe verse:

- presets reales cargados desde `/presets`;
- etiqueta `Defaults`, `Config` o `Config legacy` bajo el preset activo;
- sliders actualizados al cambiar de preset;
- preview real regenerada al cambiar preset o ajuste;
- `Sin guardar` al modificar un ajuste;
- `Reset` vuelve al preset activo;
- `Guardar preset` no aparece en la ruta normal porque el guardado real queda fuera del MVP.

Sigue sin conectarse:

- guardado/edición real de presets;
- ajustes por imagen reales;
- apertura real de carpeta de salida desde shell nativo.

## Probar APP.7 — Exportación real y progreso

1. Arrancar la app:

   ```bash
   python apps/flatshot-desktop/run_dev.py --open
   ```

2. Escanear una carpeta real con PNG.
4. Abrir la pestaña `Salida`.
5. Revisar formato, tamaño, destino y naming.
6. Pulsar `Exportar lote`.
7. Esperar progreso en la barra inferior.

Debe verse:

- botón principal `Exportar N`;
- estado `Preparando exportación` y luego `Procesando x/y`;
- barra de progreso real;
- `Exportación completada` al terminar;
- archivos generados en `_SALIDA_PRO` o en el destino configurado;
- errores parciales si el runner devuelve fallos.
- bloqueo claro si hay salidas repetidas o archivos ya existentes en destino.

Notas:

- el bridge usa `ExportRunner`;
- no se modifica el motor de exportación;
- no se cambia naming, formato, calidad ni comportamiento de salida;
- no se sobrescriben salidas existentes ni colisiones internas sin bloquear primero;
- `Pausar`, `Reanudar` y `Detener` llaman al job local del bridge;
- la ruta de destino se muestra en `Salida`; abrir la carpeta sigue pendiente de integración nativa Tauri.

## Probar APP.8 — Errores y resultados

1. Arrancar la app:

   ```bash
   python apps/flatshot-desktop/run_dev.py --open
   ```

2. Escanear una carpeta real con PNG.
4. Abrir `Salida` y pulsar `Exportar lote`.
5. Revisar el bloque de resultado bajo el resumen de salida.

Debe verse:

- estado final `Exportación completada`, `Completada con avisos` o `Exportación fallida`;
- contador de archivos procesados;
- destino generado o destino configurado;
- últimos archivos procesados;
- errores o avisos estructurados cuando existan;
- miniaturas marcadas como `Exportada` o `Error` si el bridge informa resultado por imagen.

Para probar errores controlados:

- dejar `Destino` como `Carpeta personalizada` sin ruta debe bloquear exportación con `Destino sin configurar`;
- detener un job en curso debe mostrar estado de fallo/cancelación sin traceback;
- un fallo del runner se muestra en `Salida` y en `Revisar errores`.

No hay apertura nativa de carpeta de salida todavía. La ruta queda visible para revisión.

### Feedback visual recomendado

Revisar especialmente:

- jerarquia entre lote, preview y ajustes;
- claridad de la ruta real web/bridge;
- estados vacios, loading y error;
- si la preview mantiene protagonismo;
- si exportacion se entiende de un vistazo;
- textos largos o redundantes;
- controles que parezcan reales pero sigan siendo mock.

## Estados mock incluidos en modo desarrollo

Disponible sólo abriendo:

```text
http://127.0.0.1:4173?dev=1
```

El selector `Demo` permite recorrer sin editar código:

- sin lote;
- lote listo;
- carpeta sin PNG válidos;
- preview cargando;
- preview con aviso;
- error de preview;
- destino sin configurar;
- exportación lista;
- exportación en curso;
- exportación completada;
- exportación completada con errores parciales;
- exportación fallida.

También hay interacciones simuladas para:

- añadir y limpiar lote;
- buscar y filtrar imágenes;
- seleccionar imagen;
- cambiar modo de preview;
- cambiar fondo y zoom;
- cambiar preset;
- modificar ajustes principales;
- abrir ajustes avanzados;
- alternar ajuste por imagen;
- cambiar formato, tamaño, fondo, destino y naming;
- iniciar, pausar, reanudar y detener exportación mock;
- revisar errores;
- ver resultado y destino de exportación.

## Qué no está conectado

Todavía no existe:

- Tauri;
- selector nativo Tauri de carpetas;
- presets editables/guardables;
- configuración persistente completa;
- apertura real de carpeta de salida.

El frontend no procesa imágenes ni duplica lógica del motor.

## Modo mock

El modo mock no es el modo por defecto. Permite validar la UX sin backend sólo en modo desarrollo:

- estados de lote;
- preview simulada;
- presets mock;
- exportación simulada;
- errores y resultados simulados.

El selector `Demo` sigue disponible con `?dev=1`.

## Modo bridge local

El modo bridge tambien puede arrancarse manualmente si no usas `run_dev.py`.

Arrancar primero el bridge:

```bash
python apps/flatshot-desktop/bridge/run_bridge.py --host 127.0.0.1 --port 8765
```

Abrir el prototipo:

```bash
python -m http.server 4173 --bind 127.0.0.1 --directory apps/flatshot-desktop/frontend
```

En la UI:

1. Pulsar `Seleccionar carpeta` o escribir una ruta real en `Ruta manual`.
2. Si escribiste la ruta manualmente, pulsar `Escanear`.

Esto llama a:

- `GET /health`;
- `GET /capabilities`;
- `GET /presets`;
- `POST /folders/pick`, si usas selector local;
- `POST /folders/scan`.
- `POST /preview/render`.
- `POST /exports/run` y `GET /exports/jobs/{jobId}`.

El listado de imágenes puede venir de una carpeta real. La preview se genera con Python. Presets y ajustes de sombra se envían como settings reales al bridge. La exportación se lanza por bridge con progreso consultable.

## Siguiente paso

APP.9 — Paridad funcional básica con app legacy.

La siguiente tanda debe revisar paridad funcional básica frente a la app legacy sin eliminarla ni cambiar el output de imágenes.
