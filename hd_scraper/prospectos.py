"""Escritura y actualización de prospectos.

Un prospecto es una entidad objetivo de uno de los cuatro ecosistemas (VC,
Startup, Incubadora, Corporativo). Se da de alta con su ``categoria``
obligatoria y, opcionalmente, su discurso corporativo (Thick Data).

Como el discurso de un prospecto se enriquece con el tiempo (nuevas capturas de
URLs/perfiles), la escritura es un UPSERT por ``hash_dedup``: si el prospecto ya
existe, se refresca su Thick Data y ``actualizado_en`` sin duplicar. Los
prospectos inválidos van a `rechazos`, nunca a `prospectos`.
"""
from __future__ import annotations

import json
import logging

from .db.database import Database
from .db.models import ProspectoRecord, ahora_iso, calcular_hash_prospecto
from .validation.validator import validate_prospecto

log = logging.getLogger("hd_scraper.prospectos")


def nuevo_prospecto(nombre: str, categoria: str, **thick) -> ProspectoRecord:
    """Construye un ``ProspectoRecord`` con el hash_dedup calculado.

    ``thick`` acepta: discurso_corporativo, tipo_discurso, url_perfil,
    fuente_discurso, fecha_captura.
    """
    return ProspectoRecord(
        nombre=nombre,
        categoria=categoria,
        hash_dedup=calcular_hash_prospecto(nombre, categoria),
        **thick,
    )


def _escribir_rechazo(db: Database, motivo: str, payload: dict) -> None:
    db.execute(
        "INSERT INTO rechazos (connector, motivo, payload_json, creado_en) VALUES (?, ?, ?, ?)",
        ("prospecto", motivo, json.dumps(payload, ensure_ascii=False, default=str), ahora_iso()),
    )


def upsert_prospecto(db: Database, record: ProspectoRecord) -> dict:
    """Valida y hace UPSERT del prospecto por ``hash_dedup``.

    Devuelve {"ok": bool, "accion": "insertado|actualizado|rechazado", ...}.
    Los campos de Thick Data solo se sobrescriben si vienen con valor (no borran
    lo previo con None).
    """
    veredicto = validate_prospecto(record)
    if not veredicto.ok:
        _escribir_rechazo(db, veredicto.motivo or "desconocido",
                          {"nombre": record.nombre, "categoria": record.categoria})
        return {"ok": False, "accion": "rechazado", "motivo": veredicto.motivo}

    existe = db.fetch_one(
        "SELECT id FROM prospectos WHERE hash_dedup = ?", (record.hash_dedup,)
    )
    ahora = ahora_iso()
    if existe is None:
        db.execute(
            """INSERT INTO prospectos
                 (nombre, categoria, discurso_corporativo, tipo_discurso, url_perfil,
                  fuente_discurso, fecha_captura, hash_dedup, creado_en, actualizado_en)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (record.nombre, record.categoria, record.discurso_corporativo,
             record.tipo_discurso, record.url_perfil, record.fuente_discurso,
             record.fecha_captura, record.hash_dedup, ahora, ahora),
        )
        return {"ok": True, "accion": "insertado", "id": db.fetch_one(
            "SELECT id FROM prospectos WHERE hash_dedup = ?", (record.hash_dedup,))["id"]}

    # UPSERT: refresca solo los campos de Thick Data que vengan con valor.
    db.execute(
        """UPDATE prospectos SET
             discurso_corporativo = COALESCE(?, discurso_corporativo),
             tipo_discurso        = COALESCE(?, tipo_discurso),
             url_perfil           = COALESCE(?, url_perfil),
             fuente_discurso      = COALESCE(?, fuente_discurso),
             fecha_captura        = COALESCE(?, fecha_captura),
             actualizado_en       = ?
           WHERE hash_dedup = ?""",
        (record.discurso_corporativo, record.tipo_discurso, record.url_perfil,
         record.fuente_discurso, record.fecha_captura, ahora, record.hash_dedup),
    )
    return {"ok": True, "accion": "actualizado", "id": existe["id"]}
