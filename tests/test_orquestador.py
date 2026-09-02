"""Orquestador de fuentes multifuente (Entrega 4).

Cubre los casos del brief que tocan la orquestación:
  - caso 4: dos fuentes -> dos evidencias -> misma organización;
  - caso 6: añadir una fuente no cambia la clasificación ya existente;
  - caso 7 (parcial): las fuentes reales siguen en el REGISTRY sin cambios.
"""
from __future__ import annotations

import pytest

from hd_scraper.clasificacion_store import clasificar_lote
from hd_scraper.connectors import REGISTRY
from hd_scraper.db.models import QuerySpec
from hd_scraper.orquestador import FuenteDesconocida, OrquestadorFuentes, _resolver_fuentes
from tests._fakes import (
    FakeAConnector,
    FakeBConnector,
    FakeSlugConnector,
    fakes_registrados,
)

Q = QuerySpec(empresa="Nubank", tipo_evento="ronda")


def _n(db, tabla: str) -> int:
    return db.fetch_one(f"SELECT COUNT(*) AS n FROM {tabla}")["n"]


# ── Resolución de fuentes ────────────────────────────────────────────────

def test_fuentes_por_defecto_es_todo_el_registry(db):
    orq = OrquestadorFuentes(db)
    assert set(orq.fuentes_habilitadas()) == set(REGISTRY)


def test_fuentes_explicitas_se_respetan_y_van_en_orden_del_registry(db):
    with fakes_registrados(FakeAConnector, FakeBConnector):
        orq = OrquestadorFuentes(db, fuentes=["fake_b", "fake_a"])
        # El orden es el de REGISTRY (inserción), no el que pidió el llamador.
        assert orq.fuentes_habilitadas() == ["fake_a", "fake_b"]


def test_fuente_desconocida_falla_fuerte(db):
    with pytest.raises(FuenteDesconocida):
        OrquestadorFuentes(db, fuentes=["no_existe"])


def test_resolver_ignora_duplicados():
    with fakes_registrados(FakeAConnector):
        assert _resolver_fuentes(["fake_a", "fake_a"]) == ["fake_a"]


def test_las_cuatro_fuentes_reales_siguen_registradas(db):
    # El REGISTRY real no se toca en esta entrega.
    assert {"google_news", "gdelt", "rss_fijos", "job_boards"} <= set(REGISTRY)


# ── Ejecución ────────────────────────────────────────────────────────────

def test_ejecutar_persiste_evidencia_de_la_fuente(db):
    with fakes_registrados(FakeAConnector):
        res = OrquestadorFuentes(db, fuentes=["fake_a"]).ejecutar(Q)
    assert res["fake_a"].escritos == 1
    assert _n(db, "evidencias") == 1
    fila = db.fetch_one("SELECT connector, empresa_mencionada FROM evidencias")
    assert fila["connector"] == "fake_a"
    assert fila["empresa_mencionada"] == "Nubank"


def test_fuente_no_habilitada_no_corre(db):
    with fakes_registrados(FakeAConnector, FakeBConnector):
        OrquestadorFuentes(db, fuentes=["fake_a"]).ejecutar(Q)
    assert _n(db, "evidencias") == 1
    assert db.fetch_one(
        "SELECT COUNT(*) AS n FROM evidencias WHERE connector='fake_b'"
    )["n"] == 0


def test_dos_fuentes_misma_organizacion__dos_evidencias_un_expediente(db):
    """Caso 4 del brief."""
    with fakes_registrados(FakeAConnector, FakeBConnector):
        res = OrquestadorFuentes(db, fuentes=["fake_a", "fake_b"]).ejecutar(Q)
    assert res["fake_a"].escritos == 1 and res["fake_b"].escritos == 1
    assert _n(db, "evidencias") == 2

    clasificar_lote(db, aplicar=True)
    assert _n(db, "expedientes_candidatos") == 1
    assert _n(db, "evidencia_clasificada") == 2


def test_connector_por_slug_se_salta_si_la_query_no_trae_slug(db):
    with fakes_registrados(FakeSlugConnector):
        res = OrquestadorFuentes(db, fuentes=["fake_slug"]).ejecutar(Q)
    assert res == {}
    assert _n(db, "evidencias") == 0

    with fakes_registrados(FakeSlugConnector):
        res = OrquestadorFuentes(db, fuentes=["fake_slug"]).ejecutar(
            QuerySpec(empresa="Nubank", tipo_evento="contratacion", slug="nubank")
        )
    assert res["fake_slug"].escritos == 1


def test_evidencia_normalizada_no_persiste(db):
    with fakes_registrados(FakeAConnector, FakeBConnector):
        registros = OrquestadorFuentes(
            db, fuentes=["fake_a", "fake_b"]
        ).evidencia_normalizada(Q)
    assert {r.nombre_medio for r in registros} == {"fake_a", "fake_b"}
    assert _n(db, "evidencias") == 0          # nada escrito
    assert _n(db, "raw_store") == 0


# ── Caso 6: una fuente nueva no altera la clasificación ya hecha ─────────

def test_anadir_fuente_no_cambia_la_clasificacion_existente(db):
    with fakes_registrados(FakeAConnector):
        OrquestadorFuentes(db, fuentes=["fake_a"]).ejecutar(Q)
    clasificar_lote(db, aplicar=True)

    antes = db.fetch_all(
        "SELECT id, evidencia_id, tipo_epistemologico FROM evidencia_clasificada "
        "ORDER BY id"
    )
    antes = [dict(r) for r in antes]
    assert len(antes) == 1

    # Llega una segunda fuente y se reclasifica el lote pendiente.
    with fakes_registrados(FakeBConnector):
        OrquestadorFuentes(db, fuentes=["fake_b"]).ejecutar(Q)
    rep = clasificar_lote(db, aplicar=True)
    assert rep["procesadas"] == 1        # solo la nueva evidencia estaba pendiente

    despues = db.fetch_all(
        "SELECT id, evidencia_id, tipo_epistemologico FROM evidencia_clasificada "
        "WHERE id = ?",
        (antes[0]["id"],),
    )
    assert dict(despues[0]) == antes[0]  # la fila original, intacta
