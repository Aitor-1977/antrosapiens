# Changelog — Antrosapiens (Motor A)

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).
Reconstruido desde el historial Git real (`git log`). Cada entrada incluye
fecha, commit y archivos relevantes. Versionado por hitos de capa (no hay tags
git; las versiones son etiquetas de hito de esta documentación).

> Nota de numeración: los mensajes de commit históricos usan "Capa 8 = Dolor
> Cultural" y "Capa 9 = Pipeline Comercial"; la numeración final consolidada
> (`hd_scraper/laboratorio.py`) usa 8 = Pipeline Comercial, 9 = DolorMap. Ver
> `INCONSISTENCIAS.md`. Aquí se conservan las etiquetas históricas del commit.

## [1.0.3] — Fase 4 · Análisis de eliminación (bloqueo documentado) — 2026-07-29
### Analysis (repo RadarHD, sin cambios de código)
- Protocolo de 7 pasos aplicado. **Inventario de referencias activas:**
  - `expedientes.service.ts`: 4 importadores vivos — ruta `organizaciones` +
    `ecosistema.service` + `dictamenPericial.service` + `recomendacion.service`.
  - `concentrador.ts`: `admin/ejecutar-todo` (`concentrar`), ruta `organizaciones`
    (`concentrar`, `calcularImplicacionSistemica`), `dictamenPericial.service`
    (`calcularImplicacionSistemica`), `evidencia.service` (`canonicalizar`),
    `expedientes.service` (tipos) + `concentrador.test.ts`.
- **Consumidores comerciales ya migrados** (Fase 3): `dictamen`, `recomendaciones`,
  `prioridades`, `oportunidades`, `dictamen/[org]` → Motor-A-fed vía el adaptador.
  `cadencia`/`lista-matutina`/`email-decisor` son operación comercial (Motor C),
  no inferencia; no tocan estos archivos.
- **No se eliminó ningún archivo**: `concentrador.ts` es load-bearing del
  subsistema de **ingesta local** (`canonicalizar`/`concentrar` → `senal_radar`/
  `observacion` que leen paneles vivos: señales, dashboard, lista-matutina, cron,
  tarjeta); `expedientes.service.ts` es el único adaptador compartido (borrarlo
  duplicaría lógica o acoplaría el gateway a Postgres). Verificación de
  no-regresión: `tsc=0`, `vitest` 205/205. Detalle → `ROADMAP §Fase 4`.

## [1.0.2] — Fase 3 · Detalle del Expediente Vivo migrado a Motor A — 2026-07-29
### Changed (repo RadarHD)
- `src/lib/services/expedientes.service.ts`: reescrito como **adaptador del
  gateway**. `construirExpedientesVivos`/`construirExpedienteVivo` consumen
  Motor A (`/organizaciones[/{id}]`) y mapean a `ExpedienteVivo`. RadarHD ya no
  ejecuta `curar()`/`interpretar()` en el camino de producción.
- `src/app/api/radar/organizaciones/[id]/route.ts`: el detalle obtiene toda la
  inteligencia científica (incl. `contexto_ecosistemico`) de Motor A; compone
  `recomendacion_estrategica`/`dictamen_pericial` (Motor C) server-side.
- `src/app/api/radar/drift/[org]/route.ts`: consume `GET /organizaciones/{id}/drift`.
### Added (repo antrosapiens · Motor A)
- Ítems de `GET /organizaciones` enriquecidos con `vertical`, `cadena_evidencia`
  y `fuentes` (aditivo) para la trazabilidad de Motor C.
### Removed (repo RadarHD)
- `derivarDriftNarrativo` + interfaz `DriftNarrativo` (código muerto tras migrar
  el Drift a Motor A).
### Notes
- Sin cambios visuales; sin inferencia antropológica en React. Verificación:
  `tsc=0`, `vitest` 205/205, `next build` verde, `pytest` 726/726.

## [1.0.1] — Cutover 1.0 · Expediente Vivo (paridad de forma) — 2026-07-29
### Added
- **Expediente Vivo en Motor A** (`hd_scraper/expediente_vivo.py`): funciones
  deterministas que emiten EXACTAMENTE las formas `OrganizacionObservada`
  (listado), `Dossier` (detalle) y `Drift` que consumen los componentes tipados
  de RadarHD. IDs enteros deterministas compartidos entre listado y detalle;
  `evidencia_ids` trazables a la cadena de evidencia.
- Endpoints solo-lectura `GET /organizaciones`, `/organizaciones/{id}`,
  `/organizaciones/{id}/drift` (`hd_scraper/api/app.py`).
- `tests/test_expediente_vivo.py` (22 tests; 99% de cobertura del módulo — solo
  quedan dos guardas defensivas inalcanzables). Suite total: 721 tests verdes.
- Métodos de gateway `organizaciones/organizacion/organizacionDrift`
  (repo RadarHD, `src/lib/motor-a.gateway.ts`; aditivo, `tsc=0`).
### Notes
- Frontera A/C: `recomendacion_estrategica`, `dictamen_pericial` y `dolormap`
  viajan **`null`** (comercial = Motor C / sin fuente). El **flip de las rutas
  proxy** de RadarHD se difiere a la Fase 3 (Motor C) para no alterar la
  experiencia visual. Ver `CONTRATOS_API.md §1quater` y `ROADMAP_ARQUITECTONICO.md`.

## [1.0.0] — Arquitectura 1.0 — 2026-07-25
### Changed
- Oficializada la **Arquitectura 1.0** (ADR-0001): *Motor A piensa, B muestra,
  C vende*. Un único Motor de Inferencia (Motor A). — `eaff680`
### Added
- `ADR_0001_ARQUITECTURA_1_0.md`, gateway oficial en RadarHD y manifiesto de
  migración (repo radarHD). Archivos: `docs/ADR/ADR_0001_ARQUITECTURA_1_0.md`,
  `docs/FRONTERAS_MOTORES.md`, `docs/ROADMAP_ARQUITECTONICO.md`.

## [0.18.0] — Documentación del Ecosistema — 2026-07-25
### Added
- Auditoría real de los 3 motores + 8 documentos de arquitectura del ecosistema
  (verificados contra el código de antrosapiens y radarHD). — `61efb81`
- `DOCUMENTACION_MAESTRA.md` (documentación técnica maestra de Motor A). — `643f9c0`
- Archivos: `docs/ARQUITECTURA_ECOSISTEMA.md`, `docs/CONTRATOS_API.md`,
  `docs/INVENTARIO_{COMPONENTES,ENDPOINTS,TABLAS}.md`, `docs/GUIA_RECONSTRUCCION_TOTAL.md`.

## [0.12.0]–[0.18.0] — Capas 11–18 (científicas) — 2026-07-25
### Added
- **Capa 18** Sistema Operativo del Laboratorio (dashboard maestro). — `75b27b4`
  · `hd_scraper/laboratorio.py`
- **Capa 17** Publicador Científico. — `f658b8e` · `hd_scraper/publicador.py`
- **Capa 16** Observatorio LATAM. — `97fc173` · `hd_scraper/observatorio.py`
- **Capa 15** Motor Predictivo Antropológico. — `546b179` · `hd_scraper/predictivo.py`
- **Capa 14** Comparador Temporal y Ecosistémico. — `38399ad` · `hd_scraper/comparador.py`
- **Capa 13** Memoria Científica (historial inmutable). — `00d3140` ·
  `hd_scraper/memoria.py`, `memoria_store.py`
- **Capa 12** Gobernanza Científica, Auditoría y Reproducibilidad. — `a49521f` ·
  `hd_scraper/gobernanza.py`, `gobernanza_store.py`
- **Capa 11** Validación Científica del Peritaje. — `d2d59eb` ·
  `hd_scraper/validacion_cientifica.py`

## [0.10.0] — Capa 10 (Curaduría) — 2026-07-23
### Added
- **Capa 10** Motor de Curaduría Antropológica (conclusiones primero). — `730a30f`
  · `hd_scraper/curaduria.py`
- Directiva de Curaduría Analítica (filtrado, scoring por profundidad). — `9406105`
- Exponer `profundidad_dolor` y `viabilidad` en expedientes. — `3982dd8`

## [0.09.0] — Capa 9 (Pipeline Comercial) + inteligencia — 2026-07-23
### Added
- **Capa 9** Pipeline Comercial (flujo por organización). — `d0a7c6f` ·
  `hd_scraper/pipeline_comercial.py`
- DolorMap Visual (vista consolidada por organización). — `b2d58ad`
- Fase 2: Dictamen Antropológico, Ranking TOP 10, Dossier y Alertas. — `3c08c5d`
- Centro de Inteligencia Comercial + corpus LATAM. — `143e428`
- Investigación Automática (un clic = ciclo completo). — `acdb7f3`

## [0.08.0] — Capa 8 (Dolor Cultural) / Expedientes Vivos — 2026-07-23
### Added
- Expedientes Vivos: evidencia agrupada por organización con Dolor Cultural. — `c27c107`
- CLAUDE.md: sección "Frontera de Interpretación (hd-scraper vs RadarHD)". — `42f8631`

## [0.07.0] — Capa 7 (Onlife) — 2026-07-23
### Added
- **Capa 7** Motor Onlife (observación conductual). — `474a3ae` · `hd_scraper/onlife.py`

## [0.06.0] — Capa 6 (Drift Narrativo) — 2026-07-23
### Added
- **Capa 6** Motor de Drift Narrativo (captura, comparación y UI). — `ddc432a` ·
  `hd_scraper/drift.py`, `drift_compare.py`

## [0.03.0] — Inferencia base (Capas 1–5) — 2026-07-13 … 2026-07-19
### Added
- Análisis profundo: scoring A/B/C + Deuda Cultural + ICP + decisor. — `656ded8` ·
  `hd_scraper/analisis.py`
- Afinar Deuda Cultural: combinaciones de señales, ángulo, matiz por vertical. — `ddf4803`
- Captura Inteligente: dedup robusto, filtro de relevancia y calidad. — `a37fd3f` ·
  `hd_scraper/relevance.py`, `signals.py`
- Enriquecimiento: perfil de entidad (web, tesis, vertical, LinkedIn). — `4ffa7da` ·
  `hd_scraper/enrich.py`
- Directorio Wikidata (cascada + caché 7 días). — `0d2678f` · `hd_scraper/directorio.py`
- Exportar prospectos (CSV/JSON/Markdown). — `a7751ef`, `08372ea`
- Verificación de correo del decisor con Hunter (opcional). — `faf47dd` · `hd_scraper/hunter.py`
- Descubrimiento LATAM (8 países). — `f8535fd` · `hd_scraper/discovery.py`

## [0.02.0] — Evidencia + Contrato /corpus — 2026-07-13 … 2026-07-14
### Added
- keywords + confianza + endpoint `/corpus` + frontera Motor A/B. — `de6ee10`
- Exponer `calidad_captura` en `/corpus` (extensión aditiva v1). — `4763fcc`
- Validador de producción determinista + auditoría de contrato. — `9eac847` ·
  `hd_scraper/validation/validator.py`

## [0.00.0] — Capa 0 (Sensores/Ingesta) — 2026-07-19
### Added
- **Capa 0** motor de reglas determinista + ingesta de señales (webhook). — `50b348a` ·
  `hd_scraper/engine/rule_engine.py`, `hd_scraper/ingesta/`
- Capa 0 corre en la app: ingesta de noticias y análisis desde el panel. — `aee3474`
- Regla 'Evento' para titulares de prensa + filtro de ruido. — `150aff6`
- Conectores de ingesta: RSS gratuito (reemplazo de Apify) + yt-dlp. — `a0f6a98`, `5262116`
- Base de empresas real (Wikidata). — `80830ee`
