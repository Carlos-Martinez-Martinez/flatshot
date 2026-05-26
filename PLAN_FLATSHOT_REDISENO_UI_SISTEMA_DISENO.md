# FlatShot — Plan integral de rediseño UI/UX y sistema de diseño

## Objetivo del documento

Este documento define un plan completo, paso a paso, para que Codex implemente una revisión profunda de la interfaz principal de FlatShot. La prioridad no es añadir funcionalidades nuevas, sino transformar la pantalla actual en una herramienta visual madura, profesional, coherente y mantenible.

El foco principal está en:

- construir un sistema de diseño real;
- eliminar repetición y ruido visual;
- ordenar la arquitectura de información;
- hacer que cada columna tenga una función clara;
- mejorar la jerarquía visual;
- normalizar espaciado, tipografía, botones, chips, paneles, inputs y estados;
- conseguir que toda la interfaz respire el mismo lenguaje visual, pero se adapte al contexto de cada zona.

La interfaz actual ya ha avanzado hacia un layout de columnas, pero sigue pareciendo amateur porque todavía hay acumulación de piezas, padding irregular, repetición de datos, paneles sin rol puro y componentes visuales sin una gramática común.

---

# 1. Diagnóstico de partida

## 1.1 Problema principal

La pantalla principal de FlatShot funciona como una suma de bloques independientes, pero no como un producto diseñado de forma integral.

Hay cuatro zonas principales:

```text
Lote | Galería | Visor | Inspector
```

La dirección es correcta, pero la ejecución necesita madurar. Cada zona debe tener una responsabilidad inequívoca y una estética coherente con las demás.

## 1.2 Problemas visuales actuales

La interfaz presenta varios síntomas de inmadurez visual:

- padding inconsistente entre paneles;
- secciones pegadas a bordes;
- demasiadas líneas divisorias;
- tarjetas con radios, bordes y sombras no unificados;
- jerarquía tipográfica débil;
- chips y badges con tratamientos distintos;
- botones secundarios demasiado prominentes;
- scrolls nativos visibles y poco integrados;
- footer que repite información o invade visualmente;
- selector de fondo colocado bajo el visor, generando ruido;
- avisos menores, como `Thumbs.db`, con demasiado peso visual;
- estados como `44 imágenes`, `1 aviso`, `Luz cenital`, `PNG` repetidos en varios puntos.

## 1.3 Problemas de arquitectura de información

Actualmente algunos datos aparecen en más sitios de los necesarios:

| Dato | Problema actual |
|---|---|
| `44 imágenes` | aparece en header, lote, galería y footer |
| `1 aviso` | aparece en header, lote, resumen e inspector |
| `Luz cenital` | aparece en header, inspector, chips y preset |
| `PNG` | aparece como carpeta, formato detectado y metadato de item |
| salida/exportación | aparece en header, inspector y footer |
| fondo `RGB230` | aparece en barra inferior del visor, aunque pertenece a ajustes/salida |

Una interfaz profesional necesita una regla clara: **cada dato debe tener una casa principal**. Sólo se puede repetir si aporta contexto operativo real.

## 1.4 Problemas funcionales relacionados con UI

Aunque este plan se centra en UI, hay puntos funcionales que afectan directamente a la percepción visual:

- las miniaturas deben ser imágenes reales;
- el visor debe mostrar la imagen completa por defecto;
- el layout debe estar optimizado para imágenes verticales;
- no debe haber scroll global innecesario;
- cada columna debe gestionar su propio overflow;
- la interfaz no debe saltar ni deformarse al filtrar, seleccionar o cambiar de imagen.

---

# 2. Principios rectores

Antes de tocar código, asumir estas reglas como contrato de diseño.

## 2.1 La imagen es el centro, pero no necesita ocupar todo el ancho

FlatShot trabaja principalmente con imágenes verticales de producto. Por tanto, el visor debe estar optimizado para imágenes verticales.

No hay que crear un rectángulo horizontal enorme donde la prenda flota en medio. El espacio sobrante debe usarse para contexto: galería, lote, inspector y diagnóstico.

## 2.2 Cada zona debe tener un rol puro

La pantalla debe organizarse así:

```text
Header      = identidad, contexto mínimo, acción principal
Lote        = resumen administrativo del lote
Galería     = navegación visual por imágenes
Visor       = revisión de la imagen seleccionada
Inspector   = configuración de salida, ajustes y avisos
Footer      = sólo procesos o estado mínimo, si es necesario
```

Si un elemento no encaja con el rol de su zona, debe moverse.

## 2.3 Menos repetición, más contexto

No repetir datos para llenar espacio. Repetir sólo cuando ayude a tomar una decisión.

Por ejemplo:

- `44 imágenes` puede aparecer en el header y como contador de galería.
- `1 aviso` puede aparecer en header y diagnóstico.
- `Luz cenital` debe vivir principalmente en el inspector.
- `RGB230` debe vivir en `Salida` o `Ajustes`, no debajo del visor.

## 2.4 Sistema antes que retoques

No aplicar cambios visuales sueltos. Primero crear tokens y reglas compartidas.

Todo debe apoyarse en un sistema común:

- escala de espaciado;
- escala tipográfica;
- colores semánticos;
- radios;
- sombras;
- estados interactivos;
- componentes reutilizables;
- patrones de layout.

## 2.5 Mismo lenguaje, distinto contexto

La interfaz debe respirar igual en todas partes, pero no todos los componentes deben verse idénticos.

Ejemplos:

- una tarjeta de resumen de lote puede tener fondo suave;
- una miniatura seleccionada puede usar borde de acento;
- un aviso menor puede ser una línea discreta;
- el botón de exportar debe ser el único botón claramente primario;
- los filtros pueden ser chips compactos;
- los presets pueden ser pills, pero con el mismo sistema de color y radio.

---

# 3. Resultado visual objetivo

## 3.1 Estructura general

La pantalla debe aproximarse a esta arquitectura:

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ HEADER                                                                     │
│ FlatShot · PNG · 44 imágenes · 1 aviso                         Exportar 44 │
├──────────────┬────────────────────┬──────────────────────────┬────────────┤
│ LOTE         │ IMÁGENES            │ VISOR                    │ INSPECTOR  │
│ resumen      │ buscar + filtros    │ imagen seleccionada      │ salida     │
│ diagnóstico  │ grid visual         │ controles de revisión    │ ajustes    │
└──────────────┴────────────────────┴──────────────────────────┴────────────┘
```

## 3.2 Distribución recomendada

En desktop amplio:

```css
.app-main {
  display: grid;
  grid-template-columns:
    230px
    340px
    minmax(620px, 1fr)
    320px;
  min-width: 0;
  min-height: 0;
}
```

Valores orientativos:

| Zona | Ancho recomendado | Rol |
|---|---:|---|
| Lote | 220–240 px | resumen y diagnóstico |
| Galería | 300–380 px | navegación visual |
| Visor | flexible, mínimo 620 px | revisión de imagen |
| Inspector | 300–340 px | salida, ajustes, avisos |

## 3.3 Estado final deseado

La interfaz debe sentirse:

- calmada;
- precisa;
- limpia;
- profesional;
- visualmente coherente;
- orientada a producción;
- pensada para revisar muchas imágenes con rapidez;
- no como dashboard administrativo ni formulario técnico.

---

# 4. Fase 0 — Auditoría previa obligatoria

Antes de modificar el diseño, Codex debe inspeccionar la estructura actual.

## 4.1 Localizar archivos principales

Identificar:

- archivo principal de la app;
- componentes o bloques actuales de UI;
- CSS global;
- CSS específico de FlatShot;
- lógica de escaneo;
- lógica de miniaturas;
- lógica de selección de imagen;
- lógica de filtros;
- lógica de presets/salida;
- modo mock;
- bridge local.

## 4.2 Documentar brevemente el estado actual

Antes de implementar, anotar:

```text
- Dónde se define el shell principal.
- Dónde se renderiza el panel de lote.
- Dónde se renderiza la galería.
- Dónde se renderiza el visor.
- Dónde se renderiza el inspector.
- Qué clases CSS principales existen.
- Qué nombres de estado existen para imágenes, avisos, omitidas y errores.
```

## 4.3 Identificar duplicidades

Hacer una lista interna de datos repetidos:

- número de imágenes;
- aviso/s;
- formato;
- preset;
- estado de exportación;
- ruta de salida;
- fondo;
- imagen actual.

Después aplicar la matriz de responsabilidades del punto 5.

---

# 5. Matriz de responsabilidad de información

Implementar esta matriz para decidir dónde vive cada dato.

| Información | Lugar principal | Repetición permitida | No debe aparecer en |
|---|---|---|---|
| Nº total de imágenes | Header | Galería | Footer, lote repetido varias veces |
| Imagen actual | Visor | Footer sólo si se mantiene | Header |
| Avisos | Header como resumen | Lote/diagnóstico | Repetido en cada panel |
| Omitidas | Diagnóstico/lote | Filtros | Header salvo si es relevante |
| Preset activo | Inspector | Header sólo como estado breve si aporta | Galería/lote |
| Formato `PNG` | Lote o galería como metadato | Items individuales si aporta | Header + lote + galería a la vez |
| Fondo `RGB230` | Inspector > Salida/Ajustes | Visor sólo como estado muy discreto | Barra inferior fija |
| Exportar | Header + pestaña Salida | No más | Footer |
| Debug/bridge | Panel debug | No repetir | UI normal |
| Diagnóstico | Lote/diagnóstico | Inspector Avisos si existe | Header salvo resumen mínimo |

---

# 6. Fase 1 — Crear sistema de diseño base

Esta fase es prioritaria. No rediseñar componentes antes de tener tokens.

## 6.1 Crear o consolidar tokens CSS

Localizar el CSS global y añadir una capa de tokens. Si ya existen variables, consolidarlas en vez de duplicarlas.

Ejemplo recomendado:

```css
:root {
  /* Color base */
  --color-bg-app: #f6f8f8;
  --color-bg-surface: #ffffff;
  --color-bg-soft: #f8faf9;
  --color-bg-muted: #eef3f1;

  /* Texto */
  --color-text-primary: #0f172a;
  --color-text-secondary: #475569;
  --color-text-muted: #7b8794;
  --color-text-subtle: #94a3b8;

  /* Bordes */
  --color-border-subtle: rgba(15, 23, 42, 0.08);
  --color-border-strong: rgba(15, 23, 42, 0.14);

  /* Acento */
  --color-accent: #0f8f72;
  --color-accent-hover: #0a765f;
  --color-accent-soft: rgba(15, 143, 114, 0.10);
  --color-accent-border: rgba(15, 143, 114, 0.26);

  /* Estados */
  --color-warning: #b7791f;
  --color-warning-soft: rgba(245, 158, 11, 0.14);
  --color-warning-border: rgba(245, 158, 11, 0.30);

  --color-danger: #b42318;
  --color-danger-soft: rgba(244, 63, 94, 0.10);
  --color-danger-border: rgba(244, 63, 94, 0.28);

  --color-neutral-soft: rgba(100, 116, 139, 0.12);

  /* Tipografía */
  --font-family-ui: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --font-size-2xs: 10px;
  --font-size-xs: 11px;
  --font-size-sm: 12px;
  --font-size-md: 13px;
  --font-size-base: 14px;
  --font-size-lg: 18px;
  --font-size-xl: 22px;

  --line-height-tight: 1.15;
  --line-height-normal: 1.4;
  --line-height-relaxed: 1.6;

  --font-weight-regular: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;

  /* Espaciado */
  --space-0: 0;
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-7: 32px;
  --space-8: 40px;

  /* Radios */
  --radius-xs: 6px;
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 20px;
  --radius-pill: 999px;

  /* Sombras */
  --shadow-xs: 0 1px 2px rgba(15, 23, 42, 0.05);
  --shadow-sm: 0 4px 12px rgba(15, 23, 42, 0.06);
  --shadow-md: 0 10px 28px rgba(15, 23, 42, 0.08);

  /* Layout */
  --header-height: 56px;
  --footer-height: 0px;
  --column-lote: 230px;
  --column-gallery: 340px;
  --column-inspector: 320px;

  /* Transiciones */
  --transition-fast: 120ms ease;
  --transition-normal: 180ms ease;
}
```

## 6.2 Usar tokens en lugar de valores sueltos

Después de crear tokens, sustituir valores hardcoded repetidos:

- colores hex sueltos;
- padding arbitrarios;
- radios diferentes;
- fuentes sin sistema;
- sombras distintas;
- bordes inconsistentes.

Regla: cualquier valor visual usado más de una vez debe convertirse en token o clase reutilizable.

## 6.3 Definir clases base reutilizables

Crear clases utilitarias o componentes CSS para:

```css
.ui-section-label
.ui-card
.ui-button
.ui-button--primary
.ui-button--secondary
.ui-button--ghost
.ui-chip
.ui-chip--active
.ui-badge
.ui-badge--warning
.ui-input
.ui-scrollarea
.ui-divider
.ui-muted
.ui-meta
```

No abusar de utilidades si el proyecto no está montado así, pero sí evitar estilos duplicados.

---

# 7. Fase 2 — Reestructurar shell principal

## 7.1 Crear layout principal con CSS Grid

La estructura general debe ser:

```text
AppShell
 ├─ AppHeader
 └─ MainWorkspace
     ├─ BatchRail
     ├─ ImageGallery
     ├─ ImageViewer
     └─ InspectorPanel
```

CSS conceptual:

```css
.app-shell {
  height: 100dvh;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-app);
  color: var(--color-text-primary);
  font-family: var(--font-family-ui);
  overflow: hidden;
}

.app-header {
  height: var(--header-height);
  flex: 0 0 var(--header-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-4);
  background: var(--color-bg-surface);
  border-bottom: 1px solid var(--color-border-subtle);
}

.app-main {
  flex: 1;
  min-height: 0;
  min-width: 0;
  display: grid;
  grid-template-columns:
    var(--column-lote)
    var(--column-gallery)
    minmax(620px, 1fr)
    var(--column-inspector);
  background: var(--color-bg-app);
  overflow: hidden;
}

.app-column {
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  background: var(--color-bg-surface);
  border-right: 1px solid var(--color-border-subtle);
}

.app-column:last-child {
  border-right: 0;
}
```

## 7.2 Eliminar scroll global

Asegurar:

```css
html,
body,
#root {
  height: 100%;
  overflow: hidden;
}
```

Cada columna debe gestionar su propio scroll.

## 7.3 Eliminar o minimizar footer

Si el footer actual repite información, eliminarlo.

Sólo mantener footer si hay procesos activos:

- exportando;
- escaneando;
- error global;
- actualización en curso.

Si se mantiene footer, hacerlo muy fino y no invasivo:

```css
.app-footer {
  height: 28px;
  flex: 0 0 28px;
  padding: 0 var(--space-4);
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  border-top: 1px solid var(--color-border-subtle);
  background: var(--color-bg-surface);
}
```

Pero la preferencia para esta fase es **eliminarlo o dejarlo oculto si no hay proceso activo**.

---

# 8. Fase 3 — Header profesional

## 8.1 Contenido del header

El header debe mostrar sólo:

```text
FlatShot · PNG · 44 imágenes · 1 aviso                         [Exportar 44]
```

Si el lote tiene nombre real:

```text
FlatShot · Lote: PNG · 44 imágenes · 1 aviso                    [Exportar 44]
```

## 8.2 Estructura sugerida

```text
AppHeader
 ├─ Brand
 ├─ HeaderContext
 └─ HeaderActions
```

## 8.3 Reglas visuales

- `FlatShot` debe tener presencia, pero no ocupar demasiado.
- El contexto debe ser texto secundario con separadores discretos.
- `1 aviso` puede tener punto naranja suave.
- `Exportar 44` debe ser el único botón primario fuerte.
- No mostrar `Luz cenital` salvo que sea imprescindible. Si se muestra, usar texto secundario: `Preset: Luz cenital`.

## 8.4 Ejemplo CSS

```css
.header-brand {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-base);
}

.header-context {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.header-dot {
  width: 6px;
  height: 6px;
  border-radius: var(--radius-pill);
  background: var(--color-accent);
}

.header-dot--warning {
  background: var(--color-warning);
}
```

---

# 9. Fase 4 — Columna Lote

## 9.1 Responsabilidad de la columna

La columna `Lote` debe responder a estas preguntas:

- ¿Qué lote/carpeta estoy revisando?
- ¿Cuántas imágenes hay?
- ¿Hay incidencias?
- ¿Puedo cambiar/actualizar el lote?
- ¿Puedo abrir el diagnóstico?

No debe encargarse de navegación visual. La navegación vive en la galería.

## 9.2 Contenido final recomendado

```text
LOTE
44 imágenes                                      1 aviso

Carpeta
PNG
Escaneo completado · 2 avisos
[Cambiar] [↻]

RESUMEN
45 archivos encontrados
44 imágenes listas
1 omitida · 1 aviso
Ver diagnóstico
```

## 9.3 Quitar de esta columna

Mover fuera de `Lote`:

- búsqueda;
- filtros de imágenes;
- lista de miniaturas;
- formato detectado como bloque grande;
- repeticiones de `44` que ya aparecen en header/galería.

## 9.4 Diseño visual

La columna debe ser sobria y compacta.

CSS conceptual:

```css
.batch-rail {
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  overflow-y: auto;
}

.batch-rail__header {
  display: grid;
  gap: var(--space-2);
}

.batch-rail__title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
}

.batch-rail__count {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  line-height: var(--line-height-tight);
}

.batch-summary-card {
  padding: var(--space-4);
  border-radius: var(--radius-md);
  background: var(--color-bg-soft);
  border: 1px solid var(--color-border-subtle);
}
```

## 9.5 Botones de carpeta

`Cambiar` y `Actualizar` deben ser secundarios.

Preferencia:

```text
[Cambiar] [↻]
```

- `Cambiar`: botón secundario pequeño.
- `Actualizar`: botón iconográfico con `aria-label="Actualizar lote"`.

No usar dos botones grandes del mismo peso.

## 9.6 Diagnóstico

Mostrar como link contextual:

```text
1 aviso detectado · Ver diagnóstico
```

No usar bloque amarillo grande para `Thumbs.db` en esta columna.

---

# 10. Fase 5 — Columna Galería

## 10.1 Responsabilidad de la columna

La galería responde a:

- ¿Qué imágenes hay en el lote?
- ¿Cuál está seleccionada?
- ¿Puedo filtrar/buscar?
- ¿Qué imágenes tienen incidencias?

Aquí sí viven:

- búsqueda;
- filtros;
- grid/lista de miniaturas;
- navegación visual.

## 10.2 Estructura recomendada

```text
IMÁGENES                                      44
[Buscar imagen…]
[Todas 44] [Correctas 44] [Avisos 0] [Omitidas 1]

[thumb] [thumb]
[thumb] [thumb]
[thumb] [thumb]
...
```

## 10.3 Eliminar título redundante

No usar:

```text
GALERÍA
Navegación visual
```

Es redundante. Usar:

```text
IMÁGENES 44
```

## 10.4 Filtros

Los filtros deben ser chips compactos.

Reglas:

- activo: fondo verde suave, borde de acento;
- inactivo: fondo blanco o transparente;
- contador integrado;
- filtros con 0 atenuados;
- sin caja grande alrededor.

CSS conceptual:

```css
.filter-chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.filter-chip {
  height: 28px;
  padding: 0 var(--space-3);
  border-radius: var(--radius-pill);
  border: 1px solid var(--color-border-subtle);
  background: var(--color-bg-surface);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  cursor: pointer;
}

.filter-chip.is-active {
  color: var(--color-accent);
  background: var(--color-accent-soft);
  border-color: var(--color-accent-border);
}

.filter-chip.is-empty {
  opacity: 0.5;
}
```

## 10.5 Grid de miniaturas

Preferencia: grid de 2 columnas.

```css
.gallery-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-3);
}
```

Cada item:

```text
[thumbnail]
S670373590110
PNG · 2.0 MB
```

## 10.6 Reglas para las tarjetas de imagen

- No mostrar `Correcta` textual en todas las imágenes.
- Mostrar estado normal con punto verde discreto si hace falta.
- Mostrar `Aviso` sólo en imágenes con aviso.
- Mostrar `Omitida` sólo si procede.
- Nombre truncado con ellipsis.
- Metadata pequeña.
- Selección clara pero elegante.

CSS conceptual:

```css
.gallery-item {
  position: relative;
  min-width: 0;
  padding: var(--space-2);
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  background: transparent;
  cursor: pointer;
  transition: background var(--transition-fast), border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.gallery-item:hover {
  background: var(--color-bg-soft);
}

.gallery-item.is-selected {
  background: var(--color-accent-soft);
  border-color: var(--color-accent-border);
  box-shadow: var(--shadow-xs);
}

.gallery-thumb {
  aspect-ratio: 4 / 5;
  width: 100%;
  display: grid;
  place-items: center;
  overflow: hidden;
  border-radius: var(--radius-sm);
  background: var(--color-bg-muted);
}

.gallery-thumb img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.gallery-item__name {
  margin-top: var(--space-2);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.gallery-item__meta {
  margin-top: 2px;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}
```

## 10.7 Estados de miniatura

### Cargando

Skeleton neutro, no bloque de color final.

### Cargada

Imagen real.

### Sin preview

Placeholder discreto:

```text
Icono imagen
Sin preview
```

No usar texto rojo agresivo.

### Omitida

Miniatura atenuada, badge gris.

## 10.8 Scroll de galería

La galería debe tener header fijo interno y grid scrolleable.

```css
.gallery-column {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.gallery-toolbar {
  flex: 0 0 auto;
  padding: var(--space-4);
  border-bottom: 1px solid var(--color-border-subtle);
}

.gallery-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: var(--space-4);
}
```

Personalizar scrollbar de forma discreta.

---

# 11. Fase 6 — Visor principal

## 11.1 Responsabilidad del visor

El visor responde a:

- ¿Qué imagen estoy revisando?
- ¿Cómo se ve completa?
- ¿Puedo cambiar zoom/modo de vista?
- ¿Puedo comparar si procede?

No debe contener:

- configuración de salida;
- selector de fondo permanente si no es estrictamente de revisión;
- diagnóstico del lote;
- tarjetas de aviso;
- datos administrativos.

## 11.2 Estructura recomendada

```text
S670373590110.png                 ‹ 1 / 44 › [Ajustar] [100%] [-] [81%] [+]

┌──────────────────────────────────────────────────────────────┐
│                                                              │
│                    imagen completa                            │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## 11.3 Reducir capas visuales

Evitar estructura excesiva:

```text
canvas gris
  marco blanco
    fondo gris
      imagen
```

Preferir una única superficie de revisión:

```css
.viewer-stage {
  flex: 1;
  min-height: 0;
  display: grid;
  place-items: center;
  padding: var(--space-5);
  background: var(--color-bg-app);
}

.viewer-frame {
  height: min(100%, calc(100dvh - 140px));
  max-width: min(100%, 760px);
  aspect-ratio: 3 / 4;
  display: grid;
  place-items: center;
  border-radius: var(--radius-lg);
  background: var(--preview-bg, #e6e6e6);
  box-shadow: inset 0 0 0 1px var(--color-border-subtle);
  overflow: hidden;
}

.viewer-image {
  display: block;
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: auto;
  object-fit: contain;
}
```

## 11.4 Optimización para imágenes verticales

El frame debe tener ratio de salida o ratio aproximado del producto.

Para salida 1800 × 2400:

```css
aspect-ratio: 3 / 4;
```

Esto hará que el visor parezca una mesa de revisión vertical, no una lona horizontal vacía.

## 11.5 Toolbar del visor

Unificar controles en una barra ligera:

```text
‹ 1 / 44 ›  [Ajustar] [100%] [-] [81%] [+]
```

Reglas:

- controles pequeños;
- estilo segmented/toolbar;
- no ocupar demasiada altura;
- no repetir información de galería;
- `Ajustar` activo por defecto.

## 11.6 Selector de fondo

Mover `Fondo: RGB230 / Blanco / Transparente` al inspector.

Si se mantiene en el visor, debe ser un control flotante mínimo, no una barra inferior fija.

Preferencia para esta fase: **moverlo al inspector > Ajustes o Salida**.

---

# 12. Fase 7 — Inspector derecho

## 12.1 Responsabilidad del inspector

El inspector debe responder a:

- ¿Qué salida se va a generar?
- ¿Qué preset/ajuste se aplica?
- ¿Hay avisos relevantes para esta imagen o lote?

Debe organizarse mediante pestañas claras.

## 12.2 Pestañas recomendadas

Usar tres pestañas si el espacio y el estado lo justifican:

```text
[Salida] [Ajustes] [Avisos]
```

Si se prefiere mantener dos:

```text
[Salida] [Ajustes]
```

y los avisos viven dentro de `Salida` como bloque discreto o en diagnóstico.

Recomendación: tres pestañas si ya hay avisos frecuentes; dos pestañas si se quiere máxima limpieza.

## 12.3 Pestaña Salida

Contenido:

```text
SALIDA

Preset aplicado
Luz cenital

Formato       JPG
Tamaño        1800 × 2400
Fondo         RGB230
Destino       _SALIDA_PRO
Nombre        original + _PRO

[Exportar 44]
```

Reglas:

- este es el lugar principal del fondo `RGB230`;
- este es el lugar principal del destino;
- este es el lugar principal del nombre de salida;
- no repetir estos datos en footer.

## 12.4 Pestaña Ajustes

Contenido:

```text
AJUSTES

Preset
[Luz cenital ▼]

Presets rápidos
[Luz cenital] [Estándar oscuro] [Percha 2025]

Ajustes principales
Opacidad
Blur
Distancia
Padding

Fondo de revisión
[RGB230] [Blanco] [Transparente]

> Avanzado
```

## 12.5 Pestaña Avisos

Contenido:

```text
AVISOS

1 aviso no bloqueante
Thumbs.db · Extensión no admitida
Archivo ignorado automáticamente.

[Ver diagnóstico completo]
```

No usar una tarjeta amarilla grande para un aviso menor.

## 12.6 Diseño visual del inspector

CSS conceptual:

```css
.inspector-panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: var(--color-bg-surface);
}

.inspector-tabs {
  flex: 0 0 auto;
  padding: var(--space-3) var(--space-4) 0;
}

.inspector-content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: var(--space-4);
}

.inspector-section + .inspector-section {
  margin-top: var(--space-6);
}

.inspector-kv {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: var(--space-2) var(--space-4);
  font-size: var(--font-size-sm);
}

.inspector-kv dt {
  color: var(--color-text-secondary);
}

.inspector-kv dd {
  margin: 0;
  font-weight: var(--font-weight-semibold);
}
```

---

# 13. Fase 8 — Componentes compartidos

Crear o normalizar estos componentes visuales.

## 13.1 Botones

### Primario

Uso exclusivo:

- `Exportar 44`;
- acción principal equivalente.

```css
.ui-button--primary {
  background: var(--color-accent);
  color: #fff;
  border-color: var(--color-accent);
  font-weight: var(--font-weight-semibold);
}

.ui-button--primary:hover {
  background: var(--color-accent-hover);
}
```

### Secundario

Uso:

- `Cambiar`;
- `Reset`;
- `Actualizar`;
- acciones de bajo riesgo.

### Ghost/link

Uso:

- `Ver diagnóstico`;
- `Ver detalle`;
- acciones contextuales.

## 13.2 Chips

Uso:

- filtros;
- presets rápidos;
- estados suaves.

No mezclar chips con botones de acción.

## 13.3 Badges

Uso:

- avisos;
- omitidas;
- errores;
- estados no interactivos.

Sistema:

```text
Correcta  = punto verde o badge muy discreto
Aviso     = badge naranja suave
Omitida   = badge gris
Error     = badge rojo sólo si bloquea
```

## 13.4 Cards

Usar cards sólo para:

- resumen del lote;
- salida;
- aviso importante;
- diagnóstico expandido.

No usar cards para todo.

## 13.5 Inputs

Input de búsqueda:

- icono de lupa;
- placeholder claro;
- botón de limpiar si hay texto;
- altura coherente con los chips.

## 13.6 Scrollbars

Crear estilo discreto común:

```css
.ui-scrollarea {
  scrollbar-width: thin;
  scrollbar-color: rgba(15, 23, 42, 0.22) transparent;
}

.ui-scrollarea::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.ui-scrollarea::-webkit-scrollbar-thumb {
  background: rgba(15, 23, 42, 0.18);
  border-radius: var(--radius-pill);
}

.ui-scrollarea::-webkit-scrollbar-thumb:hover {
  background: rgba(15, 23, 42, 0.28);
}
```

---

# 14. Fase 9 — Estados visuales coherentes

## 14.1 Estados de imagen

Definir una función o mapa central:

```js
const IMAGE_STATUS_META = {
  ready: {
    label: 'Correcta',
    tone: 'success',
  },
  warning: {
    label: 'Aviso',
    tone: 'warning',
  },
  omitted: {
    label: 'Omitida',
    tone: 'muted',
  },
  error: {
    label: 'Error',
    tone: 'danger',
  },
};
```

Evitar que cada componente invente su propia representación visual.

## 14.2 Estados de miniatura

```text
loading     = skeleton
loaded      = imagen real
failed      = placeholder discreto
omitted     = atenuada + motivo si se abre detalle
```

## 14.3 Estados de lote

```text
empty       = seleccionar carpeta
scanning    = escaneando
ready       = lote listo
warnings    = lote listo con avisos
error       = error bloqueante
```

## 14.4 Estados de exportación

```text
pending     = salida pendiente
ready       = listo para exportar
exporting   = exportando
completed   = exportación completada
failed      = error al exportar
```

Cada estado debe tener:

- label;
- color/tone;
- acción posible;
- lugar de visualización principal.

---

# 15. Fase 10 — Eliminar repetición visual y textual

Hacer una pasada específica para borrar duplicidades.

## 15.1 Header

Mantener:

- marca;
- lote resumido;
- aviso resumido;
- exportar.

Eliminar:

- salida detallada;
- preset si se repite en inspector;
- datos técnicos.

## 15.2 Lote

Mantener:

- total;
- carpeta;
- resumen;
- diagnóstico.

Eliminar:

- búsqueda;
- filtros;
- miniaturas.

## 15.3 Galería

Mantener:

- búsqueda;
- filtros;
- miniaturas;
- contador.

Eliminar:

- resumen administrativo de lote;
- diagnóstico completo;
- datos de salida.

## 15.4 Visor

Mantener:

- filename;
- posición;
- zoom;
- imagen.

Eliminar:

- fondo como barra fija;
- salida;
- diagnóstico;
- avisos de lote.

## 15.5 Inspector

Mantener:

- salida;
- ajustes;
- avisos si se decide.

Eliminar:

- navegación de imágenes;
- resumen de lote;
- repetición de `44 imágenes`.

---

# 16. Fase 11 — Responsive desktop

No hace falta una versión móvil, pero sí evitar roturas.

## 16.1 Desktop amplio

```text
Lote | Galería | Visor | Inspector
```

## 16.2 Desktop medio

Si el ancho baja, reducir:

- lote a 210px;
- galería a 300px;
- inspector a 300px.

## 16.3 Desktop estrecho

Permitir colapsar lote o inspector.

Ejemplo:

```css
@media (max-width: 1280px) {
  .app-main {
    grid-template-columns: 220px 300px minmax(520px, 1fr);
  }

  .inspector-panel {
    display: none;
  }
}
```

O usar un botón para mostrar inspector en drawer si ya existe patrón.

No implementar mobile complejo salvo que sea fácil.

---

# 17. Fase 12 — Accesibilidad y polish interactivo

## 17.1 Focus

Todos los botones, inputs, chips y items seleccionables deben tener focus visible.

```css
:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}
```

## 17.2 Cursor

- botones: `cursor: pointer`;
- elementos deshabilitados: `cursor: not-allowed`;
- texto normal: no debe parecer seleccionable si no lo es;
- inputs: cursor de texto.

## 17.3 No depender sólo del color

Estados de aviso/error deben tener:

- color;
- texto o icono;
- tooltip o detalle si procede.

## 17.4 Área clicable

Las miniaturas deben tener área clicable clara.

Mínimo recomendado: 40px de altura interactiva.

---

# 18. Fase 13 — Plan técnico de implementación paso a paso

## Paso 1 — Crear rama o checkpoint

Antes de tocar nada:

```bash
git status
```

Si procede:

```bash
git checkout -b ui-system-redesign
```

No continuar si hay cambios no relacionados sin identificar.

## Paso 2 — Auditar estructura

Abrir y revisar:

- archivos de entrada;
- componentes actuales;
- CSS;
- estado global;
- estructura de datos de imágenes.

Documentar mentalmente o en comentario de entrega.

## Paso 3 — Introducir tokens

Añadir variables CSS globales.

No cambiar todos los componentes todavía. Primero dejar los tokens disponibles.

## Paso 4 — Crear clases base

Añadir estilos base para:

- botones;
- chips;
- badges;
- inputs;
- cards;
- section labels;
- scrollbars.

## Paso 5 — Rehacer AppShell

Implementar estructura:

```text
AppShell
Header
MainGrid
```

Asegurar:

- `height: 100dvh`;
- sin scroll global;
- grid de 4 columnas;
- `min-width: 0`;
- `min-height: 0`.

## Paso 6 — Header limpio

Eliminar duplicidades y controles técnicos.

Dejar:

- FlatShot;
- contexto mínimo;
- aviso si existe;
- exportar.

## Paso 7 — Refactor BatchRail

Convertirlo en columna ligera:

- header de lote;
- carpeta;
- acciones compactas;
- resumen;
- diagnóstico.

Mover búsqueda y filtros a galería.

## Paso 8 — Refactor GalleryColumn

Crear toolbar de galería:

- título `Imágenes`;
- contador;
- buscador;
- filtros.

Crear grid scrollable.

Eliminar galería inferior si sigue existiendo.

## Paso 9 — Refinar miniaturas

Implementar `GalleryItem` maduro:

- thumbnail real;
- selección;
- nombre truncado;
- metadata mínima;
- estado discreto;
- placeholder profesional si falla.

## Paso 10 — Refactor Viewer

Reducir capas.

Implementar:

- viewer header;
- toolbar ligera;
- frame vertical 3:4;
- imagen con `contain`;
- sin barra inferior de fondo.

## Paso 11 — Refactor Inspector

Crear pestañas claras.

Implementar:

- Salida;
- Ajustes;
- Avisos opcional.

Mover `RGB230`, destino y nombre de salida aquí.

## Paso 12 — Eliminar footer o hacerlo condicional

Si no hay proceso activo, no mostrarlo.

Si se mantiene, debe ser mínimo y no repetir datos.

## Paso 13 — Pasada de consistencia visual

Revisar pantalla completa:

- padding;
- separación;
- bordes;
- radios;
- tipografía;
- estado activo;
- hover;
- scroll;
- texto repetido.

## Paso 14 — Pasada de estados

Probar:

- lote con aviso;
- lote sin aviso;
- imagen con preview;
- imagen sin preview;
- selección;
- filtro sin resultados;
- búsqueda sin resultados;
- exportación pendiente;
- salida lista.

## Paso 15 — Limpieza de CSS

Eliminar clases antiguas no usadas.

Evitar dejar estilos duplicados que contradigan tokens.

## Paso 16 — Tests/build

Ejecutar los comandos disponibles:

```bash
npm run lint
npm run build
npm test
```

O los equivalentes reales del proyecto.

Si no existen, indicarlo en la entrega.

---

# 19. Criterios de aceptación visual

No terminar la tarea hasta cumplir:

1. La pantalla parece una herramienta profesional, no una maqueta funcional.
2. Todas las columnas tienen un rol claro.
3. El sistema de espaciado es consistente.
4. La tipografía tiene jerarquía clara.
5. Los botones tienen jerarquía clara.
6. Los chips y badges comparten lenguaje visual.
7. Las tarjetas no se usan indiscriminadamente.
8. El lote no contiene navegación visual.
9. La galería contiene búsqueda, filtros y miniaturas.
10. El visor está optimizado para imágenes verticales.
11. El inspector separa salida y ajustes de forma real.
12. Los avisos menores no dominan la UI.
13. El footer no repite información ni corta contenido.
14. No hay padding roto ni elementos pegados al borde.
15. No hay scroll global innecesario.
16. La interfaz mantiene coherencia visual aunque cada zona tenga su función.

---

# 20. Criterios de aceptación funcional

No terminar si falla cualquiera de estos puntos:

1. La imagen seleccionada se ve completa por defecto.
2. Las miniaturas reales se ven.
3. El grid de galería permite navegar por 44 imágenes.
4. El filtro activo no rompe el layout.
5. La búsqueda no rompe el layout.
6. El inspector mantiene su scroll interno si lo necesita.
7. El lote mantiene su scroll interno si lo necesita.
8. No hay overflow horizontal global.
9. El botón `Exportar 44` sigue funcionando o mantiene su flujo actual.
10. El bridge local sigue funcionando.
11. El modo mock sigue funcionando.
12. Los avisos/omitidas/errores no se mezclan visualmente.

---

# 21. Checklist de revisión manual

## 21.1 Layout

- [ ] Header limpio.
- [ ] Grid de 4 columnas correcto.
- [ ] Lote compacto.
- [ ] Galería visual independiente.
- [ ] Visor centrado y vertical.
- [ ] Inspector claro.
- [ ] Footer eliminado o mínimo.
- [ ] Sin scroll global.

## 21.2 Visual

- [ ] Padding consistente.
- [ ] Tipografía consistente.
- [ ] Bordes sutiles.
- [ ] Radios coherentes.
- [ ] Botón primario único.
- [ ] Botones secundarios discretos.
- [ ] Chips compactos.
- [ ] Badges coherentes.
- [ ] Scrollbar discreta.
- [ ] Estados hover/focus correctos.

## 21.3 Galería

- [ ] Miniaturas reales.
- [ ] Placeholder discreto si falla preview.
- [ ] Selección clara.
- [ ] Nombres truncados.
- [ ] Metadata mínima.
- [ ] Filtros funcionan.
- [ ] Búsqueda funciona.
- [ ] Scroll propio.

## 21.4 Visor

- [ ] Imagen completa.
- [ ] `Ajustar` por defecto.
- [ ] Zoom manual funciona.
- [ ] Redimensionado correcto.
- [ ] Fondo no genera ruido.
- [ ] No hay capas visuales innecesarias.

## 21.5 Inspector

- [ ] Salida separada.
- [ ] Ajustes separados.
- [ ] Fondo RGB230 movido aquí.
- [ ] Avisos discretos.
- [ ] Exportar claro.
- [ ] Scroll interno correcto.

---

# 22. Entrega esperada de Codex

Al terminar, Codex debe responder con:

1. Resumen de la intervención.
2. Archivos modificados.
3. Componentes creados o refactorizados.
4. Tokens de diseño añadidos.
5. Cambios de layout.
6. Cambios en lote.
7. Cambios en galería.
8. Cambios en visor.
9. Cambios en inspector.
10. Qué duplicidades se han eliminado.
11. Qué estados visuales se han normalizado.
12. Qué pruebas manuales se han realizado.
13. Resultado de lint/build/test.
14. Limitaciones o deuda técnica pendiente.

---

# 23. Prompt final para ejecutar en Codex

Usar este prompt como instrucción directa:

```md
Necesito que implementes una revisión profunda de la pantalla principal de FlatShot siguiendo el documento de plan adjunto.

La prioridad absoluta es elevar la interfaz a un nivel visual y estructural mucho más profesional. No quiero retoques superficiales. Quiero un sistema de diseño real, una arquitectura de columnas clara y una interfaz coherente donde cada zona tenga una responsabilidad definida.

Puntos clave:

1. Crea o consolida tokens de diseño: colores, tipografía, spacing, radios, sombras, estados y layout.
2. Reestructura el shell principal en 4 columnas: Lote, Galería, Visor e Inspector.
3. Elimina repetición de información. Cada dato debe tener un lugar principal.
4. Lote debe quedar como resumen/diagnóstico, no como navegación visual.
5. Galería debe contener búsqueda, filtros y miniaturas reales.
6. Visor debe estar optimizado para imágenes verticales, con frame 3:4 y la imagen completa visible por defecto.
7. Inspector debe separar claramente Salida y Ajustes. Mueve aquí fondo, destino, nombre de salida y preset.
8. Elimina o minimiza el footer si sólo repite información.
9. Normaliza botones, chips, badges, cards, inputs, scrollbars, focus, hover y estados.
10. Asegura que bridge local y modo mock siguen funcionando.
11. No termines si la UI sigue pareciendo una maqueta HTML o un dashboard administrativo.

Antes de implementar, audita la estructura actual. Después aplica el plan por fases. Al terminar, entrega resumen de cambios, archivos modificados, pruebas realizadas y limitaciones.
```

---

# 24. Nota de criterio final

Este rediseño no debe perseguir simplemente que “se vea más bonito”. Debe resolver la inmadurez estructural de la interfaz.

Una pantalla profesional no se reconoce sólo por colores o sombras. Se reconoce porque:

- cada zona tiene una función clara;
- los datos no se repiten sin motivo;
- el usuario sabe dónde mirar;
- las acciones tienen jerarquía;
- los estados son consistentes;
- el espaciado tiene ritmo;
- los componentes parecen pertenecer al mismo sistema;
- la interfaz se adapta al contexto sin romper su lenguaje visual.

Ese es el objetivo de esta fase.
