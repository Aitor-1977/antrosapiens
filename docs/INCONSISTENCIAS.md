# INCONSISTENCIAS — Control de calidad documental

> Generado por el control de calidad (Fase 10). Registra hallazgos verificados
> contra el código. Cada entrada: descripción · archivo · impacto · recomendación.
> El verificador de enlaces/commits/endpoints vive en el proceso de documentación
> (ver `README_TECNICO.md` → "Cómo regenerar la documentación").

## Resultado del control automático (2026-07-25)
- **Documentos `.md` en `docs/`:** 50.
- **Enlaces `.md` rotos:** 0 (tras crear `README.md` e `INCONSISTENCIAS.md`).
- **Capas presentes:** 19/19 (`CAPA_00`…`CAPA_18`).
- **Commits citados en `CHANGELOG.md`:** 41/41 existen en Git.
- **Tablas citadas vs `schema.sql`:** 20/20 reales.
- **Endpoints Motor A citados vs `app.py`:** todos existen (72).

## A. Inconsistencias arquitectónicas (código vs documentación/diseño)

### A1 — `VERSION_PIPELINE = "12.0.0"` etiquetada "12 capas"
- **Descripción:** la constante dice "Pipeline completo (12 capas)" pero el
  sistema tiene 19 capas (0–18).
- **Archivo:** `hd_scraper/gobernanza.py:42`.
- **Impacto:** bajo (metadato de versión); puede confundir auditorías.
- **Recomendación:** subir a una versión que refleje 0–18 y corregir el comentario.

### A2 — `ETAPAS_PIPELINE` lista solo 5 etapas
- **Descripción:** `("captura","curaduria","inferencia_antropologica",
  "validacion_cientifica","gobernanza_cientifica")` — pipeline macro, no las 19 capas.
- **Archivo:** `hd_scraper/gobernanza.py:56`.
- **Impacto:** bajo (intencional); documentar para evitar lecturas erróneas.
- **Recomendación:** comentar que es el pipeline macro; opcionalmente enriquecer.

### A3 — `pipeline_comercial.py` (Motor A) cruza la frontera con Motor C
- **Descripción:** Motor A modela un embudo comercial (tablas
  `pipeline_comercial`, `pipeline_transiciones`, rutas `/pipeline/*`), pero el
  pipeline comercial real y ejecutado vive en RadarHD (Motor C).
- **Archivo:** `hd_scraper/pipeline_comercial.py`; esquema `db/schema.sql`.
- **Impacto:** medio (viola la Arquitectura 1.0: Motor A no comercializa).
- **Recomendación:** deprecar en Motor A (ver `ROADMAP_ARQUITECTONICO.md` Fase 4);
  no ejecuta contacto, es vestigial del monorepo de origen `marito-Aitorhd`.

### A4 — Doble numeración de capas (historia de commits vs numeración final)
- **Descripción:** los commits usan "Capa 8 = Dolor Cultural", "Capa 9 = Pipeline
  Comercial"; la numeración final (`laboratorio.py:CAPAS`) usa 8 = Pipeline
  Comercial, 9 = DolorMap.
- **Archivo:** historial Git vs `hd_scraper/laboratorio.py`.
- **Impacto:** bajo (histórico); podría confundir al leer el CHANGELOG.
- **Recomendación:** el CHANGELOG conserva las etiquetas históricas y lo advierte;
  la numeración canónica es la de `CAPAS/`.

### A5 — RadarHD aún infiere con IA (deuda de Arquitectura 1.0)
- **Descripción:** RadarHD (Motor B) contiene engines de inferencia y servicios
  LLM; por ADR-0001 debe eliminarlos y consumir Motor A.
- **Archivo:** repo `radarHD` (`src/lib/engines/`, `services/llm.ts`).
- **Impacto:** alto (dos fuentes de verdad hasta completar el cutover).
- **Recomendación:** ejecutar el cutover (`radarHD/MIGRACION_ARQUITECTURA_1_0.md`,
  `ROADMAP_ARQUITECTONICO.md`).

## B. Observaciones del verificador (no son defectos)

### B1 — Rutas `/api/radar/ecosistema/*` no están en `app.py` de Motor A
- **Descripción:** el verificador de endpoints marcó `/ecosistema/{clusters,
  outliers,centinelas,patrones,tendencias}`, `/prioridades`, `/recomendaciones`,
  `/ecosistema/dashboard` como "no hallados en `app.py`".
- **Aclaración:** son **rutas reales de RadarHD** (`INVENTARIO_ENDPOINTS.md §B`),
  no de Motor A. Correcto que no estén en `app.py`. Son a la vez **brechas de
  contrato** de Motor A (lo que RadarHD calcula y A no expone) — ver
  `ROADMAP_ARQUITECTONICO.md` Fase 1.
- **Impacto:** ninguno (falso positivo por contexto A vs B).
- **Recomendación:** al cerrar las brechas, Motor A expondrá equivalentes.

## C. Infraestructura

### C1 — Sin CI/CD versionado en Motor A
- **Descripción:** no existe `.github/workflows/` en `antrosapiens`.
- **Archivo:** raíz del repo.
- **Impacto:** medio (los tests no corren automáticamente en push).
- **Recomendación:** añadir workflow `pytest -q` (fuera de alcance de esta tarea
  de documentación).

### C2 — Encoding de feeds (`resp.text` vs `resp.content`)
- **Descripción:** `google_news.py` y `rss_fijos.py` parsean `resp.text` (riesgo
  de mojibake).
- **Archivo:** `hd_scraper/connectors/{google_news,rss_fijos}.py`.
- **Impacto:** bajo/medio (calidad de `cita_textual` con charsets raros).
- **Recomendación:** pasar `resp.content` a feedparser (registrado en `CLAUDE.md`
  "Errores recurrentes").

## Documentos duplicados / huérfanos
- **Duplicados:** ninguno (los documentos del ecosistema se movieron a `docs/`,
  no se copiaron).
- **Huérfanos:** ninguno tras crear `docs/README.md` (índice que enlaza todo).
- **Documentos preexistentes en `docs/`** (`captura_inteligente.md`,
  `evidencia_produccion.*`, `perfil_prospecto_hd.md`, `validacion_produccion.md`):
  conservados; enlazados desde el índice como "documentación de contexto".
