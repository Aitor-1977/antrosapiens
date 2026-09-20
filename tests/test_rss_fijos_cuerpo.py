"""Cuerpo del artículo vía JSON-LD en rss_fijos (2026-09-20).

Resuelve el techo confirmado empíricamente contra 25 URLs reales de Google
News (0/25 con cuerpo recuperable sin JavaScript): el RSS directo del medio
sí trae una URL real navegable, y su página SÍ suele declarar un bloque
JSON-LD Article/NewsArticle/BlogPosting con el cuerpo. Estructural, no
interpretación: solo se lee el JSON que el propio medio ya declara.
"""
from hd_scraper.connectors.rss_fijos import (
    MAX_CUERPO_CHARS,
    RssFijosConnector,
    _extraer_json_ld_articulo,
)
from hd_scraper.db.models import QuerySpec


def _html_con_json_ld(tipo="NewsArticle", article_body=None, description=None,
                      date_published="2026-09-20T10:00:17-06:00"):
    campos = [f'"@type": "{tipo}"', f'"datePublished": "{date_published}"']
    if article_body is not None:
        campos.append(f'"articleBody": {article_body!r}'.replace("'", '"'))
    if description is not None:
        campos.append(f'"description": {description!r}'.replace("'", '"'))
    bloque = "{" + ", ".join(campos) + "}"
    return f"<html><head><script type=\"application/ld+json\">{bloque}</script></head><body></body></html>"


# ── _extraer_json_ld_articulo (función pura) ────────────────────────────────

def test_extrae_article_body_cuando_esta_presente():
    html = _html_con_json_ld(article_body="Cuerpo completo del artículo real.")
    info = _extraer_json_ld_articulo(html)
    assert info is not None
    assert info["cuerpo"] == "Cuerpo completo del artículo real."
    assert info["fecha_publicacion"] == "2026-09-20T10:00:17-06:00"


def test_cae_a_description_si_no_hay_article_body():
    """Caso real encontrado en producción (El Financiero, 2026-09-20):
    articleBody vacío, pero description sí trae un resumen real."""
    html = _html_con_json_ld(article_body="", description="Resumen real del hecho.")
    info = _extraer_json_ld_articulo(html)
    assert info["cuerpo"] == "Resumen real del hecho."


def test_ningun_bloque_json_ld_devuelve_none():
    assert _extraer_json_ld_articulo("<html><body>sin json-ld</body></html>") is None


def test_json_ld_de_tipo_no_articulo_se_ignora():
    """Un bloque JSON-LD de @type Organization/WebSite (navegación, footer)
    no debe confundirse con el artículo."""
    html = ('<html><head><script type="application/ld+json">'
            '{"@type": "Organization", "name": "Medio X"}'
            '</script></head></html>')
    assert _extraer_json_ld_articulo(html) is None


def test_json_ld_malformado_no_rompe_nada():
    html = '<html><head><script type="application/ld+json">{esto no es json}</script></head></html>'
    assert _extraer_json_ld_articulo(html) is None


def test_cuerpo_se_recorta_al_tope():
    largo = "x" * (MAX_CUERPO_CHARS + 500)
    html = _html_con_json_ld(article_body=largo)
    info = _extraer_json_ld_articulo(html)
    assert len(info["cuerpo"]) == MAX_CUERPO_CHARS


def test_array_de_bloques_ld_encuentra_el_articulo():
    """Muchas páginas reales (DPL News, El CEO, Expansión) traen varios
    bloques JSON-LD (BreadcrumbList, Organization, NewsArticle...)."""
    html = (
        '<html><head>'
        '<script type="application/ld+json">{"@type": "BreadcrumbList"}</script>'
        '<script type="application/ld+json">'
        '{"@type": "NewsArticle", "articleBody": "El cuerpo real.", '
        '"datePublished": "2026-09-19T21:45:12.504Z"}'
        '</script></head></html>'
    )
    info = _extraer_json_ld_articulo(html)
    assert info["cuerpo"] == "El cuerpo real."
    assert info["fecha_publicacion"] == "2026-09-19T21:45:12.504Z"


# ── Integración con el conector ──────────────────────────────────────────

FEED_NUBANK = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Medio X</title>
  <item>
    <title>Nubank lanza nuevo producto en México</title>
    <link>https://medio-x.example/articulo-nubank</link>
    <description>La fintech anuncia expansión.</description>
    <pubDate>Wed, 01 Jul 2026 10:00:00 GMT</pubDate>
  </item>
</channel></rss>
"""

ARTICULO_CON_CUERPO = _html_con_json_ld(
    article_body="Juan Pérez, CEO de Nubank, declaró que la expansión continuará.",
    date_published="2026-07-01T09:00:00-05:00",
)


def _connector_con(feed_map: dict[str, str]) -> RssFijosConnector:
    return RssFijosConnector(feeds=feed_map)


def test_cita_textual_incluye_titular_y_cuerpo(monkeypatch):
    c = _connector_con({"Medio X": "https://medio-x.example/feed/"})

    def fake_get(url: str) -> str:
        if url.endswith("/feed/"):
            return FEED_NUBANK
        if url == "https://medio-x.example/articulo-nubank":
            return ARTICULO_CON_CUERPO
        raise AssertionError(f"URL inesperada: {url}")

    monkeypatch.setattr(c, "_get", fake_get)
    items = list(c.search(QuerySpec(empresa="Nubank", tipo_evento="lanzamiento")))
    assert len(items) == 1
    rec = c.normalize(items[0])
    assert rec.cita_textual.startswith("Nubank lanza nuevo producto en México.")
    assert "Juan Pérez, CEO de Nubank, declaró" in rec.cita_textual
    # Nunca se rellenan desde el autor de la nota: eso es trabajo exclusivo
    # de clasificacion_epistemologica.py sobre cita_textual, no de este conector.
    assert rec.persona_citada is None
    assert rec.cargo is None


def test_fecha_publicacion_prefiere_json_ld_sobre_el_feed(monkeypatch):
    c = _connector_con({"Medio X": "https://medio-x.example/feed/"})

    def fake_get(url: str) -> str:
        if url.endswith("/feed/"):
            return FEED_NUBANK
        return ARTICULO_CON_CUERPO

    monkeypatch.setattr(c, "_get", fake_get)
    items = list(c.search(QuerySpec(empresa="Nubank", tipo_evento="lanzamiento")))
    rec = c.normalize(items[0])
    # El feed trae "Wed, 01 Jul 2026 10:00:00 GMT"; el JSON-LD trae su propia
    # fecha con offset -05:00, que debe ganar.
    assert rec.fecha_publicacion == "2026-07-01T09:00:00-05:00"


def test_fallo_al_recuperar_el_articulo_degrada_a_solo_titular(monkeypatch):
    """Si el fetch del artículo falla (red, 404, bloqueo), la entrada no se
    pierde: cae exactamente al comportamiento anterior (solo titular)."""
    c = _connector_con({"Medio X": "https://medio-x.example/feed/"})

    def fake_get(url: str) -> str:
        if url.endswith("/feed/"):
            return FEED_NUBANK
        raise RuntimeError("artículo bloqueado")

    monkeypatch.setattr(c, "_get", fake_get)
    items = list(c.search(QuerySpec(empresa="Nubank", tipo_evento="lanzamiento")))
    assert len(items) == 1  # la entrada se conserva
    rec = c.normalize(items[0])
    assert rec.cita_textual == "Nubank lanza nuevo producto en México"


def test_sin_json_ld_en_el_articulo_degrada_a_solo_titular(monkeypatch):
    c = _connector_con({"Medio X": "https://medio-x.example/feed/"})

    def fake_get(url: str) -> str:
        if url.endswith("/feed/"):
            return FEED_NUBANK
        return "<html><body>página sin JSON-LD</body></html>"

    monkeypatch.setattr(c, "_get", fake_get)
    items = list(c.search(QuerySpec(empresa="Nubank", tipo_evento="lanzamiento")))
    rec = c.normalize(items[0])
    assert rec.cita_textual == "Nubank lanza nuevo producto en México"


def test_medios_ampliados_estan_en_feeds_default():
    from hd_scraper.connectors.rss_fijos import FEEDS_DEFAULT
    for medio in ("DPL News", "Expansión", "El Financiero", "El CEO", "Forbes México"):
        assert medio in FEEDS_DEFAULT

    # El Economista no se agrega: feed bloqueado con 403, documentado en
    # CLAUDE.md como cerrado, no como pendiente de investigar.
    assert "El Economista" not in FEEDS_DEFAULT
