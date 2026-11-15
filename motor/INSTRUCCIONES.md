# Edición semanal automática · Tendencias en redes · Fútbol

Lo sigue la rutina programada de Claude cada lunes (después de la lectura de las 6 a. m. de Miami). Resultado: una edición nueva publicada en https://almacenamiento982-blip.github.io/tendencias-redes-futbol/

## Pasos
1. Descargar la lectura de la semana desde la URL del lector (viene en el mensaje de la rutina, con su clave) a un archivo temporal FUERA del repo (por ejemplo `/tmp/lectura.json`). Si responde `{"error":"clave"}` o la fecha `leido` tiene más de 2 días, parar y avisar en el resumen final: no publicar.
2. `python motor/preparar.py /tmp/lectura.json > /tmp/resumen.json` y leer el resumen. Las cifras salen de ahí, nunca inventadas.
3. Leer la edición anterior más reciente en `motor/ediciones/` para comparar (qué se repite, qué es nuevo).
4. Escribir `motor/ediciones/AAAA-MM-DD.json` (fecha de hoy), con `numero` = anterior + 1, `"auto": true`, siguiendo el esquema de abajo. Si la edición más reciente tiene `"auto": true` y es de hace menos de 3 días (por ejemplo, una prueba), reemplazarla: borrar ese JSON y su HTML en `ediciones/` y usar su mismo `numero`. **Nunca borrar ni cambiar una edición sin `"auto": true`** (las hechas a mano, como la edición 1 del 14-11).
5. `python motor/build.py` y revisar que no falle.
6. `git add -A && git commit -m "Edición N (AAAA-MM-DD)" && git push` a `main`.

## Esquema de la edición (todo texto visible en {"es": ..., "en": ...})
- `numero`, `fecha` (AAAA-MM-DD), `actualizado` (fecha y hora UTC en ISO de cuando se escribe la edición, p. ej. `date -u +%Y-%m-%dT%H:%M:%SZ`; la página la muestra en hora de Miami junto con la próxima actualización), `fecha_texto` {es: "16 de noviembre de 2026", en: "November 16, 2026"}, `intro`.
- `kpis`: 3 o 4 `{valor, es, en}` (cifra corta + qué es).
- `hallazgos`: 4 o 5 frases; se permite `<b>…</b>` al inicio.
- `tiktok`: `titulo`, `fuente`, `filas` [{puesto, hashtag, desc{es,en}, videos, vistas, curva}] (copiar `curva` tal cual de la lectura: es la tendencia de 7 días y se dibuja como mini gráfico; el enlace a los videos del hashtag lo pone la página sola). Desde el lector solo llega el top general de EE. UU. (sin sesión, los primeros puestos): poner esos con una `desc` corta de qué es (si no se sabe, "Tema general, no de fútbol"). Agregar `nota_final` explicando que el top 100 de deportes se suma cuando se lee con sesión.
- `instagram`: `titulo`, `nota` (cuántas cuentas, ventana de días, qué es "veces lo normal"), `filas` [{cuenta, que{es,en}, formato{es,en}, veces, enlace}] (el `enlace` exacto de la publicación: la página muestra la vista previa oficial de Instagram) con 8–12 destacadas de `resumen.destacadas` (mayor `veces` primero, variando cuentas).
- `nuestras`: `nota` + `filas` [{cuenta, seguidores, posts (de la semana), mediana, mejor{es,en}}] para las 5 cuentas propias (de `resumen.cuentas`, grupo "Nuestras cuentas").
- `patrones`: 4–6 `{titulo, texto}` con lo que se repite en las destacadas.
- `ideas`: `{"Athletum": [...], "Juve Miami": [...], "Juventus Camps": [...]}`, 2–4 ideas cada una.
- `metodo`: 3–4 frases (fuentes, cuentas leídas, fecha de lectura, "se actualiza cada lunes de forma automática").

## Reglas de redacción (obligatorias)
- Impersonal ("se propone", "conviene revisar"), sin "yo", sin hablarle al lector, sin mencionar a Claude ni a ChatGPT.
- Sin veredictos tajantes ("hay que", "no se recomienda"): hallazgos y puntos a considerar.
- Español neutro e inglés natural; la versión EN sin palabras en español.
- **Nunca nombres de jugadores menores ni de niños** (los textos de las publicaciones pueden traerlos): describir el formato, no a la persona. Jugadores profesionales sí.
- La sede italiana se dice "Italy"/"Italia", nunca "Turin".
- Datos de la competencia: decir que son públicos (me gusta y comentarios); las vistas de reels de otras cuentas no están disponibles.
- No copiar textos de publicaciones a la página: solo describirlos.
