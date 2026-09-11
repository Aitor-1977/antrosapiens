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

# FASE territorial (autorizada por el operador —Mario—, 2026-09-11): filtro
# estructural por país sobre `/verificados`. `expedientes_candidatos.organizacion`
# es solo un nombre de texto (no una FK a `prospectos`), así que el país se
# resuelve por coincidencia EXACTA de nombre (LOWER(TRIM(...)), sin fuzzy-match
# ni embeddings — mismo patrón que `concentrador_evidencia.py`). Cuando no hay
# fila de `prospectos` que coincida, o esa fila no declara país (`pais IS
# NULL`), el candidato NO se excluye: la ausencia de dato no es evidencia de
# que sea de otro país. Solo se excluye cuando SÍ hay un país declarado y ese
# país no es México. Esto es filtrado estructural sobre un dato ya extraído
# (país de sede/fundación, público y verificable en `seed_prospectos.py`), no
# interpretación: no toca `directorio.py` ni su cascada de país de Wikidata.
PAIS_PERMITIDO = "México"


def listar_candidatos_verificados(db, *, limite: int = 50) -> list[dict]:
    """Expedientes 'candidato' con su evidencia primaria citada literalmente.

    Determinista: si un expediente tiene varias evidencias primarias, elige la
    de mayor prioridad (`_ORDEN_TIPO_PRIMARIO`) y, dentro del mismo tipo, la
    más antigua (id menor) — mismo insumo, mismo resultado.

    Filtrado territorial: excluye organizaciones cuyo `prospectos.pais`
    (resuelto por nombre exacto) esté declarado y no sea `PAIS_PERMITIDO`.
    """
    expedientes = db.fetch_all(
        "SELECT ec.id, ec.organizacion FROM expedientes_candidatos ec "
        "LEFT JOIN prospectos p ON LOWER(TRIM(p.nombre)) = LOWER(TRIM(ec.organizacion)) "
        "WHERE ec.estado = 'candidato' AND (p.pais IS NULL OR p.pais = ?) "
        "ORDER BY ec.organizacion LIMIT ?",
        (PAIS_PERMITIDO, int(limite)))

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
