# Plan extensivo de rediseño UX/UI para FlatShot Desktop  
## Segunda iteración crítica: pasar de “interfaz funcional” a herramienta profesional de producción

**Contexto:** la última iteración ha mejorado algunos aspectos superficiales —más aire, paneles más limpios, estados compactos—, pero la pantalla sigue transmitiendo una sensación amateur. El problema principal ya no es sólo “estética”; es una combinación de arquitectura visual débil, jerarquía insuficiente, estados mal resueltos, componentes genéricos y falta de una dirección de producto clara.

Este documento plantea una intervención más profunda. No propone pequeños retoques, sino una reordenación completa del sistema visual y del comportamiento de la interfaz sin romper la funcionalidad existente.

---

## 1. Diagnóstico crítico del estado actual

### 1.1. La interfaz ha sido suavizada, no diseñada

La pantalla actual parece haber pasado de una UI densa a una UI “más limpia”, pero no a una UI profesional. Se han reducido elementos, se ha aclarado el fondo y se han creado zonas más amplias, pero falta una composición con intención.

Problemas visibles:

- El centro tiene un gran vacío gris sin valor visual ni funcional.
- Los laterales parecen formularios pegados al canvas.
- La topbar queda excesivamente vacía y sin tensión compositiva.
- El panel derecho muestra ajustes aunque no hay imagen ni lote, generando ruido contextual.
- Los controles parecen genéricos de navegador/web, no de herramienta de producción.
- El estado vacío ocupa toda la pantalla, pero comunica muy poco.
- Los estilos de botones, tabs, chips y tarjetas no terminan de pertenecer a un mismo sistema.
- El diseño no dirige la mirada: todo está visible, pero nada manda.

La conclusión es clara: el rediseño se ha quedado en una capa cosmética. FlatShot necesita una arquitectura de producto.

---

### 1.2. El estado “sin lote” está mal planteado

El estado actual muestra:

- panel izquierdo con importación;
- canvas central vacío;
- panel derecho con ajustes;
- barra inferior con textos sueltos;
- topbar con estados técnicos.

Esto es incoherente. Si no hay lote, la interfaz no debería comportarse como si ya estuviera en modo revisión. El usuario necesita una pantalla de entrada clara: seleccionar carpeta, entender qué va a ocurrir, ver requisitos mínimos y confirmar que el sistema está preparado.

El panel derecho, en este estado, no debería mostrar sliders de sombra como elemento principal. Puede mostrar una preparación de salida o un checklist, pero no ajustes finos de una imagen inexistente.

---

### 1.3. La jerarquía visual es plana

El diseño actual tiene muchos elementos con pesos parecidos:

- títulos pequeños;
- botones con presencia similar;
- chips de estado blandos;
- paneles blancos equivalentes;
- separadores muy sutiles;
- mucho texto en gris;
- controles flotando sin bloques claros.

Esto provoca que la interfaz parezca correcta a nivel de CSS, pero débil a nivel de producto.

Una herramienta profesional debe tener una jerarquía brutalmente clara:

1. **Acción principal**: cargar carpeta o exportar.
2. **Objeto de trabajo**: lote e imagen actual.
3. **Estado operativo**: listo, bloqueado, procesando, con avisos.
4. **Controles contextuales**: sólo los necesarios en cada momento.
5. **Información secundaria**: diagnósticos, ajustes avanzados, detalles técnicos.

Ahora mismo esa jerarquía no está resuelta.

---

### 1.4. El layout desaprovecha el espacio

El centro ocupa mucha superficie, pero no construye una escena visual potente. La imagen o su ausencia deberían dominar la experiencia. En cambio, el canvas gris funciona como un contenedor muerto.

El panel izquierdo usa bastante altura para importación incluso cuando no hay contenido real. El panel derecho muestra controles sin utilidad contextual. La barra inferior reparte mensajes en posiciones arbitrarias, lo que la hace parecer una maqueta.

FlatShot debería comportarse como una aplicación de producción visual, no como un formulario de administración con un hueco central.

---

### 1.5. Los componentes no parecen “de producto final”

Hay varios signos de UI inmadura:

- tabs demasiado simples y blandas;
- botones principales muy planos;
- sliders sin refinamiento;
- inputs con aspecto genérico;
- accordions poco trabajados;
- chips que parecen etiquetas de demo;
- demasiada dependencia de bordes;
- falta de microestados bien diseñados;
- iconografía casi ausente o sin criterio;
- texto demasiado pequeño en zonas críticas;
- alineaciones correctas pero sin carácter.

El objetivo no debe ser “hacerlo bonito”, sino crear una interfaz con confianza visual: densa cuando toca, ligera cuando toca, y con patrones reconocibles.

---

## 2. Dirección de producto propuesta

### 2.1. Principio central

FlatShot no debe parecer un dashboard. Debe parecer una **herramienta de producción de imagen por lotes**.

La interfaz debe estar construida alrededor de esta secuencia:

```text
Seleccionar lote → Revisar imagen → Ajustar procesamiento → Validar salida → Exportar
```

Todo lo que no ayude a esa secuencia debe ocultarse, plegarse, reducirse o moverse a una capa secundaria.

---

### 2.2. Modelo mental recomendado

La app debe tener tres zonas conceptuales:

```text
1. Navegador de lote
   Dónde están las imágenes, cuántas hay, cuáles tienen avisos y cuál estoy revisando.

2. Mesa de revisión
   Imagen seleccionada, preview, fondo de visualización, zoom y navegación.

3. Inspector contextual
   Ajustes de procesamiento y salida aplicables al lote o a la imagen.
```

La topbar y la statusbar no son zonas de contenido; son zonas de control y estado.

---

### 2.3. Estados principales de la aplicación

La interfaz debe cambiar de comportamiento según el estado. No puede verse casi igual con y sin lote.

#### Estado A — Sin lote

Objetivo del usuario: empezar.

- Topbar: app + estado `Sin lote` + bridge.
- Izquierda: selección de carpeta.
- Centro: onboarding visual claro.
- Derecha: checklist de preparación o salida desactivada, no sliders.
- CTA principal: `Seleccionar carpeta`.

#### Estado B — Escaneando

Objetivo del usuario: entender qué está pasando.

- Centro: progreso grande.
- Izquierda: carpeta seleccionada + progreso.
- Derecha: bloqueada o mostrando preflight preliminar.
- Statusbar: actividad real.

#### Estado C — Lote cargado, sin imagen seleccionada

Objetivo del usuario: elegir una imagen o revisar resumen.

- Izquierda: lote, filtros, miniaturas.
- Centro: estado vacío contextual: “Selecciona una imagen para revisarla”.
- Derecha: salida/preflight del lote, no ajustes de imagen.

#### Estado D — Imagen seleccionada

Objetivo del usuario: revisar y ajustar.

- Izquierda: miniaturas y filtros.
- Centro: imagen dominante.
- Derecha: ajustes o salida.
- CTA: exportar si todo está listo.

#### Estado E — Exportación lista

Objetivo del usuario: confirmar y exportar.

- Derecha: salida y preflight.
- Topbar: `Exportar X` activo.
- Statusbar: destino y estado.

#### Estado F — Bloqueado / con errores

Objetivo del usuario: resolver.

- Topbar: estado bloqueante claro.
- Izquierda: filtros por error/avisos.
- Derecha: lista accionable de bloqueos.
- Exportar desactivado con explicación.

---

## 3. Dirección visual: “pro light studio”

### 3.1. Qué evitar

No seguir reforzando una estética de:

- dashboard SaaS genérico;
- formulario administrativo;
- app web de demo;
- interfaz con mucho blanco sin jerarquía;
- diseño plano con chips de colores pastel;
- paneles que parecen cajas de Bootstrap.

Tampoco conviene pasar a una UI totalmente oscura. El trabajo con producto, fondos y exportación RGB requiere neutralidad, lectura clara y control visual. Una UI oscura puede contaminar la percepción del producto y parecer más dramática de lo necesario.

---

### 3.2. Estética objetivo

Una dirección más adecuada:

- fondo general claro, técnico, ligeramente cálido;
- canvas central neutro, con presencia de “mesa de trabajo”;
- paneles laterales blancos o casi blancos, pero no como tarjetas sueltas;
- bordes finos, pocos y bien usados;
- sombras mínimas;
- tipografía compacta y precisa;
- acento verde/teal sólo para acciones, selección y estado positivo;
- avisos y errores muy controlados;
- alta legibilidad en nombres de archivo, contadores y estados.

Referencia conceptual: una mezcla entre herramienta de captura/revisión fotográfica, app desktop de producción y panel de exportación profesional. No una landing, no un CRM, no un dashboard financiero.

---

### 3.3. Paleta recomendada

Propuesta base:

```css
:root {
  --bg-app: #F3F5F4;
  --bg-rail: #F8FAF9;
  --bg-panel: #FFFFFF;
  --bg-panel-muted: #F6F8F7;
  --bg-canvas: #E6E9E8;
  --bg-canvas-stage: #F4F5F3;

  --line-soft: #E2E8E5;
  --line: #D4DDD9;
  --line-strong: #B9C7C1;

  --text-strong: #111A17;
  --text: #26332F;
  --text-muted: #65736E;
  --text-subtle: #8A9692;

  --accent: #087D69;
  --accent-strong: #056856;
  --accent-soft: #DDF4EE;
  --accent-muted: #EFFAF7;

  --warning: #A86600;
  --warning-soft: #FFF4DA;
  --warning-line: #F3D28A;

  --danger: #B42318;
  --danger-soft: #FEE4E2;
  --danger-line: #FDA29B;

  --disabled-bg: #F2F4F3;
  --disabled-text: #A2ADA9;

  --shadow-xs: 0 1px 1px rgba(16, 24, 40, .04);
  --shadow-sm: 0 1px 3px rgba(16, 24, 40, .08);
  --shadow-md: 0 12px 32px rgba(16, 24, 40, .12);

  --radius-6: 6px;
  --radius-8: 8px;
  --radius-10: 10px;
  --radius-12: 12px;
  --radius-16: 16px;

  --focus: 0 0 0 3px rgba(8, 125, 105, .18);
}
```

Reglas:

- El verde no debe invadir toda la UI.
- El rojo sólo para bloqueo/error real.
- Los fondos pastel deben ser excepcionales.
- El canvas debe distinguirse del panel, no confundirse con un simple fondo gris.
- Los estados desactivados deben verse desactivados, no sólo en gris débil.

---

### 3.4. Tipografía

Usar una escala cerrada:

```css
--font-family-ui: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;

--fs-10: 10px;
--fs-11: 11px;
--fs-12: 12px;
--fs-13: 13px;
--fs-14: 14px;
--fs-16: 16px;
--fs-18: 18px;
--fs-22: 22px;

--lh-tight: 1.15;
--lh: 1.35;
--lh-loose: 1.55;
```

Uso recomendado:

- App name: 14/15 px, semibold.
- Contadores principales: 18/22 px, semibold.
- Nombre de archivo: 15/16 px, semibold.
- Labels: 11/12 px, medium, no todo en mayúsculas salvo tokens muy técnicos.
- Texto secundario: 12/13 px.
- Valores de tabla/preflight: 12/13 px, medium.
- Statusbar: 11/12 px.

Evitar:

- demasiadas mayúsculas;
- títulos pequeños en mayúsculas;
- subtítulos explicativos permanentes;
- números con tamaño descompensado;
- pesos de fuente aleatorios.

---

### 3.5. Espaciado

Sistema de 4 px:

```css
--s-2: 2px;
--s-4: 4px;
--s-6: 6px;
--s-8: 8px;
--s-10: 10px;
--s-12: 12px;
--s-16: 16px;
--s-20: 20px;
--s-24: 24px;
--s-32: 32px;
```

Reglas:

- Paneles laterales: padding 16 px.
- Bloques internos: gap 12/16 px.
- Controles en fila: gap 8 px.
- Separadores entre secciones: margen vertical 16/20 px.
- No usar padding arbitrario por componente.
- No abrir grandes vacíos salvo en canvas/onboarding.

---

## 4. Arquitectura de layout objetivo

### 4.1. Shell general

Estructura recomendada:

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ Topbar / Command bar                                                       │ 56 px
├───────────────┬─────────────────────────────────────┬──────────────────────┤
│ Batch rail    │ Review workspace                    │ Context inspector    │
│ 300–340 px    │ flexible                            │ 340–400 px           │
├───────────────┴─────────────────────────────────────┴──────────────────────┤
│ Status bar                                                                 │ 30–34 px
└────────────────────────────────────────────────────────────────────────────┘
```

CSS aproximado:

```css
.app-shell {
  height: 100dvh;
  display: grid;
  grid-template-rows: 56px minmax(0, 1fr) 32px;
  background: var(--bg-app);
  color: var(--text);
  overflow: hidden;
}

.app-workspace {
  min-height: 0;
  display: grid;
  grid-template-columns:
    clamp(300px, 18vw, 340px)
    minmax(680px, 1fr)
    clamp(340px, 21vw, 400px);
  border-top: 1px solid var(--line-soft);
}
```

---

### 4.2. Reglas de scroll

- Nunca scroll global.
- Sólo scroll interno en:
  - lista de miniaturas;
  - panel derecho si hay demasiados controles;
  - diagnósticos/errores si la lista crece.
- El header de cada panel debe permanecer visible.
- La statusbar siempre visible.
- El canvas no debe generar scroll.

---

### 4.3. Densidad

FlatShot es una herramienta productiva; no puede tener una densidad excesivamente baja. La última pantalla tiene demasiado aire muerto. El objetivo no es hacerla más vacía, sino más clara.

Densidad recomendada:

- Topbar compacta.
- Panel izquierdo denso pero ordenado.
- Canvas amplio.
- Panel derecho denso en información, pero con revelación progresiva.
- Estados vacíos más visuales, no simplemente texto pequeño centrado.

---

## 5. Rediseño por zonas

---

# 5.1. Topbar / Command bar

## Problema actual

La topbar tiene:

- mucho espacio vacío;
- estados poco jerarquizados;
- acciones a la derecha sin suficiente estructura;
- chips que parecen añadidos;
- poca relación entre estado global y acción principal.

En estado sin lote, mostrar `Bloqueado`, `Seleccionar carpeta`, `Inspección` en el extremo derecho funciona, pero parece una barra de prototipo. El usuario no entiende qué está bloqueado ni qué debe hacer primero salvo por el botón verde.

---

## Objetivo

La topbar debe responder a cuatro preguntas:

1. ¿Qué aplicación estoy usando?
2. ¿Qué lote está activo?
3. ¿Está preparado el sistema?
4. ¿Cuál es la acción principal ahora?

---

## Estructura propuesta

```text
[Logo] FlatShot
       Sin lote / 44 imágenes · 1 omitida

                       [Bridge pendiente] [Preview real] [Avisos]

[Acción principal] [Acción secundaria]
```

Más formal:

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ F  FlatShot       Sin lote                     Bridge pendiente          │
│                                           [Seleccionar carpeta] [Inspec.]│
└──────────────────────────────────────────────────────────────────────────┘
```

Cuando hay lote:

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ F  FlatShot       44 imágenes · 1 omitida       Bridge conectado · Listo │
│                                                 [Exportar 44] [Inspec.] │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Cambios concretos

### 5.1.1. Identidad

- Mantener logo `F`, pero reducir protagonismo si compite con contenido.
- Nombre `FlatShot` en semibold.
- Segunda línea compacta: `Sin lote`, `44 imágenes`, `44 imágenes · 1 omitida`.

### 5.1.2. Estado global

Agrupar estado en una sola zona:

- `Bridge pendiente`
- `Bridge conectado`
- `Preview real`
- `Mock`
- `Con avisos`
- `Bloqueado`

No repetir estado en topbar, panel derecho y statusbar con la misma forma.

### 5.1.3. Acciones

Estados:

- Sin lote: CTA = `Seleccionar carpeta`.
- Lote cargado: CTA = `Exportar 44`.
- Exportación bloqueada: CTA desactivado = `Exportar`, con tooltip/mensaje.
- Con avisos: CTA activo o semiactivo según reglas, con badge `2 avisos`.

`Inspección` debe ser secundaria. Puede ser botón ghost o icon button con texto.

### 5.1.4. Estilo

- Altura: 56 px.
- Fondo: `--bg-panel`.
- Borde inferior: `1px solid --line-soft`.
- No usar sombras salvo que el workspace pueda pasar por debajo.
- Botón principal más sólido, sin parecer excesivo.
- Chips de estado muy compactos.

---

# 5.2. Panel izquierdo / Navegador de lote

## Problema actual

El panel izquierdo mezcla:

- selección de carpeta;
- resumen;
- búsqueda;
- filtros;
- estado vacío;
- acciones de escaneo;
- ruta manual.

En estado sin lote tiene sentido mostrar importación, pero el layout parece un formulario pobre. En estado con lote, la selección de carpeta no debe seguir ocupando el mismo protagonismo.

---

## Objetivo

El panel izquierdo debe ser un navegador de lote. Su prioridad cambia:

- sin lote: importar;
- con lote: navegar;
- con problemas: filtrar/resolver.

---

## Estados del panel izquierdo

### Sin lote

Debe mostrar una tarjeta de inicio más cuidada:

```text
Lote
0 imágenes

Selecciona una carpeta
PNG/JPG compatibles · procesamiento local

[Seleccionar carpeta] [Escanear]
▸ Ruta manual

Requisitos
✓ Carpeta local
✓ Imágenes PNG/JPG
✓ Salida configurable después
```

Mejor que el estado vacío actual, porque comunica utilidad sin saturar.

---

### Con lote cargado

La importación se reduce:

```text
Lote
44 imágenes        1 omitida

/carpeta/origen
[Cambiar] [Reescanear]

Archivos   45
Válidas    44
Omitidas    1
```

Después:

```text
Buscar
[Nombre de imagen...]

Filtros
[Todas 44] [Válidas 44] [Avisos 1] [Errores 0]

PNG
44 imágenes
[miniaturas...]
```

---

## Componentes concretos

### 5.2.1. Batch header

Debe incluir:

- título `Lote`;
- contador grande;
- estado compacto;
- ruta si hay lote, truncada;
- acciones secundarias.

No mezclar contadores principales con texto de ayuda largo.

---

### 5.2.2. Source card

En estado sin lote, la source card es principal.

En estado con lote, se convierte en fila compacta:

```text
Origen
/.../imagenes-producto
[Cambiar] [Reescanear]
```

---

### 5.2.3. Resumen de lote

Diseño:

```text
┌────────────────────────────┐
│ Archivos   Válidas   Omit. │
│   45        44        1    │
└────────────────────────────┘
```

Reglas:

- números con tabular numerals;
- etiquetas pequeñas;
- no usar tres bloques excesivamente grandes;
- avisos/errores destacados sólo si existen.

---

### 5.2.4. Búsqueda

- Input con icono de lupa si existe sistema de iconos.
- Placeholder: `Buscar archivo`.
- Altura 34/36 px.
- Clear button cuando haya texto.
- Si no hay resultados, mostrar estado compacto dentro de lista, no pantalla entera.

---

### 5.2.5. Filtros

Segmented control real:

```text
[Todas 44] [Válidas 44] [Avisos 1] [Errores 0]
```

Reglas:

- No usar anchuras aleatorias.
- Estado activo claramente visible.
- Estados con cero pueden mostrarse atenuados.
- Avisos/errores deben poder destacar si > 0.

---

### 5.2.6. Lista/grid de miniaturas

La miniatura actual parece un bloque genérico. Debe funcionar como elemento de revisión.

Opciones de layout:

#### Opción A — Grid compacto

```text
┌────────┐ ┌────────┐ ┌────────┐
│ img    │ │ img    │ │ img    │
│ S670.. │ │ S670.. │ │ S670.. │
└────────┘ └────────┘ └────────┘
```

Adecuada si se quiere máxima visualidad.

#### Opción B — Lista densa con thumbnail

```text
[thumb] S670743599111.png
        Lista · PNG · 1800×2400
```

Más profesional si se necesita información operativa.

#### Recomendación

Implementar modo único más profesional: **grid/list híbrido vertical** con miniatura más pequeña e información a la derecha o debajo según ancho. En un panel de 320 px, una lista con thumbnail de 44–56 px suele ser más legible que grid de tarjetas pequeñas.

Ejemplo recomendado:

```text
┌──────────────────────────────┐
│ ▧  S670743599111.png    Lista│
│    PNG · 1800×2400           │
└──────────────────────────────┘
```

Ventajas:

- nombres más legibles;
- estado claro;
- menos aspecto de pegatinas;
- mejor para 44+ imágenes;
- menos scroll inútil;
- más profesional.

Si se mantiene grid, aumentar intención visual: selección con fondo suave, no borde grueso; nombre alineado; estado integrado.

---

### 5.2.7. Selección

Evitar bordes verdes gruesos. Usar:

- fondo `--accent-muted`;
- borde izquierdo fino o outline sutil;
- check/indicador de selección;
- texto en semibold.

Ejemplo:

```css
.thumbnail-item.is-selected {
  background: var(--accent-muted);
  border-color: var(--accent-border);
  box-shadow: inset 3px 0 0 var(--accent);
}
```

---

# 5.3. Workspace central / Mesa de revisión

## Problema actual

El workspace central muestra un enorme rectángulo gris con un texto pequeño. No parece una herramienta de imagen, sino un hueco sin contenido.

Cuando haya imagen, la zona debe convertirse en la parte más cuidada de la aplicación. Cuando no haya imagen, debe tener un estado vacío diseñado.

---

## Objetivo

Crear una “mesa de revisión” con:

- header compacto de imagen;
- canvas dominante;
- stage interno;
- controles de vista agrupados;
- estado vacío útil;
- fondo neutro;
- sin ruido.

---

## Estructura propuesta

```text
┌──────────────────────────────────────────────┐
│ Header imagen: archivo · estado · navegación │
├──────────────────────────────────────────────┤
│                                              │
│                  Canvas                      │
│          ┌─────────────────────┐             │
│          │       Imagen        │             │
│          └─────────────────────┘             │
│                                              │
├──────────────────────────────────────────────┤
│ Fondo: [RGB230] [Blanco] [Transp.]  Preview  │
└──────────────────────────────────────────────┘
```

---

## 5.3.1. Header de imagen

### Sin imagen

No mostrar demasiados controles desactivados. El header actual muestra `Procesada`, flechas, zoom y `Fit` desactivados, lo que genera ruido.

Estado recomendado:

```text
Imagen
Sin selección
```

Y ocultar o desactivar de forma más sutil la toolbar.

### Con imagen

```text
S670743599111.png
Preview real · Procesada

[←] 5 / 44 [→]   [Fit] [100%] [-] [+]
```

Reglas:

- nombre de archivo visible y truncado correctamente;
- estado debajo o como chip pequeño;
- navegación agrupada;
- zoom agrupado;
- no repetir `Fit` dos veces;
- controles desactivados no deben parecer rotos.

---

## 5.3.2. Canvas

### Sin lote

Estado central de onboarding:

```text
┌────────────────────────────────────┐
│ Icono/carpeta                      │
│ Empieza seleccionando una carpeta  │
│ Elige una carpeta local con PNG... │
│ [Seleccionar carpeta]              │
│ Formatos compatibles: PNG, JPG     │
└────────────────────────────────────┘
```

Este card debe estar centrado, pero no ser minúsculo. Puede tener 420–520 px de ancho.

### Lote cargado sin imagen

```text
Selecciona una imagen
Elige una miniatura del lote para revisar el preview.
```

### Imagen cargada

El canvas debe tener una sensación de “stage”:

```css
.review-canvas {
  background:
    radial-gradient(circle at center, rgba(255,255,255,.55), rgba(255,255,255,0) 45%),
    var(--bg-canvas);
}

.image-stage {
  background: var(--bg-canvas-stage);
  border: 1px solid rgba(255,255,255,.55);
  box-shadow: 0 24px 60px rgba(16, 24, 40, .08);
}
```

No siempre hace falta una tarjeta visible alrededor de la imagen, pero sí debe haber una composición más intencional que un gris plano.

---

## 5.3.3. Imagen

Requisitos:

- `object-fit: contain`;
- límites máximos claros;
- nunca cortar en modo `Fit`;
- centrada en ambas direcciones;
- transición suave al cambiar de imagen, si no afecta rendimiento;
- mantener relación con fondo activo.

---

## 5.3.4. Controles inferiores del visor

Los controles de fondo actuales parecen tabs sueltas.

Rediseño:

```text
Vista de fondo  [RGB230] [Blanco] [Transparente]      Preview real · Preset Luz cenital
```

Reglas:

- no ocupar demasiada altura;
- activo claro;
- los desactivados con baja opacidad;
- `Sin imagen` no debe repetirse si ya está en el centro;
- separar fondo de visualización de fondo de exportación si son conceptos distintos.

---

# 5.4. Panel derecho / Inspector contextual

## Problema actual

El panel derecho muestra ajustes aunque no haya imagen. Además, los sliders parecen un formulario técnico. La pestaña `Salida` no parece suficientemente importante para una app cuyo objetivo final es exportar.

---

## Objetivo

El panel derecho debe ser un inspector contextual que cambia según estado:

- sin lote: preparación;
- lote cargado: salida/preflight o ajustes globales;
- imagen seleccionada: ajustes de preview/procesamiento;
- exportación bloqueada: resolución de problemas.

---

## 5.4.1. Tabs

Las tabs actuales son demasiado blandas. Deben ser estables, limpias y obvias.

Diseño:

```text
┌──────────────────────────────┐
│ [Ajustes] [Salida]           │
└──────────────────────────────┘
```

Reglas:

- altura 36/38 px;
- activo con fondo blanco o accent-soft;
- inactivo sin exceso de contraste;
- ancho completo;
- no saltos de layout;
- pueden incluir badges: `Salida · 2 avisos`.

---

## 5.4.2. Estado sin lote

No mostrar sliders como contenido principal. Propuesta:

```text
Preparación
Selecciona una carpeta para configurar el lote.

Checklist
○ Carpeta seleccionada
○ Imágenes válidas
○ Destino de salida
○ Bridge conectado

Ajustes predeterminados
Preset: Luz cenital
Formato: JPG
Fondo: RGB230
```

Acciones:

- `Seleccionar carpeta`;
- `Configurar salida` si tiene sentido.

Esto hace que el panel derecho sea útil sin mentir sobre el estado.

---

## 5.4.3. Ajustes con imagen seleccionada

Estructura:

```text
Preset
Luz cenital                         Sin cambios
Bridge local

[ Luz cenital ] [ Estándar oscuro ] [ Complementos ]
[ Sin sombra ]

Ajustes principales
Opacidad      ━━━━━●━━━━ 20
Blur          ━━━━━━━●━━ 30
Distancia     ━━━━━●━━━━ 25
Padding       ━━━━━●━━━━ 10

▸ Avanzado
```

Mejoras:

- el valor numérico debe estar alineado;
- los sliders deben tener anchura consistente;
- el label no debe competir con el valor;
- agrupar sliders en un bloque sin demasiadas cajas;
- `Reset` debe estar en la cabecera del bloque o como acción secundaria contextual, no flotando.

---

## 5.4.4. Ajustes avanzados

Cuando se abre:

```text
Avanzado
Spread        [0]
Ruido         [2]
Contacto      [10]
Escala        [0]
Fusión        [1]
Ángulo        [180]
Contracción   [0]
☑ Zoom auto
Motor         [Realista V2]
```

Reglas:

- grid de dos columnas para inputs numéricos;
- labels encima o a la izquierda, pero con patrón único;
- motor al final;
- si un valor avanzado ha sido modificado, indicarlo en el summary: `Avanzado · 2 cambios`;
- si no hay cambios, plegado por defecto.

---

## 5.4.5. Salida

La salida debe ser más fuerte. Ahora parece un formulario más.

Estructura recomendada:

```text
Salida
Lista para exportar                  44 archivos

Configuración
Formato        JPG
Tamaño         1800×2400
Fondo          RGB230
Destino        Origen / _SALIDA_PRO
Naming         {original}{suffix}

Preflight
✓ 44 imágenes válidas
⚠ 1 omitida
✓ Sin colisiones detectadas
✓ Destino disponible

[Exportar 44]
```

Si está bloqueada:

```text
Salida bloqueada
Falta seleccionar una carpeta.

Para exportar:
1. Selecciona una carpeta con imágenes.
2. Confirma destino.
3. Revisa avisos.

[Seleccionar carpeta]
```

Reglas:

- no mostrar una tabla plana sin jerarquía;
- preflight debe ser accionable;
- el CTA puede repetirse aquí si ayuda, pero el principal sigue arriba;
- destinos largos deben truncarse con tooltip/copiable;
- naming debe mostrar ejemplo: `S670743599111.jpg`.

---

# 5.5. Barra inferior / Statusbar

## Problema actual

La barra inferior actual reparte textos: `Sin lote`, `Sin imagen`, `Configura salida`, `Sin destino`, `Añade una carpeta`. Esto parece una maqueta técnica, no una statusbar profesional.

---

## Objetivo

La statusbar debe mostrar estado operativo compacto:

```text
Sin lote · Bridge pendiente · Selecciona una carpeta para empezar
```

Con lote:

```text
44 imágenes · Imagen 5/44 · Preview real · Salida lista
```

Durante exportación:

```text
Exportando 12/44 · S670743599111.jpg · 28%
```

Con error:

```text
Exportación bloqueada · Falta destino de salida
```

---

## Reglas

- Una línea coherente, no columnas sin relación.
- Iconos pequeños opcionales.
- No repetir todos los estados de topbar; sólo una síntesis operativa.
- Altura 30–34 px.
- Debe poder mostrar progreso.
- Debe poder mostrar último evento.
- Texto truncado correctamente.

---

## 6. Estados vacíos y de error

Los estados vacíos son uno de los motivos principales por los que la app parece amateur. No pueden ser simples frases pequeñas en un espacio gris.

---

### 6.1. Sin lote

```text
Empieza con una carpeta de imágenes
Selecciona una carpeta local con PNG o JPG para generar el lote de revisión.

[Seleccionar carpeta]

También puedes escanear de nuevo una ruta usada recientemente.
```

Visual:

- card centrada;
- icono simple;
- anchura 460–520 px;
- no excesivo;
- CTA claro.

---

### 6.2. Carpeta vacía

```text
No se encontraron imágenes compatibles
La carpeta seleccionada no contiene PNG o JPG procesables.

[Cambiar carpeta] [Ver diagnóstico]
```

---

### 6.3. Lote con omitidas

```text
44 imágenes listas · 1 omitida
Hay archivos que no se procesarán.

[Ver omitidas]
```

Debe aparecer en:

- panel izquierdo como aviso compacto;
- panel derecho/preflight;
- quizá topbar si afecta a exportación.

---

### 6.4. Bridge pendiente/desconectado

```text
Bridge pendiente
La app puede cargar el lote, pero el preview real no está disponible.

[Comprobar bridge] [Usar mock]
```

No esconderlo como chip minúsculo si afecta al uso.

---

### 6.5. Exportación bloqueada

```text
No se puede exportar todavía
Falta seleccionar una carpeta de origen.

[Seleccionar carpeta]
```

Debe explicar causa, no sólo mostrar `Bloqueado`.

---

### 6.6. Búsqueda sin resultados

Dentro del panel izquierdo:

```text
Sin resultados
No hay imágenes que coincidan con “abc”.
[Limpiar búsqueda]
```

---

## 7. Componentes a consolidar

Para dejar de hacer retoques, hay que crear o normalizar componentes.

### 7.1. `Button`

Variantes:

- primary;
- secondary;
- ghost;
- danger;
- icon;
- compact.

Estados:

- default;
- hover;
- active;
- focus;
- disabled;
- loading.

Alturas:

- default: 36 px;
- compact: 30/32 px;
- icon: cuadrado.

---

### 7.2. `Badge` / `StatusPill`

Tipos:

- neutral;
- success;
- warning;
- danger;
- info;
- disabled.

Reglas:

- no usar badges para todo;
- sólo estado o metadato relevante;
- no mezclar estilo de badge con botón.

---

### 7.3. `SegmentedControl`

Usos:

- tabs pequeñas;
- filtros;
- fondos de vista;
- presets si son pocos.

Debe tener:

- activo claro;
- hover;
- focus;
- disabled;
- conteos opcionales.

---

### 7.4. `PanelSection`

Estructura:

```text
Título                              Acción opcional
Contenido
```

Reglas:

- separación clara;
- no borde alrededor de cada sección salvo necesidad;
- no usar cards anidadas sin motivo.

---

### 7.5. `SliderRow`

Debe resolver:

- label;
- slider;
- valor;
- unidad opcional;
- reset por parámetro si procede;
- disabled.

Ejemplo:

```text
Opacidad        ━━━━━●━━━━        20
```

---

### 7.6. `ThumbnailItem`

Debe resolver:

- imagen;
- nombre;
- estado;
- selección;
- aviso/error;
- foco teclado;
- tooltip;
- menú contextual si existe.

---

### 7.7. `EmptyState`

Variantes:

- primary onboarding;
- inline empty;
- error;
- warning;
- search empty.

No crear estados vacíos diferentes a mano en cada pantalla.

---

### 7.8. `PreflightList`

Debe mostrar requisitos:

- ok;
- warning;
- error;
- pendiente.

Cada ítem debe poder tener acción:

- `Ver`;
- `Corregir`;
- `Configurar`;
- `Ignorar` si procede.

---

## 8. Replanteamiento de la pantalla según estados

---

### 8.1. Estado sin lote — propuesta completa

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ F FlatShot   Sin lote                         Bridge pendiente             │
│                                              [Seleccionar carpeta] [Inspec.]│
├───────────────┬─────────────────────────────────────┬──────────────────────┤
│ Lote          │                                     │ Preparación          │
│ 0 imágenes    │                                     │                      │
│               │       Empieza con una carpeta       │ ○ Carpeta            │
│ Selecciona... │       de imágenes                   │ ○ Imágenes válidas   │
│ [Seleccionar] │       [Seleccionar carpeta]         │ ○ Destino            │
│ [Escanear]    │                                     │ ○ Bridge             │
│ Ruta manual   │                                     │                      │
│               │                                     │ Valores por defecto  │
│ Archivos 0... │                                     │ JPG · RGB230         │
├───────────────┴─────────────────────────────────────┴──────────────────────┤
│ Sin lote · Bridge pendiente · Selecciona una carpeta para empezar           │
└────────────────────────────────────────────────────────────────────────────┘
```

Diferencia frente al estado actual:

- el centro tiene un onboarding real;
- el panel derecho no muestra sliders inútiles;
- la topbar no parece bloqueada sin explicación;
- la barra inferior cuenta una frase operativa.

---

### 8.2. Estado lote cargado

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ F FlatShot   44 imágenes · 1 omitida              Bridge conectado · Listo  │
│                                                       [Exportar 44] [Inspec.]│
├───────────────┬─────────────────────────────────────┬──────────────────────┤
│ Lote          │ S670743599111.png        5 / 44      │ Ajustes              │
│ 44 imágenes   │ Preview real · Procesada [←][→]      │ Salida               │
│ 1 omitida     ├─────────────────────────────────────┤                      │
│ Buscar        │                                     │ Preset               │
│ Filtros       │              Imagen                 │ Luz cenital          │
│ Lista         │                                     │                      │
│               │                                     │ Ajustes principales  │
│               │                                     │ Sliders              │
├───────────────┴─────────────────────────────────────┴──────────────────────┤
│ 44 imágenes · Imagen 5/44 · Preview real · Salida lista                     │
└────────────────────────────────────────────────────────────────────────────┘
```

---

### 8.3. Estado salida con avisos

```text
Panel derecho:

Salida con avisos                  44 archivos

Configuración
JPG · 1800×2400 · RGB230
Origen / _SALIDA_PRO

Preflight
✓ 44 imágenes listas
⚠ 1 archivo omitido
✓ Destino disponible
✓ Sin colisiones

[Exportar 44] [Ver omitidas]
```

---

### 8.4. Estado exportando

```text
Topbar:
Exportando 12/44                          [Cancelar]

Centro:
Imagen actual o progreso discreto

Derecha:
Progreso de exportación
12 de 44
Archivo actual
Tiempo estimado si existe

Statusbar:
Exportando 12/44 · S670...jpg
```

---

## 9. Revisión de copy

### 9.1. Reglas

- Menos texto permanente.
- Más texto contextual.
- Nada de explicaciones obvias.
- No usar tono de tutorial si el usuario ya está en flujo productivo.
- Evitar `Sin preview` repetido en tres zonas.
- Evitar `Bloqueado` sin causa.
- Usar verbos concretos.

---

### 9.2. Cambios recomendados

| Actual | Problema | Propuesta |
|---|---|---|
| `Añade una carpeta` | Suena informal y ambiguo | `Selecciona una carpeta` |
| `Bridge pendiente` | Correcto, pero necesita contexto si bloquea | `Bridge pendiente` + detalle sólo en panel |
| `Bloqueado` | No dice qué está bloqueado | `Exportación bloqueada` |
| `Sin imagen seleccionada` | Repetido | Usar sólo en header o empty state |
| `El lote aparecerá aquí` | Débil | `Selecciona una carpeta para generar el lote` |
| `Procesada` desactivado | No útil sin imagen | Ocultar hasta que haya imagen |
| `Configura salida` | Correcto pero vago | `Salida sin configurar` |
| `Sin destino` | Correcto en statusbar si hay lote | Añadir causa/acción en panel |

---

## 10. Interacciones y microdetalles

### 10.1. Hover

- Miniatura: fondo leve + mostrar acción secundaria si existe.
- Botón: cambio de fondo/borde, no salto de tamaño.
- Panel item: cursor sólo si es clicable.
- Sliders: thumb más visible al hover.
- Tabs: hover sutil.

---

### 10.2. Focus

Imprescindible:

```css
:focus-visible {
  outline: none;
  box-shadow: var(--focus);
}
```

Pero aplicado bien para:

- botones;
- inputs;
- tabs;
- miniaturas;
- sliders;
- accordions.

---

### 10.3. Transiciones

Usar sólo:

```css
transition:
  background-color 140ms ease,
  border-color 140ms ease,
  color 140ms ease,
  box-shadow 140ms ease,
  transform 120ms ease;
```

Evitar:

- animaciones grandes;
- fade excesivo al cambiar imagen;
- movimiento en paneles críticos;
- layout shifts.

---

### 10.4. Desactivados

Un control desactivado no debe parecer un error.

Reglas:

- opacidad controlada;
- cursor default/not-allowed según patrón;
- tooltip o explicación sólo en acciones principales desactivadas;
- ocultar controles irrelevantes en lugar de desactivar todo.

---

## 11. Plan de implementación faseado

---

### Fase 0 — Congelar diagnóstico y crear baseline

Objetivo: no seguir dando vueltas sin medir.

Tareas:

1. Crear capturas del estado actual:
   - sin lote;
   - lote cargado;
   - imagen seleccionada;
   - ajustes;
   - salida;
   - con avisos;
   - error/bridge pendiente si puede reproducirse.
2. Listar archivos UI/CSS/JS principales.
3. Documentar el árbol de componentes/render actual.
4. Identificar estilos duplicados.
5. Identificar estados globales usados por la UI.

Criterio de aceptación:

- existe una lista clara de archivos a modificar;
- se entiende cómo se calcula cada estado visible;
- no se toca todavía la funcionalidad.

---

### Fase 1 — Crear sistema visual base

Objetivo: dejar de diseñar con clases sueltas.

Tareas:

1. Crear/normalizar tokens CSS.
2. Definir escala tipográfica.
3. Definir escala de spacing.
4. Definir estilos base:
   - botones;
   - inputs;
   - selects;
   - sliders;
   - badges;
   - segmented controls;
   - panels;
   - empty states.
5. Eliminar estilos duplicados o contradictorios.
6. Comprobar que la app sigue igual funcionalmente.

Criterio de aceptación:

- ningún botón principal tiene estilo improvisado;
- inputs/selects tienen la misma altura;
- tabs/filtros/fondos comparten patrón;
- los estados hover/focus existen.

---

### Fase 2 — Refactor del shell

Objetivo: resolver layout antes de rediseñar piezas.

Tareas:

1. Asegurar `100dvh`.
2. Grid de 3 filas:
   - topbar;
   - workspace;
   - statusbar.
3. Grid de 3 columnas:
   - izquierda;
   - centro;
   - derecha.
4. Bloquear scroll global.
5. Definir scroll interno.
6. Revisar anchos mínimos/máximos.
7. Probar 1366×768 y 1920×1080.

Criterio de aceptación:

- no hay scroll global;
- el canvas no colapsa;
- los paneles no se pisan;
- la statusbar siempre se ve;
- las columnas no cambian al alternar tabs.

---

### Fase 3 — Rediseñar estados de app

Objetivo: que la UI no muestre lo mismo en todos los estados.

Tareas:

1. Crear derivadores de estado:
   - `hasBatch`;
   - `hasSelectedImage`;
   - `isBridgeReady`;
   - `canExport`;
   - `hasWarnings`;
   - `hasBlockingErrors`;
   - `isProcessing`;
   - `isExporting`.
2. Usar esos estados para decidir qué se muestra.
3. Ocultar ajustes finos si no hay contexto.
4. Mostrar preparación/checklist si no hay lote.
5. Mostrar salida/preflight si el problema es exportación.
6. Evitar controles desactivados masivos sin explicación.

Criterio de aceptación:

- sin lote no se ve una pantalla de revisión completa fingida;
- sin imagen no se muestran controles de imagen innecesarios;
- con lote la navegación domina el panel izquierdo;
- con exportación bloqueada se explica el motivo.

---

### Fase 4 — Topbar

Objetivo: convertirla en command bar real.

Tareas:

1. Reestructurar topbar en tres zonas:
   - identidad/lote;
   - estado;
   - acciones.
2. Consolidar estados repetidos.
3. Ajustar CTA según estado:
   - seleccionar carpeta;
   - exportar;
   - cancelar exportación;
   - resolver avisos.
4. Rebajar inspector.
5. Añadir tooltips si hay acciones desactivadas.
6. Revisar copy.

Criterio de aceptación:

- el usuario sabe qué hacer mirando sólo la topbar;
- no hay estados duplicados;
- la acción principal es inequívoca;
- `Bloqueado` no aparece sin explicación.

---

### Fase 5 — Panel izquierdo

Objetivo: convertirlo en navegador de lote.

Tareas:

1. Rediseñar header del lote.
2. Separar estado sin lote y lote cargado.
3. Compactar selección de carpeta cuando ya hay lote.
4. Rediseñar resumen de métricas.
5. Rediseñar búsqueda.
6. Rediseñar filtros.
7. Rediseñar miniaturas/lista.
8. Añadir estado de búsqueda sin resultados.
9. Añadir vista de omitidas/avisos si existe.
10. Corregir truncados de nombres.

Criterio de aceptación:

- el panel no parece una mezcla de formularios;
- las miniaturas son escaneables;
- búsqueda y filtros no deforman el layout;
- la selección es clara sin ser aparatosa;
- se puede trabajar con 40–100 imágenes.

---

### Fase 6 — Workspace central

Objetivo: hacer que el canvas parezca el centro del producto.

Tareas:

1. Rediseñar header de imagen.
2. Ocultar controles irrelevantes sin selección.
3. Unificar navegación y zoom.
4. Crear stage/canvas con presencia visual.
5. Rediseñar empty states centrales.
6. Rediseñar controles inferiores de fondo.
7. Asegurar que `Fit` muestra la imagen completa.
8. Comprobar con imágenes verticales/horizontales si hay datos.

Criterio de aceptación:

- el canvas deja de ser un rectángulo muerto;
- la imagen domina cuando existe;
- sin imagen hay onboarding útil;
- no hay controles duplicados;
- no se corta la imagen en modo Fit.

---

### Fase 7 — Panel derecho: Ajustes

Objetivo: pasar de formulario técnico a inspector.

Tareas:

1. Rediseñar tabs.
2. Crear estado sin lote específico.
3. Rediseñar bloque de preset.
4. Rediseñar sliders principales.
5. Reubicar reset.
6. Rediseñar avanzado.
7. Mostrar cambios de preset de forma clara.
8. Evitar que avanzado invada el primer nivel.
9. Revisar slider disabled/active/focus.

Criterio de aceptación:

- ajustes no aparecen como ruido cuando no hay lote;
- el usuario entiende qué preset está activo;
- los parámetros principales son legibles;
- avanzado es accesible pero no protagonista;
- no hay layout shift al abrir/cerrar.

---

### Fase 8 — Panel derecho: Salida

Objetivo: convertir salida en una pantalla de decisión.

Tareas:

1. Rediseñar estado de exportación.
2. Agrupar configuración principal.
3. Crear preflight visual.
4. Añadir ejemplo de naming si es posible.
5. Mejorar legibilidad de destino.
6. Añadir acciones contextuales:
   - cambiar destino;
   - ver omitidas;
   - resolver avisos.
7. Controlar estado bloqueado.
8. Evitar duplicar CTA de forma confusa.

Criterio de aceptación:

- se entiende qué se va a exportar;
- se entiende dónde se va a exportar;
- se entiende por qué no se puede exportar si está bloqueado;
- los avisos son accionables;
- la salida no parece una tabla improvisada.

---

### Fase 9 — Statusbar

Objetivo: hacerla útil.

Tareas:

1. Sustituir columnas sueltas por frase operativa.
2. Añadir modo/progreso si aplica.
3. Mostrar último evento relevante.
4. Controlar truncado.
5. Evitar duplicación inútil.
6. Integrar estados:
   - sin lote;
   - listo;
   - con avisos;
   - procesando;
   - exportando;
   - error.

Criterio de aceptación:

- la statusbar se lee como una sola línea de estado;
- no parece relleno;
- no compite con topbar;
- aporta información durante procesos.

---

### Fase 10 — Estados vacíos, avisos y errores

Objetivo: profesionalizar todos los casos no ideales.

Tareas:

1. Implementar componente `EmptyState`.
2. Crear variantes:
   - onboarding;
   - inline;
   - warning;
   - error;
   - search empty.
3. Implementar mensajes concretos.
4. Revisar bridge pendiente.
5. Revisar carpeta vacía.
6. Revisar omitidas.
7. Revisar exportación bloqueada.
8. Revisar preview no disponible.

Criterio de aceptación:

- ningún estado vacío es una frase perdida en un hueco gris;
- todos los errores indican causa;
- las acciones de resolución están cerca del problema.

---

### Fase 11 — Limpieza visual final

Objetivo: eliminar señales de amateurismo residual.

Checklist:

- Sin mayúsculas innecesarias.
- Sin microcopy redundante.
- Sin badges por todas partes.
- Sin botones con tamaños distintos sin motivo.
- Sin sliders mal alineados.
- Sin inputs con alturas diferentes.
- Sin bordes gruesos.
- Sin paneles anidados sin razón.
- Sin texto seleccionable en UI pura.
- Sin cursor de texto sobre botones.
- Sin layout shift al interactuar.
- Sin estados duplicados.
- Sin vacíos muertos.

---

### Fase 12 — QA visual y funcional

Probar:

1. Sin lote.
2. Selección de carpeta.
3. Escaneo.
4. Lote cargado.
5. Imagen seleccionada.
6. Navegación anterior/siguiente.
7. Cambio de fondo.
8. Zoom/Fit.
9. Búsqueda.
10. Filtros.
11. Omitidas/avisos.
12. Ajustes principales.
13. Avanzado.
14. Salida.
15. Exportación bloqueada.
16. Exportación lista.
17. Bridge pendiente.
18. Bridge conectado.
19. 1366×768.
20. 1920×1080.

---

## 12. Criterios de aceptación finales

El rediseño se considera satisfactorio sólo si:

- La pantalla sin lote parece diseñada, no vacía.
- El panel derecho no muestra controles irrelevantes sin contexto.
- El canvas central tiene presencia visual.
- El usuario sabe cuál es la acción principal en menos de 2 segundos.
- El panel izquierdo funciona como navegador de lote.
- El panel derecho funciona como inspector/preflight.
- La topbar no repite estados.
- La statusbar no parece relleno.
- Los controles tienen una familia visual común.
- La app no tiene scroll global.
- La imagen se puede ver completa.
- Los estados de error explican causa y acción.
- No hay saltos de layout al cambiar tabs, filtros o selección.
- La UI parece una herramienta de producción, no una demo web.

---

## 13. Recomendación estratégica

No conviene seguir pidiendo a Codex “hazlo más profesional” en abstracto. Esa instrucción produce suavizados genéricos. El trabajo debe dividirse en entregables verificables:

1. Sistema visual.
2. Shell.
3. Estados.
4. Topbar.
5. Navegador.
6. Canvas.
7. Inspector.
8. Salida.
9. Statusbar.
10. QA.

Si Codex intenta hacerlo todo como un único cambio cosmético, probablemente volverá a producir una pantalla más limpia pero igual de amateur.

La clave es obligarle a cambiar la estructura de comportamiento, no sólo los estilos.

---

## 14. Prompt de implementación recomendado para Codex

```md
# FlatShot Desktop — Rediseño UX/UI estructural completo

Actúa como ingeniero frontend senior y diseñador de producto especializado en herramientas desktop de producción visual. No quiero otra pasada cosmética. Quiero implementar una UI profesional, estable y coherente para FlatShot Desktop.

Lee este documento completo y úsalo como especificación. La prioridad no es añadir funciones nuevas, sino rediseñar la interfaz existente para que deje de parecer prototipo.

## Objetivo

Transformar FlatShot en una herramienta de producción de imagen por lotes con:

- topbar/command bar clara;
- navegador de lote profesional;
- canvas central dominante;
- inspector contextual derecho;
- salida/preflight comprensible;
- estados vacíos diseñados;
- sistema visual consistente;
- sin scroll global;
- sin layout shifts;
- sin controles irrelevantes visibles.

## Reglas

1. No rompas funcionalidad existente.
2. No hagas sólo retoques CSS superficiales.
3. Implementa por fases.
4. Después de cada fase, prueba.
5. No dejes TODOs ni placeholders.
6. No muestres sliders de imagen cuando no hay lote o imagen si no tienen sentido contextual.
7. No uses una estética de dashboard genérico.
8. No dupliques estados entre topbar, paneles y statusbar.
9. No introduzcas dependencias pesadas salvo necesidad justificada.
10. Prioriza claridad operativa, densidad controlada y jerarquía.

## Fases obligatorias

### Fase 0 — Inspección

- Localiza archivos de UI/CSS/JS.
- Identifica render de topbar, panel izquierdo, canvas, panel derecho y statusbar.
- Ejecuta la app.
- Comprueba estado sin lote y lote cargado si es posible.

### Fase 1 — Sistema visual

- Crea tokens CSS para color, spacing, radios, sombras, tipografía, focus.
- Normaliza botones, inputs, selects, sliders, badges, segmented controls, panel sections y empty states.
- Elimina duplicidades de estilos.

### Fase 2 — Shell

- `100dvh`.
- Grid: topbar / workspace / statusbar.
- Workspace: panel izquierdo / canvas / panel derecho.
- Sin scroll global.
- Scroll interno sólo donde proceda.

### Fase 3 — Estados

Implementa derivadores claros:

- `hasBatch`;
- `hasSelectedImage`;
- `isBridgeReady`;
- `canExport`;
- `hasWarnings`;
- `hasBlockingErrors`;
- `isProcessing`;
- `isExporting`.

Usa esos estados para cambiar qué se muestra.

### Fase 4 — Topbar

- Izquierda: identidad + lote.
- Centro: estado operativo.
- Derecha: acción principal + inspección secundaria.
- Sin estados duplicados.
- CTA según estado: seleccionar carpeta/exportar/cancelar/resolver.

### Fase 5 — Panel izquierdo

- Sin lote: importación clara.
- Con lote: navegador de imágenes.
- Resumen compacto.
- Búsqueda limpia.
- Filtros con conteos.
- Miniaturas/lista profesional.
- Estado de búsqueda sin resultados.
- Selección clara sin borde tosco.

### Fase 6 — Canvas central

- Header de imagen limpio.
- Ocultar controles irrelevantes sin selección.
- Canvas/stage con presencia visual.
- Empty state central diseñado.
- Imagen completa en Fit.
- Controles inferiores de fondo normalizados.

### Fase 7 — Inspector/Ajustes

- Estado sin lote: preparación/checklist, no sliders.
- Con imagen: preset + ajustes principales + avanzado plegable.
- Sliders alineados.
- Reset contextual.
- Avanzado en grid limpio.

### Fase 8 — Salida/Preflight

- Estado de exportación claro.
- Configuración principal agrupada.
- Preflight con ok/warning/error.
- Causas de bloqueo explícitas.
- Acciones contextuales.
- Ejemplo de naming si es posible.

### Fase 9 — Statusbar

- Una línea operativa.
- Mostrar progreso/eventos.
- Sin columnas sueltas.
- Sin duplicaciones inútiles.

### Fase 10 — Estados vacíos/error

- Sin lote.
- Carpeta vacía.
- Búsqueda sin resultados.
- Bridge pendiente.
- Preview no disponible.
- Exportación bloqueada.
- Lote con omitidas.
- Error general.

Cada estado debe tener título, explicación breve y acción.

### Fase 11 — QA

Prueba:

- sin lote;
- lote cargado;
- imagen seleccionada;
- ajustes;
- salida;
- bridge pendiente/conectado;
- exportación bloqueada/lista;
- 1366×768;
- 1920×1080;
- sin scroll global;
- sin layout shift;
- sin errores de consola.

## Entrega final

Devuelve:

- resumen de cambios;
- archivos modificados;
- pruebas realizadas;
- limitaciones no probadas;
- instrucciones para revisar visualmente.
```

---

## 15. Prioridad real de ejecución

Si hay poco tiempo, no empezar por sliders ni colores. El orden de impacto debe ser:

1. Estados de app.
2. Shell/layout.
3. Empty state sin lote.
4. Topbar.
5. Panel derecho contextual.
6. Canvas central.
7. Panel izquierdo.
8. Sistema visual fino.
9. Microinteracciones.
10. QA.

El gran error sería seguir retocando botones y chips sin resolver que la pantalla está mostrando el producto equivocado en el estado equivocado.

