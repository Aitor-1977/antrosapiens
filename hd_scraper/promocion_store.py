"""Persistencia de la promoción de expedientes — Entrega 3.

Lee `evidencia_clasificada` (tipos ya registrados por Entrega 2) y `prospectos`
(categoria declarada por el operador), y escribe SOLO el campo `estado` de
`expedientes_candidatos`. Nunca toca `evidencias`, `evidencia_clasificada` ni
`prospectos`.

Idempotencia: el `UPDATE` lleva `WHERE estado = 'abierto'`, así que una
reejecución sobre un expediente ya promovido no vuelve a escribir (0 filas
afectadas, verificado por `cur.rowcount`, mismo patrón que `pipeline.py`).
Nunca hay `UPDATE` que mueva `candidato` → `abierto`: no existe ese camino en
este módulo.
"""
from __future__ import annotations

from .db.models import ahora_iso
from .promocion_candidatos import DecisionPromocion, decidir_promocion


def categoria_de_organizacion(db, organizacion: str) -> str | None:
    """`categoria` declarada en `prospectos` para esa organización, o None
    si el nombre del expediente no matchea ninguna fila (p. ej. variante de
    nombre no dada de alta). Comparación case-insensitive, mismo patrón que
    `clasificacion_store.buscar_expediente`.

    ``ORDER BY id DESC``: prefiere la fila MÁS RECIENTE. `hash_dedup` de
    `prospectos` es sha256(nombre + categoria) — si `categoria` cambia para
    una organización ya sembrada (p. ej. una reclasificación de Startup a
    Corporativo en `seed_prospectos.py`), el reseed automático de `get_db()`
    no reconoce la fila vieja como la misma entidad y crea un duplicado, en
    vez de corregirla (ON CONFLICT no bloquea porque el hash es distinto). Sin
    este DESC, un duplicado así hace que la promoción lea la categoria
    OBSOLETA. Esto es una salvaguarda, no el arreglo real: los duplicados en
    sí son un defecto de datos que debe limpiarse en la base (ver incidente
    2026-08-22 documentado en el historial de commits)."""
    fila = db.fetch_one(
        "SELECT categoria FROM prospectos WHERE LOWER(nombre) = LOWER(?) "
        "ORDER BY id DESC LIMIT 1",
        (organizacion,))
    return dict(fila)["categoria"] if fila else None


def tipos_de_expediente(db, expediente_id: int) -> list[str]:
    filas = db.fetch_all(
        "SELECT DISTINCT tipo_epistemologico FROM evidencia_clasificada "
        "WHERE expediente_id = ?",
        (expediente_id,))
    return [dict(f)["tipo_epistemologico"] for f in filas]


def expedientes_abiertos(db, *, org: str | None = None,
                         limite: int | None = None) -> list[dict]:
    sql = ["SELECT id, organizacion FROM expedientes_candidatos "
           "WHERE estado = 'abierto'"]
    params: list[object] = []
    if org:
        sql.append("AND LOWER(organizacion) = LOWER(?)")
        params.append(org)
    sql.append("ORDER BY id")
    if limite:
        sql.append("LIMIT ?")
        params.append(int(limite))
    return [dict(f) for f in db.fetch_all(" ".join(sql), tuple(params))]


def evaluar_expediente(db, expediente_id: int, organizacion: str
                       ) -> tuple[DecisionPromocion, str | None, list[str]]:
    """Resuelve categoria y tipos para el expediente y aplica la decisión
    pura. No escribe nada."""
    categoria = categoria_de_organizacion(db, organizacion)
    tipos = tipos_de_expediente(db, expediente_id)
    return decidir_promocion(categoria, tipos), categoria, tipos


def promover(db, expediente_id: int) -> bool:
    """UPDATE real: 'abierto' -> 'candidato'. Devuelve True si escribió.

    Idempotente por el WHERE: si el expediente ya no está en 'abierto'
    (promovido antes, o descartado), no hace nada y devuelve False.
    """
    cur = db.execute(
        "UPDATE expedientes_candidatos SET estado = 'candidato', "
        "actualizado_en = ? WHERE id = ? AND estado = 'abierto'",
        (ahora_iso(), expediente_id))
    return cur.rowcount > 0


def promover_lote(db, *, org: str | None = None, limite: int | None = None,
                  aplicar: bool = False) -> dict:
    """Evalúa el lote de expedientes 'abierto'. Sin ``aplicar=True`` NO
    escribe nada.
    """
    expedientes = expedientes_abiertos(db, org=org, limite=limite)

    promovidos = 0
    detalle: list[dict] = []

    for exp in expedientes:
        decision, categoria, tipos = evaluar_expediente(db, exp["id"], exp["organizacion"])

        escrito = False
        if decision.promover and aplicar:
            escrito = promover(db, exp["id"])

        detalle.append({
            "expediente_id": exp["id"],
            "organizacion": exp["organizacion"],
            "categoria": categoria,
            "tipos_encontrados": sorted(tipos),
            "promovido": decision.promover,
            "razon": decision.razon,
            "escrito": escrito,
        })
        if escrito:
            promovidos += 1

    return {
        "aplicado": bool(aplicar),
        "evaluados": len(expedientes),
        "promovidos": (sum(1 for d in detalle if d["promovido"]) if not aplicar
                       else promovidos),
        "detalle": detalle,
    }
