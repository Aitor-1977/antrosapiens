# Fase 2 — Plan de corrección mínima (AntroLabsHD)

> Continúa `AUDITORIA_FASE1_ANTROLABSHD_2026-09-14.md` y
> `AUDITORIA_MATERIAL_BLOQUEADO_2026-09-14.md` (Fase 1, ya cerrada). Este
> documento **no implementa nada**: es la especificación de los cambios
> mínimos, para tu validación antes de tocar código. Ningún archivo de código
> fue modificado. Sin commit, sin push — los tres documentos de auditoría
> quedan locales, como pediste.

---

## 0. Nota de cierre sobre la taxonomía conceptual

Por instrucción explícita: la taxonomía conceptual (*Enunciación Biográfica/
Confesional · Fricción Situacional Onlife · Evidencia Estructural ·
Insuficiente/Ruido*) queda marcada como **NO CANON OPERATIVO**. No se
implementa, no se agrega al código, no aparece en ningún cambio propuesto
abajo. La taxonomía operativa vigente sigue siendo, sin cambios:
`senal_primaria_autodeclaracion` / `senal_primaria_huella_practica` /
`corroborante` / `contextual`, más la distinción Dato/Inferencia/Hipótesis/
Vacío ya implementada en `clasificacion_epistemologica.py`.

---

## 1. Corrección mínima del contrato de evidencia (bloqueador prioritario)

### 1.1 Diagnóstico ya cerrado (no se repite el detalle, solo la conclusión)

Confirmado sobre 1060 evidencias reales: el 100% tiene `url_fuente` como
wrapper de Google News sin resolver (`google_news.py:127`) y `cita_textual`
igual al titular RSS, no una cita del cuerpo (`google_news.py:129`). El
concentrador, la API y el frontend no alteran ni pierden nada — renderizan
literal lo que reciben. **La corrección vive exclusivamente en la ingesta de
Motor A**, en un solo conector.

### 1.2 Qué significa "UTILIZABLE Y VERIFICABLE" para una evidencia (definición, no tabla nueva)

Una evidencia es **verificable** cuando su `url_fuente` resuelve al artículo
real del medio (no a un intermediario). Es **utilizable** cuando, además,
`cita_textual` es un fragmento real del cuerpo — o, cuando eso no está
disponible, el sistema declara explícitamente que solo tiene un titular, en
vez de presentarlo con la misma forma que una cita real. Ninguna de las dos
condiciones exige una tabla ni un campo booleano nuevo por sí sola — ver 1.3
para el alcance mínimo.

### 1.3 Cambio propuesto — PRIMERO en orden de ejecución

| | |
|---|---|
| **Problema** | `url_fuente` nunca es la URL del medio; siempre es el wrapper `news.google.com/rss/articles/...`, que solo se resuelve con JavaScript de un navegador real. |
| **Archivo** | `hd_scraper/connectors/google_news.py`, línea 127. |
| **Causa** | `url_fuente = m.get("link") or raw.url`, y `link` viene sin procesar de `entry.get("link")` (feedparser), que para Google News RSS siempre es el wrapper. |
| **Corrección mínima** | Resolver el wrapper **una sola vez, en el momento de la ingesta** (no en cada lectura de la API, no en el frontend). Dos caminos, ambos acotados a esa función, sin tocar el resto de la arquitectura: (a) decodificar el wrapper localmente — el payload `CBMi...` es un protobuf-base64 de Google que codifica la URL real y se puede decodificar sin red (patrón ya usado por librerías públicas como `googlenewsdecoder`); o (b) un único `GET` adicional a la URL del wrapper con un cliente que siga el meta-refresh HTML de Google (no el SPA completo — Google también sirve una versión simplificada con redirect HTTP puro para bots/RSS readers en algunos casos; requiere confirmarlo empíricamente antes de elegir esta vía). **No** se propone montar un navegador headless (Playwright/Selenium) — sería sobrearquitectura para este problema. |
| **Impacto** | Solo afecta `google_news.py`. No toca `gdelt.py`, `rss_fijos.py`, `job_boards.py`, la clasificación epistemológica, el concentrador ni el frontend — todos ya reciben y muestran `url_fuente` correctamente, tal como está. Corregir la ingesta hace que el resto de la cadena, sin cambios, empiece a mostrar URLs reales. |
| **Prueba requerida** | Test que capture un `entry.link` real de un feed de Google News (fixture ya existente en `tests/`, o uno nuevo) y verifique que `url_fuente` resultante NO contiene `news.google.com` y sí resuelve (con mock de red, no contra Google en vivo) al dominio del medio declarado en `nombre_medio`. |

### 1.4 Cambio propuesto — SEGUNDO, complementario (no bloqueante para el primero)

| | |
|---|---|
| **Problema** | `cita_textual` es el titular del RSS, no una cita del cuerpo del artículo; el propio código ya lo sabe (comentario en la línea 97-98) pero el campo se sigue llamando y usando como si fuera una cita. |
| **Archivo** | `hd_scraper/connectors/google_news.py` (líneas 90, 99, 129, 140) y, en consecuencia, el techo que ya aplica `clasificacion_epistemologica.py` (sin cambios ahí: `contextual`/`sin_atribucion` ya es la clasificación correcta y honesta para este caso). |
| **Causa** | Google News RSS solo entrega título + resumen auto-generado; nunca el cuerpo del artículo. No es un bug de extracción — es el techo real de esta fuente. |
| **Corrección mínima** | **No fabricar nada nuevo.** Una vez resuelto 1.3 (URL real), la vía correcta y ya prevista por el propio código es que `resumen_fuente` (el campo que YA EXISTE para esto, `google_news.py:140`) se popule de verdad. Hoy llega vacío en el 100% de una muestra de 500 — antes de tocar nada, hay que determinar la causa exacta: ¿el campo `summary` de feedparser viene vacío de Google News (techo real de la fuente, nada que corregir), o hay un bug en cómo se persiste? Esto es una investigación de una tarde, no una reescritura. |
| **Impacto** | Si el `summary` de Google News viene vacío por diseño de la fuente (escenario más probable), la conclusión correcta es aceptar que `cita_textual` = titular es el techo epistemológico honesto de esta fuente específica, y que el corpus depende de `gdelt.py`/`rss_fijos.py` (que si extraen resumen real) para evidencia con cita más rica — no de inventar una cita donde no la hay. |
| **Prueba requerida** | Un test que corra el parser sobre un feed real de Google News (fixture) y registre si `entry.summary` viene poblado o no — eso resuelve la pregunta con datos, no con suposición. |

---

## 2. Mapa de dependencias — `hd_scraper/pipeline_comercial.py`

Solo auditoría, sin recomendación de borrar/mover/modificar todavía.

### 2.1 Quién lo importa y ejecuta

| Importador | Uso real |
|---|---|
| `hd_scraper/api/app.py:41` | Expone 5 endpoints: `POST /pipeline/registrar`, `POST /pipeline/avanzar`, `GET /pipeline`, `GET /pipeline/funnel`, `GET /pipeline/{org}`. También lo **consulta internamente** (líneas 1415 y 1442) dentro del endpoint tipo "lista matutina": anota `etapa_actual` sobre cada expediente y arma una lista de "seguimiento" (organizaciones sin mover de etapa en ≥7 días). |
| `hd_scraper/laboratorio.py` (Capa 18, `/laboratorio`, `/estado`) | Cuenta filas de `pipeline_comercial` como parte del estado global del sistema (dashboard). |
| `hd_scraper/db/database.py` | Migración idempotente: agrega columna `candidato_id` a la tabla. |
| `android/`, `android_v2/`, `android_v3/app/src/main/python/hd_scraper/` | **Copias idénticas empaquetadas** del mismo archivo (bundling histórico para builds Android basadas en Chaquopy, previas al WebView de `android_v3`). No es un uso adicional real — es la misma lógica duplicada por empaquetado, no por diseño nuevo. |
| `tests/test_pipeline_comercial.py`, `test_candidato.py`, `test_laboratorio.py`, `test_centro_corpus.py` | Cobertura de tests existente. |

**No es importado por** `curaduria.py`, `dictamen.py`, ni `onlife.py` — cero
acoplamiento de código entre esos cuatro módulos, confirmado por grep. Su
único parentesco es compartir el mismo gap de documentación en `CLAUDE.md`.

### 2.2 Funciones que contiene

`registrar_org`, `avanzar`, `obtener_pipeline`, `listar_pipeline`,
`resumen_funnel` (públicas); `_dedup_legacy`, `_resolver_fila`,
`_registrar_transicion`, `_anexar_referencia` (privadas). Depende de
`candidato.py` (vía `candidato_id`) para la identidad referencial de la
organización.

### 2.3 Tablas y API que usa

Tablas propias de Motor A (SQLite/Postgres del propio `antrosapiens`, **no**
la Neon de RadarHD): `pipeline_comercial`, `pipeline_transiciones`. Lee
también `candidatos` (de `candidato.py`). Los 5 endpoints ya listados en 2.1.

### 2.4 ¿Duplica funciones de RadarHD?

**Sí, conceptualmente, en una base de datos distinta.** RadarHD ya tiene su
propio pipeline comercial real y más rico: `prospecto.estado` (máquina de 10
estados, `0005` Máquina B), `seguimiento_comercial`, `cadencia_email`,
`kill_switch_log` — todo en la Neon de RadarHD. `pipeline_comercial.py` en
Motor A es un embudo paralelo, más simple (6 etapas:
observación/vigilancia/peritaje/dolormap/alianza/cerrado), en una base de
datos completamente distinta, **sin ningún puente automático hoy entre
ambos** — ni siquiera por nombre, porque son dos despliegues separados.

### 2.5 Qué parte contradice explícitamente el bounded context

Los **nombres** de dos de sus seis etapas: "Alianza" (definida en su propio
docstring como *"propuesta o conversación activa con la organización"*) y
"Cerrado" (*"relación formalizada (ganado o descartado)"*) son léxico
comercial de embudo de ventas. El **código en sí no ejecuta ninguna acción
comercial**: no envía correos, no registra contactos, no toca ningún dato de
outreach — solo persiste un string de etapa + una nota de texto libre. Esto
ya está reconocido por el propio repo: `scripts/docs/gen_capas.py` (el
generador interno de documentación de Capas, que **si existe y no está
reflejado en `CLAUDE.md`** — ver hallazgo J.1 de la Fase 1) etiqueta este
componente textualmente como:

> `limitaciones="VESTIGIAL: el pipeline comercial real y ejecutado vive en
> RadarHD (Motor C). A deprecar (ADR-0001 / ROADMAP)."`
> `criterios="Modela y persiste estado; NO ejecuta contacto (sin envío de
> emails)."`

Es decir: **el propio proyecto ya sabía y ya lo escribió**, solo que en un
generador de docs interno, no en `CLAUDE.md`, que es el documento que
gobierna la frontera. No es un hallazgo nuevo de comportamiento — es
confirmación de que la severidad real es más baja de lo que mi primer reporte
de hoy sugería: no ejecuta nada indebido, pero sí mantiene una segunda fuente
de verdad sobre "en qué etapa comercial está una organización", violando
`0004` Principio 5 ("ninguna responsabilidad existe duplicada").

### 2.6 Qué parte debería eventualmente pertenecer a RadarHD

El **concepto** de "etapa por organización" ya está mejor resuelto en
RadarHD (`EstadoPipeline`, 10 estados con guardas de negocio, Regla Cero).
No hay nada en `pipeline_comercial.py` que RadarHD necesite "importar" —
al revés: `pipeline_comercial.py` es la versión más simple y anterior de algo
que RadarHD ya construyó mejor y en su propio bounded context.

### 2.7 Recomendación de frontera (sin ejecutar, para tu validación)

No implementar todavía. La opción más alineada con "Regla de no
sobrearquitectura" (Sección XII) es **no migrar ni fusionar nada**: como el
propio `gen_capas.py` ya lo marca vestigial y a deprecar, la corrección
mínima sería (cuando tú autorices Fase 3) **retirarlo** de Motor A sin
reemplazo — no mover su lógica a RadarHD (que ya tiene una versión superior),
solo dejar de mantener una segunda fuente de verdad redundante. Eso sí
requiere decidir primero qué pasa con las 5 lecturas que dependen de él hoy
en `app.py`/`laboratorio.py` (la anotación de `etapa_actual` en el dashboard
de Motor A) — no se puede retirar sin antes decidir si esa anotación se
descarta o se reemplaza por una lectura de solo-lectura hacia RadarHD (lo
cual violaría "dirección única A→RadarHD" al revés, así que probablemente la
respuesta correcta es simplemente descartar esa anotación del dashboard de
Motor A, no reemplazarla).

---

## 3. Orden de ejecución para Fase 3 (cuando la autorices — no antes)

1. **Primero (bloqueador de utilidad real para Mario):** 1.3 — resolver el
   wrapper de Google News en la ingesta. Un archivo, una función, tests
   incluidos.
2. **Segundo:** 1.4 — investigar por qué `resumen_fuente` llega vacío
   (medio día de investigación, sin cambio de código garantizado si resulta
   ser techo real de la fuente).
3. **Tercero, y solo con tu autorización explícita por separado** (no forma
   parte de "resolver Google News"): decidir 2.7 sobre `pipeline_comercial.py`.
4. **En paralelo, sin tocar código:** actualizar `CLAUDE.md` para documentar
   las Capas 1-10 reales (J.1 de la Fase 1) — es trabajo de documentación,
   cero riesgo, y cierra el gap de gobernanza más barato de los encontrados.

Nada de esto se ejecuta todavía. Quedo a la espera de tu autorización para
Fase 3, punto por punto — no en bloque.
