# Fase 1 — Auditoría integral de AntroLabsHD (identificación + expediente de prospectos)

> Auditoría de solo lectura, según el marco de 15 secciones entregado por el
> operador. **No se modificó código, no hubo commit, no hubo push.** Fuentes:
> código real de `antrosapiens` (Motor A) y `radarhd` (RadarHD/Motor B-C),
> API de producción (`antrosapiens-api-pro.vercel.app`, 5204 evidencias
> reales), y la auditoría de accesibilidad ya completada hoy mismo
> (`AUDITORIA_MATERIAL_BLOQUEADO_2026-09-14.md`, que este documento
> referencia en vez de repetir).

---

## A. Mapa real del flujo actual

```
FUENTES (Google News RSS, GDELT, RSS fijos, Job boards)
   ↓
INGESTA (hd_scraper/connectors/*.py)
   ↓
EVIDENCIA (tabla `evidencias`, validada por hd_scraper/validation/validator.py)
   ↓
CLASIFICACIÓN EPISTEMOLÓGICA (clasificacion_epistemologica.py → evidencia_clasificada)
   ↓
CURADURÍA / ANÁLISIS (analisis.py, rule_engine.py, curaduria.py, dictamen.py — ver hallazgo J.1)
   ↓
CASO ORGANIZACIONAL (expediente_vivo.py, candidato.py, expedientes_candidatos)
   ↓
PIPELINE COMERCIAL (pipeline_comercial.py — ver hallazgo G.1, viola la frontera)
   ↓
API (/expedientes, /evidencias, /corpus, /dossier)
   ↓
RADARHD (motor-a.gateway.ts → engines/concentrador.ts — ver hallazgo G.2)
   ↓
ANDROID (Capacitor de RadarHD; también android_v3 de antrosapiens, WebView directo a la API)
   ↓
MATERIAL QUE VE MARIO
```

Esta cadena real **difiere del canon documentado en `CLAUDE.md`** en un punto
estructural (ver J.1): existe una capa intermedia completa (Capas 6, 7, 9, 10
y `dictamen.py`) que `CLAUDE.md` no menciona.

---

## B. Componentes involucrados (inventario, no exhaustivo de líneas)

| Capa | Módulo | Documentado en `CLAUDE.md` |
|---|---|---|
| Ingesta | `connectors/{google_news,gdelt,rss_fijos,job_boards}.py` | Sí |
| Validación | `validation/validator.py` | Sí |
| Clasificación epistemológica | `clasificacion_epistemologica.py` + `clasificacion_store.py` | Sí |
| Análisis / scoring | `analisis.py`, `engine/rule_engine.py` | Sí |
| Receptividad (triage Capa 0) | `receptividad.py` | Sí |
| Lectura estructural (pre-peritaje) | `lectura_estructural.py` | Sí |
| Síntesis estructural | `sintesis.py`, `nvidia_parser.py` | Sí |
| Validación científica / Gobernanza | `validacion_cientifica.py`, `gobernanza.py`/`gobernanza_store.py` | Sí |
| Memoria/Comparador/Predictivo/Observatorio/Publicador/Laboratorio | Capas 13-19 | Sí |
| **Drift Narrativo** | `drift.py`, `drift_compare.py` (**Capa 6**) | **No** |
| **Onlife** | `onlife.py` (**Capa 7**) | **No** |
| **Pipeline Comercial** | `pipeline_comercial.py` (**Capa 9**) | **No** |
| **Curaduría Antropológica** | `curaduria.py` (**Capa 10**) | **No** |
| **Dictamen** | `dictamen.py` (sin número de Capa visible) | **No** |
| Caso organizacional | `expediente_vivo.py`, `candidato.py` | Parcial (una mención de pasada) |
| RadarHD — gateway | `motor-a.gateway.ts` | N/A (repo RadarHD) |
| RadarHD — concentrador/curaduría local | `engines/concentrador.ts` | N/A (repo RadarHD, pero viola su propio canon `0004`) |

---

## C. Qué funciona (evidencia a favor, no solo señalamientos)

1. **Dedup real y determinista.** `hash_dedup = sha256(empresa + URL normalizada)`,
   `ON CONFLICT DO NOTHING` en `prospectos` y en `evidencias` — verificado en
   código, no supuesto.
2. **La cascada de atribución epistemológica (`clasificacion_epistemologica.py`)
   es rigurosa y ya implementa exactamente la doctrina que pide la Sección V
   del marco del operador**, aunque con otros nombres: `senal_primaria_autodeclaracion`,
   `senal_primaria_huella_practica`, `corroborante`, `contextual` — la
   "REGLA DURA" (ante ambigüedad, cae a `contextual`, nunca se fuerza hacia
   arriba) es literalmente el principio "DATO/INFERENCIA/HIPÓTESIS/VACÍO" que
   pide la Sección V, ya implementado y con tests. **No existe en el código
   real la taxonomía textual "ENUNCIACIÓN BIOGRÁFICA/CONFESIONAL, FRICCIÓN
   SITUACIONAL ONLIFE, EVIDENCIA ESTRUCTURAL, INSUFICIENTE/RUIDO"** que
   describe la Sección V del marco — o es una taxonomía deseada todavía no
   escrita, o corresponde a otro documento que no está en este repo. Lo
   marco aquí como discrepancia a resolver contigo, no como código faltante
   que yo deba inventar.
3. **Identidad organizacional para los 4 conectores de Fase 1 es estructural
   (declarada por el operador), no inferida** — evita exactamente la confusión
   IDENTIDAD ≠ RELACIÓN ≠ CONTEXTO que pide la Sección III, porque el
   operador declara el objetivo de la corrida (`QuerySpec`), el conector no
   adivina de quién habla la noticia.
4. **Para el conector de descubrimiento amplio (Tavily,
   `busqueda_dinamica_founder`), el riesgo de esa misma confusión SÍ existe y
   YA está mitigado con reglas explícitas y documentadas**: `organizacion_mencionada`
   solo se llena con "patrón fuerte de aposición/fundación en primera persona"
   (soy fundador de X, fundé X), nunca con la primera palabra capitalizada
   como heurística de respaldo — está en el propio `CLAUDE.md` y confirmado en
   `clasificacion_epistemologica.py`. Esto es la Sección III bien resuelta en
   una parte del sistema.
5. **`motor-a.gateway.ts` en RadarHD es disciplinado**: es la única puerta a
   Motor A, sin cálculo local, con validación de contrato (`validarContratoCorpus`)
   que rompe ante un tag desconocido en vez de ingerir formas no verificadas.

---

## D-F. Qué falla, dónde se pierde evidencia/información

**Remito al detalle completo ya producido hoy** en
`AUDITORIA_MATERIAL_BLOQUEADO_2026-09-14.md` (secciones A-D de ese documento),
que cubre con evidencia de código y de datos reales:

- `hd_scraper/connectors/google_news.py:127` — `url_fuente` es el wrapper
  `news.google.com/rss/articles/...` sin resolver, nunca la URL del medio.
- `hd_scraper/connectors/google_news.py:129` — `cita_textual` es el `<title>`
  del RSS (titular), no una cita del cuerpo — el propio comentario del código
  lo reconoce.
- Verificado sobre 1060 evidencias reales muestreadas: **100%** con wrapper
  sin resolver, **100%** de una submuestra de 500 con `resumen_fuente` vacío
  (el campo creado específicamente para mitigar esto).
- GDELT y RSS fijos (los otros 2 de los 4 conectores) no aparecieron en
  ninguna de las tres muestras — pregunta abierta, no conclusión, sobre si
  están corriendo con aporte real al corpus visible.
- **No hay pérdida entre backend y frontend**: confirmado en
  `SenalesNuevas.tsx:313-320`, renderiza `cita_textual`/`url_fuente` literal.
  La pérdida es 100% de ingesta.

**Nuevo hallazgo de hoy, no cubierto en el documento anterior:** el mismo
patrón de "cita = titular" se repite estructuralmente en cualquier evidencia
capturada por `google_news.py`, que — según la muestra — parece ser el
conector dominante o exclusivo en el corpus visible ahora mismo, pese a que
Fase 1 declara 4 conectores completos.

---

## G. Dónde aparece interpretación antropológica indebida

### G.1 — `hd_scraper/pipeline_comercial.py` (Motor A) — violación directa y sin ambigüedad

`CLAUDE.md` de este mismo repo dice, textualmente, en su sección "Exclusivo
de RadarHD (JAMÁS aquí)": **"El pipeline comercial (seguimiento, contacto
ejecutado, envíos)"**. `pipeline_comercial.py` (266 líneas, "Capa 9") existe
en Motor A, activo, con etapas explícitas `Observación → Vigilancia →
Peritaje → DolorMap → Alianza → Cerrado`, donde "Alianza" se define como
"propuesta o conversación activa con la organización" y "Cerrado" como
"relación formalizada (ganado o descartado)" — lenguaje de pipeline de
ventas, dentro de Motor A.

Esto **no es un hallazgo nuevo de esta sesión**: el propio roadmap de RadarHD
(`MIGRACION_ARQUITECTURA_1_0.md`, ítem **T5**) ya dice *"Deprecar
`pipeline_comercial.py` en Motor A"* — es decir, el equipo de RadarHD ya sabe
que existe y que viola la frontera, y lo tiene en su lista de deuda técnica
sin ejecutar. Lo que esta auditoría aporta es que **`CLAUDE.md` de
`antrosapiens` no menciona este archivo en absoluto**, así que quien solo lea
el canon de Motor A no se enteraría de que existe.

### G.2 — `radarhd/src/lib/engines/concentrador.ts` (RadarHD) — ya documentado hoy

Confirmado y detallado función por función en el Anexo A de la spec `0009` y
en la sección E de `AUDITORIA_MATERIAL_BLOQUEADO_2026-09-14.md`:
`clasificarDeuda()` y `interpretar() → InferenciaAntropologica` generan Deuda
Cultural™ y una hipótesis antropológica **localmente en RadarHD**, activo en
producción vía `/api/radar/organizaciones` y `expedientes.service.ts`. Viola
`0004` Principio 1-2. Ya identificado como deuda A1 en `0007_ROADMAP.md` de
RadarHD, sin resolver todavía (ver Anexo A de la spec `0009` para la decisión
pendiente).

### G.3 — `hd_scraper/curaduria.py` y `hd_scraper/dictamen.py` (Motor A) — zona gris, requiere tu decisión

Ambos módulos son grandes (636 y 357 líneas), deterministas (sin IA, sin red
— confirmado en sus propios docstrings) y **producen narrativa antropológica
interpretativa**: `curaduria.py` arma una "LECTURA ANTROPOLÓGICA curada" que
responde "¿qué significa todo esto junto?" (`_lectura_antropologica`,
`_construir_narrativa`); `dictamen.py` genera "Hipótesis de Deuda Cultural
dominante" (`_generar_hipotesis`) y un ranking con `_accion_sugerida`.

**Esto no es automáticamente una violación**: `CLAUDE.md` ya autoriza
explícitamente clasificación preliminar de Deuda Cultural™ en Motor A (a
diferencia de RadarHD, donde está prohibida sin excepción). El problema es
**procedimental, no de contenido**: la sección "Frontera de Interpretación"
de `CLAUDE.md` exige que *"cualquier ampliación futura de interpretación en
este repo exige actualizar esta misma sección ANTES de escribir código"*, y
lista explícitamente los módulos autorizados (`analisis.py`,
`lectura_estructural.py`, `sintesis.py`, `nvidia_parser.py`,
`clasificacion_epistemologica.py`, `receptividad.py`). **`curaduria.py` y
`dictamen.py` no están en esa lista.** Si son anteriores a esa regla, siguen
siendo deuda de documentación; si son posteriores, son un incumplimiento
directo del propio procedimiento del repo. No determiné cuál de las dos es
sin revisar el historial de commits — lo dejo como pregunta abierta explícita,
no como veredicto.

### G.4 — `hd_scraper/onlife.py` — ejemplo de buena práctica, para contraste

Su propio docstring declara: *"Observa comportamiento, NO interpreta...
Nunca genera hipótesis ni calcula Deuda Cultural™"*. Por nombre de función
(`observar_github`, `observar_hackernews`, `observar_blog`) parece cumplir
esa promesa — es la Sección VIII bien resuelta ("la máquina SÍ puede...
mostrar evidencia", sin cruzar a interpretación). Sigue sin estar en
`CLAUDE.md`, que es un problema de documentación, no de diseño.

---

## H. Porcentaje de evidencia accesible/bloqueada

Ya medido con datos reales en `AUDITORIA_MATERIAL_BLOQUEADO_2026-09-14.md`:
**100% (1060/1060) de la muestra tiene URL sin resolver y cita = titular, no
cita real.** No repito la tabla completa aquí; ver ese documento.

---

## I. Ejemplos concretos

Ver la tabla de 10 "deberían servir pero no sirven" y 10 "mejores casos
disponibles" en `AUDITORIA_MATERIAL_BLOQUEADO_2026-09-14.md`, sección
"Resultado operativo", puntos 5-6. Ejemplo adicional para la Sección III de
este marco (identidad mal establecida, no solo accesibilidad): evidencia
`2971`, organización registrada como **"Mundi"**, y `5323`, organización
registrada como **"Global"** — ninguna de las dos es una empresa real; son
ruido de extracción de `relevance.py`/`_STOP_CAP` capturando una palabra
suelta del titular como si fuera el nombre de la organización. Esto es
exactamente el tipo de falso positivo que pide evitar la Sección III/XI.5-6,
y es independiente del problema de accesibilidad de D-F.

---

## J. Discrepancias entre canon y código

| # | Discrepancia | Severidad |
|---|---|---|
| J.1 | `CLAUDE.md` dice "Roadmap: Capas 0–18 ✅" pero no documenta las Capas 1-10 en absoluto salvo pasajes sueltos; en código existen y están activas (Drift=6, Onlife=7, Pipeline Comercial=9, Curaduría=10, más `dictamen.py` sin número visible). | **Alta** — gap de gobernanza documental sobre ~2200 líneas de código en producción. |
| J.2 | `pipeline_comercial.py` en Motor A contradice literalmente la frase "Exclusivo de RadarHD (JAMÁS aquí): El pipeline comercial" del mismo `CLAUDE.md`. | **Alta** — violación directa, ya reconocida por el otro repo (RadarHD `T5`) pero no resuelta ni documentada en `antrosapiens`. |
| J.3 | `curaduria.py`/`dictamen.py` generan interpretación antropológica (Deuda Cultural, narrativa) sin aparecer en la lista de módulos autorizados de la sección "Frontera de Interpretación" de `CLAUDE.md`. | **Media** — puede ser deuda de documentación o incumplimiento procedimental; requiere revisar cuándo se escribieron. |
| J.4 | `engines/concentrador.ts` en RadarHD contradice `0004` Principio 1-2 y está marcado como deuda A1 sin resolver en el propio roadmap de RadarHD. | **Alta** — ya documentado en la spec `0009` de la sesión anterior, sigue pendiente de decisión humana. |
| J.5 | La taxonomía "ENUNCIACIÓN BIOGRÁFICA/CONFESIONAL, FRICCIÓN SITUACIONAL ONLIFE, EVIDENCIA ESTRUCTURAL, INSUFICIENTE/RUIDO" que describe el marco del operador no existe con esos nombres en ningún archivo de ninguno de los dos repos. | **Media** — o es una taxonomía deseada a construir, o vive en un documento externo no incluido en el repo; no se puede auditar código que no existe. |
| J.6 | `google_news.py` guarda titular como `cita_textual` y wrapper de Google como `url_fuente`; no viola ninguna regla de frontera A/B, pero sí la Sección IV del marco ("una cita textual debe ser realmente textual") y la Sección VI (accesibilidad). | **Alta** — es el hallazgo operativo central, ya detallado. |

---

## Resumen para decidir el siguiente paso

No escribí ni modifiqué código. Los hallazgos con severidad "Alta" que
requieren tu decisión explícita antes de cualquier Fase 2 son, en orden de lo
más barato de corregir a lo más costoso:

1. **J.6 / D-F** (más barato): corregir la ingesta de `google_news.py` para
   resolver el wrapper y/o aceptar honestamente que el techo epistemológico
   de esa fuente es "contextual, cita = titular" — no requiere tocar
   arquitectura, solo esa conexión.
2. **J.1 / B** (documental, sin riesgo): actualizar `CLAUDE.md` para que
   documente las Capas 1-10 reales, sea cual sea su estado deseado.
3. **J.2** (requiere tu decisión): decidir si `pipeline_comercial.py` se
   retira de Motor A (siguiendo el propio roadmap `T5` de RadarHD) o si se
   re-autoriza explícitamente en `CLAUDE.md` con una nueva entrada en la
   Frontera de Interpretación, como se hizo para `receptividad.py`.
4. **J.3** (requiere tu decisión): igual que J.2, pero para `curaduria.py`/
   `dictamen.py` — legitimar con una entrada nueva en `CLAUDE.md`, o retirar/
   limitar su alcance.
5. **J.4** (ya en curso en la sesión anterior, spec `0009` Anexo A): pendiente
   de tu decisión sobre `concentrador.ts`.

No propongo todavía ningún cambio de código para ninguno de estos puntos —
eso es Fase 2, y el marco que diste pide explícitamente no avanzar ahí
mientras existan ambigüedades epistemológicas sin resolver, que es
exactamente la situación de J.2, J.3 y J.5.
