"""Persistencia del Observatorio Antropológico del Ecosistema.

Segunda función de AntroLabsHD, independiente del radar comercial (Motor A
de evidencia/candidatos). Lee y escribe SOLO `fuente_discursiva`,
`fragmento_observado` y `nota_de_mario` — nunca `evidencias`,
`evidencia_clasificada` ni `expedientes_candidatos`.

NUNCA importa `clasificacion_epistemologica.py` ni `promocion_candidatos.py`:
el Observatorio no clasifica ni promueve nada, solo guarda discurso citable
para lectura humana (autorizado por el operador —Mario—, 2026-09-18).
"""
from __future__ import annotations


def buscar_fuente_por_hash(db, hash_contenido: str) -> int | None:
    fila = db.fetch_one(
        "SELECT id FROM fuente_discursiva WHERE hash_contenido = ?",
        (hash_contenido,))
    return dict(fila)["id"] if fila else None


def guardar_fuente_y_fragmento(db, fuente: dict, fragmento: dict) -> tuple[int, bool]:
    """Inserta `fuente_discursiva` + `fragmento_observado`. Devuelve
    (fuente_id, creado). `creado=False` cuando la fuente ya existía
    (idempotente por `hash_contenido`, mismo patrón que `hash_dedup` en
    `evidencias`): en ese caso no se duplica ni la fuente ni su fragmento.
    """
    existente = buscar_fuente_por_hash(db, fuente["hash_contenido"])
    if existente is not None:
        return existente, False

    fuente_id = db.insert_returning_id(
        "INSERT INTO fuente_discursiva "
        "(tipo_fuente, url, plataforma, actor_principal, fecha_publicacion, "
        "fecha_captura, duracion_aprox, hash_contenido) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (fuente["tipo_fuente"], fuente["url"], fuente.get("plataforma"),
         fuente["actor_principal"], fuente.get("fecha_publicacion"),
         fuente["fecha_captura"], fuente.get("duracion_aprox"),
         fuente["hash_contenido"]))

    db.execute(
        "INSERT INTO fragmento_observado "
        "(fuente_id, texto_citable, minuto_aproximado, tema_libre, "
        "tipo_registro, estado) VALUES (?, ?, ?, ?, ?, ?)",
        (fuente_id, fragmento["texto_citable"], fragmento.get("minuto_aproximado"),
         fragmento.get("tema_libre"), fragmento["tipo_registro"],
         fragmento.get("estado", "capturado")))
    return fuente_id, True


def listar_observatorio(db, *, actor: str | None = None, tema: str | None = None,
                        fuente_tipo: str | None = None, limite: int = 50) -> list[dict]:
    """Fragmentos observados, más recientes primero (por id descendente),
    con los datos de su fuente. Filtrable por actor, tema o tipo de fuente —
    coincidencia exacta, sin fuzzy-match (mismo criterio que el resto del
    repo: extracción estructural, no interpretación).
    """
    sql = [
        "SELECT fo.id AS fragmento_id, fo.texto_citable, fo.minuto_aproximado, "
        "fo.tema_libre, fo.tipo_registro, fo.estado, "
        "fd.id AS fuente_id, fd.tipo_fuente, fd.url, fd.plataforma, "
        "fd.actor_principal, fd.fecha_publicacion, fd.fecha_captura, "
        "fd.duracion_aprox "
        "FROM fragmento_observado fo "
        "JOIN fuente_discursiva fd ON fd.id = fo.fuente_id "
        "WHERE 1 = 1",
    ]
    params: list[object] = []
    if actor:
        sql.append("AND LOWER(fd.actor_principal) = LOWER(?)")
        params.append(actor)
    if tema:
        sql.append("AND LOWER(fo.tema_libre) = LOWER(?)")
        params.append(tema)
    if fuente_tipo:
        sql.append("AND fd.tipo_fuente = ?")
        params.append(fuente_tipo)
    sql.append("ORDER BY fo.id DESC LIMIT ?")
    params.append(int(limite))
    return [dict(f) for f in db.fetch_all(" ".join(sql), tuple(params))]


def guardar_nota(db, fragmento_id: int, contenido: str, fecha: str) -> int:
    """Agrega una nota de lectura de Mario a un fragmento ya capturado."""
    return db.insert_returning_id(
        "INSERT INTO nota_de_mario (fragmento_id, contenido, fecha) "
        "VALUES (?, ?, ?)",
        (fragmento_id, contenido, fecha))


def fragmento_existe(db, fragmento_id: int) -> bool:
    return db.fetch_one(
        "SELECT id FROM fragmento_observado WHERE id = ?",
        (fragmento_id,)) is not None
