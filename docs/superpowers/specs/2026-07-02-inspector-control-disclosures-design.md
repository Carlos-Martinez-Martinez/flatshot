# Inspector Control Disclosures Design

## Objetivo

Los desplegables del inspector avanzado deben sentirse estables y previsibles al ajustar imagenes. El usuario debe poder trabajar con slider o introducir valores manuales sin que el panel se cierre, pierda foco, salte de scroll o refresque la preview por estados intermedios.

## Alcance

- Afecta a los controles numericos del inspector avanzado: aspecto del lote, ajustes tecnicos, luz Studio 2.5D y ajuste local por imagen.
- No cambia el pipeline de imagen ni los valores por defecto.
- No cambia el fondo de revision ni la configuracion de formatos de salida.

## Comportamiento

- Los desplegables del inspector conservan la seccion abierta despues de cualquier render provocado por un control interno.
- Un slider aplica el valor en vivo porque representa un gesto continuo.
- Un campo numerico permite edicion manual de valores parciales (`""`, `-`, `+`) sin aplicar cambios ni refrescar preview.
- Enter y blur confirman el valor manual. El valor confirmado se redondea, se limita a `min/max`, sincroniza el slider y refresca preview si realmente cambia.
- Escape cancela la edicion manual y restaura el valor confirmado anterior.
- Mientras un input numerico tiene foco, `renderSettings()` no debe sobrescribir su texto parcial.
- Los controles deshabilitados por motor de sombra o estado de lote no deben aceptar commits.

## Arquitectura

- Centralizar parsing, clamp, commit y cancelacion en un helper/controlador de controles numericos.
- Mantener la responsabilidad de aplicar valores en los workflows existentes:
  - ajustes de preset: `state.settings` + `markPresetDirty()`;
  - ajuste local: `setCurrentImageOverrideValue()`;
  - luz: `updateLightingSceneField()`.
- Evitar mover logica de procesamiento al UI.

## Pruebas

- Helper: valores parciales no hacen commit; Enter/blur clampa y redondea; Escape restaura.
- Integracion JS: el render no cierra la seccion avanzada recordada al editar un campo numerico.
- Integracion JS: un campo numerico enfocado conserva texto parcial durante `renderSettings()`.
- CSS/frontend: mantener auditoria CSS y contrato de carga.
