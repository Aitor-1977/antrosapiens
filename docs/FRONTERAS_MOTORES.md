# FRONTERAS DE LOS MOTORES — Responsabilidad definitiva

> **ARQUITECTURA 1.0 (oficial, ADR-0001, 2026-07-25):** *Motor A piensa. Motor B
> muestra. Motor C vende. Sin excepción.* Este documento describe el estado
> **verificado** del código (2026-07-25) y marca la brecha respecto a la
> Arquitectura 1.0 como **deuda arquitectónica a eliminar**. La decisión tiene
> precedencia sobre cualquier implementación anterior — ver `ADR/ADR_0001_ARQUITECTURA_1_0.md`.

## Responsabilidad definitiva de cada motor

### Motor A — `antrosapiens` (Python/FastAPI) · **ACTIVO**
**Hace (verificado):**
- Captura de señales públicas (Google News, GDELT, RSS fijos, job boards, onlife).
- Normalización, dedup por hash, contrato de `evidencias` (validador único).
- **Inferencia DETERMINISTA sin IA** (`analisis.py:analizar`): scoring A/B/C,
  tipo_deuda, score_icp, viabilidad — reproducible y auditable.
- Curaduría (C10), Validación Científica (C11), Gobernanza (C12), Memoria/
  Comparador/Predictivo/Observatorio/Publicador/Sistema Operativo (C13–C18).
- Expone **API REST solo lectura** (72 endpoints) y el corpus `motor_a.corpus.v1`.

**Nunca hace (verificado en código):** no usa LLM; no envía emails; no ejecuta
contacto comercial; no renderiza dashboards de decisión comercial. (Existe
`pipeline_comercial.py` que **modela** etapas pero **no ejecuta** contacto — ver
Inconsistencias.)

### Motor B — RadarHD (parte de render) · **ACTIVO** (repo `radarHD`)
**Hace (verificado):** dashboard y visualizaciones en React/Next
(`src/components/*.tsx`, `src/app/admin/dashboard/page.tsx`): `Dashboard`,
`Inteligencia`, `InteligenciaEcosistemica`, `DictamenPanel`, `DriftPanel`,
`SignalRelations`, `FondosVC`, `InformesPanel`, `Sidebar`, etc. Build web (Vercel)
y **APK Android** (Capacitor).

### Motor C — Prospector HD (pipeline comercial) · **ACTIVO, DENTRO de RadarHD**
**No es un repo independiente.** Vive en `radarHD` (npm `"prospector"`). Hace
(verificado): prospección masiva, cadencia de emails, búsqueda de decisores
(Hunter/Apify), **envío de email a decisores** (`/api/email-decisor`),
seguimiento comercial (`seguimiento_comercial`), KPIs comerciales, lista
matutina, **Kill Switch**, notificaciones **Telegram**.

**Componentes/servicios/tablas (Motor C):** `SeguimientoComercial.tsx`,
`KillSwitchModal.tsx`, `ListaMatutina.tsx`, `ProspeccionMasiva.tsx` ·
`email-finder.service.ts`, `decisores.service.ts`, `telegram.service.ts`,
`contactos.service.ts` · tablas `prospecto`, `seguimiento_comercial`,
`cadencia_email`, `kill_switch_log`, `exclusion_permanente`.

---

## NORMATIVO vs REAL (frontera declarada vs código)

| Afirmación en `CLAUDE.md` (Motor A) | Realidad del código | Veredicto |
|-------------------------------------|---------------------|-----------|
| "Motor B **únicamente** renderiza" | RadarHD **renderiza Y** hace inferencia con IA, tiene BD y engines propios, y ejecuta el pipeline comercial | ❌ **NO se cumple** |
| "Motor C **únicamente** gestiona el pipeline comercial" (implícito: repo aparte) | Motor C **no es repo aparte**; está fusionado con B en `radarHD` | ⚠️ **Parcial** (sí gestiona comercial; no está separado) |
| "Todo análisis con **Gemini u otro LLM** vive en Motor B (RadarHD)" | RadarHD usa Gemini/NVIDIA/Anthropic/ZenMux (`services/llm.ts`, `scoring-llm.ts`) | ✅ **Se cumple** |
| "La Deuda Cultural™, score ICP e hipótesis son IP de HD y viven en Motor B" | RadarHD tiene `engines/scoring.ts`, `dictamenPericial.ts`, `inference.ts` | ✅ **Se cumple** (aunque Motor A también calcula un ICP determinista "preliminar", permitido por la Frontera de Interpretación 2026-07-22) |
| "Motor A no usa IA / es determinista" | `analisis.py` es 100% determinista, sin llamadas LLM | ✅ **Se cumple** |

### Resolución oficial (Arquitectura 1.0, ADR-0001)
La brecha "RadarHD también infiere/usa IA" **queda resuelta por decisión
arquitectónica**: es **deuda a eliminar**, no un estado válido.
- **Se conserva** la frontera de IA: la inferencia determinista vive en Motor A.
- **Se elimina** de RadarHD toda inferencia/clasificación/IA científica; sus
  rutas de inteligencia pasan a **consumir** los endpoints oficiales de Motor A.
- **Motor B y C siguen siendo la misma app** (`radarHD`); la separación es de
  **responsabilidad** (B representa, C vende), no de repositorio. Prospector
  permanece dentro de RadarHD (no se inventa un repo inexistente).

**A ELIMINAR de RadarHD (por ADR-0001):** `engines/{inference,scoring,
dictamenPericial,contradiction,ecosistema,onlife,priorizacion,recomendacion,
radar}`, `services/{llm,scoring-llm,scoring-reglas,dictamen*,drift,ecosistema,
evidencia,expedientes,perfil,recomendacion}`, rutas `/api/diag/{gemini,ia}` y el
cálculo local de Dolor/Drift/Onlife/Ecosistema/Dictamen. Manifiesto exacto y mapa
de acoplamiento: `radarHD/MIGRACION_ARQUITECTURA_1_0.md`.

**SE CONSERVA en RadarHD:** componentes React, layouts, pantallas, gráficos,
cache, cliente HTTP, gateway/adaptadores, estados, render, lazy loading, UX, y
**todo el pipeline comercial (Motor C)** — que pasa a consumir inteligencia de
Motor A en vez de calcularla.

---

## Qué jamás debe hacer cada motor (contrato operativo)

- **Motor A:** usar LLM, ejecutar contacto/emails, decidir "Expediente Activado",
  escribir en la BD de RadarHD.
- **Motor B/C (RadarHD):** escribir en la BD de Motor A, ni alterar el corpus
  `motor_a.corpus.v1` (lo consume, no lo muta).

## Referencias cruzadas
- Diagramas → `ARQUITECTURA_ECOSISTEMA.md` (§4 inferencia, §5 comercial)
- Contrato de corpus → `CONTRATOS_API.md`
- Inconsistencias completas → `DOCUMENTACION_MAESTRA.md` §24
