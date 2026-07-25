# Capa 13 — Memoria Científica

> Documento generado por `scripts/docs/gen_capas.py` desde datos verificados
> contra el código. No editar a mano: regenerar con
> `python -m scripts.docs.gen_capas`. Índice: [`../DOCUMENTACION_MAESTRA.md`](../DOCUMENTACION_MAESTRA.md) §4.

- **Objetivo:** Historial longitudinal inmutable de cada expediente.
- **Problema que resuelve:** El conocimiento evoluciona; hay que conservar todas las versiones sin sobrescribir.
- **Arquitectura:** Append-only; version_num monótono; dedup por hash de huella.

## Componentes (archivos)
hd_scraper/memoria.py, hd_scraper/memoria_store.py

## Endpoints
GET /historial/{org}, GET /timeline/{org}, GET /versiones/{org}

## Tablas
memoria_cientifica (UNIQUE org_nombre, version_num)

## Funciones
crear_version, comparar_versiones, detectar_cambios, construir_timeline, calcular_evolucion, emitir_historial, guardar_version, recuperar_historial

## Entradas → Salidas
- **Entradas:** Expediente + validación + huella
- **Salidas:** Timeline científica, evolución del dolor, comparación de versiones

## Dependencias
← C12 · → C14

## Tests
test_memoria (17), 100% cobertura

## Criterios de aceptación
Nunca UPDATE/DELETE; solo añade si el estado cambió.

## Limitaciones
La versión se registra al llamar /auditoria (idempotente).

## Relación con otras capas
Base del comparador (C14) y el predictivo (C15).
