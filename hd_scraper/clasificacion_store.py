"""Persistencia de la clasificación epistemológica — Entrega 2.

Lee `evidencias` (SOLO lectura: nunca UPDATE ni DELETE sobre esa tabla) y
escribe en `expedientes_candidatos` y `evidencia_clasificada`, que ya existen en
producción y NO se modifican desde aquí.

Idempotencia sin restricción única
----------------------------------
Ninguna de las dos tablas tiene índice único (`evidencia_id` en una,
`organizacion` en la otra), así que `ON CONFLICT DO NOTHING` —el patrón habitual
del repo— no tendría contra qué chocar y una segunda corrida duplicaría filas.
La idempotencia vive por tanto en el código:

* el lote se obtiene con un LEFT JOIN que excluye lo ya clasificado;
* cada escritura reverifica con un SELECT previo, por si el lote se solapa.

Es seguro para un proceso batch. No es seguro frente a dos batches simultáneos
sobre la misma base: para eso haría falta el índice único, que exigiría un
cambio de DDL en producción (recomendado en la nota de entrega, no aplicado).

El estado del expediente queda SIEMPRE en 'abierto'. La promoción a 'candidato'
es una regla de la Entrega 3 y este módulo no la implementa ni la anticipa.

Identidad organizacional del conector `busqueda_dinamica_founder` (autorizado
2026-08-28, ver CLAUDE.md): ese conector guarda en `empresa_mencionada` la
FRASE de búsqueda, nunca una organización real. Para su evidencia (y SOLO
para ella — los cuatro conectores de Fase 1 siguen usando `empresa_mencionada`
sin cambios, ahí ya es un nombre real declarado por el operador), la
organización del expediente sale de `Clasificacion.organizacion_mencionada`
(extracción estructural sobre el contenido, ver
`clasificacion_epistemologica._detectar_organizacion_mencionada`).

Evidencia sin organización identificada (§8.3 del documento maestro,
2026-08-29): la clasificación SÍ se persiste, con
`evidencia_clasificada.expediente_id = NULL` — la columna se migró a
nullable (ver `db/database.py:_migrar_expediente_id_nullable`) precisamente
para esto. Antes (hasta 2026-08-28) la fila completa se descartaba en
silencio porque la columna era NOT NULL; eso perdía evidencia real, incluida
la de mayor peso epistemológico (`senal_primaria_autodeclaracion`). Sin
`expediente_id`, no hay expediente ni promoción posible — pero la evidencia
y su clasificación quedan conservadas y pueden vincularse más adelante si
mejora la extracción de identidad organizacional.
"""
from __future__ import annotations

import logging
import time
from typing import Callable

from .clasificacion_epistemologica import (
    TIPOS,
    VERSION_REGLAS,
    Clasificacion,
    clasificar,
)

ESTADO_INICIAL = "abierto"

# Único conector cuyo `empresa_mencionada` es una frase de búsqueda, no una
# organización real (ver docstring del módulo).
_CONECTOR_BUSQUEDA_DINAMICA = "busqueda_dinamica_founder"

log = logging.getLogger("hd_scraper.clasificacion_store")

# Vocabulario de errores de RED/CONEXIÓN (no de datos), compartido por
# psycopg y sqlite3 en sus mensajes de excepción. Dialecto-agnóstico a
# propósito: no importa psycopg a nivel de módulo (solo hace falta si hay
# Postgres en el entorno) y evita acoplarse a una clase de excepción concreta.
_MARCADORES_ERROR_CONEXION = (
    "ssl syscall", "connection abort", "could not receive data",
    "could not send data", "server closed the connection",
    "connection already closed", "consuming input failed",
    "terminating connection", "connection reset", "broken pipe",
)


def _es_error_conexion(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(marcador in msg for marcador in _MARCADORES_ERROR_CONEXION)


def orgs_conocidas(db) -> tuple[str, ...]:
    """Nombres del directorio, para desambiguar a quién pertenece un cargo.

    Si un titular menciona dos organizaciones, el cargo se atribuye a la más
    cercana; sin esta lista, un «CEO de otra empresa» contaría como
    autodeclaración de la organización de la fila.
    """
    filas = db.fetch_all("SELECT nombre FROM prospectos ORDER BY nombre")
    return tuple((dict(f).get("nombre") or "").strip() for f in filas
                 if (dict(f).get("nombre") or "").strip())


def evidencias_sin_clasificar(db, *, desde: str | None = None,
                              org: str | None = None,
                              limite: int | None = None,
                              solo_ok: bool = False) -> list[dict]:
    """Evidencias que aún no tienen fila en `evidencia_clasificada`.

    ``desde`` filtra por `creado_en` (fecha de CAPTURA, siempre presente), no
    por `fecha_publicacion`, que es opcional: filtrar por ella dejaría fuera en
    silencio todas las filas `no_fechado`.
    """
    sql = [
        "SELECT e.* FROM evidencias e",
        "LEFT JOIN evidencia_clasificada ec ON ec.evidencia_id = e.id",
        "WHERE ec.id IS NULL",
    ]
    params: list[object] = []
    if solo_ok:
        sql.append("AND e.estado = 'ok'")
    if desde:
        sql.append("AND e.creado_en >= ?")
        params.append(desde)
    if org:
        sql.append("AND LOWER(e.empresa_mencionada) = LOWER(?)")
        params.append(org)
    sql.append("ORDER BY e.id")
    if limite:
        sql.append("LIMIT ?")
        params.append(int(limite))
    return [dict(f) for f in db.fetch_all(" ".join(sql), tuple(params))]


def buscar_expediente(db, organizacion: str) -> int | None:
    fila = db.fetch_one(
        "SELECT id FROM expedientes_candidatos "
        "WHERE LOWER(organizacion) = LOWER(?) ORDER BY id LIMIT 1",
        (organizacion,))
    return dict(fila)["id"] if fila else None


def obtener_o_crear_expediente(db, organizacion: str) -> tuple[int, bool]:
    """Devuelve (id, creado). Nunca toca el `estado` de un expediente existente."""
    existente = buscar_expediente(db, organizacion)
    if existente is not None:
        return existente, False
    nuevo = db.insert_returning_id(
        "INSERT INTO expedientes_candidatos (organizacion, estado) VALUES (?, ?)",
        (organizacion, ESTADO_INICIAL))
    return nuevo, True


def ya_clasificada(db, evidencia_id: int) -> bool:
    return db.fetch_one(
        "SELECT id FROM evidencia_clasificada WHERE evidencia_id = ? LIMIT 1",
        (evidencia_id,)) is not None


def guardar_clasificacion(db, expediente_id: int | None, evidencia_id: int,
                          clas: Clasificacion) -> bool:
    """Inserta la clasificación. Devuelve False si ya existía (no duplica).

    `expediente_id=None` cuando la evidencia no tiene organización
    identificada (§8.3): se persiste igual, sin vincular a ningún
    expediente."""
    if ya_clasificada(db, evidencia_id):
        return False
    db.execute(
        "INSERT INTO evidencia_clasificada (expediente_id, evidencia_id, "
        "tipo_epistemologico, enunciador_nombre, enunciador_cargo, "
        "enunciador_dominio, organizacion_mencionada) VALUES (?,?,?,?,?,?,?)",
        (expediente_id, evidencia_id, clas.tipo, clas.enunciador_nombre,
         clas.enunciador_cargo, clas.enunciador_dominio,
         clas.organizacion_mencionada))
    return True


def clasificar_lote(db, *, desde: str | None = None, org: str | None = None,
                    limite: int | None = None, solo_ok: bool = False,
                    aplicar: bool = False, muestra: int = 10,
                    max_reintentos: int = 5, backoff_base: float = 1.0,
                    sleep: Callable[[float], None] = time.sleep) -> dict:
    """Clasifica el lote pendiente. Sin ``aplicar=True`` NO escribe nada.

    El informe es idéntico en dry-run y en aplicación, salvo `escritas` y
    `expedientes_creados`, que en dry-run son proyecciones.

    Resiliencia de red: cada escritura ya commitea por su cuenta (ver
    `Database.execute`/`insert_returning_id`), así que esto NUNCA fue una
    transacción larga — pero una red inestable (datos móviles) puede tumbar el
    socket a media evidencia. Si la excepción es de conexión (no de datos), se
    reconecta con backoff y se reintenta la MISMA evidencia hasta
    `max_reintentos` veces; si sigue fallando, se salta y se registra: la
    próxima corrida la recoge sola (el lote excluye lo ya clasificado). Un
    error que no sea de conexión (de datos/programación) no se reintenta.
    """
    lote = evidencias_sin_clasificar(db, desde=desde, org=org, limite=limite,
                                     solo_ok=solo_ok)
    conocidas = orgs_conocidas(db)

    distribucion = {t: 0 for t in TIPOS}
    escritas = 0
    expedientes_creados = 0
    saltadas = 0
    orgs_proyectadas: set[str] = set()
    ejemplos: list[dict] = []

    for ev in lote:
        clas = clasificar(ev, conocidas)
        distribucion[clas.tipo] += 1
        if ev.get("connector") == _CONECTOR_BUSQUEDA_DINAMICA:
            # `empresa_mencionada` de este conector es la FRASE de búsqueda,
            # nunca una organización real (ver CLAUDE.md, entrada 2026-08-28
            # y docstring de busqueda_dinamica.py). Se usa exclusivamente la
            # organización EXTRAÍDA DEL CONTENIDO; sin ella, no hay expediente
            # (expediente_id queda NULL, ver §8.3 del documento maestro).
            organizacion = (clas.organizacion_mencionada or "").strip()
        else:
            organizacion = (ev.get("empresa_mencionada") or "").strip()

        intento = 0
        while True:
            try:
                if aplicar:
                    # Con organización, se crea/reutiliza el expediente y se
                    # vincula. Sin ella, la clasificación se persiste igual
                    # (expediente_id = NULL): la evidencia nunca se pierde
                    # por falta de identidad organizacional (§8.3).
                    if organizacion:
                        expediente_id, creado = obtener_o_crear_expediente(db, organizacion)
                        expedientes_creados += int(creado)
                    else:
                        expediente_id = None
                    if guardar_clasificacion(db, expediente_id, ev["id"], clas):
                        escritas += 1
                elif organizacion:
                    clave = organizacion.lower()
                    if (clave not in orgs_proyectadas
                            and buscar_expediente(db, organizacion) is None):
                        orgs_proyectadas.add(clave)
                        expedientes_creados += 1
                break
            except Exception as exc:
                if not _es_error_conexion(exc) or intento >= max_reintentos:
                    log.error("clasificar_lote: se salta evidencia %s tras "
                              "fallo permanente: %s", ev.get("id"), exc)
                    saltadas += 1
                    break
                intento += 1
                espera = backoff_base * (2 ** (intento - 1))
                log.warning("clasificar_lote: conexión caída en evidencia %s "
                           "(intento %d/%d), reconectando en %.1fs: %s",
                           ev.get("id"), intento, max_reintentos, espera, exc)
                sleep(espera)
                try:
                    db.reconectar()
                except Exception:
                    pass

        if len(ejemplos) < muestra:
            ejemplos.append({
                "evidencia_id": ev.get("id"),
                "organizacion": organizacion,
                "empresa_mencionada": ev.get("empresa_mencionada"),
                "organizacion_mencionada": clas.organizacion_mencionada,
                "cita_textual": ev.get("cita_textual"),
                "tipo_epistemologico": clas.tipo,
                "enunciador_nombre": clas.enunciador_nombre,
                "enunciador_cargo": clas.enunciador_cargo,
                "enunciador_dominio": clas.enunciador_dominio,
                "razon": clas.razon,
            })

    return {
        "version_reglas": VERSION_REGLAS,
        "aplicado": bool(aplicar),
        "pendientes": len(lote),
        "procesadas": len(lote),
        "distribucion": distribucion,
        "escritas": escritas,
        "expedientes_creados": expedientes_creados,
        "saltadas": saltadas,
        "muestra": ejemplos,
    }
