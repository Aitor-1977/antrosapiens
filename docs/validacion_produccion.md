# Validación final en producción (datos reales, auditable y reproducible)

Proceso **automatizado, determinista y auditable** para validar el Motor A
desplegado en Vercel (que consulta Google News real). No usa simulaciones,
mocks, fixtures ni datos generados artificialmente. Toda la evidencia proviene
del sistema en producción.

Entregable ejecutable: `scripts/validar_produccion.py` (+ envoltorio
`scripts/validar_produccion.sh`). Deja la evidencia en
`docs/evidencia_produccion.json` y `docs/evidencia_produccion.md`, suficiente para
**auditar la corrida sin leer el código fuente**.

> ⚠️ **Dónde se ejecuta.** El sandbox del asistente NO tiene salida de red: el
> proxy responde `403` a todo `CONNECT` externo (`hd-prospector.vercel.app` y
> `news.google.com` incluidos, verificado en vivo). Por eso el asistente **no
> puede** generar la evidencia y **no la declara completada**. La evidencia la
> generas tú corriendo el script desde un entorno con Internet. Si el script no
> alcanza producción, **aborta con error** y no escribe nada (no simula).

## Requisitos

1. Deploy de `main` en Vercel en estado **Ready** (incluye Captura Inteligente y
   la observabilidad de validación: `filtrados` en `/scrape`, `rechazos_por_motivo`
   y `calidad_captura` en `/stats`).
2. Python 3.9+ y el repositorio clonado (el script importa `hd_scraper.relevance`,
   `signals` y `db.models` para explicar/verificar con el mismo código objetivo
   que usó producción; no toca el servidor).
3. El **X-Ingest-Token** del despliegue (para `POST /scrape`).

## Ejecución (comando mínimo)

```bash
export MOTOR_A_URL="https://hd-prospector.vercel.app"
export HD_INGEST_TOKEN="<token-de-ingesta>"

# Captura real + auditoría completa (determinista con --seed):
python -m scripts.validar_produccion --seed 0
#   o:  ./scripts/validar_produccion.sh --seed 0

# Auditar el corpus existente sin capturar:
python -m scripts.validar_produccion --solo-leer
```

Código de salida: **0** si todas las verificaciones pasan; **1** si el contrato o
la deduplicación fallan. Ideal para CI/auditoría.

## Qué produce (todo real, todo en la evidencia)

**Métricas obligatorias**
- Total de artículos capturados (esta corrida) y vistos.
- Total de artículos descartados / rechazos (corpus, desde `/stats`).
- Total de duplicados detectados (colapsados al escribir, desde `/scrape`).
- Total de empresas identificadas (distintas + detectables objetivamente).
- Porcentaje de artículos útiles = `consumibles / (consumibles + no_fechadas + rechazos)`.
- Distribución de `calidad_captura` (Alta / Media / Baja).
- Distribución de motivos de rechazo (`/stats.rechazos_por_motivo`).

**Validación del contrato** (`motor_a.corpus.v1`), por cada item de `/corpus`:
- tag de contrato correcto;
- exactamente las 10 claves del contrato (esquema);
- campos obligatorios no vacíos (empresa, fuente, texto, url, tipo_evento, hash);
- `tipo_evento` dentro del vocabulario del contrato;
- `confianza` numérica en `[0, 1]`; `keywords` es lista; `fecha` ISO 8601;
- ausencia de duplicados: `url` y `hash` únicos en todo el corpus.

**Muestreo automático** (≥50 registros reales, reproducible con `--seed`), por
registro: empresa, evento detectado, calidad asignada, **explicación objetiva**
(recálculo de los 3 criterios con el código de producción), fuente y URL.

## Reproducibilidad

- El muestreo usa `random.Random(seed)`: con la misma `--seed` y el mismo estado
  del corpus, la muestra es idéntica → **determinista**.
- Cualquier persona con las 2 variables de entorno y el repo obtiene resultados
  equivalentes ejecutando el mismo comando.

## Observabilidad añadida (solo exposición de datos ya calculados)

Para que las métricas salgan de la propia app (no de inferencias del cliente):

- `POST /scrape` → cada resultado incluye `filtrados` (descartes por relevancia).
- `GET /stats` → `rechazos_por_motivo` (dedup/contrato/`relevancia:*`) y
  `calidad_captura` (distribución Alta/Media/Baja).

Son campos **aditivos y retrocompatibles**; no cambian el contrato
`motor_a.corpus.v1` ni el comportamiento existente.

## Smoke manual (opcional)

```bash
curl -s "$MOTOR_A_URL/health"
curl -s -X POST "$MOTOR_A_URL/scrape" \
  -H "Content-Type: application/json" -H "X-Ingest-Token: $HD_INGEST_TOKEN" \
  -d '{"empresa":"Nubank","tipo_evento":"ronda","connectors":["google_news"],"region":"LATAM"}'
curl -s "$MOTOR_A_URL/corpus?limite=5"
curl -s "$MOTOR_A_URL/stats"
```
