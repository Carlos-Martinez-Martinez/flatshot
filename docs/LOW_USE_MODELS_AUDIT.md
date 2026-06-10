# Auditoria de modelos de bajo uso

Esta nota registra decisiones de compatibilidad para simbolos que parecen heredados o poco usados. No elimina codigo ni cambia comportamiento.

## `JobItem`

Ubicacion:

- `src/flatshot/core/models.py`
- `tests/test_models.py`

Busqueda ejecutada:

```powershell
rg -n "\bJobItem\b" .
```

Resultado actual:

- El modelo esta definido en `src/flatshot/core/models.py`.
- La cobertura directa esta en `tests/test_models.py`.
- No aparece en los flujos activos de bridge/exportacion (`BridgeExportJob`, `ExportJobRequest`, `ExportJobResult`) ni en el frontend web.

Decision:

- Conservar `JobItem` por ahora.
- Tratarlo como contrato legacy o reservado hasta confirmar si hay scripts externos, configuraciones antiguas o documentacion operativa que dependan de el.
- No reutilizarlo para nuevos flujos de exportacion: el camino activo usa `src/flatshot/application/contracts.py` y `src/flatshot/bridge/export_jobs.py`.
- No eliminarlo sin una tarea dedicada que actualice tests y documente compatibilidad.

Riesgo:

- Bajo en mantenimiento diario, porque no participa en el flujo principal.
- Medio en compatibilidad si se borra sin revisar consumidores externos.

Proxima decision posible:

- Si una revision futura confirma que no hay consumidores externos, marcarlo como deprecated en docstring o moverlo a una seccion de contratos legacy antes de eliminarlo.
