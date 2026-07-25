# Capa 12 — Gobernanza Científica

> Documento generado por `scripts/docs/gen_capas.py` desde datos verificados
> contra el código. No editar a mano: regenerar con
> `python -m scripts.docs.gen_capas`. Índice: [`../DOCUMENTACION_MAESTRA.md`](../DOCUMENTACION_MAESTRA.md) §4.

- **Objetivo:** Hacer toda conclusión auditable, reproducible y explicable.
- **Problema que resuelve:** Sin versionado/huella/certificado, una conclusión no es reconstruible.
- **Arquitectura:** 14 funciones puras + persistencia idempotente; fecha fuera del hash.

## Componentes (archivos)
hd_scraper/gobernanza.py, hd_scraper/gobernanza_store.py

## Endpoints
GET /auditoria/{org}, GET /certificado/{org}

## Tablas
versionado_modelo, huellas_digitales, bitacora_decisiones, auditoria_expedientes, certificados

## Funciones
registrar_version_{modelo,taxonomia,corpus,pipeline,expediente}, generar_huella_digital, validar_integridad, verificar_consistencia, comparar_versiones, construir_linea_tiempo, registrar_decision, generar_bitacora, firmar_motor, emitir_certificado, auditar_expediente

## Entradas → Salidas
- **Entradas:** Expediente + validación
- **Salidas:** Huella, certificado con firma del Motor, bitácora, auditoría

## Dependencias
← C11 · → C13

## Tests
test_gobernanza (34), 100% cobertura

## Criterios de aceptación
Mismo insumo ⇒ misma huella/firma (fecha es metadato).

## Limitaciones
Firma = sha256 determinista (no criptografía de clave pública).

## Relación con otras capas
Sella cada expediente; base de la Memoria (C13). Ver ADR/ADR_0003_GOBERNANZA.md.
