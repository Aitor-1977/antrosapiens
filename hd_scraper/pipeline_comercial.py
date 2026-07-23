"""Capa 9 — Pipeline Comercial: gestión de etapas por organización.

Reemplaza la lógica de un CRM tradicional por un proceso basado en
evidencia antropológica. Cada organización avanza por etapas que reflejan
el nivel de conocimiento acumulado — NO la intención de venta.

Etapas (cerradas, secuenciales):
  1. Observación:  la organización aparece en el radar (evidencias captadas)
  2. Vigilancia:   se decidió monitorearla activamente (drift + onlife)
  3. Peritaje:     evidencia suficiente para análisis cualitativo profundo
  4. DolorMap:     sprint de diagnóstico de Dolor Cultural™
  5. Alianza:      propuesta o conversación activa con la organización
  6. Cerrado:      relación formalizada (ganado o descartado)

Principios:
  - Las etapas se avanzan manualmente (decisión del operador, no automática).
  - El retroceso es posible (una organización puede volver a vigilancia).
  - Cada transición queda registrada con fecha y motivo (trazable).
  - El pipeline NO interpreta evidencia — solo organiza el flujo comercial.
"""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Optional

from .db.database import get_db
from .db.models import ahora_iso

logger = logging.getLogger("hd_scraper.pipeline_comercial")

ETAPAS = (
    "observacion", "vigilancia", "peritaje",
    "dolormap", "alianza", "cerrado",
)

ETAPAS_LABELS = {
    "observacion": "Observación",
    "vigilancia": "Vigilancia",
    "peritaje": "Peritaje Cualitativo",
    "dolormap": "DolorMap Sprint",
    "alianza": "Alianza",
    "cerrado": "Cerrado",
}

RESULTADO_CIERRE = ("ganado", "descartado", "pausado")


def registrar_org(org_nombre: str, etapa: str = "observacion",
                  notas: str = "") -> dict:
    """Registra o actualiza una organización en el pipeline comercial."""
    if etapa not in ETAPAS:
        raise ValueError(f"Etapa inválida: {etapa}. Válidas: {ETAPAS}")

    db = get_db()
    ahora = ahora_iso()
    dedup = hashlib.sha256(org_nombre.strip().lower().encode()).hexdigest()[:32]

    existente = db.fetch_one(
        "SELECT id, etapa FROM pipeline_comercial WHERE hash_dedup = ?",
        (dedup,),
    )

    if existente:
        db.execute(
            "UPDATE pipeline_comercial SET etapa = ?, notas = ?, actualizado_en = ? "
            "WHERE id = ?",
            (etapa, notas, ahora, existente["id"]),
        )
        _registrar_transicion(
            db, existente["id"], org_nombre, existente["etapa"], etapa, notas, ahora,
        )
        return {
            "id": existente["id"], "org_nombre": org_nombre,
            "etapa_anterior": existente["etapa"], "etapa": etapa,
            "accion": "actualizado",
        }

    pid = db.insert_returning_id(
        """INSERT INTO pipeline_comercial
             (org_nombre, etapa, notas, resultado, hash_dedup, creado_en, actualizado_en)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (org_nombre.strip(), etapa, notas, "", dedup, ahora, ahora),
    )
    _registrar_transicion(db, pid, org_nombre, "", etapa, notas, ahora)
    return {
        "id": pid, "org_nombre": org_nombre,
        "etapa_anterior": "", "etapa": etapa,
        "accion": "creado",
    }


def avanzar(org_nombre: str, nueva_etapa: str,
            notas: str = "", resultado: str = "") -> dict:
    """Mueve una organización a una nueva etapa del pipeline."""
    if nueva_etapa not in ETAPAS:
        raise ValueError(f"Etapa inválida: {nueva_etapa}")
    if resultado and resultado not in RESULTADO_CIERRE:
        raise ValueError(f"Resultado inválido: {resultado}. Válidos: {RESULTADO_CIERRE}")

    db = get_db()
    dedup = hashlib.sha256(org_nombre.strip().lower().encode()).hexdigest()[:32]
    existente = db.fetch_one(
        "SELECT id, etapa FROM pipeline_comercial WHERE hash_dedup = ?",
        (dedup,),
    )

    if not existente:
        return registrar_org(org_nombre, nueva_etapa, notas)

    ahora = ahora_iso()
    etapa_anterior = existente["etapa"]

    updates = "etapa = ?, notas = ?, actualizado_en = ?"
    params: list = [nueva_etapa, notas, ahora]
    if resultado:
        updates += ", resultado = ?"
        params.append(resultado)
    params.append(existente["id"])

    db.execute(
        f"UPDATE pipeline_comercial SET {updates} WHERE id = ?",
        tuple(params),
    )
    _registrar_transicion(
        db, existente["id"], org_nombre, etapa_anterior, nueva_etapa, notas, ahora,
    )

    return {
        "id": existente["id"], "org_nombre": org_nombre,
        "etapa_anterior": etapa_anterior, "etapa": nueva_etapa,
        "resultado": resultado,
    }


def _registrar_transicion(
    db, pipeline_id: int, org_nombre: str,
    etapa_desde: str, etapa_hasta: str,
    notas: str, fecha: str,
) -> None:
    """Registra una transición en el historial (auditable)."""
    db.execute(
        """INSERT INTO pipeline_transiciones
             (pipeline_id, org_nombre, etapa_desde, etapa_hasta, notas, fecha)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (pipeline_id, org_nombre, etapa_desde, etapa_hasta, notas, fecha),
    )


def obtener_pipeline(org_nombre: str) -> Optional[dict]:
    """Devuelve el estado del pipeline de una organización."""
    db = get_db()
    dedup = hashlib.sha256(org_nombre.strip().lower().encode()).hexdigest()[:32]
    row = db.fetch_one(
        "SELECT * FROM pipeline_comercial WHERE hash_dedup = ?", (dedup,),
    )
    if not row:
        return None

    transiciones = db.fetch_all(
        "SELECT * FROM pipeline_transiciones WHERE pipeline_id = ? ORDER BY fecha DESC",
        (row["id"],),
    )
    result = dict(row)
    result["transiciones"] = [dict(t) for t in transiciones]
    result["etapa_label"] = ETAPAS_LABELS.get(result["etapa"], result["etapa"])
    return result


def listar_pipeline(etapa: Optional[str] = None) -> dict:
    """Lista todas las organizaciones en el pipeline, opcionalmente filtradas."""
    db = get_db()
    if etapa and etapa in ETAPAS:
        rows = db.fetch_all(
            "SELECT * FROM pipeline_comercial WHERE etapa = ? ORDER BY actualizado_en DESC",
            (etapa,),
        )
    else:
        rows = db.fetch_all(
            "SELECT * FROM pipeline_comercial ORDER BY actualizado_en DESC",
        )

    items = [dict(r) for r in rows]
    for item in items:
        item["etapa_label"] = ETAPAS_LABELS.get(item["etapa"], item["etapa"])

    por_etapa = {}
    for e in ETAPAS:
        por_etapa[e] = sum(1 for i in items if i["etapa"] == e)

    return {
        "total": len(items),
        "por_etapa": por_etapa,
        "organizaciones": items,
    }


def resumen_funnel() -> dict:
    """Resumen tipo funnel del pipeline comercial."""
    db = get_db()
    rows = db.fetch_all(
        "SELECT etapa, COUNT(*) as total FROM pipeline_comercial GROUP BY etapa",
    )
    conteo = {r["etapa"]: r["total"] for r in rows}
    funnel = []
    for e in ETAPAS:
        funnel.append({
            "etapa": e,
            "label": ETAPAS_LABELS[e],
            "total": conteo.get(e, 0),
        })
    return {
        "funnel": funnel,
        "total_organizaciones": sum(conteo.values()),
    }
