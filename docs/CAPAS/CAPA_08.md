# Capa 08 — Pipeline Comercial

> Documento generado por `scripts/docs/gen_capas.py` desde datos verificados
> contra el código. No editar a mano: regenerar con
> `python -m scripts.docs.gen_capas`. Índice: [`../DOCUMENTACION_MAESTRA.md`](../DOCUMENTACION_MAESTRA.md) §4.

- **Objetivo:** Modelar etapas del embudo por organización.
- **Problema que resuelve:** Se necesita registrar el estado de seguimiento de una organización.
- **Arquitectura:** Etapas + transiciones; dedup por hash de org.

## Componentes (archivos)
hd_scraper/pipeline_comercial.py

## Endpoints
POST /pipeline/registrar, POST /pipeline/avanzar, GET /pipeline, GET /pipeline/funnel, GET /pipeline/{org}

## Tablas
pipeline_comercial, pipeline_transiciones

## Funciones
registrar_org, avanzar, obtener_pipeline, listar_pipeline, resumen_funnel

## Entradas → Salidas
- **Entradas:** org_nombre, etapa
- **Salidas:** Estado del embudo + transiciones + funnel

## Dependencias
← C9

## Tests
test_pipeline_comercial

## Criterios de aceptación
Modela y persiste estado; NO ejecuta contacto (sin envío de emails).

## Limitaciones
VESTIGIAL: el pipeline comercial real y ejecutado vive en RadarHD (Motor C). A deprecar (ADR-0001 / ROADMAP).

## Relación con otras capas
Cruza la frontera con Motor C; ver docs/FRONTERAS_MOTORES.md y INCONSISTENCIAS.md.
