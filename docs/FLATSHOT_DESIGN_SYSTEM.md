# FlatShot Desktop Design System

Documento minimo de implementacion para la UI HTML/CSS actual.

La UI activa usa CSS modular sin build step. El orden de carga vive en
`apps/flatshot-desktop/frontend/index.html` y se audita con
`python scripts\audit_css.py --check`.

## Tokens

La fuente unica de tokens es `apps/flatshot-desktop/frontend/css/00-settings/tokens.css`.

- Superficies: `--surface-app`, `--surface-panel`, `--surface-muted`, `--surface-stage`.
- Texto: `--text-primary`, `--text-secondary`, `--text-muted`, `--text-subtle`.
- Bordes: `--border-subtle`, `--border-default`, `--border-emphasis`.
- Semantica: `--semantic-primary`, `--semantic-selection`, `--semantic-success`, `--semantic-warning`, `--semantic-danger`, `--semantic-info`.
- Espaciado, radio, tipografia y sombras siguen la escala `--space-*`, `--radius-*`, `--font-size-*`, `--shadow-*`.
- Aliases legacy como `--color-*`, `--bg-*`, `--line`, `--topbar-h`, `--statusbar-h` y `--fs-*` se mantienen en `tokens.css` mientras haya referencias.

## Modulos CSS

La cascada usa carpetas numeradas para que el orden sea visible sin build step:

- `00-settings/tokens.css`: tokens canonicos, aliases legacy y overrides responsive de tokens.
- `01-base/base.css`: reset, documento, foco y controles base.
- `02-layout/`: shell, topbar, workspace y footer.
- `03-components/`: primitivas reutilizables, patrones de flujo, resultados/revision, botones, inputs, chips, progress, cards, empty states y dev/debug.
- `04-batch-gallery/`: lote, fuente, resumen, galeria, filtros, grid y miniaturas.
- `05-viewer/`: preview, toolbar, canvas, zoom y fondos de revision.
- `06-inspector-export/`: inspector, navegacion de subviews, workflows de edicion, presets, ajustes, exportacion, formatos activos y warnings.
- `07-modals/`: dialogos y overlays.
- `08-states-responsive/`: `data-ui-state`, clases `is-*`, responsive y guards finales.
- `99-legacy-compat.css`: debe permanecer vacio salvo excepcion temporal documentada.

Todos los modulos activos, salvo `99-legacy-compat.css`, deben estar dentro de
la capa unica `@layer flatshot`. La capa no sustituye al orden de enlaces: solo
deja un limite explicito de cascada para evitar que CSS externo o futuro entre
sin contrato.

## Componentes base

Las primitivas visuales apuntan a clases reales del markup y de los templates,
sin decoracion posterior en runtime. Los botones se gobiernan por `button`,
`primary`, `danger-subtle`, `btn-linklike`, `ghost-action` e `icon-button`.
Los paneles y tarjetas usan sus clases de dominio: `batch-summary-card`,
`review-card`, `format-preview-card`, `inspector-output-card`,
`output-profile-option`, `image-item`, `settings-section`, `context-panel`,
`issue-item`, `export-confirm-risk` y equivalentes del flujo.

Los estados globales no usan clases legacy del shell. El contrato de estado es:
`data-ui-state`, `data-batch-context`, `data-status-footer` y
`data-output-editing`.

## Roles de color

- Accion principal: verde (`--semantic-primary`).
- Seleccion, pestana activa y foco contextual: azul (`--semantic-selection`).
- Correcto/listo: verde de estado (`--semantic-success`).
- Aviso: ambar (`--semantic-warning`).
- Error/destructivo: rojo (`--semantic-danger`).

## Reglas de uso

- No crear colores o paddings nuevos sin token.
- No declarar `:root` fuera de `css/00-settings/tokens.css`.
- No enlazar de nuevo `styles.css`, `ux-foundation.css` ni `ux-refactor.css`.
- No sacar modulos activos de `@layer flatshot` ni dividir esa capa en varias sin QA visual.
- Mantener `!important` por debajo de 25 y usarlo solo para ocultacion/accesibilidad o guards justificados.
- Mantener cada archivo CSS por debajo de 500 lineas; si crece, dividir por subdominio.
- No enlazar modulos CSS vacios o solo con comentario; la unica excepcion es `99-legacy-compat.css`.
- No introducir selectores duplicados ni listas de selectores duplicadas dentro del mismo contexto de cascada.
- No introducir clases legacy de estado en el shell; los estados nuevos deben usar `data-ui-state` o atributos `data-*` derivados.
- No reintroducir decoracion visual por runtime; las clases visuales deben estar en markup/templates o representadas por selectores de clases reales existentes.
- No usar tarjetas permanentes para explicar estados correctos.
- Los problemas se explican; lo correcto se indica con badge compacto.
- Las rutas, nombres finales y valores copiables pueden ser seleccionables.
- Los botones e iconos deben tener `title` y nombre accesible si el texto visible no basta.
