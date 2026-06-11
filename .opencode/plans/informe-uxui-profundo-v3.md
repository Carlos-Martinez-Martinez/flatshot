# FlatShot — Informe Profundo de UX/UI (v3)

## Resumen ejecutivo

FlatShot ha recorrido 42+ fases de refactor UX/UI y extracción de helpers JS.
La aplicación funciona correctamente y tiene una estructura reconocible, pero **no
alcanza el nivel de producto profesional cerrado**. Tras inspeccionar las 13.819
líneas de CSS en 3 capas, las ~6.888 líneas de app.js con estado centralizado, y
los 23 módulos JS extraídos, el diagnóstico es el siguiente:

**El problema ya no es de funcionalidad ni de estructura gruesa. Es de sistema
visual incompleto, densidad inconsistente, estados mezclados y cascada CSS
fragmentada.**

Este informe clasifica las mejoras en 5 niveles de prioridad y propone un plan
de acción realista, ordenado por impacto/riesgo.

---

## 1. Inventario actual del sistema

### 1.1. CSS: tres capas con fragmentación acumulada

| Archivo | Líneas | `!important` | Tokens | `@media` |
|---------|--------|-------------|--------|----------|
| `styles.css` | 9.028 | 122 | 288 | 20 |
| `ux-foundation.css` | 3.469 | 102 | 134 | 10 |
| `ux-refactor.css` | 1.322 | 113 | 16 | 4 |
| **Total** | **13.819** | **337** | **438** | **34** |

**Problemas estructurales:**

1. **145 tokens declarados más de una vez.** `--column-gallery` y
   `--column-inspector` se redeclaran 11 veces cada uno en distintas capas. Esto
   hace imposible saber qué valor gobierna sin inspeccionar toda la cascada.

2. **337 declaraciones `!important`** indican que la cascada se usa como
   mecanismo de control, no como sistema. Cada nuevo override requiere otro
   `!important` más específico, creando una espiral de especificidad.

3. **Selectores superpuestos.** `.gallery-column` tiene 131 apariciones,
   `.settings-panel` 129, `.app-shell` 104. Muchas de estas reglas compiten por
   el mismo layout (grid-template-columns, display, padding).

4. **Tres definiciones del grid principal.** El layout de 3 columnas se declara
   en `styles.css` (línea ~449), se sobreescribe en `ux-foundation.css` (líneas
   ~850, ~1229, ~1470) y se vuelve a sobreescribir en `ux-refactor.css` (líneas
   ~38, ~757, ~768). Cada capa redefine columnas, filas y visibilidad de paneles
   para los mismos estados. Resultado: comportamiento impredecible al cambiar un
   solo valor.

5. **Falta de fuente canónica de tokens.** Aunque `docs/FLATSHOT_DESIGN_SYSTEM.md`
   define una intención clara, los tokens reales viven dispersos en las 3 capas
   sin un orden de precedencia documentado.

### 1.2. JavaScript: extracción avanzada pero estado aún centralizado

**Progreso real:** 23 módulos JS extraídos desde `app.js`, pasando de ~8.734
líneas a ~6.888. Los helpers cubren: formatters, output profiles, export payload,
export state, preview state, scan state, gallery, settings, y vistas de
inspector/resultado/confirmación.

**Problemas que persisten:**

1. **Estado global sin dominio.** El objeto `state` (línea 290 de app.js) tiene
   60+ campos que mezclan: lote, selección, preview, zoom, filtros, inspector,
   presets, exportación, bridge, escaneo, mocks y overrides. No hay agrupación
   por dominio ni transiciones centralizadas.

2. **Mutación directa desde ~639 ubicaciones.** Cualquier función puede modificar
   `state.*` directamente. No hay un contrato claro de qué campos son fuente de
   verdad y cuáles son derivables.

3. **Renderizado sigue en app.js.** Las 10 funciones principales de render
   (`renderTop`, `renderBatch`, `renderPreview`, `renderSettings`,
   `renderInspector`, `renderAppSettings`, `renderFooter`, etc.) todavía están en
   `app.js`. Los helpers extraídos solo cubren sub-renderizados.

4. **Persistencia en localStorage sin capa de abstracción.** Las claves se
   acceden directamente con `readPersistentValue` y `writePersistentValue`, sin
   validación de esquema ni migración.

### 1.3. HTML: estructura correcta pero con ruido de desarrollo

El `index.html` (677 líneas) tiene la estructura correcta pero incluye:

- Panel de revisión/demo con 10 escenarios simulados (`#demo-scenario`) y botones
  de revisión que solo deberían aparecer en modo desarrollo.
- Panel de debug (`#debug-panel`) con controles de modo mock/bridge, URL,
  capacidades y preview debug.
- Elementos ocultos por defecto que compiten con reglas CSS de visibilidad
  (`hidden`, `display: none !important`, `data-ui-state`).

La regla `html:not(.dev-mode) .debug-panel { display: none !important; }`
(línea 1555 de `ux-foundation.css`) funciona, pero es un parche sobre un
problema de arquitectura: los controles de desarrollo no deberían estar en el
HTML de producción.

---

## 2. Problemas detectados por zona

### 2.1. Cabecera global (top-bar)

**Estado actual:** Correcto en estructura. Logo + acciones globales.

**Problemas:**

| # | Problema | Gravedad | Ubicación |
|---|----------|----------|-----------|
| H1 | Botón primario `Exportar X archivos` compite visualmente con los secundarios `Salida`, `Carpeta`, `Nuevo lote`. Estilos duplicados entre `styles.css:421-436`, `ux-foundation.css:1538-1540` y `ux-refactor.css:1937-1950`. | Media | `styles.css:421`, `ux-foundation.css:1538`, `ux-refactor.css:1937` |
| H2 | El chip `Bridge pendiente` (#bridge-status) aparece incluso en modo producción mock, mostrando "Bridge pendiente" cuando no aplica. | Baja | `index.html:27`, `styles.css:391-420` |
| H3 | `Escaneando...` como botón deshabilitado (durante scanning) no se distingue suficientemente de un botón activo. La regla en `ux-refactor.css:1285-1290` aplica `color: var(--color-text-muted)` y `cursor: default`, pero el borde y fondo pueden confundirse. | Media | `ux-refactor.css:1285-1290` |
| H4 | Los botones secundarios (`Salida`, `Carpeta`, `Nuevo lote`) alternan entre `min-height: 34px` vs `36px` en distintas capas. | Media | `ux-refactor.css:1952-1962`, `ux-foundation.css:1521-1526` |

### 2.2. Galería izquierda (gallery-column)

**Estado actual:** Mejorada respecto a versiones anteriores. Sin badges "✓ Lista"
por miniatura. Vista de thumbs y lista funcionales.

**Problemas:**

| # | Problema | Gravedad | Ubicación |
|---|----------|----------|-----------|
| G1 | **Falta jerarquía de panel.** La galería no tiene un título claro de sección. El `<strong id="gallery-title">` muestra "0 imágenes" pero no hay etiqueta "Lote" o "Galería" visible. | Alta | `index.html:173-175` |
| G2 | El selector de vista `Lista / Miniaturas` aparece como primer elemento dominante (`.gallery-view-switch` con `justify-self: end` y `grid-column: 1 / -1`), relegando el contador. | Media | `ux-refactor.css:856-859` |
| G3 | Las miniaturas en vista thumbs tienen `aspect-ratio: 4 / 5` (ux-refactor.css:263), pero `min-height: 158px` (ux-refactor.css:256) y `148px` (ux-refactor.css:886). Valores inconsistentes entre capas. | Baja | `ux-refactor.css:256, 263, 886` |
| G4 | El fondo de miniatura (`.thumb`) usa `background: #e6e6e6` en ux-refactor.css:905 pero `linear-gradient(...)` con variantes `tone-a` a `tone-e` en styles.css:852-868. Las clases `tone-*` se asignan en mock pero no se usan en datos reales del bridge. | Media | `styles.css:847-868`, `ux-refactor.css:903-921` |
| G5 | La semántica del fondo de miniatura no está definida explícitamente: ¿representa el preset activo, el fondo de salida, o la imagen original? `data-output-bg` cambia el fondo (ux-refactor.css:908-921) pero no hay documentación de esta decisión. | Media | `ux-refactor.css:908-921` |
| G6 | El botón de limpiar búsqueda (`#image-search-clear`) usa `visibility: hidden` con clase `.is-visible` en lugar de `display: none`. Esto reserva espacio aunque esté invisible. | Baja | `ux-refactor.css:869-877` |

### 2.3. Visor central (preview-panel + canvas)

**Estado actual:** Mejorado. Nombre de archivo visible. Controles agrupados.
Canvas centrado.

**Problemas:**

| # | Problema | Gravedad | Ubicación |
|---|----------|----------|-----------|
| V1 | **Selector de fondo híbrido.** El control de fondo (`Gris / Blanco / Transparente`) intenta ser un segmented control pero: (a) en `ux-refactor.css:134-144` los botones tienen `gap: 6px` y `::before` con círculos/swatches de 13px; (b) en `ux-refactor.css:1292-1296` los swatches cambian a 12px con `border-radius: 3px`; (c) en `ux-foundation.css` el control es parte de `.viewer-background-switch` con estilos propios. Tres definiciones distintas para el mismo componente. | Alta | `ux-refactor.css:134-169`, `ux-refactor.css:1292-1296`, `ux-foundation.css` |
| V2 | **Toolbar no homogénea.** Los controles de navegación (`‹ ›`), ajuste (`Encajar Alto 1:1`) y zoom (`- 100% +`) tienen estilos diferentes: algunos usan `.viewer-control-group` con borde y fondo, otros son botones sueltos. La toolbar parece ensamblada con piezas de distintos sistemas. | Alta | `index.html:222-238`, `styles.css:996-1027`, `ux-foundation.css:1308-1338` |
| V3 | **Modo "Procesada" oculto.** `ux-refactor.css:95-97` oculta el botón `[data-preview-mode="processed"]` con `display: none !important`. Esto deja solo "Original" y "Comparar" como opciones visibles, pero el estado por defecto sigue siendo "processed". Es una inconsistencia funcional. | Alta | `ux-refactor.css:95-97` |
| V4 | **Fondo de canvas y fondo de revisión mezclados.** `canvas-area` usa `--canvas-bg` (#e6e9e8) como fondo, `.bg-rgb230` cambia a `#e6e6e6`, `.bg-white` a `#fff`, `.bg-transparent` a patrón de damero. Pero `ux-refactor.css:183-189` fuerza `background: var(--color-bg-stage) !important` para `.canvas-area` y `.bg-rgb230`, anulando la diferenciación de `styles.css`. | Alta | `styles.css:1029-1056`, `ux-refactor.css:183-205` |
| V5 | `preview-footer` oculto con `display: none !important` (ux-refactor.css:68-69 y ux-foundation.css:1702-1704). Esto elimina la barra de metadatos inferior, pero el HTML sigue renderizándola. | Baja | `ux-refactor.css:68`, `ux-foundation.css:1702` |
| V6 | El zoom label `#zoom-label` tiene `min-width: 42px` en styles.css:1025, `46px` en ux-foundation.css:1337 y `40px` en ux-refactor.css:179. | Baja | `styles.css:1025`, `ux-foundation.css:1337`, `ux-refactor.css:179` |

### 2.4. Panel derecho / Inspector (settings-panel)

**Estado actual:** Panel con tabs (Resumen, Exportación, Avisos, Avanzado) y
secciones colapsables. Sufrió múltiples rediseños.

**Problemas:**

| # | Problema | Gravedad | Ubicación |
|---|----------|----------|-----------|
| P1 | **Tabs ocultos.** `ux-refactor.css:1722-1724` oculta `.inspector-tabs` con `display: none !important`. Pero en `ux-foundation.css:591` los tabs se muestran como `grid-template-columns: repeat(4, ...)`. El resultado depende de qué capa gana. | Alta | `ux-refactor.css:1722`, `ux-foundation.css:591` |
| P2 | **Secciones mezcladas.** Las secciones del inspector usan clases inconsistentes: algunas son `.settings-section`, otras `.review-card`, otras `.inspector-card`. No comparten el mismo padding, borde ni radio. | Alta | `styles.css:1266-1271`, `ux-foundation.css:615-626`, `ux-refactor.css:1731-1740` |
| P3 | **Badge "Activa" duplicando checkbox.** En filas de salida activa, el checkbox ya indica estado activo, pero `ux-refactor.css:994-1008` agrega un badge `.active-output-row__tag` con borde y fondo. La información se duplica visualmente. | Media | `ux-refactor.css:994-1008` |
| P4 | **Demasiados verdes.** El color `--accent` (#087d69) y sus variantes se usan para: botón primario, estado seleccionado, estado activo, chip "Principal", indicador "Listo", y badge de éxito. Esto diluye la jerarquía visual: el usuario no distingue qué es accionable, qué es estado y qué es selección. | Alta | Global en las 3 capas CSS |
| P5 | **Padding inconsistente.** `settings-panel` tiene `padding: var(--space-3)` (12px) en styles.css:475, `var(--panel-pad)` (12px) en ux-foundation.css:1719, `var(--space-3)` en ux-refactor.css:311, y `var(--space-4)` (16px) en ux-refactor.css:963. | Media | `styles.css:475`, `ux-foundation.css:1719`, `ux-refactor.css:311,963` |
| P6 | **"Avanzado" siempre colapsado** por accesibilidad (correcto), pero el indicador `Avanzado · 2 cambios` no muestra qué parámetros cambiaron sin expandir. | Baja | `index.html:327-385` |

### 2.5. Editor de ajustes de imagen (settings/controls)

**Estado actual:** Es la zona más problemática identificada en el informe v2 y
sigue sin resolverse del todo.

**Problemas:**

| # | Problema | Gravedad | Ubicación |
|---|----------|----------|-----------|
| A1 | **Encabezados duplicados.** El HTML tiene: `Gestionar ajustes` (línea 270), `Controles principales` (línea 299), `Avanzado` (línea 330), `Ajuste por imagen` (línea 390). En modo edición, el panel muestra múltiples niveles de títulos que compiten. | Muy alta | `index.html:267-385` |
| A2 | **Gestión de ajustes mezclada con edición.** El `<details class="preset-section">` incluye tanto la lista de presets guardados como los sliders de edición. Al expandir "Gestionar ajustes", el usuario ve: chips de presets, botones de guardar/exportar/eliminar/restaurar/listo. Esto es un gestor de presets, no un editor de ajustes. La edición operativa (sliders) está en un `<details>` separado (`appearance-section`). | Muy alta | `index.html:267-294`, `index.html:296-325` |
| A3 | **Sliders sin componente unificado.** Los controles de slider+input numérico están definidos con 3 grillas diferentes: `.control-row` en `styles.css:1322-1328` (78px / 1fr / 38px), `.advanced-controls .control-row` en `styles.css:1491-1493` (86px / 1.4fr / 44px), y `.control-row` en `ux-refactor.css:1047-1050` (84px / 1fr / 72px). La alineación visual es impredecible. | Alta | `styles.css:1322,1491`, `ux-refactor.css:1047` |
| A4 | **Inputs numéricos con ancho variable.** `.number-input` tiene `width: 72px` y `min-width: 64px` en `ux-refactor.css:1052-1058`, pero `width: 56px` y `min-width: 56px` en `ux-refactor.css:1078-1083` (modo edición de preset). | Media | `ux-refactor.css:1052-1058, 1078-1083` |
| A5 | **Ajuste local usa grid distinta.** `.local-control-row` tiene su propia definición de columnas en `ux-refactor.css:456-462` y otra en `ux-refactor.css:490-491`. | Media | `ux-refactor.css:456, 490` |
| A6 | El botón `Guardar cambios` (#save-preset) debería estar deshabilitado cuando no hay cambios (ya implementado en `ux-refactor.css:1318-1321`), pero no hay indicador visual de por qué está disabled (tooltip o texto auxiliar). | Baja | `ux-refactor.css:1318-1321` |

### 2.6. Modal de Gestor de Salidas (app-settings-modal)

**Estado actual:** Mejorado respecto a versiones anteriores. Formulario más
legible, lista de presets más clara.

**Problemas:**

| # | Problema | Gravedad | Ubicación |
|---|----------|----------|-----------|
| M1 | **Overlay no normalizado.** El modal usa clases `.app-settings-backdrop` + `.app-settings-dialog`, mientras que el detalle de lote usa las mismas clases con variantes `.batch-detail-backdrop` + `.batch-detail-dialog`. Comparten estructura pero tienen anchos distintos (1040px vs 820px) definidos en capas diferentes. | Media | `index.html:489-631`, `styles.css:1794-1814`, `ux-refactor.css:555-571` |
| M2 | **Footer del gestor ambiguo.** Los botones del footer son: `Cancelar`, `Guardar cambios`, `Aplicar cambios al lote`. No queda claro si "Aplicar cambios al lote" también guarda el preset o solo lo activa temporalmente. | Media | `index.html:626-629` |
| M3 | **Columna izquierda demasiado ancha.** `ux-refactor.css:576` define `grid-template-columns: minmax(340px, 0.92fr) minmax(420px, 1.08fr)` para el contenido del modal. En viewports de 1280px, la columna izquierda ocupa ~340px para una lista de presets que suele tener 3-4 elementos. | Baja | `ux-refactor.css:576` |

### 2.7. Detalle de lote (batch-detail-modal)

**Estado actual:** Mejorado como vista de auditoría con secciones colapsables.

**Problemas:**

| # | Problema | Gravedad | Ubicación |
|---|----------|----------|-----------|
| D1 | **Mismo patrón de overlay inconsistente que el gestor.** Usa clases similares pero con anchos y comportamientos diferentes (920px en ux-refactor.css:650). | Media | `ux-refactor.css:649-658` |
| D2 | **Foco del botón cerrar.** `styles.css:171-177` define `:focus-visible` con `box-shadow: var(--focus-ring)` (verde). Esto es correcto para navegación por teclado, pero si el foco queda atrapado tras cerrar con ratón, el anillo verde persiste. | Baja | `styles.css:171-177` |

### 2.8. Empty state y estado de escaneo

**Estado actual:** Corregido en fases anteriores. Estado de escaneo ahora oculta
paneles laterales (una columna).

**Problemas:**

| # | Problema | Gravedad | Ubicación |
|---|----------|----------|-----------|
| E1 | El empty state onboarding (`.empty-state.onboarding`) fuerza `border-style: solid !important` en `ux-refactor.css:1095-1097`, anulando el `dashed` definido en `ux-refactor.css:523`. La intención no está documentada. | Baja | `ux-refactor.css:523, 1095` |
| E2 | La card de onboarding tiene `min-height: 320px` (ux-refactor.css:522) pero su contenido (icono + título + subtítulo + botón) mide ~220px. El espacio extra no se usa. | Baja | `ux-refactor.css:521-525` |

### 2.9. Barra inferior (bottom-bar / footer)

**Estado actual:** Ocultada por defecto en la mayoría de estados
(`grid-template-rows: ... 0 !important` en ux-foundation.css:1461).

**Problemas:**

| # | Problema | Gravedad | Ubicación |
|---|----------|----------|-----------|
| F1 | La barra inferior se oculta/muestra con `has-status-footer` en `ux-foundation.css:1464-1466` y `ux-refactor.css:1460-1466`. Dos mecanismos compitiendo. | Media | `ux-foundation.css:1460-1466`, `ux-refactor.css:1460-1466` |
| F2 | Los botones de la barra inferior (`Pausar`, `Detener`, `Abrir destino`, `Revisar errores`) solo aparecen durante exportación, pero su visibilidad está controlada por JS manipulando `hidden` y clases CSS con `!important`. | Media | `index.html:643-649`, `app.js` renderFooter |

---

## 3. Problemas transversales

### 3.1. Sistema de color sin suficiente diferenciación semántica

El color verde (`--accent: #087d69`) y sus variantes se usan para **6 conceptos
distintos:**

| Concepto | Uso actual | Debería ser |
|----------|-----------|-------------|
| Acción primaria | `.primary` button background | Verde (correcto) |
| Selección actual | `.image-item.active` border/background | Azul o verde más suave |
| Estado "activo" | Checkbox marcado | Color de checkbox nativo |
| Chip "Principal" | `.active-output-row__tag` | Gris o badge sutil |
| Estado "Listo" | `.status-dot.ready`, `.bridge-chip.ready` | Verde de estado (correcto) |
| Edición/modificado | `preset-dirty` | Ámbar (ya existe `--warning`) |

**Recomendación:** Introducir un color de selección distinto (azul `--semantic-selection`
según el design system, pero no implementado consistentemente).

### 3.2. Densidad visual inconsistente

Componentes similares tienen espaciados diferentes:

| Componente | Padding actual | Debería ser |
|------------|---------------|-------------|
| Inspector card | `var(--card-pad)` = 12px | 12-16px |
| Review card | `var(--space-4)` = 16px | 12-16px |
| Batch summary card | `var(--ui-card-padding)` = 16px | 12-16px |
| Settings panel | 12px en una capa, 16px en otra | 16px |
| Gallery header | `var(--panel-pad)` = 12px | 12-16px |

### 3.3. Alturas de controles sin normalizar

| Elemento | Altura actual | Capa que define |
|----------|--------------|-----------------|
| Botón estándar | `var(--control-h)` = 36px | styles.css |
| Botón compacto | `var(--control-h-sm)` = 30px | styles.css |
| Botón primario (top) | 44px | ux-refactor.css:1939 |
| Botón secundario (top) | 36px en una capa, 34px en otra | ux-refactor.css y ux-foundation.css |
| Botón inspector | `var(--control-h-compact)` = 30px | ux-foundation.css |
| Input/select | `var(--control-h)` = 36px | styles.css |

### 3.4. Microcopy y lenguaje

**Mezcla de idiomas:** La interfaz está principalmente en español, pero hay
términos en inglés:
- `Debug`, `bridge`, `mock`, `preset`, `output`, `export`, `padding`, `spread`,
  `batch`, `folder`, `health`, `liveReload`, `zoom`, `fit`.
- Algunos están naturalizados ("escáner", "preset"), otros no ("debug panel").

**Inconsistencias de términos:**

| Concepto | Término actual (varía) | Recomendado |
|----------|----------------------|-------------|
| Configuración de exportación | "Salida", "Formato", "Preset de salida", "Output profile" | "Salida" (principal), "Configuración de salida" (secundario) |
| Ajuste de imagen | "Ajuste", "Ajustes guardados", "Controles principales", "Avanzado" | "Ajuste" (genérico), "Ajuste guardado" (preset) |
| Lote de imágenes | "Lote", "Carpeta", "Batch" | Unificar a "Lote" |
| Imagen lista para exportar | "Lista", "Exportable", "Válida" | "Lista" |
| Archivos no procesables | "Ignorados técnicos", "Omitidos", "Excluidos" | "Ignorados técnicos" |

### 3.5. Accesibilidad

**Aciertos:**
- `aria-label` en la mayoría de regiones y controles.
- `aria-live="polite"` en zonas dinámicas (estado, preview, resultados).
- `role="dialog"` y `aria-modal="true"` en modales.
- Contraste razonable en la mayoría del texto.

**Problemas detectados:**

| # | Problema | Gravedad |
|---|----------|----------|
| AC1 | No hay gestión de foco al abrir/cerrar modales en todas las rutas. `modalFocusReturnTarget` existe pero no se verifica que siempre se restaure correctamente. | Media |
| AC2 | Los sliders no tienen `aria-valuenow` ni `aria-valuetext` para lectores de pantalla. | Media |
| AC3 | El canvas de preview (`#preview-canvas`) tiene `tabindex="0"` pero no tiene un rol explícito (`role="img"`) ni `aria-label` descriptivo del contenido actual. | Media |
| AC4 | Las imágenes de miniatura (`.thumb`) no tienen `alt` text descriptivo; son divs con `background-image`. | Media |
| AC5 | El foco visible (`:focus-visible`) funciona, pero tras ciertas interacciones con ratón el anillo persiste en botones (especialmente el de cerrar modal). | Baja |
| AC6 | No hay soporte para `prefers-reduced-motion` en animaciones CSS (loader, indeterminate progress, transitions). | Baja |
| AC7 | Las transiciones de altura en detalles/accordions (`.inspector-disclosure__body`) usan `max-height` animado, que no es respetado por `prefers-reduced-motion`. | Baja |

### 3.6. Responsive

**Aciertos:**
- Hay media queries en múltiples breakpoints.
- La galería cambia a 1 columna en pantallas estrechas.
- El inspector se oculta por debajo de 1080px.

**Problemas:**

| # | Problema | Gravedad |
|---|----------|----------|
| R1 | Los breakpoints no están normalizados. Se usan 1240px, 1280px, 1180px, 1080px y 720px sin una escala documentada. | Alta |
| R2 | El inspector desaparece por debajo de 1080px (`display: none !important`). En portátiles estándar (1366x768, 1440x900) el inspector está visible pero muy comprimido; en tablets/monitores pequeños no hay acceso a ajustes ni exportación. | Alta |
| R3 | No hay estilos para viewports menores a 720px. La app no es usable en tablets verticales o monitores pequeños. | Media |
| R4 | Las variables `--column-gallery` y `--column-inspector` usan `clamp()` con valores mínimos que pueden ser demasiado grandes en pantallas pequeñas. | Media |

---

## 4. Priorización de mejoras

Las mejoras se agrupan en 5 niveles. Cada nivel es independiente y puede
implementarse como una fase separada.

### Nivel 1 — Crítico (correcciones que rompen funcionalidad)

| # | Problema | Esfuerzo | Riesgo |
|---|----------|----------|--------|
| **V3** | Modo "Procesada" oculto con `display: none`. El estado por defecto es "processed" pero el botón está oculto. | 5 min | Bajo |
| **V4** | Fondo de canvas forzado que anula la diferenciación de revisión. `bg-rgb230` y `canvas-area` comparten el mismo color en `ux-refactor.css`. | 15 min | Bajo |
| **P1** | Tabs del inspector ocultos/mostrados por capas contradictorias. | 10 min | Bajo |

### Nivel 2 — Alta prioridad (sistema visual y layout)

| # | Problema | Esfuerzo | Riesgo |
|---|----------|----------|--------|
| **G1** | Añadir jerarquía de panel a la galería (título "Lote" visible). | 30 min | Bajo |
| **V1** | Normalizar el selector de fondo como segmented control real. Unificar las 3 definiciones de swatches. | 1 h | Medio |
| **V2** | Homogeneizar toolbar del visor: altura, bordes, espaciado comunes para todos los grupos de controles. | 1.5 h | Medio |
| **P4** | Diferenciar colores semánticos: separar "selección" de "acción primaria" y "estado correcto". | 2 h | Medio |
| **A1** | Reestructurar editor de ajustes: un solo encabezado, eliminar títulos duplicados. | 2 h | Medio |
| **A2** | Separar "gestión de ajustes" (presets guardados) de "edición operativa" (sliders). | 2 h | Medio |
| **A3** | Unificar grilla de slider+input numérico en un solo componente CSS. | 1 h | Medio |
| **R1+R2** | Normalizar breakpoints responsive y evitar pérdida total del inspector en pantallas medianas. | 2 h | Alto |

### Nivel 3 — Media prioridad (consistencia y microcopy)

| # | Problema | Esfuerzo | Riesgo |
|---|----------|----------|--------|
| **H2-H4** | Botones de cabecera con alturas/paddings inconsistentes entre capas CSS. | 1 h | Bajo |
| **G4-G5** | Definir y documentar la semántica del fondo de miniatura. Unificar clases `tone-*` vs `data-output-bg`. | 1 h | Bajo |
| **P2-P5** | Unificar padding, borde y radio de cards del inspector. | 1 h | Medio |
| **P3** | Eliminar badge "Activa" duplicado con checkbox en filas de salida. | 30 min | Bajo |
| **M1, D1** | Normalizar patrón de overlay para gestor de salidas y detalle de lote (mismo ancho, mismo comportamiento). | 1.5 h | Medio |
| **M2** | Clarificar acciones del footer del gestor de salidas (microcopy). | 30 min | Bajo |
| **E1-E2** | Limpiar estilos de empty state contradictorios. | 30 min | Bajo |
| **F1** | Unificar visibilidad de barra inferior (un solo mecanismo CSS). | 30 min | Bajo |

### Nivel 4 — Mejora progresiva (accesibilidad y edge cases)

| # | Problema | Esfuerzo | Riesgo |
|---|----------|----------|--------|
| **AC1** | Auditar y corregir gestión de foco en todos los modales. | 2 h | Medio |
| **AC2** | Añadir atributos ARIA a sliders (`aria-valuenow`, `aria-valuetext`). | 1 h | Bajo |
| **AC3** | Añadir `role="img"` y `aria-label` al canvas de preview. | 15 min | Bajo |
| **AC4** | Añadir `alt` text descriptivo a miniaturas (cambiar divs por imágenes o usar `aria-label`). | 1 h | Medio |
| **AC6** | Añadir `prefers-reduced-motion` a animaciones CSS. | 30 min | Bajo |
| **R3** | Añadir estilos básicos para viewports < 720px. | 2 h | Alto |

### Nivel 5 — Deuda técnica (CSS y arquitectura)

| # | Problema | Esfuerzo | Riesgo |
|---|----------|----------|--------|
| **CSS** | Consolidar tokens duplicados (145 nombres repetidos). Crear una sola fuente de verdad para variables CSS. | 4 h | Alto |
| **CSS** | Reducir `!important` de 337 a < 100. Empezar por componentes aislados. | 8 h | Muy alto |
| **CSS** | Fusionar `ux-refactor.css` en `ux-foundation.css` y `styles.css`, eliminando la tercera capa. | 6 h | Muy alto |
| **JS** | Extraer renderTop, renderBatch, renderPreview, renderSettings, renderInspector, renderAppSettings, renderFooter de app.js a módulos separados. | 8 h | Alto |
| **JS** | Agrupar estado por dominios (batch, preview, export, ui) con transiciones centralizadas. | 6 h | Alto |
| **HTML** | Mover panel de debug y revisión a un archivo separado o condicionar su inclusión solo en modo desarrollo. | 2 h | Bajo |

---

## 5. Plan de acción recomendado

### Fase A: Correcciones críticas (Nivel 1) — 30 minutos

1. Restaurar visibilidad del botón "Procesada" en el visor (`ux-refactor.css:95-97`).
2. Corregir el fondo de canvas para que `.bg-rgb230` y `.bg-white` se diferencien
   correctamente (`ux-refactor.css:183-189`).
3. Resolver la contradicción de tabs del inspector entre `ux-foundation.css` y
   `ux-refactor.css`.

### Fase B: Sistema visual (Nivel 2) — 12 horas

1. **Toolbar del visor:** Crear un componente `.viewer-toolbar` unificado con
   grupos de controles que compartan altura (36px), radio (8px) y borde.
2. **Selector de fondo:** Convertirlo en un segmented control real sin swatches
   circulares, con altura y estilo consistentes con el resto de la toolbar.
3. **Colores semánticos:** Asignar `--semantic-selection` (#2563eb o similar)
   para estados de selección, separándolo del verde de acción primaria.
4. **Galería:** Añadir encabezado "Lote" con jerarquía clara sobre el contador.
5. **Editor de ajustes:** Reestructurar HTML para tener un solo encabezado de
   edición, separar "Gestionar ajustes" como acción explícita (no como sección
   mezclada), unificar la grilla de slider+input.
6. **Responsive:** Unificar breakpoints en 3 valores (1280px, 1024px, 720px),
   mantener el inspector accesible de alguna forma en pantallas medianas (ej.
   colapsado pero expandible).

### Fase C: Consistencia y microcopy (Nivel 3) — 6 horas

1. Normalizar alturas de botones en cabecera (todos 36px excepto primario 40px).
2. Unificar padding de cards del inspector (todas 12px o todas 16px).
3. Eliminar badge "Activa" redundante.
4. Normalizar overlays de gestor y detalle (mismo ancho máximo, mismo
   comportamiento de footer).
5. Revisar microcopy global: unificar términos, eliminar inglés innecesario.

### Fase D: Accesibilidad (Nivel 4) — 6 horas

1. Auditar foco en modales (apertura, cierre, trampa de foco).
2. Añadir atributos ARIA a sliders.
3. Mejorar accesibilidad del canvas y miniaturas.
4. Añadir `prefers-reduced-motion`.

### Fase E: Deuda técnica CSS (Nivel 5) — 18+ horas

1. Crear una tabla de tokens canónicos (colores, texto, radios, sombras,
   espaciado).
2. Consolidar tokens duplicados: elegir una capa como fuente de verdad para cada
   token y eliminar redeclaraciones.
3. Reducir `!important` por componente, empezando por botones, badges y cards.
4. Evaluar fusión de `ux-refactor.css` en las otras capas.
5. Actualizar `docs/FLATSHOT_DESIGN_SYSTEM.md` con el estado final real.

---

## 6. Criterios de aceptación por fase

### Fase A
- El botón "Procesada" es visible y funcional.
- El canvas muestra fondos de revisión diferenciados (gris ≠ blanco ≠
  transparente).
- Los tabs del inspector se muestran u ocultan de forma predecible.

### Fase B
- La toolbar del visor parece un solo sistema (mismas alturas, radios, bordes).
- El selector de fondo es un segmented control limpio (sin círculos).
- El color de selección (galería, tabs) es distinto del verde de acción.
- La galería tiene un título "Lote" visible.
- El editor de ajustes tiene un solo encabezado principal.
- Los breakpoints son 3 valores documentados y consistentes.

### Fase C
- Los botones de la cabecera tienen altura uniforme.
- Las cards del inspector comparten padding.
- No hay badge "Activa" junto a checkboxes.
- Gestor y detalle usan el mismo patrón de overlay.
- Microcopy revisado y unificado.

### Fase D
- El foco se gestiona correctamente en todos los modales.
- Los sliders tienen atributos ARIA.
- El canvas y miniaturas tienen textos alternativos.
- Las animaciones respetan `prefers-reduced-motion`.

### Fase E
- Los tokens están consolidados en una fuente canónica.
- `!important` reducido significativamente (< 150).
- El design system documentado refleja la realidad del CSS.
- No hay regresiones visuales respecto al estado pre-consolidación.

---

## 7. Lo que NO debe tocarse

Siguiendo las reglas del proyecto (AGENTS.md, CODE_HEALTH_AUDIT.md):

1. **Motor de imagen** (`core/engine.py`, `core/scaling.py`, `core/shadow/*`):
   no modificar. Cualquier cambio aquí requiere pruebas golden de salida.
2. **Export runner** (`application/export_runner.py`): no modificar durante
   trabajo de UI.
3. **Bridge Python** (`bridge/service.py`, `bridge/http_server.py`): no
   modificar payloads ni endpoints.
4. **Configuración** (`settings_service.py`, `preset_service.py`): mantener
   compatibilidad hacia atrás.
5. **Formato de archivos de salida**: preservar dimensiones, DPI, formato,
   nombres, destinos.
6. **No añadir dependencias** sin justificación escrita.
7. **No reescribir la app** desde cero.

---

## 8. Métricas de éxito

Al finalizar todas las fases:

- CSS total: Reducción de ~13.800 líneas a ~10.000 (eliminando duplicación).
- `!important`: Reducción de 337 a < 150.
- Tokens duplicados: Reducción de 145 a < 20.
- La app se ve y se comporta igual que antes en los flujos principales.
- `pytest` completo pasa (282+ tests).
- `node --check` para todos los archivos JS pasa.
- No hay overflow horizontal en viewports de 1024px+.
- La interfaz es usable en viewports de 720px+ (con limitaciones documentadas).

---

*Informe generado el 2026-06-11 tras inspección completa de 13.819 líneas de CSS,
6.888 líneas de JS principal, 677 líneas de HTML, 23 módulos JS auxiliares y
documentación existente (AGENTS.md, CODE_HEALTH_AUDIT.md,
UX_UI_REFACTOR_PROGRESS.md, flatshot_informe_uxui_goal_refactor_v2.md,
FLATSHOT_DESIGN_SYSTEM.md, CSS_CASCADE_INVENTORY.md).*
