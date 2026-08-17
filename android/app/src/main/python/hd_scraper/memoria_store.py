"""Persistencia inmutable de la Memoria Científica — Capa 13.

Append-only: nunca hace UPDATE ni DELETE. Cada versión se numera de forma
monótona por organización. Si el estado científico no cambió (mismo hash de
huella que la última versión), no se crea una versión nueva: la memoria es
inmutable y no duplica estados idénticos. Determinista y portable SQLite/PG.
"""
from __future__ import annotations

import json

from .db.models import ahora_iso
from .memoria import crear_version


def _ultima_version(db, org: str) -> dict | None:
    row = db.fetch_one(
        "SELECT * FROM memoria_cientifica WHERE org_nombre = ? "
        "ORDER BY version_num DESC LIMIT 1", (org,))
    return dict(row) if row else None


def guardar_version(db, org: str, expediente: dict, validacion: dict,
                    huella: dict, usuario: str = "sistema") -> dict:
    """Guarda una nueva versión inmutable si el estado científico cambió.

    Devuelve {guardado, version, hash}. Reejecutar con el mismo estado no
    crea filas nuevas (dedup por hash de huella).
    """
    ultima = _ultima_version(db, org)
    if ultima and ultima["hash"] == huella.get("hash", ""):
        return {"guardado": False, "version": ultima["version_num"],
                "hash": ultima["hash"]}

    num = (ultima["version_num"] + 1) if ultima else 1
    previo = ultima["hash"] if ultima else ""
    rec = crear_version(expediente, validacion, huella, usuario, num, previo)

    db.execute(
        "INSERT INTO memoria_cientifica (org_nombre, version_num, hash, hash_previo, "
        "veredicto, scoring, hipotesis, solidez, suficiencia, nivel_evidencia, "
        "nivel_confianza, dolor_cultural, snapshot_json, motor, pipeline, usuario, "
        "creado_en) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (org, num, rec["hash"], previo, rec["veredicto"], rec["scoring"],
         rec["hipotesis"], rec["solidez"], rec["suficiencia"], rec["nivel_evidencia"],
         rec["nivel_confianza"], rec["dolor_cultural"],
         json.dumps(rec, ensure_ascii=False), rec["motor"], rec["pipeline"],
         usuario, ahora_iso()))
    return {"guardado": True, "version": num, "hash": rec["hash"]}


def recuperar_historial(db, org: str) -> list[dict]:
    """Recupera todas las versiones inmutables de una organización (orden asc)."""
    filas = db.fetch_all(
        "SELECT snapshot_json FROM memoria_cientifica WHERE org_nombre = ? "
        "ORDER BY version_num ASC", (org,))
    return [json.loads(f["snapshot_json"]) for f in filas]
