"""Guardia de identidad en el filtro de mención de rss_fijos.py (2026-09-20).

Bug real encontrado en producción: el filtro anterior (`subcadena in texto`,
sin límite de palabra) admitía "mundi" dentro de "mundial" y "clara" dentro
de "declaración"/"aclara". Corregido reutilizando `_ocurrencias_org` (que ya
combina `\\b...\\b` con la Guardia 1, `_es_parte_de_nombre_mas_largo`) de
`clasificacion_epistemologica.py`, sin reimplementar la guardia.
"""
import pytest

from hd_scraper.connectors.rss_fijos import RssFijosConnector
from hd_scraper.db.models import QuerySpec

FEEDS = {"Medio X": "https://medio-x.example/feed/"}


def _feed_con_titular(titular: str, link: str = "https://medio-x.example/nota") -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Medio X</title>
  <item>
    <title>{titular}</title>
    <link>{link}</link>
    <description>Sin descripción relevante.</description>
    <pubDate>Wed, 01 Jul 2026 10:00:00 GMT</pubDate>
  </item>
</channel></rss>
"""


def _connector(monkeypatch, feed_xml: str) -> RssFijosConnector:
    c = RssFijosConnector(feeds=FEEDS)

    def fake_get(url: str) -> str:
        if url.endswith("/feed/"):
            return feed_xml
        # Fetch del cuerpo del artículo (JSON-LD): sin bloque reconocible,
        # degrada a solo titular — no afecta esta prueba del filtro.
        return "<html><body>sin json-ld</body></html>"

    monkeypatch.setattr(c, "_get", fake_get)
    return c


def _buscar(monkeypatch, empresa: str, titular: str) -> list:
    c = _connector(monkeypatch, _feed_con_titular(titular))
    return list(c.search(QuerySpec(empresa=empresa, tipo_evento="ronda")))


def test_mundi_dentro_de_mundial_queda_bloqueado(monkeypatch):
    """Caso real de producción: 'otros gigantes mundiales' / 'futbol mundial'
    no debe atribuirse a la organización 'Mundi'."""
    items = _buscar(monkeypatch, "Mundi",
                    "México y otros gigantes mundiales lideran la alerta sísmica")
    assert items == []


def test_clara_dentro_de_declaracion_queda_bloqueado(monkeypatch):
    """Caso real de producción: 'declaraciones de impuestos' no debe
    atribuirse a la organización 'Clara'."""
    items = _buscar(monkeypatch, "Clara",
                    "EU preguntará por estatus de ciudadanía en declaraciones de impuestos")
    assert items == []


def test_clara_dentro_de_aclara_queda_bloqueado(monkeypatch):
    """Caso real de producción: 'el gobierno aclara la situación' no debe
    atribuirse a la organización 'Clara'."""
    items = _buscar(monkeypatch, "Clara",
                    "El gobierno aclara la situación de la deuda pública")
    assert items == []


def test_nombre_como_palabra_independiente_pasa(monkeypatch):
    """Control positivo: la organización mencionada como palabra completa
    (sin coincidencia parcial) sigue detectándose con normalidad."""
    items = _buscar(monkeypatch, "Clara",
                    "Clara, la fintech mexicana, levanta 33.5 mdd")
    assert len(items) == 1


def test_mundi_como_palabra_independiente_pasa(monkeypatch):
    items = _buscar(monkeypatch, "Mundi",
                    "Mundi destinaría 20,000 millones de pesos al financiamiento de pymes")
    assert len(items) == 1


def test_clara_brugada_sigue_bloqueada_mismo_criterio_que_construir_expedientes(monkeypatch):
    """La Guardia 1 (adyacencia a otro nombre propio) sigue aplicando aquí
    igual que en _construir_expedientes: 'Clara Brugada' no es la fintech."""
    items = _buscar(monkeypatch, "Clara", "Clara Brugada, entre los mandatarios mejor evaluados")
    assert items == []
