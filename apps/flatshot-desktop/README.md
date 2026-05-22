# FlatShot Desktop

Prototipo navegable de la nueva app moderna de FlatShot.

Estado actual:

- APP.2 completada como mock de UX.
- Frontend estático en HTML/CSS/JS vanilla.
- Sin `package.json`, Tauri, Rust, Node obligatorio ni dependencias nuevas.
- Sin conexión al motor Python.
- La app PyQt legacy sigue intacta.

## Cómo abrirlo

Opción directa:

```text
apps/flatshot-desktop/frontend/index.html
```

Opción recomendada para revisar en navegador:

```bash
python -m http.server 4173 --bind 127.0.0.1 --directory apps/flatshot-desktop/frontend
```

Abrir:

```text
http://127.0.0.1:4173
```

## Estados mock incluidos

El selector `Demo` permite recorrer sin editar código:

- sin lote;
- lote listo;
- carpeta sin PNG válidos;
- preview cargando;
- preview con aviso;
- error de preview;
- destino sin configurar;
- exportación lista;
- exportación en curso;
- exportación completada;
- exportación completada con errores parciales;
- exportación fallida.

También hay interacciones simuladas para:

- añadir y limpiar lote;
- buscar y filtrar imágenes;
- seleccionar imagen;
- cambiar modo de preview;
- cambiar fondo y zoom;
- cambiar preset;
- modificar ajustes principales;
- abrir ajustes avanzados;
- alternar ajuste por imagen;
- cambiar formato, tamaño, fondo, destino y naming;
- iniciar, pausar, reanudar y detener exportación mock;
- revisar errores;
- abrir destino simulado.

## Qué no está conectado

Todavía no existe:

- Tauri;
- backend Python sidecar;
- bridge real;
- selector nativo de carpetas;
- escaneo real;
- preview real;
- presets reales;
- configuración real;
- exportación real;
- apertura real de carpeta de salida.

El frontend no procesa imágenes ni duplica lógica del motor.

## Siguiente paso

APP.3 — Bridge/backend mínimo.

La siguiente tanda debe definir un contrato mínimo de comunicación con Python sin activar todavía exportación real completa ni empaquetado.
