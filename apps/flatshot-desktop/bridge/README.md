# Bridge FlatShot Desktop

Bridge local minimo de APP.3 para conectar el prototipo moderno con servicios Python reutilizables.

Estado actual:

- servidor HTTP local de desarrollo;
- bind por defecto a `127.0.0.1`;
- implementado con stdlib, sin dependencias nuevas;
- sin PyQt;
- sin preview real;
- sin exportacion real;
- sin Tauri.

## Como arrancar

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

Real. Declara lo disponible en APP.3:

- `folderScan`: `true`;
- `presetsRead`: `true`;
- `previewRender`: `false`;
- `exportRun`: `false`;
- `exportProgress`: `false`;
- `nativeFolderPicker`: `false`.

### `GET /presets`

Parcial real. Lee presets sin escribir configuracion:

- si existe `presets_v2.json`, lee categorias reales;
- si existe solo `presets.json`, lo lee sin migrar ni escribir;
- si no existe config, devuelve presets por defecto del servicio.

No permite crear, editar, borrar ni guardar presets.

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
      "errors": []
    }
  ],
  "totalFolders": 1,
  "totalImages": 1,
  "adjustedImages": 0,
  "errors": []
}
```

Prueba rapida con PowerShell:

```powershell
$body = @{ folders = @("C:/ruta/a/carpeta") } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8765/folders/scan -ContentType "application/json" -Body $body
```

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

## Seguridad de APP.3

- Solo lectura.
- No ejecuta comandos arbitrarios.
- No borra, mueve ni modifica imagenes.
- No escribe configuracion.
- No expone preview ni exportacion.
- El servidor rechaza binds distintos de `127.0.0.1` o `localhost` desde el CLI.
- CORS esta limitado a origenes locales de desarrollo del prototipo.

## No implementado todavia

- Tauri;
- selector nativo de carpetas;
- preview real;
- exportacion real;
- progreso real;
- cola;
- pausa/reanudar/cancelar reales;
- apertura real de carpeta de salida;
- empaquetado Windows.
