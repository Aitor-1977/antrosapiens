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


def test_informe_acepta_varias_categorias(cli):
    r = cli.get("/informe", params={"categorias": "VC,Startup"})
    assert r.status_code == 200
    assert set(r.json()["categorias"]) == {"VC", "Startup"}
    # Categoría inválida dentro de la lista -> 400.
    assert cli.get("/informe", params={"categorias": "VC,Fondo"}).status_code == 400


def test_guardar_listar_y_descargar_investigacion(cli):
    # Sembramos algo de evidencia para que el informe tenga cuerpo.
    cli.post("/scrape", json={"empresa": "Nubank", "tipo_evento": "ronda",
                              "connectors": ["google_news"]}, headers=H)
    # Requiere token.
    assert cli.post("/informe/guardar", json={"categorias": ""}).status_code == 401
    g = cli.post("/informe/guardar", json={"categorias": ""}, headers=H)
    assert g.status_code == 200
    rid = g.json()["id"]
    # Aparece en la lista.
    lista = cli.get("/informes").json()
    assert any(i["id"] == rid for i in lista["items"])
    # Se descarga su Markdown.
    md = cli.get(f"/informes/{rid}.md")
    assert md.status_code == 200 and "# Informe profundo" in md.text
    assert "text/markdown" in md.headers["content-type"]
    # Un id inexistente -> 404.
    assert cli.get("/informes/999999.md").status_code == 404


def test_export_md_por_varias_categorias(cli):
    r = cli.get("/informe.md", params={"categorias": "VC,Startup"})
    assert r.status_code == 200 and "Ecosistema(s)" in r.text


def test_analizar_con_dominio_devuelve_contacto(cli):
    r = cli.post("/analizar", json={
        "titulo": "Clara enfrenta despidos y reestructuración",
        "dominio": "clara.com", "nombre_decisor": "Ana Ruiz",
    })
    assert r.status_code == 200
    c = r.json()["contacto"]
    assert c["email_sugerido"] == "ana.ruiz@clara.com"
    assert c["verificado"] is False


def test_informe_tarjeta_incluye_intensidad_y_contacto(cli):
    cli.post("/scrape", json={"empresa": "Nubank", "tipo_evento": "ronda",
                              "connectors": ["google_news"]}, headers=H)
    d = cli.get("/informe").json()
    if d["prospectos"]:
        t = d["prospectos"][0]
        assert "intensidad" in t and "deuda_secundaria" in t and "contacto" in t


def test_informe_export_markdown(cli):
    cli.post("/scrape", json={"empresa": "Nubank", "tipo_evento": "ronda",
                              "connectors": ["google_news"]}, headers=H)
    r = cli.get("/informe.md")
    assert r.status_code == 200
    assert "text/markdown" in r.headers["content-type"]
    assert "attachment" in r.headers["content-disposition"]
    assert "# Informe profundo" in r.text


def test_informe_export_csv(cli):
    cli.post("/scrape", json={"empresa": "Nubank", "tipo_evento": "ronda",
                              "connectors": ["google_news"]}, headers=H)
    r = cli.get("/informe.csv")
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    assert r.text.splitlines()[0].startswith("empresa,scoring,score_icp")
