# 0002 · Modelo de Dominio

> Evidencia completa (esquema, SoT, FKs): `docs/AUDITORIA/04_CIERRE_MODELO_DOMINIO.md`.

## Entidades raíz (dos, en dos contextos distintos)

### Organización Observada — BC-I (Científico)
- **Qué es:** una organización vista como sistema cultural a peritar.
- **SoT:** **Motor A** (Expediente Vivo; id determinista). Local `organizacion`/`observacion`
  es representación secundaria (hoy casi huérfana).
- **Ciclo de vida:** *no tiene máquina de estados*; es una vista viva. Lo único con estado
  es la **Señal** (`nueva → confirmada | descartada`).
- **Invariante:** determinista, trazable, "hipótesis a validar"; nunca editable desde RadarHD.

### Prospecto — BC-II (Operativo)
- **Qué es:** candidato comercial que avanza hacia la venta de un Sprint Fundacional.
- **SoT:** **RadarHD** (`prospecto`, Neon; id SERIAL).
- **Ciclo de vida:** máquina de 10 estados (ver `0005`).
- **Invariante:** foco único (un Peritaje Activo), freno reversible y auditado, **Regla Cero**.

## Relación entre entidades (el agregado "Expediente")
El esquema modela `Organización 0..1 — 0..1 Prospecto` vía la Señal
(`senal_radar.{organizacion_id,prospecto_id}`, `observacion.prospecto_id`). **Hoy la unión
efectiva es NOMINAL (por nombre de empresa), no referencial** — esa es la *costura débil*.
El concepto unificador **"Expediente"** (identidad única que liga lo observado y lo operado)
**debe existir por ID cruzado**, no por nombre (ver `0007`, Prioridad 1).

## Source of Truth por entidad (resumen)
| Entidad | SoT | Contexto |
|---------|-----|----------|
| Evidencia / Señal | Motor A (`evidencias`) + captura local `senal_radar` | BC-I / BC-III |
| Organización Observada / Expediente Vivo | **Motor A** | BC-I |
| Deuda Cultural™, Dictamen, DolorMap®, Onlife | **Motor A** | BC-I |
| Prospecto, Cadencia, Bitácora, Kill Switch, Caso | **RadarHD** | BC-II |
| Recomendación / Sprint (producto) | RadarHD (Motor C) sobre datos de A | BC-II |

## Lenguaje ubicuo (definiciones unívocas)
- **Organización Observada:** entidad científica peritada (BC-I). *No es* un lead.
- **Prospecto:** entidad operativa candidata a intervención (BC-II). *No es* la organización peritada.
- **Peritaje:** dictamen antropológico determinista de Motor A (BC-I).
- **DolorMap®:** síntesis del dolor cultural; artefacto-gate entre ciencia y operación.
- **Bitácora:** registro del avance metodológico/comercial (BC-II). *No es* un CRM.
- **Sprint Fundacional:** intervención decidida por el humano; congela el foco.
- **Caso:** expediente operativo cerrado con aprendizaje (BC-II).
