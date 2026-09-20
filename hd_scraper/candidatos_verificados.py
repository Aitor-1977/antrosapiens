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

from .friccion import score_relevancia
from .freshness import score_freshness

UMBRAL_SCORE_RELEVANCIA = 40

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


def listar_candidatos_verificados(
    db, *, limite: int = 50, estado_visibilidad: str = "visible"
) -> list[dict]:
    """Expedientes 'candidato' con su evidencia primaria citada literalmente.

    Determinista: si un expediente tiene varias evidencias primarias, elige la
    de mayor prioridad (`_ORDEN_TIPO_PRIMARIO`) y, dentro del mismo tipo, la
    más antigua (id menor) — mismo insumo, mismo resultado.

    Filtrado territorial: excluye organizaciones cuyo `prospectos.pais`
    (resuelto por nombre exacto) esté declarado y no sea `PAIS_PERMITIDO`.

    Visibilidad (autorizado por el operador —Mario—, 2026-09-19/20, score
    gradual el 2026-09-20, ver CLAUDE.md "Frontera de Interpretación"): cada
    expediente se etiqueta `visibilidad` ("visible" | "latente") según DOS
    scores independientes, ninguno sustituye al otro: `score_relevancia`
    (densidad de lenguaje de fricción, `friccion.score_relevancia`, sobre
    TODAS las evidencias de la organización) y `score_freshness`
    (antigüedad de la evidencia PRIMARIA seleccionada más abajo —NUNCA la
    evidencia más reciente de la organización—, `freshness.score_freshness`).
    `visible` solo si `score_relevancia >= UMBRAL_SCORE_RELEVANCIA` Y
    `score_freshness > 0`, ambas condiciones a la vez, nunca un promedio. NO
    se toca `estado` en la base ni la lógica de `promocion_candidatos.py`,
    solo se decide qué se expone como tarjeta en esta capa de lectura. Por
    defecto (`estado_visibilidad="visible"`) el resultado excluye los
    "latente"; con `estado_visibilidad="todos"` se devuelven ambos, con los
    dos scores visibles para auditoría. El límite se aplica DESPUÉS de
    filtrar por visibilidad (se sobre-consulta la tabla, igual que
    `_construir_expedientes`), para no devolver menos de lo pedido solo
    porque algunos candidatos del rango quedaron latentes.
    """
    expedientes = db.fetch_all(
        "SELECT ec.id, ec.organizacion, p.categoria AS categoria_prospecto "
        "FROM expedientes_candidatos ec "
        "LEFT JOIN prospectos p ON LOWER(TRIM(p.nombre)) = LOWER(TRIM(ec.organizacion)) "
        "WHERE ec.estado = 'candidato' AND (p.pais IS NULL OR p.pais = ?) "
        "ORDER BY ec.organizacion LIMIT 5000",
        (PAIS_PERMITIDO,))

    orden_caso = " ".join(
        f"WHEN '{tipo}' THEN {i}" for i, tipo in enumerate(_ORDEN_TIPO_PRIMARIO))

    resultado: list[dict] = []
    for fila in expedientes:
        exp = dict(fila)
        evidencia = db.fetch_one(
            "SELECT ec.tipo_epistemologico, e.cita_textual, e.url_fuente, "
            "e.nombre_medio, e.fecha_publicacion, e.persona_citada, e.cargo, "
            "e.categoria AS categoria_evidencia FROM evidencia_clasificada ec "
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
        # categoria estructural (prospectos.categoria, declarada por el
        # operador) es la autoridad, igual que en _construir_expedientes;
        # sin fila en prospectos, cae a la categoria de la propia evidencia
        # (la etiqueta de la consulta que la capturó).
        categoria = exp["categoria_prospecto"] or ev["categoria_evidencia"] or ""
        relevancia = score_relevancia(db, exp["organizacion"])
        # SIEMPRE sobre la evidencia PRIMARIA de esta fila (ev), nunca sobre
        # la evidencia más reciente de la organización: una nota nueva pero
        # irrelevante no debe rejuvenecer un expediente cuya evidencia
        # primaria es vieja.
        freshness = score_freshness(ev["fecha_publicacion"])
        visible = relevancia >= UMBRAL_SCORE_RELEVANCIA and freshness > 0
        if estado_visibilidad != "todos" and not visible:
            continue
        resultado.append({
            "organizacion": exp["organizacion"],
            "categoria": categoria,
            "tipo_epistemologico": ev["tipo_epistemologico"],
            "cita_textual": ev["cita_textual"],
            "url_fuente": ev["url_fuente"],
            "nombre_medio": ev["nombre_medio"],
            "fecha_publicacion": ev["fecha_publicacion"],
            "persona_citada": ev["persona_citada"],
            "cargo": ev["cargo"],
            "score_relevancia": relevancia,
            "score_freshness": freshness,
            "visibilidad": "visible" if visible else "latente",
        })
        if len(resultado) >= limite:
            break
    return resultado
