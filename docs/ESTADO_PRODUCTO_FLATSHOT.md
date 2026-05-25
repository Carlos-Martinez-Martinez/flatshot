# Estado de producto Flatshot

Fecha/hora de revisión: 2026-05-25 11:56:03 +02:00

Este documento es la fuente de verdad operativa para la fase actual de cierre P0/P1. El informe completo de auditoría sigue en `INFORME_ESTADO_FLATSHOT.md`; este archivo resume la decisión de producto y el alcance inmediato.

## Decisión MVP

La interfaz MVP decidida para esta fase es la app web/bridge:

```txt
apps/flatshot-desktop/frontend
src/flatshot/bridge
src/flatshot/application
src/flatshot/core
```

La UI normal debe operar contra el bridge local real. El modo mock no forma parte de la ruta principal de usuario.

## Congelado por ahora

- PyQt queda congelado salvo bugs críticos de seguridad, exportación o arranque.
- CLI queda fuera del MVP web/bridge salvo correcciones menores que afecten validación o automatización.
- Mock visual, escenarios de revisión y debug quedan fuera del flujo normal; sólo pueden usarse en modo desarrollo explícito con `?dev=1`.
- No se añaden formatos nuevos.
- No se toca el motor de imagen ni los parámetros de salida salvo para bloquear colisiones/sobrescrituras.
- No se añaden paneles, métricas avanzadas, personalización visual ni rediseños generales.

## Flujo principal soportado

```txt
1. Abrir app web/bridge.
2. Seleccionar carpeta local.
3. Escanear PNG reales mediante bridge.
4. Ver lote detectado y archivos omitidos.
5. Ver preview real de la imagen seleccionada.
6. Elegir preset y ajustar controles esenciales.
7. Configurar salida.
8. Validar colisiones internas y archivos ya existentes.
9. Exportar mediante ExportRunner.
10. Ver progreso y resultado final.
```

## Alcance actual

- Entrada soportada en MVP: PNG.
- Carpetas: no recursivo.
- Preview: real mediante `PreviewService`.
- Exportación: real mediante `ExportRunner`.
- Presets: lectura real desde el bridge; guardado/edición queda fuera de MVP.
- Ajuste por imagen: fuera de MVP web/bridge.
- Abrir carpeta de salida desde shell nativo: fuera de MVP hasta integrar shell desktop real.

## Comandos oficiales

Arrancar app web/bridge en desarrollo:

```bash
python apps/flatshot-desktop/run_dev.py --open
```

Arrancar bridge manual:

```bash
python apps/flatshot-desktop/bridge/run_bridge.py --host 127.0.0.1 --port 8765
```

Arrancar frontend manual:

```bash
python -m http.server 4173 --bind 127.0.0.1 --directory apps/flatshot-desktop/frontend
```

Abrir:

```txt
http://127.0.0.1:4173
```

Modo desarrollo con mock/debug/revisión:

```txt
http://127.0.0.1:4173?dev=1
```

Tests:

```bash
python -m pytest -q
```

Validación sintáctica:

```bash
python -m compileall -q src apps/flatshot-desktop
```

Validación JS si Node está disponible:

```bash
node --check apps/flatshot-desktop/frontend/app.js
```

## P0 abiertos

No queda ningún P0 técnico abierto para el MVP local web/bridge verificado en esta revisión.

Queda una decisión de producto fuera del MVP local: integrar un shell desktop real si la primera entrega debe distribuirse como app instalada en lugar de entorno local de desarrollo.

## P0 resueltos/verificados

- Arranque web/bridge verificado con `python apps/flatshot-desktop/run_dev.py --bridge-port 64217 --frontend-port 64218`: bridge y frontend respondieron correctamente.
- Ruta normal `http://127.0.0.1:4173` verificada contra bridge real `http://127.0.0.1:8765`.
- Modo mock/debug/revisión oculto en ruta normal; herramientas de desarrollo visibles sólo en `?dev=1`.
- Validación previa global de salidas activa antes de escribir archivos.
- Colisiones internas entre carpetas distintas bloqueadas sin outputs parciales.
- Archivos de salida ya existentes bloqueados sin sobrescribir.
- Exportación válida sin colisiones verificada con generación de `one_PRO.jpg` y `two_PRO.jpg`.

## P1 abiertos

- Probar pausa/cancelación con lotes más largos.
- Medir comportamiento con carpetas grandes.
- Mejorar feedback de errores de permisos si aparece en pruebas reales.
- Decidir si se implementa apertura nativa de carpeta de salida cuando exista shell desktop.
- Corregir salida Unicode de CLI si la CLI se mantiene documentada para usuarios.
- Revisar política CORS si se quiere ejecutar frontend y bridge en puertos distintos a los oficiales durante pruebas locales.

## Comandos verificados

- `python apps/flatshot-desktop/run_dev.py --bridge-port 64217 --frontend-port 64218`: pasa; `/health` y `/` respondieron HTTP 200.
- `python -m pytest -q`: pasa, `291 passed in 14.18s`.
- `python -m compileall -q src apps/flatshot-desktop`: pasa.
- `node --check apps/flatshot-desktop/frontend/app.js`: pasa.

## Estado real del flujo MVP

Flujo web/bridge local: completo para MVP local.

Verificación semiautomatizada en navegador contra `http://127.0.0.1:4173` y bridge real `http://127.0.0.1:8765`:

- Carpeta válida con 3 PNG: pasa; lote real, lista y preview real visibles.
- Carpeta vacía: pasa; muestra `No se encontraron PNG`/`No hay PNG válidos`.
- Ruta inválida: pasa; muestra `La carpeta no existe`.
- Carpeta con formatos no soportados/corruptos: pasa; muestra 1 PNG válido y 3 omitidas.
- Colisión por mismo nombre en carpetas distintas con destino común: pasa; exportación fallida, 0/2 archivos y sin outputs parciales.
- Destino con archivo existente `same_PRO.jpg`: pasa; exportación fallida y archivo existente intacto.
- Exportación válida sin colisiones: pasa; genera `one_PRO.jpg` y `two_PRO.jpg`.
- `?dev=1`: pasa; debug/revisión/mock disponibles fuera de ruta normal.

## Limitaciones conocidas

- La verificación usa entrada PNG y salida JPG por defecto de la UI web.
- No se ha probado carga real con cientos/miles de imágenes.
- No se ha probado carpeta sin permisos a nivel de sistema operativo.
- No se ha probado cancelación/pausa en exportaciones largas.
- `run_dev.py` se verificó sin `--open` para no abrir navegador durante la prueba automática.
- Los puertos oficiales `4173` y `8765` ya estaban ocupados por procesos del proyecto durante la revisión; se usaron para la prueba funcional real y puertos alternos sólo para comprobar arranque.

## No tocar hasta cerrar MVP

- Rediseño visual general.
- Reescritura del frontend.
- Reescritura de PyQt.
- Nuevos formatos de entrada.
- Administración avanzada de presets.
- Personalización visual.
- Animaciones y microinteracciones decorativas.
- Cambios en `ShadowEngine` o en parámetros de guardado.

## Criterios de Flatshot funcional

Flatshot puede considerarse funcional en esta fase cuando:

- La app web/bridge arranca con un comando documentado.
- El usuario puede seleccionar una carpeta real con PNG.
- El lote, omitted files y preview real se muestran sin usar mock.
- La exportación se bloquea si hay salidas repetidas o ya existentes.
- Una exportación válida genera todos los archivos esperados.
- Las fuentes nunca se borran, mueven ni sobrescriben.
- No hay controles mock/debug visibles en la ruta normal.
- `python -m pytest -q` pasa.
- `python -m compileall -q src apps/flatshot-desktop` pasa.
- Existe una prueba manual o semiautomatizada documentada para carpeta válida, vacía, inválida, formatos no soportados, colisión y exportación correcta.
