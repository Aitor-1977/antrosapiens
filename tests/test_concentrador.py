"""Concentrador de evidencia y densidad evidencial (Entrega 4).

Cubre los casos del brief:
  - caso 1: evidencia con organización -> organización identificada;
  - caso 2: evidencia sin organización -> conservada, sin expediente;
  - caso 5: evidencia sin organización -> jamás candidato;
  - más la densidad como recuento (no veredicto).
"""
from __future__ import annotations

from hd_scraper.clasificacion_store import clasificar_lote
from hd_scraper.concentrador import (
    densidad_evidencial,
    evidencia_sin_organizacion,
    evidencias_de_organizacion,
)
from hd_scraper.db.models import ahora_iso, calcular_hash_dedup
from hd_scraper.orquestador import OrquestadorFuentes
from hd_scraper.promocion_store import promover_lote
from hd_scraper.db.models import QuerySpec
from tests._fakes import FakeAConnector, FakeBConnector, fakes_registrados

Q = QuerySpec(empresa="Nubank", tipo_evento="ronda")


def _n(db, tabla: str) -> int:
    return db.fetch_one(f"SELECT COUNT(*) AS n FROM {tabla}")["n"]


def _insertar_evidencia_cruda(db, *, empresa: str, url: str, titulo: str,
                              fecha_pub: str | None = None) -> int:
    """INSERT directo en `evidencias`, saltándose el validador.

    Se usa solo para fabricar el caso límite 'empresa_mencionada vacía', que el
    contrato normalmente no deja entrar pero que la regla de conservación debe
    seguir tratando bien.
    """
    return db.insert_returning_id(
        """
        INSERT INTO evidencias (
            cita_textual, fecha_extraccion, url_fuente, nombre_medio,
            empresa_mencionada, tipo_evento, origen_declaracion, hash_dedup,
            fecha_publicacion, connector, estado, confianza, creado_en
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ok', 0, ?)
        """,
        (titulo, ahora_iso(), url, "fake_manual", empresa, "ronda", "prensa",
         calcular_hash_dedup(empresa, url), fecha_pub, "fake_manual", ahora_iso()),
    )


def _sembrar_dos_fuentes(db) -> None:
    with fakes_registrados(FakeAConnector, FakeBConnector):
        OrquestadorFuentes(db, fuentes=["fake_a", "fake_b"]).ejecutar(Q)
    clasificar_lote(db, aplicar=True)


# ── Concentración ────────────────────────────────────────────────────────

def test_evidencia_con_organizacion_se_concentra(db):
    """Caso 1."""
    _sembrar_dos_fuentes(db)
    conc = evidencias_de_organizacion(db, "Nubank")
    assert conc is not None
    assert conc["organizacion"] == "Nubank"
    assert conc["expediente_id"] is not None
    assert conc["total_evidencias"] == 2
    fuentes = {e["fuente"] for e in conc["evidencias"]}
    assert fuentes == {"fake_a", "fake_b"}
    assert all(e["tipo_epistemologico"] for e in conc["evidencias"])


def test_organizacion_sin_expediente_devuelve_none(db):
    _sembrar_dos_fuentes(db)
    assert evidencias_de_organizacion(db, "Empresa Inexistente") is None
    # case-insensitive, como el resto del repo
    assert evidencias_de_organizacion(db, "NUBANK") is not None


def test_evidencia_no_clasificada_aparece_en_sin_organizacion(db):
    with fakes_registrados(FakeAConnector):
        OrquestadorFuentes(db, fuentes=["fake_a"]).ejecutar(Q)
    # Todavía no se ha clasificado: no hay fila en evidencia_clasificada.
    sin_org = evidencia_sin_organizacion(db)
    assert len(sin_org) == 1
    assert sin_org[0]["fuente"] == "fake_a"

    clasificar_lote(db, aplicar=True)
    assert evidencia_sin_organizacion(db) == []


def test_evidencia_empresa_vacia_se_conserva_pero_nunca_es_candidato(db):
    """Casos 2 y 5: identidad insuficiente => conservar, jamás promover."""
    _insertar_evidencia_cruda(
        db, empresa="", url="https://ejemplo.test/x/sin-empresa",
        titulo="Una empresa del sector fintech levanta capital",
    )
    expedientes_antes = _n(db, "expedientes_candidatos")

    rep = clasificar_lote(db, aplicar=True)
    promover_lote(db, aplicar=True)

    # No se creó expediente para la evidencia sin organización.
    assert _n(db, "expedientes_candidatos") == expedientes_antes
    assert _n(db, "evidencia_clasificada") == 0
    # Sigue conservada y localizable.
    sin_org = evidencia_sin_organizacion(db)
    assert len(sin_org) == 1
    assert sin_org[0]["empresa_mencionada"] == ""
    assert rep["escritas"] == 0


# ── Densidad ─────────────────────────────────────────────────────────────

def test_densidad_es_recuento_no_veredicto(db):
    _sembrar_dos_fuentes(db)
    d = densidad_evidencial(db, "Nubank")

    assert d["identificada"] is True
    assert d["n_evidencias"] == 2
    assert d["n_fuentes_independientes"] == 2
    assert d["version"] == "concentrador.v1"
    assert (
        d["n_senales_primarias"] + d["n_corroborantes"] + d["n_contextuales"]
        == d["n_evidencias"]
    )
    # No hay veredicto, score ni Deuda en ninguna parte de la salida.
    prohibido = ("deuda", "score", "veredicto", "hipotesis", "dictamen", "dolor")
    plano = repr(d).lower()
    assert not any(p in plano for p in prohibido)
    assert all(isinstance(v, (int, bool, str)) or v is None for v in d.values())


def test_densidad_persistencia_es_rango_de_fechas(db):
    _sembrar_dos_fuentes(db)
    # fake_a: 2026-08-01, fake_b: 2026-08-11 -> 10 días.
    assert densidad_evidencial(db, "Nubank")["persistencia_dias"] == 10


def test_densidad_organizacion_no_identificada_es_cero(db):
    d = densidad_evidencial(db, "Nadie")
    assert d["identificada"] is False
    assert d["expediente_id"] is None
    for clave in ("n_evidencias", "n_fuentes_independientes", "n_senales_primarias",
                  "n_corroborantes", "n_contextuales", "persistencia_dias"):
        assert d[clave] == 0
