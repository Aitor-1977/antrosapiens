"""Resolver de sitio oficial: multi-estrategia + niveles de confianza.

Cubre el arreglo del bug "100% Sin web clara": ahora hay tres desenlaces
posibles (confirmada / probable / no_confirmada), no un único mensaje.
"""
import importlib

import pytest
from fastapi.testclient import TestClient

from hd_scraper.config import settings
from hd_scraper.enrich import (
    CONF_CONFIRMADA,
    CONF_NO,
    CONF_PROBABLE,
    dominios_candidatos,
    elegir_sitio_oficial,
    enriquecer,
    extraer_snippets_busqueda,
    parse_resultados_busqueda,
    resolver_sitio,
    sugerir_vertical,
)

SITE_KASZEK = """<html><head><title>Kaszek</title>
<meta name="description" content="Kaszek es un fondo de venture capital para founders en América Latina.">
</head><body><h1>Invertimos en los mejores founders de LatAm</h1>
<p>Respaldamos compañías de tecnología en etapas tempranas con tesis de largo plazo.</p></body></html>"""

SITE_GENERICO = """<html><head><title>Bienvenido</title>
<meta name="description" content="Sitio en construcción."></head><body><p>Hola mundo.</p></body></html>"""

LITE_KASZEK = """<html><body><table>
<tr><td><a rel="nofollow" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fwww.linkedin.com%2Fcompany%2Fkaszek">LinkedIn</a></td></tr>
<tr><td><a rel="nofollow" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fkaszek.com%2F">Kaszek</a></td></tr>
</table></body></html>"""

LITE_NO_MATCH = """<html><body><table>
<tr><td><a rel="nofollow" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.org%2Facme">Acme en Example</a></td></tr>
</table></body></html>"""

# Página de resultados con snippets descriptivos (columna result-snippet de DDG lite).
LITE_SNIPPETS = """<html><body><table>
<tr><td class="result-link"><a href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fpolo.com%2F">Polo</a></td></tr>
<tr><td class="result-snippet">Polo es una fintech de pagos que ofrece una plataforma de crédito para pymes en México y la región.</td></tr>
</table></body></html>"""


# ── piezas ──────────────────────────────────────────────────────────────────

def test_parse_resultados_decodifica_uddg_y_omite_ddg():
    urls = parse_resultados_busqueda(LITE_KASZEK)
    assert "https://kaszek.com/" in urls
    assert "https://www.linkedin.com/company/kaszek" in urls
    assert not any("duckduckgo.com" in u for u in urls)


def test_elegir_sitio_ignora_redes():
    assert elegir_sitio_oficial(
        ["https://www.linkedin.com/company/x", "https://kaszek.com/"]) == "https://kaszek.com/"


def test_dominios_candidatos():
    cands = dominios_candidatos("Kaszek Ventures")
    assert "https://kaszek.com" in cands  # token principal + .com
    assert any(c.endswith(".com.mx") for c in cands)


def test_sugerir_vertical():
    assert sugerir_vertical("Somos una fintech de pagos") == "fintech"
    assert sugerir_vertical("plataforma de terapia y salud mental") == "salud mental"
    assert sugerir_vertical("comida rica") is None


# ── resolver: los tres niveles de confianza ──────────────────────────────────

def test_resolver_confirmada_por_dominio():
    # El dominio adivinado responde y menciona el nombre -> confirmada.
    def get(url):
        if url == "https://kaszek.com":
            return SITE_KASZEK
        raise RuntimeError("404")
    sitio, conf, _ = resolver_sitio("Kaszek", get)
    assert conf == CONF_CONFIRMADA and sitio == "https://kaszek.com"


def test_resolver_confirmada_por_busqueda():
    # Adivinar falla; la búsqueda devuelve un host que coincide -> confirmada.
    def get(url):
        if "lite.duckduckgo.com" in url:
            return LITE_KASZEK
        raise RuntimeError("sin dominio")
    sitio, conf, _ = resolver_sitio("Kaszek", get)
    assert conf == CONF_CONFIRMADA and "kaszek.com" in sitio


def test_resolver_probable_por_busqueda_sin_coincidencia():
    # La búsqueda trae un resultado cuyo host NO coincide con el nombre -> probable.
    def get(url):
        if "lite.duckduckgo.com" in url:
            return LITE_NO_MATCH
        raise RuntimeError("sin dominio")
    sitio, conf, _ = resolver_sitio("Acme", get)
    assert conf == CONF_PROBABLE and sitio == "https://example.org/acme"


def test_resolver_probable_por_dominio_sin_mencion():
    # El dominio responde 200 pero no menciona el nombre, y no hay búsqueda -> probable.
    def get(url):
        if url == "https://acme.com":
            return SITE_GENERICO
        raise RuntimeError("nada")
    sitio, conf, _ = resolver_sitio("Acme", get)
    assert conf == CONF_PROBABLE and sitio == "https://acme.com"


def test_resolver_no_confirmada():
    def get(url):
        raise RuntimeError("todo falla")
    sitio, conf, notas = resolver_sitio("Empresa Rara", get)
    assert sitio is None and conf == CONF_NO and notas


def test_no_todos_devuelven_lo_mismo():
    # Evidencia directa del arreglo: distintos insumos -> distintos niveles.
    confirmada = resolver_sitio("Kaszek", lambda u: SITE_KASZEK if u == "https://kaszek.com" else (_ for _ in ()).throw(RuntimeError()))[1]
    nula = resolver_sitio("Zzz", lambda u: (_ for _ in ()).throw(RuntimeError()))[1]
    assert confirmada != nula
    assert {confirmada, nula} == {CONF_CONFIRMADA, CONF_NO}


# ── orquestación / endpoint ───────────────────────────────────────────────────

def test_enriquecer_incluye_confianza_y_no_lanza():
    d = enriquecer("Kaszek", lambda u: SITE_KASZEK if u == "https://kaszek.com" else (_ for _ in ()).throw(RuntimeError()))
    assert d["sitio_web"] == "https://kaszek.com"
    assert d["sitio_confianza"] == CONF_CONFIRMADA
    assert "venture capital" in d["discurso"]

    d2 = enriquecer("Empresa Inexistente XYZ", lambda u: (_ for _ in ()).throw(RuntimeError()))
    assert d2["sitio_web"] is None and d2["sitio_confianza"] == CONF_NO
    assert d2["linkedin"].startswith("https://www.linkedin.com")


# ── camino 1: descripción desde snippets de búsqueda ──────────────────────────

def test_extraer_snippets_busqueda():
    texto = extraer_snippets_busqueda(LITE_SNIPPETS)
    assert "fintech de pagos" in texto
    assert "duckduckgo" not in texto.lower()


def test_enriquecer_usa_snippets_cuando_el_sitio_no_da_discurso():
    # Sitio confirmado por dominio pero SIN texto legible (web en JavaScript):
    # el discurso debe venir de los snippets de búsqueda (camino 1).
    SITE_VACIO = "<html><head><title>Polo</title></head><body><div id=root></div></body></html>"

    def get(url):
        if url == "https://polo.com":
            return SITE_VACIO
        if "lite.duckduckgo.com" in url:
            return LITE_SNIPPETS
        raise RuntimeError("sin dominio")

    d = enriquecer("Polo", get)
    assert "fintech de pagos" in d["discurso"]
    assert "búsqueda" in d["fuentes"]
    assert d["vertical_sugerida"] == "fintech"


def test_endpoint_enrich_requiere_token(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    object.__setattr__(settings, "ingest_token", "secreto")
    cli = TestClient(api.app)
    assert cli.post("/enrich", json={"nombre": "Kaszek"}).status_code == 401
    object.__setattr__(settings, "ingest_token", "")
