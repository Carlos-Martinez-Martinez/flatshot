# FlatShot Desktop UX/UI Backlog

Estado generado para el sprint UX/UI de 2026-07-03.

## Implementado en Sprint 1 / P0

- Focus ring visible mediante token `--focus-ring` con valor de `box-shadow`.
- Contraste de texto secundario reforzado en `--color-muted-2`.
- Drag-and-drop de carpetas con fallback controlado cuando no hay ruta resoluble.
- Onboarding sin referencias obligatorias a assets inexistentes; fallback CSS intencional.
- Error boundary global para errores de carga, inicialización y promesas no capturadas.

## Implementado en Sprint 2 / P1

- Pila tipografica alineada a `system-ui` y pesos no estandar normalizados.
- Carpetas recientes persistidas localmente, visibles en onboarding y accionables.
- Undo/redo de ajustes con `Ctrl+Z`, `Ctrl+Shift+Z` y agrupacion de sliders.
- Preset activo visible en topbar y selector de ajuste mantenido en flujo visible.
- Overlay de carga de preview conservando la imagen anterior.
- Targets interactivos pequenos elevados a un minimo practico de 36px.
- Inspector accesible bajo 1120px mediante panel responsive accionado desde topbar.

## P2 Pospuesto

- Consolidar tokens redundantes restantes.
- Migrar colores hardcodeados restantes a tokens semanticos.
- Anadir multi-seleccion en galeria.
- Anadir virtualizacion de scroll en lotes grandes.
- Anadir reintento de imagenes fallidas en exportacion.
- Preparar dark mode fase 1 mediante tokens.
- Refactorizar selectores CSS fragiles de botones hacia clases positivas.
- Evaluar Proxy para state con auto-sync.
- Evaluar bundler ligero como esbuild o Vite.

## Implementado en Sprint 3 / P2 Aislado

- Animacion de apertura y cierre de modales mediante helper compartido `syncModalVisibility`.
- Respeto de `prefers-reduced-motion: reduce` para evitar movimiento innecesario.
- `DESIGN.md` creado como contrato visual de referencia para cambios UI futuros.
- Contraste del primario con texto inverso ajustado a AA para botones y estados verdes.
- Contraste de warning elevado a AA sobre `--color-warning-soft` y usos warning/error migrados a tokens semanticos.
- RGB hardcodeado del primario anterior eliminado de CSS activo y sustituido por tokens o `color-mix` basado en `--color-primary`.
- Blanco literal exacto (`#fff`/`#ffffff`) eliminado de CSS activo fuera de `tokens.css`; se anadio `--color-output-white` para fondos reales de salida/preview.
- Colores hex restantes de CSS activo migrados a tokens en `tokens.css`, incluyendo tonos mock, swatches, loaders, hover de galeria y perfiles de salida.
- Familia repetida `rgba(15, 23, 42, ...)` migrada a tokens `--ink-alpha-*` y prohibida fuera de `tokens.css` mediante contrato.
- Superficies translúcidas `rgba(255, 255, 255, ...)` migradas a tokens `--surface-alpha-*` y prohibidas fuera de `tokens.css`.
- Alphas neutrales/checker (`rgba(11, 23, 34, ...)`, `rgba(0, 0, 0, ...)`, `rgba(100, 116, 139, ...)`) migrados a tokens compartidos y cubiertos por contrato.
- `rgb()`/`rgba()` eliminado por completo de CSS activo fuera de `tokens.css`; los valores restantes de estados, onboarding, mock canvas y fallbacks visuales quedaron tokenizados.
- Presupuesto de lineas CSS relajado a 12.000 lineas totales y 650 por modulo, manteniendo auditoria de duplicados, tokens, orden y legacy compat.
- Tokens CSS no referenciados eliminados y contrato anadido para que todo token declarado sea alcanzable desde frontend activo.
- Dimensiones compartidas de modales migradas a tokens semanticos y contrato agregado para evitar reintroducir literales en detalle de lote y guide manager.
- Bloques `@media` adyacentes de `responsive.css` fusionados preservando orden de cascada; contrato agregado para evitar duplicados consecutivos por breakpoint.
- Duraciones y curvas de movimiento comunes migradas a tokens (`quick`, `fast`, `standard`, `disclosure`, onboarding) sin cambiar valores computados.
- Reglas `display` sobre `[hidden]` centralizadas en `base.css`; `!important` reducido de 18 a 12 y presupuesto del auditor endurecido.
- Reglas `display` sobre `.is-hidden` centralizadas en `states.css`; `!important` reducido a 10 y contrato agregado para evitar ocultados especificos redundantes.
- `font-size` con valores canonicos ya tokenizados migrado a `--font-size-*`; quedan fuera solo tamanos especiales sin token equivalente.
- `font-weight` directo eliminado de CSS activo fuera de `tokens.css`; se anadio `--font-weight-extrabold` para conservar enfasis existentes de `800` y el unico `650` no estandar se normalizo a semibold.
- `border-radius` canonicos eliminados de CSS activo fuera de `tokens.css`; se reutilizaron `--radius-*` existentes y se anadio `--radius-xxs` para el unico radio compacto de `4px`.
- Literales tipograficos de `line-height` y `letter-spacing` migrados a tokens dedicados, conservando valores computados.
- Aliases redundantes `--radius-6`, `--radius-8`, `--radius-12` y `--radius-16` eliminados; los usos pasan a `--radius-xs`, `--radius-sm`, `--radius-md` y `--radius-lg`.
- Aliases redundantes de controles, spacing y linea (`--control-h`, `--control-h-compact`, `--control-height-sm`, `--space-6`, `--line-tight`) eliminados en favor de los tokens canonicos existentes.
- Literales `height`/`min-height` de 36px migrados a `--control-height` para la altura estandar de controles.
- Aliases redundantes `--transition-fast` y `--transition-standard` eliminados; los usos pasan a `--duration-*` + `--ease-standard`.
- Valores canonicos de espaciado `4/8/12/16/24/32px` migrados a `--space-*` en `gap`, `padding` y `margin`, con contrato para evitar regresiones.
- Bordes hairline de `1px` migrados a `--border-width`, con contrato para evitar reintroducir anchuras literales en `border*`.
- Texto compacto de `11px` migrado a `--font-size-caption`, ampliando el contrato tipografico sin alterar la escala visual.
- Gaps compactos `2/3/6/10px` migrados a subtokens `--space-*`, limitando el cambio a `gap`, `row-gap` y `column-gap`.
- Controles compactos de `30px` migrados a `--control-size-compact`, cubriendo `width`, `height`, `min-width` y `min-height` donde aplica.
- Tamaño de elementos visualmente ocultos migrado a `--visually-hidden-size` para centralizar el patrón accesible de `1px`.
- Anillos hairline de `box-shadow` (`0 0 0 1px`) migrados a `var(--border-width)` con contrato antirregresion.
- Bordes y anillos reforzados de `2px` migrados a `--border-width-strong`, preservando grosor computado.
- Geometria de checkerboards migrada a tokens `--checker-step-*` y `--checker-tile-*`, eliminando tamanos/offsets hardcodeados repetidos.
- Alturas compactas `22/24/28px` migradas a `--control-size-2xs`, `--control-size-xs` y `--control-size-sm` para chips, toggles y acciones pequenas.
- Trazos visuales de `3px` y checkerboards de miniatura `7/14px` migrados a tokens semanticos, preservando grosor y patron visual.
- Dimensiones medias de `34px` migradas a tokens de control, switch, loader y mock de iluminacion, sin cambiar tamanos computados.
- Gutters `calc(... - 48px)` migrados al token existente `--modal-viewport-gutter` en modales, onboarding, popovers y estados del visor.
- Focus outlines y `stroke-width` de iconos migrados a tokens; se corrigio el uso invalido de `--focus-ring` como color de `outline`.
- Puntos de estado `7px` y chevrons de disclosure `9px` migrados a tokens dedicados.
- Slots compactos `32/38px` y gutter debug `calc(100vw - 32px)` migrados a tokens semanticos.
- Geometria del switch de perfiles de salida (`track`, thumb, offset y travel) migrada a tokens dedicados.
- Thumbs de sliders y swatch seleccionada de guias migrados a tokens de tamano, manteniendo la geometria computada.
- Chips y marcadores de estado de galeria migrados a tokens semanticos de tamano.
- Geometria del tab del icono de carpeta vacia migrada a tokens dedicados.
- Contador de guias del visor migrado a token de ancho minimo.
- Indicadores compactos de `18px` migrados a tokens compartidos y la anulacion del icono de onboarding simplificada sin geometria oculta.
- Dimensiones de miniaturas de galeria, rail y lista migradas a tokens dedicados.
- Geometria redundante de pseudo-elementos `active::after` ocultos eliminada en galeria.
- Metricas internas de tarjetas/filas de galeria migradas a tokens semanticos.
- Columnas estandar de filas de control del inspector migradas a tokens compartidos.
- Fila de asset del rail, alturas `42px`, metricas `48px` y metricas `58px` restantes migradas a tokens especificos por componente.
- Acciones compactas y offsets `36px` restantes migrados a tokens de componente; cache frontend actualizado a sprint 43.
- Metricas estructurales del gestor de guias migradas a tokens semanticos para columnas, filas, iconos y variantes responsive; cache frontend actualizado a sprint 44.
- Footer de estado limpiado: progreso tokenizado, target de botones elevado a la altura estandar y overrides inertes eliminados; cache frontend actualizado a sprint 45.
- Metricas base de botones migradas a tokens (`primary`, onboarding e iconos), reduciendo literales en el componente compartido; cache frontend actualizado a sprint 46.
- Altura de pistas de sliders y progress bars unificada en `--control-track-height`, evitando `6px` duplicado entre formularios y loaders; cache frontend actualizado a sprint 47.
- Metricas locales de formularios tokenizadas: offset del thumb de range, checkbox compacto y ancho minimo del label de zoom; cache frontend actualizado a sprint 48.
- Padding compacto de tarjetas/avisos (`9px 10px`) corregido a escala existente sin mantener `--compact-card-padding`; cache frontend actualizado a sprint 49.
- Ancho inline de workflow (`min(640px, 100%)`) centralizado en `--workflow-inline-width` para drop de carpeta, recientes y entrada inline; cache frontend actualizado a sprint 50.
- Gaps micro de `5px` normalizados a escala existente sin mantener `--space-1-25`; cache frontend actualizado a sprint 51.
- Separacion vertical de secciones del rail/galeria (`margin-top: 10px`) resuelta con `--space-2-5` existente sin mantener `--gallery-section-offset`; cache frontend actualizado a sprint 52.
- Correccion de deriva CSS: retirados aliases locales/microtokens de formularios, galeria, footer, botones, guide manager e inspector; duplicados estructurales de inspector consolidados; cache frontend actualizado a sprint 53.

## Evaluaciones P2 Cerradas

- Proxy para state con auto-sync: pospuesto. La app actual depende de flujos explicitos entre controladores, bridge y renderizado; un Proxy global podria ocultar efectos laterales y complicar pruebas sin resolver una friccion bloqueante.
- Bundler ligero como esbuild o Vite: pospuesto. El frontend actual funciona como scripts estaticos versionados y sin framework; introducir bundler requiere revisar empaquetado desktop, cache busting y orden de carga. Tiene sentido retomarlo junto con una migracion gradual a ES modules.
- Dark mode fase 1 y consolidacion de tokens: pospuestos para una pasada dedicada de CSS. La auditoria exige no duplicar tokens ni selectores, asi que deben abordarse como refactor controlado.

## Verificacion Manual Registrada

- Escaneo de carpeta con 2 PNG validos: `totalImages=2`, `validImages=2`, sin errores.
- Escaneo de carpeta vacia: `totalImages=0`, `validImages=0`, sin bloqueo.
- Preview renderizado desde bridge: respuesta PNG valida de 320x420.
- Preparacion de exportacion con destino custom: `sourceImages=2`, `totalOutputs=2`, sin errores.
- Exportacion bridge: job completado 2/2, progreso 100%, sin errores.
- Integridad de origen: hashes SHA-256 de los PNG fuente conservados antes y despues de exportar.

## P3 Pospuesto

- Arreglar escala de spacing duplicada.
- Consolidar breakpoints.
- Anadir divisor arrastrable en compare mode.
- Persistir historial de exportaciones.
- Anadir tour guiado inicial.
- Anadir soporte `forced-colors`.
- Animar disclosures.
- Limpiar elementos muertos adicionales si aparecen en futuras auditorias.
- Extraer strings para i18n.
- Migrar gradualmente a ES modules.

## Elementos Muertos Revisados

- Se conservaron `#active-batch-label`, `.brand-copy span`, `.top-summary`, `#primary-action`, `.folder-list.batch-format` y `.filmstrip-panel` porque tienen referencias activas en HTML, JS o CSS de layout.
- Se eliminaron `.demo-switcher` y `.mode-switcher` porque solo tenian reglas CSS y no aparecian en HTML ni JS.
