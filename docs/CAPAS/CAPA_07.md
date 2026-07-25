# Capa 07 — Onlife

> Documento generado por `scripts/docs/gen_capas.py` desde datos verificados
> contra el código. No editar a mano: regenerar con
> `python -m scripts.docs.gen_capas`. Índice: [`../DOCUMENTACION_MAESTRA.md`](../DOCUMENTACION_MAESTRA.md) §4.

- **Objetivo:** Observar señales conductuales en espacios digitales.
- **Problema que resuelve:** La vida operativa de una organización deja rastro fuera de la prensa.
- **Arquitectura:** Observadores por fuente (GitHub, Hacker News, blog/changelog) → señales estructuradas.

## Componentes (archivos)
hd_scraper/onlife.py

## Endpoints
POST /onlife/observar, GET /onlife/{org}

## Tablas
onlife_signals

## Funciones
observar, observar_github, observar_hackernews, observar_blog, persistir_señales, obtener_perfil

## Entradas → Salidas
- **Entradas:** org_nombre (+ fuentes)
- **Salidas:** Señales onlife por fuente + perfil consolidado

## Dependencias
← C5 · → C9

## Tests
test_onlife

## Criterios de aceptación
Determinista sobre lo observado; dedup por hash.

## Limitaciones
Depende de disponibilidad de las fuentes públicas.

## Relación con otras capas
Aporta comportamiento al DolorMap (C9).
