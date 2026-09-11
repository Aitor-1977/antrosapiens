# MEMORIA — hd-prospector (Motor A · Hamaca Digital)

Memoria de trabajo del proyecto. Resumen de qué es, cómo está armado y qué se ha
hecho. Se actualiza al cerrar cada bloque de trabajo.

## Qué es

`hd-prospector` es el **Motor A** de Hamaca Digital: descubre y califica empresas
(prospectos) para el servicio de **Deuda Cultural™**. Originalmente solo
capturaba hechos; por decisión del operador ahora **también analiza en
profundidad** (scoring, Deuda Cultural, ICP, decisor), de forma **determinista**
(sin IA ni red obligatoria).

- Repo: `Aitor-1977/antrosapiens` (nombre actualizado; `hd-prospector` es el nombre
  interno del servicio, visible en `"service"` de `/health`).
- Deploy: **4 proyectos Vercel separados**, mismo repo/rama `main`:
  `antrosapiens-api-pro` (el real, conectado a Neon con los ~5.200 registros de
  producción y el que consume `android_v2`), `antrosapiens-taow` (Postgres
  aparte, vacío/de prueba), `antrosapiens-api` y `antrosapiens-core` (caían a
  SQLite efímero por falta de `DATABASE_URL`/`HD_DATABASE_URL` en Vercel —
  incidente 2026-09-10, ver Bitácora).
- Stack: Python / FastAPI · SQLite (local/tests) + PostgreSQL/Neon (producción)
- Motor B (aparte): `RadarHD` (`Aitor-1977/radarhd`, Next.js) — interpretación con IA.
- **App Android**: `android_v2/` — app nativa (Kotlin + Compose + WebView).
  Pantalla principal (`assets/public/index.html`, función `cargarHallazgos()`)
  consume `GET /expedientes` y `GET /verificados` de `antrosapiens-api-pro`
  (constante `API` fija en el HTML, línea ~168). Se compila vía GitHub Actions
  (`.github/workflows/build-apk.yml`, `workflow_dispatch` o push a
  `android_v2/**`) y publica un GitHub Release `apk-<run_number>` instalable
  directo desde el navegador del teléfono.

## Arquitectura (carpeta `hd_scraper/`)

- `connectors/` — 5 conectores: `google_news.py`, `gdelt.py`, `rss_fijos.py`
  (8 feeds curados), `job_boards.py` (Greenhouse/Lever/Ashby por slug),
  `busqueda_dinamica.py` (Tavily, léxico de autodeclaraciones de founders).
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

- Pruebas: **1010 passed** (`pytest`, actualizado 2026-09-10).
- Rama: `main` (auto-deploy en Vercel, 4 proyectos — ver arriba).

## Pendiente / depende del operador

- Agregar `HUNTER_API_KEY` en Vercel para correos verificados.
- (Opcional) Base de empresas de pago (Crunchbase/Apollo) para cobertura total.
- **Revisar en Vercel** las variables `DATABASE_URL`/`HD_DATABASE_URL` de los
  proyectos `antrosapiens-api` y `antrosapiens-core` (caen a SQLite vacío;
  `antrosapiens-api-pro`, el que usa la app, está bien).
- **Rotar la contraseña de Neon** (se expuso en texto plano en el chat el
  2026-09-10 al pegar una captura de terminal).
- Configurar `TAVILY_API_KEY` y `DATABASE_URL` como *Secrets* reales en GitHub
  Actions (repo → Settings → Secrets and variables → Actions) para que
  `.github/workflows/prospeccion-tavily.yml` deje de fallar en silencio.
- P1 sin implementar (documentado, no autorizado todavía): regla general para
  ArchDaily/galerías de fotos y duplicación casi idéntica entre evidencias
  (ver auditoría de calidad de evidencia, 2026-09-10).

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

- **Diagnóstico 2026-09-10 (solo lectura, sin commits) — verificación de rutas
  pedidas por el operador:**
  1. `android_v2` (único directorio Android de este repo; `android_v3` **no
     existe** aquí) carga los expedientes por red, no por JSON empaquetado:
     `android_v2/app/src/main/assets/public/index.html:405,450-451`
     (`fetch(\`${API}/expedientes?...\`)`, `fetch(\`${API}/verificados?...\`)`).
     El WebView (`MainActivity.kt:37-38,82`) solo sirve el HTML/JS local vía
     `WebViewAssetLoader`; los datos siempre vienen de la API remota
     (`antrosapiens-api-pro.vercel.app`).
  2. `sandbox/motor_epistemico.py` **no existe** en este repo (verificado con
     `find`).
  3. `CuradorAntropologico` **no existe** en este repo (`grep -r` sobre todo el
     árbol: 0 resultados). `clasificacion_epistemologica.py` y
     `promocion_candidatos.py` no pueden llamarlo.
  4. N/A (ver punto 3).
  5. Suite completa: **1010 passed** (no existe `./venv/bin/python` en este
     entorno; se corrió con el intérprete real del contenedor,
     `/usr/local/bin/python3 -m pytest -q`).

  Los puntos 2-4 no corresponden a `Aitor-1977/antrosapiens`: el operador
  confirmó que se confundió con otra cosa (no era este repo).

- **Bloque de trabajo 2026-09-10 (sesión larga, PRs #14-#21) — resumen:**
  1. **Exclusión por escala (201-500/501+)**: Jüsto/Frubana aparecían como
     Startup ICP pese a ser grandes y con cientos de millones levantados;
     `android_v2` ahora excluye esa banda de escala siempre, sin importar
     `categoria`.
  2. **Timeout de Neon**: `_connect_postgres()` (`db/database.py`) sin
     `connect_timeout` colgaba la función serverless indefinidamente cuando
     Neon estaba suspendido (evidencia real: 55s+ sin respuesta). Fix:
     `connect_timeout=10` + un reintento a `connect_timeout=25`.
  3. **INDAGAR no debe mostrar interpretación antropológica ya hecha**:
     `cargarHallazgos()` mapeaba los expedientes con spread (`...p`), así que
     `tipo_deuda`/`deuda_razon`/`angulo_conversacion`/`decisor_sugerido`
     viajaban al estado de la app aunque no se pintaran. Se reemplazó por una
     lista blanca explícita (solo dato observable + clasificación Nivel 1).
     De paso se expusieron `persona_citada`/`cargo` que faltaban.
  4. **Banorte/HSBC/Oracle/Maersk** aparecían como Startup (usuario reportó
     "voy a desinstalar la app"): no tenían fila en `prospectos`. Se
     registraron en `seed_prospectos.py` como `Corporativo`/`501+`.
  5. **Estados de atribución de cita** (`clasificacion_epistemologica.py`,
     función `clasificar_atribucion`): 4 estados deterministas
     (`atribucion_explicita` / `atribucion_explicita_no_extraida` /
     `ambigua` / `sin_atribucion`) con fragmento literal grounded, expuestos
     en `/expedientes` y pintados en `quienHabla()` del HTML.
  6. **Auditoría de calidad/diversidad de evidencia** (solo lectura, sin
     código): mapeo completo del pipeline, hallazgo de que `google_news` y
     `rss_fijos` leían un `summary`/`description` más rico del feed y lo
     descartaban al normalizar (pérdida de extracción real, no techo de
     fuente); Tavily con 0% del corpus por `TAVILY_API_KEY`/`DATABASE_URL`
     vacíos en el workflow de GitHub Actions (falla 100% silenciosa, 3
     corridas "exitosas" con 0 evidencias reales).
  7. **Corrección P0 de esa auditoría**: nuevo campo `resumen_fuente`
     (distinto de `cita_textual`, nunca etiquetado como cita) en
     `google_news.py`/`rss_fijos.py`, persistido y expuesto en
     `/evidencias`/`/expedientes`; URL de Contxto corregida (`/feed/` → 404
     real → `/es/feed/`, verificado en vivo).
  8. **Incidente de producción — SQLite en vez de Postgres**: descubierto al
     verificar lo anterior. `antrosapiens-api` y `antrosapiens-core` sin
     `DATABASE_URL`/`HD_DATABASE_URL`/`POSTGRES_URL` en Vercel, caían al
     fallback `sqlite:////tmp/...` (vacío). `antrosapiens-api-pro` confirmado
     intacto con los ~5.204 registros reales. **Pendiente del operador**:
     revisar/copiar la variable de entorno correcta en el dashboard de Vercel
     para los proyectos afectados (no es algo que se corrija por código).
  9. **Incidente Anthropic (ICP 81)**: organizaciones sin fila en `prospectos`
     heredaban por defecto la `categoria` de la consulta de captura
     (`'Startup'`), sin verificar tamaño real en ningún punto de la fórmula
     de `score_icp` (solo palabras clave + calidad de captura). Fix: se
     reutilizó `GIGANTES` (`relevance.py`, ya usado en el filtro de
     relevancia) ampliada con laboratorios de IA y grandes tecnológicas
     (Anthropic, OpenAI, IBM, Oracle, Salesforce, SAP…), y
     `_construir_expedientes` (`api/app.py`) ahora fuerza
     `categoria='Corporativo'` para cualquier nombre que matchee `GIGANTES`
     sin fila estructural en `prospectos`.
  10. **Incidente CEO/CNBV (ICP 79-99)**: `detectar_empresa()` aceptaba
      cualquier sigla en mayúsculas sin excepción para cargos (CEO/CFO/CTO...)
      ni reguladores (CNBV, SAT, IMSS...); "CEO de Kavak regresa..." y "CNBV
      multa a la fintech Albo..." detectaban el cargo/regulador como la
      empresa. Fix: nuevo `_SIGLAS_NO_EMPRESA` en `relevance.py` + ajustes a
      `_STOP_CAP` (plural "nuevas/nuevos", "lana"). El operador purgó a mano
      los registros viejos en Neon directamente vía `psql` antes del fix de
      código (⚠️ pegó la contraseña de Neon en texto plano en el chat en ese
      proceso — recomendado rotarla).
  11. PRs #14 a #21, todos fusionados a `main`, suite completa verde en cada
      uno (982 → 1010 passed). APK recompilado tras el fix de Anthropic
      (release `apk-32`, SHA256 del .apk:
      `0fa9825b593ab1feab26da918b0a1d2c1eba1b08e071bfc37b0e415ba212ca76`).
