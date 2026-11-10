# Test de oposición C1 AGE: Constitución Española

Exámenes tipo test del Bloque I con todas las respuestas explicadas: Constitución de 1978, Corona, Cortes Generales, Poder Judicial, Gobierno, Hacienda y organización territorial. 318 preguntas en seis temas.

Se publica tal cual en GitHub Pages: no necesita compilar nada. Solo hay que subir `index.html`, `favicon.svg`, `css`, `js`, `data` e `img`.

La pantalla principal tiene dos pestañas: Examen y Apuntes. No hay supuestos.

## De dónde salen las preguntas

Todas vienen de la página antigua, que se guarda como `constitucion_fuente.html`: cada pregunta con su respuesta, el precepto literal del BOE, por qué fallan las otras tres y, a veces, un truco o un ojo.

1. `python3 tools/extraer.py` lee esa página y deja las preguntas en `tools/preguntas.json`.
2. `python3 tools/construir.py` las reparte por temas y bloques y escribe `data/tema1.js` a `data/tema6.js`. Los temas y bloques están en `TEMAS`, dentro del mismo script. También corrige las erratas de `ERRATAS`.

En Examen, la procedencia tiene dos opciones: **Oficiales del C1** (las 57 de los exámenes del INAP de 2022 a 2026) y **Otras administraciones** (las de Constitución de tests y exámenes de otros cuerpos).

## Lo que más cae

Las marcas están en `tools/marcas.py` y salen de cruzar dos cosas: las listas de artículos más preguntados que publican las academias y webs de test (coinciden en los arts. 1, 2, 14, 53 y 168, y después en derechos fundamentales, estados excepcionales, Corona, fuentes, investidura, Poder Judicial y territorio) y las preguntas oficiales del INAP del banco. Hay tres niveles:

- **Estrella de examen**: está en casi todas las listas y ha caído en el INAP.
- **Clave de examen**: está en las listas o ha caído en el INAP.
- **Poco preguntado**: no está en ninguna lista ni ha salido en las oficiales del banco (detalle de la LOTC, la LOPJ y el Reglamento del Congreso).

Cada marca va atada a artículos de la Constitución o a una ley, y `construir.py` se la pone a las preguntas que los citan. En Examen, la casilla «Solo estrella y clave de examen» deja solo esas. Para cambiar una marca se edita `MARCAS` y se vuelve a ejecutar `construir.py`.

## Estadísticas

Cada tema y bloque muestra preguntas dominadas, falladas y pendientes. En Examen solo salen las pendientes: una acertada ya no vuelve a salir y una fallada solo sale en «Repasar solo las falladas». «Reiniciar estadísticas» lo pone todo a cero. Todo se guarda en el navegador con claves `constitucion-*`, para no mezclarse con otros tests publicados en el mismo dominio.

## Apuntes

40 esquemas propios, en hoja A4 apaisada y con el mismo estilo que los de contratos, ordenados por temas y con buscador por tema o por artículo (por ejemplo 99 o Corona). Hay de varios tipos: líneas de tiempo, diagramas de flujo, organigramas, tablas comparativas, mapas mentales, diagramas de Venn, cuadros sinópticos, barras e infografías de cifras.

En la justificación de cada pregunta aparece «Consultar apuntes» con los esquemas que cubren sus artículos (hasta 4, primero los más concretos). Se regeneran con:

```bash
python3 tools/nuevos/generar.py          # todas las hojas, a PNG con Chrome
python3 tools/nuevos/generar.py tc-159   # solo algunas
python3 -I tools/esquemas.py             # las pasa a WebP y escribe data/esquemas.js
```

Hace falta Google Chrome y Pillow. Cada hoja es una función de `tools/nuevos/generar.py` (estilos en `base.css` y `ce.css`). Qué artículos cubre cada esquema y en qué bloque de Apuntes sale se decide en `ESQ` y `APUNTES`, dentro de `tools/esquemas.py`. Después de cambiar algo, sube el número `?v=` en `index.html` para que el móvil no use la versión guardada.

## Movimiento

Las animaciones van en `js/movimiento.js`, con GSAP 3.13 y su plugin Flip copiados en `js/vendor/` (sin CDN). Con «reducir movimiento» activado en el sistema no se anima nada, y si GSAP no carga la app funciona igual.
