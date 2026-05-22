# FlatShot Desktop

Prototipo navegable de la nueva app moderna de FlatShot.

Estado actual:

- APP.3.5 completada como entorno local de revision visual.
- Frontend estático en HTML/CSS/JS vanilla.
- Sin `package.json`, Tauri, Rust, Node obligatorio ni dependencias nuevas.
- Bridge HTTP local de desarrollo en Python.
- Escaneo real de carpetas por ruta manual usando servicios existentes.
- Lectura real/parcial de presets desde el servicio Python.
- La app PyQt legacy sigue intacta.

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

### Probar modo mock

1. Abrir `http://127.0.0.1:4173`.
2. Mantener `Modo` en `Mock`.
3. Usar el selector `Demo` o el panel `Revisión visual`.
4. Recorrer estados: sin lote, lote listo, preview loading/error, exportacion lista, en curso, completada y con errores.

La franja superior indica:

- modo activo;
- estado del bridge;
- URL configurada;
- ultima respuesta o estado mock.

### Probar bridge local

1. Arrancar con `python apps/flatshot-desktop/run_dev.py --open`.
2. Cambiar `Modo` a `Bridge local`.
3. Confirmar URL `http://127.0.0.1:8765`.
4. Pulsar `Comprobar bridge`.
5. Verificar `Bridge: Conectado` y `Última respuesta: health OK`.
6. Escribir una ruta real en `Ruta carpeta`.
7. Pulsar `Escanear ruta`.

Esto llama a:

- `GET /health`;
- `GET /capabilities`;
- `GET /presets`;
- `POST /folders/scan`.

El listado de imagenes puede venir de una carpeta real. La preview, ajustes y exportacion siguen siendo simulados.

### Feedback visual recomendado

Revisar especialmente:

- jerarquia entre lote, preview y ajustes;
- claridad del modo `Mock` frente a `Bridge local`;
- estados vacios, loading y error;
- si la preview mantiene protagonismo;
- si exportacion se entiende de un vistazo;
- textos largos o redundantes;
- controles que parezcan reales pero sigan siendo mock.

## Estados mock incluidos

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
- abrir destino simulado.

## Qué no está conectado

Todavía no existe:

- Tauri;
- selector nativo de carpetas;
- preview real;
- exportación real;
- progreso real;
- presets editables;
- configuración persistente completa;
- apertura real de carpeta de salida.

El frontend no procesa imágenes ni duplica lógica del motor.

## Modo mock

El modo por defecto es `Mock`. Permite validar la UX sin backend:

- estados de lote;
- preview simulada;
- presets mock;
- exportación simulada;
- errores y resultados simulados.

El selector `Demo` sigue disponible para recorrer los estados principales.

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

1. Cambiar `Modo` a `Bridge local`.
2. Mantener `Bridge` como `http://127.0.0.1:8765`.
3. Pulsar `Comprobar bridge`.
4. Escribir una ruta real en `Ruta carpeta`.
5. Pulsar `Escanear ruta`.

Esto llama a:

- `GET /health`;
- `GET /capabilities`;
- `GET /presets`;
- `POST /folders/scan`.

El listado de imágenes puede venir de una carpeta real. La preview, ajustes y exportación siguen siendo simulados.

## Siguiente paso

APP.4 — Escaneo real de carpetas en la nueva UI.

La siguiente tanda debe sustituir el input manual temporal por un flujo de escaneo más integrado en la nueva UI, manteniendo todavía fuera Tauri y exportación real.
