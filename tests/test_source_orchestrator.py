import json
from typing import Iterable

from hd_scraper import source_orchestrator
from hd_scraper.connectors.base import Connector
from hd_scraper.connectors.busqueda_dinamica import BusquedaDinamicaConnector
from hd_scraper.config import settings
from hd_scraper.db.models import EvidenceRecord, QuerySpec, RawItem, ahora_iso, calcular_hash_dedup
from hd_scraper.pipeline import run_connector
from hd_scraper.source_orchestrator import FUENTES_ACTIVAS_POR_DEFECTO, orquestar

FIXTURE_TAVILY = {
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
    ],
}


class _FakeConnector(Connector):
    """Conector de prueba, sin red: para probar el fan-out de forma aislada."""

    name = "fake_source"
    origen_declaracion_default = "prensa"

    def search(self, query: QuerySpec) -> Iterable[RawItem]:
        return [RawItem(url="https://fake.example/1", contenido="{}", formato="json", meta={})]

    def fetch(self, url: str) -> RawItem:  # pragma: no cover - no se usa en el pipeline
        return RawItem(url=url, contenido="{}")

    def normalize(self, raw: RawItem) -> EvidenceRecord:
        return EvidenceRecord(
            cita_textual="Empresa Fake anuncia una ronda de inversión",
            fecha_extraccion=ahora_iso(),
            url_fuente=raw.url,
            nombre_medio="fake.example",
            empresa_mencionada="Empresa Fake",
            tipo_evento="ronda",
            origen_declaracion="prensa",
            hash_dedup=calcular_hash_dedup("Empresa Fake", raw.url),
            fecha_publicacion="2026-06-01",
            connector=self.name,
        )


class _OtraFakeConnector(_FakeConnector):
    name = "otra_fake_source"

    def search(self, query: QuerySpec) -> Iterable[RawItem]:
        return [RawItem(url="https://fake.example/2", contenido="{}", formato="json", meta={})]

    def normalize(self, raw: RawItem) -> EvidenceRecord:
        rec = super().normalize(raw)
        rec.cita_textual = "Otra Empresa Fake despide a parte de su equipo"
        rec.empresa_mencionada = "Otra Empresa Fake"
        rec.tipo_evento = "despido"
        rec.hash_dedup = calcular_hash_dedup("Otra Empresa Fake", raw.url)
        rec.connector = self.name
        return rec


def _query() -> QuerySpec:
    return QuerySpec(empresa="Empresa Fake", tipo_evento="ronda")


def test_fuente_no_registrada_se_omite_sin_romper_las_demas(db, monkeypatch):
    monkeypatch.setitem(source_orchestrator.REGISTRY, "fake_source", _FakeConnector)
    resultado = orquestar(db, _query(), fuentes=("fake_source", "fuente_inexistente"))
    assert resultado.fuentes_no_registradas == ["fuente_inexistente"]
    assert "fake_source" in resultado.resultados_por_fuente
    assert resultado.resultados_por_fuente["fake_source"].escritos == 1
    assert resultado.escritos_totales == 1


def test_fan_out_agrega_resultados_de_varias_fuentes(db, monkeypatch):
    monkeypatch.setitem(source_orchestrator.REGISTRY, "fake_source", _FakeConnector)
    monkeypatch.setitem(source_orchestrator.REGISTRY, "otra_fake_source", _OtraFakeConnector)
    resultado = orquestar(db, _query(), fuentes=("fake_source", "otra_fake_source"))
    assert set(resultado.resultados_por_fuente) == {"fake_source", "otra_fake_source"}
    assert resultado.escritos_totales == 2
    total = db.fetch_one("SELECT COUNT(*) AS n FROM evidencias")["n"]
    assert total == 2
    # No se tocó ninguna lógica de clasificación ni de identidad organizacional:
    # cada fuente escribió exactamente su propia evidencia, sin cruces.
    clasificadas = db.fetch_one("SELECT COUNT(*) AS n FROM evidencia_clasificada")["n"]
    assert clasificadas == 0


def test_orquestar_sin_fuentes_no_escribe_nada(db):
    resultado = orquestar(db, _query(), fuentes=())
    assert resultado.resultados_por_fuente == {}
    assert resultado.fuentes_no_registradas == []
    assert resultado.escritos_totales == 0


def _connector_tavily(monkeypatch) -> BusquedaDinamicaConnector:
    object.__setattr__(settings, "tavily_api_key", "tvly-fake-key")
    monkeypatch.setattr(
        BusquedaDinamicaConnector, "_post",
        lambda self, url, payload: json.dumps(FIXTURE_TAVILY),
    )
    return BusquedaDinamicaConnector()


def test_orquestar_con_tavily_produce_el_mismo_resultado_que_run_connector_directo(db, monkeypatch):
    """Caso 7 de la especificación: la fuente activa hoy (Tavily) debe
    comportarse EXACTAMENTE igual orquestada que invocada directamente — el
    orquestador no debe alterar ni el conteo ni el contenido persistido."""
    frases = (('"cometí el error de" startup', "queja"),)

    c_directo = _connector_tavily(monkeypatch)
    c_directo.frases = frases
    query = QuerySpec(empresa="x", tipo_evento="queja")
    resultado_directo = run_connector(db, c_directo, query)

    db2 = source_orchestrator.Database(":memory:")
    db2.init_schema()
    c_orquestado = _connector_tavily(monkeypatch)
    c_orquestado.frases = frases
    monkeypatch.setitem(
        source_orchestrator.REGISTRY, "busqueda_dinamica_founder",
        lambda: c_orquestado,
    )
    resultado_orquestado = orquestar(db2, query, fuentes=FUENTES_ACTIVAS_POR_DEFECTO)

    directo = resultado_directo
    orquestado = resultado_orquestado.resultados_por_fuente["busqueda_dinamica_founder"]
    assert orquestado.vistos == directo.vistos
    assert orquestado.escritos == directo.escritos
    assert orquestado.no_fechados == directo.no_fechados
    assert orquestado.rechazados == directo.rechazados
