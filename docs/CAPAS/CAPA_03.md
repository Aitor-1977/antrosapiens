# Capa 03 — Inferencia Antropológica

> Documento generado por `scripts/docs/gen_capas.py` desde datos verificados
> contra el código. No editar a mano: regenerar con
> `python -m scripts.docs.gen_capas`. Índice: [`../DOCUMENTACION_MAESTRA.md`](../DOCUMENTACION_MAESTRA.md) §4.

- **Objetivo:** Convertir señales objetivas en análisis profundo DETERMINISTA (sin IA).
- **Problema que resuelve:** Hace falta clasificar (scoring, Dolor Cultural, ICP) de forma reproducible y auditable.
- **Arquitectura:** Reglas y tablas declaradas; combinaciones de señales; profundidad × vertical.

## Componentes (archivos)
hd_scraper/analisis.py, hd_scraper/engine/rule_engine.py, hd_scraper/dictamen.py

## Endpoints
POST /analizar, GET /alertas

## Tablas
(opera sobre evidencias agregadas)

## Funciones
analizar, _deuda_principal, _senal_dominante, _intensidad, _calcular_profundidad, generar_dictamen, generar_ranking

## Entradas → Salidas
- **Entradas:** keywords, vertical, confianza, calidad
- **Salidas:** scoring A/B/C, tipo_deuda, score_icp, profundidad_dolor, viabilidad, decisor, razon

## Dependencias
← C2 · → C9, C10, C11

## Tests
test_analisis, test_rule_engine, test_fase2

## Criterios de aceptación
Mismo insumo ⇒ mismo resultado. Sin LLM. Interpretación declarada (Frontera de Interpretación).

## Limitaciones
Hipótesis preliminares; la validación de rigor la hace C11.

## Relación con otras capas
Único motor de inferencia del ecosistema (ADR-0001).
