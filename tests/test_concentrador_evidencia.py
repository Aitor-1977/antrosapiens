from hd_scraper.clasificacion_epistemologica import Clasificacion
from hd_scraper.clasificacion_store import guardar_clasificacion
from hd_scraper.concentrador_evidencia import (
    evidencias_de_organizacion,
    resumen_organizacion,
)
from hd_scraper.db.models import EvidenceRecord, ahora_iso, calcular_hash_dedup
from hd_scraper.pipeline import _escribir_evidencia


def _insertar_evidencia(db, *, connector: str, empresa: str, url: str,
                        tipo_evento: str = "ronda") -> int:
    rec = EvidenceRecord(
        cita_textual=f"{empresa} anuncia una novedad",
        fecha_extraccion=ahora_iso(),
        url_fuente=url,
        nombre_medio="medio.example",
        empresa_mencionada=empresa,
        tipo_evento=tipo_evento,
        origen_declaracion="prensa",
        hash_dedup=calcular_hash_dedup(empresa, url),
        fecha_publicacion="2026-06-01",
        connector=connector,
    )
    assert _escribir_evidencia(db, rec)
    fila = db.fetch_one("SELECT id FROM evidencias WHERE hash_dedup = ?",
                        (rec.hash_dedup,))
    return dict(fila)["id"]


def test_evidencia_sin_organizacion_no_aparece_en_ninguna_organizacion(db):
    _insertar_evidencia(db, connector="google_news", empresa="", url="https://x.example/1")
    assert evidencias_de_organizacion(db, "Acme") == []


def test_caso4_dos_fuentes_misma_organizacion_se_agregan(db):
    """Caso 4 de la especificación: dos fuentes -> dos evidencias -> misma
    organización. Coincidencia exacta por empresa_mencionada (Fase 1)."""
    _insertar_evidencia(db, connector="google_news", empresa="Acme",
                        url="https://news.example/1")
    _insertar_evidencia(db, connector="rss_fijos", empresa="Acme",
                        url="https://rss.example/2")
    evs = evidencias_de_organizacion(db, "Acme")
    assert len(evs) == 2
    assert {e["connector"] for e in evs} == {"google_news", "rss_fijos"}

    resumen = resumen_organizacion(db, "Acme")
    assert resumen.total_evidencias == 2
    assert set(resumen.fuentes_distintas) == {"google_news", "rss_fijos"}


def test_organizaciones_distintas_no_se_mezclan(db):
    _insertar_evidencia(db, connector="google_news", empresa="Acme",
                        url="https://news.example/3")
    _insertar_evidencia(db, connector="google_news", empresa="Otra Co",
                        url="https://news.example/4")
    assert len(evidencias_de_organizacion(db, "Acme")) == 1
    assert len(evidencias_de_organizacion(db, "Otra Co")) == 1


def test_coincidencia_es_exacta_no_hace_fuzzy_match(db):
    """'Acme' y 'Acme Inc.' NO se agrupan: la resolución de entidad sigue
    diferida a propósito (ver CLAUDE.md)."""
    _insertar_evidencia(db, connector="google_news", empresa="Acme",
                        url="https://news.example/5")
    _insertar_evidencia(db, connector="google_news", empresa="Acme Inc.",
                        url="https://news.example/6")
    assert len(evidencias_de_organizacion(db, "Acme")) == 1
    assert len(evidencias_de_organizacion(db, "Acme Inc.")) == 1


def test_une_evidencia_clasificada_de_tavily_por_organizacion_mencionada(db):
    """La identidad organizacional del conector Tavily viaja en
    evidencia_clasificada.organizacion_mencionada (empresa_mencionada ahí es
    la frase de búsqueda, no una organización) — el concentrador debe unir
    por esa columna para ese conector, sin tocar clasificacion_store."""
    ev_tavily_id = _insertar_evidencia(
        db, connector="busqueda_dinamica_founder",
        empresa='"cometí el error de" startup',
        url="https://blog.example/7")
    clas = Clasificacion(
        tipo="senal_primaria_autodeclaracion",
        enunciador_nombre="Jane Doe",
        enunciador_cargo="fundadora",
        enunciador_dominio="tecnologia",
        organizacion_mencionada="Acme",
        razon="autoidentificación con rol",
    )
    guardar_clasificacion(db, None, ev_tavily_id, clas)

    _insertar_evidencia(db, connector="google_news", empresa="Acme",
                        url="https://news.example/8")

    evs = evidencias_de_organizacion(db, "Acme")
    assert len(evs) == 2
    assert {e["connector"] for e in evs} == {
        "busqueda_dinamica_founder", "google_news"}

    resumen = resumen_organizacion(db, "Acme")
    assert resumen.total_evidencias == 2
    assert resumen.senales_primarias == 1


def test_resumen_de_organizacion_sin_evidencia_es_vacio(db):
    resumen = resumen_organizacion(db, "No Existe SA")
    assert resumen.total_evidencias == 0
    assert resumen.fuentes_distintas == ()
    assert resumen.senales_primarias == 0
