# FlatShot — Informe UX/UI para rediseño estructural e implementación en Codex

**Proyecto:** `flatshot`  
**Ámbito:** interfaz de escritorio web/bridge en `apps/flatshot-desktop/frontend`  
**Objetivo:** reorganizar profundamente la UX/UI sin cambiar el motor de procesado ni el resultado de exportación.  
**Prioridad:** claridad operativa, jerarquía de acciones, reducción de redundancia y menor exposición de controles técnicos.

---

## 0. Instrucción directa para Codex

Implementa este documento como una refactorización UX/UI de la interfaz actual de FlatShot.

No es un rediseño decorativo. Es una reorganización funcional de la pantalla para que el usuario pueda:

1. elegir una carpeta;
2. revisar rápidamente qué imágenes se van a exportar;
3. cambiar el formato de salida sólo cuando sea necesario;
4. ajustar una imagen o el lote sólo si detecta un problema visual;
5. exportar sin pantallas intermedias innecesarias cuando no hay incidencias reales.

La app no debe añadir más textos explicativos. Al contrario: debe reducir subtítulos, etiquetas redundantes, términos técnicos y duplicación de datos. La información debe aparecer por jerarquía, no por acumulación.

---

## 1. Contexto técnico comprobado

FlatShot es una herramienta local de escritorio para procesado por lotes de imágenes de producto. La interfaz activa es la app moderna web/bridge en `apps/flatshot-desktop`; el paquete Python aporta motor de imagen, servicios, bridge y CLI.

La app actual:

- usa frontend estático HTML/CSS/JS en `apps/flatshot-desktop/frontend`;
- no requiere Node, Tauri, Rust, Electron, PyQt ni QtAwesome;
- se ejecuta con `python apps/flatshot-desktop/run_dev.py --open`;
- arranca frontend local y bridge local;
- debe preservar el resultado exportado: apariencia de imagen, nombres, destino, formato, calidad, transparencia y DPI salvo petición explícita.

Archivos principales que debe tocar Codex:

```text
apps/flatshot-desktop/frontend/index.html
apps/flatshot-desktop/frontend/styles.css
apps/flatshot-desktop/frontend/ux-foundation.css
apps/flatshot-desktop/frontend/app.js
```

Archivos que no deben modificarse salvo necesidad real:

```text
src/flatshot/core/
src/flatshot/application/
src/flatshot/bridge/
tests/
```

El rediseño debe ser de superficie, estado visual y flujo de interacción. No debe alterar lógica de procesado salvo para eliminar fricción de confirmación cuando no existan incidencias accionables.

---

## 2. Problema principal

La interfaz actual ya tiene una base visual razonable, pero está organizada como si todos los datos tuvieran la misma importancia. Eso genera varios problemas:

- demasiadas acciones visibles a la vez;
- demasiados bloques con bordes;
- demasiados subtítulos;
- repetición de la misma información en barra superior, columna izquierda, visor, panel derecho, modal y barra inferior;
- controles técnicos visibles en el flujo normal;
- pestañas del inspector que compiten con la acción principal;
- estados neutros tratados como incidencias;
- uso ineficiente del espacio horizontal;
- demasiada presencia de controles secundarios frente al objetivo real: revisar y exportar.

La app debería sentirse como una mesa de revisión visual y exportación, no como un panel de configuración técnica.

---

## 3. Objetivo UX

El objetivo final es que la pantalla tenga una jerarquía clara:

### Nivel 1 — acción principal

La acción principal depende del estado:

| Estado | Acción primaria |
|---|---|
| Sin lote | Seleccionar carpeta |
| Escaneando | Escaneando… |
| Lote listo | Exportar N imágenes |
| Exportando | Pausar / detener, con progreso |
| Exportado | Abrir destino o nuevo lote |

Sólo debe haber una acción primaria evidente en cada estado.

### Nivel 2 — revisión

La revisión debe permitir ver:

- imagen seleccionada;
- lista de miniaturas;
- estado de cada imagen;
- conteo de imágenes listas, excluidas, ignoradas o con aviso;
- formato de salida activo.

### Nivel 3 — configuración

La configuración no debe dominar la pantalla. Debe aparecer como:

- resumen compacto de salida;
- botón secundario `Cambiar formato`;
- edición avanzada bajo disclosure;
- modal de gestión de formatos sólo cuando se solicita.

### Nivel 4 — diagnóstico técnico

El diagnóstico técnico debe estar oculto por defecto. Sólo debe aparecer en modo desarrollo (`?dev=1`) o bajo una acción explícita tipo `Ver diagnóstico`.

---

## 4. Diagnóstico de las pantallas actuales

### 4.1 Pantalla sin lote

Problemas observados:

- aparece `Seleccionar carpeta` en varias zonas;
- la columna izquierda muestra `0 imágenes`, lo cual no aporta acción ni información útil;
- el panel derecho repite preparación y CTA;
- el centro tiene un empty state correcto, pero pierde fuerza al competir con el panel derecho;
- hay subtítulos que explican lo evidente;
- la app se percibe vacía pero ya sobrecargada.

Corrección:

- ocultar la galería hasta que exista lote;
- mantener una única acción primaria;
- usar el centro como zona principal de inicio;
- el panel derecho puede mostrar el formato actual, pero no otro CTA duplicado;
- reducir el texto a una frase operativa.

Estado recomendado:

```text
Topbar:
FlatShot · Sin lote                                      [Seleccionar carpeta] [Configurar salida]

Centro:
[icono carpeta]
Selecciona una carpeta de imágenes
PNG o JPG · salida: JPG 1800×2400 gris claro
```

No mostrar:

- `0 imágenes` como bloque dominante;
- otro botón `Seleccionar carpeta` en el panel derecho;
- valores por defecto repetidos en varios sitios.

---

### 4.2 Pantalla de escaneo

Problemas observados:

- sigue existiendo columna izquierda con `0 imágenes`;
- el panel derecho repite estado;
- el visor central comunica bien el proceso, pero queda rodeado de paneles vacíos;
- la barra inferior añade otra línea de estado redundante.

Corrección:

- durante el escaneo, ocultar galería hasta que haya resultados;
- panel derecho mínimo, si existe;
- topbar con estado claro;
- progress bar única;
- no mostrar botones que no puedan usarse.

Estado recomendado:

```text
Topbar:
FlatShot · Escaneando carpeta...                         [Escaneando…]

Centro:
spinner
Escaneando carpeta…
ruta escaneada si cabe en una línea
```

El panel derecho sólo debe aparecer si hay progreso o diagnóstico relevante. Si no, se puede ocultar.

---

### 4.3 Pantalla con lote listo

Problemas observados:

- la estructura base de tres columnas funciona, pero hay demasiada información duplicada;
- el panel derecho tiene cuatro pestañas visibles, aunque la mayoría de usuarios sólo necesita exportar;
- `Resumen`, `Exportación`, `Incidencias`, `Avanzado` tienen el mismo peso visual;
- la galería tiene botones y filtros algo sobredimensionados;
- `Seleccionada` sobre la miniatura añade ruido visual;
- `2 ignorados` aparece como si fuera casi una incidencia, aunque no afecta a la exportación;
- el visor tiene muchos controles visibles;
- el nombre de la imagen se repite en visor, panel derecho y modal.

Corrección:

- mantener tres zonas: galería, visor, inspector;
- hacer que el inspector sea contextual y no una lista de pestañas equivalentes;
- exportación en topbar;
- salida en una tarjeta compacta;
- incidencias sólo si existen incidencias accionables;
- avanzados ocultos;
- miniaturas más limpias;
- selección por borde/estado, no por etiqueta textual superpuesta.

Estructura recomendada:

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ FlatShot · PNG · 29 archivos · 27 listas · 2 ignoradas       [Exportar 27] ⋯ │
├───────────────┬──────────────────────────────────────────────┬───────────────┤
│ Galería       │ Visor principal                              │ Inspector     │
│ Buscar        │ Imagen seleccionada                           │ Lote listo    │
│ Filtros       │ Navegación + zoom mínimo                       │ Salida        │
│ Miniaturas    │ Preview                                       │ Imagen        │
│               │                                               │ Avisos        │
└───────────────┴──────────────────────────────────────────────┴───────────────┘
```

---

### 4.4 Modal `Detalle del lote`

Problemas observados:

- el modal es demasiado grande para información que debería ser secundaria;
- tiene scroll interno aunque el contenido principal podría resumirse mejor;
- mezcla entrada, conteo, salida e incidencias;
- algunas incidencias son realmente elementos ignorados no problemáticos;
- el footer ofrece acciones que compiten con la lectura del diagnóstico.

Corrección:

- mantenerlo como vista de diagnóstico, no como paso normal;
- mostrar primero resumen compacto;
- separar `Ignorados` de `Incidencias`;
- no usarlo como confirmación obligatoria para exportar si no hay errores reales;
- reducir footer a `Cerrar`, `Cambiar carpeta` y, si procede, `Abrir configuración`.

---

### 4.5 Pestaña `Exportación`

Problemas observados:

- repite datos ya visibles en topbar y resumen;
- ocupa mucho panel para una configuración normalmente estable;
- `Cambiar formato` y `Editar campos` son razonables, pero el bloque visual es pesado;
- el usuario necesita saber qué saldrá, no editarlo cada vez.

Corrección:

- convertir `Exportación` en una tarjeta compacta dentro del resumen;
- mover la edición a un subpanel o modal;
- mostrar sólo:
  - formato;
  - tamaño;
  - fondo;
  - destino;
  - nombre final de ejemplo;
  - botón `Cambiar`.

Ejemplo:

```text
Salida
JPG · 1800×2400 · gris claro
_SALIDA_PRO · {original}_PRO.jpg

[Cambiar formato]
```

La edición completa sólo aparece si el usuario pulsa `Cambiar formato`.

---

### 4.6 Pestaña `Incidencias`

Problemas observados:

- `Sin incidencias` aparece como pestaña visible, ocupando el mismo nivel que exportación;
- `2 ignorados` no afecta a la exportación, pero la interfaz le da presencia;
- `Salida · Subcarpeta no escaneada` puede confundir si no afecta al resultado.

Corrección:

- ocultar la sección si no hay incidencias accionables;
- mostrar ignorados como nota neutra en el resumen, no como problema;
- si hay avisos accionables, mostrar un bloque compacto;
- si hay errores que bloquean exportación, elevarlos al topbar y al inspector.

Clasificación recomendada:

| Tipo | Ejemplos | Tratamiento UI |
|---|---|---|
| Neutral | `Thumbs.db`, subcarpeta no escaneada, archivo de sistema | `2 ignorados`, texto gris, sin bloquear |
| Aviso | imagen con transparencia dudosa, tamaño raro, preview fallback | bloque amarillo, exportación permitida |
| Error | archivo ilegible, fallo de render, destino inaccesible | bloque rojo, exportación bloqueada o parcial |

---

### 4.7 Pestaña `Avanzado`

Problemas observados:

- ocupa una pestaña principal;
- mezcla ajuste de sombra, fondo, motor, zoom auto y ajuste por imagen;
- muchos sliders están visibles aunque el flujo normal no los necesita;
- términos como `Opacidad`, `Desenfoque`, `Distancia`, `Padding`, `Fusión`, `Contracción`, `Motor` son útiles para desarrollo o ajuste fino, pero no para el uso normal;
- la pantalla comunica que hay que configurar cosas, cuando lo normal es no tocar nada.

Corrección:

- eliminar `Avanzado` como pestaña principal visible;
- crear un bloque colapsado `Ajustes avanzados`;
- mantener `Ajuste por imagen` como acción contextual discreta, no como bloque fijo;
- mostrar presets como `Aspecto` o `Sombra`, no como panel técnico permanente;
- si `?dev=1`, sí permitir ver todo.

---

## 5. Principios de diseño que debe seguir la implementación

### 5.1 Una pantalla, una acción principal

En cada estado debe haber una acción primaria. No debe haber dos botones principales equivalentes.

Incorrecto:

```text
[Seleccionar carpeta] en topbar
[Seleccionar carpeta] en centro
[Seleccionar carpeta] en panel derecho
```

Correcto:

```text
[Seleccionar carpeta] en topbar
Centro como zona informativa o drop area, sin CTA duplicado
```

O bien:

```text
[Seleccionar carpeta] en el centro
Topbar sin CTA primaria hasta que haya lote
```

Elegir una de las dos estrategias. Recomendación: usar topbar como lugar constante de acción primaria y hacer el empty state clicable, pero sin botón duplicado.

---

### 5.2 El inspector no debe ser navegación principal

El panel derecho debe ser un inspector contextual, no una sección de navegación con cuatro pestañas igualmente importantes.

Debe mostrar:

1. estado del lote;
2. formato de salida;
3. datos de imagen seleccionada;
4. avisos si existen;
5. acciones secundarias.

No debe mostrar por defecto:

- sliders avanzados;
- debug;
- campos de edición;
- subtítulos explicativos;
- tabs con secciones vacías.

---

### 5.3 Lo técnico debe existir, pero no dominar

FlatShot tiene lógica técnica real: bridge, perfiles, render, presets, fondo, sombreado, overrides locales. Esa complejidad debe estar disponible, pero no debe ser la primera capa de UI.

Regla:

> Si el usuario medio no debe tocarlo en el 90% de los lotes, no debe aparecer abierto por defecto.

---

### 5.4 Los datos deben agruparse por decisión

No organizar la UI por estructura interna del programa. Organizarla por la decisión que permite tomar.

Ejemplo:

Malo:

```text
Entrada
Conteo
Salida
Incidencias
```

Mejor:

```text
¿Está listo el lote?
¿Qué se va a exportar?
¿Hay algo que revisar?
```

---

### 5.5 Menos bordes, más jerarquía

La UI actual tiene muchos contenedores con borde. Eso fragmenta la pantalla. Codex debe reducir los bordes visibles y usar:

- tamaño;
- posición;
- peso tipográfico;
- espacio;
- color semántico;
- agrupación;
- estado.

Los bordes deben reservarse para:

- cards interactivas;
- errores/avisos;
- selección;
- modales;
- campos editables.

---

## 6. Arquitectura de información propuesta

### 6.1 Topbar

Función: contexto global + acción primaria.

Debe contener:

- marca `FlatShot`;
- estado compacto del lote;
- acción principal;
- acciones secundarias en overflow o botones discretos.

Propuesta:

```text
FlatShot · PNG · 29 archivos · 27 listas · 2 ignoradas      [Exportar 27 imágenes] [⋯]
```

El menú `⋯` puede contener:

- Detalle del lote;
- Configurar salida;
- Cambiar carpeta;
- Diagnóstico técnico, sólo si `devMode`;
- Limpiar lote.

No mostrar como botones permanentes:

- `Detalle técnico`;
- `Debug`;
- `Bridge`;
- `Preflight`;
- acciones de revisión demo.

---

### 6.2 Galería izquierda

Función: selección y revisión rápida.

Debe contener:

- conteo principal;
- búsqueda;
- filtros con conteo;
- miniaturas;
- vista lista como secundaria.

Propuesta compacta:

```text
Imágenes
27 listas

[Buscar…]

[Todas 27] [Listas 27] [Avisos 0] [Excluidas 0]

miniaturas...
```

Reglas:

- Ocultar filtros con conteo cero salvo `Todas` y `Listas`.
- Ocultar la galería completa si no hay lote.
- En `scanning`, mostrar skeleton o nada.
- El estado de cada miniatura debe ser pequeño:
  - check verde para lista;
  - punto amarillo para aviso;
  - punto rojo para error;
  - icono gris para ignorada/excluida.
- No usar etiqueta superpuesta `Seleccionada`; la selección debe indicarse con borde/acento.
- El nombre de archivo debe aparecer, pero no dominar.

Miniatura recomendada:

```text
┌────────────┐
│ imagen     │
└────────────┘
S672713599710
✓ Lista
```

En lista:

```text
[thumb] S672713599710.png        ✓ Lista
```

---

### 6.3 Visor central

Función: revisión visual.

Debe ser la zona dominante. Toda decisión visual depende de ella.

Debe contener:

- nombre de imagen;
- posición `1 / 27`;
- navegación anterior/siguiente;
- controles de vista mínimos;
- imagen grande;
- chips de salida discretos.

Problemas actuales a corregir:

- controles de zoom ocupan demasiado;
- nombre de imagen y salida se repiten;
- el visor no siempre aprovecha todo el espacio;
- el footer del visor añade otra línea más.

Propuesta:

```text
S672713599710.png                         ‹ 1 / 27 ›   [Alto] [Encajar] [100%] [− 99% +]

[imagen grande]
```

Reducir:

- `Vista / Original / Comparar` puede seguir, pero como control secundario compacto.
- `Ancho`, `Alto`, `Encajar`, `1:1` no necesitan todos el mismo peso. Usar:
  - `Alto` como default activo;
  - `Encajar`;
  - `100%`;
  - menú o atajos para el resto.
- El chip `JPG · 1800×2400 · Gris claro · RGB 230` puede quedarse abajo-izquierda dentro del visor, pero discreto y no duplicado en varias zonas.

---

### 6.4 Inspector derecho

Función: resumen accionable.

No debe ser un sistema de pestañas visible por defecto. Debe ser una columna de cards compactas.

Estado recomendado con lote listo:

```text
Lote listo
27 exportables · 2 ignorados

Salida
JPG · 1800×2400 · gris claro
_SALIDA_PRO · original_PRO.jpg
[Cambiar formato]

Imagen
S672713599710.png
PNG · 1.0 MB
[Ajustar imagen]

Ajustes
Luz cenital
[Editar ajuste] [Avanzados]
```

Si no hay incidencias reales:

```text
Sin incidencias
```

Pero no como pestaña. Como línea pequeña o directamente no mostrarla.

Si hay incidencias:

```text
Revisar
2 avisos
[Ver avisos]
```

Si hay errores:

```text
Exportación bloqueada
3 errores
[Revisar]
```

---

### 6.5 Modales

#### 6.5.1 `Detalle del lote`

Debe ser diagnóstico, no flujo normal.

Estructura recomendada:

```text
Detalle del lote

Resumen
29 archivos encontrados · 27 exportables · 2 ignorados

Entrada
PNG · U:/00_FOTOGRAFÍA/...

Salida
JPG · 1800×2400 · gris claro · _SALIDA_PRO

Ignorados
Thumbs.db — archivo del sistema
Salida — subcarpeta no escaneada

[Cerrar]
```

No usar colores de aviso para ignorados neutros. Usar gris.

#### 6.5.2 `Configurar salida`

Debe mantener la gestión de perfiles, pero más ordenada:

Columna izquierda:

```text
Formatos
JPG gris claro 1800×2400
PNG transparente 1800×2400
JPG blanco 2000×2000
```

Columna derecha:

```text
Nombre
Archivo
Tamaño
Fondo
Destino
Nombre final
```

Acciones:

```text
[Cancelar] [Guardar] [Aplicar]
```

No mostrar todas las opciones destructivas a la vez. `Eliminar` debe ir en menú secundario.

#### 6.5.3 Confirmación de exportación

No debe aparecer si:

- todas las imágenes exportables están listas;
- sólo hay ignorados neutros;
- el formato y destino están definidos.

Sí debe aparecer si:

- hay avisos accionables;
- hay errores;
- se va a exportar parcialmente;
- el destino puede sobrescribir archivos y eso no está claro.

Si aparece, debe ser breve:

```text
Exportar 27 imágenes

2 avisos no bloqueantes.
[Cancelar] [Exportar igualmente]
```

No usar una pantalla de confirmación sólo para repetir lo que ya se sabe.

---

## 7. Nueva taxonomía de estados

Codex debe revisar la lógica de clases de estado del shell y simplificar.

Estados recomendados para `data-ui-state`:

| Estado | Significado | UI |
|---|---|---|
| `no_folder` | No hay carpeta seleccionada | empty state, sin galería |
| `scanning` | Escaneo activo | spinner/progreso, sin botones innecesarios |
| `scan_empty` | Carpeta válida sin imágenes | empty state con cambiar carpeta |
| `ready` | Lote listo sin avisos relevantes | exportación directa |
| `ready_with_omitted` | Lote listo con ignorados neutros | exportación directa, nota gris |
| `ready_with_warnings` | Hay avisos no bloqueantes | exportación permitida, aviso compacto |
| `blocked` | Hay error que impide exportar | CTA bloqueada, revisar errores |
| `exporting` | Exportación en curso | progreso y controles de pausa/detención |
| `export_done` | Exportación completada | abrir destino |
| `export_partial` | Exportación parcial | mostrar errores |
| `export_failed` | Fallo general | error claro |

Regla crítica:

`ready_with_omitted` no debe parecer un error ni cambiar el botón de exportar a amarillo. Los ignorados neutros no deben aumentar la fricción.

---

## 8. Matriz de prioridad de acciones

### 8.1 Acciones primarias

| Acción | Dónde | Cuándo |
|---|---|---|
| Seleccionar carpeta | topbar o empty center, pero no duplicada | sin lote |
| Exportar N imágenes | topbar | lote listo |
| Abrir destino | topbar o resultado | exportación completada |

### 8.2 Acciones secundarias

| Acción | Dónde | Cuándo |
|---|---|---|
| Cambiar formato | inspector, salida | siempre que haya lote |
| Configurar salida | overflow/topbar | siempre |
| Detalle lote | overflow o inspector | siempre con lote |
| Cambiar carpeta | overflow | con lote |
| Ajustar imagen | inspector, imagen seleccionada | con imagen seleccionada |

### 8.3 Acciones terciarias

| Acción | Dónde |
|---|---|
| Editar preset |
| Ajustes avanzados |
| Debug bridge |
| Cargar mock |
| Forzar preview error |
| Revisar escenarios demo |

Todas las acciones terciarias deben estar ocultas salvo modo desarrollo o disclosure explícito.

---

## 9. Redundancias que hay que eliminar

| Redundancia actual | Decisión |
|---|---|
| `Seleccionar carpeta` en topbar, centro y panel derecho | dejar una sola acción primaria |
| Conteo de imágenes en topbar, izquierda, derecha y modal | topbar compacto + galería; modal sólo diagnóstico |
| `JPG 1800×2400 gris claro RGB 230` en varios sitios | una tarjeta de salida + chip discreto en visor |
| `Sin incidencias` como pestaña | convertir en nota o no mostrar |
| `Avanzado` como pestaña principal | mover a disclosure |
| `Detalle técnico` visible | sólo dev/overflow |
| Barra inferior con acción primaria duplicada | usar sólo para progreso/resultados, no para CTA principal |
| `Seleccionada` sobre miniatura | usar borde/estado visual |
| Subtítulos debajo de cada título | eliminar salvo cuando cambien una decisión |
| Modales con acciones de configuración cruzadas | limitar footer a la acción propia del modal |

---

## 10. Especificación visual

### 10.1 Columnas

La pantalla principal debe aprovechar mejor el ancho. Recomendación:

```css
:root {
  --column-gallery: clamp(260px, 15vw, 300px);
  --column-inspector: clamp(300px, 18vw, 340px);
  --viewer-min: 0px;
}

.workspace {
  grid-template-columns:
    var(--column-gallery)
    minmax(0, 1fr)
    var(--column-inspector);
}
```

No usar `minmax(620px, 1fr)` para el visor si provoca que el layout fuerce columnas o pierda fluidez. El visor debe poder ocupar `minmax(0, 1fr)`.

Para estados sin lote:

```css
.app-shell[data-ui-state="no_folder"] .gallery-column,
.app-shell[data-ui-state="scanning"] .gallery-column {
  display: none;
}

.app-shell[data-ui-state="no_folder"] .workspace,
.app-shell[data-ui-state="scanning"] .workspace {
  grid-template-columns: minmax(0, 1fr) minmax(300px, 340px);
}
```

Si el panel derecho tampoco aporta acción durante escaneo:

```css
.app-shell[data-ui-state="scanning"] .settings-panel {
  display: none;
}

.app-shell[data-ui-state="scanning"] .workspace {
  grid-template-columns: minmax(0, 1fr);
}
```

### 10.2 Topbar

Altura recomendada: 52–56 px. Correcto.

Cambios:

- reducir número de botones;
- el estado principal debe ser legible;
- acciones secundarias a menú.

Ejemplo:

```html
<div class="top-actions">
  <button class="primary top-export" id="top-primary-action"></button>
  <details class="top-more-menu">
    <summary aria-label="Más opciones">Más</summary>
    <div class="top-more-menu__content">
      ...
    </div>
  </details>
</div>
```

Si se prefiere no usar `details`, usar botón y popover simple.

### 10.3 Galería

Anchura recomendada: 280 px. La actual en 300 px es aceptable, pero se puede ajustar.

Cambios visuales:

- búsqueda a 32 px alto;
- filtros como chips compactos;
- miniaturas con menos padding;
- no mostrar `Lista` si todas están listas, salvo icono;
- ocultar `Avisos 0` y `Excluidas 0`.

### 10.4 Inspector

Anchura recomendada: 320 px.

Cambios visuales:

- eliminar grid de cuatro tabs;
- cards compactas con padding 12–14 px;
- una sola columna;
- máximos 3–4 bloques visibles;
- avanzado siempre cerrado.

Ejemplo de card:

```css
.inspector-card {
  display: grid;
  gap: 8px;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  background: var(--surface-panel);
  padding: 12px;
}

.inspector-card__title {
  font-size: 13px;
  font-weight: 700;
}

.inspector-card__meta {
  color: var(--text-muted);
  font-size: 12px;
}
```

### 10.5 Tipografía

Reglas:

- evitar `eyebrow` constante;
- no usar mayúsculas para todo;
- títulos principales 14–16 px;
- metadatos 12 px;
- números con `font-variant-numeric: tabular-nums`;
- no usar `font-weight` extremo salvo CTA.

Eliminar o reducir textos como:

```text
PREPARACIÓN
El ajuste activo y la salida se preparan automáticamente.
Valores por defecto
Ajuste Luz cenital
Revisión y salida
Procesamiento avanzado
```

Sustituir por datos compactos:

```text
Salida
JPG · 1800×2400 · gris claro
Luz cenital
```

### 10.6 Color y estado

Mantener la paleta actual verde/gris. No introducir una estética nueva.

Uso recomendado:

| Estado | Color |
|---|---|
| Primario | verde actual |
| Selección | azul/acento si ya está en foundation, o verde si se quiere coherencia |
| Aviso | amarillo sólo si requiere atención |
| Error | rojo sólo si bloquea o falla |
| Ignorado neutro | gris |

No poner el botón `Exportar` amarillo por `2 ignorados`.

---

## 11. Comportamiento por flujo

### 11.1 Flujo normal

1. Usuario abre app.
2. Ve un estado limpio.
3. Pulsa `Seleccionar carpeta`.
4. App escanea.
5. App muestra:
   - 27 imágenes listas;
   - salida activa;
   - botón `Exportar 27 imágenes`;
   - miniaturas.
6. Usuario revisa visualmente.
7. Pulsa `Exportar 27 imágenes`.
8. Si no hay incidencias accionables, exporta directamente.
9. Al finalizar, muestra `Exportación completada` y `Abrir destino`.

No debe aparecer confirmación intermedia si no hay nada que decidir.

### 11.2 Flujo con ignorados neutros

Ejemplo: `Thumbs.db`, subcarpeta `_SALIDA_PRO`.

Comportamiento:

- topbar: `27 listas · 2 ignoradas`;
- botón: `Exportar 27 imágenes`;
- inspector: nota gris `2 ignoradas · no afectan a la exportación`;
- exportación directa.

No mostrar:

- confirmación;
- warning amarillo;
- bloqueo;
- pestaña de incidencias abierta.

### 11.3 Flujo con aviso real

Ejemplo: imagen con problema de lectura parcial pero exportable.

Comportamiento:

- topbar: `27 listas · 1 aviso`;
- inspector: card amarilla compacta;
- botón: `Exportar 27 imágenes`;
- al pulsar exportar, se puede mostrar confirmación breve si el aviso afecta al resultado.

### 11.4 Flujo con error

Ejemplo: destino inaccesible o render imposible.

Comportamiento:

- topbar: `Exportación bloqueada`;
- botón primario: `Revisar errores` o deshabilitado con explicación mínima;
- inspector: error rojo con acción;
- galería: filtrar errores.

---

## 12. Cambios concretos en `index.html`

### 12.1 Topbar

Revisar el bloque:

```html
<div class="top-actions">
  ...
</div>
```

Objetivo:

- dejar una acción primaria;
- mantener `Detalle lote` y `Configurar salida` como secundarias;
- ocultar `Detalle técnico` salvo `devMode`;
- eliminar `preflight` visible si no aporta decisión.

Estructura recomendada:

```html
<div class="top-actions">
  <button type="button" class="primary top-export" id="top-primary-action" data-action="primary">
    Seleccionar carpeta
  </button>

  <button type="button" class="top-secondary-action" id="top-secondary-action" data-action="secondary-primary" hidden></button>

  <details class="top-more-menu" id="top-more-menu">
    <summary aria-label="Más opciones">Más</summary>
    <div class="top-more-menu__content">
      <button type="button" data-action="open-batch-detail">Detalle lote</button>
      <button type="button" data-action="open-app-settings">Configurar salida</button>
      <button type="button" data-action="pick-bridge-folder">Cambiar carpeta</button>
      <button type="button" data-action="toggle-inspector">Ocultar inspector</button>
      <button type="button" data-action="open-technical-detail" data-dev-only>Diagnóstico técnico</button>
    </div>
  </details>
</div>
```

Si `details` complica el comportamiento, mantener botones secundarios, pero sólo dos visibles:

```text
[Exportar 27 imágenes] [Configurar salida] [Detalle lote]
```

No mostrar `Detalle técnico` en uso normal.

### 12.2 Galería

Mantener `gallery-column`, pero hacerla inexistente visualmente sin lote.

En HTML:

- no añadir más explicación;
- mantener búsqueda;
- mantener switch miniaturas/lista, pero hacerlo discreto;
- filtros con conteo gestionado por JS.

### 12.3 Preview

Mantener `preview-panel`, pero:

- reducir subtítulo;
- mover chip de salida a `preview-output-context`;
- evitar footer si sólo repite metadatos;
- mantener atajos accesibles.

### 12.4 Inspector

Reemplazar o reorganizar:

```html
<div class="inspector-tabs segmented compact">
  ...
</div>
```

Por una estructura de inspector contextual:

```html
<aside class="settings-panel" aria-label="Inspector">
  <section class="inspector-main" id="inspector-main" aria-live="polite">
    <section class="inspector-card" id="lot-card"></section>
    <section class="inspector-card" id="output-card"></section>
    <section class="inspector-card" id="image-card"></section>
    <section class="inspector-card" id="issues-card" hidden></section>

    <details class="inspector-disclosure advanced-tools" id="advanced-tools">
      <summary>Ajustes avanzados</summary>
      ...
    </details>
  </section>
</aside>
```

Si se mantiene internamente el sistema de tabs para reducir riesgo, visualmente debe quedar así:

- `Resumen` como vista por defecto;
- `Exportación` accesible sólo desde `Cambiar formato`;
- `Incidencias` accesible sólo si hay incidencias;
- `Avanzado` bajo disclosure.

### 12.5 Modales

Mantener los modales actuales, pero cambiar contenido renderizado:

- `batch-detail-modal`: diagnóstico compacto;
- `export-confirm-modal`: sólo cuando haya decisión real;
- `app-settings-modal`: gestión de formatos más limpia.

---

## 13. Cambios concretos en `app.js`

### 13.1 Estado

El estado actual ya tiene propiedades útiles:

```js
state.inspectorTab
state.outputEditMode
state.presetEditorOpen
state.exportStatus
state.scanDiagnostics
state.realImages
state.outputProfiles
state.activeOutputProfileId
```

No hace falta añadir mucha lógica nueva. Lo importante es cambiar renderizado y reglas de visibilidad.

Añadir helpers:

```js
function hasActionableWarnings() { ... }
function hasBlockingErrors() { ... }
function hasNeutralOmissions() { ... }
function getNeutralOmissionCount() { ... }
function getExportableCount() { ... }
function getUiState() { ... }
```

### 13.2 Clasificación de ignorados

Ya existe:

```js
const IGNORED_OMISSION_REASONS = new Set([
  "system_file",
  "temporary_or_config_file",
  "unsupported_extension",
  "subfolder_not_scanned",
]);

const ACTIONABLE_OMISSION_REASONS = new Set([
  "read_error",
]);
```

Usar esta separación en UI:

- `IGNORED_OMISSION_REASONS` → neutro;
- `ACTIONABLE_OMISSION_REASONS` → incidencia real.

No mezclar ambos bajo el mismo bloque amarillo.

### 13.3 Estado visual global

Codex debe revisar dónde se establece `data-ui-state` y asegurar que:

```js
document.querySelector(".app-shell").dataset.uiState = getUiState();
```

`getUiState()` debe priorizar:

1. exportando;
2. error bloqueante;
3. escaneando;
4. sin carpeta;
5. carpeta vacía;
6. lote listo con avisos;
7. lote listo con ignorados;
8. lote listo normal.

Ejemplo:

```js
function getUiState() {
  if (state.exportStatus === "running") return "exporting";
  if (hasBlockingErrors()) return "blocked";
  if (state.bridgeStatus === "checking" || state.scanStatus === "Escaneando ruta") return "scanning";
  if (!hasActiveBatch()) return "no_folder";
  if (getImageCount() === 0) return "scan_empty";
  if (hasActionableWarnings()) return "ready_with_warnings";
  if (hasNeutralOmissions()) return "ready_with_omitted";
  return "ready";
}
```

Ajustar nombres a los existentes si ya hay lógica similar.

### 13.4 Render de topbar

`renderTopBar` o equivalente debe producir:

- texto de estado compacto;
- CTA primaria;
- estado visual no alarmista para ignorados neutros.

Ejemplos:

```js
// no_folder
topStatus = "Sin lote";
primary = "Seleccionar carpeta";

// scanning
topStatus = "Escaneando carpeta…";
primary = "Escaneando…";
primary.disabled = true;

// ready
topStatus = "PNG · 29 archivos · 27 listas";
primary = "Exportar 27 imágenes";

// ready_with_omitted
topStatus = "PNG · 29 archivos · 27 listas · 2 ignoradas";
primary = "Exportar 27 imágenes";

// blocked
topStatus = "Exportación bloqueada · 3 errores";
primary = "Revisar errores";
```

### 13.5 Render del inspector

Crear una función principal:

```js
function renderInspector() {
  renderLotCard();
  renderOutputCard();
  renderSelectedImageCard();
  renderIssuesCard();
  renderAdvancedTools();
}
```

#### `renderLotCard()`

Debe mostrar máximo:

```text
Lote listo
27 exportables · 2 ignoradas
```

Con botón secundario:

```text
[Detalle]
```

#### `renderOutputCard()`

Debe mostrar:

```text
Salida
JPG · 1800×2400 · gris claro
_SALIDA_PRO · original_PRO.jpg
[Cambiar formato]
```

No mostrar todos los campos salvo modo edición.

#### `renderSelectedImageCard()`

Debe mostrar:

```text
Imagen
S672713599710.png
PNG · 1.0 MB
[Ajustar imagen]
```

Si no hay imagen:

```text
Imagen
Sin selección
```

#### `renderIssuesCard()`

Reglas:

- si no hay incidencias ni ignorados, ocultar;
- si sólo hay ignorados neutros, mostrar nota compacta gris o incluir en lote;
- si hay avisos, mostrar card amarilla;
- si hay errores, mostrar card roja;
- cada card debe tener acción `Ver`.

### 13.6 Exportación directa

La acción primaria `Exportar N imágenes` debe:

- validar bloqueos reales;
- si hay sólo ignorados neutros, iniciar exportación directamente;
- si hay avisos accionables, abrir confirmación breve;
- si hay errores bloqueantes, abrir revisión de errores.

Pseudocódigo:

```js
function handlePrimaryAction() {
  if (!hasActiveBatch()) {
    pickFolder();
    return;
  }

  if (hasBlockingErrors()) {
    openIssues();
    return;
  }

  if (hasActionableWarnings()) {
    openExportConfirm();
    return;
  }

  startExport();
}
```

### 13.7 Debug y demo

Todo lo siguiente debe estar oculto salvo `devMode`:

- `Debug`;
- selector `Mock/Bridge`;
- `Comprobar bridge`;
- `Lote mock`;
- escenarios de revisión;
- `force-preview-error`;
- datos de preview debug;
- `Detalle técnico`.

La app puede mantenerlos en DOM, pero con:

```css
html:not(.dev-mode) .debug-panel,
html:not(.dev-mode) [data-dev-only],
html:not(.dev-mode) .review-panel {
  display: none !important;
}
```

---

## 14. Cambios concretos en CSS

### 14.1 Crear una capa final de layout

En `ux-foundation.css`, añadir al final una sección clara:

```css
/* UX/UI final hierarchy pass */
```

Evitar seguir acumulando `Tanda 1`, `Tanda 2`, etc. La acumulación actual hace difícil razonar sobre la cascada.

Estructura recomendada:

```css
/* 1. Layout shell */
/* 2. Topbar */
/* 3. Gallery */
/* 4. Viewer */
/* 5. Inspector */
/* 6. Modals */
/* 7. States */
/* 8. Responsive */
```

### 14.2 Variables

Añadir/normalizar:

```css
:root {
  --column-gallery: clamp(260px, 15vw, 300px);
  --column-inspector: clamp(300px, 18vw, 340px);
  --viewer-min: 0px;

  --panel-pad: 12px;
  --card-pad: 12px;
  --card-gap: 10px;
  --control-h-compact: 30px;
}
```

### 14.3 Layout por estado

```css
.workspace {
  grid-template-columns:
    var(--column-gallery)
    minmax(0, 1fr)
    var(--column-inspector) !important;
}

.app-shell[data-ui-state="no_folder"] .gallery-column,
.app-shell[data-ui-state="scanning"] .gallery-column {
  display: none !important;
}

.app-shell[data-ui-state="no_folder"] .workspace {
  grid-template-columns: minmax(0, 1fr) minmax(300px, 340px) !important;
}

.app-shell[data-ui-state="scanning"] .workspace {
  grid-template-columns: minmax(0, 1fr) !important;
}

.app-shell[data-ui-state="scanning"] .settings-panel {
  display: none !important;
}
```

### 14.4 Inspector sin tabs dominantes

Si se mantienen tabs internamente:

```css
.settings-panel .inspector-tabs {
  display: none;
}

.settings-panel.is-inspector-subview .inspector-tabs {
  display: grid;
}
```

Mejor: sustituir por cards.

### 14.5 Ocultar secciones vacías

```css
.inspector-card[hidden],
.issue-card[hidden],
.gallery-filter button[hidden] {
  display: none !important;
}
```

### 14.6 Miniaturas

```css
.gallery-column .image-item {
  min-height: 128px;
  padding: 8px;
}

.gallery-column .image-item.active::after {
  content: none;
}

.gallery-column .image-item.active {
  border-color: var(--semantic-selection-border);
  background: var(--semantic-selection-soft);
  box-shadow: inset 0 0 0 1px var(--semantic-selection-border);
}
```

### 14.7 Viewer

```css
.preview-panel {
  min-width: 0;
}

.canvas-area {
  padding: clamp(8px, 1.5vh, 18px);
}

.preview-footer {
  display: none;
}
```

Si el footer contiene información útil, moverla al chip de salida dentro del canvas.

### 14.8 Bottom bar

La barra inferior no debe duplicar la CTA.

```css
.bottom-actions #primary-action {
  display: none;
}

.bottom-bar {
  display: none;
}

.app-shell[data-ui-state="exporting"] .bottom-bar,
.app-shell[data-ui-state="export_done"] .bottom-bar,
.app-shell[data-ui-state="export_partial"] .bottom-bar,
.app-shell[data-ui-state="export_failed"] .bottom-bar {
  display: grid;
}
```

Si se mantiene visible, que sea sólo estado/progreso.

---

## 15. Microcopy recomendado

### 15.1 Reglas

- Usar frases cortas.
- Evitar explicar lo evidente.
- Evitar términos internos.
- No usar `Preflight`.
- No usar `Bridge` salvo diagnóstico.
- No usar `Procesamiento avanzado` como texto visible normal.
- No repetir `Ajuste activo y salida se preparan automáticamente`.

### 15.2 Sustituciones

| Actual | Nuevo |
|---|---|
| `Seleccionar carpeta de imágenes` | `Selecciona una carpeta` |
| `PNG o JPG. Después podrás revisar y exportar el lote.` | `PNG o JPG` |
| `Valores por defecto` | eliminar |
| `JPG · 1800x2400 · Gris claro · RGB 230` | `JPG · 1800×2400 · gris claro` |
| `Ajuste Luz cenital` | `Luz cenital` |
| `Preparación` | `Salida` o eliminar |
| `Escaneando ruta` | `Escaneando carpeta…` |
| `Incidencias` | `Revisar` sólo si hay algo que revisar |
| `2 ignorados` | `2 ignoradas · no afectan` |
| `Avanzado` | `Ajustes avanzados` bajo disclosure |
| `Detalle técnico` | ocultar en modo normal |

### 15.3 Labels de acciones

| Acción | Label |
|---|---|
| elegir lote | `Seleccionar carpeta` |
| exportar | `Exportar 27 imágenes` |
| cambiar salida | `Cambiar formato` |
| abrir ajustes globales | `Configurar salida` |
| ver diagnóstico | `Detalle lote` |
| revisar avisos | `Revisar avisos` |
| abrir carpeta final | `Abrir destino` |

---

## 16. Accesibilidad y teclado

No convertir la simplificación visual en pérdida de accesibilidad.

Mantener:

- botones reales, no `div` clicables;
- `aria-label` en iconos;
- focus visible;
- `Esc` para cerrar modales;
- navegación por teclado en galería;
- atajos del visor.

Recomendaciones:

| Atajo | Acción |
|---|---|
| `← / →` | imagen anterior/siguiente |
| `F` | encajar |
| `H` | alto |
| `W` | ancho |
| `1` | 100% |
| `Ctrl/Cmd + E` | exportar si está listo |
| `Esc` | cerrar modal/subvista |

No hace falta mostrar todos los atajos en pantalla. Pueden estar en `title` o ayuda técnica.

---

## 17. Responsive / tamaños de ventana

Aunque la app se use en escritorio, debe evitar romperse.

### > 1400 px

Tres columnas:

```text
galería 280–300 | visor flexible | inspector 320–340
```

### 1080–1400 px

Reducir:

- galería a lista compacta;
- inspector puede seguir visible;
- controles del visor pueden envolverse.

### < 1080 px

Dos columnas:

```text
galería 260 | visor flexible
```

Inspector colapsado o como drawer.

### Sin lote / escaneando

Una o dos columnas máximo. Nunca mostrar una columna izquierda vacía.

---

## 18. Criterios de aceptación visual

Codex debe considerar la tarea terminada sólo si se cumplen estos puntos.

### 18.1 Sin lote

- No hay columna izquierda vacía con `0 imágenes` como bloque dominante.
- Sólo hay una acción principal `Seleccionar carpeta`.
- El texto central es breve.
- La salida por defecto aparece una sola vez como dato compacto.
- No hay debug ni detalle técnico visible.

### 18.2 Escaneando

- La pantalla comunica escaneo sin paneles vacíos.
- No hay botones activos irrelevantes.
- No se duplican mensajes de estado.
- La barra de progreso, si aparece, es única.

### 18.3 Lote listo

- El botón `Exportar N imágenes` es la acción más visible.
- La galería permite revisar imágenes sin sobrecargar.
- La imagen ocupa claramente la mayor parte del área útil.
- El inspector muestra resumen, salida e imagen seleccionada.
- `Avanzado` no está abierto.
- `Incidencias` no aparece si no hay incidencias reales.
- `2 ignorados` se muestra como información neutra.

### 18.4 Exportación

- Exportar no abre confirmación si sólo hay ignorados neutros.
- La exportación muestra progreso sin cambiar a otra pantalla innecesaria.
- Al terminar, `Abrir destino` es claro.
- No se altera ningún resultado de imagen.

### 18.5 Código

- No se cambia el motor de imagen.
- No se introducen frameworks.
- No se rompe `python apps/flatshot-desktop/run_dev.py --open`.
- Se mantiene modo dev para debug.
- Se actualizan o se mantienen tests existentes.
- Se prueba manualmente con:
  - carpeta vacía;
  - carpeta con PNG;
  - carpeta con imágenes + `Thumbs.db`;
  - carpeta con subcarpeta `_SALIDA_PRO`;
  - exportación completa.

---

## 19. Plan de implementación por fases

### Fase 1 — Limpieza de jerarquía sin romper flujo

Objetivo: reducir redundancia visible con cambios controlados.

Tareas:

1. ocultar `batch-panel` definitivamente si ya no se usa;
2. ocultar galería en `no_folder` y `scanning`;
3. ocultar debug/review/demo salvo `devMode`;
4. ocultar `Detalle técnico` en modo normal;
5. eliminar CTA duplicada de `Seleccionar carpeta`;
6. hacer que `ready_with_omitted` no pinte exportar como warning;
7. ocultar `bottom-bar` salvo exportación/progreso.

Archivos:

```text
index.html
ux-foundation.css
app.js
```

Riesgo: bajo.

---

### Fase 2 — Inspector contextual

Objetivo: sustituir tabs visibles por cards accionables.

Tareas:

1. crear `renderInspector()` por cards;
2. mover salida a card compacta;
3. mover incidencias a card condicional;
4. mover avanzado a disclosure cerrado;
5. mantener modal de salida para edición completa;
6. eliminar subtítulos innecesarios.

Archivos:

```text
index.html
app.js
ux-foundation.css
```

Riesgo: medio, porque toca renderizado.

---

### Fase 3 — Galería y visor

Objetivo: que la revisión visual sea más limpia.

Tareas:

1. quitar overlay textual `Seleccionada`;
2. ajustar miniaturas;
3. compactar filtros;
4. ocultar filtros vacíos;
5. simplificar toolbar de visor;
6. ocultar preview footer si duplica datos.

Archivos:

```text
app.js
ux-foundation.css
styles.css
```

Riesgo: bajo/medio.

---

### Fase 4 — Modales y confirmación

Objetivo: eliminar fricción innecesaria.

Tareas:

1. compactar `Detalle lote`;
2. separar ignorados neutros de incidencias;
3. no abrir confirmación de exportación si sólo hay ignorados neutros;
4. confirmación breve sólo para avisos reales;
5. simplificar modal de formatos.

Archivos:

```text
app.js
index.html
ux-foundation.css
```

Riesgo: medio.

---

### Fase 5 — Validación final

Objetivo: asegurar que el producto funciona igual pero con mejor UX.

Tareas:

1. ejecutar app;
2. probar estados;
3. exportar lote;
4. comparar resultado de salida;
5. revisar responsive;
6. limpiar CSS redundante si es seguro.

---

## 20. Pseudoflujo de render recomendado

```js
function render() {
  const uiState = getUiState();
  setShellState(uiState);

  renderTopBar(uiState);
  renderGallery(uiState);
  renderPreview(uiState);
  renderInspector(uiState);
  renderBottomBar(uiState);
  renderModals();
}
```

```js
function setShellState(uiState) {
  const shell = document.querySelector(".app-shell");
  shell.dataset.uiState = uiState;
  shell.classList.toggle("has-batch", hasActiveBatch());
  shell.classList.toggle("has-actionable-issues", hasActionableWarnings() || hasBlockingErrors());
  shell.classList.toggle("has-neutral-omissions", hasNeutralOmissions());
}
```

```js
function shouldConfirmBeforeExport() {
  if (hasBlockingErrors()) return true;
  if (hasActionableWarnings()) return true;
  return false;
}
```

```js
function handleExportRequest() {
  if (hasBlockingErrors()) {
    openIssuesReview();
    return;
  }

  if (shouldConfirmBeforeExport()) {
    openExportConfirm();
    return;
  }

  startExport();
}
```

---

## 21. Definición de “incidencia”

La palabra `incidencia` debe reservarse para algo que el usuario pueda o deba revisar.

### No son incidencias

- `Thumbs.db`;
- subcarpeta de salida no escaneada;
- archivo temporal ignorado;
- extensión no soportada que claramente no es imagen de trabajo;
- carpeta interna del sistema.

Tratamiento: nota gris, si se muestra.

### Sí son incidencias

- archivo de imagen ilegible;
- imagen exportable con error de preview;
- error de destino;
- error de render;
- formato incompatible;
- datos necesarios ausentes;
- exportación parcial.

Tratamiento: aviso o error según impacto.

---

## 22. Reglas para salida y presets

La app debe mantener los perfiles de salida actuales:

```text
JPG gris claro 1800×2400
PNG transparente 1800×2400
JPG blanco 2000×2000
```

Pero la pantalla principal no debe parecer un formulario de salida.

En pantalla principal:

```text
Salida
JPG · 1800×2400 · gris claro
```

En modal:

```text
Formato
Archivo: JPG
Fondo: gris claro
Tamaño: 1800 × 2400
Destino: _SALIDA_PRO
Nombre: {original}{suffix}
Sufijo: _PRO
```

No duplicar en inspector los campos editables si el usuario no ha pulsado `Editar`.

---

## 23. Reglas para ajustes visuales

El preset activo `Luz cenital` debe aparecer como dato, no como llamada a configurar.

En resumen:

```text
Aspecto
Luz cenital
```

Acciones:

```text
[Editar ajuste]
```

Dentro de `Editar ajuste`:

- presets;
- controles principales;
- ajuste por imagen;
- avanzados.

Por defecto:

- `Ajustes avanzados` cerrado;
- sliders no visibles;
- motor no visible;
- reset/delete no visibles salvo modo edición.

---

## 24. Qué no debe hacer Codex

No hacer:

- no cambiar el motor de exportación;
- no cambiar el naming final;
- no cambiar la calidad JPG;
- no cambiar DPI;
- no cambiar transparencia;
- no cambiar destino por defecto;
- no meter React/Vue/Svelte;
- no reescribir toda la app;
- no añadir textos largos para justificar la UI;
- no convertir ignorados neutros en avisos;
- no esconder información necesaria, sólo jerarquizarla.

---

## 25. Testing manual obligatorio

Probar con al menos estos escenarios:

### Escenario A — sin lote

- abrir app;
- comprobar empty state;
- comprobar que sólo hay un CTA principal;
- comprobar que no aparece debug.

### Escenario B — carpeta vacía

- seleccionar carpeta sin imágenes;
- comprobar mensaje;
- comprobar que permite cambiar carpeta;
- comprobar que no muestra galería vacía sobrecargada.

### Escenario C — carpeta con PNG válidos

- seleccionar carpeta con imágenes;
- comprobar galería;
- comprobar preview;
- comprobar salida;
- exportar;
- verificar `_SALIDA_PRO`.

### Escenario D — carpeta con `Thumbs.db`

- comprobar que aparece como ignorado neutro;
- comprobar que exportar no pide confirmación por eso.

### Escenario E — carpeta con subcarpeta `_SALIDA_PRO`

- comprobar que `Salida` ignorada no se trata como error;
- comprobar que no hay aviso amarillo innecesario.

### Escenario F — imagen problemática

- simular o usar una imagen ilegible;
- comprobar aviso/error;
- comprobar filtro;
- comprobar confirmación si procede.

### Escenario G — responsive

- probar 2560×1440;
- probar 1920×1080;
- probar 1366×768;
- comprobar que el visor no pierde espacio por columnas vacías.

---

## 26. Checklist final para revisión visual

Antes de dar por cerrado, mirar la pantalla y responder:

- ¿Cuál es la acción principal? Debe ser evidente en menos de un segundo.
- ¿Hay algún botón duplicado? Si sí, eliminar o degradar.
- ¿Hay algún texto que explique algo obvio? Si sí, eliminar.
- ¿Hay alguna pestaña vacía o irrelevante? Si sí, ocultar.
- ¿Hay algún panel que exista sólo para decir “0”? Si sí, ocultar.
- ¿La imagen es la protagonista? Si no, ajustar columnas.
- ¿Los ignorados parecen errores? Si sí, cambiar color/jerarquía.
- ¿El usuario puede exportar sin pensar cuando todo está listo? Si no, reducir fricción.
- ¿Lo avanzado está disponible pero no molesta? Si no, mover a disclosure/dev.

---

## 27. Prompt operativo para Codex

Puedes pegar a Codex este bloque junto con el documento completo:

```text
Implementa una refactorización UX/UI de FlatShot siguiendo el documento `FlatShot — Informe UX/UI para rediseño estructural e implementación en Codex`.

Contexto técnico:
- La interfaz activa está en `apps/flatshot-desktop/frontend`.
- Es frontend estático HTML/CSS/JS.
- No añadas frameworks.
- No cambies el motor de imagen ni el resultado exportado.
- Mantén la ejecución con `python apps/flatshot-desktop/run_dev.py --open`.

Objetivo:
Reorganizar la app para que la pantalla tenga una única acción primaria por estado, menos textos explicativos, menos redundancias y un inspector contextual. La acción principal debe ser:
- Sin lote: `Seleccionar carpeta`.
- Escaneando: estado bloqueado `Escaneando…`.
- Lote listo: `Exportar N imágenes`.
- Exportado: `Abrir destino`.

Cambios prioritarios:
1. Oculta galería y paneles vacíos cuando no hay lote o se está escaneando.
2. Elimina CTAs duplicadas de `Seleccionar carpeta`.
3. Mantén `Exportar N imágenes` como acción principal en topbar cuando el lote esté listo.
4. No trates `Thumbs.db`, subcarpetas de salida o archivos ignorados neutros como incidencias.
5. No muestres confirmación de exportación si sólo hay ignorados neutros.
6. Sustituye el inspector de pestañas visibles por cards contextuales: lote, salida, imagen, avisos si existen.
7. Mueve `Avanzado`, debug, mock, bridge y escenarios demo fuera del flujo normal; sólo en modo dev o disclosure.
8. Compacta la galería: filtros con conteo, miniaturas limpias, sin overlay textual `Seleccionada`.
9. Compacta el visor: menos controles visibles, más espacio para la imagen.
10. Simplifica los modales de detalle de lote y configuración de salida.

Criterios de aceptación:
- Una sola acción primaria visible en cada estado.
- Sin columna izquierda vacía con `0 imágenes` en estado inicial.
- Sin pestaña `Incidencias` visible cuando no hay incidencias reales.
- Sin `Avanzado` abierto o equivalente visible en el flujo normal.
- `2 ignorados` se muestra como información neutra, no como advertencia.
- La exportación se inicia directamente si el lote está listo y sólo hay ignorados neutros.
- No cambia la apariencia/nombre/destino/formato/calidad de los archivos exportados.
- La app sigue funcionando con `python apps/flatshot-desktop/run_dev.py --open`.

Implementa en fases pequeñas y valida manualmente los estados:
sin lote, escaneando, lote listo, lote con ignorados neutros, lote con aviso real, exportando y exportado.
```

---

## 28. Resultado esperado

La app resultante debe sentirse así:

- limpia al abrir;
- directa al elegir carpeta;
- visual y amplia al revisar producto;
- segura al exportar;
- técnica sólo cuando el usuario decide entrar en lo técnico.

La clave no es que haya menos funcionalidad. La clave es que la funcionalidad tenga capas:

1. **trabajo normal**: revisar y exportar;
2. **ajuste ocasional**: salida, imagen, aspecto;
3. **diagnóstico**: lote, errores, bridge;
4. **desarrollo**: mock, debug, escenarios.

Ahora mismo esas capas están mezcladas. La implementación debe separarlas.
