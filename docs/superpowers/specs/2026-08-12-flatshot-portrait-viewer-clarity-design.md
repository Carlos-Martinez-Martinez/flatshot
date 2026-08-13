# FlatShot: claridad del visor vertical y controles

## Objetivo

Corregir cuatro problemas del puesto de producción actual sin alterar el procesamiento ni la exportación: espacio lateral improductivo alrededor de imágenes verticales, contexto superior ambiguo, cierre bloqueado de `Salidas` y controles de vista ocultos pese a disponer de anchura.

## Composición del puesto

- La galería izquierda absorberá el ancho sobrante y mostrará más miniaturas por fila cuando el monitor lo permita.
- El visor central tendrá un ancho acotado de puesto vertical. El lienzo visible respetará la proporción real de la salida o preview y ocupará todo el alto disponible sin franjas internas artificiales.
- El inspector derecho conservará una anchura compacta y estable.
- El escenario podrá conservar un margen oscuro pequeño alrededor del lienzo para separación, pero no una segunda superficie vacía del ancho fijo actual.
- En ventanas intermedias la galería volverá a dos columnas y el visor conservará prioridad; en anchos estrechos seguirán aplicándose los breakpoints existentes.

## Contexto superior

Los tres elementos situados junto a Preferencias mostrarán siempre su función y su valor:

- `Carpeta` — nombre de la carpeta activa.
- `Preset` — ajuste activo.
- `Salida` — salida seleccionada.

Cada elemento conservará tooltip o título con el valor completo. `Carpeta` y `Salida` seguirán siendo acciones; `Preset` será informativo. No se añadirán nuevos conceptos ni estados.

## Herramientas del visor

- En el monitor principal y demás anchos de escritorio amplios, `Fondo` y `Guías` estarán visibles directamente en la barra del visor.
- Navegación, encaje y zoom permanecerán visibles como ahora.
- El menú `Vista` actuará únicamente como adaptación responsive cuando la barra no tenga anchura suficiente.
- La barra podrá distribuirse en dos grupos o dos líneas estables si el visor vertical no permite una sola línea, sin superponer el nombre de archivo ni provocar saltos.

## Cierre de Salidas

- La `X`, el clic en el fondo y `Escape` compartirán una única política de cierre.
- Sin cambios pendientes, cerrarán inmediatamente.
- Con cambios pendientes, mostrarán dentro del propio diálogo una confirmación clara: `Seguir editando` o `Descartar y cerrar`.
- `Descartar y cerrar` restaurará la salida persistida —o eliminará el borrador nuevo— y cerrará el diálogo.
- `Cancelar` seguirá descartando un borrador nuevo, pero no será la única vía funcional para salir.
- La confirmación evitará pérdida accidental y no abrirá un segundo modal.

## Límites técnicos

- No se modificará el cálculo de previews, el contenido de archivos, el motor de imagen, el naming ni los destinos.
- La proporción del lienzo se derivará de datos serializables ya disponibles; la UI no incorporará reglas de negocio.
- Los cambios se integrarán en los módulos propietarios existentes, sin duplicar selectores CSS.

## Validación

- Pruebas primero para: política de cierre con borrador limpio/sucio, contexto superior etiquetado, controles inline en escritorio y geometría del visor vertical.
- Auditoría CSS obligatoria y suite completa de `pytest`.
- QA real a 2048×1152 maximizado y comprobación intermedia a 1280×720.
- Comprobar selección de miniaturas, Fondo, Guías, zoom, apertura/cierre de Salidas, `Escape`, fondo del modal y confirmación de descarte.

## Resultado esperado

A 2048×1152, el usuario identifica de inmediato carpeta, preset y salida; ve Fondo y Guías sin abrir un cajón; el lote aprovecha el ancho libre; el lienzo vertical no añade franjas laterales propias; y Salidas siempre ofrece una salida comprensible y segura.
