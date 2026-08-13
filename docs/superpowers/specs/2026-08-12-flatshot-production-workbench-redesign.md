# FlatShot Production Workbench Redesign

**Fecha:** 2026-08-12

**Estado:** Corrección de composición aprobada para implementación

**Superficie:** `apps/flatshot-desktop/frontend`

**Viewport principal:** monitor maximizado de 2048 × 1152 px

## Objetivo

Recomponer la interfaz de FlatShot como una mesa de producción compacta y
operativa. El rediseño debe hacer evidente el estado del lote, aumentar el
aprovechamiento del visor y concentrar cada tarea sin cambiar el procesamiento
de imagen, la configuración persistida ni el comportamiento de los archivos
exportados.

## Corrección aprobada tras validación en la aplicación real

La captura maximizada de producción mostró tres defectos que invalidan la
composición C original:

- el visor absorbía todo el ancho libre aunque las imágenes habituales son
  verticales;
- la fila inferior no garantizaba la altura completa de miniaturas y texto;
- cabecera, barra del visor, galería e inspector mostraban contexto repetido.

La interfaz pasa a una **estación vertical de producto**:

1. galería estrecha y desplazable a la izquierda;
2. visor central contenido, dimensionado por la altura útil y no por todo el
   ancho disponible;
3. inspector compacto a la derecha;
4. cabecera reducida a contexto esencial y acción de proceso;
5. ausencia de galería inferior en escritorio.

La galería conserva filtros, búsqueda, selección y todos los estados, pero los
controles secundarios usan revelado progresivo. Las miniaturas nunca se
recortan verticalmente: el panel desplaza la lista completa en su propio eje.

El visor no modifica la preview ni su relación de aspecto. Solo limita la
superficie que la contiene para que un producto vertical ocupe una proporción
útil del monitor. Los laterales recuperados se destinan a navegación del lote
y ajustes, no a fondo vacío.

## Invariantes

- No cambia la apariencia de las imágenes exportadas.
- No cambia el tamaño, formato, alpha, fondo, DPI, calidad, subsampling,
  nombres, sufijos ni destino de las exportaciones.
- No se sobrescriben ni modifican imágenes de origen.
- El frontend continúa delegando escaneo, previews, presets y exportación al
  bridge y a los servicios existentes.
- No se añaden dependencias de runtime.
- Se conservan los estados `idle`, `ready`, `preparing`, `processing`,
  `paused`, `stopping`, `completed` y `error`.
- La configuración existente y las sesiones guardadas continúan siendo
  compatibles.
- La paleta neutra clara, el acento verde y la tipografía de sistema se
  mantienen como identidad de FlatShot.

## Dirección de producto y composición

La interfaz se concibe como una **mesa de luz operativa**. El trabajo visual
ocupa el centro; las miniaturas forman un rail vertical izquierdo; un único
inspector contextual presenta solo la tarea activa. La cabecera concentra el
contexto estable y la acción principal. El proceso de exportación sustituye el
pie normal por una barra de trabajo única.

La composición principal en 2048 × 1152 es:

1. Cabecera operativa compacta.
2. Rail izquierdo del lote con miniaturas completas.
3. Visor vertical contenido con herramientas esenciales.
4. Inspector contextual derecho.
5. Barra de proceso temporal, visible solo durante trabajos activos o recién
   terminados.

El rediseño no se convierte en un asistente paso a paso. El operador puede
acceder directamente a carpeta, preset, revisión o salida, pero la jerarquía
visual conserva el orden natural:

`Carpeta → Aspecto → Revisión → Exportación → Procesar`

## Cabecera operativa

La cabecera mantiene marca y preferencias a la izquierda. En el centro muestra
el contexto estable del lote mediante tres controles compactos:

- `Carpeta`, con nombre corto y acción para seleccionar otra;
- `Preset`, con el preset activo y acceso directo al selector;
- `Salida`, con la salida usada para la preview y acceso a su configuración.

A la derecha aparecen, en este orden:

- estado de preparación con texto y señal no dependiente solo de color;
- acción secundaria de revisión únicamente cuando existan incidencias;
- acción primaria `Procesar X imágenes`.

Se eliminan de la cabecera normal los estados de diagnóstico y los accesos de
desarrollo. En `dev=1` permanecen disponibles dentro de un único menú de QA que
no altera la composición de producción.

## Estado vacío e importación

El fondo decorativo turquesa se sustituye por una superficie neutra coherente
con el visor. El estado vacío usa una sola acción principal:

- `Seleccionar carpeta` abre el selector nativo.

La ruta manual se mantiene como alternativa secundaria bajo `Introducir ruta`.
`Gestionar salidas` no compite con la importación y queda disponible desde el
menú de preferencias o después de crear el lote. Los mensajes distinguen:

- sin carpeta;
- carpeta vacía;
- carpeta sin imágenes válidas;
- error de lectura;
- escaneo cancelable en curso.

## Visor

El visor recibe una columna central limitada entre rail e inspector. La imagen
se escala dentro de esa área respetando la relación de aspecto y los modos
actuales `Alto` y `Ancho`; no se altera el render de la preview.

La barra del visor se divide en grupos estables:

- nombre y posición de la imagen;
- fondo de revisión;
- guías;
- navegación;
- encaje y zoom.

La salida previsualizada deja de mostrarse como toast persistente y pasa a una
franja informativa fija asociada al visor: nombre, formato, dimensiones y
fondo. Los mensajes transitorios quedan reservados para carga, fallback,
errores y confirmaciones breves.

## Rail del lote

La galería se presenta en escritorio como un rail vertical estrecho. Su
cabecera contiene:

- `Lote` y el resumen semántico;
- selector `Salida visible`;
- búsqueda;
- filtros `Todas`, `Listas`, `Avisos` y `Excluidas`;
- alternancia entre `Miniaturas` y `Lista`.

Las miniaturas mantienen selección, multiselección, override local, aviso,
error, dimensiones y nombre. La lista ampliada del lote reutiliza el detalle
existente y puede ocupar el panel principal cuando el usuario elige `Lista`.

La taxonomía visible se normaliza como:

- `N listas`;
- `N con aviso`;
- `N excluidas`;
- `N personalizadas` cuando aplique.

`Error` no se presenta como sinónimo de `Aviso`. La suma de categorías debe
explicar el total del lote sin obligar al usuario a deducirlo.

## Inspector contextual

El inspector derecho muestra una sola tarea y reutiliza los controladores y
servicios actuales. Sus contextos son:

### Aspecto

- preset activo;
- densidad, suavidad y distancia visibles;
- `Producto y lienzo` plegado;
- `Calibración del motor` plegado;
- administración de presets fuera del flujo principal.

### Imagen seleccionada

- nombre, estado y origen del ajuste;
- acción `Personalizar imagen` o `Usar ajuste del lote`;
- overrides locales existentes;
- navegación entre imágenes mediante los controles del visor y el rail.

### Revisión

- resumen separado de avisos y exclusiones;
- lista de incidencias con `Ir a imagen`;
- filtro del rail sincronizado con la categoría activa;
- explicación explícita de qué se exportará y qué quedará fuera.

No se introducen nuevas acciones de aprobación, corrección automática o
marcado manual de incidencias.

### Exportación

- salidas activas y sus datos esenciales;
- activación y desactivación existentes;
- acceso a `Editar salida`, `Gestionar salidas` y `Nueva salida`;
- estado inequívoco de destino y preparación.

El editor modal de salidas conserva su organización actual `Archivo`, `Imagen`
y `Destino`, el ejemplo de nombre y el guardado automático. La indicación
`Cambios guardados` permanece en una zona estable y se complementa con un
estado transitorio al modificar valores.

## Revisión y confirmación de exportación

`Revisar incidencias` activa el contexto de revisión, filtra el rail y
selecciona la primera imagen afectada. El resumen usa categorías separadas y no
afirma que una exclusión sea un aviso no bloqueante.

La confirmación de exportación conserva:

- imágenes exportables;
- salidas activas;
- destino;
- ejemplo de nombres;
- avisos y exclusiones.

Los avisos usan tratamiento amarillo y las exclusiones tratamiento de error,
ambos con icono y texto. Si no existen incidencias, el atajo de exportación
rápida mantiene el comportamiento actual.

## Procesamiento

Durante `preparing`, `processing`, `paused` y `stopping`, una sola barra de
trabajo reemplaza el pie normal. Contiene:

- estado textual: `Preparando exportación`, `Procesando X/Y`, `Pausado` o
  `Deteniendo...`;
- nombre del archivo actual cuando exista;
- progreso lineal con valor accesible;
- `Pausar`/`Continuar`;
- `Detener`.

La cabecera mantiene el contexto del lote, pero no duplica progreso ni botones
de parada. El inspector continúa disponible en modo lectura y no ofrece
acciones incompatibles con el trabajo activo. Al completar, cancelar o fallar,
la barra presenta el resultado y vuelve al estado normal sin conservar una
barra de progreso decorativa.

## Diseño visual

- Estrategia de color restringida: neutros más un solo acento operativo.
- El verde indica selección y acción, no tiñe superficies completas del lote.
- El fondo del visor permanece neutral y no contamina la percepción del fondo
  real de exportación.
- Separación mediante bordes y contraste de superficie; sombras solo en
  overlays y modales.
- Texto operativo de 14 px como mínimo en el viewport principal; encabezados
  de panel de 16–18 px.
- Altura interactiva mínima de 36 px, foco visible y cursores semánticos.
- Rutas y nombres largos se truncan visualmente y conservan tooltip o nombre
  accesible completo.
- No se usan gradientes decorativos, vidrio, tarjetas anidadas ni pills para
  controles ordinarios.

## Adaptación

- **≥ 1600 px:** rail izquierdo, visor central e inspector derecho completos.
- **1120–1599 px:** rail e inspector más estrechos; las
  herramientas menos frecuentes pasan a menús existentes.
- **760–1119 px:** inspector se abre como panel lateral y la galería conserva
  acceso vertical.
- **< 760 px:** composición apilada para contingencia, no como uso principal;
  la acción de proceso y el estado permanecen siempre accesibles.

Ningún breakpoint elimina acceso a preset, salida, incidencias, ajustes o
proceso.

## Dirección visual aprobada

La composición C queda reemplazada por la estación vertical aprobada tras la
captura real: rail izquierdo, visor central contenido e inspector derecho. La
referencia anterior se conserva únicamente como evidencia histórica; no es la
fuente de verdad del layout final.

## Accesibilidad

- Orden de tabulación: cabecera, rail, visor, inspector y barra de proceso.
- Los modales conservan captura y restauración de foco.
- Estados y categorías usan texto e icono además del color.
- El progreso expone etiqueta, máximo, valor actual y estado textual.
- Los controles icon-only conservan `aria-label` y tooltip.
- Los cambios de selección, preview, preparación y progreso usan las regiones
  vivas existentes sin anunciar mensajes duplicados.
- Se respeta `prefers-reduced-motion`.

## Arquitectura y flujo de datos

La implementación se limita a la capa de presentación y a presentadores
frontend puros:

- el estado global y los servicios del bridge no cambian;
- los presentadores producen resúmenes semánticos y contextos del inspector;
- los controladores existentes siguen enviando las mismas acciones;
- la nueva estructura HTML solo reubica superficies y añade puntos de montaje
  cuando sea imprescindible;
- CSS se extiende en el módulo propietario, sin duplicar selectores;
- la barra de proceso consume el estado existente de exportación, pausa y
  cancelación.

No se mueve lógica de presets, exportación, escaneo o procesamiento a los
componentes visuales.

## Gestión de errores

- Los errores de bridge mantienen mensaje breve y detalle disponible.
- Un error de preview no bloquea navegación ni revisión del resto del lote.
- Una salida inválida desactiva el proceso y explica la corrección necesaria.
- Cancelar o fallar restablece controles, progreso y capacidad de reintento.
- Los estados visuales no ocultan archivos válidos ni modifican selecciones de
  manera irreversible.

## Pruebas y aceptación

La implementación se realizará con pruebas de contrato escritas antes de cada
cambio de comportamiento. La aceptación requiere:

1. Tests de estructura para cabecera, visor, rail, inspector y barra de
   proceso.
2. Tests de resumen que diferencien listas, avisos, exclusiones y overrides.
3. Tests de estados `ready`, revisión, confirmación, procesamiento, pausa,
   parada, finalización y error.
4. Tests de accesibilidad para nombres, foco, progreso y estados no dependientes
   solo del color.
5. `python scripts/audit_css.py --check` sin incidencias.
6. `pytest tests/test_frontend_css_contract.py` correcto.
7. Suite completa `pytest` correcta.
8. QA visual a 2048 × 1152 con ventana maximizada para estado vacío, lote
   listo, ajustes, revisión, salidas, confirmación y procesamiento.
9. Comprobación secundaria a 1280 × 720 y 760 × 720 para asegurar acceso a
   controles y ausencia de overflow.
10. Smoke manual con una carpeta vacía y una carpeta con PNG si el entorno
    dispone de imágenes representativas.

## Fuera de alcance

- Cambios al algoritmo de sombra o composición.
- Cambios de formato o calidad de exportación.
- Nuevas acciones de aprobación de imagen.
- Edición destructiva de originales.
- Nuevo framework frontend o shell de escritorio.
- Nuevas dependencias.
- Rediseño de marca, modo oscuro o selección de tonos.
