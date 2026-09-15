"""Pruebas de POST /mobile/scrape — BFF de búsqueda en vivo para Android,
SIN X-Ingest-Token (ver hd_scraper/api/app.py:mobile_scrape).

No reimplementa /scrape: usa el mismo `_correr_query`, mismos conectores
reales (mockeados aquí para no salir a red), mismo contrato de evidencia.
"""
import importlib

import pytest
from fastapi.testclient import TestClient

from hd_scraper.api.app import _MOBILE_RATE_LIMIT_MAX, _mobile_rate_ventanas
from hd_scraper.config import settings
from tests.test_gdelt import FIXTURE_JSON as GDELT_FIXTURE
from tests.test_google_news import FIXTURE_RSS


@pytest.fixture()
def cli(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    # /mobile/scrape NUNCA exige X-Ingest-Token: se deja configurado igual
    # para probar, en test aparte, que jamás aparece en la respuesta.
    object.__setattr__(settings, "ingest_token", "secreto-123")
    # Evita red real: ambos conectores que /mobile/scrape usa (fijos, no
    # elegibles por el cliente) devuelven fixtures ya usados en sus propias
    # suites (test_google_news.py, test_gdelt.py).
    from hd_scraper.connectors.gdelt import GdeltConnector
    from hd_scraper.connectors.google_news import GoogleNewsConnector
    monkeypatch.setattr(GoogleNewsConnector, "_get", lambda self, url: FIXTURE_RSS)
    monkeypatch.setattr(GdeltConnector, "_get", lambda self, url: GDELT_FIXTURE)
    _mobile_rate_ventanas.clear()
    yield TestClient(api.app)
    object.__setattr__(settings, "ingest_token", "")
    _mobile_rate_ventanas.clear()


def test_mobile_scrape_payload_valido_escribe_evidencia(cli, db):
    r = cli.post("/mobile/scrape", json={"empresa": "Nubank"})
    assert r.status_code == 200
    d = r.json()
    assert d["ok"] is True
    assert d["new_evidence"] > 0
    assert db.fetch_one("SELECT COUNT(*) n FROM evidencias")["n"] == d["new_evidence"]


def test_mobile_scrape_payload_invalido_422(cli):
    assert cli.post("/mobile/scrape", json={"empresa": ""}).status_code == 422
    assert cli.post("/mobile/scrape", json={"empresa": "   "}).status_code == 422
    assert cli.post("/mobile/scrape", json={"empresa": "x" * 201}).status_code == 422
    # Sin el campo obligatorio: error de validación de pydantic (422).
    assert cli.post("/mobile/scrape", json={}).status_code == 422


def test_mobile_scrape_conectores_fijos_no_elegibles_por_el_cliente(cli):
    # El cliente NO puede pedir otros conectores ni ampliar la lista: el
    # payload solo declara "empresa" (pydantic ignora cualquier otro campo).
    r = cli.post("/mobile/scrape", json={
        "empresa": "Nubank", "connectors": ["job_boards"], "categoria": "VC",
    })
    assert r.status_code == 200
    assert sorted(r.json()["connectors"]) == ["gdelt", "google_news"]


def test_mobile_scrape_nunca_expone_el_token(cli):
    r = cli.post("/mobile/scrape", json={"empresa": "Nubank"})
    cuerpo = r.text
    assert "secreto-123" not in cuerpo
    assert "ingest" not in cuerpo.lower()
    assert "token" not in cuerpo.lower()


def test_mobile_scrape_delega_en_correr_query_existente(cli):
    # Mismo contrato de "resultados" que ya expone /scrape para cada
    # conector (vistos/escritos/filtrados/...), no uno reinventado.
    r = cli.post("/mobile/scrape", json={"empresa": "Nubank"})
    resultados = r.json()["resultados"]
    conectores_reportados = {x["connector"] for x in resultados}
    assert conectores_reportados == {"google_news", "gdelt"}
    for x in resultados:
        assert "vistos" in x and "escritos" in x and "filtrados" in x


def test_mobile_scrape_respuesta_incluye_timestamp_y_live(cli):
    r = cli.post("/mobile/scrape", json={"empresa": "Nubank"})
    d = r.json()
    assert d["live"] is True
    assert d["timestamp"]


def test_mobile_scrape_busqueda_real_sin_resultados_no_es_error(cli, monkeypatch):
    # LIVE_SEARCH_EMPTY: se buscó de verdad y no había nada nuevo -> 200 con
    # new_evidence=0, nunca un error. Ambos conectores sin artículos.
    monkeypatch.setattr(
        "hd_scraper.connectors.google_news.GoogleNewsConnector._get",
        lambda self, url: '<?xml version="1.0"?><rss><channel></channel></rss>',
    )
    monkeypatch.setattr(
        "hd_scraper.connectors.gdelt.GdeltConnector._get",
        lambda self, url: '{"articles": []}',
    )
    r = cli.post("/mobile/scrape", json={"empresa": "OrganizacionSinNoticias"})
    assert r.status_code == 200
    d = r.json()
    assert d["ok"] is True and d["live"] is True
    assert d["new_evidence"] == 0


def test_mobile_scrape_rate_limit(cli):
    for _ in range(_MOBILE_RATE_LIMIT_MAX):
        assert cli.post("/mobile/scrape", json={"empresa": "Nubank"}).status_code == 200
    r = cli.post("/mobile/scrape", json={"empresa": "Nubank"})
    assert r.status_code == 429


def test_scrape_sigue_exigiendo_token_sin_cambios(cli):
    # /mobile/scrape es una superficie DISTINTA: /scrape conserva su
    # protección de siempre, sin debilitarse por la existencia de la nueva.
    r = cli.post("/scrape", json={"empresa": "Nubank"})
    assert r.status_code == 401
