# Bridge FlatShot Desktop

Bridge local minimo para conectar el prototipo moderno con servicios Python reutilizables.

Estado actual:

- servidor HTTP local de desarrollo;
- bind por defecto a `127.0.0.1`;
- implementado con stdlib, sin dependencias nuevas;
- sin PyQt;
- preview real por endpoint JSON;
- presets reales de solo lectura con settings serializables;
- exportacion real con jobs locales en memoria;
- progreso real consultable por polling;
- sin Tauri.

## Como arrancar

Opcion recomendada para revision visual completa:

```bash
python apps/flatshot-desktop/run_dev.py --open
```

Ese comando arranca este bridge y el frontend estatico, comprueba `/health` y muestra las URLs.

Para arrancar solo el bridge manualmente:

Desde la raiz del repositorio:

```bash
python apps/flatshot-desktop/bridge/run_bridge.py --host 127.0.0.1 --port 8765
```

Alternativa si el paquete esta en `PYTHONPATH`:

```bash
python -m flatshot.bridge.http_server --host 127.0.0.1 --port 8765
```

## Endpoints

### `GET /health`

Real. Comprueba que el bridge responde.

```json
{
  "ok": true,
  "service": "flatshot-bridge",
  "mode": "development"
}
```

Prueba rapida:

```bash
python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8765/health').read().decode())"
```

### `GET /app-info`

Real. Devuelve informacion basica de FlatShot, version de bridge y tipo de UI.

### `GET /capabilities`

Real. Declara lo disponible en APP.7:

- `folderScan`: `true`;
- `presetsRead`: `true`;
- `previewRender`: `true`;
- `exportRun`: `true`;
- `exportProgress`: `true`;
- `nativeFolderPicker`: `false`.

### `GET /presets`

Real de solo lectura. Lee presets sin escribir configuracion:

- si existe `presets_v2.json`, lee categorias reales;
- si existe solo `presets.json`, lo lee sin migrar ni escribir;
- si no existe config, devuelve presets por defecto del servicio.

No permite crear, editar, borrar ni guardar presets.

Response:

```json
{
  "items": [
    {
      "name": "Luz cenital",
      "categoryId": "ropa_clara",
      "category": "Ropa Clara",
      "settings": {
        "angle": 180,
        "distance": 25,
        "blur": 30,
        "spread": 0,
        "fusion": 1,
        "opacity": 20,
        "noise": 2,
        "padding": 10,
        "contact_blur": 10,
        "contraction": 0,
        "adaptive_zoom": true,
        "scale_adjustment": 0,
        "shadow_engine": "realistic_v2",
        "transparent_bg": false,
        "bg_color": [230, 230, 230]
      }
    }
  ],
  "source": "defaults"
}
```

### `POST /folders/scan`

Real. Escanea carpetas usando `flatshot.application.folder_scanner.FolderScanner`.

Request:

```json
{
  "folders": ["C:/ruta/a/carpeta"]
}
```

Response:

```json
{
  "folders": [
    {
      "path": "C:/ruta/a/carpeta",
      "exists": true,
      "isDir": true,
      "images": [
        {
          "path": "C:/ruta/a/carpeta/imagen.png",
          "name": "imagen.png",
          "stem": "imagen",
          "suffix": ".png",
          "sizeBytes": 123456,
          "hasLocalOverride": false
        }
      ],
      "filesFound": 42,
      "validImages": 28,
      "omittedCount": 14,
      "omitted": [
        {
          "path": "C:/ruta/a/carpeta/foto.jpg",
          "name": "foto.jpg",
          "suffix": ".jpg",
          "reason": "unsupported_extension",
          "detail": "Extensión no admitida: .jpg"
        }
      ],
      "errors": []
    }
  ],
  "totalFolders": 1,
  "totalImages": 28,
  "totalFiles": 42,
  "totalOmitted": 14,
  "omittedByReason": {
    "unsupported_extension": 8,
    "read_error": 3,
    "subfolder_not_scanned": 3
  },
  "adjustedImages": 0,
  "errors": []
}
```

Prueba rapida con PowerShell:

```powershell
$body = @{ folders = @("C:/ruta/a/carpeta") } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8765/folders/scan -ContentType "application/json" -Body $body
```

### `POST /folders/pick`

Real de desarrollo. Abre un selector local de carpeta desde el proceso Python del bridge usando stdlib (`tkinter`).

Request:

```json
{
  "initialPath": "C:/ruta/opcional"
}
```

Response con carpeta seleccionada:

```json
{
  "ok": true,
  "selected": true,
  "path": "C:/ruta/a/carpeta"
}
```

Response si se cancela:

```json
{
  "ok": true,
  "selected": false,
  "path": null
}
```

Notas:

- no escanea ni modifica archivos por si mismo;
- la UI llama despues a `/folders/scan`;
- no sustituye al selector nativo Tauri futuro;
- si `tkinter` no esta disponible, devuelve error JSON controlado.

### `POST /preview/render`

Real. Genera una preview con `flatshot.application.preview_service.PreviewService`.

Request:

```json
{
  "imagePath": "C:/ruta/a/carpeta/imagen.png",
  "targetWidth": 675,
  "targetHeight": 900,
  "settings": {
    "presetName": "Luz cenital",
    "angle": 180,
    "opacity": 20,
    "blur": 30,
    "distance": 25,
    "spread": 0,
    "fusion": 1,
    "noise": 2,
    "padding": 10,
    "contact_blur": 10,
    "contraction": 0,
    "adaptive_zoom": true,
    "scale_adjustment": 0,
    "shadow_engine": "realistic_v2",
    "bgColor": [230, 230, 230],
    "transparentBg": false
  }
}
```

Response:

```json
{
  "ok": true,
  "image": {
    "mimeType": "image/png",
    "dataBase64": "...",
    "width": 675,
    "height": 900
  },
  "source": {
    "path": "C:/ruta/a/carpeta/imagen.png",
    "name": "imagen.png"
  },
  "warning": null,
  "renderTimeMs": 123
}
```

Notas:

- sólo soporta PNG en esta fase;
- no modifica archivos;
- no escribe configuracion;
- limita cada lado de preview a 1200 px;
- los presets y ajustes principales/avanzados se envian como settings reales de `ShadowSettings`;
- `presetName` se conserva como contexto para UI/contrato, pero el render usa el objeto `settings`.

### `POST /exports/prepare`

Real. Valida y resume una exportacion sin escribir archivos.

Request:

```json
{
  "imagePaths": ["C:/ruta/a/carpeta/imagen.png"],
  "presetName": "Luz cenital",
  "settings": {
    "opacity": 20,
    "blur": 30,
    "distance": 25,
    "padding": 10,
    "shadow_engine": "realistic_v2"
  },
  "export": {
    "format": "JPG",
    "size": "1800x2400",
    "background": "rgb230",
    "destinationMode": "source",
    "destinationValue": "_SALIDA_PRO",
    "namingTemplate": "{original}{suffix}",
    "suffix": "_PRO"
  }
}
```

Response:

```json
{
  "ok": true,
  "sourceImages": 1,
  "totalOutputs": 1,
  "destinations": ["C:/ruta/a/carpeta/_SALIDA_PRO"],
  "activeVariants": [
    {
      "id": "web_rgb230",
      "label": "Web RGB230",
      "format": "JPG",
      "suffix": "_PRO"
    }
  ],
  "errors": []
}
```

### `POST /exports/run`

Real. Lanza una exportacion en segundo plano usando `flatshot.application.export_runner.ExportRunner`.

Devuelve `202` con el estado inicial del job:

```json
{
  "ok": true,
  "jobId": "abc123",
  "status": "running",
  "sourceImages": 1,
  "totalOutputs": 1,
  "progress": {
    "processed": 0,
    "total": 1,
    "percent": 0
  },
  "destinations": ["C:/ruta/a/carpeta/_SALIDA_PRO"]
}
```

Notas:

- solo acepta PNG en esta fase;
- no borra ni mueve fuentes;
- respeta `ExportRunner`, naming, sufijos, formatos, calidad y dimensiones existentes;
- escribe en `_SALIDA_PRO` por defecto o en el destino personalizado indicado;
- los jobs viven en memoria del proceso bridge de desarrollo.

### `GET /exports/jobs/{jobId}`

Real. Devuelve progreso y resultado del job.

Estados posibles:

- `queued`;
- `running`;
- `paused`;
- `cancelling`;
- `completed`;
- `partial`;
- `failed`;
- `cancelled`.

Respuesta resumida:

```json
{
  "ok": true,
  "jobId": "abc123",
  "status": "completed",
  "progress": {
    "processed": 1,
    "total": 1,
    "percent": 100
  },
  "completedItems": [
    {
      "name": "imagen_PRO.jpg",
      "success": true
    }
  ],
  "issues": [],
  "destinations": ["C:/ruta/a/carpeta/_SALIDA_PRO"],
  "result": {
    "success": true,
    "processed": 1,
    "total": 1,
    "errors": 0,
    "durationMs": 230,
    "destinations": ["C:/ruta/a/carpeta/_SALIDA_PRO"]
  }
}
```

`issues` contiene errores/avisos estructurados derivados de eventos del runner. No incluye tracebacks brutos.

### `POST /exports/jobs/{jobId}/pause`

Real. Pausa el job usando `PauseToken`.

### `POST /exports/jobs/{jobId}/resume`

Real. Reanuda el job pausado.

### `POST /exports/jobs/{jobId}/cancel`

Real. Solicita cancelacion usando `CancellationToken`.

## Errores JSON

Las rutas desconocidas, metodos incorrectos e inputs invalidos devuelven errores controlados:

```json
{
  "ok": false,
  "error": {
    "code": "invalid_request",
    "message": "Field 'folders' must be a list of paths."
  }
}
```

No se devuelve traceback bruto en JSON.

## Seguridad de APP.7

- No ejecuta comandos arbitrarios.
- No borra, mueve ni modifica imagenes.
- No escribe configuracion.
- No guarda ni edita presets.
- El selector de carpeta solo devuelve una ruta seleccionada por el usuario.
- Expone preview de lectura para rutas solicitadas por la UI.
- Expone exportacion solo para rutas de imagen solicitadas por la UI.
- La exportacion usa `ExportRunner`; no reimplementa motor ni naming en el bridge.
- El servidor rechaza binds distintos de `127.0.0.1` o `localhost` desde el CLI.
- CORS esta limitado a origenes locales de desarrollo del prototipo.

## No implementado todavia

- Tauri;
- selector nativo Tauri de carpetas;
- cola;
- apertura real de carpeta de salida;
- empaquetado Windows.
- guardado/edicion real de presets.
