# Especificación Arquitectónica Canónica de RadarHD
### Documento de referencia oficial · Laboratorio de Antropología de la Innovación · Hamaca Digital
### v1.0 — Contrato de arquitectura para todo desarrollo futuro

> **Naturaleza dual del documento.** Contiene dos registros claramente separados:
> - **[ACTUAL]** — reconstrucción del sistema tal como está, anclada a evidencia del
>   repo (`archivo:línea`). Auditoría de solo lectura; no se modificó código.
> - **[CANÓNICO]** — norma prescriptiva: cómo DEBE comportarse RadarHD. Es el contrato
>   contra el cual se valida toda funcionalidad, refactor o módulo nuevo.
> Lo no comprobable se marca **[NO VERIFICADO]**.

---

# PARTE I — MODELO OPERATIVO RECONSTRUIDO  [ACTUAL]

## I.1 · Las pantallas (propósito, insumo, producto, decisión que habilita/impide)

Navegación real: `page.tsx` mantiene 6 estaciones de **libre navegación** (`page.tsx:64,91-96`)
+ un sub-toggle dentro de "radar" (`senales/organizaciones/masivo/fondos`). `Sidebar.tsx`
define OTRAS 4 vistas y **no es importado por `page.tsx`** → navegación duplicada/legacy.

| Pantalla | Propósito metodológico | Pregunta del laboratorio | Consume | Produce | Habilita | Debe impedir | La alimenta | Depende de ella | Si desaparece |
|----------|------------------------|--------------------------|---------|---------|----------|--------------|-------------|-----------------|---------------|
| **Dashboard** | Monitoreo del estado global | "¿Cómo va el embudo?" | `/api/dashboard/metricas` (senal_radar) + KPIs seguimiento | Vista agregada | Navegar a Bitácora | Decidir sin peritar | métricas + kpisComerciales | nadie (hoja) | Se pierde la vista panorámica |
| **SenalesNuevas** (radar) | **Cribado** de señales crudas | "¿Esta señal merece expediente?" | `/api/radar/senales` (nueva), `/api/radar/run` | señal → `confirmada`/`descartada`; **crea Prospecto 'Detectado'** | Confirmar/Descartar | Confirmar con Peritaje Activo (423) | ejecutarRadar → senal_radar | Prospectos/Bitácora | Sin puerta de entrada al pipeline |
| **OrganizacionesObservadas** | **Peritaje científico** (Expediente Vivo) | "¿Qué Deuda Cultural sostiene la evidencia?" | Motor A: `/organizaciones[/id]`, `/drift`, `/onlife` | Vista de peritaje (read-only) | Leer dossier, abrir Drift/Onlife | Editar/inferir en cliente | gateway → Motor A | nadie (lectura) | Se pierde el peritaje científico |
| **InteligenciaEcosistemica** | Lectura macro | "¿Qué patrones comparte el ecosistema?" | Motor A `/ecosistema/dashboard` | Dashboard ecosistémico | Contextualizar | Interpretar localmente | gateway → Motor A | nadie | Se pierde la mirada macro |
| **RecomendacionesEstrategicas** | Traducir peritaje → acción | "¿Qué producto y a quién?" | `/api/radar/oportunidades` (Motor C sobre A) | Recomendación (incl. Sprint Fundacional) | Proponer Sprint | Ejecutar venta sin dictamen | recomendacion.service | Bitácora | Sin puente inteligencia→comercial |
| **Prospectos** (Bitácora) | **Operación del pipeline** | "¿En qué fase está cada expediente?" | pipeline: `/api/prospectos`, `/api/cadencia`, `/api/decisores`, `/api/email-decisor`, `/api/enriquecer`, `/api/sow`, `/api/radar/buscar-uno`, `/api/informes` | avance de `EstadoPipeline`; Kill Switch | Avanzar estado, congelar (Peritaje) | Avanzar sin verificación/liminal | prospecto (senal_radar) + engines/scoring (**en cliente**) | SeguimientoComercial, KillSwitch | Sin operación comercial |
| **SeguimientoComercial** (ventas) | **Bitácora hacia el Sprint** | "¿Cómo avanza la venta del Sprint?" | `/api/seguimiento` (seguimiento_comercial) | filas: reunión, `sprint_vendido`, monto | Registrar avance/venta | — | kpisComerciales (**en cliente**) | Dashboard (embudo) | Sin registro del proceso |
| **KillSwitchHistory** | Auditoría de frenos | "¿Qué expedientes se detuvieron y por qué?" | `/api/kill-switch` (kill_switch_log) | Historial reversible | Revisar/reactivar | — | prospecto PATCH | nadie | Sin trazabilidad del freno |
| **DictamenPanel** | Motor pericial **(LLM V3)** | "¿Qué contradicción estructural hay?" | `/api/dictamen` (**LLM**) | dictamen 15 campos | Emitir dictamen comercial | — | dictamen.service (LLM) | Prospecto | ⚠ Duplica el dictamen de A |
| **DriftPanel** | Motor de drift narrativo | "¿Diverge el discurso de la conducta?" | `/api/drift` (LLM) | drift | Ver drift | — | drift.service | Prospecto | Se pierde el drift comercial |
| **Inteligencia** | Vista de prospectos | "¿Qué sé de mis prospectos?" | `/api/prospectos` | Lista/inteligencia | Explorar | — | prospecto | nadie | Vista redundante |
| **IntelligencePanel** | **Índice de Deuda (en React)** | "¿Cuánta Deuda hay?" | `engines/inference/contradiction/ritual` (**cliente**) | índice Deuda, contradicciones, ritual | Explorar | ⚠ **infiere en la vista** | engines locales | nadie | Deja de violar BC-3 |

**Clasificación exploración vs decisión [ACTUAL]:**
- **Exploración:** Dashboard, OrganizacionesObservadas, InteligenciaEcosistemica, Inteligencia, DriftPanel, IntelligencePanel.
- **Decisión:** SenalesNuevas (confirmar/descartar), Prospectos (avanzar estado/Kill Switch), RecomendacionesEstrategicas (proponer producto), SeguimientoComercial (registrar venta), DictamenPanel (emitir).

## I.2 · Transiciones entre pantallas

| Transición | Evento | Estado origen | Estado destino | Datos que viajan | Validación | Restricción metodológica |
|------------|--------|---------------|----------------|------------------|------------|--------------------------|
| Radar → confirmar | click "Confirmar" | señal `nueva` | Prospecto `Detectado` | señal→dictamen Capa 0 (decisor, ICP, síntoma, relato) | **423 si Peritaje Activo** (`senales/[id]:41-49`) | Congelamiento (un peritaje a la vez) |
| Radar → descartar | click "Descartar" | señal `nueva` | señal `descartada` | id | — | Reversible |
| Prospecto → Siembra | PATCH estado | `Detectado` | `Búnker/Enviado/…` | estado, contacto | **requiere verificación** (`scoring.ts:93`) | No outreach sin contacto verificado |
| Prospecto (C) → cadencia | PATCH estado | `Detectado` (monitoreo pasivo) | (bloqueado salvo Detectado/Kill Switch) | — | `esMonitoreoPasivo` (`prospectos/[id]:78`) | Señales C no entran a venta |
| Respuesta → cualificar | PATCH accion_liminal | `Respuesta` | `Silencio/Call Activa/Kill Switch` | `AccionLiminal` (defensa/curiosidad/receptividad) | `clasificarCualificacionLiminal` (`scoring.ts:97`) | Curiosidad sin dolor → vuelve a cadencia |
| Cualquiera → Kill Switch | PATCH estado=Kill Switch | * | `Kill Switch` | fecha, razón | **razón obligatoria** salvo defensa (`prospectos/[id]:98`) | Freno auditado + reversible |
| Bitácora → venta | POST seguimiento | Prospecto activo | fila seguimiento | reunión, sprint_vendido, monto | empresa obligatoria | Registro del Sprint |

## I.3 · Recorrido completo de un expediente (9 etapas) [ACTUAL, con brechas]

1. **Captura de señal** — `radar/run|cron` → `ejecutarRadar` (scrape GDELT/RSS/GNews/Motor A + **LLM scoring-llm**) → `senal_radar` estado `nueva`. **⚠ La clasificación de Deuda ocurre AQUÍ, en RadarHD, con LLM.**
2. **Investigación automática** — en la misma detección: `decisor-hunter`, `dominio`, `email-finder`; se arma un **"dictamen Capa 0"** (LLM). No es Motor A.
3. **Creación del Expediente** — `confirmar` señal → `prospecto` `Detectado` (arrastra el dictamen Capa 0). **Guard: congelamiento**. → Nace el **linaje comercial** (Prospecto).
4. **Ejecución de motores** — **dos conjuntos desacoplados:** (a) *comercial* sobre el Prospecto: DictamenPanel (LLM), DriftPanel, enriquecer, cadencia, decisores/email, SOW; (b) *científico* sobre la Organización Observada: Motor A (organizaciones/[id], onlife, drift). **⚠ No comparten id ni se cruzan.**
5. **Construcción de DolorMap®** — **[BRECHA]** no existe artefacto: `dolormap: null` en el Dossier; "Sprint Fundacional DolorMap®" es un **producto recomendado**, `hipotesis_dolormap` viene de Onlife. No hay pantalla ni paso que "construya" el DolorMap.
6. **Bitácora** — el Prospecto avanza `EstadoPipeline`; `SeguimientoComercial` registra reunión/sprint/monto.
7. **Decisión del laboratorio** — `seleccionarProducto → 'Sprint Fundacional DolorMap®'` (si viabilidad Alta); el humano avanza el estado.
8. **Activación de Sprint Fundacional** — estado `Peritaje Activo` (**congela el pipeline**) y/o `seguimiento.sprint_vendido + monto`.
9. **Cierre y aprendizaje** — `Kill Switch` (terminal, reversible vía `Reactivación`). **[BRECHA]** el resultado (vendido/muerto) **NO se reporta a Motor A** (grep de feedback→A vacío): **no hay loop de aprendizaje A←B.**

## I.4 · Máquina de estados del Expediente comercial (Prospecto) [ACTUAL]

Estados (`types/index.ts:4-16`): `Detectado · Búnker · Enviado · Respuesta · Silencio ·
Call Activa · SOW Emitido · Peritaje Activo · Reactivación · Kill Switch`.

```
                  (confirmar señal; BLOQUEADO si hay Peritaje Activo)
                                     │
                                     ▼
                                [Detectado] ──(monitoreo pasivo C: solo aquí o Kill Switch)
                                     │  requiere verificación de contacto
                                     ▼
                    [Búnker]→[Enviado]  ── (fase Siembra / cadencia)
                                     │
                                     ▼
                                [Respuesta] ──cualificación liminal──▶ defensa→[Kill Switch]
                                     │                                curiosidad→[Silencio]→(cadencia)
                                     ▼                                receptividad→[Call Activa]
                               [Call Activa]
                                     ▼
                              [SOW Emitido]
                                     ▼
                            [Peritaje Activo] ← CONGELA todo el pipeline (invariante global)
                                     ▼
                    [Reactivación]        [Kill Switch] (razón obligatoria; log; reversible)
```

**Guardas VERIFICADAS en código (no inferidas):**
- **G1 · Congelamiento global:** con un `Peritaje Activo`, no se confirman señales nuevas
  (`senales/[id]:41-49`, 423) ni se cambia el estado de otros prospectos (`prospectos/[id]:48-51`).
- **G2 · Monitoreo pasivo:** señales C solo `Detectado`/`Kill Switch` (`prospectos/[id]:78`).
- **G3 · Verificación previa a Siembra:** entrar a `Búnker/Enviado/Respuesta/Silencio` requiere
  verificación (`scoring.ts:93-94`).
- **G4 · Cualificación liminal:** salir de `Respuesta` exige `AccionLiminal` (`scoring.ts:97-106`).
- **G5 · Kill Switch trazable:** requiere fecha+razón salvo defensa; se registra en
  `kill_switch_log` (`prospectos/[id]:98,149-153`).

**[NO VERIFICADO]:** el grafo exacto `Enviado→Respuesta→Call Activa→SOW Emitido→Peritaje` no
tiene guardas explícitas de transición en el código leído (más allá de G1–G5); el orden se
infiere del enum + la cadencia. **No se afirma como regla dura.**

## I.5 · ¿La UX obliga la metodología? [ACTUAL — veredicto]

**Parcialmente, y del lado equivocado.** El **backend comercial** SÍ codifica el método
(G1–G5). Pero:
- **La navegación no lo hace:** 6 pestañas libres (`page.tsx:107`); se puede abrir Bitácora,
  Ventas o Kill Switch sin pasar por el Expediente científico.
- **Los dos linajes están desacoplados:** se puede avanzar un **Prospecto** comercialmente sin
  que exista el **peritaje científico** (Organización Observada / DolorMap) de esa entidad,
  porque son objetos distintos sin id compartido. → **Atajo metodológico: "vender sin peritar".**
- **El DolorMap® no es un gate:** no hay paso que exija construirlo antes de decidir el Sprint.
- **El dictamen que seeda el Prospecto es el LLM Capa 0**, no el dictamen determinista de A.

**Deuda de diseño documentada (atajos que comprometen el rigor):**
- **DD-1:** navegación libre permite decidir sin peritar.
- **DD-2:** linaje comercial (Prospecto) independiente del linaje científico (Organización A).
- **DD-3:** DolorMap® ausente como artefacto obligatorio.
- **DD-4:** dictamen comercial = LLM, no Motor A.
- **DD-5:** sin loop de aprendizaje del cierre hacia Motor A.

---

# PARTE II — ARQUITECTURA OPERATIVA OBJETIVO (Target Operating Model)  [CANÓNICO]

> Cómo DEBE comportarse RadarHD para que la experiencia **haga cumplir** el método.
> No es rediseño visual: son invariantes de comportamiento y guardas de estado.

### II.1 Máquina de estados canónica del Expediente (unificado)
El "Expediente" debe ser **un solo objeto** con dos facetas (científica y comercial) sobre la
**misma identidad**. Ciclo de vida canónico:
`Observado → Peritado → Con-DolorMap → En-Bitácora → Decidido → Sprint-Activo → Cerrado(Kill/Éxito) → Aprendido`.
El linaje comercial actual (`EstadoPipeline`) se **subordina** a este ciclo: la cadencia
comercial solo puede correr sobre un Expediente que ya está **Peritado**.

### II.2 Acciones permitidas por estado (canónico)
- **Observado:** ver evidencia, pedir peritaje a Motor A. *Prohibido:* contactar, vender.
- **Peritado:** ver dictamen (de A), construir DolorMap. *Prohibido:* vender sin DolorMap.
- **Con-DolorMap:** proponer producto, entrar a Bitácora. *Prohibido:* saltarse la Bitácora.
- **En-Bitácora / Decidido:** avanzar cadencia (con G2–G4). *Prohibido:* segundo Peritaje Activo (G1).
- **Sprint-Activo:** ejecutar Sprint; congela el pipeline. *Prohibido:* abrir otro expediente activo.
- **Cerrado / Aprendido:** registrar outcome; **reportar aprendizaje a Motor A**.

### II.3 Acciones que deben bloquearse siempre
Vender/contactar antes de Peritado; avanzar sin contacto verificado (G3); dos Peritajes Activos
(G1); Kill Switch sin razón (G5); editar/inferir Deuda en el cliente; decidir Sprint sin DolorMap.

### II.4 Qué información primero y cuál después
Orden canónico de revelación (progressive disclosure metodológico):
**1º Síntoma métrico** (evidencia observable) → **2º Hipótesis estructural** (Deuda, de A,
marcada "hipótesis a validar") → **3º Implicación sistémica** → **4º Recomendación comercial**.
Nunca mostrar la recomendación de venta antes que la evidencia y la hipótesis.

### II.5 Pantallas de exploración vs decisión (canónico)
- **Exploración (leen, no mutan):** Dashboard, Organización Observada, Inteligencia Ecosistémica, DolorMap.
- **Decisión (mutan estado, con guardas):** Cribado de señales, Bitácora, Kill Switch, Sprint.
Toda pantalla de decisión debe exponer **las guardas que aplica** y **por qué** un botón está deshabilitado.

### II.6 Eventos que provocan cambio de estado
Confirmar señal (→Observado), Peritaje de A completo (→Peritado), DolorMap construido
(→Con-DolorMap), primer contacto verificado (→En-Bitácora), decisión humana (→Decidido),
activación (→Sprint-Activo), cierre (→Cerrado), feedback a A (→Aprendido).

### II.7 Validaciones metodológicas antes de avanzar
V1 evidencia suficiente (la da la Validación Científica de A, Capa 11); V2 dictamen de A presente;
V3 DolorMap construido; V4 contacto verificado (G3); V5 un solo expediente activo (G1);
V6 cualificación liminal registrada (G4).

### II.8 Responsabilidades UX vs dominio
- **UX:** ordenar la revelación, deshabilitar lo no permitido, explicar el porqué, guiar el método.
- **Dominio (server):** decidir qué es válido (guardas), qué estado sigue, qué se persiste.
- **Invariante:** la UX **nunca** calcula Deuda/dictamen/contradicciones; solo los **muestra**.

### II.9 Principios de interacción inmutables (aunque cambie la interfaz)
- La evidencia se ve antes que la hipótesis; la hipótesis antes que la recomendación.
- Ninguna acción de decisión sin sus guardas de dominio.
- Todo freno (Kill Switch) es reversible y auditado.
- Un solo expediente en Peritaje Activo (foco pericial).
- La vista no piensa.

### II.10 Diagrama del flujo ideal (captura → cierre de Sprint)
```
Señal (Motor A captura+clasifica)
  → Cribado humano (Observado)
    → Peritaje (Motor A: dictamen determinista + Validación C11)  [Peritado]
      → DolorMap® construido (gate obligatorio)                    [Con-DolorMap]
        → Recomendación (Motor C compone: producto, decisor)
          → Bitácora (cadencia G2–G4, contacto verificado)         [En-Bitácora]
            → Decisión humana                                       [Decidido]
              → Sprint Fundacional (congela pipeline, G1)           [Sprint-Activo]
                → Cierre (éxito/Kill G5, reversible)                [Cerrado]
                  → Aprendizaje reportado a Motor A                 [Aprendido]
```

---

# PARTE III — ESPECIFICACIÓN CANÓNICA  [CANÓNICO / NORMATIVO]

## III.1 ¿Qué es RadarHD?
**Propósito:** la **capa de operación y experiencia** del Laboratorio de Antropología de la
Innovación. Convierte la inteligencia producida por Motor A en **decisiones humanas trazables**
(peritar → construir DolorMap → decidir Sprint), y opera el pipeline comercial.
**Alcance:** visualización, navegación metodológica, composición comercial (Motor C), Bitácora,
Kill Switch, Sprint Fundacional, persistencia operativa/comercial.
**Límites:** RadarHD **consume** inteligencia; **no la produce**. No es un motor de inferencia.

## III.2 ¿Qué NUNCA debe hacer RadarHD? (responsabilidades prohibidas para siempre)
1. **Inferir Deuda Cultural / ICP / hipótesis** (con LLM, reglas o en React). → siempre Motor A.
2. **Clasificar o re-interpretar la evidencia** del corpus de A.
3. **Emitir dictamen pericial propio** paralelo al de A.
4. **Calcular inteligencia en componentes** (la vista no piensa).
5. **Escribir en Motor A** ni compartir su base de datos.
6. **Permitir decisiones comerciales sin peritaje + DolorMap** previos.
7. **Duplicar la captura de fuentes** que A ya cubre.

## III.3 Arquitectura de referencia
```
Captura de evidencia ─┐
Normalización         ├─►  MOTOR A (Antrosapiens)  ── única inferencia, determinista, gobernada
Corpus (motor_a.corpus.v1)                                   │  API read-only + contratos versionados
                                                             ▼
                                                     GATEWAY (motor-a.gateway.ts)  ── frontera única
                                                             ▼
                                RADARHD ── consume · compone (Motor C) · opera · registra
                                  ├─ DolorMap®  (síntesis visual del peritaje de A)  [gate]
                                  ├─ Bitácora   (avance metodológico + comercial)
                                  └─ Sprint Fundacional  (decisión humana, congela foco)
```

## III.4 Principios arquitectónicos inmutables
1. **Toda inferencia antropológica ocurre exclusivamente en Motor A.**
2. **RadarHD nunca interpreta evidencia; solo la consume y representa.**
3. **Toda decisión metodológica es humana** (la máquina propone, el humano dispone).
4. **La UX refuerza el método** (evidencia→hipótesis→implicación→recomendación; guardas visibles).
5. **Ninguna responsabilidad existe duplicada** (una responsabilidad, un único dueño).
6. **Integración solo por contrato HTTP versionado**, dirección única A→RadarHD, sin BD compartida.
7. **Todo freno es reversible y auditado.**
8. **Un solo expediente en Peritaje Activo** (foco pericial).
9. **La vista no piensa** (cero lógica de dominio en React).
10. **El aprendizaje del cierre retorna a Motor A** (loop cerrado).

## III.5 Modelo de dominio (lenguaje ubicuo + entidades)
- **Evidencia** — hecho objetivo capturado (owner: A; contrato `motor_a.corpus.v1`).
- **Organización Observada / Expediente** — unidad de peritaje; DEBE ser identidad única que une
  la faceta científica (A) y la comercial. *(Hoy están partidas: Organización vs Prospecto.)*
- **Deuda Cultural™** — hipótesis estructural (owner exclusivo: A).
- **Dictamen** — veredicto pericial determinista (owner: A). *(Hoy duplicado por LLM V3.)*
- **DolorMap®** — síntesis del dolor cultural; **gate** entre peritaje y decisión.
- **Recomendación / Producto** — traducción comercial (Motor C): Peritaje, Sprint Fundacional, Escalabilidad.
- **Bitácora** — registro del avance metodológico y comercial.
- **Sprint Fundacional** — intervención decidida por el humano; congela el foco.
- **Kill Switch** — freno reversible y auditado.
Relaciones: `Evidencia*→Expediente 1—1 Dictamen 1—1 DolorMap →* Recomendación →1 Bitácora →0..1 Sprint`.

## III.6 Máquina de estados canónica (resumen)
Ver Parte II.1–II.3. Ciclo: `Observado→Peritado→Con-DolorMap→En-Bitácora→Decidido→Sprint-Activo→Cerrado→Aprendido`.
Invariantes: G1 (foco único), G3 (verificación), G4 (liminal), G5 (Kill trazable), + gates V2 (dictamen A) y V3 (DolorMap).

## III.7 Arquitectura de interacción
La experiencia debe: (a) revelar en orden metodológico; (b) deshabilitar acciones no permitidas y
**explicar por qué**; (c) impedir el salto "vender sin peritar" mediante gates de estado, no
mediante confianza en el usuario; (d) mantener un único expediente activo; (e) exhibir siempre la
naturaleza "hipótesis a validar" de la Deuda. La UX **guía**, el dominio **decide**.

## III.8 Contratos entre módulos
| Productor | Contrato | Consumidor | Regla |
|-----------|----------|------------|-------|
| Motor A | `motor_a.corpus.v1` (`/corpus`) | gateway | evidencia objetiva, sin Deuda; tag versionado (rompe si desconocido) |
| Motor A | `motor_a.dossier.v1` (`/dossier`) | gateway | peritaje completo |
| Motor A | Expediente Vivo (`/organizaciones[/id]`,`/drift`,`/onlife`,`/ecosistema/*`) | gateway | forma que la UI consume; A produce, RadarHD representa |
| **[CANÓNICO — a crear]** Motor A | `clasificar señal → Deuda/ICP` | captura de RadarHD | elimina el LLM local (BC-3) |
| gateway | cliente HTTP único | services/rutas | **única** puerta a A; nadie llama a A por fuera |
| expedientes.service (adaptador) | `Dossier(A) → ExpedienteVivo` | recomendacion/dictamenPericial/ecosistema/listado | adaptador **temporal** de compatibilidad |
| Motor C (RadarHD) | recomendación, dictamen pericial, cadencia, seguimiento | UI | composición comercial sobre datos de A; nunca infiere |
| **[CANÓNICO — a crear]** RadarHD | `outcome del Sprint → A` | Motor A (memoria) | cierra el loop de aprendizaje |

## III.9 Roadmap por tipo de deuda (priorizado por impacto×riesgo)
**Deuda arquitectónica (impacto alto):**
- A1 · Colapsar la inferencia de Deuda a Motor A (retirar `scoring-llm`, crear contrato `clasificar`). *(impacto máx, riesgo alto — toca ingesta viva)*
- A2 · Unificar el Dictamen en el determinista de A (retirar `dictamen.service` LLM V3). *(alto, medio)*
- A3 · Unificar los dos linajes (Organización Observada ≡ Prospecto) bajo una identidad. *(alto, alto)*

**Deuda metodológica (impacto alto en rigor):**
- M1 · Gate DolorMap® obligatorio antes de la decisión de Sprint. *(alto, medio)*
- M2 · Loop de aprendizaje: outcome del Sprint → Motor A. *(medio, medio)*
- M3 · "Vender solo sobre expediente peritado" como invariante de estado. *(alto, medio)*

**Deuda de UX (impacto medio):**
- U1 · Navegación que codifique el método (gates de estado, no wizard estético). *(medio, bajo)*
- U2 · Revelación ordenada evidencia→hipótesis→recomendación (ya presente en el Dossier; falta global). *(bajo)*
- U3 · Retirar `Sidebar.tsx` duplicado/legacy. *(bajo, bajo)*

**Deuda técnica (impacto bajo, riesgo bajo):**
- T1 · Sacar inferencia de React (`inference/contradiction/ritual`). *(bajo, medio)*
- T2 · Extraer tipos de `concentrador.ts` (runtime-neutral). *(bajo, bajo)*
- T3 · Separar `ecosistema.service` (contexto ⟂ fingerprint). *(bajo, bajo)*
- T4 · Versionar el cron (`vercel.json`); decidir destino del `sqlite.adapter` móvil. *(bajo)*
- T5 · Deprecar `pipeline_comercial.py` en Motor A. *(bajo)*

**Orden recomendado:** A1 → A2 → M1 → M3 → A3 → M2 → U1 → T1 → T2/T3 → U3/T4/T5.

## III.10 Principios de evolución (reglas para todo desarrollo futuro)
1. **Contrato antes que código:** todo cambio de inteligencia se define primero como contrato de A.
2. **Strangler-fig sobre contrato estable:** se cambia el productor detrás del gateway; nunca se
   reescribe al consumidor sin necesidad.
3. **Una responsabilidad, un dueño:** antes de crear un módulo, probar que la responsabilidad no
   existe ya (si existe, se consume, no se duplica).
4. **La frontera de inferencia es sagrada:** cualquier PR que infiera Deuda fuera de A se rechaza.
5. **La UX guía el método:** toda pantalla de decisión declara sus guardas; ningún atajo silencioso.
6. **Nada se borra sin inventario de importadores** (regla probada en Fases 3–4).
7. **Validación contra esta especificación** es requisito de merge de cualquier módulo nuevo.

---

## Anexo — Límites de verificación (honestidad de la auditoría)
- Grafo exacto de transiciones comerciales intermedias: **[NO VERIFICADO]** más allá de G1–G5.
- Programación real del cron: **[NO VERIFICADO]** (no hay `vercel.json`).
- `sqlite.adapter.ts` móvil: **no existe en el repo** (propuesto).
- Consumidores exactos de `pipeline_comercial.py` en A: no re-verificados esta pasada.
- Partes I = evidencia (ACTUAL); Partes II–III = norma (CANÓNICO), fundadas en esa evidencia.
