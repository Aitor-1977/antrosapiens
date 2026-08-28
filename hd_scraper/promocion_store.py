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

import logging

from .db.models import ahora_iso
from .promocion_candidatos import DecisionPromocion, decidir_promocion

log = logging.getLogger("hd_scraper.promocion_store")


def categoria_de_organizacion(db, organizacion: str) -> tuple[str | None, bool]:
    """`categoria` declarada en `prospectos` para esa organización.

    Devuelve ``(categoria, conflicto)``. Comparación case-insensitive, mismo
    patrón que `clasificacion_store.buscar_expediente`. Sin ninguna fila:
    ``(None, False)`` — variante de nombre no dada de alta, la exclusión de
    Corporativo no aplica (ver `promocion_candidatos.decidir_promocion`).

    ``conflicto=True`` cuando existe más de una fila para el mismo `nombre`
    con `categoria` DISTINTA: un defecto de datos, no un caso normal.
    `hash_dedup` de `prospectos` es sha256(nombre + categoria) — si
    `categoria` cambia para una organización ya sembrada (p. ej. una
    reclasificación de Startup a Corporativo en `seed_prospectos.py`), el
    reseed automático de `get_db()` no reconoce la fila vieja como la misma
    entidad y crea un duplicado en vez de corregirla (`ON CONFLICT` no
    bloquea porque el hash es distinto). Elegir en silencio la fila más
    reciente (comportamiento anterior) fue precisamente lo que dejó promover
    a Bitso/Kavak/Nubank/Rappi/Ualá pese a estar marcadas 'Corporativo': un
    duplicado 'Startup' más nuevo ganaba la lectura (incidente 2026-08-22/23,
    ver historial de commits). Ahora, ante conflicto, esta función NO decide
    por ninguna de las dos: registra una advertencia en el log y devuelve
    ``(None, True)`` para que la orquestación (`evaluar_expediente`) bloquee
    la promoción hasta que el duplicado se limpie a mano en `prospectos`
    (fuera de alcance aquí: esta función nunca escribe en `prospectos`, y
    `POST /prospectos/bulk` —origen probable de estos duplicados— queda
    deliberadamente sin tocar, para otra sesión)."""
    filas = db.fetch_all(
        "SELECT categoria FROM prospectos WHERE LOWER(nombre) = LOWER(?)",
        (organizacion,))
    categorias = {dict(f)["categoria"] for f in filas}
    if len(categorias) > 1:
        log.warning(
            "categoria_de_organizacion: conflicto de categoria para %r: "
            "%d filas en prospectos con categorias distintas entre sí %s. "
            "No se promueve hasta resolver el duplicado en prospectos.",
            organizacion, len(filas), sorted(categorias))
        return None, True
    if categorias:
        return next(iter(categorias)), False
    return None, False


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
                       ) -> tuple[DecisionPromocion, str | None, list[str], bool]:
    """Resuelve categoria y tipos para el expediente y aplica la decisión
    pura. No escribe nada.

    Si `categoria_de_organizacion` señala conflicto (duplicado con categoria
    distinta en `prospectos`), esta función NO llama a `decidir_promocion`
    con una categoria adivinada: construye la decisión aquí mismo, siempre
    `promover=False`, dejando la ambigüedad visible en `razon` y en el
    último elemento devuelto (`conflicto`). `promocion_candidatos.py` no se
    toca: sigue sin saber que los conflictos existen."""
    categoria, conflicto = categoria_de_organizacion(db, organizacion)
    tipos = tipos_de_expediente(db, expediente_id)
    if conflicto:
        decision = DecisionPromocion(
            False,
            "conflicto de categoria en prospectos: hay más de una fila para "
            "esta organización con categoria distinta (defecto de datos, "
            "ver log de advertencia) — requiere revisión manual antes de "
            "promover, no se resuelve en automático")
    else:
        decision = decidir_promocion(categoria, tipos)
    return decision, categoria, tipos, conflicto


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
        decision, categoria, tipos, conflicto = evaluar_expediente(
            db, exp["id"], exp["organizacion"])

        escrito = False
        if decision.promover and aplicar:
            escrito = promover(db, exp["id"])

        detalle.append({
            "expediente_id": exp["id"],
            "organizacion": exp["organizacion"],
            "categoria": categoria,
            "categoria_en_conflicto": conflicto,
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
        "conflictos_categoria": sum(1 for d in detalle if d["categoria_en_conflicto"]),
        "detalle": detalle,
    }
