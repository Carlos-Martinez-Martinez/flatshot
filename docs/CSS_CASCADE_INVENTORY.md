# Inventario de cascada CSS - FlatShot

Este documento registra el estado actual de la cascada CSS activa antes de
consolidar tokens, selectores u overrides. Es una fase de inventario: no cambia
estilos, layout, comportamiento de UI, exportacion ni salida de imagen.

## Carga activa

`apps/flatshot-desktop/frontend/index.html` carga las hojas en este orden:

1. `styles.css`
2. `ux-foundation.css`
3. `ux-refactor.css`

Ese orden es parte del comportamiento actual. `ux-refactor.css` gana la cascada
cuando repite selectores o tokens anteriores.

## Metricas actuales

Medicion no destructiva ejecutada sobre los tres CSS activos:

| Archivo | Lineas | `!important` | Tokens declarados | `@media` | `@keyframes` |
| --- | ---: | ---: | ---: | ---: | ---: |
| `styles.css` | 9.028 | 122 | 288 | 20 | 3 |
| `ux-foundation.css` | 3.469 | 102 | 134 | 10 | 1 |
| `ux-refactor.css` | 1.322 | 113 | 16 | 4 | 0 |
| Total | 13.819 | 337 | 438 | 34 | 4 |

Resumen de tokens:

- Declaraciones de tokens CSS: 438.
- Tokens unicos: 223.
- Nombres de token declarados mas de una vez: 145.

## Duplicados principales

Tokens mas repetidos:

| Token | Declaraciones |
| --- | ---: |
| `--column-gallery` | 11 |
| `--column-inspector` | 11 |
| `--inspector-w` | 6 |
| `--topbar-h` | 6 |
| `--statusbar-h` | 5 |
| `--viewer-min` | 5 |
| `--control-h` | 4 |
| `--control-h-sm` | 4 |
| `--footer-height` | 4 |
| `--gallery-width` | 4 |
| `--lot-rail-width` | 4 |
| `--app-bg` | 3 |
| `--border-subtle` | 3 |
| `--color-bg-muted` | 3 |
| `--color-bg-soft` | 3 |
| `--color-border` | 3 |
| `--color-border-strong` | 3 |
| `--color-text` | 3 |
| `--column-lot` | 3 |
| `--line` | 3 |

Selectores simples con muchas repeticiones aproximadas:

| Selector | Repeticiones |
| --- | ---: |
| `.gallery-column` | 131 |
| `.settings-panel` | 129 |
| `.app-shell` | 104 |
| `.preview-canvas` | 48 |
| `.batch-rail` | 34 |
| `.canvas-area` | 33 |
| `.zoom-controls` | 30 |
| `.empty-state` | 24 |
| `.image-item` | 24 |
| `.preview-header` | 24 |
| `.batch-summary-card` | 23 |
| `.preset-chip` | 22 |
| `.gallery-filter` | 20 |
| `.issue-item` | 20 |

La repeticion de selectores no implica automaticamente codigo muerto. En esta
base suele mezclar estado responsive, variantes visuales y overrides historicos.
Por eso la recomendacion es consolidar por dominio visual, no con borrados
globales por busqueda.

## Riesgos de mantenibilidad

### Riesgo 1: tokens re-declarados por capa

- Archivos afectados: `styles.css`, `ux-foundation.css`, `ux-refactor.css`.
- Gravedad: media-alta.
- Riesgo: cambiar un token en la primera capa puede no tener efecto si otra capa
  lo redefine despues.
- Impacto: dificulta saber cual es la fuente real de verdad para superficies,
  texto, radios, columnas, anchos de panel y alturas fijas.
- Recomendacion: crear una tabla de tokens canonicos antes de mover reglas. Los
  tokens de layout criticos (`--column-*`, `--*-width`, `--topbar-h`,
  `--statusbar-h`) deben consolidarse despues de screenshots responsive.

### Riesgo 2: uso alto de `!important`

- Archivos afectados: `styles.css`, `ux-foundation.css`, `ux-refactor.css`.
- Gravedad: media-alta.
- Riesgo: un ajuste local puede requerir otro override aun mas especifico.
- Impacto: aumenta regresiones visuales y hace dificil razonar por especificidad.
- Recomendacion: reducir `!important` por componente, empezando por controles y
  estados simples. No retirar varios overrides a la vez sin revisar foco,
  hover, disabled, responsive y modo modal.

### Riesgo 3: selectores de dominios mezclados

- Archivos afectados: principalmente reglas de `.app-shell`,
  `.gallery-column`, `.settings-panel`, `.preview-canvas`, `.batch-rail` y
  `.canvas-area`.
- Gravedad: media.
- Riesgo: reglas de estructura, componente y estado conviven en varias capas.
- Impacto: un cambio visual pequeno puede tocar layout global o provocar saltos.
- Recomendacion: consolidar por dominios: shell/layout, galeria/lote, preview,
  inspector, exportacion/modales y componentes `ui-*`.

## Refactor recomendado

### Fase CSS A: contrato y capturas

- Mantener el orden de carga actual.
- Capturar estados antes/despues para escritorio y movil:
  - lote vacio;
  - carpeta con PNGs;
  - imagen seleccionada;
  - inspector abierto;
  - dialogo de exportacion;
  - exportacion en progreso;
  - errores/preflight.
- Registrar viewport, DPI si aplica y fecha de captura.

### Fase CSS B: tokens canonicos

- Declarar una fuente principal para colores, texto, radios, sombras y
  espaciado.
- Separar tokens de layout que cambian por responsive de tokens visuales.
- No eliminar alias antiguos hasta confirmar que no se usan en los tres CSS.
- Mantener nombres existentes donde la UI ya depende de ellos.

### Fase CSS C: componentes comunes

- Consolidar primero componentes `ui-*`, botones, badges, empty states,
  progress y modales.
- Reducir `!important` dentro de un componente a la vez.
- Verificar foco visible, contraste, overflow y estados disabled/active.

### Fase CSS D: layout de dominios

- Consolidar `app-shell`, topbar/statusbar, galeria, batch rail, preview canvas
  e inspector por bloques completos.
- Evitar mover reglas de layout y color en el mismo cambio.
- Probar viewports estrechos antes de retirar reglas duplicadas.

### Fase CSS E: limpieza de capas

- Solo despues de las fases anteriores, evaluar si `ux-refactor.css` puede
  reducirse o fusionarse parcialmente.
- Mantener una capa final de overrides solo si documenta estados temporales
  claros.

## Criterios de aceptacion para cambios CSS futuros

- El orden de carga se mantiene o se documenta explicitamente el cambio.
- No hay diferencias inesperadas en preview, batch grid, inspector, modales,
  topbar, statusbar ni estados de preflight.
- No aparecen solapamientos, overflow horizontal, saltos de layout ni perdida de
  foco visible.
- Cada retirada de `!important` tiene una razon local y una comprobacion visual.
- La salida exportada permanece sin cambios; CSS no debe afectar el pipeline de
  imagen ni el comportamiento de archivos.

## Comandos usados para este inventario

```powershell
Get-ChildItem apps/flatshot-desktop/frontend/styles.css,apps/flatshot-desktop/frontend/ux-foundation.css,apps/flatshot-desktop/frontend/ux-refactor.css
```

```powershell
Select-String -Path apps/flatshot-desktop/frontend/styles.css,apps/flatshot-desktop/frontend/ux-foundation.css,apps/flatshot-desktop/frontend/ux-refactor.css -Pattern '!important'
```

```powershell
Select-String -Path apps/flatshot-desktop/frontend/styles.css,apps/flatshot-desktop/frontend/ux-foundation.css,apps/flatshot-desktop/frontend/ux-refactor.css -Pattern '^\s*(--[A-Za-z0-9-]+)\s*:'
```

## Primer ajuste aplicado

Se retiraron 25 aliases tempranos de `ux-foundation.css` que estaban
redefinidos por el bloque final de la misma hoja. Se conservaron los aliases que
esta capa sigue poseyendo, como `--semantic-success-soft`, `--semantic-info-*`,
`--z-*` y `--ui-*`.

Este ajuste no cambia selectores, `!important`, orden de carga, layout ni valores
finales esperados de tokens.

## Estado de esta fase

- Archivos CSS modificados: `apps/flatshot-desktop/frontend/ux-foundation.css`.
- Cambios funcionales: ninguno esperado; limpieza de aliases CSS redundantes.
- Checks manuales UI: no se ejecuto flujo visual completo; se verifico carga
  estatica local de HTML/CSS/JS por HTTP.
- Salida exportada: sin cambios; no se modifico procesamiento, preview,
  exportacion ni escritura de archivos.
