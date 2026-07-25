# Capa 06 — Drift Narrativo

> Documento generado por `scripts/docs/gen_capas.py` desde datos verificados
> contra el código. No editar a mano: regenerar con
> `python -m scripts.docs.gen_capas`. Índice: [`../DOCUMENTACION_MAESTRA.md`](../DOCUMENTACION_MAESTRA.md) §4.

- **Objetivo:** Detectar cambios en el discurso público entre snapshots.
- **Problema que resuelve:** El relato de una organización cambia con el tiempo; ese cambio es evidencia.
- **Arquitectura:** Snapshots versionados; comparación de consecutivos → evidencias narrativas (hechos).

## Componentes (archivos)
hd_scraper/drift.py, hd_scraper/drift_compare.py

## Endpoints
POST /drift/capturar, GET /drift/{org}

## Tablas
drift_snapshots, drift_evidencias

## Funciones
capturar_snapshot, obtener_timeline, obtener_snapshot_anterior

## Entradas → Salidas
- **Entradas:** org_nombre, sitio_web
- **Salidas:** Timeline de snapshots + evidencias de cambio (tipo cerrado)

## Dependencias
← C5 · → C9

## Tests
test_drift, test_drift_compare

## Criterios de aceptación
Los tipos de cambio están cerrados; se observa el hecho, no se interpreta.

## Limitaciones
Requiere páginas observables (no SPA/robots/bloqueo).

## Relación con otras capas
Nutre el DolorMap (C9) con evolución del relato.
