# Bridge FlatShot Desktop

Placeholder de APP.1 para la futura capa de comunicacion entre el frontend moderno y el motor Python.

Decision actual:

- No hay API local activa.
- No hay sidecar Python todavia.
- No hay `src-tauri` todavia.
- No se duplica logica de imagen en frontend.

Contrato objetivo:

```text
frontend moderno
    ↓
Tauri IPC / bridge local
    ↓
servicios Python Qt-free
    ↓
motor FlatShot
```

Primeros comandos previstos:

- `health`
- `settings.get`
- `presets.list`
- `folders.scan`
- `preview.render`
- `export.prepare`
- `export.start`
- `export.pause`
- `export.resume`
- `export.cancel`
- `output.open`

