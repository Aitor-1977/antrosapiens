"""Pruebas del endpoint temporal de escritura
POST /ops/rss-directo-una-vez-7f3c1a9d2e (corrida única pedida por Mario,
2026-09-20, para verificar la ampliación de RSS directo). Se elimina junto
con el endpoint al cerrar el encargo.
"""
import importlib

import pytest
from fastapi.testclient import TestClient

from hd_scraper.config import settings

RUTA = "/ops/rss-directo-una-vez-7f3c1a9d2e"

FEED_MUNDI = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>DPL News</title>
  <item>
    <title>Mundi lanza nueva línea de crédito para pymes exportadoras</title>
    <link>https://dplnews.com/mundi-credito</link>
    <description>La fintech amplía su oferta.</description>
    <pubDate>Wed, 01 Jul 2026 10:00:00 GMT</pubDate>
  </item>
</channel></rss>
"""

ARTICULO_MUNDI = (
    '<html><head><script type="application/ld+json">'
    '{"@type": "NewsArticle", '
    '"articleBody": "Ana Ruiz, CEO de Mundi, declar\\u00f3 que la nueva '
    'linea de credito llega en un momento clave.", '
    '"datePublished": "2026-07-01T09:00:00-05:00"}'
    '</script></head></html>'
)


@pytest.fixture()
def cli(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    object.__setattr__(settings, "ingest_token", "secreto-123")
    yield TestClient(api.app)
    object.__setattr__(settings, "ingest_token", "")


H = {"X-Ingest-Token": "secreto-123"}


def test_requiere_token(cli):
    assert cli.post(RUTA, json={"empresas": ["Mundi"]}).status_code == 401


def test_tipo_evento_invalido_se_rechaza(cli):
    r = cli.post(RUTA, json={"empresas": ["Mundi"], "tipo_evento": "no_existe"}, headers=H)
    assert r.status_code == 400


def test_corre_solo_sobre_los_4_medios_nuevos(cli, db, monkeypatch):
    def fake_get(self, url):
        if "dplnews.com/feed" in url:
            return FEED_MUNDI
        if url == "https://dplnews.com/mundi-credito":
            return ARTICULO_MUNDI
        # Cualquier otro feed configurado (los 11 de FEEDS_DEFAULT) no debe
        # tocarse: esta corrida está acotada a los 4 medios nuevos.
        return """<?xml version="1.0"?><rss version="2.0"><channel></channel></rss>"""

    monkeypatch.setattr(
        "hd_scraper.connectors.rss_fijos.RssFijosConnector._get", fake_get)
    r = cli.post(RUTA, json={"empresas": ["Mundi"], "tipo_evento": "ronda"}, headers=H)
    assert r.status_code == 200
    data = r.json()["resultados"][0]
    assert data["empresa"] == "Mundi"
    assert data["escritos"] == 1
    # Clasifica lo recién escrito (acotado por organización, no todo el
    # corpus): la cita real trae "Ana Ruiz, CEO de Mundi, declaró...",
    # patrón Nombre+cargo+verbo declarativo -> autodeclaración.
    assert data["clasificacion"]["senal_primaria_autodeclaracion"] == 1

    fila = db.fetch_one(
        "SELECT cita_textual, nombre_medio, connector FROM evidencias "
        "WHERE empresa_mencionada = 'Mundi' ORDER BY id DESC LIMIT 1")
    assert fila is not None
    assert fila["connector"] == "rss_fijos"
    assert fila["nombre_medio"] == "DPL News"
    assert "Ana Ruiz, CEO de Mundi, declaró" in fila["cita_textual"]
