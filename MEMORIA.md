# MEMORIA — hd-prospector (Motor A · Hamaca Digital)

Memoria de trabajo del proyecto. Resumen de qué es, cómo está armado y qué se ha
hecho. Se actualiza al cerrar cada bloque de trabajo.

## Qué es

`hd-prospector` es el **Motor A** de Hamaca Digital: descubre y califica empresas
(prospectos) para el servicio de **Deuda Cultural™**. Originalmente solo
capturaba hechos; por decisión del operador ahora **también analiza en
profundidad** (scoring, Deuda Cultural, ICP, decisor), de forma **determinista**
(sin IA ni red obligatoria).

- Repo: `Aitor-1977/hd-prospector` · Deploy: `hd-prospector.vercel.app`
- Stack: Python / FastAPI · SQLite (local/tests) + PostgreSQL/Neon (producción)
- Motor B (aparte): `RadarHD` (`Aitor-1977/radarhd`, Next.js) — interpretación con IA.

## Arquitectura (carpeta `hd_scraper/`)

- `connectors/` — fuentes de noticias (Google News RSS, GDELT).
- `pipeline.py` — search → normalize → validate → dedup → escribe evidencia.
- `relevance.py` — filtro determinista (opinión, geografía, no-empresa, **gigantes**,
  sucesos) + calidad de captura.
- `signals.py` — taxonomía objetiva de señales (ronda, despido, churn…).
- `analisis.py` — **análisis profundo**: scoring A/B/C, Deuda Cultural™ (con
  combinaciones, intensidad, deuda secundaria, ángulo de conversación), ICP, decisor.
- `contacto.py` — rutas de contacto (correos candidatos por dominio, hipótesis).
- `hunter.py` — verificación de correo del decisor (Hunter.io, opcional, bajo demanda).
- `directorio.py` — **directorio de empresas reales (Wikidata)** para volumen.
- `enrich.py` — auto-investiga (sitio, discurso, vertical; fallback a snippets de búsqueda).
- `engine/rule_engine.py` + `engine/schemas.py` — **Capa 0**: motor de reglas
  determinista (Operativa/Discursiva/Rescate) que puntúa texto/transcripciones y
  emite señales auditables (tabla `senales_capa0`, endpoint `POST /webhook/ingesta`).
- `ingesta/` — conectores que alimentan la Capa 0: `apify.py` (LinkedIn/Jobs/News),
  `youtube.py` (transcripciones vía yt-dlp), `webhook.py` (POST resiliente con
  reintentos+backoff). CLI: `python -m hd_scraper.ingesta {apify|youtube}` (o `run.sh`/`make`).
  Credenciales por `.env` (cero hardcoding).
- `api/app.py` — API + panel `/admin` (PWA).

## Fuentes de prospectos

1. **Noticias** (Google News) → empresas con evento caliente → scoring A/B.
2. **Directorio** (Wikidata, base pública gratis) → volumen de empresas reales → scoring C pero reales, con web y contacto.

## Endpoints clave

- `POST /scrape` — descubrimiento por ecosistema/empresa (presupuesto de tiempo, `parcial`).
- `GET /informe` · `/informe.md` · `/informe.csv` — informe profundo priorizado.
- `POST /analizar` — análisis bajo demanda de un título/señales.
- `POST /verificar-contacto` — verifica correo con Hunter (requiere `HUNTER_API_KEY`).
- `POST /directorio` — trae empresas reales de Wikidata como prospectos.
- `POST /enrich` — auto-investiga un nombre.

## Variables de entorno

- `DATABASE_URL` — Postgres en producción (Neon).
- `HD_INGEST_TOKEN` — token para escritura (`/scrape`, `/enrich`, `/directorio`, …).
- `HUNTER_API_KEY` — (opcional) verificación real de correos. Sin ella: hipótesis.
- Ajustes serverless (defaults ya aptos): `HD_REQUEST_TIMEOUT_S=8`, `HD_MAX_RETRIES=1`,
  `HD_SCRAPE_BUDGET_S=7`, `HD_ENRICH_BUDGET_S=6`.

## Conector de directorio (Wikidata) — estado actual

- **Cascada de relajación**: país+vertical → país+todas → toda LATAM. Si se amplía,
  devuelve nota "filtro ampliado automáticamente" en vez de error.
- **Caché** (tabla `directorio_cache`, SQLite/PG): sirve consultas idénticas de los
  últimos **7 días** sin volver a llamar a Wikidata.
- **Resiliencia**: `User-Agent` que identifica la app; ante error/bloqueo espera
  **5 s** y reintenta **una** vez; solo si ese reintento falla se avisa.
- Filtra gigantes y entidades sin etiqueta; una sola consulta SPARQL cubre varios
  países (VALUES), así "toda LATAM" no multiplica llamadas.
- Cobertura honesta: Wikidata cubre mejor empresas notables/medianas que
  micro-startups. Volumen real, no exhaustividad (para eso, base de pago).

## Estado técnico

- Pruebas: **185 passed** (`pytest`).
- Rama: `main` (auto-deploy en Vercel).

## Pendiente / depende del operador

- Agregar `HUNTER_API_KEY` en Vercel para correos verificados.
- (Opcional) Base de empresas de pago (Crunchbase/Apollo) para cobertura total.

## Bitácora

- Filtro de relevancia endurecido: España/Europa, gobierno, reportes, **gigantes**
  (Google, Wendy's…), sucesos/nota roja.
- Búsqueda por ecosistema con grupos OR (más recall) + presupuesto de tiempo
  (evita el "Internal Server Error" por timeout serverless).
- Análisis profundo: scoring, Deuda Cultural (combinaciones, intensidad, ángulo),
  ICP, decisor + correo candidato; verificación con Hunter; export MD/CSV.
- Directorio Wikidata para volumen real, con **cascada + caché 7 días + reintento**.
- **Síntesis Estructural (Capa 19)** autorizada por el operador (2026-08-04) y
  registrada en `CLAUDE.md` → «Frontera de Interpretación»: reordenamiento
  determinista de señales Nivel 1 por organización ([patrón, tensión/dolor,
  actores, sustancia] + evidencia_urls), grounded, sin IA, sin Deuda Cultural™,
  preliminar. Implementación: `hd_scraper/sintesis.py` + `GET /sintesis/{org}`.
- **Síntesis estructural con LLM (NVIDIA)** autorizada por el operador
  (2026-08-04, misma sesión): Motor A puede enriquecer la Capa 19 con NVIDIA
  NIM (`NVIDIA_API_KEY`), SOLO sobre evidencia ya extraída, con vocabulario
  público genérico (sin Deuda Cultural™ ni juicios), salida preliminar
  etiquetada (`metodo: llm_nvidia`) y **fallback determinista garantizado**.
  Implementación: `hd_scraper/nvidia_parser.py`.
- **Interfaz: síntesis como fuente principal, corpus como respaldo técnico**
  (decisión del operador 2026-08-04): el envío de texto crudo a la interfaz se
  bloquea SOLO a nivel de presentación — la app Radar muestra la síntesis
  estructurada (Capa 19, LLM) como contenido primario y el corpus crudo queda
  colapsado como respaldo read-only. El contrato `GET /corpus` NO cambia: el
  texto crudo de GDELT/Google News sigue fluyendo a `evidencias` y es servible
  para el consumidor técnico. Implementación: app (interfaz) → `IndagacionScreen`.
