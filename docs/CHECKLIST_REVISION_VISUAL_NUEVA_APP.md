# Checklist revisión visual nueva app FlatShot

Usar antes de cerrar cada tanda visual de la nueva app.

## Arranque

- [ ] `python apps/flatshot-desktop/run_dev.py --open` arranca sin errores.
- [ ] El navegador abre la app.
- [ ] El header muestra estado operativo sin datos técnicos.
- [ ] `Debug` indica modo mock/bridge cuando se abre.
- [ ] El bridge aparece conectado si está activo.
- [ ] `Ctrl+C` detiene bridge y frontend.

## Layout

- [ ] La preview tiene protagonismo.
- [ ] El panel de lote es claro.
- [ ] El panel de ajustes no satura.
- [ ] La exportación se entiende de un vistazo.
- [ ] La barra inferior aporta estado real.
- [ ] La franja de desarrollo no compite con el flujo principal.

## Flujo mock

- [ ] Sin lote.
- [ ] Lote cargado.
- [ ] Selección de imagen.
- [ ] Preview lista.
- [ ] Preview con error.
- [ ] Exportación lista.
- [ ] Exportación completada.
- [ ] Exportación con errores.

## Bridge

- [ ] Health OK.
- [ ] Capabilities visibles.
- [ ] Presets cargan o fallback claro.
- [ ] `Seleccionar carpeta` abre selector local en modo bridge.
- [ ] Escaneo real por ruta funciona.
- [ ] Error de ruta se muestra bien.
- [ ] La UI diferencia claramente escaneo real de estados simulados.

## APP.4 — Escaneo real en UI

- [ ] `Modo` en `Bridge local` muestra el panel de ruta en el flujo principal.
- [ ] `Comprobar bridge` muestra `health OK`.
- [ ] `Seleccionar carpeta` rellena la ruta y escanea.
- [ ] Escanear una carpeta con PNG actualiza carpetas, imagenes y contadores.
- [ ] La primera imagen real queda seleccionada.
- [ ] La preview muestra estado claro para imagen real.
- [ ] La preview muestra nombre y ruta de la imagen real.
- [ ] La salida queda disponible en la pestaña `Salida`.
- [ ] Una carpeta vacia muestra `No se encontraron PNG`.
- [ ] Una ruta invalida muestra error controlado.
- [ ] Una ruta vacia muestra `Ruta vacia`.
- [ ] El bridge desconectado muestra feedback claro.
- [ ] Cambiar a `Mock` conserva escenarios de revision.
- [ ] `Limpiar lote` deja un estado inicial claro.

## APP.4.5 — Shell visual

- [ ] No hay scroll horizontal.
- [ ] No hay scroll vertical global.
- [ ] La barra inferior está siempre visible.
- [ ] Los paneles laterales tienen scroll interno si hace falta.
- [ ] El área de preview mantiene protagonismo.
- [ ] Los controles de revisión no dominan la interfaz.
- [ ] Mock y Bridge se distinguen claramente.
- [ ] El panel derecho no desborda.
- [ ] La app es usable en 1920×1080.

## APP.5 — Preview real

- [ ] `run_dev.py --open` arranca frontend y bridge.
- [ ] Bridge conecta correctamente.
- [ ] Se escanea una carpeta real con PNG.
- [ ] Al seleccionar una imagen aparece loading.
- [ ] La preview real aparece en el panel central.
- [ ] La imagen no rompe el layout.
- [ ] No hay scroll global.
- [ ] No hay scroll horizontal.
- [ ] Los warnings se muestran sin invadir.
- [ ] Los errores de preview son claros.
- [ ] Modo mock sigue funcionando.
- [ ] Exportación real sigue disponible en `Salida`.

## APP.6 — Presets y ajustes reales

- [ ] `Comprobar bridge` carga presets reales.
- [ ] El panel de preset indica `Defaults`, `Config` o `Config legacy`.
- [ ] Cambiar preset actualiza sliders principales.
- [ ] Cambiar preset regenera preview real.
- [ ] Opacidad, blur, distancia y padding afectan la preview real.
- [ ] Los controles avanzados están plegados por defecto.
- [ ] Ruido, contacto, escala y motor se pueden modificar.
- [ ] `Sin guardar` aparece al cambiar ajustes.
- [ ] `Reset` vuelve al preset activo.
- [ ] `Guardar preset` queda claramente pendiente en Bridge.
- [ ] Modo mock sigue funcionando.
- [ ] Exportación real sigue disponible y no cambia al ajustar presets.

## APP.7 — Exportación real y progreso

- [ ] `run_dev.py --open` arranca frontend y bridge.
- [ ] Bridge conecta correctamente.
- [ ] Se escanea una carpeta real con PNG.
- [ ] La pestaña `Salida` muestra formato, tamaño, destino, naming y total.
- [ ] El botón principal muestra `Exportar N`.
- [ ] Al exportar aparece `Preparando exportación`.
- [ ] La barra de progreso avanza con datos reales del bridge.
- [ ] `Pausar` pausa el job y `Reanudar` continúa.
- [ ] `Detener` solicita cancelación sin romper la UI.
- [ ] Al completar, aparecen archivos en `_SALIDA_PRO` o destino configurado.
- [ ] Los nombres generados conservan el sufijo esperado.
- [ ] Exportar a destino personalizado funciona si se configura ruta válida.
- [ ] Un destino inválido muestra error claro.
- [ ] Modo mock sigue simulando exportación sin bridge.
- [ ] No hay scroll global ni horizontal durante progreso.

## APP.8 — Gestión de errores y resultados

- [ ] Al completar exportación aparece un bloque de resultado en `Salida`.
- [ ] El resultado muestra estado, procesadas/total y destino.
- [ ] Los últimos archivos procesados son visibles.
- [ ] Las miniaturas exportadas muestran `Exportada`.
- [ ] Una exportación parcial muestra errores/avisos estructurados.
- [ ] `Revisar errores` filtra imágenes con error real o de exportación.
- [ ] Un destino personalizado vacío bloquea la exportación con mensaje claro.
- [ ] Detener exportación muestra estado controlado sin traceback.
- [ ] `Abrir destino` no se presenta como acción real mientras no exista integración nativa.
- [ ] Modo mock sigue mostrando resultados simulados.
- [ ] No cambia el output de imágenes.

## UX/UI principal — Saneamiento crítico

- [ ] La imagen seleccionada se ve completa por defecto.
- [ ] `Ajustar` es el modo visual inicial del visor.
- [ ] Una carpeta con muchas PNG muestra todas las válidas.
- [ ] El diagnóstico muestra archivos encontrados, válidos y omitidos.
- [ ] Las omisiones tienen motivo visible.
- [ ] No hay scroll vertical global.
- [ ] No hay scroll horizontal.
- [ ] El header normal no muestra URL, capabilities ni última respuesta técnica.
- [ ] `Debug` contiene modo mock/bridge y datos técnicos.
- [ ] El lote muestra miniaturas compactas.
- [ ] El inspector separa `Ajustes` y `Salida`.
- [ ] La barra inferior no duplica todos los estados.
- [ ] El inspector puede ocultarse y el visor gana espacio.
- [ ] Exportación se comunica como `Salida pendiente` si aún no está conectada.

## UX/UI principal — Rediseño profundo

- [ ] El visor central domina claramente sobre header, footer y paneles laterales.
- [ ] El header normal sólo muestra FlatShot, lote, contador, conexión resumida y acción principal.
- [ ] URL, capabilities, modo Mock/Bridge, health y controles técnicos sólo aparecen dentro de `Debug`.
- [ ] El panel izquierdo se lee como rail de lote, no como panel técnico.
- [ ] `Seleccionar carpeta` sigue visible, pero no domina cuando hay lote cargado.
- [ ] La lista de miniaturas mantiene tamaño estable al filtrar o seleccionar.
- [ ] Filtro sin resultados muestra un mensaje contextual y botón `Ver todas`.
- [ ] No parece que el lote esté vacío cuando sólo está filtrado.
- [ ] `Válidas`, `Avisos`, `Errores` y `Omitidas` se entienden como categorías distintas.
- [ ] `Ver diagnóstico` explica omisiones sin invadir el flujo principal.
- [ ] El visor muestra `Imagen n de m` y permite anterior/siguiente.
- [ ] Los controles `Ajustar`, `100%`, `Original`, `Procesada` y `Comparar` son discretos.
- [ ] El control de error simulado no aparece en modo usuario normal.
- [ ] El inspector separa `Ajustes` y `Salida` sin mostrar todo a la vez.
- [ ] El footer es fino, contextual y no duplica información técnica.
- [ ] La pantalla se siente como herramienta visual, no como dashboard de debug.

## Feedback a revisar

- [ ] Jerarquía visual.
- [ ] Claridad de acciones.
- [ ] Textos demasiado largos.
- [ ] Estados confusos.
- [ ] Información redundante.
- [ ] Elementos que sobran.
- [ ] Controles que parecen reales pero siguen siendo mock.
