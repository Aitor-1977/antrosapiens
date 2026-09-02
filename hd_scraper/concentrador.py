"""Concentrador de evidencia y densidad evidencial — Entrega 4.

Autorizado por el operador el 2026-09-02 (ver «Frontera de Interpretación» en
CLAUDE.md). Sobre evidencia YA extraída y YA clasificada por este motor:

  1. agrupa todas las evidencias de una **organización identificada** —la que
     tiene un ``expediente_candidatos``— sin importar de qué fuente vinieron;
  2. lista la evidencia **sin organización identificada**, que se conserva pero
     nunca entra en un caso ni se promueve;
  3. calcula una **métrica de densidad** puramente aritmética.

Naturaleza (INVIOLABLE, igual que Entregas 2 y 3):
- **Solo lectura.** Nunca INSERT/UPDATE/DELETE. Lee ``expedientes_candidatos``,
  ``evidencia_clasificada`` y ``evidencias``.
- **Determinista y reproducible.** Mismo insumo ⇒ misma salida. Sin IA, sin red.
- **No interpreta.** ``densidad ≠ Deuda Cultural``. La densidad es un recuento
  (evidencias, fuentes independientes, señales primarias, persistencia): sirve
  para priorizar qué casos mira una persona, no para decidir nada. No promueve
  expedientes (eso es Entrega 3) ni ejecuta acción comercial.
"""
from __future__ import annotations

from datetime import datetime

from .clasificacion_epistemologica import (
    TIPO_AUTODECLARACION,
    TIPO_CONTEXTUAL,
    TIPO_CORROBORANTE,
    TIPO_HUELLA_PRACTICA,
)

VERSION = "concentrador.v1"

#: Tipos epistemológicos que cuentan como "señal primaria" (misma pareja que usa
#: la promoción; se declara aquí para no acoplar este módulo a la doctrina de
#: promoción, solo al vocabulario del clasificador).
SENALES_PRIMARIAS: frozenset[str] = frozenset(
    {TIPO_AUTODECLARACION, TIPO_HUELLA_PRACTICA}
)


def _fila(row) -> dict:
    return dict(row) if row is not None else {}


def buscar_expediente(db, organizacion: str) -> dict | None:
    """Expediente de la organización (case-insensitive), o None si no existe.

    Mismo criterio que ``clasificacion_store.buscar_expediente``: sin expediente,
    la organización no está identificada para el motor.
    """
    row = db.fetch_one(
        "SELECT id, organizacion, estado FROM expedientes_candidatos "
        "WHERE LOWER(organizacion) = LOWER(?) ORDER BY id LIMIT 1",
        (organizacion,),
    )
    return _fila(row) or None


def evidencias_de_organizacion(db, organizacion: str) -> dict | None:
    """Todas las evidencias clasificadas de una organización identificada.

    Devuelve ``None`` si la organización no tiene expediente (no identificada);
    para esa evidencia usar :func:`evidencia_sin_organizacion`.

    La lista viene ordenada por ``evidencia_id`` (estable). Cada elemento trae su
    fuente (``connector``), su peso epistemológico (``tipo_epistemologico``) y los
    campos de procedencia, para que cada evidencia sea trazable a su origen.
    """
    exp = buscar_expediente(db, organizacion)
    if exp is None:
        return None

    filas = db.fetch_all(
        """
        SELECT
            e.id                AS evidencia_id,
            e.connector         AS fuente,
            e.nombre_medio      AS nombre_medio,
            e.url_fuente        AS url_fuente,
            e.cita_textual      AS cita_textual,
            e.fecha_publicacion AS fecha_publicacion,
            e.fecha_extraccion  AS fecha_extraccion,
            e.tipo_evento       AS tipo_evento,
            e.origen_declaracion AS origen_declaracion,
            ec.tipo_epistemologico AS tipo_epistemologico,
            ec.enunciador_nombre   AS enunciador_nombre,
            ec.enunciador_cargo    AS enunciador_cargo
        FROM evidencia_clasificada ec
        JOIN evidencias e ON e.id = ec.evidencia_id
        WHERE ec.expediente_id = ?
        ORDER BY e.id
        """,
        (exp["id"],),
    )
    evidencias = [dict(f) for f in filas]

    return {
        "expediente_id": exp["id"],
        "organizacion": exp["organizacion"],
        "estado": exp["estado"],
        "total_evidencias": len(evidencias),
        "evidencias": evidencias,
    }


def evidencia_sin_organizacion(db, *, limite: int | None = None) -> list[dict]:
    """Evidencia conservada pero SIN organización identificada.

    Son las filas de ``evidencias`` que no tienen ninguna fila en
    ``evidencia_clasificada`` que las enganche a un expediente. Regla del brief:
    evidencia válida + identidad insuficiente ⇒ se conserva, nunca se promueve.
    """
    sql = [
        "SELECT e.id AS evidencia_id, e.connector AS fuente,",
        "       e.nombre_medio, e.url_fuente, e.cita_textual,",
        "       e.empresa_mencionada, e.fecha_publicacion, e.fecha_extraccion",
        "FROM evidencias e",
        "LEFT JOIN evidencia_clasificada ec ON ec.evidencia_id = e.id",
        "WHERE ec.id IS NULL",
        "ORDER BY e.id",
    ]
    params: list[object] = []
    if limite:
        sql.append("LIMIT ?")
        params.append(int(limite))
    return [dict(f) for f in db.fetch_all(" ".join(sql), tuple(params))]


def _persistencia_dias(fechas_iso: list[str | None]) -> int:
    """Rango en días entre la evidencia fechada más antigua y la más reciente.

    0 si hay menos de dos evidencias con ``fecha_publicacion`` legible. No es un
    juicio: es max(fecha) - min(fecha).
    """
    fechas: list[datetime] = []
    for valor in fechas_iso:
        if not valor:
            continue
        try:
            fechas.append(datetime.fromisoformat(valor.replace("Z", "+00:00")))
        except (ValueError, AttributeError):
            continue
    if len(fechas) < 2:
        return 0
    return (max(fechas) - min(fechas)).days


def densidad_evidencial(db, organizacion: str) -> dict:
    """Métrica aritmética de densidad para una organización.

    NO es un score ni un veredicto: es un recuento reproducible. Claves:

    - ``identificada``: bool. Si es False, todo lo demás va a 0.
    - ``n_evidencias``: total de evidencias clasificadas del expediente.
    - ``n_fuentes_independientes``: conectores distintos que la aportaron.
    - ``n_senales_primarias``: evidencias con ``tipo_epistemologico`` en
      ``SENALES_PRIMARIAS``.
    - ``n_corroborantes`` / ``n_contextuales``.
    - ``persistencia_dias``: rango temporal de las evidencias fechadas.
    - ``version``: versión de esta métrica.
    """
    base = {
        "organizacion": organizacion,
        "identificada": False,
        "expediente_id": None,
        "estado": None,
        "n_evidencias": 0,
        "n_fuentes_independientes": 0,
        "n_senales_primarias": 0,
        "n_corroborantes": 0,
        "n_contextuales": 0,
        "persistencia_dias": 0,
        "version": VERSION,
    }

    concentrado = evidencias_de_organizacion(db, organizacion)
    if concentrado is None:
        return base

    evidencias = concentrado["evidencias"]
    fuentes = {(e.get("fuente") or "").strip() for e in evidencias}
    fuentes.discard("")
    tipos = [e.get("tipo_epistemologico") for e in evidencias]

    base.update(
        identificada=True,
        expediente_id=concentrado["expediente_id"],
        estado=concentrado["estado"],
        organizacion=concentrado["organizacion"],
        n_evidencias=len(evidencias),
        n_fuentes_independientes=len(fuentes),
        n_senales_primarias=sum(1 for t in tipos if t in SENALES_PRIMARIAS),
        n_corroborantes=sum(1 for t in tipos if t == TIPO_CORROBORANTE),
        n_contextuales=sum(1 for t in tipos if t == TIPO_CONTEXTUAL),
        persistencia_dias=_persistencia_dias(
            [e.get("fecha_publicacion") for e in evidencias]
        ),
    )
    return base
