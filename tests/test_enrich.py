"""Enriquecimiento: descubrir web + extraer discurso (con fixtures, sin red)."""
import importlib

import pytest
from fastapi.testclient import TestClient

from hd_scraper.config import settings
from hd_scraper.enrich import (
    elegir_sitio_oficial,
    enriquecer,
    extraer_discurso,
    linkedin_search_url,
    parse_ddg_resultados,
)

DDG_HTML = """
<div><a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fwww.linkedin.com%2Fcompany%2Fkaszek">LinkedIn</a></div>
<div><a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fkaszek.com%2F">Kaszek — sitio oficial</a></div>
"""

SITE_HTML = """
<html><head>
<meta name="description" content="Kaszek es un fondo de venture capital para founders en América Latina.">
</head><body>
<h1>Invertimos en los mejores founders de LatAm</h1>
<p>Respaldamos compañías de tecnología en etapas tempranas con tesis de largo plazo.</p>
<p>corto</p>
</body></html>
"""


def test_parse_ddg_decodifica_uddg():
    urls = parse_ddg_resultados(DDG_HTML)
    assert "https://www.linkedin.com/company/kaszek" in urls
    assert "https://kaszek.com/" in urls


def test_elegir_sitio_ignora_redes():
    urls = ["https://www.linkedin.com/company/x", "https://kaszek.com/"]
    assert elegir_sitio_oficial(urls) == "https://kaszek.com/"


def test_extraer_discurso_incluye_meta_y_parrafos():
    t = extraer_discurso(SITE_HTML)
    assert "venture capital" in t
    assert "mejores founders" in t
    assert "corto" not in t  # descarta fragmentos muy cortos


def test_enriquecer_orquesta(monkeypatch):
    def fake_get(url):
        return DDG_HTML if "duckduckgo" in url else SITE_HTML
    d = enriquecer("Kaszek", fake_get)
    assert d["sitio_web"] == "https://kaszek.com/"
    assert "venture capital" in d["discurso"]
    assert d["linkedin"] == linkedin_search_url("Kaszek")
    assert d["fuentes"] == ["https://kaszek.com/"]


def test_enriquecer_nunca_falla():
    def boom(url):
        raise RuntimeError("sin red")
    d = enriquecer("X", boom)
    assert d["sitio_web"] is None and d["linkedin"].startswith("https://www.linkedin.com")
    assert d["notas"]  # registró la falla, no lanzó


def test_endpoint_enrich_requiere_token(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    object.__setattr__(settings, "ingest_token", "secreto")
    cli = TestClient(api.app)
    assert cli.post("/enrich", json={"nombre": "Kaszek"}).status_code == 401
    object.__setattr__(settings, "ingest_token", "")
