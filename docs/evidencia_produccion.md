# Evidencia de validación en producción — Motor A

> ⏳ **PENDIENTE DE GENERAR CON DATOS REALES.**
>
> Este archivo es un marcador. **No contiene evidencia**: se sobrescribe
> automáticamente al ejecutar el validador desde un entorno con acceso a Internet
> y al despliegue de producción.
>
> El entorno del asistente (sandbox) tiene la salida de red bloqueada por el
> proxy (todo `CONNECT` externo → `403`, incluidos `hd-prospector.vercel.app` y
> `news.google.com`), por lo que la evidencia real **no puede** generarse desde
> ahí. No se simula ni se estima.

## Cómo generar la evidencia real

```bash
export MOTOR_A_URL="https://hd-prospector.vercel.app"
export HD_INGEST_TOKEN="<token-de-ingesta-del-despliegue>"
python -m scripts.validar_produccion
```

Al terminar, este archivo y `evidencia_produccion.json` quedarán reemplazados por
la evidencia real y auditable de la corrida (métricas, verificación de contrato,
deduplicación, distribución de calidad y de motivos de rechazo, y la muestra de
≥50 registros con su explicación objetiva).

Ver `docs/validacion_produccion.md` para el procedimiento completo y reproducible.
