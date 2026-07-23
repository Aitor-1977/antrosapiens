"""Capa 9 — Pipeline Comercial: tests de gestión de etapas."""
import pytest

from hd_scraper.pipeline_comercial import (
    ETAPAS,
    ETAPAS_LABELS,
    RESULTADO_CIERRE,
    avanzar,
    listar_pipeline,
    obtener_pipeline,
    registrar_org,
    resumen_funnel,
)


# ── registrar_org ────────────────────────────────────────────────────────────

def test_registrar_nueva_org(db, monkeypatch):
    monkeypatch.setattr("hd_scraper.pipeline_comercial.get_db", lambda: db)
    r = registrar_org("Acme Corp")
    assert r["accion"] == "creado"
    assert r["etapa"] == "observacion"
    assert r["org_nombre"] == "Acme Corp"
    assert r["id"] is not None


def test_registrar_con_etapa(db, monkeypatch):
    monkeypatch.setattr("hd_scraper.pipeline_comercial.get_db", lambda: db)
    r = registrar_org("Acme Corp", etapa="vigilancia", notas="Alta prioridad")
    assert r["etapa"] == "vigilancia"
    assert r["accion"] == "creado"


def test_registrar_duplicado_actualiza(db, monkeypatch):
    monkeypatch.setattr("hd_scraper.pipeline_comercial.get_db", lambda: db)
    r1 = registrar_org("Acme Corp")
    r2 = registrar_org("Acme Corp", etapa="vigilancia")
    assert r2["accion"] == "actualizado"
    assert r2["etapa_anterior"] == "observacion"
    assert r2["etapa"] == "vigilancia"


def test_registrar_etapa_invalida(db, monkeypatch):
    monkeypatch.setattr("hd_scraper.pipeline_comercial.get_db", lambda: db)
    with pytest.raises(ValueError, match="Etapa inválida"):
        registrar_org("Acme Corp", etapa="inexistente")


def test_registrar_dedup_case_insensitive(db, monkeypatch):
    monkeypatch.setattr("hd_scraper.pipeline_comercial.get_db", lambda: db)
    r1 = registrar_org("Acme Corp")
    r2 = registrar_org("acme corp", etapa="vigilancia")
    assert r2["accion"] == "actualizado"
    assert r1["id"] == r2["id"]


# ── avanzar ──────────────────────────────────────────────────────────────────

def test_avanzar_org_existente(db, monkeypatch):
    monkeypatch.setattr("hd_scraper.pipeline_comercial.get_db", lambda: db)
    registrar_org("Acme Corp")
    r = avanzar("Acme Corp", "vigilancia", notas="Evidencia suficiente")
    assert r["etapa_anterior"] == "observacion"
    assert r["etapa"] == "vigilancia"


def test_avanzar_org_inexistente_la_crea(db, monkeypatch):
    monkeypatch.setattr("hd_scraper.pipeline_comercial.get_db", lambda: db)
    r = avanzar("NuevaOrg", "peritaje")
    assert r["accion"] == "creado"
    assert r["etapa"] == "peritaje"


def test_avanzar_con_resultado_cierre(db, monkeypatch):
    monkeypatch.setattr("hd_scraper.pipeline_comercial.get_db", lambda: db)
    registrar_org("Acme Corp")
    r = avanzar("Acme Corp", "cerrado", resultado="ganado")
    assert r["etapa"] == "cerrado"
    assert r["resultado"] == "ganado"


def test_avanzar_resultado_invalido(db, monkeypatch):
    monkeypatch.setattr("hd_scraper.pipeline_comercial.get_db", lambda: db)
    registrar_org("Acme Corp")
    with pytest.raises(ValueError, match="Resultado inválido"):
        avanzar("Acme Corp", "cerrado", resultado="inventado")


def test_avanzar_retroceso_posible(db, monkeypatch):
    monkeypatch.setattr("hd_scraper.pipeline_comercial.get_db", lambda: db)
    registrar_org("Acme Corp", etapa="peritaje")
    r = avanzar("Acme Corp", "vigilancia", notas="Regresar a vigilancia")
    assert r["etapa_anterior"] == "peritaje"
    assert r["etapa"] == "vigilancia"


def test_avanzar_etapa_invalida(db, monkeypatch):
    monkeypatch.setattr("hd_scraper.pipeline_comercial.get_db", lambda: db)
    with pytest.raises(ValueError):
        avanzar("Acme Corp", "invalida")


# ── obtener_pipeline ─────────────────────────────────────────────────────────

def test_obtener_pipeline_existente(db, monkeypatch):
    monkeypatch.setattr("hd_scraper.pipeline_comercial.get_db", lambda: db)
    registrar_org("Acme Corp", etapa="vigilancia")
    p = obtener_pipeline("Acme Corp")
    assert p is not None
    assert p["org_nombre"] == "Acme Corp"
    assert p["etapa"] == "vigilancia"
    assert p["etapa_label"] == "Vigilancia"
    assert len(p["transiciones"]) >= 1


def test_obtener_pipeline_inexistente(db, monkeypatch):
    monkeypatch.setattr("hd_scraper.pipeline_comercial.get_db", lambda: db)
    assert obtener_pipeline("NoExiste") is None


def test_obtener_pipeline_multiples_transiciones(db, monkeypatch):
    monkeypatch.setattr("hd_scraper.pipeline_comercial.get_db", lambda: db)
    registrar_org("Acme Corp")
    avanzar("Acme Corp", "vigilancia")
    avanzar("Acme Corp", "peritaje")
    p = obtener_pipeline("Acme Corp")
    assert len(p["transiciones"]) == 3


# ── listar_pipeline ──────────────────────────────────────────────────────────

def test_listar_pipeline_vacio(db, monkeypatch):
    monkeypatch.setattr("hd_scraper.pipeline_comercial.get_db", lambda: db)
    r = listar_pipeline()
    assert r["total"] == 0
    assert r["organizaciones"] == []


def test_listar_pipeline_con_datos(db, monkeypatch):
    monkeypatch.setattr("hd_scraper.pipeline_comercial.get_db", lambda: db)
    registrar_org("Acme Corp")
    registrar_org("Beta Inc", etapa="vigilancia")
    r = listar_pipeline()
    assert r["total"] == 2
    assert r["por_etapa"]["observacion"] == 1
    assert r["por_etapa"]["vigilancia"] == 1


def test_listar_pipeline_filtro_etapa(db, monkeypatch):
    monkeypatch.setattr("hd_scraper.pipeline_comercial.get_db", lambda: db)
    registrar_org("Acme Corp")
    registrar_org("Beta Inc", etapa="vigilancia")
    r = listar_pipeline(etapa="vigilancia")
    assert r["total"] == 1
    assert r["organizaciones"][0]["org_nombre"] == "Beta Inc"


def test_listar_pipeline_etapa_invalida_muestra_todo(db, monkeypatch):
    monkeypatch.setattr("hd_scraper.pipeline_comercial.get_db", lambda: db)
    registrar_org("Acme Corp")
    r = listar_pipeline(etapa="inventada")
    assert r["total"] == 1


# ── resumen_funnel ───────────────────────────────────────────────────────────

def test_resumen_funnel_vacio(db, monkeypatch):
    monkeypatch.setattr("hd_scraper.pipeline_comercial.get_db", lambda: db)
    r = resumen_funnel()
    assert r["total_organizaciones"] == 0
    assert len(r["funnel"]) == len(ETAPAS)
    assert all(f["total"] == 0 for f in r["funnel"])


def test_resumen_funnel_con_datos(db, monkeypatch):
    monkeypatch.setattr("hd_scraper.pipeline_comercial.get_db", lambda: db)
    registrar_org("A")
    registrar_org("B")
    registrar_org("C", etapa="vigilancia")
    r = resumen_funnel()
    assert r["total_organizaciones"] == 3
    obs = next(f for f in r["funnel"] if f["etapa"] == "observacion")
    vig = next(f for f in r["funnel"] if f["etapa"] == "vigilancia")
    assert obs["total"] == 2
    assert vig["total"] == 1


def test_funnel_orden_etapas(db, monkeypatch):
    monkeypatch.setattr("hd_scraper.pipeline_comercial.get_db", lambda: db)
    r = resumen_funnel()
    etapas = [f["etapa"] for f in r["funnel"]]
    assert etapas == list(ETAPAS)


# ── constantes ───────────────────────────────────────────────────────────────

def test_etapas_son_6():
    assert len(ETAPAS) == 6


def test_etapas_secuencia():
    assert ETAPAS == (
        "observacion", "vigilancia", "peritaje",
        "dolormap", "alianza", "cerrado",
    )


def test_etapas_labels_completas():
    for e in ETAPAS:
        assert e in ETAPAS_LABELS


def test_resultado_cierre():
    assert set(RESULTADO_CIERRE) == {"ganado", "descartado", "pausado"}
