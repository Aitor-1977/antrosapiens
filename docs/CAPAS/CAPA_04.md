# Capa 04 — Relevancia y Señales

> Documento generado por `scripts/docs/gen_capas.py` desde datos verificados
> contra el código. No editar a mano: regenerar con
> `python -m scripts.docs.gen_capas`. Índice: [`../DOCUMENTACION_MAESTRA.md`](../DOCUMENTACION_MAESTRA.md) §4.

- **Objetivo:** Filtrar ruido, detectar el sujeto (empresa) y medir calidad de captura.
- **Problema que resuelve:** No toda noticia es relevante ni menciona una organización objetivo.
- **Arquitectura:** Reglas de relevancia + detección de nombre propio + keywords de señal.

## Componentes (archivos)
hd_scraper/relevance.py, hd_scraper/signals.py

## Endpoints
(interno; usado por pipeline y expedientes)

## Tablas
(anota confianza/calidad en evidencias)

## Funciones
detectar_empresa, es_opinion, evaluar_relevancia, calcular_calidad, detectar_keywords, calcular_confianza

## Entradas → Salidas
- **Entradas:** Título/cita textual
- **Salidas:** Relevancia (bool), empresa detectada, keywords, confianza, calidad

## Dependencias
← C0/C2 · → C3

## Tests
test_relevance, test_signals

## Criterios de aceptación
Subcadena sin acentos = extracción (no interpretación).

## Limitaciones
Detección de empresa por heurística de nombre propio.

## Relación con otras capas
Habilita la agregación de expedientes y el scoring de C3.
