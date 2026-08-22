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
"""
from __future__ import annotations

from .clasificacion_epistemologica import (
    TIPOS,
    VERSION_REGLAS,
    Clasificacion,
    clasificar,
)

ESTADO_INICIAL = "abierto"


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


def guardar_clasificacion(db, expediente_id: int, evidencia_id: int,
                          clas: Clasificacion) -> bool:
    """Inserta la clasificación. Devuelve False si ya existía (no duplica)."""
    if ya_clasificada(db, evidencia_id):
        return False
    db.execute(
        "INSERT INTO evidencia_clasificada (expediente_id, evidencia_id, "
        "tipo_epistemologico, enunciador_nombre, enunciador_cargo, "
        "enunciador_dominio) VALUES (?,?,?,?,?,?)",
        (expediente_id, evidencia_id, clas.tipo, clas.enunciador_nombre,
         clas.enunciador_cargo, clas.enunciador_dominio))
    return True


def clasificar_lote(db, *, desde: str | None = None, org: str | None = None,
                    limite: int | None = None, solo_ok: bool = False,
                    aplicar: bool = False, muestra: int = 10) -> dict:
    """Clasifica el lote pendiente. Sin ``aplicar=True`` NO escribe nada.

    El informe es idéntico en dry-run y en aplicación, salvo `escritas` y
    `expedientes_creados`, que en dry-run son proyecciones.
    """
    lote = evidencias_sin_clasificar(db, desde=desde, org=org, limite=limite,
                                     solo_ok=solo_ok)
    conocidas = orgs_conocidas(db)

    distribucion = {t: 0 for t in TIPOS}
    escritas = 0
    expedientes_creados = 0
    orgs_proyectadas: set[str] = set()
    ejemplos: list[dict] = []

    for ev in lote:
        clas = clasificar(ev, conocidas)
        distribucion[clas.tipo] += 1

        organizacion = (ev.get("empresa_mencionada") or "").strip()
        if aplicar and organizacion:
            expediente_id, creado = obtener_o_crear_expediente(db, organizacion)
            expedientes_creados += int(creado)
            if guardar_clasificacion(db, expediente_id, ev["id"], clas):
                escritas += 1
        elif organizacion:
            clave = organizacion.lower()
            if (clave not in orgs_proyectadas
                    and buscar_expediente(db, organizacion) is None):
                orgs_proyectadas.add(clave)
                expedientes_creados += 1

        if len(ejemplos) < muestra:
            ejemplos.append({
                "evidencia_id": ev.get("id"),
                "organizacion": organizacion,
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
        "muestra": ejemplos,
    }
