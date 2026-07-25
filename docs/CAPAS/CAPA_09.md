# Capa 09 — Dolor Cultural / DolorMap

> Documento generado por `scripts/docs/gen_capas.py` desde datos verificados
> contra el código. No editar a mano: regenerar con
> `python -m scripts.docs.gen_capas`. Índice: [`../DOCUMENTACION_MAESTRA.md`](../DOCUMENTACION_MAESTRA.md) §4.

- **Objetivo:** Vista consolidada por organización (todas las capas).
- **Problema que resuelve:** La inteligencia por org está repartida entre evidencia, drift, onlife y análisis.
- **Arquitectura:** Agregación por organización + análisis determinista + patrones.

## Componentes (archivos)
hd_scraper/analisis.py + endpoints en api/app.py (dolormap, dossier)

## Endpoints
GET /dolormap/{org}, GET /dossier/{org}

## Tablas
(lee evidencias, drift, onlife, pipeline)

## Funciones
_detectar_patrones, _construir_expedientes, dolormap, dossier_org

## Entradas → Salidas
- **Entradas:** org_nombre
- **Salidas:** Expediente consolidado + dossier HTML imprimible

## Dependencias
← C3, C6, C7, C8 · → C10, C11, C12

## Tests
test_dolormap

## Criterios de aceptación
Hipótesis marcadas como preliminares hasta validación (C11).

## Limitaciones
El dossier se sirve como HTML (brecha JSON para Motor B, ROADMAP).

## Relación con otras capas
Insumo del expediente que validan/gobiernan C11/C12.
