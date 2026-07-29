# 0005 · Máquinas de Estado

> Evidencia de guardas: `docs/AUDITORIA/04_CIERRE_MODELO_DOMINIO.md` §4–5
> (`scoring.ts`, `prospectos/[id]`, `senales/[id]`, `radar.ts`).

## Máquina A — Señal (BC-I, intake)
`nueva → confirmada | descartada`
- `confirmar` (`senales/[id]`) es el **único cruce** BC-I→BC-II: instancia un Prospecto.
- Bloqueado si hay un Peritaje Activo (Protocolo de Congelamiento, G1).

## Máquina B — Prospecto / Expediente operativo (BC-II)
Estados (`EstadoPipeline`): `Detectado · Búnker · Enviado · Respuesta · Silencio · Call Activa ·
SOW Emitido · Peritaje Activo · Reactivación · Kill Switch`.

```
[Detectado] ──(REGLA CERO: requiere peritaje/DolorMap validado de BC-I)──▶ Siembra
   (monitoreo pasivo C: solo Detectado/Kill Switch)          requiere verificación de contacto
[Búnker]→[Enviado] ──cadencia──▶ [Respuesta] ──cualificación liminal──▶ defensa→[Kill Switch]
                                                              curiosidad→[Silencio]→cadencia
                                                              receptividad→[Call Activa]
[Call Activa] → [SOW Emitido] → [Peritaje Activo] (CONGELA el pipeline, foco único)
                                        ▼
                          [Reactivación]   |   [Kill Switch] (razón obligatoria; log; reversible)
```

## Guardas / reglas de negocio (canónicas)
| # | Regla | Protege | Capa |
|---|-------|---------|------|
| **G0 · REGLA CERO** | avanzar/contactar exige peritaje+DolorMap validados de BC-I | el rigor científico como candado comercial | Dominio |
| G1 · Congelamiento | un solo Peritaje Activo | foco pericial | Dominio |
| G2 · Monitoreo pasivo | señales C solo Detectado/Kill Switch | ruido fuera de la venta | Dominio |
| G3 · Verificación previa a Siembra | contacto verificado antes de cadencia | deliverability/seriedad | Dominio |
| G4 · Cualificación Liminal | interpretar la respuesta (curiosidad ≠ dolor) | priorización correcta | Dominio |
| G5 · Kill Switch trazable | razón obligatoria + log + reversible | auditoría del freno | Aplicación+Dominio |
| G6 · No disparar (SMTP) | flag si SMTP < mínimo | reputación de envío | Dominio |
| G7 · Exclusión permanente | orgs excluidas fuera de captura | defensa del corpus | Dominio |
| G8 · Bloque 1 obligatorio | campos mínimos al alta | completitud del expediente | Aplicación |

## Ciclo de vida unificado (objetivo canónico)
`Observado → Peritado → Con-DolorMap → En-Bitácora → Decidido → Sprint-Activo → Cerrado(Caso) → Aprendido`.
La cadencia comercial (Máquina B) **solo corre** sobre un Expediente ya **Peritado + Con-DolorMap**
(G0). El estado `Aprendido` **reporta el resultado a Motor A** (loop cerrado, hoy inexistente).
