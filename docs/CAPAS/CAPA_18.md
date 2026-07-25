# Capa 18 — Sistema Operativo del Laboratorio

> Documento generado por `scripts/docs/gen_capas.py` desde datos verificados
> contra el código. No editar a mano: regenerar con
> `python -m scripts.docs.gen_capas`. Índice: [`../DOCUMENTACION_MAESTRA.md`](../DOCUMENTACION_MAESTRA.md) §4.

- **Objetivo:** Integrar las 19 capas en un dashboard maestro y estado integral.
- **Problema que resuelve:** Se necesita una vista única del estado de motores, corpus, ciencia y gobernanza.
- **Arquitectura:** Funciones puras que agregan estados ya calculados; endpoint HTML.

## Componentes (archivos)
hd_scraper/laboratorio.py

## Endpoints
GET /laboratorio, GET /estado, GET /dashboard (HTML)

## Tablas
(lee conteos de todas las tablas)

## Funciones
estado_general/capas/corpus/pipeline/validacion/gobernanza/observatorio

## Entradas → Salidas
- **Entradas:** Conteos de BD + expedientes
- **Salidas:** Estado integral (motores A/B/C, corpus, validación, gobernanza, 19 capas)

## Dependencias
← C11, C12, C16 (y conteos de todas)

## Tests
test_laboratorio (13), 100% cobertura

## Criterios de aceptación
Determinista; el dashboard HTML es bien formado (verificado).

## Limitaciones
Los estados de Motor B/C son declarativos (viven en RadarHD).

## Relación con otras capas
Capa cúspide: consolida el estado del pipeline completo.
