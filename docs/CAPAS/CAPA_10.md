# Capa 10 — Curaduría Antropológica

> Documento generado por `scripts/docs/gen_capas.py` desde datos verificados
> contra el código. No editar a mano: regenerar con
> `python -m scripts.docs.gen_capas`. Índice: [`../DOCUMENTACION_MAESTRA.md`](../DOCUMENTACION_MAESTRA.md) §4.

- **Objetivo:** Transformar expedientes en una lectura de ecosistema (conclusiones primero).
- **Problema que resuelve:** El usuario necesita significado, no una lista de hechos.
- **Arquitectura:** Tensión central por umbrales + narrativa determinista + convergencias.

## Componentes (archivos)
hd_scraper/curaduria.py, hd_scraper/dictamen.py

## Endpoints
POST /investigacion, GET /centro, GET /informe(.md/.csv), GET /informes

## Tablas
informes_guardados

## Funciones
curar, _identificar_tension, _construir_narrativa, _curar_convergencias, _organizaciones_curadas

## Entradas → Salidas
- **Entradas:** Lista de expedientes (+ query/region/vertical)
- **Salidas:** Tensión, narrativa, convergencias, preguntas abiertas, siguiente paso

## Dependencias
← C9 · → C11

## Tests
test_curaduria, test_centro_corpus, test_informe, test_export

## Criterios de aceptación
100% determinista; no juzga (contradicciones/vacíos los trata C11).

## Limitaciones
Sin datos, entrega curaduría 'sin evidencia suficiente'.

## Relación con otras capas
Capa que precede a la Validación Científica (C11).
