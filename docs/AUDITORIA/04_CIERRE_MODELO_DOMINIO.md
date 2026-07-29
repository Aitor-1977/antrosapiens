# Cierre del Modelo de Dominio — RadarHD + Motor A
### Anexo canónico · Bounded contexts definitivos, máquinas de estado y lenguaje ubicuo
### (Auditoría de solo lectura · sin recomendaciones de refactor · evidencia `archivo:línea`)

---

## 1. Fuentes de datos de cada pantalla (confirmado)

| Pantalla | Endpoint(s) | Tabla / origen físico | Source of Truth real |
|----------|-------------|-----------------------|----------------------|
| Dashboard | `/api/dashboard/metricas` | `senal_radar` + `seguimiento_comercial` | RadarHD (local) |
| SenalesNuevas | `/api/radar/senales`, `/api/radar/run` | `senal_radar` (estado_revision) | RadarHD (local) |
| OrganizacionesObservadas | `/api/radar/organizaciones[/id]`, `/drift`, `/onlife` | **Motor A** (gateway) | **Motor A (remoto)** |
| InteligenciaEcosistemica | `/api/radar/ecosistema/dashboard` | **Motor A** (gateway) | **Motor A (remoto)** |
| RecomendacionesEstrategicas | `/api/radar/oportunidades` | Motor C sobre datos de **Motor A** | Motor A (compuesto por C) |
| Prospectos (Bitácora) | `/api/prospectos`, `/api/cadencia`, `/api/decisores`, `/api/email-decisor`, `/api/enriquecer`, `/api/sow`, `/api/radar/buscar-uno`, `/api/informes` | `prospecto`, `cadencia_email` | RadarHD (local) |
| SeguimientoComercial (ventas) | `/api/seguimiento` | `seguimiento_comercial` | RadarHD (local) |
| KillSwitchHistory | `/api/kill-switch` | `kill_switch_log` | RadarHD (local) |
| DictamenPanel | `/api/dictamen` (**LLM V3**) | `prospecto.dictamen_pericial` + LLM | RadarHD (local + LLM) |
| DriftPanel | `/api/drift` (LLM) | drift.service | RadarHD (local + LLM) |
| Inteligencia | `/api/prospectos` | `prospecto` | RadarHD (local) |
| IntelligencePanel | — (calcula en cliente) | `engines/inference/contradiction/ritual` | ⚠ **ninguno (infiere en React)** |

**Hecho de arquitectura de datos:** las **dos únicas pantallas** cuyo SoT es Motor A son las
**científicas** (OrganizacionesObservadas, InteligenciaEcosistemica) + la recomendación que se
deriva de A. **Todo el resto lee tablas locales.** La producción de la faceta operativa vive en
RadarHD; la de la faceta científica, en Motor A.

---

## 2. Source of Truth por entidad (confirmado por esquema `db.ts`)

| Entidad | Tabla / servicio | Clave | Source of Truth | Poblada por | Leída por |
|---------|------------------|-------|-----------------|-------------|-----------|
| **Evidencia / Señal** | `senal_radar` | `id` SERIAL; FKs `organizacion_id`, `prospecto_id` (SET NULL) | RadarHD (captura local) **y** Motor A (`evidencias`) | `ejecutarRadar`→`evidencia.service` | señales, dashboard, lista-matutina, cron, tarjeta |
| **Organización (local)** | `organizacion` | `id` | RadarHD | `concentrar` | `observacion`, `senal_radar` |
| **Organización Observada (científica)** | `observacion` (agg) | `organizacion_id` **UNIQUE**; FK `prospecto_id` (SET NULL) | **desacoplada:** hoy la UI la lee de **Motor A** (id alfabético), no de esta tabla | `concentrar` | ecosistema.service (fingerprint) — **casi huérfana** |
| **Expediente Vivo (científico)** | Motor A `/organizaciones/{id}` | id alfabético determinista | **Motor A** | `_construir_expedientes` (A) | OrganizacionesObservadas |
| **Prospecto (comercial)** | `prospecto` | `id` SERIAL | **RadarHD** | confirmar señal (`senales/[id]`) | Prospectos, Dictamen, Drift, cadencia, seguimiento, kill |
| **Cadencia** | `cadencia_email` | FK `prospecto_id` CASCADE | RadarHD | cadencia | Prospectos |
| **Bitácora comercial** | `seguimiento_comercial` | FK `prospecto_id` SET NULL | RadarHD | SeguimientoComercial | Dashboard (embudo) |
| **Kill Switch** | `kill_switch_log` | FK `prospecto_id` CASCADE | RadarHD | PATCH prospecto / kill | KillSwitchHistory |
| **Exclusión permanente** | `exclusion_permanente` | UNIQUE `lower(empresa)` | RadarHD | Kill defensa (`prospectos/[id]:158`) | captura (`radar.ts:116`) |
| **Onlife (local)** | `motor_onlife_analysis` | por org | RadarHD (local) **vs** Motor A `/onlife` | — | (post-Fase3 la UI usa A) — posible huérfana |
| **Corrida** | `radar_run` | `id` | RadarHD | `ejecutarRadar` | señales/cron |

**Observación crítica de SoT:** la entidad "organización observada" tiene **dos representaciones
físicas** con SoT distintos — `observacion` (local, hoy casi huérfana) y el Expediente Vivo de
Motor A (remoto, el que ve el usuario). El puente `observacion.prospecto_id` fue diseñado para
unir ciencia↔comercio, pero **la representación que la UI muestra ya no es `observacion`**, sino
la de Motor A, que **no comparte id** con `prospecto`. Ahí está la fractura del agregado.

---

## 3. Los dos "expedientes" como ENTIDADES DE DOMINIO distintas

No es una diferencia de implementación: son **dos entidades con identidad, ciclo de vida,
invariantes y dueño distintos.**

### 3.1 Entidad A — **Organización Observada** (dominio de Observación)
- **Qué es:** una organización vista como *sistema cultural* a peritar.
- **Identidad:** id determinista de Motor A (alfabético) para la vista; `organizacion.id` en local.
- **Ciclo de vida:** **no tiene máquina de estados**. Es una *vista viva* (read-only) que refleja
  la evidencia acumulada. Lo único con estado aquí es la **Señal**: `nueva → confirmada | descartada`
  (`senal_radar.estado_revision`).
- **Invariantes:** determinista, trazable, "hipótesis a validar"; nunca se edita desde RadarHD.
- **Dueño:** **Motor A.**

### 3.2 Entidad B — **Prospecto** (dominio de Operación Comercial)
- **Qué es:** un candidato comercial que avanza hacia la venta de un Sprint Fundacional.
- **Identidad:** `prospecto.id` (SERIAL local).
- **Ciclo de vida:** **máquina de estados de 10 estados** (`EstadoPipeline`).
- **Invariantes:** G1–G8 (§5). Foco único (un Peritaje Activo), reversibilidad del freno.
- **Dueño:** **RadarHD (Motor C).**

### 3.3 La relación (¿agregado o contextos separados?)
- **Existe un agregado DISEÑADO pero no ejercido:** `senal_radar` enlaza `organizacion_id` **y**
  `prospecto_id`; `observacion` enlaza `organizacion_id` (UNIQUE) **y** `prospecto_id`. Es decir,
  el esquema modela **`Organización 0..1 — 0..1 Prospecto`** vía la Señal.
- **Pero está fracturado:** como la faceta científica se sirve desde **Motor A** (otro id-space),
  el enlace `observacion.prospecto_id` **no conecta lo que el usuario ve**. Hoy la única unión
  efectiva entre ambos linajes es el **nombre de empresa** (el adaptador de Fase 3 resuelve el
  decisor buscando `prospecto` por nombre, no por id).
- **Conclusión de dominio (sin recomendar aún):** son **dos bounded contexts distintos** que
  **comparten un origen** (la Señal) y **deberían** relacionarse por una **identidad de agregado
  única** — el concepto **"Expediente"** que une *lo observado* (A) con *lo operado* (Prospecto).
  Hoy esa identidad unificada **no existe**; la relación es nominal (por nombre), no referencial.

---

## 4. Clasificación de estados por dominio

| Estado / valor | Entidad | Dominio | Naturaleza |
|----------------|---------|---------|------------|
| `nueva` | Señal | **Observación** | intake pendiente de cribado |
| `confirmada` | Señal | **Observación → puente** | evento que **cruza** a Operación (crea Prospecto) |
| `descartada` | Señal | **Observación** | descarte reversible |
| `Detectado` | Prospecto | **Operación** | entrada al pipeline comercial |
| `Búnker`, `Enviado`, `Respuesta`, `Silencio` | Prospecto | **Operación (Siembra/cadencia)** | interacción comercial |
| `Call Activa` | Prospecto | **Operación** | conversación activa |
| `SOW Emitido` | Prospecto | **Operación** | propuesta emitida |
| `Peritaje Activo` | Prospecto | **Operación (con invariante global de foco)** | congela el pipeline |
| `Reactivación` | Prospecto | **Operación** | reingreso tras freno |
| `Kill Switch` | Prospecto | **Operación** | freno auditado + defensa del corpus |

**Frontera de dominio:** el **único punto de cruce** Observación→Operación es el evento
`confirmar señal` (`senales/[id]`), que instancia un `Prospecto` a partir de una `Señal`. No hay
retorno Operación→Observación (ni loop de aprendizaje hacia Motor A). Los estados comerciales
**no pertenecen** al dominio de Observación; la Observación **no tiene** máquina de estados.

---

## 5. Reglas de negocio (guards metodológicos) — tabla canónica

| # | Regla de negocio | Dónde se implementa | Qué protege | Si se elimina | Capa |
|---|------------------|---------------------|-------------|---------------|------|
| **G1** | **Protocolo de Congelamiento** — un solo `Peritaje Activo`; con uno activo no se confirman señales ni se mueven otros prospectos | `senales/[id]:41-49` (423), `prospectos/[id]:48-51`, `prospectos/route.ts:57`, UI `Prospectos.tsx:95,254,306`; engine `pipelineCongelado` `scoring.ts:107` | El **foco pericial** (un peritaje profundo a la vez); evita dispersión metodológica | El laboratorio abre N peritajes simultáneos → se degrada a CRM de volumen | **Dominio** (invariante), aplicada en Aplicación, reflejada en Interfaz |
| **G2** | **Monitoreo pasivo** — señales `C` solo pueden estar en `Detectado`/`Kill Switch` | `esMonitoreoPasivo` `scoring.ts:62`; `prospectos/[id]:78`, `prospectos/route.ts:65` | Que **ruido de baja calidad no entre a la venta** | Se contacta a organizaciones sin señal real → falsos positivos comerciales | **Dominio** |
| **G3** | **Verificación previa a Siembra** — entrar a `Búnker/Enviado/Respuesta/Silencio` requiere contacto verificado | `requiereVerificacion`/`puedeAvanzarASiembra` `scoring.ts:75,93`; `prospectos/[id]:86` | La **deliverability y la seriedad del outreach** | Se dispara cadencia sin contacto válido → daño reputacional | **Dominio** |
| **G4** | **Cualificación Liminal** — salir de `Respuesta` exige `AccionLiminal` (defensa/curiosidad/receptividad) | `clasificarCualificacionLiminal` `scoring.ts:98`; `prospectos/[id]:59-67` | Que la **respuesta se interprete metodológicamente** (curiosidad ≠ dolor) | Se asume interés donde solo hubo curiosidad → mala priorización | **Dominio** |
| **G5** | **Kill Switch trazable y reversible** — razón obligatoria (salvo defensa), registrado en log | `prospectos/[id]:98,149-153`, `kill-switch:21` | La **auditoría del freno** y la reversibilidad | Frenos silenciosos, sin memoria del porqué | **Aplicación** (validación) + **Dominio** (reversibilidad) |
| **G6** | **No disparar (SMTP mínimo)** — si `smtp_score < SMTP_MINIMO`, flag `no_disparar` | `esNoDisparar`/`SMTP_MINIMO`; `email-decisor:48`, `db.ts:43` | La **reputación de envío** (no mandar a buzones inválidos) | Bounce alto, listas negras | **Dominio** (regla), aplicada en Aplicación |
| **G7** | **Exclusión permanente / Defensa del corpus** — orgs excluidas se filtran en captura; se añaden en Kill por defensa | `exclusion_permanente` `db.ts:202,212`; `radar.ts:116`; `prospectos/[id]:158` | El **corpus** contra re-ingestar organizaciones ya descartadas | Ruido recurrente; se re-peritan casos ya cerrados | **Dominio** |
| **G8** | **Bloque 1 obligatorio** — alta de prospecto exige campos mínimos | `prospectos/route.ts:41` (400) | La **completitud mínima** del expediente comercial | Prospectos vacíos, no accionables | **Aplicación** (validación de entrada) |

**Lectura:** el método **está codificado como reglas de negocio de dominio** (G1–G4, G6, G7) en
el **lado comercial** — pero **no existe ninguna regla equivalente que obligue a peritar
científicamente antes de operar** (no hay gate "Prospecto requiere Organización Observada peritada +
DolorMap"). Ese es el vacío de dominio, no un defecto de UI.

---

## 6. Bounded contexts definitivos (con lenguaje ubicuo)

### BC-I · **Observación Antropológica**  (owner: Motor A)
- **Lenguaje ubicuo:** Evidencia, Señal, Corpus, Organización Observada, Deuda Cultural™, Dictamen
  (científico), Curaduría, Onlife, DolorMap®, Validación, Gobernanza, Solidez, Veredicto.
- **Entidades:** Evidencia, Señal (estado_revision), **Organización Observada** (aggregate root).
- **Invariante rector:** *toda inferencia ocurre aquí; read-only hacia afuera; determinista.*

### BC-II · **Operación Comercial (Motor C)**  (owner: RadarHD)
- **Lenguaje ubicuo:** Prospecto, Pipeline, Cadencia, Siembra, Cualificación Liminal, Decisor,
  SOW, Sprint Fundacional, Peritaje Activo, Kill Switch, Reactivación, Bitácora, Embudo.
- **Entidades:** **Prospecto** (aggregate root), Cadencia, Seguimiento (Bitácora), Kill Switch.
- **Invariante rector:** *foco único (un Peritaje Activo); todo freno reversible y auditado.*

### BC-III · **Captura & Corpus**  (owner: Motor A; hoy duplicado en RadarHD)
- **Lenguaje ubicuo:** Fuente, Conector, Prefiltro, Ruido, Normalización, Dedup, Contrato `corpus.v1`.
- **Frontera violada:** RadarHD tiene captura+clasificación LLM propia (`sources/*`, `scoring-llm`).

### BC-IV · **Presentación & Navegación**  (owner: RadarHD)
- **Lenguaje ubicuo:** Estación, Pestaña, Dossier, Panel, Banner, Vista.
- **Invariante rector:** *la vista no piensa.*

**Context map (relaciones entre contextos):**
- BC-I → BC-IV: **Customer/Supplier** vía contrato read-only (gateway). Correcto.
- BC-I → BC-II: **relación por evento** (`confirmar señal`) — hoy **nominal (por nombre)**, no
  referencial. Es la costura débil del sistema.
- BC-III ⇄ BC-I: **duplicado** (dos capturas). Frontera a colapsar.
- BC-II → BC-I: **inexistente** (no hay retorno de aprendizaje). Vacío.

---

## 7. Contratos entre contextos (inputs / outputs / responsabilidad)

| De → A | Contrato | Input | Output | Responsabilidad |
|--------|----------|-------|--------|-----------------|
| BC-I → BC-IV | `motor_a.corpus.v1`, `motor_a.dossier.v1`, Expediente Vivo | filtros / id | evidencia y peritaje | A produce, RadarHD representa |
| BC-I → BC-IV | Onlife, Ecosistema | org | análisis | idem |
| Señal → Prospecto (BC-I→BC-II) | `confirmar` (`senales/[id]`) | señal + dictamen Capa 0 | `prospecto Detectado` | **cruce único de dominios** (con G1) |
| BC-II interno | PATCH `prospecto` | estado + accion_liminal + kill | nuevo estado (G2–G8) | máquina de estados comercial |
| BC-II interno | `seguimiento`, `kill-switch`, `cadencia` | prospecto_id | Bitácora / log / cadencia | operación comercial |
| BC-III → BC-I (**faltante canónico**) | `A: clasificar señal → Deuda/ICP` | señal cruda | clasificación determinista | eliminaría el LLM local |
| BC-II → BC-I (**faltante canónico**) | `outcome → A` | resultado Sprint | aprendizaje | cerraría el loop |

---

## 8. Síntesis del modelo de dominio (para fijar en canon)

1. **Dos entidades raíz, dos contextos:** *Organización Observada* (BC-I, Motor A, sin estados) y
   *Prospecto* (BC-II, RadarHD, 10 estados). **No** son la misma cosa.
2. **SoT dividido por faceta:** ciencia = Motor A; operación = RadarHD (Neon). La tabla local
   `observacion` que debía unirlos quedó **casi huérfana** tras servir la ciencia desde A.
3. **El agregado unificador ("Expediente") existe en el esquema pero no en la práctica:** la unión
   real es **por nombre de empresa**, no por identidad referencial.
4. **El método vive como reglas de dominio (G1–G8) del lado comercial**, pero **falta el gate que
   ligue operación a peritaje científico + DolorMap** (vacío de dominio, no de UI).
5. **Faltan dos contratos entre contextos:** clasificación (BC-III→BC-I) y aprendizaje (BC-II→BC-I).

*(Sin recomendaciones de refactor, por instrucción. Este documento fija el modelo de dominio,
las dos máquinas de estado, las reglas de negocio y el context map como base canónica.)*

---

### Anexo — verificación
- Verificado por esquema (`db.ts:17-331`): FKs `prospecto`↔`observacion`↔`senal_radar`.
- Verificado por código: guards G1–G8 (`scoring.ts`, `prospectos/[id]`, `senales/[id]`, `radar.ts`).
- **[NO VERIFICADO]:** grafo exacto de transiciones intermedias BC-II más allá de G1–G8;
  si `motor_onlife_analysis` local sigue leyéndose (parece huérfana post-Fase 3).
