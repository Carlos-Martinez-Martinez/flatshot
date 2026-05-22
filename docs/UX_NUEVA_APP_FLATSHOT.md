# UX NUEVA APP FLATSHOT

## 1. Principios UX

La nueva app debe sentirse:

- clara;
- moderna;
- de escritorio;
- visual;
- rapida;
- orientada a flujo;
- densa sin ser caotica;
- profesional;
- segura para trabajar con lotes.

Principios operativos:

- El lote es el punto de partida.
- La preview central es la zona de confianza.
- El preset activo debe verse siempre.
- Los ajustes principales deben estar a mano.
- Los ajustes avanzados deben existir, pero no competir con el flujo.
- Exportacion debe mostrar de un vistazo que se va a generar, donde y con que nombre.
- El progreso solo aparece cuando hay trabajo real o preparacion real.
- Los errores deben ser breves en superficie y detallados bajo demanda.
- No se deben mostrar rutas completas como contenido principal si rompen el layout.

## 2. Flujo principal

Estado inicial:

- Se muestra una pantalla de trabajo vacia, no una landing.
- Accion principal: `Añadir carpeta`.
- Panel de lote preparado para recibir carpetas.
- Preview central con estado `Sin imagen seleccionada`.
- Panel derecho con `Preset`, ajustes principales y exportacion desactivada hasta tener imagenes.

Añadir carpeta:

- El usuario elige una o varias carpetas.
- La app muestra `Escaneando...` con estado breve.
- No se bloquea la ventana.

Escaneo:

- Se cuentan PNG validos.
- Se registran carpetas vacias o inaccesibles.
- Se selecciona la primera imagen valida si existe.
- Si no hay PNG validos, el estado visible es `No hay PNG válidos`.

Seleccion de imagen:

- El panel de lote permite cambiar de imagen rapidamente.
- La seleccion actual queda clara por nombre corto, miniatura o marcador.
- El nombre completo queda disponible en tooltip o detalle.

Preview:

- La imagen seleccionada se renderiza en el centro.
- Durante carga se muestra `Generando preview`.
- Si hay warning del motor, aparece como aviso no bloqueante.
- El usuario puede comparar original/procesada, ajustar zoom y alternar fondo.

Preset:

- El preset activo se muestra en top bar y panel de ajustes.
- Cambiar preset actualiza preview.
- Guardar o administrar presets no domina la vista principal.

Ajuste:

- Ajustes principales visibles: opacidad, blur, distancia, padding y escala si procede.
- Sombras avanzadas quedan plegadas.
- Si hay ajustes por imagen, se indica en la imagen y se puede resetear.

Configuracion de exportacion:

- Formato, tamano, destino y naming se ven como resumen compacto.
- Los detalles se editan en panel lateral o drawer, no como interrupcion innecesaria.
- La app muestra `Listo para procesar` solo si hay lote, salidas activas y destino valido.

Exportacion:

- Boton principal: `Procesar X imágenes`.
- Durante el proceso se bloquean cambios que puedan invalidar la exportacion.
- Se muestra `Procesando 8/23` u otro estado real.
- Pausa, reanudar y detener estan disponibles cuando el runner lo permita.

Resultado:

- Al terminar se muestra resumen de exportados, errores y destino.
- Accion visible: `Abrir destino`.
- El estado vuelve a permitir otro lote.

Errores parciales:

- El flujo no falla por una imagen si el runner puede continuar.
- Se muestra cantidad de errores y una lista filtrable o expandible.
- El detalle tecnico queda en panel de errores/log.

Continuar con otro lote:

- El usuario puede limpiar el lote o añadir otro.
- La exportacion anterior conserva acceso a destinos recientes hasta que se cierre o se reemplace el lote.

## 3. Layout conceptual

Layout propuesto:

```text
┌──────────────────────────────────────────────────────────────┐
│ Top bar: lote activo · preset · estado · acciones generales  │
├───────────────┬──────────────────────────────┬───────────────┤
│ Lote          │ Preview principal            │ Ajustes       │
│ carpetas      │ imagen seleccionada          │ preset        │
│ imagenes      │ comparacion / zoom / fondo   │ sombras       │
│ filtros       │ warnings                     │ exportacion   │
├───────────────┴──────────────────────────────┴───────────────┤
│ Barra inferior: progreso · errores · destino · accion final  │
└──────────────────────────────────────────────────────────────┘
```

Razonamiento:

- El lote queda a la izquierda porque es navegacion de trabajo.
- La preview ocupa el centro porque define confianza visual.
- Los ajustes y exportacion quedan a la derecha porque modifican la salida.
- La barra inferior concentra estado y accion final sin competir con preview.

## 4. Zonas funcionales

### Panel de lote

Debe resolver:

- carpetas cargadas;
- imagenes encontradas;
- imagenes ajustadas;
- errores de carpeta;
- seleccion rapida;
- miniaturas o lista compacta;
- filtro por todas, ajustadas, errores;
- truncado estable de nombres;
- tooltip o detalle para rutas completas.

Estados internos:

- `Sin lote`;
- `Escaneando`;
- `24 PNG`;
- `2 ajustadas`;
- `1 carpeta con errores`.

### Preview central

Debe resolver:

- imagen seleccionada;
- preview grande;
- estado de carga;
- warnings;
- comparacion original/procesada;
- zoom;
- pan;
- fondo transparente o color;
- posible checkerboard;
- seleccion visible de variante si hay salidas multiples.

La preview no debe:

- recalcular por cada cambio menor si hay debounce pendiente;
- mostrar controles tecnicos como contenido principal;
- ocultar errores de render.

### Panel de ajustes

Debe resolver:

- preset activo;
- presets disponibles;
- ajustes principales;
- ajustes avanzados;
- reset de ajustes;
- guardar preset;
- ajustes por imagen si existen;
- indicacion clara de override local.

Estructura recomendada:

- `Preset`
- `Aspecto`
- `Sombra`
- `Avanzado`
- `Exportación`

`Avanzado` debe estar plegado por defecto.

### Exportacion

Debe resolver:

- formato;
- tamano;
- destino;
- naming;
- salidas activas;
- resumen claro;
- boton principal;
- progreso;
- errores;
- resultado final.

Resumen compacto esperado:

```text
JPG · 1800x2400 · Web RGB230 · {original}{suffix}
Destino: origen / _SALIDA_PRO
```

## 5. Estados vacios

Sin carpeta:

- Estado: `Añade una carpeta`.
- Accion: `Añadir carpeta`.
- No mostrar controles de exportacion como listos.

Carpeta sin imagenes:

- Estado: `No hay PNG válidos`.
- Mostrar carpeta afectada y permitir quitarla.

Sin imagen seleccionada:

- Estado: `Sin imagen seleccionada`.
- Preview central sin render.

Preview cargando:

- Estado: `Generando preview`.
- Reservar espacio para evitar saltos.

Error de preview:

- Estado: `No se pudo generar preview`.
- Accion secundaria: `Ver detalle`.

Sin preset:

- Estado: `Sin preset`.
- Usar ajustes por defecto si el motor lo permite.
- No bloquear lote solo por no elegir preset.

Exportacion no configurada:

- Estado: `Configura exportación`.
- Indicar solo el primer bloqueo: destino, salida activa o tamano invalido.

Exportacion en curso:

- Estado: `Procesando 8/23`.
- Acciones: pausar, detener si estan soportadas.

Exportacion completada:

- Estado: `Exportación completada`.
- Accion: `Abrir destino`.

Exportacion con errores:

- Estado: `Exportación con errores`.
- Mostrar conteo y acceso a detalle.

## 6. Microcopy

Estilo:

- breve;
- operativo;
- sin sobreexplicar;
- sin tono tutorial;
- sin mensajes tecnicos innecesarios;
- orientado a accion.

Ejemplos buenos:

- `Preset`
- `Aspecto`
- `Imagen seleccionada`
- `Lote`
- `Exportación`
- `Destino`
- `Procesar 24 imágenes`
- `Listo para procesar`
- `No hay PNG válidos`
- `Generando preview`
- `Procesando 8/23`
- `Pausado`
- `Deteniendo...`
- `Abrir destino`
- `2 errores`

Ejemplos malos:

- `Opciones`
- `Más`
- `Editar...`
- `Configuración avanzada de parámetros técnicos del motor`
- `Pulse aquí para comenzar a seleccionar una carpeta de imágenes`
- `Ha ocurrido una excepción no controlada en el subsistema de renderizado`
- `La operación ha finalizado satisfactoriamente con código de retorno cero`

Regla de detalle:

- La superficie muestra accion y estado.
- El detalle tecnico vive en tooltip, drawer de errores o log.

