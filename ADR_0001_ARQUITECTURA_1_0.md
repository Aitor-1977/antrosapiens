# ADR-0001 — Arquitectura 1.0 del Laboratorio Hamaca Digital

- **Estado:** ACEPTADA (decisión oficial del Arquitecto Principal, 2026-07-25).
- **Prioridad:** ARQUITECTÓNICA. Tiene precedencia sobre cualquier implementación
  anterior. Toda decisión de código futura debe cumplir este ADR.
- **Alcance:** los tres motores del ecosistema (A `antrosapiens`, B+C `radarHD`).

## Decisión (una frase)

> **Motor A piensa. Motor B muestra. Motor C vende. Sin excepción.**

Existe **un único Motor de Inferencia**: Motor A. Toda inteligencia científica
(hipótesis, clasificación, interpretación, validación, gobernanza) **nace y vive
exclusivamente en Motor A**. RadarHD (Motor B) solo **representa**; Prospector
(Motor C, dentro de RadarHD) solo **vende**, consumiendo inteligencia ya
producida por Motor A. Ninguno de los dos interpreta, clasifica, infiere ni
ejecuta IA para producir inteligencia científica.

## Contexto (por qué se toma ahora)

La auditoría del ecosistema (2026-07-25, ver `ARQUITECTURA_ECOSISTEMA.md`)
encontró que **RadarHD hoy duplica la función de inferencia** de Motor A:
- Tiene 13 *engines* propios (`inference`, `scoring`, `dictamenPericial`,
  `contradiction`, `ecosistema`, `onlife`, `priorizacion`, `recomendacion`, …).
- Usa **LLMs** (Gemini/NVIDIA/Anthropic/ZenMux) para clasificar y peritar
  (`services/llm.ts`, `scoring-llm.ts`).
- Calcula **localmente** Dolor Cultural, Drift, Onlife, Ecosistema, dictámenes y
  contradicciones — en paralelo (y desacoplado) de las Capas 3–18 de Motor A.

Consecuencia: **dos fuentes de verdad divergentes**, inferencia no determinista
en el lado de RadarHD, y clasificaciones duplicadas. Esto contradice la razón de
ser del laboratorio (rigor científico auditable y reproducible).

## Decisión detallada

### Motor A — `antrosapiens` · ÚNICA FUENTE DE VERDAD
Responsabilidad exclusiva: Captura · Normalización · Evidencia · Curaduría ·
Inferencia Antropológica · Dictamen · Dolor Cultural · Drift · Onlife ·
Validación Científica · Gobernanza · Ecosistema · Certificados · Auditoría ·
Versionado. **Determinista, sin IA generativa.** Toda hipótesis, clasificación,
interpretación, validación y gobernanza **nace aquí**.

### Motor B — `radarHD` (render) · SOLO REPRESENTA
Responsabilidad exclusiva: Centro de Inteligencia (visual), visualización,
render, UX, dashboard, expedientes, dossier, DolorMap, alertas, búsqueda,
filtros, cache, estados, adaptadores HTTP, **cliente del Motor A**.
**Nunca** interpreta, clasifica, infiere, genera hipótesis, ejecuta IA ni
modifica evidencia. **Solo consume y representa.**

### Motor C — Prospector HD (dentro de `radarHD`) · SOLO VENDE
Responsabilidad exclusiva: prospección, seguimiento, cadencias, pipeline, email,
Telegram, Hunter, Apollo, KPIs, automatizaciones, CRM. **Nunca** interpreta
evidencia ni modifica inferencias. **Solo consume inteligencia del Motor A.**

## Fuente única de inteligencia (endpoints oficiales de Motor A)

Toda inteligencia proviene EXCLUSIVAMENTE de la API de Motor A:
`/corpus` · `/expedientes` · `/investigacion` · `/dossier/{org}` ·
`/dolormap/{org}` · `/drift/{org}` · `/onlife/{org}` · `/alertas` · `/centro` ·
`/validacion/{org}` · `/auditoria/{org}` · `/certificado/{org}` — y cualquier
endpoint científico existente (Capas 11–18: `/historial`, `/timeline`,
`/proyeccion`, `/latam`, `/vertical`, `/comparar`, `/publicar/*`).

## Por qué un único Motor de Inferencia

1. **Una sola verdad.** Dos motores de inferencia (uno determinista en A, otro
   con IA en RadarHD) producen resultados divergentes para la misma evidencia.
   Un único motor elimina la ambigüedad sobre "cuál dato es el correcto".
2. **Reproducibilidad.** Motor A es determinista y auditable (mismo insumo ⇒
   misma salida, con huella y certificado). Un LLM no lo es. La ciencia del
   laboratorio exige reproducibilidad; por eso la inferencia vive donde es
   determinista.
3. **Trazabilidad de extremo a extremo.** Con la inferencia centralizada, cada
   conclusión que muestra RadarHD y cada prospecto que trabaja Motor C puede
   rastrearse hasta un `hash`/`certificado` de Motor A.
4. **Frontera de IA nítida.** La IA generativa deja de producir inteligencia
   científica en ningún motor: A no la usa (determinista) y B/C dejan de usarla
   para clasificar. La IA queda, si acaso, para asistencia de UX/redacción, nunca
   para peritaje.

## Por qué RadarHD deja de interpretar

- **Elimina duplicación** (clasificaciones, dictámenes, drift, onlife, ecosistema
  existían en ambos lados).
- **Reduce superficie de error**: RadarHD ya no mantiene 13 engines + prompts LLM
  que hay que versionar y validar; consume un contrato estable.
- **Coste y latencia**: se eliminan llamadas a LLMs de pago para producir
  inteligencia que Motor A ya calcula gratis y de forma determinista.
- **Coherencia visual = coherencia científica**: lo que se ve es exactamente lo
  que Motor A certificó.

## Por qué Prospector consume inteligencia (no la produce)

El pipeline comercial necesita **priorizar y contactar** a partir de inteligencia
fiable. Si Motor C infiere por su cuenta, vende sobre hipótesis no validadas.
Consumiendo la inteligencia **validada y certificada** de Motor A, cada acción
comercial se apoya en evidencia auditable — protegiendo la reputación del
laboratorio y del cliente.

## Ventajas científicas para Hamaca Digital

- **Rigor**: toda conclusión es determinista, versionada y certificada.
- **Auditoría total**: un peritaje puede reconstruirse desde su `hash`.
- **Defendibilidad**: ante un cliente o un tribunal, la inteligencia tiene
  origen único y trazable, no "lo que dijo un LLM".
- **Evolución controlada**: la taxonomía y las reglas cambian en un solo lugar
  (Motor A), con versionado (`versionado_modelo`), no en dos motores divergentes.

## Consecuencias e implementación

- **Motor A**: sin cambios de responsabilidad; puede necesitar **exponer en JSON**
  algunas vistas que hoy solo sirve como HTML (p. ej. `/dossier`) o agregados que
  RadarHD calculaba (clusters/outliers/oportunidades) — ver
  `ROADMAP_ARQUITECTONICO.md` (brechas de contrato).
- **RadarHD**: se eliminan engines de inferencia, servicios LLM de clasificación y
  el cálculo local de Dolor/Drift/Onlife/Ecosistema/Dictamen; sus rutas `/api/*`
  de inteligencia pasan a ser **proxies** al gateway oficial de Motor A. Se
  conservan componentes React, layouts, cache, cliente HTTP, gateway, estados,
  render, lazy loading y **todo el pipeline comercial (Motor C)**.
- **Migración**: es un **cutover coordinado** (la inferencia está entretejida:
  `engines/scoring` lo importan 11 archivos, incl. rutas comerciales). Se ejecuta
  por fases con el gateway como cimiento. Manifiesto exacto en el repo RadarHD:
  `MIGRACION_ARQUITECTURA_1_0.md`.

## Cumplimiento (checklist de Arquitectura 1.0)

- [ ] RadarHD no contiene engines de inferencia.
- [ ] RadarHD no contiene scoring científico ni clasificación local.
- [ ] RadarHD no ejecuta IA para producir inteligencia científica.
- [ ] Todo dato científico en RadarHD proviene de la API de Motor A.
- [ ] Motor C consume inteligencia; no la produce.
- [ ] Sin lógica/clasificación/hipótesis duplicadas entre motores.
- [x] Decisión oficializada y documentada (este ADR + docs del ecosistema).

## Referencias
- `ARQUITECTURA_ECOSISTEMA.md` · `FRONTERAS_MOTORES.md` · `CONTRATOS_API.md` ·
  `ROADMAP_ARQUITECTONICO.md` · `DOCUMENTACION_MAESTRA.md` §24 ·
  RadarHD: `MIGRACION_ARQUITECTURA_1_0.md`, `src/lib/motor-a.gateway.ts`.
