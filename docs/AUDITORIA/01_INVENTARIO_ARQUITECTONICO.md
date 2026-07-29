# Auditoría Arquitectónica Integral — Ecosistema Hamaca Digital
### Antrosapiens (Motor A) + RadarHD (Motor B/C) · Laboratorio de Antropología de la Innovación

> **Naturaleza:** auditoría de solo lectura. No se modificó código, ni se eliminó
> ni refactorizó nada. Cada afirmación se ancla a evidencia del repo (`archivo:línea`
> o resultado de inspección). Lo que **no** pude verificar se marca **[NO VERIFICADO]**.
>
> **Repos inspeccionados:**
> - `Aitor-1977/antrosapiens` → `/home/user/antrosapiens` (Python 3.11 / FastAPI).
> - `aitor-1977/radarhd` → `/workspace/radarhd` (Next.js 16 / React 19 / TS; npm `prospector`).

---

## 1. Resumen ejecutivo

El ecosistema **NO** cumple todavía el principio rector *«toda inferencia
antropológica ocurre exclusivamente en Motor A»*. Las Fases 2–4 migraron con éxito
el **camino de lectura del Expediente Vivo** (display) a Motor A vía gateway, pero
la auditoría revela que **coexisten dos motores de inteligencia completos**:

- **Motor A (Antrosapiens):** inferencia determinista, sin IA, 30+ módulos, Capas 0–18.
- **Un segundo motor de inferencia dentro de RadarHD**, con **tres focos activos**:
  1. **Pipeline de ingesta paralelo** — `engines/radar.ts:ejecutarRadar` scrapea
     GDELT/RSS/Google News (y consume Motor A como *una fuente más*), y clasifica
     **Deuda Cultural + Score ICP con LLM** (`services/scoring-llm.ts`, Gemini/NVIDIA/
     Claude/ZenMux) escribiendo en `senal_radar`. Es un Motor-A-equivalente completo.
  2. **Inferencia en el frontend (React)** — `components/IntelligencePanel.tsx`
     calcula índice de Deuda, contradicciones y "ritual competidor" **en el
     componente** (`engines/inference|contradiction|ritual`).
  3. **Dictamen pericial vía LLM** — `services/dictamen.service.ts` (Motor pericial V3)
     emite un reporte de 15 campos con `generarTexto()` (LLM), en paralelo al
     dictamen **determinista** de Motor A.

**Conclusión:** el trabajo de Fases 2–4 desacopló el *display*, pero la **producción
de inteligencia** (captura → clasificación de Deuda) sigue duplicada en RadarHD. La
frontera "A piensa / B observa" está **violada en el pipeline de ingesta y en 3
componentes**. La deuda arquitectónica central no es código muerto: es **duplicación
de responsabilidad de dominio** (dos sistemas infieren Deuda Cultural).

Los archivos que la misión anterior quería borrar (`concentrador.ts`,
`expedientes.service.ts`) **no son el problema**: son, respectivamente, (a) el motor
de la ingesta local aún viva y (b) el adaptador único Motor A→Motor C. El problema
real está **aguas arriba** (el pipeline de captura+LLM) y **en el frontend**.

**Prioridad estratégica:** antes de borrar nada, hay que decidir el destino del
**pipeline de ingesta de RadarHD** (¿lo absorbe Motor A?; ¿RadarHD deja de scrapear?).
Esa decisión gobierna todo lo demás.

---

## 2. Mapa completo de arquitectura

### 2.1 Flujo de información (noticia → decisión de Sprint Fundacional)

Reconstruido del código. **Hoy existen DOS caminos** que producen el mismo tipo de dato:

```
CAMINO A — Motor A (determinista, sin IA)                [antrosapiens]
  Fuentes reales (Google News RSS, GDELT, RSS fijos, Job boards)
    → connectors/*  → pipeline.py (search→normalize→validate→dedup)
    → tabla `evidencias`
    → analisis.py (scoring A/B/C, ICP, Deuda preliminar)
    → curaduria.py → dictamen.py → validacion_cientifica.py (Capa 11)
    → gobernanza.py (Capa 12) → memoria/predictivo/observatorio/publicador (13–18)
    → API FastAPI (solo lectura): /corpus, /organizaciones, /dossier, /ecosistema, …

CAMINO B — RadarHD ingesta propia (IA)                   [radarhd]
  engines/radar.ts:ejecutarRadar()
    → sources/{gdelt,rss,google-news,motor-a}.ts   (Motor A es UNA fuente más)
    → sources/prefiltro.ts (descarte de ruido, determinista)
    → services/scoring-llm.ts (LLM: Deuda Cultural + ICP) + scoring-reglas.ts
    → services/decisor-hunter.service.ts (decisor + email)
    → INSERT `senal_radar`
    → engines/concentrador.ts:concentrar() → tabla `observacion`
    → services/expedientes.service.ts  [ADAPTADOR: hoy relee de Motor A vía gateway]
    → services/{recomendacion,dictamenPericial,ecosistema}.service.ts (Motor C)
    → API interna Next.js /api/radar/* → componentes React

CONVERGENCIA (Fases 2–4):
  Las rutas de *lectura* (organizaciones, organizaciones/[id], drift, onlife,
  ecosistema/*) YA consumen Motor A vía motor-a.gateway.ts. Pero las tablas
  locales senal_radar/observacion las siguen llenando el CAMINO B, y las leen
  varios paneles (señales, dashboard, lista-matutina, cron, tarjeta).

DECISIÓN HUMANA (Sprint Fundacional):
  engines/recomendacion.ts:seleccionarProducto() → 'Sprint Fundacional DolorMap®'
    → RecomendacionesEstrategicas.tsx / OrganizacionesObservadas (Dossier)
    → SeguimientoComercial.tsx (Bitácora: avance hacia el Sprint) + /api/seguimiento
    → KillSwitchModal (freno de cadencia comercial)
```

**Evidencia:** `engines/radar.ts:1-12` (imports del pipeline); `services/scoring-llm.ts`
(header "Scoring con IA (Gemini + respaldo ZenMux). Detecta Deuda Cultural y Score ICP");
`engines/recomendacion.ts:46,117,134` ('Sprint Fundacional DolorMap®');
`components/SeguimientoComercial.tsx:12,75` (Bitácora hacia el Sprint).

### 2.2 Inventario de componentes por tipo

**Persistencia**
- **PostgreSQL / Neon** (servidor): `lib/db.ts:1-7` (`pg.Pool`, `DATABASE_URL`); `.env.example`
  ("PostgreSQL (Neon). Cadena de conexión completa"). Tablas: `senal_radar`, `observacion`,
  `organizacion`, `prospecto`, `seguimiento`, … (`lib/db.ts` initSchema).
- **SQLite / Capacitor** (móvil/APK): `capacitor.config.ts`, `@capacitor/android` (package.json),
  script `build:apk`. **[NO VERIFICADO en repo]** el `src/services/storage/sqlite.adapter.ts`
  que se compartió en el chat **no existe** en el repo (`find` sin resultados): es código
  **propuesto/externo**, no integrado. Sí existe `src/services/queue.service.ts` (cola de
  fetch cliente, usada por `Prospectos.tsx`).
- **SQLite (Motor A):** `antrosapiens` usa SQLite (dev/test) o PostgreSQL (prod) según URL
  (`db/database.py`; CLAUDE.md §Base).

**Backend / APIs**
- **Motor A:** FastAPI, ~85 endpoints solo-lectura (`hd_scraper/api/app.py`).
- **RadarHD:** 47 route handlers Next.js (`src/app/api/**/route.ts`).

**Motores (RadarHD `lib/engines/`)** — 12: `radar` (pipeline ingesta), `concentrador`
(curaduría+dedup local), `inference` (índice Deuda), `contradiction`, `ritual`, `scoring`,
`priorizacion`, `recomendacion`, `dictamenPericial`, `ecosistema`, `kpisComerciales`, `tarjeta`.

**Servicios (RadarHD `lib/services/`)** — 24: incluye `scoring-llm`, `scoring-reglas`, `llm`
(cliente Gemini/NVIDIA/Claude/ZenMux), `expedientes`, `recomendacion`, `dictamenPericial`,
`dictamen` (LLM V3), `ecosistema`, `evidencia`, `drift`, `perfil`, `decisor-hunter`,
`email-finder`, `hunter-search`, `dominio`, `sitio`, `wayback`, `apify`, `appstore`,
`empleos`, `fondos`, `contactos`, `telegram`, `decisores`.

**Fuentes (`lib/sources/`)** — `google-news`, `gdelt`, `rss`, `motor-a`, `prefiltro`,
`drift-densificador`, `empleo-densificador`, `adopcion-densificador`, `types`.

**Colas / Workers / Cron**
- **Cron:** endpoint `/api/radar/cron` protegido por `CRON_SECRET` (`route.ts:14`). La
  **programación** del cron **[NO está en el repo]** (no hay `vercel.json`): se configura
  fuera (Vercel dashboard). Motor A tiene su propio `scheduler.py` (APScheduler, 12 h).
- **Cola:** RadarHD `services/queue.service.ts` (cola cliente). Motor A `jobs.py` (tabla
  `jobs`, sin Redis).
- **Workers:** no hay worker dedicado server-side en RadarHD; el "trabajo pesado" corre en
  route handlers `force-dynamic` (p. ej. `admin/ejecutar-todo`, `radar/run`).

**Gateway:** `lib/motor-a.gateway.ts` — cliente HTTP único hacia Motor A (contrato
`motor_a.corpus.v1` / `motor_a.dossier.v1`).

**IA / LLM (solo RadarHD):** `services/llm.ts` (Gemini `gemini-2.5-flash` → NVIDIA → Claude →
ZenMux). Consumido por `scoring-llm`, `dictamen.service`, y rutas `decisores`, `drift`,
`buscar-uno`, `cron`, `fondos`, `run`, `dictamen`. **Motor A no usa IA** (determinista).

**Motor Onlife / DolorMap**
- **Onlife:** Motor A `onlife.py` + endpoints `/onlife/{org}[/analisis]`; RadarHD lo consume
  vía gateway (`motorA.onlifeAnalisis`) en `OrganizacionesObservadas`.
- **DolorMap:** Motor A `/dolormap/{org}`; en RadarHD hoy es **placeholder** (`dolormap: null`
  en el Dossier, `OrganizacionesObservadas.tsx`). `hipotesis_dolormap` proviene del análisis
  Onlife. El "Sprint Fundacional DolorMap®" es un **producto** recomendado, no un panel.

**Presentación (React, 23 componentes):** Dashboard, Sidebar, OrganizacionesObservadas,
InteligenciaEcosistemica, IntelligencePanel, Inteligencia, DictamenPanel, DriftPanel,
RecomendacionesEstrategicas, SeguimientoComercial (Bitácora), SenalesNuevas, Prospectos,
ProspeccionMasiva, ListaMatutina, FondosVC, InformesPanel, KillSwitch*, Tarjeta*, Banners,
Cualificacion*, SignalRelations, icons.

---

## 3. Mapa de dependencias

### 3.1 Cadenas críticas (qué rompe a qué)

```
motor-a.gateway.ts  ──consumido por──▶ expedientes.service (adaptador)
                                        ├─▶ recomendacion.service ─▶ engines/recomendacion, engines/ecosistema
                                        ├─▶ dictamenPericial.service ─▶ engines/dictamenPericial, recomendacion.service
                                        ├─▶ ecosistema.service ─▶ engines/ecosistema
                                        └─▶ ruta organizaciones (listado)

  Rutas Motor-A-fed (Fase 3): organizaciones, organizaciones/[id], drift/[org],
  onlife/[org], ecosistema/*.  ─▶ SOLO gateway. ✅

concentrador.ts (908 líneas) ── es núcleo del CAMINO B (ingesta local) ──
   ├─ concentrar()            ◀── admin/ejecutar-todo, organizaciones (POST)
   ├─ canonicalizar()         ◀── evidencia.service ◀── {drift,empleo,adopcion}-densificador
   ├─ calcularImplicacionSistemica() ◀── ruta organizaciones, dictamenPericial.service
   ├─ curar()/interpretar()   ◀── SOLO concentrador.test.ts (muertas en prod desde Fase 3)
   └─ tipos (Curaduria, Inferencia…) ◀── expedientes.service, engines/{recomendacion,dictamenPericial,ecosistema}

engines/radar.ts:ejecutarRadar ── orquesta el CAMINO B ──
   ◀── radar/run, radar/cron, admin/ejecutar-todo
   ─▶ sources/*, scoring-llm, scoring-reglas, decisor-hunter, prefiltro ─▶ INSERT senal_radar

senal_radar (tabla) ── leída por paneles vivos ──
   ◀── radar/senales, dashboard/metricas, lista-matutina, radar/cron, tarjeta/[id],
        ecosistema.service (fingerprint de caché)
```

### 3.2 Clasificación estructural vs adaptador vs puente

| Módulo | Rol estructural real | Tipo |
|--------|----------------------|------|
| `motor-a.gateway.ts` | Frontera única A→B/C | **Estructural (correcto)** |
| `expedientes.service.ts` | Mapea Dossier de A → `ExpedienteVivo` | **Adaptador (puente Fase 3)** |
| `concentrador.ts` | Motor de la ingesta local (curaduría, dedup, implicación) | **Estructural (CAMINO B)** |
| `engines/radar.ts` | Orquestador del pipeline de captura + LLM | **Estructural (CAMINO B, duplica A)** |
| `scoring-llm.ts` / `llm.ts` | Inferencia de Deuda con IA | **Estructural (duplica A, viola frontera)** |
| `dictamen.service.ts` | Dictamen pericial V3 con LLM | **Estructural (duplica A)** |
| `dictamenPericial.service.ts` | Dictamen determinista Motor C sobre datos de A | **Servicio (composición comercial)** |
| `recomendacion.service.ts` | Recomendación comercial sobre datos de A | **Servicio (composición comercial)** |
| `ecosistema.service.ts` | Contexto ecosistémico local + fingerprint de caché | **Servicio híbrido (ver §7)** |
| `evidencia.service.ts` | Escritura idempotente en `senal_radar` | **Servicio (persistencia CAMINO B)** |

### 3.3 Dependencias circulares
- **No se detectaron ciclos duros de import.** Sí hay **acoplamiento bidireccional de
  servicios**: `dictamenPericial.service` ↔ `recomendacion.service` (dictamen consume
  recomendaciones; ambos consumen `expedientes.service` y `ecosistema.service`). Es un
  **cluster fuertemente acoplado** (no ciclo, pero migran/rompen juntos). Evidencia:
  `dictamenPericial.service.ts:4-6`, `recomendacion.service.ts:6-7`.

---

## 4. Inventario de responsabilidades (archivos clave)

> Formato: **¿Qué hace? · ¿Quién lo consume? · ¿De quién depende? · ¿Eliminable? ·
> ¿Dividir? · ¿Repo correcto? · Dominio (A / RadarHD / Infra)**

**Motor A (antrosapiens)**
- `api/app.py` — expone toda la inteligencia (corpus, expedientes, dossier, ecosistema,
  organizaciones, onlife, validación, gobernanza). Consume: todos los módulos `hd_scraper/*`.
  Eliminable: no. Repo correcto: **sí (A)**.
- `expediente_vivo.py` — paridad de forma `OrganizacionObservada`/`Dossier`/`Drift` (Fase 3).
  Consume: observatorio, analisis, predictivo, validacion_cientifica. Repo: **A**.
- `analisis.py`, `curaduria.py`, `dictamen.py`, `validacion_cientifica.py`, `gobernanza.py`,
  `observatorio.py`, `onlife.py`, `predictivo.py`, `memoria.py`, `publicador.py` — capas de
  inferencia/validación/gobernanza. Repo: **A**.
- `pipeline_comercial.py` — **[MAL UBICADO]** pipeline comercial dentro de Motor A. El
  comercial vive en RadarHD (Motor C). Ya marcado como "vestigial" en CLAUDE.md/ROADMAP.
  **No eliminar aún** (verificar consumidores en `app.py`); candidato a deprecación (§7/§10).

**RadarHD — motores**
- `engines/radar.ts` — **pipeline de captura + LLM** (CAMINO B). Consume: sources/*,
  scoring-llm, scoring-reglas, decisor-hunter, prefiltro. Consumido por: radar/run, cron,
  admin/ejecutar-todo. **Eliminable:** no (hoy alimenta `senal_radar` → paneles). **Repo
  correcto:** **discutible** — es *captura+inferencia*, que por el principio rector debería
  vivir en Motor A. **Dominio: hoy RadarHD; debería migrar a A.**
- `engines/concentrador.ts` — curaduría/dedup/implicación local. Consumido: §3.1. Eliminable:
  **no** (canonicalizar/concentrar load-bearing). Dividir: **sí** (ver §7). Dominio: A-like
  pero atado a `senal_radar` local.
- `engines/inference.ts` (`calculateDebtIndex`), `contradiction.ts`, `ritual.ts` — **inferencia
  antropológica pura**. Consumido por **`IntelligencePanel.tsx` (React)**. **[VIOLACIÓN]** —
  inferencia en el frontend. Dominio: **debería ser Motor A**.
- `engines/scoring.ts` — scoring comercial + estados de pipeline. Consumido por `Prospectos.tsx`
  (React), `cadencia`, `email-decisor`. Mezcla Deuda/estado comercial. Dominio: híbrido.
- `engines/recomendacion.ts`, `dictamenPericial.ts` — **composición comercial** determinista
  sobre datos de A. Consumido por servicios homónimos. Dominio: **Motor C (correcto)**.
- `engines/priorizacion.ts`, `kpisComerciales.ts`, `tarjeta.ts` — comercial/operativo (Motor C).

**RadarHD — servicios**
- `scoring-llm.ts` / `llm.ts` — **inferencia de Deuda con IA**. **[VIOLACIÓN de frontera]**.
- `dictamen.service.ts` — dictamen pericial **V3 con LLM** (15 campos). **[DUPLICA A]**.
- `expedientes.service.ts` — adaptador único A→ExpedienteVivo (Fase 3). Dividir: no. Eliminar:
  no (único adaptador). Dominio: **puente A→C (correcto como adaptador)**.
- `recomendacion.service.ts`, `dictamenPericial.service.ts` — orquestan composición comercial
  Motor-A-fed. Dominio: **Motor C**.
- `ecosistema.service.ts` — **híbrido**: (a) contexto ecosistémico local, (b) fingerprint de
  caché sobre `senal_radar/observacion`. Dividir: **sí** (§7).
- `evidencia.service.ts` — persistencia idempotente `senal_radar` (usa `canonicalizar`). Dominio:
  captura (CAMINO B).

**Infra compartida**
- `lib/db.ts` (Pool Neon), `motor-a.gateway.ts`, `queue.service.ts`, `capacitor.config.ts`.

---

## 5. Deuda arquitectónica (con evidencia)

1. **Inferencia antropológica DUPLICADA (la deuda madre).** Motor A y RadarHD clasifican
   Deuda Cultural + ICP de forma independiente. RadarHD lo hace con LLM en `scoring-llm.ts`
   (header: "Detecta Deuda Cultural y Score ICP") dentro de `ejecutarRadar` (`engines/radar.ts:7`).
   Viola *«toda inferencia ocurre en Motor A»*.

2. **Lógica antropológica en el frontend (React).** `IntelligencePanel.tsx:3-5` importa
   `calculateDebtIndex` (inference), `detectContradictions`, `detectRitualCompetitor`. El
   componente **calcula** Deuda/contradicciones/ritual en render. `Prospectos.tsx:13` importa
   `engines/scoring`. `SeguimientoComercial.tsx:6` importa `kpisComerciales` (comercial, menos grave).

3. **Doble "Dictamen".** `dictamen.service.ts` (LLM, V3, `/api/dictamen`) vs
   `dictamenPericial.service.ts` (determinista, Motor-A-fed, `/api/radar/dictamen`). Dos
   conceptos de dictamen con nombres casi iguales → confusión de dominio + duplicación.

4. **Doble captura de fuentes.** `sources/{gdelt,google-news,rss}.ts` en RadarHD replican los
   conectores de Motor A (`connectors/{gdelt,google_news,rss_fijos}.py`). Motor A es, además,
   *una fuente más* dentro del pipeline de RadarHD (`sources/motor-a.ts`), que luego lo
   **re-clasifica** con LLM — el corpus objetivo de A se re-interpreta en B.

5. **Servicio híbrido `ecosistema.service.ts`** — mezcla contexto ecosistémico (dominio) con
   fingerprint de caché (infra). Dos responsabilidades en un archivo (`ecosistema.service.ts:45-47`).

6. **`concentrador.ts` monolítico (908 líneas)** — reúne: dedup (`canonicalizar`,
   `deduplicarEvidencia`), curaduría (`curar`), inferencia (`interpretar`), formato
   (`calcularImplicacionSistemica`), pipeline (`concentrar`), tipos de dominio. Seis
   responsabilidades en un archivo. `curar/interpretar` están **muertas en producción** (solo
   `concentrador.test.ts`) desde Fase 3.

7. **`pipeline_comercial.py` en Motor A** — comercial en el repo equivocado (CLAUDE.md lo
   reconoce; el comercial real vive en RadarHD).

8. **Persistencia potencialmente triple.** Neon (server) + SQLite/Capacitor (móvil,
   `sqlite.adapter` **propuesto, no en repo**) + SQLite de Motor A. Riesgo de modelos duplicados
   (`prospects` móvil con `llm_evidence/llm_confidence/model_used/llm_hash` vs `prospecto`/`senal_radar`
   en Neon). **[PARCIALMENTE VERIFICADO]** — el adaptador móvil no está integrado.

9. **Cron fuera del repo.** No hay `vercel.json`; la cadencia del cron no es versionada →
   inconsistencia entre "lo que el código espera" y "lo que Vercel ejecuta".

10. **Naming/dominio inconsistentes.** `dictamen` vs `dictamenPericial`; `Inteligencia.tsx`
    vs `InteligenciaEcosistemica.tsx` vs `IntelligencePanel.tsx` (mezcla ES/EN + tres paneles
    de "inteligencia"); `senal_radar`/`observacion`/`organizacion` (tres tablas para la misma
    entidad conceptual "organización observada").

---

## 6. Riesgos

| # | Riesgo | Severidad | Evidencia |
|---|--------|-----------|-----------|
| R1 | Divergencia de verdad: A y B clasifican Deuda distinto para la misma org | **Alta** | scoring-llm vs analisis.py |
| R2 | Si se apaga el CAMINO B sin sustituir la captura, se vacían paneles (señales, dashboard, lista-matutina, tarjeta, cron) | **Alta** | §3.1 lectores de `senal_radar` |
| R3 | Cambiar la fuente de `implicacion_sistemica` altera copy visible del Dossier | Media | ruta organizaciones + dictamenPericial.service |
| R4 | Coste/latencia/no-determinismo del LLM en la ruta de captura | Media | llm.ts (4 proveedores) |
| R5 | Cron no versionado → corridas no reproducibles | Media | ausencia de vercel.json |
| R6 | Modelo móvil (Capacitor) divergente si se integra el `sqlite.adapter` propuesto | Media | adapter fuera de repo |
| R7 | Acoplamiento fuerte recomendacion↔dictamenPericial↔expedientes: refactor arriesgado si no es coordinado | Media | §3.3 |
| R8 | Inferencia en React no testeable ni cacheable server-side | Media | IntelligencePanel.tsx:3-5 |

---

## 7. Responsabilidades mal ubicadas + cómo dividir (no borrar)

**7.1 `scoring-llm.ts` + `engines/radar.ts` (captura+inferencia con IA)**
- **Problema:** inferencia de Deuda fuera de Motor A.
- **No borrar.** Decisión de arquitectura previa: ¿Motor A absorbe la captura, o RadarHD
  scrapea pero **delega la clasificación** a un endpoint de Motor A? Recomendación: mover la
  **clasificación de Deuda/ICP** a Motor A (nuevo `POST /clasificar` determinista o el ya
  existente `analisis`), dejando en RadarHD solo el *fetch* de fuentes (o eliminándolo si A ya
  cubre esas fuentes). Riesgo: **alto** (toca la ingesta viva).

**7.2 `IntelligencePanel.tsx` / `inference|contradiction|ritual`**
- **Dividir:** sacar el cálculo del componente. Crear endpoint Motor A (o método gateway) que
  emita índice de Deuda + contradicciones + ritual con la MISMA forma; el componente solo
  renderiza. Riesgo: **medio** (hay que preservar la vista pixel a pixel).

**7.3 `concentrador.ts` (908 líneas → módulos)**
- `dedup.ts` (`canonicalizar`, `deduplicarEvidencia`) — infra de datos.
- `curaduria.local.ts` (`curar`) + `inferencia.local.ts` (`interpretar`) — **muertas en prod**;
  aislarlas para deprecarlas cuando se retire la ingesta local.
- `formato.ts` (`calcularImplicacionSistemica`) — presentación.
- `pipeline.local.ts` (`concentrar`) — orquestación de ingesta.
- `expediente.types.ts` — tipos de dominio compartidos (hoy los importan 4 módulos).
- **Orden:** primero extraer **tipos** (runtime-neutral, tsc lo verifica), luego helpers puros,
  al final el pipeline. Riesgo por paso: bajo→medio.

**7.4 `ecosistema.service.ts` (híbrido)**
- Separar `contextoEcosistemico` (dominio) de `fingerprintCorpus` (infra de caché). Riesgo: bajo.

**7.5 `dictamen.service.ts` (LLM V3) vs `dictamenPericial.service.ts`**
- Decidir cuál es canónico. El principio rector favorece el **determinista Motor-A-fed**
  (`dictamenPericial`). `dictamen.service` (LLM) debería deprecarse o moverse a Motor A si su
  salida de 15 campos aporta algo que A no da. Riesgo: medio (revisar `/api/dictamen` consumers).

**7.6 `pipeline_comercial.py` (Motor A)** — mover el concepto a RadarHD o deprecar. Riesgo: bajo
(si no lo consume `app.py`; **verificar**).

---

## 8. Responsabilidades duplicadas (resumen)

| Responsabilidad | En Motor A | En RadarHD | Veredicto |
|-----------------|-----------|------------|-----------|
| Clasificar Deuda Cultural + ICP | `analisis.py` | `scoring-llm.ts` (LLM) + `inference.ts` (React) | **A es canónico** |
| Captura de fuentes (GNews/GDELT/RSS) | `connectors/*` | `sources/*` | **A es canónico** |
| Curaduría / dedup de evidencia | `curaduria.py` | `concentrador.ts` (`curar`) | **A es canónico** (B muerto en prod) |
| Dictamen pericial | `dictamen.py`+`validacion_cientifica.py` | `dictamen.service.ts` (LLM) | **A es canónico** |
| Contexto ecosistémico | `observatorio.py` | `engines/ecosistema.ts` | **A es canónico** (B usado internamente) |
| Contradicciones / tensiones | `validacion_cientifica.py` | `contradiction.ts` (React) | **A es canónico** |
| Pipeline comercial | `pipeline_comercial.py` | `seguimiento`/`cadencia`/`kill-switch` | **RadarHD es canónico** |

---

## 9. Plan de integración definitiva

**Principio de corte:** *RadarHD nunca produce inteligencia; solo la consume y la opera.*
La integración se logra cuando **el único productor de Deuda/ICP/dictamen/contexto es Motor A**,
y RadarHD queda como **captura opcional + composición comercial + presentación + operación**.

**Estado objetivo por capa (una responsabilidad, un lugar):**
- **Producción de inteligencia** → 100% Motor A (incluida la clasificación que hoy hace `scoring-llm`).
- **Captura de fuentes** → Motor A (RadarHD deja de scrapear, o lo hace solo como disparador que
  entrega URLs crudas a Motor A). Elimina `sources/*` duplicados y `scoring-llm`.
- **Composición comercial (Motor C)** → RadarHD server-side (`recomendacion`, `dictamenPericial`,
  `cadencia`, `seguimiento`, `kill-switch`), alimentada por el gateway.
- **Presentación** → React puro, **sin** imports de `engines/inference|contradiction|ritual|scoring`.
- **Persistencia** → Neon para operación comercial (prospecto/seguimiento); `senal_radar/observacion`
  se retiran cuando la captura migre a A; SQLite/Capacitor solo para caché offline de lectura.

---

## 10. Roadmap de refactorización (ordenado por dependencia y riesgo)

> Cada paso mantiene el protocolo: inventario → contrato en A → gateway → ruta → tsc/tests →
> borrar solo lo que quede muerto. Sin cambios visuales.

**F5 — Sacar inferencia del frontend (riesgo medio, alto valor de principio).**
Exponer en Motor A (o gateway) el índice de Deuda + contradicciones + ritual con la forma que
consume `IntelligencePanel`; el componente pasa a solo-render. Al quedar sin importadores,
`inference/contradiction/ritual` se deprecan.

**F6 — Unificar el Dictamen.** Declarar canónico el determinista (`dictamenPericial`, Motor-A-fed).
Migrar/retirar `dictamen.service.ts` (LLM V3) y su ruta `/api/dictamen`.

**F7 — Migrar la CLASIFICACIÓN de captura a Motor A.** `ejecutarRadar` deja de llamar
`scoring-llm`; en su lugar entrega las fuentes crudas a un endpoint determinista de Motor A que
devuelve la clasificación. Se retira `scoring-llm`/`llm` de la ruta de captura.

**F8 — Retirar la captura duplicada.** Si Motor A cubre las fuentes, eliminar `sources/*` y
`engines/radar.ts`; los paneles que hoy leen `senal_radar` pasan al corpus de Motor A. **Recién
aquí** `concentrador.ts` (via `concentrar`/`canonicalizar`) queda sin importadores y es
eliminable — junto con `senal_radar/observacion`.

**F9 — Dividir monolitos** (`concentrador` §7.3, `ecosistema.service` §7.4) y **consolidar el
adaptador** (`expedientes.service` → un único módulo adaptador nombrado como tal).

**F10 — Limpieza y coherencia.** Deprecar `pipeline_comercial.py` en Motor A; unificar naming
(`Inteligencia*`, `dictamen*`); versionar el cron (`vercel.json`); decidir el destino del
`sqlite.adapter` móvil (integrarlo con un solo modelo o descartarlo).

**Auditoría de UX (§ objetivo 10 del encargo).** El flujo metodológico
`Observación → Selección → Expediente → Motores → DolorMap → Bitácora → Decisión` **[NO VERIFICADO
end-to-end]**: existen los componentes para cada etapa (SenalesNuevas → OrganizacionesObservadas
→ Dossier → recomendacion/onlife → SeguimientoComercial), y el `Sidebar` permite **navegación
libre entre estaciones** (no un wizard secuencial). **Hallazgo preliminar:** la interfaz **no
fuerza** el orden metodológico — el usuario puede abrir Bitácora o Recomendaciones sin pasar por
el Expediente. Confirmarlo exige leer `Sidebar.tsx` + el enrutado de estaciones (pendiente de una
segunda pasada de UX).

---

### Anexo — Afirmaciones NO verificadas (honestidad de la auditoría)
- Scheduling real del cron (fuera del repo).
- Integración del `sqlite.adapter.ts` móvil (no existe en el repo).
- Flujo UX end-to-end forzado/no-forzado (requiere lectura de `Sidebar.tsx` + rutas de página).
- Consumidores exactos de `pipeline_comercial.py` en `app.py` (no re-verificado en esta pasada).
- Comportamiento línea a línea de cada engine (se auditó por headers, imports y firmas, no full-read).
