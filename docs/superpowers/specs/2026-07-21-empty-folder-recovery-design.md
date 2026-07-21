# Recuperación tras una carpeta sin imágenes compatibles

## Objetivo

Cuando un escaneo no encuentra imágenes compatibles, FlatShot debe mostrar un estado vacío coherente y permitir elegir otro directorio que se escanee inmediatamente. La recuperación debe conducir al lote válido sin conservar restos visuales o de estado del escaneo vacío.

## Alcance

- Mantener el lote en estado `empty` mientras no existan imágenes compatibles.
- Presentar el visor como una única superficie neutra, independiente del fondo de previsualización configurado.
- Centrar un mensaje compacto con icono, título, explicación y la acción principal `Elegir otra carpeta`.
- Ocultar o desactivar los controles exclusivos de una imagen mientras el lote esté vacío.
- Lanzar el escaneo automáticamente después de seleccionar una carpeta en el selector nativo.
- Conservar la entrada manual de ruta y su acción explícita de escaneo.

## Fuera de alcance

- Cambios en formatos compatibles, escaneo recursivo o reglas de omisión.
- Cambios en presets, perfiles de salida o procesamiento de imagen.
- Cambios en dimensiones, color, transparencia, nombres o destinos exportados.

## Flujo de estado

1. El escaneo de una carpeta sin imágenes termina en `batch: "empty"`.
2. El visor recibe una clase de estado vacío y usa el fondo de aplicación, no el fondo de salida.
3. La acción `Elegir otra carpeta` abre el selector.
4. Al confirmar una ruta, se persiste la ruta y comienza `scanBridgeFolder()`.
5. Un resultado válido reemplaza el lote, selecciona la primera imagen y solicita su vista previa.
6. Cancelar el selector conserva el lote vacío y no inicia un escaneo.

## Presentación

El estado no simulará un lienzo de exportación. Usará una superficie continua, sin la franja blanca del fondo de salida ni una tarjeta flotante pesada. El contenido tendrá ancho limitado, jerarquía breve y una única acción primaria. El inspector puede seguir mostrando la configuración de salidas, pero los controles dependientes de una imagen permanecerán inactivos.

## Pruebas

- Prueba de flujo: elegir una carpeta confirma la ruta y dispara exactamente un escaneo.
- Prueba de cancelación: cancelar el selector no dispara el escaneo.
- Prueba de render: el estado `empty` incluye la acción de recuperación y aplica la clase visual correspondiente.
- Auditoría CSS y contrato CSS obligatorios.
- Suite completa de `pytest`.

## Criterios de aceptación

- No queda visible el estado de la carpeta vacía después de elegir y escanear una carpeta válida.
- El área central no aparece partida por el fondo de previsualización cuando no hay imágenes.
- `Elegir otra carpeta` es visible, accesible y ejecuta el flujo completo.
- La salida de imágenes no cambia.
