# Capa 16 — Observatorio LATAM

> Documento generado por `scripts/docs/gen_capas.py` desde datos verificados
> contra el código. No editar a mano: regenerar con
> `python -m scripts.docs.gen_capas`. Índice: [`../DOCUMENTACION_MAESTRA.md`](../DOCUMENTACION_MAESTRA.md) §4.

- **Objetivo:** Pasar de la organización individual al ecosistema.
- **Problema que resuelve:** Se necesita inteligencia agregada por región/vertical/ecosistema.
- **Arquitectura:** Agregación determinista; reutiliza ranking (C3) y riesgo (C15).

## Componentes (archivos)
hd_scraper/observatorio.py

## Endpoints
GET /latam, GET /latam/{pais}, GET /vertical/{nombre}

## Tablas
(opera sobre expedientes)

## Funciones
analizar_region/vertical/ecosistema, identificar_patrones_regionales/tensiones, calcular_indicadores, emitir_reporte_regional

## Entradas → Salidas
- **Entradas:** Conjunto de expedientes (+ filtro país/vertical)
- **Salidas:** Ranking, riesgos comunes, patrones, vacíos sistémicos, tensiones, indicadores

## Dependencias
← C3, C14, C15 · → C18

## Tests
test_observatorio (13), 100% cobertura

## Criterios de aceptación
País por mención literal (substring sin acentos) = extracción.

## Limitaciones
Algunas vistas avanzadas (clusters/outliers) no tienen endpoint aún.

## Relación con otras capas
Fuente ecosistémica del dashboard (C18).
