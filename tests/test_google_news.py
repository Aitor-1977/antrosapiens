from hd_scraper.config import settings
from hd_scraper.connectors.google_news import GoogleNewsConnector
from hd_scraper.db.models import ESTADO_NO_FECHADO, ESTADO_OK, QuerySpec

FIXTURE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>Nubank - Google News</title>
  <item>
    <title>Nubank anuncia nueva ronda de inversión - Bloomberg Línea</title>
    <link>https://news.google.com/rss/articles/ABC123?oc=5</link>
    <pubDate>Wed, 01 Jul 2026 10:00:00 GMT</pubDate>
    <source url="https://www.bloomberglinea.com">Bloomberg Línea</source>
    <description>La fintech brasileña cierra una ronda liderada por fondos regionales.</description>
  </item>
  <item>
    <title>Nota sin fecha sobre Nubank</title>
    <link>https://news.google.com/rss/articles/NODATE?oc=5</link>
    <source url="https://medio-x.com">Medio X</source>
  </item>
</channel>
</rss>
"""


def _connector(monkeypatch) -> GoogleNewsConnector:
    c = GoogleNewsConnector()
    monkeypatch.setattr(c, "_get", lambda url: FIXTURE_RSS)
    # Los tests de arriba de esta fábrica no ejercitan la resolución del
    # wrapper (eso tiene su propia sección de tests, con mocks explícitos de
    # red): se apaga aquí para que sigan siendo unitarios y deterministas,
    # sin tocar la red real ni depender de su disponibilidad.
    monkeypatch.setattr(c, "_resolver_url_real", lambda url: None)
    return c


def test_search_extrae_items(monkeypatch):
    c = _connector(monkeypatch)
    items = list(c.search(QuerySpec(empresa="Nubank", tipo_evento="ronda")))
    assert len(items) == 2
    assert items[0].meta["fuente"] == "Bloomberg Línea"
    assert items[0].meta["fecha_publicacion"] is not None
    assert items[1].meta["fecha_publicacion"] is None


def test_normalize_no_interpreta_usa_estructura(monkeypatch):
    c = _connector(monkeypatch)
    items = list(c.search(QuerySpec(empresa="Nubank", tipo_evento="ronda")))
    rec = c.normalize(items[0])
    # tipo_evento viene de la consulta (estructura), no del texto:
    assert rec.tipo_evento == "ronda"
    # origen_declaracion es estructural para un feed de prensa:
    assert rec.origen_declaracion == "prensa"
    assert rec.cita_textual.startswith("Nubank anuncia")
    assert rec.nombre_medio == "Bloomberg Línea"
    assert rec.empresa_mencionada == "Nubank"


def test_normalize_conserva_resumen_fuente_distinto_de_cita_textual(monkeypatch):
    """Auditoría 2026-09-10 (P0): el <description>/<summary> del feed se
    conserva en resumen_fuente, NUNCA se mezcla con cita_textual (que sigue
    siendo solo el título) ni se etiqueta como cita de una persona."""
    c = _connector(monkeypatch)
    items = list(c.search(QuerySpec(empresa="Nubank", tipo_evento="ronda")))
    rec0 = c.normalize(items[0])
    assert rec0.resumen_fuente == (
        "La fintech brasileña cierra una ronda liderada por fondos regionales."
    )
    assert rec0.resumen_fuente != rec0.cita_textual
    assert rec0.persona_citada is None  # resumen no se confunde con una cita

    # La segunda entrada no trae <description>: resumen_fuente es None, nunca
    # se sintetiza ni se copia del título para rellenarlo.
    rec1 = c.normalize(items[1])
    assert rec1.resumen_fuente is None


def test_valida_ok_y_no_fechado(monkeypatch):
    c = _connector(monkeypatch)
    items = list(c.search(QuerySpec(empresa="Nubank", tipo_evento="ronda")))
    v0 = c.validate(c.normalize(items[0]))
    v1 = c.validate(c.normalize(items[1]))
    assert v0.ok and v0.estado == ESTADO_OK
    assert v1.ok and v1.estado == ESTADO_NO_FECHADO


# ── Resolución del wrapper de Google News (auditoría 2026-09-14) ───────────
#
# Verificado contra producción: el 100% de una muestra de 1060 evidencias
# reales tenía `url_fuente` = wrapper de Google sin resolver. Estos tests
# cubren el mecanismo de resolución (dos peticiones HTTP planas, sin
# navegador headless) con la red mockeada — deterministas, sin tocar red real.

_HTML_CON_FIRMA = (
    '<div data-n-a-id="CBMi_id_de_prueba" data-n-a-ts="1789420272" '
    'data-n-a-sg="firma_de_prueba"></div>'
)
_RESPUESTA_BATCHEXECUTE_OK = (
    ")]}'\n\n"
    '[["wrb.fr","Fbv4je","[\\"garturlres\\",'
    '\\"https://www.medio-real.com/articulo-verdadero\\",1]",'
    'null,null,null,"generic"],["di",19]]'
)


def test_resolver_url_real_decodifica_wrapper(monkeypatch):
    c = GoogleNewsConnector()
    llamadas = []

    def fake_get(url, timeout):
        llamadas.append(("GET", url))
        return _HTML_CON_FIRMA

    def fake_post(url, data, timeout):
        llamadas.append(("POST", url))
        return _RESPUESTA_BATCHEXECUTE_OK

    monkeypatch.setattr(c, "_get_con_timeout", fake_get)
    monkeypatch.setattr(c, "_post_con_timeout", fake_post)

    resultado = c._resolver_url_real(
        "https://news.google.com/rss/articles/CBMi_id_de_prueba?oc=5"
    )
    assert resultado == "https://www.medio-real.com/articulo-verdadero"
    assert [m for m, _ in llamadas] == ["GET", "POST"]


def test_resolver_url_real_sin_firma_devuelve_none(monkeypatch):
    """Si la página del wrapper no trae los atributos de firma esperados
    (Google cambió el formato, o la respuesta es distinta), no se intenta
    adivinar nada: se degrada al wrapper original."""
    c = GoogleNewsConnector()
    monkeypatch.setattr(c, "_get_con_timeout", lambda url, timeout: "<html>sin firma</html>")
    assert c._resolver_url_real("https://news.google.com/rss/articles/X?oc=5") is None


def test_resolver_url_real_ante_excepcion_de_red_devuelve_none(monkeypatch):
    """Cualquier fallo de red (timeout, conexión rechazada, 4xx/5xx tras
    agotar reintentos) es best-effort puro: nunca rompe la ingesta."""
    c = GoogleNewsConnector()

    def falla(url, timeout):
        raise TimeoutError("simulado")

    monkeypatch.setattr(c, "_get_con_timeout", falla)
    assert c._resolver_url_real("https://news.google.com/rss/articles/X?oc=5") is None


def test_resolver_url_real_respuesta_batchexecute_malformada_devuelve_none(monkeypatch):
    c = GoogleNewsConnector()
    monkeypatch.setattr(c, "_get_con_timeout", lambda url, timeout: _HTML_CON_FIRMA)
    monkeypatch.setattr(c, "_post_con_timeout", lambda url, data, timeout: "esto no es JSON válido")
    assert c._resolver_url_real("https://news.google.com/rss/articles/X?oc=5") is None


def test_search_resuelve_wrapper_y_respeta_tope_por_corrida(monkeypatch):
    """search() usa la URL resuelta cuando está disponible, y dos entradas
    con wrapper != la misma URL no chocan entre sí. El tope
    (`google_news_resolver_max`) evita que un feed grande dispare
    resoluciones sin límite dentro del tiempo de una función serverless."""
    c = GoogleNewsConnector()
    monkeypatch.setattr(c, "_get", lambda url: FIXTURE_RSS)

    llamadas = []

    def fake_resolver(wrapper_url):
        llamadas.append(wrapper_url)
        return "https://www.bloomberglinea.com/articulo-real"

    monkeypatch.setattr(c, "_resolver_url_real", fake_resolver)
    items = list(c.search(QuerySpec(empresa="Nubank", tipo_evento="ronda")))
    assert len(llamadas) == 2  # las 2 entradas del fixture tienen wrapper
    assert items[0].meta["link"] == "https://www.bloomberglinea.com/articulo-real"

    # Con el tope en 1, la segunda entrada conserva el wrapper original (sin
    # regresión: es exactamente el comportamiento de antes de esta corrección).
    # `settings` es un dataclass inmutable: se sustituye la referencia que usa
    # el módulo del conector por una copia con el tope bajado, en vez de mutarla.
    import dataclasses

    import hd_scraper.connectors.google_news as gn_mod
    monkeypatch.setattr(gn_mod, "settings", dataclasses.replace(settings, google_news_resolver_max=1))
    c2 = GoogleNewsConnector()
    monkeypatch.setattr(c2, "_get", lambda url: FIXTURE_RSS)
    monkeypatch.setattr(c2, "_resolver_url_real", fake_resolver)
    items2 = list(c2.search(QuerySpec(empresa="Nubank", tipo_evento="ronda")))
    assert items2[0].meta["link"] == "https://www.bloomberglinea.com/articulo-real"
    assert items2[1].meta["link"] == "https://news.google.com/rss/articles/NODATE?oc=5"


# ── Limpieza de resumen_fuente (Google News no entrega cuerpo real) ────────


def test_resumen_fuente_descarta_marcado_html_redundante_con_el_titulo(monkeypatch):
    """Verificado contra el feed real de Google News (auditoría 2026-09-14):
    <description> no trae un extracto del artículo, trae
    `<a href="...">TITULAR</a>&nbsp;&nbsp;<font>MEDIO</font>` — el mismo
    titular disfrazado de marcado HTML. Guardar eso como resumen_fuente
    presentaría el titular como si fuera contenido nuevo: se descarta."""
    fixture = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><item>
  <title>Nowports abre sede en Miami</title>
  <link>https://news.google.com/rss/articles/REAL1?oc=5</link>
  <pubDate>Wed, 01 Jul 2026 10:00:00 GMT</pubDate>
  <source url="https://www.wired.com">WIRED</source>
  <description>&lt;a href="https://news.google.com/rss/articles/REAL1?oc=5" target="_blank"&gt;Nowports abre sede en Miami&lt;/a&gt;&amp;nbsp;&amp;nbsp;&lt;font color="#6f6f6f"&gt;WIRED&lt;/font&gt;</description>
</item></channel></rss>
"""
    c = GoogleNewsConnector()
    monkeypatch.setattr(c, "_get", lambda url: fixture)
    monkeypatch.setattr(c, "_resolver_url_real", lambda url: None)
    items = list(c.search(QuerySpec(empresa="Nowports", tipo_evento="expansion")))
    rec = c.normalize(items[0])
    assert rec.resumen_fuente is None
    assert rec.cita_textual == "Nowports abre sede en Miami"


def test_resumen_fuente_conserva_contenido_realmente_distinto(monkeypatch):
    """Cuando el resumen SÍ trae información más allá del titular (formato
    de descripción simple, sin el envoltorio de enlace de Google), se
    conserva — no todo resumen se descarta, solo el que no aporta nada."""
    c = _connector(monkeypatch)
    items = list(c.search(QuerySpec(empresa="Nubank", tipo_evento="ronda")))
    rec = c.normalize(items[0])
    assert rec.resumen_fuente == (
        "La fintech brasileña cierra una ronda liderada por fondos regionales."
    )
