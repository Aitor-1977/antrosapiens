# Modelo Mental del Sistema — Documento de Arquitectura (nivel CTO)
### Hamaca Digital · Laboratorio de Antropología de la Innovación
### Antrosapiens (Motor A) + RadarHD (Motor B/C)

> Auditoría de solo lectura. No se modificó código. Este documento **no** inventaría
> archivos: reconstruye el sistema como **una sola plataforma** y razona sobre
> **responsabilidades, fronteras y contratos**. Toda afirmación se ancla a evidencia
> del repo; lo no comprobable se marca **[NO VERIFICADO]**.

---

## 0. Tesis de la auditoría (para el CTO, en tres frases)

El sistema tiene **un dominio claro y correcto** — *«Motor A piensa, RadarHD observa
y opera»* — pero **una topología que aún no lo refleja**: la responsabilidad de
**inferir Deuda Cultural** vive hoy en **tres lugares a la vez** (Motor A determinista,
un pipeline LLM en RadarHD, y componentes React). El trabajo de las Fases 2–4 arregló
el *consumo* (la lectura), no la *producción* (la escritura de inteligencia). La
evolución no es "borrar archivos": es **colapsar la producción de inteligencia a un
único productor** y dejar que todo lo demás sea consumo, composición comercial y
operación. La buena noticia: la plataforma ya tiene la pieza que lo hace posible sin
romper nada — **el gateway** — y un patrón (strangler-fig) ya probado en las Fases 2–4.

---

## 1. El sistema como UNA plataforma: la columna de 10 etapas

Narro la plataforma según tu propia espina de 10 etapas, diciendo **quién es el dueño
real hoy** y **si la frontera está limpia o violada**.

| # | Etapa | Dueño conceptual | Dueño **real hoy** | Estado de frontera |
|---|-------|------------------|--------------------|--------------------|
| 1 | Captura de evidencia | Motor A | **A y RadarHD** (`connectors/*` vs `sources/*`+`engines/radar`) | ⚠ Duplicada |
| 2 | Normalización | Motor A | A (`pipeline.py`) · RadarHD normaliza aparte en captura propia | ⚠ Duplicada |
| 3 | Construcción de corpus | Motor A | A (`evidencias`, contrato `motor_a.corpus.v1`) | ✅ Limpia |
| 4 | **Inferencia antropológica** | **Motor A (exclusivo)** | **A + RadarHD (LLM) + React** | ❌ **Violada (crítica)** |
| 5 | Servicios de dominio | Compartido según dominio | Mezclado (ver §3 bounded contexts) | ⚠ Parcial |
| 6 | Gateway de integración | Frontera única | RadarHD `motor-a.gateway.ts` | ✅ Correcta (subutilizada) |
| 7 | Operación del laboratorio | RadarHD | RadarHD | ✅ Correcta |
| 8 | Experiencia de usuario | RadarHD | RadarHD | ⚠ No fuerza el método (§9) |
| 9 | Bitácora metodológica | RadarHD | RadarHD (`SeguimientoComercial` + `/api/seguimiento`) | ✅ Correcta |
| 10 | Sprint Fundacional | RadarHD (decisión humana) | RadarHD (`recomendacion` → producto → Bitácora) | ✅ Correcta |

**Lectura CTO:** las etapas 3, 6, 7, 9, 10 están sanas. El problema es un **bloque
contiguo, 1→2→4**: la producción de inteligencia (capturar + normalizar + inferir Deuda)
está partida entre los dos repos. Todo el resto de la deuda es consecuencia de esto.

---

## 2. Flujo de datos completo: de la señal al Sprint Fundacional

Existen **dos caminos de producción** que terminan en el mismo tipo de dato
("organización observada con hipótesis de Deuda"), y **convergen** en la capa de
lectura y decisión.

### 2.1 Camino A — Motor A (determinista, sin IA) · *el que debería ser único*
`Fuente pública → connectors/* → pipeline.py (search·normalize·validate·dedup) →
tabla evidencias → analisis.py (A/B/C, ICP, Deuda preliminar) → curaduria → dictamen →
validacion_cientifica (Capa 11, bloquea sin evidencia) → gobernanza (Capa 12, sella
huella) → observatorio/predictivo/memoria/publicador → API FastAPI solo-lectura.`

### 2.2 Camino B — RadarHD (con IA) · *el que duplica al Camino A*
`engines/radar.ts:ejecutarRadar → sources/{gdelt,rss,google-news,motor-a} (Motor A es
UNA fuente más) → prefiltro (determinista) → scoring-llm (LLM: Deuda + ICP) +
scoring-reglas → decisor-hunter → INSERT senal_radar → concentrador.concentrar →
tabla observacion.`
Evidencia: `engines/radar.ts:1-12`; `scoring-llm.ts` (header "Detecta Deuda Cultural y
Score ICP"); `sources/motor-a.ts` importado como fuente #4.

### 2.3 Convergencia (lo que las Fases 2–4 lograron)
`expedientes.service (ADAPTADOR: hoy relee de A vía gateway) → recomendacion /
dictamenPericial / ecosistema services (Motor C) → /api/radar/* → React.`
Las rutas de lectura (organizaciones, /[id], drift, onlife, ecosistema/*) **ya consumen
A**. Pero `senal_radar`/`observacion` las siguen **llenando** el Camino B y las **leen**
paneles vivos: `radar/senales`, `dashboard/metricas`, `lista-matutina`, `radar/cron`,
`tarjeta/[id]`.

### 2.4 Decisión humana — el Sprint Fundacional
`engines/recomendacion.ts:seleccionarProducto → 'Sprint Fundacional DolorMap®' (si
viabilidad Alta) → RecomendacionesEstrategicas / Dossier → SeguimientoComercial
(Bitácora: avance hacia el Sprint) + /api/seguimiento → KillSwitch (freno de cadencia).`
Evidencia: `engines/recomendacion.ts:46,117,134`; `SeguimientoComercial.tsx:12,75`.

**Insight de flujo:** el Sprint Fundacional **no es un motor**; es el *output comercial*
de la recomendación + el *registro* de la Bitácora. Está bien ubicado (RadarHD/Motor C).
El defecto no está en el final del flujo, sino en su **origen bifurcado**.

---

## 3. Bounded contexts del dominio y sus fronteras

Ocho contextos. Para cada uno: **por qué existe · qué problema resuelve · qué principio
protege · qué pasaría si desapareciera · estado de su frontera.**

### BC-1 · Captura de Evidencia
- **Por qué existe:** convertir la web pública en señales estructuradas.
- **Problema que resuelve:** obtener materia prima objetiva sin sesgo de interpretación.
- **Principio que protege:** "los hechos antes que el juicio".
- **Si desapareciera:** el sistema se queda sin insumo; todo lo demás se seca.
- **Frontera:** ⚠ **duplicada** — `connectors/*` (A) y `sources/*`+`engines/radar` (B).

### BC-2 · Corpus / Evidencia objetiva
- **Por qué existe:** una base de verdad normalizada, fechada y deduplicada.
- **Problema:** que todos los consumidores compartan **una** definición de "hecho".
- **Principio:** *single source of truth* de la evidencia (contrato `motor_a.corpus.v1`).
- **Si desapareciera:** cada consumidor reinventaría "qué es una señal" → caos semántico.
- **Frontera:** ✅ limpia y correcta (Motor A). **Preservar intacta.**

### BC-3 · Inferencia Antropológica  *(el corazón, y la frontera violada)*
- **Por qué existe:** transformar evidencia en **hipótesis de Deuda Cultural** trazable.
- **Problema:** interpretar sin inventar; reproducibilidad; auditabilidad.
- **Principio:** *«toda inferencia ocurre exclusivamente en Motor A»* — es el principio
  fundacional del laboratorio (IP de HD).
- **Si desapareciera:** RadarHD dejaría de tener contenido; el laboratorio perdería su tesis.
- **Frontera:** ❌ **violada en 3 puntos** — `scoring-llm.ts` (LLM), `inference/contradiction/
  ritual` en `IntelligencePanel.tsx`, y `dictamen.service.ts` (LLM V3). **Esta es la deuda madre.**

### BC-4 · Inteligencia Ecosistémica
- **Por qué existe:** pasar de la organización individual al ecosistema (clusters, centinelas).
- **Problema:** ver patrones que ninguna org revela sola.
- **Principio:** agregación determinista, "solo compara, no interpreta".
- **Si desapareciera:** se pierde la lectura macro (Observatorio LATAM).
- **Frontera:** ✅ canónica en A (`observatorio.py`); ⚠ hay una copia local (`engines/ecosistema`)
  usada como contexto interno de la recomendación.

### BC-5 · Composición Comercial (Motor C)
- **Por qué existe:** traducir inteligencia en **acción de negocio** (producto, decisor, cadencia).
- **Problema:** decidir a quién, cuándo y con qué oferta acercarse — **sin re-inferir**.
- **Principio:** "Motor A recomienda, Motor C decide y ejecuta la acción comercial" (frontera A/C).
- **Si desapareciera:** el laboratorio pensaría pero no vendería; no habría Sprint.
- **Frontera:** ✅ correcta en RadarHD (`recomendacion`, `dictamenPericial`, `cadencia`,
  `seguimiento`, `kill-switch`). **Preservar en RadarHD.**

### BC-6 · Operación del Laboratorio
- **Por qué existe:** revisar señales, confirmar/descartar, curar la lista de prospectos.
- **Problema:** poner al humano en el loop de decisión sobre lo que el motor propone.
- **Principio:** "la máquina propone, el humano dispone".
- **Si desapareciera:** el sistema decidiría solo → contradice la metodología pericial.
- **Frontera:** ✅ RadarHD (`SenalesNuevas`, `senales/[id]` confirmar/descartar, `Prospectos`).

### BC-7 · Bitácora Metodológica
- **Por qué existe:** registrar el avance de cada organización hacia el Sprint Fundacional.
- **Problema:** trazabilidad de la decisión humana; memoria del proceso, no CRM.
- **Principio:** "toda decisión queda registrada y es reversible" (kill-switch).
- **Si desapareciera:** se pierde la auditoría del *proceso* (distinta de la auditoría de la
  *evidencia*, que vive en A).
- **Frontera:** ✅ RadarHD (`SeguimientoComercial` + `/api/seguimiento` + `KillSwitch`).

### BC-8 · Presentación / UX
- **Por qué existe:** hacer legible y operable la inteligencia.
- **Problema:** convertir datos en decisiones humanas.
- **Principio:** "la vista no piensa" — cero lógica de dominio en React.
- **Si desapareciera:** no habría laboratorio usable.
- **Frontera:** ⚠ **violada** — `IntelligencePanel`, `Prospectos`, `SeguimientoComercial`
  **calculan** en render (importan `engines/*`).

**Mapa de fronteras (resumen CTO):** las fronteras **sanas** son BC-2, BC-5, BC-6, BC-7.
Las **violadas** son BC-1 (duplicada), BC-3 (crítica), BC-8 (lógica en la vista). Toda la
evolución debe apuntar a **cerrar BC-3** primero: es la que da sentido al resto.

---

## 4. Contratos entre Motor A y RadarHD

La integración es **unidireccional y de solo lectura**: A **publica**, RadarHD **consume**.
RadarHD nunca escribe en A (la API de A es read-only). Esta es una de las **mejores
decisiones del sistema y debe preservarse**.

| Contrato | Input (RadarHD → A) | Output (A → RadarHD) | Responsabilidad que fija |
|----------|---------------------|----------------------|--------------------------|
| `motor_a.corpus.v1` (`GET /corpus`) | filtros (empresa, categoría, fechas, confianza) | evidencia **objetiva** (empresa·fuente·fecha·texto·keywords·confianza·tipo_evento) — **sin Deuda** | "A entrega hechos, no juicios" |
| `motor_a.dossier.v1` (`GET /dossier/{org}`) | org | expediente completo (27 claves: narrativa, hipótesis, validación, gobernanza…) | "A entrega el peritaje completo" |
| Expediente Vivo (`GET /organizaciones[/{id}]`, `/drift`) | id determinista | `OrganizacionObservada` / `Dossier` / `Drift` (paridad de forma) | "A entrega la forma que la UI ya consume" |
| Ecosistema (`GET /ecosistema/panel`, `/clusters`…) | — | Dashboard ecosistémico | "A entrega la lectura macro" |
| Onlife (`GET /onlife/{org}/analisis`) | org | `RespuestaOnlife` | "A entrega la continuidad Onlife" |

**Propiedades del contrato (lo que hay que proteger):**
1. **Dirección única** A→B. Sin llamadas de vuelta. Sin BD compartida. (`db/database.py` en A;
   `lib/db.ts` en RadarHD son bases **distintas**.)
2. **Versionado con candado:** tag `motor_a.corpus.v1`; un tag desconocido **rompe** el consumo
   (`motor-a.gateway.ts:validarContratoCorpus`). Evita ingerir formas desconocidas.
3. **Frontera semántica:** `/corpus` **no** incluye Deuda/ICP/hipótesis — por diseño. Esa línea
   es la que `scoring-llm` **cruza** al re-clasificar el corpus con LLM.

**Contrato que FALTA (la pieza que cerraría BC-3):** no existe un contrato
`A: clasificar señal → Deuda/ICP` que RadarHD pueda invocar en su captura. Hoy RadarHD lo
resuelve **localmente con LLM**. Ese contrato inexistente es la causa raíz de la duplicación.

---

## 5. Responsabilidades duplicadas (dónde el dominio aparece dos veces)

| Responsabilidad de dominio | Instancia A (canónica) | Instancia RadarHD (a colapsar) | Naturaleza de la duplicación |
|----------------------------|------------------------|--------------------------------|------------------------------|
| Clasificar Deuda + ICP | `analisis.py` (determinista) | `scoring-llm.ts` (LLM) + `inference.ts` (React) | **Divergente** (métodos distintos → verdades distintas) |
| Capturar fuentes | `connectors/*` | `sources/*` | **Redundante** (mismas fuentes) |
| Curaduría / dedup | `curaduria.py` | `concentrador.curar/canonicalizar` | **Redundante** (`curar` ya muerto en prod) |
| Dictamen pericial | `dictamen.py`+`validacion_cientifica.py` | `dictamen.service.ts` (LLM V3) | **Divergente** |
| Contexto ecosistémico | `observatorio.py` | `engines/ecosistema.ts` | **Redundante** (B como caché de contexto) |
| Contradicciones / tensiones | `validacion_cientifica.py` | `contradiction.ts` (React) | **Divergente** |

**Distinción clave para el CTO:** las duplicaciones **divergentes** (métodos distintos que
pueden dar resultados distintos) son las peligrosas — generan "¿cuál Deuda es la verdadera?".
Las **redundantes** (misma lógica repetida) son molestas pero benignas. Priorizar el colapso
de las **divergentes** (filas 1, 4, 6).

---

## 6. Semántica de dependencias: fuertes, débiles y accidentales

- **Fuertes (estructurales; si se rompen, cae el sistema):**
  `gateway → endpoints de A`; `expedientes.service → gateway`; `recomendacion/dictamenPericial/
  ecosistema services → expedientes.service`; `paneles vivos → senal_radar`. Son la **columna
  vertebral**; se tocan solo con contrato estable.

- **Débiles (reemplazables/opcionales; el sistema tolera su ausencia):**
  `sources/motor-a.ts` (A como *una* fuente); los 4 proveedores LLM con fallback en cascada
  (`llm.ts`); las fuentes RSS (fallan en silencio y la corrida sigue). Buen diseño defensivo.

- **Accidentales (acoplamientos que no deberían existir; deuda pura):**
  1. `IntelligencePanel/Prospectos/SeguimientoComercial → engines/*` — dominio dentro de la vista.
  2. **El corpus objetivo de A entra al LLM de B** (`sources/motor-a.ts` → `scoring-llm`) — A
     produce hechos que B **re-interpreta**: acoplamiento invertido (el productor de verdad se
     vuelve insumo de una segunda verdad).
  3. Tipos de dominio (`Curaduria`, `Inferencia`…) **atrapados dentro de `concentrador.ts`**
     (el monolito de ingesta), lo que acopla los engines comerciales al motor de captura.
  4. `ecosistema.service` mezcla `fingerprintCorpus` (infra de caché) con `contextualizar`
     (dominio) — dos ejes de cambio en un archivo.

**Regla CTO:** las dependencias **accidentales** son las que se atacan primero en cualquier
modularización, porque no cuestan compatibilidad (nadie depende de que existan *así*).

---

## 7. Adaptadores temporales (existen solo por compatibilidad)

- **`expedientes.service.ts` — el adaptador estrella de la migración.** Nació en la Fase 3
  para mapear el `Dossier` de A → la forma legacy `ExpedienteVivo` que los servicios comerciales
  y el listado **ya consumían**, de modo que no hubo que reescribirlos. **Por qué existe:**
  strangler-fig — cambiar el productor sin tocar a los consumidores. **Qué pasaría si
  desapareciera hoy:** 4 módulos dejarían de compilar (§ acoplamiento). **Cuándo debe morir:**
  cuando los consumidores hablen nativamente la forma de A (o cuando se decida que la forma de A
  *es* `ExpedienteVivo`). Es un puente **sano y temporal**, no deuda permanente.
- **Shims dentro del adaptador:** `interes_analitico` derivado de viabilidad (A no lo emite),
  recompute de `implicacion_sistemica` para preservar copy exacto, y `prospecto_id` por
  nombre (A no conoce el vínculo comercial). Son **costuras de compatibilidad** que
  desaparecen cuando el contrato de A incorpore esos campos o cuando el copy migre.
- **`sources/motor-a.ts`** — puente que mete el corpus de A en la ingesta de B. **Transicional
  por definición:** su existencia es la prueba de que aún hay dos pipelines. Muere en la F8.

---

## 8. Decisiones históricas: cuáles preservar y cuáles ya no tienen sentido

**Preservar (aciertos que sostienen la plataforma):**
- **Contrato de solo lectura A→B con tag versionado.** Evita acoplar bases y formas.
- **Determinismo + gobernanza en A** (huella reproducible, validación que bloquea). Es la
  diferencia entre "peritaje" y "opinión de LLM".
- **Gateway como frontera única.** Es el habilitador de toda la evolución (strangler-fig).
- **Motor C (comercial) en RadarHD.** La acción comercial pertenece a quien opera, no a quien piensa.
- **Bitácora reversible + kill-switch.** Trazabilidad del proceso humano.

**Ya no tienen sentido (fueron correctas en su momento, hoy son deuda):**
- **RadarHD infiere Deuda con LLM (`scoring-llm`, `dictamen.service`).** Tuvo sentido cuando A
  **no** clasificaba Deuda. Desde la actualización de frontera del 2026-07-22 (CLAUDE.md: A puede
  clasificar Deuda preliminar de forma determinista), esta decisión quedó **obsoleta**.
- **Inferencia en React** (`inference/contradiction/ritual` en componentes). Fue atajo de
  prototipo; hoy contradice "la vista no piensa".
- **Captura propia de RadarHD** (`sources/{gdelt,rss,google-news}`) — duplica los conectores de A.
- **`pipeline_comercial.py` en Motor A** — comercial en el repo del pensador. El propio CLAUDE.md
  lo reconoce como vestigial.

---

## 9. Auditoría de UX desde la arquitectura (¿la interfaz obliga el método?)

**Hallazgo (verificado):** **NO.** La navegación es de **pestañas libres**, no un wizard.
`page.tsx:64` mantiene `view` en estado local; `page.tsx:91-96` renderiza cada estación por
igualdad simple; el `Sidebar`/`TABS` permite saltar a cualquiera con `setView(id)`
(`page.tsx:107`). Las estaciones: `dashboard · radar · prospectos(Bitácora) · ventas · inteligencia
· killswitch`. Dentro de `radar`, un sub-toggle `senales/organizaciones/masivo/fondos`.

**Consecuencia metodológica:** el flujo canónico
`Observación → Selección → Expediente → Motores → DolorMap → Bitácora → Decisión` **existe como
componentes** (SenalesNuevas → OrganizacionesObservadas → Dossier → recomendación/onlife →
SeguimientoComercial), **pero la UI no lo impone**: se puede abrir la Bitácora o Kill Switch sin
pasar por el Expediente. Para un laboratorio pericial, esto es un **riesgo metodológico**: permite
"decidir" sin "peritar". No es un bug estético; es que la **arquitectura de navegación no
codifica el método**. (Recomendación en §10; **no** implica rediseño visual: puede resolverse
con guardas de estado que habiliten la Decisión solo si existe Expediente+Dictamen.)

---

## 10. Evolución hacia arquitectura modular (sin romper compatibilidad)

**Principio de evolución:** *strangler-fig sobre contrato estable.* Nunca se reescribe un
consumidor; se cambia el productor detrás de un contrato que no se mueve. Ya funcionó en Fases 2–4.

**Secuencia por responsabilidad (no por archivo), ordenada por dependencia y menor riesgo:**

1. **Cerrar BC-3 en la vista (F5).** Publicar en A (o gateway) índice de Deuda + contradicciones +
   ritual con la forma que consume `IntelligencePanel`; el componente pasa a solo-render. Riesgo
   bajo-medio, alto valor de principio. Al quedar sin importadores, los 3 engines se deprecan.
2. **Unificar el Dictamen (F6).** Declarar canónico el determinista (Motor-A-fed); retirar
   `dictamen.service` (LLM V3). Elimina una duplicación **divergente**.
3. **Crear el contrato faltante `A: clasificar → Deuda/ICP` (F7).** Es la pieza que hace posible
   todo lo demás: RadarHD delega la clasificación en A en vez de usar LLM. Retira `scoring-llm`
   del camino de captura. Colapsa la duplicación **divergente** #1.
4. **Colapsar la captura (F8).** Si A cubre las fuentes, retirar `sources/*` y `engines/radar`;
   los paneles que hoy leen `senal_radar` pasan al corpus de A. **Recién aquí** `concentrador.ts`
   y `senal_radar/observacion` quedan sin razón de ser.
5. **Extraer tipos de dominio (F9a).** Sacar `Curaduria/Inferencia/…` de `concentrador.ts` a un
   paquete de tipos: rompe la dependencia **accidental** #3 sin coste de runtime (tsc lo verifica).
6. **Separar híbridos (F9b).** Partir `ecosistema.service` (contexto ⟂ fingerprint) y consolidar
   `expedientes.service` como adaptador único nombrado como tal.
7. **Codificar el método en la navegación (F10, opcional).** Guardas de estado, **sin** cambiar
   estilos: la Decisión/Sprint solo se habilita si existe Expediente + Dictamen. Convierte el
   método en invariante de la plataforma.
8. **Limpieza de coherencia (F10).** Deprecar `pipeline_comercial.py` en A; unificar naming
   (`Inteligencia*`, `dictamen*`); versionar el cron (`vercel.json`); decidir el destino del
   `sqlite.adapter` móvil (un solo modelo o descartarlo).

**Compatibilidad garantizada:** cada paso mantiene estable el contrato `ExpedienteVivo`/`Dossier`
y el tag `motor_a.corpus.v1`. La UI no cambia de forma; cambia **quién produce** detrás del gateway.

---

## Cierre — la única frase que resume la evolución

> **Hoy hay dos motores que piensan y una vista que también piensa. La plataforma estará
> integrada cuando exista un solo productor de inteligencia (Motor A), un solo adaptador de
> forma (el gateway), y todo lo demás — RadarHD — solo consuma, componga lo comercial, opere y
> registre. La herramienta para lograrlo (gateway + strangler-fig) ya existe y ya se probó.**

---

### Anexo — límites de esta auditoría (honestidad)
- Programación real del cron: **[NO VERIFICADO]** (no hay `vercel.json`; se configura en Vercel).
- Integración del `sqlite.adapter.ts` móvil: **no existe en el repo** (código propuesto).
- Consumidores exactos de `pipeline_comercial.py` en `app.py`: no re-verificados en esta pasada.
- Comportamiento línea a línea de cada engine: auditado por headers, imports, firmas y contratos,
  no full-read exhaustivo.
