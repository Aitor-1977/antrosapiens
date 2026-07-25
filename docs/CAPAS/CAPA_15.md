# Capa 15 — Motor Predictivo Antropológico

> Documento generado por `scripts/docs/gen_capas.py` desde datos verificados
> contra el código. No editar a mano: regenerar con
> `python -m scripts.docs.gen_capas`. Índice: [`../DOCUMENTACION_MAESTRA.md`](../DOCUMENTACION_MAESTRA.md) §4.

- **Objetivo:** Detectar trayectorias culturales con reglas deterministas.
- **Problema que resuelve:** Anticipar sin IA ni modelos opacos, solo con evidencia histórica.
- **Arquitectura:** Serie temporal mensual + mínimos cuadrados + banda de volatilidad.

## Componentes (archivos)
hd_scraper/predictivo.py

## Endpoints
GET /proyeccion/{org}, GET /escenarios/{org}

## Tablas
(deriva serie de evidencias fechadas)

## Funciones
serie_temporal, calcular_tendencia/estabilidad/volatilidad/madurez, proyectar_escenarios, estimar_riesgo, detectar_inflexiones, emitir_proyeccion

## Entradas → Salidas
- **Entradas:** Expediente (evidencia histórica)
- **Salidas:** Tendencia, estabilidad, volatilidad, escenarios, riesgo, madurez, inflexiones

## Dependencias
← C13 · → C18

## Tests
test_predictivo (23), 100% cobertura

## Criterios de aceptación
Proyección aritmética declarada; sin aleatoriedad ni IA.

## Limitaciones
No es predicción probabilística; requiere serie con historia.

## Relación con otras capas
Complementa el Observatorio y el Sistema Operativo.
