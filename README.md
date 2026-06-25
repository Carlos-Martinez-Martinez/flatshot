# FlatShot

FlatShot prepara imágenes de producto por lotes desde tu propio equipo. Importa
una carpeta, aplica un ajuste de aspecto y exporta copias finales sin modificar
las imágenes originales.

## Cómo funciona

1. Eliges una carpeta con imágenes PNG.
2. FlatShot crea el lote y muestra una vista previa.
3. Seleccionas un ajuste de aspecto.
4. Revisas la imagen seleccionada y posibles avisos del lote.
5. Configuras la carpeta de destino.
6. Procesas el lote y FlatShot guarda los archivos finales.

## Instalar

### Si tienes la versión portátil

No necesitas instalar nada. Abre:

```text
release\FlatShotPortable\Abrir FlatShot.vbs
```

FlatShot se abrirá en una ventana local. Si esa ventana no puede iniciarse, se
abrirá en el navegador.

### Si partes del proyecto

Necesitas Python 3.10 o superior.

En Windows:

```bat
scripts\install.bat
```

En macOS o Linux:

```bash
./scripts/install.sh
```

Cuando termine la instalación, abre FlatShot con:

```bat
scripts\run.bat
```

En macOS o Linux:

```bash
./scripts/run.sh
```

## Crear la versión portátil

Desde la carpeta del proyecto:

```powershell
python scripts\build_portable.py
```

La versión portátil se genera en:

```text
release\FlatShotPortable
```

## Uso básico

- Importa una carpeta con imágenes PNG.
- Elige un ajuste de aspecto.
- Ajusta el resultado si hace falta.
- Revisa la vista previa y los avisos.
- Elige la carpeta de destino.
- Procesa el lote.

## Qué conserva FlatShot

- Las imágenes originales no se sobrescriben.
- Los archivos exportados se guardan en la carpeta de destino configurada.
- La exportación mantiene el comportamiento definido por la aplicación para
  tamaño, formato, transparencia, calidad y nombre de archivo.

## Comprobar el proyecto

```bash
pytest
```

Si cambia la interfaz o la exportación, abre FlatShot y revisa al menos una
carpeta vacía y una carpeta con imágenes PNG.
