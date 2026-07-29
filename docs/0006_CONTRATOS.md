# 0006 · Contratos entre Módulos y Contextos

> Evidencia: `docs/AUDITORIA/03_ESPECIFICACION_CANONICA.md` §III.8 y
> `04_CIERRE_MODELO_DOMINIO.md` §7.

## Contratos vigentes (verificados)
| Productor | Contrato | Input | Output | Regla |
|-----------|----------|-------|--------|-------|
| Motor A | `motor_a.corpus.v1` (`GET /corpus`) | filtros | evidencia **objetiva** (sin Deuda) | tag versionado; rompe si desconocido |
| Motor A | `motor_a.dossier.v1` (`GET /dossier/{org}`) | org | peritaje completo (27 claves) | A produce, RadarHD representa |
| Motor A | Expediente Vivo (`/organizaciones[/{id}]`, `/drift`, `/onlife`, `/ecosistema/*`) | id | `OrganizacionObservada`/`Dossier`/`Drift`/panel | paridad de forma |
| Gateway (`motor-a.gateway.ts`) | cliente HTTP único | — | — | **única** puerta a A |
| `expedientes.service` (adaptador temporal) | `Dossier(A) → ExpedienteVivo` | id | ExpedienteVivo | puente Fase 3; a retirar |
| Motor C (RadarHD) | recomendación, dictamen pericial, cadencia, seguimiento | datos de A + prospecto | acción comercial | nunca infiere |

## Contratos FALTANTES (canónicos — a crear; ver `0007`)
| # | De → A | Contrato | Propósito |
|---|--------|----------|-----------|
| C-1 | RadarHD (captura) → Motor A | `clasificar señal → Deuda/ICP` (determinista) | eliminar el LLM local (cierra BC-III duplicado) |
| C-2 | RadarHD (cierre) → Motor A | `outcome del Sprint → A` (memoria) | cerrar el loop de aprendizaje BC-II→BC-I |
| C-3 | BC-I → BC-II | **enlace referencial por ID** Organización Observada ↔ Prospecto | reemplaza la unión nominal (Prioridad 1) |
| C-4 | Gate Regla Cero | `peritaje_validado(org) → boolean` expuesto por A/gateway | habilita/bloquea el avance del Prospecto |

## Propiedades inviolables del contrato
1. Dirección única A→RadarHD; sin BD compartida; sin escrituras a A (salvo C-2 vía API dedicada).
2. Versionado aditivo o `v2`; nunca cambios incompatibles silenciosos.
3. `/corpus` nunca incluye Deuda/ICP/hipótesis (frontera semántica).
