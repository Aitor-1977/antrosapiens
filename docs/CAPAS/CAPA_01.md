# Capa 01 — Normalización

> Documento generado por `scripts/docs/gen_capas.py` desde datos verificados
> contra el código. No editar a mano: regenerar con
> `python -m scripts.docs.gen_capas`. Índice: [`../DOCUMENTACION_MAESTRA.md`](../DOCUMENTACION_MAESTRA.md) §4.

- **Objetivo:** Normalizar URL/empresa/título y calcular hashes de deduplicación.
- **Problema que resuelve:** La misma noticia aparece con URLs y títulos distintos; hay que dedup de forma estable.
- **Arquitectura:** Funciones puras de normalización + hashes (sha256).

## Componentes (archivos)
hd_scraper/db/models.py, hd_scraper/pipeline.py

## Endpoints
(sin endpoint propio; interno del pipeline)

## Tablas
(prepara filas para evidencias)

## Funciones
normalizar_url, normalizar_empresa, normalizar_titulo, hash_contenido, clave_contenido, calcular_hash_dedup

## Entradas → Salidas
- **Entradas:** RawItem crudo
- **Salidas:** EvidenceRecord normalizado con hash_dedup

## Dependencias
← C0 · → C2

## Tests
test_models

## Criterios de aceptación
hash_dedup = sha256(empresa + URL normalizada), único.

## Limitaciones
La detección de duplicados depende de la normalización de título.

## Relación con otras capas
Puente entre captura (C0) y contrato de evidencia (C2).
