# QA Lab Production Parity Design

## Objetivo

FlatShot debe tener un flujo principal equivalente a produccion tambien durante el desarrollo. El modo dev no debe sustituir escaneo, previews ni estado de lote con datos mock cuando se valida el producto. Los estados mock quedan separados en un QA Lab claramente etiquetado para revisar pantallas visuales.

## Principios

- La app principal siempre usa el bridge real para importar carpetas, escanear, pedir previews y preparar exportacion.
- La entrada manual de ruta debe estar disponible tambien fuera de `devMode`, como alternativa secundaria al selector nativo de carpeta.
- Los escenarios mock no deben aparecer mezclados con las acciones principales de lote.
- El QA Lab puede cambiar estados visuales sin prometer paridad funcional.
- Los cambios no alteran el pipeline de imagen ni la salida exportada.

## UI

- Pantalla inicial de produccion:
  - mantiene `Seleccionar carpeta`;
  - muestra `Ruta manual` como `details` secundario para pegar una carpeta y escanear;
  - usa el mismo `scanBridgeFolder()` que el boton de actualizar.
- Topbar en dev:
  - elimina `Modo Mock` como alternativa de uso normal;
  - muestra herramientas de diagnostico y acceso a QA Lab;
  - mantiene health/check bridge y URL del bridge.
- QA Lab:
  - vive en un panel/modal de diagnostico separado;
  - contiene escenarios visuales como `Sin lote`, `Lote listo`, `Vista cargando`, `Exportacion completada`;
  - etiqueta claramente que son estados simulados;
  - no se usa para validar comportamiento productivo.

## Arquitectura

- Mantener `scanBridgeFolder()` como unica entrada de importacion real.
- Conservar `setScenario()` para QA Lab visual, no para el flujo principal.
- Separar acciones:
  - `scan-bridge-folder`, `pick-bridge-folder`: produccion;
  - `open-qa-lab`, `close-qa-lab`, `qa-scenario`: diagnostico visual.
- Guardar el estado `qaLabOpen` en memoria de UI, sin persistencia.

## Pruebas

- HTML/view tests:
  - la ruta manual aparece en la pantalla inicial sin depender de `devMode`;
  - `Lote mock` no aparece en acciones principales;
  - existe QA Lab con acciones de escenario etiquetadas.
- JS behavior tests:
  - `loadBatch()` no fabrica lote mock cuando no hay bridge real;
  - QA Lab usa `showReviewScenario()`/`setScenario()` de forma aislada;
  - `scanBridgeFolder()` sigue usando `/folders/scan`.
- Validacion manual:
  - app arranca;
  - ruta manual escanea una carpeta temporal por bridge real;
  - QA Lab abre/cierra y muestra escenarios visuales sin errores de consola.
