# 0007 · Roadmap Arquitectónico (post-sellado)

> Clasificado por tipo de deuda y priorizado por impacto × riesgo. Detalle:
> `docs/AUDITORIA/03_ESPECIFICACION_CANONICA.md` §III.9.

## PRIORIDAD TÉCNICA 1 (primera tarea de desarrollo) — Reparar la costura débil BC-I↔BC-II
**Problema:** la unión entre *Organización Observada* (BC-I) y *Prospecto* (BC-II) es hoy
**nominal (por nombre de empresa)**. **Objetivo:** convertirla en **estrictamente referencial
(por ID cruzado)**.
- Introducir identidad de agregado **"Expediente"** que ligue ambas entidades por ID.
- El Prospecto debe portar una referencia estable a la Organización Observada peritada.
- Habilita la **Regla Cero** (G0): sin enlace referencial a un peritaje validado, el Prospecto
  no avanza. Contratos C-3 y C-4 (ver `0006`).
- **Riesgo:** alto (identidad cruzada entre id-space de Motor A y `prospecto.id` local).
  Ejecutar por strangler-fig, contrato antes que código, sin cambiar la UI.

## Deuda arquitectónica
- **A1** · Colapsar la inferencia de Deuda a Motor A (contrato C-1; retirar `scoring-llm`). *(impacto máx, riesgo alto)*
- **A2** · Unificar el Dictamen en el determinista de A (retirar `dictamen.service` LLM V3). *(alto, medio)*
- **A3** · Unificar los dos linajes bajo el agregado "Expediente" (Prioridad 1). *(alto, alto)*

## Deuda metodológica
- **M0 · REGLA CERO** · gate de peritaje+DolorMap antes de operar (G0). *(máx, medio)* — **primero tras Prioridad 1.**
- **M1** · DolorMap® como artefacto-gate obligatorio. *(alto, medio)*
- **M2** · Loop de aprendizaje: outcome del Sprint → Motor A (C-2). *(medio, medio)*

## Deuda de UX (sin rediseño estético; solo guardas de estado)
- **U1** · Navegación que codifique el método (gates de estado, no wizard). *(medio, bajo)*
- **U2** · Revelación ordenada evidencia→hipótesis→recomendación (global). *(bajo)*
- **U3** · Retirar `Sidebar.tsx` duplicado/legacy. *(bajo, bajo)*

## Deuda técnica
- **T1** · Sacar inferencia de React (`inference/contradiction/ritual`). *(bajo, medio)*
- **T2** · Extraer tipos de `concentrador.ts` (runtime-neutral). *(bajo, bajo)*
- **T3** · Separar `ecosistema.service` (contexto ⟂ fingerprint). *(bajo, bajo)*
- **T4** · Versionar el cron (`vercel.json`); decidir destino del `sqlite.adapter` móvil. *(bajo)*
- **T5** · Deprecar `pipeline_comercial.py` en Motor A. *(bajo)*

## Orden recomendado
**Prioridad 1 (costura referencial)** → **M0 (Regla Cero)** → A1 → A2 → M1 → M2 → A3 → U1 → T1 → T2/T3 → U3/T4/T5.

## Enforcement del congelamiento (a implementar, requiere autorización de código)
- Hook/CI que **rechace** merges que: (a) importen motores de inferencia desde BC-II o React,
  (b) crucen contextos, (c) introduzcan léxico prohibido (`0004`). Se documenta aquí como política;
  su implementación como hook es una tarea de código separada, sujeta a autorización explícita.
