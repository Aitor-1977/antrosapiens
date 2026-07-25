# INVENTARIO DE TABLAS — Ecosistema Hamaca Digital

> Verificado (2026-07-25). **Total: 34 tablas** = 20 (Motor A) + 14 (RadarHD).
> **Bases de datos SEPARADAS** (PostgreSQL): Motor A y RadarHD no comparten BD.
> Fuente A: `antrosapiens/hd_scraper/db/schema.sql`. Fuente B/C:
> `radarHD/src/lib/db.ts` (`initSchema`).

## §A. Motor A — `antrosapiens` (20 tablas)

| Tabla | PK | UNIQUE / CHECK / FK | Capa |
|-------|----|---------------------|------|
| `evidencias` | id | `hash_dedup` UNIQUE | 2 |
| `rechazos` | id | — | 2 |
| `prospectos` | id | `hash_dedup` UNIQUE; CHECK categoria | intake |
| `jobs` | id | — | infra |
| `salud_fuentes` | fuente | — | gob. fuentes |
| `raw_store` | id | — | storage |
| `directorio_cache` | clave | — | 5 |
| `senales_capa0` | id | — | 0 |
| `informes_guardados` | id | — | informes |
| `drift_snapshots` | id | — | 6 |
| `drift_evidencias` | id | `hash_dedup` UNIQUE; FK→drift_snapshots | 6 |
| `onlife_signals` | id | `hash_dedup` UNIQUE | 7 |
| `pipeline_comercial` | id | `hash_dedup` UNIQUE | 8 (vestigial→§24) |
| `pipeline_transiciones` | id | FK→pipeline_comercial | 8 |
| `versionado_modelo` | id | UNIQUE(componente,hash_contenido) | 12 |
| `huellas_digitales` | id | `hash` UNIQUE | 12 |
| `bitacora_decisiones` | id | — | 12 |
| `auditoria_expedientes` | id | `hash_expediente` UNIQUE | 12 |
| `certificados` | id | `certificado_id` UNIQUE | 12 |
| `memoria_cientifica` | id | UNIQUE(org_nombre,version_num) | 13 |

Detalle de columnas → `DOCUMENTACION_MAESTRA.md` §9.

## §B. RadarHD — `radarHD` / "prospector" (14 tablas)

Definidas en `radarHD/src/lib/db.ts:initSchema`. Motor: `pg.Pool` (PostgreSQL).

| Tabla | Propósito (verificado) | Motor lógico |
|-------|------------------------|--------------|
| `prospecto` | prospecto comercial (nombre, empresa, dominio, país, señal, `calificacion` A/B/C CHECK, `estado`) | C |
| `organizacion` | organizaciones observadas por el radar | B |
| `senal_radar` | señales detectadas por el radar | B |
| `observacion` | observaciones sobre organizaciones | B |
| `motor_onlife_analysis` | análisis onlife propio de RadarHD | B |
| `seguimiento_comercial` | seguimiento del pipeline comercial | C |
| `cadencia_email` | cadencia de emails a decisores | C |
| `kill_switch_log` | historial del Kill Switch | C |
| `exclusion_permanente` | exclusiones permanentes de contacto | C |
| `config_priorizacion` | configuración de priorización | B |
| `radar_run` | corridas del radar (cron/run) | B |
| `app_meta` | metadatos de la app | infra |
| `export_temp` | exportaciones temporales | infra |

## Observaciones (code-backed)
1. **Dos `prospecto(s)` distintos:** `prospectos` (Motor A, intake HD, dedup por
   hash, campos "thick data") **≠** `prospecto` (RadarHD, comercial, con estado y
   calificación). No comparten BD ni esquema.
2. **`pipeline_comercial`/`pipeline_transiciones` (Motor A) vs
   `seguimiento_comercial`/`cadencia_email` (RadarHD):** el pipeline comercial
   **real y ejecutado** está en RadarHD (Motor C). Las tablas homónimas de Motor A
   son un modelo vestigial heredado del monorepo `marito-Aitorhd`. → §24 MAESTRA.
3. **Onlife duplicado conceptualmente:** `onlife_signals` (A, determinista) y
   `motor_onlife_analysis` (RadarHD, con IA).

## Referencias
- ERD Motor A → `DOCUMENTACION_MAESTRA.md` §9.2 · Fronteras → `FRONTERAS_MOTORES.md`.
