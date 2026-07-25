# Capa 17 — Publicador Científico

> Documento generado por `scripts/docs/gen_capas.py` desde datos verificados
> contra el código. No editar a mano: regenerar con
> `python -m scripts.docs.gen_capas`. Índice: [`../DOCUMENTACION_MAESTRA.md`](../DOCUMENTACION_MAESTRA.md) §4.

- **Objetivo:** Generar documentación científica desde evidencia validada.
- **Problema que resuelve:** Hay que producir peritajes/informes firmados y reproducibles.
- **Arquitectura:** Builders puros JSON/CSV/HTML/PDF + firma determinista.

## Componentes (archivos)
hd_scraper/publicador.py

## Endpoints
GET /publicar/peritaje/{org} (json|csv|html), GET /publicar/informe/{org}, GET /publicar/pdf/{org}

## Tablas
(usa expediente + validación + gobernanza)

## Funciones
generar_peritaje/informe/pdf/html/json/csv, firmar_documento

## Entradas → Salidas
- **Entradas:** Expediente + validación + huella + certificado
- **Salidas:** Documento firmado; publicable=False si el veredicto no valida

## Dependencias
← C11, C12 · reutiliza C3 (dictamen)

## Tests
test_publicador (13), 100% cobertura

## Criterios de aceptación
Nunca inventa; la firma cubre el contenido científico (no la fecha).

## Limitaciones
El 'PDF' es HTML imprimible (convención del repo).

## Relación con otras capas
Consume la ciencia de C11/C12 para exportarla.
