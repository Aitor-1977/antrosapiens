# PLAN DE ACCIÓN ÓPTIMO — VALIDACIÓN PRODUCCIÓN

> Nota de origen: este documento se generó a partir del estado real verificado
> en la sesión de trabajo del 2026-08-29 (commit `740443f` en
> `claude/dynamic-search-connector-xb81v3`), no de un archivo `hiy2.docx` —
> ningún archivo llegó adjunto a esa solicitud. El contenido coincide con el
> resumen provisto porque describe los mismos hechos ya confirmados en esa
> sesión.

## 1. Diagnóstico de bloqueo

El código está listo, no el proceso. `evidencia_clasificada.expediente_id`
ya admite `NULL` en producción (migración automática confirmada corriendo
sin errores tras el deploy), la lógica de persistencia en
`clasificacion_store.py` ya respeta esa nulabilidad, los 3 tests de
`clasificar_lote` relevantes pasan, y la doctrina ("una evidencia sin
organización no se descarta, nunca se inventa una organización") ya quedó
escrita en `CLAUDE.md`. No falta escribir ni corregir nada de eso. Lo que
falta es una sola pieza de información operativa: **con qué base de datos
Neon estamos hablando en realidad cuando ejecutamos algo "en producción".**

La información faltante es el identificador exacto (proyecto Neon, rama, y
qué variable de entorno de Vercel resuelve a él para el entorno
**Production**) de la base que usa `antrosapiens-api-pro` ahora mismo. Hoy
se intentó dos veces conectar desde Termux usando valores tomados de
Vercel, y ninguno era el correcto: uno no tenía ninguna evidencia del
conector de Tavily, el otro ni siquiera tenía columnas que sabemos existen
en producción (`empresa_mencionada`). El agente no tiene acceso a la API de
Vercel para esta cuenta (404 en `get_project`, límite de permisos/visibilidad
que no se puede resolver desde la terminal) — por eso esto requiere
inspección manual.

Avanzar sin esa certeza tiene dos riesgos concretos, no hipotéticos: (1)
**corromper o escribir sobre una base equivocada** — ya ocurrió dos veces
hoy que una variable con nombre plausible resultó ser la base incorrecta;
si en vez de solo leer se hubiera escrito ahí, el daño habría sido real y
en una base que no es la que consume la app; (2) **gastar cuota de Tavily
en vano** — aunque el script de reprocesamiento no vuelve a consultar
Tavily (usa evidencia ya capturada), cualquier paso posterior de este plan
que sí lo haga (activar la automatización) sobre la base equivocada
produciría evidencia huérfana en un lugar que nadie lee, sin avisar del
error hasta mucho después.

## 2. Protocolo para Mario

**Instrucción 1 — Vercel → proyecto `antrosapiens-api-pro` → pestaña
"Storage"** (junto a "Deployments", "Analytics", "Settings" en la
navegación del proyecto — no dentro de Settings).
- Si ahí aparece un recurso Neon conectado: anota **nombre del proyecto
  Neon, nombre de la rama (branch), y para qué entorno está vinculado**
  (Production / Preview / Development). Esta es la fuente más confiable
  porque muestra explícitamente el vínculo real, no un nombre de variable
  que alguien pudo escribir a mano.

**Instrucción 2 — si "Storage" aparece vacío**, ve a Settings →
Environment Variables.
- Busca `HD_DATABASE_URL`, `DATABASE_URL` y `POSTGRES_URL`.
- Para **cada una** que exista, ábrela y revisa si la casilla
  **"Production"** aparece marcada (no te quedes con el nombre solo —
  hoy la confusión fue exactamente ahí).
- El código (`hd_scraper/config.py:_resolve_database_url`) revisa
  `HD_DATABASE_URL` **antes** que `DATABASE_URL`/`POSTGRES_URL` — si
  `HD_DATABASE_URL` existe y está marcada para Production, esa es la que
  manda, sin importar que las otras también existan.

**Instrucción 3 — qué compartir de vuelta (nunca la cadena completa):**
- `"El proyecto Neon se llama [X], rama [Y], vinculado a Production"`, **o**
- `"La variable activa en producción es HD_DATABASE_URL"` (o el nombre que
  corresponda).
- No pegues la cadena de conexión completa en el chat — con el nombre del
  proyecto/rama o el nombre de la variable activa basta para que el
  desarrollador la use él mismo desde donde tenga acceso, sin que quede
  expuesta en texto plano en la conversación.

## 3. Preparación del script de reprocesamiento

Mientras Mario verifica, el desarrollador prepara — **sin ejecutar** —
`scripts/reprocesar_96_evidencias.py`. Ya está escrito (ver archivo en el
repo) y reutiliza `clasificacion_store.clasificar_lote` tal cual existe hoy
— no reimplementa la cascada de clasificación ni la lógica de persistencia.
Hace, en este orden:

1. Detecta el host de la base activa (a partir de la misma resolución que
   usa el resto de la app: `HD_DATABASE_URL` → `DATABASE_URL` →
   `POSTGRES_URL` → `POSTGRES_PRISMA_URL`) y lo muestra en pantalla.
2. **Verificación de seguridad**: si se pasa `--host-esperado <host>`,
   aborta inmediatamente si no coincide. Siempre, además, pide escribir
   literalmente `SI` en consola antes de escribir nada (se salta esta
   confirmación solo en `--dry-run`, que no escribe).
3. Toma una foto ANTES: evidencias totales del conector
   `busqueda_dinamica_founder`, cuántas ya tienen fila en
   `evidencia_clasificada`, cuántas con/sin `expediente_id`, distribución
   por `tipo_epistemologico` — la imprime y la deja en el log.
4. Carga las evidencias YA capturadas de ese conector (no dispara ninguna
   búsqueda nueva contra Tavily — es una lectura sobre `evidencias`, tabla
   que ya existe).
5. Llama a `clasificar_lote(db, aplicar=not dry_run)` — el mismo módulo que
   ya usa `scripts/clasificar_evidencia.py` en producción. Respeta
   `expediente_id = NULL` y `organizacion_mencionada = NULL` porque esa
   lógica ya vive en `clasificacion_store.py`, sin nada nuevo aquí.
6. **No importa ni llama a `promocion_candidatos.py`** en ningún punto del
   archivo.
7. Toma una foto DESPUÉS (mismas métricas que el paso 3) y genera el
   informe con las 10 preguntas de validación (ver `_preguntas_de_validacion`
   en el script).

**Comandos de ejecución** (para cuando Mario confirme la base — no antes):

```bash
# Simulación: no escribe nada, solo muestra el plan y las fotos antes/después
python -m scripts.reprocesar_96_evidencias --dry-run

# Ejecución real, con verificación de host esperado
python -m scripts.reprocesar_96_evidencias --host-esperado "<host confirmado por Mario>"
```

## 4. Plan de ejecución por fases

- **Fase 0** — Mario confirma la base (Protocolo, sección 2). Este
  documento se actualiza con la respuesta antes de avanzar a Fase 1.
- **Fase 1** — `python -m scripts.reprocesar_96_evidencias --dry-run`.
  Revisar la foto ANTES y el plan que imprime; nada se escribe todavía.
- **Fase 2** — `python -m scripts.reprocesar_96_evidencias --host-esperado "<host>"`,
  monitoreando la salida en tiempo real (el script imprime cada paso, no
  hay logging silencioso).
- **Fase 3** — Validación POST: correr las consultas SQL de las 10
  preguntas (el script ya las imprime, pero para auditoría independiente
  se pueden correr a mano contra la misma base).
- **Fase 4** — Si el resultado coincide con lo esperado (evidencias
  persistidas, 0 organizaciones inventadas, 0 candidatos promovidos),
  declarar **"PIPELINE VALIDADO"** y cerrar este documento.

## 5. Criterios de parada y contingencia

- **Si `organizacion_mencionada` NO es `NULL` para alguna evidencia que
  debería no tener organización identificable** (patrón fuerte de
  aposición/fundación ausente en el texto): **detenerse y reportar** —
  no continuar el lote, no promover nada, investigar esa fila puntual
  antes de seguir. Sería indicio de una regresión en
  `_detectar_organizacion_mencionada`, no algo que se deba "corregir a
  mano" sobre la marcha.
- **Si alguna evidencia de las capturadas originalmente no aparece en la
  foto DESPUÉS con una fila en `evidencia_clasificada`**: eso es pérdida
  de evidencia, exactamente el problema que este trabajo existe para
  cerrar. Detenerse, reportar cuántas y cuáles, no intentar "completar"
  el lote con una segunda corrida hasta entender la causa.
- **Rollback**: `clasificar_lote` es aditivo — solo hace `INSERT`, nunca
  `UPDATE` ni `DELETE` sobre `evidencias` ni `evidencia_clasificada` (ver
  docstring del propio módulo). Si algo sale mal, el rollback es borrar
  las filas de `evidencia_clasificada` que el script acaba de insertar
  (identificables por su `id` más reciente o por un rango de tiempo), NUNCA
  tocar `evidencias`:
  ```sql
  -- Solo si Fase 2 falló y hay que revertir: ajustar el rango de fecha/hora
  -- al momento real de la corrida antes de ejecutar.
  DELETE FROM evidencia_clasificada
  WHERE creado_en >= '<timestamp de inicio de la corrida>';
  ```
  Este `DELETE` no se ejecuta como parte del script — es manual, deliberado,
  y solo ante contingencia real.
