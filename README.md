# FlatShot
Procesador de imágenes de producto con generación de sombras realistas y flujo de trabajo listo para e-commerce (percha/maniquí). Incluye interfaz moderna en PyQt6 y CLI para automatización en lote.

## Qué hace
- Motor de sombras multicapa (`ShadowEngine`) con ruido, AO, blur de contacto y zoom adaptativo según proporción y luminancia del producto.
- Interfaz gráfica con previsualización en vivo, comparador original/procesado, cuadrícula de miniaturas y barra de herramientas flotante.
- Cola de carpetas con controles de iniciar/pausar/reanudar/detener, progreso por carpeta y log de errores.
- Presets categorizados (ropa clara/oscura, complementos, personalizados) con migración desde formatos antiguos y editor de curva geométrica para escalar productos según su aspecto.
- Exportación configurable: tamaño objetivo, formato (JPG/PNG), fondo transparente o color, plantilla de nombres, sufijo y carpeta de destino (subcarpeta o ruta personalizada).
- CLI (`flatshot list-presets`, `flatshot process ...`) para integraciones en scripts y CI.

## Requisitos
- Python 3.10 o superior.
- Dependencias: PyQt6, Pillow, numpy, pydantic, qtawesome (ver `requirements.txt`).
- Sistema operativo: Windows, macOS o Linux con soporte Qt.

## Instalación rápida
1) Clona o descarga el proyecto y abre una terminal en `flatshot/`.  
2) Crea y activa un entorno virtual:
   - Windows: `python -m venv .venv && .\.venv\Scripts\activate`
   - macOS/Linux: `python3 -m venv .venv && source .venv/bin/activate`
3) Instala en modo editable: `pip install -e .`
4) Alternativa: usa los scripts `scripts/install.bat` o `scripts/install.sh`.

## Ejecución (GUI)
- Lanza la aplicación:
  - Recomendado (sin depender de instalación editable): `python main.py`
  - Alternativa: `python -m flatshot` (o `flatshot` si está en el PATH tras la instalación con `pip install -e .`).
  - Scripts rápidos: `scripts/run.bat` (Windows) / `scripts/run.sh` (macOS/Linux).
- Si aparece `No module named flatshot`, estás usando un entorno virtual distinto al del proyecto.
  - Windows: `.\venv\Scripts\python.exe main.py`
  - macOS/Linux: `./venv/bin/python main.py`
- Flujo típico:
  1) Añade una o varias carpetas con PNG recortados (fondo transparente).  
  2) Elige un preset y ajusta los deslizadores: ángulo, distancia, blur, spread, fusión, opacidad, ruido, padding y blur de contacto.  
  3) Ajusta la curva de escala con “Calibrar escala” para controlar cuánto espacio ocupa cada tipo de aspecto (vertical → horizontal).  
  4) Configura la exportación (formato, tamaño, fondo, sufijo, plantilla de nombres y destino).  
  5) Lanza la cola. Puedes pausar/reanudar o detener en cualquier momento.

## Uso por CLI
- Listar presets disponibles:  
  `flatshot list-presets`
- Procesar una carpeta (solo archivos PNG dentro de la carpeta):  
  ```bash
  flatshot process \
    --input RUTA/DE/ENTRADA \
    --preset "Luz cenital" \
    --output _SALIDA_CLI \
    --size 1800x2400 \
    --format JPG \
    --suffix _PRO \
    --template "{original}{suffix}" \
    --dry-run
  ```
- Parámetros relevantes:
  - `--size`: `ANCHOxALTO` (por defecto 1800x2400).
  - `--format`: `JPG` o `PNG` (JPG fuerza RGB, PNG respeta transparencia).
  - `--template`: placeholders `{original}`, `{suffix}`, `{folder}`, `{index}` o `{index:03d}`.
  - `--output`: nombre de la subcarpeta de salida (default `_SALIDA_CLI`).
  - `--dry-run`: muestra el plan sin procesar ni crear archivos.

## Presets y configuración
- Los presets se guardan en el directorio de configuración que proporciona Qt (`QStandardPaths.AppConfigLocation`), archivo `presets_v2.json` (se migra automáticamente desde `presets.json` si existe).
- Categorías por defecto: `Ropa Clara`, `Ropa Oscura`, `Complementos` y `Personalizados`.
- Puedes importar/exportar presets desde el menú `Presets` o desde `Archivo`. El archivo exportado (`.json`) sirve para mover tus presets a otro ordenador y volver a cargarlos allí.
- El historial de ajustes (undo/redo) se gestiona internamente y se evita duplicar estados idénticos.

## Exportación y nomenclatura
- Configuración por defecto: carpeta `_SALIDA_PRO`, sufijo `_PRO`, formato JPG, tamaño 1800x2400, fondo gris (230,230,230) y plantilla `{original}{suffix}`.
- Puedes activar fondo transparente (`transparent_bg`) o definir color personalizado (`bg_color`).
- Destino: subcarpeta junto a la carpeta origen o ruta externa personalizada.
- Plantilla de nombres soporta placeholders `{original}`, `{suffix}`, `{folder}`, `{index}` y `{index:NNd}` para padding numérico.

## Sesión y logs
- El estado de la sesión (ventana, carpetas recientes, preset activo, splitter, export config y ajustes de sombra) se guarda en `~/.flatshot/session.json`.
- Los logs diarios de exportación viven en `AppConfigLocation/logs/flatshot_YYYY-MM-DD.log`.  
- Si la GUI se bloquea, el hook global escribe en `logs/app_crash.log` (dentro del proyecto) y en un fichero temporal de respaldo.

## Estructura del proyecto
- `src/flatshot/` código fuente (motor, UI, workers, utilidades).
- `scripts/` instaladores y arranque para Windows/macOS/Linux.
- `tests/` suite de pytest (motor, CLI, historial, modelos).
- `logs/` carpeta local para crash logs (la app crea su propia carpeta de logs de runtime en AppConfigLocation).

## Desarrollo
- Ejecuta la suite: `pytest` desde la raíz del proyecto.
- Entry point CLI/GUI: `flatshot` (registrado vía `project.scripts` en `pyproject.toml`).
- Recomendado: activar entorno virtual antes de desarrollar (`.venv`), y mantener `requirements.txt` sincronizado si añades dependencias.
