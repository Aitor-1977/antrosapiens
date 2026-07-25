# Capa 14 — Comparador Temporal y Ecosistémico

> Documento generado por `scripts/docs/gen_capas.py` desde datos verificados
> contra el código. No editar a mano: regenerar con
> `python -m scripts.docs.gen_capas`. Índice: [`../DOCUMENTACION_MAESTRA.md`](../DOCUMENTACION_MAESTRA.md) §4.

- **Objetivo:** Comparar organizaciones, ecosistemas, periodos y patrones.
- **Problema que resuelve:** Se necesita contraste estructural sin interpretación.
- **Arquitectura:** Funciones puras de diferencia (sets, distribuciones).

## Componentes (archivos)
hd_scraper/comparador.py

## Endpoints
GET /comparar, GET /ecosistema/comparar, GET /periodos

## Tablas
(opera sobre expedientes)

## Funciones
comparar_organizaciones/ecosistemas/periodos/patrones/narrativas/dolor/validaciones, detectar_convergencias/divergencias, generar_matriz

## Entradas → Salidas
- **Entradas:** Dos organizaciones/conjuntos o una org + fecha de corte
- **Salidas:** Diferencias campo a campo, matriz, convergencias/divergencias

## Dependencias
← C13 · → C16, C18

## Tests
test_comparador (15), 100% cobertura

## Criterios de aceptación
Solo compara, no interpreta.

## Limitaciones
Comparación de narrativas por solapamiento léxico (Jaccard).

## Relación con otras capas
Alimenta al Observatorio (C16).
