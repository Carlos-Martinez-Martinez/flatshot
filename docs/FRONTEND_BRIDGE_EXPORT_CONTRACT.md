# Contrato frontend -> bridge para exportacion

Este documento fija el contrato actual que la UI estatica envia al bridge local para preparar o ejecutar una exportacion. No describe una API nueva: documenta el JSON existente para evitar divergencias entre `app.js`, los helpers frontend y los servicios Python.

## Endpoint

- `POST /exports/run`
- `POST /exports/prepare`

Ambos endpoints reciben la misma forma base de payload. La UI activa lo construye en `apps/flatshot-desktop/frontend/export-payload.js` y el bridge lo normaliza en `src/flatshot/bridge/service.py`.

## Payload raiz

```json
{
  "imagePaths": ["C:/lote/a.png"],
  "presetName": "Luz cenital",
  "settings": {},
  "imageOverrides": {},
  "export": {}
}
```

- `imagePaths`: rutas locales seleccionadas y exportables. La UI solo incluye imagenes `source: "bridge"` con `path`.
- `presetName`: nombre del preset activo.
- `settings`: ajustes de preview/export derivados del preset activo y overrides globales.
- `imageOverrides`: ajustes locales por imagen, indexados por ruta/id segun el estado actual.
- `export`: configuracion de salida y variantes.

## Bloque `export`

El bloque mantiene campos legacy del perfil primario y, ademas, una lista completa de `variants`.

```json
{
  "format": "JPG",
  "size": "1800x2400",
  "background": "rgb230",
  "destinationMode": "source",
  "destinationValue": "_SALIDA_PRO",
  "outputFolderName": "_SALIDA_PRO",
  "customOutputPath": "",
  "namingTemplate": "{original}{suffix}",
  "suffix": "_PRO",
  "variants": []
}
```

- `format`: `JPG` o `PNG` del perfil primario.
- `size`: tamano del perfil primario como `ANCHOxALTO`.
- `background`: `rgb230`, `white` o `transparent`.
- `destinationMode`: `source` en frontend equivale a `subfolder` en backend; `custom` se conserva como `custom`.
- `destinationValue`: subcarpeta o ruta personalizada visible en la UI.
- `outputFolderName`: subcarpeta usada cuando `destinationMode` es `source`.
- `customOutputPath`: ruta usada cuando `destinationMode` es `custom`.
- `namingTemplate`: plantilla de nombres del perfil primario.
- `suffix`: sufijo del perfil primario.
- `variants`: salidas activas normalizadas para `ExportVariant`.

Los campos legacy no deben eliminarse mientras `src/flatshot/bridge/service.py` siga aceptando payloads antiguos o usando esos valores como fallback.

## Variante de salida

Cada perfil activo se transforma a esta forma:

```json
{
  "id": "web_rgb230",
  "label": "Web gris claro",
  "enabled": true,
  "format": "JPG",
  "transparent_bg": false,
  "bg_color": [230, 230, 230],
  "suffix": "_PRO",
  "naming_template": "{original}{suffix}",
  "output_destination": "subfolder",
  "output_folder_name": "_SALIDA_PRO",
  "custom_output_path": null,
  "output_width": 1800,
  "output_height": 2400
}
```

Reglas actuales:

- `background: "transparent"` produce `transparent_bg: true` y mantiene `bg_color: [230, 230, 230]` como fallback.
- `background: "white"` produce `bg_color: [255, 255, 255]`.
- `background: "rgb230"` produce `bg_color: [230, 230, 230]`.
- `destinationMode: "source"` produce `output_destination: "subfolder"`.
- `destinationMode: "custom"` produce `output_destination: "custom"`.
- IDs duplicados se deduplican con sufijo incremental (`id`, `id_2`, `id_3`).

## Invariantes

- No cambiar nombres de campos sin actualizar tests frontend y tests de bridge.
- No cambiar defaults de formato, tamano, fondo, destino, naming o sufijo durante refactors UI.
- No mover esta logica al renderizado ni a handlers DOM.
- No tocar `ExportRunner` para cambios de UI; cualquier cambio en salida necesita pruebas de paridad/golden.

## Validacion relacionada

- `tests/test_frontend_export_payload.py`
- `tests/test_frontend_output_profiles.py`
- `tests/test_bridge_service.py`
- `tests/test_export_config_service.py`
- `tests/test_export_variants.py`
