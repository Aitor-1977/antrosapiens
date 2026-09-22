"""Integración de GET /ficha-prospeccion/{org_nombre} (Capa 20)."""
import importlib

import pytest
from fastapi.testclient import TestClient

from hd_scraper.db.models import ahora_iso


@pytest.fixture()
def client(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    yield TestClient(api.app)


def _evidencia(db, n, org, cita, *, fecha_publicacion=None, nombre_medio="Greenhouse",
               origen_declaracion="operador", persona_citada=None, cargo=None):
    return db.insert_returning_id(
        "INSERT INTO evidencias (cita_textual, fecha_extraccion, url_fuente, "
        "nombre_medio, empresa_mencionada, tipo_evento, origen_declaracion, "
        "hash_dedup, connector, fecha_publicacion, persona_citada, cargo, creado_en) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (cita, ahora_iso(), f"https://ej.test/{n}", nombre_medio, org,
         "contratacion", origen_declaracion, f"hfp{n}", "job_boards",
         fecha_publicacion, persona_citada, cargo, ahora_iso()))


def _clasificar(db, evidencia_id, tipo):
    db.execute(
        "INSERT INTO evidencia_clasificada (expediente_id, evidencia_id, "
        "tipo_epistemologico) VALUES (?,?,?)",
        (None, evidencia_id, tipo))


def test_endpoint_devuelve_fichas_agrupadas_por_situacion(client, db):
    e1 = _evidencia(db, 1, "Clara", "Reduce customer churn across accounts.",
                     fecha_publicacion="2026-01-01")
    e2 = _evidencia(db, 2, "Clara", "Investigate churn drivers in the funnel.",
                     fecha_publicacion="2026-01-05")
    e3 = _evidencia(db, 3, "Clara", "Buscamos mejorar procesos internos.")
    _clasificar(db, e1, "senal_primaria_huella_practica")
    _clasificar(db, e2, "senal_primaria_huella_practica")
    _clasificar(db, e3, "senal_primaria_huella_practica")

    r = client.get("/ficha-prospeccion/Clara")
    assert r.status_code == 200
    d = r.json()
    assert d["organizacion"] == "Clara"
    assert d["evidencia_evaluada"] == 3
    assert d["total_fichas"] == 1
    ficha = d["fichas"][0]
    assert ficha["situacion_observable"] == "churn"
    assert ficha["recurrencia"] == 2
    assert ficha["estado_evaluacion"] == "PROSPECTO_INVESTIGABLE"
    assert "fit_comercial" in ficha
    assert "score_icp" in ficha["fit_comercial"]


def test_endpoint_sin_evidencia_devuelve_vacio(client, db):
    r = client.get("/ficha-prospeccion/Desconocida")
    assert r.status_code == 200
    d = r.json()
    assert d["organizacion"] == "Desconocida"
    assert d["total_fichas"] == 0
    assert d["fichas"] == []
    assert d["evidencia_evaluada"] == 0


def test_endpoint_evidencia_generica_no_produce_fichas(client, db):
    e1 = _evidencia(db, 1, "Acme", "Buscamos optimizar procesos y mejorar eficiencia.")
    _clasificar(db, e1, "senal_primaria_huella_practica")

    r = client.get("/ficha-prospeccion/Acme")
    d = r.json()
    assert d["evidencia_evaluada"] == 1
    assert d["total_fichas"] == 0


def test_endpoint_es_case_insensitive_al_nombre(client, db):
    e1 = _evidencia(db, 1, "Clara", "We track customer churn closely.")
    _clasificar(db, e1, "senal_primaria_autodeclaracion")

    r = client.get("/ficha-prospeccion/clara")
    d = r.json()
    assert d["total_fichas"] == 1
