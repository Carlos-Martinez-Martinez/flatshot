# FlatShot — Informe UX/UI para segunda consolidación con `/goal`

## 0. Propósito del documento

Este informe analiza el estado actual de FlatShot tras la última iteración de refactor UX/UI y define qué debe corregirse a partir de ahora. No plantea rehacer la interfaz desde cero: el estado actual ya es bastante más coherente que las versiones anteriores, pero todavía no está cerrado como producto profesional.

El objetivo de esta nueva pasada es convertir la interfaz actual en un sistema consolidado: menos parches, menos redundancia, menos inconsistencias de espaciado y estados, y más claridad operativa en los flujos principales.

Este documento está pensado para entregarse a Codex en modo `/goal`, de forma que lo implemente completo y de manera secuencial, validando internamente cada bloque antes de pasar al siguiente.

---

## 1. Diagnóstico ejecutivo

FlatShot ha evolucionado correctamente respecto a las propuestas anteriores. La app ya tiene una estructura reconocible:

```text
Seleccionar carpeta → escanear lote → revisar imágenes → ajustar salidas/imagen → exportar
```

Las mejoras principales son claras:

- La pantalla inicial es más limpia y ya no muestra información de salida fuera de contexto.
- La cabecera global está menos saturada.
- La galería izquierda ha eliminado metadata innecesaria y badges repetitivos.
- El nombre de archivo vuelve a mostrarse correctamente.
- El panel derecho ya funciona como resumen operativo.
- El detalle de lote ya distingue ignorados técnicos y salidas activas.
- El gestor de salidas es mucho más legible.
- Los ajustes de imagen ya incorporan inputs numéricos junto a sliders.

Sin embargo, la interfaz todavía no parece terminada porque conserva problemas de segunda capa:

- Hay inconsistencias de padding, altura, borde, radio y densidad entre componentes similares.
- Se siguen mezclando estados visuales: activo, seleccionado, principal, modificado y acción primaria usan recursos demasiado parecidos.
- El panel de ajustes de imagen sigue sobreexplicado y repite encabezados.
- El selector de fondo del visor parece un híbrido entre radio buttons y segmented control.
- El estado de escaneo introduce un layout raro, con columnas laterales vacías y un centro demasiado aislado.
- El panel derecho ha mejorado, pero aún contiene redundancias y microcopy débil.
- El gestor de salidas y el detalle de lote funcionan, pero necesitan una última pasada de jerarquía, densidad y patrones de overlay.
- La app todavía parece una suma de componentes corregidos, no un sistema visual cerrado.

La prioridad ahora no es “embellecer” la interfaz, sino cerrar el sistema: componentes, estados, estructura, interacción y microcopy.

---

## 2. Evolución respecto a las propuestas anteriores

| Área | Evolución positiva | Problemas pendientes | Prioridad |
|---|---|---|---|
| Pantalla inicial | Icono correcto, jerarquía limpia, CTA principal claro, acción secundaria como botón outline. | Card algo genérica; si no hay drag & drop, el borde/espacio debe comportarse como card normal; microcopy puede afinarse. | Media |
| Estado de escaneo | Se muestra feedback de carga y estado global. | Layout extraño: grandes columnas laterales vacías, centro demasiado desnudo, botón superior “Escaneando...” aislado. | Alta |
| Cabecera global | Más limpia, sin contadores junto al logo. | Jerarquía y altura de botones aún debe quedar estrictamente normalizada. | Media |
| Galería izquierda | Mucho más limpia: sin `✓ Lista`, sin peso/PNG por miniatura, nombres claros. | Falta título de panel claro; tabs demasiado protagonistas; buscador y contador deben alinearse mejor; preview debe representar la salida principal de forma inequívoca. | Alta |
| Visor central | Nombre de archivo visible, controles agrupados, canvas vertical claro. | Selector de fondo no está bien resuelto; aparece un punto/radio residual; toolbar aún parece ensamblada por piezas; relación entre canvas, fondo de revisión y salida real debe aclararse. | Alta |
| Panel derecho resumen | Ahora muestra lote, salidas, imagen y ajuste con mucha más lógica. | Redundancias de texto; `Activa` duplica checkbox; `Listo para procesar` es microcopy débil; demasiados verdes compiten. | Alta |
| Detalle de lote | Mejor auditoría, ignorados técnicos colapsados, varias salidas listadas. | Overlay/drawer no está normalizado; foco del botón cerrar demasiado llamativo; algunas cards duplican datos; salida activa podría leerse mejor por salida. | Media |
| Gestor de salidas | Lista de presets mucho más clara; formulario más legible; acciones más localizadas. | Acción `Aplicar al lote` ambigua; ejemplo de exportación demasiado prominente; columna izquierda muy vacía; se debe normalizar patrón con otros drawers. | Media-Alta |
| Ajustes de imagen | Sliders con inputs numéricos, valores visibles, mejor precisión. | Es la zona menos resuelta: exceso de headers, subtítulos, secciones duplicadas, acciones de gestión mezcladas con edición, demasiado peso de “ajustes guardados”. | Muy alta |

---

## 3. Problema raíz actual

El problema actual no es que falten pantallas ni que la interfaz sea inusable. El problema es sistémico:

> La interfaz ha mejorado por zonas, pero todavía no tiene una gramática visual suficientemente cerrada.

Esto se percibe en detalles como:

- botones visualmente parecidos pero con jerarquías distintas;
- cards con paddings ligeramente diferentes;
- headers de sección que alternan mayúsculas, texto pequeño, chips y títulos normales;
- verdes usados para selección, activación, principal, confirmación y acción primaria;
- overlays que se comportan como drawers pero se perciben como modales;
- campos y controles que a veces parecen de formulario y a veces de toolbar;
- etiquetas de estado que duplican información ya comunicada por checkboxes o selección.

La nueva iteración debe reducir esa fricción. Codex debe aplicar reglas de sistema, no hacer ajustes a ojo por captura.

---

## 4. Reglas visuales transversales obligatorias

### 4.1. Tokens de espaciado

Usar una escala única:

```text
4 / 8 / 12 / 16 / 24 / 32 px
```

Recomendación:

- 4 px: microseparación interna entre icono/texto.
- 8 px: separación entre controles relacionados.
- 12 px: gap de cards compactas.
- 16 px: padding de paneles laterales y cards estándar.
- 24 px: padding interno de modales/drawers.
- 32 px: separación grande entre bloques principales.

### 4.2. Alturas de controles

```text
Botón compacto: 32 px
Botón estándar: 36 px
Botón primario global: 40 px, sólo si se justifica
Input/select: 36 px
Grupo de toolbar: 36 px
Control segmentado: 32-36 px
```

No debe haber botones de la misma jerarquía con alturas distintas.

### 4.3. Radios

```text
Control/input: 8 px
Card pequeña: 10-12 px
Panel/drawer/modal: 16 px
```

### 4.4. Gramática de estados

Separar visualmente estos conceptos:

| Estado | Tratamiento recomendado | No hacer |
|---|---|---|
| Seleccionado | Borde verde + fondo verde muy suave | No usar checkbox para selección actual |
| Activo | Checkbox marcado | No añadir badge `Activa` si el checkbox ya lo comunica |
| Principal | Badge pequeño `Principal` | No convertirlo en botón ni hacerlo competir con activo |
| Modificado | Texto/badge ámbar o neutro destacado | No usar el mismo verde de activo |
| Acción primaria | Botón verde sólido | No usar dos primarios en la misma zona |
| Acción secundaria | Outline o ghost | No usar verde sólido si no es acción principal |
| Peligro | Rojo/ámbar suave | No mezclar con estados de activo |
| Disabled | Opacidad, cursor y contraste adecuados | No dejar botones activos visualmente si no funcionan |

---

## 5. Análisis por zona y correcciones necesarias

# 5.1. Pantalla inicial sin carpeta

## Estado actual

La pantalla inicial está bastante bien resuelta. La card central tiene jerarquía clara, icono correcto, CTA principal y acción secundaria.

## Problemas

- La card tiene un aspecto algo genérico, pero no crítico.
- Si la zona no admite drag & drop, no debería sugerir dropzone mediante exceso de borde/espacio.
- El texto `Gestionar salidas` está bien, pero debe mantener el mismo lenguaje que el resto de la app.

## Correcciones

- Mantener la estructura actual.
- Verificar si admite arrastrar carpeta/imágenes:
  - si sí: añadir microcopy discreto `También puedes arrastrar una carpeta aquí`;
  - si no: no usar patrón visual de dropzone.
- Mantener `Seleccionar carpeta` como único botón primario.
- Mantener `Gestionar salidas` como secundario outline.
- Alinear la card con los mismos tokens de padding/radio/borde del resto.

## Criterios de aceptación

- La pantalla inicial no muestra información de salida activa.
- Hay una única acción primaria.
- El estilo de card coincide con el sistema común.

---

# 5.2. Estado de escaneo

## Estado actual

El estado de escaneo muestra feedback, pero el layout es débil. Aparecen grandes columnas laterales azuladas/grisáceas sin contenido, un centro blanco muy aislado y un botón superior derecho `Escaneando...` que parece una acción bloqueada.

## Problemas

- Parece un shell parcialmente cargado, no un estado de proceso diseñado.
- Las columnas laterales vacías dan sensación de interfaz rota o incompleta.
- El mensaje central es correcto, pero no aprovecha bien el contexto.
- El botón superior `Escaneando...` puede confundirse con una acción, aunque esté deshabilitado.

## Correcciones

Implementar uno de estos dos patrones, no una mezcla:

### Opción A — Estado de escaneo centrado

- Ocultar temporalmente los paneles laterales hasta tener datos.
- Mostrar una card/estado central:

```text
Escaneando carpeta…
Analizando imágenes y preparando salidas.
[spinner/progress]
```

- En la cabecera, mostrar un indicador pasivo de estado, no un botón primario.

### Opción B — Shell con skeleton real

- Mantener la estructura de tres columnas.
- Mostrar skeletons de galería, visor y panel derecho.
- No dejar columnas planas sin contenido.
- El centro debe mostrar el estado de escaneo dentro del visor.

Recomendación: usar Opción A si el escaneo es rápido; Opción B si puede tardar varios segundos.

## Criterios de aceptación

- El estado de escaneo no parece una pantalla rota.
- No hay columnas laterales vacías sin función.
- El usuario entiende que la app está trabajando.
- `Escaneando...` no parece un botón accionable si no lo es.

---

# 5.3. Cabecera global

## Estado actual

La cabecera está limpia y conserva acciones globales claras.

## Problemas

- El botón principal y los secundarios deben normalizarse exactamente.
- Los botones secundarios no deben variar en altura/padding.
- El estado `Escaneando...` no debe ocupar el mismo rol visual que `Exportar` si no es una acción.

## Correcciones

Estructura estable:

```text
[FlatShot]                                      [Exportar X archivos] [Salida] [Carpeta] [Nuevo lote]
```

Reglas:

- `Exportar X archivos`: primario verde.
- `Salida`, `Carpeta`, `Nuevo lote`: secundarios outline.
- `Escaneando...`: estado pasivo o botón deshabilitado con apariencia claramente disabled.
- No añadir contadores junto al logo.
- No reintroducir menú de tres puntos si no contiene varias acciones reales.

## Criterios de aceptación

- Una sola acción primaria global.
- Botones alineados verticalmente.
- Estados disabled reconocibles.

---

# 5.4. Galería izquierda

## Estado actual

La galería ha mejorado mucho. Ya no hay badge `✓ Lista`, ni metadata de PNG/MB en cada miniatura. Las miniaturas son más limpias y se lee el nombre de archivo.

## Problemas

- Falta un header de panel claro. El panel empieza con `Lista / Miniaturas`, pero no con `Lote` o una estructura jerárquica sólida.
- `27 imágenes listas` está bien, pero queda demasiado separado conceptualmente del selector de vista.
- La búsqueda debe mostrar el botón de limpiar sólo cuando haya texto.
- La miniatura parece usar un fondo gris uniforme, pero no queda claro si representa origen, fondo de revisión o preset principal.
- Las miniaturas ocupan bien el ancho, pero el ritmo vertical puede optimizarse.

## Correcciones

Estructura recomendada:

```text
Lote                         [Lista] [Miniaturas]
27 imágenes listas
[Buscar referencia…]

[grid de miniaturas]
```

Reglas:

- El título `Lote` debe volver o existir como encabezado claro.
- El selector `Lista / Miniaturas` debe estar alineado a la derecha del título o inmediatamente debajo, pero no ser el primer elemento dominante sin contexto.
- El contador debe ser claro: `27 imágenes listas` o `27 exportables`. No usar `27 listas`.
- El buscador debe ser compacto, con icono discreto y `x` sólo si hay texto.
- Las miniaturas deben representar una de estas dos cosas de forma explícita:
  - preset principal activo, preferido;
  - imagen de origen, si generar preview final tiene coste excesivo.
- Si representan el preset principal, el fondo debe coincidir con ese preset.
- Si representan origen, no usar un fondo que pueda confundirse con salida final.
- La miniatura seleccionada: borde verde + fondo verde muy suave.
- El estado exportable no debe comunicarse con badge textual repetido.

## Criterios de aceptación

- El panel tiene jerarquía clara.
- No hay badges invasivos por miniatura.
- El usuario distingue la imagen seleccionada.
- El fondo de miniatura tiene una semántica definida.

---

# 5.5. Visor central, canvas y toolbar

## Estado actual

El visor central está mucho mejor que antes. El nombre de archivo se ve, el canvas vertical está centrado y los controles de fondo/navegación/zoom están agrupados.

## Problemas

- El selector de fondo todavía parece un híbrido entre radio buttons y segmented control.
- Se ve un punto/círculo residual antes del control de fondo. Debe eliminarse.
- `Gris`, `Blanco`, `Transparente` aparecen con radios internos. Si es segmented control, no debe llevar radios visuales.
- La toolbar parece compuesta por controles de sistemas distintos.
- El canvas gris puede confundirse con fondo de salida real si no está bien definido.
- La imagen podría aprovechar algo mejor el alto útil, siempre que no rompa la proporción de salida.

## Correcciones

Toolbar recomendada:

```text
[NombreArchivo.png]        [Gris] [Blanco] [Transparente]   [‹] 6/27 [›]   [Encajar] [Alto] [1:1]   [-] 93% [+]
```

Reglas:

- El nombre de archivo debe estar alineado con la toolbar y tener prioridad de espacio.
- Los controles deben usar el mismo componente base de botón/segmento.
- El selector de fondo debe ser un segmented control real:
  - sin radios visibles;
  - estado activo claro;
  - borde y altura iguales al resto.
- Quitar cualquier punto, radio oculto, pseudo-elemento o residuo visual antes del selector.
- `Fondo de revisión` puede existir como tooltip/aria-label, no necesariamente como texto visible.
- El fondo de revisión sólo afecta al canvas.
- El canvas representa la salida o revisión, no la interfaz.
- Evitar sombras/degradados externos que no formen parte del preset o del render de la prenda.

## Criterios de aceptación

- No hay radios/puntos residuales en la toolbar.
- Todos los controles de toolbar parecen del mismo sistema.
- El canvas tiene una semántica clara.
- El nombre de archivo nunca se trunca de forma agresiva si hay espacio.

---

# 5.6. Panel derecho resumen

## Estado actual

El panel derecho funciona bastante mejor. Tiene secciones claras: lote, salidas, imagen seleccionada y ajuste.

## Problemas

- `Salidas activas · 2` y luego `Listo para procesar` no es la mejor jerarquía. `Listo para procesar` suena a estado general, no a salidas.
- El badge `Activa` duplica el checkbox marcado.
- Hay demasiados verdes: checkbox, principal, activa, botón primario, links.
- `Detalle` como link verde debe alinearse con una variante de `ActionLink`, no parecer texto suelto.
- La sección de imagen y ajuste podría ser más compacta sin perder claridad.

## Correcciones

Estructura recomendada:

```text
Lote
Lote listo
27 imágenes listas · ignorados técnicos en detalle
[Ver detalle]

Salidas activas · 2
54 archivos previstos

[✓] JPG gris claro 1800x2400           Principal
    JPG · 1800 × 2400 · gris claro

[✓] Zalando
    PNG · 1800 × 2400 · transparente

[ ] JPG blanco 2000x2000
    JPG · 2000 × 2000 · blanco

[Editar salidas] [Gestionar presets]

Imagen seleccionada
S677633662610.png
PNG · 7.5 MB

Ajuste
Luz cenital · Global · Modificado
[Editar ajuste]
```

Reglas:

- Eliminar badge `Activa` si hay checkbox.
- Mantener badge `Principal`, pero discreto.
- `Editar salidas`: botón primario de la card.
- `Gestionar presets`: botón secundario outline.
- `Detalle` debe renombrarse a `Ver detalle` si se quiere coherencia con acción.
- No repetir `2 salidas`, `2 activas`, `Listo para procesar` en varios niveles.
- `Modificado` no debería usar el mismo tratamiento verde que activo.

## Criterios de aceptación

- Una sola acción primaria dentro de la card de salidas.
- No hay estados duplicados por checkbox + badge.
- El panel se lee de arriba abajo como resumen operativo.

---

# 5.7. Detalle del lote

## Estado actual

El detalle de lote ha mejorado. Ya es más auditoría y menos configuración. Lista resumen, entrada, lote, salidas activas, ignorados técnicos e incidencias.

## Problemas

- El overlay se comporta como drawer/modal híbrido. Debe normalizarse como `SideSheet` o `ModalShell` de sistema.
- El botón de cerrar muestra un foco/borde verde demasiado fuerte en algunas capturas. El focus visible es necesario, pero no debe parecer estado permanente ni competir visualmente.
- Hay duplicidad entre `Resumen` y `Lote`.
- Algunas rutas se truncarán inevitablemente, pero deben tener tooltip/title o acción de copia.
- Las salidas activas están mucho mejor, pero cada salida debe funcionar como bloque independiente.
- El footer debe limitarse a acciones realmente propias del detalle.

## Correcciones

- Convertirlo en patrón estable de overlay:
  - si es drawer: anclado a la derecha, ancho consistente, overlay opcional;
  - si es modal: centrado, no anclado a derecha.
- Recomendación: usar `SideSheet` para detalle y gestor, con ancho 720-860 px según contenido.
- Normalizar botón cerrar:
  - foco visible sólo al navegar con teclado o cuando corresponda;
  - sin borde verde permanente tras click de ratón.
- Reducir duplicidad:
  - `Resumen`: encontrados, exportables, ignorados técnicos, incidencias.
  - `Lote`: sólo estado y detalles específicos si no están en resumen.
- Asociar destino/ejemplo a cada salida activa.
- Mantener `Ignorados técnicos` colapsado salvo que el usuario lo abra.
- Footer recomendado:

```text
Cerrar | Cambiar carpeta
```

No añadir `Gestionar presets` en el footer salvo que sea imprescindible.

## Criterios de aceptación

- El detalle no parece un gestor de configuración.
- Las salidas múltiples se leen correctamente.
- No hay foco visual permanente en cerrar.
- No hay truncados evitables en datos importantes.

---

# 5.8. Gestor de salidas / presets

## Estado actual

El gestor es mucho mejor que antes. La lista de presets es legible, el formulario está ordenado y las acciones superiores están más claras.

## Problemas

- Sigue existiendo mucho vacío en columna izquierda y mucha densidad en columna derecha.
- `Aplicar al lote` puede ser ambiguo: no queda claro si guarda, activa, aplica cambios temporales o sólo actualiza el lote.
- `Ejemplo` ocupa mucho peso visual para ser información auxiliar.
- Algunas acciones superiores (`Nuevo`, `Duplicar`, `Restaurar`, `Eliminar`) deben estar condicionadas al contexto y no competir demasiado.
- La relación entre checkbox activo, badge `Principal` y chip `Activo en este lote · Principal` debe ser sistemática.
- El gestor debe compartir patrón de overlay con el detalle de lote.

## Correcciones

Estructura recomendada:

```text
Gestor de salidas
Crea y edita presets de exportación.

[Columna izquierda]
Salidas guardadas                 [Nuevo]
[Duplicar] [Restaurar] [Eliminar] sólo si aplican, o dentro de menú contextual real

[✓] JPG gris claro 1800x2400       Principal
    JPG · 1800 × 2400 · gris claro
    _SALIDA_PRO

[✓] Zalando
    PNG · 1800 × 2400 · transparente
    _SALIDA_PRO

[ ] JPG blanco 2000x2000
    JPG · 2000 × 2000 · blanco
    _SALIDA_PRO

[Panel derecho]
JPG gris claro 1800x2400
Activo en este lote · Principal

Formato
Nombre del formato
Archivo
Fondo

Tamaño
Anchura
Altura

Destino
Ubicación
Carpeta de salida

Nombre de archivo
Sufijo
Plantilla

Ejemplo
S677633662610_PRO.jpg
```

Reglas:

- `Principal` puede aparecer como badge en lista y header derecho, pero no debe repetirse de forma invasiva.
- Checkbox comunica activo. No añadir badge `Activa`.
- El ejemplo debe ser compacto, no una card excesivamente grande.
- Si hay cambios sin guardar, mostrar estado claro:
  - `Cambios pendientes`;
  - activar `Guardar cambios`.
- Renombrar botón según acción real:
  - `Aplicar al lote` si sólo aplica selección actual;
  - `Guardar y aplicar` si guarda cambios y aplica;
  - `Activar en este lote` si activa un preset inactivo.

## Criterios de aceptación

- El usuario entiende qué preset está seleccionado, cuál está activo y cuál es principal.
- No hay acciones ambiguas.
- El ejemplo no domina la pantalla.
- El overlay comparte patrón con detalle de lote.

---

# 5.9. Panel de ajustes de imagen

## Estado actual

Es la zona más problemática en el estado actual. Los sliders con inputs han mejorado funcionalmente, pero la estructura sigue demasiado pesada.

## Problemas principales

### 5.9.1. Encabezados duplicados

Aparecen capas como:

```text
Editar ajuste
Luz cenital

EDITAR AJUSTE
Luz cenital

AJUSTE
Controles principales
Ajuste global del lote

AVANZADO
Avanzado · 2 cambios
Procesamiento avanzado

IMAGEN SELECCIONADA
Ajuste por imagen
Sin ajuste local
```

Esto es redundante. La pantalla dice demasiadas veces que se está editando un ajuste.

### 5.9.2. Gestión de ajustes mezclada con edición

Cuando se despliega `Editar ajuste`, aparece `Ajustes guardados`, botones como `Guardar cambios`, `Exportar ajustes`, `Eliminar`, `Restaurar`, `Listo`. Esa parte parece más un gestor de presets de ajuste que una edición operativa.

No debe mezclarse toda la gestión de ajustes guardados con el flujo principal de ajustar la imagen/lote.

### 5.9.3. Mayúsculas y subtítulos técnicos

Las etiquetas en mayúscula (`EDITAR AJUSTE`, `AJUSTE`, `AVANZADO`, `IMAGEN SELECCIONADA`) dan sensación de panel administrativo y añaden ruido.

### 5.9.4. Avanzado domina demasiado cuando se despliega

Los parámetros avanzados son útiles, pero deben permanecer colapsados por defecto y no convertir la interfaz principal en un panel técnico si el usuario no lo pide.

## Corrección propuesta

Separar dos modos:

### Modo A — Edición operativa de ajuste

Este debe ser el modo principal al pulsar `Editar ajuste`:

```text
Editar ajuste                         [Volver]
Luz cenital · Global · Modificado

Controles principales
Opacidad       [slider] [20]
Desenfoque     [slider] [30]
Distancia      [slider] [25]
Padding        [slider] [10]

Avanzado · 2 cambios                  [expandir]

Ajuste por imagen
Sin ajuste local
[Crear ajuste local]
```

Si `Avanzado` se despliega:

```text
Spread        [slider] [0]
Ruido         [slider] [2]
Contacto      [slider] [15]
Escala        [slider] [-12]
Fusión        [slider] [1]
Ángulo        [slider] [180]
Contracción   [slider] [0]
Zoom auto     [checkbox] Activo
Motor         [select]
```

### Modo B — Gestión de ajustes guardados

Debe abrirse sólo desde una acción explícita, por ejemplo:

```text
Gestionar ajustes
```

Ahí sí tiene sentido mostrar:

- ajustes guardados;
- guardar cambios;
- exportar ajustes;
- eliminar;
- restaurar.

No debe aparecer de forma dominante dentro del flujo normal de ajuste si no es necesario.

## Reglas para sliders

Crear o consolidar un componente `SliderField`:

```text
Label fijo        [ slider flexible ] [ input numérico fijo ]
```

Reglas:

- labels con ancho estable;
- slider flexible;
- input numérico de 56-64 px;
- `font-variant-numeric: tabular-nums`;
- validación de rango;
- soporte de teclado;
- sin overflow;
- misma altura de fila en todos.

## Criterios de aceptación

- Sólo hay un encabezado claro de edición.
- No se repite `Editar ajuste` varias veces.
- `Ajustes guardados` no invade la edición operativa salvo acción explícita.
- Avanzado está colapsado por defecto.
- Sliders e inputs están perfectamente alineados.

---

# 5.10. Terminología y microcopy

## Cambios recomendados

Usar terminología estable:

| Concepto | Término recomendado |
|---|---|
| Configuración activa de exportación | Salida |
| Configuración guardada reutilizable | Preset de salida |
| Ajuste visual/procesamiento | Ajuste |
| Ajuste aplicado a todo el lote | Ajuste global |
| Ajuste específico de una imagen | Ajuste por imagen |
| Imagen válida para exportar | Imagen lista / exportable |
| Elementos ignorados sin relevancia operativa | Ignorados técnicos |

Evitar:

- `Lista` como badge individual de miniatura.
- `Activa` como badge si hay checkbox.
- `Listo para procesar` dentro de salidas si ya hay `Lote listo`.
- Repetir `Editar ajuste` en varias capas.
- Usar mayúsculas constantes para subtítulos internos.

Microcopy recomendado:

```text
27 imágenes listas
Salidas activas · 2
54 archivos previstos
Ignorados técnicos en detalle
Luz cenital · Global · Modificado
Gestionar ajustes
Gestionar salidas
Ver detalle
```

---

## 6. Fases de implementación para Codex

Codex debe implementar todo este informe en modo `/goal`, pero siguiendo fases internas. No debe pedir confirmación entre fases salvo bloqueo real.

# Fase 0 — Auditoría rápida del estado actual

- Localizar componentes afectados:
  - shell/cabecera;
  - empty state;
  - scanning state;
  - galería;
  - visor/canvas/toolbar;
  - panel derecho;
  - detalle lote;
  - gestor salidas;
  - editor ajustes;
  - componentes comunes.
- Identificar estilos duplicados.
- Confirmar si existe sistema de tokens/componentes comunes.
- Crear o actualizar `UX_UI_REFACTOR_PROGRESS.md`.

# Fase 1 — Cierre del sistema visual base

- Consolidar tokens de espaciado, radios, alturas y bordes.
- Normalizar `Button`, `PanelCard`, `SegmentedControl`, `SliderField`, `SideSheet`, `StatusBadge`, `ActionLink`.
- Separar estados: seleccionado, activo, principal, modificado, disabled, peligro.
- Corregir foco visible para que no quede como estado permanente tras click.

# Fase 2 — Empty state, scanning state y cabecera global

- Mantener empty state, con ajustes menores de card y microcopy.
- Rediseñar estado de escaneo para que no muestre columnas laterales vacías.
- Normalizar cabecera global y estados de botón.
- `Escaneando...` debe ser estado pasivo o disabled claro, no CTA confuso.

# Fase 3 — Galería izquierda

- Reintroducir jerarquía clara de panel: `Lote`, contador, tabs, buscador, grid.
- Ajustar tabs `Lista/Miniaturas` para que no sean el primer elemento sin contexto.
- Asegurar que el buscador sólo muestra `x` cuando hay búsqueda activa.
- Definir y aplicar semántica de miniatura: preset principal o imagen origen.
- Normalizar estados hover/selected.

# Fase 4 — Visor central y toolbar

- Convertir selector de fondo en segmented control real.
- Eliminar punto/radio residual antes del selector de fondo.
- Homogeneizar toolbar: fondo, navegación, encaje, zoom.
- Revisar canvas para distinguir claramente app background, canvas y fondo de revisión.
- Mantener nombre de archivo visible y correctamente truncado sólo si hace falta.

# Fase 5 — Panel derecho resumen

- Reducir redundancias.
- Eliminar badge `Activa` si hay checkbox.
- Mantener `Principal` como badge discreto.
- Ajustar microcopy de salidas activas.
- Unificar `Ver detalle`, `Editar salidas`, `Gestionar presets`, `Editar ajuste` como acciones consistentes.
- Evitar dos botones primarios en la misma card.

# Fase 6 — Detalle de lote y gestor de salidas

- Normalizar overlay como `SideSheet` o `ModalShell`, no híbrido inconsistente.
- Corregir foco visual del botón cerrar.
- Reducir duplicidades en detalle de lote.
- Mejorar listado de salidas activas por salida.
- Revisar acciones de footer.
- En gestor de salidas:
  - clarificar acción `Aplicar al lote`;
  - compactar ejemplo;
  - revisar acciones superiores;
  - equilibrar columna izquierda/derecha.

# Fase 7 — Editor de ajustes de imagen

- Reestructurar como edición operativa, no como gestor mezclado.
- Eliminar encabezados duplicados.
- Reducir mayúsculas y subtítulos técnicos.
- Mantener `Avanzado` colapsado por defecto.
- Mover gestión de ajustes guardados a acción explícita o panel separado.
- Consolidar `SliderField`.
- Asegurar inputs numéricos precisos y sin overflow.

# Fase 8 — QA visual, responsive e interacción

- Verificar estados principales.
- Revisar ventana ancha y ventana más estrecha.
- Comprobar overlays, scroll interno, z-index y cierre con Escape/click exterior.
- Ejecutar lint/build/tests.
- Actualizar `UX_UI_REFACTOR_PROGRESS.md` con resultado final.

---

## 7. Criterios de aceptación globales

Codex no debe considerar completado el objetivo hasta cumplir estos puntos:

### Sistema visual

- Botones, inputs, selects, cards, sliders, segmented controls, overlays y badges usan variantes comunes.
- No hay paddings/radios/alturas arbitrarias por componente.
- Verde no se usa para todos los estados.
- No hay dos acciones primarias compitiendo en una misma zona.

### Layout

- La cabecera global está limpia.
- El estado de escaneo no parece una pantalla rota.
- La estructura de tres columnas es estable.
- La galería tiene jerarquía clara.
- El visor está optimizado para formato vertical.
- El panel derecho es resumen operativo, no mezcla desordenada de edición y auditoría.

### Galería

- No hay badges repetidos por miniatura.
- El nombre de archivo/referencia se lee bien.
- El estado seleccionado es claro.
- La semántica del fondo de miniatura está definida.

### Visor

- No hay punto/radio residual en el selector de fondo.
- El selector de fondo es un segmented control real.
- Toolbar homogénea.
- Canvas con semántica clara.

### Panel derecho

- No aparece badge `Activa` duplicando checkbox.
- Las salidas activas se entienden sin redundancia.
- `Principal` es discreto.
- Imagen seleccionada y ajuste aplicado son compactos y claros.

### Detalle de lote

- Overlay normalizado.
- Botón cerrar sin foco permanente extraño.
- Ignorados técnicos con peso visual bajo.
- Salidas activas listadas correctamente.

### Gestor de salidas

- Preset seleccionado, activo y principal no se confunden.
- Acciones del footer tienen significado claro.
- Ejemplo de exportación compacto.
- No hay textos truncados sin tooltip/title cuando son importantes.

### Ajustes de imagen

- Sólo hay un encabezado claro de edición.
- No se repite `Editar ajuste` varias veces.
- `Ajustes guardados` no invade el flujo operativo.
- `Avanzado` está colapsado por defecto.
- Sliders e inputs están alineados y sin overflow.

### Interacción

- Overlays cierran con Escape y click exterior si aplica.
- Focus visible correcto, no permanente tras click de ratón.
- Sin overflow horizontal accidental.
- Scroll interno correcto.
- Lint/build/tests pasan.

---

## 8. Prompt recomendado para Codex en modo `/goal`

Usar este prompt en Codex:

```text
/goal Implementar completo el informe UX/UI definido en `flatshot_informe_uxui_goal_refactor_v2.md`, trabajando por fases internas y sin detenerse hasta dejar implementadas todas las correcciones aplicables.

Lee primero íntegramente `flatshot_informe_uxui_goal_refactor_v2.md` situado en la raíz del proyecto.

Objetivo:
Consolidar la interfaz actual de FlatShot como un sistema UX/UI coherente y profesional, corrigiendo las inconsistencias que persisten tras el último refactor: scanning state, sistema visual, estados, galería, visor, toolbar, panel derecho, detalle de lote, gestor de salidas y editor de ajustes de imagen.

Modo de trabajo obligatorio:
1. No rehagas la app desde cero.
2. No implementes cambios a ojo basados en las capturas.
3. No hardcodees datos concretos de ejemplo.
4. Implementa el informe por fases internas, en el orden indicado.
5. No pidas confirmación entre fases salvo bloqueo real.
6. Después de cada fase, valida que no se han roto estados ya existentes.
7. Crea o actualiza `UX_UI_REFACTOR_PROGRESS.md` con:
   - fase implementada,
   - archivos/componentes tocados,
   - validaciones ejecutadas,
   - decisiones tomadas,
   - deuda técnica restante.

Restricciones:
- No elimines funcionalidades existentes.
- No modifiques la lógica de exportación, carga de carpetas, selección de imágenes, presets o ajustes salvo que sea imprescindible para corregir una incoherencia de UI/estado descrita.
- No introduzcas nuevas librerías salvo necesidad justificada.
- Reutiliza componentes existentes si ya los hay.
- Si un componente común no existe, créalo o consolídalo antes de seguir parcheando pantallas individuales.

Prioridades:
1. Cerrar sistema visual: tokens, botones, cards, inputs, selects, sliders, segmented controls, overlays, badges y estados.
2. Corregir estado de escaneo.
3. Normalizar galería, visor y toolbar.
4. Simplificar panel derecho.
5. Normalizar detalle de lote y gestor de salidas.
6. Reestructurar editor de ajustes de imagen, que es la zona más pendiente.
7. Hacer QA responsive/interacción.

Criterios de finalización:
- Se cumplen todos los criterios de aceptación globales del informe.
- No hay textos ni botones cortados.
- No hay overflow horizontal accidental.
- El selector de fondo no muestra radios ni puntos residuales.
- El panel derecho no duplica estados con checkbox + badge `Activa`.
- El editor de ajustes no repite encabezados ni mezcla gestión de ajustes guardados con edición operativa.
- El estado de escaneo no muestra columnas laterales vacías sin función.
- El detalle y el gestor usan patrones de overlay coherentes.
- Lint/build/tests disponibles pasan.

Al finalizar:
1. Resume fases implementadas.
2. Lista archivos/componentes principales modificados.
3. Indica validaciones ejecutadas y resultados.
4. Indica cualquier deuda técnica pendiente.
5. No cierres el objetivo hasta que todas las fases aplicables estén completadas o justificadamente marcadas como no aplicables.
```

---

## 9. Nota final para Codex

La app ya ha mejorado. Esta iteración no debe volver a iniciar un rediseño completo. Debe actuar como una pasada de consolidación de producto: cerrar patrones, eliminar contradicciones visuales, limpiar microcopy, separar estados y dejar la interfaz lista para uso real.

El mayor riesgo es seguir haciendo correcciones locales. La solución correcta es sistematizar: componentes comunes, tokens, estados y patrones de overlay compartidos.
