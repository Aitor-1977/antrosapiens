import json

from hd_scraper.config import settings
from hd_scraper.connectors.busqueda_dinamica import BusquedaDinamicaConnector
from hd_scraper.db.models import ESTADO_NO_FECHADO, ESTADO_OK, QuerySpec

FIXTURE_RESPUESTA = {
    "items": [
        {
            "title": "Cometí el error de contratar rápido sin cultura clara",
            "link": "https://blog.ejemplo.com/error-contratacion",
            "snippet": "En mi startup, cometí el error de crecer el equipo antes de tener claridad de cultura...",
            "pagemap": {
                "metatags": [{"article:published_time": "2026-06-01T10:00:00Z"}]
            },
        },
        {
            "title": "Sin fecha: reflexión sobre un error de founder",
            "link": "https://medium.com/@founder/reflexion-error",
            "snippet": "Una historia sin metadatos de fecha.",
        },
    ]
}


def _connector(monkeypatch, frases=None) -> BusquedaDinamicaConnector:
    object.__setattr__(settings, "google_cse_api_key", "fake-key")
    object.__setattr__(settings, "google_cse_cx", "fake-cx")
    c = BusquedaDinamicaConnector(frases=frases)
    monkeypatch.setattr(c, "_get", lambda url: json.dumps(FIXTURE_RESPUESTA))
    return c


def test_sin_credenciales_no_hace_red_y_devuelve_vacio(monkeypatch):
    object.__setattr__(settings, "google_cse_api_key", "")
    object.__setattr__(settings, "google_cse_cx", "")
    c = BusquedaDinamicaConnector()

    def _falla(url):  # pragma: no cover - no debe llamarse
        raise AssertionError("no debe llamar a la red sin credenciales")

    monkeypatch.setattr(c, "_get", _falla)
    items = list(c.search(QuerySpec(empresa="x", tipo_evento="queja")))
    assert items == []


def test_search_extrae_items_de_cada_frase(monkeypatch):
    frases = (('"cometí el error de" startup', "queja"),)
    c = _connector(monkeypatch, frases=frases)
    items = list(c.search(QuerySpec(empresa="x", tipo_evento="queja")))
    assert len(items) == 2
    assert items[0].meta["frase"] == '"cometí el error de" startup'
    assert items[0].meta["tipo_evento"] == "queja"
    assert items[0].meta["fecha_publicacion"] == "2026-06-01T10:00:00Z"
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
    assert rec.connector == "busqueda_dinamica_founder"


def test_valida_ok_y_no_fechado(monkeypatch):
    frases = (('"cometí el error de" startup', "queja"),)
    c = _connector(monkeypatch, frases=frases)
    items = list(c.search(QuerySpec(empresa="x", tipo_evento="queja")))
    v0 = c.validate(c.normalize(items[0]))
    v1 = c.validate(c.normalize(items[1]))
    assert v0.ok and v0.estado == ESTADO_OK
    assert v1.ok and v1.estado == ESTADO_NO_FECHADO


FIXTURE_CON_AUTOR = {
    "items": [
        {
            "title": "Founder de Acme: cometí el error de contratar sin cultura",
            "link": "https://medium.com/@ana/error-contratacion",
            "snippet": "Cometí el error de crecer el equipo demasiado rápido.",
            "pagemap": {
                "person": [{"name": "Ana Torres", "jobtitle": "Founder"}],
                "metatags": [{"article:published_time": "2026-06-01T10:00:00Z"}],
            },
        },
        {
            "title": "Sin metadata de autor",
            "link": "https://blog.ejemplo.com/error-generico",
            "snippet": "Una historia sin schema.org Person ni metatags de autoría.",
            "pagemap": {
                "metatags": [{"article:published_time": "2026-06-02T10:00:00Z"}],
            },
        },
        {
            "title": "Autor solo por metatag",
            "link": "https://blog.ejemplo.com/con-metatag-autor",
            "snippet": "El autor viene declarado por metatag, no por schema.org Person.",
            "pagemap": {
                "metatags": [{"author": "Luis Gómez", "article:published_time": "2026-06-03T10:00:00Z"}],
            },
        },
    ]
}


def test_persona_y_cargo_solo_si_hay_metadata_estructural(monkeypatch):
    frases = (('"cometí el error de" startup', "queja"),)
    object.__setattr__(settings, "google_cse_api_key", "fake-key")
    object.__setattr__(settings, "google_cse_cx", "fake-cx")
    c = BusquedaDinamicaConnector(frases=frases)
    monkeypatch.setattr(c, "_get", lambda url: json.dumps(FIXTURE_CON_AUTOR))

    items = list(c.search(QuerySpec(empresa="x", tipo_evento="queja")))
    recs = [c.normalize(it) for it in items]

    # schema.org Person: persona_citada + cargo estructurales.
    assert recs[0].persona_citada == "Ana Torres"
    assert recs[0].cargo == "Founder"
    # sin metadata de autor: ambos None (igual que Fase 1).
    assert recs[1].persona_citada is None
    assert recs[1].cargo is None
    # solo metatag de autor (sin jobtitle): persona sí, cargo no.
    assert recs[2].persona_citada == "Luis Gómez"
    assert recs[2].cargo is None


def test_una_frase_caida_no_tumba_a_las_demas(monkeypatch):
    frases = (
        ('"frase que falla"', "queja"),
        ('"cometí el error de" startup', "queja"),
    )
    object.__setattr__(settings, "google_cse_api_key", "fake-key")
    object.__setattr__(settings, "google_cse_cx", "fake-cx")
    c = BusquedaDinamicaConnector(frases=frases)

    def _get(url):
        if "frase+que+falla" in url:
            raise RuntimeError("500 boom")
        return json.dumps(FIXTURE_RESPUESTA)

    monkeypatch.setattr(c, "_get", _get)
    items = list(c.search(QuerySpec(empresa="x", tipo_evento="queja")))
    assert len(items) == 2  # solo los de la segunda frase
    eventos = c.drain_health_events()
    ok_por_frase = {f: ok for f, ok, _ in eventos}
    assert ok_por_frase['busqueda_dinamica_founder:"frase que falla"'] is False
