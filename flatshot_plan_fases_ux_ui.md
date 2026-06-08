# FlatShot — Plan por fases para consolidación UX/UI

## 1. Objetivo del documento

Este documento define un plan de implementación progresivo para corregir las inconsistencias UX/UI detectadas en FlatShot tras el último refactor. La prioridad no es rehacer la interfaz completa de una vez, sino consolidarla mediante fases independientes, verificables y ordenadas.

El objetivo final es que FlatShot pase de una interfaz parcialmente mejorada a una herramienta visualmente coherente, operativa y profesional para revisar y exportar imágenes de producto, especialmente imágenes verticales de e-commerce.

---

## 2. Diagnóstico actual resumido

La interfaz ha evolucionado positivamente respecto a versiones anteriores:

- La pantalla inicial está más limpia y ya no muestra información de salida fuera de contexto.
- La cabecera global se ha simplificado.
- La galería izquierda ha eliminado parte del ruido visual.
- El visor central muestra mejor el nombre de archivo y agrupa controles de fondo, navegación y zoom.
- El panel derecho ya funciona como resumen operativo del lote, salidas activas, imagen seleccionada y ajuste aplicado.
- El gestor de salidas es más legible que antes.
- Los ajustes de imagen ya incorporan inputs numéricos junto a sliders.

Sin embargo, aún quedan problemas sistémicos:

- Falta una gramática visual común para botones, cards, inputs, selects, sliders, chips, estados y paneles.
- Hay paddings, alturas, radios y separaciones inconsistentes.
- Algunos elementos parecen pertenecer a sistemas distintos.
- Se mezclan demasiados estados visuales con el mismo verde: activo, seleccionado, principal, acción primaria y modificado.
- El panel derecho sigue teniendo redundancias y acciones con jerarquía débil.
- El gestor de salidas y el detalle de lote siguen teniendo truncados y zonas ambiguas.
- El panel de ajustes de imagen sigue sobreexplicado y con demasiadas capas de títulos.
- El canvas, las miniaturas y el fondo de revisión todavía no comunican de forma inequívoca qué representa la salida real y qué es sólo una ayuda visual.

---

## 3. Principios de implementación

Antes de tocar componentes concretos, Codex debe aplicar estos principios durante todo el refactor:

1. **No rehacer todo de una vez.** Implementar fase por fase, validando cada bloque antes de pasar al siguiente.
2. **No hardcodear datos de las capturas.** Usar siempre el estado real de la app.
3. **No romper lógica existente.** Mantener carga de lote, selección de imágenes, presets, ajustes y exportación.
4. **Reducir redundancia.** Cada dato debe aparecer donde toma sentido operativo, no repetido en varias zonas.
5. **Una acción primaria por zona.** No usar varios botones verdes sólidos compitiendo dentro del mismo bloque.
6. **Separar estados visuales.** Activo, seleccionado, principal, modificado y error no deben comunicarse todos igual.
7. **Ajustar por sistema, no a ojo.** Definir tokens/componentes reutilizables antes de corregir pantallas aisladas.
8. **Mantener la interfaz compacta, pero no comprimida.** Menos texto y menos ruido, sin ocultar decisiones importantes.
9. **Pensar en imágenes verticales.** El visor y el canvas deben optimizarse para formatos tipo 1800×2400.
10. **Validar cada fase.** Ejecutar build/lint/tests disponibles y revisar manualmente los estados afectados.

---

## 4. Orden general de fases

| Fase | Bloque | Objetivo principal | Riesgo si se salta |
|---:|---|---|---|
| 0 | Auditoría y protección | Evitar regresiones y localizar componentes | Cambios dispersos sin control |
| 1 | Sistema visual base | Unificar tokens, componentes y estados | La app seguirá pareciendo inconsistente |
| 2 | Shell, cabecera y layout | Consolidar estructura principal | El resto se ajustará sobre una base inestable |
| 3 | Galería y miniaturas | Mejorar selección visual y preview | El lote seguirá siendo visualmente ruidoso |
| 4 | Visor, canvas y toolbar | Clarificar revisión, fondo y zoom | La zona central seguirá pareciendo ambigua |
| 5 | Panel derecho resumen | Hacerlo operativo y no redundante | Seguirá mezclando resumen, edición y navegación |
| 6 | Edición de salidas y gestor de presets | Resolver exportación/presets con lógica clara | Formularios comprimidos o acciones ambiguas |
| 7 | Ajustes de imagen | Reducir sobreexplicación y mejorar precisión | Panel técnico pesado y poco escalable |
| 8 | Detalle lote y auditoría | Convertir detalle en vista informativa clara | Seguirá compitiendo con configuración |
| 9 | Microinteracciones, responsive y QA | Cerrar comportamiento profesional | Persistirán errores pequeños de producto |

---

# Fase 0 — Auditoría inicial y protección contra regresiones

## Objetivo

Preparar el terreno antes de modificar la interfaz para que los cambios sean localizables, reversibles y verificables.

## Acciones

- [ ] Crear una rama específica para este refactor, por ejemplo `ui-system-consolidation`.
- [ ] Localizar los componentes actuales de:
  - cabecera global;
  - empty state;
  - shell de tres columnas;
  - galería izquierda;
  - visor central;
  - panel derecho;
  - detalle de lote;
  - gestor de salidas/presets;
  - panel de ajustes de imagen;
  - sliders, inputs, selects, botones, chips, cards y overlays.
- [ ] Identificar estilos duplicados o definidos localmente dentro de componentes.
- [ ] Documentar brevemente dónde vive cada bloque antes de cambiarlo.
- [ ] Capturar estado visual de referencia para:
  - app sin carpeta;
  - lote cargado;
  - detalle de lote;
  - gestor de salidas;
  - ajustes principales;
  - ajustes avanzados.

## Criterios de aceptación

- Existe una lista clara de archivos/componentes afectados.
- No se ha modificado aún la UI funcional.
- Hay una referencia visual previa para comparar.
- Se puede revertir esta fase sin afectar lógica de negocio.

---

# Fase 1 — Sistema visual base: tokens, componentes y estados

## Objetivo

Unificar la gramática visual antes de seguir corrigiendo pantallas. Esta fase es prioritaria porque muchos errores actuales vienen de componentes parecidos, pero no idénticos.

## Acciones

### 1.1. Definir tokens visuales

Crear o consolidar variables/tokens para:

```text
Espaciado: 4 / 8 / 12 / 16 / 24 / 32 px
Alturas:
- botón compacto: 32 px
- botón estándar: 36 px
- botón primario global: 40 px, sólo si se justifica
- input/select: 36 px
- grupo de toolbar: 36 px
Radios:
- input/control: 8 px
- card pequeña: 10-12 px
- panel/modal/drawer: 16 px
Paddings:
- panel lateral: 16 px
- card compacta: 12 px
- card normal: 16 px
- modal/drawer: 24 px
```

### 1.2. Crear o normalizar componentes comunes

Revisar o crear componentes reutilizables:

- [ ] `Button`
- [ ] `IconButton`
- [ ] `PanelCard`
- [ ] `SectionHeader`
- [ ] `SegmentedControl`
- [ ] `ThumbnailCard`
- [ ] `PresetRow`
- [ ] `SliderField`
- [ ] `NumberInput`
- [ ] `SideSheet` / `Drawer`
- [ ] `ModalShell`
- [ ] `StatusBadge`
- [ ] `ActionLink`

### 1.3. Definir gramática de estados

Separar visualmente estos estados:

| Estado | Uso | Tratamiento visual recomendado |
|---|---|---|
| Seleccionado | Elemento actualmente abierto | borde verde + fondo verde muy suave |
| Activo | Participa en el lote | checkbox marcado |
| Principal | Preset prioritario | badge pequeño “Principal” |
| Modificado | Cambios no guardados o alterados | texto/badge ámbar suave, no verde |
| Acción primaria | Acción principal de una zona | botón verde sólido |
| Acción secundaria | Acción disponible pero no principal | outline o ghost |
| Error/incidencia | Problema real | rojo/ámbar según severidad |
| Disabled | Acción no disponible | opacidad + cursor/estado coherente |

## Criterios de aceptación

- Botones, cards, inputs, selects, sliders y badges comparten altura, padding, radio y estados.
- No hay dos botones verdes sólidos compitiendo dentro de una misma zona salvo justificación explícita.
- Verde no se usa indistintamente para todo.
- Los componentes empiezan a reutilizarse en varias pantallas.

## No hacer en esta fase

- No rediseñar aún la galería completa.
- No cambiar la lógica de presets.
- No tocar exportación.
- No modificar nombres de datos ni reglas de negocio.

---

# Fase 2 — Shell principal, cabecera global y layout de tres columnas

## Objetivo

Consolidar la estructura base de la app para que las demás fases se ajusten sobre un layout estable.

## Acciones

### 2.1. Cabecera global

Mantener la cabecera superior limpia:

- Izquierda:
  - icono/logo de FlatShot;
  - nombre de la app.
- Derecha:
  - `Exportar X archivos`;
  - `Salida`;
  - `Carpeta`;
  - `Nuevo lote`.

Corregir:

- [ ] alturas de botones;
- [ ] padding horizontal;
- [ ] separación entre acciones;
- [ ] estados hover/focus;
- [ ] alineación vertical;
- [ ] jerarquía entre botón primario y secundarios.

Eliminar o revisar:

- [ ] cualquier contador junto al nombre de app;
- [ ] menú de tres puntos si sólo contiene una acción;
- [ ] acciones redundantes en cabecera.

### 2.2. Empty state

Ajustar la pantalla sin carpeta:

- Usar terminología coherente: `Gestionar salidas` en vez de `Configurar salidas` si se mantiene esa acción.
- Si el área no soporta drag & drop, evitar que el borde punteado sugiera una dropzone.
- Si sí soporta drag & drop, reforzar el texto para indicarlo.
- Mantener el CTA principal `Seleccionar carpeta` como acción dominante.

### 2.3. Layout de tres columnas

Definir una estructura estable:

```css
grid-template-columns:
  clamp(300px, 18vw, 360px)
  minmax(640px, 1fr)
  clamp(320px, 20vw, 380px);
```

Ajustar según implementación real, pero respetando la intención:

- galería izquierda suficientemente ancha para dos columnas cómodas;
- visor central optimizado para imagen vertical;
- panel derecho compacto, no formulario avanzado comprimido;
- scroll interno por zona;
- sin scroll global innecesario.

## Criterios de aceptación

- La cabecera global no contiene redundancia.
- Los botones de la cabecera comparten sistema visual.
- La pantalla inicial tiene jerarquía clara.
- El shell de tres columnas es estable en ventana ancha y mediana.
- El panel derecho no se deforma cuando el visor cambia de zoom/fondo.

---

# Fase 3 — Galería izquierda y miniaturas

## Objetivo

Convertir la galería en una herramienta visual de selección rápida, con menos ruido y mayor coherencia con el preset principal.

## Acciones

### 3.1. Jerarquía del panel

Estructura recomendada:

```text
Lote
27 imágenes listas
[Lista] [Miniaturas]
[Buscar referencia...]
Grid/lista de imágenes
```

Cambios:

- [ ] Cambiar `27 listas` por `27 imágenes listas` o `27 exportables`.
- [ ] Mostrar la `x` del buscador sólo cuando haya texto introducido.
- [ ] Mantener selector Lista/Miniaturas con el mismo componente `SegmentedControl` usado en otras zonas.
- [ ] No incluir ignorados técnicos en el contador principal.

### 3.2. Tarjetas de miniatura

Cada tarjeta debe mostrar sólo:

- preview visual;
- nombre base/referencia.

No mostrar en miniaturas:

- formato PNG/JPG;
- tamaño de archivo;
- badge textual repetido;
- estado `Lista` repetido en cada miniatura.

Estados:

- normal: borde neutro casi invisible;
- hover: borde suave;
- seleccionada: borde verde + fondo verde muy leve;
- incidencia: icono discreto, no texto invasivo.

### 3.3. Preview según preset principal

Definir una regla clara:

- Si las miniaturas representan origen, mantener damero para transparencia.
- Si representan salida principal, aplicar el fondo/formato visual del preset principal.

Recomendación para esta app:

- Usar el preset principal activo para la preview cuando sea viable.
- Si el preset principal es `JPG gris claro`, la miniatura debe usar fondo gris claro.
- Si el preset principal es `PNG transparente`, puede usar damero.

## Criterios de aceptación

- No aparece `✓ Lista` repetido en miniaturas.
- El contador del panel es semánticamente claro.
- El buscador no muestra limpiar si está vacío.
- Las miniaturas tienen menos marco visual.
- La miniatura seleccionada se distingue sin saturar.
- La preview no contradice el preset principal activo.

---

# Fase 4 — Visor central, canvas, fondo de revisión y toolbar

## Objetivo

Hacer que el visor central comunique con claridad qué se está revisando, sobre qué fondo y con qué escala, sin parecer una composición arbitraria.

## Acciones

### 4.1. Toolbar del visor

Estructura recomendada:

```text
[Nombre de archivo]    [Gris | Blanco | Transparente] [‹ 6/27 ›] [Encajar | Alto | 1:1] [- 93% +]
```

Corregir:

- [ ] El nombre de archivo debe mostrarse completo siempre que quepa.
- [ ] Si se trunca, usar ellipsis al final y tooltip/title con el nombre completo.
- [ ] Los controles no deben comprimir el nombre hasta dejarlo inútil.
- [ ] Todos los grupos de toolbar deben tener la misma altura y radio.
- [ ] El selector de fondo no debe parecer una mezcla entre radio buttons y segmented control.
- [ ] Eliminar puntos/círculos residuales antes de los controles si no tienen función clara.

### 4.2. Selector de fondo de revisión

Usar un `SegmentedControl` real:

```text
[Gris] [Blanco] [Transparente]
```

Reglas:

- El fondo elegido afecta sólo al canvas/área de previsualización.
- No afecta a la interfaz general.
- No debe confundirse con el preset de exportación si sólo es fondo de revisión.
- Si se necesita aclaración, usar label discreto `Fondo de revisión`, no subtítulos largos.

### 4.3. Canvas central

Revisar:

- [ ] proporción exacta según salida principal activa cuando aplique;
- [ ] max-height calculado para aprovechar la vertical;
- [ ] max-width controlado por proporción vertical;
- [ ] imagen centrada;
- [ ] sin sombras decorativas externas;
- [ ] borde sutil si ayuda a distinguir salida/interfaz;
- [ ] pan limitado para que la imagen no pueda perderse fuera de vista.

## Criterios de aceptación

- El visor se entiende como zona de revisión, no como decoración.
- La imagen vertical aprovecha mejor el alto disponible.
- El fondo de revisión no se confunde con el fondo general de la app.
- Los controles del visor parecen del mismo sistema.
- El usuario no puede desplazar la imagen hasta perderla completamente.

---

# Fase 5 — Panel derecho como resumen operativo

## Objetivo

Convertir el panel derecho en una zona compacta, accionable y sin redundancia, separando claramente resumen, salidas, imagen y ajuste.

## Estructura recomendada

```text
Lote
Lote listo
27 imágenes listas
Ver detalle

Salidas activas · 2
54 archivos previstos

[✓] JPG gris claro 1800x2400        Principal
    JPG · 1800×2400 · gris claro

[✓] Zalando
    PNG · 1800×2400 · transparente

[ ] JPG blanco 2000x2000
    JPG · 2000×2000 · blanco

[Editar salidas] [Gestionar presets]

Imagen seleccionada
S677633662610.png
PNG · 7.5 MB

Ajuste
Luz cenital · Modificado
Editar ajuste
```

## Acciones

- [ ] Reducir redundancias tipo `Salidas activas`, `2`, `2 salidas`, `54 archivos previstos`.
- [ ] Usar `Salidas activas · 2` como título compacto.
- [ ] Mantener `54 archivos previstos` como dato secundario.
- [ ] Mostrar cada salida como fila de preset con checkbox, nombre y metadata.
- [ ] Usar badge `Principal` sólo para la salida principal.
- [ ] Usar botón verde sólido sólo para la acción principal de la sección.
- [ ] Convertir `Gestionar presets` en botón secundario/outline/ghost si `Editar salidas` es primario.
- [ ] Unificar `Imagen` y `Ajuste aplicado` si reduce ruido sin perder claridad.
- [ ] Mantener `Detalle`/`Ver detalle` con estilo consistente de acción secundaria.

## Criterios de aceptación

- El panel derecho responde rápidamente a: estado del lote, salidas activas, imagen seleccionada y ajuste aplicado.
- No repite la misma información en varias líneas.
- No hay dos botones verdes sólidos compitiendo en la misma card.
- Las salidas activas se entienden sin abrir otro panel.
- La acción para editar ajuste es clara y única.

---

# Fase 6 — Edición de salidas y gestor de presets

## Objetivo

Resolver de forma coherente la edición de salidas y presets, evitando formularios comprimidos en el panel derecho y acciones ambiguas.

## 6.1. Edición rápida de salidas

Al pulsar `Editar salidas`, no comprimir un formulario avanzado dentro del panel derecho estrecho.

Usar una de estas soluciones:

### Opción preferida: drawer lateral derecho expandido

- Anchura recomendada: 440-520 px.
- Anclado a la derecha.
- Scroll interno.
- Footer sticky.
- Mantiene contexto visual del visor si el ancho lo permite.

### Opción alternativa: panel derecho expandible

- El panel derecho se expande temporalmente a 440-520 px.
- No debe romper toolbar ni visor.

### Requisitos del formulario

- [ ] Ningún botón cortado.
- [ ] Ningún texto solapado.
- [ ] Grid de 2 columnas sólo si cabe.
- [ ] En ancho reducido, pasar a 1 columna.
- [ ] Footer con jerarquía clara:
  - `Cancelar`;
  - `Aplicar temporalmente`;
  - `Guardar preset`;
  - `Guardar como nuevo`.

Si hay demasiadas acciones:

- primaria: `Aplicar`;
- secundaria: `Guardar preset`;
- terciaria: `Guardar como nuevo`;
- cancelación como link/botón discreto.

## 6.2. Estados de cambios

Cuando el usuario modifica una salida activa:

- [ ] marcar estado `Cambios temporales`;
- [ ] permitir aplicar sin guardar;
- [ ] permitir guardar sobre preset actual;
- [ ] permitir guardar como nuevo preset;
- [ ] permitir descartar.

No usar textos largos ni explicaciones permanentes.

## 6.3. Gestor de presets

Estructura recomendada:

```text
Gestor de salidas
Crea y edita presets de exportación.

Columna izquierda:
Salidas guardadas
[Nuevo]

[✓] JPG gris claro 1800x2400       Principal
    JPG · 1800×2400 · gris claro

[✓] Zalando
    PNG · 1800×2400 · transparente

[ ] JPG blanco 2000x2000
    JPG · 2000×2000 · blanco

Columna derecha:
JPG gris claro 1800x2400
Activo en este lote · Principal

Formato
Nombre
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

Acciones:

- [ ] `Nuevo` visible.
- [ ] Evitar `Más opciones` si sólo contiene una o dos acciones.
- [ ] Mostrar nombre completo de presets o truncado razonable con tooltip.
- [ ] No duplicar `Activo` si ya lo comunica el checkbox, salvo en header contextual.
- [ ] Convertir `Ejemplo de exportación` en bloque compacto visible o acordeón real. No dejarlo como franja rota.
- [ ] Revisar `Aplicar al lote`: debe significar algo explícito según contexto.

## Criterios de aceptación

- Editar salidas no rompe el panel derecho.
- Los botones de edición no se solapan ni se cortan.
- El gestor de presets permite entender qué presets existen, cuáles están activos y cuál es principal.
- Los nombres de presets son legibles.
- El ejemplo de exportación no parece un componente roto.
- Las acciones de guardar/aplicar no son ambiguas.

---

# Fase 7 — Panel de ajustes de imagen

## Objetivo

Reducir sobreexplicación, mejorar jerarquía y convertir los sliders en controles precisos, compactos y consistentes.

## Estructura recomendada

```text
Editar ajuste
Luz cenital
Global · Modificado
[Volver]

Controles principales
Opacidad       [slider] [20]
Desenfoque     [slider] [30]
Distancia      [slider] [25]
Padding        [slider] [10]

Avanzado · 2 cambios
[expandible]

Ajuste por imagen
Sin ajuste local
[Crear ajuste local]
```

Cuando `Avanzado` está abierto:

```text
Spread         [slider] [0]
Ruido          [slider] [2]
Contacto       [slider] [15]
Escala         [slider] [-12]
Fusión         [slider] [1]
Ángulo         [slider] [180]
Contracción    [slider] [0]
Zoom auto      [✓] Activo
Motor          [Realista V2]
```

## Acciones

- [ ] Cambiar `Ajustes Luz cenital` por `Editar ajuste` + `Luz cenital`.
- [ ] Eliminar duplicidad conceptual entre `Ajuste de aspecto` y `Aspecto`.
- [ ] Reducir etiquetas en mayúscula si no aportan jerarquía real.
- [ ] Mantener `Avanzado` colapsado por defecto si no hay cambios relevantes.
- [ ] Si hay cambios avanzados, indicar `Avanzado · 2 cambios`.
- [ ] Implementar `SliderField` común:
  - label con ancho fijo;
  - slider flexible;
  - input numérico de ancho fijo;
  - valor sin clipping;
  - validación de rango;
  - soporte para valores negativos si el parámetro lo permite;
  - `font-variant-numeric: tabular-nums` para valores.

## Criterios de aceptación

- Los ajustes se entienden sin leer subtítulos técnicos repetidos.
- No hay valores cortados.
- Todos los sliders tienen input manual.
- Avanzado no domina la vista salvo que el usuario lo despliegue.
- La distinción global/local/modificado es clara.

---

# Fase 8 — Detalle del lote como vista de auditoría

## Objetivo

Hacer que `Detalle del lote` sea una vista informativa clara, no una pantalla de configuración que compite con salidas/presets.

## Estructura recomendada

```text
Detalle del lote

Resumen
29 encontrados
27 exportables
2 ignorados técnicos
0 incidencias

Entrada
Carpeta: PNG
Ruta: U:/00_FOTOGRAFÍA/.../04_Codificadas
Imágenes: 27

Salidas activas
1. JPG gris claro 1800x2400 · Principal
   JPG · 1800×2400 · gris claro
   Destino: _SALIDA_PRO
   Ejemplo: S677633662610_PRO.jpg

2. Zalando
   PNG · 1800×2400 · transparente
   Destino: _SALIDA_PRO
   Ejemplo: S677633662610_PRO.png

Ignorados técnicos
2 archivos

Incidencias
Sin incidencias
```

Footer recomendado:

```text
Cerrar | Cambiar carpeta
```

## Acciones

- [ ] Corregir truncados evitables en resumen.
- [ ] Las rutas largas deben truncarse de forma útil, con tooltip o acción de copiar.
- [ ] Si hay varias salidas activas, mostrar los datos por salida, no como si fueran globales.
- [ ] Mantener ignorados técnicos colapsados por defecto.
- [ ] No tratar `Thumbs.db` como incidencia importante.
- [ ] Eliminar `Gestionar presets` del footer salvo que haya una razón funcional fuerte.
- [ ] Si se mantiene acceso a salidas, usar acción discreta dentro de la sección `Salidas activas`.

## Criterios de aceptación

- El detalle informa, no configura.
- Las salidas activas se representan correctamente una a una.
- No hay truncados absurdos en datos importantes.
- Ignorados técnicos no reciben peso visual de incidencia.
- El footer no compite con el panel derecho.

---

# Fase 9 — Microinteracciones, responsive, accesibilidad y QA final

## Objetivo

Cerrar los detalles que hacen que la app se perciba como producto profesional y no como una suma de pantallas corregidas.

## Acciones

### 9.1. Microinteracciones

- [ ] Menús/dropdowns se cierran con click fuera.
- [ ] Menús/dropdowns se cierran con Escape.
- [ ] Drawers/modales se cierran con Escape si no hay cambios sin guardar.
- [ ] Si hay cambios sin guardar, pedir confirmación antes de cerrar.
- [ ] Tooltips para nombres de archivo, presets y rutas truncadas.
- [ ] Estados hover/focus visibles y consistentes.
- [ ] Transiciones muy cortas y discretas, sin efectos decorativos.

### 9.2. Responsive

Revisar en:

- [ ] ventana ancha tipo 1920 px;
- [ ] ventana mediana;
- [ ] ventana con altura reducida;
- [ ] panel de ajustes expandido;
- [ ] gestor de salidas con scroll;
- [ ] detalle lote con varias salidas;
- [ ] lote con nombres largos.

### 9.3. Accesibilidad básica

- [ ] Focus visible en botones, inputs, selects, checkboxes y segmented controls.
- [ ] Labels/aria-labels para controles sin texto visible.
- [ ] Navegación por teclado razonable en paneles y modales.
- [ ] Contraste suficiente en texto secundario.
- [ ] No depender sólo del color para diferenciar estados críticos.

### 9.4. QA funcional

Validar manualmente:

1. App sin carpeta seleccionada.
2. Carga de lote.
3. Lote con una salida activa.
4. Lote con varias salidas activas.
5. Cambio de salida principal.
6. Activar/desactivar salida.
7. Editar salida temporalmente.
8. Guardar preset.
9. Guardar como nuevo preset.
10. Abrir gestor de salidas.
11. Abrir detalle lote.
12. Cambiar fondo de revisión.
13. Cambiar zoom y encaje.
14. Mover imagen y comprobar límites de pan.
15. Editar ajuste global.
16. Editar ajuste avanzado.
17. Crear o modificar ajuste por imagen si existe esa lógica.
18. Exportar lote.

## Criterios de aceptación

- No hay botones cortados o solapados.
- No hay textos importantes truncados sin tooltip.
- No hay overflow horizontal accidental.
- No hay sombras/degradados decorativos que confundan el canvas.
- El comportamiento de cierre de overlays es consistente.
- La app mantiene lógica funcional previa.
- La interfaz se percibe como un sistema único.

---

## 5. Definición de terminado global

El refactor puede considerarse completado cuando se cumplan estos puntos:

- [ ] La interfaz tiene un sistema visual común aplicado a botones, cards, inputs, selects, sliders, chips, toolbar, paneles y overlays.
- [ ] La pantalla inicial es clara y no muestra información fuera de contexto.
- [ ] La cabecera global contiene sólo identidad y acciones globales.
- [ ] La galería izquierda permite seleccionar imágenes visualmente sin ruido repetido.
- [ ] Las miniaturas no contradicen el preset principal o, si muestran origen, eso queda definido como regla.
- [ ] El visor central comunica claramente imagen, fondo de revisión, navegación y zoom.
- [ ] El canvas representa la salida/revisión sin efectos decorativos innecesarios.
- [ ] El panel derecho es operativo, compacto y sin redundancias importantes.
- [ ] La edición de salidas no se comprime en un panel estrecho.
- [ ] El gestor de presets muestra claramente presets guardados, activos y principal.
- [ ] El panel de ajustes reduce subtítulos redundantes y permite valores precisos.
- [ ] El detalle lote funciona como auditoría, no como configuración.
- [ ] Los estados activo, seleccionado, principal, modificado y error se diferencian visualmente.
- [ ] La app funciona correctamente en distintos tamaños de ventana.
- [ ] Build/lint/tests disponibles pasan sin errores.

---

## 6. Secuencia recomendada de commits

Se recomienda trabajar con commits pequeños y verificables:

```text
chore(ui): audit current FlatShot layout and components
feat(ui-system): add shared tokens and base controls
refactor(shell): normalize global header and three-column layout
refactor(gallery): simplify thumbnails and gallery hierarchy
refactor(viewer): consolidate toolbar, canvas and review background
refactor(sidebar): simplify right operational summary
feat(outputs): add expanded output editing flow
refactor(presets): clean preset manager layout and actions
refactor(adjustments): normalize adjustment panel and slider fields
refactor(batch-detail): convert lot detail into audit view
fix(ui): close menus, overflow, focus states and responsive issues
test(ui): validate final FlatShot UX states
```

---

## 7. Instrucción general para Codex

Implementa este plan por fases. No avances a la fase siguiente si la fase actual deja errores visuales evidentes, solapamientos, truncados graves o regresiones funcionales.

Después de cada fase:

1. Resume qué archivos/componentes se han tocado.
2. Ejecuta lint/build/tests disponibles.
3. Indica cualquier decisión tomada o limitación encontrada.
4. Comprueba visualmente los estados afectados.

No conviertas este plan en un rediseño completo desde cero. Aprovecha la lógica existente, consolida componentes, elimina redundancias y corrige la interfaz de forma incremental.
