# ADR-0003 — Gobernanza científica: versionado, hashes, auditoría, reproducibilidad

## Estado
ACEPTADA (2026-07-25). Implementada en la **Capa 12** (`hd_scraper/gobernanza.py`,
`gobernanza_store.py`). Complementa a [ADR-0002](./ADR_0002_CAPAS_CIENTIFICAS.md).

## Contexto
Una conclusión científica solo es defendible si puede **reconstruirse**. Sin
versionado del modelo/taxonomía, sin huella de contenido y sin certificado, no
hay forma de demostrar que un dictamen proviene de una evidencia concreta y de
una versión concreta del algoritmo. El laboratorio necesita rigor auditable.

## Decisión
Cada expediente se **sella** con gobernanza determinista:
- **Versionado** (`versionado_modelo`): versión de motor, taxonomía, corpus,
  pipeline y expediente, con hash de contenido.
- **Huella digital** (`huellas_digitales`): `id` + `hash` de contenido +
  versiones. La **fecha de emisión es metadato y NO entra en el hash** ⇒ mismo
  insumo produce la misma huella.
- **Integridad** (`validar_integridad`) y **consistencia** (`verificar_consistencia`).
- **Bitácora** (`bitacora_decisiones`): qué evidencia llegó/aceptó/descartó, qué
  reglas se ejecutaron y cuáles bloquearon la hipótesis.
- **Certificado** (`certificados`) con **firma del Motor** (`firmar_motor`,
  `AS-MOTORA::<sha256[:32]>`), determinista.
- **Auditoría** (`auditoria_expedientes`) reproducible (`auditar_expediente`).
Persistencia **idempotente** (select-then-insert por hash/id), portable
SQLite/PostgreSQL.

## Consecuencias
- **(+)** Reproducibilidad verificable: `GET /certificado/{org}` dos veces ⇒
  mismo `hash` y `firma_motor` (verificado en tests).
- **(+)** Auditoría total: cada conclusión se rastrea a un `hash`.
- **(+)** Memoria inmutable (Capa 13) construida sobre estas huellas.
- **(−)** La "firma" es integridad determinista (sha256), **no** criptografía de
  clave pública; no prueba autoría frente a terceros, solo integridad de contenido.
- **(−)** Coste de almacenamiento por versión (mitigado con dedup por hash).

## Referencias
`../CAPAS/CAPA_12.md` · `../CAPAS/CAPA_13.md` · `../DIAGRAMAS/06_gobernanza.md` ·
`../INVENTARIO_TABLAS.md` §A.
