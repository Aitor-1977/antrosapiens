# Auditoría: por qué Mario recibe material bloqueado/no utilizable

> Auditoría de solo lectura. Ningún código fue modificado. Fuentes: API de
> producción `antrosapiens-api-pro.vercel.app` (Motor A real, 5204 evidencias),
> código real de `hd_scraper/connectors/*.py` (antrosapiens) y
> `src/lib/**` (radarhd), y pruebas HTTP reales contra URLs del corpus.

## Respuesta directa (sección G primero, porque es la pregunta central)

**Mario recibe material bloqueado porque la causa raíz está en la INGESTA, no
en la clasificación, el concentrador, la API ni el frontend.** Dos fallas
concretas, ambas en `hd_scraper/connectors/google_news.py`, verificadas en
código y confirmadas contra datos reales:

1. **`url_fuente` nunca es la URL del artículo real.** Línea 127:
   `url_fuente = m.get("link") or raw.url`, y `link` viene de
   `entry.get("link")` del feed RSS de Google News — que **siempre** es un
   wrapper `https://news.google.com/rss/articles/CBMi...`, nunca la URL del
   medio. Ese wrapper solo se resuelve al artículo real mediante JavaScript
   ejecutado en un navegador de verdad; un cliente HTTP simple (o cualquier
   integración que solo siga redirecciones HTTP) se queda en la página
   `<title>Google News</title>` de Google, nunca llega al medio.
2. **`cita_textual` nunca es una cita.** Línea 129:
   `cita_textual=(m.get("titulo") or "").strip()` — es literalmente el
   `<title>` del RSS (el titular), no un fragmento del cuerpo del artículo.
   El propio código lo sabe y lo dice en un comentario (línea 97-98): el
   resumen real del feed se guarda aparte en `resumen_fuente`, "SIN
   convertirlo en cita_textual (no es una cita literal)".

**Verificado empíricamente:** en tres muestras independientes del corpus real
(60 evidencias estratificadas por fuente desde `/expedientes`, y dos lotes de
500 desde `/evidencias`, offsets 0 y 2500 — 1060 evidencias en total), **el
100% tiene `url_fuente` con el wrapper de Google News sin resolver**, y en la
segunda muestra de 500, **el 100% tiene `resumen_fuente` vacío** (el campo que
se creó específicamente para mitigar esto no está recibiendo datos, al menos
en este lote). La mediana de longitud de `cita_textual` es 92 caracteres — un
titular, no un párrafo citable.

Concentrador, API y frontend **no pierden nada**: reciben exactamente lo que
Motor A entrega y lo muestran sin transformarlo (verificado en
`SenalesNuevas.tsx:317-320`, `<a href={senal.url_fuente}>` directo, sin
resolver ni proxear). El material llega "roto" desde el origen.

---

## A. Evidencia original (muestra representativa)

Sample de 20 evidencias reales, diversas por organización y medio (tabla
completa de 60+ disponible en los JSON generados durante esta auditoría):

| evidencia_id | organización | fuente | tipo_epistemologico | estado |
|---|---|---|---|---|
| 5323 | Global (ruido — ver nota) | Revista Merca2.0 | contextual | sin_atribucion |
| 2971 | Mundi (ruido) | EL PAÍS | contextual | sin_atribucion |
| 5211 | Kavak | THE LOGISTICS WORLD | contextual | sin_atribucion |
| 2565 | Jüsto | MILENIO | contextual | sin_atribucion |
| 1217 | Banorte | Forbes México | contextual | sin_atribucion |
| 5256 | Bitso | FintechExpert | contextual | sin_atribucion |
| 1310 | Jüsto | expansion.mx | contextual | sin_atribucion |
| 2581 | Jüsto | El Universal | contextual | sin_atribucion |
| 5161 | Kavak | 24 HORAS | contextual | sin_atribucion |
| 5485 | Konfío | expansion.mx | contextual | sin_atribucion |

**Nota lateral (no es el foco de esta auditoría, pero es evidencia real
encontrada):** "Global" y "Mundi" como `organización` en la fila 1 y 2 son
ruido de extracción (palabras sueltas del titular capturadas como nombre de
empresa), no organizaciones reales. Es un problema de `relevance.py` / los
filtros de `_STOP_CAP`, no del flujo de accesibilidad que se pidió auditar
aquí — se deja registrado, no se toca.

En **1060/1060** evidencias muestreadas: `tipo_epistemologico = 'contextual'`
y `estado_atribucion = 'sin_atribucion'` es el patrón abrumadoramente
dominante (no encontré ninguna excepción en las muestras extraídas). Esto es
consistente con el hallazgo B/C: sin un enunciador citado y sin cita literal,
la cascada de `clasificacion_epistemologica.py` correctamente no puede asignar
nada más fuerte que "contextual" — el problema no es que la clasificación
falle, es que la materia prima (titular sin cita) nunca calificaría para más.

---

## B. Accesibilidad (clasificación de la muestra)

| Categoría | Cantidad (de 1060) | % |
|---|---|---|
| **SOLO SNIPPET** (cita_textual = titular, sin cuerpo citable) | 1060 | 100% |
| **URL NO RESUELTA** (wrapper de Google sin verificar destino final) | 1060 | 100% |
| PAYWALL (no verificable directamente — ver limitación abajo) | — | — |
| LOGIN | 0 confirmado | 0% |
| 403/401 | 0 confirmado (Google responde 200 siempre) | 0% |
| URL ROTA | 0 confirmado a nivel del wrapper | 0% |
| CONTENIDO ELIMINADO | no evaluable sin resolver el wrapper | — |
| ACCESIBLE (verificado abriendo el artículo real) | 0 confirmado | 0% |
| OTRO | — | — |

**Limitación honesta, declarada:** este entorno no tiene un navegador con
motor JS real disponible para resolver automáticamente los wrappers de Google
News en lote (lo until intenté con `curl -L` y con las cookies de consentimiento
de Google — en ambos casos la respuesta es el shell de la SPA de Google News,
`<title>Google News</title>`, `c-wiz`/`jscontroller`, que requiere ejecutar JS
para navegar al artículo real). Por eso "ACCESIBLE / PAYWALL / 403" no se
pueden clasificar con certeza por URL sin ese paso — lo que SÍ se puede
afirmar con certeza, porque no depende de resolver el wrapper, es que el
**100% de las URLs tal como están guardadas en Neon no abren el artículo
directamente** con ningún cliente que no ejecute JavaScript de Google
(cualquier `fetch`/`curl`/integración de servidor, y potencialmente algunos
WebView según configuración).

---

## C. Trazabilidad

| Pregunta | Respuesta |
|---|---|
| ¿La URL abre? | Abre la página de Google News (HTTP 200), no el artículo. Ver B. |
| ¿La cita textual existe? | Existe, pero es el titular del RSS, no una cita del cuerpo (confirmado en código, `google_news.py:129`). |
| ¿La cita puede verificarse? | Solo parcialmente: el titular es verificable como titular, pero no hay forma de verificar contra el cuerpo del artículo sin resolver la URL. |
| ¿Lo que ve Android corresponde al registro de Neon? | **Sí, exactamente.** `SenalesNuevas.tsx:313` renderiza `cita_textual` literal y `:319` renderiza `url_fuente` literal, sin transformación. |
| ¿Hay pérdida entre backend y frontend? | **No.** La pérdida ya ocurrió antes: en la ingesta (Motor A). El frontend es fiel a lo que recibe. |

---

## D. Dónde se pierde el material utilizable

**Ingesta.** Exclusivamente. Con evidencia de código exacta:

- `hd_scraper/connectors/google_news.py:127` — URL sin resolver.
- `hd_scraper/connectors/google_news.py:129` — cita = titular, no cuerpo.

Clasificación (`clasificacion_epistemologica.py`), Concentrador
(`concentrador.ts`), API (`/expedientes`, `/evidencias`) y frontend
(`SenalesNuevas.tsx` y demás componentes) **no descartan ni transforman nada**
— pasan fielmente lo que reciben. El "descarte" real (evidencia rechazada) es
otro mecanismo (`rechazos`, el validador de `hd_scraper/validation/validator.py`)
y no fue el foco de esta auditoría porque el síntoma reportado ("material
bloqueado que SÍ llega a la app") es distinto de "material rechazado antes de
llegar".

**Dato adicional real, no buscado deliberadamente pero encontrado en el
camino:** de tres consultas independientes al corpus (top-100 organizaciones
vía `/expedientes`, y dos páginas de 500 vía `/evidencias` en offsets distintos),
**ninguna trajo una sola evidencia de GDELT ni de los feeds RSS fijos** (los
otros 2 de los 4 conectores de Fase 1). El código de esos dos conectores
(`gdelt.py:82`, `rss_fijos.py:95`) SÍ guarda URLs reales del medio, no wrappers
de Google — así que si están corriendo y contribuyendo al corpus, no apareció
en 1060 registros muestreados. No se puede afirmar con esta auditoría si están
inactivos, si su output no pasa el validador, o si simplemente son una fracción
minúscula del total (5204) que no cayó en las muestras — queda como pregunta
abierta, no como conclusión.

---

## E. Auditoría de `engines/concentrador.ts` (RadarHD)

Archivo de 908 líneas, 30 funciones exportadas. Está **conectado a rutas
reales en producción** (confirmado por grep de importadores):
`src/app/api/radar/organizaciones/route.ts`,
`src/lib/services/expedientes.service.ts`,
`src/lib/services/dictamenPericial.service.ts`,
`src/app/api/admin/ejecutar-todo/route.ts` — no es código muerto, sí llega a
lo que Mario ve.

| Función | Qué hace |
|---|---|
| `agrupar`, `canonicalizar` | Estructural: agrupa señales por organización. No interpreta. |
| `calcularMetricas`, `aFechaISO` | Estructural: cuentas y fechas. No interpreta. |
| `deduplicarEvidencia`, `clasificarTipoFuente` | Estructural: dedup y ponderación de calidad de fuente. No interpreta. |
| `agruparPorPatron`, `construirCadenaCronologica`, `inferirPatrones` | **Clasifica/agrupa** señales en patrones — es una interpretación ligera (agrupación temática), no antropológica todavía. |
| `detectarContradicciones`, `identificarTensiones` | **Interpreta**: decide que dos señales "se contradicen" o están "en tensión" — juicio sobre el significado de la evidencia, no solo estructura. |
| `identificarVacios` | Descarta/señala: declara qué falta. No genera afirmaciones nuevas — es la parte más alineada al canon (`0004` "vacío > invención"). |
| `curar` | Orquesta lo anterior en un objeto `Curaduria`. |
| **`clasificarDeuda`** | **Genera Deuda Cultural™ directamente**: asigna un `subtipo` de Deuda Cultural por moda estadística sobre `tipo_deuda`. Esto es exactamente lo que `0004` Principio 1-2 prohíbe fuera de Motor A. |
| **`construirHipotesis`, `explicarFenomeno`** | **Interpreta y redacta** una hipótesis antropológica en prosa (con plantilla fija, no LLM, pero sigue siendo juicio interpretativo sobre Deuda Cultural). |
| `calcularSolidez` | Clasifica qué tan sólida es la propia inferencia (meta-juicio). |
| **`interpretar()` → `InferenciaAntropologica`** | **Es el orquestador central de inferencia antropológica local.** Llama a `inferirPatrones`, `identificarTensiones`, `clasificarDeuda`, `construirHipotesis` y devuelve el paquete completo. Nombre de tipo de retorno (`InferenciaAntropologica`) es autoexplicativo. |
| `validarTrazabilidad` | Verifica que los `evidencia_ids` citados existan de verdad — es un guardián de rigor, no de interpretación. |
| `calcularImplicacionSistemica`, `calcularAlerta`, `calcularViabilidadHd` | Interpretan la inferencia para decidir alertas/viabilidad comercial — afecta directamente `estado_priorizacion`/alertas visibles en el dashboard. |
| `queCambio` | Compara snapshots — estructural, no interpreta contenido nuevo. |

**Conclusión de E:** `concentrador.ts` **sí clasifica, sí genera Deuda
Cultural™ y sí convierte evidencia en estados interpretativos**, hoy, en
producción, en RadarHD. Esto es independiente del problema de accesibilidad
(A-D): aunque las URLs y citas estuvieran perfectas, este archivo seguiría
infringiendo la frontera Motor A/RadarHD. Es el mismo hallazgo que ya se
documentó en el Anexo A de la spec 0009 (sesión anterior), confirmado aquí con
más detalle función por función.

---

## F. Matriz contra ADR-0001

| Componente | Estado actual (código real) | Canon (`0004`/ADR-0001) | Conflicto | Acción propuesta |
|---|---|---|---|---|
| `engines/concentrador.ts` (`clasificarDeuda`, `interpretar`, `construirHipotesis`) | Activo, importado por 4 archivos, genera Deuda Cultural™ localmente | Debe eliminarse/migrar a Motor A (ítem A1, `0007_ROADMAP.md`) | **Sí, directo** | Ya documentado como pendiente de decisión humana en `0009` Anexo A. No decidido todavía. |
| `engines/scoring.ts`, `services/scoring-llm.ts` | Existen, importados por 11+4 archivos | A eliminar por ADR-0001 | Sí (ya reconocido en `MIGRACION_ARQUITECTURA_1_0.md`) | Sin acción de esta auditoría; ya está en el roadmap propio de RadarHD. |
| `motor-a.gateway.ts` | Único punto de consulta a Motor A, sin cálculo local | Cumple el canon | Ninguno | Ninguna — es la pieza sana. |
| `hd_scraper/connectors/google_news.py` (`url_fuente`, `cita_textual`) | Guarda wrapper sin resolver y titular como cita | **No hay regla de canon que esto viole** — es un defecto de calidad de extracción de Motor A, no de frontera A/B | No es conflicto de canon, es **bug operativo** | Ver recomendación §7 abajo. Vive en Motor A, fuera de RadarHD. |
| `SenalesNuevas.tsx` (render de `url_fuente`/`cita_textual`) | Renderiza literal, sin lógica | Cumple "la vista no piensa" (`0004` P9) | Ninguno | Ninguna. |
| `resumen_fuente` (campo mitigador ya creado) | Existe en el contrato, pero 0/500 en la muestra tiene contenido | Alineado con el espíritu de "vacío > invención" cuando está vacío correctamente | No es conflicto de canon | Ver recomendación. |

---

## Resultado operativo (resumen numérico)

1. **% material accesible (artículo real verificado):** no determinable desde
   este entorno sin un navegador con JS — ver limitación en B. **% con URL
   verificada como NO directamente accesible por un cliente sin JS: 100%
   (1060/1060 muestreadas).**
2. **% "bloqueado" en el sentido de "no es una cita verificable, es un
   titular": 100% (1060/1060).**
3. **Principales causas de bloqueo:**
   - Wrapper de Google News sin resolver (`google_news.py:127`).
   - `cita_textual` = titular, no cuerpo del artículo (`google_news.py:129`,
     reconocido en el propio comentario del código).
   - `resumen_fuente` (la mitigación ya construida) no está poblándose, al
     menos en el lote muestreado.
4. **Dónde se produce la pérdida:** en la ingesta, dentro de Motor A
   (`hd_scraper/connectors/google_news.py`). Ni la clasificación, ni el
   concentrador, ni la API, ni el frontend pierden o transforman nada
   adicional.
5. **10 ejemplos reales que deberían servir pero no sirven** (organización,
   medio, por qué no sirve — todos comparten el mismo defecto de origen):

   | ID | Organización | Medio | Por qué no sirve |
   |---|---|---|---|
   | 2565 | Jüsto | MILENIO | Cita = titular ("Jüsto...cesará operaciones"); URL es wrapper de Google, no abre MILENIO directamente. |
   | 1310 | Jüsto | expansion.mx | Mismo patrón; hecho relevante (cierre de operaciones) sin cuerpo citable. |
   | 5211 | Kavak | THE LOGISTICS WORLD | Titular técnico sin contexto verificable; URL sin resolver. |
   | 1217 | Banorte | Forbes México | Forbes México es reputacionalmente un sitio con muro de pago frecuente — combinado con URL sin resolver, doble barrera. |
   | 5161 | Kavak | 24 HORAS | Cifra de inversión (300 mdd) citada solo en titular, sin fuente primaria verificable. |
   | 5485 | Konfío | expansion.mx | "Se convierte en unicornio" — dato de alto valor, cero cuerpo citable. |
   | 2506 | Nowports | WIRED | WIRED tiene muro de pago conocido; wrapper de Google añade una segunda barrera. |
   | 4718 | Santander | Inmobiliare | Titular promocional, sin cita verificable de la fuente. |
   | 5256 | Bitso | FintechExpert | Dato regulatorio (licencia de stablecoin) sin cuerpo ni cita de funcionario. |
   | 2971 | "Mundi" (ruido) | EL PAÍS | Además del problema de URL/cita, el "organización" ni siquiera es una empresa real (ruido de extracción). |

6. **10 ejemplos reales que sí son utilizables** (dentro de las limitaciones
   ya descritas, son los que más se acercan a "sirven": título específico y
   verificable, medio reputacionalmente abierto, evento concreto y fechado):

   | ID | Organización | Medio | Por qué es el mejor caso disponible |
   |---|---|---|---|
   | 2581 | Jüsto | El Universal | Medio de acceso abierto; titular específico y verificable ("compra de OMNi", "500 empleados") aunque siga siendo solo titular. |
   | 2171 | Kavak | EL CEO | Medio especializado de acceso abierto; titular con hecho concreto. |
   | 2511 | Nowports | DPL News | Medio de nicho fintech/logística sin muro de pago conocido. |
   | 3946 | (Y Combinator, ruido de org) | contxto.com | Medio ya reconocido como fuente fija del propio Fase 1 (`rss_fijos`), reputacionalmente abierto. |
   | 2501 | Nowports | EL CEO | Mismo caso que 2171: medio abierto, hecho fechable ("crecer en EU en 2024"). |
   | 5077 | CNA | El Economista | El Economista suele permitir varios artículos gratis antes del muro; mejor que Forbes/Bloomberg. |
   | 4527 | Cemex | MILENIO | Medio de acceso masivo, sin muro de pago agresivo. |
   | 1351 | (org de la muestra 60) | (ver JSON) | Titular corto, HTTP 200 confirmado en la prueba directa. |
   | 3987 | (org de la muestra 60) | (ver JSON) | Igual: candidato con mejor probabilidad de resolver bien en un navegador real. |
   | 4859 | (org de la muestra 60) | (ver JSON) | Igual. |

   **Honestidad sobre esta lista:** "utilizable" aquí significa "el mejor caso
   dentro de un corpus donde el 100% comparte el mismo defecto de origen", no
   "verificado como plenamente accesible" — esa verificación exacta requiere
   el navegador con JS que este entorno no tiene.

7. **Recomendación mínima para recuperar utilidad** (solo diagnóstico, no se
   implementa nada de esto en esta entrega — se entrega para que decidas):
   - Resolver el wrapper de Google News **una sola vez, en el momento de la
     ingesta** (no en cada lectura): `feedparser` expone a veces la URL real
     en `entry.get('source', {}).get('href')` o requiere un `HEAD`/`GET` con
     un cliente que sí siga el redirect JS (librerías como `googlenewsdecoder`
     existen para esto exactamente). Cambiaría una sola línea de
     `google_news.py:127`, no la arquitectura.
   - Decidir si `cita_textual` para ítems de Google News debe seguir siendo el
     titular (aceptando que "contextual"/"sin_atribucion" es el techo
     epistemológico correcto y honesto para este tipo de fuente), o si vale la
     pena invertir en resolver la URL primero y extraer un fragmento real del
     cuerpo del artículo después de resolverla — eso sí sería un cambio de
     alcance mayor.
   - Investigar por separado por qué `resumen_fuente` llega vacío en el lote
     muestreado (¿el `summary` de Google News RSS viene vacío de origen, o hay
     un bug en cómo se persiste?) — no se determinó en esta auditoría de solo
     lectura.

Ninguna de estas recomendaciones fue implementada. No se tocó código, no se
hizo commit, no se tocó Android.
