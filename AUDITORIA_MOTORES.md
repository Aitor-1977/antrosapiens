# AUDITORÍA DE MOTORES DE BÚSQUEDA Y CONECTORES — hd-scraper

Dictamen técnico de solo lectura. Fecha: 2026-07-22. Alcance: conectores
(`hd_scraper/connectors/`), clase base `Connector`, pipeline, validación,
gobernanza, scheduling/cola, persistencia y rutas de ingesta asociadas.
No se modificó código.

## Tabla resumen

| # | Hallazgo | Zona | Evidencia |
|---|----------|------|-----------|
| 1 | Google News RSS cumple el ciclo completo search→fetch→normalize→validate, con escritura y dedup | ✅ Sin bloqueo | `connectors/google_news.py:70-129`, `connectors/base.py:87-89`, `pipeline.py:126-213` |
| 2 | Los 4 conectores de Fase 1 están funcionales end-to-end | ✅ Sin bloqueo | ver §1 |
| 3 | Contradicción normativa: CLAUDE.md prohíbe interpretación aquí, pero el repo hoy contiene scoring/Deuda/ICP (autorizado por el operador, no documentado en CLAUDE.md) | Riesgo | `CLAUDE.md` (sección "Frontera Motor A / Motor B") vs `analisis.py`, `engine/rule_engine.py` |
| 4 | Encoding: dos conectores pasan `resp.text` (charset adivinado) a feedparser en vez de bytes | Riesgo (repetido 2×, registrado en CLAUDE.md) | `connectors/google_news.py:72-73`, `connectors/rss_fijos.py:76-77` |
| 5 | GDELT trata la respuesta de rate-limit (HTML) como "0 artículos" y la corrida se registra OK | Riesgo | `connectors/gdelt.py:91-101` |
| 6 | `normalizar_url` descarta el query string completo: colapsa artículos distintos en sitios `?p=123` | Riesgo | `db/models.py:51-62` |
| 7 | Dedup por título normalizado colapsa artículos distintos con título genérico idéntico | Riesgo | `db/models.py:106-109`, `pipeline.py:88-111` |
| 8 | Sin tests: scheduler, cola de jobs, RateLimiter (backoff/Retry-After), `fetch()` de los 4 conectores, purga de raw_store | Riesgo | ver §5 |
| 9 | Google News persiste la URL de redirect (`news.google.com/...`), no la del medio | Ruido | `connectors/google_news.py:85-97` |
| 10 | `_get()` y `normalize()` casi idénticos duplicados en los 4 conectores | Ruido | `google_news.py:106-109`, `gdelt.py:109-112`, `rss_fijos.py:110-113`, `job_boards.py:160-163` |
| 11 | Jobs en estado `error` no se reintentan automáticamente | Ruido (aceptado Fase 1) | `jobs.py:47-58` |

**Zona Bloqueante: vacía.** Nada impide Google News RSS end-to-end; ya está completo.

---

## 1. Inventario de conectores y estado real

Los cuatro conectores registrados (`connectors/__init__.py`) heredan de la clase
abstracta `Connector` (`base.py:27-99`), que define el contrato
`search/fetch/normalize/validate` y delega `validate` en el validador único
(`base.py:87-89` → `validation/validator.py:58-94`).

| Conector | Estado | Ciclo completo | Evidencia |
|----------|--------|----------------|-----------|
| `google_news` | **Funcional end-to-end** | search `:70-98`, fetch `:101-104`, normalize `:112-129`, validate heredado | `connectors/google_news.py`; e2e con escritura SQLite en `tests/test_pipeline.py:15-32` y `tests/test_captura_inteligente.py` |
| `gdelt` | Funcional end-to-end | search `:70-89`, fetch `:104-107`, normalize `:115-132` | `connectors/gdelt.py`; `tests/test_gdelt.py` (6 tests) |
| `rss_fijos` | Funcional end-to-end (8 feeds, salud por feed) | search `:71-102`, fetch `:105-108`, normalize `:116-133` | `connectors/rss_fijos.py`; `tests/test_rss_fijos.py` (6 tests) |
| `job_boards` | Funcional end-to-end (Greenhouse/Lever/Ashby, salud por plataforma) | search `:112-152`, fetch `:155-158`, normalize `:166-183` | `connectors/job_boards.py`; `tests/test_job_boards.py` (7 tests) |

**Respuesta directa a la pregunta (1): el conector Google News RSS ya cumple el
ciclo completo.** No está "en desarrollo": search construye la URL RSS con la
consulta estructural (`:59-68`), parsea el feed (`:70-98`), normalize mapea a
`EvidenceRecord` con `cita_textual` = título literal y `hash_dedup` calculado
(`:112-129`), validate aplica el contrato, y el pipeline escribe con dedup
(`pipeline.py:198-203`). CLAUDE.md ya declara "Fase 1 COMPLETA" y los tests lo
confirman. Ningún conector está en estado esqueleto ni muerto.

Rutas de ingesta adicionales (no son subclases de `Connector`): `ingesta/noticias.py`
(RSS→webhook, en proceso), `ingesta/youtube.py` (yt-dlp por subprocess; no
ejecutable en serverless), `directorio.py` (Wikidata con cascada+caché+reintento).
Funcionales con red inyectada en tests; sin verificación en vivo desde este entorno
(el proxy bloquea egress, ya documentado en CLAUDE.md).

## 2. Frontera Motor A / Motor B (extracción pura)

**Los 4 conectores respetan la regla.** `tipo_evento` viaja en la `QuerySpec`
declarada por el operador (`google_news.py:89-91`, `gdelt.py:84-86`,
`rss_fijos.py:97-98`) o es estructural (`job_boards.py:104-105,147-148`);
`origen_declaracion` se deriva de la estructura de la fuente. El filtro de
`rss_fijos` es coincidencia literal de subcadena (`:88-90`), extracción, no
interpretación.

**Pero el repo, fuera de los conectores, hoy SÍ contiene interpretación**, en
contradicción con CLAUDE.md ("La Deuda Cultural™ … el score ICP … JAMÁS en este
repo"):

- `analisis.py` — scoring A/B/C, hipótesis de Deuda Cultural™ (con combinaciones),
  Score ICP 0-100, decisor sugerido, ángulo de conversación (todo el módulo).
- `engine/rule_engine.py:24-52` — pesos por tipo de señal y umbral de alerta
  (scoring), consumido por `api/app.py` (`/webhook/ingesta`, `/ingesta/noticias`).
- `api/app.py` — endpoints `/informe*`, `/analizar`, `/verificar-contacto`
  exponen esa interpretación desde el Motor A.
- Frontera gris aceptable: `relevance.py` (filtros deterministas de
  opinión/geografía/no-empresa) se documenta como estructural, aunque las listas
  `GIGANTES` (`relevance.py:167-173`) y `RUIDO_MEDIATICO` (`:197-216`) codifican
  una decisión de ICP (a quién no observar). `signals.py` usa taxonomía genérica
  declarada — dentro de la regla.

Contexto verificable: esta ampliación fue **ordenada explícitamente por el
operador** (registrada en `MEMORIA.md`, sección "Qué es", y en la historia de
commits `656ded8`, `52fede1`, `ddf4803`). La violación no es clandestina; es una
**decisión de producto sin reflejar en el documento normativo**. Mientras
CLAUDE.md diga una cosa y el código otra, cualquier agente futuro recibirá
instrucciones contradictorias.

## 3. Normalización de datos

Correcto:
- Fechas → ISO 8601 en los 4 conectores: `google_news.py:36-44`
  (`published_parsed` UTC), `gdelt.py:31-39` (`seendate`), `job_boards.py:38-53`
  (ISO y epoch-ms), `rss_fijos.py:37` (reutiliza el de google_news).
- `cita_textual` siempre es el título literal y el validador rechaza su ausencia
  (`validator.py:28-37,66-69`). `fecha_publicacion` ausente ⇒ `no_fechado`, no
  consumible por la API (`validator.py:89-90`; `api/app.py` sirve solo
  `estado='ok'`). **La regla "sin cita textual fechada no es admisible" se
  cumple en la superficie de consumo.**
- Integridad de `hash_dedup` verificada contra recomputación (`validator.py:83-86`).

Hallazgos:
- **(4) Encoding (repetido 2×):** `google_news.py:72-73` y `rss_fijos.py:76-77`
  pasan a `feedparser.parse()` el resultado de `resp.text` (charset adivinado por
  httpx desde cabeceras); se pierde la detección de encoding del prólogo XML.
  Feeds cuyo charset real difiere de la cabecera HTTP pueden producir mojibake en
  `cita_textual`. Solución conocida: pasar `resp.content` (bytes) y dejar que
  feedparser resuelva. Registrado en CLAUDE.md § Errores recurrentes.
- **(6)** `normalizar_url` (`db/models.py:51-62`) descarta el query string
  completo. En sitios que identifican el artículo por query (`/nota?p=123`),
  URLs distintas colapsan a la misma clave → dedup falso positivo en
  `hash_dedup` y `clave_contenido` (`models.py:112-124`).
- **(7)** `hash_contenido` = sha256 del título normalizado (`models.py:106-109`)
  y `_es_duplicado_contenido` acepta coincidencia por título **solo**
  (`pipeline.py:88-111`, OR): dos artículos distintos con el mismo título
  genérico ("Resumen semanal de fintech") se colapsan aunque la URL difiera.
- **(9)** Google News persiste el link de redirect de `news.google.com`
  (`google_news.py:85-97`): el mismo artículo capturado además por `rss_fijos`
  (URL del medio) no colapsa por URL, solo por título — dedup entre fuentes
  parcialmente dependiente del hallazgo 7.

## 4. Robustez

Correcto:
- Timeout en el cliente compartido (`base.py:48-52`, `config.py:73` — 8 s).
- Reintentos con backoff exponencial y `Retry-After` para 429/5xx/errores de
  transporte (`governance/rate_limit.py:44-80`).
- Aislamiento por sub-fuente: un feed caído no tumba a los demás
  (`rss_fijos.py:78-80`); una plataforma caída no tumba a las otras y el 404 no
  cuenta como fallo (`job_boards.py:121-129`); salud por sub-fuente persistida
  (`base.py:92-99` + `pipeline.py:114-117`, `governance/health.py:13-53`).
- Respuestas vacías: GDELT devuelve `{"articles": []}` ante cuerpo vacío
  (`gdelt.py:93-96`); feedparser tolera XML vacío.
- Dedup en escritura (`ON CONFLICT hash_dedup DO NOTHING`, `pipeline.py:63-85`)
  más dedup de contenido previo (`pipeline.py:182-187`).
- Serverless: presupuesto de tiempo en `/scrape` y fallo-rápido configurado
  (`config.py:69-79`, `api/app.py`).

Hallazgos:
- **(5)** `gdelt._parse_json` (`gdelt.py:91-101`) convierte una respuesta
  no-JSON — típicamente el HTML de rate-limit de GDELT — en "0 artículos" **sin
  emitir señal de salud**; `run_connector` registra la corrida como OK
  (`pipeline.py:209-212`). Un rate-limit sostenido es indistinguible de "no hay
  noticias". Contraste: `job_boards` sí registra `json invalido` como fallo
  (`job_boards.py:131-135`).
- **(11)** Un job que falla queda en `estado='error'` sin reintento automático
  (`jobs.py:47-58`); el reintento llega recién en la siguiente corrida del
  scheduler si se re-encola. Aceptado para Fase 1, documentado aquí.

## 5. Cobertura de pruebas

Suite total: **215 tests** (`pytest -q`). Por conector: `test_google_news.py` 3,
`test_gdelt.py` 6, `test_rss_fijos.py` 6, `test_job_boards.py` 7, más
`test_pipeline.py` 3 (end-to-end con escritura y dedup) y `test_validator.py` 7.
El ciclo search→normalize→validate→persistencia de Google News está cubierto
(`test_pipeline.py:15-43`, `test_captura_inteligente.py`).

**Rutas críticas sin test** (verificado por búsqueda en `tests/`):
- `scheduler.py` (`corrida`, `build_scheduler`) — 0 referencias.
- `jobs.py` (`encolar`, `procesar_pendientes`, transición a `error`) — 0 referencias.
- `governance/rate_limit.py` (backoff, `Retry-After`, agotamiento de reintentos) — 0 referencias.
- Método `fetch()` de los 4 conectores — 0 referencias (`grep "\.fetch(" tests/` vacío).
- `storage/raw_store.py:purgar_expirados` — sin test directo (la retención sí se
  prueba en `test_pipeline.py:15`).

## Acción siguiente recomendada (una sola)

**Actualizar CLAUDE.md para que el documento normativo coincida con el alcance
real autorizado del repo**: registrar que, por decisión del operador
(2026-07-19/22), hd-prospector incorpora una capa de interpretación determinista
(`analisis.py`, `engine/`) además de la extracción, delimitando explícitamente
qué interpretación vive aquí y cuál sigue siendo exclusiva de RadarHD. Es el
hallazgo raíz: todos los agentes (humanos o IA) que trabajen este repo leen
CLAUDE.md primero, y hoy ese documento ordena lo contrario de lo que el código
hace. Mientras no se corrija, cada sesión futura arriesga "corregir" en la
dirección equivocada (borrar módulos autorizados o negarse a mantenerlos).
