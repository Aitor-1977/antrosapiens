# README Técnico — Antrosapiens (Motor A)

> Verificado contra el código (`CLAUDE.md`, `config.py`, `.env.example`,
> `scripts/`, `vercel.json`, `requirements.txt`). No contiene comandos inventados.
> Índice general de la documentación: [`docs/README.md`](./README.md).

## Qué es Antrosapiens
**Motor A** del ecosistema Hamaca Digital: la **capa de extracción de evidencia**.
Extrae, normaliza y almacena señales públicas sobre organizaciones, y —de forma
**determinista, sin IA**— infiere, valida científicamente y gobierna esa
inteligencia. Es la **única fuente de verdad** del ecosistema (ADR-0001).

## Propósito científico
Convertir señales dispersas en **evidencia trazable, clasificada de forma
reproducible y auditable** (huella + certificado), de modo que toda conclusión
pueda reconstruirse desde su `hash`. Sin reproducibilidad no hay ciencia; por eso
la inferencia vive donde es determinista (ver `ADR/ADR_0002_CAPAS_CIENTIFICAS.md`).

## Arquitectura general
Pipeline de 19 capas (0–18): Captura → Normalización → Evidencia → Inferencia →
Curaduría → Validación Científica → Gobernanza → Memoria/Comparación/Predicción →
Observatorio → Publicación → Sistema Operativo → API. Detalle:
[`ARQUITECTURA_ECOSISTEMA.md`](./ARQUITECTURA_ECOSISTEMA.md),
[`DOCUMENTACION_MAESTRA.md`](./DOCUMENTACION_MAESTRA.md), [`CAPAS/`](./CAPAS/).

## Repositorios del ecosistema
- `Aitor-1977/antrosapiens` — **Motor A** (este repo, Python/FastAPI).
- `Aitor-1977/radarHD` (npm `prospector`) — **Motor B + Motor C** (Next.js).
- `Aitor-1977/Radar-Hd`, `Aitor-1977/marito-Aitorhd` — legacy.
Ver [`FRONTERAS_MOTORES.md`](./FRONTERAS_MOTORES.md).

## Motores
Motor A **piensa** · Motor B **muestra** · Motor C **vende** (ADR-0001).

## Tecnologías (de `requirements.txt`)
Python 3.11 · FastAPI · Uvicorn · httpx · feedparser · APScheduler ·
python-dateutil · psycopg[binary] (PostgreSQL) · BeautifulSoup4 · python-dotenv ·
yt-dlp · pytest. BD: **SQLite** (dev/tests) / **PostgreSQL** (producción).

## Cómo instalar
```bash
pip install -r requirements.txt
```
> Nota de entorno (documentada): si `feedparser` falla al construir `sgmllib3k`
> en Debian, instalar el sdist de `sgmllib3k` manualmente (copiar `sgmllib.py` a
> `site-packages`). No es un requisito del proyecto, sino del entorno.

## Variables de entorno (de `config.py` / `.env.example`)
Todas opcionales (hay defaults para dev). Las relevantes:

| Variable | Default | Uso |
|----------|---------|-----|
| `HD_DATABASE_URL` | `sqlite:///data/hd_scraper.db` | BD (SQLite dev / `postgres://…` prod) |
| `HD_INGEST_TOKEN` | `""` | Token de alta de prospectos; **vacío ⇒ escritura deshabilitada** |
| `HD_RAW_DIR` / `HD_RAW_ENABLED` | `data/raw` / `1` | Retención de crudo comprimido |
| `HD_RAW_RETENTION_DAYS` | `90` | Días de retención |
| `HD_SCHEDULE_HOURS` | `12` | Periodicidad del scheduler |
| `HD_REQUEST_TIMEOUT_S` | `8` | Timeout HTTP |
| `HD_MAX_RETRIES` / `HD_BACKOFF_BASE_S` | `1` / `0.5` | Reintentos/backoff por fuente |
| `HD_MIN_INTERVAL_S` | `0.5` | Rate limit por fuente |
| `HD_HEALTH_ALERT_THRESHOLD` | `2` | Fallos consecutivos ⇒ alerta |
| `HUNTER_API_KEY` | `""` | Verificación de contacto (opcional) |
| `HD_TRACKED_EMPRESAS` / `HD_TRACKED_SLUGS` | `""` | Empresas/slugs seguidos por el scheduler |
| `HD_WEBHOOK_URL`, `HD_INGESTA_*` | — | Conectores de ingesta Capa 0 |

En Vercel se auto-detectan `DATABASE_URL`/`POSTGRES_URL`; `vercel.json` fija
`HD_RAW_DIR=/tmp/hd_raw`, `HD_RAW_ENABLED=0`.

## Cómo ejecutar (comandos de `CLAUDE.md` / `scripts/`)
```bash
python -m scripts.run_once "Nubank" --tipo ronda                        # google_news
python -m scripts.run_once "Nubank" --tipo ronda --connector gdelt      # gdelt
python -m scripts.run_once "Nubank" --tipo lanzamiento --connector rss_fijos
python -m scripts.run_once "Acme" --connector job_boards --slug acme     # requiere --slug
python -m scripts.serve_api                     # API + scheduler
uvicorn hd_scraper.api.app:app --reload          # solo API
```
> El proxy de egress puede bloquear `news.google.com` / `api.gdeltproject.org`;
> la verificación en vivo puede no ser posible en algunos entornos.

## Cómo migrar la BD
```bash
python -m scripts.migrate        # crea el esquema (idempotente: CREATE TABLE IF NOT EXISTS)
```

## Cómo correr tests
```bash
pytest -q                        # esperado: 657 passed
```
Cobertura de un módulo:
```bash
python -m coverage run --source=hd_scraper -m pytest && python -m coverage report
```

## Cómo desplegar
- **Vercel** (`vercel.json`): build `@vercel/python` sobre `api/index.py`
  (incluye `hd_scraper/**`); ruta comodín → `api/index.py`. Conectar PostgreSQL
  (Neon) → autodetecta `DATABASE_URL`. Producción actual: `hd-prospector.vercel.app`.

## Cómo regenerar la documentación
La documentación de capas/diagramas se genera con los scripts versionados en
`scripts/docs/` (`gen_capas.py`, `gen_diagramas.py`):
```bash
python -m scripts.docs.gen_capas       # regenera docs/CAPAS/CAPA_00..18.md
python -m scripts.docs.gen_diagramas   # regenera docs/DIAGRAMAS/*.md
```
El resto de documentos se mantiene a mano, verificando contra el código.

## Cómo recuperar el proyecto desde cero
Ver la guía completa: [`GUIA_RECONSTRUCCION_TOTAL.md`](./GUIA_RECONSTRUCCION_TOTAL.md).
Resumen: clonar → `venv` → `pip install -r requirements.txt` → `.env` →
`python -m scripts.migrate` → `pytest -q` → `python -m scripts.serve_api`.

## Referencias
Índice: [`docs/README.md`](./README.md) · Capas: [`CAPAS/`](./CAPAS/) ·
ADR: [`ADR/`](./ADR/) · Diagramas: [`DIAGRAMAS/`](./DIAGRAMAS/) ·
Inconsistencias: [`INCONSISTENCIAS.md`](./INCONSISTENCIAS.md).
