# Capa 11 — Validación Científica

> Documento generado por `scripts/docs/gen_capas.py` desde datos verificados
> contra el código. No editar a mano: regenerar con
> `python -m scripts.docs.gen_capas`. Índice: [`../DOCUMENTACION_MAESTRA.md`](../DOCUMENTACION_MAESTRA.md) §4.

- **Objetivo:** Auditar la calidad epistémica de cada hipótesis y emitir el Dictamen Científico.
- **Problema que resuelve:** Una hipótesis sin evidencia suficiente no debe sostenerse ni escalar.
- **Arquitectura:** 14 funciones puras; umbrales declarados; bloqueo automático.

## Componentes (archivos)
hd_scraper/validacion_cientifica.py

## Endpoints
GET /validacion/{org}

## Tablas
(opera sobre el expediente en memoria)

## Funciones
14: contar_fuentes_independientes, calcular_confianza_agregada, validar_trazabilidad, validar_fechado, calcular_suficiencia_corpus, calcular_solidez, detectar_contradicciones, detectar_vacios, validar_reproducibilidad, nivel_evidencia, evaluar_bloqueo_hipotesis, clasificar_veredicto, emitir_dictamen_cientifico, validar_expediente

## Entradas → Salidas
- **Entradas:** Expediente (hipótesis + evidencia)
- **Salidas:** Veredicto (VALIDADA|VALIDADA_PARCIAL|NO_VALIDADA|BLOQUEADA|SIN_HIPOTESIS), solidez, suficiencia, nivel GRADE

## Dependencias
← C10 · → C12

## Tests
test_validacion_cientifica (46), 100% cobertura

## Criterios de aceptación
MIN_EVIDENCIAS=3, MIN_FUENTES_INDEPENDIENTES=2; bloqueo si bajo umbral.

## Limitaciones
No re-extrae evidencia; audita la ya producida.

## Relación con otras capas
Integrada en _construir_expedientes (bloqueo automático); insumo de C12.
