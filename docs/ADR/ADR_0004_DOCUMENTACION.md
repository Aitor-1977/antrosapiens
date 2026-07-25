# ADR-0004 — Toda la documentación vive dentro del repositorio

## Estado
ACEPTADA (2026-07-25).

## Contexto
El objetivo de continuidad operativa exige que **cualquier persona pueda
reconstruir el ecosistema clonando el repositorio**, incluso si desaparecen
wikis, chats o servicios externos. La documentación dispersa (en herramientas de
terceros) se pierde, se desincroniza del código y no es versionable ni auditable.

## Decisión
- **Toda** la documentación técnica vive en `docs/` dentro del repositorio,
  versionada con Git junto al código que describe.
- Estructura canónica: `docs/` (documentos maestros e inventarios), `docs/ADR/`
  (decisiones), `docs/CAPAS/` (una por capa), `docs/DIAGRAMAS/` (Mermaid).
- **Toda afirmación se verifica contra el código**; lo no verificable se marca
  explícitamente. Nada se inventa.
- La documentación **repetitiva y estructural** (capas, diagramas) se **genera**
  con scripts versionados (`scripts/docs/gen_capas.py`, `gen_diagramas.py`) desde
  datos verificados, para que sea reproducible y no derive del código.
- Las inconsistencias detectadas se registran en `docs/INCONSISTENCIAS.md`.
- Los enlaces entre documentos son **relativos** (funcionan tras clonar).

## Consecuencias
- **(+)** Fuente única y reconstruible; documentación versionada y auditable.
- **(+)** La documentación evoluciona con el código en el mismo commit/PR.
- **(+)** Regeneración reproducible de capas/diagramas.
- **(−)** Disciplina de mantenimiento: cambiar código exige actualizar `docs/`.
- **(−)** Riesgo de deriva si no se ejecutan los generadores; mitigado por
  `INCONSISTENCIAS.md` y el control de calidad (Fase 10 del proceso documental).

## Referencias
`../README_TECNICO.md` (cómo regenerar) · `../INCONSISTENCIAS.md` ·
`../GUIA_RECONSTRUCCION_TOTAL.md`.
