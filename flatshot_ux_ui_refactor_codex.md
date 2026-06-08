# FlatShot — Refactor UX/UI y correcciones funcionales

Documento de implementación para Codex.

## 1. Objetivo

Refactorizar la interfaz de FlatShot para que sea más clara, menos redundante, más accionable y más coherente visualmente, sin perder funcionalidad existente.

La app debe seguir orientada a un flujo de trabajo real de producción: cargar un lote de imágenes, revisar rápidamente el resultado final esperado, ajustar salida/imagen cuando haga falta y exportar sin fricción. La interfaz actual muestra demasiada información repetida, controles poco jerarquizados, modales innecesarios y varios problemas de layout/CSS que reducen la percepción profesional de la herramienta.

## 2. Principios de diseño obligatorios

### 2.1. Reducir redundancia informativa

Cada dato debe aparecer en un único lugar principal. Si se repite, debe haber una razón funcional clara.

Evitar repetir en varios sitios:

- número de archivos listos;
- número de ignorados;
- formato de salida;
- dimensiones de salida;
- fondo/transparencia;
- nombre del preset;
- estado del lote;
- estado individual de la imagen.

Los archivos ignorados por razones técnicas esperables, como `Thumbs.db`, no deben tratarse como información relevante para el usuario principal. Pueden existir en un panel de detalle o diagnóstico, pero no deben contaminar los contadores visibles del flujo normal.

### 2.2. Información mínima, pero suficiente

Eliminar subtítulos y microtextos que no aporten decisión ni contexto. Hay exceso de etiquetas del tipo “Ajuste de aspecto”, “Vista”, “Avanzado”, “Imagen seleccionada”, etc. Si el título de la tarjeta ya explica la función, no añadir subtítulo.

La app no debe volverse críptica. Se debe conservar la información necesaria para operar con seguridad, pero no explicar permanentemente lo obvio.

### 2.3. Acciones directas en el contexto adecuado

El panel derecho debe dejar de ser un resumen pasivo y convertirse en el lugar principal para ajustar la salida y los parámetros de imagen del lote o de la imagen seleccionada.

Evitar enviar al usuario a modales o pantallas separadas para ajustes frecuentes.

### 2.4. Coherencia de sistema de diseño

Todos los botones, inputs, chips, selectores, paneles, paddings, radios, estados hover/focus/active y tamaños deben seguir un sistema común.

No usar estilos aislados, degradados sueltos ni componentes con padding distinto sin justificación.

### 2.5. Iconografía fiable

Si se usan iconos, deben venir de una librería establecida y consistente. Recomendación si el proyecto es React: `lucide-react`. Alternativas válidas: Radix Icons, Phosphor Icons o Heroicons.

No crear iconos complejos a mano con CSS si existe un icono estándar equivalente.

Usar una sola familia de iconos en toda la app.

---

## 3. Alcance funcional

Este refactor afecta principalmente a:

1. pantalla inicial sin carpeta seleccionada;
2. cabecera superior global;
3. layout principal de tres zonas: galería izquierda, visor central y panel derecho;
4. galería de miniaturas;
5. visor central de imagen;
6. panel derecho de lote/salida/ajustes;
7. gestión de formatos de salida;
8. ajustes de imagen y controles con sliders;
9. menús desplegables y redundancias funcionales;
10. errores de CSS, overflow, padding y clipping.

No se debe modificar la lógica de procesamiento/exportación salvo que sea necesario para sincronizar correctamente estados de UI, presets seleccionados o overrides temporales.

---

## 4. Problemas detectados y requisitos de corrección

## 4.1. Pantalla inicial sin carpeta seleccionada

### Problemas actuales

- El icono de carpeta parece una construcción improvisada y poco profesional.
- La jerarquía de información es débil.
- Se muestra una salida seleccionada aunque todavía no hay carpeta cargada. Esto no es pertinente en este estado.
- El CTA principal no domina lo suficiente el estado vacío.
- El estado vacío parece una tarjeta genérica, no una entrada clara al flujo de trabajo.

### Requisitos

1. Sustituir el icono actual por un icono estándar de librería fiable.
   - Recomendado: `FolderOpen`, `FolderPlus` o equivalente.
   - Tamaño contenido, sin ornamentación excesiva.

2. Reestructurar el empty state con jerarquía clara:
   - título: `Selecciona una carpeta`;
   - texto breve opcional: `Carga un lote de imágenes PNG o JPG para revisar y exportar.`;
   - acción principal: `Seleccionar carpeta`;
   - acción secundaria opcional: `Nuevo lote` o `Configurar salidas`, sólo si tiene utilidad real antes de cargar carpeta.

3. No mostrar información de salida activa antes de seleccionar carpeta.

4. Si se quiere informar del formato por defecto, debe hacerse de forma secundaria y no como si fuese un dato operativo del lote.
   - Ejemplo aceptable: `Salida por defecto: Zalando` en una zona de configuración, no dentro del CTA principal.

5. Mantener la pantalla inicial visualmente limpia y centrada, pero no sobredimensionada.

### Criterios de aceptación

- No aparece ninguna salida activa como información principal antes de cargar carpeta.
- El icono procede de una librería, no de CSS artesanal.
- La acción principal es inequívoca.
- El estado vacío no repite datos que se mostrarán después en el panel derecho.

---

## 4.2. Cabecera superior global

### Problemas actuales

- Junto al nombre `FlatShot` se repite información que luego aparece varias veces dentro de la interfaz.
- Los chips de estado junto al nombre del programa sobrecargan la cabecera.
- Los botones de la derecha tienen tamaños inconsistentes.
- Hay poco padding interno en algunos botones, lo que genera sensación de interfaz apretada.
- Existe un botón de tres puntos que sólo muestra una opción. Esto no justifica un menú.
- El menú de tres puntos queda fijo y sólo se cierra al pulsar de nuevo el mismo botón.
- `Detalle lote` y `Ver detalle` parecen funciones duplicadas.

### Requisitos

1. Limpiar la zona izquierda de la cabecera.
   - Debe contener sólo el logo/icono de la app y el nombre `FlatShot`.
   - Opcionalmente se puede mostrar el nombre del lote o carpeta activa si aporta orientación, pero no contadores repetidos.

2. Mover la información de estado del lote al panel izquierdo o derecho, no a la cabecera global.

3. Normalizar botones de cabecera:
   - altura común;
   - padding horizontal común;
   - misma familia visual;
   - estados hover/focus/disabled coherentes;
   - separación consistente.

4. Mantener `Exportar` como acción primaria.
   - Debe destacar más que el resto.
   - El texto debe reflejar correctamente cuántas salidas se generarán si hay varias salidas por imagen.

5. Revisar acciones secundarias:
   - `Salida`;
   - `Carpeta`;
   - `Nuevo lote`;
   - otras opciones.

6. El menú de tres puntos sólo debe existir si contiene dos o más acciones secundarias reales.
   - Si sólo contiene una opción, eliminar el menú y mostrar esa acción directamente si es necesaria.
   - Si se mantiene el menú, debe cerrarse al hacer click fuera, al pulsar `Escape` y al seleccionar una opción.

7. Eliminar duplicidad entre `Detalle lote` y `Ver detalle`.
   - Debe existir una sola entrada para detalle del lote.
   - Debe tener apariencia clara de botón o link según su importancia.

### Criterios de aceptación

- La cabecera no repite contadores ni estado técnico del lote.
- Los botones tienen altura y padding consistentes.
- El menú de tres puntos no existe con una sola opción.
- El menú, si existe, se cierra correctamente con click exterior y `Escape`.
- No hay dos controles distintos que abran el mismo detalle del lote.

---

## 4.3. Layout principal y distribución de columnas

### Problemas actuales

- El espacio central del visor es demasiado ancho para imágenes que casi siempre serán verticales.
- Hay demasiado vacío lateral alrededor de la imagen.
- La cabecera del visor central es demasiado alta.
- El nombre de la imagen y los controles de vista están desalineados.
- La galería izquierda podría aprovechar parte del espacio que sobra en el centro.
- El layout no parece ajustado a distintos tamaños de ventana.

### Requisitos

1. Rediseñar el layout principal como una estructura de tres zonas:
   - panel izquierdo de galería más ancho;
   - visor central con ancho útil controlado;
   - panel derecho de ajustes/resumen.

2. El visor central no debe crecer indefinidamente en horizontal.
   - Debe tener un `max-width` razonable para imágenes verticales.
   - El espacio sobrante debe aprovecharse para galería o paneles, no para crear vacío inútil.

3. La galería izquierda debe poder mostrar más miniaturas de un vistazo.
   - Ajustar ancho del panel izquierdo.
   - Hacer grid responsive de miniaturas.

4. La cabecera del visor central debe ser compacta.
   - Nombre de imagen alineado verticalmente con controles.
   - Controles agrupados en una toolbar de altura uniforme.
   - Reducir altura total.

5. El layout debe escalar a distintos tamaños de ventana:
   - evitar scroll global innecesario;
   - usar scroll interno en panel izquierdo/derecho cuando haga falta;
   - conservar visor central visible.

### Sugerencia de layout

Implementar una grid similar a:

```css
.app-main {
  display: grid;
  grid-template-columns: clamp(300px, 22vw, 380px) minmax(520px, 1fr) clamp(300px, 22vw, 360px);
  min-height: 0;
}

.viewer-shell {
  max-width: min(820px, 100%);
  margin: 0 auto;
}
```

La cifra exacta debe ajustarse al diseño actual, pero el objetivo es claro: el visor central debe priorizar la relación vertical de las imágenes, no ocupar horizontalmente todo lo disponible.

### Criterios de aceptación

- El visor central deja de tener grandes vacíos laterales innecesarios.
- El panel izquierdo muestra más miniaturas sin sentirse comprimido.
- La cabecera del visor central es compacta y alineada.
- La app no depende de una única resolución concreta.

---

## 4.4. Panel izquierdo: galería del lote

### Problemas actuales

- La jerarquía del panel no es clara.
- Se muestran datos no relevantes, como ignorados técnicos.
- El panel podría ser más ancho.
- La estructura `nombre del panel / vista / búsqueda / galería` necesita mejor orden visual.
- El filtro `Todas` no tiene sentido si no hay otras opciones.
- La información de archivo bajo las miniaturas es excesiva.
- Los badges `Lista` se repiten en cada miniatura y son invasivos.
- Las miniaturas PNG aparecen apretadas dentro del marco.

### Requisitos

1. Reestructurar el panel con orden estable:
   - título del panel: `Lote` o `Imágenes`;
   - contador útil: número de imágenes procesables/listas;
   - selector de vista: `Lista` / `Miniaturas`;
   - búsqueda;
   - filtros sólo si existen opciones reales;
   - galería.

2. Ocultar ignorados técnicos del resumen principal.
   - Si hay ignorados relevantes para el usuario, mostrarlos en detalle de lote.
   - Si son archivos de sistema, no deben condicionar la percepción del estado del lote.

3. El filtro `Todas` debe eliminarse si no hay más filtros.
   - Alternativa: crear filtros útiles y mostrarlos sólo cuando correspondan:
     - `Todas`;
     - `Listas`;
     - `Revisar`;
     - `Error`;
     - `Con ajuste local`.
   - Si sólo existe `Todas`, no mostrar el grupo de filtros.

4. Las miniaturas deben mostrar el resultado final esperado con el preset principal elegido.
   - Si hay varios presets activos, usar como preview el preset principal o el primero marcado como principal.
   - Debe quedar claro visualmente que la miniatura representa el resultado final, no simplemente el archivo original.

5. Simplificar metadata bajo miniatura.
   - Mostrar sólo nombre de archivo o referencia.
   - No mostrar `PNG` ni tamaño en MB en vista de miniaturas, salvo que haya un modo técnico.

6. Sustituir el badge repetido `Lista`.
   - Usar un check discreto, una marca de estado menos invasiva o un borde/estado visual.
   - El estado debe estar visible, pero no competir con la imagen.

7. Mejorar el encaje visual de PNGs transparentes.
   - Añadir padding interno controlado.
   - Usar checkerboard sutil sólo dentro del área de imagen si es necesario.
   - Evitar que la prenda quede pegada al borde de la tarjeta.

8. La tarjeta seleccionada debe tener un estado claro:
   - borde visible;
   - fondo levemente destacado;
   - accesible por teclado.

### Criterios de aceptación

- La galería muestra más imágenes de un vistazo.
- No se repiten badges invasivos en todas las miniaturas.
- No se muestra información irrelevante como tamaño de archivo en miniatura.
- El usuario puede localizar una referencia con búsqueda y escaneo visual rápido.
- El estado seleccionado/listo/revisar se entiende sin sobrecargar la tarjeta.

---

## 4.5. Visor central de imagen

### Problemas actuales

- El área central contiene demasiado espacio horizontal vacío.
- Hay una etiqueta inferior indicando la salida/exportación, pero esa información ya aparece en el panel derecho.
- Esa etiqueta inferior ni siquiera se corresponde claramente con el nombre del preset.
- El fondo/sombreado del área central distrae.
- El ajuste de vista/fondo debería estar integrado en el visor central.
- La imagen se puede desplazar completamente fuera de la vista.
- Hay un botón `Vista` sin utilidad clara.

### Requisitos

1. Eliminar la etiqueta inferior de exportación/preset dentro del visor central.
   - La salida activa debe gestionarse en el panel derecho.
   - El visor debe centrarse en revisar visualmente la imagen.

2. Eliminar sombreado/degradado decorativo del fondo del visor.
   - Sólo debe representarse el fondo real de revisión/exportación que el usuario haya indicado.
   - No añadir efectos visuales al resto de la interfaz que puedan confundirse con el resultado.

3. Integrar control de fondo de revisión en el visor central.
   - Debe permitir cambiar el fondo de previsualización para revisar contraste.
   - Opciones recomendadas:
     - transparente/checkerboard;
     - blanco;
     - negro/gris oscuro;
     - gris neutro;
     - color personalizado si ya existe.
   - Este ajuste es de visualización/revisión salvo que se indique explícitamente que forma parte del preset de exportación.

4. Quitar el botón `Vista` si no tiene una función real y comprensible.
   - Si se mantiene, debe renombrarse y tener comportamiento claro.
   - Preferencia: eliminarlo.

5. Mantener controles útiles:
   - anterior/siguiente;
   - encajar;
   - 1:1;
   - alto/anchura si aplica;
   - zoom con porcentaje.

6. Compactar y alinear toolbar superior del visor.

7. Restringir el pan/drag de imagen.
   - La imagen no debe poder moverse completamente fuera del viewport.
   - Implementar límites de desplazamiento según zoom y tamaño de contenedor.
   - En modo `fit`, la imagen debe quedar centrada y sin posibilidad de arrastrarse fuera.
   - Al cambiar de imagen, aplicar reset razonable de vista salvo que exista una preferencia clara de mantener zoom.

### Criterios de aceptación

- No hay información redundante de salida dentro del visor.
- El fondo mostrado sirve para revisión, no como decoración.
- La imagen nunca puede quedar completamente fuera del área visible.
- El botón `Vista` se elimina o se reemplaza por un control claramente útil.
- La toolbar del visor queda compacta y alineada.

---

## 4.6. Panel derecho: resumen accionable del lote

### Problemas actuales

- El panel derecho funciona demasiado como resumen pasivo.
- El bloque `Salida` usa degradados y estilos poco coherentes con el sistema de diseño.
- Hay padding insuficiente en secciones como `Imagen` y `Ajuste activo`.
- `Editar salida` abre un modal excesivo para una acción frecuente.
- Si hay varias salidas seleccionadas, el panel no refleja correctamente cuáles están activas.
- El modal de formatos no refleja en la captura la salida realmente elegida.
- El panel derecho no permite editar parámetros de salida directamente.
- `Ajustar imagen` y `Editar ajuste` llevan al mismo sitio, generando duplicidad.

### Requisitos

Rediseñar el panel derecho como un panel operativo dividido en bloques claros.

### Estructura propuesta

#### 1. Estado del lote

Contenido mínimo:

- título: `Lote listo` o estado real;
- contador de imágenes exportables;
- incidencias reales si existen;
- enlace único a detalle del lote si hace falta.

No mostrar ignorados técnicos como alerta principal.

#### 2. Salidas activas

Debe mostrar todas las salidas seleccionadas, no sólo una.

Cada salida debe mostrarse como fila compacta:

- checkbox o toggle activo/inactivo;
- nombre completo del preset;
- resumen compacto: formato, tamaño, fondo;
- indicador de salida principal si aplica;
- acción secundaria discreta para editar parámetros.

Ejemplo conceptual:

```text
Salidas
[x] Zalando              PNG · 1800×2400 · transparente
[x] JPG gris claro 18    JPG · 1800×2400 · gris claro
[ ] JPG blanco 2000      JPG · 2000×2000 · blanco
```

#### 3. Edición directa de salida

Desde el propio panel derecho se deben poder ajustar parámetros frecuentes:

- formato;
- tamaño;
- fondo;
- carpeta/destino si es parte del preset;
- sufijo/nombre si aplica;
- calidad JPG si aplica.

Los cambios deben distinguir entre:

- cambio temporal para este lote;
- guardar cambios en el preset existente;
- crear nuevo preset a partir de estos ajustes.

No hace falta forzar una decisión modal en cada cambio. Se puede mostrar una barra/estado:

```text
Cambios temporales en esta salida
[Guardar en preset] [Guardar como nuevo] [Descartar]
```

#### 4. Imagen seleccionada

Contenido mínimo:

- nombre/referencia actual;
- estado real: lista, revisar, error;
- ajuste local si existe.

No repetir formato/tamaño/salida salvo que haya un override específico por imagen.

#### 5. Ajuste de imagen

Debe permitir editar en contexto el ajuste activo.

- Selector de preset de ajuste.
- Parámetros principales en acordeones compactos.
- Overrides por imagen claramente diferenciados de ajustes globales del lote.

Eliminar duplicidad entre `Ajustar imagen` y `Editar ajuste`.
Debe existir una única acción clara:

- `Ajustes de imagen` como bloque expandible;
- o `Editar ajuste` como acción que expande el panel inline.

### Estilo visual

- Eliminar degradados decorativos.
- Usar tarjetas planas o superficies del sistema de diseño.
- Padding consistente.
- Jerarquía tipográfica clara.
- Botones secundarios discretos.
- Acciones destructivas separadas visualmente.

### Criterios de aceptación

- El panel derecho permite activar/desactivar varias salidas sin abrir modal.
- El panel derecho refleja exactamente las salidas activas del lote.
- Los cambios de salida pueden ser temporales, guardarse en preset o guardarse como preset nuevo.
- No hay dos botones que lleven al mismo menú de ajustes.
- No hay degradados o estilos ajenos al sistema de diseño.

---

## 4.7. Panel/modal de formatos de salida

### Problemas actuales

- El panel `Formatos de salida` está sobrecargado.
- Hay mala jerarquía de información.
- El selector lateral de salidas no permite ver bien el nombre completo del preset.
- Hay chips y datos redundantes que no aportan.
- El panel parece mezclar dos funciones distintas:
  - elegir salidas para el lote;
  - editar presets guardados.
- En la captura, el modal no parece reflejar correctamente la salida seleccionada en el lote.

### Requisitos

Replantear este panel como gestor de presets, no como paso obligatorio para ajustes frecuentes.

### Nueva función principal del panel

Debe servir para:

- crear presets de salida;
- editar valores por defecto de presets;
- duplicar presets;
- eliminar/restaurar presets;
- definir cuál es preset principal si aplica.

La selección rápida de salidas activas para el lote debe poder hacerse desde el panel derecho principal.

### Selector lateral de presets

1. Simplificar tarjetas laterales.
2. Mostrar nombre completo del preset.
3. Evitar chips redundantes si ya hay estado por checkbox/toggle.
4. Indicar activo/inactivo con un patrón simple.
5. Mostrar datos secundarios sólo si caben sin cortar:
   - formato;
   - tamaño;
   - fondo.

### Zona de edición

1. Mostrar el nombre del preset y sus valores por defecto.
2. Reducir texto explicativo.
3. Agrupar campos por necesidad real, no por categorías excesivas.
4. Mantener sincronización con el lote actual:
   - si un preset está activo en el lote, debe verse activo;
   - si hay varias salidas activas, deben verse todas;
   - si hay cambios temporales, deben diferenciarse de valores guardados.

### Reglas de información

Eliminar o reducir:

- chips como `Activo en este lote` si ya existe toggle claro;
- duplicación de `Formato`, `Tamaño`, `Fondo` en varias zonas próximas;
- ejemplo de exportación demasiado grande si no aporta a la edición;
- subtítulos que sólo repiten el título.

Mantener:

- preview de nombre final si ayuda a evitar errores de exportación;
- carpeta destino;
- sufijo/regla de nombre;
- advertencias reales de conflicto.

### Criterios de aceptación

- El gestor de presets no es necesario para activar/desactivar salidas rápidas del lote.
- Los nombres completos de presets se leen sin truncado innecesario.
- El estado activo del lote está sincronizado con el panel.
- La información redundante se reduce de forma visible.

---

## 4.8. Ajustes de imagen y controles con sliders

### Problemas actuales

- Los valores numéricos de los deslizadores se ven cortados.
- No se pueden introducir valores manualmente.
- Esto impide precisión, copiar valores de un ajuste previo o reproducir una configuración exacta.
- Hay problemas de CSS/estructura en el panel `Ajuste por imagen`.

### Requisitos

1. Cada parámetro ajustable debe tener:
   - etiqueta clara;
   - slider;
   - input numérico editable;
   - unidad si aplica;
   - botón de reset si es útil.

2. El input numérico debe permitir:
   - escribir a mano;
   - pegar valores;
   - seleccionar texto;
   - validar mínimos/máximos;
   - confirmar con `Enter`;
   - cancelar o perder foco sin romper el valor.

3. Evitar clipping:
   - revisar `overflow`, `width`, `min-width`, `flex-shrink` y `box-sizing`;
   - los valores no deben cortarse aunque tengan varios dígitos.

4. Normalizar filas de parámetros:

```text
Opacidad        [ slider ---------------- ] [ 20 ]
Desenfoque      [ slider ---------------- ] [ 30 ]
Distancia       [ slider ---------------- ] [ 25 ]
Padding         [ slider ---------------- ] [ 10 ]
```

5. Diferenciar claramente entre:
   - ajuste global del lote;
   - ajuste del preset;
   - ajuste local por imagen.

### Criterios de aceptación

- Ningún valor numérico aparece cortado.
- Todo slider importante puede editarse con input numérico.
- Los valores pueden copiarse/pegarse.
- La estructura del panel no se rompe al expandir/cerrar secciones.

---

## 4.9. Vista/fondo de revisión

### Problemas actuales

- El ajuste `Vista / Fondo` está en el panel derecho, pero su utilidad real es revisar la imagen final sobre otro fondo.
- El fondo central incluye sombreado decorativo que no aporta.
- Puede confundirse fondo de revisión con fondo real de exportación.

### Requisitos

1. Mover el control de fondo de revisión al visor central.
2. Diferenciar conceptualmente:
   - fondo de exportación del preset;
   - fondo de revisión del visor.
3. El fondo de revisión no debe modificar el preset salvo que el usuario lo indique explícitamente.
4. El sombreado decorativo del lienzo debe eliminarse.
5. Si el preset incluye sombra aplicada al producto, esa sombra sí debe verse en la prenda.
   - No añadir sombra al contenedor completo.

### Criterios de aceptación

- El usuario puede cambiar el fondo de revisión desde el visor central.
- El cambio de fondo de revisión no altera accidentalmente la exportación.
- No hay efectos decorativos que simulen parte de la imagen exportada.

---

## 4.10. Menús, duplicidades y comportamiento interactivo

### Problemas actuales

- Menú de tres puntos persistente hasta volver a pulsar el mismo botón.
- `Detalle lote` y `Ver detalle` duplican función.
- Algunos botones parecen links y algunos links parecen botones.
- Algunas acciones llevan al mismo sitio con nombres distintos.

### Requisitos

1. Revisar todas las acciones de la interfaz y crear un mapa de acción única.

Cada acción debe tener:

- un único propósito;
- un único nombre;
- una ubicación principal;
- feedback visual claro.

2. El menú de tres puntos debe:
   - cerrarse al click exterior;
   - cerrarse con `Escape`;
   - cerrarse al elegir opción;
   - no usarse si sólo tiene una acción.

3. Eliminar duplicidades funcionales:
   - `Detalle lote` / `Ver detalle`;
   - `Ajustar imagen` / `Editar ajuste` si llevan al mismo sitio;
   - cualquier otra acción equivalente detectada en código.

4. Homogeneizar affordances:
   - botones con aspecto de botón;
   - links con aspecto de link;
   - acciones primarias/ secundarias/ destructivas con jerarquía visual clara.

### Criterios de aceptación

- No quedan acciones duplicadas que abran el mismo panel/modal sin justificación.
- Los menús se comportan como menús estándar.
- El usuario entiende qué es botón, qué es link y qué es estado.

---

## 4.11. CSS, spacing y robustez visual

### Problemas actuales

- Hay errores de CSS y estructuración en paneles concretos.
- Algunos campos tienen padding insuficiente.
- Algunos valores aparecen cortados.
- Hay exceso de subtítulos y divisiones internas.
- Algunos componentes parecen diseñados de forma independiente del resto.

### Requisitos

1. Hacer auditoría de componentes visuales comunes:
   - Button;
   - IconButton;
   - Card;
   - Panel;
   - SectionHeader;
   - Chip/Badge;
   - Input;
   - Select;
   - SliderWithInput;
   - DropdownMenu;
   - ThumbnailCard.

2. Normalizar tokens:
   - spacing;
   - radius;
   - border;
   - color;
   - typography;
   - shadows;
   - focus ring;
   - disabled state.

3. Evitar estilos sueltos para casos concretos salvo necesidad real.

4. Revisar overflow:
   - panel derecho;
   - panel izquierdo;
   - modal de salidas;
   - sliders;
   - nombres de preset largos;
   - nombres de archivo largos.

5. Reducir subtítulos innecesarios en toda la interfaz.

### Criterios de aceptación

- No hay textos cortados en controles principales.
- Los paddings son consistentes en tarjetas y paneles.
- Los componentes comparten lenguaje visual.
- Los nombres largos se gestionan con truncado razonable, tooltip o layout que permita lectura completa en zonas críticas.

---

## 5. Modelo de estado recomendado

Revisar el modelo de datos de UI para evitar inconsistencias entre panel derecho, visor y gestor de presets.

### Entidades sugeridas

```ts
type OutputPreset = {
  id: string;
  name: string;
  format: 'png' | 'jpg' | 'webp';
  width: number;
  height: number;
  background: 'transparent' | 'white' | 'gray' | 'custom';
  backgroundColor?: string;
  destination: string;
  filenameSuffix?: string;
  jpgQuality?: number;
  isPrimary?: boolean;
};

type ActiveOutput = {
  presetId: string;
  enabled: boolean;
  temporaryOverrides?: Partial<OutputPreset>;
};

type ImageAdjustmentPreset = {
  id: string;
  name: string;
  params: Record<string, number | string | boolean>;
};

type ImageLocalOverride = {
  imageId: string;
  outputOverrides?: Record<string, Partial<OutputPreset>>;
  adjustmentOverrides?: Record<string, number | string | boolean>;
};
```

No es obligatorio usar exactamente estos tipos, pero la UI necesita distinguir claramente:

- preset guardado;
- preset activo en este lote;
- override temporal del lote;
- override local por imagen.

### Regla clave

El panel derecho debe leer y escribir sobre el mismo estado que el gestor de presets. No puede mostrar una salida distinta de la que está activa realmente.

---

## 6. Orden de implementación recomendado

## Fase 1 — Auditoría y limpieza de estructura

1. Localizar componentes responsables de:
   - cabecera global;
   - empty state;
   - layout principal;
   - galería;
   - visor;
   - panel derecho;
   - modal/gestor de formatos;
   - ajustes de imagen;
   - menús.

2. Identificar datos duplicados y lugares donde se renderizan.
3. Crear lista de acciones duplicadas.
4. Confirmar librería de iconos actual. Si no hay una, instalar una sola librería fiable.

## Fase 2 — Sistema visual base

1. Normalizar botones, cards, chips, inputs y spacing.
2. Eliminar degradados no justificados.
3. Corregir padding inconsistente.
4. Crear/ajustar `SliderWithInput` reutilizable.
5. Garantizar focus states accesibles.

## Fase 3 — Cabecera y empty state

1. Limpiar cabecera izquierda.
2. Normalizar acciones de cabecera derecha.
3. Corregir menú de tres puntos o eliminarlo.
4. Rediseñar pantalla inicial sin carpeta.

## Fase 4 — Layout principal y visor

1. Ajustar grid de tres columnas.
2. Compactar cabecera del visor.
3. Eliminar etiqueta inferior redundante.
4. Integrar fondo de revisión en el visor.
5. Eliminar botón `Vista` si no aporta.
6. Corregir límites de pan/drag de imagen.

## Fase 5 — Galería izquierda

1. Ampliar panel izquierdo.
2. Mejorar grid de miniaturas.
3. Simplificar metadata.
4. Sustituir badge `Lista` invasivo.
5. Eliminar filtro inútil si sólo hay una opción.
6. Ocultar ignorados técnicos del resumen principal.

## Fase 6 — Panel derecho accionable

1. Rediseñar bloque de estado del lote.
2. Mostrar todas las salidas activas.
3. Permitir activar/desactivar salidas desde panel derecho.
4. Añadir edición directa de parámetros frecuentes.
5. Distinguir cambios temporales, guardar preset y guardar como nuevo.
6. Integrar ajustes de imagen en contexto.
7. Eliminar duplicidad `Ajustar imagen` / `Editar ajuste`.

## Fase 7 — Gestor de formatos de salida

1. Convertirlo en gestor de presets.
2. Simplificar selector lateral.
3. Asegurar lectura del nombre completo del preset.
4. Sincronizar estados activos con el lote.
5. Reducir chips y bloques redundantes.
6. Mantener preview de nombre final sólo si aporta valor.

## Fase 8 — QA visual y funcional

Probar manualmente:

1. Estado inicial sin carpeta.
2. Lote con una sola salida activa.
3. Lote con varias salidas activas.
4. Lote con archivos ignorados técnicos.
5. Miniaturas con PNG transparente.
6. Nombres de archivo largos.
7. Nombres de preset largos.
8. Ajustes con sliders y valores de varios dígitos.
9. Cambio de fondo de revisión.
10. Pan/zoom de imagen.
11. Click exterior y `Escape` en menús.
12. Redimensionado de ventana.
13. Exportación final.

---

## 7. Criterios globales de aceptación

El refactor se considera completo si:

1. La cabecera superior queda limpia y sin contadores redundantes.
2. La pantalla inicial no muestra salida activa de forma prominente antes de cargar carpeta.
3. El visor central está mejor proporcionado para imágenes verticales.
4. La galería izquierda muestra más miniaturas y menos metadata irrelevante.
5. El panel derecho permite gestionar salidas activas y ajustes sin depender de un modal para acciones frecuentes.
6. El gestor de formatos queda como gestor de presets, no como única vía para elegir salidas del lote.
7. Los sliders tienen input numérico editable y no se cortan.
8. El fondo de revisión se controla desde el visor central.
9. La imagen no puede moverse completamente fuera del área visible.
10. No existen botones duplicados con la misma función.
11. El menú de tres puntos, si existe, se comporta correctamente.
12. La interfaz reduce textos y subtítulos innecesarios.
13. No se rompen las funciones actuales de carga, revisión y exportación.

---

## 8. Restricciones de implementación

- No eliminar funcionalidad existente sin reemplazo equivalente.
- No hardcodear datos del ejemplo de las capturas.
- No crear una UI sólo visual sin conectar al estado real.
- No introducir una segunda librería de iconos si ya existe una fiable en el proyecto.
- No cambiar la lógica de exportación salvo necesidad justificada.
- No esconder errores reales: sólo ocultar ruido técnico irrelevante del flujo principal.
- Mantener compatibilidad con el entorno local actual del proyecto.

---

## 9. Prompt sugerido para Codex

```text
Lee el documento `flatshot_ux_ui_refactor_codex.md` situado en la raíz del proyecto e implementa el refactor UX/UI descrito para FlatShot.

Objetivo: mejorar la interfaz actual sin romper la lógica existente de carga, revisión y exportación. La prioridad es reducir redundancia, hacer el panel derecho más accionable, mejorar el layout para imágenes verticales, limpiar la cabecera, mejorar la galería, eliminar modales innecesarios para ajustes frecuentes y corregir errores de CSS/spacing/overflow.

Trabaja por fases:

1. Audita los componentes actuales y localiza cabecera, empty state, layout principal, galería, visor, panel derecho, gestor de formatos, ajustes de imagen y menús.
2. Normaliza el sistema visual: botones, tarjetas, inputs, chips, sliders, paddings, radios, focus states e iconos.
3. Limpia la cabecera superior: sólo logo/nombre a la izquierda, acciones consistentes a la derecha, sin contadores redundantes. Elimina o corrige el menú de tres puntos según el documento.
4. Rediseña la pantalla inicial sin carpeta: icono de librería fiable, CTA claro, sin mostrar salida activa como información principal.
5. Ajusta el layout principal de tres columnas: galería izquierda más útil, visor central menos ancho y más adecuado para imágenes verticales, panel derecho estable.
6. Refactoriza la galería: más miniaturas visibles, menos metadata, sin badge repetitivo “Lista”, filtro oculto si no tiene opciones reales, preview basada en el preset principal.
7. Refactoriza el visor: toolbar compacta, nombre alineado, sin etiqueta inferior redundante, fondo de revisión integrado, sin sombreado decorativo, pan/drag limitado para que la imagen no pueda salir completamente de la vista.
8. Convierte el panel derecho en un panel operativo: mostrar todas las salidas activas, permitir activar/desactivar salidas, editar parámetros frecuentes inline, distinguir cambios temporales/guardar preset/guardar como nuevo, integrar ajustes de imagen sin duplicar botones.
9. Replantea el panel de formatos como gestor de presets: simplifica selector lateral, muestra nombres completos, reduce chips redundantes y sincroniza estado activo con el lote.
10. Sustituye sliders por controles con slider + input numérico editable, sin clipping, con validación de rangos.
11. Elimina duplicidades funcionales como “Detalle lote”/“Ver detalle” y “Ajustar imagen”/“Editar ajuste” si llevan al mismo sitio.
12. Ejecuta build/lint/tests disponibles y corrige regresiones.

No hagas cambios cosméticos aislados: implementa una estructura coherente y conectada al estado real de la app. No hardcodees valores de las capturas. Mantén la funcionalidad existente y documenta brevemente en tu respuesta qué componentes has cambiado y qué queda pendiente si algo no puede completarse.
```
