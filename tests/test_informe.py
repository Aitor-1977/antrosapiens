"""Análisis profundo expuesto por la API: /informe y /analizar."""
import importlib

import pytest
from fastapi.testclient import TestClient

from hd_scraper.config import settings
from tests.test_google_news import FIXTURE_RSS


@pytest.fixture()
def cli(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    object.__setattr__(settings, "ingest_token", "secreto-123")
    from hd_scraper.connectors.google_news import GoogleNewsConnector
    monkeypatch.setattr(GoogleNewsConnector, "_get", lambda self, url: FIXTURE_RSS)
    yield TestClient(api.app)
    object.__setattr__(settings, "ingest_token", "")


H = {"X-Ingest-Token": "secreto-123"}


def test_analizar_publico_devuelve_scoring_y_deuda(cli):
    r = cli.post("/analizar", json={"titulo": "Konfío enfrenta quejas y churn de clientes",
                                    "vertical": "fintech", "confianza": 0.8, "calidad": "Alta"})
    assert r.status_code == 200
    d = r.json()
    assert d["scoring"] == "A"
    assert d["tipo_deuda"] == "Deuda Relacional"
    assert d["score_icp"] >= 70
    assert "friccion_retencion" in d["keywords"]


def test_analizar_sin_senal_da_c(cli):
    r = cli.post("/analizar", json={"titulo": "Empresa celebra su aniversario"})
    assert r.status_code == 200 and r.json()["scoring"] == "C"


def test_informe_prioriza_y_resume(cli):
    # Sembramos evidencia real vía scrape (fixture), luego pedimos el informe.
    cli.post("/scrape", json={"empresa": "Nubank", "tipo_evento": "ronda",
                              "connectors": ["google_news"]}, headers=H)
    r = cli.get("/informe")
    assert r.status_code == 200
    d = r.json()
    assert "resumen_scoring" in d and set(d["resumen_scoring"]) == {"A", "B", "C"}
    assert isinstance(d["prospectos"], list)
    # Cada tarjeta trae la interpretación profunda.
    if d["prospectos"]:
        t = d["prospectos"][0]
        for k in ("empresa", "scoring", "tipo_deuda", "score_icp", "decisor_sugerido"):
            assert k in t


def test_informe_categoria_invalida_400(cli):
    assert cli.get("/informe", params={"categoria": "Fondo"}).status_code == 400
