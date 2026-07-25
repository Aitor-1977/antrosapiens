# INVENTARIO DE ENDPOINTS — Ecosistema Hamaca Digital

> Verificado (2026-07-25). **Total: 121 endpoints** = 72 (Motor A) + 49 (RadarHD).
> Fuente A: `antrosapiens/hd_scraper/api/app.py` (decoradores `@app.*`).
> Fuente B/C: `radarHD/src/app/api/**/route.ts` (Next App Router).

## §A. Motor A — `antrosapiens` (72, FastAPI, solo lectura)

| # | Método | Ruta | Capa |
|---|--------|------|------|
| 1 | GET | `/` | — |
| 2 | GET | `/health` | — |
| 3 | GET | `/evidencias` | 2 |
| 4 | GET | `/evidencias/{id}` | 2 |
| 5 | GET | `/corpus` | **contrato A→B/C** |
| 6 | GET | `/salud-fuentes` | gob. fuentes |
| 7 | GET | `/stats` | métricas |
| 8–13 | GET | `/prospectos`, `/prospectos/categorias`, `/prospectos/{id}`, `/prospectos/export.{csv,json,md}` | intake |
| 14–15 | POST | `/prospectos`, `/prospectos/bulk` (X-Ingest-Token) | intake |
| 16 | GET | `/admin` | intake |
| 17–19 | POST | `/scrape`, `/investigacion`, `/corpus/poblar` | captura |
| 20–23 | POST | `/enrich`, `/analizar`, `/verificar-contacto`, `/directorio` | 5/3 |
| 24–25 | POST | `/webhook/ingesta`, `/ingesta/noticias` | 0 |
| 26–27 | GET | `/senales-capa0`, `/centro` | 0 |
| 28–34 | GET/POST/DELETE | `/informe`, `/informe.md`, `/informe.csv`, `/informe/guardar`, `/informes`, `/informes/{id}.md`, `/informes/{id}` | informes |
| 35 | GET | `/expedientes` | agregación |
| 36 | GET | `/alertas` | dictamen |
| 37 | GET | `/validacion/{org}` | 11 |
| 38–39 | GET | `/auditoria/{org}`, `/certificado/{org}` | 12 |
| 40–42 | GET | `/historial/{org}`, `/timeline/{org}`, `/versiones/{org}` | 13 |
| 43–45 | GET | `/comparar`, `/ecosistema/comparar`, `/periodos` | 14 |
| 46–47 | GET | `/proyeccion/{org}`, `/escenarios/{org}` | 15 |
| 48–50 | GET | `/latam`, `/latam/{pais}`, `/vertical/{nombre}` | 16 |
| 51–53 | GET | `/publicar/peritaje/{org}`, `/publicar/informe/{org}`, `/publicar/pdf/{org}` | 17 |
| 54–56 | GET | `/laboratorio`, `/estado`, `/dashboard` | 18 |
| 57–58 | POST/GET | `/drift/capturar`, `/drift/{org}` | 6 |
| 59–60 | POST/GET | `/onlife/observar`, `/onlife/{org}` | 7 |
| 61–62 | GET | `/dolormap/{org}`, `/dossier/{org}` | 9 |
| 63–67 | POST/GET | `/pipeline/registrar`, `/pipeline/avanzar`, `/pipeline`, `/pipeline/funnel`, `/pipeline/{org}` | 8 |
| 68–72 | GET | `/manifest.webmanifest`, `/sw.js`, `/icon-192.png`, `/icon-512.png`, `/apple-touch-icon.png` | PWA |

## §B. RadarHD — `radarHD` / "prospector" (49, Next App Router)

### Motor de inteligencia propio (`/api/radar/*`)
| Método | Ruta |
|--------|------|
| POST | `/api/radar/buscar-uno` |
| GET | `/api/radar/cron` |
| POST,GET | `/api/radar/densificar` |
| GET | `/api/radar/dictamen`, `/api/radar/dictamen/[org]` |
| GET | `/api/radar/drift/[org]` |
| GET | `/api/radar/ecosistema`, `/ecosistema/centinelas`, `/ecosistema/clusters`, `/ecosistema/dashboard`, `/ecosistema/outliers`, `/ecosistema/patrones`, `/ecosistema/riesgos`, `/ecosistema/tendencias` |
| POST | `/api/radar/fondos` |
| GET | `/api/radar/onlife/[org]` |
| GET | `/api/radar/oportunidades`, `/prioridades`, `/recomendaciones`, `/recomendaciones/[org]` |
| GET,POST | `/api/radar/organizaciones`, `/organizaciones/[id]` (GET) |
| POST | `/api/radar/run` |
| GET,PATCH | `/api/radar/senales`, `/senales/[id]` |

### Pipeline comercial (Motor C)
| Método | Ruta |
|--------|------|
| GET,POST | `/api/cadencia` |
| POST | `/api/decisores` |
| POST | `/api/email-decisor` |
| GET,POST | `/api/kill-switch` |
| GET | `/api/lista-matutina` |
| POST | `/api/prospeccion`; GET `/api/prospeccion/descargar`; `/api/prospeccion/diag` |
| GET,DELETE,POST | `/api/prospectos`; GET,DELETE,PATCH `/api/prospectos/[id]` |
| GET,POST | `/api/seguimiento`; PATCH,DELETE `/api/seguimiento/[id]` |

### Soporte / diagnóstico / render
| Método | Ruta |
|--------|------|
| GET,POST | `/api/admin/ejecutar-todo` |
| GET | `/api/dashboard/metricas` |
| POST | `/api/dictamen`, `/api/drift`, `/api/enriquecer` |
| GET | `/api/informes` |
| GET | `/api/diag/drift`, `/api/diag/gemini`, `/api/diag/ia`, `/api/diag/sitio` |
| GET | `/api/sow/[id]`, `/api/tarjeta/[id]` |

> Nota: las rutas de RadarHD son **internas** (su UI + crons las llaman). Motor A
> **no** las consume. Detalle de métodos por ruta: ver el árbol en
> `ARQUITECTURA_ECOSISTEMA.md` y el código `src/app/api/**/route.ts`.

## Solapamiento conceptual entre motores (hallazgo)
Ambos motores exponen "dictamen", "drift", "onlife", "ecosistema": Motor A de
forma **determinista**, RadarHD con **IA**. No es duplicación *dentro* de un repo
(prohibida), sino **paralelismo entre motores** por diseño (A objetivo, B/C
interpretativo). → `DOCUMENTACION_MAESTRA.md` §24, `ROADMAP_ARQUITECTONICO.md`.
