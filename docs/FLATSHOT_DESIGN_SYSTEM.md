# FlatShot Desktop Design System

Documento minimo de implementacion para la UI HTML/CSS actual.

## Tokens

La capa viva esta en `apps/flatshot-desktop/frontend/styles.css` y se consolida en `ux-foundation.css`.

- Superficies: `--surface-app`, `--surface-panel`, `--surface-muted`, `--surface-stage`.
- Texto: `--text-primary`, `--text-secondary`, `--text-muted`, `--text-subtle`.
- Bordes: `--border-subtle`, `--border-default`, `--border-emphasis`.
- Semantica: `--semantic-primary`, `--semantic-selection`, `--semantic-success`, `--semantic-warning`, `--semantic-danger`, `--semantic-info`.
- Espaciado, radio, tipografia y sombras siguen la escala `--space-*`, `--radius-*`, `--font-size-*`, `--shadow-*`.

## Componentes base

Las clases `ui-*` son primitivas reutilizables. El runtime las asigna a la UI existente en `renderDesignSystemComponents()` para evitar reescribir toda la plantilla.

- `ui-button`: boton base, con variantes `ui-button--primary`, `ui-button--secondary`, `ui-button--ghost`, `ui-button--danger`, `ui-button--icon`.
- `ui-status-badge`: badges de estado, preflight, chips y estados de miniatura.
- `ui-summary-card`: bloques de resumen y tarjetas compactas.
- `ui-thumbnail-card`: tarjeta seleccionable de galeria.
- `ui-inspector-section`: secciones del inspector, detalle y contexto.
- `ui-modal-shell` y `ui-modal-backdrop`: estructura de modal.
- `ui-segmented-control` y `ui-tabs`: controles segmentados y pestanas.
- `ui-toolbar`: barras de accion compactas.
- `ui-empty-state`: estados vacios.
- `ui-progress-state`: progreso determinado o indeterminado.
- `ui-problem-card`: avisos, errores y riesgos de exportacion.

## Roles de color

- Accion principal: verde (`--semantic-primary`).
- Seleccion, pestana activa y foco contextual: azul (`--semantic-selection`).
- Correcto/listo: verde de estado (`--semantic-success`).
- Aviso: ambar (`--semantic-warning`).
- Error/destructivo: rojo (`--semantic-danger`).

## Reglas de uso

- No crear colores o paddings nuevos sin token.
- No usar tarjetas permanentes para explicar estados correctos.
- Los problemas se explican; lo correcto se indica con badge compacto.
- Las rutas, nombres finales y valores copiables pueden ser seleccionables.
- Los botones e iconos deben tener `title` y nombre accesible si el texto visible no basta.
