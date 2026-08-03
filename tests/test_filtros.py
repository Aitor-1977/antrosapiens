"""Filtros avanzados del radar (Región, Enfoque, Tamaño, Palabra clave).

Verifican el vocabulario estructural, la selección de objetivos por
categorías/escalas y su traducción a parámetros de consulta por fuente.
"""
import pytest

from hd_scraper.connectors.gdelt import GdeltConnector
from hd_scraper.connectors.google_news import GoogleNewsConnector
from hd_scraper.db.models import QuerySpec
from hd_scraper.filtros import (
    CATEGORIAS_FILTRO,
    ESCALAS,
    REGIONES,
    FiltrosRadar,
    descripcion,
    filtros_desde_env,
    objetivos_por_filtros,
)


def test_vocabularios_estructura():
    assert "Toda LATAM" in REGIONES
    assert set(REGIONES["México"]) == {"gl", "hl", "ceid", "country"}
    assert set(CATEGORIAS_FILTRO) == {"VC", "Startup", "Incubadora", "Corporativo"}
    assert "1-10" in ESCALAS and "501+" in ESCALAS


def test_region_default_es_toda_latam():
    assert FiltrosRadar().region == "Toda LATAM"
    assert FiltrosRadar().activo is False


def test_filtros_activo_con_cualquier_campo():
    assert FiltrosRadar(region="Chile").activo
    assert FiltrosRadar(categorias=("VC",)).activo
    assert FiltrosRadar(escalas=("1-10",)).activo
    assert FiltrosRadar(palabra_clave="fintech").activo


def test_terminos_extra_ignora_espacios():
    assert FiltrosRadar(palabra_clave="  ").terminos_extra is None
    assert FiltrosRadar(palabra_clave="fintech").terminos_extra == "fintech"


def test_objetivos_por_filtros_sin_filtros_devuelve_base():
    base = objetivos_por_filtros()
    assert len(base) >= 40
    assert objetivos_por_filtros(FiltrosRadar()) == base


def test_filtro_por_categoria_solo_incluye_metadatos():
    vc = objetivos_por_filtros(FiltrosRadar(categorias=("VC",)))
    corp = objetivos_por_filtros(FiltrosRadar(categorias=("Corporativo",)))
    assert vc and corp and set(vc).isdisjoint(set(corp))
    assert "Kaszek" in vc and "Mercado Libre" in corp


def test_filtro_por_tamano_dos_bandas():
    r = objetivos_por_filtros(FiltrosRadar(escalas=("501+",)))
    assert r and "Mercado Libre" in r


def test_filtro_combinado_categoria_y_tamano(monkeypatch):
    # sin HD_TRACKED_EMPRESAS la explícita no aplica
    monkeypatch.delenv("HD_TRACKED_EMPRESAS", raising=False)
    r = objetivos_por_filtros(FiltrosRadar(categorias=("Startup",), escalas=("1-10",)))
    assert r and len(r) < len(objetivos_por_filtros(FiltrosRadar(categorias=("Startup",))))


def test_tracked_explicito_gana_sobre_filtros(monkeypatch):
    monkeypatch.setenv("HD_TRACKED_EMPRESAS", "Acme,CorpX")
    assert objetivos_por_filtros(FiltrosRadar(categorias=("VC",))) == ("Acme", "CorpX")


def test_filtros_desde_env(monkeypatch):
    monkeypatch.setenv("HD_RADAR_REGION", "Brasil")
    monkeypatch.setenv("HD_RADAR_CATEGORIAS", "VC,Corporativo,Malo")
    monkeypatch.setenv("HD_RADAR_ESCALAS", "1-10,999+")
    monkeypatch.setenv("HD_RADAR_PALABRA_CLAVE", " expansion ")
    f = filtros_desde_env()
    assert f.region == "Brasil"
    assert f.categorias == ("VC", "Corporativo")       # 'Malo' se descarta
    assert f.escalas == ("1-10",)                       # '999+' se descarta
    assert f.palabra_clave == "expansion"


def test_filtros_desde_env_region_invalida_vuelve_default(monkeypatch):
    monkeypatch.setenv("HD_RADAR_REGION", "NoExiste")
    assert filtros_desde_env().region == "Toda LATAM"


def test_descripcion_describe_lo_aplicado():
    d = descripcion(FiltrosRadar(region="México", categorias=("VC",),
                                 palabra_clave="fintech"))
    assert "México" in d and "VC" in d and "fintech" in d


def test_google_news_aplica_region_y_keyword():
    c = GoogleNewsConnector()
    url = c._build_url(QuerySpec(empresa="Kavak", tipo_evento="ronda",
                                 region="México", terminos="expansión"))
    assert "hl=es" in url and "gl=MX" in url and "ceid=MX%3Aes" in url
    assert "expansi%C3%B3n" in url


def test_google_news_default_sin_region_mantiene_params_clase():
    c = GoogleNewsConnector()
    url = c._build_url(QuerySpec(empresa="Kavak", tipo_evento="ronda"))
    assert "hl=es-419" in url and "gl=MX" in url


def test_gdelt_traduce_region_a_sourcecountry():
    g = GdeltConnector()
    url = g._build_url(QuerySpec(empresa="Kavak", tipo_evento="ronda", region="Brasil"))
    assert "sourcecountry%3ABR" in url


def test_gdelt_toda_latam_no_anade_sourcecountry():
    g = GdeltConnector()
    url = g._build_url(QuerySpec(empresa="Kavak", tipo_evento="ronda", region="Toda LATAM"))
    assert "sourcecountry" not in url


def test_queryspec_region_roundtrip():
    q = QuerySpec(empresa="Kavak", tipo_evento="ronda", region="Chile")
    assert QuerySpec.from_dict(q.to_dict()).region == "Chile"
