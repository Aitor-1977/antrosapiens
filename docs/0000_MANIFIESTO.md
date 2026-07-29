# 0000 · Manifiesto — Plataforma de Inteligencia Territorial
### Hamaca Digital · Laboratorio de Antropología de la Innovación
### Línea base canónica · SELLADA

> Este documento y sus hermanos `0001`–`0007` constituyen la **Especificación
> Arquitectónica Canónica** de la plataforma (Antrosapiens = Motor A; RadarHD =
> Motor B/C). Toda funcionalidad, refactor o módulo nuevo **debe validarse contra
> este canon antes de implementarse**. La evidencia y el detalle viven en
> `docs/AUDITORIA/` (Inventario, Modelo mental CTO, Especificación canónica,
> Cierre de dominio).

## Qué es la plataforma
Una **plataforma de inteligencia territorial** que observa organizaciones como
**sistemas culturales**, produce **peritaje antropológico determinista** (Motor A)
y lo convierte en **decisiones humanas trazables** de intervención (RadarHD).

## El principio fundacional (inviolable)
> **Toda inferencia antropológica ocurre exclusivamente en Motor A. RadarHD
> consume, compone lo comercial, opera y registra — nunca infiere.**

## Los dos dominios (separación estricta — ver `0003`)
- **BC-I · Contexto Científico** — raíz: **Organización Observada**.
  Ciclo: `Señal → Evidencia → Corpus → Motor A → Peritaje → DolorMap®`.
  **Prohibido** ejecutar lógica comercial, CRM o ventas aquí.
- **BC-II · Contexto Operativo** — raíz: **Prospecto**.
  Ciclo: `DolorMap® válido → Bitácora → Contacto → Sprint → Caso → Aprendizaje`.
  **Prohibido** interpretar evidencia, ejecutar IA o generar Deuda Cultural aquí.

## INVARIANTE REGLA CERO (el candado científico)
> **Ninguna entidad del BC-II (Prospecto) puede avanzar de estado ni iniciar
> contacto sin un dictamen antropológico validado (Peritaje / DolorMap®) originado
> en el BC-I (Observación Antropológica). La ciencia es el candado de la operación
> comercial.**

Consecuencia: el estado inicial operativo (`Detectado`) es admisible, pero **toda
transición hacia Siembra/Contacto exige `dictamen_validado = true` proveniente de
Motor A**. Sin peritaje, no hay operación.

## Congelamiento formal
A partir del commit que sella esta línea base, la arquitectura queda **congelada**
bajo esta Especificación. Todo desarrollo posterior debe **rechazar** código, ruta
o módulo que (a) viole la separación de contextos, (b) infiera fuera de Motor A, o
(c) introduzca léxico no autorizado (`leads`, `churn`, `funnel`, "UX genérico" y
similares). El léxico canónico es el del Laboratorio (ver `0004`).

## Índice del canon
`0001` Arquitectura · `0002` Modelo de dominio · `0003` Bounded contexts ·
`0004` Principios inmutables + léxico · `0005` Máquinas de estado ·
`0006` Contratos · `0007` Roadmap.
