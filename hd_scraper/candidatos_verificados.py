"""Lectura de expedientes ya promovidos a 'candidato' (Entrega 3), para
exponerlos vía API a los clientes de Motor A (p. ej. la app Android).

Este módulo NO decide ni promueve nada: `expedientes_candidatos.estado` ya lo
escribió `scripts.promover_candidatos --aplicar` (Entrega 3) sobre evidencia ya
clasificada por `scripts.clasificar_evidencia --aplicar` (Entrega 2). Aquí solo
se proyecta ese resultado ya calculado, con la evidencia primaria (la que
sustentó la promoción) citada literalmente. No reproduce ni modifica la lógica
de `promocion_candidatos.py` / `promocion_store.py`.
"""
from __future__ import annotations

# Orden de prioridad determinista cuando un expediente tiene más de una
# evidencia primaria: autodeclaración (máxima autoridad) antes que huella
# práctica (acto publicado sin declaración de persona).
_ORDEN_TIPO_PRIMARIO = (
    "senal_primaria_autodeclaracion",
    "senal_primaria_huella_practica",
)


def listar_candidatos_verificados(db, *, limite: int = 50) -> list[dict]:
    """Expedientes 'candidato' con su evidencia primaria citada literalmente.

    Determinista: si un expediente tiene varias evidencias primarias, elige la
    de mayor prioridad (`_ORDEN_TIPO_PRIMARIO`) y, dentro del mismo tipo, la
    más antigua (id menor) — mismo insumo, mismo resultado.
    """
    expedientes = db.fetch_all(
        "SELECT id, organizacion FROM expedientes_candidatos "
        "WHERE estado = 'candidato' ORDER BY organizacion LIMIT ?",
        (int(limite),))

    orden_caso = " ".join(
        f"WHEN '{tipo}' THEN {i}" for i, tipo in enumerate(_ORDEN_TIPO_PRIMARIO))

    resultado: list[dict] = []
    for fila in expedientes:
        exp = dict(fila)
        evidencia = db.fetch_one(
            "SELECT ec.tipo_epistemologico, e.cita_textual, e.url_fuente, "
            "e.nombre_medio FROM evidencia_clasificada ec "
            "JOIN evidencias e ON e.id = ec.evidencia_id "
            "WHERE ec.expediente_id = ? "
            "AND ec.tipo_epistemologico IN (?, ?) "
            f"ORDER BY CASE ec.tipo_epistemologico {orden_caso} END, ec.id "
            "LIMIT 1",
            (exp["id"], *_ORDEN_TIPO_PRIMARIO))
        if not evidencia:
            # Expediente 'candidato' sin evidencia primaria localizable (no
            # debería ocurrir dado cómo promueve Entrega 3, pero no se inventa
            # nada: se omite en vez de mostrar una tarjeta vacía).
            continue
        ev = dict(evidencia)
        resultado.append({
            "organizacion": exp["organizacion"],
            "tipo_epistemologico": ev["tipo_epistemologico"],
            "cita_textual": ev["cita_textual"],
            "url_fuente": ev["url_fuente"],
            "nombre_medio": ev["nombre_medio"],
        })
    return resultado
