# ADR-0002 — La inferencia científica vive únicamente en Motor A

## Estado
ACEPTADA (2026-07-25). Complementa a [ADR-0001](./ADR_0001_ARQUITECTURA_1_0.md).

## Contexto
La auditoría (`../ARQUITECTURA_ECOSISTEMA.md`) encontró dos motores de inferencia
divergentes: Motor A infiere de forma **determinista** (`hd_scraper/analisis.py`,
`validacion_cientifica.py`), mientras RadarHD infería con **LLM**
(`services/scoring-llm.ts`). Dos fuentes de verdad para la misma evidencia
producen resultados distintos y no auditables.

Las capas científicas de Motor A (3, 10, 11, 12, 13–18) son puras y reproducibles:
- **Capa 3** clasifica por reglas declaradas (scoring A/B/C, Dolor Cultural, ICP).
- **Capa 11** valida (solidez, suficiencia, contradicciones, vacíos, GRADE) y
  **bloquea** hipótesis sin evidencia suficiente.
- **Capa 12** sella con huella/certificado reproducibles (fecha fuera del hash).

## Decisión
**Toda inferencia científica del ecosistema reside exclusivamente en Motor A.**
Ningún otro motor infiere, clasifica, interpreta ni genera hipótesis. La IA
generativa queda excluida de la producción de inteligencia científica en todos
los motores (Motor A es determinista; RadarHD deja de usar LLM para clasificar).

Endpoints que exponen la inferencia (fuente única): `/expedientes`, `/dolormap/{org}`,
`/validacion/{org}`, `/auditoria/{org}`, `/certificado/{org}`, `/dossier/{org}`,
`/alertas`, `/centro`, `/proyeccion/{org}`, `/latam`, `/publicar/*`.

## Consecuencias
- **(+)** Una sola verdad; reproducibilidad y trazabilidad de extremo a extremo.
- **(+)** Menor coste/latencia (sin LLM de pago para inteligencia).
- **(+)** Evolución controlada de la taxonomía en un solo lugar (versionado C12).
- **(−)** Motor A debe exponer en JSON vistas que hoy sirve como HTML (dossier) o
  que RadarHD calculaba (clusters/oportunidades) — brechas listadas en
  `../ROADMAP_ARQUITECTONICO.md`.
- **(−)** RadarHD pierde flexibilidad de "interpretar a su manera"; a cambio gana
  coherencia científica y defendibilidad.

## Referencias
[ADR-0001](./ADR_0001_ARQUITECTURA_1_0.md) · [ADR-0003](./ADR_0003_GOBERNANZA.md) ·
`../DOCUMENTACION_MAESTRA.md` §12–13 · `../CAPAS/CAPA_11.md`.
