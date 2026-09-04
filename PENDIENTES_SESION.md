# Pendientes de sesión (2026-08-28)

Notas para retomar en la próxima sesión. No implementadas todavía —
solo diagnóstico y especificación.

> **Nota (2026-09-03):** commit sin cambios de lógica, únicamente para forzar
> un deploy nuevo en Vercel después de rotar `HD_INGEST_TOKEN` en Environment
> Variables — guardar la variable ahí NO dispara un deploy por sí solo; hace
> falta un push (o "Redeploy" manual) para que el runtime tome el valor
> nuevo. Ver punto 2 más abajo (endpoint temporal de reversión de "Clara").

> **Nota (2026-09-04):** segundo commit sin cambios de lógica, para forzar
> el redeploy después de corregir `HD_DATABASE_URL` — el valor apuntaba al
> proyecto Neon equivocado (`antro-labs`, confirmado con `/_debug/db?mapear_columnas=true`:
> `evidencias` con columnas de otro modelo de datos, `evidencia_clasificada`
> y `expedientes_candidatos` inexistentes). El operador identificó y
> actualizó el proyecto Neon correcto directamente en Vercel.
>
> **Incidente cerrado (2026-09-04):** `/health`, `/verificados` (7 items) y
> `/evidencias` (5204 items) confirmados en 200 con la base correcta. El
> endpoint temporal `/_debug/db` (y sus tests) se retiró del código en este
> mismo commit — ya cumplió su propósito de diagnóstico y no debía quedar
> permanentemente. Pendiente sin urgencia: reverificar que el estado de
> "Clara" (`abierto` vs `candidato`) siga correcto ahora que se conecta a
> esta base (se revirtió antes, contra un proceso que puede haber estado
> usando una conexión distinta).
>
> **Punto 1 resuelto (2026-09-04):** se volvió a ejecutar
> `GET /admin/revertir-candidato-clara` contra la base Neon ya correcta.
> `GET /verificados` confirmado en `"total":6` (bajó de 7), sin "Clara" en la
> lista de items (verificado por el operador desde el navegador y de forma
> independiente por el agente vía curl). El expediente quedó en `estado =
> 'abierto'` en la base de producción real. Punto 2 (destino del endpoint
> temporal) sigue abierto — ver más abajo.

## 1. "Clara" sigue promovida por error en producción — ✅ RESUELTO 2026-09-04

`expedientes_candidatos.organizacion = 'Clara'` sigue en `estado = 'candidato'`
en Neon (producción), y por lo tanto sigue apareciendo en `GET /verificados`.

Es un **falso positivo confirmado**: la evidencia real era sobre "Clara
Brugada" (alcaldesa de CDMX, nota de seguridad pública sin relación con la
fintech "Clara"), promovida antes de que se corrigiera la causa raíz en
`clasificacion_epistemologica.py` (commit `794ed6d`, PR #4 — ver
`_vinculado_a_org` y `_dominio_bajo_autoridad`).

El código ya no puede volver a producir este bug hacia adelante. Lo que falta
es **corregir el dato ya persistido**: revertir ese expediente específico de
`'candidato'` a `'abierto'`.

No se pudo ejecutar hoy porque requiere `HD_INGEST_TOKEN`, que vive solo en
las variables de entorno de Vercel — no se compartió con el agente en esta
sesión (por diseño: es un secreto del operador). Dos caminos, sin tocar
código:

- **Endpoint temporal ya desplegado** (ver punto 2 abajo):
  ```
  curl "https://antrosapiens-api-pro.vercel.app/admin/revertir-candidato-clara" \
    -H "X-Ingest-Token: <HD_INGEST_TOKEN>"
  ```
  Respuesta esperada: `{"organizacion":"Clara","filas_afectadas":1}`.
- **SQL manual en Neon** (alternativa, mismo patrón usado para
  Bitso/Kavak/Nubank/Rappi/Ualá):
  ```sql
  UPDATE expedientes_candidatos
  SET estado = 'abierto', actualizado_en = now()
  WHERE organizacion = 'Clara' AND estado = 'candidato';
  ```

Después de correr cualquiera de los dos, verificar con `GET /verificados`
que el total baja de 7 a 6 y que "Clara" ya no aparece en la lista.

## 2. Endpoint temporal de reversión — ✅ RETIRADO 2026-09-04

`GET /admin/revertir-candidato-clara` (`hd_scraper/api/app.py`) cumplió su
propósito de un solo uso: revertir el expediente `'Clara'` de `'candidato'`
a `'abierto'` en la base de producción correcta (ver punto 1, resuelto el
mismo día). Se eliminó del código siguiendo el patrón acordado originalmente
("de un solo uso, se retira apenas se confirme que revirtió a Clara"),
respetando el invariante de `promocion_candidatos.py` ("nunca degrada un
candidato de vuelta a abierto... no existe ese camino en este módulo").
Solo queda `GET /admin` (el formulario HTML de intake) bajo `/admin/*`.
976 tests pasando tras el retiro.

## 3. "Rasgos a evaluar" (checklist pericial) — especificación pendiente, sin iniciar

Funcionalidad propuesta para la ficha de detalle de un expediente (pantalla
OBSERVAR en `android_v2/.../index.html`, o el `dossier` server-side): una
sección con 6 rasgos fijos, cada uno con 3 valores seleccionables
(`presente` / `ausente` / `no_determinado`) + nota de texto opcional:

1. Contradicción entre lo declarado y lo practicado
2. Ritual competidor (práctica vieja que sigue cumpliendo función)
3. Relación de poder en juego (no solo un proceso)
4. Raíz histórica (pasivo del pasado, no problema nuevo)
5. Función invisible de la práctica (qué se pierde si desaparece)
6. Lenguaje evasivo/psicologizante en la explicación dada

**Regla dura acordada**: el sistema NUNCA marca estos rasgos automáticamente.
Todos nacen en `no_determinado` hasta que el perito los marque a mano — es un
formulario de lectura humana, no un cálculo. Confirmado que esto NO requiere
entrada nueva en CLAUDE.md → «Frontera de Interpretación» (mismo motivo que
exime `discurso_corporativo`/Thick Data: el motor solo almacena lo que
declara un humano, nunca lo infiere).

Esquema propuesto (no escrito todavía, pendiente de dos decisiones):
- Tabla nueva `lectura_pericial` (`expediente_id`, `rasgo`, `valor`, `nota`,
  `quien_marco`, `actualizado_en`), `UNIQUE(expediente_id, rasgo)`.
- Módulo nuevo `hd_scraper/lectura_pericial.py` (constantes + `guardar_rasgo`
  UPSERT + `rasgos_de_expediente` que siempre devuelve los 6, default
  `no_determinado`).
- Dos endpoints en `hd_scraper/api/app.py`: `GET /lectura-pericial/{id}`
  (lectura pública) y `POST /lectura-pericial/{id}` (autenticado con
  `X-Ingest-Token`).
- Sección nueva en `mostrarObservar()` (`index.html`).

**Decisiones abiertas antes de escribir código:**
1. ¿UPSERT (una fila por rasgo, se sobrescribe al corregir) o histórico
   append-only (cada marca queda, como `memoria_cientifica` en Capa 13)?
2. `quien_marco`: no hay sistema de login/usuarios en la app (solo el token
   compartido). ¿Campo de texto libre que el perito escribe a mano, o vale
   la pena explorar autenticación por perito antes de construir esto?
