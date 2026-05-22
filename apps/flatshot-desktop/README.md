# FlatShot Desktop

Scaffold inicial de la nueva app moderna de FlatShot.

Estado actual:

- APP.1 solamente.
- Frontend mock estatico.
- Sin conexion real al motor.
- Sin Tauri, Rust, Node ni dependencias nuevas todavia.
- La app PyQt legacy sigue intacta.

Como verlo:

1. Abre `frontend/index.html` directamente en el navegador.
2. Opcional: sirve la carpeta con `python -m http.server 4173 -d apps/flatshot-desktop/frontend`.
3. Abre `http://127.0.0.1:4173`.

Siguiente paso previsto:

- APP.2: convertir el mock en UI navegable completa con estados simulados.
- APP.3: definir el bridge minimo hacia servicios Python.

