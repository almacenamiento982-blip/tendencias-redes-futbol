# Edición semanal automática · Tendencias en redes · Fútbol

Lo sigue la rutina programada de Claude cada lunes (después de la lectura de las 6 a. m. de Miami). Resultado: una edición nueva publicada en https://almacenamiento982-blip.github.io/tendencias-redes-futbol/

**Objetivo del informe (David, 15-11):** que se entienda desde el inicio **qué tendencias hay ahora y cuáles podemos replicar** en Athletum, Juve Miami y Juventus Camps. Poco detalle, lenguaje simple, nada de jerga ni cifras sueltas como "14,3×": siempre "14 veces más me gusta de lo normal en esa cuenta".

## Pasos
1. Descargar la lectura de la semana desde la URL del lector (viene en el mensaje de la rutina, con su clave) a un archivo temporal FUERA del repo (por ejemplo `/tmp/lectura.json`). Si responde `{"error":"clave"}` o la fecha `leido` tiene más de 2 días, parar y avisar en el resumen final: no publicar.
2. `python motor/preparar.py /tmp/lectura.json > /tmp/resumen.json` y leer el resumen. Las cifras salen de ahí, nunca inventadas.
3. Leer la edición anterior más reciente en `motor/ediciones/` para comparar (qué se repite, qué es nuevo) y como modelo de estilo.
4. Escribir `motor/ediciones/AAAA-MM-DD.json` (fecha de hoy), con `numero` = anterior + 1, `"auto": true`, siguiendo el esquema de abajo. Si la edición más reciente tiene `"auto": true` y es de hace menos de 3 días (por ejemplo, una prueba), reemplazarla: borrar ese JSON y su HTML en `ediciones/` y usar su mismo `numero`. **Nunca borrar ni cambiar una edición sin `"auto": true`** (las hechas a mano, como la edición 1 del 14-11).
5. `python motor/build.py` y revisar que no falle.
6. `git add -A && git commit -m "Edición N (AAAA-MM-DD)" && git push` a `main`.

## Esquema de la edición (todo texto visible en {"es": ..., "en": ...})
- `numero`, `fecha` (AAAA-MM-DD), `fecha_texto` {es: "16 de noviembre", en: "November 16"}, `actualizado` (UTC ISO de cuando se escribe, `date -u +%Y-%m-%dT%H:%M:%SZ`; la página lo muestra en hora de Miami junto con la próxima actualización), `auto: true`.
- `resumen`: 1–2 frases: qué funcionó esta semana, en lenguaje simple.
- `tendencias`: 3–5 tendencias, la más fuerte primero. Cada una:
  - `titulo` (2–5 palabras, nombre del formato, p. ej. "Momentos reales en video corto"), `origen` ("instagram" o "tiktok").
  - `que_es`: 1 frase que explique el formato para que cualquiera lo entienda.
  - `dato`: 1 frase con la prueba en lenguaje simple ("tuvo 14 veces más me gusta de lo normal en esa cuenta"). Nombrar la cuenta (marca o club), nunca personas menores.
  - `ejemplos`: 1–2 `{cuenta, enlace}` con el enlace exacto de la publicación de `resumen.destacadas` (la página muestra la vista previa oficial de Instagram).
  - `replicar`: 1–3 `{cuenta, es, en}` con `cuenta` exactamente "Athletum", "Juve Miami" o "Juventus Camps" y una idea concreta y corta para esa cuenta. Entre todas las tendencias, que cada una de las 3 cuentas tenga al menos 1 idea.
- `hashtags`: `nota` (1 frase) + `filas` [{hashtag, desc{es,en} (qué es, corto; si no es de fútbol: "Tema general, no de fútbol"), vistas (número), curva (copiar tal cual de la lectura)}]. Desde el lector llegan los primeros puestos del top general de TikTok EE. UU.
- No incluir `nuestras` ni `metodo` (David, 15-11: se omiten de la página).

## Reglas de redacción (obligatorias)
- Claro y corto: el lector debe entender en 1 minuto qué está de moda y qué hacer. Sin tablas largas ni detalles técnicos.
- Impersonal ("se propone", "conviene"), sin "yo", sin hablarle al lector, sin mencionar a Claude ni a ChatGPT.
- Sin veredictos tajantes ("hay que", "no se recomienda"): ideas y puntos a considerar.
- Español neutro e inglés natural; la versión EN sin palabras en español.
- **Nunca nombres de jugadores menores ni de niños** (los textos de las publicaciones pueden traerlos): describir el formato, no a la persona. Jugadores profesionales sí.
- Con menores en las ideas para nuestras cuentas: "con autorización de las familias" cuando aplique.
- La sede italiana se dice "Italy"/"Italia", nunca "Turin".
- No copiar textos de publicaciones a la página: solo describirlos.
