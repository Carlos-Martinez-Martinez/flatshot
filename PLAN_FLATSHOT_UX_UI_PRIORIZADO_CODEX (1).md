# Plan priorizado de rediseño UX/UI de FlatShot Desktop

**Documento para Codex**  
**Objetivo:** implementar, en orden lógico y por prioridad, una mejora profunda de la interfaz de FlatShot Desktop para que sea más clara, profesional, operativa y segura para usuarios no técnicos.

---

## 0. Instrucciones generales para Codex

Trabaja sobre el proyecto actual de FlatShot Desktop. Antes de modificar, inspecciona la estructura real del proyecto y localiza los archivos responsables de:

- shell/layout principal;
- panel izquierdo de lote;
- galería de imágenes;
- visor central;
- panel derecho/inspector;
- modal de formatos de salida;
- estados de escaneo;
- exportación;
- estilos globales, variables CSS o sistema visual.

Si la app está construida con HTML/CSS/JS plano, aplica los cambios en los archivos existentes. Si hay componentes, módulos o framework, respeta la arquitectura actual. **No migres de tecnología salvo que el proyecto ya lo haga necesario.**

### Reglas de ejecución

1. Implementa por fases, en el orden de este documento.
2. Después de cada fase, ejecuta la app y valida visualmente.
3. No rompas el flujo funcional actual: selección de carpeta, escaneo, revisión, ajustes, exportación.
4. No elimines lógica existente sin sustituirla por una alternativa equivalente o mejor.
5. No añadas nuevas dependencias salvo que sean estrictamente necesarias.
6. Evita cambios estéticos aislados sin conexión con el sistema visual global.
7. Centraliza textos, etiquetas, estados y clases visuales siempre que sea razonable.
8. Mantén los controles pensados para usuario no técnico.
9. Prioriza claridad operativa sobre densidad de opciones.
10. Documenta al final los archivos modificados y qué se ha cambiado.

---

## 1. Diagnóstico sintético

La interfaz actual ya tiene una estructura base útil: panel de lote a la izquierda, galería, visor central y ajustes a la derecha. El problema no es la distribución general, sino la **jerarquía operativa** y la **fragmentación del lenguaje visual**.

Problemas principales detectados:

- Hay demasiados datos repartidos en varias zonas.
- El usuario no entiende de forma inmediata cuál es el siguiente paso.
- Se mezclan ajustes de lote, ajustes de imagen, ajustes de preset/formato y configuración general.
- La palabra “Ajustes” aparece con varios significados.
- Se repiten conceptos: avisos, salida, estado del lote, escaneo, etc.
- Los números no tienen una taxonomía clara: 44 listas, 44 imágenes, 45 archivos, 1 omitida, 1 aviso.
- El visor central podría aprovechar mejor el espacio para producto vertical.
- La gestión de presets ocupa demasiado espacio en la pantalla principal.
- El modal de formatos de salida necesita una vista previa clara del resultado.
- El estado de escaneo repite información y muestra controles que todavía no sirven.
- El color verde se usa para demasiados significados.
- La interfaz sigue pareciendo parcialmente “interna” o “en construcción”.

---

## 2. Principio de diseño final

La pantalla principal debe responder en menos de cinco segundos a estas preguntas:

1. ¿Qué carpeta o entrada está cargada?
2. ¿Cuántos archivos se han encontrado?
3. ¿Cuántas imágenes se pueden exportar?
4. ¿Hay avisos o problemas?
5. ¿Qué formato de salida se aplicará?
6. ¿Dónde se guardarán los archivos?
7. ¿Cuál es el siguiente botón que debo pulsar?

Todo lo demás debe quedar en segundo nivel: detalle técnico, gestión avanzada de formatos, diagnóstico, parámetros finos, restauración, exportación/importación de presets, etc.

---

# FASE 1 — Modelo de estados, vocabulario y jerarquía funcional

Esta fase es prioritaria porque todo lo demás depende de que la app use un lenguaje consistente.

---

## 1.1. Definir una taxonomía única de conteos

### Problema

Actualmente aparecen términos y números con posible ambigüedad:

- `44 listas`
- `44 imágenes`
- `45 archivos`
- `1 omitida`
- `1 aviso`
- `Correctas 44`
- `Avisos 1`
- `Omitidas 1`

El usuario puede no saber si hay 44, 45 o 46 elementos, ni si los avisos están incluidos dentro de las imágenes correctas.

### Cambio requerido

Unificar internamente y visualmente estos conceptos:

| Concepto | Significado |
|---|---|
| Archivos encontrados | Todo lo detectado en la carpeta de entrada. |
| Imágenes válidas | Archivos de imagen que la app puede leer/procesar. |
| Imágenes exportables | Imágenes que pueden exportarse. Puede incluir imágenes con avisos no bloqueantes. |
| Imágenes listas | Imágenes exportables sin avisos pendientes. |
| Imágenes con aviso | Imágenes exportables pero que requieren revisión. |
| Archivos omitidos | Archivos ignorados, no compatibles, duplicados o descartados por regla. |
| Avisos bloqueantes | Problemas que impiden exportar una imagen o el lote. |
| Avisos no bloqueantes | Problemas que conviene revisar pero que no impiden exportar. |

### Acciones

- Crear una función centralizada que calcule todos los conteos del lote.
- Evitar cálculos duplicados en cada componente.
- Renombrar visualmente:
  - `44 listas` → `44 exportables` o `44 imágenes exportables`.
  - `Correctas` → `Listas`.
  - `Avisos` → `Con aviso`.
  - `Omitidas` → `Omitidas` solo si realmente aparecen como elementos consultables.
- Si los archivos omitidos no aparecen en la galería, no deben formar parte de `Todas`.

### Criterios de aceptación

- En toda la app, los conteos tienen el mismo significado.
- No aparece `listas` como sustantivo principal.
- El usuario puede distinguir entre archivos encontrados, imágenes exportables, avisos y omitidas.
- Los filtros de galería y el resumen del lote no se contradicen.

---

## 1.2. Crear un modelo de estados de pantalla

### Problema

La app muestra muchos elementos aunque no todos sean válidos en cada fase. Por ejemplo, durante el escaneo aparecen filtros, búsqueda o paneles de salida con datos incompletos.

### Cambio requerido

Definir estados principales de la pantalla:

| Estado | Descripción | Acción principal |
|---|---|---|
| `idle` | No hay carpeta seleccionada. | Seleccionar carpeta |
| `scanning` | La app está leyendo la carpeta. | Sin acción o Cancelar si existe |
| `scan_empty` | Se ha leído la carpeta pero no hay imágenes válidas. | Elegir otra carpeta |
| `ready_clean` | Hay imágenes exportables sin avisos. | Exportar imágenes |
| `ready_with_warnings` | Hay imágenes exportables con avisos. | Revisar avisos |
| `ready_with_blockers` | Hay problemas que impiden exportar. | Resolver problemas |
| `export_confirm` | El usuario va a exportar y hay riesgos/avisos/sobrescrituras. | Confirmar exportación |
| `exporting` | Exportación en curso. | Cancelar si es posible |
| `export_done` | Exportación terminada. | Abrir carpeta de salida |
| `error` | Error de lectura, escritura o configuración. | Ver detalle / Reintentar |

### Acciones

- Implementar una función tipo `getAppState(lotState)` o equivalente.
- El header, el panel izquierdo, el panel derecho y los botones deben derivar de ese estado.
- Evitar que cada zona decida por separado qué mostrar.

### Criterios de aceptación

- El botón principal cambia según el estado.
- No se muestran controles inútiles durante escaneo.
- Si hay avisos, la acción principal no debe ser directamente `Exportar 44`, sino `Revisar avisos`.
- Si no hay imágenes, no aparecen filtros con `0` como si fueran una galería funcional.

---

## 1.3. Centralizar textos y etiquetas

### Problema

Hay términos técnicos o ambiguos:

- Preset
- Naming
- Técnico
- Motor
- Parámetros finos
- Diagnóstico
- Ruta
- RGB230
- Ajustes usado con varios significados

### Cambio requerido

Crear una tabla centralizada de copy o, como mínimo, revisar todos los textos visibles.

### Sustituciones recomendadas

| Actual | Nuevo |
|---|---|
| Preset actual | Ajuste activo / Formato activo, según contexto |
| Presets disponibles | Formatos guardados |
| Acciones de preset | Gestionar formato |
| Naming | Nombre de archivo |
| Ruta o subcarpeta | Carpeta de salida |
| RGB230 | Gris claro · RGB 230 |
| Técnico | Avanzado |
| Motor y parámetros finos | Procesamiento avanzado |
| Ver diagnóstico | Ver detalle técnico |
| Ajustes, cuando sea global | Configuración |
| Ajustes, cuando sea salida | Salida |
| Ajustes, cuando sea imagen | Imagen actual |

### Criterios de aceptación

- El usuario no técnico entiende las acciones principales sin saber qué es un preset.
- `Ajustes` deja de usarse para tres cosas distintas.
- Los términos técnicos quedan en segundo nivel o acompañados de ejemplo.

---

# FASE 2 — Header global y acción principal

---

## 2.1. Rediseñar el header como resumen de estado y acción

### Problema

El header actual muestra `FlatShot`, estado tipo `PNG · 1 aviso`, botón `Exportar 44` y `Ajustes`. Es limpio, pero no guía lo suficiente.

### Cambio requerido

El header debe convertirse en la fuente rápida de estado:

Ejemplo con avisos:

```text
FlatShot
PNG · 45 archivos encontrados · 44 exportables · 1 aviso

[Revisar aviso] [Exportar igualmente] [Configuración]
```

Ejemplo sin avisos:

```text
FlatShot
PNG · 45 archivos encontrados · 44 exportables · Sin avisos

[Exportar 44 imágenes] [Configuración]
```

Ejemplo escaneando:

```text
FlatShot
Leyendo carpeta…

[Escaneando…] [Configuración]
```

### Acciones

- Mostrar resumen compacto del lote en una sola línea.
- Hacer que la acción principal dependa del estado.
- Cambiar `Ajustes` global por `Configuración`.
- No mostrar `Exportar 44` como acción dominante si hay avisos pendientes.
- Si se permite exportar con avisos, usar una acción secundaria: `Exportar igualmente`.

### Criterios de aceptación

- El usuario entiende el estado del lote sin mirar los paneles laterales.
- La acción principal es coherente con el riesgo del estado actual.
- El header no repite información innecesaria, solo resume.

---

## 2.2. Definir matriz de acciones principales

Implementar esta lógica:

| Estado | Botón principal | Botón secundario |
|---|---|---|
| `idle` | Seleccionar carpeta | Configuración |
| `scanning` | Escaneando… | Cancelar, si es posible |
| `scan_empty` | Elegir otra carpeta | Ver detalle |
| `ready_clean` | Exportar N imágenes | Cambiar salida |
| `ready_with_warnings` | Revisar avisos | Exportar igualmente |
| `ready_with_blockers` | Resolver problemas | Ver detalle |
| `exporting` | Exportando… | Cancelar, si es posible |
| `export_done` | Abrir carpeta de salida | Exportar de nuevo |
| `error` | Reintentar | Ver detalle técnico |

### Criterios de aceptación

- No hay botones ambiguos.
- El botón principal nunca invita a saltarse una revisión importante salvo que esté claramente marcado como secundario.
- Los botones deshabilitados explican por qué están deshabilitados mediante tooltip o texto auxiliar.

---

# FASE 3 — Panel izquierdo: resumen operativo del lote

---

## 3.1. Convertir el panel izquierdo en un resumen por bloques

### Problema

La columna izquierda mezcla demasiados niveles: entrada, estado, salida, destino, avisos y siguiente acción. Parece un informe técnico.

### Cambio requerido

Estructurar en tres bloques fijos:

1. Entrada
2. Estado
3. Salida

### Propuesta visual

```text
LOTE
44 imágenes exportables
1 aviso

ENTRADA
PNG
45 archivos encontrados
1 archivo omitido

[ Cambiar carpeta ] [ Reescanear ]

ESTADO
✓ 43 listas
⚠ 1 con aviso
− 1 omitida

[ Revisar aviso ]

SALIDA
JPG · 1800 × 2400
Gris claro · RGB 230
Destino: _SALIDA_PRO

[ Cambiar salida ]
```

### Acciones

- Sacar textos largos del panel izquierdo.
- Mantener solo información de alto nivel.
- Mostrar detalles técnicos bajo enlaces o acordeones secundarios.
- Evitar que la tarjeta de estado ocupe demasiado alto.
- Si no hay avisos, no reservar un bloque grande para avisos.

### Criterios de aceptación

- El panel izquierdo se puede leer de arriba abajo en pocos segundos.
- Entrada, estado y salida no se mezclan.
- El panel no repite exactamente lo mismo que el header.
- El estado del lote no parece un log técnico.

---

## 3.2. Mejorar microcopy del panel izquierdo

### Cambios concretos

Reemplazar:

```text
1 aviso para revisar
44 imágenes preparadas; revisa la galería antes de procesar.
```

Por algo más operativo:

```text
1 imagen requiere revisión.
Puedes revisarla antes de exportar.
```

Reemplazar:

```text
Siguiente
Revisar avisos o procesar 44
```

Por estado contextual:

```text
Siguiente paso
Revisar aviso
```

O, si no hay avisos:

```text
Siguiente paso
Exportar 44 imágenes
```

### Criterios de aceptación

- No aparece `procesar` si la acción real se llama `exportar`.
- No hay frases largas innecesarias.
- El texto dice qué hacer, no cómo funciona internamente.

---

# FASE 4 — Galería de imágenes

---

## 4.1. Reordenar filtros según utilidad real

### Problema

Los filtros aparecen como:

```text
Todas 44
Correctas 44
Avisos 1
Omitidas 1
```

El orden favorece `Todas`, pero si hay avisos, el usuario debería poder llegar primero a ellos.

### Cambio requerido

Cuando hay avisos:

```text
Con aviso 1
Listas 43
Todas 44
Omitidas 1
```

Cuando no hay avisos:

```text
Todas 44
Listas 44
Omitidas 1
```

Si las omitidas no son imágenes visibles, moverlas a `Detalle del lote` y no mezclarlas con la galería.

### Acciones

- Cambiar `Correctas` por `Listas`.
- Priorizar `Con aviso` cuando `warnings > 0`.
- Usar badges de contador en vez de meter el número en el texto.
- Mantener los filtros compactos.

### Criterios de aceptación

- Con avisos, el filtro de avisos es fácil de encontrar.
- No hay categorías semánticamente contradictorias.
- Los filtros no aparecen activos con `0` durante el escaneo.

---

## 4.2. Rediseñar tarjeta de miniatura

### Problema

La tarjeta de miniatura muestra nombre completo, tamaño, punto verde y miniatura. El punto verde no se entiende sin leyenda. La selección funciona, pero podría ser más clara.

### Cambio requerido

Cada tarjeta debe tener:

```text
[Miniatura]

S67196217011
PNG · 1.6 MB
```

Estados:

```text
✓ Lista
⚠ Aviso
− Omitida
```

### Acciones

- Ocultar `.png` en el título visible si el tipo ya se muestra como metadata.
- Mantener nombre completo en tooltip o detalle.
- Hacer que la tarjeta seleccionada tenga:
  - borde visible;
  - fondo sutil;
  - indicador no dependiente solo del color;
  - estado textual o iconográfico.
- Sustituir el punto verde por un estado comprensible.
- Añadir tooltip breve al estado si se mantiene un icono.

### Criterios de aceptación

- La miniatura seleccionada se reconoce sin esfuerzo.
- El usuario entiende si una imagen está lista o tiene aviso.
- No se depende solo del color verde.

---

## 4.3. Mejorar búsqueda de imágenes

### Problema

La búsqueda está presente, pero su alcance no queda del todo claro.

### Cambio requerido

Placeholder recomendado:

```text
Buscar por nombre o referencia…
```

### Acciones

- Buscar por nombre completo, nombre sin extensión y referencia.
- Si el sistema detecta estructura de código, permitir búsqueda parcial por fragmentos.
- Mostrar estado vacío de búsqueda:

```text
No hay imágenes que coincidan con “...”
```

- Añadir acción:

```text
Limpiar búsqueda
```

### Criterios de aceptación

- La búsqueda no parece un campo decorativo.
- El usuario entiende qué puede buscar.
- Si no hay resultados, se explica por qué.

---

## 4.4. Preparar vista densa o lista para lotes grandes

### Cambio requerido

Añadir, aunque sea en una segunda iteración dentro de la misma fase, un modo alternativo:

- `Miniaturas`
- `Lista`

La vista de lista puede mostrar:

```text
Referencia | Estado | Tamaño | Avisos
```

### Criterios de aceptación

- Con muchos archivos, la app no obliga a depender solo de miniaturas grandes.
- El selector de vista no debe ocupar mucho ni complicar el flujo.

---

# FASE 5 — Visor central

---

## 5.1. Aprovechar mejor el espacio para producto vertical

### Problema

El visor tiene mucho espacio vacío alrededor del producto. Para imágenes verticales de producto, el modo por defecto debería aprovechar mejor la altura.

### Cambio requerido

Implementar modos de visualización explícitos:

- `Encajar`
- `Altura`
- `Anchura`
- `100 %`

El modo recomendado por defecto para producto vertical es `Altura`, siempre que no recorte imagen.

### Acciones

- Ajustar cálculo de zoom para que el producto ocupe más alto útil.
- Mantener margen visual razonable, pero no excesivo.
- No permitir que la imagen quede cortada sin que el usuario lo haya elegido.
- Recordar el último modo de visualización durante la sesión.

### Criterios de aceptación

- Una camiseta vertical no aparece perdida en el centro del lienzo.
- El usuario puede alternar fácilmente entre encajar y 100 %.
- El zoom y el modo activo son comprensibles.

---

## 5.2. Rediseñar la toolbar del visor

### Problema

Los controles actuales son correctos pero algo ambiguos:

```text
< 23 / 44 > Ajustar 1:1 - 89% +
```

### Cambio requerido

Propuesta:

```text
[‹] 23 / 44 [›]   [Encajar] [Altura] [100 %]   [−] 89 % [+]
```

O versión compacta:

```text
‹ 23 / 44 ›   Vista: Altura   − 89 % +
```

### Acciones

- Cambiar `Ajustar` por `Encajar`.
- Cambiar `1:1` por `100 %`.
- Mostrar modo activo de manera visible.
- Añadir tooltip a cada control.
- Evitar que la toolbar parezca un conjunto de botones técnicos sin contexto.

### Criterios de aceptación

- El usuario entiende qué significa cada control.
- El modo activo no se confunde con una acción.
- La navegación anterior/siguiente es clara.

---

## 5.3. Añadir interacción de teclado y ratón

### Acciones

Implementar o revisar:

- Flecha izquierda: imagen anterior.
- Flecha derecha: imagen siguiente.
- Doble clic en visor: alternar entre `Encajar/Altura` y `100 %`.
- Rueda del ratón con modificador, si procede: zoom.
- `F`: encajar.
- `1`: 100 %.
- `Esc`: salir de modal o cancelar foco.
- `Enter`: abrir detalle o confirmar acción enfocada, según contexto.

### Criterios de aceptación

- El usuario puede revisar imágenes rápidamente sin depender solo del ratón.
- Los atajos no interfieren con campos de texto activos.
- Hay tooltips o ayuda mínima de atajos en configuración o ayuda.

---

## 5.4. Mostrar contexto de salida sobre el visor

### Problema

El usuario no siempre sabe si está viendo el fondo original, el fondo de salida o una vista previa.

### Cambio requerido

Añadir una etiqueta discreta en el visor:

```text
Vista previa: JPG · 1800 × 2400 · fondo gris RGB 230
```

O:

```text
Fondo de salida: gris claro RGB 230
```

### Acciones

- Mostrar overlay inferior o superior discreto.
- No tapar el producto.
- Permitir cambiar vista de fondo:
  - Fondo final
  - Transparencia
  - Blanco
  - Gris
  - Negro

### Criterios de aceptación

- El usuario distingue entre transparencia original y fondo final.
- La vista previa de salida está conectada con el formato activo.

---

# FASE 6 — Panel derecho / Inspector

---

## 6.1. Separar Revisión, Salida y Avisos

### Problema

El panel derecho mezcla:

- preset actual;
- presets disponibles;
- acciones de preset;
- aspecto;
- vista;
- técnico;
- imagen seleccionada.

Esto hace que el usuario no sepa qué afecta al lote, a la imagen o al formato.

### Cambio requerido

Reorganizar las pestañas en:

```text
Revisión | Salida | Avisos
```

Si se mantiene `Ajustes`, debe referirse solo a configuración avanzada, no al flujo principal.

### Estructura recomendada

#### Revisión

```text
Imagen seleccionada
S67196217011.png

Estado
Lista para exportar

Salida prevista
S67196217011_PRO.jpg

Avisos
Sin avisos
```

#### Salida

```text
Formato activo
INSIDE Web

JPG · 1800 × 2400
Fondo gris claro · RGB 230
Destino: _SALIDA_PRO
Nombre: original + _PRO

[Cambiar formato]
```

#### Avisos

```text
1 aviso en el lote

S67196217011.png
Motivo: ...
[Ir a imagen] [Marcar revisado]
```

### Criterios de aceptación

- El panel derecho ya no es un cajón de ajustes.
- El usuario sabe qué pertenece a la imagen actual y qué pertenece al lote.
- La pestaña `Salida` es la fuente principal de configuración de exportación.

---

## 6.2. Sacar la gestión completa de presets de la pantalla principal

### Problema

La pantalla principal muestra demasiadas acciones de administración:

- Guardar
- Exportar presets
- Eliminar
- Restaurar
- Listo
- lista de presets

Esto no debería estar siempre visible durante la revisión.

### Cambio requerido

En pantalla principal, mostrar solo:

```text
Formato activo
INSIDE Web
JPG · 1800 × 2400 · fondo gris

[Cambiar]
```

Al pulsar `Cambiar`, abrir selector o modal.

La gestión avanzada debe ir dentro de:

```text
Gestionar formatos de salida
```

### Acciones

- Retirar botones de administración de presets del panel principal.
- Mover `Eliminar`, `Restaurar`, `Exportar presets` a modal o menú secundario.
- Mantener visible solo lo necesario para aplicar/cambiar formato.

### Criterios de aceptación

- La pantalla principal no parece un gestor de presets.
- Las acciones destructivas no están a la vista durante tareas normales.
- El usuario puede cambiar formato sin entrar en opciones técnicas.

---

## 6.3. Mostrar siempre la imagen seleccionada en contexto

### Problema

La imagen seleccionada aparece en el visor y en la galería, pero el panel derecho no la explota suficientemente.

### Cambio requerido

El panel `Revisión` debe iniciar con la imagen seleccionada:

```text
S67196217011.png
Lista para exportar
Sin avisos
```

Y debajo:

```text
Resultado previsto
S67196217011_PRO.jpg
```

### Criterios de aceptación

- El usuario no pierde contexto al mirar al panel derecho.
- La salida prevista se entiende por imagen, no solo por lote.

---

# FASE 7 — Modal de formatos de salida

---

## 7.1. Renombrar y redefinir el modal

### Problema

El modal actual se llama `Formatos de salida`, lo cual está bien, pero dentro conserva términos técnicos como `Naming`, y las acciones `Guardar formato`, `Usar en este lote`, `Cerrar` pueden ser ambiguas.

### Cambio requerido

El modal debe responder a:

1. Qué formato estoy editando.
2. Qué salida genera.
3. Dónde guarda los archivos.
4. Cómo se llamará el archivo final.
5. Si los cambios se guardan, se aplican al lote o ambas cosas.

### Estructura recomendada

```text
Formatos de salida

[Lista de formatos guardados]

INSIDE Web
Activo en este lote

Resumen
JPG · 1800 × 2400 · Fondo gris claro RGB 230
Destino: _SALIDA_PRO
Nombre: original + _PRO

Archivo
Tipo: JPG
Fondo: Gris claro RGB 230

Tamaño
Anchura: 1800
Altura: 2400

Destino
Ubicación: junto al origen
Subcarpeta: _SALIDA_PRO

Nombre de archivo
Sufijo: _PRO
Vista previa: S67196217011_PRO.jpg

[Cancelar] [Guardar cambios] [Aplicar al lote]
```

### Criterios de aceptación

- El modal se entiende sin saber qué es un preset.
- El usuario ve una vista previa concreta.
- El usuario distingue guardar formato de aplicar formato.

---

## 7.2. Añadir vista previa de exportación

### Cambio requerido

Incluir un bloque visible:

```text
Ejemplo de exportación

Original:
S67196217011.png

Resultado:
_SALIDA_PRO/S67196217011_PRO.jpg

Formato:
JPG · 1800 × 2400 · fondo gris claro RGB 230
```

### Acciones

- Usar la imagen seleccionada actual como ejemplo, si existe.
- Si no hay imagen seleccionada, usar ejemplo genérico:
  - `imagen_original.png`
  - `imagen_original_PRO.jpg`
- Actualizar la vista previa al cambiar sufijo, destino, formato o extensión.

### Criterios de aceptación

- Cualquier usuario puede anticipar el resultado antes de aplicar.
- La vista previa se actualiza en tiempo real.
- No hay que interpretar `{original}{suffix}` sin ayuda.

---

## 7.3. Rediseñar la lista de formatos guardados

### Problema

Los nombres largos se cortan y los formatos parecidos son difíciles de distinguir.

### Cambio requerido

Cada formato debe mostrarse así:

```text
INSIDE Web
JPG · 1800 × 2400 · gris claro
En uso
```

Otro ejemplo:

```text
PNG transparente
PNG · 1800 × 2400 · transparente
Salida: _SALIDA_PRO
```

### Acciones

- Permitir que la tarjeta tenga dos o tres líneas.
- Evitar truncados agresivos.
- Mostrar estado `En uso` solo para el formato activo.
- Si hay muchos formatos, añadir búsqueda sencilla.

### Criterios de aceptación

- Se distinguen formatos similares.
- El formato activo se reconoce sin depender solo del color.

---

## 7.4. Reordenar acciones destructivas

### Problema

`Eliminar` aparece cerca de `Nuevo` y `Duplicar`. Es demasiado accesible.

### Cambio requerido

Mover acciones destructivas a un menú secundario:

```text
Más opciones
- Duplicar formato
- Exportar formatos
- Restaurar valores
- Eliminar formato…
```

### Confirmación de eliminación

```text
Eliminar formato “INSIDE Web”

Este formato se eliminará de los formatos guardados.
No se eliminarán imágenes ni exportaciones anteriores.

[Cancelar] [Eliminar formato]
```

### Criterios de aceptación

- No se puede eliminar un formato por accidente.
- Las acciones destructivas no compiten visualmente con guardar/aplicar.
- La confirmación explica alcance y consecuencias.

---

## 7.5. Revisar botones finales del modal

### Problema

`Guardar formato`, `Usar en este lote` y `Cerrar` pueden generar dudas.

### Cambio requerido

Usar:

```text
[Cancelar] [Guardar cambios] [Aplicar al lote]
```

Si hay cambios sin guardar y se pulsa aplicar:

```text
[Guardar y aplicar]
```

### Lógica recomendada

- `Cancelar`: cierra sin aplicar cambios no guardados.
- `Guardar cambios`: guarda el formato editado, no necesariamente lo aplica al lote.
- `Aplicar al lote`: usa ese formato en el lote actual.
- `Guardar y aplicar`: aparece si hay cambios pendientes.

### Criterios de aceptación

- No hay dudas sobre si los cambios se pierden.
- Si el usuario intenta cerrar con cambios sin guardar, se le avisa.
- Los botones mantienen posición estable.

---

# FASE 8 — Estado de escaneo, vacíos y errores

---

## 8.1. Rediseñar pantalla de escaneo

### Problema

Durante el escaneo se repite la misma información en varias zonas:

- panel izquierdo;
- centro;
- panel derecho;
- barra inferior.

Además, se muestra `0 %`, que puede parecer bloqueo si no hay progreso real.

### Cambio requerido

Estado central único y claro:

```text
Escaneando carpeta

Buscando imágenes PNG…
Archivos encontrados: 28
Imágenes válidas: 27
Omitidas: 1
```

Si no hay progreso real:

```text
Leyendo archivos…
```

No mostrar porcentaje falso.

Si hay progreso real:

```text
28 de 45 archivos revisados
62 %
```

### Acciones

- Ocultar filtros de galería durante escaneo.
- Sustituir galería por skeleton o mensaje de preparación.
- Reducir el panel derecho a estado de preparación o esconderlo si no aporta.
- No mostrar datos definitivos hasta terminar.

### Criterios de aceptación

- El usuario sabe que la app está trabajando.
- No hay cuatro mensajes distintos diciendo lo mismo.
- No se muestran controles inútiles durante escaneo.

---

## 8.2. Crear estados vacíos específicos

### Estados requeridos

#### Sin carpeta seleccionada

```text
Selecciona una carpeta para empezar

FlatShot buscará imágenes compatibles y preparará el lote para exportación.

[Seleccionar carpeta]
```

#### Carpeta sin imágenes compatibles

```text
No se han encontrado imágenes compatibles

Formatos admitidos: PNG, JPG, JPEG.

[Elegir otra carpeta]
```

#### Todo omitido

```text
No hay imágenes exportables

Todos los archivos encontrados fueron omitidos.
[Ver archivos omitidos] [Elegir otra carpeta]
```

#### Error de lectura

```text
No se pudo leer la carpeta

Comprueba que la ruta existe y que tienes permisos de lectura.
[Reintentar] [Elegir otra carpeta] [Ver detalle técnico]
```

### Criterios de aceptación

- Cada estado vacío tiene una causa y una acción.
- No se deja la pantalla en blanco.
- No se muestran filtros o paneles sin contenido real.

---

## 8.3. Simplificar la barra inferior

### Problema

La barra inferior muestra información repetida como:

```text
Escaneando · Escaneando ruta
```

### Cambio requerido

Usarla solo para información útil:

```text
Entrada: C:\...\producto_png · 44 imágenes exportables · Última lectura: hace 12 s
```

Durante escaneo:

```text
Leyendo C:\...\producto_png · 28 archivos revisados
```

Si no aporta, reducirla o hacerla menos prominente.

### Criterios de aceptación

- La barra inferior no repite el mensaje central.
- Aporta ruta, estado técnico o último evento.
- No compite con la acción principal.

---

# FASE 9 — Exportación y prevención de errores

---

## 9.1. Confirmación inteligente antes de exportar

### Problema

El usuario debería saber exactamente qué va a pasar antes de exportar, sobre todo si hay avisos, omitidas o riesgo de sobrescritura.

### Cambio requerido

Al pulsar exportar, si existe cualquier riesgo, mostrar modal:

```text
Exportar lote

44 imágenes se exportarán.
Formato: JPG · 1800 × 2400 · fondo gris claro.
Destino: _SALIDA_PRO.
1 imagen tiene aviso.
1 archivo fue omitido.

[Cancelar] [Exportar 44 imágenes]
```

Si no hay riesgos, se puede exportar directamente.

### Riesgos que deben disparar confirmación

- Hay avisos pendientes.
- Hay archivos omitidos.
- Hay archivos existentes en destino.
- Hay rutas inválidas.
- Hay formato incompleto.
- Hay imágenes con dimensiones inferiores al objetivo, si aplica.
- Hay parámetros avanzados no estándar.

### Criterios de aceptación

- El usuario no exporta a ciegas.
- Los avisos no bloqueantes se explican como no bloqueantes.
- Los bloqueantes impiden exportar hasta resolverse.

---

## 9.2. Gestión de sobrescritura

### Cambio requerido

Si existen archivos con el mismo nombre en la salida:

```text
Ya existen 12 archivos en la carpeta de salida.

¿Qué quieres hacer?

( ) Sobrescribir archivos existentes
( ) Crear copias numeradas
( ) Cancelar exportación

[Continuar]
```

### Criterios de aceptación

- La app no sobrescribe sin consentimiento.
- La opción seleccionada queda clara.
- El comportamiento se aplica de forma consistente.

---

## 9.3. Estado de exportación y finalización

### Durante exportación

```text
Exportando imágenes

23 de 44 exportadas
S67196217011_PRO.jpg
```

### Al finalizar

```text
Exportación completada

44 imágenes exportadas correctamente.
Destino: C:\...\_SALIDA_PRO

[Abrir carpeta de salida] [Exportar de nuevo]
```

### Si hay errores parciales

```text
Exportación completada con errores

41 exportadas
3 con error

[Ver errores] [Abrir carpeta]
```

### Criterios de aceptación

- Hay progreso real o estado indeterminado honesto.
- El usuario sabe dónde están los archivos.
- Los errores parciales son consultables.

---

# FASE 10 — Sistema visual y componentes

Esta fase puede empezar en paralelo a fases anteriores, pero debe consolidarse después de fijar estados y estructura.

---

## 10.1. Crear tokens visuales

### Problema

La interfaz tiene elementos correctos pero no parece un sistema completamente cerrado. Hay variaciones de padding, bordes, colores y jerarquías.

### Cambio requerido

Crear variables CSS o tokens equivalentes.

### Tokens mínimos

```css
:root {
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 24px;
  --space-6: 32px;

  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;
  --radius-xl: 18px;

  --font-size-xs: 11px;
  --font-size-sm: 12px;
  --font-size-md: 14px;
  --font-size-lg: 18px;
  --font-size-xl: 24px;

  --surface-app: #f6f7f8;
  --surface-panel: #ffffff;
  --surface-muted: #f3f5f6;
  --border-subtle: rgba(15, 23, 42, 0.10);

  --text-primary: #0f172a;
  --text-secondary: #475569;
  --text-muted: #64748b;

  --semantic-primary: #0f8f78;
  --semantic-warning: #b7791f;
  --semantic-danger: #c2410c;
  --semantic-info: #2563eb;
}
```

Ajustar valores a la paleta real del proyecto, pero mantener roles.

### Criterios de aceptación

- No hay tamaños/paddings inventados en cada componente.
- Los colores tienen rol semántico.
- La interfaz respira igual en todas las zonas.

---

## 10.2. Definir escala tipográfica

### Reglas

```text
Título de pantalla: 18–20 px / semibold
Título de panel: 12–13 px / uppercase discreto / medium
Valor importante: 18–24 px / semibold
Texto normal: 13–14 px
Texto auxiliar: 12 px
Metadatos: 11–12 px
```

### Acciones

- Revisar títulos de panel.
- Revisar nombres de archivo.
- Revisar botones.
- Revisar textos secundarios.
- Evitar mayúsculas excesivas en tarjetas informativas.

### Criterios de aceptación

- La información importante se lee antes.
- Los metadatos no compiten con títulos.
- No hay tamaños descompensados entre paneles.

---

## 10.3. Revisar color semántico

### Problema

El verde se usa para todo: acción principal, selección, estado correcto, preset activo, spinner, tabs. Pierde significado.

### Cambio requerido

Asignar roles:

| Rol | Uso |
|---|---|
| Primario | Acción principal: exportar, aplicar |
| Selección | Imagen activa, pestaña activa, foco |
| Éxito/listo | Estado correcto |
| Aviso | Requiere revisión |
| Peligro | Eliminar, error destructivo |
| Neutro | Información secundaria |

### Acciones

- No usar el mismo verde para acción principal, selección y estado si genera confusión.
- Usar ámbar para avisos.
- Usar rojo/naranja solo para errores o destructivo.
- Usar azul/neutro para selección si ayuda a diferenciar del estado correcto.
- Asegurar contraste suficiente.

### Criterios de aceptación

- El usuario distingue visualmente acción, selección, aviso y peligro.
- Los avisos destacan más que ahora.
- El color no es el único indicador.

---

## 10.4. Componentes base

Crear o consolidar componentes/clases reutilizables:

### Layout

- `AppShell`
- `TopBar`
- `LeftSummaryPanel`
- `GalleryPanel`
- `ViewerPanel`
- `InspectorPanel`
- `StatusBar`

### UI

- `Button`
  - primary
  - secondary
  - ghost
  - danger
  - icon
- `StatusBadge`
  - ready
  - warning
  - error
  - processing
  - muted
- `SummaryBlock`
- `MetricRow`
- `ThumbnailCard`
- `InspectorSection`
- `SegmentedControl`
- `ModalShell`
- `EmptyState`
- `ProgressState`

### Criterios de aceptación

- No hay estilos duplicados innecesariamente.
- Los componentes se comportan de forma consistente.
- Nuevas pantallas futuras podrán reutilizar el sistema.

---

# FASE 11 — Accesibilidad y usabilidad fina

---

## 11.1. Estados de foco y navegación por teclado

### Acciones

- Añadir foco visible a botones, inputs, miniaturas y tabs.
- Asegurar que `Tab` recorre la interfaz en orden lógico.
- Permitir cerrar modales con `Esc`.
- Evitar que los atajos se activen mientras se escribe en inputs.
- Revisar `aria-label` o texto accesible en botones de icono.

### Criterios de aceptación

- Se puede usar la app razonablemente con teclado.
- El foco no desaparece.
- Los botones de icono tienen nombre accesible.

---

## 11.2. No depender solo del color

### Acciones

- Añadir iconos o texto para:
  - lista;
  - aviso;
  - error;
  - omitida;
  - seleccionada.
- Mantener contraste suficiente en badges y botones.
- Evitar puntos verdes sin explicación.

### Criterios de aceptación

- Un usuario con dificultad para distinguir colores entiende los estados.
- Los estados son comprensibles en blanco y negro.

---

## 11.3. Revisar tamaños clicables

### Reglas

- Botones principales: mínimo 36–40 px de alto.
- Botones secundarios: mínimo 32–36 px.
- Botones de icono: área clicable mínima 32 × 32 px.
- Miniaturas: área seleccionable completa, no solo imagen.

### Criterios de aceptación

- No hay controles demasiado pequeños.
- La app se siente precisa y no frágil.

---

# FASE 12 — Estados técnicos, diagnóstico y configuración avanzada

---

## 12.1. Encapsular diagnóstico técnico

### Problema

`Ver diagnóstico` puede ser útil, pero no debe competir con acciones principales.

### Cambio requerido

Ubicar diagnóstico bajo:

```text
Ver detalle técnico
```

Dentro de:

- error;
- configuración;
- estado avanzado;
- panel de soporte.

### Criterios de aceptación

- El usuario normal no se ve obligado a leer diagnóstico.
- El usuario avanzado puede acceder al detalle cuando lo necesita.

---

## 12.2. Reorganizar configuración global

### Cambio requerido

El botón superior `Configuración` debe abrir configuración global, no ajustes de salida del lote.

Contenido sugerido:

```text
Configuración

General
- Carpeta por defecto
- Comportamiento al iniciar
- Confirmaciones

Formatos de salida
- Gestionar formatos guardados

Atajos
- Lista de atajos de teclado

Avanzado
- Motor de procesamiento
- Logs
- Diagnóstico
```

### Criterios de aceptación

- Configuración global no se mezcla con la revisión del lote.
- Salida del lote vive en la pestaña `Salida` o modal de formatos.
- Diagnóstico queda en avanzado.

---

# FASE 13 — Revisión de layout general

---

## 13.1. Ajustar anchuras de columnas

### Estado actual

La distribución base es buena, pero debe afinarse para que:

- la galería no quede demasiado estrecha;
- el visor aproveche mejor el centro;
- el panel derecho no se convierta en cajón excesivo;
- el panel izquierdo no parezca un informe.

### Recomendación para desktop ancho

```text
Panel izquierdo: 270–300 px
Galería: 300–340 px
Visor central: flexible, prioridad máxima
Inspector derecho: 320–360 px
```

### Acciones

- Evitar scroll global.
- Mantener scroll interno en galería e inspector.
- El visor debe ocupar toda la altura disponible.
- La imagen debe centrarse respecto al área útil, no respecto a la ventana completa si hay paneles laterales.

### Criterios de aceptación

- En 1920 px de ancho, la interfaz se siente equilibrada.
- En anchuras menores, los paneles no rompen el layout.
- No aparece scroll horizontal.

---

## 13.2. Revisar ritmo visual y espaciado

### Reglas

- Padding de panel: 16 px.
- Separación entre bloques: 16 px.
- Separación entre grupos grandes: 24 px.
- Separación título/contenido: 8 px.
- Tarjetas: padding 12–16 px.
- Modal: padding exterior 24 px; grupos internos 16–24 px.

### Acciones

- Corregir zonas sin padding o con padding inconsistente.
- Eliminar líneas divisorias innecesarias.
- Usar bordes solo cuando ayuden a separar secciones reales.
- Evitar tarjetas dentro de tarjetas si no aportan jerarquía.

### Criterios de aceptación

- Todo parece diseñado con la misma retícula.
- No hay zonas apretadas junto a zonas excesivamente abiertas sin intención.

---

# FASE 14 — Testing manual y criterios finales de aceptación

---

## 14.1. Casos de prueba obligatorios

Probar como mínimo:

1. Sin carpeta seleccionada.
2. Carpeta con 0 imágenes compatibles.
3. Carpeta con 1 imagen.
4. Carpeta con 44 imágenes y 1 omitida.
5. Carpeta con avisos no bloqueantes.
6. Carpeta con avisos bloqueantes.
7. Escaneo de carpeta grande.
8. Cambio de formato de salida.
9. Edición de formato con cambios sin guardar.
10. Eliminación de formato.
11. Exportación sin avisos.
12. Exportación con avisos.
13. Exportación con archivos ya existentes.
14. Error de permisos en carpeta de salida.
15. Búsqueda sin resultados.
16. Navegación con teclado por galería.
17. Cierre de modal con `Esc`.
18. Zoom y navegación de visor.
19. Ruta larga en barra inferior.
20. Nombre de archivo largo en galería.

---

## 14.2. Checklist visual final

La implementación se considerará correcta si:

- La pantalla se entiende en menos de cinco segundos.
- La acción principal siempre es obvia.
- No se mezclan configuración global, salida del lote e imagen seleccionada.
- No se repite `Ajustes` con varios significados.
- No se repite la misma información en cuatro lugares.
- Los avisos son visibles, pero no alarmistas.
- Las acciones destructivas están protegidas.
- El modal de formatos muestra una vista previa concreta.
- El escaneo no parece bloqueado.
- Los números son coherentes en toda la app.
- El visor aprovecha mejor la imagen vertical.
- La galería permite localizar rápidamente imágenes con aviso.
- La interfaz mantiene un sistema visual consistente.
- El usuario no técnico puede completar el flujo sin entender detalles internos.

---

# Orden de implementación recomendado

Este es el orden exacto sugerido para Codex:

1. Crear modelo central de estados y conteos.
2. Centralizar vocabulario/copy principal.
3. Rediseñar header y acción principal dinámica.
4. Reestructurar panel izquierdo en Entrada / Estado / Salida.
5. Rehacer filtros y tarjetas de galería.
6. Mejorar visor central: modos, zoom, aprovechamiento vertical.
7. Reorganizar panel derecho en Revisión / Salida / Avisos.
8. Sacar gestión de presets/formats de pantalla principal.
9. Rediseñar modal de formatos con vista previa.
10. Implementar estados de escaneo, vacíos y errores.
11. Añadir confirmación inteligente de exportación.
12. Añadir gestión explícita de sobrescritura.
13. Consolidar sistema visual con tokens y componentes.
14. Revisar accesibilidad, foco, teclado y tamaños clicables.
15. Reorganizar configuración global y diagnóstico técnico.
16. Ajustar layout, spacing y responsive desktop.
17. Ejecutar checklist de pruebas.
18. Documentar cambios y posibles tareas pendientes.

---

# Notas finales para Codex

- No basta con “hacerlo más bonito”. El rediseño debe resolver flujo, comprensión, seguridad y jerarquía.
- No añadas más paneles si puedes resolverlo con mejor agrupación.
- No llenes la pantalla de explicaciones. La interfaz debe ser clara por estructura, no por exceso de texto.
- No uses color como único significado.
- No mantengas la gestión avanzada de formatos visible en el flujo principal.
- Prioriza siempre:
  1. siguiente acción clara;
  2. conteos coherentes;
  3. estado visible;
  4. salida predecible;
  5. errores prevenidos;
  6. diseño consistente.

