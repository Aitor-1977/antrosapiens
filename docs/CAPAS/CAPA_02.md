# Capa 02 — Evidencia (contrato)

> Documento generado por `scripts/docs/gen_capas.py` desde datos verificados
> contra el código. No editar a mano: regenerar con
> `python -m scripts.docs.gen_capas`. Índice: [`../DOCUMENTACION_MAESTRA.md`](../DOCUMENTACION_MAESTRA.md) §4.

- **Objetivo:** Guardián único del contrato de la tabla evidencias.
- **Problema que resuelve:** Solo debe persistirse evidencia completa y trazable; lo incompleto no puede contaminar el corpus.
- **Arquitectura:** Validador único; registro incompleto → rechazos; sin fecha → estado no_fechado.

## Componentes (archivos)
hd_scraper/validation/validator.py, hd_scraper/db/models.py

## Endpoints
GET /evidencias, GET /evidencias/{id}, GET /corpus

## Tablas
evidencias, rechazos

## Funciones
validate (contrato), campos_contrato, _row_a_corpus

## Entradas → Salidas
- **Entradas:** EvidenceRecord
- **Salidas:** Fila en evidencias (estado ok|no_fechado) o rechazo

## Dependencias
← C1 · → C3, corpus para Motor B

## Tests
test_validator, test_corpus, test_scrape, test_intake

## Criterios de aceptación
Obligatorios: cita_textual, fecha_extraccion, url_fuente, nombre_medio, empresa_mencionada, tipo_evento, origen_declaracion, hash_dedup.

## Limitaciones
no_fechado no es consumible por la API (pero no se rechaza).

## Relación con otras capas
Fuente del corpus (contrato motor_a.corpus.v1) que consume RadarHD.
