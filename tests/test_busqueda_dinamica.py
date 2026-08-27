import json

from hd_scraper.config import settings
from hd_scraper.connectors.busqueda_dinamica import BusquedaDinamicaConnector
from hd_scraper.db.models import ESTADO_NO_FECHADO, ESTADO_OK, QuerySpec

FIXTURE_RESPUESTA = {
    "query": '"cometí el error de" startup',
    "results": [
        {
            "title": "Cometí el error de contratar rápido sin cultura clara",
            "url": "https://blog.ejemplo.com/error-contratacion",
            "content": "En mi startup, cometí el error de crecer el equipo antes de tener claridad de cultura...",
            "raw_content": "Texto completo del artículo, mucho más largo que el resumen.",
            "published_date": "2026-06-01",
            "score": 0.9,
        },
        {
            "title": "Sin fecha: reflexión sobre un error de founder",
            "url": "https://medium.com/@founder/reflexion-error",
            "content": "Una historia sin metadata de fecha.",
            "raw_content": "",
        },
    ],
}


def _connector(monkeypatch, frases=None) -> BusquedaDinamicaConnector:
    object.__setattr__(settings, "tavily_api_key", "tvly-fake-key")
    c = BusquedaDinamicaConnector(frases=frases)
    monkeypatch.setattr(c, "_post", lambda url, payload: json.dumps(FIXTURE_RESPUESTA))
    return c


def test_sin_credenciales_no_hace_red_y_devuelve_vacio(monkeypatch):
    object.__setattr__(settings, "tavily_api_key", "")
    c = BusquedaDinamicaConnector()

    def _falla(url, payload):  # pragma: no cover - no debe llamarse
        raise AssertionError("no debe llamar a la red sin credenciales")

    monkeypatch.setattr(c, "_post", _falla)
    items = list(c.search(QuerySpec(empresa="x", tipo_evento="queja")))
    assert items == []


def test_search_extrae_items_de_cada_frase(monkeypatch):
    frases = (('"cometí el error de" startup', "queja"),)
    c = _connector(monkeypatch, frases=frases)
    items = list(c.search(QuerySpec(empresa="x", tipo_evento="queja")))
    assert len(items) == 2
    assert items[0].meta["frase"] == '"cometí el error de" startup'
    assert items[0].meta["tipo_evento"] == "queja"
    assert items[0].meta["fecha_publicacion"] == "2026-06-01"
    assert items[1].meta["fecha_publicacion"] is None


def test_normalize_no_interpreta_usa_estructura(monkeypatch):
    frases = (('"cometí el error de" startup', "queja"),)
    c = _connector(monkeypatch, frases=frases)
    items = list(c.search(QuerySpec(empresa="x", tipo_evento="queja")))
    rec = c.normalize(items[0])
    # tipo_evento viene de la frase declarada en el módulo, no del contenido:
    assert rec.tipo_evento == "queja"
    # origen_declaracion es estructural para este léxico (primera persona):
    assert rec.origen_declaracion == "usuario"
    # empresa_mencionada es el TÉRMINO de búsqueda, no una empresa detectada:
    assert rec.empresa_mencionada == '"cometí el error de" startup'
    # nombre_medio es el dominio de la URL, no algo leído del contenido:
    assert rec.nombre_medio == "blog.ejemplo.com"
    assert rec.cita_textual.startswith("Cometí el error de contratar rápido")
    assert "Texto completo del artículo" in rec.cita_textual
    assert rec.connector == "busqueda_dinamica_founder"
    assert rec.persona_citada is None
    assert rec.cargo is None


def test_valida_ok_y_no_fechado(monkeypatch):
    frases = (('"cometí el error de" startup', "queja"),)
    c = _connector(monkeypatch, frases=frases)
    items = list(c.search(QuerySpec(empresa="x", tipo_evento="queja")))
    v0 = c.validate(c.normalize(items[0]))
    v1 = c.validate(c.normalize(items[1]))
    assert v0.ok and v0.estado == ESTADO_OK
    assert v1.ok and v1.estado == ESTADO_NO_FECHADO


def test_una_frase_caida_no_tumba_a_las_demas(monkeypatch):
    frases = (
        ('"frase que falla"', "queja"),
        ('"cometí el error de" startup', "queja"),
    )
    object.__setattr__(settings, "tavily_api_key", "tvly-fake-key")
    c = BusquedaDinamicaConnector(frases=frases)

    def _post(url, payload):
        if payload["query"] == '"frase que falla"':
            raise RuntimeError("500 boom")
        return json.dumps(FIXTURE_RESPUESTA)

    monkeypatch.setattr(c, "_post", _post)
    items = list(c.search(QuerySpec(empresa="x", tipo_evento="queja")))
    assert len(items) == 2  # solo los de la segunda frase
    eventos = c.drain_health_events()
    ok_por_frase = {f: ok for f, ok, _ in eventos}
    assert ok_por_frase['busqueda_dinamica_founder:"frase que falla"'] is False
