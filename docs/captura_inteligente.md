# Captura Inteligente del Motor A

Mejora del Motor A (`hd-prospector`) para **reducir el ruido del corpus sin
convertirlo en un clasificador**. El Motor A sigue capturando hechos públicos y
objetivos; la interpretación, el scoring y la Deuda Cultural™ siguen siendo
responsabilidad EXCLUSIVA del Motor B (RadarHD).

Restricciones respetadas:

- **No** se modifica el contrato `motor_a.corpus.v1` (endpoint `/corpus`).
- **No** se modifica el Motor B (RadarHD) ni su scoring.
- **No** se usa IA ni criterios ambiguos: todo el filtrado es determinista,
  léxico/estructural y auditable.
- Los descartes se registran en la tabla `rechazos` con su motivo (trazable).

---

## 1. Deduplicación robusta

**Problema:** el `hash_dedup` del contrato es `sha256(empresa + url)`. En el
descubrimiento por categoría la "empresa" es el TÉRMINO de la consulta, no una
compañía real; el mismo artículo surgido por dos consultas distintas obtenía dos
`hash_dedup` distintos y se **guardaba repetido**.

**Solución:** identidad de contenido independiente de la empresa, con esta
cascada de prioridad (la primera disponible gana) — `hd_scraper/db/models.py`:

1. **URL canónica** declarada por la fuente (`rel=canonical` / `og:url`), normalizada.
2. **URL normalizada** (host en minúsculas, sin query → descarta UTM y demás
   parámetros de rastreo, sin fragmento ni slash final).
3. **Hash del contenido** (`hash_contenido` = sha256 del título normalizado, sin
   el sufijo " - Medio", sin acentos ni puntuación) — colapsa el MISMO artículo
   republicado en URLs distintas.

En el pipeline, antes de escribir, `_es_duplicado_contenido` descarta el registro
si ya existe otra evidencia con la misma `clave_contenido` **o** el mismo
`hash_contenido`. Se conserva además el `hash_dedup UNIQUE` del contrato como
última barrera.

## 2. Filtro mínimo de relevancia (objetivo y documentado)

`hd_scraper/relevance.py`. Se aplica **solo en descubrimiento amplio**
(`QuerySpec.exact = False`); las consultas dirigidas por nombre de empresa no se
filtran. Reglas (todas deben cumplirse para conservar):

| Regla | Criterio objetivo | Motivo de descarte |
|-------|-------------------|--------------------|
| R1 | No es opinión / tendencia / listículo (marcadores léxicos: `opinión`, `columna`, `editorial`, `análisis`, `el futuro de`, `tendencias`, `N claves/razones/formas`, `los mejores`, …) | `relevancia:opinion` |
| R2 | Hay una **empresa identificable** (nombre propio o sigla en el titular; no palabra común ni término de sector) | `relevancia:sin_empresa` |
| R3 | Hay un **evento verificable** (al menos una señal genérica detectada) | `relevancia:sin_evento` |

Esto descarta lo que se pidió: artículos de opinión, análisis general de
industria, tendencias sin empresa, noticias sin empresa concreta y noticias sin
evento de negocio verificable.

## 3. Eventos conservados

`hd_scraper/signals.py` amplía la taxonomía **genérica** (Motor A, no Deuda
Cultural™) para cubrir todos los eventos pedidos:

`ronda_inversion`, `reduccion_personal` (despidos/reestructuración),
`friccion_retencion` (churn, pérdida/fuga de clientes, cancelaciones, demandas),
`expansion`, `cambio_liderazgo`, `lanzamiento`, `adquisicion` (adquisición/fusión),
**`alianza`** (alianza estratégica), **`contratacion_masiva`**,
**`cierre_operaciones`**, **`crecimiento`** (crecimiento relevante) y
**`regulacion`** (regulación con impacto empresarial).

## 4. Mejores consultas de descubrimiento (fricción)

`hd_scraper/discovery.py`. `TIPO_KEYWORDS` pasa de una frase única a **variantes**:
`queries_para` emite una consulta por variante (frases cortas amplían el
descubrimiento; una frase larga estrecha por conjunción en Google News).

El bucket de fricción (`queja`) deja de ser un solo término y cubre
explícitamente: **pérdida de clientes**, **cancelación de servicios**,
**demandas**, **conflictos regulatorios / multas**, **caídas de crecimiento**,
**reestructuración**, **crisis operativas** y **despidos / cierre de operaciones**.

## 5. Campo `calidad_captura` (informativo)

Etiqueta objetiva del acto de captura — `Alta | Media | Baja` — calculada con
cuatro criterios objetivos: empresa identificada, evento identificado, fuente
confiable (medio nombrado) y ausencia de duplicados (garantizada tras la dedup).
`3/3` de los criterios variables → **Alta**, `2/3` → **Media**, `≤1/3` → **Baja**.

- Se almacena en la columna `evidencias.calidad_captura` (SQLite + Postgres, con
  migración idempotente `ADD COLUMN IF NOT EXISTS`).
- Se expone en `GET /evidencias` (y en `/evidencias/{id}`).
- Se expone también en `GET /corpus` como **extensión aditiva y retrocompatible**
  del contrato `motor_a.corpus.v1` (misma versión; los consumidores previos la
  ignoran). RadarHD la usa como contexto objetivo para reducir falsos positivos.
- Es un **hecho objetivo**, no interpretación: no añade Deuda Cultural™/ICP ni
  modifica el scoring del Motor B.

---

## Reporte comparativo (antes / después)

Reproducible con `python -m scripts.reporte_captura`. Es una **simulación
controlada y determinista**: en el entorno de desarrollo no hay salida a
Internet, así que en lugar de Google News en vivo se usa un pool de titulares
representativos (eventos reales, republicaciones, opiniones, tendencias sin
empresa y notas sin evento) surgidos por **3 consultas** con solapes — igual que
en producción, donde el mismo artículo aparece bajo varias consultas.

| Métrica | ANTES | DESPUÉS |
|---------|------:|--------:|
| Titulares vistos (con solapes) | 17 | 17 |
| Artículos almacenados (total) | 17 | 6 |
| Artículos útiles (`estado=ok`) | 16 | 5 |
| Duplicados eliminados | 0 | 2 |
| Descartados por relevancia | 0 | 9 |
| Descartados totales (dup + filtro) | 0 | 11 |
| **Reducción de ruido del corpus** | — | **70.6 %** |
| Distribución de calidad | — | Alta = 4 · Media = 1 · Baja = 0 |

**Lectura:** antes, el mismo artículo entraba varias veces (una por consulta) y
las opiniones/tendencias/notas sin empresa o sin evento se almacenaban como
corpus; el operador veía "info irrelevante y repetida". Después, la
deduplicación robusta colapsa las republicaciones y el filtro objetivo descarta
el ruido, dejando un corpus más limpio y etiquetado por calidad — **sin tocar el
contrato ni el Motor B**.
