# Plan extensivo de mejora UX/UI — FlatShot Desktop

**Fecha:** 2026-05-25  
**Objeto:** revisión profunda del layout y del aspecto final de la interfaz de FlatShot Desktop a partir de las capturas actuales.  
**Objetivo:** llevar la UI a un nivel más profesional, más estable visualmente y más fácil de operar en un flujo real de revisión/exportación de imágenes de producto.

---

## 1. Diagnóstico ejecutivo

La interfaz ya tiene una base funcional razonable: existe una estructura de tres zonas, una vista central de previsualización, navegación lateral por lote y un panel derecho de ajustes/salida. El problema principal no es que falten piezas, sino que las piezas todavía no están jerarquizadas como una herramienta de producción madura. La pantalla comunica demasiadas cosas a la vez, con una jerarquía débil, estados repetidos, controles dispersos y un acabado visual todavía de prototipo.

La prioridad no debería ser añadir más funcionalidades visibles, sino **convertir la pantalla actual en un entorno de trabajo estable, escaneable y predecible**. FlatShot debe sentirse como una herramienta de producción fotográfica, no como una demo de controles.

### Problemas principales observados

1. **Jerarquía visual insuficiente.** Hay información importante, secundaria y técnica conviviendo con pesos parecidos. El usuario tiene que interpretar la pantalla en vez de leerla de forma natural.
2. **Exceso de microcontenedores.** Muchas cajas, chips, badges y módulos pequeños fragmentan la percepción. La UI parece ocupada aunque no tenga tanta información real.
3. **Repetición de estados.** Aparecen varias formas de decir cosas similares: lote, imagen 5/44, lista, preparada/lista, preview, bridge, exportación lista. Esto añade ruido.
4. **Panel izquierdo demasiado denso.** Mezcla importación, diagnóstico, métricas, búsqueda, filtros, agrupación por formato y navegación de imágenes en poco ancho.
5. **Panel derecho con aspecto de formulario técnico.** En `Ajustes` y `Salida` la información es funcional, pero la presentación todavía parece una pila de controles. Falta una capa de diseño orientada a decisiones.
6. **La zona central no domina lo suficiente como espacio de revisión.** La imagen tiene buen protagonismo, pero la barra superior, el fondo, las pestañas inferiores y las columnas laterales compiten visualmente.
7. **Acabado visual irregular.** Bordes, radios, alturas, chips, botones y campos no parecen pertenecer aún a un sistema visual cerrado.
8. **Estados mock/bridge/previsualización poco integrados.** Se entienden técnicamente, pero deben mostrarse como estado de sistema, no como texto de depuración permanente.
9. **Los controles avanzados están demasiado expuestos.** Un usuario que sólo quiere revisar/exportar ve sliders, motor, spread, contacto, fusión, ángulo, etc. antes de necesitarlos.
10. **Falta un modelo visual claro de “qué va a pasar al exportar”.** La salida debería explicarse con tarjetas de variantes, destino y preflight, no con un formulario resumen de lectura lenta.

---

## 2. Principio de producto recomendado

FlatShot debe organizarse alrededor de una tarea principal:

> **Seleccionar un lote, revisar el resultado visual, resolver excepciones y exportar una o varias salidas seguras.**

Todo lo que no ayude a esa secuencia debe quedar subordinado, plegado o contextualizado.

### Flujo mental deseado

1. **Tengo un lote cargado.** Sé cuántas imágenes hay, cuántas son válidas y si hay avisos.
2. **Estoy revisando una imagen concreta.** Veo claramente la imagen, su estado y puedo avanzar/retroceder.
3. **Puedo cambiar lo esencial sin perder contexto.** Fondo, preset, zoom, vista original/procesada.
4. **Sólo entro en ajustes profundos si hace falta.** Los controles técnicos no deben invadir el primer nivel.
5. **Antes de exportar sé exactamente qué se va a generar.** Formato, tamaño, fondo, destino, colisiones, omitidas y número de archivos.
6. **El sistema me avisa sin bloquearme innecesariamente.** Los avisos deben ser claros, accionables y no alarmistas.

---

## 3. Objetivos de diseño

### 3.1. Objetivos visuales

- Interfaz **desktop-first**, pensada para trabajar en pantalla grande y a pantalla completa.
- Estética profesional, sobria, limpia, de herramienta productiva.
- Menos fragmentación visual: menos cajas pequeñas y más superficies amplias bien jerarquizadas.
- Mayor consistencia en espaciado, altura de controles, radios, bordes, sombras y pesos tipográficos.
- Mayor protagonismo del visor central, sin perder capacidad operativa en los laterales.
- Reducción del ruido textual y de los microestados repetidos.

### 3.2. Objetivos funcionales

- Mantener la estructura general de app desktop: barra superior, navegador lateral, visor central, panel contextual derecho y barra inferior/status.
- Evitar scroll global. Sólo deben hacer scroll las zonas internas que lo necesiten.
- Evitar cualquier cambio de layout al alternar pestañas, seleccionar imágenes, activar filtros o cambiar ajustes.
- Separar con claridad tres niveles: operación normal, revisión de problemas y configuración avanzada.
- Hacer visible el estado de exportación/preflight sin convertirlo en una zona técnica permanente.
- Mantener separación clara entre funcionamiento real, mock, bridge local y herramientas de inspección.

---

## 4. Dirección visual recomendada

No recomiendo girar ahora hacia una UI oscura completa. Para este caso de uso, una interfaz clara, neutra y técnica encaja mejor: se revisan fondos, sombras, recortes y producto; un tema oscuro puede distorsionar la percepción del contraste de la imagen y exigir más ajustes finos. La dirección más sólida sería una **UI light profesional**, con fondo gris muy suave, superficies blancas, acento verde/teal controlado y una zona de canvas claramente separada.

### 4.1. Estilo visual objetivo

- **Fondo de app:** gris frío muy claro, no blanco puro.
- **Paneles:** blanco o blanco roto, sin sombras gruesas.
- **Canvas:** gris neutro, con opción de fondo RGB230/blanco/transparente bien diferenciada.
- **Acento:** verde/teal sólo para acciones primarias, estados correctos y selección activa.
- **Estados de aviso:** ámbar discreto; no abusar de fondos amarillos grandes.
- **Estados de error:** rojo sólo cuando hay bloqueo real.
- **Controles:** bordes finos, radios coherentes, alturas constantes.

### 4.2. Paleta base propuesta

```css
:root {
  --app-bg: #F4F6F5;
  --surface: #FFFFFF;
  --surface-muted: #F8FAF9;
  --surface-raised: #FFFFFF;
  --canvas-bg: #E9ECEB;
  --canvas-bg-soft: #EEF1F0;

  --border-subtle: #E1E7E4;
  --border-strong: #CBD5D1;

  --text-primary: #17201D;
  --text-secondary: #61706A;
  --text-tertiary: #8A9792;
  --text-inverse: #FFFFFF;

  --accent: #087D69;
  --accent-hover: #066C5B;
  --accent-soft: #DFF4EF;
  --accent-border: #A9DCD1;

  --warning: #B7791F;
  --warning-soft: #FFF3D6;
  --danger: #B42318;
  --danger-soft: #FEE4E2;

  --radius-xs: 6px;
  --radius-sm: 8px;
  --radius-md: 10px;
  --radius-lg: 14px;
  --radius-xl: 18px;

  --shadow-popover: 0 16px 40px rgba(15, 23, 42, 0.12);
  --shadow-card: 0 1px 2px rgba(15, 23, 42, 0.06);
}
```

### 4.3. Tipografía

Usar un sistema tipográfico más explícito. Ahora mismo muchos textos se perciben con pesos y tamaños parecidos, lo que reduce jerarquía.

```css
:root {
  --font-ui: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;

  --text-2xs: 10px;
  --text-xs: 11px;
  --text-sm: 12px;
  --text-md: 13px;
  --text-base: 14px;
  --text-lg: 16px;
  --text-xl: 20px;

  --line-tight: 1.15;
  --line-normal: 1.35;
}
```

Reglas:

- Los títulos de zona deben ser escasos y útiles: `Lote`, `Imagen`, `Salida`, `Ajustes`.
- Evitar mayúsculas sostenidas salvo etiquetas técnicas muy cortas. `IMAGEN SELECCIONADA` puede funcionar, pero actualmente hay demasiadas etiquetas de sección compitiendo.
- Los números operativos deben usar peso medio/semibold y, si es posible, números tabulares.
- El nombre del archivo debe tener más jerarquía que el subtítulo `Preview real`.
- Los textos de ayuda deben aparecer sólo cuando reducen fricción. No convertir cada módulo en una explicación.

---

## 5. Layout objetivo

La estructura actual de tres columnas es válida, pero debe refinarse. La pantalla debe sentirse como una herramienta con regiones claras y estables:

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ Topbar: identidad · lote · estado sistema · acciones globales                │
├───────────────┬──────────────────────────────────────────────┬───────────────┤
│ Navegador     │ Visor / revisión                             │ Panel         │
│ de lote       │                                              │ contextual    │
│               │ Header imagen + toolbar                       │ Ajustes/Salida│
│ Filtros       │ Canvas grande                                 │ Preflight     │
│ Miniaturas    │ Controles de fondo/zoom/vista                  │ Avanzado      │
│ Diagnóstico   │                                              │               │
├───────────────┴──────────────────────────────────────────────┴───────────────┤
│ Status bar: progreso, mensajes, cola, actividad                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 5.1. Medidas recomendadas para viewport 2048×1104 / entorno 1920×1080

```css
.app-shell {
  height: 100dvh;
  display: grid;
  grid-template-rows: 56px minmax(0, 1fr) 34px;
}

.workspace {
  min-height: 0;
  display: grid;
  grid-template-columns:
    clamp(280px, 17vw, 340px)
    minmax(720px, 1fr)
    clamp(320px, 20vw, 390px);
}
```

Observaciones:

- El panel izquierdo puede subir ligeramente de ancho si se quiere que las miniaturas sean legibles. La versión actual parece en torno a 300 px; es aceptable, pero la composición interna está demasiado comprimida.
- El panel derecho necesita anchura estable. Debe poder mostrar campos y sliders sin parecer estrecho, pero no debe robar protagonismo al canvas.
- La zona central debe reservarse como área dominante. La imagen debe sentirse como el objeto de trabajo, no como una previsualización incrustada entre paneles.
- En pantallas muy anchas, no conviene que los laterales crezcan indefinidamente. Mejor limitar ancho y dejar crecer el canvas.

---

## 6. Barra superior global

### 6.1. Problema actual

La topbar contiene identidad, contador, estado de bridge, botón exportar, botón inspector y estado conectado, pero la lectura queda algo dispersa. El resultado parece más un encabezado de prototipo que una barra de comando consolidada.

### 6.2. Objetivo

La barra superior debe responder a cuatro preguntas:

1. ¿Qué app estoy usando?
2. ¿Qué lote está cargado?
3. ¿El sistema está listo?
4. ¿Cuál es la acción principal?

### 6.3. Propuesta de composición

```text
[ F ] FlatShot        44 imágenes · 1 omitida       ● Bridge conectado
                                                        [Preflight listo] [Exportar 44]
```

`Inspector` debe quedar como acción secundaria o menú técnico, no al mismo nivel que exportar.

### 6.4. Cambios concretos

- Mantener logo y nombre, pero reducir protagonismo del bloque de identidad.
- Fusionar `Preview lista · Bridge conectado` en un único indicador de sistema: `Bridge conectado · Preview real`.
- Evitar repetir `Conectado` junto a `Bridge conectado`. Una sola señal basta.
- Convertir `Inspector` en icono/menú secundario o botón discreto `Inspección` sólo visible en modo desarrollo.
- Hacer que `Exportar 44` sea el CTA dominante, con altura y peso consistentes.
- Añadir estado de preflight cerca del CTA: `Listo`, `2 avisos`, `Bloqueado`, etc.
- Si hay cambios pendientes en ajustes, mostrar `Cambios sin aplicar` o `Preset modificado` de forma contextual, no como badge suelto.

### 6.5. Criterios de aceptación

- La barra superior se lee de izquierda a derecha en menos de dos segundos.
- No hay más de dos chips de estado visibles simultáneamente.
- El botón de exportación es el único elemento con máximo peso visual en la barra.
- El inspector no compite con la acción principal.

---

## 7. Panel izquierdo — Navegador de lote

### 7.1. Problema actual

El panel izquierdo intenta hacer demasiadas cosas: resumen, cambio de carpeta, estado de escaneo, diagnósticos, búsqueda, agrupación por formato, filtros y miniaturas. Además, las miniaturas actuales parecen tarjetas de estado más que previews reales; la etiqueta `Lista` repetida en cada item añade ruido y no ayuda a diferenciar.

### 7.2. Objetivo

El panel izquierdo debe ser un **navegador operativo de lote**, no un panel de configuración. Su función principal es permitir orientarse, filtrar y saltar entre imágenes.

### 7.3. Estructura propuesta

```text
Lote
44 imágenes                         [1 omitida]
Carpeta: Escaneo completado         [Cambiar] [Reescanear]
45 archivos · 44 válidas · 1 omitida

Buscar imagen...
[ Todas ] [ Válidas ] [ Avisos ] [ Errores ]

PNG · 44                            [colapsar]
┌──────┐ ┌──────┐ ┌──────┐
│ img  │ │ img  │ │ img  │
│S670… │ │S670… │ │S670… │
└──────┘ └──────┘ └──────┘

Diagnóstico                         [Ver]
2 avisos no bloqueantes
```

### 7.4. Reorganización recomendada

#### Bloque 1 — Resumen de lote

Debe ser compacto, pero más limpio que ahora.

- Título: `Lote`
- Número principal: `44 imágenes`
- Badge secundario: `1 omitida`
- Estado de carpeta: `Escaneo completado · 2 avisos`
- Acciones: `Cambiar carpeta` y `Reescanear`, con jerarquía clara.

Evitar que `Cambiar carpeta`, `Carpeta local`, `Escaneo completado con 2 avisos`, `Seleccionar carpeta` y `Escanear` compitan todos a la vez.

#### Bloque 2 — Métricas

Las métricas deben ocupar una línea o mini-grid sobria:

```text
Archivos 45     Válidas 44     Omitidas 1
```

No necesitan grandes números si el título ya dice `44 imágenes`.

#### Bloque 3 — Diagnóstico

`Ver diagnóstico` no debería estar suelto como un enlace con triángulo. Mejor:

```text
Diagnóstico
2 avisos no bloqueantes       [Ver]
```

Si no hay avisos:

```text
Diagnóstico
Sin incidencias
```

Si hay errores bloqueantes:

```text
Diagnóstico
1 error bloqueante            [Resolver]
```

#### Bloque 4 — Búsqueda y filtros

- El buscador debe ser sticky dentro del panel cuando se hace scroll por muchas imágenes.
- Placeholder más concreto: `Buscar por nombre...`
- Añadir `⌘/Ctrl+F` o icono de búsqueda si se implementa atajo.
- Los filtros deben ser compactos y estables. No deben mover el grid al activarse.

#### Bloque 5 — Grupos y miniaturas

La agrupación `PNG` debe ser útil, pero no una tarjeta amarilla grande salvo que haya avisos del grupo. Propuesta:

```text
PNG      44 imágenes · 1 omitida
```

La etiqueta `44` puede ir a la derecha, pero no debe parecer un badge de alerta.

### 7.5. Miniaturas

#### Problemas actuales

- Las tarjetas parecen placeholders de color, no previews informativas.
- La etiqueta `Lista` se repite demasiado.
- La selección activa se ve, pero podría integrarse mejor.
- Los nombres están truncados de forma demasiado agresiva.
- No queda claro si una imagen tiene aviso, error, está omitida o procesada salvo por etiquetas repetidas.

#### Diseño propuesto de item

```text
┌────────────────┐
│                │
│   preview      │
│                │
├────────────────┤
│ S6707435...    │
│ ● Lista        │
└────────────────┘
```

Pero en una versión más limpia:

- No mostrar `Lista` como texto en todas las tarjetas. Usar un punto/mini-icono sólo cuando el estado sea relevante.
- Mostrar texto de estado únicamente para avisos, errores u omitidas.
- En estado normal, basta con borde neutro y nombre.
- El item activo debe tener borde/acento claro y quizás un fondo suave.
- Usar tooltip o title completo para nombre largo.
- Si la miniatura real no está disponible, mostrar placeholder con icono y texto `Sin preview`, no un bloque de color que parezca intencionado.

#### Estados de miniatura

| Estado | Tratamiento visual recomendado |
|---|---|
| Normal/lista | Borde neutro, sin badge textual repetido |
| Seleccionada | Borde accent 2 px, fondo accent-soft muy sutil |
| Aviso | Punto o badge ámbar pequeño en esquina |
| Error | Borde rojo y badge `Error`, sólo si bloquea |
| Omitida | Opacidad reducida, etiqueta `Omitida` |
| Procesando | Overlay ligero con spinner o shimmer |
| Exportada | Check discreto si procede |

### 7.6. Comportamiento

- El panel debe recordar el scroll y la selección.
- Al avanzar con teclado, la miniatura seleccionada debe mantenerse visible.
- Filtros y búsqueda no deben resetear la selección salvo que el elemento deje de existir en la vista filtrada.
- La búsqueda debe tolerar errores leves y coincidencias parciales.
- En lote grande, usar virtualización para evitar degradación.

---

## 8. Zona central — Visor y revisión

### 8.1. Problema actual

La zona central es amplia y va en buena dirección, pero todavía no se siente como un visor de producción terminado. Hay elementos en la parte superior y bottom del canvas que no parecen completamente integrados. La imagen se ve bien, aunque podría aprovechar más el área útil y comunicar mejor el contexto de revisión.

### 8.2. Objetivo

La zona central debe ser el **núcleo de la aplicación**. Todo debe ayudar a revisar la imagen seleccionada, comparar estados, ajustar fondo/zoom y navegar por el lote sin ruido.

### 8.3. Header de imagen

Actualmente se muestra:

```text
IMAGEN SELECCIONADA
S670743599111.png
Preview real
[Procesada]  < Imagen 5 de 44 > Ajustar 100% - Fit +
```

Debe convertirse en una barra más integrada:

```text
S670743599111.png      Procesada · Preview real
[←] 5 / 44 [→]        [Original] [Procesada]     [Fit] [100%] [-] [+]
```

O, más compacto:

```text
S670743599111.png   ·   Procesada   ·   Preview real       ← 5/44 →   Fit  100%  − +
```

### 8.4. Reglas para el header

- El nombre del archivo es el título principal de la zona central.
- `Preview real` debe ser un estado secundario, no un subtítulo pesado.
- `Procesada` debe parecer un selector de vista si se puede alternar; si no se puede, debe ser un estado, no un botón.
- `Imagen 5 de 44` sólo debe aparecer en un sitio. No repetirlo también en la barra inferior salvo como status muy compacto.
- Agrupar navegación `← 5/44 →` como un solo control.
- Agrupar zoom `− 100% + Fit` como un solo control.
- `Ajustar` y `Fit` parecen redundantes. Usar una sola convención: `Fit`, `100%`, `Rellenar` si hace falta.

### 8.5. Canvas

#### Problemas actuales

- El canvas tiene mucho espacio gris, pero la imagen no siempre parece ajustada al máximo útil.
- El fondo RGB230/blanco/transparente aparece abajo, separado del contexto principal de visualización.
- El usuario puede no saber si está viendo fondo real de exportación, fondo de preview o fondo de canvas.

#### Propuesta

- El canvas debe tener una superficie clara y contenida, no una zona plana sin límites perceptivos.
- Mostrar fondo activo como control contextual cerca del visor, no como elemento residual abajo.
- Usar una pequeña barra flotante o integrada en la parte inferior izquierda del canvas:

```text
Fondo preview: [RGB230] [Blanco] [Transparente]
```

- Si el fondo seleccionado afecta realmente a la exportación, usar `Fondo salida`. Si sólo afecta a visualización, usar `Fondo preview`. No mezclar.
- En transparente, usar patrón checkerboard sutil y profesional.
- Si hay sombra activa, mostrar `Sombra: Luz cenital` como estado secundario sólo si es útil.

### 8.6. Tamaño de imagen

Implementar cálculo de fit más agresivo:

- La imagen debe ocupar el máximo espacio útil sin recortar.
- Debe respetar márgenes mínimos de 48–64 px dentro del canvas.
- En productos verticales, aprovechar la altura disponible.
- En productos horizontales, aprovechar anchura sin generar vacío excesivo.
- Evitar que paneles inferiores o toolbars resten altura si no son necesarios.

### 8.7. Herramientas de comparación

No añadir complejidad visible de entrada, pero prever:

- Toggle `Original / Procesada`.
- Mantener pulsado `O` para ver original temporalmente.
- Comparación antes/después tipo split sólo en un modo explícito.
- Zoom al 100% con doble clic.
- Pan con espacio + arrastrar si hay zoom.

### 8.8. Estados del visor

Diseñar estados específicos:

| Estado | Qué debe ver el usuario |
|---|---|
| Sin lote | Zona central vacía con CTA `Seleccionar carpeta` |
| Lote escaneando | Progreso claro, sin mostrar controles inútiles |
| Imagen cargando | Skeleton/loader dentro del canvas |
| Preview no disponible | Mensaje breve + acción `Reintentar` |
| Error de procesamiento | Mensaje claro + detalle plegable |
| Imagen omitida | Aviso contextual y motivo |
| Bridge desconectado | Banner discreto indicando limitación real |

---

## 9. Panel derecho — Ajustes y salida

### 9.1. Problema actual

El panel derecho es funcional, pero todavía parece un formulario técnico. En `Salida`, los campos se leen de forma relativamente clara, pero el resumen inferior repite información. En `Ajustes`, los sliders y valores están expuestos al mismo nivel que los presets, y el bloque avanzado ocupa demasiado peso visual.

### 9.2. Objetivo

El panel derecho debe ser un **panel contextual de decisión**. Debe responder:

- En `Ajustes`: qué preset estoy usando, qué puedo cambiar de forma segura y qué está avanzado.
- En `Salida`: qué archivos se van a generar, dónde y con qué configuración.

### 9.3. Tabs

Los tabs `Ajustes` / `Salida` están bien, pero necesitan pulido:

- Altura estable: 36–40 px.
- Borde inferior o fondo claro, no apariencia de botones flotantes independientes.
- Estado activo claro, sin sombra azul exagerada.
- El contenido bajo tabs debe mantener el mismo padding y estructura.
- Cambiar de tab no debe alterar el ancho del panel ni mover el canvas.

### 9.4. Tab Ajustes

#### Estructura propuesta

```text
Ajustes
Preset: Luz cenital                          Sin cambios
[ Luz cenital ] [ Estándar oscuro ]          [Reset]

Ajustes principales
Opacidad        ━━━━━━━──── 20
Blur            ━━━━━━━━━── 30
Distancia       ━━━━━━───── 25
Padding         ━━━──────── 10

Avanzado                         [Mostrar]
Motor: Realista V2
```

#### Cambios concretos

- `PRESET Luz cenital` debe convertirse en una cabecera legible: `Preset` + nombre.
- `Defaults` sobra si no aporta algo accionable. Puede ocultarse o moverse a tooltip.
- `Sin cambios` debe estar asociado al preset, no flotando como badge sin relación clara.
- `Reset` debe aclarar si resetea preset completo o sólo cambios actuales.
- Los sliders deben tener valores alineados en columna. Ahora hay cierto aspecto de formulario irregular.
- Añadir `Reset` por sección sólo si hay cambios en esa sección.
- El bloque avanzado debe estar plegado por defecto. En la captura aparece expandido y genera mucho ruido.
- `Motor` debería estar dentro de avanzado, no expuesto al final como un campo más si el usuario normal no lo toca.

#### Sliders

Recomendación visual:

```text
Opacidad                         20
[────────────●────────────]
```

No poner el valor demasiado separado si el panel es estrecho. Mantener una retícula fija.

#### Controles avanzados

Los campos `Spread`, `Ruido`, `Contacto`, `Escala`, `Fusión`, `Ángulo`, `Contracción`, `Zoom auto`, `Motor` deben tratarse como parámetros expertos.

Propuesta:

```text
Avanzado
Ajustes técnicos para casos específicos. Mantener plegado salvo necesidad.
[Mostrar parámetros]
```

Al expandir:

- Usar grid de dos columnas sólo si el ancho lo permite.
- Agrupar por tipo:
  - Sombra: Spread, Ruido, Contacto, Fusión.
  - Geometría: Escala, Ángulo, Contracción.
  - Render: Zoom auto, Motor.
- Mostrar valores numéricos con input compacto.
- Añadir botón `Restaurar avanzado` si procede.

### 9.5. Tab Salida

#### Problema actual

La salida se muestra como campos sueltos:

- Formato
- Tamaño
- Fondo
- Destino
- Ruta destino
- Naming
- Resumen

Esto funciona, pero no transmite bien el resultado final. El usuario necesita ver “qué se generará” antes que “qué campos tiene el formulario”.

#### Modelo recomendado: tarjetas de salida

La exportación debería mostrarse como una o varias variantes. Esto conecta con la necesidad real de exportar varias versiones de una imagen en una ejecución: RGB230, blanco, transparente u otras.

```text
Salida
44 archivos listos

Variantes
[✓] Web RGB230
    JPG · 1800×2400 · fondo RGB230
    /_SALIDA_PRO · {original}{suffix}

[ ] Blanco
    JPG · 1800×2400 · fondo RGB255
    Misma sombra · destino configurable

[ ] Transparente
    PNG · 1800×2400 · sin fondo
    Sin sombra/fondo según preset

Destino
Origen / _SALIDA_PRO
[ Cambiar destino ]

Preflight
✓ 44 imágenes válidas
✓ Permiso de escritura correcto
✓ Sin colisiones de nombre
⚠ 1 imagen omitida
```

#### Ventajas

- El usuario entiende la exportación como resultado, no como formulario.
- Permite crecer hacia multi-salida sin rehacer la UI.
- Reduce repetición: el resumen final se integra en las tarjetas.
- Los avisos de preflight quedan cerca del botón exportar.

#### Campos editables

Los campos actuales no deben desaparecer, pero pueden moverse a edición contextual:

- Clic en una tarjeta de variante abre sus detalles.
- `Formato`, `Tamaño`, `Fondo`, `Naming` aparecen dentro de esa variante.
- `Destino` puede ser global o por variante, pero debe indicarse explícitamente.
- Evitar tener `Fondo` duplicado en `Ajustes`, canvas y `Salida` sin aclarar el alcance.

### 9.6. Preflight

Debe existir una capa de preflight visible y accionable:

```text
Preflight
Listo para exportar
44 imágenes se exportarán · 1 omitida

✓ Carpeta de destino disponible
✓ Sin sobrescrituras
✓ Naming válido
⚠ 1 archivo omitido por formato no válido
```

Si hay problema:

```text
Preflight
Exportación bloqueada

✕ No se puede escribir en destino
[Elegir otro destino]
```

### 9.7. Relación entre panel derecho y botón exportar

El botón global `Exportar 44` debe tomar su estado del preflight:

| Estado | CTA |
|---|---|
| Todo correcto | `Exportar 44` |
| Avisos no bloqueantes | `Exportar 44` + badge `1 aviso` |
| Error bloqueante | `Resolver errores` o `Exportar` deshabilitado con motivo |
| Cambios pendientes | `Aplicar y exportar` sólo si realmente hay cambios no aplicados |
| Exportando | `Exportando… 18/44` |
| Finalizado | `Exportado 44` + acción `Abrir carpeta` |

---

## 10. Barra inferior / estado

### 10.1. Problema actual

La barra inferior muestra `44 imágenes · Imagen 5/44`, `Lista` y `Preview lista`, pero parte de esa información ya aparece arriba o en el visor. No aporta suficiente valor para ocupar una fila persistente si no se usa mejor.

### 10.2. Objetivo

La barra inferior debe ser un sistema de estado operativo, no un duplicado de datos.

### 10.3. Propuesta

```text
44 imágenes · 1 omitida       Imagen 5/44       Bridge conectado · Preview real       Última acción: carpeta escaneada hace 12 s
```

Durante exportación:

```text
Exportando 18/44      ███████████░░░░░░░░      S6707435...jpg      Cancelar
```

Tras exportación:

```text
Exportación completada · 44 archivos creados      [Abrir carpeta] [Ver informe]
```

### 10.4. Reglas

- Si la barra inferior sólo repite información, eliminar o reducir.
- Usarla para progreso, cola, mensajes breves y última acción relevante.
- No usarla para controles principales salvo progreso/cancelación.
- Mantener altura fija para evitar saltos.

---

## 11. Sistema de componentes

Para que la app deje de sentirse como una suma de piezas, conviene definir componentes base y no seguir ajustando estilos caso por caso.

### 11.1. Componentes base

- `AppShell`
- `TopCommandBar`
- `StatusChip`
- `PrimaryButton`
- `SecondaryButton`
- `IconButton`
- `SegmentedControl`
- `Panel`
- `SectionHeader`
- `MetricRow`
- `BatchSummaryCard`
- `AssetGrid`
- `AssetThumbnail`
- `PreviewStage`
- `StageToolbar`
- `ContextPanel`
- `AdjustmentPanel`
- `OutputPanel`
- `OutputVariantCard`
- `PreflightCard`
- `BottomStatusBar`
- `ToastStack`
- `EmptyState`
- `InlineAlert`
- `Disclosure`
- `Tooltip`

### 11.2. Reglas globales

- Ningún componente debe inventar su propio radio, borde o sombra.
- Ningún botón debe tener altura arbitraria.
- Los chips deben tener semántica clara: estado, filtro, contador o acción. No mezclar.
- Los campos de formulario deben tener label, valor y ayuda sólo si es necesaria.
- Los estados deben resolverse con una taxonomía común.

### 11.3. Tokens de tamaño

```css
:root {
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;

  --control-sm: 28px;
  --control-md: 34px;
  --control-lg: 40px;

  --sidebar-pad: 16px;
  --panel-pad: 16px;
  --section-gap: 18px;
}
```

---

## 12. Microcopy y lenguaje de interfaz

### 12.1. Problema actual

Hay bastante texto técnico o redundante. Ejemplos visibles:

- `Preview lista · Bridge conectado`
- `Preview real · Preset real`
- `EXPORTACIÓN Lista`
- `Defaults`
- `Imagen seleccionada`
- `Ver diagnóstico`
- `Lista` repetido en cada miniatura

No todo está mal, pero se percibe como lenguaje generado para explicar la app, no como microcopy de producto final.

### 12.2. Reglas

- Una etiqueta debe decir qué es una cosa, no narrar el estado interno salvo que sea útil.
- Evitar frases técnicas persistentes si sólo importan para desarrollo.
- Usar sustantivos claros: `Lote`, `Imagen`, `Salida`, `Ajustes`, `Diagnóstico`.
- Usar estados breves: `Listo`, `Procesada`, `Con avisos`, `Bloqueado`, `Exportando`.
- Evitar duplicar el estado en varios sitios.

### 12.3. Propuesta de vocabulario

| Actual | Propuesto |
|---|---|
| Preview lista | Preview real / Preview disponible |
| Bridge conectado | Bridge conectado, sólo en estado de sistema |
| Exportación Lista | Salida lista |
| Imagen seleccionada | Imagen |
| Cambiar carpeta | Cambiar lote / Cambiar carpeta, elegir una y mantenerla |
| Escanear | Reescanear si ya hay carpeta cargada |
| Procesada | Vista procesada si es selector; Procesada si es estado |
| Ajustar | Fit / Ajustar a pantalla, elegir una convención |
| Sin cambios | Sin cambios del preset |
| Defaults | Valores por defecto / ocultar |

---

## 13. Estados visuales y feedback

### 13.1. Taxonomía de estados

Definir estados de forma cerrada:

```text
Sistema:
- Bridge conectado
- Bridge desconectado
- Modo mock
- Modo real
- Procesando
- Exportando

Lote:
- Sin lote
- Escaneando
- Listo
- Con avisos
- Con errores

Imagen:
- Lista
- Procesando
- Procesada
- Omitida
- Error
- Sin preview

Salida:
- Sin configurar
- Lista
- Con avisos
- Bloqueada
- Exportando
- Exportada
```

### 13.2. Reglas visuales

- Verde sólo para estados correctos o acción principal.
- Ámbar para avisos no bloqueantes.
- Rojo para errores bloqueantes.
- Gris para estados neutros o inactivos.
- No usar badges verdes por todas partes. Si todo es verde, nada destaca.
- No usar texto como único indicador; combinar con icono/punto/estructura.

### 13.3. Feedback de acciones

Cada acción relevante debe tener feedback:

| Acción | Feedback recomendado |
|---|---|
| Seleccionar carpeta | Loader + resultado de escaneo |
| Reescanear | Progreso y número detectado |
| Cambiar filtro | Conteo actualizado sin salto de layout |
| Seleccionar imagen | Cambio inmediato de visor + item activo visible |
| Cambiar fondo | Canvas actualiza y estado queda claro |
| Cambiar preset | Badge `Cambios sin guardar` o `Preset modificado` |
| Reset | Confirmación suave, sin modal salvo pérdida relevante |
| Exportar | Progreso, archivo actual, cancelar, resultado final |
| Error de exportación | Motivo, solución y posibilidad de reintentar |

---

## 14. Interacciones y fluidez

### 14.1. Evitar layout shift

FlatShot debe sentirse estable. Prohibir microcambios de layout al:

- Cambiar entre `Ajustes` y `Salida`.
- Seleccionar imagen.
- Activar/desactivar filtros.
- Mostrar estados de aviso.
- Expandir `Avanzado`.
- Cambiar de fondo.
- Activar modo inspector.

Soluciones:

- Reservar espacio para headers y barras.
- Usar paneles internos con scroll en vez de empujar el layout global.
- Usar overlays/popovers para edición contextual.
- Usar alturas mínimas en tarjetas de resumen.
- Evitar que badges aparezcan/desaparezcan alterando anchuras.

### 14.2. Animaciones

Usar microtransiciones muy discretas:

```css
:root {
  --ease-standard: cubic-bezier(.2, .8, .2, 1);
  --duration-fast: 120ms;
  --duration-base: 180ms;
}
```

Aplicar a:

- Hover/focus de botones.
- Selección de miniatura.
- Cambio de tabs.
- Apertura de avanzado.
- Aparición de toasts.
- Carga de imagen.

Evitar:

- Animaciones largas.
- Slides grandes en layout principal.
- Rebotes o efectos decorativos.

### 14.3. Teclado

Para una app de producción, los atajos son importantes:

| Atajo | Acción |
|---|---|
| ← / → | Imagen anterior/siguiente |
| Ctrl/Cmd+F | Buscar imagen |
| Ctrl/Cmd+E | Exportar si preflight listo |
| F | Ajustar/Fit |
| 1 | Fondo RGB230 |
| 2 | Fondo blanco |
| 3 | Transparente |
| O mantenida | Ver original temporalmente |
| Esc | Cerrar panel/overlay |

Los atajos deben aparecer en tooltips, no como texto permanente.

---

## 15. Accesibilidad y usabilidad técnica

### 15.1. Contraste

- Verificar contraste de texto secundario sobre fondos claros.
- No usar verde suave para textos pequeños si no llega a contraste suficiente.
- Los placeholders deben ser claramente secundarios, pero legibles.

### 15.2. Tamaños de objetivo

- Botones principales: mínimo 36–40 px de alto.
- Icon buttons: mínimo 32×32 px.
- Chips clicables: mínimo 28–32 px de alto.
- Sliders: área interactiva amplia, no sólo línea fina.

### 15.3. Foco

- Focus ring visible y consistente.
- No depender sólo del hover.
- Navegación por teclado lógica: topbar → panel izquierdo → visor → panel derecho → status.

### 15.4. Selección de texto

- UI no seleccionable por defecto: botones, chips, labels, headers, tarjetas.
- Seleccionable donde tenga sentido: rutas, nombres de archivo, logs, mensajes de error, informes.

### 15.5. Tooltips

Usar tooltips para:

- Iconos sin texto.
- Estados técnicos: bridge, mock, preview real.
- Nombres truncados.
- Atajos de teclado.

No usar tooltips para explicar acciones básicas que deberían entenderse por el propio label.

---

## 16. Responsive desktop y comportamiento en pantalla completa

FlatShot no necesita una estrategia mobile prioritaria. Sí necesita una estrategia desktop sólida.

### 16.1. Breakpoints recomendados

```css
/* Desktop mínimo aceptable */
@media (max-width: 1440px) {
  .workspace {
    grid-template-columns: 280px minmax(620px, 1fr) 320px;
  }
}

/* Desktop amplio */
@media (min-width: 1920px) {
  .workspace {
    grid-template-columns: 320px minmax(860px, 1fr) 360px;
  }
}

/* Muy ancho */
@media (min-width: 2400px) {
  .workspace {
    grid-template-columns: 340px minmax(1000px, 1fr) 390px;
  }
}
```

### 16.2. Reglas

- No permitir que la imagen quede pequeña en pantallas grandes.
- No permitir que los paneles se ensanchen hasta generar líneas demasiado largas.
- Mantener controles agrupados y no dispersarlos por toda la anchura.
- El canvas debe absorber el crecimiento horizontal.

---

## 17. Plan de implementación por fases

La implementación debe hacerse por fases cerradas. No conviene seguir con microcambios aislados porque eso mantiene la sensación de prototipo.

---

### Fase 0 — Congelación funcional y auditoría de layout

**Objetivo:** no añadir funciones nuevas mientras se consolida la interfaz.

#### Tareas

1. Identificar archivos reales de UI actuales. Probablemente `index.html`, `styles.css`, `app.js` o equivalentes, pero no asumir rutas si el proyecto ha cambiado.
2. Documentar componentes existentes y responsabilidades visuales.
3. Separar funciones reales, mock, bridge local e inspector.
4. Listar todos los estados de app/lote/imagen/salida.
5. Sacar capturas base de comparación:
   - Sin lote.
   - Lote cargado sin avisos.
   - Lote con avisos.
   - Ajustes abierto.
   - Salida abierta.
   - Exportando.
   - Exportación finalizada.
   - Error de bridge.

#### Entregable

- Inventario breve de pantallas/estados.
- Lista de componentes a refactorizar.
- Confirmación de que no se han añadido features fuera de alcance.

#### Criterios de aceptación

- Existe una referencia visual antes/después.
- El equipo/agente sabe qué piezas son reales y cuáles son mock.
- No se modifica la lógica de exportación en esta fase salvo para corregir estados visuales.

---

### Fase 1 — Sistema visual base

**Objetivo:** crear tokens y estilos base para que todo lo demás herede consistencia.

#### Tareas

1. Crear variables CSS de color, espaciado, radios, sombras, tipografía y alturas de control.
2. Normalizar `box-sizing`, fuente global, antialiasing y selección de texto.
3. Definir estilos base para botones, campos, chips, tabs, panels y scrollbars.
4. Eliminar estilos duplicados o contradictorios.
5. Sustituir colores hardcodeados por tokens.
6. Revisar contraste de todos los textos pequeños.

#### Entregable

- `design tokens` aplicados globalmente.
- Componentes base visualmente coherentes.

#### Criterios de aceptación

- Todos los botones comparten altura/radio/padding coherente.
- Todos los paneles comparten borde/fondo/radio coherente.
- No hay colores críticos hardcodeados dispersos.
- La app mantiene el layout actual, pero ya parece más unificada.

---

### Fase 2 — AppShell y distribución macro

**Objetivo:** cerrar la estructura general para que no haya scroll global ni saltos de layout.

#### Tareas

1. Implementar `AppShell` con tres filas: topbar, workspace y statusbar.
2. Implementar `Workspace` con tres columnas: lote, visor, contexto.
3. Definir widths mediante `clamp()`.
4. Asegurar `min-height: 0` y scroll interno en paneles.
5. Eliminar scroll horizontal y vertical global.
6. Fijar topbar y statusbar sin overlays accidentales.
7. Revisar comportamiento en 1440, 1920, 2048 y 2560 px de ancho.

#### Entregable

- Layout estable y full-screen.

#### Criterios de aceptación

- No aparece scroll global.
- Cambiar tab derecho no mueve el visor.
- Seleccionar imágenes no cambia ancho/alto de paneles.
- En 2048×1104 se ve todo el flujo principal sin scroll global.

---

### Fase 3 — Rediseño de topbar

**Objetivo:** convertir la barra superior en una barra de comando limpia.

#### Tareas

1. Reorganizar identidad, lote, estado de sistema y acciones.
2. Unificar `Conectado` y `Bridge conectado` en un único estado.
3. Reducir exposición del inspector.
4. Crear estado de preflight junto al CTA.
5. Revisar el label del botón primario según estado.
6. Añadir menú secundario si hay acciones técnicas.

#### Entregable

- Topbar final de producción.

#### Criterios de aceptación

- Sólo hay un CTA principal.
- Los estados no se repiten.
- El inspector no compite visualmente.
- El usuario entiende si puede exportar o no.

---

### Fase 4 — Rediseño del panel izquierdo

**Objetivo:** convertir el panel izquierdo en un navegador de lote más claro y operativo.

#### Tareas

1. Rehacer el bloque `Lote`.
2. Simplificar métricas y estado de carpeta.
3. Convertir diagnóstico en tarjeta compacta.
4. Hacer sticky la búsqueda/filtros si el panel scrollea.
5. Rediseñar grupo `PNG`.
6. Rediseñar miniaturas y estados.
7. Eliminar `Lista` repetido en miniaturas normales.
8. Implementar tooltips para nombres truncados.
9. Mantener item seleccionado visible al navegar.
10. Revisar virtualización si el lote puede crecer.

#### Entregable

- Navegador de lote refinado.

#### Criterios de aceptación

- El usuario distingue rápido válidas, omitidas, avisos y errores.
- Las miniaturas se reconocen como imágenes o como placeholders claros.
- El estado normal no genera ruido textual.
- El panel sigue siendo usable con muchas imágenes.

---

### Fase 5 — Rediseño del visor central

**Objetivo:** reforzar la imagen como elemento principal de la app.

#### Tareas

1. Rediseñar header de imagen.
2. Agrupar navegación y zoom.
3. Normalizar `Original/Procesada` si existe comparación.
4. Reubicar selector de fondo del preview.
5. Mejorar cálculo de fit.
6. Crear estados del canvas: vacío, cargando, error, sin preview, omitida.
7. Añadir comportamiento de teclado básico.
8. Integrar fondo RGB230/blanco/transparente de forma semántica.

#### Entregable

- Visor central de aspecto final.

#### Criterios de aceptación

- La imagen ocupa más y mejor el espacio útil.
- El usuario sabe qué fondo está viendo.
- No hay duplicación de `Imagen 5/44`.
- Los controles de navegación y zoom están agrupados.

---

### Fase 6 — Rediseño del panel derecho: Ajustes

**Objetivo:** convertir los ajustes en una herramienta clara, con avanzado plegado.

#### Tareas

1. Rediseñar tabs.
2. Crear cabecera de preset con estado `Sin cambios` / `Modificado`.
3. Rehacer chips de preset.
4. Reorganizar sliders con labels y valores alineados.
5. Plegar avanzado por defecto.
6. Agrupar campos avanzados por categoría.
7. Revisar significado de `Reset`.
8. Evitar que expandir avanzado altere el layout global.

#### Entregable

- Tab `Ajustes` limpio y profesional.

#### Criterios de aceptación

- Un usuario normal no ve parámetros expertos salvo que los pida.
- El estado del preset es inequívoco.
- Los sliders parecen parte de un sistema, no campos sueltos.

---

### Fase 7 — Rediseño del panel derecho: Salida y preflight

**Objetivo:** hacer que la exportación sea comprensible antes de ejecutar.

#### Tareas

1. Sustituir formulario plano por modelo de tarjetas de salida.
2. Integrar formato, tamaño, fondo, destino y naming por variante.
3. Preparar UI para varias variantes de salida sin obligar a activar todas.
4. Crear bloque de preflight.
5. Asociar preflight al estado del CTA global.
6. Mostrar colisiones/sobrescrituras/permisos como checks claros.
7. Definir comportamiento tras exportación: abrir carpeta, informe, reintentar fallos.

#### Entregable

- Tab `Salida` orientado a resultado.

#### Criterios de aceptación

- El usuario sabe qué archivos se van a generar.
- Se entiende destino y naming sin leer un formulario largo.
- Los problemas bloqueantes están cerca de la solución.
- La UI queda preparada para multi-salida.

---

### Fase 8 — Barra inferior y feedback de actividad

**Objetivo:** convertir la barra inferior en un sistema de estado útil.

#### Tareas

1. Eliminar duplicidades con topbar/visor.
2. Definir mensajes por estado.
3. Implementar progreso de exportación.
4. Añadir última acción relevante.
5. Añadir acciones post-exportación.
6. Diseñar estado de error no invasivo.

#### Entregable

- Statusbar útil y estable.

#### Criterios de aceptación

- La barra inferior aporta información que no está ya arriba.
- Durante exportación, se entiende progreso y archivo actual.
- Tras exportación, se puede abrir carpeta o ver informe.

---

### Fase 9 — Estados vacíos, errores y edge cases

**Objetivo:** que la app no parezca rota cuando no está en el caso feliz.

#### Casos obligatorios

1. Sin carpeta seleccionada.
2. Carpeta vacía.
3. Carpeta inválida.
4. Sin permisos de lectura.
5. Bridge desconectado.
6. Modo mock.
7. Imagen no soportada.
8. Preview no disponible.
9. Exportación sin permisos de escritura.
10. Colisión de nombres.
11. Exportación parcialmente fallida.
12. Lote con muchas imágenes.
13. Lote con una sola imagen.
14. Todas omitidas.
15. Cambio de carpeta durante procesamiento.

#### Criterios de aceptación

- Cada estado tiene mensaje y acción clara.
- No hay pantallas en blanco sin explicación.
- No aparecen controles inútiles en estados imposibles.
- No se mezclan errores técnicos con mensajes de usuario final.

---

### Fase 10 — QA visual y pulido final

**Objetivo:** cerrar el acabado visual, no seguir iterando sin criterio.

#### Checklist visual

- Alineaciones horizontales y verticales revisadas.
- Espaciado consistente entre secciones.
- Bordes y radios coherentes.
- Contrastes correctos.
- Iconos consistentes en tamaño y estilo.
- Estados hover/focus/active definidos.
- Textos no seleccionables salvo contenido útil.
- No hay scroll global.
- No hay saltos de layout.
- La imagen se ajusta bien en varios formatos.
- Topbar, paneles y statusbar mantienen altura fija.
- El CTA principal siempre es reconocible.

#### Entregable

- Capturas antes/después.
- Lista de cambios realizados.
- Lista de deuda pendiente, si queda.
- Confirmación de criterios de aceptación.

---

## 18. Backlog priorizado

### P0 — Imprescindible antes de seguir añadiendo funciones

1. Crear tokens visuales y normalizar estilos base.
2. Cerrar layout macro sin scroll global ni saltos.
3. Rediseñar topbar y eliminar duplicidad de estados.
4. Rediseñar panel izquierdo para navegación clara.
5. Rediseñar header del visor y controles de zoom/navegación.
6. Reubicar selector de fondo y aclarar si afecta a preview o salida.
7. Plegar avanzado en `Ajustes`.
8. Rediseñar `Salida` como resultado/preflight, no formulario plano.
9. Corregir miniaturas y eliminar `Lista` repetido.
10. Añadir estados vacíos/error mínimos.

### P1 — Muy recomendable para versión funcional/pulida

1. Atajos de teclado básicos.
2. Feedback completo de exportación.
3. Preflight con colisiones/permisos/naming.
4. Tooltips en nombres truncados e iconos.
5. Estados de hover/focus/active consistentes.
6. Virtualización de miniaturas si hay lotes grandes.
7. Comparación original/procesada si ya existe soporte.
8. Acciones post-exportación: abrir carpeta, informe.

### P2 — Mejoras posteriores

1. Split view antes/después.
2. Panel de inspector desacoplado como drawer técnico.
3. Personalización de columnas/miniaturas.
4. Persistencia de preferencias de vista.
5. Modo compacto/amplio.
6. Temas visuales si realmente hacen falta.

---

## 19. Propuesta de estructura de pantalla final

### 19.1. Vista normal — Salida

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ [F] FlatShot    44 imágenes · 1 omitida    Bridge conectado    [Exportar 44] │
├───────────────┬──────────────────────────────────────────────┬───────────────┤
│ Lote          │ S670743599111.png · Procesada · Preview real │ Salida        │
│ 44 imágenes   │                 ← 5/44 →  Fit 100% − +        │ 44 listos     │
│ 1 omitida     │                                              │               │
│               │            ┌────────────────────┐            │ Variantes     │
│ Buscar...     │            │                    │            │ ✓ Web RGB230  │
│ Filtros       │            │      producto      │            │ JPG 1800×2400 │
│               │            │                    │            │               │
│ Miniaturas    │            └────────────────────┘            │ Preflight     │
│               │                                              │ ✓ Sin errores │
│ Diagnóstico   │ Fondo preview: RGB230 Blanco Transparente     │ ⚠ 1 omitida   │
├───────────────┴──────────────────────────────────────────────┴───────────────┤
│ Listo · Imagen 5/44 · Último escaneo completado                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 19.2. Vista normal — Ajustes

```text
┌───────────────┐
│ Ajustes       │
│ Preset        │
│ Luz cenital   │ Sin cambios
│               │
│ Principales   │
│ Opacidad  20  │
│ Blur      30  │
│ Distancia 25  │
│ Padding   10  │
│               │
│ Avanzado [>]  │
└───────────────┘
```

---

## 20. Errores de diseño que conviene evitar

1. **No añadir más paneles para solucionar ruido.** El problema no es falta de espacio, sino jerarquía.
2. **No convertir todo en tarjetas.** Las tarjetas sólo deben agrupar decisiones o entidades claras.
3. **No usar badges para todo.** Los badges pierden significado si cada dato tiene uno.
4. **No esconder la salida demasiado.** Exportar es el objetivo final; debe ser evidente.
5. **No ocultar problemas críticos en inspector.** El inspector es técnico; los bloqueos reales deben estar en preflight.
6. **No meter todos los controles avanzados en primer nivel.** Eso hace que la app parezca más compleja de lo que es.
7. **No rediseñar sólo colores.** El problema principal es jerarquía, estructura y densidad.
8. **No permitir cambios de layout por estados.** Es una app de producción; la estabilidad visual importa.
9. **No seguir añadiendo microcopy explicativo.** El producto debe explicarse por estructura.
10. **No mezclar modo mock y modo real sin señal clara.** Es una fuente de errores y desconfianza.

---

## 21. Criterios de calidad final

La UI estará suficientemente pulida cuando se cumplan estas condiciones:

1. Un usuario puede abrir la app y entender en menos de cinco segundos:
   - lote cargado,
   - imagen actual,
   - estado del sistema,
   - si puede exportar.
2. El visor central domina la pantalla.
3. Los paneles laterales parecen herramientas auxiliares, no competidores del visor.
4. No hay información repetida salvo que tenga una función clara.
5. El panel `Salida` permite entender el resultado final sin interpretar campos sueltos.
6. El panel `Ajustes` no intimida con controles técnicos innecesarios.
7. No hay saltos de layout al interactuar.
8. Los estados vacíos y errores parecen diseñados, no improvisados.
9. La app mantiene consistencia visual entre topbar, paneles, canvas y statusbar.
10. El acabado general deja de parecer prototipo y empieza a parecer herramienta interna lista para uso real.

---

## 22. Prompt de implementación para Codex

Usar este prompt cuando se quiera ejecutar el plan:

```text
Revisa la UI actual de FlatShot Desktop y aplica el plan de mejora UX/UI definido en `plan_mejora_ui_flatshot_extensivo.md`.

Objetivo principal:
Convertir la pantalla actual en una interfaz de producción mucho más pulida, estable, profesional y fácil de usar, sin añadir funcionalidades nuevas innecesarias ni romper el flujo real de bridge/exportación.

Prioridades obligatorias:
1. No añadir funciones nuevas antes de cerrar layout, jerarquía visual y consistencia.
2. Mantener app desktop/fullscreen, sin scroll global ni saltos de layout.
3. Separar claramente modo real, mock, bridge, inspector y estados de exportación.
4. Rediseñar topbar, panel izquierdo, visor central, panel derecho y statusbar según el plan.
5. Crear o consolidar tokens visuales: color, tipografía, espaciado, radios, sombras, alturas de control.
6. Reducir duplicidad de estados y microcopy innecesario.
7. Rediseñar `Salida` como tarjetas de resultado/preflight, no como formulario técnico plano.
8. Plegar parámetros avanzados en `Ajustes` y dejar visible sólo lo esencial.
9. Mejorar miniaturas, estados y selección sin repetir `Lista` en cada item.
10. Añadir estados vacíos/error imprescindibles.

Modo de trabajo:
- Localiza primero los archivos reales de UI. No asumas rutas si han cambiado.
- Haz una auditoría breve antes de tocar código.
- Trabaja por fases: tokens, shell, topbar, panel izquierdo, visor, panel derecho, statusbar, estados, QA.
- Después de cada fase, verifica visualmente que no hay scroll global ni layout shift.
- No rompas lógica real de exportación ni bridge.
- Si encuentras diferencias entre el plan y el estado real del repositorio, adapta el plan manteniendo sus principios.

Entrega final:
- Resumen de cambios realizados.
- Archivos modificados.
- Capturas o descripción de verificación visual.
- Lista de estados probados.
- Problemas pendientes y deuda técnica/UI que no se haya podido cerrar.
```

---

## 23. Checklist final para revisión manual

### Layout

- [ ] No hay scroll global vertical.
- [ ] No hay scroll horizontal.
- [ ] Panel izquierdo con scroll interno si hace falta.
- [ ] Panel derecho con scroll interno si hace falta.
- [ ] Topbar y statusbar mantienen altura fija.
- [ ] El visor central no cambia de tamaño al alternar tabs.

### Topbar

- [ ] Identidad clara.
- [ ] Estado de sistema único.
- [ ] CTA principal reconocible.
- [ ] Inspector secundario.
- [ ] Sin estados duplicados.

### Panel izquierdo

- [ ] Resumen de lote claro.
- [ ] Métricas sin ruido.
- [ ] Diagnóstico accionable.
- [ ] Filtros estables.
- [ ] Miniaturas legibles.
- [ ] Item seleccionado inequívoco.
- [ ] Nombres truncados con tooltip.

### Visor

- [ ] Nombre de archivo claro.
- [ ] Estado de imagen claro.
- [ ] Navegación 5/44 en un solo sitio.
- [ ] Zoom agrupado.
- [ ] Fondo activo claro.
- [ ] Imagen ajustada al máximo útil.

### Ajustes

- [ ] Preset claro.
- [ ] Estado `Sin cambios/Modificado` claro.
- [ ] Sliders alineados.
- [ ] Avanzado plegado por defecto.
- [ ] Reset con alcance claro.

### Salida

- [ ] Se entiende qué se exporta.
- [ ] Se entiende dónde se exporta.
- [ ] Se entiende el naming.
- [ ] Preflight visible.
- [ ] Avisos y errores accionables.
- [ ] CTA refleja estado real.

### Estados

- [ ] Sin lote.
- [ ] Carpeta vacía.
- [ ] Carpeta inválida.
- [ ] Bridge desconectado.
- [ ] Preview no disponible.
- [ ] Exportando.
- [ ] Exportación completada.
- [ ] Exportación fallida.

### Accesibilidad

- [ ] Focus visible.
- [ ] Contraste suficiente.
- [ ] Botones con tamaño mínimo.
- [ ] UI no seleccionable salvo contenido útil.
- [ ] Tooltips donde proceda.

---

## 24. Conclusión operativa

La app no necesita más decoración ni más controles visibles. Necesita una consolidación seria del sistema visual y de la arquitectura de pantalla. La pantalla actual ya contiene las piezas necesarias para convertirse en una herramienta útil, pero todavía hay demasiada fricción perceptiva: estados repetidos, controles técnicos expuestos, panel izquierdo saturado, salida demasiado formulario y visor central algo subordinado por elementos periféricos.

El orden correcto es:

1. Cerrar tokens y layout.
2. Limpiar jerarquía y estados.
3. Rehacer panel izquierdo y visor.
4. Convertir salida en preflight/variantes.
5. Plegar ajustes avanzados.
6. Pulir microinteracciones, errores y QA visual.

Sólo después de eso conviene seguir añadiendo capacidades. Si se continúa iterando sobre detalles aislados sin cerrar esta estructura, la app seguirá dando vueltas sobre el mismo punto.
